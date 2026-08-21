# 0058. Orchestration ships as `scripts/dispatch.py`; the `consil` CLI surface stays the principal's to settle

- **Status:** ACCEPTED
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (authority to build orchestration, and the CLI surface). The script-not-subcommand split is the orchestrator's reversible reading of a pinned test plus his words.
- **Inquiry tier reached:** T0 assert — a values and surface decision, not a modelling question
- **Executable model:** none — there is no decision variable. The principal asked to *use* the harness, and a shipped test pins the `consil` command set.

## Context

Stage 3 was entered on 20 August 2026 under [ADR-0039](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md). That decision permits building and exercising orchestration; it does not pass Gate B, and it does not authorise `routing_orchestration_enabled`.

Overnight, roughly fifteen agents produced ADRs about loop architectures, personas, capability routing and quota pools. Not one of them built an orchestrator. This morning the principal could not use the harness to dispatch work to the four subscription runtimes he already pays for.

His words, 21 August 2026:

> "I WANT TO BE ABLE TO USE CONSILIENT MYSELF TO PROPERLY ORCHESTRATE ALL THE HARNESSES WITHOUT HAVING TO SHOUT AT YOU WITH ALL OF THIS FRICTION ... WE HAVE NEARLY $1000 OF MONTHLY MAX SUBSCRIPTIONS AND WE CAN'T BUILD A SIMPLE CLI?"

A shipped test, `test_the_cli_exposes_no_routing_or_blocking_surface`, pins `consil` to exactly `{record, replay, beta, doctor}`. Quietly editing that test to add `dispatch` would launder a surface change the principal has not settled.

`src/consilient/` is AST-locked against `subprocess`. Policy can live there; execution cannot.

## Decision

**Build the dispatch capability now. Do not add it to `consil`. Do not flip `routing_orchestration_enabled`.**

1. **The command is `python scripts/dispatch.py`.** Registry, selection and recording live in `src/consilient/harness.py`. Process execution, probing and process-tree kill live in `scripts/dispatch.py`, the same split as `scripts/run_fallback.py` and `scripts/capture_health.py`.
2. **The `consil` command set stays `{record, replay, beta, doctor}`** until Joe decides otherwise. Whether dispatch later becomes `consil dispatch` is his question, not this commit's.
3. **`routing_orchestration_enabled` remains the gate report.** Building the capability is authorised by ADR-0039; depending on it for work on another repository is still Gate B, and Gate B is not passed.
4. **Every dispatch appends through `events.append()`.** An orchestration that leaves no record is worthless here.

## Evidence

- `[asserted]` Joe's quoted request is the authority to build. Stage 3 entry (ADR-0039) is the authority that building is in-bounds.
- `[measured]` `test_the_cli_exposes_no_routing_or_blocking_surface` pins the CLI command set; this commit does not edit it.
- `[measured]` 21 August 2026 operator observation: Claude weekly nearly exhausted; Cursor Models 1% used; Cursor Other Models 58% used; SuperGrok Heavy 2% used; Codex unknown. Selection prefers remaining headroom and refuses the exhausted pool.

## Evidence against

- `[cited]` [ADR-0007](0007-cli-only-no-review-surface.md) says CLI only. A script beside `consil` is a second surface. We did it anyway because the pinned test forbids growing `consil` without Joe, and because he asked to *use* something this morning, not to wait on a surface redesign.
- `[cited]` [ADR-0003](0003-no-learned-routing-policy-in-v0.md) forbids a learned router. Headroom-greedy selection is a policy. It is not learned, and refusing the exhausted pool is the whole point of this commit, but it is still a routing rule and it will look like one.
- `[asserted]` `routing_orchestration_enabled: false` will now sit next to a working dispatcher. That is confusing. It is also honest: the flag reports the gates, not whether a script exists.
- Searched `docs/decisions/` for an existing "dispatch is a consil subcommand" decision and found none. The closest are ADR-0007 (CLI-only) and ADR-0039 (build is permitted).

## Consequences

**Positive** — Joe can dispatch a task to Cursor Composer or Grok without spending the exhausted Claude pool, and fan the same task out to two families.

**Negative** — two entry points (`consil` and `scripts/dispatch.py`). The second is easy to forget and easy to treat as "the product" before Gate B passes.

**Neutral but load-bearing** — Gate B still governs pointing this at any repository other than this one.

## Enforcement

- Check: `tests/test_v0_invariants.py::test_the_cli_exposes_no_routing_or_blocking_surface` (unchanged)
- Check: `tests/test_dispatch.py::test_exhausted_pool_with_lowest_used_percent_is_never_selected` (mutation-tested in this commit)
- Check: `tests/test_dispatch.py::test_dispatch_is_a_script_not_a_consil_subcommand`
- Check: `tests/test_budget.py::test_product_tree_has_no_outbound_or_credential_capability` still covers `src/consilient/harness.py`
- Fails CI: yes
- Added in the same commit as the implementation: yes

## What would overturn this

Joe adding `dispatch` to `consil` and asking for the pin test to move. Or Gate B passing, at which point `routing_orchestration_enabled` flipping is a different decision, not this one.

## Publication candidate?

No. This is a surface split for one repository's CLI pin, not a result.
