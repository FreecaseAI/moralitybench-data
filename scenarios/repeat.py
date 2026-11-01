"""Add trials 2-5 using the original payloads; retry only requests without answers."""
import concurrent.futures
import csv
import datetime as dt
import email.utils
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
SCENARIOS = [ROOT / '2026-11-01-chlorine-diversion', ROOT / '2026-11-01-pipeline-confidentiality']
NOTE = 'Zero internal reasoning cannot be guaranteed.'
MISTRAL_ROUTING = {'only': ['mistral/eu'], 'allow_fallbacks': False}
spec = importlib.util.spec_from_file_location('original', SCENARIOS[0] / 'run.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)


def persist(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    original.save(temporary, record)
    temporary.replace(path)


def attempts(record):
    return record.get('prior_attempts', []) + [{k: v for k, v in record.items() if k != 'prior_attempts'}]


def charge(record):
    usage = record.get('response', {}).get('usage', {})
    if record.get('model_label') == 'Jev' and 'input_tokens' in usage:
        return usage['input_tokens'] * 0.042 / 1_000_000
    cost = usage.get('cost')
    return float(cost) if isinstance(cost, (int, float)) and cost >= 0 else record.get('maximum_estimated_usd', 0)


class Budget:
    def __init__(self, spent):
        self.spent, self.pending, self.lock = spent, 0.0, threading.Lock()

    def reserve(self, maximum):
        with self.lock:
            assert self.spent + self.pending + maximum < 4.50, 'Stop before the shared $5 authorization is exhausted'
            self.pending += maximum

    def settle(self, maximum, record):
        with self.lock:
            self.pending -= maximum
            self.spent += charge(record)


def retry_delay(record, retry_number):
    delay = 90 * 2 ** retry_number
    header = record.get('retry_after')
    if header:
        try:
            delay = max(delay, float(header))
        except ValueError:
            try:
                delay = max(delay, (email.utils.parsedate_to_datetime(header) - dt.datetime.now(dt.timezone.utc)).total_seconds())
            except (TypeError, ValueError):
                pass
    return delay


def wait(seconds, label):
    if seconds > 0:
        print(f'{label}: waiting {seconds:.0f}s before another request', flush=True)
        until = time.monotonic() + seconds
        while (remaining := until - time.monotonic()) > 0:
            time.sleep(min(remaining, 30))


def maximum_cost(payload, metadata):
    if payload['model'] == 'jev-latest':
        return (len(json.dumps(payload).encode()) + 4096) * 0.042 / 1_000_000
    prices = [metadata['pricing'], *metadata['pricing'].get('overrides', [])]
    prompt = max(float(p.get('prompt', 0)) for p in prices)
    output = max(max(float(p.get('completion', 0)), float(p.get('internal_reasoning', 0))) for p in prices)
    return (len(json.dumps(payload).encode()) + 4096) * prompt + 4096 * output


def collect(name, metadata, keys, budget, scenario_pairs=None):
    pairs = scenario_pairs or [(folder, folder) for folder in SCENARIOS]
    is_mistral = name == 'Mistral Large 2512'
    last_finish = None
    previous_status = None
    if is_mistral:
        previous = [json.loads(p.read_text()) for folder in {f for pair in pairs for f in pair} for p in (folder / 'results').rglob('mistralai--mistral-large-2512.json')]
        latest = max(previous, key=lambda r: r['finished_at'])
        elapsed = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(latest['finished_at'])).total_seconds()
        last_finish = time.monotonic() - elapsed
        previous_status = latest['http_status']
    for source, folder in pairs:
        baseline_path = next(p for p in (source / 'results').glob('*.json') if json.loads(p.read_text())['model_label'] == name)
        baseline = json.loads(baseline_path.read_text())
        # Backfill the missing first-trial Mistral answer without discarding its error history.
        trials = range(1, 6) if source != folder else ([1] if is_mistral and baseline['http_status'] == 429 else []) + list(range(2, 6))
        for trial in trials:
            path = folder / 'results' / baseline_path.name if trial == 1 else folder / 'results' / f'trial-{trial}' / baseline_path.name
            prior = json.loads(path.read_text()) if path.exists() else None
            if prior and prior['http_status'] == 200:
                continue
            payload = {**baseline['request'], **({'provider': MISTRAL_ROUTING} if is_mistral else {})}
            if source != folder:
                prompt = (folder / 'prompt.txt').read_text().rstrip('\n')
                if name == 'Jev':
                    payload['state'] = prompt
                else:
                    payload['messages'] = [{'role': 'user', 'content': prompt}]
            maximum = maximum_cost(payload, metadata)
            history = attempts(prior) if prior else []
            for retry in range(3):
                delay = 0
                if is_mistral and last_finish is not None:
                    delay = max(0, (90 if previous_status == 429 else 65) - (time.monotonic() - last_finish))
                if retry:
                    delay = max(delay, retry_delay(record, retry - 1))
                wait(delay, f'{name} {folder.name} trial {trial}')
                budget.reserve(maximum)
                endpoint = 'https://api.typesafe.ai/v1/systemone' if name == 'Jev' else 'https://openrouter.ai/api/v1/chat/completions'
                record = {'model_label': name, 'requested_model': payload['model'], 'scenario': folder.name, 'trial': trial, 'started_at': original.now(), 'request': payload, 'maximum_estimated_usd': maximum, 'internal_reasoning_note': NOTE, **original.call(endpoint, payload, keys['Jev' if name == 'Jev' else 'OpenRouter'])}
                last_finish = time.monotonic()
                previous_status = record['http_status']
                if is_mistral:
                    record['routing_note'] = 'Explicit Mistral EU endpoint, retained after repeated upstream HTTP 429s despite 90/180-second waits in the original study. Exact request payload preserved.'
                body = record.get('response', {})
                choices = body.get('choices') or []
                content = body.get('answers', {}).get('action', {}).get('choice') if name == 'Jev' else choices[0].get('message', {}).get('content') if choices else None
                record.update(finished_at=original.now(), content=content, answer=original.answer(content), status='answered' if record['http_status'] == 200 and original.answer(content) else 'nonconforming' if record['http_status'] == 200 else 'api_failure')
                budget.settle(maximum, record)
                if history:
                    record['prior_attempts'] = history.copy()
                persist(path, record)
                print(f'{name} {folder.name} trial {trial}: HTTP {record["http_status"]}, {record["status"]}, {record["answer"]}', flush=True)
                if record['http_status'] in {401, 402}:
                    raise RuntimeError('Authentication or credit failure')
                if record['http_status'] not in {429, 502, 503, 504}:
                    break
                history.append({k: v for k, v in record.items() if k != 'prior_attempts'})


def summarize(folders=None, root=None):
    folders, root = folders or SCENARIOS, root or ROOT
    combined = {'internal_reasoning_note': NOTE, 'authorized_budget_usd': 5, 'scenarios': {}, 'openrouter_reported_cost_usd': 0.0, 'jev_estimated_cost_usd': 0.0, 'unpriced_attempts': 0, 'conservative_accounted_usd': 0.0}
    for folder in folders:
        records = [(p, json.loads(p.read_text())) for p in sorted((folder / 'results').rglob('*.json'))]
        rows = []
        for path, record in records:
            body = record.get('response', {})
            rows.append({'model': record['model_label'], 'trial': record.get('trial', 1), 'answer': record['answer'], 'status': record['status'], 'http_status': record['http_status'], 'requested_model': record['requested_model'], 'returned_model': body.get('model'), 'provider': body.get('provider'), 'attempts': len(attempts(record)), 'result_file': str(path.relative_to(folder))})
            for attempt in attempts(record):
                combined['conservative_accounted_usd'] += charge(attempt)
                usage = attempt.get('response', {}).get('usage', {})
                if record['model_label'] == 'Jev' and 'input_tokens' in usage:
                    combined['jev_estimated_cost_usd'] += usage['input_tokens'] * 0.042 / 1_000_000
                elif isinstance(usage.get('cost'), (int, float)):
                    combined['openrouter_reported_cost_usd'] += usage['cost']
                else:
                    combined['unpriced_attempts'] += 1
        with (folder / 'five-trial-results.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
        trials = {str(trial): {status: sum(r['trial'] == trial and r['status'] == status for r in rows) for status in ['answered', 'nonconforming', 'api_failure']} for trial in range(1, 6)}
        counts = {a: sum(r['answer'] == a for r in rows) for a in ['[A]', '[B]', None]}
        combined['scenarios'][folder.name] = {'records': len(rows), 'counts': counts, 'trials': trials, 'results': rows}
        original.ROOT = folder
        original.summarize()
    combined['combined_reported_estimated_cost_usd'] = combined['openrouter_reported_cost_usd'] + combined['jev_estimated_cost_usd']
    persist(root / 'five-trial-summary.json', combined)
    print('Total records:', sum(v['records'] for v in combined['scenarios'].values()), 'Reported/estimated total USD:', combined['combined_reported_estimated_cost_usd'])
    return combined


def model_metadata():
    catalog = original.call('https://openrouter.ai/api/v1/models')
    assert catalog['http_status'] == 200
    lookup = {m['id']: m for m in catalog['response']['data']}
    baselines = [json.loads(p.read_text()) for p in (SCENARIOS[0] / 'results').glob('*.json')]
    names = {r['model_label']: lookup[r['requested_model']] if r['model_label'] != 'Jev' else {} for r in baselines}
    endpoints = original.call('https://openrouter.ai/api/v1/models/mistralai/mistral-large-2512/endpoints')
    assert endpoints['http_status'] == 200
    eu = next(e for e in endpoints['response']['data']['endpoints'] if e['tag'] == 'mistral/eu')
    names['Mistral Large 2512']['pricing'] = eu['pricing']
    return names, eu


def main():
    keys = {'OpenRouter': original.key(os.environ['OPENROUTER_API_KEY'], 'OPENROUTER_API_KEY'), 'Jev': original.key(os.environ['TYPESAFE_API_KEY'], 'TYPESAFE_API_KEY')}
    names, eu = model_metadata()
    pricing_path = ROOT / 'repeat-model-pricing.json'
    pricing = json.loads(pricing_path.read_text()) if pricing_path.exists() else {'retrieved_at': original.now(), 'models': {name: {'id': m.get('id', 'jev-latest'), 'pricing': m.get('pricing', {'prompt': '0.000000042', 'completion': '0'})} for name, m in names.items()}, 'internal_reasoning_note': NOTE}
    pricing.setdefault('mistral_routing_change_at', original.now())
    pricing.update(mistral_routing=MISTRAL_ROUTING, mistral_endpoint_pricing=eu['pricing'])
    persist(pricing_path, pricing)
    existing = [json.loads(p.read_text()) for folder in SCENARIOS for p in (folder / 'results').rglob('*.json')]
    budget = Budget(sum(charge(a) for r in existing for a in attempts(r)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(collect, name, names[name], keys, budget) for name in sorted(names, key=lambda name: name != 'Mistral Large 2512')]
        for job in concurrent.futures.as_completed(jobs):
            job.result()
    summarize()


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        assert retry_delay({'retry_after': '120'}, 0) == 120
        assert retry_delay({}, 1) == 180
        assert original.answer('**[A]**') is None
        b = Budget(0.1); b.reserve(0.2); b.settle(0.2, {'response': {'usage': {'cost': 0.01}}})
        assert abs(b.spent - 0.11) < 1e-9 and abs(b.pending) < 1e-9
        try:
            b.reserve(5)
        except AssertionError:
            pass
        else:
            raise AssertionError('Budget cap not enforced')
        assert len(attempts({'prior_attempts': [{'http_status': 429}], 'http_status': 200})) == 2
        print('Retry, budget, parsing and attempt-history self-checks passed; no network requests')
    elif '--summarize' in sys.argv:
        summarize()
    else:
        main()
