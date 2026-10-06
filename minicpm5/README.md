# MiniCPM5: small local models on checkable tasks

RUNTIME compared the final OpenBMB MiniCPM5-1B and MiniCPM5-2B checkpoints on twelve original, synthetic text tasks: routing, extraction and proposing the next tool action. These are illustrative cases, not a general benchmark or a claim about phone performance.

## Recompute the saved results

Only Python 3's standard library is needed:

```sh
python3 analyze_saved.py
```

| Configuration | Strict matches / 12 | One surrounding JSON fence removed |
|---|---:|---:|
| 1B thinking | 5 | 6 |
| 2B thinking | 11 | 11 |
| 1B non-thinking | 0 | 3 |

The analyzer verifies the frozen task hash, unique case IDs, exact prompts and expected answers. It reparses the saved final answers; it does not simply count saved success flags. The relaxed diagnostic removes at most one complete Markdown JSON code block. It does not repair content or change the original score.

Both thinking models chose the correct clarification tool and question in one case, but returned a string where our checker expected a nested argument object. The prompt did not explicitly spell out that nesting or supply a native function schema. Treat this as a checker/interface mismatch, not evidence that the models chose an unauthorized refund.

`data/` contains final-answer projections. Intermediate reasoning is omitted. The one 1B response that reached its output cap before completing thinking has `final_answer: null`; that does not mean it generated no tokens. Original dataset and record hashes are retained in the projection/provenance files. The original frozen prompts and expected values are unchanged.

## Run the thinking text cases locally

The portable runner is a projection of the measured implementation. Its syntax, CLI and fail-closed checkpoint validation were checked; a clean-environment inference rerun of this exported copy has not been qualified. The saved measurements used Linux on NVIDIA GB10, CUDA PyTorch 2.11.0+cu130, Transformers 5.17.0 and Accelerate. These historical versions are not a security-audited dependency recommendation or a guarantee that the same wheels exist for your platform.

Use a dedicated environment with compatible [PyTorch](https://pytorch.org/get-started/locally/), Transformers, Accelerate and Hugging Face Hub. Consult the [official model instructions](https://github.com/OpenBMB/MiniCPM) for your platform. No account or private service is needed for these public checkpoints.

Download the exact revisions separately; weights are not included here:

```sh
hf download openbmb/MiniCPM5-1B --revision 87179e5c1f455ef22e6223592d2d61351b525bfc --local-dir models/1b
hf download openbmb/MiniCPM5-2B --revision f97400052a43d642bbc6e9975e2397e3ae6a6b52 --local-dir models/2b
mkdir -p runs
python3 run_text.py 1b --model-dir models/1b --output runs/1b-thinking
python3 run_text.py 2b --model-dir models/2b --output runs/2b-thinking
python3 analyze_saved.py --results runs/1b-thinking/results.jsonl
python3 analyze_saved.py --results runs/2b-thinking/results.jsonl
```

Output directories must be new. The runner verifies required checkpoint bytes against `checkpoint-manifest.json` before loading, remains offline during inference, and does not execute model-generated code. It reproduces the thinking text cases only; the saved 1B non-thinking result is available for offline analysis.

Both thinking runs use BF16, seed 510, a 4,096 new-token ceiling and top_p 0.95. Temperature is 0.9 for 1B and 1.0 for 2B, following their respective guidance. The measured implementation inherited Transformers' top_k default of 50. The separate 1B non-thinking run used temperature 0.7. Full recorded settings and measured allocation scopes are in `configurations.json`. One attempt and one seed cannot establish general reliability.

The Linux runner checks for 20 GiB available RAM before loading and a 12 GiB reserve between requests. Those checks are not continuous monitoring and are not a minimum-hardware specification. The original experiments additionally used an external memory watchdog. Arrange appropriate monitoring for your own machine and avoid competing important workloads. CUDA allocated, reserved and whole-system memory overlap; do not add them together.

## Sources and interpretation

See [SOURCES.md](SOURCES.md) for exact model revisions, architecture, published training claims and native tool-interface references. These are text models, not MiniCPM-V. MiniCPM5-2B's supported release mode is thinking; 1B also supports non-thinking.

The short tool-choice prompts here ask for custom JSON. They are not native tool-calling benchmarks. A separate native integration must supply the model's `tools=` template, preserve XML delimiters and replay tool results correctly. A parser failure is not automatically a model reasoning failure.

The code in this tutorial follows the repository's code license. Upstream model weights and referenced third-party code retain their own licenses. No narration, voice recordings or model weights are included.

## Executed native-tool control

[The native workflow kit](native/README.md) contains the corrected adapter, runner and saved call/result projections. Both thinking models retrieved the correct posted 2,845-cent invoice: 1B used five calls, including two redundant order lookups; 2B used the three necessary calls. The 1B non-thinking run made two calls and claimed zero cents without retrieving the invoice amount. These are actual local read-only lookups over synthetic data, with one attempt per configuration. The native controls are separate from the twelve custom-JSON checks above.
