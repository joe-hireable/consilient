# Trusted human ingress and dormant self-improvement implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` and complete one unit at a time. Do not start a dependent unit until its predecessor is accepted and committed.

**Goal:** Add one authenticated human-action receipt to every protected existing path, then build self-improvement as a dormant, replayable path that cannot activate without all named evidence. [asserted]

**Architecture:** The append-only trajectory remains the sole authority record and `events.py` its sole writer. One host-only ingress mints one receipt envelope; one central validator consumes it under closed action profiles. Existing consent, verdict, intervention, capability, expertise, model and promotion paths reuse that validator. Self-improvement remains in `promote.py`/`promote_loop.py`; there is no second broker, journal, scheduler, orchestrator or `consil` command. [cited: ADR-0075, ADR-0076, ADR-0078, ADR-0080]

**Tech stack:** Python 3.13 standard-library product code, the future principal-approved WebAuthn verifier or OS broker, pytest, mypy and Ruff. This plan neither chooses nor adds that dependency. [measured: repository constraints] [asserted]

**Specifications:** autonomy-and-friction, self-improvement, task-management and verdict-supply; ADR-0075, ADR-0076, ADR-0078, ADR-0079 and ADR-0080. [measured]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after EXP-104 is registered/reported, A07 changes status, or the trusted-ingress backend/origin decision changes. [asserted]

**Falsifier:** Stop and amend this plan if one centrally consumed receipt cannot bind every listed protected action without exposing its issuer to a child harness, or if any transition can make candidate bytes active while registered EXP-104, trusted ingress, A07, the sealed instrument, promoter beta or downstream evidence is absent. [asserted]

## Boundaries and shared contract

- H01-H03 are a side branch. Durable tasks, local delivery, recall, decision/consilience reports, fake effects, read-only observability and inferred expertise proposals do not depend on trusted ingress. [asserted]
- H01 is blocked until the principal approves an audited WebAuthn/COSE dependency or an OS-isolated verifier broker and configures the private HTTPS origin, RP ID, allowed origin, network scope and TLS/key arrangement. [cited: verdict-supply section 4]
- H01 is also blocked until A07 proves child harnesses and direct wrappers cannot invoke the issuer, obtain authentication material or write its output. A caller-supplied `actor`, `principal` or `via` is not authentication. [cited: ADR-0075; verdict-supply section 4]
- No unit adds a seventh `consil` command. H01 is import-only; H02/H03 extend existing writers. [asserted]
- Historical unauthenticated human rows remain historical/unmeasured. Replay never upgrades them. [cited: ADR-0072, ADR-0080]
- S01-S03 may land as refusal, quarantine, sealed evaluation and owner-inspection machinery. S04-S06 remain unreachable until every conjunct is current; no unit changes Gate A, Gate B or `routing_orchestration_enabled=false`. [cited: ADR-0076]
- EXP-104 has no register heading. Its separately authorised research amendment is outside these claim sets, and no other experiment may be aliased to it. [measured]

`human_action_receipt.v1` binds `receipt_id`, `principal_id`, `action`, `instance_id`, `workspace_root_sha256`, protocol version, canonical bindings, issuer/version, issue/expiry times, single-use nonce, challenge ID/digest, ceremony digest, expected origin/RP ID, credential-ID digest, signature-counter result and `user_verified=true`. No key, bearer credential, biometric, secret or hidden instrument item enters the repository or trajectory. [cited: verdict-supply section 4] [asserted]

The central profile catalogue is closed and extended only through H02's validator/test lane: [asserted]

| Action profile | Exact binding family |
|---|---|
| `consent.grant`, `consent.withdraw` | purpose, use/retention reference, principal and exact disposition [asserted] |
| `attempt.verdict`, `attempt.verdict.correction` | queue/protocol/attempt, artefact, candidate-time contract, verifier/presentation, answer and prior verdict when correcting [cited: verdict-supply] |
| `promote.approve`, `promote.refuse` | proposal, experiment, impact contract, candidate/parent/instrument digests, expiry and disposition [cited: self-improvement] |
| `intervention.stop`, `intervention.redirect`, `intervention.add_evidence`, `owner.transfer`, `owner.return` | work item/run/epoch, correction or evidence digest, safe boundary, source/target owner and expiry [cited: ADR-0083] |
| `capability.grant`, `capability.credential_use` | manifest/version, effect scope, destination, broker reference, budget and expiry; never credential bytes [cited: ADR-0078, ADR-0084] |
| `expertise.authorise`, `expertise.activate`, `expertise.assign` | proposal/purpose/postcondition, source/privacy boundary, bundle/evaluation digest, task/destination and expiry [cited: ADR-0086] |
| `training.data_use`, `model.route.approve` | source/owner/purpose/retention/sharing/candidate run, or exact model/comparator/bank/instrument/result/rollback manifest [cited: ADR-0085] |

