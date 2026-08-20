# Gate B cannot be passed as written, and Gate B2 could never fail

**Date:** 20 August 2026
**Status:** `[measured]` — the quotations below are the current text of both documents.
**This note establishes the defect. The correction is an ADR and is Joe's to accept.**

---

## The circularity

Two documents say the same thing in the same shape.

`docs/40-spec/v0-draft.md` §3:

> ### Stage 3 — route, criticise and orchestrate, after Gate B
> Control begins on a project other than Consilience **only after Gate B**.
> …
> 4. Twenty non-Consilience tickets complete without intervention in the harness itself.

`docs/decisions/0015-dogfooding-gate.md`:

> ### Stage 3 — Consilience routes and orchestrates (gate B)
> It makes routing decisions and runs parallel agents on real work, **starting with a project
> that is *not* Consilience.**
> **Gate B — all four must hold:**
> 4. **Consilience has orchestrated 20 tickets on a non-Consilience repository** without the
>    maintainer intervening in the harness itself.

So:

1. Orchestrating on a non-Consilience repository is Stage 3 behaviour.
2. Stage 3 begins only after Gate B.
3. Gate B requires twenty tickets orchestrated on a non-Consilience repository.

**Condition 4 can only be satisfied by doing the thing the gate forbids until condition 4 is
satisfied. Gate B, as written, can never be passed.** [algebra]

## This is the same defect Stage 2 had, and it was corrected this morning

`v0-draft.md` §3 records the Stage 2 repair, made on 20 August 2026:

> **Corrected 2026-08-20.** This section previously read "after Gate A", which is circular:
> Gate A requires seven days of trajectory capture and a replay invariant green in CI, and
> neither can exist until the recorder does. Stage 2 is therefore *entered* when Joe approves
> the specification and *exited* through Gate A.

The identical correction was not applied one stage down. **The pattern is the finding: a gate
whose conditions are produced by the very activity it gates is unpassable, and this repository
has now written that pattern twice and noticed it once.**

## Gate B was broken in both directions at once

Also found on 20 August, separately, and now repaired on branch `fleet-gate-b2`:

**Gate B condition 2 could never fail.** It asked whether the derived parallelism ceiling
exceeds 1. Under the project's own model `frac_seen ≤ 1`, so `T_eff ≤ T_r`, giving
`n_max ≥ 25/8 = 3.125` for every critic recall and therefore every β — including β = 1.0, a
critic that catches nothing. A threshold below the minimum possible value of the quantity it
gates passes by tautology. [measured]

So Gate B had **one condition that could never fail and one that could never pass**, and the
two defects are opposites. B2 admitted everything; B4 admitted nothing. Between them they meant
the gate's verdict was determined by neither β nor evidence.

That is worth stating plainly because the project's founding claim is that *convergence is a
test, and tests have error rates*. A gate is a test. These two conditions had error rates of
100% in opposite directions and nobody had computed either.

## What Gate B was actually for

From ADR-0015's own Context, which is the thing any correction must preserve:

> If the tool you build with becomes the tool you are building, then every defect in it slows
> the work to fix it. A solo maintainer can lose weeks this way, and the failure is
> self-concealing: you attribute the slowdown to the work being hard.

And from its Never clause:

> Consilience does not become the only way to work on Consilience. The fallback in Gate B3 is
> permanent, not transitional.

**Gate B protects against dependence, not against construction.** Read that way, the correction
is available and it is narrow: orchestration may be *built and exercised under supervision,
with the fallback always present*; what Gate B gates is *depending* on it — making it the
default or only path, or running it unattended.

That reading also makes B4 meaningful for the first time. Twenty supervised tickets on a
non-Consilience repository become the *evidence* the gate consumes, rather than a precondition
that cannot be met.

## What a corrected Stage 3 must still forbid

A correction that forbids nothing is a gate lift wearing a correction's clothes. Any proposal
must keep at least these, or it is not a correction:

- **The bare-agent fallback stays permanent and stays tested.** B3 is unchanged, and it is
  currently unbuilt — `.github/workflows/` contains no scheduled job, which is recorded debt.
- **Unattended operation stays behind the gate.** Supervised means a human sees the dispatch
  and can stop it; that is what makes the twenty tickets evidence rather than exposure.
- **B2's replacement must still bind.** It now flips at β ≈ 0.63 and β is not measured to that
  precision, so it genuinely gates something.
- **`consil doctor` remains owed.** ADR-0015's Enforcement clause requires the feature flag to
  be *derived from measured state*, not advisory. Today the gate is held in a stronger form —
  no routing surface exists at all — and the commit that adds one owes `doctor` in the same
  commit. Absence beats refusal only while it lasts.

## Falsifier

If a reading exists under which B4 is satisfiable without Stage 3 — a supervised mode, a
dry-run mode, or orchestration on Consilience itself counting toward the twenty — then the
circularity is a wording problem rather than a structural one, and the fix is a sentence rather
than an ADR. **Nothing in either document currently offers that reading**, and this note should
be withdrawn if one is found in the history.

## Who decides

The correction is an ADR superseding ADR-0015, and **only Joe may accept it**. ADR-0033 §2
reserves lifting a gate to the principal, and a gate lifted by reinterpretation is the same
failure arriving through the front door. This note establishes the defect; it does not resolve
it, and no agent may treat it as resolved.
