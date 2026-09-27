"""Download only the official inputs used by the recorded small demonstration."""
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PINS={
    'crater':('nasa-ibm-ai4science/Crater-Detection-NASA-IBM-Lunar-Foundation-Model','f09ebeae2099c28f09bf4060f56d3e327a6192de','model'),
    'base':('nasa-ibm-ai4science/NASA-IBM-Lunar-Foundation-Model','b657bdfe6fc4c0445d918f77a2d7b919805f3bce','model'),
    'dataset':('nasa-ibm-ai4science/Sombench-NAC-Crater-Detection','79419eb3486b2dd9ad09a283802e0bb8d75c767d','dataset'),
}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--root',type=Path,default=ROOT,help='Directory containing inputs and the official code checkout')
    args=parser.parse_args();data=json.loads((ROOT/'recorded-results.json').read_text())
    jobs=[]
    for key,group,name in [('checkpoint','crater','NAC_ni_lfm_ps8_s44.ckpt'),('backbone_config','base','backbone/config.yaml'),('dataset_annotation','dataset','annotations_min5px_test.json')]:
        entry=data['run'][key];jobs.append((group,name,entry['path'],entry['sha256']))
    jobs.extend(('dataset',entry['id'],entry['path'],entry['sha256']) for entry in data['test_split_tiles'])
    for group,name,rel,sha in jobs:
        target=args.root/rel
        if not args.verify_only:
            from huggingface_hub import hf_hub_download
            repo,revision,kind=PINS[group]
            local=args.root/('inputs/dataset' if group=='dataset' else 'inputs/model/'+group)
            hf_hub_download(repo_id=repo,filename=name,revision=revision,repo_type=kind,local_dir=local)
        with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=sha:raise ValueError('Input hash mismatch: '+rel)
        print('verified',rel)
    for entry in data['official_pre_post']:
        with (args.root/entry['path']).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=entry['sha256']:raise ValueError('Official example hash mismatch: '+entry['path'])
        print('verified',entry['path'])

if __name__=='__main__':main()
