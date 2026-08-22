# Evidence, decision and action implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Execute one unit, run its exact acceptance command, commit only its claim paths, then release the claim. [asserted]

**Goal:** Make candidate exposure, evidence, decisions and effect attempts replayable and structurally checkable while every action remains fake, inert or refused until containment and the registered activation evidence exist. [asserted]

**Architecture:** `events.py` remains the only authoritative append-only record and SQLite remains a disposable projection; this plan adds neither an evidence store nor an effect store. [cited: ADR-0077, ADR-0078, ADR-0079] One pure `effects.py` module owns the single admission protocol, while existing outer scripts and connectors may consume that protocol but may not create another boundary. [asserted]

**Tech stack:** Existing Python 3.13 standard-library product code, append-only UTF-8 JSONL, rebuildable SQLite projections, existing outer scripts/connectors and pytest. [measured: `pyproject.toml`; `AGENTS.md`]

**Spec:** `docs/superpowers/specs/2026-08-22-evidence-fusion.md`, `docs/superpowers/specs/2026-08-22-verdict-supply.md`, `docs/superpowers/specs/2026-08-22-decision-protocol.md`, `docs/superpowers/specs/2026-08-22-action-surface.md`, `docs/superpowers/specs/2026-08-22-consilience-gate.md`, ADR-0067, ADR-0075 and ADR-0077 through ADR-0081. [measured]

- **Document class:** W, because this plan contains implementation judgement rather than generated state. [cited: `docs/superpowers/specs/2026-08-22-living-documentation.md`, Class W]
- **Review by:** 2026-09-22. [asserted]
- **Falsifier:** Withdraw or amend this decomposition if a clean execution cannot accept any unit using only its claimed paths and committed predecessors, or if completing a unit requires a second authoritative evidence/effect store or a second path to live reach. [asserted]

## Global constraints

- `routing_orchestration_enabled` remains `false`; Gate A and Gate B do not change, and no seventh `consil` command is added. [measured: `AGENTS.md`; dispatch brief] [asserted]
- `src/consilient/` remains standard-library-only and under the existing bans on subprocess, network, credentials, third-party imports, `getattr` and raw effect reach. [measured: `tests/test_budget.py`; `tests/test_tier1_imports.py`]
- `events.py` is the sole authoritative writer. New SQLite tables, dashboard payloads and queue views are rebuildable projections only; another evidence ledger, decision database, effect ledger or provider-state authority is a defect. [cited: ADR-0077, ADR-0078, ADR-0079]
- Foundation units `F01` through `F03` must first provide process-serialised durable append, atomic compare-and-append and stable exact event references. [cited: ADR-0079; decision protocol sections 4, 7 and 9]
- The current uncommitted `verification.outcome` validator/tests and robust union-bound arithmetic are partial `E01` and `R01` work. Their units finish, rename and verify those slices; workers must not create duplicate event kinds, helpers or tests under new names. [measured: current diffs in `events.py`, `routing.py`, `test_coordination.py` and `test_v0_invariants.py`]
- ADR-0079 governs ordering where ADR-0075/0078 and the action-surface prose still mention a later receipt inside the decision: durable decision or protected proposal/authority, durable `effect.intent`, single-use reach, non-forking `effect.receipt`, then existing outcome. No future result is copied backwards. [cited: ADR-0079 sections Context and Decision]
- Every action-path acceptance fixture uses a fake sink, inert adapter, an isolated scratch-only containment probe or refusal. A07 may start a local test container whose denied process/file/network attempts are the measurement; no unit activates an external request, message, publication, spend, credential, provider or physical effect. [asserted]
- `A07` must prove containment before any later plan may expose live reach. A passing static scan without an outer runtime denial is not containment, and process-tree termination is not reversal. [cited: ADR-0078; ADR-0079; action-surface sections 5 and 9]
- EXP-106 decides whether hard pre-action decision admission may activate; EXP-109 decides whether a single-anchor high-consequence conclusion may be refused. This plan builds schemas, projections, report-only evaluation, bounded acquisition and fake admission only. [cited: ADR-0079; ADR-0081; experiment register EXP-106 and EXP-109]
- Human ingress is not on this stream's build critical path. Authenticated human beta, phone writes and protected authority remain separate prerequisites; `Q02` is local and read-only, and `G03A/G03B` never ask a human to manufacture an evidence anchor. [cited: verdict-supply sections 5 and 8; ADR-0081]
- One Owner emits one candidate. Candidate exposure is bounded by `R01`; additional readers remain cut unless they acquire a named different fact anchor, and role count never enlarges `n_attempt_max`. [cited: ADR-0067; ADR-0077]
- Each unit has one deliverable and one reviewer gate. A worker stages only its exact claim paths and never uses `git add -A`; shared source paths are serial even where logical dependencies would otherwise permit parallel work. [asserted]
- The brief's 891 passing tests are a floor, not an exact future count. Every focused command and the whole-program checks must finish with zero failures. [measured: dispatch brief] [asserted]

## Dependency and path-claim order

```text
R01 (finish robust arithmetic; remains unwired)

F03 -> E01 -> V01
  |      |       `-> Q01 -> Q02
  |      `-------------> G01
  |
  `-> A01 -> A02 -> P01 -> P02 -> A03 -> A04 -> G02
                                                |       \
                                                |        `-> G03A -> G03B (after A07 and task/capability substrate)
                                                `-> A05 and A06 -> A07
                                                         `-------> A08 -> A09 (also after G01/Q02)

EXP-106: later activation decision for P01/A04
EXP-109: later activation decision for G02/G03A/G03B
```

The arrows mean accepted and committed predecessors, not merely available working-tree changes. [asserted]

| Shared path | Required claim order |
|---|---|
| `src/consilient/events.py` | `E01 -> A01 -> A02 -> P01 -> Q01 -> G01` [asserted] |
| `src/consilient/projection.py` | `V01 -> Q01 -> Q02 -> G01 -> A08 -> A09` [asserted] |
| `src/consilient/beta.py` | `V01 -> Q01` [asserted] |
| `src/consilient/effects.py` | `A01 -> A02 -> A03 -> A04 -> G02` [asserted] |
| `src/consilient/instructions.py` | `P02 -> G03A` [asserted] |
| `src/consilient/work_items.py` | foundation `T03 -> P01 -> G03A` [asserted] |
| `scripts/dispatch.py` | `A04 -> A07 -> G03B` [asserted] |
| `src/consilient/dashboard.py` | `Q02 -> A08 -> A09` [asserted] |
| `tests/test_v0_invariants.py` | `E01 -> Q01 -> A04 -> A07` [asserted] |

