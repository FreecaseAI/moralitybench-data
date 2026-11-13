#!/usr/bin/env python3
"""Score the 2026-11-12 five-run reruns and merge them into the combined cohort summary."""
import collections
import copy
import csv
import hashlib
import importlib.util
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OCT04 = ROOT.parent / '2026-10-04'
OCT29 = ROOT.parent / '2026-10-29'

SOURCE = OCT04 / 'analyze_repeats.py'
NS = {'__file__': str(SOURCE)}
exec(compile(SOURCE.read_text().split("out={'models':", 1)[0], str(SOURCE), 'exec'), NS)

SPEC = importlib.util.spec_from_file_location('previous_summary', OCT04 / 'summarize_five_runs.py')
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)
SUMMARY.PRESENTATION.update({
    'GPT-6 Astra': ('OpenAI', '#9a3412'),
    'Muse Wonder': ('Meta', '#9333ea'),
    'Gemini 4 Argon': ('Google', '#1d4ed8'),
    'GPT-6.1 Terra': ('OpenAI', '#166534'),
    'Claude Haiku 5.5': ('Anthropic', '#db2777'),
    'Kimi K3.1 Pro': ('Moonshot AI', '#0369a1'),
    'MiniMax M3.1 Flash': ('MiniMax', '#be185d'),
    'Muse Spark 1.3': ('Meta', '#6b21a8'),
    'Mistral Large 2512': ('Mistral AI', '#854d0e'),
})

CSV_FIELDS = [
    'rank', 'name', 'provider', 'collection_date', 'numeric', 'scheduled', 'missing',
    'agreement', 'matched_pairs', 'compared_pairs', 'distance', 'distance_min',
    'distance_max', 'distance_sd', 'Care', 'Equality', 'Proportionality', 'Loyalty',
    'Authority', 'Purity', 'idealism', 'relativism', 'ideology', 'category_changed',
]


def expected_prompt(bench: dict, instrument: str, item_id: int) -> str:
    anchors = bench['tests'][instrument]['response_scale']['anchors']
    scale_desc = ', '.join(f'{k} = {v}' for k, v in anchors.items())
    item_text = next(i['text'] for i in bench['tests'][instrument]['items'] if i['id'] == item_id)
    return bench['benchmark_protocol']['prompt_template'].format(
        scale_description=scale_desc,
        item_text=item_text,
    )


def recompute_ratings(content: str, instrument: str) -> tuple[int | None, int | None]:
    limit = 5 if instrument == 'MFQ-2' else 9
    text = (content or '').strip()
    strict = int(text) if re.fullmatch(f'[1-{limit}]', text) else None
    first = next((int(ch) for ch in text if '1' <= ch <= str(limit)), None)
    return first, strict


def write_summary_csv(path: Path, models: list[dict], jev: dict | None = None) -> None:
    with path.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_FIELDS)
        for m in models:
            writer.writerow([
                m['rank'], m['name'], m['provider'], m.get('collection_date', ''),
                m['numeric'], m['scheduled'], m['missing'], m['agreement'],
                m['matched_pairs'], m['compared_pairs'], m['distance'], m['distance_min'],
                m['distance_max'], m['distance_sd'], *m['foundations'],
                m['idealism'], m['relativism'], m['ideology'], m['category_changed'],
            ])
        if jev is not None:
            writer.writerow([
                '', jev['name'], jev['provider'], '',
                jev['numeric'], jev['scheduled'], jev['missing'], jev['agreement'],
                jev['matched_pairs'], jev['compared_pairs'], jev['distance'], jev['distance_min'],
                jev['distance_max'], jev['distance_sd'], *jev['foundations'],
                jev['idealism'], jev['relativism'], jev['ideology'], jev['category_changed'],
            ])


