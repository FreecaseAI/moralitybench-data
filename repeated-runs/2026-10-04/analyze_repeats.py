#!/usr/bin/env python3
import collections,itertools,json,math,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parent
BENCH=json.loads((ROOT/'benchmark.json').read_text())
MODELS=json.loads((ROOT/'models.json').read_text())
FOUND=list(BENCH['tests']['MFQ-2']['foundations'])
NORM=[4.05,2.88,3.63,2.81,3.01,2.26]
BASE={}
for f in (ROOT/'baseline').glob('raw_results_batch*.json'):BASE.update(json.loads(f.read_text()))

def mean(v):return statistics.mean(v) if v else None
def spread(v):
 v=[x for x in v if x is not None]
 return {'n':len(v),'mean':mean(v),'sd':statistics.stdev(v) if len(v)>1 else None,'min':min(v) if v else None,'max':max(v) if v else None,'range':max(v)-min(v) if v else None}
def valid(v,t):return v if isinstance(v,int) and 1<=v<=(5 if t=='MFQ-2' else 9) else None
def getbase(name):return {(t,x['id']):valid(x['rating'],t) for t,v in BASE.get(name,{}).items() for x in v}
def score(values,restrict=None):
 def vals(test,ids):return [values[(test,i)] for i in ids if (test,i) in values and values[(test,i)] is not None and (restrict is None or (test,i) in restrict)]
 f={};counts={}
 for name in FOUND:
  v=vals('MFQ-2',BENCH['tests']['MFQ-2']['foundations'][name]['items']);f[name]=mean(v);counts[name]=len(v)
 iv=vals('EPQ',range(1,11));rv=vals('EPQ',range(11,21));I=mean(iv);R=mean(rv)
 cat=None if I is None or R is None else ('Situationist' if R>=5 else 'Absolutist') if I>=5 else ('Subjectivist' if R>=5 else 'Exceptionist')
 return {'foundations':f,'foundation_counts':counts,'distance':mean([abs(f[k]-h) for k,h in zip(FOUND,NORM)]) if all(f[k] is not None for k in FOUND) else None,'idealism':I,'relativism':R,'epq_counts':[len(iv),len(rv)],'category':cat,'numeric':sum(v is not None for v in values.values())}
def agreement(a,b):
 ks=[k for k in a.keys() & b.keys() if a[k] is not None and b[k] is not None]
 same=sum(a[k]==b[k] for k in ks)
 return {'matched':same,'compared':len(ks),'rate':same/len(ks) if ks else None,'mean_absolute_difference':mean([abs(a[k]-b[k]) for k in ks])}
def aggregate_agreement(pairs):
 n=sum(x['compared'] for x in pairs);same=sum(x['matched'] for x in pairs)
 return {'matched':same,'compared':n,'rate':same/n if n else None}
def fmt(v,n=3):return 'NA' if v is None else f'{v:.{n}f}'
def pct(v):return 'NA' if v is None else f'{v*100:.1f}%'

out={'models':{},'design':{'original_run':1,'new_runs':[2,3,4,5],'primary_parser':'original first-digit within valid range','sensitivity_parser':'strict full-answer integer'}}
for name in MODELS:
 slug=''.join(c.lower() if c.isalnum() else '-' for c in name)
 import re
 slug=re.sub('-+','-',slug).strip('-');folder=ROOT/'results'/slug
 rows={};runs={1:getbase(name)};strict_runs={}
 for run in range(2,6):
  path=folder/f'run-{run}.jsonl';records={}
  if path.exists():
   for line in path.read_text().splitlines():
    x=json.loads(line)
    if x.get('record_type')=='result':records[(x['instrument'],x['item_id'])]=x
  rows[run]=records;runs[run]={k:valid(x.get('rating'),k[0]) for k,x in records.items()};strict_runs[run]={k:valid(x.get('strict_rating'),k[0]) for k,x in records.items()}
 pairs=[{'runs':[a,b],**agreement(runs[a],runs[b])} for a,b in itertools.combinations(range(2,6),2)]
 basepairs=[{'runs':[1,n],**agreement(runs[1],runs[n])} for n in range(2,6)]
 common=set.intersection(*[{k for k,v in runs[n].items() if v is not None} for n in range(2,6)])
 common5=common & {k for k,v in runs[1].items() if v is not None}
 allrows=[x for records in rows.values() for x in records.values()]
 scores={n:score(runs[n]) for n in range(1,6)}
 m={'new_records':len(allrows),'completed_runs':sum(len(rows[n])==56 and not any(x['status'].startswith('blocked') for x in rows[n].values()) for n in range(2,6)),
 'statuses':dict(collections.Counter(x['status'] for x in allrows)), 'scores':scores,'strict_scores':{n:score(strict_runs[n]) for n in range(2,6)},
 'new_pairwise':aggregate_agreement(pairs),'new_pairs':pairs,'baseline_agreement':aggregate_agreement(basepairs),'baseline_pairs':basepairs,
 'all_four_observed_items':len(common),'all_four_identical_items':sum(len({runs[n][k] for n in range(2,6)})==1 for k in common),
 'common_four_scores':{n:score(runs[n],common) for n in range(2,6)},'common_five_scores':{n:score(runs[n],common5) for n in range(1,6)},
 'new_spread':{k:spread([scores[n][k] for n in range(2,6)]) for k in ['distance','idealism','relativism']},
 'foundation_spread':{k:spread([scores[n]['foundations'][k] for n in range(2,6)]) for k in FOUND},
 'returned_models':dict(collections.Counter(x.get('returned_model') for x in allrows if x.get('returned_model'))),
 'providers':dict(collections.Counter(x.get('provider') for x in allrows if x.get('provider'))),
 'recorded_cost_usd':sum((x.get('usage') or {}).get('cost',0) or 0 for x in allrows),
 'tokens':{k:sum((x.get('usage') or {}).get(k,0) or 0 for x in allrows) for k in ['prompt_tokens','completion_tokens','total_tokens']}}
 out['models'][name]=m