`R01` may run immediately. After `F03`, `E01` and `A01` cannot run concurrently because both claim `events.py`; the table chooses `E01` first so the existing partial work is secured. [asserted] `V01` may run beside the action lane after `E01`, while `A05` and `A06` may run in parallel because `A04` freezes their shared interface and their claim paths are disjoint. [asserted]

## Human-ingress boundary

Trusted human ingress is not on the critical path for any unit in this file: `R01/E01/V01` are record/projection work, `Q02` stops at a read-only card, `P01/P02/G01/G02` are schema/reporting work, `A01-A09` use fake or inert reach, and `G03A/G03B` acquire a world anchor without a human. [asserted]

Trusted ingress is a real prerequisite for authenticated human-verdict beta, a write-capable phone card, WebAuthn enrolment/recovery and a protected action lacking already valid standing authority. [cited: ADR-0075; ADR-0080; verdict-supply sections 5 and 8] Independent human outcome judgements are also part of EXP-106 and EXP-109 measurement, but their absence does not block construction of the dormant treatment/control mechanisms. [cited: experiment register EXP-106 and EXP-109]

---

## R01 - finish the dependence-robust candidate ceiling

**Deliverable:** The existing unwired routing helper exposes `n_attempt_max = floor(epsilon / beta_upper)`, returns zero when `epsilon < beta_upper`, and refuses unmeasured human beta without importing an iid assumption. [algebra] [cited: ADR-0077; evidence-fusion sections 1, 2 and 10]

**Why:** Candidate attempts form a union, not the verifier intersection, and the current partial patch still publishes the superseded field name `n_max`. [measured: `src/consilient/routing.py`; evidence-fusion lines 131-133]

**Depends on:** No implementation unit; this is a finish-not-duplicate unit over the existing partial diff and remains unwired. [measured] [asserted]

**Claim exactly:** [asserted]

- `src/consilient/routing.py`
- `tests/test_coordination.py`

**Interfaces:** `routing.Ceiling.n_attempt_max: int | None`, `routing.candidates_ceiling(estimate: beta.Beta, epsilon: float) -> Ceiling | RoutingRefusal`, and the existing `ceiling_for_trajectory()` bridge. [asserted]

**Steps:**

1. Extend the current focused tests for `epsilon` below, equal to and above `beta_upper`, interval endpoints zero/one, invalid epsilon and insufficient human beta; retain a negative test that dispatch does not consume the helper. [asserted]
2. Run the acceptance command and confirm the field rename/edge cases fail against the partial slice rather than creating another test file. [asserted]
3. Rename `n_max` to `n_attempt_max`, finish the robust arithmetic and update only direct callers/docstrings; do not add an iid activation branch or wire dispatch. [asserted]
4. Re-run the acceptance command and inspect the returned object, not only the process exit code. [asserted]

**Done:** All robust-ceiling cases pass, the unmeasured trajectory refuses, and a source assertion proves `scripts/dispatch.py` still does not import or call routing. [asserted]

```powershell
python -m pytest tests/test_coordination.py -q
```

**Commit:** `fix(routing): finish the robust candidate ceiling`. [asserted]

## E01 - finish replayable verification outcome records

**Deliverable:** The existing partial `verification.outcome` kind becomes the one complete, replayable component-verification record required for later correlation and structural-anchor analysis. [cited: ADR-0077; evidence-fusion section 7]

**Why:** Correlation cannot be measured from a composite Boolean, and another evidence table or outcome kind would split authority. [cited: ADR-0077]

**Depends on:** `F03`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/events.py`
- `tests/test_v0_invariants.py`

**Interfaces:** `verification.outcome.data` requires `verification_id`, `attempt_id`, `protocol_id`, lowercase `artefact_sha256`, `verifier_id`, `verifier_version`, `evidence_class`, terminal `status`, and `verifier_accept` only for `completed`; it remains appendable only through `events.append()`. [cited: evidence-fusion lines 263-308]

**Steps:**

1. Extend the two existing partial tests in place to cover every terminal status, conditional Boolean, malformed digest/version, human-verdict smuggling, repeated evidence classes and all four paired contingency cells. [asserted]
2. Run the acceptance command and identify only the missing cases in the partial validator. [asserted]
3. Finish the validator without inventing a composite outcome, uniqueness index, writer or CLI path; leave duplicate correlation-key refusal to replay analysis in `G01`. [asserted]
4. Rebuild a projection from the appended fixtures and compare the paired payloads and rejection list to the expected artefact. [asserted]

**Done:** Every planned component has one terminal record shape; paired outcomes survive append/replay; missing/error states are not cast to rejection; and no human verdict can enter this event. [asserted]

```powershell
python -m pytest tests/test_v0_invariants.py -k "verification_outcome" -q
```

**Commit:** `feat(evidence): complete verification outcome records`. [asserted]

## V01 - project only authenticated human beta and quarantine bad joins

**Deliverable:** One truthful human-beta projection excludes proxy estimands, quarantines relationally invalid verdict rows without halting replay, and exposes quarantine, sampling and oracle caveats in both human and JSON output. [cited: ADR-0080; verdict-supply sections 2, 4 and 5]

**Why:** Schema-valid but unjoinable rows currently can brick projection or disappear from the operator's view, and proxy estimands must never become routing input. [measured: `projection.py`; verdict-supply lines 143-170 and 285-318]

**Depends on:** `F03`, `E01`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/projection.py`
- `src/consilient/beta.py`
- `src/consilient/cli.py`
- `tests/test_verdict_supply.py` (new)

**Interfaces:** The beta consumer admits only `estimand_kind == "human_verdict_beta"` with authenticated provenance; relational quarantine rows carry source path, line, digest and reason; beta output carries quarantine count/locators, projection-derived `sampling_unconditioned` and the human-oracle caveat. [cited: verdict-supply lines 149-170 and 305-310]

**Steps:**

1. Create fixtures for all four named estimands, unknown/duplicate outcomes and verdicts, invalid corrections, missing component joins and a valid legacy declared-principal row. [asserted]
2. Run the acceptance command and confirm current replay either raises or omits the required caveat/quarantine evidence. [asserted]
3. Convert relational failures into deterministic projection quarantine while retaining parser/schema failures in `events.Rejection`; keep replay moving and preserve every adverse count. [asserted]
4. Gate beta/routing input by exact estimand and authenticated status, then render the same quarantine, sampling and oracle facts in human and JSON forms. [asserted]
5. Rebuild twice from the same log and compare quarantine identities, beta fields and state digest. [asserted]

