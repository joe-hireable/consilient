# Consilient implementation plan: from specifications to a claim-safe swarm

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan one unit at a time. A worker may claim only the paths named by its unit.

**Goal:** Turn the current specification set into one ordered, test-gated build programme that delivers useful local product value without making the principal a routine dependency. [asserted]

**Architecture:** Extend the existing JSONL trajectory, projections, work-item kernel and outer dispatch script. `events.py` remains the sole authoritative writer; every other view is reconstructable. No second task store, router, memory service, decision store, effect boundary or orchestrator is admitted. [asserted]

**Tech stack:** Python 3.13 standard library, append-only UTF-8 JSONL, rebuildable SQLite projections, existing scripts and pytest/mypy/Ruff checks. No dependency is added by this plan. [measured: `pyproject.toml`; `AGENTS.md`] [asserted]

**Specifications:** Every file present under `docs/superpowers/specs/` at 2026-08-22 15:08 BST, ADR-0067 and ADR-0070 through ADR-0081, ADR-0068 where those specifications make it a direct dependency, the experiment register, `AGENTS.md`, `CONSILIENCE.md`, and `docs/00-context/the-machine-2026-08-22.md`. [measured]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after any listed specification/ADR changes status or an activation experiment reports. [asserted]

**Falsifier:** A unit cannot be dispatched from this set without inventing an interface, sharing an unlisted mutable path, or weakening an acceptance command; that failure requires a plan amendment before implementation. [asserted]

## Inventory correction

The dispatch brief is wrong in both counts. The directory contains **12** specifications, not 13; the requested ADR set contains **13** ADRs (`0067` plus `0070` through `0081`), not 12. [measured: directory census after the consilience-gate artefacts landed] ADR-0068 is an additional direct dependency of chat, task and delivery, so it is included in this plan but not in the requested-count arithmetic. [measured: chat-conversation section 1; task-management sections 3 and 6]

This count mismatch is not repaired by inventing a missing document. A future thirteenth specification must enter through the ordinary document/ADR trail and receive its own plan amendment. [asserted]

## Global constraints

- `routing_orchestration_enabled` stays `false`; Gate A and Gate B do not change. [measured: `AGENTS.md`] [asserted]
- The `consil` command set stays at six. New operator behaviour uses existing commands, existing scripts or projections. [measured: dispatch brief] [asserted]
- `src/consilient/` remains stdlib-only and under the existing AST ban on subprocess, network, credentials, third-party imports, `getattr` and raw effect methods. [measured: `tests/test_budget.py`; `tests/test_tier1_imports.py`]
- A unit delivers exactly one independently testable capability. It commits after its focused check and before a dependent unit starts. [asserted]
- A worker stages only its named paths and commits with its own `CONSILIENT_RUN_ID`; it never uses `git add -A`. [measured: dispatch contract]
- Every retry, refusal, timeout, quarantine, missing artefact and missing verdict remains in the record and in relevant denominators. [cited: ADR-0072, ADR-0077, ADR-0080]
- One accountable Owner emits one candidate. Extra roles require a named, non-overlapping fact anchor; model agreement over shared inputs is echo. [cited: ADR-0067; `CONSILIENCE.md`]
- Hard decision, action, consilience and self-change admission remain inactive until their registered activation evidence exists. Schema, projection, fake-sink and refusal-only work may land first. [cited: ADR-0076, ADR-0079, ADR-0081]

## Launch gate: specification rulings before affected implementation

The separate specification audit may change wording, but the swarm needs one interpretation. These rulings are the recommended build contract; any audit correction that chooses differently must amend this index and the affected stream plan before dispatch. [asserted]

