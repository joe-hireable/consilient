# Squad roles and pull-only observability implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Execute one numbered unit, run its exact acceptance command, commit only its claim paths, then release the claim.

**Goal:** Project exact per-item role rights and let a user inspect recorded squad state without creating meetings, epistemic votes, pushed progress or implicit authority. [asserted]

**Architecture:** Extend the native work-item, coordination, projection, dashboard, instruction and dispatch paths. The trajectory remains the only role/control record; the dashboard remains disposable; adapter controls stay in `scripts/dispatch.py`. [cited: ADR-0067, ADR-0082, ADR-0083]

**Tech stack:** Existing Python standard library, JSONL trajectory, rebuildable SQLite/dashboard projections and harness probes. No dependency or command is added. [measured] [asserted]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after EXP-107/108 reports or ADR-0082/0083 changes status. [asserted]

**Falsifier:** Any unit grants epistemic weight from a role/model label, mutates a run before its request record, makes watching authoritative, or needs a second assignment/control store. [asserted]

## Stream constraints

- The default composition stays one runtime co-holding Accountable and Responsible; schema and experiment-arm work do not activate generic RACI before EXP-107. [cited: ADR-0082]
- Responsible and Consulted roles feed one Owner candidate. Candidate exposure remains solely under ADR-0077 and `routing.py`. [cited: ADR-0077, ADR-0082]
- Read-only pull can ship without trusted human ingress. Redirect, stop on request and Owner takeover remain proposals until H01/H02 authenticates their author; autonomous safety timeout/kill remains controller-owned. [cited: ADR-0083] [asserted]
- Live inspection remains opt-in and local until EXP-108; ordinary chat still sends only the estimate/exception/final delivery defined by ADR-0071. [cited: ADR-0071, ADR-0083]
- Units sharing `events.py`, `work_items.py`, `projection.py`, `coordination.py`, `dashboard.py` or `scripts/dispatch.py` are serial with the global lanes in the build-plan index. [asserted]

## RAC01 — closed per-item role and authorship contract

**Deliverable:** One native work-item revision records exactly one Accountable Owner plus bounded R/C/I assignments, and the universal event transition enforces each role's authoring rights without creating standing identity or principal authority. [asserted]

**Depends on:** F03, T01 and A02. It remains experiment-only/default-one-runtime pending EXP-107. [asserted]

**Why:** ADR-0082 decision “Exact rights”, “Composition, method and authority” and “Assignment and release”. [cited: ADR-0082]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `tests/test_squad_role_contract.py` (new)
- `tests/test_work_items.py`
- `tests/test_v0_invariants.py`

**Steps:**

1. Freeze `assignment_id`, closed role, assignee, ticket/revision, scope/contract, authority/budget refs, expiry and the role-specific R/C/I contract in native composition. [asserted]
2. Keep Accountable as the existing scalar Owner; reject a second A, persistent rank and free-form role rights. [asserted]
3. Enforce A-only candidate/disposition/closure content, R-only scoped artefacts/receipts, C-only sealed readings/dissent and no I-authored contribution through F02's generic append path. [asserted]
4. Reject every attempt to turn role assignment into one of ADR-0075's six protected authorities. [asserted]
5. Default to one runtime holding A+R; reject extra R/C runtime execution unless the work item binds the prospectively frozen EXP-107 arm. Add a source-tree ratchet rejecting a second assignment registry, writer, coordinator, fusion path or CLI command. [asserted]

**Done:** Raw append and helper calls make the same decision; role co-holding is explicit; an agent labelled A cannot author approval, consent, verdict, spend or gate lift. [asserted]

```powershell
python -m pytest tests/test_squad_role_contract.py tests/test_work_items.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(work): enforce per-item squad rights`. [asserted]

## RAC02 — structurally admitted consultation

**Deliverable:** The projection admits C only from a completed, contract-matching distinct acquisition and otherwise records the assignment as I with `echo` or `unmeasured`, without requiring agreement. [asserted]

**Depends on:** RAC01, E01 and G01. [asserted]

