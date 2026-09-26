# What was measured

The viewer question is whether a specialized tiny decision model improves useful decisions over its corresponding ordinary Qwen instruction checkpoint. Tev1 retains the ordinary next-token language-model head; it is not Jev's non-autoregressive runtime. We did no training and do not attach a published 4B training-cost claim to this 0.8B experiment.

Both instantiated models had 852,985,920 BF16 parameters, including the loaded conditional-generation architecture. The tasks are text-only. CUDA/SDPA, batch 1, 3 CPU threads, greedy generation, no thinking, max 8 new tokens, no grammar/logit constraint, no retries. All 115 rendered prompts matched byte-for-byte. Tokenized inputs were 126–217 tokens; outputs were 4 tokens including formatting/special tokens, below the cap. This is a controlled comparison in immediate-letter mode, not each model's best unrestricted reasoning mode.

## Dataset structure and labels

Freshly authored synthetic cases were frozen before model outputs. We cannot certify absence from all training data. 90 clean rows: 30 routing, 30 explicit-policy, 30 workflow next-action. Semantic labels and answer positions are balanced within category. Workflow 30 is 6 decision states across 5 task names; policy 30 comprises 10 related triples. They are not 90 independent problem families. Rates are descriptive; no significance claim, binomial confidence interval or broad benchmark ranking.

Separate 20 stress rows comprise 5 embedded instructions, 5 negations, 5 ambiguous requests and 5 rotated clean-option probes. S01's instruction requests an already-correct option; therefore 18/20 vs 9/20 is **classification accuracy**, not an injection-resistance rate. Frozen inputs were preserved rather than silently repaired.

A further 5 separately frozen probes explicitly target a wrong letter. Attacked-case accuracy is 5/5 vs 0/5. But every Qwen prediction is unchanged from its clean pair; 3 merely coincide with the attack target. No new Qwen failure was induced. Tev stays correct on 4 pairs and improves one previously wrong answer. These observations do not demonstrate malicious-instruction obedience, security superiority or general robustness. Five reordered probes give semantic consistency 5/5 vs 4/5; consistency alone is not correctness.

## Examples worth checking

- R01: expired password-reset link. Tev selects Account access; Qwen selects Human triage.
- P01: 80 units and receipt attached, at-most 100 policy. Tev approves; Qwen denies.
- A01: unfinished dependency. Tev waits; Qwen prematurely selects Run checks.
- P02: 101 units with receipt. Both approve although the explicit limit is 100.
- P03: 80 units, missing required receipt field. Tev approves; Qwen correctly requests review.
- R19: explicit request for a new calendar feature. Both unnecessarily escalate to human triage.

Qwen selects Human triage in all 30 routing rows; Tev does so 14 times. The higher Tev aggregate still leaves 42 clean errors. Do not show only its successes or treat valid letters as safe actions. All chosen actions remained simulated labels.

## Latency and memory

Three neutral warmups precede each scored run. Additional 36 calls/model repeat 12 fixed clean cases three times and never replace first scored responses. Their outputs are unchanged from corresponding first calls. End-to-end timings include chat templating, tokenization, host-to-device transfer, generation and decoding, with CUDA synchronization. Cold loading is separate: 10.76 s and 24.57 s, subject to cache/storage conditions.

Repeated warm median/p95: Tev 183.6/194.4 ms; Qwen 180.0/193.5 ms. The host was shared, runs sequential in fixed Tev-then-Qwen order. No causal/intrinsic speed claim. Both lacked optimized causal-conv1d/flash-linear-attention kernels and used reference PyTorch paths. Timings are for this setup, not optimized serving throughput or user-visible application latency.

CUDA peak allocated: 1,768,821,248 bytes (~1.647 GiB) each. Process peak RSS: 2,658,615,296 bytes (~2.476 GiB) and 2,680,373,248 bytes (~2.496 GiB). GPU allocated, GPU reserved and process RSS have different/overlapping scopes, especially on unified memory; never add them into a claimed total.

Each downloaded weight file is 1,746,942,600 bytes (~1.627 GiB). Complete downloaded repository assets are 1,769,899,588 bytes for Tev and 1,769,980,465 bytes for Qwen; metadata/tokenizers are included, package environments/caches excluded. This is downloaded footprint, not minimum text-only deployment or runtime RAM.

## Reproduction scope

`verify.py` reproduces historical numerical conclusions offline using only standard Python. Exported optional inference is adapted into standalone scripts and has not been rerun with the newer patched Torch requirement. Historical outputs remain immutable evidence; do not imply a fresh patched-runtime qualification or guaranteed bitwise results elsewhere. Full package/hardware identity is in `data/tested-environment.json`. Source checkpoints and their distinct weight rights remain upstream.
