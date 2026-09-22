# RUNTIME tutorials

Small, runnable examples from [RUNTIME on YouTube](https://www.youtube.com/@runtime-weekly),
with setup instructions, saved outputs and honest limits.

**New to this? [Start here](START_HERE.md).**
**Already using Python? [Open the technical index](docs/TECHNICAL_INDEX.md).**

## Pick a guide

| Guide | What you build | Start / watch |
| --- | --- | --- |
| Kev vs Laya | Inspect 180 recorded decisions, compare architectures and resources, recompute findings | [Research and analysis](kev-laya/README.md) |
| Laya | Classify requests, inspect uncertainty, customize categories, optionally draft with a local LLM | [Guide](laya/README.md) · [Video](https://youtu.be/J-Cn9UUJtdA) |
| Needle 3 | Convert seven synthetic requests into proposed tool calls and inspect failures | [Guide](needle/README.md) · [Video](https://youtu.be/FnKINBWJPTs) |

For the advanced experiment from our Dream-RSI episode, use the separate
[dream-rsi-experiment repository](https://github.com/Runtime-weekly/dream-rsi-experiment).

These guides were checked on **Python 3.12 / Linux ARM64 / CPU**. Other platform
commands are adaptations, not completed tests. Model weights download separately.

These small synthetic demonstrations are not performance or accuracy benchmarks. Nothing sends messages or changes accounts.

## Download and run

Use **Code → Download ZIP** above and extract the folder, or clone:

```sh
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials
```

Then open **one guide** and create its virtual environment inside that example
folder. The repository root has no shared install command. No RUNTIME account,
API key or private service is required; Laya's optional drafting step needs your
own local language-model server.

The [Laya tutorial ZIP](https://github.com/Runtime-weekly/runtime-tutorials/releases/download/laya-v19-r4/laya-tutorial.zip)
contains the video examples with updated, tested dependency pins.
The [Laya and Needle tutorial library](https://github.com/Runtime-weekly/runtime-tutorials/releases/tag/tutorials-v1.1)
includes those two guides, historical outputs and navigation. The Kev vs Laya
research companion is available in the current repository ZIP or clone. Older releases are
retained for reference; use these current downloads for a new installation.

## Find your way around

| Folder / page | Contents |
| --- | --- |
| [START_HERE.md](START_HERE.md) | Downloading files, opening a terminal and creating an environment |
| [kev-laya/](kev-laya/README.md) | Frozen synthetic cases, saved decisions, architecture and resource measurements, standard-library analysis |
| [laya/](laya/README.md) | Laya code, requirements, instructions and saved results |
| [needle/](needle/README.md) | Needle code, test sentences, instructions and saved results |
| [docs/](docs/TECHNICAL_INDEX.md) | [Glossary](docs/GLOSSARY.md), [troubleshooting](docs/TROUBLESHOOTING.md) and direct technical links |

## Validation

The Laya example code is unchanged from the video; dependency pins were updated
after an advisory review. The CPU examples were rerun in a fresh environment and
their labels, rounded probabilities and gate decisions matched. The optional
LLM integration was not rerun with the updated packages. The Needle
export was installed in a fresh Python environment and all seven requests were
rerun; proposed calls and warnings matched the recorded demonstration. Package
downloads used existing caches. This does not qualify a cold download or other
operating systems. See each guide for source/version details and actual failures.

## License and sources

Original RUNTIME example code and accompanying tutorial documentation are available
under the [MIT License](LICENSE). Upstream code, model weights and dependencies
retain their own licenses. This license does not cover channel videos, narration,
portraits, logos or other brand assets. Models and environments are downloaded
separately; they are not bundled here.

## Updates and corrections

[Roundups and newsletters](https://github.com/Runtime-weekly/Blogs---Posts) are kept
in a separate archive. For a problem with this tutorial, open an issue with the
command, platform and a small synthetic example. Remove secrets, personal details,
private paths and customer data before sharing logs.
