"""Verify the five-trial dataset offline, including prompt fidelity and retry timing."""
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import repeat


def main(root=None, folders=None):
    root = root or Path(__file__).resolve().parent
    folders = folders or repeat.SCENARIOS
    summary = json.loads((root / 'five-trial-summary.json').read_text())
    assert summary['internal_reasoning_note'] == repeat.NOTE
    since = json.loads((root / 'repeat-model-pricing.json').read_text())['retrieved_at']
    mistral_attempts = []
    generation_ids = set()
    reported = jev_estimated = accounted = 0
    total = 0
    for folder in folders:
        records = {str(p.relative_to(folder)): json.loads(p.read_text()) for p in (folder / 'results').rglob('*.json')}
        assert len(records) == 105, (folder.name, len(records))
        identities = {(r['model_label'], r.get('trial', 1)) for r in records.values()}
        assert len(identities) == 105 and len({name for name, _ in identities}) == 21
        assert all({trial for n, trial in identities if n == name} == {1, 2, 3, 4, 5} for name, _ in identities)
        baselines = {r['model_label']: r for r in records.values() if r.get('trial', 1) == 1}
        prompt = (folder / 'prompt.txt').read_text().rstrip('\n')
        for record in records.values():
            baseline_request = baselines[record['model_label']]['request']
            assert {k: v for k, v in record['request'].items() if k != 'provider'} == {k: v for k, v in baseline_request.items() if k != 'provider'}
            if 'provider' in record['request']:
                assert record['model_label'] == 'Mistral Large 2512' and record['request']['provider'] == repeat.MISTRAL_ROUTING
            assert record['requested_model'] == record['request']['model']
            assert record == repeat.original.clean(record)
            if record.get('trial', 1) != 1:
                assert record['internal_reasoning_note'] == repeat.NOTE
            if record['model_label'] == 'Jev':
                assert record['request']['state'] == prompt
                content = record['response'].get('answers', {}).get('action', {}).get('choice')
            else:
                assert record['request']['messages'] == [{'role': 'user', 'content': prompt}]
                choices = record['response'].get('choices') or []
                content = choices[0].get('message', {}).get('content') if choices else None
                if record['http_status'] == 200:
                    generation_id = record['response']['id']
                    assert generation_id and generation_id not in generation_ids
                    generation_ids.add(generation_id)
            assert record['answer'] == repeat.original.answer(content)
            expected = 'answered' if record['http_status'] == 200 and record['answer'] else 'nonconforming' if record['http_status'] == 200 else 'api_failure'
            assert record['status'] == expected
            for attempt in repeat.attempts(record):
                accounted += repeat.charge(attempt)
                assert {k: v for k, v in attempt['request'].items() if k != 'provider'} == {k: v for k, v in record['request'].items() if k != 'provider'}
                if 'provider' in attempt['request']:
                    assert record['model_label'] == 'Mistral Large 2512' and attempt['request']['provider'] == repeat.MISTRAL_ROUTING
                usage = attempt.get('response', {}).get('usage', {})
                if record['model_label'] == 'Jev' and 'input_tokens' in usage:
                    jev_estimated += usage['input_tokens'] * 0.042 / 1_000_000
                elif isinstance(usage.get('cost'), (int, float)):
                    reported += usage['cost']
                if record['model_label'] == 'Mistral Large 2512' and attempt['started_at'] >= since:
                    mistral_attempts.append(attempt)
        with (folder / 'five-trial-results.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 105
        for row in rows:
            record = records[row['result_file']]
            assert int(row['trial']) == record.get('trial', 1) and row['answer'] == (record['answer'] or '') and row['status'] == record['status']
        saved = summary['scenarios'][folder.name]
        for key, value in saved['counts'].items():
            assert value == sum(r['answer'] == (None if key == 'null' else key) for r in records.values())
        for trial in range(1, 6):
            actual = collections.Counter(r['status'] for r in records.values() if r.get('trial', 1) == trial)
            assert all(actual[status] == count for status, count in saved['trials'][str(trial)].items())
        total += len(records)
    ordered = sorted(mistral_attempts, key=lambda r: r['started_at'])
    for before, after in zip(ordered, ordered[1:]):
        gap = (dt.datetime.fromisoformat(after['started_at']) - dt.datetime.fromisoformat(before['finished_at'])).total_seconds()
        same_trial = (before.get('scenario'), before.get('trial')) == (after.get('scenario'), after.get('trial'))
        minimum = 89 if before['http_status'] == 429 and same_trial else 64
        assert gap >= minimum, ('Mistral cooldown too short', gap, minimum)
    assert abs(reported - summary['openrouter_reported_cost_usd']) < 1e-9
    assert abs(jev_estimated - summary['jev_estimated_cost_usd']) < 1e-9
    assert abs(accounted - summary['conservative_accounted_usd']) < 1e-9 and accounted < 5
    assert reported + jev_estimated < 5
    print(f'Verified {total} records: five trials per system/scenario, {len(generation_ids)} unique LLM generation IDs, unchanged prompts/generation parameters, parsing, summaries, CSVs, redaction, Mistral cooldowns and costs')


if __name__ == '__main__':
    main()
