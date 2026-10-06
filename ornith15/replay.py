"""Extract exact generated artifacts and optionally check in an offline Docker sandbox."""
import argparse,hashlib,json,os,subprocess,tempfile,uuid
from pathlib import Path
D=Path(__file__).resolve().parent
def extract(record,destination):
 destination.mkdir(exist_ok=False)
 for name,item in record['files'].items():
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe artifact path')
  data=item['text'].encode();assert hashlib.sha256(data).hexdigest()==item['sha256'],name
  p=destination/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run');p.add_argument('--output',type=Path);p.add_argument('--check',choices=['frozen','prompt-faithful','boundary']);p.add_argument('--image',default='runtime-ornith-replay:local');p.add_argument('--execute',action='store_true');a=p.parse_args()
 records=json.loads((D/'saved-artifacts.json').read_text())
 if not a.run:
  print('\n'.join(r['run'] for r in records));return
 record=next(r for r in records if r['run']==a.run)
 if a.output:extract(record,a.output)
 if not a.check:return
 if not a.execute:p.error('--check requires --execute: it runs generated code in Docker')
 from checks import get_check
 code=get_check(record['result']['task'],a.check)
 with tempfile.TemporaryDirectory(prefix='ornith-replay-',dir=Path.cwd()) as t:
  w=Path(t)/'workspace';extract(record,w)
  name='ornith-replay-'+uuid.uuid4().hex
  args=['docker','run','--name',name,'--rm','--pull=never','--network','none','--user',f'{os.getuid()}:{os.getgid()}','--read-only','--memory','512m','--cpus','1','--pids-limit','64','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-w','/workspace','-i',a.image,'python3','-']
  try:
   r=subprocess.run(args,input=code,text=True,capture_output=True,timeout=45)
  finally:
   subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=15)
  print(json.dumps({'run':a.run,'mode':a.check,'passed':r.returncode==0,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
if __name__=='__main__':main()
