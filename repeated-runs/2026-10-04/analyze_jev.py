import ast,collections,itertools,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parent
b=json.loads((ROOT/'benchmark.json').read_text());ns={'statistics':statistics,'BENCH':b,'FOUND':list(b['tests']['MFQ-2']['foundations']),'NORM':[4.05,2.88,3.63,2.81,3.01,2.26]}
tree=ast.parse((ROOT/'analyze_repeats.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'score-functions','exec'),ns)
baseline=json.loads((ROOT/'baseline'/'raw_results_jev.json').read_text());runs={1:{(t,x['id']):x['rating'] for t,v in baseline.items() for x in v}};continuous={1:{(t,x['id']):x['jev_score']+1 for t,v in baseline.items() for x in v}}
for r in range(2,6):
 runs[r]={};continuous[r]={}
 for t in ['MFQ-2','EPQ']:
  p=ROOT/'results'/'jev-typesafe'/f'run-{r}-{t}.json';d=json.loads(p.read_text());assert d['status']=='complete'
  for x in d['items']:
   assert x['rating']==max(1,min(round(x['score'])+1,5 if t=='MFQ-2' else 9));runs[r][(t,x['id'])]=x['rating'];continuous[r][(t,x['id'])]=x['score']+1
 assert len(runs[r])==56 and all(v is not None for v in runs[r].values())
newpairs=[ns['agreement'](runs[x],runs[y]) for x,y in itertools.combinations(range(2,6),2)];basepairs=[ns['agreement'](runs[1],runs[r]) for r in range(2,6)]
score={r:ns['score'](runs[r]) for r in range(1,6)};cs={r:ns['score'](continuous[r]) for r in range(1,6)}
cchanges=[abs(continuous[x][k]-continuous[y][k]) for x,y in itertools.combinations(range(2,6),2) for k in continuous[x]]
out={'numeric':224,'new_pairwise':ns['aggregate_agreement'](newpairs),'baseline_agreement':ns['aggregate_agreement'](basepairs),'scores':score,'continuous_scores':cs,'all_four_identical_items':sum(len({runs[r][k] for r in range(2,6)})==1 for k in runs[2]),'new_distance_spread':ns['spread']([score[r]['distance'] for r in range(2,6)]),'continuous_pairwise_mean_absolute_item_difference':statistics.mean(cchanges),'continuous_max_pairwise_item_difference':max(cchanges),'continuous_pairwise_equal_within_1e-9':sum(x<1e-9 for x in cchanges)/len(cchanges)}
(ROOT/'jev-consistency.json').write_text(json.dumps(out,indent=2))
md=['# Jev repeat-study results','',f"All four additional runs returned every item (224/224). Exact agreement across the six pairs of new runs was {out['new_pairwise']['rate']*100:.2f}% ({out['new_pairwise']['matched']}/{out['new_pairwise']['compared']}). Agreement with the original rounded ratings was {out['baseline_agreement']['rate']*100:.2f}%. {out['all_four_identical_items']} of 56 items were identical in all four new runs.",'','| Run | Rounded distance | Continuous distance | Idealism | Relativism | Category |','| --- | --- | --- | --- | --- | --- |']
for r in range(1,6):
 s=score[r];md.append(f"| {r} | {s['distance']:.4f} | {cs[r]['distance']:.4f} | {s['idealism']:.3f} | {s['relativism']:.3f} | {s['category']} |")
md+=['',f"The average absolute difference between continuous item scores across pairs of new runs was {out['continuous_pairwise_mean_absolute_item_difference']:.4f} points; the largest was {out['continuous_max_pairwise_item_difference']:.4f}. This describes score stability, not probability calibration or moral correctness.",'','Jev retains the original separate task framing and score conversion. Its results should not be treated as an architecture-controlled comparison with the LLMs.']
(ROOT/'jev-consistency.md').write_text('\n'.join(md)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['scores','continuous_scores']},indent=2))