**Done:** Proxy values cannot reach `Beta.compute()` or a sizing consumer, invalid relational rows stay visible without bricking replay, and both output modes report the same adverse evidence. [asserted]

```powershell
python -m pytest tests/test_verdict_supply.py -q
```

**Commit:** `fix(beta): quarantine invalid verdict evidence`. [asserted]

## A01 - define the canonical effect contract

**Deliverable:** One canonical effect module and event contract represent the twelve exact effect classes, one secret-free manifest, write-ahead intent and non-forking receipt without performing an effect. [cited: ADR-0078; action-surface sections 3 and 5]

**Why:** An action taxonomy without an exact-set validator and a single manifest is documentation, not a chokepoint. [cited: working principle 3; ADR-0078]

**Depends on:** `F03`, `E01` by shared-path order. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/effects.py` (new)
- `src/consilient/events.py`
- `tests/test_effect_contract.py` (new)

**Interfaces:** `effects.EFFECT_CLASSES` is the closed twelve-value set; `EffectManifest` owns operation/work/attempt identity, exact effects, scope, operations, inventory/gate/authority/law snapshots, residuals and ceilings; `effect.intent` and `effect.receipt` bind that manifest digest and use opaque broker references or keyed commitments for private values. [cited: action-surface lines 78-137 and 224-239]

**Steps:**

1. Write exact-set and malformed-value tests plus manifest canonicalisation, secret/low-entropy rejection and intent/receipt discriminated-schema fixtures. [asserted]
2. Run the acceptance command and confirm the new contracts are absent. [asserted]
3. Add the smallest immutable data types/canonical digest helper in `effects.py` and register only `effect.intent`/`effect.receipt` validation in the sole writer. [asserted]
4. Add non-forking receipt-chain validation, including `unknown` followed by one monotonic `supersedes` resolution and refusal of conflicting heads. [asserted]
5. Replay fixtures and prove no manifest field, secret value or provider payload is duplicated into a second record shape. [asserted]

**Done:** Unknown/padded/case-varied effects fail, composites retain every applicable class, private values never enter the trajectory, and one operation has one replayable intent/receipt chain. [asserted]

```powershell
python -m pytest tests/test_effect_contract.py -q
```

**Commit:** `feat(effects): define canonical effect records`. [asserted]

## A02 - derive gated capability admission and escalation

**Deliverable:** The existing capability inventory derives one fail-closed admission class and one ADR-0075 disposition from actual manifest facts while all unauthenticated present capabilities remain visibly gated. [cited: ADR-0075; ADR-0078]

**Why:** Technical availability is not authority, and neither a gate pass nor caller-supplied `actor: principal` may expose a live handle. [cited: action-surface section 4; ADR-0078]

**Depends on:** `A01`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/effects.py`
- `src/consilient/events.py`
- `src/consilient/capabilities.py`
- `tests/test_effect_admission.py` (new)
- `tests/test_capabilities.py`

**Interfaces:** Inventory entries gain the exact `gate` object from action-surface section 4; `effects.derive_admission()` returns one of `observation`, `contained_execution`, `proof_operation`, `material_choice`, `recoverable_mutation`, `protected_covered`, `protected_uncovered` or `capability_gap`, plus the final execute/reshape/refuse/escalate disposition and reason. [cited: ADR-0079 lines 129-136]

**Steps:**

1. Add inventory fixtures for unavailable, unknown, present-but-gated, exact admitted, expired, scope-mismatched and malformed capability states. [asserted]
2. Add admission fixtures for the pure-observation predicate, missing inputs, composites, failed recovery, each protected class and the closed six-class escalation mapping. [asserted]
3. Run the acceptance command and confirm current exact-key capability parsing rejects the new gate shape. [measured] [asserted]
4. Extend the existing inventory parser and implement the pure derivation; do not add authentication, a principal path or a mutable permission cache. [asserted]
5. Prove an ordinary writer and same-OS dispatched actor cannot mint or widen authority, and that a project-gate change never alters capability admission. [asserted]

**Done:** Missing/malformed/stale authority produces `capability_gap` or refusal, exact authorised facts alone can produce an admitted disposition, and no handle is issued by this unit. [asserted]

```powershell
python -m pytest tests/test_effect_admission.py tests/test_capabilities.py -q
```

**Commit:** `feat(effects): derive gated effect admission`. [asserted]

## P01 - bind the durable pre-action decision record

**Deliverable:** The existing `decision.autonomous` event and protected proposal shape carry one exact pre-action planning/evidence contract, and the same dormant treatment predicate can refuse a dependent material-choice claim without that contract. [cited: ADR-0079; decision-protocol sections 5 through 7]

**Why:** A post-action rationale is only an audit row; ADR-0079 requires the choice to be durable before intent and reach. [cited: ADR-0079]

**Depends on:** `F03`, `A02`, foundation `T03`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `tests/test_decision_protocol.py` (new)
- `tests/test_work_items.py`

**Interfaces:** The common record requires stable decision/operation/work-item identity, Owner/actor, derived `record_level`, decision/reasoning/falsifier/reversal, real alternatives or `only_admissible.rule_refs`, exact `{event_id,event_kind,event_sha256}` evidence references, acceptance-contract digest and a discriminated protocol record; class-specific bindings contain expected digests but never a future result. [cited: decision-protocol lines 180-244] `work_items.decision_readiness()` is a pure EXP-106 treatment predicate over an accepted prefix, dependent item and expected decision digest; ordinary claim issuance does not call it before activation. [asserted]

**Steps:**

1. Write conditional-schema fixtures for every admission class, both record depths, alternatives versus `only_admissible`, valid/late/mismatched evidence references, supersession and protected proposal/authority separation. [asserted]
2. Run the acceptance command and confirm the existing syntactic decision validator accepts records that the new contract must refuse. [measured] [asserted]
3. Extend `decision.autonomous` rather than adding another decision kind, and reuse the same nested planning validator inside the existing escalation proposal. [asserted]
4. Enforce unique operation binding through the `F02` transaction, earlier exact references through `F03`, and the ADR-0079 order without copying receipt/outcome data backwards. [asserted]
5. Add the pure treatment predicate and fixtures proving an absent, late or digest-mismatched decision leaves a dependent material-choice item unready; do not wire that refusal into ordinary claim issuance before EXP-106. [cited: ADR-0079 Enforcement] [asserted]
6. Prove `principal_authority` classes cannot be autonomous and a proposal cannot satisfy its own authority requirement. [asserted]