| ID | Contradiction or gap | Ruling for this plan | Blocks |
|---|---|---|---|
| S-01 | Task management admits one candidate while authenticated human beta is unmeasured, but chat delivery refuses `Done` when relevant beta is unmeasured. [measured: task-management lines 199-205; chat-delivery lines 243-255] | Permit exactly one verifier-exposed candidate under the explicit cold-start policy and render it `closed / unreviewed`; refuse candidate two and never call machine closure human acceptance. This is an `[asserted]` policy, not a beta result. [asserted] | `D04` |
| S-02 | ADR-0068 names an expected future artefact digest; task management correctly says future content has no digest. [measured: ADR-0068 decision 4; task-management lines 221-226] | Freeze the predecessor identity, revision and hand-off-contract digest; bind the actual artefact and verifier-receipt digests at the consumer claim. [algebra] | `T01`, `T02` |
| S-03 | Chat correction defines `pause`, but the task state vocabulary has no `paused`. [measured: chat-conversation lines 268-289; task-management lines 150-161] | Project pause as `blocked` with typed cause `commitment_paused`; do not add a free-form state. [asserted] | `C03` |
| S-04 | Chat migration would make legacy dispatch claims read-only before direct dispatch has a native commitment/plan/item. [measured: chat-conversation lines 347-353; current `scripts/dispatch.py`] | Preserve `item_schema: "dispatch-claim.v1"` for new outer-dispatch claims until the native intake path is end-to-end; only `native.v1` can become evidence-closed task state. Historical rows are never rewritten. [asserted] | `C01`, `T01`, `T02` |
| S-05 | ADR-0078 requires authenticated authority for every present capability, while ADR-0075 permits recovery-proved local/restorable mutation without another approval. [measured: ADR-0075 decision; ADR-0078 decision] | The controller owns baseline authority only for bounded local/restorable operations already inside the committed workspace/authority envelope. Scope widening and every V0-18 class still require exact first-party authority. [asserted] | `A02`, `A04` |
| S-06 | ADR-0078/action-surface place the autonomous decision after or against a receipt; ADR-0079 expressly moves it before intent and reach. [measured] | ADR-0079 governs: decision or protected proposal/authority -> durable intent -> single-use reach -> non-forking receipt -> outcome. No future result is copied backwards. [cited: ADR-0079] | `A01`, `P01`, `A04` |
| S-07 | ADR-0075's closed six-class rule conflicts with ADR-0076's owner approval for every active-harness byte. [measured] | Treat active-harness activation as ADR-0076's narrower use of existing `principal_authority: approval`, not a seventh escalation class. [asserted] | `S04` |
| S-08 | The self-improvement and verdict-supply records claim EXP-104 and EXP-105 are registered, but neither heading exists in the register. EXP-109 now exists and is the ADR-0081 killing test. [measured: exact-heading register search; register lines 4355-4455] | Do not run or activate the affected branches until authorised research-base amendments register EXP-104 and EXP-105. Do not alias them to another experiment. [asserted] | `Q01` research arm; `S01` activation path |
| S-09 | The memory specification fixes fields but not canonical event kinds or capture API; verdict supply likewise leaves queue fields partly open. [measured] | The owning schema units freeze names once in `events.py`: `record.captured`, `capability.versioned`, `model.change`, `review.queue.opened`, `candidate.exposed`, `attempt.reviewed`. Later units consume those contracts and do not invent aliases. [asserted] | `M01`, `M04`, `M06`, `Q01` |
| S-10 | ADR-0081 needs channel, anchor and complete derivation-root metadata beyond the current `verification.outcome` contract. [measured: ADR-0077 enforcement; ADR-0081 decision] | Extend the existing source-kind events; do not create a second evidence table or consilience event. Missing metadata remains `unmeasured`. [asserted] | `G01` |
| S-11 | Class-W documents require falsifier and review-by date, but the living-documentation specification and several peer specifications lack the date. [measured: living-documentation lines 73-83 and its header] | Build the inventory/checker first, migrate admitted files in bounded batches, and enable CI only when the inventory is green. No silent grandfathering. [asserted] | `L04`, `L06` |
| S-12 | Chat defines records but not the executable first-party compiler host; `dispatch.py` explicitly receives sealed work and does not parse chat. [measured: chat-conversation reuse table] | Use the existing local `transport.py`/`scripts/ingest_transport.py` boundary for unprotected intake; protected answers remain proposals until the shared trusted ingress exists. `dispatch.py` still receives only sealed work. [asserted] | `C04` |

## Dependency graph

