"""One administration per model; no answer retries, no third-party dependencies."""
import csv
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SECRETS = []


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def key(text, name):
    text = text.strip()
    match = re.search(r'(?m)^\s*(?:export\s+)?' + name + r'\s*=\s*(.+?)\s*$', text)
    value = (match.group(1) if match else text).strip().strip('\"\'')
    assert value and not any(c.isspace() for c in value), 'Invalid credential format'
    SECRETS.append(value)
    return value


def save(path, value):
    encoded = json.dumps(clean(value), indent=2, ensure_ascii=False)
    for secret in SECRETS:
        assert secret not in encoded, 'Refusing to persist credential material'
    path.write_text(encoded + '\n')


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in {'signature', 'user_id', 'organization_id', 'execution_host'} and not (value.get('type') == 'reasoning.encrypted' and k == 'data')}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def call(url, payload=None, token=None):
    assert url.startswith(('https://openrouter.ai/api/v1/', 'https://api.typesafe.ai/v1/'))
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    started = time.monotonic()
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=120) as response:
            code, raw = response.status, response.read().decode()
    except urllib.error.HTTPError as response:
        code, raw = response.code, response.read().decode(errors='replace')
    except (OSError, TimeoutError) as error:
        return {'http_status': None, 'transport_error': type(error).__name__, 'elapsed_seconds': round(time.monotonic()-started, 3)}
    try:
        body = json.loads(raw)
    except ValueError:
        body = {'unparsed_body': raw}
    return {'http_status': code, 'response': body, 'elapsed_seconds': round(time.monotonic()-started, 3)}


def answer(content):
    return content.strip() if isinstance(content, str) and content.strip() in {'[A]', '[B]'} else None


def main():
    prompt = (ROOT / 'prompt.txt').read_text().rstrip('\n')
    models = {}
    for date in ['2026-10-04', '2026-10-14', '2026-10-29']:
        models.update(json.loads((REPO / 'repeated-runs' / date / 'models.json').read_text()))
    models.pop('Muse Spark 1.3')  # Not in the live site's 20-configuration leaderboard.
    assert len(models) == 20
    token = key(os.environ['OPENROUTER_API_KEY'], 'OPENROUTER_API_KEY')
    jev_token = key(os.environ['TYPESAFE_API_KEY'], 'TYPESAFE_API_KEY')
    catalog = call('https://openrouter.ai/api/v1/models')
    assert catalog['http_status'] == 200
    lookup = {m['id']: m for m in catalog['response']['data']}
    selected = {name: lookup[mid] for name, mid in models.items()}
    save(ROOT / 'models.json', {'retrieved_at': now(), 'source': 'https://moralitybench.ai/', 'models': selected})
    (ROOT / 'results').mkdir(exist_ok=True)
    reserved = sum((r := json.loads(p.read_text())).get('maximum_estimated_usd', 0) * (1 + len(r.get('prior_attempts', []))) for p in (REPO / 'scenarios').glob('*/results/*.json'))
    for name, mid in models.items():
        path = ROOT / 'results' / (mid.replace('/', '--') + '.json')
        if path.exists():
            continue
        metadata = selected[name]
        reasoning = {'enabled': False, 'exclude': True}
        if metadata.get('reasoning', {}).get('mandatory'):
            efforts = metadata['reasoning'].get('supported_efforts', [])
            effort = next((x for x in ['none', 'minimal', 'low', 'medium', 'high'] if x in efforts), None)
            reasoning = {'exclude': True, **({'effort': effort} if effort else {})}
        payload = {'model': mid, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 4096, 'reasoning': reasoning}
        # Byte length plus framing is a conservative input-token allowance at this prompt size.
        pricing = metadata['pricing']
        ceiling = (len(json.dumps(payload).encode()) + 4096) * float(pricing['prompt']) + 4096 * max(float(pricing['completion']), float(pricing.get('internal_reasoning', '0')))
        assert reserved + ceiling < 4.50, 'Stop before exceeding OpenRouter allocation; $0.50 reserved for Jev'
        record = {'model_label': name, 'requested_model': mid, 'started_at': now(), 'request': payload, 'maximum_estimated_usd': ceiling, **call('https://openrouter.ai/api/v1/chat/completions', payload, token)}
        body = record.get('response', {})
        choices = body.get('choices') or []
        content = choices[0].get('message', {}).get('content') if choices else None
        record.update(finished_at=now(), content=content, answer=answer(content), status='answered' if record['http_status'] == 200 and answer(content) else 'nonconforming' if record['http_status'] == 200 else 'api_failure')
        save(path, record)
        reserved += ceiling
        print(name, record['status'], record['answer'], flush=True)
        if record['http_status'] in {401, 402}:
            raise RuntimeError('Authentication or credit failure; stopped')
    path = ROOT / 'results' / 'jev-typesafe.json'
    if not path.exists():
        criteria = dict(re.findall(r'(?m)^(\[[AB]\]) (.+)$', prompt))
        assert set(criteria) == {'[A]', '[B]'}
        payload = {'model': 'jev-latest', 'state': prompt, 'questions': {'action': {'type': 'choice', 'instructions': 'Which action do you take? Answer with only [A] or [B].', 'criteria': criteria}}}
        record = {'model_label': 'Jev', 'requested_model': 'jev-latest', 'started_at': now(), 'request': payload, **call('https://api.typesafe.ai/v1/systemone', payload, jev_token)}
        choice = record.get('response', {}).get('answers', {}).get('action', {}).get('choice')
        record.update(finished_at=now(), answer=answer(choice), status='answered' if record['http_status'] == 200 and answer(choice) else 'api_failure')
        save(path, record)
        print('Jev', record['status'], record['answer'], flush=True)
    summarize()


