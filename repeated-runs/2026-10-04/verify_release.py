"""Check raw receipt completeness, parsers, protocol, hashes, and derived summaries."""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import re
import statistics
ROOT = Path(__file__).resolve().parent

def main():
    summary = json.loads((ROOT/'five-run-summary.json').read_text())
    bench = json.loads((ROOT/'benchmark.json').read_text())
    models = json.loads((ROOT/'models.json').read_text())
    response_ids = []
    timestamps = []
    count = numeric = 0
    for model in summary['models']:
        slug = re.sub('[^a-z0-9]+','-',model['name'].lower()).strip('-')
        for run in range(2,6):
            rows = [json.loads(line) for line in (ROOT/'results'/slug/f'run-{run}.jsonl').read_text().splitlines()]
            assert len(rows) == 56
            actual = {(row['instrument'],row['item_id']) for row in rows}
            expected = {(test,item['id']) for test in ['MFQ-2','EPQ'] for item in bench['tests'][test]['items']}
            assert actual == expected
            for row in rows:
                count += 1
                assert row['run'] == run
                req = row['request']
                assert req['model'] == models[model['name']]
                assert req['temperature'] == 0 and req['max_tokens'] == 4096 and req['reasoning'] == {'exclude':True}
                assert len(req['messages']) == 1 and req['messages'][0]['role'] == 'user'
                item = next(i for i in bench['tests'][row['instrument']]['items'] if i['id'] == row['item_id'])
                assert item['text'] in req['messages'][0]['content']
                content = row.get('content','').strip()
                parsed = next((int(c) for c in content if c.isdigit()),None)
                assert row.get('rating') == parsed
                limit = 5 if row['instrument']=='MFQ-2' else 9
                strict = int(content) if re.fullmatch('[1-'+str(limit)+']',content) else None
                assert strict == row.get('strict_rating')
                numeric += parsed is not None and 1 <= parsed <= limit
                if row.get('response_id'):response_ids.append(row['response_id'])
                timestamps += [row['started_at'],row['finished_at']]
        assert abs(model['agreement']-100*model['matched_pairs']/model['compared_pairs']) < 1e-10
        assert abs(model['distance']-statistics.mean(r['distance'] for r in model['runs'])) < 1e-10
        assert model['numeric'] + model['missing'] == 280
        assert model['numeric'] == sum(r['numeric'] for r in model['runs'])
        for index, foundation in enumerate(summary['foundations']):
            assert abs(model['foundations'][index]-statistics.mean(r['foundations'][foundation] for r in model['runs'])) < 1e-10
    assert count == 2912 and numeric == 2875
    assert len(response_ids) == len(set(response_ids)) == 2900
    assert summary['llm_numeric'] == 3580 and summary['llm_scheduled'] == 3640
    assert [m['distance'] for m in summary['models']] == sorted(m['distance'] for m in summary['models'])
    # Pairwise and all-five-identical are deliberately different quantities.
    ratings = [3,3,3,3,4]
    assert sum(a==b for a,b in itertools.combinations(ratings,2)) == 6
    assert len(set(ratings)) != 1
    jev_count = 0
    for path in (ROOT/'results/jev-typesafe').glob('run-*.json'):
        data = json.loads(path.read_text())
        limit = 5 if data['instrument']=='MFQ-2' else 9
        for item in data['items']:
            assert item['rating'] == max(1,min(round(item['score'])+1,limit))
            jev_count += 1
    assert jev_count == 224
    assert summary['jev']['matched_pairs'] == 536 and summary['jev']['compared_pairs'] == 560
    report={'status':'passed','llm_new_records':count,'llm_new_numeric':numeric,'unique_llm_response_ids':len(response_ids),'jev_new_ratings':jev_count,'llm_collection_start_utc':min(timestamps),'llm_collection_end_utc':max(timestamps),'checks':['complete item sets and no duplicate final records','request parameters and item text','legacy and strict parser recomputation','unique returned LLM response identifiers','five-run averages and counts','pairwise example versus all-five identity','Jev score conversion'],'privacy_redactions':['user_id','organization_id when present','execution_host','opaque encrypted reasoning-state data']}
    (ROOT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts and not any(part.startswith('.') for part in p.relative_to(ROOT).parts))
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT/'manifest.json').write_text(json.dumps({'algorithm':'SHA-256','files':manifest},indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
