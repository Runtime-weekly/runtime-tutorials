# Sources and tested identity

## CLM

- [Official source, tested commit](https://github.com/Contrastive-LM/CLM/tree/bb42c6c5bf914fd449bed2f6ca65be80602cb1f7).
- [Released heads](https://huggingface.co/Contrastive-LM/CLM-v0.1-8B/tree/e939398d4556fcd9400c76fa8c5a513202f42b0a).
- [Qwen3-8B backbone](https://huggingface.co/Qwen/Qwen3-8B/tree/b968826d9c46dd6066d109eabc6255188de91218).

The frozen backbone encodes text; learned state/criterion projections score candidate choices. The small head download does not replace the 8B encoder. The tested heads have 18,887,680 parameters, 4,096-dimensional input, 512-dimensional output and effective similarity scale 100. Head SHA256: `b2b4a8c9c2d39263eff78a351eb909a342ce9b3bf21a3f07c1d1bf15f1c4eda5`.

Pilot/sorting adapter: BF16 Qwen3-8B, Transformers 4.57.3, Torch 2.11.0+cu130, SDPA CUDA, last non-padding token and L2 normalization, unchanged upstream engine/heads on CPU, no chat template. Pilot text cache was cleared for each scored request. Driving and reference qualification use the separately documented reference stack in METHOD.md. Later qualification matched choices on 60 frozen requests with vLLM 0.27.2rc1 nightly, BF16 LAST pooling and activation enabled. Choice parity on those inputs is not numerical embedding equivalence, general parity or a throughput reproduction.

## Jev

- [TypeSafe API](https://docs.typesafe.ai/api), [introduction](https://docs.typesafe.ai/introduction).

Hosted `jev-1.13.0`, System One endpoint; requests contain structured state and questions with choice criteria. Saved responses retain returned model identifiers. Network request time includes remote service and transport; model weights and server hardware are not under our control. This companion does not redistribute hosted implementation or credentials.

## Laya

- [Official model repository](https://huggingface.co/convaiinnovations/laya).
- [RUNTIME's earlier English tutorial](https://github.com/Runtime-weekly/runtime-tutorials/tree/main/laya), a different checkpoint/configuration.

This experiment uses the released **typed-decisions** variant, Laya 0.3.4, CPU with three Torch threads and no task adaptation. Do not apply these results to every Laya variant or substitute the English tutorial identity. See METHOD.md for the recorded checkpoint pin and reproducibility limitations.

## Claims versus measurements

Official architecture descriptions and author evaluations describe their own releases. Our small frozen pilot and custom simulations do not reproduce broad author benchmarks, published speedups, or general agent capability. Unknown pretraining overlap means these are not guaranteed unseen cases. No task-specific retraining or post-result prompt selection was performed for these recorded runs.
