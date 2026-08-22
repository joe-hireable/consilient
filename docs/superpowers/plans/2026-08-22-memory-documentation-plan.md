# Memory, capability and living-documentation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Execute one numbered unit, run its exact acceptance command, commit only its claim paths, then release the claim.

**Goal:** Make captured records, recall, explicit capability use and the admitted specification corpus reconstructable from authoritative sources, with omissions and staleness visible and without activating autonomous learning or capability reuse. [asserted]

**Architecture:** `events.py` remains the only authoritative trajectory writer; immutable payloads live in a private content-addressed object directory; SQLite remains a disposable projection; `recall.py`, `capabilities.py` and `instructions.py` retain their present selection/assembly responsibilities; generated documents are checked against named producers and written specifications are admitted in bounded Class-W tranches. [cited: ADR-0073, ADR-0074]

**Tech stack:** Existing Python standard library, daily JSONL trajectory, SHA-256 objects below `.harness/`, SQLite projections, Markdown, JSON manifests, Git history and pytest. [measured]

**Specs:** `2026-08-22-memory-and-capability.md`, `2026-08-22-autonomy-and-friction.md`, `2026-08-22-self-improvement.md`, `2026-08-22-action-surface.md`, `2026-08-22-living-documentation.md`, `2026-08-22-model-lifecycle.md`; ADR-0073 through ADR-0076, ADR-0078, ADR-0079 and ADR-0085. [measured]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after a named dependency, launch ruling or admitted specification changes. [asserted]

**Falsifier:** This plan must be superseded if any unit needs a second authoritative log, a new product CLI command, a new mutable state service, an added dependency, an unclaimed mutable path, or cannot prove its single deliverable through the named focused test and acceptance command. [asserted]

## Frozen rulings and interfaces

- The only new event-kind names in this stream are `record.captured`, `capability.versioned` and `model.change`; aliases are refused. [asserted: build-plan ruling S-09]
- `.harness/objects/sha256/<first-two-hex>/<remaining-hex>` is the immutable payload layout. The trajectory stores a repository-relative locator, never an absolute private path or payload. [asserted]
- `records.capture_file(source, *, workspace_root, object_root, log_dir, actor, media_type, consent_purpose, retention_class)` is the sole capture interface. It returns a frozen `RecordRef(record_id, digest, byte_count, media_type, object_locator, event_id, event_sha256)` only after object install, reread/digest verification and durable `record.captured` append. [asserted]
- A `record.captured` body contains `record_id`, `digest`, `byte_count`, `media_type`, `object_locator`, `source`, `consent_purpose`, `retention_class`, `valid_time`, `supersedes` and `invalidates`; relation fields are arrays of exact F03 event references and may be empty. [asserted]
- The existing `recall.pack(...) -> str` signature stays source-compatible. Its returned text ends with one canonical JSON recall-receipt block; `recall.parse_receipt(text)` is the one parser for that block. [asserted]
- A recall receipt contains exactly: `query_digest`, `prefix_digest`, `scanned_universe_count`, ordered `candidate_ids`, ordered `selected_ids`, ordered `omitted` entries, `bytes_used`, `continuation_cursor`, `scan_complete`, `context_complete` and `semantic_status`. Omission reasons are closed to `irrelevant`, `superseded`, `permission`, `context_bound` and `corrupt`. [cited: memory-and-capability specification]
- `CapabilityManifest` contains the specification's canonical fields: stable `kind:name`, immutable version and content digests, source/object locator, authoring run, licence/privacy, purpose/postcondition, normalised input/output, permission/effect/trust boundaries, verifier semantics/version, evidence class, status, `supersedes`, `duplicate_of`, expiry and recheck. [cited: memory-and-capability specification]
- The execution-contract key is the canonical digest of kind, purpose/postcondition, interface, permission/trust boundary and verifier semantics. `capabilities.select_capabilities(...)` remains the only selector and may select only an explicitly requested active head; automatic reuse remains inert. [cited: ADR-0074]
- `instructions.assemble(...)` remains the only instruction assembler and `scripts/dispatch.py` remains its caller. No memory unit adds a `consil` subcommand or parses unsealed chat. [measured] [asserted]
- A data-driven persistent learned-state mutation is training; embedding computation used only for retrieval is not training, while fitting an embedding model is. M06 records this boundary but starts no fitting or promotion. [cited: ADR-0076]
- Class G output carries producer, source set and source SHA-256, has deterministic output and supports `--check`. Class W carries evidence tags, a falsifier and a review-by date. Class S remains an event-derived projection and is not introduced by this stream. [cited: ADR-0073]
- No unit changes Gate A, Gate B, `routing_orchestration_enabled`, the six-command `consil` surface, the standard-library policy or live effect authority. [measured] [asserted]

