"""Download only the pinned English checkpoint, not all Laya variants."""
import hashlib,json
from pathlib import Path
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parent
REPO='convaiinnovations/laya'
REVISION='1c5edc17a7acd8701df6fc341c0d179f1c62c982'
MODEL_DIR=ROOT/'models/laya-english'
if __name__=='__main__':
 snapshot_download(REPO,revision=REVISION,local_dir=MODEL_DIR,allow_patterns=['model.safetensors','rl_agent_config.json','encoder/*','tokenizer/*'])
 files=[]
 for p in sorted(MODEL_DIR.rglob('*')):
  if not p.is_file() or '.cache' in p.parts:continue
  with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  files.append({'path':str(p.relative_to(MODEL_DIR)),'bytes':p.stat().st_size,'sha256':digest})
 receipt={'repo':REPO,'revision':REVISION,'files':files,'total_bytes':sum(x['bytes'] for x in files)}
 (ROOT/'download-receipt.json').write_text(json.dumps(receipt,indent=2))
 print('English checkpoint ready:',MODEL_DIR)
 print('Downloaded model files:',receipt['total_bytes'],'bytes')
