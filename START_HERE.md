# Start here

You do not need to know Git or train a model to follow these guides. Start with
one example, get its expected result, then change one thing at a time.

## 1. Choose an example

| Guide | What you will do | What you need |
| --- | --- | --- |
| [Laya](laya/README.md) | Sort short requests into categories and inspect uncertainty | Python 3.12; a package and model download; CPU |
| [Needle](needle/README.md) | Turn seven example requests into proposed tool calls | Python 3.12; a package, model and runtime download; CPU |

Both were tested on Linux ARM64. Windows/macOS commands are provided where useful,
but have not been tested here. See the guide's compatibility notes before installing.
Neither example controls a device or sends a real message.

Prefer to look first? Read [Laya's saved output](laya/demo-results.json) or
[Needle's saved output](needle/example-results.json). JSON is simply a text format
with named fields: look for `input`, then the answer or `function_calls`.

## 2. Get the files

**Without Git:** open the [repository home](https://github.com/Runtime-weekly/runtime-tutorials),
choose **Code → Download ZIP**, and extract it. Open the `laya` or `needle` folder.
Do not run files while they are still inside the ZIP viewer.

For the exact Laya video bundle, use [the tagged release](https://github.com/Runtime-weekly/runtime-tutorials/releases/tag/laya-v19-r3).
Its README is self-contained; newer navigation pages live in this repository.

**With Git:**

```sh
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials
```

## 3. Open a terminal in the example folder

A terminal runs typed commands. On Linux/macOS, open Terminal; on Windows, open
PowerShell. `cd` changes folders and `ls` lists their contents (PowerShell also
supports `ls`). Use your own extracted folder's location.

Before installing anything, check that the current folder contains the guide's
`requirements.txt` and Python example files. Copy commands from one operating-system
section only, one line at a time. Do not type the Markdown backticks.

## 4. Create an isolated Python environment

Install [Python 3.12](https://www.python.org/downloads/) if needed. A virtual
environment keeps this example's packages separate from other projects.
The guide gives the exact commands; they follow this pattern:

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

Check the first command reports **3.12.x**. On Windows the guides use
`py -3.12` and `.venv\Scripts\python.exe` instead. You do not need to change
PowerShell's execution policy or use administrator access for these examples.

## 5. Run the guide's first example

Return to [Laya](laya/README.md) or [Needle](needle/README.md) and follow its download
and run steps. Initial downloads need internet access and may take time. Keep
model files and installed environments on your computer; they are not in this repo.

The result should be printed in the terminal. Compare its meaning with the saved
example; probabilities and timings may differ. Success means understanding what
the program actually returned, not just seeing a high confidence number.

## If something goes wrong

Start with [troubleshooting](docs/TROUBLESHOOTING.md). Include your Python version,
operating system, command and a short redacted error when asking for help.
Never post passwords, access tokens, private documents or full system logs.

Next: [plain-language glossary](docs/GLOSSARY.md) · [technical index](docs/TECHNICAL_INDEX.md)
