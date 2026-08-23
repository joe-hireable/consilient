# Foundation, task and delivery implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Execute one numbered unit, run its exact acceptance command, commit only its claim paths, then release the claim.

**Goal:** Make one sentence become a durable commitment, the minimum verified work graph, evidence-closed tasks and an honest finished delivery without routine human intervention. [asserted]

**Architecture:** The trajectory is authoritative. Chat is an intake compiler, `work_items.py` is the task kernel, `coordination.py` is the atomic lease boundary, `dispatch.py` remains the outer runner, and dashboard/delivery state is a disposable projection. [cited: ADR-0068, ADR-0070, ADR-0071, ADR-0072]

**Tech stack:** Existing Python standard-library modules, daily JSONL trajectory, SQLite projections, Git objects for checkpoints, pytest. [measured]

**Spec:** `2026-08-22-chat-conversation.md`, `2026-08-22-chat-delivery.md`, `2026-08-22-task-management.md`, ADR-0068 and ADR-0070 through ADR-0072. [measured]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after any named dependency or launch ruling changes. [asserted]

**Falsifier:** Any listed unit needs an unclaimed mutable path, cannot complete through its named focused test, or produces delivery state that replay cannot reconstruct. [asserted]

## Stream constraints

- Apply launch rulings S-01 through S-04 and S-12 from the index before coding. [asserted]
- Preserve legacy dispatch rows; only `native.v1` items can become evidence-closed durable tasks. [asserted]
- An outcome precedes closure, an estimate precedes a claim, and a decision precedes any material effect. [cited: ADR-0071, ADR-0072, ADR-0079]
- No task/UI state may be inferred from model prose, process identity or launcher exit code. [measured: recorded local failures] [asserted]
- Units sharing a source path are serial even if their logical prerequisites are otherwise satisfied. [asserted]

## F01 — durable single-event append

**Deliverable:** `events.append(path, event)` returns only after a complete UTF-8 line is serialised across processes, flushed, fsynced and rereadable; a killed writer releases the kernel-backed per-log lock. [asserted]

**Depends on:** none. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `tests/test_event_durability.py` (new)
- `tests/test_budget.py`

**Steps:**

1. Add failing multiprocessing fixtures for simultaneous ordinary appends, kill while holding the lock, short writes, flush/fsync failure and first-file creation. [asserted]
2. Add the smallest Windows/POSIX standard-library lock and durability path; keep the public `append(path, event)` call intact. [asserted]
3. Extend the AST allowlist only for the inert stdlib primitives actually used; the existing environment/network/dynamic-call bans stay effective and their negative controls stay green. [asserted]
4. Prove every acknowledged event can be read immediately and no partial JSON line is acknowledged. Directory fsync is required where the platform exposes it; the Windows guarantee is stated no more broadly than the tested primitive. [asserted]

**Done:** 200 concurrent appends produce 200 valid distinct lines; a killed holder does not leave a stale lock; each injected durability failure returns an error and no success acknowledgement. [asserted]

```powershell
python -m pytest tests/test_event_durability.py tests/test_budget.py::test_product_tree_has_no_outbound_or_credential_capability -q
```

**Commit:** `feat(events): make ordinary append durable and process-serialised`. [asserted]

## F02 — atomic compare-and-append transaction

**Deliverable:** One per-log transaction reads the accepted prefix and rejections while holding the F01 lock, runs a pure domain transition validator, then appends one or more contiguous records with one durable acknowledgement. [asserted]

**Depends on:** F01. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `tests/test_event_transactions.py` (new)

**Steps:**

1. Freeze the internal contract in the test as `append_transaction(log_dir, candidates, transition_validator)`; candidates are validated before any byte is written. [asserted]
2. Pass the immutable accepted prefix and rejection list to the validator under the same lock; a rejection is never treated as an empty history. [asserted]
3. Keep `append(path, event)` as the one-event front door and route transition-governed kinds through the same transaction, so `consil record` cannot bypass a domain rule. [asserted]
4. Inject failure before validation, between candidates, before flush and after flush; a partial multi-event success is never returned. [asserted]

