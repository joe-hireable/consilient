# 0050. Gate on effect size, not on the mere existence of uncertainty

- **Status:** **ACCEPTED 21 August 2026.** Decided by Joe Brown. Sharpens
  [`0049`](0049-experiments-inform-they-do-not-gate.md) rather than superseding it.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown. The mechanism, the threshold's weakness and the objections are mine.
- **Inquiry tier reached:** T0 assert — a process decision, correctly the principal's.

## Context

ADR-0049 settled that experiments inform rather than gate construction. It did not say **when an
experiment legitimately does gate something**, which left the door open to the same drift under a
new name.

Joe, 21 August 2026:

> *"it's not worth it to gate an important feature for 5 days for an experiment that could only ever
> matter <5% — those numbers matter no matter how small — but should not gate real progress on
> working code — just improve it"*

Both halves are load-bearing. **The small numbers still matter and still get measured.** What they
do not do is hold up the feature.

## Decision

**An experiment gates construction only when its largest possible effect would change the
decision.** Not when it is merely unresolved.

The test, applied before an experiment is allowed to block anything:

1. **What is the largest effect this experiment could plausibly show?** If the answer is small —
   a few percent on a rate, a modest constant factor — it does not gate.
2. **Would that largest effect change what gets built, or only how well it works?** An experiment
   that can only *tune* a component never gates it. One that could show the component should not
   exist does.
3. **What does the delay cost?** Five days of blocked feature work against a result that can only
   adjust a parameter is a bad trade and should be named as one.

**A small effect is still measured, still recorded, and still improves the thing later.** It is
demoted from gate to backlog, not discarded. The distinction is between *what we must know before
building* and *what we want to know about what we built*.

## Why this needed saying separately from ADR-0049

ADR-0049 removed the general block. Without this, the obvious next failure is an argument that some
*particular* experiment is the exception — and every experiment feels like the exception to whoever
registered it. **The magnitude test is what makes ADR-0049 enforceable rather than a sentiment.**

It also names something the project had backwards. Sixty-five experiments are registered and most
are not runnable. That register was accumulating as a *prerequisite queue in front of* construction.
Under ADR-0049 and this ADR it becomes a **backlog against built code**, and the ordering principle
is effect size.

## Evidence against

- **"Largest plausible effect" is a guess, and it is guessed by the party who wants to proceed.**
  That is the same conflict of interest recorded against every gate amendment made on 20 August, and
  flagging it is not the same as fixing it. The only real mitigation is that the guess is written
  down before the experiment runs, so it can be checked against the result afterwards.
- **Small effects compound.** Three components each built on a 4% assumption are not 4% wrong. The
  threshold has no mechanism for accumulation, and this project has no measurement of how many such
  assumptions it is carrying.
- **This project has already been burnt by exactly this shape.** A figure of 72.8–75.9% with no
  producing script propagated into six documents including a draft paper, because nobody asked
  whether it was measured. [measured] **An unstated assumption is not made safe by being small.**
- **"5%" is not derived from anything.** It is a round number the principal used conversationally.
  It should not become a threshold in code, and this ADR deliberately gives no numeric constant —
  the test is comparative, not absolute.
- **The counterfactual is untested.** The two days that produced β = 0.3132, a refuted independence
  assumption and four gate defects were spent measuring rather than building. Nothing establishes
  that a faster, less measured version of this project would be ahead now, and the honest position
  is that we do not know.

## Consequences

**Positive.** Feature work proceeds at the speed of engineering rather than the speed of the slowest
registered question. The register becomes ordered by consequence.

**Negative.** More components rest on assumptions at any moment, and the number of unfalsified
PROVISIONAL decisions grows. **A PROVISIONAL unconfirmed after three months is already defined as a
bug here; that rule now carries more weight.**

**Neutral but load-bearing.** This makes "what is the largest effect this could show?" a required
field in practice for any experiment claiming to gate something — and most registrations do not
currently answer it.

## Enforcement

- **Check:** an experiment may be cited as blocking a build only if its register entry states the
  largest effect it could show. **An entry that does not state it cannot gate.** This is mechanical:
  the field is present or it is not.
- **Check:** ADR-0049's existing control stands — every `PROVISIONAL` decision names an experiment
  that exists in the register.
- **Check:** the evidence-tag discipline is untouched and remains the real control. Building on an
  assumption is permitted; presenting an assumed number as `[measured]` is not, and the corrections
  of 21 August are the standing example of what that costs.

## What would overturn this

If a component built under this ADR is later found wrong in a way an unrun experiment would have
caught, **and the experiment's effect had been judged small**, then the magnitude test is
mis-calibrated and the threshold is too permissive. That is a specific, observable event and it
should be recorded against this ADR when it happens rather than explained away.