```text
spec rulings
   |
   v
F01 durable append -> F02 atomic transition -> F03 stable event identity
   |                       |                       |
   |                       |                       +-> E01 verification records -> G01 anchor report
   |                       +-> C01 commitment -> O01 frozen plan -> T01 native tasks -> T02 atomic claim -> D02 checkpoint -> D03 recovery
   |                              |                                      |              |               |
   |                              +-> C02 recall                         +-> T03 closure+-> C03 intake   +-> D04 delivery
   |                                                   +-> T04 task view     |
   |                                                                          +-> D01 estimate
   |
   +-> M01 object capture -> M02 temporal projection -> M03 recall receipt -> M04 manual capability -> M05 dispatch assembly
   |                                                                              |
   |                                                                              +-> M06 model-change record
   |
   +-> A01 effect schema -> A02 gate/escalation -> P01 decision record -> A03 recovery proof -> A04 fake action admission
                                                |                                      |
                                                +-> P02 skill binding                  +-> G02 report-only consilience
                                                                                       +-> A05/A06 adapter migrations
                                                                                       +-> A07 containment -> live local activation evidence

F03 -> V01 estimand/quarantine -> Q01 frozen review queue -> Q02 local card
F03 -> S01 promoter policy -> S02 sealed evaluator/card

L01 ADR index -> L02 generated manifest -> L04 lints/migration -> L06 CI activation
L03 trail ratchet ----------------------------------------------^

H01 trusted ingress -> authenticated consent, grants, verdicts and protected actions
H01 + A07 + registered EXP-104 -> S03 commit binding -> S04 activation -> S05 rollback/drift

G02 + task/capability substrate -> G03 bounded missing-anchor acquisition
EXP-106 decides hard decision-gate activation; EXP-109 decides hard consilience-gate activation.
```

Edges mean “must be accepted and committed before”, not merely “should be considered”. [asserted] The graph deliberately places human ingress on a side branch. [asserted]

## Is trusted human ingress on the critical path?

**No for useful ordinary local product value.** Durable events, native work items, one-candidate machine closure, truthful task/delivery views, bounded recall receipts, explicit/manual capability reuse, decision/consilience reporting, local recovery proofs and refusal-only effect admission do not need the principal to authenticate anything. [asserted]

**Yes for five narrow outcomes:** authenticated consent/grants, authenticated human-verdict beta, protected V0-18 effects without existing standing authority, persistent self-change activation, and a phone/WebAuthn write surface. [asserted] A person is also required when the unresolved input is genuinely their preference or authority; they are not an epistemic tie-breaker. [cited: ADR-0075, ADR-0081]

The nearer blocker for live autonomous child-harness actuation is host containment, not human ingress: current child processes can retain ambient filesystem/network/credential/provider reach outside a typed manifest. [measured: action-surface current-state audit; ADR-0079 context] Until `A07` proves real containment, action work stays fake-sink, local-draft or refusal-only. [asserted]

## Recommended build order

1. **Make the record truthful and durable (`F01-F03`).** Every later promise depends on pre-action and closure records surviving concurrency/crash; building above the current writer would multiply races. [measured] [asserted]
2. **Ship the native task/commitment spine (`C01`, `O01`, `T01-T04`, `C03`).** It turns work into checkable state and produces the earliest substantial surface without a human dependency. [asserted]
3. **Ship honest recall and explicit capability use (`M01-M05`) beside task work where paths permit.** This improves every dispatch while leaving automatic reuse inert. [asserted]
4. **Add estimates, checkpoints and recovery (`D01-D04`).** Their UI waits for authoritative task state, so it cannot become a polished spinner over unverified progress. [asserted]
5. **Add evidence, decision and consilience reporting (`E01`, `V01`, `P01-P02`, `G01-G03`) without hard activation.** The Owner can obtain and expose different anchors before any provisional gate is trusted. [asserted]
6. **Build effect containment and fake-sink admission (`A01-A07`).** Live reach follows only after the universal bypass/host test passes and the relevant experiment authorises activation. [asserted]
7. **Build the shared human ingress and dormant self-improvement path last (`H01-H02`, `S01-S05`).** These are high-risk and do not unlock the ordinary product spine. [asserted]
8. **Run global documentation activation only after bounded migration (`L01-L06`).** Its generator/index units may run earlier in parallel, but a failing global lint is not useful product state. [asserted]

Ingress-first loses because it makes the principal the boot dependency and still does not contain same-OS child capabilities. UI-first loses because it projects claims the kernel cannot yet prove. Action/self-improvement-first loses because both are intentionally dormant behind missing evidence. Dispatching all specifications at once loses because `events.py`, `projection.py`, `work_items.py` and `scripts/dispatch.py` are shared serial surfaces. [asserted]

## Parallelism and claim lanes

The stream plans give exact paths per unit. The following lanes are globally serial even when logical dependencies would otherwise allow overlap. [asserted]

