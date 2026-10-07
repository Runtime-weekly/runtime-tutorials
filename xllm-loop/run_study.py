import argparse,hashlib,json,os,platform,statistics,threading,time
from pathlib import Path
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer
from reference_model import ReferenceModel,cache_bytes

def available():
    return int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024

def save(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--out',required=True);ap.add_argument('--study',default='study.json');args=ap.parse_args()
    if not args.execute:raise SystemExit('Use --execute')
    out=Path(args.out);out.mkdir(exist_ok=False)
    study_path=Path(args.study); study=json.loads(study_path.read_text());assert hashlib.sha256(study_path.read_bytes()).hexdigest()==study_path.with_name(study_path.stem+'-sha256.txt').read_text().strip()
    if available()<20*1024**3:raise SystemExit('Resource admission below20GiB')
    torch.set_num_threads(3);torch.backends.cuda.matmul.allow_tf32=False
    stop=threading.Event();samples=[]
    def monitor():
        with (out/'memory.jsonl').open('w') as f:
            while not stop.is_set():
                row={'time':time.time(),'available_bytes':available()};samples.append(row);f.write(json.dumps(row)+'\n');f.flush()
                if row['available_bytes']<12*1024**3:
                    save(out/'aborted.json',{'reason':'available_memory_below12GiB','sample':row});os._exit(73)
                stop.wait(.5)
    threading.Thread(target=monitor,daemon=True).start()
    tok=Tokenizer.from_file('checkpoints/learned-s/tokenizer/tokenizer.json')
    rows=[];times=[];smokes=[]
    sync=torch.cuda.synchronize
    def prefill(m,tokens,mode):
        _,cache=m.forward(tokens[:,:-1],mode);return m.forward(tokens[:,-1:],mode,cache)
    for model in ('learned-s','fixed-s'):
        save(out/'progress.json',{'phase':'loading','model':model})
        start=time.perf_counter();m=ReferenceModel('checkpoints/'+model,device='cuda');sync();load=time.perf_counter()-start
        tokens=torch.tensor([[1,100,200,300,400,500,600,700]],device='cuda')
        a,ca=prefill(m,tokens,'full');b,cb=m.forward(tokens,'full')
        difference=(a-b).abs().max().item(); assert torch.isfinite(a).all()
        # BF16 cached/full-prefix reductions are not bit-identical; record, don't silently replace results.
        r1a,c=m.forward(tokens[:,:-1],'full',depth=1);r1a,c=m.forward(tokens[:,-1:],'full',c,depth=1)
        r1b,c=m.forward(tokens[:,:-1],'terminal',depth=1);r1b,c=m.forward(tokens[:,-1:],'terminal',c,depth=1)
        assert torch.equal(r1a,r1b)
        smokes.append({'model':model,'load_seconds':load,'coverage':m.coverage,'BF16_full_prefix_vs_cached_max_abs':difference,'BF16_R1_exact':True})
        save(out/'smokes.json',smokes)
        del a,b,ca,cb,r1a,r1b,c
        for case in study['cases']:
            ids=case['tokens'];n=case['prefix_tokens'];count=case['score_tokens']
            for mode in ('full','terminal'):
                save(out/'progress.json',{'phase':'continuation','model':model,'case':case['id'],'mode':mode})
                cache=None;logits=None;torch.cuda.reset_peak_memory_stats();sync();start=time.perf_counter()
                logits,cache=prefill(m,torch.tensor([ids[:n]],device='cuda'),mode);loss=[];pred=[]
                for j in range(count):
                    pred.append(int(logits[0,-1].argmax()));loss.append(float(F.cross_entropy(logits[0,-1:].float(),torch.tensor([ids[n+j]],device='cuda'))))
                    if j+1<count:logits,cache=m.forward(torch.tensor([[ids[n+j]]],device='cuda'),mode,cache)
                sync();elapsed=time.perf_counter()-start
                row={'model':model,'case':case['id'],'mode':mode,'prefix_tokens':ids[:n],'target_tokens':ids[n:n+count],'predicted_tokens':pred,'token_nll':loss,'mean_nll':statistics.mean(loss),'scored_tokens':count,'elapsed_seconds':elapsed,'retained_kv_bytes':cache_bytes(cache),'torch_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'torch_peak_reserved_bytes':torch.cuda.max_memory_reserved()}
                logits,cache=prefill(m,torch.tensor([ids[:n]],device='cuda'),mode);generated=[]
                for j in range(case['generated_token_limit']):
                    token=int(logits[0,-1].argmax());generated.append(token)
                    if j+1<case['generated_token_limit']:logits,cache=m.forward(torch.tensor([[token]],device='cuda'),mode,cache)
                row.update(generated_tokens=generated,generated_text=tok.decode(generated),prompt_text=tok.decode(ids[:n]))
                rows.append(row);save(out/'continuations.json',rows)
        for length in study['timing']['prefix_lengths']:
            base=study['cases'][0]['tokens'];tokens=torch.tensor([(base*(length//len(base)+1))[:length]],device='cuda')
            for rep in range(-1,3):
                for mode in (('full','terminal') if rep%2==0 else ('terminal','full')):
                    save(out/'progress.json',{'phase':'timing','model':model,'prefix':length,'repetition':rep,'mode':mode})
                    cache=None;logits=None;torch.cuda.reset_peak_memory_stats();sync();start=time.perf_counter();logits,cache=prefill(m,tokens,mode);sync();pre=time.perf_counter()-start
                    start=time.perf_counter()
                    for j in range(32):logits,cache=m.forward(logits[:,-1].argmax(-1,keepdim=True),mode,cache)
                    sync();dec=time.perf_counter()-start
                    item={'model':model,'prefix_length':length,'mode':mode,'rep':rep,'warmup':rep<0,'prefill_seconds':pre,'decode32_seconds':dec,'retained_kv_bytes':cache_bytes(cache),'torch_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'torch_peak_reserved_bytes':torch.cuda.max_memory_reserved()}
                    times.append(item);save(out/'timings.json',times)
        del m,cache,logits;torch.cuda.empty_cache()
    stop.set()
    save(out/'qualification.json',{'status':'completed','smokes':smokes,'torch':torch.__version__,'device':torch.cuda.get_device_name(),'platform':platform.platform(),'dtype':'BF16','backend':'custom source-faithful PyTorch SDPA port','min_host_available_bytes':min(x['available_bytes'] for x in samples),'study_sha256':hashlib.sha256(study_path.read_bytes()).hexdigest(),'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['reference_model.py','qualify.py','run_study.py']},'limitations':['No official fused-backend numerical equivalence established','Whole-host available memory overlaps unrelated workloads','Batch1 short-context synthetic timings are not paper H200 batch8/8192 benchmark','KV payload excludes GQA temporaries and allocator overhead','Three authored passages are illustrative, not representative benchmark']})
    save(out/'progress.json',{'phase':'completed','continuation_rows':len(rows),'timing_rows':len(times)})
if __name__=='__main__':main()