**Done:** two contenders using the same stale prefix cannot both admit a unique transition, and an outcome-plus-closure batch is either durably ordered or visibly incomplete with no false closure. [asserted]

```powershell
python -m pytest tests/test_event_transactions.py tests/test_event_durability.py -q
```

**Commit:** `feat(events): add atomic transition append`. [asserted]

## F03 — stable event identity and exact references

**Deliverable:** Every newly appended event has one stable `event_id`; `{event_id, event_kind, event_sha256}` resolves only to a unique earlier canonical event, while legacy rows without an ID remain readable and explicitly `unmeasured`. [asserted]

**Depends on:** F02. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `tests/test_event_identity.py` (new)

**Steps:**

1. Require `event_id` on new appends without rewriting schema-v1 history; use one validated format and reject case/whitespace aliases. [asserted]
2. Reject duplicate IDs inside one transaction and against the locked prefix. [asserted]
3. Compute `event_sha256` over the complete canonical event; do not store the hash as the identity or exclude mutable-looking fields from the digest. [asserted]
4. Add an earlier-event resolver which rejects missing, late, kind-mismatched and hash-mismatched references and returns `unmeasured` only for a genuine legacy row. [asserted]

**Done:** replay detects historical duplicate IDs, reference substitution and line reordering; valid references reproduce after deleting all projections. [asserted]

```powershell
python -m pytest tests/test_event_identity.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(events): bind stable event references`. [asserted]

## C01 — conversation turn and committed-request contract

**Deliverable:** A sanitised sealed `conversation.turn` can produce one versioned `work_item.committed` request whose source turns, success/non-goal boundary, Owner, authority and verifier contracts are digest-bound. [asserted]

**Depends on:** F03 and launch ruling S-04. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `tests/test_conversation.py` (new)
- `tests/test_work_items.py`

**Steps:**

1. Write failing central-writer tests for the turn identity and complete commitment fields in chat-conversation sections 3 and 5. [asserted]
2. Add deterministic canonical commitment hashing and immediate-prior supersession. [asserted]
3. Add `work_items.validate_transition()` for duplicate revision, changed digest, stale supersession, actor/authority and source-turn ordering; register it at F02's universal boundary. [asserted]
4. Preserve `dispatch-claim.v1` rows as claim history and refuse them as native task closure evidence. [asserted]
5. Test that unauthenticated chat may author an unprotected request but cannot author a protected answer, approval, consent or verdict. [asserted]

**Done:** generic `events.append()` and the helper make the same accept/refuse decision; concurrent duplicate commitment revisions admit exactly one; no secret fixture bytes or hash enter the trajectory. [asserted]

```powershell
python -m pytest tests/test_conversation.py tests/test_work_items.py -q
```

**Commit:** `feat(work): record immutable request commitments`. [asserted]

## C02 — protected verbatim context for active commitments

**Deliverable:** Bounded recall and instruction assembly always retain active commitment/corrections, unresolved authority, dissent and adverse outcomes or return an explicit omission plus direct stable-ID continuation. [asserted]

**Depends on:** C01. It may run in parallel with O01 because its paths are disjoint. [asserted]

**Claim exactly:**

- `src/consilient/recall.py`
- `src/consilient/instructions.py`
- `tests/test_recall.py`
- `tests/test_instructions.py`

**Steps:**

1. Add fixtures where ordinary history crowds an active commitment beyond the current character bound. [asserted]
2. Extend the protected-kind/selection logic and stable direct lookup; do not summarise or copy bulky artefacts. [asserted]
3. Bind the selected event IDs, canonical digest, omissions and continuation into `instructions.assembled`. [asserted]
4. Preserve deterministic reconstruction from the same prefix. [asserted]

