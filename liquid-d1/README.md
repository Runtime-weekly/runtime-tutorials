# Liquid d1-3B — public-photo experiment record

RUNTIME tested the same photos under two different written rules. This folder
contains the exact prompts, recorded decisions, timings and input provenance.
It is an evidence record, not a fully qualified model installation tutorial.

Liquid AI released d1-3B on October 7, 2026.
[Official release](https://www.liquid.ai/blog/d1-open)

## Check the record

Python 3.12, no third-party packages, network or GPU required:

```sh
python3 -B validate.py
python3 -B -m unittest test_record.py
```

The validator checks all18 saved calls against the exact rule text, choice order,
photo hashes and recorded diagnostic outcomes. It does not rerun the model or
independently establish the truth of the observations.

## Results

- Three public photographs, two rules: six primary decisions matched labels
  written before inference by an agent inspecting the images.
- Six reversed-choice calls preserved the chosen answers. They are stability
  checks, not six new independent accuracy samples.
- Removing the image produced UNCLEAR under Rule A and READY under Rule B.
  Those two distinct text-only prompts were each repeated three times.
- Eleven warm still-image API calls:61.7ms median. First image call:1,678ms.
  Loading:32.2seconds. These are different measurements, not robot frame rate.

No general accuracy, unseen-data, reliable abstention or calibrated-confidence
claim follows from this small test. Public photos may have appeared in training.

Read `METHOD.md` for the exact procedure, timing boundaries, historical dependency
advisories and limitations. `recorded.json` preserves typed outputs and timings;
`experiment.json` and `plan.json` preserve prompts and order; `photos.json`
contains source URLs, credits and hashes without redistributing images.
`model-files.json` identifies the pinned upstream files without bundling them.

Related RUNTIME coverage: [JEV-27B Tested Locally](https://youtu.be/hYSeZrYUDxA).
This d1 experiment is not a head-to-head comparison with JEV.

RUNTIME's code is MIT. Model/photo terms remain separate in `THIRD_PARTY.md`.
No voice material, video or brand assets are included.
