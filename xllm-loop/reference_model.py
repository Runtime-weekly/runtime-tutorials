"""Local inference-only Part II S port. Not the official xLLM kernel backend.
Equations from pinned xllm sources; SDPA or explicit attention for qualification.
No training, model parallelism, learned stopping, quantization or fused kernels.
"""
import hashlib,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from safetensors.torch import load_file

class ReferenceModel:
    def __init__(self, path, device='cpu', dtype=torch.bfloat16, attention='sdpa'):
        self.path=Path(path); self.attention=attention
        manifest=json.loads((self.path/'artifact_manifest.json').read_text())
        for item in manifest['files']:
            p=self.path/item['path']
            if p.is_symlink() or p.stat().st_size!=item['size_bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError(f"Artifact integrity failure: {item['path']}")
        self.cfg=json.loads((self.path/'config.json').read_text())['model']
        required={'arch':'huginn','model_dim':1536,'num_layers':4,'num_heads':24,'num_kv_heads':6,'head_dim':64,'huginn_input_injection':'diagonal','huginn_prelude_norm':'none','huginn_recurrent_exit_norm':'none','qknorm':False,'scale_emb':False,'residual_func':'base','layernorm_num_groups':1,'apply_rmsnorm':True,'swiglu':True,'apply_attn_gate':False,'loop_start_layer':1,'loop_end_layers':3,'rope_head_dim':64,'huginn_prelude_layers':1,'huginn_recurrent_layers':2,'huginn_coda_layers':1,'huginn_hierarchical_state':'none'}
        for k,v in required.items():
            if self.cfg[k]!=v: raise ValueError(f'Unsupported config {k}')
        expected={'embed.weight':(64256,1536),'output.output.weight':(64256,1536),'output.final_norm.weight':(1536,), 'input_injection.A_log':(1536,), 'input_injection.dt_bias':(1536,), 'input_injection.input_adapter.weight':(1536,1536)}
        shapes={'attention.norm.weight':(1536,), 'attention.wq.weight':(1536,1536),'attention.wk.weight':(384,1536),'attention.wv.weight':(384,1536),'attention.wo.weight':(1536,1536),'nffn.norm.weight':(1536,),'nffn.fc1.weight':(4352,1536),'nffn.fc3.weight':(4352,1536),'nffn.fc2.weight':(1536,4352)}
        for i in range(4): expected.update({f'layers.{i}.{k}':v for k,v in shapes.items()})
        self.w={}
        index=json.loads((self.path/'model.safetensors.index.json').read_text())['weight_map']
        for shard in sorted(set(index.values())): self.w.update(load_file(self.path/shard))
        assert set(self.w)==set(expected), (set(self.w)-set(expected),set(expected)-set(self.w))
        for k,shape in expected.items(): assert tuple(self.w[k].shape)==shape,(k,self.w[k].shape,shape)
        self.coverage={'keys':len(self.w),'parameters':sum(v.numel() for v in self.w.values()),'unused_keys':[], 'manifest_verified':True}
        self.w={k:v.to(device=device,dtype=dtype) for k,v in self.w.items()}
        self.device=device; self.dtype=dtype
    def norm(self,x,key):
        # Upstream GroupRMSNorm stores zero-centered gamma; addition is in parameter dtype.
        weight=self.w[key]+1.0
        return (x.float()*torch.rsqrt(x.float().square().mean(-1,keepdim=True)+self.cfg['rmsnorm_eps'])*weight.float()).to(x.dtype)
    def linear(self,x,key): return F.linear(x,self.w[key])
    def rope(self,x,start):
        freqs=torch.tensor([self.cfg['rope_base']**(j/64) for j in range(0,64,2)],device=x.device,dtype=torch.float32).reciprocal()
        angles=torch.outer(torch.arange(start,start+x.shape[1],device=x.device,dtype=torch.float32),freqs)
        cis=torch.polar(torch.ones_like(angles),angles).unsqueeze(1)
        z=torch.view_as_complex(x.float().reshape(*x.shape[:-1],-1,2))
        return torch.view_as_real(z*cis).flatten(3).to(x.dtype)
    def block(self,x,layer,cache,start):
        p=f'layers.{layer}.'; z=self.norm(x,p+'attention.norm.weight')
        q=self.rope(self.linear(z,p+'attention.wq.weight').view(*z.shape[:2],24,64),start)
        k=self.rope(self.linear(z,p+'attention.wk.weight').view(*z.shape[:2],6,64),start)
        v=self.linear(z,p+'attention.wv.weight').view(*z.shape[:2],6,64)
        if cache is not None: k=torch.cat((cache[0],k),1); v=torch.cat((cache[1],v),1)
        new=(k,v); kt=k.repeat_interleave(4,2).transpose(1,2); vt=v.repeat_interleave(4,2).transpose(1,2); qt=q.transpose(1,2)
        mask=torch.arange(k.shape[1],device=x.device)[None,:] <= (start+torch.arange(x.shape[1],device=x.device))[:,None]
        if self.attention=='sdpa': y=F.scaled_dot_product_attention(qt,kt,vt,attn_mask=mask,dropout_p=0.0)
        elif self.attention=='explicit':
            score=(qt @ kt.transpose(-1,-2))*(1/math.sqrt(64)); score=score.masked_fill(~mask,float('-inf'))
            y=score.softmax(-1,dtype=torch.float32).to(qt.dtype) @ vt
        else: raise ValueError(self.attention)
        x=x+self.linear(y.transpose(1,2).contiguous().flatten(2),p+'attention.wo.weight')
        z=self.norm(x,p+'nffn.norm.weight')
        return x+self.linear(F.silu(self.linear(z,p+'nffn.fc1.weight'))*self.linear(z,p+'nffn.fc3.weight'),p+'nffn.fc2.weight'),new
    def identity_state(self,emb,start,ids,seed):
        mod=16777213; ids=ids.to(device=emb.device,dtype=torch.long).remainder(mod)
        phase=((ids*104729+(seed%mod)*130363).remainder(mod)).float().mul_(2*math.pi/mod).view(-1,1,1)
        dim=torch.arange(emb.shape[-1],device=emb.device,dtype=torch.float32).view(1,1,-1)
        pos=torch.arange(start,start+emb.shape[1],device=emb.device,dtype=torch.float32).view(1,-1,1)
        state=dim.expand_as(emb).clone(); state.mul_(.013579); state.add_(pos*.021713); state.add_(phase); state.add_(.123457); state.sin_(); state.mul_(43758.5453123); state.sub_(state.floor()); state.clamp_(1e-6,1-1e-6); state.mul_(2).sub_(1); state.erfinv_(); state.mul_(math.sqrt(2)/math.sqrt(1536))
        return state.to(emb.dtype)
    @torch.inference_mode()
    def forward(self,tokens,mode='terminal',cache=None,ids=None,seed=42,depth=5,full_logits=False):
        if mode not in ('terminal','full'): raise ValueError(mode)
        banks=4 if mode=='terminal' else 2+2*depth
        cache=[None]*banks if cache is None else list(cache)
        assert len(cache)==banks
        start=0 if cache[0] is None else cache[0][0].shape[1]
        ids=torch.arange(tokens.shape[0],device=tokens.device) if ids is None else ids
        x=F.embedding(tokens,self.w['embed.weight']); x,cache[0]=self.block(x,0,cache[0],start)
        emb=x; x=self.identity_state(emb,start,ids,seed)
        dt=F.softplus(self.w['input_injection.dt_bias']).to(x.dtype); rate=self.w['input_injection.A_log'].exp().to(x.dtype); decay=(-dt*rate).exp()
        # Compute each iteration exactly as upstream (do not change rounding/order).
        for step in range(depth):
            x=x*decay+dt*self.linear(emb,'input_injection.input_adapter.weight')
            for layer in (1,2):
                slot=layer if mode=='terminal' else 1+2*step+layer-1
                x,updated=self.block(x,layer,cache[slot],start)
                if mode=='full' or step==depth-1: cache[slot]=updated
        x,cache[-1]=self.block(x,3,cache[-1],start)
        if not full_logits:x=x[:,-1:]
        return self.linear(self.norm(x,'output.final_norm.weight'),'output.output.weight').float(),cache

def cache_bytes(cache): return sum(t.numel()*t.element_size() for pair in cache if pair is not None for t in pair)
