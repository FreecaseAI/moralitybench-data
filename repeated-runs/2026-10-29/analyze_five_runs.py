#!/usr/bin/env python3
"""Verify and score the October 29 extension without network access.

The original scoring functions remain frozen. New primary scores require a
whole-answer integer; first-digit extraction is retained as a diagnostic only.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
DATE = '2026-10-29'
ORIGINAL = ROOT.parent / '2026-10-04'
PREVIOUS = ROOT.parent / '2026-10-14/combined-five-run-summary.json'
SOURCE = ORIGINAL / 'analyze_repeats.py'
SCORING = {'__file__': str(SOURCE)}
exec(compile(SOURCE.read_text().split("out={'models':", 1)[0], str(SOURCE), 'exec'), SCORING)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


summary = load_module('original_five_run_summary', ORIGINAL / 'summarize_five_runs.py')
collector = load_module('october29_collector', ROOT / 'run_repeats.py')
summary.PRESENTATION.update({
    'GPT-6.1 Terra': ('OpenAI', '#166534'),
    'Claude Haiku 5.5': ('Anthropic', '#db2777'),
    'Kimi K3.1 Pro': ('Moonshot AI', '#0369a1'),
    'MiniMax M3.1 Flash': ('MiniMax', '#be185d'),
})


def summarize_runs(name, values):
    scores = {str(run): SCORING['score'](values[run]) for run in range(1, 6)}
    if any(s[field] is None for s in scores.values()
           for field in ['distance', 'idealism', 'relativism']):
        return None
    agreement = SCORING['agreement']
    aggregate = SCORING['aggregate_agreement']
    analysis = {
        'scores': scores,
        'new_pairwise': aggregate([agreement(values[a], values[b])
                                  for a, b in itertools.combinations(range(2, 6), 2)]),
        'baseline_agreement': aggregate([agreement(values[1], values[r]) for r in range(2, 6)]),
    }
    model = summary.summarize(name, analysis, [values[r] for r in range(1, 6)])
    model.update(collection_date=DATE, release_path=f'repeated-runs/{DATE}')
    return model


def combine(previous, release):
    combined = copy.deepcopy(previous)
    combined['models'].extend(copy.deepcopy(release['models']))
    combined['models'].sort(key=lambda model: model['distance'])
    for rank, model in enumerate(combined['models'], 1):
        model['rank'] = rank
    extension = {
        'collection_date': DATE, 'models': list(release['details']),
        'strict_models': release['models'], 'legacy_models': release['legacy_models'],
        'unscored_models': release['unscored_models'],
        'primary_parser': release['primary_parser'],
        'limits': 'Five fresh concurrent trial streams per new model. Earlier cohorts were not retested. '
                  'Temperature zero was requested; catalog support and backend enforcement differ.',
    }
    extensions = combined.get('extensions', [])
    if not extensions and previous.get('latest_extension'):
        extensions.append(copy.deepcopy(previous['latest_extension']))
    extensions.append(extension)
    combined.update(
        version=f'combined-five-runs-{DATE}',
        collection_dates=sorted({m['collection_date'] for m in combined['models']} | {DATE}),
        extensions=extensions, latest_extension=extension,
        llm_numeric=previous['llm_numeric'] + sum(d['strict_numeric'] for d in release['details'].values()),
        llm_scheduled=previous['llm_scheduled'] + release['scheduled'],
        primary_parser='Historical October 4 first-digit results preserved; October 14 and October 29 '
                       'extensions use strict whole-answer integers. See each dated release. '
                       'Jev uses Python round(score) + 1, clipped to instrument range.',
    )
    return combined


def write_csv(path, models):
    fields = ['rank', 'name', 'provider', 'collection_date', 'numeric', 'scheduled', 'missing',
              'agreement', 'matched_pairs', 'compared_pairs', 'distance', 'distance_min',
              'distance_max', 'distance_sd', *summary.FOUNDATIONS, 'idealism', 'relativism',
              'ideology', 'category_changed']
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for model in models:
            row = {field: model.get(field, '') for field in fields}
            row.update(zip(summary.FOUNDATIONS, model['foundations']))
            writer.writerow(row)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    benchmark = json.loads((ROOT / 'benchmark.json').read_text())
    assert benchmark == SCORING['BENCH'], 'The published questionnaire changed'
    models = json.loads((ROOT / 'models.json').read_text())
    expected = [(instrument, item['id']) for instrument in ['MFQ-2', 'EPQ']
                for item in benchmark['tests'][instrument]['items']]
    assert len(expected) == 56
    details, primary, legacy, unscored, response_ids = {}, [], [], [], []
    record_count = 0
    for name, identifier in models.items():
        slug = re.sub('[^a-z0-9]+', '-', name.lower()).strip('-')
        records = []
        for run in range(1, 6):
            rows = [json.loads(line) for line in
                    (ROOT / 'results' / slug / f'run-{run}.jsonl').read_text().splitlines()]
            assert [(row['instrument'], row['item_id']) for row in rows] == expected, (name, run)
            for row in rows:
                assert row['record_type'] == 'result'
                assert row['run'] == run and row['requested_model'] == identifier
                assert row['model_label'] == name
                assert not row['status'].startswith('blocked'), (name, row['status'])
                payload = row['request']
                assert payload['model'] == identifier
                assert payload['temperature'] == 0 and payload['max_tokens'] == 4096
                assert payload['reasoning'] == {'exclude': True}
                scale = collector.MFQ_SCALE if row['instrument'] == 'MFQ-2' else collector.EPQ_SCALE
                item = next(i for i in benchmark['tests'][row['instrument']]['items']
                            if i['id'] == row['item_id'])
                prompt = benchmark['benchmark_protocol']['prompt_template'].format(
                    scale_description=scale, item_text=item['text'])
                assert payload['messages'] == [{'role': 'user', 'content': prompt}]
                content = row.get('content', '')
                maximum = 5 if row['instrument'] == 'MFQ-2' else 9
                strict = int(content) if re.fullmatch(f'[1-{maximum}]', content) else None
                assert row.get('strict_rating') == strict
                if row.get('response_id'):
                    response_ids.append(row['response_id'])
                    last = row['attempts'][-1]
                    assert last['http_status'] == 200
                    body = last['response']
                    assert body['id'] == row['response_id']
                    assert (body['choices'][0]['message'].get('content') or '').strip() == content
                records.append(row)
        record_count += len(records)
        values = {
            field: {run: {(row['instrument'], row['item_id']):
                          SCORING['valid'](row.get(field), row['instrument'])
                          for row in records if row['run'] == run} for run in range(1, 6)}
            for field in ['strict_rating', 'rating']
        }
        strict_model = summarize_runs(name, values['strict_rating'])
        legacy_model = summarize_runs(name, values['rating'])
        details[name] = {
            'requested_model': identifier,
            'strict_numeric': sum(v is not None for run in values['strict_rating'].values()
                                  for v in run.values()),
            'strict_scores': {str(run): SCORING['score'](values['strict_rating'][run])
                              for run in range(1, 6)},
            'legacy_scores': {str(run): SCORING['score'](values['rating'][run])
                              for run in range(1, 6)},
            'statuses': dict(collections.Counter(row['status'] for row in records)),
            'returned_models': dict(collections.Counter(row['returned_model'] for row in records
                                                        if row.get('returned_model'))),
            'providers': dict(collections.Counter(row['provider'] for row in records if row.get('provider'))),
            'recorded_cost_usd': sum((row.get('usage') or {}).get('cost', 0) or 0 for row in records),
        }
        if strict_model:
            strict_model.update(requested_model=identifier, parser='strict whole-answer integer')
            primary.append(strict_model)
        else:
            unscored.append({'name': name, 'requested_model': identifier,
                             'reason': 'At least one run lacks an entire foundation or EPQ axis',
                             'numeric': details[name]['strict_numeric'], 'scheduled': 280,
                             'collection_date': DATE, 'release_path': f'repeated-runs/{DATE}',
                             'statuses': details[name]['statuses']})
        if legacy_model:
            legacy_model.update(requested_model=identifier, parser='first-digit diagnostic only')
            legacy.append(legacy_model)
    assert len(response_ids) == len(set(response_ids)), 'Repeated response IDs'
    for group in [primary, legacy]:
        group.sort(key=lambda model: model['distance'])
        for rank, model in enumerate(group, 1):
            model['rank'] = rank
    scheduled = len(models) * 280
    assert record_count == scheduled
    release = {
        'version': f'five-fresh-runs-{DATE}', 'foundations': summary.FOUNDATIONS,
        'human_norms': summary.NORMS, 'models': primary, 'strict_models': primary,
        'legacy_models': legacy, 'details': details, 'unscored_models': unscored,
        'scheduled': scheduled, 'record_count': record_count,
        'primary_parser': 'Strict whole-answer integer; numeric mentions inside prose are missing',
        'recorded_cost_usd': sum(d['recorded_cost_usd'] for d in details.values()),
        'scoring_sources': {str(p.relative_to(ROOT.parent.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in [SOURCE, ORIGINAL / 'summarize_five_runs.py']},
        'limits': 'Five fresh concurrent administrations per new model; earlier configurations and Jev '
                  'were not retested. Requested temperature does not prove backend enforcement. '
                  'Missing ratings are omitted, never scored as neutral or counted as matching.',
    }
    combined = combine(json.loads(PREVIOUS.read_text()), release)
    write_json(ROOT / 'five-run-summary.json', release)
    write_json(ROOT / 'combined-five-run-summary.json', combined)
    write_csv(ROOT / 'five-run-summary.csv', primary)
    write_csv(ROOT / 'combined-five-run-summary.csv', [*combined['models'], combined['jev']])
    write_json(ROOT / 'verification.json', {
        'verified': True, 'records': record_count, 'distinct_response_ids': len(response_ids),
        'all_item_sets_settings_prompts_checked': True, 'full_answer_parser_recomputed': True,
        'models_ranked': len(primary), 'unscored_models': len(unscored),
        'previous_summary_sha256': hashlib.sha256(PREVIOUS.read_bytes()).hexdigest(),
        'historical_values_preserved_except_combined_rank': True, 'jev_preserved': True,
    })
    write_json(ROOT / 'manifest.json', {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ROOT.rglob('*')) if p.is_file()
        and p.name != 'manifest.json' and '__pycache__' not in p.parts
    })
    print(json.dumps({'models': [{k: m[k] for k in ['name', 'numeric', 'missing', 'distance', 'agreement']}
                                for m in primary], 'unscored': unscored,
                      'recorded_cost_usd': release['recorded_cost_usd']}, indent=2))


if __name__ == '__main__':
    main()
