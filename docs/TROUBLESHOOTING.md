# Troubleshooting

| What you see | What to check |
| --- | --- |
| Python is not found | Install Python 3.12, reopen the terminal, and check `python3 --version` or Windows `py -3.12 --version`. |
| `requirements.txt` is missing | Use `ls` to check the current folder. Enter `laya` or `needle`, not the repository root. |
| `No module named ...` | Install with the same interpreter used to run the example. On Windows use `.venv\Scripts\python.exe -m pip ...`. |
| No matching package/runtime | Check Python version, CPU architecture and the upstream supported-platform list. Do not force an incompatible wheel. |
| A model is still downloading | The first run needs internet access. Inspect the error before retrying; package installation and model download are separate steps. |
| Laya cannot find its model | Run `python download_model.py` from the Laya folder first. |
| Local LLM connection refused | The optional server is separate. Check its port and model ID. Laya's other demos do not need that server. |
| Different scores or timing | Inspect the selected answer and warnings. These results are not guaranteed performance figures. |
| Needle proposes the wrong action | Inspect the full output, especially negation and grounding warnings. The demo does not execute any action. |

To stop a foreground example, press **Ctrl+C**. To leave an activated virtual
environment, type `deactivate`. Keep generated `results/`, model downloads and
`.venv/` out of contributions.

For help, [open an issue](https://github.com/Runtime-weekly/runtime-tutorials/issues/new/choose).
Share the example, OS/architecture, Python version, exact command and a short error.
Replace usernames, home paths and sensitive values with placeholders first.

[Back to start](../START_HERE.md) · [Technical index](TECHNICAL_INDEX.md)
