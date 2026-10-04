#!/usr/bin/env python3
"""Build the public five-run summary after analyze_repeats.py and analyze_jev.py.

Standard library only. No network access or credentials are needed for analysis.
"""
import collections
import csv
import itertools
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parent
FOUNDATIONS = ['Care', 'Equality', 'Proportionality', 'Loyalty', 'Authority', 'Purity']
NORMS = [4.05, 2.88, 3.63, 2.81, 3.01, 2.26]
PRESENTATION = {
    'DeepSeek V4.1 Flash': ('DeepSeek', '#0d9488'),
    'Nemotron 3 Ultra 550B': ('NVIDIA', '#b45309'),
    'MiMo v2.6 Pro': ('Xiaomi', '#7c3aed'),
    'Gemini 3.8 Flash': ('Google', '#2563eb'),
    'Qwen3.8 27B': ('Alibaba Cloud', '#be123c'),
    'GPT-6.1 Sol': ('OpenAI', '#a16207'),
    'GLM 5.3': ('Zhipu AI', '#15803d'),
    'Claude Opus 5.5': ('Anthropic', '#c026d3'),
    'Kimi K3': ('Moonshot AI', '#0284c7'),
    'Llama 4 Maverick': ('Meta', '#ea580c'),
    'Grok 4.7': ('xAI', '#4f46e5'),
    'MiniMax M3': ('MiniMax', '#475569'),
    'Mistral Large 2512': ('Mistral AI', '#854d0e'),
    'Jev (TypeSafe)': ('TypeSafe', '#0f766e'),
}


def category(idealism, relativism):
    if idealism >= 5:
        return 'Situationist' if relativism >= 5 else 'Absolutist'
    return 'Subjectivist' if relativism >= 5 else 'Exceptionist'


def summarize(name, analysis, values):
    scores = [analysis['scores'][str(r)] for r in range(1, 6)]
    assert len(values) == 5 and all(len(run) == 56 for run in values)
    matched = compared = 0
    for a, b in itertools.combinations(values, 2):
        for key in a.keys() & b.keys():
            if a[key] is not None and b[key] is not None:
                compared += 1
                matched += a[key] == b[key]
    # Independent raw-value computation must match the archived 6 + 4 pairs.
    assert matched == analysis['new_pairwise']['matched'] + analysis['baseline_agreement']['matched']
    assert compared == analysis['new_pairwise']['compared'] + analysis['baseline_agreement']['compared']
    common = set.intersection(*[{k for k, v in run.items() if v is not None} for run in values])
    identical = sum(len({run[k] for run in values}) == 1 for k in common)
    idealism = statistics.mean(s['idealism'] for s in scores)
    relativism = statistics.mean(s['relativism'] for s in scores)
    distance = [s['distance'] for s in scores]
    numeric = sum(s['numeric'] for s in scores)
    provider, color = PRESENTATION[name]
    return {
        'name': name, 'provider': provider, 'color': color,
        'agreement': 100 * matched / compared, 'matched_pairs': matched,
        'compared_pairs': compared, 'possible_pairs': 560,
        'all_five_observed_items': len(common), 'all_five_identical_items': identical,
        'all_five_identical_percent': 100 * identical / len(common) if common else None,
        'numeric': numeric, 'scheduled': 280, 'missing': 280 - numeric,
        'distance': statistics.mean(distance),
        'distance_min': min(distance), 'distance_max': max(distance),
        'distance_sd': statistics.stdev(distance),
        'foundations': [statistics.mean(s['foundations'][f] for s in scores) for f in FOUNDATIONS],
        'idealism': idealism, 'relativism': relativism,
        'ideology': category(idealism, relativism),
        'categories_by_run': [s['category'] for s in scores],
        'category_counts': dict(collections.Counter(s['category'] for s in scores)),
        'category_changed': len({s['category'] for s in scores}) > 1,
        'runs': [{'run': r, **analysis['scores'][str(r)]} for r in range(1, 6)],
    }


