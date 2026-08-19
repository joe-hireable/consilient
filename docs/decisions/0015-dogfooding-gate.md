# 0015. Dogfooding gate — do not depend on Consilience until it clears three tests

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (intent), Claude (the gate)
- **Inquiry tier reached:** T1 ground
- **Executable model:** none.

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