An unused matching receipt and protected event are one compare-and-append transaction. Identical retry returns the committed references; conflicting retry, expiry, replay, partial binding or cross-action substitution refuses. Profiles grant only their named action: acquisition is not activation, activation is not assignment, and historical approval is not standing authority. [asserted]

The promotion predicate is conjunctive: registered EXP-104 confirms; an unused exact H03 approval exists; A07 is current; instrument/hold-outs are sealed; scratch forward/reverse equality passes; `PromoterBetaReceipt` has at least 30 independently human-rejected conditionals and a one-sided 95% upper bound below 0.20; downstream beta and alpha each have at least 30 applicable conditionals and one-sided 95% harm upper bounds no greater than 0.05; the registered joint outcome improves; and no other candidate is activating, observing or rolling back. Missing or mismatched evidence leaves the parent active and records refusal/quarantine. [cited: ADR-0076; self-improvement sections 3-6] [algebra]

## Dependency graph and claim lanes

```text
ordinary product spine ------------------------------------------> useful local product
                              (no H/S dependency)

F03 -> S01 -> S02 -> S03
  \
   + A07 + approved verifier/origin -> H01 -> H02 -> H03
                                                    |      |
registered+confirmed EXP-104 + all evidence + S02/S03      |
                                                    v      |
                                                   S04 <---+
                                                    |
                                                   S05 -> S06
```

Edges are accepted domain prerequisites. Global mutable paths add serial lane edges without creating false domain dependencies: `events.py` is `F03 -> S01 -> H01 -> H02 -> S05 -> S06`; `promote.py` is `S01 -> S02 -> S04 -> S05 -> S06`; `promote_loop.py` is `S02 -> H03 -> S05 -> S06`. [asserted]

## H01 — shared trusted human ingress

**Deliverable:** One host-only ingress prepares a digest-bound challenge and, only after the approved verifier establishes origin/RP ID, signature, credential, replay policy and user verification, durably mints `human_action_receipt.v1`; otherwise it mints nothing. [cited: verdict-supply section 4]

**Depends on:** F03, accepted A07, one principal-approved verifier/broker and principal-approved private HTTPS configuration. It does **not** depend on promotion. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `scripts/human_action_broker.py` (new)
- `tests/test_human_action_ingress.py` (new)

**Steps:**

1. Refuse to begin until A07 and the verifier/origin decision are bound to the work item. [asserted]
2. Test valid UV, wrong origin/RP ID, absent UV, altered binding, expiry, replay, conflicting retry and child-harness invocation. [asserted]
3. Add challenge/receipt schemas and atomic challenge/nonce transition to the existing writer. [asserted]
4. Implement only the approved import-only host adapter; expose no CLI parser or candidate manifest capability. [asserted]

**Done:** One challenge produces at most one exact receipt and a child process cannot invoke or mint it. [asserted]

```powershell
python -m pytest tests/test_human_action_ingress.py -q
```

**Commit:** `feat(authority): add shared trusted human ingress`. [asserted]

## H02 — central profiles plus consent and verdict integration

**Deliverable:** One central validator enforces the closed profile catalogue, while existing consent and verdict/correction writers consume the same receipt ID atomically and reject every prompt answer or actor string as authority. [cited: ADR-0075, ADR-0080]

**Depends on:** H01 and Q01's frozen review-queue contract. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `scripts/consent.py`
- `scripts/verdict.py`
- `tests/test_human_action_receipts.py` (new)

**Steps:**

1. Test every closed profile's required bindings, both consent dispositions, verdict/correction, cross-action substitution, replay and append-fault retry. [asserted]
2. Add one central profile validator/nonce consumer and preserve legacy rows as unauthenticated history. [asserted]
3. Thread `receipt_id` through existing consent/verdict functions and parsers; `--principal` or local prompt alone can no longer author a protected event. [asserted]
4. Replay from an empty projection and compare protected events and consumed nonces. [asserted]

**Done:** Consent/verdict work once through the shared envelope; every downstream profile can be validated centrally but authorises nothing until its owning unit consumes it. [asserted]

```powershell
python -m pytest tests/test_human_action_receipts.py -q
```

**Commit:** `feat(authority): validate protected action receipts`. [asserted]

## H03 — promotion receipt integration

