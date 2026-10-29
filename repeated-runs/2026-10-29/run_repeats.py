#!/usr/bin/env python3
"""Five fresh administrations with the previously published request parameters.
Credentials are read at runtime and never written into request/result archives.
"""
import argparse,ast,concurrent.futures,datetime,hashlib,json,os,pathlib,re,threading,time,urllib.error,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
BENCH=json.loads((ROOT/'benchmark.json').read_text())
MODELS=json.loads((ROOT/'models.json').read_text())
MFQ_SCALE='1 = Does not describe me at all, 2 = Slightly describes me, 3 = Moderately describes me, 4 = Describes me fairly well, 5 = Describes me extremely well'
EPQ_SCALE='1 = Completely disagree, 2 = Largely disagree, 3 = Moderately disagree, 4 = Slightly disagree, 5 = Neither agree nor disagree, 6 = Slightly agree, 7 = Moderately agree, 8 = Largely agree, 9 = Completely agree'
LOCK=threading.Lock();STOP=threading.Event();STATE={};KEYS=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def credential(name):
 v=os.environ.get(name)
 if not v:raise RuntimeError(name+' is not configured')
 KEYS.append(v);return v
def clean(value):
 if isinstance(value,dict) and value.get('type')=='reasoning.encrypted':value={k:v for k,v in value.items() if k!='data'}
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in {'user_id','organization_id','execution_host'}}
 if isinstance(value,list):return [clean(v) for v in value]
 if isinstance(value,str):
  for key in KEYS:value=value.replace(key,'[REDACTED]')
 return value
def writejson(path,obj):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(clean(obj),indent=2));tmp.replace(path)
def status(name,**values):
 with LOCK:
  STATE.setdefault(name,{}).update(values)
  writejson(ROOT/'status.json',{'updated_at':now(),'stopped':STOP.is_set(),'models':STATE})
def trial_status(name,trial_id,**values):
 with LOCK:
  model=STATE.setdefault(name,{})
  model.pop('error',None)
  trials=model.setdefault('trials',{})
  trials.setdefault(str(trial_id),{}).update(values)
  model['completed']=sum(v.get('completed',0) for v in trials.values())
  model['scheduled']=280
  model['state']='complete' if len(trials)==5 and all(v.get('state')=='complete' for v in trials.values()) else 'running'
  if any(v.get('state','').startswith('blocked') for v in trials.values()):model['state']='blocked_model_access'
  model['last_update']=now()
  writejson(ROOT/'status.json',{'updated_at':now(),'stopped':STOP.is_set(),'models':STATE})
def log(path,obj):
 with path.open('a') as f:f.write(json.dumps(clean(obj),ensure_ascii=False)+'\n');f.flush()
def parse(content,limit):
 legacy=next((int(c) for c in content if c.isdigit()),None)
 strict=int(content) if re.fullmatch('[1-'+str(limit)+']',content) else None
 return legacy,strict

def request(url,payload,key):
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=120) as resp:return resp.status,json.loads(resp.read()),None
 except urllib.error.HTTPError as e:
  txt=e.read().decode(errors='replace')
  try:body=json.loads(txt)
  except Exception:body={'unparsed_body':txt}
  return e.code,body,'http_error'
 except Exception as e:return None,None,type(e).__name__+': '+str(e)