**Done:** Absent, malformed, duplicate, reserved, late and hash-mismatched planning records refuse in the fake action and dormant work-readiness treatment paths; replay preserves superseded decisions and dissent while the ordinary product path remains unactivated. [asserted]

```powershell
python -m pytest tests/test_decision_protocol.py tests/test_work_items.py -k "decision or proposal or reference" -q
```

**Commit:** `feat(decisions): bind pre-action decision records`. [asserted]

## P02 - bind Better-Than-Best execution to the decision

**Deliverable:** A deterministic tri-state threshold selects the existing Better-Than-Best skill conservatively and makes its exact reconstructed assembly a required decision reference only when the protocol completes. [cited: ADR-0079; decision-protocol section 8]

**Why:** Code may enforce whether the procedure was bound, but must not reimplement its judgement or infer semantic completeness from condensed recall. [cited: decision-protocol lines 246-278]

**Depends on:** `P01`, foundation `C01/T01`, documentation `L02` and delivery-estimate `D01`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/instructions.py`
- `tests/test_instructions.py`

**Interfaces:** `instructions.protocol_threshold()` returns true/false/unknown for later reliance, complete same-question lookup and relative cost; `instructions.assemble()` produces the exact skill name/path/digest recorded by `instructions.assembled`; `instructions.reconstruct()` verifies the pinned body used by the decision. [asserted]

**Steps:**

1. Add fixtures for every true/false/unknown combination, incomplete index lookup, incomparable cost inputs, wrong task, late assembly, digest substitution and reconstructed-body mismatch. [asserted]
2. Run the acceptance command and confirm the existing selector lacks the three-condition binding. [asserted]
3. Implement the tri-state threshold: all true, or no false plus at least one unknown, selects the existing skill; any false records the reason and requires no completion artefacts. [cited: decision-protocol lines 253-274]
4. Bind the selected assembly and required bar/search/killing-check references without modifying the skill body or adding another instruction store. [asserted]
5. Reconstruct from the same tree/prefix and compare name, path, digest and body before accepting the protocol reference. [asserted]

**Done:** A firing threshold cannot validate without the earlier same-task assembly and artefacts, while a non-firing threshold cannot be forced to fabricate them. [asserted]

```powershell
python -m pytest tests/test_instructions.py -q
```

**Commit:** `feat(decisions): bind better-than-best execution`. [asserted]

## Q01 - freeze candidate exposure before verification

**Deliverable:** One independently selected review queue and shared verification-start boundary durably expose candidates before any component outcome and derive sampling status entirely from replay. [cited: ADR-0080; verdict-supply section 5]

**Why:** A caller-controlled sampling Boolean or queue chosen after verifier/consequence results cannot measure operational beta. [algebra] [cited: verdict-supply lines 174-208]

**Depends on:** `F03`, `E01`, `V01`, `P01` by shared `events.py` claim order. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/events.py`
- `src/consilient/projection.py`
- `src/consilient/beta.py`
- `src/consilient/verification.py` (new)
- `tests/test_review_queue.py` (new)
- `tests/test_v0_invariants.py`

**Interfaces:** `review.queue.opened` freezes `stream_cap=90`, `EXP105_prefix_n=30`, rejection target, population, verifier protocol/version/contract, start position, eligible-universe digest, deterministic order and first-90 selector; `candidate.exposed` is emitted by `verification.begin_attempt()` before components; `attempt.reviewed` and `review.presentation.frozen` schemas are reserved for `Q02`/trusted ingress. No unlisted `review.queue.frozen` alias is introduced. [cited: verdict-supply lines 181-208]

**Steps:**

1. Add queue/exposure fixtures for absent/late exposure, altered verifier values, incomplete outcomes, version drift, selector overflow, duplicate attempt and manually asserted sampling. [asserted]
2. Run the acceptance command and confirm there is currently no shared verification-start producer or replayable queue manifest. [measured]
3. Add the exact event validators and one `verification.begin_attempt()` front door that atomically appends exposure before returning a start token; it executes no verifier itself. [asserted]
4. Project the first matching exposure identities/order from the frozen manifest, pass that derived state through `beta.from_connection()`, and keep `sampling_unconditioned` false on any coverage gap; no caller Boolean survives. [asserted]
5. Add the executable-tree source scan which fails if a component-outcome producer can run without the start token; mutate every verifier/consequence/critic value and prove queue membership/order is unchanged. [asserted]

**Done:** No component outcome can precede exposure, callers cannot set sampling status, and projection deletion/replay reproduces the same queue and eligible-universe digest. [asserted]

```powershell
python -m pytest tests/test_review_queue.py tests/test_v0_invariants.py -k "review_queue or candidate_exposed or verification_start" -q
```

**Commit:** `feat(review): freeze candidate exposure queues`. [asserted]

## Q02 - prepare a blinded local review card

**Deliverable:** A local read-only card freezes Contract, Artefact, Question and hidden Reveal from the selected queue and complete component roll-up without accepting or authenticating an answer. [cited: ADR-0080; verdict-supply sections 5 and 8]

**Why:** The machine can remove preparation work now, but a phone or write-capable surface without authenticated first-party presence would forge the very oracle being measured. [cited: verdict-supply lines 210-283]

**Depends on:** `Q01`, `E01`, `V01`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/projection.py`
- `src/consilient/dashboard.py`
- `scripts/verdict.py`
- `tests/test_review_card.py` (new)

**Interfaces:** The projection joins one selected exposure to the exact protocol component key-set and candidate-time contract; `review.presentation.frozen` binds contract, artefact, component-rollup and presentation digests; the local renderer displays Contract/Artefact/Question and keeps Reveal sealed. [cited: verdict-supply lines 201-229]

**Steps:**

1. Add card fixtures for complete accept/reject component sets, missing/error components, stale contract, wrong artefact, changed render, `Unclear`, and attempts to pass a verdict through local card arguments. [asserted]
2. Run the acceptance command and confirm the existing script can manually record a verdict but cannot prepare the frozen blinded card. [measured]
3. Derive the composite Boolean only from the complete frozen component key-set, store its roll-up digest, and treat missing/error components as terminal preparation states rather than guessed values. [asserted]
4. Add a local preparation/render mode to the existing `scripts/verdict.py`; add no `consil` command, network listener, credential, phone route or verdict writer. [asserted]
5. Prove the pre-answer rendering contains no verifier/consequence outcome, the reveal digest is bound, and no `human_verdict` or beta row is appended. [asserted]

**Done:** A person can inspect one bounded prepared question locally, but the surface is demonstrably read-only and contributes zero authenticated verdicts. [asserted]

```powershell
python -m pytest tests/test_review_card.py -q
```

**Commit:** `feat(review): prepare blinded local verdict cards`. [asserted]

## G01 - project structural acquisition anchors

**Deliverable:** One replay-only resolver classifies a decision's immutable evidence references as `converged`, `insufficient`, `disagreed` or `unmeasured` and names the exact qualifying pair or failure. [cited: ADR-0081; consilience-gate sections 3, 4 and 7]

**Why:** Provenance, evidence class and structural acquisition difference are distinct; missing metadata must not become an empty root set or an inferred independent channel. [cited: ADR-0081]

**Depends on:** `F03`, `E01`, `P01`, `Q02` by shared projection-path order. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/events.py`
- `src/consilient/projection.py`
- `tests/test_consilience_gate.py` (new)

