#!/usr/bin/env python3
"""Optional local BF16 rerun. Patched runtime required; new inference NOT requalified for this export."""
import argparse,json,hashlib,time,os,threading,resource,statistics,random
from pathlib import Path
from download import MODELS
ROOT=Path(__file__).resolve().parent
def available():
 p=Path('/proc/meminfo')
 if not p.exists():raise RuntimeError('Resource guard requires Linux; other platforms unqualified')
 return int(next(x.split()[1] for x in p.read_text().splitlines() if x.startswith('MemAvailable:')))*1024

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',choices=MODELS);p.add_argument('--model-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError('Use a NEW output directory; prior results will not be overwritten')
 if available()<16*1024**3:raise RuntimeError('Need at least16GiB MemAvailable; do not unload another workload automatically')
 manifest=next(x for x in json.loads((ROOT/'data/model-files.json').read_text()) if x['model']==a.model)
 for entry in manifest['files']:
  file=a.model_dir/entry['relative_path'];digest=hashlib.sha256()
  with file.open('rb') as stream:
   for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
  if digest.hexdigest()!=entry['sha256']:raise RuntimeError('Pinned checkpoint checksum mismatch: '+entry['relative_path'])
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
 import torch,transformers
 from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration
 from packaging.version import Version
 if Version(torch.__version__.split('+')[0])<Version('2.13.0'):raise RuntimeError('Torch>=2.13.0 required: historical2.11 measurement version has GHSA-rrmf-rvhw-rf47')
 if not torch.cuda.is_available():raise RuntimeError('CUDA required; no silent CPU fallback')
 a.output.mkdir(parents=True,exist_ok=False);minimum=available();stop=threading.Event()
 def guard():
  nonlocal minimum
  while not stop.wait(.5):
   value=available();minimum=min(minimum,value)
   if value<8*1024**3:
    (a.output/'resource-abort.json').write_text(json.dumps({'reason':'Available host memory below8GiB'}));os._exit(78)
 threading.Thread(target=guard,daemon=True).start();torch.set_num_threads(3);torch.set_num_interop_threads(1);torch.manual_seed(260926)
 cases=json.loads((ROOT/'data/cases.json').read_text())+json.loads((ROOT/'data/supplemental-attacks.json').read_text());random.Random(91026).shuffle(cases)
 for filename,digest in json.loads((ROOT/'data/frozen-inputs.json').read_text()).items():assert hashlib.sha256((ROOT/'data'/filename).read_bytes()).hexdigest()==digest
 t=time.perf_counter();tok=AutoTokenizer.from_pretrained(a.model_dir,local_files_only=True,trust_remote_code=False);model,info=Qwen3_5ForConditionalGeneration.from_pretrained(a.model_dir,dtype=torch.bfloat16,device_map='cuda:0',attn_implementation='sdpa',local_files_only=True,trust_remote_code=False,output_loading_info=True);torch.cuda.synchronize();load=time.perf_counter()-t
 if any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']):raise RuntimeError('Incomplete checkpoint load: '+str(info))
 model.eval()
 def call(system,user):
  torch.cuda.synchronize();start=time.perf_counter();prompt=tok.apply_chat_template([{'role':'system','content':system},{'role':'user','content':user}],tokenize=False,add_generation_prompt=True,enable_thinking=False);inputs=tok(prompt,return_tensors='pt',add_special_tokens=False).to('cuda');n=inputs.input_ids.shape[1]
  with torch.inference_mode():output=model.generate(**inputs,max_new_tokens=8,do_sample=False,use_cache=True)
  torch.cuda.synchronize();response=tok.decode(output[0,n:],skip_special_tokens=True);seconds=time.perf_counter()-start
  return {'response':response,'elapsed_seconds':seconds,'input_tokens':n,'generated_token_ids':output[0,n:].tolist(),'rendered_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
 warm=[call('Return only the letter of the correct option.','Choose the color of a clear daytime sky: A. Blue B. Orange') for _ in range(3)];(a.output/'warmup.json').write_text(json.dumps(warm,indent=2))
 with (a.output/'results.jsonl').open('w') as f:
  for c in cases:
   row={'model':a.model,'id':c['id'],**call(c['system'],c['user_prompt'])};row['correct']=row['response'].strip()==c['expected'];f.write(json.dumps(row)+'\n');f.flush()
 repeats=[]
 for repeat in range(3):
  for id in ['R01','R10','R20','R28','P01','P10','P20','P28','A01','A10','A20','A28']:
   c=next(x for x in cases if x['id']==id);repeats.append({'id':id,'repeat':repeat+1,**call(c['system'],c['user_prompt'])})
 (a.output/'latency-repeats.json').write_text(json.dumps(repeats,indent=2));stop.set();repo,rev=MODELS[a.model]
 (a.output/'run.json').write_text(json.dumps({'model_id':repo,'revision':rev,'checkpoint_files_sha256_verified':True,'note':'All pinned exported model-file digests verified before loading. Patched-runtime run is separate from historical evidence.','torch':torch.__version__,'transformers':transformers.__version__,'gpu':torch.cuda.get_device_name(0),'load_seconds':load,'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'host_min_available_bytes':minimum},indent=2))
if __name__=='__main__':main()