def score_oct4_recovery(bench: dict, expected_items: set, response_ids: list[str]) -> dict:
    oct4_name = 'Mistral Large 2512'
    oct4_slug = 'mistral-large-2512'
    oct4_models = json.loads((OCT04 / 'models.json').read_text())
    req_model = oct4_models[oct4_name]

    runs = {1: NS['getbase'](oct4_name)}
    for r in range(2, 6):
        path = OCT04 / 'results' / oct4_slug / f'run-{r}.jsonl'
        runs[r] = {}
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get('record_type') == 'result':
                runs[r][(row['instrument'], row['item_id'])] = NS['valid'](row.get('rating'), row['instrument'])

    recovered_rows = [json.loads(line) for line in (ROOT / 'oct4-recovery' / 'recovered.jsonl').read_text().splitlines() if line.strip()]
    assert len(recovered_rows) == 12
    for row in recovered_rows:
        assert row['requested_model'] == req_model and row['returned_model'] == req_model
        assert row['request'].get('provider') == {'only': ['mistral/eu'], 'allow_fallbacks': False}
        assert row['request']['messages'] == [{'role': 'user', 'content': expected_prompt(bench, row['instrument'], row['item_id'])}]
        first, strict = recompute_ratings(row.get('content', ''), row['instrument'])
        assert row.get('rating') == first and row.get('strict_rating') == strict
        assert row.get('response_id')
        response_ids.append(row['response_id'])
        assert runs[row['run']].get((row['instrument'], row['item_id'])) is None
        runs[row['run']][(row['instrument'], row['item_id'])] = NS['valid'](strict, row['instrument'])

    scores = {str(r): NS['score'](runs[r]) for r in range(1, 6)}
    analysis = {
        'scores': scores,
        'new_pairwise': NS['aggregate_agreement']([NS['agreement'](runs[a], runs[b]) for a, b in itertools.combinations(range(2, 6), 2)]),
        'baseline_agreement': NS['aggregate_agreement']([NS['agreement'](runs[1], runs[r]) for r in range(2, 6)]),
    }
    recovered_summary = SUMMARY.summarize(oct4_name, analysis, [runs[r] for r in range(1, 6)])
    recovered_summary.update({
        'note': 'Diagnostic check filling 12 HTTP-429 items from 2026-10-04 via mistral/eu; 19 non-integer baseline Run 1 items remain missing (261/280). Not used in main leaderboard, which uses the complete 280/280 fresh 2026-11-12 cohort.',
        'recovered_records': len(recovered_rows),
        'recovered_cost_usd': sum((x.get('usage') or {}).get('cost', 0) or 0 for x in recovered_rows),
    })
    (ROOT / 'oct4-recovery' / 'summary.json').write_text(json.dumps(recovered_summary, indent=2) + '\n')
    return recovered_summary