| Lane | Required order |
|---|---|
| `src/consilient/events.py` | `F01 -> F02 -> F03 -> C01 -> O01 -> E01 -> M01(event schema) -> M06 -> A01 -> A02 -> P01 -> Q01 -> H02/self-change schemas` [asserted] |
| `src/consilient/work_items.py` | `C01 -> O01 -> T01 -> T03 -> C03 -> G03 -> D04` [asserted] |
| `src/consilient/projection.py` | `T01 -> T03 -> M02 -> D01 -> V01 -> Q01/Q02 -> G01 -> D04/A08` [asserted] |
| `src/consilient/coordination.py` | `T02 -> C03 -> D02 -> G03` [asserted] |
| `scripts/dispatch.py` | `T02 -> M05 -> D02 -> A03 -> A04 -> G03 -> A07 -> S04` [asserted] |
| `src/consilient/dashboard.py` | `T04 -> V01/Q02 -> A08 -> S02 -> D04` [asserted] |
| `scripts/promote_loop.py` | `S02 -> S04 -> S05` [asserted] |

Safe early parallel work after `F03` is: task schema preparation on `work_items.py`, routing arithmetic on `routing.py`, object-store helper work on `records.py`, promoter policy on `promote.py`, and ADR-index generation under `scripts/build_decision_index.py`. [asserted] Workers still claim their full named path sets before starting. [asserted]

## Three earliest visible product-value units

1. **`M03` — recall receipts and continuation.** Every brief shows what was scanned, selected, omitted and whether context was complete; loss stops being silent. [asserted]
2. **`T04` — evidence-bearing task view.** The existing dashboard shows Owner, blocker, exact artefact/receipts, dissent, adverse counts and `closed / unreviewed` separately. [asserted]
3. **`D04` — honest start/final delivery projection.** One commitment/window message and one final artefact/adverse outcome replace progress chatter, with no claim of human acceptance. [asserted]

`L01` may land first in wall-clock time and visibly repairs the ADR index, but it is repository hygiene rather than the product value the principal asked to see. [asserted]

## Explicit deferrals and cuts

- **Defer:** authenticated phone/WebAuthn writes until a principal-approved dependency or OS broker and a private HTTPS origin are selected; local/read-only review remains. [cited: verdict-supply]
- **Defer:** automatic capability reuse and semantic/vector/graph retrieval until EXP-101; explicit/manual active-head selection remains. [cited: ADR-0074]
- **Defer:** hard decision-gate activation until EXP-106 and hard consilience-gate activation until EXP-109. Build only schema, reporting, acquisition and fake-sink refusal first. [cited: ADR-0079, ADR-0081]
- **Defer:** protected sends, publication, spend, credentials and widened grants until shared trusted ingress and host containment pass. [asserted]
- **Defer:** active self-promotion until EXP-104 is registered and confirms, promoter beta has its denominator, the instrument is sealed, ingress is trusted and rollback is proved. [cited: ADR-0076]
- **Defer:** Tier-1 consequence labels as operational beta and any proxy as a routing input. They remain typed research/preparation signals. [cited: ADR-0080]
- **Defer:** external GitHub Projects/Linear/ClickUp projection until explicit exposure authority and a synthetic/private-safe pilot. [cited: ADR-0072]
- **Cut:** native Kanban, sprint/meeting machinery, generic workflow editor, notification centre, vector database, second memory service, second router, second orchestrator and seventh CLI command. The incumbents already provide the generic surfaces and none is required for the authoritative kernel. [cited: task-management; ADR-0072]
- **Out of scope:** secrets, metered calls, pushing, private commercial repositories, power-loss guarantees beyond the specified fsync/platform contract, and claims that the unrun experiments have passed. [measured: dispatch limits] [asserted]

## Plan files

- `2026-08-22-foundation-task-delivery-plan.md` — `F`, `C`, `T` and `D` units. [asserted]
- `2026-08-22-memory-documentation-plan.md` — `M` and `L` units. [asserted]
- `2026-08-22-evidence-decision-action-plan.md` — `E`, `R`, `V`, `Q`, `P`, `G` and `A` units. [asserted]
- `2026-08-22-human-self-improvement-plan.md` — `H` and `S` units, mostly dormant or deferred. [asserted]

## Whole-program completion check

No stream declares completion until its focused tests pass, the complete existing suite passes, strict mypy passes over `src/consilient`, Ruff passes, the six-command and routing-flag invariants remain, and a replay from the append-only log reproduces every affected projection. [asserted]

```powershell
python -m pytest tests -q
python -m mypy --strict src/consilient
python -m ruff check .
```

The recorded baseline of 891 tests is a floor from the brief, not a frozen expected test count; implementation adds tests, so acceptance is zero failures rather than equality to 891. [asserted]
