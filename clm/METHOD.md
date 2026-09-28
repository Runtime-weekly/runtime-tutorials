# What was measured

The September 27, 2026 experiment used synthetic text observations and explicit
action descriptions. This companion preserves saved model responses and provides
the deterministic environments that applied their selected actions. The graphics
are replays, not camera input or live inference recordings.

## Models and implementation

- CLM backbone: `Qwen/Qwen3-8B`, revision
  `b968826d9c46dd6066d109eabc6255188de91218`.
- CLM decision heads: `Contrastive-LM/CLM-v0.1-8B`, revision
  `e939398d4556fcd9400c76fa8c5a513202f42b0a`.
- Jev: hosted `jev-1.13.0`; saved responses, not a downloadable local checkpoint.
- Laya: `convaiinnovations/laya`, revision
  `1c5edc17a7acd8701df6fc341c0d179f1c62c982`, explicit `typed-decisions`
  variant, Laya 0.3.4 on CPU. This is not the English base variant.

Original CLM question and sorting runs used a BF16 Transformers embedding
adapter on GPU and the released heads on CPU. The adapter selected the final
non-padding hidden state and applied L2 normalization. A separate replay through
the project's vLLM serving path selected the same answers on all 60 requests
(48 question requests plus 12 sorting calls). This establishes choice agreement
on those inputs, not numerical equality or equivalence on all inputs. Driving
used the vLLM path directly (0.27.2rc1, BF16, LAST pooling, activation enabled).
No task-specific training or post-result question tuning was performed.

## Denominators and transitions

The pilot has 24 cases: eight routing, eight evidence and eight next-step cases.
Reversing option order produces another 24 requests, not 24 new problems.
Original/reversed correct counts are CLM 11/11, Jev 24/24 and Laya 12/11,
each out of 24. Unchanged selections: CLM 24, Jev 24, Laya 21.

Sorting has six independent situations with a two-action limit per situation.
Bins reset between situations. Inspection reveals the true color but does not
finish the situation. Every executed action must be correct and the situation
must terminate to pass. Results: CLM 0/6, Jev 5/6, Laya 2/6, rules 6/6.
Do not count each inspection as a sorted object or accumulate physical bin
inventory across independent cases.

Driving has three fixed routes and one run per model per route. The simulator
waits for a response, applies its action, and returns the resulting observation.
Lane changes occur before forward movement. Every crossed cell is checked;
speed two cannot jump an obstacle. Runs stop on collision, off-road movement,
finish or the 40-action limit. All three models finish 0/3; the programmed
breadth-first planner finishes 3/3. The planner searches transitions explicitly;
it is not another learned model. This is discrete control, not real driving.

## Timing and limits

`seconds` records wall time around the decision call, before simulator execution.
Jev includes network transport; Laya includes its local wrapper and sometimes
initialization; CLM includes embedding/head processing and runtime effects.
For example, the first straight-route calls take 21.83 seconds for CLM and
8.07 seconds for Laya. Animation time must not be presented as measured latency.
The world does not advance while the caller waits for an answer.

These small, fixed diagnostic examples do not establish a general ranking,
production reliability, security robustness, or matched-hardware speed advantage.
Offline replay verifies consistency of the saved evidence. It does not reproduce
fresh neural inference, validate every probability, or establish that a hosted
service still behaves the same way today.
