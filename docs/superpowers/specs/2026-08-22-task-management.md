# Task management: evidence-bearing work items across dependent streams

- **Date:** 2026-08-22
- **Status:** Specification. Decided provisionally by ADR-0072; EXP-98 tests the stream mechanism,
  EXP-19 tests the human-load boundary, and EXP-53 tests the signature primitive for trusted
  ingress without proving human isolation by itself. [cited]
- **Author:** Codex dispatch `20260822T124219-82dd26876d`. The principal supplied the requirement;
  the mechanism below is this dispatch's design. [measured]
- **Review by:** 2026-11-22, or immediately after either named experiment reports. [asserted]

Two premises in the brief need correction. [measured] `consil beta` reports one *declared* human
rejection against a minimum of 30, but `events.py` authenticates only self-declared
`actor == principal` and `via == "cli"`; `scripts/verdict.py --principal` accepts caller-supplied
identity. [measured] The row therefore cannot support authenticated human-labelled beta, which
remains unestimated. [asserted] The brief's logarithmic candidate formula is the iid special case;
ADR-0077 makes the distribution-free ceiling `floor(epsilon / beta_upper)`, with refusal when beta is
unmeasured. [cited] Nothing below converts an agent's completion claim, silence, a derived proxy or a
remote integration event into a human verdict. [asserted]

## 1. Problem, outcome and boundary

`work_items.py` currently records `opened`, evidence-classed `comment` and bare `completed` events;
`coordination.py` projects expiring path claims and refuses observed overlap. [measured] (current
source) Neither module sequences dependent streams or requires closure evidence. [measured] (current
source) A task can therefore be marked complete without an artefact or verifier receipt, while a
consumer has no machine-checkable reason to wait for its producer. [measured] This specification
closes that gap by extending those modules, not by introducing another task store. [asserted]

### Goals

1. A work item has one accountable Owner, one frozen success contract and a state reconstructed from
   the trajectory rather than edited in place. [asserted]
2. A dependent item becomes claimable only after its predecessor's exact artefact and verifier
   receipts have been sealed and bound to the claim. [asserted]
3. `closed` means the frozen checks accepted the sealed artefact; it never means a human accepted it
   unless a separate principal-authored verdict exists. [asserted]
4. Material disagreement remains visible and blocks affected consumers until it has a typed
   disposition. [asserted]
5. The principal receives completed work and genuinely reserved decisions, not routine status work.
   [asserted]

### Non-goals

- No seventh `consil` command, second router, second orchestrator, new dependency or gate change.
  [asserted]
- No Kanban, sprint, meeting, points, badge or generic project-management surface. [asserted]
- No mandatory human review of every item and no attempt to manufacture the 30 rejections beta needs.
  [asserted]
- No agent approval, inferred principal verdict, vote, average or last-write-wins merge. [asserted]
- No external PM tool becomes an authority over the local trajectory. [asserted]

### User stories

- As the Founder/CEO, I can ask what is happening and see owners, blockers, adverse outcomes,
  unresolved dissent and the latest sealed artefact without maintaining a dashboard. [asserted]
- As an Owner, I receive one ready item with its frozen goal, bounded context, budget, dependencies and
  verifier contract, and I can close it only by producing checkable receipts. [asserted]
- As a downstream Owner, I cannot start from a producer's prose claim; my claim names the exact
  predecessor artefact digest I consumed. [asserted]
- As an auditor, I can distinguish machine closure, human acceptance, human rejection, refusal,
  timeout and unreviewed work from the append-only record. [asserted]

## 2. The incumbent bar and the adoption decision

Official documentation for Linear, GitHub Projects and ClickUp was retrieved and read on 22 August
2026. [measured] The search covered item schemas, status transitions, assignment and automation,
dependencies, comments and review, closure controls, notifications, APIs, export, audit history,
data ownership and pricing. [measured] The representative queries were: [measured]

- `site:linear.app/docs issue status assignment dependencies approvals evidence notifications API`
- `site:docs.github.com issues projects dependencies custom fields workflows required checks export`
- `site:help.clickup.com task statuses dependencies required fields approvals audit notifications API`

