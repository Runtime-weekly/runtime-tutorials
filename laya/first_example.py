"""First result: load the downloaded English model on CPU and classify a message."""
import json,os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
import torch,laya
from download_model import MODEL_DIR
torch.set_num_threads(3)
agent=laya.load(str(MODEL_DIR),device='cpu')
questions={'department':{
 'type':'choice',
 'instructions':'Which team should handle this message?',
 'criteria':{
  'billing':'payments, duplicate charges, refunds',
  'technical':'software errors, bugs, login problems',
  'sales':'pricing or buying the product',
  'other':'unclear request or none of these',
 }}}
result=agent.system_one('I was charged twice. Please refund the duplicate payment.',questions)
print(json.dumps(result['answers']['department'],indent=2))
