# CLM, Jev and Laya: inspect the decisions

RUNTIME's synthetic diagnostic pilot, item-sorting simulation and discrete driving experiment, recorded September 27–28, 2026. This companion contains research notes, frozen requests and responses, portable experiment/replay code, and an interactive saved-data viewer.

## Open the results

Download this repository using **Code → Download ZIP**, extract it, and enter the `clm` folder. Python 3.10+ is sufficient; no extra packages, accounts, models or GPU are required for the offline tools.

```sh
python3 visualizer.py
python3 replay.py
python3 -m unittest test_simulators.py
```

Open the generated **visualizer.html** in your browser. Choose pilot, sorting or driving; choose a system and case; step through actual requests, selected actions and state changes. The generated HTML is self-contained and makes no network requests. On Windows use `py -3` instead of `python3` if necessary. Validation details are in [REPRODUCE.md](REPRODUCE.md).

The visualizer is a saved-data inspector, not a chat interface or live model service. [REPRODUCE.md](REPRODUCE.md) explains running and modifying the deterministic experiments and the limits of fresh inference reproduction. No live inference runner or model weights are bundled. Original private runtime wrappers are deliberately excluded; offline replay does not demonstrate a new model inference run.

## What is included

- [Research and exact model identities](SOURCES.md), [method and limitations](METHOD.md).
- `data/cases.json` and `data/protocol.json`: the frozen 24-case pilot.
- `data/pilot/`: 48 recorded calls per system, including paired reversed insertion order. CLM records also retain the no-head embedding ablation.
- `data/sorting/`: six reset scenarios for each of CLM, Jev, Laya and a deterministic rule baseline.
- `data/driving/`: three routes for each system and the rule baseline, with every saved action and transition.
- Python simulator, replay and viewer code. Saved numbers are preserved; private local model paths were removed from metadata.

## Read the results narrowly

**Code baseline revision:** the driving viewer includes both **Code original:
shortest-path planner** and **Code v2: lane-keeping planner**. The latter was
added after feedback, prioritizing fewest safe steps and then fewest lane
changes. It is a new deterministic controller run, not a neural-model rerun.
Original traces remain unchanged. See [METHOD.md](METHOD.md) for the objective
and privileged access to simulator rules.

In the original-order pilot, CLM scored 11/24, hosted Jev 24/24 and Laya typed-decisions 12/24. The same 24 cases in reverse option insertion order produced 11/24, 24/24 and 11/24. These are authored diagnostics, not a general leaderboard. The no-head Qwen embedding ablation scored 8/24; it is not a native generative Qwen baseline.

Driving uses supplied numeric road geometry, not camera images. A deterministic shortest-safe-route planner completed the three routes; none of the three tested model configurations completed them. The planner knows the simulator's transition rules, so it is not an equal-information learned baseline. Model outcomes do not establish general driving ability.

Local CLM CUDA, local Laya CPU and hosted Jev call times have different boundaries. First-call costs and cache effects matter. Reported probability/confidence fields do not establish calibration. Do not infer why a model failed merely from its chosen action.

Original RUNTIME code and documentation use the repository's [MIT license](../LICENSE). Upstream model weights, dependencies and hosted services retain their own terms. Videos, narration and brand assets are not included or licensed by this companion.