**Done:** a fresh process reconstructs the supplied context byte-for-byte; an overflow says incomplete and points to the omitted active record rather than claiming semantic completeness. [asserted]

```powershell
python -m pytest tests/test_recall.py tests/test_instructions.py -q
```

**Commit:** `feat(recall): protect active commitment context`. [asserted]

## O01 — frozen minimum-stream plan

**Deliverable:** One `organisation.plan.frozen` event validates the smallest structural DAG, incumbent/delta, success/verifier contracts, hand-off contracts, ownership, paths, budget, expiry, estimate inputs and integration stream before native tasks open. [asserted]

**Depends on:** C01, F03 and principal acceptance of the PROPOSED S-02 source amendment to ADR-0068. This unit is non-dispatchable while that amendment remains proposed. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `tests/test_organisation_plan.py` (new)

**Steps:**

1. Freeze the plan schema from ADR-0068, binding the commitment digest and whole-plan digest. [asserted]
2. Validate unique stream IDs, one deliverable/Owner per stream, existing dependency IDs, acyclicity, one integration stream, non-overlapping mutable paths or an explicit integration owner, and frozen verifier/hand-off contracts. [asserted]
3. Store predecessor identity/revision/hand-off-contract digest only; future artefact digests are forbidden in the frozen plan and bound later at claim. [algebra]
4. Add fixtures proving an atomic request remains one stream, an independently checkable dependency splits, and a title/model/specialism alone never splits. [asserted]

**Done:** the same commitment and plan input produce the same digest; cycles, missing predecessors, pathless mutable streams and outcome-aware plan edits refuse at the central writer. [asserted]

```powershell
python -m pytest tests/test_organisation_plan.py tests/test_work_items.py -q
```

**Commit:** `feat(work): freeze minimum verifiable plan`. [asserted]

## T01 — native work-item graph and replay state

**Deliverable:** `native.v1` work items project deterministically to `blocked`, `ready`, `active`, `closed`, `failed`, `refused`, `cancelled`, `expired`, `invalidated`, `superseded`, with one frozen contract and many attempts. [asserted]

**Depends on:** O01 and the source-aligned S-03/S-04 rulings. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `src/consilient/projection.py`
- `tests/test_native_work_items.py` (new)
- `tests/test_task_projection.py` (new)

**Steps:**

1. Add the exact frozen item, dependency, exposure and attempt contracts from task-management section 3. [asserted]
2. Materialise only streams from a matching frozen plan; reject cycles/missing hand-off verifiers again at this trust boundary. [asserted]
3. Implement a pure projection; `commitment_paused` is a typed blocking cause, not a new mutable status. [asserted]
4. Preserve legacy claim rows outside native state and make projection deletion/rebuild the acceptance oracle. [asserted]

**Done:** two complete replays yield identical state and blocker ordering; prose comments and bare completion cannot change native state. [asserted]

```powershell
python -m pytest tests/test_native_work_items.py tests/test_task_projection.py tests/test_work_items.py -q
```

**Commit:** `feat(work): project evidence-bearing native items`. [asserted]

## T02 — atomic readiness, claim and fencing

**Deliverable:** One locked transition proves task readiness and canonical path non-overlap, binds exact predecessor receipts and candidate ordinal, provisions a runtime-conformant isolated workspace/index, then issues one lease/fencing epoch before harness launch. [asserted]

**Depends on:** T01, launch ruling S-01 and the runtime-conformant workspace contract in ADR-0091/dependency-scheduling. [asserted]

**Claim exactly:**

- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_coordination.py`
- `tests/test_dispatch.py`

**Steps:**

1. Replace the separate live-claim check/open sequence with F02's atomic transition. [asserted]
2. Bind ticket/revision/attempt/run, plan and commitment digests, canonical paths, predecessor artefact/receipt digests, expiry, route/capability context and fencing epoch. [asserted]
3. At the composite-verifier boundary, refuse candidate `1` and every successor while `routing.py` is unwired or returns a refusal; record no exposure. Only a sufficient authenticated, trajectory-derived `human_verdict_beta` projection bound to the same task family and frozen composite-verifier protocol/version is eligible; proxy, mutation and missing/mismatched scope values refuse. Do not substitute an asserted cold-start allowance for that exact projection-derived ceiling. [cited: ADR-0077; verdict-supply §§ 2, 4-5] [asserted]
4. Provision a separate workspace and Git index using only a form the exact runtime/version has passed through read, write, stage and throwaway commit: linked worktree, isolated exported Git environment or full clone. A failing or unprobed tuple falls back to a proved form or refuses; retain the two-writer index-isolation regression. [cited: ADR-0091; dependency-scheduling D1]
5. Launch only after the durable claim and workspace probe return; a failed launch becomes an adverse attempt and releases by terminal event/expiry without pretending work ran. [asserted]

**Done:** two Windows/WSL contenders for overlapping paths yield exactly one lease; every write-admitted runtime/version proves read, write, stage, commit and index isolation; no unready, stale-revision, predecessor-mismatched or pathless mutable item reaches `run_process()`; and no beta-refused candidate reaches the composite verifier. [asserted]

```powershell
python -m pytest tests/test_coordination.py tests/test_dispatch.py -q
```

**Commit:** `feat(coordination): claim ready native work atomically`. [asserted]

## T03 — evidence-bound closure, conflict and invalidation

**Deliverable:** A native item closes only after its matching `attempt.outcome`, sealed artefact digests, every frozen verifier receipt, consumed predecessor bindings and conflict dispositions are durable; later rejection invalidates only exact descendants. [asserted]

**Depends on:** T01 and E01. Run after T02 if both would claim current work-item tests in the same branch. [asserted]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/projection.py`
- `tests/test_work_item_closure.py` (new)

**Steps:**

1. Add outcome-before-closure and idempotent recovery under one F02 transaction. [asserted]
2. Validate artefact/receipt locators, bytes and hashes against the frozen contracts; missing/fail/unknown is not closure. [asserted]
3. Implement the four conflict dispositions and keep affected consumers blocked until disposition. [asserted]
4. Project later principal rejection, predecessor invalidation and supersession by exact consumed digest; preserve unrelated descendants. [asserted]

**Done:** kill between outcome and closure, replay and retry reuse the same outcome without ever showing false closure; generic direct append cannot create a bare completion. [asserted]

```powershell
python -m pytest tests/test_work_item_closure.py tests/test_task_projection.py -q
```

**Commit:** `feat(work): require evidence for closure`. [asserted]

## T04 — truthful compact task view

**Deliverable:** The existing dashboard projects goal, Owner, critical path, exact blockers, latest sealed artefacts/receipts, dissent, quarantines/adverse counts and machine closure separately from absent/accepted/rejected human verdict. [asserted]

**Depends on:** T03. [asserted]

**Claim exactly:**

- `src/consilient/dashboard.py`
- `tests/test_task_dashboard.py` (new)

**Steps:**

1. Add a compact local render from the task projection; do not add a board, editable status or new store. [asserted]
2. Render zero adverse/quarantine counts, not only non-zero ones. [asserted]
3. Escape all trajectory text and preserve the existing no-network/no-script dashboard property. [asserted]
4. Label closure `closed / unreviewed` until an authenticated separate verdict exists. [asserted]

**Done:** deleting SQLite and rerendering from JSONL gives byte-identical task facts; a stale/unavailable projection connector cannot change readiness or closure. [asserted]

```powershell
python -m pytest tests/test_task_dashboard.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(dashboard): show evidence-bearing task state`. [asserted]

## C03 — DeliveryIntake and correction fencing

