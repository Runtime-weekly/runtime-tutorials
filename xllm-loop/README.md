# xLLM-Loop: a smaller cache, tested locally

RUNTIME tested two released xLLM-Loop Part II checkpoints on NVIDIA DGX Spark
(GB10). Our custom PyTorch SDPA port retained **one third of the KV tensor
payload**, while total observed allocation barely changed and decoding was
effectively the same speed in this small test. This is a compatibility/mechanics
study, not a reproduction of the paper's benchmark suite.

[RUNTIME videos](https://www.youtube.com/@runtime-weekly) ·
[Paper](https://arxiv.org/abs/2610.06833v1) ·
[Official implementation](https://github.com/ifm-ai/xllm-loop)

## Check the recorded results without a GPU

Python 3.12 was tested. These two commands use only Python's standard library;
they make no network calls and do not load a model:

```sh
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials/xllm-loop
python3 -m venv .venv
.venv/bin/python validate_saved.py saved --study study-bos.json
.venv/bin/python analyze.py saved
```

The first command checks all 12 continuation rows and 32 timing rows, paired
inputs, the frozen study hash, and every cache-size ratio. The second regenerates
`saved/summary.json`. This checks saved arithmetic and consistency, not the
truth of arbitrary measurements or equivalence to the authors' fused kernels.

Read `saved/visual-evidence.json` for the exact prompts, both generated
continuations, and per-token evidence. `saved/continuations.json` and
`saved/timings.json` are the measured rows, including the warmups.

## What we measured

Both released checkpoints have 303,579,648 total parameters, including embedding
and output tensors. Each full/shared-cache comparison holds the checkpoint fixed.
BF16, batch one, five core repeats, 512 input tokens plus 32 decode steps:

| Quantity | Full cache | Terminal sharing |
|---|---:|---:|
| Retained cache banks | 12 | 4 |
| KV tensor payload | 10,027,008 bytes | 3,342,336 bytes |
| Same payload in MiB | 9.5625 | 3.1875 |
| Learned-S observed peak allocation | about 653.91 MB | about 647.62 MB |
| Learned-S median time for 32 decode steps | 271.72 ms | 270.42 ms |

The 3x ratio concerns **cache tensors**, not total RAM or model size. The timing
has only three measured repetitions per condition after a warmup; it does not
establish a useful speedup. Allocator reservations depend on process history.
Whole-host available memory and process allocation are different measurements.

Three authored passages provide 96 scored continuation tokens per model/mode.
Learned-S mean negative log likelihood was 3.38964 full / 3.38358 shared;
fixed-S was 3.44111 / 3.51822. Lower means higher average probability of these
particular target tokens. This tiny sample cannot establish general quality.
All six paired greedy continuations differ, and several are repetitive. Terminal
sharing is not lossless cache compression; these are base models, not evaluated
chat assistants. Generated continuations use a fixed 24-token budget.

## Optional fresh inference

The released runner was tested on Linux ARM64, GB10, Python 3.12 and
PyTorch 2.11.0+cu130. Other hardware/operating systems and a completely fresh CUDA
installation have not been qualified here. The historical PyTorch 2.11.0 environment
is affected by [GHSA-rrmf-rvhw-rf47](https://github.com/advisories/GHSA-rrmf-rvhw-rf47),
which is fixed in 2.13.0. The runner does not use the affected `torch.jit.script`
path, but do not treat this historical environment as a recommended fresh install.
For fresh inference use PyTorch 2.13.0 or newer with compatible CUDA support; this
updated inference environment is not yet qualified against our saved outputs.
Offline result analysis needs no PyTorch. Install a compatible CUDA-enabled
[PyTorch build](https://pytorch.org/get-started/locally/) first. Then install the
small dependencies into your own environment:

```sh
python3 -m pip install -r requirements-local.txt
python3 -m pip install --upgrade huggingface_hub
hf download IFM/LoopedLM-P2-huginn-s-learned-entropy0p01 --revision e83177781693848c631142dcf9de3b0688e328e1 --local-dir checkpoints/learned-s
hf download IFM/LoopedLM-P2-huginn-s-fixed-r5 --revision 17cdf78e0d9fd8d19bba07ed800875e1de5675fd --local-dir checkpoints/fixed-s
git clone https://github.com/ifm-ai/xllm-loop.git source
git -C source checkout --detach df0ed1ea415b55f0a944a291f90da9d47c98b5d5
python3 qualify.py
python3 source_schedule_check.py
python3 run_study.py --execute --out run-NEW --study study-bos.json
python3 validate_saved.py run-NEW --study study-bos.json
python3 analyze.py run-NEW
```

Use the same Python environment for installation and execution. The model loader
checks upstream artifact manifests and all 42 expected tensor names/shapes.
`qualify.py` checks CPU FP32 mathematics; `source_schedule_check.py` checks the
pinned upstream terminal-cache schedule using the port's blocks. Neither proves
BF16 fused-kernel equivalence. The pinned upstream source is downloaded separately,
and those controls execute selected methods from that revision.

Fresh inference requires an NVIDIA GPU with a working CUDA PyTorch installation.
The Linux runner also requires at least 20 GiB available host memory and aborts
below 12 GiB. These conservative host checks do not guarantee sufficient discrete
GPU memory. Run in an otherwise idle measurement window. Output directories must
be new; do not overwrite the saved reference data. If no GPU is available, use the
offline commands above. No paid API or RUNTIME account is required.

## Corrections and scope

The initial exploratory run omitted BOS. This exported, corrected companion adds
the official BOS token 0 to the same 48 content-token prefixes and 32 targets.
It was frozen after inspecting the initial run, so it is not an independent
held-out test. The correction also releases preceding cache references before
resetting allocation peaks. Original exploratory artifacts remain archived by
RUNTIME; this folder intentionally presents the corrected publication dataset.

The official xLLM native extension and FlashAttention backend were not used.
We did not test the distilled student, training speed, RL updates, or the authors'
H200 performance claims. `qualification-cpu.json` and
`qualification-source-schedule.json` preserve the original local control results.
Source hashes in the saved qualification identify the actual runner used.
The public reference port differs only in whitespace around matrix multiplication
operators to avoid ambiguity in automated text checks.

## Share a result

If you rerun this, include the checkpoint revision, backend, device, precision,
loop depth, prompt/decode lengths, timings and the exact output. Report failures
too. A different backend or longer context is useful follow-up evidence, not an
automatic contradiction of these bounded measurements.

This folder's port and experiment code are under Apache-2.0; see `LICENSE` and
`NOTICE.txt`. Upstream model/tokenizer rights remain with their authors. Weights,
private infrastructure, narration, and channel artwork are not redistributed.