def llm_worker(name,model,key,run_id):
 slug=re.sub('[^a-z0-9]+','-',name.lower()).strip('-');folder=ROOT/'results'/slug;folder.mkdir(parents=True,exist_ok=True)
 completed=0;fatal_streak=0
 for run in [run_id]:
  path=folder/('run-'+str(run)+'.jsonl');old={}
  if path.exists():
   for line in path.read_text().splitlines():
    d=json.loads(line)
    if d.get('record_type')=='result' and d.get('status') not in ['blocked_auth_or_credit','blocked_model_access']:old[(d['instrument'],d['item_id'])]=d
  for test in ['MFQ-2','EPQ']:
   limit=5 if test=='MFQ-2' else 9;scale=MFQ_SCALE if test=='MFQ-2' else EPQ_SCALE
   for item in BENCH['tests'][test]['items']:
    if STOP.is_set():trial_status(name,run,state='stopped',completed=completed);return
    if (test,item['id']) in old:completed+=1;continue
    prompt=BENCH['benchmark_protocol']['prompt_template'].format(scale_description=scale,item_text=item['text'])
    payload={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':4096,'reasoning':{'exclude':True}}
    record={'record_type':'result','requested_model':model,'model_label':name,'run':run,'instrument':test,'item_id':item['id'],'started_at':now(),'request':payload,'attempts':[]}
    for attempt in range(1,4):
     before=time.monotonic();code,body,error=request('https://openrouter.ai/api/v1/chat/completions',payload,key)
     receipt={'attempt':attempt,'finished_at':now(),'elapsed_seconds':round(time.monotonic()-before,3),'http_status':code,'response':body,'transport_error':error}
     record['attempts'].append(receipt)
     log(folder/'attempts.jsonl',{'run':run,'instrument':test,'item_id':item['id'],**receipt})
     if code==403:
      record.update(status='blocked_model_access',rating=None,strict_rating=None);break
     if code in [401,402]:
      record.update(status='blocked_auth_or_credit',rating=None,strict_rating=None);STOP.set();break
     if error is None and isinstance(body,dict) and body.get('choices'):
      content=(body['choices'][0].get('message',{}).get('content') or '').strip()
      legacy,strict=parse(content,limit)
      record.update(content=content,rating=legacy,strict_rating=strict,status='numeric' if strict is not None else 'non_strict_numeric' if legacy is not None else 'non_numeric',returned_model=body.get('model'),provider=body.get('provider'),response_id=body.get('id'),usage=body.get('usage'))
      fatal_streak=0;break
     if attempt==3:
      record.update(status='api_failure',rating=None,strict_rating=None)
      fatal_streak=fatal_streak+1 if code in [400,404] else 0
     else:time.sleep(2**attempt)
    record['finished_at']=now();log(path,record);completed+=1
    trial_status(name,run,state='running',completed=completed,scheduled=280,run=run,instrument=test,item=item['id'],last_status=record['status'])
    if completed%28==0:print(name,completed,'/280',flush=True)
    if record['status']=='blocked_model_access':
     trial_status(name,run,state='blocked_model_access',completed=completed);return
    if fatal_streak>=3:
     trial_status(name,run,state='blocked_model_endpoint',completed=completed);return
    time.sleep(0.3)
 trial_status(name,run,state='complete',completed=completed)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model');args=ap.parse_args()
 if (ROOT/'status.json').exists():STATE.update(json.loads((ROOT/'status.json').read_text()).get('models',{}))
 selected={n:m for n,m in MODELS.items() if not args.model or n==args.model}
 if not selected:raise RuntimeError('No selected model identifiers')
 key=credential('OPENROUTER_API_KEY')
 writejson(ROOT/'execution.json',{'started_at':now(),'runs':[1,2,3,4,5],'model_count':len(selected),'scheduled_llm_items':len(selected)*280,'concurrent_trial_streams':16,'temperature':0,'max_tokens':4096,'reasoning':{'exclude':True},'item_order':'original stored order, one user message per item','parser':'original first digit retained alongside strict full-response integer validation','benchmark_sha256':hashlib.sha256((ROOT/'benchmark.json').read_bytes()).hexdigest()})
 names=list(selected)
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
  jobs={pool.submit(llm_worker,n,selected[n],key,r):n for n in names for r in range(1,6)}
  for f in concurrent.futures.as_completed(jobs):
   try:f.result()
   except Exception as e:status(jobs[f],state='worker_error',error=str(e));print(jobs[f],'worker error',type(e).__name__,flush=True)
 print('LLM collection finished',flush=True)
if __name__=='__main__':main()