**Deliverable:** A read-only `DeliveryIntake` resolves the exact commitment/plan references and prefix anchor; a correction fences the old revision and reuses only byte-compatible sealed work. [asserted]

**Depends on:** C01, O01, T01, T02, T03 and S-03. [asserted]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/coordination.py`
- `tests/test_delivery_intake.py` (new)

**Steps:**

1. Freeze every field listed in chat-conversation `DeliveryIntake`; accept references, never a transcript summary. [asserted]
2. Verify commitment/plan event IDs, hashes and prefix digest before returning the projection. [asserted]
3. Make `pause`, `cancel` and `replan` append-only correction dispositions; fence new claims and stale completion under the atomic transition. [asserted]
4. Admit reuse only when inputs, deliverable/hand-off and verifier contracts plus relevant digests are byte-identical. [asserted]

**Done:** a correction racing closure retains the old adverse attempt, blocks stale closure and produces one deterministic new intake or typed terminal disposition. [asserted]

```powershell
python -m pytest tests/test_delivery_intake.py tests/test_coordination.py -q
```

**Commit:** `feat(delivery): bind intake and correction revisions`. [asserted]

## D01 — immutable delivery estimate and reforecast

**Deliverable:** `delivery.estimate` revision zero is durable before any claim; later evidence can append one pre-breach revision without overwriting the original range. [asserted]

**Depends on:** C03 and O01. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/projection.py`
- `tests/test_delivery_estimates.py` (new)

**Steps:**

1. Validate the exact identity, range, evidence, resource, stream and recovery fields from chat-delivery section 3. [asserted]
2. Derive comparable ranges only from uncensored matching completed outcomes; retain adverse/censored rows and use the frozen-slice low-evidence fallback when fewer than five match. [asserted]
3. Preserve revision zero and require a cause/new range before its upper bound for any reforecast. [asserted]
4. Refuse claim ordering when estimate zero is absent or digest-mismatched. [asserted]

**Done:** fixed fixtures reproduce their range and evidence references; post-breach/silent overwrite and outcome-aware cohort selection fail. [asserted]

```powershell
python -m pytest tests/test_delivery_estimates.py tests/test_task_projection.py -q
```

**Commit:** `feat(delivery): freeze estimate before work`. [asserted]

## D02 — sealed checkpoint and stale-epoch refusal

**Deliverable:** A checkpoint event binds plan/commitment/item/attempt identity, sequence and fencing epoch, reachable Git object, owned-path artefacts, verifier/adverse receipts and exact next action; only the live epoch can advance it. [asserted]

