# Memory and capability accretion: durable records, bounded recall, versioned reuse

**Correction:** Consilient already implements deterministic skill selection and a private,
trajectory-backed adapted-instruction layer, but neither is wired into dispatch; the trajectory is
not durability-perfect or retrieval-complete, and EXP-45's committed 20 August snapshot reported
59.29% loss of mechanically extracted entities with 0.00% observed consequential-loss proxy — not
59% loss of what mattered. [measured]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0074 is PROVISIONAL and EXP-101 can kill automatic capability
  reuse. [asserted]
- **Author:** Codex dispatch `20260822T122851-6fe9119269`; the principal supplied the goal, while
  the mechanisms and thresholds below are this dispatch's provisional design. [measured]
- **Scope:** future extensions of the existing event, projection, recall, capability, instruction
  and dispatch paths; this document changes no gate, CLI surface or product code. [asserted]

## 1. Outcome and definitions

The Machine must preserve what it acknowledges, retrieve what a task needs without concealing
omissions, retain useful capabilities without an ever-growing active prompt, and distinguish
parameter training from retrieval. [asserted]

Four terms are deliberately separate: [asserted]

| Term | Operational meaning |
|---|---|
| **Record** | An immutable, provenance-bearing item accepted into private storage. |
| **Recall** | A bounded selection of records for one question, accompanied by a coverage receipt. |
| **Capability** | A versioned tool, skill, instruction, connection or procedure with a bounded interface and verifier contract. |
| **Training** | A data-driven update algorithm mutates persistent learned parameters or state of a named base model; a content-addressed checkpoint or adapter is required before admission. |

“Perfect” is not a claim that every relevant fact can fit in a context window or survive physical
destruction of the only disk. It is an operational contract over an explicitly retained scope:
every acknowledged byte remains addressable and integrity-checkable; every recall says what it
included and omitted; a system with one local copy says so. Semantic recall remains measured, not
promised. [asserted]

## 2. Current substrate and measured gaps

The shortest implementation path extends what exists. A second memory service, capability loader
or orchestrator is outside this specification. [asserted]

| Surface | What exists | Gap this specification closes |
|---|---|---|
| `events.py` | Valid JSONL events retain their payloads; invalid lines remain as rejections. [measured] | General appends have no cross-process lock or `fsync`, and uncaptured transcripts or artefact bodies cannot be recalled. [measured] |
| `projection.py` | SQLite is a disposable projection of valid events, outcomes, usage and rejections. [measured] | It has no record-address or capability projection. [measured] |
| `recall.py` | It scans JSONL, includes exact priority kinds and query-token matches, then drops the oldest selected events until the 8,000-character bound fits. [measured] | It ignores rejected-line information, returns no per-record coverage receipt, and can omit relevant records. [measured] |
| `capabilities.py` | It validates a fail-closed inventory and returns only explicitly requested, available `tool`, `mcp`, `skill`, `plugin` or `connection` entries. [measured] | Entries have no durable identity, version, lifecycle, usage evidence or duplicate control. [measured] |
| `instructions.py` | It selects skills and reconstructs a private adapted layer from trajectory events with reversal support. [measured] | Production dispatch has no caller of its assembly path; this is prompt state, not model training. [measured] |
| `dispatch.py` | It embeds selected capability JSON and a bounded recall pack in the child brief. [measured] | It calls `recall.pack()` directly, retains outcome metadata rather than stdout, stderr or artefact bodies, and does not capture successful capabilities. [measured] |

The committed EXP-45 snapshot covered 1,495 files and 203 sessions but recorded no reproducible
private-corpus digest. A 22 August rerun over 1,725 files and 266 sessions reported 42.35% entity
retention while the 0.00% consequential-loss verdict stayed unchanged. The proxy cannot decide
silent semantic loss or paraphrased retention. Its stopping rule retired a dedicated condensation
memory layer because observed consequential loss did not bite; this design therefore retains
verbatim records and measures the expressly unmeasured retrieval gap instead of reviving
summarisation as an authority. [measured]

## 3. Incumbent bar and intended delta