**Interfaces:** Source-kind contracts own one of `artefact_execution`, `browser_observation`, `primary_source_retrieval` or `novel_corpus_observation`, plus canonical observation anchor, complete derivation roots, sealed conclusion/alternative and acceptance-contract digest; `projection.consilience_status(decision_id)` returns status, qualifying refs, all non-qualifying refs and reasons. [cited: consilience-gate lines 51-110]

**Steps:**

1. Add fixtures for each channel, same/different anchors, shared/unknown roots, opposing stances, late/malformed refs, duplicate verification keys, timeouts and a different-model reading of the same source. [asserted]
2. Run the acceptance command and confirm the current source kinds do not carry enough validated channel/anchor/root data for ADR-0081. [measured]
3. Extend the existing source-kind validators with their channel-specific metadata; do not add a `consilience.outcome` event or fusion table. [asserted]
4. Resolve only unique valid earlier id/kind/hash references, refuse repeated verification identities/correlation keys, and require same conclusion/contract/alternative with distinct channels, anchors and known-disjoint roots. [cited: consilience-gate lines 65-85]
5. Project the four statuses, preserving every minority, timeout, refusal, malformed and unmeasured reading after deletion/replay. [asserted]

**Done:** One qualifying existential pair converges, opposed qualifying anchors disagree, missing/echo evidence cannot receive structural credit, and every raw observation remains visible. [asserted]

```powershell
python -m pytest tests/test_consilience_gate.py -k "anchor or status or duplicate" -q
```

**Commit:** `feat(evidence): project structural acquisition anchors`. [asserted]

## A03 - evaluate an isolated recovery proof

**Deliverable:** One scratch-only proof protocol evaluates forward state, inverse state, enclosing-scope equality, escaped effects and residuals against a fake/inert broker and emits a bound proof result for a later live-operation decision. [cited: ADR-0075; ADR-0079]

**Why:** A model-supplied inverse or successful exit code is not mechanical reversibility, while running against the live target before admission would invert the required order. [cited: ADR-0075 sections Mechanical reversibility and Reversal record]

**Depends on:** `A02`, `P01`, `P02`, foundation `F02/F03`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/effects.py`
- `scripts/dispatch.py`
- `tests/test_recovery_proof.py` (new)

**Interfaces:** `effects.RecoveryProof` binds proof operation, manifest, start state, sandbox/verifier policy, observer log, forward/inverse/readback results and residuals; the outer runner receives only a new scratch root and fake verifier log in this unit. [cited: ADR-0079 lines 80-85]

**Steps:**

1. Add inert fixtures for exact restoration, wrong preimage, incomplete scope, failed inverse, undeclared out-of-root/network/credential attempt, escaped child, changed verifier policy and residual-only process execution. [asserted]
2. Run the acceptance command and confirm current reversal validation proves syntax only. [measured: ADR-0075]
3. Implement the proof-result contract and fake scratch runner using the existing outer dispatch boundary; do not expose the real target, network, credentials, spend or provider handles. [asserted]
4. Require the proof operation's own minimal decision/intent identities and bind the completed proof digest to the separate proposed live operation. [cited: ADR-0079]
5. Compare canonical start/end/enclosing-scope artefacts and prove one lying-adapter fixture is independently refused despite a passing declared inverse. [asserted]

**Done:** Only exact scratch restoration with no escaped protected effect produces a reusable proof digest; every other case is a visible capability gap or refusal. [asserted]

```powershell
python -m pytest tests/test_recovery_proof.py -q
```

**Commit:** `feat(effects): verify recovery in isolation`. [asserted]

## A04 - admit one fake effect atomically

**Deliverable:** The single effect boundary atomically consumes one valid pre-action chain, durably appends intent, exposes one fake single-use handle, then appends a non-forking receipt and existing outcome. [cited: ADR-0078; ADR-0079]

**Why:** Separate validation, append and handle issuance allow two callers or a crash window to reach the effect with missing or duplicated evidence. [cited: ADR-0079 section Enforcement]

**Depends on:** `A03`, `P01`, `P02`, foundation `F02/F03`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/effects.py`
- `scripts/dispatch.py`
- `tests/test_action_boundary.py` (new)
- `tests/test_v0_invariants.py`

**Interfaces:** `effects.admit_effect()` is the canonical pure manifest/admission protocol. It consumes the actual manifest and either the observation identity, autonomous decision, or protected proposal plus first-party authority chain, then returns one opaque single-use admission for an outer host after durable intent. It imports or calls no raw reach. Existing dispatch/connectors are the only outer reach hosts and must consume this protocol; none may validate and reach independently. [asserted]

**Steps:**

1. Add fake-sink fixtures for absent, malformed, duplicate, mismatched and late decisions; observation predicate violations; stale authority; prior intent; concurrent consumers; and crash cuts before/after decision, intent, fake reach, receipt and acknowledgement. [asserted]
2. Run the acceptance command and confirm no current boundary orders and consumes the complete chain. [measured]
3. Use the `F02` locked transition to reserve operation identity, validate the complete discriminated chain, append/fsync the first intent and issue one opaque single-use admission. [asserted]
4. Invoke the registered fake adapter only in the existing outer dispatch host, then append refused/succeeded/failed/unknown receipt observations and the existing linked outcome without adding `decision.outcome` or provider state authority. [asserted]
5. Add a tracked-source ratchet proving every raw reach host consumes the canonical protocol and `effects.py` itself contains no reach; retry every crash cut and prove exact retries return the committed receipt, conflicts refuse, non-idempotent effects are never blindly repeated and two contenders invoke the fake sink once. [asserted]

**Done:** The artefact order is decision/proposal-authority, intent, one fake reach, receipt, outcome; any missing/different order refuses before fake reach. [cited: ADR-0079] [asserted]

