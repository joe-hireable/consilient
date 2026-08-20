# 0043. Gate A3 counts new refusals, not historical ones

- **Status:** PROPOSED 20 August 2026. Amends ADR-0015 Gate A condition 3. **Only Joe may accept
  this**, because it changes when this project is permitted to route and orchestrate.
- **Date:** 2026-08-20
- **Deciders:** proposed by Claude Opus 5; ADR-0015 belongs to Joe Brown
- **Inquiry tier reached:** T1 ground — one measured defect, exact arithmetic, no controlled
  comparison.
- **Executable model:** none. There is no dispersed prior here; the condition is either
  satisfiable or it is not, and that was settled by running it.

## Context

ADR-0015 Gate A condition 3 reads *"Seven consecutive days of trajectory capture with no data
loss."* `consil doctor` implements it as `run >= 7 and issue_count == 0`, where `issue_count`
counts, across the current consecutive run, both misdated lines and lines the validator **refused**.

Three V0-18-violating lines were quarantined on 20 August. The trajectory log is append-only, so
they are permanent, and the run window always reaches back to them while capture is continuous.
Projected over 7, 60 and 365 days of unbroken capture, A3 fails identically every time.
[measured — `docs/00-context/gate-a-cannot-be-passed-either-2026-08-20.md`]

Introduce a single day's gap and `issue_count` falls to zero; seven days later the gate passes.
[measured]

> **The only way to pass "seven consecutive days with no data loss" is to lose a day of data.**

## Decision

Amend Gate A condition 3 to:

> Seven consecutive days of trajectory capture during which **no new** line is rejected and no line
> is misdated. Refusals already present at the start of the run are counted, reported beside the
> verdict, and do not block it.

The count of pre-existing refusals is reported, never hidden, and may only fall — the ratchet
already used for `append()` bypass (`bypassed() <= 92`) and for the quarantine ceiling.

## Why this is the right shape

The condition conflates two things this project separates everywhere else.

**Loss** is an event that should be in the record and is not. That is what the condition is *for*
and — per ADR-0040's deprecation, which established that a census over a self-reported record
measures diligence rather than practice — it is **not observable from inside the record at all**.

**Refusal** is an event that *is* in the record, named invalid, with its reason and line, reported
beside every figure derived from the log.

Counting refusals as loss penalises the exact behaviour the 20 August repair introduced on purpose:
refusing loudly rather than skipping silently. **A log that had silently dropped those three lines
would pass the gate today.** The gate rewards the failure mode it exists to prevent.

## Evidence against

- **This makes a gate easier to pass, and it is proposed by the party the gate constrains.** That
  is a conflict of interest and it should be read as one. The mitigation on offer is that the
  amendment is strictly narrower than "count nothing": a single *new* rejection during the window
  still fails, so the gate retains its teeth against the failure it can actually observe.
- **The seven-day requirement was never validated.** Seven is a round number, not a measured
  sufficiency threshold, and this ADR leaves it untouched. Amending the part that was measured to
  be broken while leaving the arbitrary part alone is defensible but not principled.
- **A ratchet with a non-zero floor can normalise its floor.** `bypassed() <= 92` has the same
  hazard: a ceiling nobody is trying to lower is a ceiling that stays. If pre-existing refusals
  never fall, this amendment converts a permanent failure into a permanent tolerance, which is
  quieter but not obviously better.
- **The alternative was not taken, and it is real.** A3 could instead require that the *canonical
  replay digest* is reproducible across the window — which A2 already tests, and which is a
  property rather than a count. That would arguably subsume A3 entirely and delete a condition
  rather than fix it. It is not proposed here only because deleting a gate condition is a larger
  claim than repairing one, and both belong to Joe.
- **I searched for a reading of `issue_count` that excludes historical rejections and found none.**
  The arithmetic is at `src/consilient/cli.py` lines 250–293 and the projection script is in the
  finding document. If that reading exists, this ADR is unnecessary.

## Consequences

**Positive.** Gate A becomes passable by doing the thing it asks for. A1 (EXP-01) becomes the
genuine remaining blocker on Gate A rather than a false one, and the roadmap stops containing a
condition that time cannot satisfy.

**Negative.** A gate boundary moved on the initiative of the party it binds. The record must carry
that plainly, which is what this section is for.

**Neutral but load-bearing.** It sets a precedent that a measured-unsatisfiable gate condition is
repaired rather than worked around — which will be needed again for Gate B4, where the equivalent
repair is much larger.

## Enforcement

Every rule ships with its check (working principle 3, `AGENTS.md`). **This one deliberately does
not, and that is not an oversight.** Implementing it means editing the A3 arithmetic in
`consil doctor`, and doing so *is* the amendment — a gate crossed by inference is not a gate
(`CLAUDE.md`). The check ships in the same commit as acceptance, or not at all:

- **Check:** `_capture_condition()` counts only rejections on days at or after `run_start` **that
  were not present when the run began**, and reports the pre-existing count separately in the
  reason string.
- **Check:** a test asserting the pre-existing count may only fall, in the shape of
  `test_no_new_event_may_bypass_append`.
- **Check:** a test asserting that a *new* rejection inside the window still fails A3, so the
  amendment cannot be mistaken for a removal.

## What would overturn this

If capture runs for seven days and A3 still fails under the amended arithmetic, the defect is not
the one diagnosed here and this ADR should be withdrawn rather than patched.

If, after acceptance, the pre-existing refusal count has not fallen in three months, the ratchet is
decorative and the honest response is to say so — as ADR-0038's own test requires of a PROVISIONAL
decision — not to leave a tolerance standing because it is quiet.
