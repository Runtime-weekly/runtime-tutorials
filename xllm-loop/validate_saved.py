"""Offline acceptance checks for completed local paired runs."""
import argparse,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--study',default='study.json');a=p.parse_args();run=Path(a.run)
study=json.loads(Path(a.study).read_text());q=json.loads((run/'qualification.json').read_text());rows=json.loads((run/'continuations.json').read_text());times=json.loads((run/'timings.json').read_text())
assert q['status']=='completed';assert q['study_sha256']==hashlib.sha256(Path(a.study).read_bytes()).hexdigest()
assert len(rows)==12 and len({(r['model'],r['case'],r['mode']) for r in rows})==12
for r in rows:
 c=next(c for c in study['cases'] if c['id']==r['case']);n=c['prefix_tokens'];assert r['prefix_tokens']==c['tokens'][:n];assert r['target_tokens']==c['tokens'][n:n+32]
 assert len(r['token_nll'])==len(r['target_tokens'])==r['scored_tokens']==32
 assert all(math.isfinite(x) and x>=0 for x in r['token_nll']);assert len(r['generated_tokens'])==24
for model in study['models']:
 for length in (128,512):
  for rep in (-1,0,1,2):
   arow=next(r for r in times if (r['model'],r['prefix_length'],r['rep'],r['mode'])==(model,length,rep,'full'))
   brow=next(r for r in times if (r['model'],r['prefix_length'],r['rep'],r['mode'])==(model,length,rep,'terminal'))
   assert arow['retained_kv_bytes']==3*brow['retained_kv_bytes']
   assert brow['retained_kv_bytes']==4*2*(length+32)*6*64*2
   assert all(math.isfinite(r[k]) and r[k]>0 for r in (arow,brow) for k in ('prefill_seconds','decode32_seconds'))
assert q['min_host_available_bytes']>12*2**30
checks={'passed':True,'rows':len(rows),'timings':len(times),'identical_scored_tokens':True,'cache_ratio_all_pairs':3,'memory_floor_maintained':True,'scope':'saved arithmetic/schema/integrity checks, not fused-backend or language-quality validation'}
(run/'acceptance.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))
