# 0103. Make contract-β the gate quantity, and keep human-β as alignment rather than a blocker

- **Status:** PROVISIONAL — the identification is exact, but that a held-out contract suite has
  errors independent of the checks is `[asserted]`. EXP-142 confirms or kills it.
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Supersedes:** 0100 — its route to Gate A1 is replaced. Its diagnosis of EXP-01 stands.
- **Relates to:** 0002 (β as the organising quantity), 0080 (the estimand separation and its algebra),
  0039 (gate changes are reserved to the principal)
- **Inquiry tier reached:** T2 algebra, on ADR-0080's identification result
- **Executable model:** none — the identification is exact; what is unknown is an empirical error
  correlation, and a model of it would assume the quantity EXP-142 exists to measure.

## Context

Gate A1 requires β with an interval on two independently verified repositories. Two routes to it
have now been falsified.

**EXP-01** mined git history and its stopping rule fired: the interval would not narrow below ±0.05
and the method was retired. [measured] **ADR-0100** replaced it with prospective human verdicts.
That route is not falsified in principle, but its rate is: `beta.MIN_REJECTIONS = 30` and the
trajectory holds **exactly one** human rejection, recorded on 21 August. [measured] At the observed
rate the gate opens in months, and the constraint is the principal's attention rather than anything
the system can influence.

The principal raised the deeper objection on 23 August 2026: he is, by design, less qualified than
the system to judge its output, so a gate resting on his judgement measures agreement with a weaker
judge rather than correctness. **He is right about β_H, and the conclusion he drew from it is the
important one:** the human belongs at the *statement of intent*, where his authority is definitional
and cannot be outranked, not at the *judgement of output*, where it is a ceiling.

ADR-0080 already did the algebra that makes this precise. With `A` for verifier acceptance, `H` for
an independent human rejection, `T` for a candidate-time contract violation and `C` for a
demonstrated later repair: human β is `P(A | H)`, while consequence and contract signals observe a
different quantity and **"say nothing about `H` without labels"**. [algebra, ADR-0080] Those signals
are not a cheaper estimate of β_H. They estimate β_T, and this ADR's decision is that **β_T is the
quantity Gate A should have been testing.**

This is a one-way door on what "safe to act" means in this system.

## Decision

**Gate A1 tests β_T — the rate at which the automated checks accept an artefact that violates a
contract stated before the work began.** β_H is retained, measured opportunistically whenever the
principal does review something, reported separately, and **never blocking**. It is renamed for what
it honestly is: the rate at which checks accept work the principal would reject, which is a measure
of alignment with him rather than of correctness.

**The contract must be held out.** A contract the builder can read is a target it optimises against,
and β_T measured on a visible contract measures nothing. The contract is therefore derived from the
same stated intent by a **different model family**, committed before the build dispatch, and never
placed anywhere the builder or its checks can read.

β_T's denominator is contract violations, which are plentiful, so sample size stops being the
binding constraint. Nothing about the *bar* changes: two independently verified repositories, an
interval, and a refusal below the sample floor.

## Evidence

- `[measured]` One human rejection in the trajectory against a floor of 30, across three days of
  continuous operation. The human route cannot reach the floor on any timeline the system controls.
- `[algebra]` ADR-0080 establishes that consequence and contract signals identify a different
  estimand from β_H, and that the substitution `q_upper := beta_upper` is human-oracle-relative.
  This ADR does not attempt the substitution ADR-0080 forbids; it changes which estimand the gate
  names.
- `[measured]` A contract stated in advance is machine-checkable and needs no judgement at scoring
  time. This repository already runs about 1,200 such contracts as its test suite.
- `[measured]` A mutation run on 23 August 2026 killed 40 of 40 injected faults in
  `src/consilient/`, so the existing checks are strong against fault classes they can see. That is
  evidence the instrument has resolution, not that β_T is low.
- `[cited]` Held-out test suites are the established mechanism for exactly this problem in agentic
  code evaluation; SWE-bench's hidden tests are the worked example.

## Evidence against

- `[asserted]` **Goodhart is the real risk and it is not mitigated by this ADR.** A contract written
  in advance can be wrong or incomplete, and β_T would score a system perfectly while it does
  precisely the wrong thing very correctly. Gate A would then be measuring compliance rather than
  value. The only defence is that contracts get falsified over time, which is what the experiment
  register is for, and that defence is slow.
- `[asserted]` **The held-out suite is itself model-generated and has its own error rate.** The
  design needs its errors to be *independent* of the checks', not zero. If all model families miss
  the same subtle defect, the held-out suite misses it too and β_T is biased **downward** —
  flattering the system, which is the direction nobody catches. EXP-142 exists to measure that
  correlation, and until it reports, this ADR rests on an assumption.
- `[measured]` **This is the second gate redesign, and that pattern deserves suspicion.** Four gate
  conditions were already found unpassable as written (`../00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`).
  A gate that keeps being redefined until it can be passed is not a safety property. Recorded here
  so the next person can weigh it: if β_T also fails, the honest reading is that Gate A's *purpose*
  needs restating, not its quantity.
- `[measured]` ADR-0080 records that the human-verdict boundary is weaker than its name: `events.py`
  checks only that the declared actor equals the declared principal and the channel says `cli`, and
  `scripts/verdict.py` lets its caller choose the principal, so **a local agent process can write a
  syntactically valid declared-principal verdict.** This ADR does not repair that. It reduces the
  consequence of it — β_H no longer gates anything — but the forgeable boundary remains and should
  be fixed on its own merits.

## Consequences

**Positive** — Gate A becomes reachable on a timeline the system controls. The principal's authority
moves to stating intent, where it is definitional and cannot be a ceiling. The measurement stops
depending on his availability.

**Negative** — the gate now tests compliance with a stated contract rather than correctness in the
world. Something can pass while being useless. β_H would have caught that and no longer blocks.

**Neutral but load-bearing** — every unit now needs a contract written before it is dispatched, by a
different family, held out. That is real work on the critical path of every future unit, and it will
slow dispatch.

## Enforcement

- Check: `.github/scripts/check_heldout_isolation.py` — **refuses a build dispatch whose brief,
  worktree or claims can reach the held-out contract for that unit.** This is the load-bearing check:
  a builder that can read the contract voids the measurement, and discipline will not hold across
  hundreds of dispatches. Without it this ADR is prose.
- Check: `beta.admits_gate_row()` — a new admission rule for `contract_beta`, kept strictly separate
  from `admits_human_beta_row`, which is unchanged and continues to refuse every proxy.
- Check: the contract's authoring family must differ from the builder's family, refused at dispatch.
- Fails CI: yes, all three.
- Added in the same commit as the implementation: **no — none of these exists today.** Until they
  run in `invariants.yml`, this ADR describes an intention rather than a chokepoint, and Gate A1
  must continue to report FAIL. That is stated here so nobody reads this ADR as having opened it.

## What would overturn this

EXP-142 measuring the held-out suite's errors as **correlated** with the checks' errors. If both fail
on the same artefacts, β_T is biased downward and the gate would open on a flattering number, which
is worse than a shut gate. The pre-registered stopping rule is in the register.

Separately: evidence that contracts are being written to match what the builder was going to do
anyway — Goodhart arriving through the front door — would mean β_T measures nothing, whatever its
value. The signal to watch is contracts that never fail.
