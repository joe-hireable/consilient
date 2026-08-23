# 0072. Close native work items only against evidence and project them outward

- **Status:** PROVISIONAL — EXP-98 can kill the dependency mechanism for its frozen mixture;
  EXP-19 can kill the residual human-feedback path; EXP-53 can kill the signing primitive but cannot
  prove human isolation by itself. [cited]
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (requirement only, quoted below); Codex dispatch
  `20260822T124219-82dd26876d` (the mechanism, which he has not reviewed). [measured]
- **Inquiry tier reached:** T1 source and incumbent grounding; T3 is registered as EXP-98, EXP-19
  and EXP-53, none run for this decision. [measured]
- **Executable model:** none. This decision selects discrete authority and transition invariants;
  EXP-98 measures the uncertain organisational benefit. [asserted]

## Context

The principal's requirement on 22 August 2026 was: [measured]

> "consilient needs to run similar spec and plans and organised documentstion and project
> management/task management systems for organisation etc."

The wording specifies the outcome, not the mechanism below. [measured] The source note also says
the principal is strategic rather than hands-on, should receive completed work, and should be
interrupted only for genuinely consequential decisions. [cited] (`the-machine-2026-08-22.md`)

`work_items.py` currently appends `opened`, evidence-classed `comment` and bare `completed` events.
[measured] `coordination.py` projects expiring path claims and refuses observed overlap, but it has no
dependency readiness, evidence-bearing closure or disagreement state. [measured] Dispatch already
owns harness selection, capability context, cwd authority, budget and claim integration. [measured]
Another project store or router would duplicate those primitives. [asserted]

The current beta instrument reports one declared human rejection and requires 30. [measured] That is
not one authenticated rejection: `events.py` accepts caller-declared `actor == principal` with
`via="cli"`, and `scripts/verdict.py --principal` accepts caller-supplied identity. [measured]
Authenticated human-labelled beta is therefore unestimated. [asserted] A task system that converts
an agent's completion claim, forged identity, silence, status or proxy into human acceptance would
poison the measurement it is meant to support. [asserted]

### Incumbent search

Official documentation for GitHub Projects, Linear and ClickUp was retrieved on 22 August 2026.
[measured] The bounded search covered item fields and states, assignment, dependencies, closure,
approvals, comments, notifications, APIs, export, audit history, data ownership and pricing.
[measured] Query families included: [measured]

- `site:docs.github.com issues projects dependencies custom fields workflows required checks export`
- `site:linear.app/docs issue status assignment dependencies approvals evidence notifications API`
- `site:help.clickup.com task statuses dependencies required fields approvals audit notifications API`

[GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
provides table, board and roadmap views, custom fields, automation and multi-repository tracking;
[issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
expose blocked work; and
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
can require code checks, reviews and resolved conversations. [cited] A GitHub issue can nevertheless
be [closed directly](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/closing-an-issue),
and the cited dependency documentation presents blocked state rather than a general execution or
closure gate. [cited] Branch protection governs repository integration, not arbitrary task truth or
principal-authored verdicts. [asserted]

[Linear](https://linear.app/docs/configuring-workflows) provides one-assignee issues and configurable
workflows;
[issue relations](https://linear.app/docs/issue-relations),
[project updates](https://linear.app/docs/initiative-and-project-updates), and
[its API and webhooks](https://linear.app/docs/api-and-webhooks) provide dependencies, visibility and
integration. [cited] The bounded official-documentation search found no general requirement for
immutable verifier receipts, preserved dissent or a principal-only verdict at issue closure.
[asserted] EXP-16 separately measured unsupported-state coercion and loss of per-agent provenance in
the connector path it tested. [measured]

ClickUp provides rich
[task fields](https://help.clickup.com/hc/en-us/articles/34958796358039-Task-fields-and-the-task-description),
[dependency relationships](https://help.clickup.com/hc/en-us/articles/6309155073303-Intro-to-Dependency-Relationships)
and [Automations](https://help.clickup.com/hc/en-us/articles/6312097314199-Use-Automation-Actions).
[cited] Its documented
[required fields](https://help.clickup.com/hc/en-us/articles/30407234676887-Make-Custom-Fields-required)
do not block later status transitions, while dependency and incomplete-item controls are documented
as [dependency warnings](https://help.clickup.com/hc/en-us/articles/6304410420759-Dependency-Warnings)
and an [incomplete warning](https://help.clickup.com/hc/en-us/articles/6304420229527-Incomplete-Warning).
[cited] Its Enterprise [Workspace audit logs](https://help.clickup.com/hc/en-us/articles/21929900448535-Workspace-audit-logs)
are time-bounded. [cited]

The strongest incumbent is therefore GitHub Projects for presentation and repository-adjacent work,
not for authoritative evidence closure. [asserted]

## Decision

Consilient will extend its native trajectory-backed work items and coordination claims into the
minimum task-management kernel described by
`../superpowers/specs/2026-08-22-task-management.md`. [asserted] It will not build a second
orchestrator, router, editable project database or general project-management interface. [asserted]

### 1. One durable item, many attempts

One work item carries a frozen goal, acceptance and non-goal digest, one accountable Owner, authority
reference, plan and stream identity, incumbent/delta, deliverable contract, verifier contracts,
owned paths, dependencies, budget, expiry and candidate-exposure contract. [asserted] The exposure
key covers goal lineage and the composite verifier, so a retry, harness change or cosmetic revision
cannot reset the count. [asserted] A changed goal or verifier creates a new revision that names the
old one. [asserted] The append-only trajectory remains authoritative and every other store is a
projection. [cited] (ADR-0006)

The projected state set is `blocked`, `ready`, `active`, `closed`, `failed`, `refused`, `cancelled`,
`expired`, `invalidated` and `superseded`. [asserted] Actors append typed evidence; they never set a
free-form state. [asserted] `closed` means all sealed artefacts exist and every frozen verifier
accepted. [asserted] It does not mean a human accepted the result. [asserted]

### 2. Reuse dispatch for assignment

Only `ready` items can be assigned. [asserted] The scheduler orders them deterministically by
critical-path blocking impact, then expiry, then trajectory position, and asks existing dispatch
eligibility and headroom logic to select the route. [asserted] An item retains one Owner. Without a
sufficient authenticated, trajectory-derived `human_verdict_beta` projection bound to the same task
family and frozen composite-verifier protocol/version, policy admits zero automatic verifier
exposure: candidate `1` refuses before the verifier boundary. Proxy, mutation and unscoped generic
`Beta` values are ineligible. [cited: ADR-0077; verdict-supply §§ 2, 4-5] A pre-verifier process
restart remains the same candidate; any revised artefact presented after verifier rejection is
candidate `n + 1`, across attempts, harnesses and revisions. [asserted]
Another member is admitted only for a frozen, non-overlapping, decision-changing evidence anchor.
[cited] (ADR-0067)

ADR-0077 corrects the brief's logarithmic formula: the distribution-free ceiling is
`floor(epsilon / beta_upper)`; the logarithmic form is only for a measured iid candidate population.
[algebra] `routing.py` implements the robust refusal but is deliberately absent from the dispatch run
path. [measured] Until that path consumes a ceiling derived from the exact eligible projection above,
automatic verifier exposure remains frozen. This documentation decision does not wire it or change
the routing flag. [asserted]

`coordination.py` serialises readiness-check, canonical-path conflict-check and claim-open as one
operation before harness invocation. [asserted] Claims bind the attempt, route, plan, paths, lease and
exact predecessor evidence consumed. [asserted]

### 3. Bind dependencies to evidence, not status

The frozen plan records each predecessor identity, revision and hand-off contract digest. [asserted]
A future artefact cannot honestly have a content digest before it exists. [algebra] Producer closure
therefore seals the actual artefact and verifier-receipt digests; the consumer becomes `ready` only
when those receipts accept and its claim binds those exact digests. [asserted]

Cycles, missing predecessors, failed or rejected predecessors, digest mismatches and unresolved
material conflicts block affected consumers before dispatch. [asserted] A later human rejection
invalidates every descendant that consumed the rejected digest, not unrelated work. [asserted]

### 4. Preserve disagreement and give it a typed disposition

Parallel producers do not write the shared integration surface; one integration item owns it.
[cited] (ADR-0068) A material disagreement records both claims, their evidence and the affected
contract. [asserted] Resolution is ordered: the frozen verifier; one bounded decision-changing
execution; a reversible Owner choice above the acceptance floor with reason, reversal and falsifier;
then principal escalation only for reserved authority or preference. [asserted]

The only dispositions are `resolved_by_evidence`, `owner_selected_reversible`, `escalated` and
`recorded_unresolved`. [cited] (ADR-0068) `recorded_unresolved` keeps affected work blocked while
unrelated work continues. [asserted] Voting, agreement between models, seniority and last writer are
not evidence. [cited] (`CONSILIENCE.md`)

### 5. Separate machine closure from the human verdict

Valid closure is a serialised operation that validates all receipts, appends the existing
`attempt.outcome` first, then appends evidence-bearing `work_item.completed` under the same
`attempt_id`. [asserted] A crash between writes leaves an outcome without false closure and resumes
idempotently. [asserted] The universal `events.append()` boundary must reject a bare or state-invalid
completion, including direct callers that bypass `work_items.py`. [asserted]

Beta later joins the machine outcome to zero or one separate `attempt.verdict`. [measured]
(`projection.py`) Current V0-18/V0-28 validation checks self-consistent declared fields, not the
caller's identity. [measured] No authenticated verdict ingress exists today. [measured]

A valid future verdict requires a single-use receipt from a first-party human-action broker outside
every dispatched harness's capability set. [asserted] The verified receipt binds principal identity,
action, `attempt_id`, artefact digest, issuer/version, time and nonce; the universal writer consumes
the nonce atomically with append. [asserted] A field-perfect event without that receipt refuses.
[asserted]

EXP-53 tests signing cost, replay and key custody at the append boundary, but its registered scope
explicitly does not prove that the signer was human. [cited] Human isolation remains a separate
acceptance condition on the broker. [asserted]

Once that ingress exists, ordinary use, merge, approval or explicit acceptance may yield `accept`;
return for correction, explicit rejection or wrong-result revert may yield `reject`, but only when
the authenticated action is bound to the attempt. [asserted] Silence, elapsed time, remote webhooks,
agent inference, model graders, task status and durability proxies never become human verdicts.
[asserted]

Existing verdict rows without a verified receipt remain append-only as `declared_unverified` and do
not enter authenticated beta. [asserted] They are neither deleted nor retroactively blessed.
[asserted]

No new beta survey is added. [asserted] An item with no naturally occurring acceptance action stays
`closed / unreviewed` and contributes no beta row. [asserted] This cannot promise 30 rejections by a
date without adding human labelling work or deliberately presenting bad work; neither is accepted.
[asserted] EXP-19 remains the killing test for the already designed sampled close prompt. [cited]

### 6. Render visibility; do not assign it to the principal

The conversational front door renders owners, critical path, exact blockers, adverse outcomes,
sealed artefacts, verifier receipts, unresolved dissent and human-verdict absence on demand.
[asserted] It pushes only the initial contract/range, one finished or adverse terminal result, one
pre-breach reforecast, or a genuinely principal-only or unrecoverable blocker. [asserted] Routine
progress, dashboard maintenance, reminders to review and agent discussion are not pushed.
[asserted]

GitHub Projects is the first optional presentation projection to test after explicit authority for
external exposure. [asserted] Linear and ClickUp remain optional views or intake surfaces. [asserted]
All are one-way with respect to readiness, closure and verdicts; connector failure is visible and
cannot alter local state. [asserted]

## Evidence

- `[measured]` Current source has native work-item, path-claim, dispatch, budget, context, outcome,
  verdict and visibility primitives, but no dependency readiness or evidence-bearing work-item
  closure.
- `[measured]` The local beta projection has one declared human rejection against a minimum of 30,
  but a field-consistent forged principal payload passes current event validation; authenticated
  human beta therefore has no row.
- `[measured]` `routing.py` refuses an unmeasured ceiling in isolation and `dispatch.py` is pinned not
  to import it; candidate exposure is not currently enforced in the run path.
- `[measured]` A bare `work_item.completed` passes the universal event validator today; guarding only
  the `work_items.py` helper would leave a direct-writer bypass.
- `[measured]` EXP-16 found connector state/provenance failures, supporting the accepted ADR-0006
  boundary that external tools are projections rather than authorities.
- `[cited]` ADR-0067 supplies one Owner, default-one composition and distinct evidence anchors;
  ADR-0068 supplies the minimum dependency graph and conflict dispositions; ADR-0077 separates
  candidate exposure from verifier fusion and supplies the robust ceiling.
- `[cited]` EXP-53 is the registered killing experiment for signatures at `events.append()` and
  records that signing alone cannot prove human authorship.
- `[cited]` The incumbent sources above establish that GitHub, Linear and ClickUp already exceed any
  justified native presentation scope.
- `[algebra]` A consumer cannot bind a hash of content that does not yet exist; freezing the hand-off
  contract first and binding the actual sealed digest at claim time preserves both preregistration
  and content identity.
- `[asserted]` Evidence-closed work items will reduce false completion and founder review load without
  making the task system a second oracle. The acceptance checks in the specification are the route
  from assertion to measurement.

## Evidence against

**Adopt GitHub Projects now.** The work is already repository-adjacent; GitHub supplies mature table,
board and roadmap views, custom fields, sub-issues, dependencies, automation, status updates,
notifications, GraphQL, export, established identity and protected code integration. [cited] It
would give the principal a polished interface immediately and avoid maintaining a bespoke task
system in a young project. [asserted] Linear offers a cleaner dedicated issue experience and ClickUp
offers richer custom workflows, proofing and assigned comments if presentation quality matters more
than repository proximity. [cited]

The native proposal duplicates commodity creation, assignment, dependency and status concepts while
shipping none of the incumbents' mobile, accessibility, notification, comment, search or workflow
polish. [asserted] It adds schemas, replay logic, atomic coordination, migrations, tests and failure
modes that one maintainer must own. [asserted] A local append-only log can be technically pure and
operationally worse if nobody can see or use it. [asserted] A one-way projection also creates two
representations and staleness states rather than eliminating integration risk. [asserted]

GitHub also authenticates account actions and can protect code integration with required named
reviews today, while Consilient's local CLI currently accepts caller-declared principal identity.
[cited] [measured] For code acceptance, GitHub is therefore the stronger deployed identity boundary
at present. [asserted] The proposed human-action broker is new load-bearing machinery and may add the
very friction this task is meant to remove; until it exists, authenticated beta remains empty.
[asserted]

**Why the objection does not decide authority.** GitHub's strongest hard gate is branch protection,
which protects code integration rather than general work-item truth. [cited] Generic issue closure,
GitHub dependency display, Linear status transitions and ClickUp warnings do not establish the
immutable artefact/receipt closure, digest-bound execution dependency, preserved typed dissent or
principal-only verdict that this decision requires. [cited] [asserted] Rebuilding those rules in
Actions, automations or middleware would recreate the native kernel across a network boundary and
may require credentials that this public repository may not hold. [asserted]

**What is conceded.** The incumbents win presentation, collaboration and generic workflow by a wide
margin. [asserted] Consilient will not build those surfaces. [asserted] GitHub Projects becomes the
default projection candidate if a no-private-data pilot reduces founder review time without becoming
an authority. [asserted] The native kernel itself is unimplemented and may prove more burdensome than
the integrity it buys; PROVISIONAL status and the overturn conditions below keep that objection live.
[asserted]

## Consequences

**Positive** — creation, assignment, dependency readiness, disagreement and evidence closure share
one replayable identity chain without another orchestrator; authenticated human actions can join it
once an isolated ingress exists. [asserted] The founder can inspect adverse and incomplete work
without administering it. [asserted]

**Negative** — the local schema and atomic claim path become load-bearing, external projections can
be stale, no authenticated human-verdict ingress exists, and no polished project interface exists
until separately authorised capabilities are tested. [measured] [asserted]

**Neutral but load-bearing** — `routing_orchestration_enabled` remains `false`; Gate A and Gate B do
not move; orchestration remains `scripts/dispatch.py`; the CLI remains six commands; no dependency is
added; `src/consilient/` remains outside this documentation-only commit. [asserted]

## Enforcement

This commit records the specification and decision only. [measured] It adds no implementation, CLI,
router, gate change or external connector. [measured]

Any implementation commit must add checks that: [asserted]

- call `events.append()` directly with a bare or state-invalid completion and prove refusal;
  [asserted]
- kill the process after outcome append and prove the item never closed, then resume idempotently;
  [asserted]
- refuse a claim with an unclosed/mismatched predecessor, a non-atomic overlapping path claim, a
  cycle, an unresolved affecting conflict or replay drift; [asserted]
- submit a field-perfect forged principal CLI payload and prove the missing/used human-action receipt
  refuses without changing authenticated beta; [asserted]
- expose a revised artefact as a retry, successor ticket and new harness, and prove all count as
  candidate `n + 1` under the same lineage key; [asserted]
- prove a later authenticated principal rejection invalidates exactly descendants bound to that
  digest; and [asserted]
- prove a connector cannot influence local readiness, closure or verdicts. [asserted]

The implementation and these checks ship together. [cited] (working principle 3) Dispatch remains
unwired to beta routing in this documentation commit. [measured]

No native board, notification centre, comment system or workflow editor may be added under this ADR.
[asserted] An external projection requires the existing authority for external exposure and a visible
failure path; it cannot be required for correctness. [asserted]

## What would overturn this

EXP-98 kills dependency scheduling, integration items and automated readiness for its frozen task
mixture if the registered organisation admission rule fails. [asserted] The system then retains one
evidence-bearing item and closure contract but defaults all work to the coherent Owner. [asserted]

EXP-19 kills the sampled close prompt if its registered friction rule fires. [asserted] Human verdicts
then arise only from ordinary authenticated acceptance or rejection actions. [asserted]

If EXP-53 rejects signing at the append boundary or its key-custody result leaves the signing
capability available to dispatched harnesses, the proposed receipt path remains blocked. [asserted]
A passing EXP-53 result still does not prove human presence. [cited] (experiment register)

If no first-party ingress can make a human-action receipt unavailable to dispatched harnesses
without adding review homework or a repository-held secret, the by-product verdict mechanism is
falsified. [asserted] Verdicts then remain absent rather than falling back to declared CLI identity,
and a separate authority decision must replace this clause. [asserted]

A synthetic no-private-data incumbent pilot overturns the local-authority decision if one incumbent,
without a custom authority service, atomically refuses canonical-path clashes, enforces digest-bound
dependencies, requires immutable closure receipts, preserves typed dissent, prevents agent tokens
from authoring principal verdicts, exports a complete replayable history, and measurably reduces
founder review time. [asserted] A failure of the native implementation to pass those same integrity
checks also overturns it; local is not privileged merely for being local. [asserted]

## Publication candidate?

**No.** The mechanism is provisional, the local source and beta observations are instance evidence,
and neither EXP-98, EXP-19 nor the incumbent pilot has reported. [asserted]