def valid(value, instrument):
    limit = 5 if instrument == 'MFQ-2' else 9
    return value if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= limit else None


def main():
    analysis = json.loads((ROOT / 'consistency-analysis.json').read_text())
    baseline = {}
    for path in sorted((ROOT / 'baseline').glob('raw_results_batch*.json')):
        baseline.update(json.loads(path.read_text()))
    models = []
    for name, result in analysis['models'].items():
        if result['completed_runs'] != 4:
            continue
        values = [{(t, x['id']): valid(x['rating'], t) for t, rows in baseline[name].items() for x in rows}]
        slug = re.sub('[^a-z0-9]+', '-', name.lower()).strip('-')
        for run in range(2, 6):
            rows = [json.loads(line) for line in (ROOT / 'results' / slug / f'run-{run}.jsonl').read_text().splitlines()]
            values.append({(x['instrument'], x['item_id']): valid(x.get('rating'), x['instrument']) for x in rows if x.get('record_type') == 'result'})
        models.append(summarize(name, result, values))
    models.sort(key=lambda model: model['distance'])
    for rank, model in enumerate(models, 1):
        model['rank'] = rank
    assert len(models) == 13

    jev_analysis = json.loads((ROOT / 'jev-consistency.json').read_text())
    jev_baseline = json.loads((ROOT / 'baseline' / 'raw_results_jev.json').read_text())
    jev_values = [{(t, x['id']): x['rating'] for t, rows in jev_baseline.items() for x in rows}]
    for run in range(2, 6):
        values = {}
        for test in ['MFQ-2', 'EPQ']:
            data = json.loads((ROOT / 'results' / 'jev-typesafe' / f'run-{run}-{test}.json').read_text())
            values.update({(test, x['id']): x['rating'] for x in data['items']})
        jev_values.append(values)
    jev = summarize('Jev (TypeSafe)', jev_analysis, jev_values)
    out = {
        'version': 'five-runs-2026-10-04', 'original_run': 1, 'new_runs': [2, 3, 4, 5],
        'agreement_definition': 'Exact rating matches divided by available item comparisons across all ten pairs of five runs; missing ratings excluded, never counted as matches.',
        'distance_definition': 'Arithmetic mean of the five per-run mean absolute distances across the six foundation scores; not distance from the averaged profile.',
        'score_definition': 'Foundation and EPQ values are arithmetic means of five per-run scores. Available items form each per-run score. Each run has equal weight.',
        'classification_definition': 'Midpoint classification of mean EPQ scores; >= 5 is high. Categories for individual runs are retained.',
        'primary_parser': 'Original first digit, restricted to instrument range. Jev uses Python round(score) + 1, clipped to instrument range.',
        'foundations': FOUNDATIONS, 'human_norms': NORMS,
        'models': models, 'jev': jev,
        'llm_numeric': sum(m['numeric'] for m in models),
        'llm_scheduled': sum(m['scheduled'] for m in models),
    }
    (ROOT / 'five-run-summary.json').write_text(json.dumps(out, indent=2) + '\n')
    fields = ['rank', 'name', 'agreement', 'matched_pairs', 'compared_pairs', 'possible_pairs', 'all_five_observed_items', 'all_five_identical_items', 'all_five_identical_percent', 'numeric', 'scheduled', 'missing', 'distance', 'distance_sd', 'distance_min', 'distance_max', *FOUNDATIONS, 'idealism', 'relativism', 'ideology', 'category_changed']
    with (ROOT / 'five-run-summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for model in [*models, jev]:
            row = {k: model.get(k, '') for k in fields}
            row.update(zip(FOUNDATIONS, model['foundations']))
            writer.writerow(row)
    print(json.dumps({'llm_numeric': out['llm_numeric'], 'llm_scheduled': out['llm_scheduled'], 'agreement_range': [min(m['agreement'] for m in models), max(m['agreement'] for m in models)], 'jev_agreement': jev['agreement']}, indent=2))


if __name__ == '__main__':
    main()