## Dependency and path schedule

```text
F03 -- E01(path lane) --> M01 --> M02 --> M03 --> M04 --> M05
                                  ^                       ^
                                  T03                     T02
                                                |
                                                +----> M06

L01 --> L02 --> L04 --> L05 --> L06
                         L03 ---------------> L06
```

The diagram records both semantic dependencies and the global shared-path lanes. `E01 -> M01` serialises `events.py`, `T03 -> M02` serialises `projection.py`, and `T02 -> M05` serialises `scripts/dispatch.py`; they do not add product semantics to the downstream unit. [asserted]

- After F03, M01 may run in parallel with L01 and L03 because their mutable paths are disjoint. [asserted]
- M04 follows M03 and releases `events.py` and `projection.py` before M06 or any later stream claims them. [asserted]
- L03 may run beside L01/L02/L04/L05. L06 is the only documentation unit that claims the workflow and therefore waits for every mechanical check it activates. [asserted]
- Workers must claim every listed path before editing, use `CONSILIENT_RUN_ID`, stage the named paths only, and never use `git add -A`. [asserted]

## Human-ingress critical path

M01-M05 do not depend on the future shared human-ingress units: they consume an already sealed task, an existing authority envelope and an explicit capability request, and they refuse missing consent or authority rather than asking through a second channel. [cited: ADR-0075, ADR-0078, ADR-0079] This keeps ordinary local/restorable memory work off the principal's critical path while preserving authenticated authority for scope widening or protected effects. [asserted]

M06 records model-state changes only. Any actual training, promotion, active-harness mutation, live publication or private-derived weight distribution remains behind the self-improvement experiments, the shared trusted ingress and the relevant first-party authority. [cited: ADR-0076, ADR-0078] L01-L06 are repository-local checks; they do not author principal words, accept an ADR, publish a result or silently renew a judgement. [cited: ADR-0073]

## M01 — acknowledged immutable object capture

**Deliverable:** One authorised file becomes an immutable SHA-256 object with a durably linked `record.captured` event before the caller receives an acknowledgement. [asserted]

**Depends on:** F03 and release of the `events.py` path by E01. [asserted]

**Claim exactly:**

- `.gitignore`
- `src/consilient/events.py`
- `src/consilient/records.py` (new)
- `tests/test_records.py` (new)

**Steps:**

1. Write failing tests for the frozen `capture_file`/`RecordRef` interface, exact object layout, duplicate-content reuse, non-UTF-8 bytes and the complete `record.captured` body. [asserted]
2. Add fixtures that refuse a source outside the resolved authorised workspace, a symlink escape, `.env`/private-key/token fixtures and an object locator which is absolute or leaves `.harness/objects/`; a refusal must expose its reason without appending a success event. [asserted]
3. Install to a same-directory temporary file, flush/fsync, atomically replace, reopen and recompute SHA-256 and byte count; reuse a matching existing object and refuse a mismatching collision. [asserted]
4. Add the central `record.captured` contract in `events.py`, including exact F03 validation for `supersedes` and `invalidates`; reject aliases, missing consent/retention metadata and self/future references. [asserted]
5. Append through F02/F03 only after the verified object exists, reread the appended event reference, then construct `RecordRef`. Inject failures at install, reread and event append to prove none returns success. [asserted]
6. Ignore `.harness/objects/` explicitly and test that neither an object nor its absolute source path is trackable through this interface. [asserted]

**Done:** A killed or fault-injected capture never acknowledges an unverified/unlinked object; two captures of identical bytes share content but retain distinct source events; every accepted event resolves to the exact bytes after a fresh process starts. [asserted]

```powershell
python -m pytest tests/test_records.py tests/test_event_identity.py -q
```

**Commit:** `feat(memory): capture immutable linked records`. [asserted]

## M02 — temporal memory projection

**Deliverable:** Replaying the accepted trajectory produces one deterministic temporal record view with current, historical, invalidated and contested heads. [asserted]

**Depends on:** M01 and T03; T03 must first release `src/consilient/projection.py`. [asserted]

**Claim exactly:**

- `src/consilient/projection.py`
- `tests/test_memory_projection.py` (new)

