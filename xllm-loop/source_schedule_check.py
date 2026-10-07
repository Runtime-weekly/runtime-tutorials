"""Execute the pinned upstream terminal method AST against port block interface."""
import json,types
from pathlib import Path
import torch
import torch.nn.functional as F
from qualify import native_method
from reference_model import ReferenceModel

def main():
 torch.set_num_threads(3);m=ReferenceModel('checkpoints/learned-s',dtype=torch.float32)
 class Layer:
  def __init__(self,i):self.i=i
  def __call__(self,x,freq,segments,cache=None,**kwargs):
   old=None if cache is None or cache[0] is None else cache[:2]
   y,c=m.block(x,self.i,old,freq)
   return y,None,None if cache is None else (*c,freq+x.shape[1])
 native=types.SimpleNamespace(training=False,context_parallel_size=1,num_layers=4,loop_start_layer=1,loop_end_layers=3,loop_times=5,huginn_recurrent_exit_norm_module=None)
 native.embed=lambda tokens:F.embedding(tokens,m.w['embed.weight'])
 native.rope=types.SimpleNamespace(get_freqs_cis=lambda start,end,device:start)
 native.layers=[Layer(i) for i in range(4)];native._recurrence_input=lambda x:x
 native.identity_recurrent_state=m.identity_state
 def injection(x,emb):
  dt=F.softplus(m.w['input_injection.dt_bias']);a=m.w['input_injection.A_log'].exp()
  return x*(-dt*a).exp()+dt*m.linear(emb,'input_injection.input_adapter.weight')
 native.input_injection=injection
 native.output=lambda x,*args:m.linear(m.norm(x,'output.final_norm.weight'),'output.output.weight').float()
 native.terminal_kv_forward=types.MethodType(native_method('terminal_kv_forward'),native)
 tokens=torch.tensor([[1,43,22,781,19]]);ids=torch.tensor([0]);a=ca=None;b=cb=None
 for chunk in (tokens[:,:3],tokens[:,3:4],tokens[:,4:]):
  a,ca=native.terminal_kv_forward(chunk,ids,42,ca)
  b,cb=m.forward(chunk,'terminal',cb,ids)
  assert torch.equal(a,b),(a-b).abs().max().item()
  for x,y in zip(ca,cb):assert torch.equal(x[0],y[0]) and torch.equal(x[1],y[1])
 Path('qualification-source-schedule.json').write_text(json.dumps({'passed':True,'scope':'Pinned original terminal_kv_forward AST executed with port blocks; exact logits and cache values across3 chunks, FP32 CPU. This validates schedule, not fused kernels.'},indent=2)+'\n')
if __name__=='__main__':main()
