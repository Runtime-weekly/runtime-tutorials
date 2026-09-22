# Run Laya locally: a practical Jev alternative

RUNTIME tutorial, tested September 21, 2026. Laya is an independent Apache-licensed
open-source decision model, not an official open-source distribution of Jev.
These examples classify synthetic text and optionally prepare an unsent reply.

**Current download: revision r4.** Dependency pins were updated after GitHub
reported advisories in the original video environment. A fresh Python 3.12.3
Linux ARM64 environment with PyTorch 2.13.0+cpu and Transformers 5.10.0 passed
`pip check`, the first example, triage, clarification and custom categories.
Labels, rounded probabilities and gate decisions matched the recording. The
existing pinned checkpoint was reused; this was not a cold model download.
The optional local-LLM draft step was not rerun with these dependency versions.
`demo-results.json` and the resource measurements below describe the original
video run. Example Python code and checkpoint revision are unchanged.

## What was tested

- Fresh Python 3.12.3 environment on Linux ARM64 / DGX Spark.
- Public `laya==0.3.5`, pinned dependencies in `requirements.txt`.
- Explicit CPU inference; no GPU required for the Laya steps shown here.
- English checkpoint revision `1c5edc17a7acd8701df6fc341c0d179f1c62c982`.
- Downloaded English files: 846,195,574 bytes, about 807 MiB.
- Example process peak RSS: about 2.73 GiB in our measured triage run. This is
  one process on our machine, not a universal minimum-RAM recommendation.
- Python environment plus model used about 1.6 GiB here, excluding installer
  caches. Leave additional disk and RAM headroom. No claimed laptop benchmark.
- Larger-model example used an already running Qwen 3.8 27B server. That model's
  requirements are separate; a smaller compatible local model can be substituted,
  but other models and servers were not tested in this guide.

Windows and macOS command adaptations below have not been executed on those
operating systems. Use a supported 64-bit Python/PyTorch platform. Older Intel
Macs may not have a wheel for the pinned PyTorch release.

## 1. Prepare Python and the tutorial folder

Install Python 3.12 if needed from https://www.python.org/downloads/ and extract
the tutorial ZIP. Open a terminal in the extracted `laya-tutorial` folder.
The video shows the Linux path; `python3 --version` must report 3.12.x here.

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m pip check
```

The interpreter should be Python 3.12, and pip check should report no broken
requirements. This installs public packages into the folder's own environment.
Initial installation/download duration varies with your connection and cache.
Installing the CPU wheel first avoids pulling in a GPU runtime for this CPU demo.

Windows PowerShell adaptation (avoids changing script execution policy):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip check
```

