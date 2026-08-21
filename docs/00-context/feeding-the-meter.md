# Feeding the β meter — the two-event version

**Written 20 August 2026**, because the briefing's top finding is that the meter has never
received a row of its own input: 60 trajectory events, 60 distinct event kinds, zero
`attempt.outcome` events, zero human verdicts. `consil beta` says `insufficient data (0 human
rejections, need 30)` and it is right. [measured]

The verifier outcome and human verdict are separate append-only events joined by one stable
`attempt_id`. [measured] Replay resolves them into one row for β; `task` is not the join key,
because retries legitimately give one task several attempts. [measured]

## The one-command version

`scripts/verdict.py` writes both events below in one call, in the required order, sharing one
generated `attempt_id`, through the same `append()` writer.

```bash
python scripts/verdict.py reject "fix pagination off-by-one" --checks pass
python scripts/verdict.py accept "tighten the retry backoff"  --checks fail
```

It exists for two measured reasons. The hand-written form below **does not survive PowerShell**:
5.1 strips the inner double quotes before Python sees them, and the documented command exits 2
with `--event is not valid JSON`. [measured, 21 Aug 2026] And a verdict whose `attempt_id` has no
recorded outcome appends with exit 0 and then refuses to project forever, on an append-only log
— thirty hand-written pairs is thirty chances at that. [measured]

`--checks` is required, not defaulted: if the only artefacts you review are the ones whose checks
already passed, every rejected row carries `verifier_accept: true` and β is 1.000 by construction
rather than by measurement. [cited, `src/consilient/beta.py`]

The hand-written form below remains the schema of record, and is still the way to give a verdict
on an attempt whose outcome another process already logged.

## First record the verifier outcome

Replace the timestamp with the current RFC3339 clock value and allocate the attempt identifier
when the attempt is created. [asserted]

```bash
consil record --event '{
  "v": 1,
  "ts": "<current RFC3339 timestamp>",
  "event": "attempt.outcome",
  "actor": "consilience-verifier",
  "data": {
    "attempt_id": "attempt-7f20c8b1",
    "task": "some-task-id",
    "task_family": "repair",
    "verifier_version": "pytest+mypy",
    "verifier_accept": true
  }
}'
```

## Later record the human verdict

The verdict carries the same `attempt_id` and no repeated verifier result. [asserted]

```bash
consil record --event '{
  "v": 1,
  "ts": "<current RFC3339 timestamp>",
  "event": "attempt.verdict",
  "actor": "joe-brown",
  "data": {
    "attempt_id": "attempt-7f20c8b1",
    "human_verdict": "reject",
    "principal": "joe-brown",
    "via": "cli"
  }
}'
```

`verifier_accept` is what the automated checks said. `human_verdict` is what the human principal
said. **β is the rate at which those disagree in the dangerous direction** — checks accepted,
the human rejected. [algebra]

## What the invariant tests verify on 20 August

| | result |
|---|---|
| Deferred verdict references its attempt | one projected row; β sees one rejection [measured] |
| Agent tries to author a verdict or correction | refused under V0-18 [measured] |
| Verdict references an unknown attempt | projection fails closed [measured] |
| A second ordinary verdict references the same attempt | projection fails closed [measured] |

V0-18 applies to both `attempt.verdict` and `attempt.verdict.correction`; a null verdict is also
refused rather than treated as an absent field. [measured] `attempt.outcome` cannot carry a human
verdict, eliminating the second projection path that previously bypassed the authority guard.
[measured]

## Three things worth knowing before the habit forms

**1. `ts` must be the real clock.** `append()` refuses a timestamp more than fifteen minutes out.
That check exists because the orchestrator spent last night writing invented timestamps into this
very log while auditing other people's instruments. To record something that happened earlier, put
the occurrence time in `data` and let `ts` record when it was written.

**2. Only the principal may author a verdict.** `actor` must equal `data.principal`, and `via`
must name the channel it arrived through. No agent can supply this for you, by design — if one
could, β would be the agents grading themselves.

**3. Rows with no `human_verdict` are excluded from both numerator and denominator.** Recording
the verifier outcome alone creates one unlabelled row. The later verdict amends that row rather
than adding another attempt, so it does not move β until the verdict exists and cannot double the
observation set. [measured]

If the human changes their judgement, append `attempt.verdict.correction` with `attempt_id`, the
`previous_verdict`, the new `human_verdict`, and a non-empty `reason`. [asserted] A plain second
verdict is refused; a correction whose expected prior value does not match is also refused, so
replay never silently chooses the last value. [measured]

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