The external bar has three useful parts. Zep/Graphiti represents facts with provenance and temporal
validity instead of overwriting history; its benchmark numbers are vendor-authored and are not used
as acceptance thresholds here. [cited: Rasmussen et al. (2025), *Zep: A Temporal Knowledge Graph
Architecture for Agent Memory*, arXiv:2501.13956, https://arxiv.org/abs/2501.13956]

MemPalace sets a useful local, deterministic, verbatim-write bar, while a critical analysis
attributes much of its reported retrieval performance to verbatim storage plus ordinary embedding
retrieval and disputes the architectural marketing claim. [cited: Dey and Viradecha (2026),
*Spatial Metaphors for LLM Memory: A Critical Analysis of the MemPalace Architecture*,
arXiv:2604.21284, https://arxiv.org/abs/2604.21284]

Official skill catalogues already provide packaging, discovery and revision histories; cataloguing
alone does not establish that loading a skill improves a task outcome. [cited: Google Agent Skills,
https://github.com/google/skills; NVIDIA Agent Skills, https://github.com/NVIDIA/skills]

The local organisation bar requires one accountable Owner, provenance-bearing artefacts, an
independent execution or source anchor, a matched capable single-owner control and outcomes rather
than agreement or confidence. [measured: `docs/00-context/agentic-organisation-bar-2026-08-22.md`]

Consilient clears this combined bar only if it preserves verbatim source bytes and temporal truth,
reports retrieval loss, and shows that automatic capability reuse improves blinded joint outcomes
without worsening alpha, beta or cost. EXP-101 fixes that comparison before the capability library
exists. [asserted]

**Search record, 22 August 2026:** repository bibliography and ADR search, then web searches for
“MemPalace spatial memory LLM agents”, “Graphiti temporal knowledge graph agent memory”, “AI models
collapse recursively generated data”, “retained real data model collapse”, and official agent-skill
registries. Only primary papers, official repositories and the critical MemPalace analysis were
used; search snippets and disputed vendor point estimates were excluded. [measured]

## 4. Memory contract

### 4.1 Acknowledgement and addressability

`events.py` remains the only authoritative trajectory writer and SQLite remains rebuildable. Large
payloads live in the existing private, gitignored `.harness/` instance boundary as immutable objects
addressed by SHA-256; the event records the digest, byte count, media type, source, consent purpose
and retention class. The object store is payload storage, not a second state log. [asserted]

An ingest is acknowledged only after the object is atomically installed, its bytes and digest are
re-read, and the linking event has passed schema validation and durable, cross-process-serialised
append. A crash before acknowledgement may require retry; a returned success may not name an object
that is absent. [asserted]

Dispatch capture includes the submitted task, assembled instruction/capability identities, stdout,
stderr, produced artefact manifests and verifier outcomes. Secrets, credential values and data
outside the authorised root are rejected or replaced by non-reversible references before capture.
[asserted]

Private-by-default remains binding: no record, object, capability or training example is tracked,
published or sent to another provider merely because it was retained. Sharing needs purpose-specific
consent, and explicit retention expiry or user deletion narrows the “never lost” scope. A deletion
leaves only the minimum non-sensitive tombstone needed to prove it occurred, where policy permits.
[asserted]

Every record also carries its authorised workspace and destination class. Recall and capability
selection filter on both before assembly; a record from another root, a private record not admitted
to the selected harness, or a capability whose source escapes the allowed root is refused and named
in the receipt without exposing its content. [asserted]

### 4.2 Bounded recall without silent loss

Recall continues to return verbatim records. The projection adds exact indexes for stable id,
digest, kind, actor, work item, capability contract, source and valid time; SQLite full-text search
may propose candidates without becoming authority. Semantic or graph retrieval is P2 and is admitted
only if it beats this dependency-free baseline on the frozen bank. [asserted]

Every recall emits a machine-readable receipt containing: query digest; projection/event prefix
digest; scanned-universe count; candidate ids; selected record ids and versions; omitted ids and
reason (`irrelevant`, `superseded`, `permission`, `context_bound` or `corrupt`); bytes used; and a
continuation cursor. Three states remain separate: `scan_complete` says every authorised record in
the frozen event prefix was considered; `context_complete` says every selected candidate fitted;
and `semantic_status` is `measured` only on a frozen gold bank and otherwise `unknown`. Neither of
the first two states may claim semantic completeness. [asserted]

Principal instructions and authority boundaries, active commitments and claims, unresolved verdict
corrections, active work items, and current capability versions are considered before ordinary
recency. Priority does not mean unlimited inclusion: if these exceed the bound, recall sets
`context_complete=false` and provides stable ids or a continuation. [asserted]

### 4.3 Retrieval-loss measurement

Before inspecting any candidate retriever, freeze questions with a gold set `G_q` of atomic record
ids required to answer each question and weights `w(r)` fixed by independent task relevance. For the
records actually returned within the production bound, `R_q`: [asserted]

`L_retrieval = Σ_q Σ_{r∈G_q} w(r)·1[r∉R_q] / Σ_q Σ_{r∈G_q} w(r)`. [algebra]

Also report precision, stale-return rate, contested-fact disclosure, bytes, latency, scan-completion
rate, context-completion rate and **silent critical loss**: the count of gold-bank questions where a
critical record is absent while `semantic_status=measured` reports no loss. An `unknown` or
incomplete status is honest but does not erase raw retrieval loss; missing, corrupt, refused and
timed-out queries retain full loss in the denominator. [asserted]

The frozen bank has a feasible arm, in which every gold set fits the production context bound, and
an overflow arm, in which some do not. It must include relevant records pushed beyond recency,
paraphrased queries, superseded and conflicting facts, rejected JSONL lines and source-changed
claims. “Perfect critical recall” may be reported only for the named feasible arm when every query
has `scan_complete=true`, `context_complete=true`, zero raw critical loss and a reported confidence
interval. Every overflow query must return `context_complete=false` plus a valid continuation. The
label never generalises to questions outside the bank. [asserted]

## 5. Capability contract

### 5.1 Capture and identity

A useful procedure first survives as a **session-scoped candidate**. Capture writes its content to
the private object store and appends an event; capture prevents loss but grants no automatic use.
The candidate remains quarantined until its provenance, interface, permissions, verifier and
outcome evidence validate under ADR-0018. EXP-101 may mark a frozen candidate
`experiment_eligible` inside its isolated runner, but that state is never selectable by product
dispatch and is not an ADR-0018 promotion. [asserted]

The canonical manifest contains: stable `kind:name`; immutable version digest; content digest;
source/object locator; authoring run; licence and privacy class; functional purpose and executable
postcondition; normalised input/output interface; permission, side-effect and trust boundaries;
verifier semantics and version; evidence class; status; `supersedes` or `duplicate_of`; and
expiry/recheck rule. It never contains credential values. [asserted]

Tools and connections keep their existing kinds. Reusable prompts and procedures are represented as
`skill` or adapted `instruction` content rather than inventing a sixth executable capability kind.
[asserted]

### 5.2 Duplicate-sprawl rule

Payload blobs deduplicate globally by content digest. Manifest versions merge only when functional
purpose/postcondition, normalised interface, permission and trust boundaries, verifier semantics,
provenance and licence are equivalent. A shared payload with different provenance or trust remains
a distinct manifest pointing to the same blob. [asserted]

The execution contract key is the canonical digest of `(kind, functional purpose/postcondition,
normalised interface, permission and trust boundaries, verifier semantics)`, not a display name or
verifier identifier. A near-duplicate may split that key only with evidence of a material semantic
difference; adding an optional field or renaming a verifier does not suffice. Otherwise it is an
inactive alias linked by `duplicate_of`. At most one selectable head exists per execution contract
and authorised destination class; history is never erased. [asserted]

Rebuilding an existing contract, selecting an inactive/stale version, selected-but-unused content,
and wrong-capability failures are recorded. Usage count alone cannot promote a candidate; popularity
is not correctness. [asserted]

### 5.3 Selection and outcome

`capabilities.py` is the one selector. `instructions.py` consumes the selected skill/instruction
versions when assembling context, and `dispatch.py` invokes that assembly instead of creating a
second loader. Selection is deterministic from the recorded task, inventory prefix, permission
boundary and active projection. [asserted]

Every attempt records which version was eligible, selected, loaded and actually used, plus outcome,
verifier version, human verdict when present, cost, reversal and capability gap. A product version
becomes `active` only through an ADR-0018-valid promotion event. EXP-101 can confirm the
library-level selection policy for its frozen mixture but promotes no member; explicit user
selection and the archive remain available if the experiment kills automation. [asserted]

## 6. The exact training boundary

**Retrieval ends at any persistent mutation of learned model parameters or state. Training begins
when a data-driven fitting or editing procedure performs that mutation on a named base model,
whether by gradient optimiser, closed-form update or direct weight edit. A content-addressed
checkpoint or adapter is required to admit the result, but a failed checkpoint write is still a
failed training run.** [asserted]

Computing embeddings for records is inference and indexing; fitting or editing the embedding model
is training. Recalled examples, summaries, prompt text, instruction adaptation, skill selection,
context assembly and transient inference caches remain memory or capability reuse. A persistent
learned-state change that is not data-driven is recorded under the broader `model_change` boundary
and receives the same provenance and quarantine controls even when it is not called training.
[asserted]

Loading an existing adapter changes the inference configuration but is not a new training run.
Model weights are a lossy statistical transformation and never replace the retained sources,
examples, licences, adverse outcomes or corrections. [asserted]

Deep study therefore has three independently visible outputs: [asserted]

1. source bytes and provenance enter memory; [asserted]
2. a tested procedure may enter capability quarantine; [asserted]
3. rights-cleared examples may enter a frozen training-candidate dataset, but do not become
   training until a parameter update actually runs. [asserted]

A training run freezes the question, base-model digest, source licences, dataset digest, real versus
synthetic provenance, split, update algorithm/configuration, seed, code revision and executable/human
verifiers before training. It uses source/time-separated held-out data, compares the unchanged base
with the checkpoint under equal inference budgets, retains refusals and missing outcomes, and cannot
use its own verifier verdict as independent truth. [asserted]

Local hardware is the default. A run that fits the RTX 5090 must run locally; this specification
requires no metered API call and grants no hosted spend, publication, model distribution or new
provider authority. [asserted]

## 7. Being wrong, becoming stale and forgetting

Facts are assertions with sources, not truth merely because they were remembered. Each mutable fact
carries observation time, valid-from/valid-to when known, source digest and a recheck condition.
Structural memory points to current source state; the source confirms it. [asserted]

A correction appends `supersedes` or `invalidates`; it never edits the old record. The active
projection returns the chain head with its validity and provenance. Two supported, incompatible
heads produce `contested`, not an arbitrary winner. Historical facts remain retrievable only when
the question asks for history or names their stable id. [asserted]

An expired external claim is stale until refreshed from its source. A historical approval or
credential grant is evidence that authority once existed, never authority for a new action. The
principal-only decisions and first-party ingress requirements remain outside memory, capability
promotion and training. [asserted]

## 8. Requirements and acceptance

| Priority | Requirement | Acceptance |
|---|---|---|
| P0 | Durable, private, content-addressed capture linked from the trajectory. [asserted] | Kill a writer between each ingest step and run concurrent writers; every acknowledged item re-reads by digest, and every failure is explicit. [asserted] |
| P0 | Recall receipts and stable continuation. [asserted] | Every recall distinguishes scan, context and semantic status; semantic status is `unknown` outside a frozen bank, and overflow fixtures provide a continuation. [asserted] |
| P0 | Workspace, destination and consent filtering before context assembly. [asserted] | Cross-root, unconsented-provider and escaping capability-path fixtures fail closed without exposing content. [asserted] |
| P0 | Temporal correction without destructive overwrite. [asserted] | Superseded and contested fixtures return the current state, history and provenance deterministically. [asserted] |
| P0 | Versioned capability manifests with one selectable head per execution contract and destination class. [asserted] | Payload, semantic-collision and trivial-key-evasion fixtures preserve distinct provenance while bounding the selectable view. [asserted] |
| P0 | Training and broader model-change record boundary. [asserted] | Optimiser, closed-form, direct-edit, embedding-fit and failed-checkpoint fixtures cannot bypass provenance or quarantine. [asserted] |
| P1 | Wire existing selection and instruction assembly into dispatch. [asserted] | A recorded dispatch reconstructs the exact recall and capability versions from stable ids; malformed input still fails closed. [asserted] |
| P1 | Frozen retrieval-loss bank and EXP-101 runner. [asserted] | Re-running by recorded seed/digests reproduces denominators, adverse outcomes and arm assignments. [asserted] |
| P2 | Semantic/graph retrieval or automatic selection. [asserted] | Ship only after a matched comparison clears the dependency-free baseline and the applicable safety gate. [asserted] |

No new CLI command is required. Existing scripts and projections are the operator and read surfaces;
implementation must remain stdlib-only inside `src/consilient/`. [asserted]

## 9. Success measures

- Zero acknowledged objects missing or digest-mismatched in crash/concurrency fixtures. [asserted]
- On the feasible retrieval bank, every query is scan/context complete with zero raw critical loss;
  on overflow, every query is explicitly incomplete with a valid continuation. Report all adverse
  queries and denominators. [asserted]
- Zero duplicate selectable heads per execution-contract/destination class and every
  inactive/superseded manifest still addressable. [asserted]
- EXP-101 treatment improves paired joint success by at least 0.10 with interval lower bound above
  zero, no cost increase and alpha/beta one-sided regression bounds at most 0.05 after their fixed
  denominators. [asserted]
- An admitted checkpoint is a training result only when its learned-state update and evaluation
  records reconstruct; failed model changes remain adverse runs, and retrieval-only improvements
  are reported as retrieval. [asserted]

## 10. Evidence against and reversal

The strongest case against accumulated memory is not storage cost. Stale records can crowd fresh
evidence out of a bounded context; a plausible but wrong retrieval can anchor the Owner; duplicate
procedures can create inconsistent behaviour and negative transfer; and recursive training on
model-generated outputs can discard the tails of the original distribution. [asserted] [cited:
Shumailov et al. (2024), *AI models collapse when trained on recursively generated data*, Nature
631, https://doi.org/10.1038/s41586-024-07566-y]

ADR-0030 provisionally prefers compact retrieval because full history may crowd out fresh evidence;
that performance rationale remains asserted rather than measured. [asserted:
`docs/decisions/0030-size-orchestration-by-usable-context-and-measured-outcomes.md`]

The model-collapse result is not a universal ban on synthetic data. Accumulating synthetic data
alongside the original real observations avoided collapse across the tested settings, whereas
replacing the real data did not. [cited: Gerstgrasser et al. (2024), *Is Model Collapse Inevitable?
Breaking the Curse of Recursion by Accumulating Real and Synthetic Data*, arXiv:2404.01413,
https://arxiv.org/abs/2404.01413]

The answer is therefore bounded active context, source-confirmed temporal heads, explicit semantic
unknowns, one selectable capability per execution-contract/destination class, preservation of
real/adverse/corrective data, and held-out outcome comparisons. These controls reduce the risk;
they do not prove semantic perfect recall or improvement from reuse. [asserted]

If EXP-101 kills automatic selection, remove it from the product plan and keep only immutable
capture plus explicit/manual retrieval. If the retrieval bank finds silent critical loss, withdraw
the “perfect recall” label for that bank and repair selection or the receipt before activation. If
training degrades the held-out result or a synthetic-data arm loses tail performance, quarantine
the checkpoint while keeping the source archive. All three reversals preserve history and require
no gate change. [asserted]

## 11. Non-goals and open measurements

- No promise of physical immortality, unlimited context, omniscient relevance or truth by storage.
  [asserted]
- No new vector database, graph database, role, router, orchestrator or CLI command in v0. [asserted]
- No automatic promotion, unattended external-repository use, metered training, publication or
  distribution of private-derived weights. [asserted]
- Whether semantic retrieval beats exact/FTS retrieval, whether local fine-tuning beats retrieval,
  and what replication boundary merits a “perfect” durability label remain empirical questions;
  each must be pre-registered before activation rather than answered by this specification.
  [asserted]
