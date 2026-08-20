# 0015. Dogfooding gate — do not depend on Consilience until it clears three tests

- **Status:** ACCEPTED (Gate B condition 2 superseded by [0037](0037-replace-gate-b2-with-measured-critic-throughput-gain.md))
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (intent), Claude (the gate)
- **Inquiry tier reached:** T1 ground
- **Executable model:** none.

## Update: 2026-08-20 — gate status recorded, and `consil doctor` named as debt

Bookkeeping against the conditions below, checked in the repository on 20 August 2026. No
gate condition is altered here; only its state is recorded.

**Gate A condition 2 — WITHDRAWN the same day it was recorded. Not satisfied.**

This section first recorded the condition as satisfied, on the reasoning below. Hours later, a
cross-family audit found that **the check could not fail**. `cmd_replay` built the projection
from the log twice and compared the two rebuilds — identical by construction — and
`projection.build` unlinks the database first, so any drift the check existed to detect was
destroyed before the comparison it was meant to feed. [measured] The gate was satisfied by a
tautology, which is worse than an open gate, because an open gate is visible.

The check is repaired (`32eacb8`): `replay` now digests the state on disk, rebuilds, and compares
the two; where there is no prior state it reports `compared: false` and `identical: null`, because
a check that did not run must not report a pass; and CI builds the projection before replaying so
the comparison has a subject. On the real trajectory it reports `compared: true, identical: true`
over 51 events, and a new test drifts the database out of band and asserts the divergence is
caught. [measured]

**The condition is therefore satisfiable and currently holds — but it is recorded here as newly
satisfied on the repaired check, not as continuously satisfied.** The earlier record was worth
nothing, and re-dating it rather than withdrawing it would hide the only interesting thing that
happened: a gate condition passed for a day on evidence that could not have failed.

The original reasoning, retained because it is what a reader would otherwise repeat:
`.github/workflows/invariants.yml` runs
`consilience.cli --json replay` against the committed trajectory on every push and pull
request and exits non-zero when `identical` is false. [measured] — true as far as it went, and
insufficient, because nothing established that `identical` could ever *be* false.

**Gate A condition 3 — day 2 of 7.** `.harness/log/` holds `2026-08-19.jsonl` and
`2026-08-20.jsonl`. [measured] A gap restarts the count.

**Gate A condition 1 — open, and it is the binding one.** EXP-01 remains `IN PROGRESS`.
Both repositories have been mined, but the corrected estimate is β̂ ≈ 0.12 with an honest
interval of [0.02, 0.42] on `jobboard-v2` and wider on the weaker repository, and both
intervals span the decision threshold; the honest verdict is "insufficient data".
[measured] The interval is audit-limited, not history-limited, so what closes it is the
~146-pair audit named in `../10-research/experiments/exp01/findings-exp01.md` § *Next
steps* — agent-hours, not human-weeks. Condition 3's clock will finish first and is not
what Gate A is waiting on. Note also that the condition as written asks for "a reported
confidence interval" and does not say the interval must exclude the threshold; a future
reader should not take the looser reading, because an interval spanning the threshold has
not measured β for any purpose this ADR has. [asserted]

**Gate B condition 1 — satisfied, and recorded here for the first time.** EXP-05 wrote six
adapters. #2 (Codex) fit the same interface with no redesign; #3 (Cursor CLI) forced
host-to-WSL path translation, which was contained inside the adapter and left the common
ticket/result interface intact; #4, #5 and #6 fit without redesign. [measured] ADR-0001's
stopping rule therefore did not fire — see
`../10-research/experiments/exp05/findings-exp05.md`. Gate B stays closed on conditions 2,
3 and 4.

**Gate B condition 2 — SUPERSEDED by [0037](0037-replace-gate-b2-with-measured-critic-throughput-gain.md).**
Condition 2 as written (*"derived parallelism ceiling is > 1"*) is a mathematical tautology ($n_{\text{max}} \ge 3.125 > 1$ for all $\beta \in [0, 1]$) and cannot fail. Superseded by ADR-0037, which requires a measured $\ge 20\%$ review-throughput gain over the unassisted baseline in EXP-08 ($G(\beta) \ge 0.20$, $\beta \le 0.6296$). [algebra]

**The Enforcement clause below is unimplemented, and that is now recorded as debt.**
`consil doctor` does not exist; the CLI exposes `record`, `replay` and `beta` and nothing
else. Today the gate is held in a **stronger** form than this ADR asked for: there is no
routing or blocking surface for a doctor command to refuse, and
`tests/test_v0_invariants.py::test_the_cli_exposes_no_routing_or_blocking_surface` asserts
the command set is exactly `{record, replay, beta}` and that no argument destination
contains `route`, `dispatch`, `block`, `accept`, `gate` or `escalate`. [measured] Absence
beats refusal while it lasts, and the exact-set assertion means no routing surface can land
without that test failing first. **Debt, stated so that it is an obligation rather than a
discovery: the commit that adds any routing or orchestration surface owes `consil doctor`
in the same commit — gate status reported, feature flag derived from measured state (I1).**
[asserted]

