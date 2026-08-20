# 0039. Stage 3 is entered on approval; Gate B gates dependence, not construction

- **Status:** **PROPOSED** — not accepted. Lifting or altering a gate is reserved to Joe by
  ADR-0033 §2 and by `v0-draft.md` §3.1. **No agent may treat this as in force.**
- **Date:** 2026-08-20
- **Proposer:** Claude Opus 5. **Decider: Joe Brown, and only Joe.**
- **Would supersede:** [`0015`](0015-dogfooding-gate.md) Stage 3 and Gate B condition 4 only.
  Gate A, Gate B1, B3 and the Never clause are untouched; B2 was already replaced by
  [`0037`](0037-replace-gate-b2-with-measured-critic-throughput-gain.md).
- **Inquiry tier reached:** T1 ground — the defect is `[algebra]` over quoted text.
- **Executable model:** none. No decision variable, no free parameter; Gate G4 not satisfied.

## Context — Gate B cannot be passed as written

Established in [`gate-b-cannot-be-passed-2026-08-20.md`](../00-context/gate-b-cannot-be-passed-2026-08-20.md),
quoting both `0015` and `v0-draft.md` §3, which agree word for word:

1. Orchestrating on a non-Consilience repository is Stage 3 behaviour.
2. Stage 3 begins only after Gate B.
3. Gate B condition 4 requires **twenty tickets orchestrated on a non-Consilience repository**.

**Condition 4 can only be satisfied by doing the thing the gate forbids until condition 4 is
satisfied.** [algebra] The gate can never open.

This is the identical defect Stage 2 carried and which was corrected on the morning of
20 August: it read "observe only, **after** Gate A" while Gate A required seven days of
trajectory capture that only the recorder could produce. The fix was "*entered* on approval,
*exited* through Gate A". **The same correction was not applied one stage down.**

Gate B was in fact broken in both directions at once: B2 could never *fail* — it passed for
every critic recall including β = 1.0 — and B4 can never *pass*. B2 has since been replaced by
`0037`. B4 has not.

## Decision proposed

**Stage 3 is *entered* when Joe approves it, and *exited* through Gate B — and what Gate B gates
is dependence on the harness, not construction of it.**

Concretely:

1. **Orchestration may be built and exercised under supervision**, on any repository, with the
   bare-agent fallback present and working. Supervised means a human can see the dispatch and
   stop it.
2. **Gate B gates unattended and default operation.** Until it passes, Consilient may not run
   orchestration unattended, and may not be the default or only path to any work.
3. **Condition 4 becomes evidence rather than a precondition.** Twenty supervised tickets on a
   non-Consilience repository are what the gate *consumes*, which is the only reading under
   which the condition is reachable at all.

## Why this is the faithful reading, not a convenient one

`0015`'s own Context states what the gate is for:

> If the tool you build with becomes the tool you are building, then every defect in it slows
> the work to fix it. A solo maintainer can lose weeks this way, and the failure is
> self-concealing: you attribute the slowdown to the work being hard.

That risk is **dependence**, not construction. Building an orchestrator you do not yet rely on
costs a solo maintainer nothing they have not already chosen to spend; relying on a defective
one is what loses the weeks.

## What a corrected Stage 3 must still forbid

A correction that forbids nothing is a gate lift wearing a correction's clothes. This proposal
keeps all of the following, and should be rejected if any is dropped:

- **The bare-agent fallback stays permanent and stays tested.** B3 is unchanged and is currently
  **unbuilt** — `.github/workflows/` contains no scheduled job. Under this proposal B3 becomes
  *more* load-bearing, not less, and should arguably be built before Stage 3 is entered.
- **Unattended operation stays behind the gate.** Supervision is what makes twenty tickets
  evidence rather than exposure.
- **The Never clause is untouched.** Consilient does not become the only way to work on
  Consilient.
- **`consil doctor` remains owed and becomes mandatory.** `0015`'s Enforcement clause requires
  the feature flag to be *derived from measured state*. Today the gate is held in a stronger
  form than the ADR asked — no routing surface exists at all — and **absence beats refusal only
  while it lasts.** The commit that adds any routing surface owes `doctor` in the same commit.
- **ADR-0037's replacement for B2 still binds.** It flips at β ≈ 0.63 and β is currently
  `insufficient_data`, so it genuinely gates something.

## Evidence

- `[algebra]` The circularity, derived from quoted text in two documents that agree.
- `[measured]` The identical defect existed one stage up and was corrected the same day, so the
  pattern is established in this repository rather than hypothesised.
- `[measured]` Gate B2 was simultaneously unfailable. A gate with one condition that cannot fail
  and one that cannot pass produced a verdict determined by neither β nor evidence.
- `[asserted]` "Dependence, not construction" is the reading that makes `0015`'s stated Context
  and its Never clause both coherent.

## Evidence against

- **This proposal was written by the party it grants latitude to.** Q19's rule applies: the
  party that produced the material cannot certify what it missed. That is the strongest single
  objection and it is why the status is PROPOSED. [asserted]
- **"Supervised" is undefined and undermeasured.** Nothing in the repository records whether a
  dispatch was supervised, and today's own orchestration ran roughly fifteen agent dispatches
  where the human was absent for most of them. A correction resting on a property nobody
  measures is weaker than it looks, and the honest version of this ADR would ship the check that
  records supervision in the same commit. **It does not, and that is a real gap.** [measured]
- **The circularity might be a wording problem rather than a structural one.** If any reading
  exists under which B4 is satisfiable without Stage 3 — a dry-run mode, or Consilient-internal
  tickets counting toward the twenty — then the fix is a sentence, not an ADR. Nothing in either
  document currently offers that reading, but nobody has searched the drafting history.
  [asserted]
- **Gates that get corrected lose force.** `0015` says plainly that a gate waived once should be
  deleted rather than kept. This is the second Gate B condition altered in one day. A reader is
  entitled to ask whether Gate B is now a real constraint or a formality, and the honest answer
  is that it is weaker than it was this morning. [asserted]

## Consequences

**Positive.** Gate B becomes passable, so it can constrain something. Condition 4 becomes
evidence that accumulates rather than a precondition that cannot be met.

**Negative.** Orchestration gets built before β is measured to any useful precision — currently
bracketed at [0.81, 0.93] by one oracle and [0.0, 0.0713] by another, on populations that do not
overlap. The harness would be constructed on a verification layer it cannot yet trust. That is
the trade, and it should be made knowingly or not at all.

## Enforcement

If accepted, the same commit must add: a recorded `supervised` property on every dispatch event,
and a `doctor` condition that reports Stage 3 as entered-but-not-exited. **Without the first,
"supervised" is a word rather than a constraint**, and this ADR would have replaced an
unpassable gate with an unenforceable one.

## What would overturn this

Joe rejecting it, which is his to do and needs no justification. Or the discovery of a reading
under which Gate B4 was always satisfiable, which would make the whole document unnecessary and
should retire it rather than amend it.