```powershell
python -m pytest tests/test_action_boundary.py -q
```

**Commit:** `feat(effects): admit fake effects atomically`. [asserted]

## G02 - evaluate consilience in report-only admission

**Deliverable:** The fake action boundary computes and reports whether consilience is required and the `G01` status, but does not yet refuse a single-anchor action. [cited: ADR-0081; EXP-109 flag-only control]

**Why:** EXP-109 requires a flag-only incumbent, and activating an unmeasured refusal rule before that comparison would treat the hypothesis as a result. [cited: experiment register EXP-109]

**Depends on:** `G01`, `A04`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/effects.py`
- `tests/test_consilience_gate.py`

**Interfaces:** `effects.evaluate_consilience()` derives `requires_consilience` from `record_level == full` or `protected_covered/protected_uncovered`, consumes the `G01` report and returns a report-only admission annotation; it cannot open a boundary refused by recovery, authority, beta, budget, law or capability checks. [cited: consilience-gate sections 5 and 6]

**Steps:**

1. Add fixtures for every admission class/record level, one valid anchor, two label/family variants, a shared root, missing metadata, a qualifying pair and disagreement. [asserted]
2. Run the acceptance command and confirm the fake boundary currently has no consilience evaluation. [measured]
3. Add the exact consequence trigger after manifest/disposition/record-depth derivation and before fake reach, consuming the projection report without copying evidence metadata. [asserted]
4. Keep the mode report-only: record/return `required`, status, pair/refusal reason and threshold facts while leaving the fake control path unchanged. [asserted]
5. Prove a minimal recovery-proved action proceeds with one anchor, a high-consequence single anchor is visibly flagged, and no other failed boundary becomes admitted. [asserted]

**Done:** The EXP-109 control is reconstructible and exposes every single-anchor/disagreement case without claiming or activating a safety gate. [asserted]

```powershell
python -m pytest tests/test_consilience_gate.py -k "required or report_only or minimal" -q
```

**Commit:** `feat(consilience): report high-consequence anchor gaps`. [asserted]

## A05 - migrate outbound messaging to the boundary

**Deliverable:** The existing outbound connector derives all applicable effects and can reach only its fake provider through `A04`; its live transport remains gated. [cited: ADR-0078]

**Why:** Current outbound paths can send before their event append and embed private recipient/content data in the trajectory. [measured: ADR-0078 Context and Evidence]

**Depends on:** `A04`, `G02`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient_connectors/outbound.py`
- `tests/test_outbound.py`

**Interfaces:** Outbound manifest recomputation declares at least `message.send` plus `network.call` for remote transport and any substantive child class; provider recipients/content/idempotency remain opaque broker references; the connector consumes only `effects.admit_effect()`. [cited: action-surface sections 3 and 5]

**Steps:**

1. Add fake SMTP/Twilio fixtures for refusal, success, failure, timeout/unknown, exact retry, private recipient/content leakage and undeclared effect classes. [asserted]
2. Run the acceptance command and capture the existing send-before-record behaviour with the fake provider. [measured]
3. Recompute the manifest from the actual invocation and route the fake provider call through the frozen `A04` interface; remove no unrelated connector behaviour. [asserted]
4. Replace raw private trajectory values with broker references/commitments and bind provider observations into the receipt chain. [asserted]
5. Prove refusal exposes no fake handle, intent precedes invocation and a crash/retry cannot duplicate the fake message. [asserted]

**Done:** Every outbound attempt has the canonical pre-action chain and no live provider is reachable under current gated authority. [asserted]

```powershell
python -m pytest tests/test_outbound.py -q
```

**Commit:** `feat(outbound): route sends through effect admission`. [asserted]

## A06 - migrate computer use to the boundary

**Deliverable:** The existing computer-use connector derives browser/message/network effects and can execute only fake browser operations through `A04`; live browser reach remains gated. [cited: ADR-0078]

**Why:** Browser navigate/fill/click paths can precede event append, and raw browser reach is wildcard-effect reach until an outer sandbox proves exclusions. [measured: ADR-0078; action-surface section 3]

**Depends on:** `A04`, `G02`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient_connectors/computer_use.py`
- `tests/test_computer_use.py`

**Interfaces:** The connector recomputes a manifest per actual operation, includes `network.call`, `message.send` or substantive mutation classes where applicable, stores screenshots/DOM/accessibility/console/network observations by immutable digest/reference, and consumes only `effects.admit_effect()`. [cited: action-surface; consilience-gate section 4]

**Steps:**

1. Add fake-browser fixtures for read-only observation, navigation, fill/click mutation, local human-visible render, undeclared child request, refusal, crash and exact retry. [asserted]
2. Run the acceptance command and capture the existing act-before-append path using only the fake browser. [measured]
3. Derive all applicable classes from the actual browser operation and route fake reach through the frozen boundary without treating a browser label as containment. [asserted]
4. Bind retained browser observations to version, artefact, anchor and derivation metadata required by `G01`. [asserted]
5. Prove an undeclared fake child request is denied independently of the manifest and no live browser/provider handle is exposed. [asserted]

**Done:** Browser observations can become structural evidence, but every mutable or human-facing operation remains fake/gated and ordered through the one boundary. [asserted]

```powershell
python -m pytest tests/test_computer_use.py -q
```

**Commit:** `feat(browser): route actions through effect admission`. [asserted]

## A07 - prove containment classification without live activation

**Deliverable:** One executable Docker containment/bypass evaluator proves that a test-profile child lacks every unmanifested live capability, or classifies that proposed launch as a capability gap without granting a new action-boundary handle. [cited: ADR-0079; action-surface section 9]

**Why:** Gating `run_harness()` alone records process launch but does not contain child filesystem, network, credential, provider or descendant effects. [measured: ADR-0079]

**Depends on:** `A04`, `A05`, `A06`. [asserted]

**Claim exactly:** [asserted]

- `scripts/dispatch.py`
- `.github/scripts/check_effect_paths.py` (new)
- `tests/test_dispatch.py`
- `tests/test_v0_invariants.py`

**Interfaces:** Docker Desktop 4.80.0 / Engine 29.6.1 is the first measured local primitive on this machine. [measured: `docker version`, 2026-08-22] The frozen profile uses the already-local `python@sha256:eb43ff125d8d58d7449dcba7d336c23bcac412f526d861db493b9994d8010280`, `--network none`, read-only root, non-root UID/GID, `--cap-drop ALL`, `no-new-privileges`, bounded PIDs/CPU/memory/logs, a private bounded `/tmp`, and only the exact claimed scratch bind writable. The outer launch check records Docker/OS/image/profile digests and returns a report covering mutable roots, network, environment/credential canaries, provider sockets, descendants and residuals. Only a complete passing report may classify `contained_execution`; Claude/Codex/Cursor/Grok provider launches remain `uncontained` until their necessary brokered network and credentials can satisfy the same proof. [asserted]

**Steps:**

1. Add runtime probes which attempt root/out-of-claim writes, network/DNS connection, environment/credential-canary read, Docker/provider socket access, detached descendant and human-facing render under the frozen Docker profile. [asserted]
2. Add the complete tracked-executable/dependency source scan for raw filesystem/process/network/message/provider/credential/money sinks outside the one boundary allowlist. [asserted]
3. Run the acceptance command without pulling an image; prove every escape against the local digest is denied and confirm the current permission-bypass provider profile is classified uncontained rather than mislabelled contained. [asserted]
4. Add the evaluator beside the existing dispatch launch slice and exercise it only with the local fixture launcher in this plan; do not turn it into the default provider `run_harness()` decision gate before EXP-106. [asserted]
5. Prove process-tree termination and residual reporting separately from restoration, and prove every admitted child effect requires its own operation chain. [asserted]

**Done:** Every escape probe is denied under the contained test profile, the current ambient profile returns an uncontained/capability-gap assessment, and the source scan finds no raw sink falsely claimed to be mediated. Existing supervised dispatch remains explicitly outside the new safety claim until a later authorised activation unit. [asserted]

```powershell
python -m pytest tests/test_dispatch.py tests/test_v0_invariants.py -k "containment or effect_path or run_harness_refuses" -q
```

**Commit:** `feat(dispatch): refuse uncontained harness reach`. [asserted]

## A08 - project complete action chains

**Deliverable:** The existing dashboard exposes one replay-derived operation chain from decision/proposal through intent, receipt head and outcome, including refusal, failure, unknown, residual and child-effect states. [cited: ADR-0078; ADR-0079]

**Why:** An acknowledged intent without a receipt is unresolved rather than not-run, and hiding adverse states would make the operator view contradict the record. [cited: action-surface section 5]

**Depends on:** `A05`, `A06`, `G01`, `G02`, `Q02`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/projection.py`
- `src/consilient/dashboard.py`
- `tests/test_action_projection.py` (new)