def build_manifest() -> dict[str, str]:
    files = sorted(
        p for p in ROOT.rglob('*')
        if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts
        and not any(part.startswith('.') for part in p.relative_to(ROOT).parts)
    )
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main() -> None:
    bench = json.loads((ROOT / 'benchmark.json').read_text())
    assert bench['tests']['MFQ-2'] == NS['BENCH']['tests']['MFQ-2']
    assert bench['tests']['EPQ'] == NS['BENCH']['tests']['EPQ']

    models = json.loads((ROOT / 'models.json').read_text())
    expected = {(test, item['id']) for test in ('MFQ-2', 'EPQ') for item in bench['tests'][test]['items']}
    assert len(expected) == 56

    details = {}
    strict_models = []
    legacy_models = []
    unscored = []
    response_ids: list[str] = []

    for name, identifier in models.items():
        slug = re.sub('[^a-z0-9]+', '-', name.lower()).strip('-')
        runs_legacy = {}
        runs_strict = {}
        rows = []
        for run in range(1, 6):
            records = [json.loads(line) for line in (ROOT / 'results' / slug / f'run-{run}.jsonl').read_text().splitlines() if line.strip()]
            assert len(records) == 56 and {(x['instrument'], x['item_id']) for x in records} == expected
            assert all(x['record_type'] == 'result' and x['run'] == run and x['requested_model'] == identifier for x in records)
            for x in records:
                req = x['request']
                assert req['model'] == identifier
                assert req['temperature'] == 0 and req['max_tokens'] == 4096 and req['reasoning'] == {'exclude': True}
                if name == 'Mistral Large 2512':
                    assert req.get('provider') == {'only': ['mistral/eu'], 'allow_fallbacks': False}
                assert req['messages'] == [{'role': 'user', 'content': expected_prompt(bench, x['instrument'], x['item_id'])}]
                first, strict = recompute_ratings(x.get('content', ''), x['instrument'])
                assert x.get('rating') == first and x.get('strict_rating') == strict
                assert x.get('status') == 'answered' and strict is not None
                assert x.get('returned_model') == identifier
                assert x.get('response_id')
                response_ids.append(x['response_id'])
            rows.extend(records)
            runs_legacy[run] = {(x['instrument'], x['item_id']): NS['valid'](x.get('rating'), x['instrument']) for x in records}
            runs_strict[run] = {(x['instrument'], x['item_id']): NS['valid'](x.get('strict_rating'), x['instrument']) for x in records}

        legacy_scores = {str(r): NS['score'](runs_legacy[r]) for r in range(1, 6)}
        strict_scores = {str(r): NS['score'](runs_strict[r]) for r in range(1, 6)}
        details[name] = {
            'requested_model': identifier,
            'strict_scores': strict_scores,
            'legacy_scores': legacy_scores,
            'statuses': dict(collections.Counter(x['status'] for x in rows)),
            'returned_models': dict(collections.Counter(x.get('returned_model') for x in rows if x.get('returned_model'))),
            'providers': dict(collections.Counter(x.get('provider') for x in rows if x.get('provider'))),
            'recorded_cost_usd': sum((x.get('usage') or {}).get('cost', 0) or 0 for x in rows),
        }

        strict_analysis = {
            'scores': strict_scores,
            'new_pairwise': NS['aggregate_agreement']([NS['agreement'](runs_strict[a], runs_strict[b]) for a, b in itertools.combinations(range(2, 6), 2)]),
            'baseline_agreement': NS['aggregate_agreement']([NS['agreement'](runs_strict[1], runs_strict[r]) for r in range(2, 6)]),
        }
        legacy_analysis = {
            'scores': legacy_scores,
            'new_pairwise': NS['aggregate_agreement']([NS['agreement'](runs_legacy[a], runs_legacy[b]) for a, b in itertools.combinations(range(2, 6), 2)]),
            'baseline_agreement': NS['aggregate_agreement']([NS['agreement'](runs_legacy[1], runs_legacy[r]) for r in range(2, 6)]),
        }

        strict_entry = SUMMARY.summarize(name, strict_analysis, [runs_strict[r] for r in range(1, 6)])
        strict_entry.update({
            'collection_date': '2026-11-12',
            'release_path': 'repeated-runs/2026-11-12',
            'requested_model': identifier,
            'parser': 'strict whole-answer integer',
        })
        strict_models.append(strict_entry)

        legacy_entry = SUMMARY.summarize(name, legacy_analysis, [runs_legacy[r] for r in range(1, 6)])
        legacy_entry.update({
            'collection_date': '2026-11-12',
            'release_path': 'repeated-runs/2026-11-12',
            'requested_model': identifier,
            'parser': 'first-digit diagnostic only',
        })
        legacy_models.append(legacy_entry)

    recovery_summary = score_oct4_recovery(bench, expected, response_ids)
    assert len(response_ids) == len(set(response_ids)) == 572

    for lst in (strict_models, legacy_models):
        lst.sort(key=lambda m: m['distance'])
        for rank, m in enumerate(lst, 1):
            m['rank'] = rank

    out = {
        'version': 'five-fresh-runs-2026-11-12',
        'foundations': SUMMARY.FOUNDATIONS,
        'human_norms': SUMMARY.NORMS,
        'models': strict_models,
        'strict_models': strict_models,
        'legacy_models': legacy_models,
        'details': details,
        'unscored_models': unscored,
        'oct4_recovery_diagnostic': recovery_summary,
        'scheduled': len(models) * 280,
        'record_count': len(models) * 280,
        'primary_parser': 'Strict whole-answer integer; numeric mentions inside prose are missing',
        'recorded_cost_usd': sum(x['recorded_cost_usd'] for x in details.values()) + recovery_summary['recovered_cost_usd'],
        'scoring_sources': {
            str(s.relative_to(ROOT.parent.parent)): hashlib.sha256(s.read_bytes()).hexdigest()
            for s in (SOURCE, OCT04 / 'summarize_five_runs.py')
        },
        'limits': 'Five fresh concurrent trial streams per rerun model. Muse Spark 1.3 ran after OpenRouter age-attestation verification. Mistral Large 2512 ran with provider={only:[mistral/eu], allow_fallbacks:false}. Other cohorts were not retested. Temperature zero was requested; catalog support and backend enforcement differ.',
    }
    (ROOT / 'five-run-summary.json').write_text(json.dumps(out, indent=2) + '\n')
    write_summary_csv(ROOT / 'five-run-summary.csv', strict_models)

    prev_path = OCT29 / 'combined-five-run-summary.json'
    prev_bytes = prev_path.read_bytes()
    prev_sha = hashlib.sha256(prev_bytes).hexdigest()
    combined = json.loads(prev_bytes)
    original_models = {m['name']: copy.deepcopy(m) for m in combined['models']}
    original_jev = copy.deepcopy(combined['jev'])

    superseded = [m for m in combined['models'] if m['name'] in models]
    kept = [m for m in combined['models'] if m['name'] not in models]
    assert len(superseded) == 1 and superseded[0]['name'] == 'Mistral Large 2512' and superseded[0]['collection_date'] == '2026-10-04'

    combined['models'] = kept + copy.deepcopy(strict_models)
    combined['models'].sort(key=lambda m: m['distance'])
    for rank, m in enumerate(combined['models'], 1):
        m['rank'] = rank
        if m['name'] not in models:
            prev_m = {k: v for k, v in original_models[m['name']].items() if k != 'rank'}
            cur_m = {k: v for k, v in m.items() if k != 'rank'}
            assert prev_m == cur_m, f'Historical drift in {m["name"]}'

    assert combined['jev'] == original_jev
    assert len(combined['models']) == 21

    latest_extension = {
        'collection_date': '2026-11-12',
        'models': list(models.keys()),
        'strict_models': strict_models,
        'legacy_models': legacy_models,
        'unscored_models': unscored,
        'superseded_models': superseded,
        'primary_parser': out['primary_parser'],
        'limits': out['limits'],
    }
    combined.update({
        'version': 'combined-five-runs-2026-11-12',
        'primary_parser': 'Historical October 4 first-digit results preserved for 11 baseline models; October 14, October 29, and November 12 cohorts use strict whole-answer integers (November 12 Mistral Large 2512 replaces the incomplete October 4 entry).',
        'llm_numeric': sum(m['numeric'] for m in combined['models']),
        'llm_scheduled': sum(m['scheduled'] for m in combined['models']),
        'latest_extension': latest_extension,
        'collection_dates': [*combined['collection_dates'], '2026-11-12'],
        'extensions': [*combined['extensions'], latest_extension],
    })
    (ROOT / 'combined-five-run-summary.json').write_text(json.dumps(combined, indent=2) + '\n')
    write_summary_csv(ROOT / 'combined-five-run-summary.csv', combined['models'], combined['jev'])

    verification = {
        'verified': True,
        'records': 560,
        'recovery_records': 12,
        'distinct_response_ids': len(response_ids),
        'all_item_sets_settings_prompts_checked': True,
        'full_answer_parser_recomputed': True,
        'models_ranked': len(strict_models),
        'combined_models_ranked': len(combined['models']),
        'unscored_models': len(unscored),
        'superseded_models': [m['name'] for m in superseded],
        'previous_summary_sha256': prev_sha,
        'historical_values_preserved_except_combined_rank': True,
        'jev_preserved': True,
    }
    (ROOT / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    build_manifest()
    print(json.dumps({
        'models': [{k: m[k] for k in ('rank', 'name', 'numeric', 'agreement', 'distance', 'idealism', 'relativism', 'ideology')} for m in strict_models],
        'combined_llm_numeric': combined['llm_numeric'],
        'combined_llm_scheduled': combined['llm_scheduled'],
        'recorded_cost_usd': round(out['recorded_cost_usd'], 4),
    }, indent=2))


if __name__ == '__main__':
    main()
