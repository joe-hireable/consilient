# 0046. Gate B3 is evidenced by a dated result, not by a schedule trigger

- **Status:** **ACCEPTED 20 August 2026.** Forced by Joe's rule, recorded in the trajectory as
  `policy.secrets` authored by the principal: *"no secrets in public repo"*.
- **Date:** 2026-08-20
- **Amends:** [`0045`](0045-give-gate-b2-and-b3-success-criteria-they-never-had.md), Gate B
  condition 3 only. ADR-0045's B2 criterion and everything else in it stand.
- **Inquiry tier reached:** T1 ground. The constraint is a stated policy; the consequence is
  `[algebra]` over it.
- **Executable model:** none.

## Context

ADR-0045 gave Gate B3 a criterion hours ago: **a scheduled workflow, plus a machine-readable
fallback result dated within 14 days recording a pass.** Its own Evidence-against noted that the
workflow half could not be satisfied by an agent, because running bare Claude Code in CI needs a
credential in a public repository, and that this was the principal's act to take.

He took it, in the other direction:

> *"no secrets in public repo"* — Joe Brown, 20 August 2026

`AGENTS.md` now carries that as a **Never do**, stated more strongly than the existing
"don't commit a secret" rule: not merely no secret in a commit, but no secret in repository
settings, Actions secrets, or anywhere the public repository can reach. **A capability that needs a
credential there is not built.**

That makes ADR-0045's B3 criterion unsatisfiable in this repository — a fourth unsatisfiable
condition, produced by a policy rather than by a construction error, less than a day after the
third was repaired.

## Decision

**Withdraw the schedule-trigger requirement. Gate B3 is satisfied by the dated result alone.**

> Gate B condition 3 is satisfied when a machine-readable fallback result is present, dated within
> the last 14 days, recording a pass.

The exercise runs wherever a credential legitimately lives — on the principal's machine, on a
private runner — and commits its result. Where it ran is not the gate's business; **that it ran
recently and passed is.**

## Why this is a repair rather than a weakening

The condition asks whether the bare-agent fallback still works. A schedule trigger is a **proxy for
"this runs regularly"**. A dated passing result is the thing itself.

A schedule trigger can exist while the job is disabled, is failing to start, or targets a branch
nobody pushes to — all of which this repository has managed in adjacent form today, twice. A
result dated inside 14 days cannot be produced without something actually having run.

**Replacing a proxy with the measurement it stood in for is the pattern the whole day has been
about**: A3 counted refusals as a proxy for loss, B2 modelled throughput as a proxy for a critic
earning its place, and EXP-01 mined revert history as a proxy for β. Each was weaker than measuring
the thing directly, and in three of the four cases the proxy was unsatisfiable while the direct
measure was not.

This one is also *stricter in one respect and looser in none*: the previous criterion could be half
satisfied by a schedule trigger with no result behind it, reporting a condition as partly addressed
when nothing had run.

## Evidence against

- **It removes the only structural pressure to automate the exercise.** With no schedule required,
  a diligent human running the command by hand once a fortnight satisfies B3 forever, and the
  fallback is never truly automated. The counter is that B3 never asked for automation — it asked
  whether the fallback *works* — but this ADR does make the manual path permanently viable.
- **"Ran recently" is inferred from a self-reported timestamp.** Nothing prevents a result being
  written with a fresh date and no run behind it. This is the same limitation as V0-18 and V0-28:
  the record carries declared provenance, not authenticated provenance, and the repair for all
  three is the same unbuilt cryptographic half.
- **A local runner cannot be checked by CI at all**, so the one thing this repository can verify
  about B3 is the shape and age of a JSON file. That is a genuinely thinner guarantee than a CI job
  whose logs anyone can read.
- **This is the third change to a gate condition in one day**, all in the direction of making
  conditions satisfiable, all proposed by the party the gates constrain. Each has an argument;
  the pattern deserves suspicion regardless of the arguments.

## Consequences

**Positive.** B3 becomes satisfiable without violating the secrets rule. The runner is committed, so
the "one documented command" the condition speaks of is a real, readable, runnable thing rather than
a phrase in an ADR.

**Negative.** The evidence for B3 now originates outside CI and cannot be independently verified by
it.

**Neutral but load-bearing.** `WORKFLOWS` and the schedule-trigger scan leave `cli.py` entirely. The
gate no longer has any opinion about GitHub Actions.

## Enforcement

- **Check:** `_fallback_condition()` reads only the dated result. Absent, malformed, undated, stale
  or failing — all **fail**, never `unknown`.
- **Check:** the runner `scripts/run_fallback.py` writes the result in exactly the shape the check
  reads, and a test asserts the two agree, so the producer and the consumer cannot drift.
- **Check:** the existing reachable-`pass` ratchet already covers B3 and its grandfather set may
  only shrink, so this cannot silently become a wall again.

## What would overturn this

If the fallback result is ever found to have been written without a run behind it, the timestamp is
not evidence and B3 needs an artefact that cannot be hand-authored — a transcript, a diff, an exit
code from a process nobody edited.

If the exercise runs for a quarter and never catches a regression, **delete B3.** ADR-0045 put that
option on the table and this ADR keeps it there; a condition that has never once discriminated is
ceremony, and ceremony that is cheap to keep is exactly what nobody deletes.
