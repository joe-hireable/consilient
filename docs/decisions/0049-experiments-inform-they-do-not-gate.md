# 0049. Experiments inform; they do not gate construction

- **Status:** **ACCEPTED 21 August 2026.** Decided by Joe Brown. This ADR records his decision and
  corrects a practice the project had drifted into without ever deciding it.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown. The correction, the evidence and the objections are mine.
- **Relates to:** [`0039`](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md),
  [`0015`](0015-dogfooding-gate.md), and the `PROVISIONAL` status defined in
  [`README.md`](README.md).
- **Inquiry tier reached:** T0 assert — a process decision, correctly the principal's.

## Context

Joe, 21 August 2026:

> *"Can we start any actual harness development yet or are we still gated on experiments? We must
> not let progress be hindered. We should be able to proceed quickly with educated assumptions even
> pending experiments. Experiments can prompt changes to be promoted etc but should not gate
> progress."*

**He is right, and the honest answer to his question is that the project was never gated — it was
under-built.** Measured on the day: [measured]

| | |
|---|---|
| Product code in `src/consilient/` | **2,223 lines** — recorder, projection, β meter, CLI, refuse-only budget |
| Coordinator, router, dispatcher | **none** |
| Adapters in the product | **none.** Seven exist, all under `docs/10-research/experiments/exp05/` |
| Documented dispatch requirements | **fifteen**, every one measured from a real failure |
| Dispatch requirements implemented | **zero** |

Stage 3 was entered on 20 August. ADR-0039 had already separated entry from exit: **Gate B gates
*dependence* on the harness, not *construction* of it.** Nothing was stopping the build. Two days of
effort went into measurement, and the orchestrator dispatched work by hand while the product
contained no dispatch code at all.

## Decision

1. **Experiments do not gate construction.** A registered, unrun experiment is a reason to record an
   assumption, never a reason to stop building.
2. **Where the evidence is absent, build on a stated assumption and record it as `PROVISIONAL`**,
   with the experiment that would confirm or kill it. This is not new machinery — it is precisely
   what `PROVISIONAL` already means in this repository: *accepted for now, resting on `[simulated]`
   or `[asserted]` evidence, with a named experiment that would confirm or kill it.*
3. **Experiments promote, demote or kill what is already built.** That is their job. A result that
   arrives after the code is a normal and expected event, not a failure of sequencing.
4. **What experiments DO still gate is unchanged and remains gated**: `routing_orchestration_enabled`
   flips only when every gate condition passes, and Gate B still governs pointing the harness at any
   repository other than this one.

## Why the drift happened, because naming it is the point

The project's discipline is unusually strong on evidence, and that strength has an obvious failure
mode: **if a claim needs evidence before it may be believed, it is a short step to believing that a
component needs evidence before it may be built.** Nobody decided that. It was inferred from the
surrounding culture and it cost two days of construction.

The distinction that was missing:

- **A claim about the world** needs evidence before it is asserted. That discipline stands and is
  the most valuable thing here.
- **A component** needs a stated assumption, a falsifier, and a reversal path. It does not need a
  finished experiment, because building it is frequently how the experiment becomes possible at all.

The second is what `PROVISIONAL` was for, and the project had been using it only for decisions.

## Evidence against

- **This is the loosening it looks like, and it should be read as one.** "Build on assumptions" is
  how every project that abandoned rigour began. The defence is that the assumption must be
  *recorded*, *falsifiable* and *reversible* — and if those three are skipped, this ADR has been
  used as cover for exactly what it claims not to be.
- **The project has already been burnt by an unevidenced number this week.** A figure of 72.8–75.9%
  with no producing script propagated into six documents including a draft paper, and was caught by
  an adversarial audit rather than by any check. [measured] **That was an unrecorded assumption
  wearing the appearance of a measurement**, which is the precise failure this ADR must not license.
  The difference is the tag: `[asserted]` is honest, and a number presented as `[measured]` is not.
- **Building before measuring can make the measurement harder**, not easier — a component built on a
  wrong assumption creates artefacts, habits and dependencies that bias the experiment that comes
  later. EXP-52 is currently at risk of exactly this: the corpus it needs was shaped by earlier work.
- **Nothing here establishes that speed is the binding constraint.** The two days were not wasted;
  they produced β = 0.3132, a refuted independence assumption, and four gate defects found before
  anyone depended on them. A version of this project that had built faster and measured less would
  have shipped a harness with unmeasured error and no way to know.

## Consequences

**Positive.** Construction resumes immediately, and the dispatch layer — fifteen requirements,
every one measured from a real failure, zero implemented — becomes buildable work rather than a
document.

**Negative.** More of the codebase will rest on `[asserted]` foundations at any given moment, and
the number of PROVISIONAL decisions carrying unrun experiments will grow. **A PROVISIONAL decision
unconfirmed after three months is already defined as a bug in this repository; that rule now matters
more, not less.**

**Neutral but load-bearing.** The experiment register becomes a backlog against built code rather
than a prerequisite queue in front of it. That is a different document in practice, and it should be
read as one.

## Enforcement

- **Check:** every `PROVISIONAL` decision names an experiment ID that exists in the register. A
  PROVISIONAL with no falsifier is an assumption with no way out, which is the thing this ADR
  forbids.
- **Check:** the existing evidence-tag discipline is unchanged and is the load-bearing control. A
  component built on an assumption is fine; a *number* presented as measured when it was assumed is
  the failure, and the corrections of 21 August are the standing example.
- **Check:** `routing_orchestration_enabled` remains derived from the gate conditions and is not
  reachable by inference. Already enforced by
  `test_every_gate_condition_has_a_reachable_pass_state`.

## What would overturn this

If the ratio of PROVISIONAL to ACCEPTED decisions keeps rising while the register's unrun backlog
grows, the project is accumulating unfalsified assumptions and calling it progress. **That is
measurable from the repository itself** — count both, monthly — and if it holds for a quarter, this
ADR is being used as cover and should be superseded rather than defended.
