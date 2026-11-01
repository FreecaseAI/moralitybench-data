"""Five fresh trials per scenario with exactly the words 'reasoning or' removed."""
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import repeat
import verify

ROOT = Path(__file__).resolve().parent / '2026-11-01-without-reasoning-or'
PAIRS = list(zip(repeat.SCENARIOS, [ROOT / 'chlorine-diversion', ROOT / 'pipeline-confidentiality']))


def revised(text):
    assert text.count('reasoning or ') == 1, 'Expected exactly one occurrence'
    return text.replace('reasoning or ', '', 1)


def prepare():
    for source, target in PAIRS:
        expected = revised((source / 'prompt.txt').read_text())
        target.mkdir(parents=True, exist_ok=True)
        path = target / 'prompt.txt'
        if path.exists():
            assert path.read_text() == expected
        else:
            path.write_text(expected)


def summarize():
    result = repeat.summarize([target for _, target in PAIRS], ROOT)
    prior = json.loads((repeat.ROOT / 'five-trial-summary.json').read_text())
    result.update(prompt_change='Remove only the two words reasoning or and their following separator space; all other text preserved.', api_generation_settings='Identical to the original study; explicit Mistral EU routing retained.', prior_study_reported_estimated_cost_usd=prior['combined_reported_estimated_cost_usd'], cumulative_conservative_accounted_usd=prior['conservative_accounted_usd'] + result['conservative_accounted_usd'])
    repeat.persist(ROOT / 'five-trial-summary.json', result)


def verify_all():
    verify.main(ROOT, [target for _, target in PAIRS])
    old_ids = {r.get('response', {}).get('id') for source, _ in PAIRS for p in (source / 'results').rglob('*.json') for r in [json.loads(p.read_text())]}
    for source, target in PAIRS:
        assert (target / 'prompt.txt').read_text() == revised((source / 'prompt.txt').read_text())
        baselines = {r['model_label']: r for p in (source / 'results').glob('*.json') for r in [json.loads(p.read_text())]}
        for path in (target / 'results').rglob('*.json'):
            record = json.loads(path.read_text())
            expected = dict(baselines[record['model_label']]['request'])
            if record['model_label'] == 'Jev':
                expected['state'] = revised(expected['state'])
            else:
                expected['messages'] = [{'role': 'user', 'content': revised(expected['messages'][0]['content'])}]
                if record['http_status'] == 200:
                    assert record['response']['id'] not in old_ids, 'Reused original generation'
            if record['model_label'] == 'Mistral Large 2512':
                expected['provider'] = repeat.MISTRAL_ROUTING
            assert record['request'] == expected, str(path)
            if record['http_status'] == 200:
                returned_model = baselines['Jev']['response']['model'] if record['model_label'] == 'Jev' else expected['model']
                assert record['response']['model'] == returned_model, str(path)
            assert record['internal_reasoning_note'] == repeat.NOTE
    summary = json.loads((ROOT / 'five-trial-summary.json').read_text())
    assert summary['cumulative_conservative_accounted_usd'] < 5
    print('Verified exact two-word deletion, unchanged other request fields, fresh generation IDs and cumulative shared budget')


def main():
    prepare()
    keys = {'OpenRouter': repeat.original.key(os.environ['OPENROUTER_API_KEY'], 'OPENROUTER_API_KEY'), 'Jev': repeat.original.key(os.environ['TYPESAFE_API_KEY'], 'TYPESAFE_API_KEY')}
    names, eu = repeat.model_metadata()
    pricing = ROOT / 'repeat-model-pricing.json'
    if not pricing.exists():
        repeat.persist(pricing, {'retrieved_at': repeat.original.now(), 'models': {name: {'id': metadata.get('id', 'jev-latest'), 'pricing': metadata.get('pricing', {'prompt': '0.000000042', 'completion': '0'})} for name, metadata in names.items()}, 'mistral_routing': repeat.MISTRAL_ROUTING, 'mistral_endpoint_pricing': eu['pricing'], 'internal_reasoning_note': repeat.NOTE})
    folders = {folder for pair in PAIRS for folder in pair}
    existing = [json.loads(p.read_text()) for folder in folders for p in (folder / 'results').rglob('*.json')]
    budget = repeat.Budget(sum(repeat.charge(a) for record in existing for a in repeat.attempts(record)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(repeat.collect, name, names[name], keys, budget, PAIRS) for name in sorted(names, key=lambda name: name != 'Mistral Large 2512')]
        for job in concurrent.futures.as_completed(jobs):
            job.result()
    summarize()
    verify_all()


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        assert revised('without reasoning or reference\n') == 'without reference\n'
        assert revised('without reasoning or reference\n\nRest. ') == 'without reference\n\nRest. '
        try:
            revised('missing phrase')
        except AssertionError:
            pass
        else:
            raise AssertionError('Ambiguous prompt edit accepted')
        print('Exact prompt-edit self-checks passed; no network requests')
    elif '--verify' in sys.argv:
        verify_all()
    elif '--summarize' in sys.argv:
        summarize()
    else:
        main()