**Deliverable:** Existing promotion approve/refuse consumes the same central receipt against the exact S03 proposal card; it authenticates disposition only and cannot activate bytes. [cited: ADR-0076]

**Depends on:** H02 and S03. [asserted]

**Claim exactly:**

- `scripts/promote_loop.py`
- `tests/test_promotion_authority.py` (new)

**Steps:**

1. Test approve/refuse, card/proposal mutation, expiry, cross-profile substitution, replay and identical retry. [asserted]
2. Thread `receipt_id` through existing promotion disposition and consume it through H02's validator. [asserted]
3. Prove the unit appends only disposition; no commit, installation or active pointer changes. [asserted]

**Done:** One exact owner disposition is durable and replayable, while all candidate bytes remain inactive. [asserted]

```powershell
python -m pytest tests/test_promotion_authority.py tests/test_human_action_receipts.py -q
```

**Commit:** `feat(authority): bind promotion disposition receipts`. [asserted]

## S01 — immutable promoter policy and impact contract

**Deliverable:** `promote.py` registers one immutable impact contract and typed promoter-beta receipt, while active-harness decisions remain disabled without exact registered EXP-104 and all activation evidence. [cited: ADR-0076]

**Depends on:** F03 and explicit implementation authorisation. Refusal machinery may precede H01. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/promote.py`
- `tests/test_promote_contracts.py`

**Steps:**

1. Test missing/weakened/mutated contracts, generic-beta substitution, absent EXP-104 and every mechanical effect class. [asserted]
2. Add immutable `ImpactContract`/`PromoterBetaReceipt` schemas and pure decision policy; no execution enters product code. [asserted]
3. Preserve fail-closed defaults and make the current absent EXP-104 produce a recorded refusal. [asserted]

**Done:** The policy accepts only an exact immutable contract and specialised receipt; current activation always refuses. [asserted]

```powershell
python -m pytest tests/test_promote_contracts.py -q
```

**Commit:** `feat(promote): freeze impact contracts and safety floors`. [asserted]

## S02 — sealed one-use evaluation and reversal proof

**Deliverable:** One quarantined candidate is evaluated exactly once against a sealed instrument and complete adverse table, with candidate-hidden fields and exact scratch forward/reverse equality; no owner card or activation is produced. [cited: ADR-0076; self-improvement sections 2-3]

**Depends on:** S01 and A07 for any non-fixture candidate. Offline fixtures may land first; an uncontained real candidate records `candidate_unexecutable`. [asserted]

**Claim exactly:**

- `src/consilient/promote.py`
- `scripts/promote_loop.py`
- `tests/test_promote_instrument.py` (new)

**Steps:**

1. Test alternate instrument imports, repeat query, hidden-field access, missing adverse rows, Goodhart improvement and reversal mismatch. [asserted]
2. Add one-use lineage/sealed-manifest policy and keep aggregate qualification evidence privileged. [asserted]
3. Extend the existing loop only for offline evaluation and scratch forward/reverse proof; it cannot commit, install or swap a pointer. [asserted]

**Done:** A sealed candidate yields one immutable evaluation/reversal package or an exact refusal, and cannot inspect the hidden instrument. [asserted]

```powershell
python -m pytest tests/test_promote_instrument.py -q
```

**Commit:** `feat(promote): seal one-use candidate evaluation`. [asserted]

## S03 — deterministic owner card and privileged omissions

**Deliverable:** The existing dashboard renders one deterministic four-sentence proposal card from S02 facts, while recall/instruction assembly omits qualification, sentinel and card-private fields from candidate contexts. [cited: ADR-0076; self-improvement section 3]

**Depends on:** S02, T04 and M03. [asserted]

**Claim exactly:**

- `src/consilient/dashboard.py`
- `src/consilient/recall.py`
- `src/consilient/instructions.py`
- `tests/test_promote_card.py` (new)

**Steps:**

1. Test exact four-sentence rendering, absent/adverse facts, projection replay and every privileged-field canary. [asserted]
2. Render solely from bound evaluation/contract facts; no free-form model summary. [asserted]
3. Add explicit non-content omission reasons to recall/instruction receipts. [asserted]

**Done:** Projection rebuild gives byte-identical card text and no candidate context contains privileged fields. [asserted]

```powershell
python -m pytest tests/test_promote_card.py tests/test_recall_receipts.py -q
```

**Commit:** `feat(dashboard): render sealed promotion proposals`. [asserted]

## S04 — exact approval-to-commit binding

**Deliverable:** The existing commit gate admits one inactive tracked-skill commit only when staged parent/tree/paths and resulting commit/tree match S02/S03 plus one unused H03 receipt. [cited: ADR-0076]

**Depends on:** S02, S03, H03, A07, registered and confirmed EXP-104, and every promoter/downstream beta/alpha/joint-outcome conjunct. It is currently blocked. [measured] [asserted]

**Claim exactly:**

- `src/consilient/commit_gate.py`
- `scripts/commit_gate.py`
- `src/consilient/promote.py`
- `tests/test_promote_commit_binding.py`

**Steps:**

1. Refuse before editing if any dependency reference is absent; do not edit the research register. [asserted]
2. Test staged/working-tree divergence, index mutation, wrong parent, path escape, hook bypass history and receipt replay. [asserted]
3. Add one promotion conjunct to the existing commit gate, reading index blobs and permitting only tracked `.agents/skills/`. [asserted]
4. Bind the resulting Git objects back to the proposal without loading the candidate. [asserted]

**Done:** Only exact approved staged bytes acquire a commit-bound receipt; every mismatch remains inactive. [asserted]

```powershell
python -m pytest tests/test_promote_commit_binding.py -q
```

**Commit:** `feat(commit-gate): bind promotion approval to staged bytes`. [asserted]

## S05 — durable active-pointer transaction

**Deliverable:** `promote_loop.py` alone performs the idempotent write-ahead activation of one read-only versioned installation, and every supported fresh loader resolves the durable pointer. [cited: ADR-0076]

**Depends on:** S04 and every activation conjunct rechecked at execution time. Landing code alone enables nothing. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/promote.py`
- `scripts/promote_loop.py`
- `scripts/dispatch.py`
- `src/consilient/instructions.py`
- `tests/test_promote_activation.py`

