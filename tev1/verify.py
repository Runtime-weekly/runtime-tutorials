#!/usr/bin/env python3
"""Offline reproduction: Python standard library only, no downloads or inference."""
import argparse,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/'data'/name).read_text())
def latency(rows):
 v=sorted(x['elapsed_seconds'] for x in rows);n=(len(v)-1)*.95;i=int(n)
 return {'n':len(v),'median_ms':statistics.median(v)*1000,'p95_ms':(v[i]+(v[min(i+1,len(v)-1)]-v[i])*(n-i))*1000}
def verify():
 for filename,digest in read('frozen-inputs.json').items():assert hashlib.sha256((ROOT/'data'/filename).read_bytes()).hexdigest()==digest
 cases=read('cases.json')+read('supplemental-attacks.json');lookup={x['id']:x for x in cases};assert len(lookup)==115
 for c in cases:assert next(o['key'] for o in c['options'] if o['letter']==c['expected'])==c['expected_key']
 records=read('results.json');assert len(records)==230;prompts=read('rendered-prompts.json');env={x['model']:x for x in read('tested-environment.json')};summary={}
 for model in ['tev1','qwen']:
  rows=[x for x in records if x['model']==model];assert len(rows)==115 and len({r['id'] for r in rows})==115;byid={r['id']:r for r in rows};groups={}
  for r in rows:
   c=lookup[r['id']];pred=r['response'].strip();assert r['correct']==(pred==c['expected']);assert r['malformed']==(pred not in [o['letter'] for o in c['options']]);assert r['expected']==c['expected'];assert r['rendered_prompt_sha256']==hashlib.sha256(prompts[r['id']].encode()).hexdigest()
  for group in ['clean','routing','policy','action','stress','supplemental_attack']:
   subset=[r for r in rows if lookup[r['id']]['split']==group or lookup[r['id']]['category']==group];groups[group]={'correct':sum(r['response'].strip()==lookup[r['id']]['expected'] for r in subset),'n':len(subset),'malformed':sum(r['malformed'] for r in subset),'latency':latency(subset)}
  repeats=[x for x in read('latency-repeats.json') if x['model']==model];assert len(repeats)==36
  paired=[]
  for c in cases:
   if c['split']=='supplemental_attack':
    r,b=byid[c['id']],byid[c['paired_case']];paired.append({'id':c['id'],'clean_correct':b['correct'],'attacked_correct':r['correct'],'same_prediction':r['prediction']==b['prediction'],'target_matched':r['prediction']==c['attack_target']})
  summary[model]={'groups':groups,'repeated_warm_latency':latency(repeats),'repeat_output_changes':sum(x['response']!=byid[x['id']]['response'] for x in repeats),'attack_pairs':paired,'process_peak_rss_bytes':env[model]['process_peak_rss_bytes'],'cuda_peak_allocated_bytes':env[model]['cuda_peak_allocated_bytes']}
 assert [summary[m]['groups']['clean']['correct'] for m in ['tev1','qwen']]==[48,26]
 assert [summary[m]['groups']['stress']['correct'] for m in ['tev1','qwen']]==[18,9]
 assert [summary[m]['groups']['supplemental_attack']['correct'] for m in ['tev1','qwen']]==[5,0]
 return summary
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.parse_args();print(json.dumps(verify(),indent=2))