def summarize():
    rows = []
    records = []
    for path in sorted((ROOT / 'results').glob('*.json')):
        r = json.loads(path.read_text()); b = r.get('response', {})
        records.append(r)
        rows.append({'model': r['model_label'], 'requested_model': r['requested_model'], 'returned_model': b.get('model'), 'provider': b.get('provider'), 'answer': r['answer'], 'status': r['status'], 'http_status': r['http_status'], 'reported_cost_usd': b.get('usage', {}).get('cost'), 'result_file': str(path.relative_to(ROOT))})
    with (ROOT / 'results.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    maximum = sum(r.get('maximum_estimated_usd', 0) * (1 + len(r.get('prior_attempts', []))) for r in records)
    jev_usage = next(r['response']['usage']['input_tokens'] for r in records if r['model_label'] == 'Jev')
    save(ROOT / 'summary.json', {'completed_at': max(r['finished_at'] for r in records), 'systems': len(rows), 'counts': {a: sum(r['answer'] == a for r in rows) for a in ['[A]', '[B]', None]}, 'openrouter_reported_cost_usd': sum(r['reported_cost_usd'] or 0 for r in rows), 'openrouter_maximum_estimated_usd': maximum, 'jev_input_price_usd_per_million': 0.042, 'jev_estimated_cost_usd': jev_usage * 0.042 / 1_000_000, 'results': rows})


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        assert answer('[A]') == '[A]' and answer(' [B]\n') == '[B]'
        assert all(answer(x) is None for x in ['A', '[A] because...', 'Neither', '', None])
        assert key('OPENROUTER_API_KEY="test-value"', 'OPENROUTER_API_KEY') == 'test-value'
        assert clean({'type': 'reasoning.encrypted', 'data': 'opaque'}) == {'type': 'reasoning.encrypted'}
        assert clean({'content': '[A]', 'signature': 'opaque'}) == {'content': '[A]'}
        assert dict(re.findall(r'(?m)^(\[[AB]\]) (.+)$', '[A] Divert\n[B] Refrain')) == {'[A]': 'Divert', '[B]': 'Refrain'}
        print('Parser and credential-format self-checks passed; no network requests')
    else:
        if len(sys.argv) > 1:
            ROOT = Path(sys.argv[1]).resolve()
            assert ROOT.parent == REPO / 'scenarios', 'Keep scenario results in this repository'
        if '--summarize' in sys.argv:
            summarize()
        else:
            main()
