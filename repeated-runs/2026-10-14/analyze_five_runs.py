#!/usr/bin/env python3
"""Score five fresh runs with the frozen October 4 scoring functions."""
import collections,csv,hashlib,importlib.util,itertools,json,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'2026-10-04'
source=PREVIOUS/'analyze_repeats.py'
ns={'__file__':str(source)}
exec(compile(source.read_text().split("out={'models':",1)[0],str(source),'exec'),ns)
spec=importlib.util.spec_from_file_location('previous_summary',PREVIOUS/'summarize_five_runs.py')
summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)
summary.PRESENTATION.update({'GPT-6 Astra':('OpenAI','#9a3412'),'Muse Wonder':('Meta','#9333ea'),'Gemini 4 Argon':('Google','#1d4ed8')})

def main():
 models=json.loads((ROOT/'models.json').read_text());details={};scored=[];strict_models=[];unscored=[];response_ids=[]
 expected={(test,item['id']) for test in ['MFQ-2','EPQ'] for item in ns['BENCH']['tests'][test]['items']}
 assert len(expected)==56
 for name,identifier in models.items():
  slug=re.sub('[^a-z0-9]+','-',name.lower()).strip('-');runs={};rows=[]
  for run in range(1,6):
   records=[json.loads(line) for line in (ROOT/'results'/slug/f'run-{run}.jsonl').read_text().splitlines()]
   assert len(records)==56 and {(x['instrument'],x['item_id']) for x in records}==expected
   assert all(x['run']==run and x['requested_model']==identifier for x in records)
   for x in records:
    assert x['request']['temperature']==0 and x['request']['max_tokens']==4096 and x['request']['reasoning']=={'exclude':True}
    expected_prompt=ns['BENCH']['benchmark_protocol']['prompt_template'].format(scale_description=__import__('run_repeats').MFQ_SCALE if x['instrument']=='MFQ-2' else __import__('run_repeats').EPQ_SCALE,item_text=next(i['text'] for i in ns['BENCH']['tests'][x['instrument']]['items'] if i['id']==x['item_id']))
    assert x['request']['messages']==[{'role':'user','content':expected_prompt}]
    if x.get('response_id'):response_ids.append(x['response_id'])
   rows+=records
   runs[run]={(x['instrument'],x['item_id']):ns['valid'](x.get('rating'),x['instrument']) for x in records}
  scores={str(r):ns['score'](runs[r]) for r in range(1,6)}
  analysis={'scores':scores,'new_pairwise':ns['aggregate_agreement']([ns['agreement'](runs[a],runs[b]) for a,b in itertools.combinations(range(2,6),2)]),'baseline_agreement':ns['aggregate_agreement']([ns['agreement'](runs[1],runs[r]) for r in range(2,6)])}
  details[name]={'requested_model':identifier,'scores':scores,'statuses':dict(collections.Counter(x['status'] for x in rows)),'returned_models':dict(collections.Counter(x.get('returned_model') for x in rows if x.get('returned_model'))),'providers':dict(collections.Counter(x.get('provider') for x in rows if x.get('provider'))),'recorded_cost_usd':sum((x.get('usage') or {}).get('cost',0) or 0 for x in rows),'strict_scores':{str(r):ns['score']({(x['instrument'],x['item_id']):ns['valid'](x.get('strict_rating'),x['instrument']) for x in rows if x['run']==r}) for r in range(1,6)}}
  if any(s['distance'] is None or s['idealism'] is None or s['relativism'] is None for s in scores.values()):
   unscored.append({'name':name,'requested_model':identifier,'reason':'At least one run lacks an entire foundation or EPQ axis; not ranked','statuses':details[name]['statuses']});continue
  strict_values={r:{(x['instrument'],x['item_id']):ns['valid'](x.get('strict_rating'),x['instrument']) for x in rows if x['run']==r} for r in range(1,6)}
  strict_analysis={'scores':details[name]['strict_scores'],'new_pairwise':ns['aggregate_agreement']([ns['agreement'](strict_values[a],strict_values[b]) for a,b in itertools.combinations(range(2,6),2)]),'baseline_agreement':ns['aggregate_agreement']([ns['agreement'](strict_values[1],strict_values[r]) for r in range(2,6)])}
  if all(s['distance'] is not None and s['idealism'] is not None and s['relativism'] is not None for s in strict_analysis['scores'].values()):strict_models.append(summary.summarize(name,strict_analysis,[strict_values[r] for r in range(1,6)]))
  m=summary.summarize(name,analysis,[runs[r] for r in range(1,6)]);m.update({'requested_model':identifier,'collection_date':'2026-10-14','release_path':'repeated-runs/2026-10-14'});scored.append(m)
 assert len(response_ids)==len(set(response_ids)), 'Repeated response IDs'
 scored.sort(key=lambda m:m['distance'])
 for rank,m in enumerate(scored,1):m['rank']=rank
 strict_models.sort(key=lambda m:m['distance'])
 for rank,m in enumerate(strict_models,1):
  m.update({'rank':rank,'requested_model':models[m['name']],'collection_date':'2026-10-14','release_path':'repeated-runs/2026-10-14','parser':'strict whole-answer integer'})
 for d in details.values():d['legacy_scores']=d.pop('scores')
 out={'version':'five-fresh-runs-2026-10-14','foundations':summary.FOUNDATIONS,'human_norms':summary.NORMS,'models':strict_models,'legacy_models':scored,'strict_models':strict_models,'primary_parser':'Strict whole-answer integer; numeric mentions inside prose are not self-ratings','unscored_models':unscored,'scheduled':840,'record_count':840,'details':details,'recorded_cost_usd':sum(x['recorded_cost_usd'] for x in details.values()),'scoring_sources':{str(s.relative_to(ROOT.parent.parent)):hashlib.sha256(s.read_bytes()).hexdigest() for s in [source,PREVIOUS/'summarize_five_runs.py']},'limits':'Five independent fresh administrations per added model, not longitudinal repeats of older configurations. Shared prompt and scoring do not guarantee fixed checkpoints or support for temperature=0 on every endpoint. Missing values are omitted, never neutral. Data collection dates differ across cohorts.'}
 (ROOT/'five-run-summary.json').write_text(json.dumps(out,indent=2)+'\n')
 (ROOT/'verification.json').write_text(json.dumps({'verified':True,'records':840,'distinct_response_ids':len(response_ids),'all_item_sets_settings_prompts_checked':True,'models_ranked':len(strict_models),'unscored_models':len(unscored)},indent=2)+'\n')
 prior=json.loads((PREVIOUS/'five-run-summary.json').read_text())
 for m in prior['models']:m.update({'collection_date':'2026-10-04','release_path':'repeated-runs/2026-10-04','parser':'historical first digit within range'})
 prior['models'] += [dict(m) for m in strict_models]
 prior['models'].sort(key=lambda m:m['distance'])
 for rank,m in enumerate(prior['models'],1):m['rank']=rank
 prior.update({'version':'combined-five-runs-2026-10-14','llm_numeric':sum(m['numeric'] for m in prior['models']),'llm_scheduled':sum(m['scheduled'] for m in prior['models']),'latest_extension':{'collection_date':'2026-10-14','models':list(details),'strict_models':strict_models,'legacy_models':scored,'unscored_models':unscored,'primary_parser':out['primary_parser'],'limits':'Older cohort uses original first-digit parsing and includes cross-time pairs; October14 uses strict whole-answer integers and concurrent same-session trial streams. Rankings are descriptive across dates and parser policies.'}})
 (ROOT/'combined-five-run-summary.json').write_text(json.dumps(prior,indent=2)+'\n')
 manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts}
 (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'models':[{k:m[k] for k in ['name','numeric','missing','distance','agreement']} for m in strict_models],'unscored':unscored,'recorded_cost_usd':out['recorded_cost_usd']},indent=2))
if __name__=='__main__':main()
