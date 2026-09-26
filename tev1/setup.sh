#!/bin/sh
set -eu
# Optional patched rerun environment; not the historical measurement environment.
# CPU/CUDA wheel selection is hardware-specific: follow official PyTorch install guidance.
if [ -e .venv ]; then echo "Refusing to modify existing .venv; use a fresh directory" >&2; exit 1; fi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install 'torch==2.13.0' 'transformers==5.17.0' 'accelerate==1.15.0' 'tokenizers==0.23.2' 'safetensors==0.8.0' 'huggingface-hub==1.32.0'
.venv/bin/python -c 'import torch; print("Torch:",torch.__version__,"CUDA available:",torch.cuda.is_available())'
