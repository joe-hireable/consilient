# Feeding the β meter — the one-command version

**Written 20 August 2026**, because the briefing's top finding is that the meter has never
received a row of its own input: 60 trajectory events, 60 distinct event kinds, zero
`attempt.outcome` events, zero human verdicts. `consil beta` says `insufficient data (0 human
rejections, need 30)` and it is right. [measured]

Nothing needs building. The event kind exists, the projection applies it, `beta.py` computes from
it, and `consil record` writes it. What is missing is the habit, and the half only Joe can supply.

## The one command

```bash
consil record --event '{
  "v": 1,
  "ts": "2026-08-20T09:15:00+01:00",
  "event": "attempt.outcome",
  "actor": "joe-brown",
  "data": {
    "task": "some-task-id",
    "task_family": "repair",
    "verifier_version": "pytest+mypy",
    "verifier_accept": true,
    "human_verdict": "reject",
    "principal": "joe-brown",
    "via": "cli"
  }
}'
```

`verifier_accept` is what the automated checks said. `human_verdict` is what you said. **β is the
rate at which those disagree in the dangerous direction** — checks accepted, you rejected.

## What is checked, verified end to end on 20 August

| | result |
|---|---|
| Human authors their own verdict | **accepted**, `rc=0` [measured] |
| Agent tries to author one | **refused**, `rc=2`, *"a human_decision event must name its principal"* [measured] |
| β picks it up | `insufficient data (1 human rejections, need 30)` [measured] |

That middle row is V0-18 holding **through the command line**, not merely in a unit test. Until
this morning the invariant was bypassable by exactly this route — an `attempt.outcome` carrying a
`human_verdict` with no `human_decision` sailed straight through into the table β is computed
from. It does not now.

## Three things worth knowing before the habit forms

**1. `ts` must be the real clock.** `append()` refuses a timestamp more than fifteen minutes out.
That check exists because the orchestrator spent last night writing invented timestamps into this
very log while auditing other people's instruments. To record something that happened earlier, put
the occurrence time in `data` and let `ts` record when it was written.

**2. Only the principal may author a verdict.** `actor` must equal `data.principal`, and `via`
must name the channel it arrived through. No agent can supply this for you, by design — if one
could, β would be the agents grading themselves.

**3. Rows with no `human_verdict` are excluded from both numerator and denominator.** Recording
the verifier outcome alone is still worth doing — it costs nothing and the verdict can be added
later as a second event — but it does not move β until a verdict exists.

## What it takes to get an answer

`MIN_REJECTIONS = 30` gates the `measured` verdict. But the arithmetic is harsher than that
constant suggests: against β\* = 0.111, a **flawless** record of 0/30 gives a Wilson upper bound of
0.11352 and fails; 0/31 gives 0.11026 and clears. Realistically you need **48** rejections at true
β = 0.02, **62** at 0.04, **137** at 0.06, **368** at 0.08 — and at or above 0.111, no sample size
clears it at all. [measured]

Those are **rejections**, not reviews. At a plausible rejection rate, thirty of them is weeks of
ordinary working. **Which is exactly why the clock should start now rather than after the
question becomes urgent.**

## The honest caveat

This does not make β decision-grade on its own, and it does not resolve which conditional β
should be — see `beta-axis-defect-2026-08-20.md`, which is decision A in the briefing. It does
mean that whichever way that decision goes, the input exists to compute it from, instead of the
project having spent another week gating an architecture on a number nothing produces.

A meter with one honest row is in a different category from a meter with none.
