# Native MiniCPM5 invoice workflow

This portable projection reproduces the corrected native tool interface used in the saved controls. It has syntax/help and checkpoint-rejection checks; the original local runtime performed the actual inference. No new inference was performed with this relocated file.

Download the exact model revision listed in checkpoint-manifest.json. In a separately qualified compatible CUDA PyTorch/Transformers/Accelerate environment:

```
python3 run_native.py 1b --model-dir MODEL_DIRECTORY --output NEW_RESULT_DIRECTORY
python3 run_native.py 2b --model-dir MODEL_DIRECTORY --output NEW_RESULT_DIRECTORY
python3 run_native.py 1b --no-thinking --model-dir MODEL_DIRECTORY --output NEW_RESULT_DIRECTORY
```

Every required checkpoint file must match the recorded size and SHA-256 before loading. The output directory must not exist. 2B no-thinking is rejected because it is not an officially supported mode. The measured environment was PyTorch 2.11.0+cu130 and Transformers 5.17.0 on NVIDIA GB10, BF16/SDPA, three CPU threads. Historical versions are measurement facts, not a fresh dependency-security qualification or recommendation. Reserve adequate resources and use your own continuous watchdog; the original controls required 20GiB host availability before load and a 12GiB reserve checked every two seconds by an external supervisor. This minimal portable runner does not include that supervisor and must not be run blindly on a shared GPU.

The fixture is entirely synthetic. Actual read-only Python lookups return an order, a stale invoice error with a replacement reference, and the current posted 2845-cent invoice. Successful completion requires the three correct calls in order plus an exact final object. Repeated calls are permitted but recorded. Six model turns, 4096 generated tokens per turn, one seed 510. Thinking samples use official temperatures 0.9/1.0 for 1B/2B; 1B no-thinking uses 0.7. top_p is 0.95; other checkpoint/Transformers defaults, including top_k 50, remain active.

The adapter passes OpenAI-style function schemas to the native chat template, preserves special XML tokens when decoding, replays argument dictionaries and reasoning_content, and passes tool feedback through role=tool. Incomplete XML is rejected before executing calls. Unlike earlier custom JSON diagnostics, native delimiters are not stripped. Only the two supplied local lookup functions can execute; generated shell/Python code is never evaluated by this workflow.

Saved projections omit long reasoning/token streams while retaining actual calls, tool results, final answers, timings and hashes of original full receipts. The runner writes full private raw receipts; sanitize and review before sharing them. Both thinking models succeeded on this one example; the 1B non-thinking configuration did not. This single workflow is illustrative, not an overall tool-use benchmark or latency ranking.

An initial setup attempt failed before inference while allocating a CUDA graphics context. A tiny unchanged CUDA probe then passed and the second setup attempt completed; no services were changed. That setup failure is excluded from model-answer scoring. Model weights and private operational logs are not redistributed; upstream checkpoint licenses apply.

## Sources and code scope

See [the parent source notes](../SOURCES.md) for pinned OpenBMB model cards, templates, official parser and licenses. This small two-function adapter and runner follow the repository code license; upstream model weights and third-party material retain their own terms. No upstream weights are included.

The full `result.json` is the authoritative run receipt, including the final turn. Separate `turn-XX.json` files may omit the last turn because completion exits that per-turn write path.