| incumbent | bar it sets | boundary found at source | decision here |
|---|---|---|---|
| **GitHub Issues + Projects** | Flexible table, board and roadmap projections; custom fields; multi-level sub-issues; explicit issue dependencies; built-in workflows; status updates; GraphQL/Actions; and code closure that can be protected by required checks, reviews and resolved conversations. [cited] ([Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects), [issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), retrieved 2026-08-22) | An issue opener or triager can close an issue without evidence; a dependency is displayed as blocked but is not documented as an execution or closure gate; Project fields are mutable; and branch protection covers repository integration, not arbitrary work-item truth or principal authorship. [cited] ([closing an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/closing-an-issue), retrieved 2026-08-22) | Strongest presentation incumbent and first optional projection candidate; not the authoritative task kernel. [asserted] |
| **Linear** | One-assignee issues, configurable workflow statuses, blocking relations, projects/initiatives, structured updates, subscriptions, GraphQL and webhooks. [cited] ([issue status](https://linear.app/docs/configuring-workflows), [issue relations](https://linear.app/docs/issue-relations), [project updates](https://linear.app/docs/initiative-and-project-updates), [API and webhooks](https://linear.app/docs/api-and-webhooks), retrieved 2026-08-22) | Official documentation exposes general status closure, comments and relations, not mandatory verifier evidence, immutable dissent or a protected general human verdict. [asserted] (bounded official-documentation search) EXP-16 also measured unsupported state coercion and single OAuth identity erasing agent provenance in its connector path. [measured] (ADR-0006 update and EXP-16) | Optional intake or view only; no round-trip authority. [asserted] |
| **ClickUp** | Rich task fields, custom statuses, multiple assignees, cross-List dependencies, Automations, assigned comments, Proofing, All Tasks, notifications and public APIs. [cited] ([task fields](https://help.clickup.com/hc/en-us/articles/34958796358039-Task-fields-and-the-task-description), [dependencies](https://help.clickup.com/hc/en-us/articles/6309155073303-Intro-to-Dependency-Relationships), [Automations](https://help.clickup.com/hc/en-us/articles/6312097314199-Use-Automation-Actions), retrieved 2026-08-22) | Required fields do not natively block later status changes; dependency and incomplete-item controls are warnings; comments are mutable/deletable; and the Enterprise task audit is time-bounded. [cited] ([required fields](https://help.clickup.com/hc/en-us/articles/30407234676887-Make-Custom-Fields-required), [dependency warnings](https://help.clickup.com/hc/en-us/articles/6304410420759-Dependency-Warnings), [incomplete warning](https://help.clickup.com/hc/en-us/articles/6304420229527-Incomplete-Warning), [audit logs](https://help.clickup.com/hc/en-us/articles/21929900448535-Workspace-audit-logs), retrieved 2026-08-22) | Optional human-facing projection only; warning-based closure cannot guard the evidence record. [asserted] |

The plain answer would be to adopt GitHub Projects because this work already lives beside GitHub
repositories and Projects supplies the mature interface Consilient lacks. [asserted] The retrieved
evidence changes only the authority boundary: adopt that interface later if it measurably reduces
visibility cost, but keep the local append-only work-item record authoritative because none of the
three incumbents enforces the properties beta depends on. [asserted]

This concedes a substantial point: Consilient should never build the views, mobile notifications,
rich comments, proofing or generic workflow editor those products already provide. [asserted] A
projection failure must be visible but must not change readiness, closure or a human verdict.
[asserted]

## 3. One work item, one contract, many attempts

The trajectory is the authority and the work-item state is a pure projection over it. [cited]
(ADR-0006) One ticket survives retries, process deaths and harness changes; each execution gets a new
`attempt_id` and expiring claim. [asserted] A legitimate change of goal or verifier creates a new
revision that names the prior revision; no item is reopened or rewritten in place. [asserted]

### Frozen item fields

`work_item.opened` gains the following required contract. [asserted]

| field | contract |
|---|---|
| `ticket`, `revision` | Stable item identity and positive revision. A later revision carries `supersedes`; the pair is never reused. [asserted] |
| `plan_id`, `plan_digest`, `stream_id` | Binds the item to ADR-0068's frozen minimum-stream plan. A plan change appends a new version. [cited] (ADR-0068) |
| `goal_text`, `success_digest` | The goal is stored verbatim before work starts; the digest covers ordered acceptance criteria and non-goals. [cited] (`feedback-signals.md`) |
| `incumbent` | Source/version, retrieval date, bounded-search digest and measurable better-than-best delta. [asserted] |
| `deliverable_contract` | Expected kind, hand-off schema and allowed locator set; it does not predict the future content digest. [asserted] |
| `accountable` | Exactly one Owner. Added evidence roles never acquire closure authority. [cited] (ADR-0067) |
| `authority_ref` | The frozen authority envelope; principal-only classes remain those enforced by V0-18 and `USER_ONLY`. [measured] (`events.py`) |
| `verifier_contracts` | One or more `{id, digest, task_family, required_outcome}` records frozen before execution. [asserted] |
| `dependencies` | Zero or more `{ticket, revision, handoff_contract_digest}` edges. Future content cannot honestly have a digest yet; the exact artefact digest is bound when the predecessor seals. [algebra] |
| `owned_paths` | Canonical mutable paths. A mutating item with no declared paths is not parallel-claimable. [cited] (ADR-0068) |
| `budget_ref`, `expires_at` | References the existing enforced budget and a timezone-aware upper bound. [asserted] |
| `exposure_contract` | Frozen `{key, epsilon, rule, beta_version, n_max}`. The key covers the goal lineage and composite-verifier contract so a retry or cosmetic revision cannot reset candidate count. [asserted] |
| `composition` | One Owner plus only the ADR-0067 roles whose manifests name a non-overlapping, decision-changing evidence anchor. [cited] (ADR-0067) |

### Attempt and assignment fields

An atomic claim carries `ticket`, `revision`, `attempt_id`, `run_id`, canonical claimed paths,
`opened_at`, `expires_at`, chosen harness/model/family/pool, capability-context digest, plan digest,
candidate ordinal/exposure state and the exact sealed predecessor artefact and verifier-receipt
digests it will consume. [asserted] Family is provenance metadata, never an evidence class. [cited]
(ADR-0067)

### Closure fields

`work_item.completed` is no longer a bare ticket. [asserted] It carries: [asserted]

- `ticket`, `revision`, `attempt_id` and `plan_digest`;
- every delivered artefact's locator, media kind, byte count and SHA-256;
- every required verifier's identifier, frozen contract digest, observed outcome, receipt locator and
  receipt SHA-256;
- the predecessor bindings actually consumed;
- every material conflict and its terminal disposition; and
- the accountable Owner and the coordinator that validated the transition.

`close_item()` validates under the same serialised coordination boundary, then appends the existing
`attempt.outcome` **before** `work_item.completed`, keyed by the same `attempt_id`. [asserted] A crash
between them leaves an outcome without closure, which is visible and safe to resume idempotently; it
never leaves a closed item without its outcome. [asserted] The universal `events.append()` boundary,
not only the convenience helper in `work_items.py`, must refuse a bare or state-invalid completion.
[asserted]

## 4. State machine

The vocabulary is deliberately smaller than Linear, ClickUp or GitHub's configurable workflow
surface. [asserted] State is derived; no actor sets a free-form status string. [asserted]

| state | meaning |
|---|---|
| `blocked` | The contract is valid, but at least one dependency is not evidence-closed, its sealed digest is not bound, a material conflict affecting this item is unresolved, or an accepted commitment correction carries typed cause `commitment_paused`. [asserted] |
| `ready` | All dependency contracts and digests match, no affecting conflict blocks it, budget/expiry admit an attempt, and no live claim exists. [asserted] |
| `active` | One non-expired atomic claim names the attempt, owner, route, paths and predecessor bindings. [asserted] |
| `closed` | All deliverables are sealed and every required frozen verifier accepted; human verdict may still be absent. [asserted] |
| `failed` | Execution or a required verifier failed and the retry policy is exhausted or the failure is non-retryable. [asserted] |
| `refused` | A capability, authority, safety or evidence precondition refused; the reason and attempted path are recorded. [asserted] |
| `cancelled` | Work is intentionally stopped with actor, reason, affected descendants and reversal/replacement where one exists. [asserted] |
| `expired` | The item contract expired before valid closure. A claim expiry alone returns a retryable item to `ready`; it does not expire the item. [asserted] |
| `invalidated` | A later principal rejection, predecessor invalidation or plan revision makes this result unusable. The original record remains and successors name it. [asserted] |
| `superseded` | A newer item revision replaces this contract before closure; the prior revision remains replayable. [asserted] |

### Transitions and their evidence

| transition | admission evidence | assertion alone sufficient? |
|---|---|---|
| create -> `blocked` or `ready` | Valid frozen contract; acyclic existing predecessors; allowed authority; declared paths; verifier and plan digests. [asserted] | **No.** Schema and graph checks decide the initial state. [asserted] |
| `blocked` -> `ready` | Each predecessor is `closed`; its required verifier receipt accepted; its actual artefact digest is bound; every affecting conflict has a non-blocking disposition. [asserted] | **No.** A producer's comment or status is ignored. [asserted] |
| `ready` -> `active` | One serialised read-conflict-open operation proves readiness and no canonical path overlap, then records the assignment and lease. [asserted] | **No.** `coordination.py` is the chokepoint. [asserted] |
| `ready` or `active` -> `blocked` | A bound predecessor is invalidated, a material affecting conflict is recorded, or an accepted superseding commitment carries `commitment_paused`; any live attempt ends adversely and releases its lease before the blocked state projects. [asserted] | **No.** The dependency/conflict/correction record and terminal attempt evidence drive the transition. [asserted] |
| `active` -> `ready` | Attempt timeout, stall or recoverable failure; no live lease; retry budget remains; any reused checkpoint and Git object verify. A retry after composite-verifier exposure also requires admission for candidate `n + 1`. [asserted] | **No.** Process identity, launcher exit code and the label `retry` are insufficient. [measured] (local failure record) [asserted] |
| `active` -> `closed` | Artefact digests, accepted receipts from every frozen verifier, matching dependency bindings and terminal conflict dispositions. [asserted] | **Never.** "Done" in agent prose has no transition. [asserted] |
| non-terminal -> `failed` / `refused` / `cancelled` / `expired` | Typed observed outcome, actor, reason, attempted repair and affected descendants; principal authorship where the reason is principal-only. [asserted] | **No.** The adverse evidence is retained even when zero bytes were produced. [asserted] |
| any revision -> `invalidated` / `superseded` | Principal verdict rejection, a rejected bound predecessor, or a new contract naming the exact prior digest and cause. [asserted] | **No.** The predecessor graph identifies every affected consumer. [asserted] |

All terminal outcomes count in visibility and experiment denominators. [asserted] `closed` is not an
alias for `accepted`: the projection displays `closed / unreviewed`, `closed / accepted` or
`invalidated / rejected` according to the separately authored human verdict. [asserted]

## 5. Assignment policy: schedule the item, reuse the router

Assignment is a policy around `dispatch.py`, not a new router. [asserted]

1. Project all open items and admit only `ready` ones. [asserted]
2. Order ready items by critical-path blocking impact, then earliest expiry, then opening position in
   the trajectory; the order is deterministic and replays identically. [asserted]
3. Keep the item's one accountable Owner. [cited] (ADR-0067) If the principal explicitly named a
   harness, honour it when installed, allowed and budget-feasible; otherwise reuse the existing
   capability, cwd, headroom, family and pool eligibility checks. [measured] (`dispatch.py`,
   `harness.py`, `budget.py`)
4. Bind the selected capability context through `instructions.py` and bounded verbatim history
   through `recall.py`; do not copy the whole project or summarise away adverse events. [measured]
   (current source; EXP-45)
5. Acquire the item and its paths atomically in `coordination.py`; only then invoke the harness.
   [asserted]
6. Create a specialist only when its frozen ADR-0067 manifest names a truth-relevant anchor the
   Owner cannot independently acquire under the isolation contract. [cited] (ADR-0067) The specialist
   receives a child attempt, not a second owner or acceptance vote. [asserted]
7. Count an exposure when a distinct artefact first reaches the frozen composite verifier. [asserted]
   A process restart or checkpoint retry before that boundary remains the same candidate; a revised
   artefact presented after verifier rejection is candidate `n + 1`, whatever its ticket, revision,
   harness or label. [asserted]
8. Check the lineage exposure ledger before that boundary. [asserted] Without a sufficient
   authenticated, trajectory-derived `human_verdict_beta` projection bound to the same task family and
   frozen composite-verifier protocol/version, automatic exposure is zero: candidate `1` refuses
   before the frozen composite verifier. A proxy, mutation estimate or `Beta` with missing or
   mismatched scope fields is ineligible. A non-zero ceiling may come only from `routing.py` over
   that exact projection; ADR-0067's one-Owner default is not an exposure allowance. [cited: ADR-0077;
   verdict-supply §§ 2, 4-5] [asserted]

ADR-0077's dependence-robust ceiling is `n_max = floor(epsilon / beta_upper)`; the logarithmic
formula applies only to a measured frozen iid candidate population. [algebra] `routing.py` implements
the robust refusal but `dispatch.py` does not yet consume it. [measured] Until that boundary is
wired, automatic verifier exposure remains frozen. This specification does not change
`routing_orchestration_enabled`; a future implementation must test the dispatch-path refusal rather
than citing the isolated routing unit. [asserted]

Headroom decides which eligible prepaid route performs the work; it never changes priority, evidence
requirements or authority. [asserted] Model family is allowed to break an otherwise equal routing tie
but cannot justify another member or candidate. [asserted]

## 6. Dependency and disagreement mechanism

### Dependency binding

The frozen plan can know a producer's hand-off contract but cannot know the hash of content not yet
created. [algebra] The plan therefore freezes `{predecessor identity, revision, handoff contract
digest}`; predecessor closure seals the actual artefact and verifier receipts; the consumer's atomic
claim binds those exact digests. [asserted] This is the checkable interpretation of ADR-0068's
"expected predecessor artefact digest", avoiding an invented future hash or a mutable pointer.
[asserted]

Cycles, missing predecessors and a hand-off contract without a required verifier are rejected before
the first claim. [asserted] A failed, refused, expired, invalidated or rejected predecessor blocks its
affected consumers. [asserted] If a later human rejection invalidates an artefact already consumed,
every descendant bound to that digest becomes `invalidated`; a new revision may reuse only unaffected
sealed predecessors. [asserted]

### Shared-artefact disagreement

Parallel producers never write the shared integration surface; one integration item and Owner own
it. [cited] (ADR-0068) A material conflict records the competing claims, evidence references, affected
contract and options before synthesis. [asserted]

Resolution is ordered: [asserted]

1. The already frozen verifier decides when it distinguishes the alternatives. [asserted]
2. If a bounded new execution can decide within authority and budget, append one resolution item
   whose distinct evidence class is that execution. [asserted]
3. If facts do not distinguish several options above the acceptance floor, the integration Owner
   chooses one, records why the other lost, an executable reversal and a falsifier through the
   existing `decision.autonomous` contract. [cited] (working principle 11) [measured] (`events.py`)
4. Escalate only a principal-reserved preference, authority, credential, spend, external exposure or
   irreversible action. [cited] (ADR-0033)
5. Otherwise retain both positions as `recorded_unresolved`. Work whose success contract depends on
   the conflict stays `blocked`; unrelated work may continue. [asserted]

The allowed dispositions are `resolved_by_evidence`, `owner_selected_reversible`, `escalated` and
`recorded_unresolved`. [cited] (ADR-0068) Votes, role seniority, message volume, agreement between
models and last writer are never resolution evidence. [cited] (`CONSILIENCE.md`)

## 7. Closure and human verdicts without homework

Machine closure and human judgement use the identity bridge that already exists: one
`attempt.outcome`, followed later by zero or one `attempt.verdict` with the same `attempt_id`.
[measured] (`events.py`, `projection.py`) The current V0-18/V0-28 check is declared provenance, not
authentication: a caller can set `actor`, `principal` and `via="cli"` consistently. [measured]
Therefore no authenticated verdict ingress exists today. [measured]

A valid future `attempt.verdict` requires a single-use `human_action_receipt` minted by a first-party
human-action broker outside every dispatched harness's capability set. [asserted] The verified
receipt binds principal identity, action, `attempt_id`, delivered artefact digest, issuer/version,
time and nonce; copying fields into an event is insufficient. [asserted] The universal writer checks
the receipt and consumes its nonce atomically with append. [asserted] Until that broker exists, the
CLI and chat may propose or record an unverified feedback signal but may not add a beta verdict.
[asserted]
EXP-53 tests signing cost, replay and key custody at this writer boundary; its register explicitly
does not establish that the signer was human. [cited] (experiment register)

Ordinary work supplies verdicts only when the principal already takes an acceptance action:
[asserted]

- using, merging, approving or explicitly accepting the delivered artefact records `accept` when the
  action is bound to the attempt by an authenticated first-party surface; [asserted]
- returning it for correction, explicitly rejecting it or reverting it as wrong records `reject`
  through the same surface; [asserted]
- the existing task-close feedback answer and durability proxies remain separate signals unless the
  principal explicitly accepts or rejects this attempt; [cited] (`feedback-signals.md`)
- silence, elapsed time, an agent's inference, a remote webhook, a status called `Done`, a model
  grader and a proxy revert pattern never become a human verdict. [measured] (current authority and
  beta contracts)

Existing verdict rows without a verified receipt remain append-only as `declared_unverified` and are
excluded from authenticated beta; they are not silently deleted or retroactively blessed. [asserted]
No extra beta survey is added. [asserted] If no ordinary authenticated acceptance or rejection
occurs, the item remains unreviewed and beta gains no row. [asserted]

Once authenticated ingress exists, this captures naturally occurring rejections at no additional
interaction cost but cannot guarantee 30 rejections by a date. [asserted] Guaranteeing them would
require asking the principal to label work or deliberately presenting bad work; both are rejected.
[asserted] EXP-19 remains the killing test for the existing sampled close prompt, and the beta
verdict takes priority if prompts ever
compete. [cited] (`feedback-signals.md`)

A principal rejection appends the verdict, invalidates the closed revision and opens a corrective
successor unless the principal also cancels the goal. [asserted] It never edits the old closure,
silently relabels descendants or lets an agent "resolve" the verdict. [asserted]

## 8. Visibility without load

The principal never has to remember a dashboard. [asserted] The one conversational front door renders
the work-item projection on demand; the trajectory remains the record and visibility remains a pure
rendering under ADR-0035. [cited] (ADR-0035 and ADR-0067)

On demand, the compact view shows: [asserted]

- the frozen goal and original duration range;
- items by `blocked`, `ready`, `active`, adverse and `closed` state;
- the critical path, accountable Owner and exact blocker for each blocked item;
- latest sealed artefact and verifier receipts;
- failed or unrun checks, refusals, quarantined log lines and unresolved conflicts, including zero
  counts; and
- machine closure separately from absent, accepted or rejected human verdicts.

Only four classes are pushed without the principal asking: [asserted]

1. the initial duration range and success contract; [cited] (ADR-0068)
2. one finished artefact or honest terminal adverse result; [asserted]
3. one pre-breach exception notice when the original upper duration bound will be missed; [cited]
   (ADR-0068)
4. a principal-only or unrecoverable blocker, with what was tried, the default on silence and the
   cost of resolving without him. [cited] (ADR-0033)

Routine progress, green-check narration, reminders to review, agent discussion, unchanged state,
weekly status prose and feedback requests are never pushed as project management. [asserted] A
configured external projection may carry user-selected notifications, but its notification state
never becomes evidence that the principal saw or decided anything. [asserted]

## 9. Implementation boundary

| existing component | minimum extension or reuse |
|---|---|
| `work_items.py` | Validate the frozen contract, project the state machine and prepare evidence-bearing terminal events; `events.append()` remains the sole writer. [asserted] |
| `coordination.py` | Atomically project readiness, refuse path overlap, bind predecessor receipts, issue/release attempt leases and block unresolved shared-artefact conflicts. [asserted] |
| `dispatch.py` | Ask `coordination.py` for the next ready item, then reuse existing headroom/family/capability routing. Record verifier-boundary exposure; do not wire beta routing or add a selection engine under this ADR. [asserted] |
| `events.py`, `projection.py`, `feedback.py` | Enforce the complete closure schema and state at the universal writer; project outcome-before-closure idempotently; exclude unverified declared verdicts; later verify single-use human-action receipts. SQLite remains disposable. [asserted] |
| `recall.py`, `instructions.py`, `routing.py`, `budget.py` | Reuse bounded verbatim context, context layering, robust candidate-ceiling arithmetic and spend enforcement; keep `routing.py` outside the run path. [measured] [asserted] |
| GitHub Projects / Linear / ClickUp | Optional one-way views after explicit external-exposure authority; never required for correctness. [asserted] |

Legacy `dispatch:<run_id>` opened/completed claim events remain replayable as claim history, not as
evidence-closed durable items. [asserted] New runs claim the durable task ticket and identify the
attempt separately; migration never rewrites historical events. [asserted]

## 10. P0 requirements and acceptance checks

Every item below is P0; removing any one permits false closure, premature execution, lost dissent or
human-authority poisoning. [asserted]

- Given an item has no artefact receipt or a required verifier returned fail/unknown, when any actor
  calls either `work_items.py` or `events.append()` directly, then the universal writer refuses and
  no `work_item.completed` is appended. [asserted]
- Given an accepted outcome was appended and the process dies before completion append, when closure
  resumes, then the same outcome is reused idempotently and the item was never projected closed
  during the gap. [asserted]
- Given a predecessor is not evidence-closed or its digest differs, when a consumer is claimed, then
  `coordination.py` refuses before harness invocation. [asserted]
- Given two contenders race on overlapping canonical Windows/WSL paths, when both acquire, then one
  and only one claim succeeds. [asserted]
- Given a live claim expires or its process tree dies, when the item is projected, then the attempt is
  adverse and the item returns to `ready` only under a recorded retry policy and verified checkpoint.
  [asserted]
- Given a material conflict has no allowed disposition, when an affected consumer is projected, then
  it remains `blocked`. [asserted]
- Given an agent submits a field-perfect principal payload with `via="cli"` but no valid unused
  human-action receipt, when universal validation runs, then it refuses and authenticated beta is
  unchanged. [asserted]
- Given relevant beta is unmeasured or insufficient, when candidate `1` would reach the composite
  verifier, admission refuses before verifier execution and no exposure is recorded. Given the
  exact eligible projection admits ceiling `n`, candidate `n + 1` likewise refuses. [asserted]
- Given a proxy or mutation beta, or a generic measured `Beta` whose task family or verifier version
  is absent or mismatched, when candidate `1` would reach the composite verifier, admission refuses
  and the value never enters candidate sizing. [cited: verdict-supply §§ 2, 4-5] [asserted]
- Given a principal rejects a bound predecessor, when descendants are projected, then every consumer
  of that exact digest is invalidated and no unrelated item is changed. [asserted]
- Given the runtime restarts, when the same trajectory is replayed, then state, readiness, owners,
  claims, blockers, conflict dispositions and closure evidence are identical. [asserted]
- Given a projection connector is unavailable or stale, when local state is projected, then readiness
  and closure are unchanged and the projection failure is visible. [asserted]
- Given this documentation-only decision, when the current run path is inspected, then `dispatch.py`
  still does not import `routing.py` and `routing_orchestration_enabled` remains `false`. [measured]
  (existing check)

Success is zero admitted violations in these mutation/property tests, not a self-reported completion
rate. [asserted] EXP-98 separately decides whether the dependency organisation beats one capable
Owner on its frozen mixture; EXP-19 decides whether any residual close prompt survives its friction
budget. [cited] (experiment register)

## 11. Risks, reversals and falsifier

The strongest risk is duplication: the local kernel may grow into an inferior copy of GitHub
Projects, Linear or ClickUp while the principal gets none of their polished interfaces. [asserted]
The boundary above is the reversal: delete any native presentation feature and project the minimal
authoritative state into the strongest incumbent. [asserted]

The mechanism is falsified for the tested task mixture if EXP-98 fails its registered organisation
admission rule; retain one evidence-bearing work item and closure contract, but cut DAG scheduling,
integration items and dependency automation. [asserted] The human-load mechanism is falsified if
EXP-19 fires; remove the sampled prompt and retain only verdicts arising from ordinary acceptance
actions. [asserted]

The verdict path remains blocked if EXP-53 rejects signing at the append boundary or if its key
custody makes the signing capability available to a dispatched harness. [asserted] A passing EXP-53
result still requires a separate executed proof of human isolation before any row enters
authenticated beta. [cited] [asserted]

The adoption decision is overturned if a synthetic, no-private-data pilot demonstrates that an
incumbent can, without a custom authority service: atomically refuse canonical-path clashes; enforce
digest-bound dependencies; require immutable closure evidence; preserve typed dissent; prevent every
agent/integration token from authoring a principal verdict; and export a complete replayable history.
[asserted] A measured reduction in founder review time is then required before making it the
authoritative store. [asserted]
