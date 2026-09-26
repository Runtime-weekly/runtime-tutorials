# Tev1 vs Qwen: reproducible local decision-model evidence

This is the code and synthetic evidence for RUNTIME's September 26, 2026 comparison of **Tev1-0.8B-experimental** and its **Qwen3.5-0.8B instruction-model baseline**. Both were run locally in BF16 on an NVIDIA GB10. Tev1 scored **48/90** versus **26/90** in this specific immediate-letter pilot. Neither result supports unattended policy enforcement: both approved a 101-unit request against a 100-unit limit.

## Reproduce the published analysis now

No model, GPU, credentials, network connection or third-party package required:

```sh
python3 verify.py
```

The verifier reads every saved decision, checks frozen input hashes and prompt hashes, recomputes correctness from the raw response, confirms the 48/90 and 26/90 totals, and calculates warm latency and paired stress outcomes. It does not trust saved correctness flags without recomputing them. It was checked with standard Python 3 on the measurement host and in a fresh, network-disabled container; no third-party analysis package was installed.

| Clean category | Tev1 | Qwen |
|---|---:|---:|
| Routing |17/30|6/30|
| Explicit policy |21/30|15/30|
| Next action |10/30|5/30|
| Total |48/90|26/90|

Both emitted valid letters for all cases. Correct formatting is not correct decision-making. Repeated warm median/p95 was 183.6/194.4 ms for Tev1 and 180.0/193.5 ms for Qwen—similar, not a speed win. See [METHOD.md](METHOD.md) for clustered cases, sample sizes, timing boundaries and failure examples.

## Files

- `data/cases.json`: 110 original inputs, labels, rationales and exact user/system prompts; 90 clean and 20 separate stress.
- `data/supplemental-attacks.json`: 5 separately frozen wrong-target probes; never merged silently with the original stress set.
- `data/results.json`: 230 actual first responses, token IDs, correctness flags, input counts and timing.
- `data/rendered-prompts.json`: exact 115 chat-template-rendered prompts; identical for both models.
- `data/latency-repeats.json`: 36 extra timing calls/model, separate from accuracy.
- `data/tested-environment.json`: actual historical model/runtime/settings and memory measurements, without machine identifiers or local paths.
- `data/model-files.json`: exact downloaded file sizes/hashes, no weights included.
- `verify.py`: standard-library analysis and consistency checks.
- `download.py`, `setup.sh`, `infer.py`: optional self-contained model rerun, described below.

## Optional model rerun: separate qualification required

**Saved-result analysis is tested offline. This exported inference adaptation is syntax/CLI checked but was NOT used for fresh model inference.** Historical inference used Torch 2.11.0+cu130, Transformers 5.17.0, Python 3.12.3, Linux ARM64 and GB10; the exact historical package versions are recorded in the data.

The historical Torch version is affected by [GHSA-rrmf-rvhw-rf47](https://github.com/advisories/GHSA-rrmf-rvhw-rf47), fixed in 2.13.0. Do not reinstall the historical version as a recommended current setup. The optional recipe uses patched Torch 2.13.0 and the recorded remaining package versions. That patched combination has **not** been requalified here, and may change outputs, latency or compatibility. Check current advisories before installing.

```sh
sh setup.sh
.venv/bin/python download.py tev1 --destination models/tev1
.venv/bin/python download.py qwen --destination models/qwen
.venv/bin/python infer.py tev1 --model-dir models/tev1 --output rerun/tev1
.venv/bin/python infer.py qwen --model-dir models/qwen --output rerun/qwen
```

Run one model at a time. The setup recipe uses the default package index; GPU wheels and CUDA support depend on platform. If its CUDA check is false, follow the [official PyTorch installer](https://pytorch.org/get-started/locally/) for a compatible **patched** wheel before proceeding. No CPU fallback is hidden in the runner. It requires Linux, CUDA, BF16 support, 16 GiB available host memory at admission, and aborts its own process below 8 GiB available. It never stops another workload. Output folders must be new.

`download.py` pins official revisions and invokes HF checksum verification. `infer.py` independently verifies each exported checkpoint-file digest before loading locally with `trust_remote_code=False`. It performs the same greedy, thinking-disabled, max 8-token protocol, fixed case order, neutral warmups and 36 timing repeats; it never executes a chosen action. Results go to your new output directory, not the historical data. The memory guard is a conservative host admission rule, not a universal GPU fit guarantee.

Troubleshooting: no CUDA→install the appropriate patched GPU build; missing checkpoint/checksum mismatch→rerun the pinned download; unsupported model class→check Transformers version; existing output directory→choose a new name; low memory→wait or use a different machine, without terminating unrelated processes. Non-Linux, CPU, other GPUs and fresh patched inference remain untested here.

## Rights and sources

Original code, documentation and synthetic cases are under the [MIT license](LICENSE). This does not license upstream weights, datasets, brand artwork, narration or video. Tev1's pinned card says its fine-tuned weight license is still being finalized; weights are not redistributed. The baseline is Apache-2.0 according to its upstream card. See [SOURCES.md](SOURCES.md).

Canonical project location: [Runtime-weekly/runtime-tutorials/tev1](https://github.com/Runtime-weekly/runtime-tutorials/tree/main/tev1). The video link will be added when a verified upload URL exists.
