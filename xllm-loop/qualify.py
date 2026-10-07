import ast,json,math,time,types
from pathlib import Path
import torch
from reference_model import ReferenceModel,cache_bytes

def native_method(name):
    tree=ast.parse(Path('source/xllm/models/looped.py').read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
    node.decorator_list=[]
    for arg in node.args.args:arg.annotation=None
    node.returns=None
    ns={'torch':torch,'math':math,'get_model_parallel_rank':lambda:0}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'native_ast','exec'),ns)
    return ns[name]

def main():
    torch.set_num_threads(3)
    m=ReferenceModel('checkpoints/learned-s',dtype=torch.float32)
    tokens=torch.tensor([[1,100,200,300,400,500,600,700]])
    native=types.SimpleNamespace(model_dim=1536)
    native._hashed_normal_state=types.MethodType(native_method('_hashed_normal_state'),native)
    native.identity_recurrent_state=types.MethodType(native_method('identity_recurrent_state'),native)
    emb=torch.zeros(1,3,1536); ids=torch.tensor([19])
    assert torch.equal(m.identity_state(emb,7,ids,42),native.identity_recurrent_state(emb,7,ids,42))
    checks=[]
    for depth in (1,5):
        whole,_=m.forward(tokens,'full',depth=depth)
        _,cache=m.forward(tokens[:,:-1],'full',depth=depth)
        split,cache=m.forward(tokens[:,-1:],'full',cache,depth=depth)
        diff=(whole-split).abs().max().item()
        assert torch.allclose(whole,split,atol=3e-4,rtol=3e-4),diff
        checks.append({'name':f'full_cache_vs_recompute_depth{depth}','max_absolute_difference':diff})
    a,ca=m.forward(tokens[:,:-1],'full',depth=1); b,cb=m.forward(tokens[:,:-1],'terminal',depth=1)
    a,ca=m.forward(tokens[:,-1:],'full',ca,depth=1); b,cb=m.forward(tokens[:,-1:],'terminal',cb,depth=1)
    assert torch.equal(a,b)
    sdpa,_=m.forward(tokens,'terminal');m.attention='explicit';explicit,_=m.forward(tokens,'terminal')
    diff=(sdpa-explicit).abs().max().item();assert torch.allclose(sdpa,explicit,atol=3e-4,rtol=3e-4),diff
    checks.append({'name':'SDPA_vs_explicit_FP32','max_absolute_difference':diff})
    _,full=m.forward(tokens,'full');_,terminal=m.forward(tokens,'terminal')
    assert cache_bytes(full)==3*cache_bytes(terminal)
    result={'status':'passed','scope':'CPU FP32 mathematical controls, not official fused-kernel equivalence','coverage':m.coverage,'identity_state_original_AST_exact':True,'R1_cache_modes_exact':True,'cache_bytes':{'full':cache_bytes(full),'terminal':cache_bytes(terminal)},'checks':checks}
    Path('qualification-cpu.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
