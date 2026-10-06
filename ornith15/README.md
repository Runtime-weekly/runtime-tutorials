# Ornith 1.5 9B: three practical local coding checks

This companion contains saved, unmodified generated files and executable offline checks. All six saved runs are present: the same three tasks for Ornith and the Qwen control.

Three original tasks ask for a fictional Energy Juice shop, a repair of supplied double-add/currency bugs, and CSV totals with one explicitly injected shell transport failure. The injected failure executes no command. Later shell calls execute in an isolated local container. These are small, one-attempt demonstrations, not a general coding benchmark.

## Try the saved artifacts

Python 3 alone can list runs and extract exact original files:

```
python3 replay.py
python3 replay.py --run ornith-energy-shop-native-1 --output energy-demo
```

The destination must not exist. Every extracted file is checked against its original SHA-256. Generated HTML/CSS/JavaScript/Python are stored byte-for-byte as text in `saved-artifacts.json`; this packaging does not repair them. View the extracted site in a disposable local browser profile. Treat generated code as untrusted.

To execute the frozen checks in a network-disabled Docker container:

```
docker build -f Dockerfile.txt -t runtime-ornith-replay:local .
python3 replay.py --run ornith-repair-cart-native-1 --check frozen --execute
python3 replay.py --run ornith-repair-cart-native-1 --check prompt-faithful --execute
```

The container has a read-only root and candidate files, 512 MiB RAM, one CPU, no network and dropped capabilities. Docker must be local and able to mount the working directory. Building the test image needs network access; checking does not. The measured original test container used Node 22.23.2, jsdom 26.1.0 and Python 3. The `Dockerfile.txt` pins jsdom and the Node major line; a future image build is not an exact historical environment.

`tasks.frozen.json` preserves original prompts, initial files, allowed modifications and check code. `checks.py` keeps those checks intact and exposes two separately labelled post-hoc interpretations: a total explicitly labelled 1047 cents is valid without dollar formatting; invalid inputs can be rejected without mutation through a silent return rather than an exception. Both interpretations address requirements the original checker over-specified. They do not change generated files or the original scores.

## Measured scope and limits

The Ornith shop generation hit the 16,384-token context ceiling while forming a tool command, resulting in incomplete tool JSON and HTTP 500. Its saved cart API arithmetic works; actual browser counters update correctly. Its line-item renderer accesses an out-of-scope variable, leaving a real UI error. The supplied-app repair ran out of input context before its next request: 16,630 input tokens exceed 16,384. Its saved file fixes double-add and currency behavior and passes the prompt-faithful check; the strict exception assumption fails. The recovery task completed, changed only summarize.py, and passed the frozen cases.

Completion, budget/setup failure and saved-artifact correctness are separate outcomes. Context errors do not establish unrestricted coding inability. The original generated summaries may claim broader verification; only the supplied checks and recorded browser evidence substantiate our conclusions. The CSV checks do not cover every possible decimal precision or CSV edge case.

Both measured arms use Q8_0, llama.cpp e9fa0781f1c25fc4fe8c86be1edc6970661ad6f0, a 16K context, one slot, full CUDA offload and thinking enabled. Sampling is temperature 0.6, top_p 0.95, top_k 20, min_p 0, seed 2310. Limits are 8192 output tokens per call, 16,384 cumulative output tokens, 12 turns and 900 seconds checked between calls; an in-flight request can extend wall time. Timings include shared-host activity and are descriptive, not optimized serving benchmarks. No vision or maximum-context qualification is claimed.

Ornith and the Qwen control come from different GGUF conversion publishers, so equal Q8_0 labels do not eliminate converter differences. The initial older loader could not handle the appended MTP block; no weights or GGUF metadata were changed. The compatible binary was selected before successful inference and is shared by both arms.

## Sources and provenance