original=[n for n in MODELS if out['models'][n]['scores'][1]['distance'] is not None]
for run in range(1,6):
 vals={n:out['models'][n]['scores'][run]['distance'] for n in original if out['models'][n]['scores'][run]['distance'] is not None}
 for n,v in vals.items():out['models'][n].setdefault('ranks',{})[run]=1+sum(x<v for x in vals.values())+(sum(x==v for x in vals.values())-1)/2
out['total_cost_usd']=sum(m['recorded_cost_usd'] for m in out['models'].values())
(ROOT/'consistency-analysis.json').write_text(json.dumps(out,indent=2))
finished=all(out['models'][n]['completed_runs']==4 for n in original)
md=['# MoralityBench repeat-study results','', 'Collection complete for the 13 originally scored LLMs.' if finished else 'Collection is in progress. Partial statistics must not be interpreted as the completed four-run comparison.','',
'The four new administrations preserve the original requests. The comparison with the original archive is reported separately from agreement among new runs. Primary agreement uses the original first-digit parser, limited to valid scale values; the archive also contains strict-parser results.','',
'| Model | New runs complete | Numeric / 224 | Pairwise agreement, new runs | Agreement with original | Distance, new mean (SD) | New distance range |','| --- | --- | --- | --- | --- | --- | --- |']
for n in sorted(original,key=lambda n:out['models'][n]['scores'][1]['distance']):
 m=out['models'][n];sp=m['new_spread']['distance'];md.append('| '+n+' | '+str(m['completed_runs'])+'/4 | '+str(sum(m['scores'][r]['numeric'] for r in range(2,6)))+' / 224 | '+pct(m['new_pairwise']['rate'])+' ('+str(m['new_pairwise']['compared'])+' pairs) | '+pct(m['baseline_agreement']['rate'])+' ('+str(m['baseline_agreement']['compared'])+' comparisons) | '+fmt(sp['mean'])+' ('+fmt(sp['sd'])+') | '+fmt(sp['min'])+' to '+fmt(sp['max'])+' |')
md+=['','Pairwise agreement pools the six pairs of new runs, comparing only items with valid ratings in both members. Agreement with the original pools the four baseline-to-new comparisons. Missing responses never count as agreement. Means and standard deviations describe these observations and are not estimates of uncertainty over all future queries.','', '## Completion and output format','', '| Model | Strict numeric | Other numeric text | Nonnumeric | API failures | Items present in all four | Identical in all four |','| --- | --- | --- | --- | --- | --- | --- |']
for n in original:
 m=out['models'][n];c=m['statuses'];md.append('| '+' | '.join([n,str(c.get('numeric',0)),str(c.get('non_strict_numeric',0)),str(c.get('non_numeric',0)),str(c.get('api_failure',0)),str(m['all_four_observed_items']),str(m['all_four_identical_items'])])+' |')
md+=['','## EPQ and distance by run','','| Model | Run | Distance | Idealism | Relativism | Category | Numeric items |','| --- | --- | --- | --- | --- | --- | --- |']
for n in original:
 for r in range(1,6):
  s=out['models'][n]['scores'][r];md.append('| '+' | '.join([n,str(r),fmt(s['distance']),fmt(s['idealism']),fmt(s['relativism']),str(s['category'] or 'NA'),str(s['numeric'])+'/56'])+' |')
md+=['','## Access limits','','Muse Spark 1.3 requires an age attestation in the OpenRouter account before it can serve requests. Its original record contains no usable ratings, and it is excluded from the primary comparison. Jev is reported separately in jev-consistency.md.','',f"Reported OpenRouter cost for archived result responses: ${out['total_cost_usd']:.4f}. This may exclude charges for failed or retried requests."]
(ROOT/'consistency-report.md').write_text('\n'.join(md)+'\n')
print('Completed model studies',sum(m['completed_runs']==4 for m in out['models'].values()),'/ 13 primary; result records',sum(m['new_records'] for m in out['models'].values()),'; recorded cost USD',round(out['total_cost_usd'],4))