**Depends on:** T02 and D01. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/coordination.py`
- `scripts/dispatch.py`
- `tests/test_checkpoints.py` (new)
- `tests/test_dispatch.py`

**Steps:**

1. Add checkpoint schema/chain validation and one per-stream local Git ref in the outer script; product code performs no subprocess call. [asserted]
2. Verify object reachability, base tree, owned paths and all digests before append. [asserted]
3. Atomically compare the live claim epoch, advance the checkpoint ref, then append; a stale worker can do neither. [asserted]
4. Reject repeated sequence/digest, missing object, escaped path and transcript/process-ID substitutes. [asserted]

**Done:** a stale worker after reassignment cannot publish; the latest valid checkpoint survives process-tree death and is verifiable from artefacts, not launcher status. [asserted]

```powershell
python -m pytest tests/test_checkpoints.py tests/test_dispatch.py tests/test_coordination.py -q
```

**Commit:** `feat(delivery): seal attributed checkpoints`. [asserted]

## D03 — restart from evidence, not process identity

**Deliverable:** Restart marks the killed attempt unknown/adverse, projects the latest valid checkpoint, starts a new run/epoch for the same unfinished candidate and never reruns a completed predecessor. [asserted]

**Depends on:** D02 and T03. [asserted]

**Claim exactly:**

- `src/consilient/loop.py`
- `scripts/run_loop.py`
- `tests/test_delivery_recovery.py` (new)

**Steps:**

1. Preserve current honest abandoned-tick accounting. [asserted]
2. Reconstruct ready unfinished streams and verify checkpoint refs/digests before selecting one deterministic next slice. [asserted]
3. Launch through the existing dispatch entry with a new run ID/higher epoch; do not claim the process resumed. [asserted]
4. Add process-tree kill fixtures at predecessor-complete/dependent-unclaimed and mid-slice boundaries. [asserted]

**Done:** every terminal replay has no duplicate completed stream, no early dependent, unchanged predecessor digest and a distinct adverse old attempt. [asserted]

```powershell
python -m pytest tests/test_delivery_recovery.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(loop): recover from sealed task checkpoints`. [asserted]

## D04 — honest start, exception and final delivery

**Deliverable:** One deterministic start/window projection, at most one pre-breach exception and one final `delivery.outcome`/card expose the finished artefact or typed adverse terminal result. [asserted]

**Depends on:** T03, T04, D01, D02 and S-01. This unit may implement refusal and projection, but automatic `Done` remains inactive unless the exposure was admitted by the exact eligible human-beta projection in S-01. It produces a same-machine projection only; any later outward delivery consumes the action-boundary protocol in A05. [cited: ADR-0077] [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `src/consilient/projection.py`
- `src/consilient/dashboard.py`
- `tests/test_delivery_outcome.py` (new)

**Steps:**

1. Encode the seven-condition Done predicate: `closed / unreviewed` requires a prior exposure admission from a sufficient authenticated, trajectory-derived `human_verdict_beta` projection bound to the same task family and frozen composite-verifier protocol/version; missing, insufficient, proxy, mutation, unscoped or mismatched beta, or unwired routing, cannot close automatically. [cited: ADR-0077; verdict-supply §§ 2, 4-5] [asserted]
2. Bind final commitment/plan/item/checkpoint chains, artefact/verifier receipts, beta state, dissent, cost and every adverse count. [asserted]
3. Make visible messages pure projections with exact source event IDs; local display is not a human verdict or external-send receipt. [asserted]
4. Preserve a later authenticated rejection as the same false-accept pair without rewriting delivery history. [asserted]

**Done:** changed commitment, missing dependency/check, invalid checkpoint, omitted adverse count, missing/insufficient beta, missing prior exposure admission or exposure overrun refuses `Done`; a later rejection leaves `verifier-accepted / human-rejected`. [asserted]

```powershell
python -m pytest tests/test_delivery_outcome.py tests/test_task_dashboard.py tests/test_feedback.py -q
```

**Commit:** `feat(delivery): project honest finished outcomes`. [asserted]

## C04 — construct an inactive one-sentence intake experiment

**Deliverable:** An explicit `--experiment-only` path at the existing local transport-ingest boundary accepts one sealed fixture turn, redacts/brokers secret spans, emits C01/O01/T01/D01 records into a caller-supplied isolated trajectory and returns its D04 start projection. The configured live intake and default path remain unchanged. [asserted]

**Depends on:** C01, O01, T01, C03, D01, D04, S-12 and explicit principal authorisation to construct the inactive experiment. This unit is non-dispatchable until that construction authority exists; ADR-0070 and one-surface authorise no product activation. [cited: ADR-0070; one-surface]

**Claim exactly:**

- `src/consilient/transport.py`
- `scripts/ingest_transport.py`
- `tests/test_conversation_intake.py` (new)

**Steps:**

1. Require the explicit experiment flag and an isolated output root; without both, the compiler path is unavailable. Reuse the existing final-message transport record; preview/typing deltas remain ephemeral. [asserted]
2. Implement the zero-question default and one-question maximum only for an otherwise unresolved principal-only decision; an unanswered question blocks only the protected branch. [asserted]
3. Call the existing sealed commitment/plan/item/estimate helpers in order against the isolated trajectory only; do not parse chat inside dispatch, write a second state file or append to the configured live log. [asserted]
4. Add local fixtures for typos, factual ambiguity, reversible choice, genuine preference, secret redaction, unanswered question, correction, refusal and timeout. [asserted]

**Done:** the explicit isolated experiment reaches a truthful start record with zero confirmation turns; the normal transport path is byte-for-byte unchanged and appends no compiler record; a protected answer remains an untrusted proposal until H01/H02; no arrow in the experimental sequence can be skipped. [asserted]

**Activation:** Absent from this plan. Default or live intake remains disabled until the matched
chat-versus-command trial reports and the principal accepts ADR-0070 or a superseding decision that
explicitly amends one-surface's no-implementation boundary. A positive trial does not itself author
that decision. [cited: ADR-0070; one-surface] [asserted]

```powershell
python -m pytest tests/test_conversation_intake.py tests/test_transport_ingest.py tests/test_delivery_intake.py -q
```

**Commit:** `test(transport): construct inactive chat intake experiment`. [asserted]

## Stream completion

Run the focused files above, then the complete suite, strict type check and Ruff. Verify by replayed task/delivery artefacts, not only command exit status. [asserted]

```powershell
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m mypy --strict src/consilient
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m ruff check .
```

## F04 — verify which Cursor models the vendor actually includes

**Deliverable:** every `ModelOption` in `harness.py` carries a pool assignment that is either
verified against the vendor's own billing surface or explicitly marked unverified, and routing
refuses by default to spend a pool it cannot verify. [asserted]

**Depends on:** none. It touches `harness.py` and its own tests, so it shares no lane with
`F01-F03` on `events.py` and may run beside them. [asserted]

**Claim exactly:**

- `src/consilient/harness.py`
- `tests/test_headroom.py`
- `tests/test_model_pools.py` (new)

**Why this exists.** On 23 August 2026 the principal's Cursor billing page read: *"Cursor Models —
Includes Cursor Grok and Composer — 1% used"* and *"Other Models — 81% used"*, with *"Additional
usage beyond limits consumes Other Models quota or on-demand spend."* `harness.py` assigns
`kimi-k3-max`, `kimi-k3-high`, `kimi-k3-low`, `kimi-k2.7-code`, `glm-5.2-max` and `glm-5.2-high` to
the `cursor-models` pool, but the vendor names only Grok and Composer as included. Other Models rose
from 58% to 81% across a day of heavy `kimi-k3-max` dispatch. [measured] **If that mapping is wrong,
the router spends a metered pool while believing it is free** — and `CURSOR_OTHER_PREFIXES` guards
only `claude-`, `gpt-` and `gemini-`, so nothing catches it.

**Prior art — read this before step 1.** `docs/20-design/quota-pools-and-routes-2026-08-21.md`
already did much of this work on 21 August 2026. It records that **Cursor Models means "Cursor Grok,
Composer"**, enumerates seven route variants with their measured model attestation, and measured the
actual dispatch mix as `claude-opus-5` 135, `gpt-5.6-sol` 86, `kimi-k3` 2, with **"zero grok rows and
zero composer rows"** across 78 trajectory files. [measured] **Start from that document, confirm or
refute its findings against the current tree, and say which.** Re-deriving it from scratch is the
failure this unit exists to stop. `docs/20-design/supergrok-feasibility-2026-08-20.md` may also bear
on the grok pool.

**Steps:**

1. Add failing tests: a model whose pool is unverified must not be selectable by automatic routing;
   an explicitly named model must still be spendable so the principal keeps the override.
2. Establish, from Cursor's own surfaces only, which model families the Ultra plan includes. **Do not
   infer from the model name.** A vendor page, a CLI output or an API response is evidence; a prefix
   convention is not. Record the source and the retrieval date beside each assignment.
3. Mark every assignment `verified` or `unverified` in the registry, and make the unverified ones
   fail closed for automatic selection — the same posture `reasoning: unknown` already takes.
4. If the evidence shows kimi or glm bill to Other Models, correct their pool and say so plainly in
   the commit; if it shows the current mapping is right, **say that too** and leave it unchanged.

**Done:** no `ModelOption` carries an unsourced pool; automatic selection refuses an unverified pool;
an explicitly named model still dispatches; the existing headroom tests stay green. [asserted]

```powershell
python -m pytest tests/test_model_pools.py tests/test_headroom.py -q
```

**Commit:** `fix(routing): source every Cursor pool assignment or fail closed`. [asserted]

## F05 — make the Grok arm usable, or retire it with evidence

**Deliverable:** `scripts/dispatch.py` invokes `grok` in a configuration that returns a completion
for a trivial prompt in under 60 seconds, or the arm is deregistered with the measured reason
recorded. [asserted]

**Depends on:** F04. It touches `dispatch.py`'s Grok branch and may touch `harness.py` only on the measured deregistration branch, so F04 must release the `harness.py` lane first. [asserted]

**Claim exactly:**

- `scripts/dispatch.py`
- `src/consilient/harness.py`
- `tests/test_grok_arm.py` (new)
- `docs/00-context/grok-arm-2026-08-23.md` (new)

**Why this exists.** SuperGrok Heavy is 17% used with 83% idle and a spare reset banked, while the
`grok` CLI arm times out roughly two runs in three. [measured, principal's usage page 23 Aug 2026]
**The capacity is idle because the arm does not finish work, not because it was never tried.**

**What is already established — do not re-derive it** [measured, 23 Aug 2026]:

1. `grok -p "Reply READY." --output-format json --always-approve` **times out with zero bytes** on a
   12-character prompt. The brief size is not the cause.
2. Its own `--debug-file` log gives the timeline: startup at `00:45:43`, and
   `session.handle_prompt{prompt_length=12}` at `00:47:43`. **Two minutes elapse before the prompt is
   even handled**, and it was only handled as the process was torn down at the deadline.
3. The startup cost is plugin and MCP discovery. The log shows it resolving plugins out of
   **Claude Code's** directory — `plugin_name=playwright winner=C:\Users\jpbpr\.claude\...`, likewise
   `github`, `firebase`, `feature-dev` — and `~/.grok/config.toml` declares `[mcp_servers.*]` for
   figma, context7, playwright and others. **It launches one MCP child per server on every run.**
4. `grok inspect` reports **`Project trusted: no`**, which may independently block a headless run.
5. These do **not** fix it: `--output-format json`, `--tools ""`, `--no-subagents`,
   `--disable-web-search`, setting `GROK_HOME` to an isolated directory, and killing a 35-hour-stale
   `grok.exe` leader that was holding `~/.grok/leader.sock`.

**Steps:**

1. Add a failing test: a trivial prompt through the dispatch grok path returns a completion within
   60 seconds.
2. Find the supported way to run grok without loading the user's MCP servers and plugins — a config
   key, a real environment variable, a profile, or a flag. **Read grok's own documentation and
   `grok inspect`; do not guess env var names.** `GROK_HOME` was tried and is not it.
3. Resolve the trust state without weakening it globally. **Do not edit `~/.grok/config.toml`** — that
   is the principal's interactive setup and his MCP servers must keep working. A dispatch-scoped
   config or profile is the shape wanted.
4. **If no supported configuration gets a trivial prompt under 60 seconds, deregister the arm** in
   `harness.py` with the measured reason, and say so plainly. **A paid but unusable arm should be
   recorded as unusable, not left in a rotation where it silently burns wall-clock.**

**Done:** either the new test passes against the real CLI, or the arm is deregistered and the report
states what was tried and what the vendor does not support. [asserted]

```powershell
python -m pytest tests/test_grok_arm.py -q
```

**Commit:** `fix(dispatch): make the grok arm return work or retire it`. [asserted]