**Interfaces:** The projection returns stable operation/decision/work-item identities, admission/record level, manifest/effect classes, current non-forking receipt head, child operations, residuals, outcome and report-only consilience status; the dashboard renders these values without becoming authority. [asserted]

**Steps:**

1. Add replay fixtures for refused, succeeded, failed, unresolved unknown, late resolution, conflicting fork, missing receipt, child effect and projection deletion. [asserted]
2. Run the acceptance command and confirm the existing dashboard cannot reconstruct the complete action chain. [measured]
3. Build the disposable join from canonical generic events; do not add a mutable action counter, provider-state cache or second effect ledger. [asserted]
4. Render exact adverse counts, current receipt head, missingness, residuals and consilience status, with `unknown` visually distinct from success/failure. [asserted]
5. Delete the SQLite projection, replay the log and compare the complete payload and rendered-state digest. [asserted]

**Done:** The operator can locate every unresolved or adverse action state and the view reproduces exactly from the sole trajectory. [asserted]

```powershell
python -m pytest tests/test_action_projection.py -q
```

**Commit:** `feat(effects): project complete action chains`. [asserted]

## A09 - ratchet avoidable escalation friction

**Deliverable:** The existing projection/dashboard computes the complete non-overlapping 30-attempt autonomy-friction window, exposes every numerator/denominator/reason and ratchets the next avoidable-refusal ceiling without changing protected-action authority. [cited: ADR-0075; autonomy-and-friction section 7]

**Why:** Refusing everything is superficially safe but makes the principal the routine control plane; unavailable or selectively omitted escalation outcomes would hide that failure. [cited: ADR-0075]

**Depends on:** `A02`, `Q02`, `A08`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/projection.py`
- `src/consilient/dashboard.py`
- `tests/test_autonomy_friction.py` (new)

**Interfaces:** `avoidable_escalation_ratio = refused_avoidable_attempts / all_escalation_attempts`. The denominator includes delivered, refused, timed-out and unanswered escalation attempts; zero denominator is `unavailable`, never zero. Avoidable means a reason outside ADR-0075's closed six classes, a duplicate open request, an already matching standing authority, or an available verified local/reversible surrogate. Non-overlapping 30-attempt windows retain all six class counts and zeroes. The next ceiling is the lower of the prior ceiling and current avoidable count; a breach is visible and cannot raise the ceiling. [asserted]

**Steps:**

1. Add fixed windows containing each terminal status, all six protected classes, duplicate requests, standing authority, reversible surrogates, missing reason and zero attempts. [asserted]
2. Derive counts only from the trajectory prefix and the closed classification contract; no mutable counter/table is introduced. [asserted]
3. Render numerator, denominator, ratio/unavailable, every reason/class count, ceiling and breach with explicit zeroes. [asserted]
4. Delete and rebuild the projection, then prove the same windows and ratchet; changing an outcome from refusal to timeout must remain in the denominator. [asserted]

**Done:** A fixture cannot improve the ratio by omitting, timing out or relabelling a request, and the ratchet never loosens automatically. [asserted]

```powershell
python -m pytest tests/test_autonomy_friction.py tests/test_action_projection.py -q
```

**Commit:** `feat(dashboard): expose and ratchet escalation friction`. [asserted]

## G03A - define one bounded missing-anchor acquisition

**Deliverable:** An insufficient high-consequence decision deterministically selects at most one useful different-class channel and opens one bounded native child item whose contract withholds peer outcomes. [cited: ADR-0081; consilience-gate section 8]

**Why:** A refusal-only two-anchor rule creates avoidable denial of service, while another model reading the same facts or a human confirmation supplies no admissible objective anchor. [cited: ADR-0081 Evidence against]

**Depends on:** `G02`, foundation `T01/T02`, memory/capability `M05`, and the accepted existing capability/work-item/coordination APIs. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/capabilities.py`
- `src/consilient/work_items.py`
- `src/consilient/instructions.py`
- `tests/test_consilience_acquisition_contract.py` (new)

**Interfaces:** The child item binds frozen conclusion, acceptance-contract digest, selected channel, anchor contract, budget, expiry and terminal stopping reasons; instruction assembly withholds peer outcomes and gives the child no parent-effect handle. [cited: consilience-gate lines 183-219]

