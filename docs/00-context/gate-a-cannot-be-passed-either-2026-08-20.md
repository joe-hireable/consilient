# Gate A cannot be passed either, and the only way to pass it is to lose data

**Date:** 20 August 2026
**Status:** `[measured]` for every count and for the two futures simulated below; `[algebra]` for
the unsatisfiability argument; `[asserted]` for the proposed amendment, which is ADR-0043 and is
not accepted.

---

## The finding

Gate B was found on 20 August to forbid the orchestration required to produce its own evidence
(`gate-b-cannot-be-passed-2026-08-20.md`). **Gate A has the same defect in a different shape, and
nobody had looked.**

ADR-0015, Gate A, condition 3:

> **Seven consecutive days of trajectory capture with no data loss.**

`consil doctor` implements it as `run >= 7 and issue_count == 0`, where `issue_count` sums, over
the days at or after the start of the current *consecutive* run, the lines the validator rejected
plus the lines whose timestamp does not match their file's date. Today it reports:

```
A3 FAIL: Seven consecutive days of trajectory capture with no data loss
  Latest capture run is 2/7 days, 2026-08-19 through 2026-08-20.
  The run has 3 rejected or misdated line(s).
```

Those three lines are the V0-18 violations quarantined on 20 August. The log is append-only.
**They can never leave it.**

## Run rather than argued

Reproducing `cli.py`'s window arithmetic exactly and projecting both futures: [measured]

| capture behaviour | days | run | issues | A3 |
|---|---|---|---|---|
| unbroken from 19 Aug | 7 | 7 | 3 | **FAIL** |
| unbroken from 19 Aug | 60 | 60 | 3 | **FAIL** |
| unbroken from 19 Aug | 365 | 365 | 3 | **FAIL** |
| **one day lost**, then unbroken | 7 after the gap | 7 | 0 | **PASS** |
| **one day lost**, then unbroken | 60 after the gap | 60 | 0 | **PASS** |

The run window only ever extends backwards through *consecutive* days, so while capture is
continuous the window always reaches 19 August and always contains the three permanent rejects. It
fails at seven days, and it fails identically at a year.

**A3 becomes satisfiable the moment capture is broken for a day.** A gap resets `run_start` past
the offending days, `issue_count` falls to zero, and seven clean days later the gate passes.

> **The only way to pass "seven consecutive days with no data loss" is to lose a day of data.**

## Why the condition is wrong, not merely inconvenient

The condition conflates two things that the rest of this project is careful to separate:

- **Loss** — an event that should be in the record and is not. This is what the condition is *for*,
  and — per ADR-0040's deprecation — it is not observable from inside the record at all. A missing
  event leaves no trace to count.
- **Refusal** — an event that *is* in the record, which the validator names as invalid, with its
  reason and line number, and which `consil replay` and `consil beta` both report beside their
  figures. **Quarantine is the opposite of loss.** It is the mechanism working.

`issue_count` counts refusals and calls them data loss. So the gate penalises exactly the behaviour
that the 20 August repair introduced deliberately: refusing loudly rather than skipping silently.
A log that silently dropped those three lines would pass.

That last sentence is the whole finding. **The gate rewards the failure mode it was written to
prevent.**

## What this means for the roadmap

Both gates standing between this repository and Stage 3 are now known to be unpassable as written:

| gate | status | reason |
|---|---|---|
| A1 | FAIL | EXP-01 is IN PROGRESS. Ordinary, actionable work. |
| A2 | PASS | Replay reproduces an identical canonical digest over 93 events. |
| **A3** | **FAIL, permanently** | this document |
| B1 | PASS | EXP-05 done; adapter two forced no redesign. |
| B2 | UNKNOWN | β is `insufficient_data` from **zero** human rejections. |
| B3 | FAIL | no workflow has a schedule trigger. Ordinary, actionable work. |
| **B4** | **STRUCTURALLY-UNSATISFIABLE** | Gate B forbids producing its own evidence. |

Three of the seven conditions are ordinary work. Two are unpassable by construction. One (B2)
cannot be evaluated because nothing has ever been rejected by a human, which is its own finding.

## The proposed amendment — ADR-0043, PROPOSED, not accepted

Make A3 a **ratchet rather than a purity check**, exactly as `bypassed() <= 92` already is:

> Seven consecutive days of trajectory capture during which **no new** line is rejected and no line
> is misdated. Refusals already in the record at the start of the run are counted, reported beside
> the verdict, and do not block it.

This preserves the intent — capture is working and is not silently dropping events — while removing
the perverse incentive. It does not weaken the gate: a single new rejection during the window still
fails it.

**It is not applied here.** Amending ADR-0015 is a decision about when this project is permitted to
route and orchestrate, and ADR-0015 is Joe's. `consil doctor` continues to report A3 as FAIL
against the condition as written, because a gate crossed by inference is not a gate
(`CLAUDE.md`). The check that would implement the amendment ships with the amendment, in the same
commit, if it is accepted.

## Reversal and falsifier

**Reversal:** nothing was changed; this document is the whole of it. `git revert` removes it.
**Falsifier:** if some reading of `issue_count` excludes historical rejections that I have missed —
or if the three quarantined lines can be legitimately re-dated or superseded without rewriting the
append-only log — then A3 is satisfiable as written and this document is wrong. The arithmetic
above is reproducible from `src/consilient/cli.py` lines 250–293; check it against that, not
against this summary.
