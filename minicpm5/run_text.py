"""Isolated native BF16 matched-settings small text pilot; no generated code runs."""
import argparse,hashlib,json,os,time,resource
from pathlib import Path
D=Path(__file__).resolve().parent
REVS={'1b':'87179e5c1f455ef22e6223592d2d61351b525bfc','2b':'f97400052a43d642bbc6e9975e2397e3ae6a6b52'}
def avail():return int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
def main():
 p=argparse.ArgumentParser();p.add_argument('model',choices=REVS);p.add_argument('--output',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
 manifest=json.loads((D/'checkpoint-manifest.json').read_text())[a.model]
 assert manifest['revision']==REVS[a.model]
 for name,expected in manifest['files'].items():
  path=a.model_dir/name
  assert path.is_file() and path.stat().st_size==expected['size'],f'Checkpoint file missing/size mismatch: {name}'
  digest=hashlib.sha256()
  with path.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
  assert digest.hexdigest()==expected['sha256'],f'Checkpoint hash mismatch: {name}'
 assert avail()>20*2**30,'Require20GiB available before load'
 b=(D/'tasks.frozen.json').read_bytes();assert hashlib.sha256(b).hexdigest()==(D/'tasks.sha256.txt').read_text().strip();tasks=json.loads(b)
 a.output.mkdir(exist_ok=False);os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 import torch,transformers
 from transformers import AutoTokenizer,AutoModelForCausalLM
 torch.set_num_threads(3);torch.manual_seed(510);torch.cuda.reset_peak_memory_stats()
 start=time.perf_counter();tokenizer=AutoTokenizer.from_pretrained(a.model_dir,local_files_only=True)
 model,info=AutoModelForCausalLM.from_pretrained(a.model_dir,local_files_only=True,dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa',output_loading_info=True);model.eval();torch.cuda.synchronize();load=time.perf_counter()-start
 assert not any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']),info
 meta={'model':f'openbmb/MiniCPM5-{a.model.upper()}','revision':REVS[a.model],'checkpoint_verified':True,'torch':torch.__version__,'transformers':transformers.__version__,'dtype':'bfloat16','attention':'sdpa','threads':3,'thinking':True,'do_sample':True,'temperature':.9 if a.model=='1b' else 1.0,'top_p':.95,'configuration':'official recommended thinking sampling','max_new_tokens':4096,'load_seconds':load,'loading_info':info,'task_sha256':hashlib.sha256(b).hexdigest(),'runtime_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'timing_scope':'Already loaded model, full template/tokenization/GPU generation/decode; first case labeled cold-request, no optimized serving claim'}
 (a.output/'meta.json').write_text(json.dumps(meta,indent=2,default=lambda x:sorted(x) if isinstance(x,set) else str(x)))
 with (a.output/'results.jsonl').open('x') as f:
  for idx,c in enumerate(tasks):
   assert avail()>12*2**30,'12GiB runtime reserve reached'
   messages=[{'role':'system','content':'Follow the task. Return only the requested JSON, with no markdown or explanation.'},{'role':'user','content':c['prompt']}]
   start=time.perf_counter();rendered=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=True);inputs=tokenizer(rendered,return_tensors='pt',add_special_tokens=False).to('cuda');official=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=True,add_generation_prompt=True,enable_thinking=True)['input_ids'];assert inputs.input_ids[0].tolist()==official,'Template token mismatch';torch.cuda.synchronize()
   with torch.inference_mode():out=model.generate(**inputs,max_new_tokens=4096,do_sample=True,temperature=.9 if a.model=='1b' else 1.0,top_p=.95,pad_token_id=tokenizer.eos_token_id)
   torch.cuda.synchronize();ids=out[0,inputs.input_ids.shape[1]:];answer=tokenizer.decode(ids,skip_special_tokens=True);elapsed=time.perf_counter()-start
   row={'id':c['id'],'kind':c['kind'],'prompt':c['prompt'],'rendered_prompt':rendered,'expected':c['expected'],'answer':answer,'seconds':elapsed,'input_tokens':inputs.input_ids.shape[1],'output_tokens':len(ids),'truncated':len(ids)>=4096,'cold_request':idx==0,'valid_json':False,'correct':False,'available_bytes':avail(),'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved()}
   try:row['final_answer']=answer.rsplit('</think>',1)[-1].strip();row['parsed']=json.loads(row['final_answer']);row['valid_json']=True;row['correct']=row['parsed']==c['expected']
   except ValueError:pass
   f.write(json.dumps(row)+'\n');f.flush();print(json.dumps({k:row[k] for k in ['id','correct','valid_json','seconds','truncated']}),flush=True)
 # Native tool integration is a separate experiment; this runner reproduces the twelve text cases.
 meta.update(peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(),available_end_bytes=avail());(a.output/'meta.json').write_text(json.dumps(meta,indent=2,default=lambda x:sorted(x) if isinstance(x,set) else str(x)))
if __name__=='__main__':main()
