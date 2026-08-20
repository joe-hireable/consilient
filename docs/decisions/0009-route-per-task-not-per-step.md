# 0009. Route per task, not per step

- **Status:** PROVISIONAL
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request
- **Inquiry tier reached:** T1 ground — **this one should be re-decided from measurement**
  (see the experiment register, EXP-06)
- **Executable model:** none yet.

## Context

Q9. The cascade could make its routing decision once per ticket, or re-evaluate at every
tool-call boundary within a run. Per-step is finer-grained and might capture more of the
available gain.

## Decision

Route **once per task**. Escalate on verifier failure at task completion, not mid-run.

## Evidence

- `[algebra]` Per-step routing multiplies verifier invocations by the number of tool calls,
  and **the verifier is the expensive component** — running a test suite, not a model call.
  A 20-step run would invoke the suite 20 times.
- `[algebra]` **It breaks the β measurement.** β is defined over artefacts a human judged
  (`0002`). There is no human verdict on an intermediate tool call, so per-step routing has
  no label to learn from and no way to compute its own error rate. A project whose product
  is a measurement cannot adopt a granularity at which the measurement does not exist.
- `[cited]` Consistent with the routing literature, which is predominantly per-query.
  Dekoninck et al. (ICML 2025) treat the unit of routing as the request.

## Evidence against

- `[cited]` *When to Think Deeply: Inhibitory Deliberation* (arXiv:2606.06745) argues that
  pre-response routing discards a crucial signal — the fast answer itself — and that
  deciding *after* seeing a candidate response outperforms deciding before. That argument
  applies within a task and is not addressed here.
- If most failures occur early in a run, a step-level abort would save real work that
  per-task routing wastes. **Unmeasured.**
- Long agentic runs are not single inductions; treating a 40-step trajectory as one routing
  unit may be too coarse to be meaningful.

## Consequences

**Positive.** One verifier invocation per attempt. β stays measurable. Simpler orchestrator.

**Negative.** Wasted work when a run is doomed early. No mid-run correction.

**Neutral but load-bearing.** Fixes the ticket as the unit of routing, of verification and
of the β label — three things that must agree.

## Enforcement

- Check: a test asserts exactly one routing decision per ticket attempt in the trajectory
  log. More than one is a bug.

## What would overturn this

**EXP-06** in the experiment register: instrument where in a run failures occur. If the
distribution is heavily front-loaded, reopen and consider a step-level abort (distinct from
step-level *routing*, which the β argument still blocks).

## Publication candidate?

No.