**Steps:**

1. Add replay fixtures for ordinary capture, immediate supersession, invalidation, two independently supported heads, corrupt/rejected lines and a reference to an unavailable object. [asserted]
2. Add disposable projection tables for immutable record facts and temporal relations, keyed by `record_id` and exact F03 event reference; do not copy payload bytes into SQLite. [asserted]
3. Project stable identity, digest, kind, actor, work item, capability contract, source and valid time from accepted events only. Rejected rows increment an adverse count and never become an empty prefix. [cited: memory-and-capability specification]
4. Resolve a single supported head as `current`, retain its predecessor chain as history, expose explicit invalidation, and return `contested` plus every supported head when no deterministic evidence rule resolves a conflict. [asserted]
5. Treat missing/corrupt objects and malformed relation targets as visible projection defects; never silently discard them or choose another head. [asserted]
6. Delete and rebuild the database twice from the same prefix and compare the complete ordered query output and `state_digest`. [asserted]

**Done:** Superseded and contested fixtures return current state, history and provenance deterministically; projection deletion loses no authoritative information. [asserted]

```powershell
python -m pytest tests/test_memory_projection.py tests/test_task_projection.py -q
```

**Commit:** `feat(memory): project temporal record heads`. [asserted]

## M03 — auditable bounded recall

**Deliverable:** Every existing recall string carries a deterministic receipt and direct continuation which make selection, omission and incompleteness inspectable. [asserted]

**Depends on:** M02. [asserted]

**Claim exactly:**

- `src/consilient/recall.py`
- `scripts/recall.py`
- `tests/test_recall_receipts.py` (new)

**Steps:**

1. Add failing fixtures for exact queries, paraphrases, superseded/contested records, permission exclusions, corrupt/rejected JSONL, source-changed records and a byte limit that excludes protected context. [cited: memory-and-capability specification]
2. Preserve `pack(...) -> str`; append one delimited canonical JSON receipt and add the strict `parse_receipt(text)` inverse. Reject duplicate receipt blocks and non-canonical/unknown omission reasons. [asserted]
3. Digest the normalised query and exact accepted prefix/projection identity, count the whole scanned universe, and retain stable ordered candidate and selected IDs. No self-reported semantic-confidence field is admitted. [asserted]
4. Distinguish `scan_complete` from `context_complete`. Set `semantic_status` to `unknown` outside a frozen labelled bank; absence of semantic measurement is never rendered as success. [cited: ADR-0074]
5. Make the continuation cursor bind the query, prefix digest, last stable candidate and limit; reject a cursor after source change and return a direct stable-ID continuation for omitted protected context. [asserted]
6. Update the existing script to print the pack and receipt without adding a product subcommand, and prove repeated runs over the same prefix are byte-identical. [asserted]

**Done:** The overflow fixture says exactly what was scanned, selected and omitted, reports both completion flags honestly, and resumes without duplicate or skipped candidate IDs. [asserted]

```powershell
python -m pytest tests/test_recall_receipts.py tests/test_recall.py -q
```

**Commit:** `feat(recall): emit bounded recall receipts`. [asserted]

## M04 — explicit active capability selection

**Deliverable:** An explicit request resolves to one validated active capability-manifest head per execution-contract/destination class while every other version remains addressable. [asserted]

