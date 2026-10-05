# JEV-27B: fast decisions versus extra reasoning

RUNTIME tested AutoTrust AI Lab's independent JEV-27B locally on an NVIDIA DGX Spark. This companion contains our original synthetic fixtures, recorded choices and timings, and Python standard-library analysis. It reproduces the **analysis of the recorded experiment**, not a new inference run.

## Reproduce the analysis

Clone this repository, enter `jev27b`, and use Python 3.10 or newer. No model, GPU, account or extra package is needed for these commands:

```bash
python3 -m unittest test_harness.py
python3 analyze.py --cases conditions.frozen.json --results results/dev-s1.json results/dev-s2.json --select-gate gate.json --output dev-analysis.json
python3 analyze.py --cases conditions.frozen.json --results results/test-s1.json results/test-s2.json results/test-generation.json results/test-rules.json --gate gate.json --output analysis.json
```

Output files are created exclusively: use new filenames on subsequent runs. `dev-analysis.json` uses the test-summary schema and therefore reports missing test rows; the useful development output is `gate.json`. Read the canonical results from `analysis.json`.

| Arm | Correct / 72 original test cases | Median measured time |
|---|---:|---:|
| Simple rules | 70 | 0.00000303 seconds |
| S1: native decision head | 63 | 0.653 seconds |
| Pure S2: reasoning plus typed readout | 71 | 102.203 seconds |
| Ordinary Qwen generation, adapter disabled | 50 | 2.336 seconds |

These are serial, batch-one reference-runtime measurements, not optimized throughput claims. Rules run locally without HTTP; model times include the client/server request. Missing optimized linear-attention kernels affect the model timings.

## What we tested

The frozen dataset has 24 development and 72 canonical test cases. Twelve mechanism groups are split into three development and nine test groups; related cases are dependent. Another 96 test conditions change the presentation of 24 test parents: option order, irrelevant text, or an untrusted instruction. They are not 96 independent new problems. Across four arms there are 768 recorded evaluations: 576 model requests and 192 local rules evaluations.

The two tasks are support routing and selecting the next authorized action from an explicit runbook. Every arm sees the same supplied policy, facts, question and options. `common.model_input()` excludes labels and split metadata. The rules baseline is deliberately a small deterministic parser, not a general language-understanding system. `build_cases.py` preserves the original fixture construction; the frozen file is the analysis input.

The model is [autotrust/JEV-27B](https://huggingface.co/autotrust/JEV-27B/tree/51740a8891c2a8baefd969237fd44187b3e3a115), revision `51740a8891c2a8baefd969237fd44187b3e3a115`. AutoTrust trained additions to the frozen Qwen3.8-27B backbone using TypeSafe Jev outputs. This is not TypeSafe releasing its own model weights, and our local model does not call the teacher API.

Our BF16 run kept the backbone and adapter separate. S1 uses the native decision head; S2 disables the adapter, generates reasoning with a 512-token budget, then reads option logits. It is **pure S2**, not the upstream default 50/50 S1/S2 blend. Ordinary generation disables the adapter, turns thinking off and must return exact JSON with one allowed key. These arms also differ in prompt and readout; the comparison does not isolate the causal effect of reasoning alone.

For model installation and API examples, start with the [pinned upstream model card](https://huggingface.co/autotrust/JEV-27B/blob/51740a8891c2a8baefd969237fd44187b3e3a115/README.md) and [server implementation](https://huggingface.co/autotrust/JEV-27B/blob/51740a8891c2a8baefd969237fd44187b3e3a115/serve_decide.py). Model weights and upstream code have their own license terms. A fresh inference runner and a cold installation are not qualified by this analysis kit; the upstream default settings do not reproduce our pure-S2 condition unchanged. Budget roughly 50 GiB for this BF16 backbone/runtime, plus system headroom; a small trained adapter does not remove the backbone.

## Limitations and failures worth inspecting

- **No confidence gate qualified.** All six fixed thresholds on development data made two errors, versus one for always-S2. A high supplied-option score is not a measured probability that an answer is correct.
- In `mechanism-09-A2`, diagnostic age 14 exceeds the allowed 13. S1 selects retry at about 94.874%; S2 and rules correctly collect fresh evidence. Retry authorization alone is insufficient.
- In `mechanism-01-R2`, yesterday's duplicate charge was refunded but today's export fails. The rules parser incorrectly selects billing; all three model arms select technical. S2 reaches its reasoning budget before its final readout.
- Five canonical test cases contain wording tension: an enterprise policy routes billing to security for a human audit, while the security option describes unauthorized activity. Cases `mechanism-13-R1`, `mechanism-15-R1`, `mechanism-18-R1`, `mechanism-19-R2`, and `mechanism-23-R1` are retained in the primary 72-case result. Excluding them **post hoc** leaves 67 cases: rules 65, S1 63, S2 67, generation 50 correct. This sensitivity check is not a preregistered cleaned benchmark.
- S2 hit its reasoning budget in 20/72 canonical and 47/168 total test conditions. Successful transport and a valid final choice do not prove reasoning completed.
- Across the 96 dependent variations, same-choice consistency was S1 91/96, S2 95/96, generation 91/96 and rules 96/96. Consistency is not correctness.

Recorded results are projected onto the fields needed for analysis: semantic choices, scores, probabilities, client timings, completion flags and request counts. They contain no private infrastructure configuration or voice recordings. Reasoning transcripts are not included. `analyze.py` rejects duplicate arm/case rows rather than silently replacing attempts.

Share improvements with the exact model revision, prompts, settings, task definitions and both successes and failures. A stronger test is more useful than a universal winner claim from this small synthetic set.