**Why:** ADR-0082 “Consulted admission and echo”; ADR-0081 countable channel and anchor contract. [cited: ADR-0081, ADR-0082]

**Claim exactly:**

- `src/consilient/projection.py`
- `tests/test_consulted_admission.py` (new)

**Steps:**

1. Resolve the exact earlier source-kind event and its acquisition channel, observation anchor, derivation roots and frozen decision-changing observation. [asserted]
2. Require known disjoint roots and no recorded prohibited pre-seal peer/Owner synthesis access; missing isolation metadata is `unmeasured`. [asserted]
3. Preserve a structurally valid dissenting reading as C; agreement is never an admission predicate. [asserted]
4. Give model/provider family, title, persona, evidence tag, repeated context and vote zero structural credit. [asserted]

**Done:** Metamorphic fixtures changing only family/role labels never change I to C; a valid distinct contradictory reading remains C and retains its immutable refs. [asserted]

```powershell
python -m pytest tests/test_consulted_admission.py tests/test_decision_protocol.py -q
```

**Commit:** `feat(projection): admit consulted evidence structurally`. [asserted]

## RAC03 — dissent and pre-committed blocking through closure

**Deliverable:** Structured R/C positions and necessary-condition failures survive replay, and native closure refuses every undispositioned material conflict while leaving the Owner as sole non-protected decider. [asserted]

**Depends on:** RAC01, RAC02 and T03. [asserted]

**Why:** ADR-0082 “Dissent and blocking”; task-management conflict vocabulary. [cited: ADR-0082]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/projection.py`
- `src/consilient/events.py`
- `tests/test_squad_dissent.py` (new)

**Steps:**

1. Freeze a pre-outcome `position_contract_ref` with the canonical position kind/domain/comparator and explicit neutral value; bind every R/C return to that contract, scope/estimand/limits, exact evidence refs and immutable assignment. [asserted]
2. Derive dissent for every incompatible non-neutral return against the Owner's explicit `selected_position` using that comparator; contributors cannot suppress numeric, ranked, enum, Boolean or scoped disagreement with a Boolean flag. [asserted]
3. Derive frozen necessary-condition failures separately, never from prose sentiment, and require `resolved_by_evidence`, `owner_selected_reversible`, `escalated` or `recorded_unresolved`; validate consequence/reversal/falsifier fields for Owner selection. [asserted]
4. Enforce the derivation and closure rule through the universal append path, block success-dependent unresolved conflict and preserve every earlier position after resolution. [asserted]

**Done:** Deleting projections and replaying reproduces conflict/disposition state; bypass append cannot erase dissent or close through an undispositioned conflict. [asserted]

```powershell
python -m pytest tests/test_squad_dissent.py tests/test_work_item_closure.py -q
```

**Commit:** `feat(work): preserve squad dissent through closure`. [asserted]

## RAC04 — atomic assignment claim and authorised release

**Deliverable:** R/C assignment acquisition, lease fencing and terminal release are one identity-bound coordination transition; I receives no claim and expiry remains an adverse return. [asserted]

**Depends on:** RAC01 and T02. [asserted]

**Why:** ADR-0082 “Assignment and release”; the measured check-then-open and unauthorised-release gaps. [cited: ADR-0082]

**Claim exactly:**

- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_role_claims.py` (new)

**Steps:**

1. Bind ticket/revision, assignment/attempt, assignee, role, canonical paths or observation-anchor contract, expiry and fencing epoch under F02's lock. [asserted]
2. Recheck role rights, structural acquisition contract and path/anchor conflict before issuing a claim. [asserted]
3. Accept release only from the assigned actor or accountable controller with the matching terminal outcome/refusal/root closure. [asserted]
4. Release resource ownership after expiry while recording the required assignment's adverse outcome; never treat expiry as successful optionality. [asserted]

**Done:** Two contenders admit one claim; another actor and a stale epoch cannot release it; an expired required C remains adverse and blocks closure. [asserted]

```powershell
python -m pytest tests/test_role_claims.py tests/test_coordination.py -q
```

