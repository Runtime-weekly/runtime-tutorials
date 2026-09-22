# RUNTIME tutorials

Runnable examples and setup guides from the RUNTIME YouTube channel.

## Laya local setup

[Watch the tutorial on YouTube](https://youtu.be/J-Cn9UUJtdA)

[Read the step-by-step guide](laya/README.md) · [Download the tutorial ZIP](https://github.com/Runtime-weekly/runtime-tutorials/releases/download/laya-v19-r3/laya-tutorial.zip)

Install the independent open-source Laya decision model, sort requests, pause uncertain cases, and connect a local language model to draft a reply. A project-notes example shows how to change the categories.

Tested on Linux ARM64 with Python 3.12 and CPU inference. Other platform commands are adaptations, not completed tests. Model weights download separately from their upstream repository.

These small synthetic demonstrations are not performance or accuracy benchmarks. Nothing sends messages or changes accounts.

## Start here

Download and extract the ZIP, then follow its README. If you prefer Git:

```sh
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials/laya
```

Continue with the [Python 3.12 setup and first example](laya/README.md). The guide
includes dependency versions, model downloads, expected results, three demos,
category customization and troubleshooting. No RUNTIME account or private server
is required. The optional larger-model demo needs your own local model server.

## License and sources

Original RUNTIME example code and accompanying tutorial documentation are available
under the [MIT License](LICENSE). Upstream Laya code, model weights and dependencies
retain their own licenses. This license does not cover channel videos, narration,
portraits, logos or other brand assets. Models and environments are downloaded
separately; they are not bundled here.

## Updates and corrections

[Roundups and newsletters](https://github.com/Runtime-weekly/Blogs---Posts) are kept
in a separate archive. For a problem with this tutorial, open an issue with the
command, platform and a small synthetic example. Remove secrets, personal details,
private paths and customer data before sharing logs.
