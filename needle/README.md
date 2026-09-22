# Needle 3: from a sentence to a proposed command

[Watch the video](https://youtu.be/FnKINBWJPTs) · [Beginner setup](../START_HERE.md) ·
[Technical index](../docs/TECHNICAL_INDEX.md)

This example asks Needle to interpret seven synthetic requests using two tool
schemas: lights and a thermostat. It prints proposed calls. **It does not connect
to devices or execute those calls.** No account or API key is needed.

## Look before installing

Open [example-results.json](example-results.json), or use Python alone:

```sh
python3 demo.py --saved
```

This displays the recorded video run, not fresh inference. Its seven examples
include ordinary requests, two commands at once, negation, ambiguity, an unavailable
tool, and an out-of-range temperature.

## Install and run

Tested here: **Python 3.12, Linux ARM64, CPU**, package `cactus-needle==3.0.3`.
Check the [upstream supported platforms](https://cactuscompute.com/blog/needle-supported-devices)
for other systems. The commands below for Windows/macOS are adaptations, not
completed platform tests.

Download this repository's ZIP and open its `needle` folder, or:

```sh
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials/needle
```

Linux/macOS, with Python 3.12:

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python demo.py --output results/first-run.json
```

Windows PowerShell, with Python 3.12:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe demo.py --output results/first-run.json
```

The package retrieves the model/runtime on first use if absent. This needs internet
access. We disable the package's telemetry options before importing it; that does
not turn downloads into offline activity. Use a new output filename for each run.

## Read the result

Look inside `cases`. Each entry has the input sentence, `response.function_calls`,
validation details and elapsed milliseconds. A normal lights request produced a
`set_lights` call in the recorded run. That JSON is a proposed action only.

Two important failures in the recorded results:

- “Do not turn off the kitchen lights” still produced a lights-off call, with a
  negation warning.
- A request for 100 degrees produced 17 degrees, with an ungrounded-value warning.

The ambiguous room request was suppressed. An unavailable flight-booking request
returned no calls. `success: true` and high confidence do not prove the request
was handled correctly. This tests `complete()`, not the higher-level `run()` or
`extract()` APIs. Do not connect this demonstration directly to real devices.

## Change one thing

Edit a sentence in [cases.json](cases.json), run again with a new output filename,
and inspect the whole response. Tool definitions are plain JSON schemas; no Python
handler executes the returned names. This keeps experimentation inspectable.

## Versions, sizes and limits

[provenance.json](provenance.json) records the historical model hash, 35,335,380-byte
weight file and engine-cache version. The package pin alone does not pin every
downloaded artifact; compare hashes before claiming an identical reproduction.
We distribute only our small example and results, not model weights or runtime binaries.

Historical calls took 18.06–58.03 ms after initialization. Those measurements exclude
speech recognition and actual device actions. The runtime reported 124.3 MB peak
RAM; that is not an independent process-memory measurement. Seven examples do not
establish a general accuracy, latency or safety benchmark.

Problems installing or interpreting output? See [troubleshooting](../docs/TROUBLESHOOTING.md).

## Sources and license

- [Needle source and license](https://github.com/cactus-compute/needle)
- [Pinned Python package](https://pypi.org/project/cactus-needle/3.0.3/)
- [Official model/runtime artifacts](https://huggingface.co/Cactus-Compute/needle3)

RUNTIME example code and documentation use the repository's [MIT license](../LICENSE).
Upstream Needle, model weights and dependencies keep their own licenses.
