# Technical index

| | Laya | Needle 3 |
| --- | --- | --- |
| Guide | [README](../laya/README.md) | [README](../needle/README.md) |
| Pinned dependency | `laya==0.3.5` | `cactus-needle==3.0.3` |
| Requirements | [requirements.txt](../laya/requirements.txt) | [requirements.txt](../needle/requirements.txt) |
| Entry point | [first_example.py](../laya/first_example.py) | [demo.py](../needle/demo.py) |
| Other examples | [examples.py](../laya/examples.py), [custom_notes.py](../laya/custom_notes.py) | [cases.json](../needle/cases.json) |
| Saved outputs | [demo-results.json](../laya/demo-results.json) | [example-results.json](../needle/example-results.json) |
| Artifact identity | [download-receipt.json](../laya/download-receipt.json) | [provenance.json](../needle/provenance.json) |
| Execution | CPU; local checkpoint | CPU; package downloads runtime/weights when absent |
| Actual external actions | None; optional LLM response is an unsent draft | None; tool schemas are data, not executable device handlers |

Use a separate Python 3.12 virtual environment **inside each example folder**.
All execution checks are Linux ARM64. Other platforms are not qualified here.

## Laya commands

After following the guide's installation and model download:

```sh
python first_example.py
python examples.py triage --output results/triage.json
python examples.py clarify --output results/clarify.json
python custom_notes.py
```

`python examples.py llm` additionally needs your own loopback OpenAI-compatible
server and the exact model ID from that server. The guide explains both variables.

## Needle commands

```sh
python demo.py --saved
python -m pip install -r requirements.txt
python demo.py --output results/latest.json
```

`--saved` reads the historical example without importing Needle or downloading a
model. The other mode performs fresh inference and never executes generated calls.
`complete()` is deliberately used; this does not test Needle's higher-level `run()`
or `extract()` interfaces.

## Reproducibility

The Laya guide pins an upstream checkpoint revision. The Needle package is pinned,
but its runtime and model downloads are separate; compare artifact hashes with
the historical provenance before claiming identical reproduction. See each guide
for actual failures and for what the recorded timing includes. These small case
sets are demonstrations, not accuracy or hardware benchmarks.
