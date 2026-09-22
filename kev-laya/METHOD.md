# Method

## Question

How do Kev-0.8B and the Laya English checkpoint behave on the same small English support-routing task? We measured agreement with an authored policy, option-order sensitivity, in-process CPU response times and peak process memory. We did not isolate the causal effect of architecture, reproduce vendor benchmarks, or test Jev itself.

## Frozen input

Thirty new synthetic messages were authored with expected routes before inference: ten clear, ten ambiguous/missing-evidence, and ten negation/priority/policy-boundary cases. Four routes are available: billing, technical, sales and clarify. Cases were not edited or tuned using the results.

The frozen `cases.json` SHA256 is:

```text
f8ae9a541e11e5a760d6eadfbf3fd617e04356b9b8dd79b10220cf5297a0915b
```

Each model evaluated the same three orders:

1. billing, technical, sales, clarify
2. clarify, sales, technical, billing
3. technical, clarify, billing, sales

This yields 90 decisions per model but only 30 unique cases. These are three different option orders, not identical repeated trials. The first order supplies the primary 30-case result; the other orders probe robustness.

Refund requests always route to billing, regardless of purchase date. Date-bearing cases therefore test whether irrelevant dates distract routing, not date arithmetic or refund eligibility. `clarify` is an explicit class, not a probability-threshold abstention system. Labels reflect this chosen policy; another organization may choose differently.

## Common input format

The policy was too long for Laya's default question-head allocation, so before scored inference it was placed in the **state for both models**, followed by the unchanged customer message:

```text
Routing policy: {instructions from cases.json}

Customer message: {case state}
```

The common choice question was:

```text
Choose the support route using the policy in the state. Return one listed option.
```

Criteria were the exact `options` mapping in `cases.json`, inserted in the current permutation order. All 90 inputs per model were checked before scored calls for instruction, option and state truncation. Laya inputs were 235–251 tokens; Kev inputs were 224–240. No silent truncation or request error occurred.

This policy-in-state layout is one chosen application format, not a search for each model's best prompt. Different layouts need separate tests.

## Execution

Both ran CPU float32 with three intra-op threads, one inter-op thread, batch size one, sequentially in separate environments. Each had one unscored warmup. Seed was 20260922. No GPU inference, prefix caching, external actions or paid model calls were used.

Laya used its documented `system_one` method, English root checkpoint and shipped four-option calibration temperature of 1.7601518630981445. Its default router, queried without inference, selected English for all raw customer messages. That router check used the raw message; model evaluation used the policy-prefixed state. No specialized typed-decisions checkpoint or fine-tuning is included.

Kev used its official checkpoint loader, input encoder, probability computation and answer mapper. Its LoRA adapter was merged into the base in float32. Pointer temperature was 2.406050072164233; eager CPU attention, no date-fact augmentation and no prefix cache. Reference CPU fallbacks for causal convolution and gated delta attention were used. This single-question path scores options rather than generating a paragraph.

The distributions in `results.json` preserve Laya's native probabilities and Kev's unrounded probabilities. The public API's confidence field is not used as an interchangeable probability. Native temperatures were not fitted to these 30 cases. Do not infer deployment calibration or a reliable action threshold from this pilot.

## Calculations

Accuracy is exact semantic-label agreement with the prewritten answer. Order instability means any different chosen semantic label across the three orders. Stable correctness requires matching the key in all three orders. Maximum native probability at least 0.9 is reported descriptively, not recommended as an action gate.

Latency includes tokenization, forward evaluation and answer formatting; excludes loading, networking and the separate token audit. Median averages sorted observations 45 and 46; p95 uses nearest rank, sorted observation 86 of 90. Shared-host activity was not controlled for a hardware benchmark.

Process memory is the original process high-water RSS including imports and model loading. Disk totals come from recorded individual model-asset lengths; no filesystem or model access is required to recompute the published totals. Recomputing those totals validates arithmetic, not the current availability or identity of an upstream download.

The original checks confirmed 180 unique model/case/order rows, no runtime errors, complete option vectors and unchanged frozen input. An independent review reproduced the counts and found no major invalidating input/count discrepancy. This is not external peer review or a claim of statistical population superiority.

## Limits

Small hand-authored synthetic sample, one domain, one policy and one prompt layout. Training-data overlap is unknown. Models differ in size, tokenizer, training, context limits, architecture, dependencies and native probability calibration. There was no held-out threshold tuning, language sweep, real traffic evaluation or application deployment. Historical runtime versions are evidence, not safe installation instructions.
