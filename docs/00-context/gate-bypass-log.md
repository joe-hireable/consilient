# Gate bypass log

Admin merges that skipped one or more gates from `../decisions/0023-pr-review-gates.md`.

Gates are **blocking for contributors, advisory for admin.** That asymmetry is deliberate and
defensible — but only if it is visible. This log is what makes it visible.

## Why this exists

Bypassing the *process* is fine. Bypassing the *evidence* on a T3 change is the failure mode,
and it is a documented risk for this maintainer specifically: `jobboard-v2` carries PRs of
1,693 and 1,350 files, self-merged, followed by same-day production firefighting, with five
self-identified Major findings still unfixed twelve days later.

The log does not stop any of that. It makes it countable.

## The debt rule

A **T3 bypass still owes** its ADR and its enforcement check. Skipping the gate defers the
work; it does not cancel it. Open debt is listed below until it is paid, with the commit that
paid it.

## Format

| date | PR | tier | what was skipped | why | debt | paid by |
|---|---|---|---|---|---|---|

## Log

| date | PR | tier | what was skipped | why | debt | paid by |
|---|---|---|---|---|---|---|
| 2026-08-21 | #1 | T2 | I1: token-lockdown invariant stated in ADR-0060 §1 without a shipped CI check | Aesthetic invariants are harder to lint than structural ones; the CI check (hex/font/radius verification against a declared DESIGN.md palette) requires implementation that is not yet scoped | Ship the check in the same commit as the first governed artefact | PR #2 (`check_design_tokens.py`) |

## When this log is the problem

`0023`'s overturn condition: **an unlogged bypass, not a bypass, is the failure.** If merges
continue while this file goes stale, the honest response is to delete ADR-0023 rather than
maintain a rule nobody follows — the same standard `0015` applies to its own gates.
