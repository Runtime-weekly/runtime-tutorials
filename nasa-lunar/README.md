# NASA + IBM Lunar Foundation Model: local crater test

Companion to RUNTIME's **NASA + IBM’s Open Lunar Model — Tested Locally**.

We ran the released narrow-angle-camera crater detector on two official example images and four annotated test tiles. This is a small compatibility demonstration, not a reproduction of the authors' benchmark. The saved boxes and scores are in `recorded-results.json`; the original test harness is `run_crater_inference.py`.

## What the run showed

- The released checkpoint loaded and produced detections on a DGX Spark (NVIDIA GB10).
- Cold model loading: 17.861 seconds. First image: 1.263 seconds. Second image: 0.126 seconds. Four subsequent tiles: approximately 37–41 milliseconds each.
- Peak Torch CUDA allocation: 1,254,125,056 bytes. Process maximum RSS: 4,075,843,584 bytes. These overlap in scope on unified-memory hardware; do not add them.
- At score 0.5 the four tiles had 201, 128, 141 and 136 predictions. Prediction counts are not accuracy.
- Blue boxes are detector outputs. The orange target in the official after-image example is an annotation supplied by the notebook, not a model prediction. Green boxes are dataset annotations.

No precision, recall or mAP is claimed. The sample is too limited to support a broad accuracy ranking. We did not test printer-bed inspection or other non-lunar adaptations.

## Reproduce the inputs

Use a separate environment and download models/data from their official repositories. This repository does not redistribute weights or imagery.

```bash
git clone https://github.com/Runtime-weekly/runtime-tutorials.git
cd runtime-tutorials/nasa-lunar
git clone https://github.com/NASA-IMPACT/NASA-IBM-Lunar-Foundation-Model.git
git -C NASA-IBM-Lunar-Foundation-Model checkout d54c67aad513cb9daca444afa425cfb278e4fbf8
python3 -m venv .venv
. .venv/bin/activate
python -m pip install huggingface_hub
python download_inputs.py
```

`download_inputs.py` fetches only the checkpoint, backbone configuration, annotation JSON and four selected tiles, at pinned revisions. It verifies their recorded SHA256 hashes. The two example PNGs come from the pinned official code checkout and are checked too. Model/data downloads total roughly 1.7 GiB; dependencies need additional space.

## Environment and execution

Follow the [upstream installation instructions](https://github.com/NASA-IMPACT/NASA-IBM-Lunar-Foundation-Model/tree/d54c67aad513cb9daca444afa425cfb278e4fbf8) for Torch/CUDA and the packages in its requirements file. Choose wheels appropriate for your hardware. This test harness additionally imports matplotlib, numpy and Pillow.

Our measured environment was Linux ARM64, Python 3.12.3, Torch 2.11.0+cu130, torchvision 0.26.0+cu130, Lightning 2.6.6, timm 1.0.30 and torchmetrics 1.9.0. The upstream release declares newer minimum Torch/torchvision versions. **Our run is a compatibility observation using an existing isolated environment, not a validated fresh installation of upstream's dependency set.** We do not recommend downgrading a working environment to reproduce our package versions. Fresh installations, other GPUs and other operating systems have not been qualified by this companion.

Once dependencies and inputs are available, from this directory:

```bash
PYTHONPATH="$PWD/NASA-IBM-Lunar-Foundation-Model${PYTHONPATH:+:$PYTHONPATH}" \
  OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  python run_crater_inference.py
```

The harness requires CUDA and writes new measurements to `outputs/raw_results.json`, plus visual comparisons. It leaves `recorded-results.json` unchanged. It loads a PyTorch checkpoint; use the pinned official source and verify its hash before loading it. If registration imports fail, check that `PYTHONPATH` points at the upstream checkout and its required dependencies are installed. If a hash fails, preserve the file and investigate; do not bypass the check or claim it is the same experiment.

The original harness hash recorded with the run is `18fe500b00a7a1e1bd8aecc53b6e4698ad72741dae99e49585c080f4d8cccc8f`. The companion preserves that script unchanged. Current checks cover source compilation, input verification against the existing experiment, and recorded-result consistency; they do not constitute a new inference run or dependency-security audit.

## Sources and attribution

- [NASA announcement](https://science.nasa.gov/science-research/artificial-intelligence-lunar-foundation-model/)
- [Technical report](https://arxiv.org/abs/2609.13283)
- [Base model](https://huggingface.co/nasa-ibm-ai4science/NASA-IBM-Lunar-Foundation-Model)
- [Crater detector](https://huggingface.co/nasa-ibm-ai4science/Crater-Detection-NASA-IBM-Lunar-Foundation-Model)
- [NAC crater dataset](https://huggingface.co/datasets/nasa-ibm-ai4science/Sombench-NAC-Crater-Detection)

Imagery credit: NASA/GSFC/Arizona State University; NASA/IBM Research. Upstream code, data and weights retain their respective licenses and notices. RUNTIME's original companion scripts use this repository's MIT license; it does not relicense NASA/IBM assets, video, narration or branding.