**Commit:** `feat(coordination): fence squad assignments`. [asserted]

## RAC05 — remove family-derived evidence credit

**Deliverable:** Harness family remains correlation metadata only; fan-out emits no `family:*` evidence class and cannot turn shared inputs into Consulted admission or an extra candidate allowance. [asserted]

**Depends on:** RAC02 and RAC04. [asserted]

**Why:** ADR-0067 and ADR-0082 explicitly reject model family as a fact class. [cited: ADR-0067, ADR-0082]

**Claim exactly:**

- `src/consilient/harness.py`
- `scripts/dispatch.py`
- `tests/test_dispatch_evidence_classes.py` (new)

**Steps:**

1. Trace and remove every family-derived evidence-class producer while preserving family as dependence/correlation metadata. [asserted]
2. Route every proposed evidence role through RAC02's structural result. [asserted]
3. Keep routing exposure determined by attempts and the robust ceiling, not role or runtime count. [algebra]

**Done:** Same-fact cross-family fan-out projects as echo/I and one candidate; adding a valid external execution anchor changes evidence state but not candidate count. [asserted]

```powershell
python -m pytest tests/test_dispatch_evidence_classes.py tests/test_coordination.py -q
```

**Commit:** `fix(dispatch): stop treating family as evidence`. [asserted]

## RAC06 — method ownership and artefact binding

**Deliverable:** When P02 selects Better-than-Best or an empirical Experimenter contract, A cannot waive it and closure requires the assigned R's registered, pre-outcome method artefacts. [asserted]

**Depends on:** P02 and RAC03. [asserted]

**Why:** ADR-0082 “Composition, method and authority”. [cited: ADR-0082]

**Claim exactly:**

- `src/consilient/instructions.py`
- `src/consilient/work_items.py`
- `tests/test_squad_method_roles.py` (new)

**Steps:**

1. Bind the selected skill/experiment contract to the A and R assignments and assembled-instruction digest. [asserted]
2. Require the five Better-than-Best artefact references when selected. [cited: ADR-0079]
3. For empirical resolution, require a register heading and fixed stopping-rule digest predating the first outcome. [asserted]
4. Keep the skill responsible for judgement; the structural check verifies invocation and artefacts only. [asserted]

**Done:** Removing, postdating or substituting the method artefact blocks closure; a one-runtime A+R case retains both responsibilities without adding a member. [asserted]

```powershell
python -m pytest tests/test_squad_method_roles.py tests/test_instructions.py -q
```

**Commit:** `feat(work): bind assigned scientific method`. [asserted]

## OBS01 — deterministic four-depth pull projection

**Deliverable:** The existing local dashboard exposes attention, squad, work-item and agent depths from one pinned event prefix, renders every absent fact as `not recorded`/`unavailable`, and performs no write or network action. [asserted]

**Depends on:** T04, M03, M05, R01, V01, P01 and RAC02. Missing later facts remain named absences rather than blocking the projector. [asserted]

