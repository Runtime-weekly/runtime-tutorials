#!/usr/bin/env python3
"""Download the exact official checkpoints. Requires the Hugging Face `hf` CLI."""
import argparse,subprocess,sys,shutil
from pathlib import Path
MODELS={'tev1':('togethercomputer/Tev1-0.8B-experimental','6bb2dff14b38fea90ddb14d870166ccaf77374e9'),'qwen':('Qwen/Qwen3.5-0.8B','2fc06364715b967f1860aea9cf38778875588b17')}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',choices=MODELS);p.add_argument('--destination',type=Path,required=True);a=p.parse_args();repo,rev=MODELS[a.model]
 executable=Path(sys.executable).parent/'hf';hf=str(executable) if executable.is_file() else shutil.which('hf')
 if not hf:raise SystemExit('Install huggingface-hub in this Python environment to obtain the hf CLI')
 subprocess.run([hf,'download',repo,'--revision',rev,'--local-dir',str(a.destination)],check=True)
 subprocess.run([hf,'cache','verify',repo,'--revision',rev,'--local-dir',str(a.destination)],check=True)
