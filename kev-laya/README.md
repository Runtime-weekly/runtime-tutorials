# Kev-0.8B versus Laya English

A small, inspectable RUNTIME experiment: **30 synthetic English support messages, three option orders, two local decision models**. September 22, 2026.

[Watch the comparison: Open-Source Jev? Kev vs Laya — We Tested Both](https://youtu.be/ijSZfUtdVaY).

Kev matched more of our predefined routes in this setup. Laya used less process memory and responded faster. Both made mistakes. This is a comparison of two specific configurations, not a general leaderboard or a test of hosted Jev.

| Original option order | Kev-0.8B | Laya English |
|---|---:|---:|
| Clear requests | 8/10 | 7/10 |
| Missing evidence or conflicting requests | 8/10 | 0/10 |
| Negation and policy boundaries | 10/10 | 5/10 |
| **Total** | **26/30** | **12/30** |

Across all orders: **74/90 versus 33/90** correct decisions. The same 30 messages repeat; these are not 90 independent examples. Four Kev cases and five Laya cases changed answer when option order changed.

## Reproduce the analysis

Requirements: Python 3.10 or newer. No packages, model downloads, accounts, GPU or network calls are needed.

```sh
python3 analyze.py --check
python3 analyze.py
```

Expected check output:

```text
PASS: 30 frozen cases, 180 decisions, CSV/JSON consistency, and saved summary verified.
```

The second command prints all recomputed counts and resource calculations. Tested with Python 3.12.3 on Linux ARM64 in a fresh standard-library-only environment. Other platforms have not been tested. Windows users may use `py -3` instead of `python3`.

If the check fails, retain the error and compare your files with the published versions. Do not edit the expected summary merely to obtain a pass. If you intentionally change the examples, describe that as a separate experiment.

## Read and inspect

- [Method and limits](METHOD.md): frozen inputs, common request layout, model settings and denominators.
- [Architectures and resources](ARCHITECTURE-AND-RESOURCES.md): what was actually loaded; disk, process memory and response times.
- [Sources and model revisions](SOURCES.md): primary sources and exact checkpoint/code identities.
- [cases.json](cases.json): all messages, policies, expected answers and permutations, frozen before inference.
- [results.csv](results.csv) and [results.json](results.json): sanitized complete per-decision evidence.
- [measurements.json](measurements.json): public checkpoint-file hashes/bytes and historical runtime measurements.
- [expected-summary.json](expected-summary.json): expected output of the independent analysis.

### Three useful failures

**C06:** exports produce an empty file. Our expected route was technical. Kev chose clarify; Laya chose billing, in every order.

**A04:** an incorrect invoice and an app crash, neither prioritized. Our policy says clarify. Kev changed from clarify to technical and back to clarify as options moved; Laya selected billing throughout.

**A06:** a refund request and buying information, explicitly equally urgent. Both chose billing rather than our expected clarify. Native probability estimates did not guarantee adherence to the routing policy.

No incorrect choice had maximum option probability at least 0.9 in this sample. That does not establish a safe automation threshold. No customer message or account action was sent.

## Model reruns

This repository reproduces **analysis of saved decisions**, not fresh model inference. It deliberately does not ship an inference installer or dependency lock recommending the historical model stacks. Original runtime versions are retained as measurement provenance; they are not current security or compatibility recommendations.

For a new model experiment, use the official projects linked in [SOURCES.md](SOURCES.md), isolated environments, current dependency advisory review, and pinned model revisions. Keep this dataset/result pair unchanged. A new model, prompt layout, checkpoint, library stack or precision is a new condition; report it separately. No inference output is fabricated by the analysis script.

Related RUNTIME material: [Laya and Needle tutorials](https://github.com/Runtime-weekly/runtime-tutorials), [Laya setup video](https://youtu.be/J-Cn9UUJtdA).

Original analysis code, authored synthetic cases and documentation are licensed under [MIT](LICENSE). Upstream models/code retain their own licenses. No model weights, voice, video or branding rights are granted by this repository.
