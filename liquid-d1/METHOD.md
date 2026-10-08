# Method and limits

Model: LiquidAI/d1-3B, revision051bcc464b01b9f92942b364d9586b0ef5912432.
Platform: Linux ARM64, Python3.12, NVIDIA GB10. BF16, SDPA, direct CUDA loading.
Full historical package versions appear in environment-recorded.json. The four
components of the nvidia-curand version are stored as a numeric array.

Three public JPEGs were orientation-corrected, converted to RGB, resized with
Lanczos to a maximum384-pixel longest side without cropping, then saved as fresh
pixel-only PNGs. Source and resulting PNG hashes are in photos.json. The actual
model inputs were visually reviewed by an agent before inference. They are not
human-held-out labels or an unseen evaluation set.

Each prompt requests a `readiness` choice. A requires an apple AND a banana.
B requires an apple AND no visible banana. Exact wording and option definitions
are in experiment.json. The model API was called as
`model.system_one(None, question, images=[image])`; the missing-image control used
`images=[]`. Normal option order was READY, WAIT, UNCLEAR; reversed order was
UNCLEAR, WAIT, READY. All18 question objects and answers are in recorded.json.

The first five calls formed a small checkpoint; thirteen frozen calls followed.
The record contains six primary calls, six option-order checks and six no-image
calls. No-image prompts repeat once for each paired photo, so there are only two
unique text-only inputs. Their `expected` field is the paired image's original
label and must not be scored as text-only ground truth.

## What was measured

One still image per call. Instrumentation counted one forward pass and zero
generated output tokens per call. Explicit CUDA synchronization bracketed the
API and internal preprocessing/model timings. API timing includes internal
image processing, transfer, model work, scoring and synchronization overhead.
File decoding, external resizing, model loading, network, capture and action are
excluded. No optimized throughput, camera, Jetson or end-to-end robot claim.

Model load took32,213.044813ms. The first API call took1,678.141876ms. The next11
image calls had median61.692067ms, minimum58.719701ms and maximum65.45385ms.
No-image timings are separate; do not combine them with the warm image median.

The `raw.answers.readiness` object is the model output. Its `confidence` field is
an option-relative score, not a proven probability of correctness. `action`
comes from an unused application wrapper requiring repeated READY decisions;
the streak resets for each still-image call. It can say WAIT even when the model
chooses READY. This was not a controller or temporal stability test.

## Reproduction status

These files allow inspection and deterministic validation of the saved record.
They do not certify a fresh model installation or repeated inference on a new
system. Original measurements remain unchanged. Scores/timings may differ with
hardware, package versions or execution settings.

Historical pins include Pillow12.2.0, setuptools81.0.0 and torch2.11.0, which were
flagged by an October8,2026 OSV lookup. They are not recommended installation pins.
Relevant advisory records include:

- https://github.com/python-pillow/Pillow/security/advisories/GHSA-45hq-cxwh-f6vc
- https://github.com/advisories/GHSA-h35f-9h28-mq5c
- https://github.com/advisories/GHSA-rrmf-rvhw-rf47

A separate patched setup candidate remains unqualified for model inference and
is not included as installation instructions here. Non-inference preparation
confirmed that Pillow12.3.0 reproduces the three original PNG hashes. That does
not establish full model compatibility. No new inference was run to prepare
this evidence export. Cold source downloads and other platforms were not tested.
