#!/usr/bin/env python3
"""Offline descriptive analysis and development-only confidence gate selection."""
import argparse,json,statistics
from pathlib import Path
THRESHOLDS=[.5,.6,.7,.8,.9,.95]
def good(row,case):return bool(row and row.get('status')=='ok' and row.get('choice')==case['expected_key'])
def escalate(row,threshold):return not row or row.get('status')!='ok' or row.get('score') is None or row['score']<threshold
def gate(dev,results):
 target=sum(not good(results.get(('s2',c['id'])),c) for c in dev)
 trials=[]
 for t in THRESHOLDS:
  decisions=[(c,escalate(results.get(('s1',c['id'])),t)) for c in dev]
  errors=sum(not good(results.get(('s2' if e else 's1',c['id'])),c) for c,e in decisions)
  trials.append({'threshold':t,'errors':errors,'escalations':sum(e for _,e in decisions)})
 accepted=next((x for x in trials if x['errors']<=target),None)
 return {'status':'qualified_on_dev' if accepted else 'no_gate_qualified','threshold':accepted['threshold'] if accepted else None,'always_s2_dev_errors':target,'dev_count':len(dev),'trials':trials,'rule':'lowest threshold with dev errors <= always-S2; strict score < threshold escalates; missing/failed S1 escalates'}
def summary(cases,results,arm):
 rows=[results.get((arm,c['id'])) for c in cases];times=[r['seconds'] for r in rows if r and isinstance(r.get('seconds'),(float,int))];correct=sum(good(r,c) for r,c in zip(rows,cases));n=len(cases)
 return {'n':n,'correct':correct,'accuracy':correct/n if n else None,'missing':sum(r is None for r in rows),'failed':sum(r is not None and r.get('status')!='ok' for r in rows),'median_seconds':statistics.median(times) if times else None,'p95_seconds_nearest_rank':sorted(times)[max(0,__import__('math').ceil(.95*len(times))-1)] if times else None}
def diagnostics(cases,results,arm):
 bins=[{'lower':i/5,'upper':(i+1)/5,'n':0,'correct':0,'score_sum':0} for i in range(5)];brier=[];wrong_high=[];paired={'n':0,'same_semantic_choice':0,'both_correct':0};unfinished=0;requests=0
 for c in cases:
  r=results.get((arm,c['id']))
  if not r:continue
  raw=r.get('raw_response',{});thinking=raw.get('thinking',{})
  if thinking.get('finished_within_budget') is False:unfinished+=1
  requests+=raw.get('num_model_requests',0) or 0
  if c['transform']=='canonical' and r.get('status')=='ok' and r.get('score') is not None:
   score=r['score'];b=bins[min(4,int(score*5))];b['n']+=1;b['correct']+=good(r,c);b['score_sum']+=score
   if score>=.9 and not good(r,c):wrong_high.append(c['id'])
   if r.get('probabilities'):
    brier.append(sum((p-float(o['key']==c['expected_key']))**2 for p,o in zip(r['probabilities'],c['options'])))
  if c['parent_id']:
   parent=results.get((arm,c['parent_id']))
   paired['n']+=1
   if r.get('status')=='ok' and parent and parent.get('status')=='ok':
    paired['same_semantic_choice']+=r['choice']==parent['choice'];paired['both_correct']+=r['choice']==parent['choice']==c['expected_key']
 return {'calibration_scope':'descriptive canonical scored rows only; five fixed bins, small sample and dependent families; no calibration claim','bins':bins,'multiclass_brier_mean':statistics.mean(brier) if brier else None,'wrong_at_score_ge_0_9':wrong_high,'paired_stress':paired,'unfinished_reasoning_rows':unfinished,'reported_model_requests':requests}
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=Path,required=True);p.add_argument('--results',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--select-gate',type=Path);p.add_argument('--gate',type=Path);a=p.parse_args();cases=json.loads(a.cases.read_text());results={}
 for path in a.results:
  for r in json.loads(path.read_text()):
   k=(r['arm'],r['id'])
   if k in results:raise ValueError('Duplicate result; refusing cherry-picked replacement: '+str(k))
   results[k]=r
 dev=[c for c in cases if c['split']=='dev' and c['transform']=='canonical'];test=[c for c in cases if c['split']=='test'];canonical=[c for c in test if c['transform']=='canonical']
 if a.select_gate:
  if any(r.get('split')!='dev' for r in results.values()):raise ValueError('Gate selection accepts dev results only')
  if any((arm,c['id']) not in results for arm in ['s1','s2'] for c in dev):raise ValueError('Complete dev S1/S2 required')
  with a.select_gate.open('x') as f:json.dump(gate(dev,results),f,indent=2)
 arms=sorted({x[0] for x in results});report={'scope':'descriptive synthetic template-family test; no independent-binomial claims','canonical':{arm:summary(canonical,results,arm) for arm in arms},'by_task':{task:{arm:summary([c for c in canonical if c['task']==task],results,arm) for arm in arms} for task in ['routing','next_action']},'stress':{kind:{arm:summary([c for c in test if c['transform']==kind],results,arm) for arm in arms} for kind in ['reverse','permuted','irrelevant','attack']}}
 report['diagnostics']={arm:diagnostics(test,results,arm) for arm in arms}
 if a.gate:
  g=json.loads(a.gate.read_text());t=g.get('threshold')
  if t is None:report['gated']={'status':'no_gate_qualified'}
  else:
   hybrid={};escalations=0
   for c in test:
    one=results.get(('s1',c['id']));e=escalate(one,t);escalations+=e;chosen=results.get(('s2' if e else 's1',c['id']))
    if chosen:
     hybrid[('gated',c['id'])]={**chosen,'seconds':(one or {}).get('seconds',0)+(chosen.get('seconds',0) if e else 0)}
   report['gated']={'threshold':t,'canonical':summary(canonical,hybrid,'gated'),'all_condition_escalations':escalations,'timing_scope':'offline reconstructed S1 plus S2 when escalated; excludes live orchestration overhead, not measured online gate'}
 with a.output.open('x') as f:json.dump(report,f,indent=2)
if __name__=='__main__':main()
