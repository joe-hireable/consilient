# 0104. Re-derive both halves of β\* from evidence, and let the arithmetic fall where it does

- **Status:** PROVISIONAL — the decision to re-derive is settled; the values are unknown until
  EXP-143 reports. It may leave the gate shut.
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Relates to:** 0002 (β as the organising quantity), 0018 (the persistence threshold),
  0039 (gate changes are reserved to the principal), 0103 (contract-β as the gate quantity)
- **Inquiry tier reached:** T2 algebra plus a measurement route for each unknown
- **Executable model:** the closed form already exists in `simulations.py`; what is missing is not a
  model but two measured inputs to it.

## Context

The threshold every routing and gating decision is compared against is

```
β* = (1 − α) · e^(−k·Δ)
```

where α is `P(verifier rejects | artefact is good)` — the flaky-rejection rate — and Δ is the
capability gap. At the values in use, β\* evaluates to **0.1119**.

**Both inputs are invented.** `../00-context/alpha-is-invented-2026-08-20.md` records that α was
never measured, and that the post-experiment sweep had additionally recorded the converse of β as
having "no name" when it has one and is half the formula. Δ has no measurement behind it either.

This matters because of what the arithmetic then says. The project's own two corrected estimates of
actual β are **0.12 and 0.14** — both above β\* = 0.1119. **At the measured error rate, no sample
size clears the threshold.** The gate is not merely shut; on these numbers it is unpassable, and the
number deciding that was invented rather than observed. [measured 23 Aug 2026]

The principal decided on 23 August 2026: re-derive from evidence, and let the arithmetic fall where
it does. He named Δ. This ADR extends it to α as well, because re-deriving one half of a two-input
formula and leaving the other fabricated would produce a number that looks measured and is not —
which is the precise failure this repository exists to prevent.

## Decision

We measure α and Δ rather than asserting them, and we recompute β\* from the measured values
whatever they turn out to be. **No adjustment is made to make a gate pass.** If the recomputed β\*
still sits below the measured β, that is a finding about the system and not a reason to revisit the
constants a second time.

Until EXP-143 reports, β\* remains at its current value and is labelled `[asserted]` wherever it is
shown, so nothing downstream reads it as measured.

**α is measured first**, because it is cheap and nobody has done it. α is the rate at which the
checks reject a good artefact — observable directly from rerun history, where a check that fails and
then passes unchanged has rejected a good artefact by definition. The data already exists in CI and
in the trajectory.

## Evidence

- `[measured]` α has never been measured. Recorded in
  `../00-context/alpha-is-invented-2026-08-20.md`, which also records that it went unnamed in a
  sweep for several hours while it was the most decision-relevant open item.
- `[measured]` Δ has no measurement behind it; the value in use is a choice.
- `[algebra]` β\* = (1 − α)·e^(−k·Δ) = 0.1119 at the values in use, against project estimates of
  actual β at 0.12 and 0.14 — so the threshold is currently below the error rate it is meant to
  discriminate.
- `[asserted]` α is cheaply observable. A check that rejects an artefact and then accepts the same
  artefact unchanged has, on that occasion, rejected a good one. Flaky-test data is the standard
  form of this and CI already produces it.

## Evidence against

- `[asserted]` Re-deriving a threshold that currently blocks a capability, at the request of the
  party who benefits from it unblocking, is exactly the shape of a motivated measurement. The
  defence is that the stopping rule and the estimator are fixed in EXP-143 **before** any value is
  seen, and that this ADR commits in advance to accepting an unfavourable result. That defence is
  procedural, and procedural defences are weaker than structural ones.
- `[asserted]` α measured from rerun history is α *for the current test suite on the current work*.
  A cross-family review on 23 August 2026 found 14 of 19 units carry a guard deletable with the
  suite still green, so this suite rejects less than it appears to — which biases α **downward** and
  β\* **upward**, in the direction that opens the gate. That is the wrong direction to be wrong in,
  and it is the strongest objection to this ADR.
- `[asserted]` k is also unexamined. This ADR does not address it, so a third invented input remains
  in a formula being described as re-derived. Named here rather than discovered later.
- `[measured]` This is now the third time the project has re-instrumented β or its threshold after
  two falsified routes. That pattern more often indicates the quantity resists measurement as framed
  than that the instrument was unlucky.

## Consequences

**Positive** — the number every routing and gating decision is compared against becomes an
observation rather than a choice. α becomes measured for the first time, and it is the cheaper half.

**Negative** — the recomputed β\* may be lower, which would make the gate harder rather than easier.
The decision commits to accepting that.

**Neutral but load-bearing** — every threshold derived from β\* moves when it moves, so anything
recorded against the current value must be re-checked rather than assumed to hold.

## Enforcement

- Check: `tests/test_v0_invariants.py` must refuse a β\* presented as `[measured]` while EXP-143 is
  unreported, so the invented value cannot be quietly promoted by a later edit.
- Check: `consil doctor` continues to compute gate state from the register rather than from any
  hand-maintained figure, so this ADR cannot change a gate by assertion.
- Fails CI: the second already does; **the first does not exist yet** and this ADR is not a
  chokepoint until it does.
- Added in the same commit as the implementation: no.

## What would overturn this

EXP-143 measuring α on a suite subsequently shown to be unfalsifiable — the guard-survival finding
suggests this is likely — would mean α is an artefact of weak tests rather than a property of the
checks. In that case α must be re-measured after the guard backlog is cleared, and any β\* computed
before then is void. That dependency is recorded in the register so the order cannot be forgotten.