**Why:** ADR-0083 decision “one same-machine, pull-only projection”. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/projection.py`
- `src/consilient/dashboard.py`
- `tests/test_observability_projection.py` (new)

**Steps:**

1. Define stable selectors for delivery, squad, ticket, run and recorded runtime/session identity. [asserted]
2. Project the exact four depth contracts without a progress percentage, quality adjective, inferred rationale or hidden-chain-of-thought claim. [asserted]
3. Keep opening/refreshing a view ephemeral in v0; do not add optional `observability.pull` storage merely to count views. [asserted]
4. Prove same-machine rendering, HTML escaping, no remote resources/telemetry and no tracked trajectory artefact. [asserted]

**Done:** Identical prefixes give byte-identical facts; repeated pulls leave trajectory, authority, acceptance, Owner and delivery messages unchanged. [asserted]

```powershell
python -m pytest tests/test_observability_projection.py tests/test_task_dashboard.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(dashboard): add pull-only squad depths`. [asserted]

## OBS02 — write-ahead intervention and lineage record

**Deliverable:** `intervention.requested`, `intervention.outcome` and applied Owner-change state form one exact reference chain, and the projector derives `autonomous`, `steered`, `operator_controlled` or `cancelled_by_user`. [asserted]

**Depends on:** F03, C03, T02, D02 and P01. This unit records/refuses only; it invokes no adapter. [asserted]

**Why:** ADR-0083 decision and enforcement “write-ahead”/“lineage”. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `src/consilient/projection.py`
- `tests/test_intervention_protocol.py` (new)

**Steps:**

1. Validate the complete request/outcome identities, target epoch, auth status, safe boundary, instruction/evidence revision, checkpoint, preserved/quarantined artefacts and pre/post state. [asserted]
2. Require one earlier request for every outcome and exactly one terminal outcome per request. [asserted]
3. Refuse principal-only action/Owner transfer without H02's exact authority receipt; actor/channel strings remain declarations. [asserted]
4. Derive lineage from immutable events; a runtime may not supply or downgrade its own label. [asserted]

**Done:** Late/missing/duplicate/mismatched outcomes refuse; adding any applied mutating intervention makes `autonomous` impossible while read-only projection has no effect. [asserted]

```powershell
python -m pytest tests/test_intervention_protocol.py tests/test_decision_protocol.py -q
```

**Commit:** `feat(events): record intervention lineage`. [asserted]

## OBS03 — harness control-capability probe

**Deliverable:** Each installed harness/version truthfully declares addressable inspect, safe-inject, stop and takeover primitives; an absent capability returns a typed refusal and is never emulated from PID or prompt text. [asserted]

**Depends on:** OBS02. Run before PC03-PC07, which extend the same probe lane. [asserted]

**Why:** ADR-0083 requires adapter-native control and explicit absence. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/harness.py`
- `scripts/dispatch.py`
- `tests/test_dispatch_control_capabilities.py` (new)

**Steps:**

1. Extend the existing harness probe result with closed control capabilities and the version/rationale which established them. [asserted]
2. Keep process handles and subprocess operations in the outer script; product code receives inert typed facts only. [asserted]
3. Mark unsupported/unknown/stale native surfaces unavailable and refuse a mutation that needs them. [asserted]

**Done:** Fake version/help fixtures reproduce capability results; changing only PID/process name cannot make an unsupported control available. [asserted]

```powershell
python -m pytest tests/test_dispatch_control_capabilities.py tests/test_dispatch.py -q
```

**Commit:** `feat(dispatch): probe native run controls`. [asserted]

## OBS04 — recorded-context inspection

**Deliverable:** Agent-depth inspection joins the sealed commitment, plan, instruction/recall receipts, declared tools, decisions, evidence, checkpoint and retained adapter output without claiming unrecorded live context. [asserted]

**Depends on:** OBS01, OBS03, M05 and D02. [asserted]

**Why:** ADR-0083 distinguishes read context from attaching to hidden process state. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/dashboard.py`
- `scripts/dispatch.py`
- `tests/test_run_inspection.py` (new)

**Steps:**

1. Resolve every displayed component by stable id/digest from retained run artefacts and trajectory refs. [asserted]
2. Attach a native live transcript only when OBS03 proves the surface and label it non-authoritative. [asserted]
3. Render missing/deleted/unavailable transcript and context explicitly; never synthesise reasoning from outcome prose. [asserted]

**Done:** Removing any optional retained file changes only that field to unavailable; commitment, evidence, authority and task state remain event-derived. [asserted]

```powershell
python -m pytest tests/test_run_inspection.py tests/test_observability_projection.py -q
```

**Commit:** `feat(dashboard): inspect recorded run context`. [asserted]

## OBS05 — controller-owned terminal stop and release

**Deliverable:** The existing external dispatcher controller writes an intent, revokes the epoch, tree-kills/verifies the child, appends one terminal dispatch/outcome and releases the claim without asking the killed process to report itself. [asserted]

**Depends on:** T02, D02, OBS02, OBS03 and A01. User-requested use also depends on H02; autonomous timeout/safety-stop uses controller baseline authority. [asserted]

**Why:** ADR-0083's measured killed-claim defect and displacement check. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_dispatch_stop.py` (new)