**Depends on:** M03; M01 and M02 provide the event/object and temporal projection seams. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/capabilities.py`
- `src/consilient/projection.py`
- `scripts/capability_context.py`
- `tests/test_capability_manifests.py` (new)

**Steps:**

1. Freeze `CapabilityManifest`, its canonical serialisation, `kind:name` validation, immutable version/content digests and the execution-contract-key calculation in tests. [asserted]
2. Register the exact `capability.versioned` contract at the F02/F03 writer and reject a missing field, unresolvable source object, mutable version alias, unknown status, inconsistent `duplicate_of`/`supersedes` link or future/self reference. [asserted]
3. Extend the disposable projection with manifest versions and heads. Refuse two selectable active heads for the same execution-contract key and destination class; surface a conflict rather than choosing by time or prose. [asserted]
4. Extend the existing inventory/selector interface rather than adding a service: an explicit task request names stable identities or execution-contract keys, and `select_capabilities(...)` returns manifest IDs/version digests plus refusal/omission reasons. [asserted]
5. Keep automatic recommendation, semantic matching and promotion disabled even when an eligible head exists. Expired, inactive, superseded and duplicate manifests remain directly retrievable but not selectable. [cited: ADR-0074]
6. Update the existing context script to render the exact selected manifests and evidence/authority boundaries; retain schema-v1 inventory compatibility as explicitly `unmeasured`, never as an active version. [asserted]

**Done:** Manual exact selection is deterministic, an active-head conflict refuses, an inactive predecessor remains retrievable, and no query without an explicit capability request receives an automatic capability. [asserted]

```powershell
python -m pytest tests/test_capability_manifests.py tests/test_capabilities.py -q
```

**Commit:** `feat(capabilities): version explicit active manifests`. [asserted]

## M05 — reconstructable dispatch envelope

**Deliverable:** One dispatch can be reconstructed from its sealed task, recall receipt, selected capability versions, assembled instructions, outputs, artefact manifest and verifier outcome references. [asserted]

**Depends on:** M04 and T02; T02 must first release `scripts/dispatch.py`. [asserted]

**Claim exactly:**

- `src/consilient/instructions.py`
- `scripts/dispatch.py`
- `tests/test_dispatch_memory.py` (new)

**Steps:**

1. Add a fake-harness fixture which produces stdout, stderr, an artefact manifest and a verifier outcome, plus adverse fixtures for a missing output, secret-bearing output, outside-root artefact and truncated recall receipt. [asserted]
2. Replace direct/raw capability JSON insertion with the M04 selector result, then call the existing `instructions.assemble(...)` once. `dispatch.py` remains a caller, not a second selector or assembler. [asserted]
3. Capture the sealed task, exact assembled instructions, stdout, stderr, artefact manifest and verifier outcome through M01. Record an explicit absent/refused reference and reason when a source is unavailable or unsafe. [asserted]
4. Bind the recall receipt digest, ordered capability manifest IDs/version digests and pre-run record references into the existing `instructions.assembled` event; bind post-run output references into the existing non-forking dispatch outcome. [asserted]
5. Reconstruct the complete envelope from trajectory and object store in a new process and compare byte digests; do not infer success from launcher exit code or process identity. [measured: recorded local failures] [asserted]
6. Keep `--capability-inventory` and current dispatch entry points source-compatible, and leave automatic capability reuse and non-allowlisted workspaces refused. [asserted]

**Done:** The happy-path envelope reconstructs byte-for-byte; every adverse fixture remains visible in the outcome/receipt; secret or outside-root bytes enter neither object store nor trajectory. [asserted]

```powershell
python -m pytest tests/test_dispatch_memory.py tests/test_dispatch.py tests/test_instructions.py -q
```

**Commit:** `feat(dispatch): bind reconstructable memory envelope`. [asserted]

## M06 — model-change provenance record

**Deliverable:** Every attempted persistent model-state mutation can be represented by one validated `model.change` record without running or promoting a model. [asserted]

**Depends on:** M04; M04 must release `events.py` before this unit starts. [asserted]

**Claim exactly:**

- `src/consilient/events.py`
- `tests/test_model_change_records.py` (new)

**Steps:**

1. Freeze the exact body in tests: `change_id`, `mutation_class`, `base_model_digest`, nullable `dataset_digest`, `procedure_digest`, `authoring_run`, nullable `checkpoint_digest`, `status`, nullable `failure`, licence/privacy and exact record/capability references. [asserted]
2. Close `mutation_class` to `data_driven_training` and `non_data_driven_state_change`, and close `status` to `started`, `succeeded`, `failed` and `refused`. [asserted]
3. Register `model.change` at the central writer. Require a dataset record for data-driven training, forbid one for a declared non-data-driven change, require a checkpoint on success and require a visible failure/refusal reason otherwise. [cited: ADR-0076]
4. Resolve every base, dataset, procedure, checkpoint and capability reference through F03/M01/M04; reject aliases, future references and private-derived outputs lacking explicit licence/privacy disposition. [asserted]
5. Add tests that fitting an embedding model is classified as training while computing a frozen embedding for retrieval is not represented as a model change. [cited: ADR-0076]
6. Prove the unit imports no trainer, changes no model bytes, invokes no provider and cannot activate a capability. [asserted]

**Done:** Valid success/failure/refusal records replay with complete provenance; a fitting attempt cannot be disguised as retrieval and no test creates or promotes learned state. [asserted]

```powershell
python -m pytest tests/test_model_change_records.py tests/test_event_identity.py -q
```

**Commit:** `feat(events): record model-state changes`. [asserted]

## L01 — deterministic ADR index

**Deliverable:** `docs/decisions/index.md` is reproducibly generated from the ADR files and fails `--check` on any drift, collision or incomplete row. [asserted]

**Depends on:** none. It may start after F03 in parallel with M01. [asserted]

**Claim exactly:**

- `scripts/build_decision_index.py` (new)
- `docs/decisions/index.md`
- `tests/test_decision_index.py` (new)

**Steps:**

1. Add fixtures for ordered ADR files, duplicate numbers, missing/invalid status, supersession pointers, Markdown-significant titles and a stale generated index. [asserted]
2. Parse only `docs/decisions/[0-9][0-9][0-9][0-9]-*.md`; derive number, title, status and supersession target without consulting the existing index. [asserted]
3. Compute the source SHA-256 over the ordered `(relative path, file digest)` sequence and emit a header naming producer, source glob, source digest and the no-hand-edit warning. No wall-clock value enters output. [cited: ADR-0073]
4. Make ordinary invocation write atomically and `--check` compare bytes without writing; return 0 for exact output, 1 for drift and 2 for misuse. [asserted]
5. Preserve intentional index sections only if they are expressible from ADR source metadata; otherwise delete the maintained duplicate rather than adding a second source. [asserted]
6. Run the generator, inspect the diff for private repository material, then prove a second generation has no diff. [asserted]

**Done:** Adding, renaming or changing the status of an ADR changes the generated bytes; duplicate IDs refuse; two unchanged builds are byte-identical. [asserted]

```powershell
python -m pytest tests/test_decision_index.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/build_decision_index.py --check
```

**Commit:** `feat(docs): generate the ADR index`. [asserted]

## L02 — executable generated-document manifest

**Deliverable:** One checked manifest deterministically verifies every admitted Class-G document through its named producer. [asserted]

**Depends on:** L01. [asserted]

**Claim exactly:**

- `docs/generated-manifest.json` (new)
- `.github/scripts/check_generated_documents.py` (new)
- `scripts/build_requirements.py`
- `docs/40-spec/requirements.md`
- `tests/test_generated_documents.py` (new)

**Steps:**

1. Freeze manifest schema v1 in tests: ordered entries with `output`, repository-relative `producer`, literal `check_args`, ordered `sources` and expected header fields. Reject duplicate outputs/producers, traversal, shell metacharacters and a producer outside the repository. [asserted]
2. Admit exactly `docs/40-spec/requirements.md` via `scripts/build_requirements.py --check` first and `docs/decisions/index.md` via `scripts/build_decision_index.py --check` second. [measured] [asserted]
3. Make `build_requirements.py` emit the same producer/source/source-SHA header contract as L01 and preserve deterministic requirements ordering. [asserted]
4. Run each producer with `sys.executable`, an argument array, repository cwd, UTF-8 replacement decoding and a bounded timeout; never use a shell or execute a command supplied by a generated document. [asserted]
5. Report every failing entry and adverse count, including timeout and malformed output, before returning non-zero. An empty/malformed manifest is a failure, not zero generated documents. [asserted]
6. Regenerate requirements once, then prove the manifest runner and both direct `--check` calls agree. CI wiring remains deferred to L06. [asserted]

**Done:** Either generated output drifts when its source changes and both checks fail, while an unchanged checkout passes without modifying any file. [asserted]

```powershell
python -m pytest tests/test_generated_documents.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_generated_documents.py --check
```

**Commit:** `feat(docs): check generated-document manifest`. [asserted]

## L03 — append-only settled-record ratchet

**Deliverable:** The existing Git-history ratchet rejects silent edits to settled experiment outcomes and correction records as well as accepted/superseded ADR bodies. [asserted]

**Depends on:** none. It may run in parallel with L01-L05. [asserted]

**Claim exactly:**

- `.github/scripts/check_adr_trail.py`
- `tests/test_adr_trail.py`

**Steps:**

1. Add temporary-Git-repository fixtures for a `DONE` experiment entry, a still-open `READY` entry, a `docs/00-context/corrections-*.md` record, pure append, whitespace-only change, line deletion and historical body rewrite. [asserted]
2. Generalise the current history path classifier without renaming the script: retain accepted/superseded ADR semantics; treat the body of an experiment heading whose status contains `DONE` as settled; treat every committed correction-record line as append-only. [cited: ADR-0073]
3. Permit a new dated correction/outcome section to be appended after settled text, but never permit that marker to launder deletion or modification of the prior text. [asserted]
4. Keep the current history pin for pre-existing ADR findings and add no blanket exception for the new paths; the ratchet begins at the implementing commit and reports the exact commit/path/entry. [asserted]
5. Preserve Git-environment scrubbing, UTF-8 replacement decoding, bounded subprocess timeouts and the distinction between reported pre-pin candidates and post-pin failures. [measured]
6. Prove an open experiment remains editable until outcome while its transition to `DONE` freezes the resulting entry on the next commit. [asserted]

**Done:** Append-only updates pass; changing or deleting a settled outcome/correction line after the new pin fails with its exact locator; existing ADR behaviour is unchanged. [asserted]

```powershell
python -m pytest tests/test_adr_trail.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_adr_trail.py --self-test
```

**Commit:** `feat(docs): ratchet settled records append-only`. [asserted]

## L04 — first admitted Class-W specification tranche

**Deliverable:** The first eight specifications are admitted as Class W by one mechanical contract for evidence tags, falsifier, review date, generated-surface restatement and principal-quote provenance. [asserted]

**Depends on:** L02. [asserted]

**Claim exactly:**

- `.github/scripts/check_living_documents.py` (new)
- `tests/test_living_documents.py` (new)
- `docs/superpowers/specs/2026-08-22-action-surface.md`
- `docs/superpowers/specs/2026-08-22-autonomy-and-friction.md`
- `docs/superpowers/specs/2026-08-22-chat-conversation.md`
- `docs/superpowers/specs/2026-08-22-chat-delivery.md`
- `docs/superpowers/specs/2026-08-22-consilience-gate.md`
- `docs/superpowers/specs/2026-08-22-decision-protocol.md`
- `docs/superpowers/specs/2026-08-22-evidence-fusion.md`
- `docs/superpowers/specs/2026-08-22-expertise-acquisition.md`

**Steps:**

1. Freeze the Class-W parser in fixture tests: exactly one `Document class: W`, an ISO `Review by` date, one non-empty falsifier or anchor to a falsifier section, and evidence tags on load-bearing claim paragraphs. [cited: ADR-0073]
2. Add negative fixtures for an expired review, impossible date, missing/empty falsifier, untagged claim, principal-attributed quotation without an adjacent retrievable locator, dead local locator and literal restatement of an admitted generated surface. [asserted]
3. Derive generated surfaces from `docs/generated-manifest.json`. Normalise sentence whitespace/Markdown deterministically and refuse a matching substantive sentence; allow only a pointer or an explicit adjacent `living-doc: restatement-ok` directive naming the generated path/anchor and rationale. Print counts for checked, stale, suppressed, broken and unknown items, including a zero count. [asserted]
4. Require a principal quote's adjacent `Source:` locator to resolve to a repository path plus line/event identity or a syntactically valid public URL; do not accept author inference or a bare date as provenance. [cited: ADR-0073]
5. Migrate only the eight named files. Add the metadata block and a dated `22 August 2026` contract-adoption note; point to an existing falsifier section where possible and do not rewrite existing claim prose or upgrade evidence tags. [asserted]
6. Run the checker over exactly this tranche and inspect the diff for accidental content edits, duplicated falsifiers, private locators and principal wording attributed without a source. [asserted]

**Done:** All eight named specifications pass; every missing/expired field, literal restatement and unlocated principal quote fixture fails; no ninth specification is silently represented as admitted. [asserted]

```powershell
python -m pytest tests/test_living_documents.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$specs = @(
  'docs/superpowers/specs/2026-08-22-action-surface.md'
  'docs/superpowers/specs/2026-08-22-autonomy-and-friction.md'
  'docs/superpowers/specs/2026-08-22-chat-conversation.md'
  'docs/superpowers/specs/2026-08-22-chat-delivery.md'
  'docs/superpowers/specs/2026-08-22-consilience-gate.md'
  'docs/superpowers/specs/2026-08-22-decision-protocol.md'
  'docs/superpowers/specs/2026-08-22-evidence-fusion.md'
  'docs/superpowers/specs/2026-08-22-expertise-acquisition.md'
)
python .github/scripts/check_living_documents.py --check $specs
```

**Commit:** `feat(docs): admit first written-spec tranche`. [asserted]

## L05 — complete current Class-W specification tranche

**Deliverable:** The remaining nine specifications join an exact seventeen-file Class-W inventory, leaving no current specification silently unclassified. [asserted]

**Depends on:** L04. [asserted]

**Claim exactly:**

- `tests/test_living_document_inventory.py` (new)
- `docs/superpowers/specs/2026-08-22-living-documentation.md`
- `docs/superpowers/specs/2026-08-22-memory-and-capability.md`
- `docs/superpowers/specs/2026-08-22-model-lifecycle.md`
- `docs/superpowers/specs/2026-08-22-observability-and-steering.md`
- `docs/superpowers/specs/2026-08-22-portable-capability.md`
- `docs/superpowers/specs/2026-08-22-self-improvement.md`
- `docs/superpowers/specs/2026-08-22-squad-roles.md`
- `docs/superpowers/specs/2026-08-22-task-management.md`
- `docs/superpowers/specs/2026-08-22-verdict-supply.md`

**Steps:**

1. Add an inventory test whose expected set is the exact seventeen specification paths from L04 and L05; a missing file, unlisted new file, duplicate/case alias or non-W class fails. [asserted]
2. Add the Class-W metadata block and dated `22 August 2026` contract-adoption note to only the nine claimed specifications. Point at an existing falsifier where present; otherwise add one honest falsifier without upgrading evidence. [asserted]
3. Give every claimed specification `Review by: 2026-09-22` unless it already names an earlier review date; preserve the earlier date rather than extending it. [asserted]
4. Repair checker findings with pointers and source locators. Do not copy generated prose, weaken the checker, add a file-specific exception or silently alter the underlying design judgement. [asserted]
5. Run the L04 checker across all seventeen paths and verify the inventory failure by temporarily adding an unlisted fixture under a temporary copied specs root, not the working tree. [asserted]
6. Inspect the exact nine-document diff for the five newly landed specifications — `expertise-acquisition`, `model-lifecycle`, `observability-and-steering`, `portable-capability` and `squad-roles` — and prove each now has the same review-by contract. [measured] [asserted]

**Done:** The glob and explicit inventory are identical at seventeen files, all seventeen pass Class-W checks, and any eighteenth specification fails until deliberately classified. [asserted]

```powershell
python -m pytest tests/test_living_document_inventory.py tests/test_living_documents.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$specs = Get-ChildItem 'docs/superpowers/specs/2026-08-22-*.md' | Sort-Object FullName | ForEach-Object { $_.FullName }
if ($specs.Count -ne 17) { Write-Error "Expected exactly 17 admitted specifications, found $($specs.Count)"; exit 1 }
python .github/scripts/check_living_documents.py --check $specs
```

**Commit:** `docs(specs): admit remaining written-spec tranche`. [asserted]

## L06 — CI enforcement for the admitted documentation surface

**Deliverable:** Existing invariant CI fails drift, silent settled-record edits, stale Class-W specifications and unlocated/restated claims across the admitted generated and written surfaces. [asserted]

**Depends on:** L02, L03 and L05. [asserted]

**Claim exactly:**

- `.github/workflows/invariants.yml`
- `tests/test_living_document_ci.py` (new)

**Steps:**

1. Add a workflow-fixture test which parses `invariants.yml` and requires literal invocations of the manifest runner, the settled-record ratchet and the Class-W checker over the full specification glob. [asserted]
2. Place literal `python scripts/build_requirements.py --check` first, then run the complete generated-document manifest, the ADR/settled-record ratchet and the Class-W check. A failed first check prevents downstream claims of a clean documentation gate. [cited: ADR-0073]
3. Add a weekly schedule to the existing workflow so review-by expiry and local citation breakage are surfaced even without a pull request; do not add a workflow, bot, issue writer, secret or publication step. [asserted]
4. Preserve every existing invariant job, permission and trigger. Reuse the bounded, UTF-8-safe check interfaces and their checked/stale/suppressed/broken/unknown counts without modifying an unclaimed checker path. [asserted]
5. Test negative workflow copies with each invocation removed or reordered, plus a one-file-short inventory regression. The test reads YAML as text and adds no YAML dependency. [asserted]
6. Run every direct command once before relying on workflow wiring, then run the repository's static checks. Do not mark EXP-99 ready merely because mechanical CI is green; its different-class adversarial re-derivation remains a separate experiment precondition. [cited: living-documentation specification]

**Done:** A changed generated source, missing specification metadata, expired review date, silent settled-record edit or removed workflow invocation fails locally and in the existing invariant job; unchanged admitted surfaces pass without writes. [asserted]

```powershell
python -m pytest tests/test_living_document_ci.py tests/test_living_document_inventory.py tests/test_living_documents.py tests/test_generated_documents.py tests/test_adr_trail.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/build_requirements.py --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_generated_documents.py --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_adr_trail.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$specs = Get-ChildItem 'docs/superpowers/specs/2026-08-22-*.md' | Sort-Object FullName | ForEach-Object { $_.FullName }
python .github/scripts/check_living_documents.py --check $specs
```

**Commit:** `ci(docs): enforce admitted living documents`. [asserted]

## Visible value and measurement opportunities

1. M03 is the earliest user-visible memory value: a brief says what was scanned, selected, omitted and whether it is complete instead of silently truncating context. Measure exact-recall accuracy, stale-return rate, contested disclosure, bytes, latency and both completion flags on the frozen bank. [cited: memory-and-capability specification]
2. M04 makes an explicit capability choice inspectable by stable identity and version without taking the risk of automatic reuse. Measure duplicate-version detection, active-head conflicts, manual exact-selection accuracy and inactive-version retrievability. [asserted]
3. L01 is the earliest repository-visible repair: ADR index drift becomes reproducible and locally checkable. L05 then makes every current specification's judgement age and falsifier visible. [asserted]
4. M05 provides the first end-to-end reconstruction target: delete projections, rebuild one dispatch envelope and compare every referenced digest. A launcher exit code is not acceptance. [measured: recorded local failures] [asserted]

## Explicit deferrals

- Semantic/vector/graph retrieval, a vector or graph database, learned ranking, automatic capability recommendation/reuse and duplicate auto-promotion remain deferred until EXP-101 supplies the frozen evaluation bank and activates the relevant threshold. [cited: ADR-0074]
- Actual fitting, promotion, auto-revert, active-harness mutation and private-derived weight distribution remain outside M06. EXP-104 and EXP-105 must exist in the authorised research register before affected self-improvement branches can activate; this plan does not alias them to another experiment. [measured: build-plan ruling S-08] [asserted]
- No second scheduler, router, role system, orchestrator, state service, product CLI command, network client or third-party dependency is added. [asserted]
- L04-L06 admit only the seventeen current `docs/superpowers/specs/2026-08-22-*.md` files. Repository-wide conversion of every historical document to G/W/S, automatic paraphrase-drift detection and the different-class semantic re-derivation required by EXP-99 remain explicit future work. [asserted]
- Weekly CI surfaces an overdue adversarial review; it does not pretend a mechanical lint performed that review. External citation reachability that cannot be checked reliably without network access is reported `unknown`, not healthy. [asserted]

## Contradictions resolved for execution

- ADR-0074 permits a manual P0 capability path while blocking automatic reuse on EXP-101. M04 therefore selects only an explicit request; the existence of an active head is insufficient to inject it. [cited: ADR-0074]
- ADR-0075 permits recovery-proved local/restorable autonomy while ADR-0078 requires authenticated authority for present capabilities. Existing baseline authority covers only the bounded local envelope; missing or widened authority is a refusal, not inferred consent. [cited: ADR-0075, ADR-0078]
- The action-surface draft places some autonomy reasoning after a receipt, while ADR-0079 makes the pre-action order authoritative. These units use decision/protected authority, then durable intent, then reach, then non-forking receipt/outcome; no future result is copied backwards. [cited: ADR-0079]
- The living-documentation decision abolishes maintained prose, but the current specifications lack a complete review-by contract. L04 and L05 make that debt an exact, bounded migration instead of grandfathering it; L06 activates enforcement only when all seventeen are green. [measured] [asserted]
- A generated check can detect byte drift and literal restatement but cannot establish that a paraphrase remains true. CI therefore reports only its mechanical scope, and EXP-99's different-class audit stays separately required. [cited: ADR-0073]

## Whole-stream completion

Run only after all twelve units and their upstream dependencies have landed. [asserted]

```powershell
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m mypy --strict src/consilient
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/build_requirements.py --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_generated_documents.py --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python .github/scripts/check_adr_trail.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$specs = Get-ChildItem 'docs/superpowers/specs/2026-08-22-*.md' | Sort-Object FullName | ForEach-Object { $_.FullName }
python .github/scripts/check_living_documents.py --check $specs
```

Acceptance is zero failures, zero generated drift, an exact seventeen-specification inventory, no hidden adverse outcome, and no activation of automatic reuse, training, live effects or a closed gate. [asserted]
