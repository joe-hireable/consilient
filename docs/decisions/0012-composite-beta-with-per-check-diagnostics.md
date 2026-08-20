# 0012. Measure the composite β directly; keep per-check β as diagnostics

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — but see EXP-03 in the experiment register.

## Context

Q10. Different checks have very different false-accept rates. A type checker is near-zero β
on type errors and near-1.0 on logic errors. Test suites depend entirely on coverage. Lint
catches almost nothing semantic. So is β one number per repository, or a vector per check
class?

## Decision

**Measure the composite directly.** The routing decision in `0002` needs one number, the
checks compose as all-must-pass, and the composite is the quantity that gates the decision.

**Also measure per-check β separately, as diagnostics only.** Never compose them
analytically into the routing number.

## Evidence

- `[algebra]` Under conditional independence given a bad artefact, the composite false-accept
  rate is the *product* of the individual rates — which is why stacking several weak checks
  helps far more than intuition suggests.
- `[algebra]` **Independence is certainly false.** A bug that slips the tests often slips the
  type checker for the same underlying reason (both blind to the same class of error). So
  the product is a **lower bound** on the true composite, and using it would systematically
  overstate how safe routing is — failing in the dangerous direction.
- `[algebra]` Measuring the composite directly requires no independence assumption at all.
  It is both simpler and safer.
- `[asserted]` Per-check diagnostics are actionable in a way the composite is not.
  *"Your tests are the weak link, not your types"* tells a user what to fix; a single
  composite number does not.

## Evidence against

- Per-check measurement fragments an already-scarce label supply. `0002` establishes that
  50–200 accepted diffs are needed for a usable composite estimate; splitting those across
  four or five check classes leaves each severely underpowered.
- Check classes are not cleanly separable in practice — a failing build masks whether the
  tests would have caught the bug, so per-check β is only observable for checks that
  actually ran to completion.

## Consequences

**Positive.** Routing rests on a directly measured quantity with no independence assumption.
Diagnostics give users something to act on.

**Negative.** Per-check estimates will be noisy for a long time and must be labelled as such
rather than presented alongside the composite as though equally reliable.

**Neutral but load-bearing.** The trajectory schema must record *which checks ran and each
verdict*, not just an aggregate pass/fail. That is a schema decision, and `0006` makes the
schema a public interface — so it has to be right early.

## Enforcement

- Check: the routing path reads only the composite. A lint rule forbids any per-check β from
  reaching the routing decision. Same commit (I1).
- Check: per-check β is surfaced only with its sample size and confidence interval; a test
  asserts no per-check figure is rendered bare.

## What would overturn this

EXP-03: if measured per-check β values turn out close to independent on real data, the
product becomes a usable prior that could extend the composite estimate at low sample
sizes. Worth checking, not worth assuming.

## Publication candidate?

Possibly, inside the β paper: *"verifier false-accept rates are strongly dependent across
check classes"* would be a small, useful, checkable result if the data supports it.