**Steps:**

1. Add the stop path to the existing dispatcher script, not a seventh `consil` command or second controller. [asserted]
2. Validate request, run, epoch and authority before revocation; refuse unrelated/stale terminal records. [asserted]
3. Reuse the proven Windows/POSIX process-tree termination path, independently verify death, mark unsealed work diagnostic and preserve the latest sealed checkpoint. [asserted]
4. Append terminal outcome/release as one recoverable transaction and make retries idempotent. [asserted]

**Done:** Process-tree and crash-cut fixtures leave no live stale claim, no stale writer, one terminal outcome and the prior checkpoint/artefacts unchanged. [asserted]

```powershell
python -m pytest tests/test_dispatch_stop.py tests/test_coordination.py tests/test_delivery_recovery.py -q
```

**Commit:** `fix(dispatch): stop runs and release claims externally`. [asserted]

## OBS06 — authenticated redirect and evidence addition

**Deliverable:** An authenticated unprotected steering receipt applies one instruction/evidence revision at a declared safe boundary or stops/restarts the same candidate from its valid checkpoint under a higher epoch; incompatible output is quarantined. [asserted]

**Depends on:** H02, C03, D02, OBS02, OBS03 and OBS05. [asserted]

**Why:** ADR-0083's redirect/add-evidence semantics. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/instructions.py`
- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_steering.py` (new)

**Steps:**

1. Bind the accepted steering receipt, correction/evidence refs and new instruction digest before adapter contact. [asserted]
2. Use native safe injection only when OBS03 proves it; otherwise use OBS05 plus D03 recovery for the same candidate. [asserted]
3. Require child acknowledgement of the new revision before another operation and quarantine incompatible unsealed output. [asserted]
4. Reforecast/replan through C03/D01 when the commitment changed; never edit the original request or estimate. [asserted]

**Done:** Injection/restart races cannot admit output under the old revision; every applied steer has one outcome and makes delivery `steered`. [asserted]

```powershell
python -m pytest tests/test_steering.py tests/test_intervention_protocol.py tests/test_delivery_recovery.py -q
```

**Commit:** `feat(dispatch): steer at recorded safe boundaries`. [asserted]

## OBS07 — authenticated Owner takeover

**Deliverable:** Exact first-party authority transfers one stream to the principal at a safe boundary under a higher epoch, prevents autonomous closure and permits an equally explicit transfer back. [asserted]

**Depends on:** H02, A07, RAC01, OBS02, OBS05 and OBS06. [asserted]

**Why:** ADR-0083 requires authenticated takeover and `operator_controlled` lineage. [cited: ADR-0083]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_owner_takeover.py` (new)

**Steps:**

1. Verify H02 receipt purpose/scope/expiry and the matching live assignment/epoch. [asserted]
2. Seal or quarantine the slice, revoke the old epoch and bind the new local principal session without exposing a reusable authority handle. [asserted]
3. Block autonomous completion for the transferred stream and derive `operator_controlled`; preserve unrelated streams. [asserted]
4. Require another authenticated event and higher epoch to return control. [asserted]

**Done:** Spoofed/replayed/wrong-scope authority and stale agents cannot take/recover control or close; a valid round trip preserves the full artefact and intervention chain. [asserted]

```powershell
python -m pytest tests/test_owner_takeover.py tests/test_human_action_receipts.py tests/test_role_claims.py -q
```

**Commit:** `feat(coordination): transfer owner control safely`. [asserted]

## Stream completion and activation

RAC01-RAC06 may support the frozen EXP-107 arm but the default remains one A+R until that experiment confirms and ADR-0082 changes status. OBS01/OBS04 may ship as local pull-only views; live-default trust claims wait for EXP-108. OBS06/OBS07 remain unreachable until H02 and containment pass. [cited: ADR-0082, ADR-0083]

```powershell
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m mypy --strict src/consilient
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m ruff check .
```
