#!/usr/bin/env python3
"""Small reproducible agent pilot; never executes generated shell on the host."""
import argparse,csv,hashlib,json,os,re,subprocess,time,urllib.request
from pathlib import Path
DATA_ROOT=Path(__file__).resolve().parent
ROOT=DATA_ROOT
ENDPOINT="http://127.0.0.1:18593"
IMAGE="runtime-ornith-replay:local"
SYSTEM='You are a coding agent working in /workspace. Inspect files, complete the requested task, and verify your changes. Use the provided shell tool. Do not change unrelated files. Finish with a short factual summary.'
TOOL={'type':'function','function':{'name':'shell','description':'Run a shell command inside the isolated task workspace. Python 3, Node.js 22 and basic shell tools are available.','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command'],'additionalProperties':False}}}
def command(args,**kw):return subprocess.run(args,capture_output=True,text=True,**kw)
def snapshot(p):
    result={}
    for f in p.rglob('*'):
        if f.is_symlink():raise ValueError('Generated symlinks are not followed by host snapshot')
        if f.is_file() and '__pycache__' not in f.parts:
            digest=hashlib.sha256()
            with f.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
            result[str(f.relative_to(p))]=digest.hexdigest()
    return result
def request(payload):
    start=time.monotonic();first=None;chunks=[];content='';reasoning='';calls={};usage={};timings={};finish=None
    payload.update(stream=True,stream_options={'include_usage':True})
    req=urllib.request.Request(ENDPOINT+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=240) as r:
        for line in r:
            if not line.startswith(b'data: '):continue
            raw=line[6:].strip()
            if raw==b'[DONE]':break
            x=json.loads(raw);chunks.append(x)
            if x.get('usage'):usage=x['usage']
            if x.get('timings'):timings=x['timings']
            for choice in x.get('choices',[]):
                d=choice.get('delta',{})
                if any(d.get(k) for k in ('content','reasoning_content','tool_calls')) and first is None:first=time.monotonic()-start
                content+=d.get('content') or '';reasoning+=d.get('reasoning_content') or ''
                for t in d.get('tool_calls',[]):
                    c=calls.setdefault(t['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
                    if t.get('id'):c['id']=t['id']
                    for k,v in t.get('function',{}).items():c['function'][k]+=v or ''
                finish=choice.get('finish_reason') or finish
    msg={'role':'assistant','content':content}
    if reasoning:msg['reasoning_content']=reasoning
    if calls:msg['tool_calls']=list(calls.values())
    return msg,dict(seconds=time.monotonic()-start,ttft=first,usage=usage,timings=timings,finish_reason=finish,chunks=chunks)
def run(model,task,repeat,path):
    out=ROOT/'runs'/f'{model}-{task["id"]}-{path}-{repeat}'
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True,exist_ok=False);work=out/'workspace';work.mkdir()
    for name,body in task['files'].items():
        p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    before=snapshot(work);name='runtime-ornith-'+hashlib.sha256(str(out).encode()).hexdigest()[:12]
    image=IMAGE
    cmd=['docker','run','--pull=never','-d','--name',name,'--network','none','--memory','512m','--cpus','1','--pids-limit','64','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp','--user',f'{os.getuid()}:{os.getgid()}','--mount',f'type=bind,source={work},target=/workspace','-w','/workspace','-e','PYTHONDONTWRITEBYTECODE=1',image,'sleep','1800']
    r=command(cmd);assert r.returncode==0,r.stderr
    extra='' if path=='native' else '\nTool transport: reply with exactly one JSON object: {"tool":"shell","command":"..."} to use the same shell tool, or {"final":"summary"} when finished. No markdown fences.'
    messages=[{'role':'system','content':SYSTEM+extra},{'role':'user','content':task['prompt']}]
    result=dict(model=model,task=task['id'],repeat=repeat,path=path,success=False,valid_calls=0,invalid_calls=0,repeated_commands=0,empty_final=False,reasoning_leak=False,crash=None,retries=0,calls=0,generated_tokens=0,max_prompt_tokens=0)
    seen=set();metrics=[];start=time.monotonic();error=None
    try:
        for turn in range(12):
            if time.monotonic()-start>900:raise TimeoutError('task wall budget 900 seconds')
            remaining=16384-result['generated_tokens']
            if remaining<=0:raise TimeoutError('task output budget 16384 tokens')
            payload=dict(model=model,messages=messages,max_tokens=min(8192,remaining),temperature=.6,top_p=.95,seed=2309+repeat,cache_prompt=False,chat_template_kwargs={'enable_thinking':True})
            if path=='native':payload.update(tools=[TOOL],tool_choice='auto')
            msg,m=request(payload);metrics.append(m);result['calls']+=1
            usage=m.get('usage',{});result['generated_tokens']+=usage.get('completion_tokens',0);result['max_prompt_tokens']=max(result['max_prompt_tokens'],usage.get('prompt_tokens',0))
            (out/f'turn-{turn:02d}.json').write_text(json.dumps({'request':payload,'response':msg,'metrics':m},indent=2))
            result['reasoning_leak'] |= '<think>' in (msg.get('content') or '') or '</think>' in (msg.get('content') or '')
            messages.append(msg)
            if path=='native':calls=msg.get('tool_calls',[])
            else:
                try:
                    x=json.loads(msg.get('content') or '')
                    if 'final' in x:calls=[]
                    elif x.get('tool')=='shell':calls=[{'id':f'call-{turn}','function':{'name':'shell','arguments':json.dumps({'command':x['command']})}}]
                    else:raise ValueError('Expected shell or final object')
                except (ValueError,KeyError) as e:
                    result['invalid_calls']+=1;messages.append({'role':'user','content':f'Invalid tool envelope: {e}. Return the required JSON object.'});continue
            if not calls:
                result['empty_final']=not bool((msg.get('content') or '').strip())
                result['final']=msg.get('content') or ''
                if m['finish_reason']=='length':error='output truncated before tool/final'
                break
            for call in calls:
                try:
                    f=call['function'];a=json.loads(f['arguments']);assert f['name']=='shell' and isinstance(a.get('command'),str)
                    cmdtext=a['command'];result['valid_calls']+=1;result['repeated_commands']+=int(cmdtext in seen);seen.add(cmdtext)
                    r=(subprocess.CompletedProcess([],75,'','Injected transient shell transport failure; no command executed. Retry or inspect safely.') if task.get('inject_first_tool_error') and result['valid_calls']==1 else command(['docker','exec',name,'sh','-c',cmdtext],timeout=25))
                    feedback=json.dumps(dict(returncode=r.returncode,stdout=r.stdout[:14000],stderr=r.stderr[:4000]))
                except Exception as e:result['invalid_calls']+=1;feedback=str(e)
                messages.append({'role':'tool','tool_call_id':call['id'],'content':feedback} if path=='native' else {'role':'user','content':'Tool result: '+feedback})
        else:error='tool turn budget exhausted'
        # Hidden evaluator is sent only after the agent has stopped; never present in its filesystem.
        r=command(['docker','exec','-i',name,'python3','-'],input=task['check'],timeout=30)
        (out/'hidden-result.json').write_text(json.dumps(dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2))
        after=snapshot(work);changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
        result.update(changed=changed,unintended_edits=[k for k in changed if k not in task['allowed']],hidden_pass=r.returncode==0)
        result['success']=r.returncode==0 and not result['unintended_edits']
    except Exception as e:result['crash']=type(e).__name__+': '+str(e)
    finally:command(['docker','rm','-f',name],timeout=20)
    result.update(seconds=time.monotonic()-start,budget_failure=error,ttft_seconds=[m['ttft'] for m in metrics],generation_timings=[m['timings'] for m in metrics])
    (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result.get(k) for k in ['model','task','path','repeat','success','seconds','crash','budget_failure']}),flush=True)
    return result
