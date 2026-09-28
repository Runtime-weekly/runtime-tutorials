# Try the tests yourself

Run these commands from this `clm` directory using Python 3.10 or newer. The
offline tools use only the standard library: no installation, model download,
credentials, GPU or network is required. They were tested with Python 3.12 on
Linux ARM64. Other platforms are not independently qualified.

```sh
python3 -B -m unittest -v test_simulators
python3 -B replay.py
```

The first command executes 11 simulator tests. The second checks the exported
saved responses against their observations, selected actions, state transitions,
outcomes and pilot option order. Expected: 103 verified simulator transitions;
sorting pass counts CLM 0, Jev 5, Laya 2, rules 6; driving pass counts 0, 0, 0, 3.
Pilot original/reversed scores are 11/11, 24/24 and 12/11 out of 24. The JSON
report also computes descriptive call-time summaries directly from saved data.
A missing or inconsistent required record stops verification with an error.

Run your own deterministic actions separately from the historical model data:

```sh
python3 -B experiment.py sorting --case 03
python3 -B experiment.py sorting --case 03 --actions inspect,inspect
python3 -B experiment.py sorting --case 05 --actions hold
python3 -B experiment.py driving --route straight
python3 -B experiment.py driving --route straight --actions hold,hold,hold,hold,hold,hold,hold
```

Expected: the sorting rule inspects then places blue; repeated inspection leaves
the item unresolved; holding the fifth case is wrong. The driving planner reaches
the finish; seven holds collide. Each command prints the actual before/after
states from a new simulator execution. Explicit action sequences stop when
exhausted, when the environment terminates, or at the task's action budget;
extra actions after termination or beyond the budget are not executed.

You may change rules or cases in a separate copy and explore their consequences.
Such changes are new experiments and must not be represented as the original
model results. `replay.py` intentionally rejects records inconsistent with the
included environment. The tools only read the saved data and print results.

## Fresh model inference is a separate project

This export does not provide a newly qualified model installation recipe or
silently reuse a private server. For new model runs, consult the primary sources
in SOURCES.md, check their current licenses and dependency advisories, and record
the exact runtime, checkpoint revisions, input formatting and hardware. Use the
observations and action schemas shown here, save every response, and feed the
selected action back into the simulator. Do not expose hidden sorting color
before inspection. Hosted Jev requires your own authorized access and may incur
charges; none of these offline commands contacts it.

Keep new outputs separate from `data/`. Historical runtime versions in METHOD.md
describe the measured evidence, not a recommendation to install older software.