The clause's second check — a weekly scheduled CI job exercising the bare-Claude-Code
fallback — does not exist either; `.github/workflows/` contains no scheduled job.
[measured] It is a Gate B3 obligation and Gate B is not close, but an invariant without its
check is named here rather than left implied. [asserted]

## Context

Joe intends to replace his own workflows with Consilience once published — including
further development of Consilience itself, and his other projects.

That is the right end state. `0004`'s success condition is "the smallest thing worth a
stranger's install and the smallest thing that improves my week are the same artefact", and
self-hosting is how you find out whether that's true.

**But it has a specific failure mode.** If the tool you build with becomes the tool you are
building, then every defect in it slows the work to fix it. A solo maintainer can lose weeks
this way, and the failure is self-concealing: you attribute the slowdown to the work being
hard.

## Decision

**Bootstrap in three stages, gated.**

### Stage 1 — Claude Code builds Consilience (now)
Consilience is not on the critical path for anything. Skills and rules are written in the
portable format (`0014`) so nothing is thrown away.

### Stage 2 — Consilience observes, Claude Code decides (gate A)
Consilience runs alongside, collecting trajectory data and computing β. It makes no routing
decisions and blocks nothing. Pure instrumentation.

**Gate A — all three must hold:**
1. **EXP-01 complete**: β measured on at least two repositories of differing verification
   quality, with a reported confidence interval.
2. **Log-replay invariant green in CI** (`0006`): delete the database, replay the log,
   byte-identical state.
3. **Seven consecutive days of trajectory capture with no data loss.**

### Stage 3 — Consilience routes and orchestrates (gate B)
It makes routing decisions and runs parallel agents on real work, starting with a project
that is *not* Consilience.

**Gate B — all four must hold:**
1. **EXP-05 complete**: two adapters written, second one did not force a redesign.
2. **EXP-08 complete**: critic recall measured, and the derived parallelism ceiling is > 1.
3. **A one-command fallback to bare Claude Code exists and is tested weekly.**
4. **Consilience has orchestrated 20 tickets on a non-Consilience repository** without the
   maintainer intervening in the harness itself.

### Never
Consilience does not become the only way to work on Consilience. The fallback in Gate B3
is permanent, not transitional.

## Evidence

- `[measured]` Precedent from `jobboard-v2`: 991 commits in 36 days, and the codebase
  assessment found five self-identified Major findings **still unfixed 12 days later** while
  launch work shipped. Velocity did not protect correctness. A tool that slows the fix loop
  is more dangerous than one that is merely absent.
- `[algebra]` Gate B2 is not arbitrary: `findings.md` §5 gives `n_max = T_cycle / T_review`.
  If measured critic recall yields a ceiling of 1, orchestration provides no throughput at
  all and Stage 3 is pure risk.
- `[asserted]` Instrumentation before control is the standard sequence for any control
  system. Stage 2 delivers the project's core value — β — while risking nothing.

## Evidence against

- Gates delay the feedback that dogfooding exists to provide. Real defects surface under
  real dependence, and Stage 2 will not find them.
- Four conditions on Gate B is a lot for a solo project, and a gate nobody passes is a gate
  nobody respects. Risk that they get quietly waived.
- The "not Consilience first" rule in Stage 3 adds a project-management burden that may not
  be worth it.

## Consequences

**Positive.** β — the actual product — is delivered at Stage 2, before any orchestration
risk is taken. Skills carry across from day one via `0014`.

**Negative.** Slower to the satisfying end state.

**Neutral but load-bearing.** Stage 2 requires the trajectory log and verdict prompt but
*not* the router, critic or orchestrator. That is the minimum viable increment, and it
matches the experiment register's blocked-on list.

## Enforcement

- Check: `consil doctor` reports gate status against the four/three conditions and refuses
  to enable routing or orchestration until the relevant gate passes. **Not advisory** — the
  feature flag is derived from measured state, same commit (I1).
- Check: the bare-Claude-Code fallback path is exercised by a weekly scheduled CI job.

## What would overturn this

- Stage 2 runs for a month and surfaces nothing, suggesting the gates are too conservative
  and observation is not finding what dependence would.
- A gate is waived once. If that happens, the honest response is to delete this ADR rather
  than keep a rule nobody follows.

## Publication candidate?

No — but the staged-bootstrap pattern with measured gates could be a short, useful blog post
for the community strategy in `0004`.