**Steps:**

1. Add contract fixtures for each countable channel, no useful available channel, budget/expiry exhaustion and attempts to use family fan-out or principal confirmation. [asserted]
2. Run the acceptance command and confirm no current path opens a channel-bound acquisition item. [measured]
3. Select the cheapest available channel whose possible result can change the action, open/claim one child item and assemble bounded instructions without peer outcomes. [asserted]
4. Prove no branch rewrites the earlier decision, silently downgrades full to minimal, invokes generic fan-out, asks a human for evidence or creates a second child after its stopping condition. [asserted]

**Done:** One insufficiency either creates exactly one claimable child contract or terminates with an exact visible no-channel/budget/expiry reason. [asserted]

```powershell
python -m pytest tests/test_consilience_acquisition_contract.py -q
```

**Commit:** `feat(consilience): contract a missing anchor`. [asserted]

## G03B - execute and re-enter fake admission

**Deliverable:** The existing coordination/dispatch path executes one G03A child inside A07 containment, seals its countable source-kind observation, appends a superseding decision and re-enters the same fake boundary. [cited: ADR-0081; consilience-gate section 8]

**Why:** Contract selection and outer execution claim different shared paths and fail independently; joining them would recreate the oversized dispatches this plan is meant to prevent. [measured: dispatch brief] [asserted]

**Depends on:** `G03A`, `A07`. [asserted]

**Claim exactly:** [asserted]

- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_consilience_acquisition.py` (new)

**Interfaces:** Dispatch accepts only the contracted observation/contained-execution capability; the sealed source event closes the child; a new decision consumes its exact reference and reuses `effects.evaluate_consilience()`/`admit_effect()`. [asserted]

**Steps:**

1. Add fake contained fixtures for zero-value observation, timeout/refusal/error, qualifying convergence, disagreement and crash/retry around source sealing and re-entry. [asserted]
2. Dispatch only the selected capability under the live claim/epoch and A07 profile; append every adverse terminal result. [asserted]
3. Close the child, append a superseding decision with the new exact reference and re-enter the fake boundary once. [asserted]
4. Stop on convergence, disagreement or terminal insufficiency and prove neither the earlier decision nor the parent fake receipt is rewritten. [asserted]

**Done:** One bounded acquisition either supplies a qualifying pair and re-enters fake admission once or terminates with an exact visible insufficiency/disagreement reason. [asserted]

```powershell
python -m pytest tests/test_consilience_acquisition.py tests/test_consilience_acquisition_contract.py -q
```

**Commit:** `feat(consilience): execute a missing-anchor acquisition`. [asserted]

## Recommended execution and visible value

1. Finish `R01`, then accept foundation `F01-F03`; arithmetic can land first but remains unwired. [asserted]
2. Secure the existing partial evidence work with `E01`, then run `V01` beside the serial action lane `A01 -> A02 -> P01 -> P02`. [asserted]
3. Run `Q01 -> Q02`; `Q02` is the first new human-visible product value because it prepares one bounded local question without making the principal a build dependency. [asserted]
4. Run `G01` and `A03 -> A04 -> G02`; this yields replayable decision/anchor/action reports while every effect is fake. [asserted]
5. Run `A05` and `A06` in parallel, then `A07`; a host that cannot prove containment completes honestly as refused rather than blocking earlier local/reporting value. [asserted]
6. Run `A08 -> A09` for complete action accountability and visible autonomy friction, then `G03A -> G03B` for autonomous missing-anchor acquisition. [asserted]

`V01` is the earliest operator-visible correction because beta output stops hiding quarantine and oracle limitations. [asserted] `Q02` is the earliest new interaction surface. [asserted] `A08` is the earliest complete action-accountability surface. [asserted]

Action-first loses because the writer, evidence identity and containment are not yet trustworthy. [measured] UI-first loses because it would render assertions that queue/action projections cannot reconstruct. [asserted] Human-ingress-first loses because it makes the principal the boot dependency while doing nothing to contain same-OS child reach. [asserted]

## Explicit deferrals

- Hard decision-gate activation is deferred until EXP-106 confirms its frozen stopping rule; an adverse or equivalent result leaves `P01/P02` as optional audit/skill structure and removes the live refusal edge. [cited: ADR-0079; EXP-106]
- Hard consilience-gate activation is deferred until EXP-109 confirms fewer bad actuations without merely increasing refusal; until then `G02` is report-only and `G03A/G03B` are exercised only with fake/inert admission. [cited: ADR-0081; EXP-109]
- Live process, filesystem, network, message, publication, spend, credential, provider and physical actuation are deferred beyond this plan even if `A07` passes; activation also needs the applicable gate, beta, budget, law and exact authority conditions. [cited: ADR-0078; ADR-0081]
- Authenticated phone/WebAuthn verdict writes, enrolment/recovery, HTTPS origin and an approved verifier dependency or OS broker are deferred to the trusted-human-ingress stream. `Q02` remains local/read-only. [cited: verdict-supply lines 231-283]
- Tier-1 consequence labels and every proxy estimand remain research/preparation evidence; neither may enter human beta, routing or candidate sizing. [cited: ADR-0080]
- Tier-1 collector execution and EXP-105 are deferred: no exact EXP-105 heading exists in the experiment register at this plan's review, and authenticated queue/verdict prerequisites are absent. `Q01/Q02` build preparation only and do not alias another experiment number. [measured: exact experiment-register heading search, 2026-08-22] [asserted]
- EXP-80 squad-specific manifests, isolation, disagreement UI and likelihood-fusion machinery are deferred; one Owner with all ordinary tools remains the control. [cited: ADR-0067; ADR-0077]
- An iid candidate-exposure exception, automatic routing and any change to `routing_orchestration_enabled` are deferred; `R01` remains the unwired robust ceiling. [cited: ADR-0077]
- Another queue, coordinator, router, decision kind, evidence/fusion table, effect/provider-state store, principal path or CLI command is explicitly not built. [cited: ADR-0077 through ADR-0081]

## Stream completion check

No unit authorises live action. [asserted] The stream is implementation-complete only when every focused command passes, replay after projection deletion reproduces all affected views, the complete suite has zero failures, strict mypy passes and Ruff passes while the routing flag and six-command invariants remain unchanged. [asserted]

```powershell
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m mypy --strict src/consilient
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m ruff check .
```

Passing those checks establishes only the implemented schemas, fake/inert boundary, containment fixture and replayed reports. It does not establish low beta, authenticated principal authorship, legal correctness, universal evidence independence or safe live actuation. [asserted]
