# 0100. Measure β prospectively from live dispatch, and retire history mining

- **Status:** PROVISIONAL — rests on `[asserted]` reasoning; EXP-141 confirms or kills it
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the unknown is an empirical rate, and a model of it would assume the
  quantity the experiment exists to measure.

## Context

Gate A1 requires β measured on two independently verified repositories with a confidence interval.
The route designed for it was EXP-01: mine git history, treat a later revert or fix as evidence that
a check had accepted bad work, and estimate β from the ratio.

**EXP-01's stopping rule fired.** The interval would not narrow below ±0.05 and the method was
retired without a usable measurement. The gate governing whether Consilient may route, block or
orchestrate anything is therefore currently unpassable — not because the work is unfinished, but
because the route to it was falsified.

Changing a gate is reserved to the principal under ADR-0039. He decided on 23 August 2026 to replace
the route and keep the bar.

## Decision

We measure β **prospectively**, from live dispatch, rather than retrospectively from history. Every
dispatch already produces the two things the measurement needs: an artefact, and a verdict from the
checks. Where a human later rejects an artefact the checks accepted, that is a false accept, and it
is recorded as one at the moment it happens rather than inferred from a commit graph months later.

**The bar does not move.** Gate A1 still requires two independently verified repositories and an
interval. Only the instrument changes.

## Evidence

- `[measured]` EXP-01 is retired. `consil doctor` reports A1 FAIL with the reason: the stopping rule
  fired because history mining could not narrow the interval below ±0.05.
- `[measured]` The trajectory already records dispatch outcomes and verdicts as first-class events,
  so prospective capture requires no new instrumentation — only that the join between them is
  recorded when it happens.
- `[cited]` The generation–verification gap is measurable, model-specific, and predicts how much
  self-improvement is available (arXiv:2412.02674, ICLR 2025). It is the same shape as β and supports
  measuring the accept/reject join directly rather than reconstructing it.
- `[asserted]` A revert in git history has many causes that are not a verifier false-accept —
  changed requirements, taste, a later refactor. That confound is the most likely reason EXP-01's
  interval would not narrow, and prospective capture removes it by construction.

## Evidence against

- `[asserted]` Prospective measurement is slower and cannot be backdated. The gate stays shut for
  longer than a retrospective method would have required had it worked, and there is no way to
  shorten that with more effort.
- `[asserted]` It requires a human rejection signal to exist at all. On work nobody reviews, β is
  unmeasurable by this route — which means the measurement is best exactly where it is least needed
  and worst where autonomy matters most. **This is the strongest objection and it is not resolved.**
- `[measured]` Sample size is the binding constraint. Twenty units retired so far have produced no
  recorded human rejections, so the current interval would be uselessly wide. EXP-141 fixes the
  stopping rule in advance rather than discovering this later.

## Consequences

**Positive** — the confound that killed EXP-01 is removed. The measurement uses signals the system
already produces, so no separate corpus study is needed.

**Negative** — Gate A stays shut until enough reviewed dispatches accumulate. That is real delay and
it is not recoverable by working harder.

**Neutral but load-bearing** — β becomes a property of live operation rather than of a corpus, so it
drifts as the system changes. That is more honest and it means the number needs re-measuring rather
than establishing once.

## Enforcement

- Check: `tests/test_v0_invariants.py` already refuses a PROVISIONAL ADR naming an experiment absent
  from the register, and `.github/scripts/check_adr_experiments.py` refuses it at commit time.
- Check: `consil doctor` continues to compute A1 from the register rather than from any
  hand-maintained statement, so this ADR cannot open the gate by assertion.
- Fails CI: yes.
- Added in the same commit as the implementation: yes — both checks already exist and run.

## What would overturn this

EXP-141 reaching its stopping rule without a usable interval, exactly as EXP-01 did. If prospective
capture also cannot narrow β below ±0.05 within the pre-registered number of reviewed dispatches,
then the problem is not the instrument and the gate's design needs revisiting rather than its route.
That would be the second falsified route, and it should be treated as evidence about the gate.
