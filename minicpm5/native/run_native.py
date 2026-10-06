import argparse,hashlib,json,time,resource,xml.etree.ElementTree as ET
from pathlib import Path
from native_tools import TOOLS,parse
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('model',choices=['1b','2b']);p.add_argument('--no-thinking',action='store_true');p.add_argument('--output',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args();assert not(a.model=='2b' and a.no_thinking)
manifest=json.loads((D/'checkpoint-manifest.json').read_text())[a.model]
for name,expected in manifest['files'].items():
 path=a.model_dir/name
 assert path.is_file() and path.stat().st_size==expected['size'],f'Checkpoint file missing/size mismatch: {name}'
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
 assert digest.hexdigest()==expected['sha256'],f'Checkpoint hash mismatch: {name}'
a.output.mkdir(exist_ok=False);spec=json.loads((D/'tool_demo.frozen.json').read_text())
import torch,transformers
from transformers import AutoModelForCausalLM,AutoTokenizer
torch.set_num_threads(3);torch.manual_seed(510);start=time.perf_counter();tok=AutoTokenizer.from_pretrained(a.model_dir,local_files_only=True);model,info=AutoModelForCausalLM.from_pretrained(a.model_dir,local_files_only=True,dtype=torch.bfloat16,device_map='cuda',attn_implementation='sdpa',output_loading_info=True);model.eval();torch.cuda.synchronize();load=time.perf_counter()-start
assert not any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs'])
question='Find the current posted invoice amount for order ORD-72 using the available read-only tools. Follow replacement references returned by a superseded invoice. Once you have evidence, return only a JSON object with order_id, amount_cents and status. Do not modify records.'
messages=[{'role':'user','content':question}];records=[];executed=[];final=None;temp=.7 if a.no_thinking else (.9 if a.model=='1b' else 1.0)
for turn in range(6):
 rendered=tok.apply_chat_template(messages,tools=TOOLS,tokenize=False,add_generation_prompt=True,enable_thinking=not a.no_thinking);inputs=tok(rendered,return_tensors='pt',add_special_tokens=False).to('cuda');official=tok.apply_chat_template(messages,tools=TOOLS,tokenize=True,return_dict=True,add_generation_prompt=True,enable_thinking=not a.no_thinking)['input_ids'];assert inputs.input_ids[0].tolist()==official
 start=time.perf_counter()
 with torch.inference_mode():ids=model.generate(**inputs,max_new_tokens=4096,do_sample=True,temperature=temp,top_p=.95,pad_token_id=1)[0,inputs.input_ids.shape[1]:]
 torch.cuda.synchronize();seconds=time.perf_counter()-start;tokens=ids.tolist();raw=tok.decode(tokens,skip_special_tokens=False);cleanids=list(tokens);eos=model.generation_config.eos_token_id;eos=eos if isinstance(eos,list) else [eos]
 while cleanids and cleanids[-1] in eos:cleanids.pop()
 text=tok.decode(cleanids,skip_special_tokens=False);answer=text.rsplit('</think>',1)[-1].strip();reasoning=text.rsplit('</think>',1)[0].removeprefix('<think>') if '</think>' in text else '';record={'turn':turn,'request_messages':list(messages),'tools':TOOLS,'rendered_prompt':rendered,'input_ids':official,'output_ids':tokens,'raw_output':raw,'answer':answer,'reasoning_content':reasoning,'seconds':seconds,'truncated':len(tokens)>=4096};records.append(record)
 if (not a.no_thinking and '</think>' not in text) or len(tokens)>=4096:
  record['incomplete_generation_no_tools_executed']=True;break
 try:
  calls=parse(answer)
  if not calls:
   record['final_candidate']=answer
   try:final=json.loads(answer)
   except ValueError:record['final_parse_error']='Final answer is not strict JSON'
   break
  replay=[];feedback=[]
  for index,c in enumerate(calls):
   c['id']=f'call-{turn}-{index}';name=c['function']['name'];args=c['function']['arguments'];key=next(iter(args.values()));result=spec['tools'][name].get(key,{'error':'not_found'});executed.append([name,key]);feedback.append({'role':'tool','tool_call_id':c['id'],'content':json.dumps(result)});replay.append(c)
  record['executed_calls']=replay;record['tool_results']=feedback;messages.append({'role':'assistant','content':'','reasoning_content':reasoning,'tool_calls':replay});messages.extend(feedback)
 except (ValueError,ET.ParseError):
  record['adapter_error']='Rejected XML envelope';messages.extend([{'role':'assistant','content':answer,'reasoning_content':reasoning},{'role':'user','content':'The tool call could not be parsed. Use the supplied tool schema.'}])
 (a.output/f'turn-{turn:02}.json').write_text(json.dumps(record,indent=2))
required=iter(spec['required_calls']);want=next(required,None)
for call in executed:
 if call==want:want=next(required,None)
receipt={'revision':{'1b':'87179e5c1f455ef22e6223592d2d61351b525bfc','2b':'f97400052a43d642bbc6e9975e2397e3ae6a6b52'}[a.model],'checkpoint_verified':True,'fixture_sha256':hashlib.sha256((D/'tool_demo.frozen.json').read_bytes()).hexdigest(),'model':a.model,'thinking':not a.no_thinking,'temperature':temp,'top_p':.95,'seed':510,'load_seconds':load,'torch':torch.__version__,'transformers':transformers.__version__,'tools':TOOLS,'prompt':question,'executed_calls':executed,'required_ordered_calls_completed':want is None,'final':final,'expected':spec['expected_final'],'correct_final':final==spec['expected_final'],'success':want is None and final==spec['expected_final'],'turns':records,'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256((D/'native_tools.py').read_bytes()).hexdigest(),'scope':'Native template tools and XML retained; actual deterministic read-only synthetic Python tools. Six turns maximum, one attempt; no shared services changed.'}
(a.output/'result.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:receipt[k] for k in ['model','thinking','success','executed_calls','final']}),flush=True)