def main():
    global ROOT,ENDPOINT,IMAGE
    from urllib.parse import urlparse
    p=argparse.ArgumentParser();p.add_argument('--model-label',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--endpoint',default=ENDPOINT);p.add_argument('--image',default=IMAGE);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:p.error('--execute is required: this requests local model inference and executes generated commands inside Docker')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.model_label):p.error('Use a simple model alias')
    u=urlparse(a.endpoint)
    if u.scheme!='http' or u.hostname not in ['127.0.0.1','localhost','::1'] or u.username or u.password or u.path not in ['', '/']:p.error('Endpoint must be an unauthenticated loopback HTTP model server')
    b=(DATA_ROOT/'tasks.frozen.json').read_bytes();assert hashlib.sha256(b).hexdigest()==(DATA_ROOT/'tasks-checksum.txt').read_text().split()[0]
    tasks=json.loads(b);ROOT=a.output.resolve();ROOT.mkdir(exist_ok=False);ENDPOINT=a.endpoint.rstrip('/');IMAGE=a.image
    (ROOT/'invocation.json').write_text(json.dumps({'model_alias':a.model_label,'identity_scope':'User-supplied alias, not independently verified checkpoint identity. Verify model SHA separately.','task_sha256':hashlib.sha256(b).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'image':IMAGE},indent=2))
    for task in tasks:run(a.model_label,task,1,'native')
if __name__=='__main__':main()
