# Architectures and measured resources

## The tested paths

**Laya English:** ModernBERT-large encoder → two additional transformer layers → option scoring network → probabilities over the supplied choices. The complete checkpoint already includes its encoder weights. Other Laya variants may use different encoders or task specialization; this experiment does not rank them.

**Kev-0.8B:** Qwen3.5-0.8B-Base text backbone with trained LoRA adjustments → decision/option-marker representations → pointer head comparing those representations → option probabilities. The adapter was merged at loading, not run as a separate sequential inference block. The retained text backbone and head contain approximately 753 million parameters; the marketed base name remains 0.8B.

For our one routing question, both score the available options in one forward evaluation. Neither path generates a chatbot paragraph. Different internals do not themselves explain the observed score gap; this comparison includes size, training, software and prompt-format differences.

## Numbers from this run

| Measure | Laya English | Kev-0.8B |
|---|---:|---:|
| Loaded parameters | 421,293,827 | 752,917,824 |
| Stored weight files | 842,609,210 bytes | 1,792,384,327 bytes |
| Complete retained text model asset set | 846,195,574 bytes | 1,815,339,333 bytes |
| Model assets on disk | **0.79 GiB** | **1.69 GiB** |
| Peak process memory | **2.86 GiB** | **4.94 GiB** |
| Median CPU response | **541 ms** | **756 ms** |
| p95 CPU response | **607 ms** | **802 ms** |

GiB means bytes divided by 1,073,741,824. Model asset totals in decimal megabytes are 846.2 MB and 1,815.3 MB. Disk and RAM are different quantities and must not be added together.

Laya's five model files comprise weights, encoder/task configuration and tokenizer. Kev's ten comprise the entire acquired Qwen base weight shard, adapter, pointer head, configuration/shard index and text tokenizer package. Files are enumerated with upstream repository/revision and SHA256 in `measurements.json`.

The full Qwen weight shard includes tensors beyond the final retained text backbone. It was actually acquired and used during loading, so its complete stored size counts. We did not create a stripped checkpoint or infer bytes from runtime parameter count. Tokenizer fallback assets such as vocabulary and merges are retained even where a fast tokenizer might need fewer files.

These are logical model-package bytes, deduplicating snapshot links to the same stored file. They exclude Python environments/libraries, inference source, documentation, cache metadata and unused image/video processor configuration. They are not total installed software size, physical allocated blocks or a proven minimum deployment package.

Memory is the process high-water reading during the original CPU run, including loading and imports. It is not minimum required system memory, incremental host memory or GPU memory. Models ran one at a time; summing their peaks would not describe this run.

## Historical software context

| Original measured stack | Laya English | Kev-0.8B |
|---|---|---|
| API/package | Laya 0.3.5 | pinned Kev source |
| Torch | 2.13.0+cpu | 2.8.0 |
| Transformers | 5.10.0 | 5.17.0 |
| Device/precision | CPU float32 | CPU float32 |
| Intra-op/inter-op threads | 3 / 1 | 3 / 1 |

These versions identify historical measurements only. **They are not recommended dependency pins or a current security assessment.** The analysis script needs none of them. A fresh model rerun requires current advisory/compatibility review in isolated environments and separately labeled results.

These measurements support “Laya was faster and used less process memory in this CPU setup.” They do not support an intrinsic architecture speed claim, GPU prediction or minimum hardware recommendation.