**Steps:**

1. Test fault cuts at every append, installation and pointer replacement plus unsupported loaders. [asserted]
2. Add one-candidate monotonic schemas using F01/F02; no second journal. [asserted]
3. Add one transaction lock, versioned installation, atomic pointer replacement and evidence-derived recovery. [asserted]
4. Make every supported fresh dispatch/instruction load resolve only the protected pointer. [asserted]

**Done:** Every crash leaves only the durably approved parent or candidate active; missing evidence leaves the parent active. [asserted]

```powershell
python -m pytest tests/test_promote_activation.py -q
```

**Commit:** `feat(promote): make active-pointer changes durable`. [asserted]

## S06 — exact rollback and drift controller

**Deliverable:** A registered safety, drift, missing-telemetry or instrument-mismatch trigger restores the exact last approved pointer and records success only after governed-state equality and frozen probes pass. [cited: ADR-0076]

**Depends on:** S05 and a registered contract with fixed triggers, horizon and cumulative drift budget. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/promote.py`
- `scripts/promote_loop.py`
- `scripts/run_loop.py`
- `tests/test_promote_rollback.py`

**Steps:**

1. Test every trigger, cumulative regression, missing sentinel, instrument drift, probe failure and crash cut. [asserted]
2. Validate attempted/proved/unproven rollback records centrally. [asserted]
3. Restore only the recorded parent, rehash governed state and run frozen probes; failed proof stops at `rollback_unproven`. [asserted]
4. Reuse the ordinary cadence only; it cannot classify, retry forward or persist another state. [asserted]

**Done:** Replay reproduces active state/adverse counts, and rollback is never claimed from an event or exit code without restored artefact proof. [asserted]

```powershell
python -m pytest tests/test_promote_rollback.py -q
```

**Commit:** `feat(promote): prove rollback on registered drift`. [asserted]

## Order, deferrals and completion

Continue the ordinary product spine first. Land S01-S03 as refusal/evaluation/inspection value. When external verifier/origin decisions and A07 exist, land H01-H03. Start S04-S06 only after EXP-104 is genuinely registered and confirmed and every fixed evidence floor passes. An EXP-104 kill retains S01-S03 and permanently removes the active branch unless a new prospectively registered decision supersedes it. [asserted]

Defer phone/WebAuthn writes, dependency selection, private HTTPS configuration, research-register changes, live candidate building, tracked-skill activation and external/metered/credentialled effects until their named authorities/evidence exist. `.harness/adapted/` activation remains deferred because the commit transaction cannot bind its event-projected payload. [asserted]

```powershell
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m mypy --strict src/consilient
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m ruff check .
```

Before accepting the stream, prove the six-command surface and `routing_orchestration_enabled=false`, confirm only `events.py` wrote trajectory rows, replay receipt/proposal/pointer/rollback state, and scan candidate contexts for credentials, hidden instrument fields and authentication material. [asserted]
