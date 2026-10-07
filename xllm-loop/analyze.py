"""Recompute compact metrics from saved measurements; no inference imports."""
import argparse,json,statistics,hashlib
from pathlib import Path

def summarize(run):
 rows=json.loads((run/'continuations.json').read_text());times=json.loads((run/'timings.json').read_text());q=json.loads((run/'qualification.json').read_text())
 result={'qualification':q,'continuation':[],'timing':[],'comparisons':[],'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [run/'continuations.json',run/'timings.json',run/'qualification.json']}}
 for model in ('learned-s','fixed-s'):
  for mode in ('full','terminal'):
   selected=[r for r in rows if r['model']==model and r['mode']==mode];loss=[v for r in selected for v in r['token_nll']]
   result['continuation'].append({'model':model,'mode':mode,'passages':len(selected),'tokens':len(loss),'mean_nll':statistics.mean(loss),'next_token_argmax_matches':sum(p==t for r in selected for p,t in zip(r['predicted_tokens'],r['target_tokens']))})
   for length in (128,512):
    group=[r for r in times if r['model']==model and r['mode']==mode and r['prefix_length']==length and not r['warmup']]
    result['timing'].append({'model':model,'mode':mode,'prefix_length':length,'n':len(group),'prefill_median_seconds':statistics.median(r['prefill_seconds'] for r in group),'decode32_median_seconds':statistics.median(r['decode32_seconds'] for r in group),'prefill_range_seconds':[min(r['prefill_seconds'] for r in group),max(r['prefill_seconds'] for r in group)],'decode32_range_seconds':[min(r['decode32_seconds'] for r in group),max(r['decode32_seconds'] for r in group)],'retained_kv_bytes':group[0]['retained_kv_bytes'],'torch_peak_allocated_max_bytes':max(r['torch_peak_allocated_bytes'] for r in group),'torch_peak_reserved_max_bytes':max(r['torch_peak_reserved_bytes'] for r in group)})
  for case in sorted({r['case'] for r in rows}):
   a=next(r for r in rows if r['model']==model and r['case']==case and r['mode']=='full');b=next(r for r in rows if r['model']==model and r['case']==case and r['mode']=='terminal')
   result['comparisons'].append({'model':model,'case':case,'terminal_minus_full_nll':b['mean_nll']-a['mean_nll'],'greedy_tokens_equal':a['generated_tokens']==b['generated_tokens'],'next_argmax_changes':sum(x!=y for x,y in zip(a['predicted_tokens'],b['predicted_tokens'])),'prompt':a['prompt_text'],'full_output':a['generated_text'],'terminal_output':b['generated_text']})
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('run');a=ap.parse_args();run=Path(a.run);r=summarize(run);(run/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('qualification','comparisons')},indent=2))