For subsequent Windows commands below, replace `python` with
`.venv\Scripts\python.exe`. On macOS with Python 3.12, use the Linux-style venv
commands but skip the CPU-index install line and install `requirements.txt`
directly. Check the [PyTorch platform guide](https://pytorch.org/get-started/locally/)
for wheel availability. These adaptations are not Windows or macOS validation claims.

## 2. Download one checkpoint

```sh
python download_model.py
```

This downloads the pinned English checkpoint from the official model repository
into `models/laya-english`. It does not preload the multilingual or typed-decision
models. `download-receipt.json` records revision, sizes and hashes. An internet
connection is required for package and model downloads. Subsequent Laya examples
set offline mode and load the local directory. We did not measure network egress
with packet capture; “offline” describes the configured inference path.

## 3. Get your first result

```sh
python first_example.py
```

The core is `laya.load(local_model_path, device="cpu")`, a `choice` question
with four described options, and `agent.system_one(message, questions)`.
Our saved run chose `billing` with about 0.9806 probability. A probability is
not measured accuracy, and a different version or input may produce a different
result. Laya chooses an answer; it does not write a chat reply.

## 4. Demo one: sort requests

```sh
python examples.py triage --output results/triage.json
```

Three synthetic messages: duplicate payment, login error, and team-plan pricing.
Our top labels were billing, technical and sales. The pricing case was uncertain:
sales 0.3655 versus billing 0.3464. Inspect the full probabilities, not just the
winning label. This tiny set is not a quality benchmark. The code does not move
real email, issue refunds or send any messages.

## 5. Demo two: ask instead of guessing

```sh
python examples.py clarify --output results/clarify.json
```

Our illustrative gate proceeds only when the chosen category is not `other`,
the highest model probability is at least 0.80, and the lead over second place
is at least 0.20. Otherwise it prints `ask_for_clarification`. The clear refund
case passed; the vague account message did not. The rules are our application
code, not an autonomous follow-up question generated by Laya. These thresholds
have not been calibrated or validated for a real deployment.

## 6. Demo three: pair Laya with a larger local model

This optional step needs a separately running local server supporting
`GET /v1/models` and `POST /v1/chat/completions`. Install/start that server using
its own instructions. This tutorial does not install a language-model server
or download Qwen. The first two demos work without it.

For our recorded server, we verified the model ID and then ran:

```sh
curl http://127.0.0.1:30000/v1/models
export LOCAL_LLM_BASE_URL=http://127.0.0.1:30000/v1
export LOCAL_LLM_MODEL=qwen3.8-27b
python examples.py llm --output results/llm.json
```

Use YOUR server's port and exact returned model ID; `30000` and `qwen3.8-27b`
are our recording setup, not universal defaults. For example, a server on port
1234 would use `http://127.0.0.1:1234/v1` as its base URL.

PowerShell environment-variable adaptation:

```powershell
$env:LOCAL_LLM_BASE_URL="http://127.0.0.1:30000/v1"
$env:LOCAL_LLM_MODEL="qwen3.8-27b"
.venv\Scripts\python.exe examples.py llm --output results/llm.json
```

Laya selects billing; deterministic application code selects a billing policy;
Qwen drafts a short reply asking for the order number without promising a refund.
The draft is printed/saved for a person to review. No reply is sent. The example
only accepts a loopback HTTP endpoint and reads no API key. Adapt it deliberately
if your own server requires authentication. The non-thinking request field was
tested with our SGLang/Qwen server; compatibility with other servers varies.

## Change the categories: project notes

The revised video includes a small adaptation in `custom_notes.py`. It keeps the
same CPU model and changes the question and category descriptions. No training
step is involved. Run it after downloading the model:

```bash
python custom_notes.py
```

On Windows, use `.venv\Scripts\python.exe custom_notes.py`.

The three synthetic notes returned bug (PDF export freezes, 94.85%), feature
(dark mode, 68.01%), and setup (Python version, 54.97%). These are the selected
categories' model probabilities, not measured accuracy. The last two would fail
the earlier 80% gate. `custom_notes.py` only prints the scores; it does not apply
that gate or perform actions. The short fixed examples do not need truncation;
use the checked input-budget pattern in `examples.py` when adapting to arbitrary
user input. Full outputs are included in `demo-results.json`.

## Common problems

- `No module named laya`: use the same environment's Python and `python -m pip`.
- No matching Torch distribution: check Python version, OS and architecture;
  this pin is tested on Python 3.12 Linux ARM64. Consult PyTorch's installer for
  your platform rather than assuming all platforms have the same wheel.
- Missing model directory: run `python download_model.py` successfully first.
- Download interrupted: rerun the download command; inspect its error, disk space
  and network rather than deleting unrelated caches.
- First call slower: loading a model and running an already loaded model are
  different operations. Our scripts deliberately load once per command.
- Long input: `examples.py` rejects input that does not fit this question's
  token budget. Do not silently truncate a long document and call it complete.
- Startup temperature warning: the pinned checkpoint triggers a warning about
  its 11-or-more-choice temperature bucket in Laya 0.3.5. These demos use four
  choices. The warning is preserved; no probability-calibration claim is made.
- Local-model connection refused: the optional server is not running at that
  address. Check its port and `/v1/models`, and copy the exact model ID.
- A clear request gets an uncertain score: revise category descriptions or
  review it manually; do not lower thresholds merely to force a desired result.

## Sources

- Laya source: https://github.com/NandhaKishorM/laya
- Version tested: https://pypi.org/project/laya/0.3.5/
- Model and license: https://huggingface.co/convaiinnovations/laya
- Jev is a separate product: https://docs.typesafe.ai/introduction
- Python environments: https://docs.python.org/3.12/library/venv.html
- PyTorch platform setup: https://pytorch.org/get-started/locally/

Our wrapper/example code is original RUNTIME tutorial material. Laya and its
weights retain their upstream licenses. This ZIP does not redistribute weights
or include the Python environment. Sources and saved demonstration receipts
accompany the review; no performance claims beyond the measured run are made.