- [Ornith source checkpoint](https://huggingface.co/ornith-ai/Ornith-1.5-9B/tree/489cb97981b8654bcfcf30ce1f94ed1b62e07b53)
- [Official Ornith GGUF](https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF/tree/abdd624b12ebf020b767fff532ff44fe552b28c3), Q8_0 SHA-256 `22086870b009dbe9815ee752c48a82de930118a7c5ce5599590892ae03b8b010`
- [Qwen control GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/3885219b6810b007914f3a7950a8d1b469d598a5), Q8_0 SHA-256 `809626574d0cb43d4becfa56169980da2bb448f2299270f7be443cb89d0a6ae4`
- [llama.cpp source](https://github.com/ggml-org/llama.cpp/tree/e9fa0781f1c25fc4fe8c86be1edc6970661ad6f0)

Saved projections include original result/turn hashes, tool calls, observed tool feedback, final answers and generated file hashes. Long private operational receipts, host paths, model weights, reasoning streams and raw SSE logs are omitted. Model weights remain subject to their upstream licenses and are not redistributed. Offline replay does not call a model or reconstruct a fresh inference run.

## Optional new inference

`run_agent.py` is a portable projection of the measured harness, with a one-attempt CLI replacing its old internal entrypoint. It requires an already running, separately qualified local model endpoint, a fresh output directory and explicit `--execute`. It never starts, unloads or changes model services. Model aliases are labels; they do not prove checkpoint identity. Verify the model SHA-256 yourself and use the pinned binary/settings above.

```
python3 run_agent.py --model-label ornith --endpoint http://127.0.0.1:18593 --output new-local-run --execute
```

The tested server options were `-c 16384 -np 1 -ngl 99 -fa on -b 512 -ub 256 --top-k 20 --min-p 0.0 --jinja --reasoning-format deepseek --chat-template-kwargs '{"enable_thinking":true}' --no-warmup`. Use the appropriate pinned GGUF as the model input and bind only loopback. Provision resources and a watchdog before loading. The measured supervisor required 32 GiB available host RAM and stopped only its own server below 14 GiB; this portable client is not that supervisor.

Download the Q8_0 file from the pinned model repository above into a local `models` directory. Compare its `sha256sum` with `study.json`. With a compatible CUDA-enabled `llama-server` built from the linked commit, the corresponding Ornith launch is:

```bash
./llama-server -m models/Ornith-1.5-9B-Q8_0.gguf --alias ornith \
  --host 127.0.0.1 --port 18593 -c 16384 -np 1 -ngl 99 -fa on \
  -b 512 -ub 256 --top-k 20 --min-p 0.0 --jinja \
  --reasoning-format deepseek --chat-template-kwargs '{"enable_thinking":true}' \
  --no-warmup
```

Wait for its ready message before running the client in another terminal. For the baseline, stop only this test server, change the model file to `Qwen3.5-9B-Q8_0.gguf`, use `--alias qwen`, and run the client with `--model-label qwen` and a different fresh output directory. This recipe describes the measured settings; it does not replace the resource admission/watchdog described above or qualify another device.

The projection retains the original fixed context behavior, including possible input-history exhaustion. It does not silently compact history or promise all three tasks will finish. It adds fail-closed output-directory, loopback-endpoint and host snapshot symlink checks, uses Python 3 explicitly, and will not pull a missing test image automatically. Syntax/help and offline artifact replay are verified; no fresh model inference was run with this relocated wrapper. New private output includes long raw reasoning/stream records; review and project it before sharing. Generated-code results must be checked independently even if an agent claims success.

The optional live wrapper is for trusted local experimentation, not a complete sandbox for adversarial generated code. CPU, container RAM, process count and network are constrained, but host-side subprocess stdout/stderr capture and writable workspace disk usage are not bounded. The external server watchdog does not bound client output buffering. Inspect the harness and provide suitable filesystem/process supervision before using arbitrary prompts or untrusted models. These limitations describe the original measured harness too; its outputs were not silently regenerated using stronger limits.

## Matched control and final outcomes

Qwen's shop run returned a final response, but its saved JavaScript never wires the cart API to the buttons; browser counts and totals remain zero. Its repair stopped at the twelve-turn limit, while the saved code passes the main prompt-faithful add/clear/arithmetic checks. Its recovery also stopped at that limit, but the saved CSV implementation passes the frozen cases. A saved-code pass is not proof the agent returned a final completed response.

Additional source-audit boundary probes are exploratory and excluded from frozen scores. The same probes were applied to all four saved carts: setting an existing quantity to zero, setting a valid quantity before an initial add, and rejecting the inherited Object key `toString` as an unknown product. Both Ornith carts pass those probes. Qwen's shop fails setting a quantity before add; its repair fails setting zero and rejecting that inherited key. These are specific findings, not exhaustive correctness guarantees. Exact diagnostic code/results are in the saved records.

Copy compliance is not granted automatically: Qwen's shop says “wake you up” and “sustained energy,” which imply benefits despite its footer claiming no health claims. The main functional finding remains its inactive cart UI.

Browser captures use real unmodified generated pages. The initial capture environment lacked emoji fonts; corrected captures add an existing Noto Color Emoji font without editing the model output. Missing-glyph boxes in the earlier captures are not counted as a model defect. Timing captures are sampled screenshots of actual interactions, not invented UI or rewritten code.

Run the explicitly exploratory boundary checks with `python3 replay.py --run qwen-repair-cart-native-1 --check boundary --execute`. Exact source revisions, GGUF hashes/sizes, binary identity and measured settings are in study.json. The task checksum is tasks-checksum.txt.

The `Dockerfile.txt` is a reproducibility aid, not a security-audited production deployment. Dependency advisories and a fresh inference run with the relocated wrapper remain outside this qualification.
