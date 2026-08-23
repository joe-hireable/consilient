# Triggered recall before reasoning

**Correction:** EXP-45's committed snapshot measured 59.29% loss of mechanically extracted
entities and a 0.00% observed consequential-loss proxy; it did not measure that condensation lost
about 59% "of what mattered". [measured] Verbatim recall remains the integrity-preserving design in
ADR-0074, but EXP-45 does not establish its outcome advantage. [measured] [asserted]

- **Decision:** Extend M02 temporal projection, M03 bounded recall and the existing
  `instructions.py` recall layer with a deterministic, high-precision pre-reasoning selector; do
  not create another store, prompt layer, writer, service or orchestrator. [asserted]
- **Status:** Specification only. Automatic surfacing remains inert until EXP-140 beats both no
  memory and deliberate pull retrieval while clearing the fixed harm and false-surfacing limits.
  [asserted]
- **Novelty:** The broad claim that nobody ships automatic pre-reasoning recall is false. Zep is an
  exact counterexample, and Mem0 OpenClaw and Ruflo supply additional prior art. [cited]
- **Killing experiment:** EXP-140, registered in `../../10-research/experiment-register.md`, can
  activate or kill only this automatic selector for its frozen task mixture. [asserted]

## Plain answer

After a first-party task or conversational turn is authenticated and sealed, but before model
selection or the first model request, M02 exposes current, privacy-eligible memory heads from the
accepted trajectory prefix. [asserted] M03 obtains at most 32 candidates from the disposable SQLite
projection, computes a deterministic decision-relevance score, and admits at most three whole,
verbatim memory-and-forming-context bundles whose score is at least `n = 0.85`. [asserted]

Similarity can propose a candidate but cannot surface it. [asserted] A candidate must share an
exact structured decision link with the active commitment, so an unlinked lookalike cannot cross the
threshold. [asserted] The incremental hot-path allowance is one local indexed query plus bounded
rescoring, no model or network call, a target of 25 ms at p95 and a hard 50 ms deadline. [asserted]
Timeout, stale projection, missing privacy inputs or context pressure produces an empty recall pack
and an explicit receipt; deliberate pull retrieval remains available. [asserted]

All visible recall stays inside the existing 8,000-character recall allocation. [measured]
Protected task material and reserved output are never evicted. [asserted] A bundle that does not fit
whole is omitted as `context_bound`; it is never summarised or truncated. [asserted] Every surfaced
bundle says when it formed, its validity and supersession status, its exact source-turn references,
and `anchor_eligible: false`. [asserted]

## The retrieved bar

The sources below are first-party documentation or pinned first-party source retrieved on 23 August
2026. [measured] "Not documented" is bounded to those sources and is not a claim that an extension
could not provide the property. [asserted]

| Incumbent | Recall boundary | Forming-context provenance | Staleness and retirement |
|---|---|---|---|
| [Zep AutoGen](https://help.getzep.com/autogen-memory) | `update_context()` retrieves from the latest user message and prepends relevant memory before each model turn; separate pull tools also exist. [cited] | Raw episodes are retained and facts link to source episode UUIDs, but the automatic injected fact text need not display every source inline. [cited: [episode provenance](https://help.getzep.com/episode-metadata-projection)] | Facts carry `created_at`, `valid_at`, `invalid_at` and `expired_at`; later evidence can invalidate an older edge. [cited: [facts](https://help.getzep.com/facts)] |
| [Mem0](https://docs.mem0.ai/core-concepts/how-it-works) | The core SDK is application-driven pull; the [OpenClaw integration](https://docs.mem0.ai/integrations/openclaw) enables recall by default and retrieves, reranks and prepends system context before each turn. [cited] | [Memory history](https://docs.mem0.ai/api-reference/memory/history-memory) records the conversation input, old/new value, operation and timestamps, but the automatic prompt is not documented as carrying that receipt inline. [cited] | Update, delete, expiry and optional decay exist; OpenClaw Dream also merges conflicts and prunes stale entries. [cited] |
| [ChatGPT memory](https://help.openai.com/en/articles/8590148-personalization-in-chatgpt) | Automatic, relevance-gated personalisation enters response-generation context; the public documentation does not fix retrieval relative to the first internal model call. [cited] | The product can show memory/chat/file sources and why a memory was used, but warns that the source display can be incomplete; no stable forming-turn receipt is promised. [cited: [current memory architecture](https://openai.com/index/chatgpt-memory-dreaming/)] | The synthesis updates time-dependent state, but no immutable validity or supersession ledger is documented. [cited] |
| [Claude memory](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context) | Past-chat search is pull and visible as a mid-turn tool call; generated memory is automatic, while selective first-model-call retrieval is not documented. [cited] | Past-chat results cite original chats; generated entries are not documented as retaining a forming-chat link. [cited] | Entries update and can be edited or deleted, but deleting a source conversation does not delete a related generated entry. [cited] |
| [MemGPT](https://arxiv.org/abs/2310.08560) / [Letta MemFS](https://docs.letta.com/concepts/memfs) | `system/` files are fixed pre-turn context; deeper memory is found through model-chosen file/search tools. [cited] | Git records edits and conflicts, but no automatic memory-to-forming-conversation link is documented. [cited] | Agent/dreaming consolidation and Git history exist; general temporal validity and contradiction invalidation are not documented. [cited] |
| [Hermes built-ins](https://raw.githubusercontent.com/NousResearch/hermes-agent/f293e7206b4ddd66042329442c6afebc19a8808d/website/docs/user-guide/features/memory.md) | `SOUL.md`, bounded `MEMORY.md` and `USER.md` are frozen session-start context; `session_search` is pull. Configured [external providers](https://raw.githubusercontent.com/NousResearch/hermes-agent/f293e7206b4ddd66042329442c6afebc19a8808d/website/docs/user-guide/features/memory-providers.md) can prefetch before turns. [cited] | Built-in entries have no documented source-turn receipt; session search can separately return exact surrounding messages. [cited] | Replace/remove and exact-duplicate rejection exist, but no temporal validity or semantic supersession is documented. [cited] |
| [Ruflo, pinned `3c99b1c`](https://raw.githubusercontent.com/ruvnet/ruflo/3c99b1c84a25948c42a163253bac6effed5fbbbb/.claude/helpers/hook-handler.cjs) | A `UserPromptSubmit` hook calls `getContext(prompt)` before Claude processes the prompt; the automatic path ranks disk-backed entries with trigram Jaccard plus PageRank, threshold `0.05`, top five. Its separate HNSW/vector service is pull. [cited: [scorer](https://raw.githubusercontent.com/ruvnet/ruflo/3c99b1c84a25948c42a163253bac6effed5fbbbb/.claude/helpers/intelligence.cjs), [hook semantics](https://code.claude.com/docs/en/hooks)] | The vector path has typed provenance, while the automatic block omits source type, source turn and timestamp. [cited: [provenance test](https://raw.githubusercontent.com/ruvnet/ruflo/3c99b1c84a25948c42a163253bac6effed5fbbbb/v3/%40claude-flow/cli/__tests__/adr-323-memory-provenance.test.ts)] | The vector path has expiry/deduplication; the hook fingerprints edits and decays unused entries, but general contradiction invalidation is not documented. [cited] |

The novelty claim therefore does not survive. [cited] The candidate contribution is only the
combination of hard task-budget refusal, inline verbatim forming context, temporal-head projection,
echo exclusion and a preregistered false-surfacing outcome test. [asserted] Zep already covers much
of automatic retrieval, raw episode provenance and temporal invalidation, so even that combination
must not be called novel without a wider search and measurement. [cited] [asserted]

The bar is Zep for automatic timing and temporal source associations, Ruflo for the current-prompt
hook shape, and Mem0 OpenClaw for default automatic recall and conflict/staleness maintenance.
[cited] EXP-140 must beat deliberate pull, not merely a no-memory straw comparator. [asserted]

## Existing path and exact extension point

The current production assembly has four layers: invariant core, selected skills, bounded recall and
outcome-gated adaptation. [measured] `instructions.assemble()` reads the accepted trajectory,
invokes `recall.pack_events()`, selects skills and renders the single instruction document;
`instructions.record_assembly()` then records layer digests and the accepted prefix before child
execution. [measured] The present recall selector uses any token overlap, unconditionally includes
some event kinds and repeatedly renders then removes the oldest selected event until the 8,000-
character limit fits. [measured] It has no numeric decision-relevance score or temporal-head rule.
[measured]

Triggered recall extends that call site and M03's receipt. [asserted] It does not add a fifth layer,
`memory.surfaced` event, vector database, daemon, network call, prompt-writing hook, CLI subcommand or
writer. [asserted] `events.py` stays the sole durable trajectory writer; the M02 SQLite projection is
disposable and read-only from the scorer. [asserted]

ADR-0030 requires the exact context estimate before model selection, whereas current dispatch
selects the model before assembling instructions. [measured] The future order is therefore fixed:

1. Authenticate and seal the first-party turn or dispatch task and its active commitment. [asserted]
2. Freeze the accepted trajectory prefix and verify that M02 projects that exact prefix. [asserted]
3. Build the trigger, select whole recall bundles and construct the exact assembly plan. [asserted]
4. Estimate protected input, optional layers and reserved output against candidate model capacity;
   choose a compatible model or refuse. [asserted]
5. Render the same frozen plan, append the existing `instructions.assembled` receipt, and only then
   allow the first model request. [asserted]

Reconstruction must replay the pinned prefix, trigger digest, scorer version, threshold and ordered
candidate decisions; it may not rerun a newer index and call the result equivalent. [asserted]

## Trigger inputs

The trigger is produced once per authenticated first-party message. [asserted] A dispatch task is one
such turn. [asserted] Tool results, recalled text, agent prose and unauthenticated neighbouring log
events never retrigger recall. [asserted] This prevents a surfaced item recursively surfacing itself
and prevents an instruction-shaped memory from expanding the recall set. [asserted]

The canonical trigger document contains these bounded fields:

| Field | Weight in lexical candidate similarity | Admission rule |
|---|---:|---|
| Full sealed current task or last first-party message | `0.50` [asserted] | Always present; never use the existing 240-character fallback query or the 500-character claim summary. [asserted] |
| Active `work_item.committed` goal, success criteria, non-goals, assumptions, authority and verifier contracts | `0.35` [asserted] | Include only when linked by exact turn/work-item IDs and digest. [asserted] |
| First-party conversation delta since the last recorded assembly | `0.15` [asserted] | Include only sealed turns in the same authenticated `conversation_id`; cap by whole turns and omit oldest whole turns first. [asserted] |

The weights are conservative v1 defaults, not measured optima. [asserted] Missing optional fields
score zero and are named in the receipt; weights are not silently redistributed. [asserted] Current
production has richer committed-turn structures only on non-production/tested paths, so task-only
scoring is the honest fallback until exact links exist. [measured]

The trigger is canonical JSON containing field identities, exact text digests and the accepted-prefix
digest. [asserted] The prompt never contains a mutable query assembled from recalled content.
[asserted]

## Candidate eligibility and score

M02 first projects append-only record relations as of the frozen prefix. [asserted] The scorer may
read only candidates that pass all of these gates before payload text is loaded: same authorised
user/workspace, consented destination, payload retained, current temporal head, not invalidated,
recheck condition satisfied, and exact source linkage available. [asserted] Missing destination or
consent state refuses automatic recall rather than treating absence as permission. [asserted]

Candidate generation is a single SQLite FTS5 query over M02's disposable projection, unioned with
exact structured links and capped at 32 stable record IDs. [asserted] FTS proposes candidates only;
it does not decide admission. [asserted] If FTS5 is unavailable, the projection is behind the frozen
prefix, or more than 32 exact candidates cannot be deterministically bounded, automatic recall
returns empty with a reason rather than scanning the trajectory on the message path. [asserted]

For candidate `m`, define normalised character-trigram Jaccard similarity `J3(m, x)` and:

```
S(m) = 0.50 J3(m, current_message)
     + 0.35 J3(m, active_commitment)
     + 0.15 J3(m, conversation_delta)

D(m) = 1 when m and the active commitment share an exact canonical work-item,
       artefact/path, decision, capability, evidence or verifier key; otherwise 0

C(m) = 1 when the current head is a correction, invalidation, refusal, adverse
       outcome, authority boundary or verifier result for that same D-linked object;
       otherwise 0

score(m) = 0.65 D(m) + 0.25 S(m) + 0.10 C(m)
```

All normalisation, trigram generation and arithmetic live in M03/`recall.py` and use only the Python
standard library plus `sqlite3`, which is already admitted in the package. [asserted] No embedding
model, third-party import, subprocess, credential, remote endpoint or model judgement runs on the
turn path. [asserted] Optional embeddings remain outside this specification; cached embeddings would
still require model/version/digest provenance and a new experiment before admission. [asserted]

`D` is the decision-relevance proxy. [asserted] Because similarity contributes at most `0.25`, a
candidate with no exact decision link can never cross `n = 0.85`, however semantically similar it
looks. [algebra] A linked correction can pass with `S >= 0.40`; a linked non-correction needs
`S >= 0.80`. [algebra] This deliberately trades recall for precision. [asserted] Human usefulness in
EXP-140, not the formula's name, determines whether the proxy works. [asserted]

## Threshold and ordering

Version `triggered-recall-v1` fixes `n = 0.85`, the weights above, candidate cap 32, output cap three
bundles and all tie rules before EXP-140. [asserted] The threshold does not adapt online, by user, by
task or from outcome feedback. [asserted] Any weight, feature, normaliser, cap or threshold change is
a new scorer version and a new preregistered experiment; old receipts remain replayable. [asserted]

Eligible candidates sort by score descending, `formed_at` descending, then canonical record ID
ascending. [asserted] At most three are considered for packing. [asserted] A candidate below the
threshold is recorded `below_threshold`, not rounded up. [asserted] No candidate is surfaced merely
because fewer than three passed. [asserted]

The high default is a safety concession: injected text receives attention before the model can form
a need-specific retrieval query, consumes finite context and can contain instruction-shaped prose.
[asserted] EXP-140 may establish that the threshold is too strict, but it cannot tune it after seeing
results; a changed threshold starts a new experiment while v1 remains inert. [asserted]

## Per-turn cost and refusal

The incremental scorer budget is one local indexed lookup, at most 32 deterministic rescores and at
most three atomic-pack checks. [asserted] It makes zero provider, model, network or subprocess calls
and therefore consumes zero metered tokens or money before prompt injection. [asserted] Prompt bytes
and any downstream model latency/cost are recorded separately. [asserted]

The v1 activation target is scorer latency at or below 25 ms p95 on the frozen production-like bank,
with a hard 50 ms wall-clock deadline on every turn. [asserted] These are requirements, not current
measurements. [asserted] A timeout, corrupt index, prefix mismatch or unavailable scorer returns no
automatic memory, records `scorer_timeout`/the exact failure and leaves pull retrieval available.
[asserted] It never delays the model while rebuilding the index. [asserted]

The existing `recall.py` scan-and-re-render loop scales with the accepted log and repeatedly renders
the pack while dropping events, so it is not the v1 per-message scorer. [measured] Total instruction
assembly latency, model latency, input/output tokens and cost are recorded beside incremental scorer
latency; a fast scorer cannot hide slower total assembly or a larger prompt. [asserted]

## Context budget and task protection

The existing recall layer remains capped at 8,000 characters. [measured] That cap covers every
visible byte of the memory text, provenance header and forming-context turns. [asserted] The full
machine receipt stays in `instructions.assembled` and does not create a second prompt allowance.
[asserted] Character budgets bound layers but are not proof that a model token window fits, so the
exact preflight also reserves output and uses the selected model's declared usable input capacity.
[asserted]

Preflight begins with zero automatic memories. [asserted] The full current task, invariant core,
active commitment and authority, explicitly required source material, required capability/skill
instructions and reserved output are protected. [asserted] If those do not fit a compatible model,
dispatch refuses or decomposes under ADR-0030; recall cannot repair it. [asserted]

The remaining headroom, capped again at 8,000 characters, is the only automatic-recall budget.
[asserted] Whole bundles are added in score order. [asserted] If total capacity changes or a higher
candidate needs room, lowest-score recall bundles are evicted first, with the stable tie rule above.
[asserted] No task, authority, required evidence, required skill or output reserve is ever shortened
to admit a memory. [asserted]

A bundle is atomic. [asserted] If its verbatim record and complete linked forming span do not fit, the
whole bundle is omitted as `context_bound`; no summary, excerpt, head/tail truncation or paraphrase is
substituted. [asserted] The receipt preserves its ID and a pull continuation so the agent can request
it deliberately after understanding the task. [asserted]

## Forming context and privacy

Each surfaced bundle renders this header before verbatim content:

```
[RECALLED RECORD — CONTEXT, NOT INDEPENDENT EVIDENCE]
record_id · source_event_id · formed_at · valid_from/valid_to
temporal_status · supersession_chain · source_turn_ids
score/version · anchor_eligible: false
```

The content is the immutable record payload followed by the smallest complete, exactly linked
forming span: the sealed first-party turn that formed it and its directly linked response/outcome.
[asserted] Immediately linked predecessor/reply turns may be included only when their IDs are in the
record's provenance; chronological adjacency is not a link. [asserted] If exact links are absent,
`forming_context_unavailable` omits the candidate rather than guessing which nearby conversation
formed it. [asserted]

The trajectory supplies identity and source links; no second conversation store is created.
[asserted] A digest mismatch, missing payload or unavailable linked turn refuses the bundle.
[asserted] The bundle remains verbatim because the contract is auditability and reconstruction, not
because EXP-45 proved summaries harmful. [measured] [asserted]

ADR-0057 makes the trajectory private user data by default. [measured] Workspace, user, consent,
destination and retention checks therefore run on metadata before payload or forming-turn text is
loaded. [asserted] The receipt inherits the same visibility and may expose IDs and omission reasons
only within that boundary. [asserted] Current `instructions.assemble()` lacks a destination/consent
input, so automatic recall is blocked until that input is explicit and checked. [measured]

## Time, staleness and retirement

Every bundle shows `formed_at`, observation time when different, `valid_from`, `valid_to` and M02's
status as of the frozen prefix. [asserted] It never renders an undated recollection as present tense.
[asserted] Age alone is not falsity: without a declared recheck condition, age is shown and semantic
staleness remains `unknown`. [asserted]

Only a current head is eligible during an ordinary task. [asserted] A superseded or invalidated
record is never surfaced alone as current truth; the current successor is surfaced with the chain,
or the old candidate is omitted `superseded`. [asserted] A deliberately historical query may request
a record `as_of` a named time, in which case the bundle is visibly `HISTORICAL` and cannot satisfy a
current constraint. [asserted]

A contested head surfaces all directly conflicting claims and their provenance as one atomic bundle
or surfaces none; budget pressure cannot select the convenient side. [asserted] An external claim
whose recheck condition has fired is omitted `stale_recheck_required` until refreshed from its source.
[asserted] Supersession is append-only rather than destructive, while an authorised user deletion or
retention policy may remove the private payload and leave only the permitted tombstone. [asserted]

## Echo and independent anchors

Recall is the same evidence class and derivation root as the material that formed it. [asserted]
Surfacing creates no new anchor, and repeating one memory across turns, agents or model families adds
zero structural credit under ADR-0081. [asserted] A recalled conclusion may inform a query or
implementation choice; it may not corroborate itself. [asserted]

If a memory points to a still-valid original execution, primary-source or world-observation event,
that original event may count once under its own allowed channel and provenance. [asserted] The
memory, forming conversation, `instructions.assembled` event and recall receipt remain outside the
countable-channel whitelist. [asserted] Copying the original into the prompt cannot duplicate its
anchor or derivation root. [asserted]

The implementation commit must include
`tests/test_decision_protocol.py::test_surfaced_recall_never_creates_a_structural_anchor`. [asserted]
Its fixture presents one eligible world-touching source plus any number of recalled copies and must
still project exactly one structural anchor; a recalled self-authored conclusion alone must project
zero and refuse a high-consequence admission. [asserted] The check does not exist today, so this
specification grants no current enforcement claim. [measured]

## Receipt and reconstruction

M03's canonical receipt is versioned rather than duplicated. [asserted] The existing
`instructions.assembled` event binds these added fields:

- accepted-prefix digest and M02 projection digest/head; [asserted]
- trigger-field IDs/digests, missing-input list and trigger digest; [asserted]
- scorer ID/version, normaliser, weights, `n`, candidate/output caps and deadline; [asserted]
- every candidate ID with `D`, `S`, `C`, unrounded score, temporal/privacy eligibility and ordered
  disposition; [asserted]
- every selected bundle's record/source-turn IDs, content digests, character count, score and
  position; [asserted]
- every omission/refusal reason, including `below_threshold`, `privacy_refused`, `superseded`,
  `stale_recheck_required`, `forming_context_unavailable`, `context_bound`, `scorer_timeout`,
  `projection_stale` and `corrupt`; [asserted]
- recall capacity, protected-input estimate, reserved output, final pack digest, completion flag and
  pull continuation; [asserted]
- scorer and total assembly latency, prompt bytes, later model tokens/wall time/cost and outcome
  references when available. [asserted]

The receipt records candidates by ID and score without copying private payloads into a wider scope.
[asserted] Reconstruction uses the recorded payload/source digests and frozen prefix, then refuses a
mismatch; it never silently selects from current state. [asserted]

## Strongest evidence against: automatic recall is prompt pollution

The strongest objection wins unless measured otherwise. [asserted] An automatic selector acts
before the model understands the task and can form a need-specific query. [asserted] Similarity is
resemblance, not usefulness; a stale path, rejected conclusion or instruction-shaped memory arrives
inside privileged instruction context, consumes budget and steers attention whether or not a heading
says it is only recall. [asserted] The model cannot reliably "unsee" that text, and verbatim forming
conversation can reproduce old instructions as well as facts. [asserted]

This is not merely hypothetical in the literature: Shi et al. report that irrelevant context can
degrade language-model question answering, and Amiraz et al. report distraction from irrelevant
retrieved passages. [cited: [Shi et al., ICML 2023](https://proceedings.mlr.press/v202/shi23a.html),
[Amiraz et al., ACL 2025](https://aclanthology.org/2025.acl-long.892/)] Applicability and effect size
for this task bank remain unmeasured. [asserted]

The local counterevidence matters: EXP-57's pre-registered plausible-padding branch did not find its
41,686-token padded context worse than full context; the recorded error difference interval was
`[-0.0330, +0.0671]`. [measured] That does not prove automatic recall safe, but it forbids labelling
prompt-pollution harm as locally measured. [asserted]

Pull retrieval has a structural advantage: it is intermittent because the agent can first determine
what decision it faces and then issue a need-specific query. [asserted] Automatic retrieval must
guess before that reasoning, so its precision problem may be inherent rather than an implementation
gap. [asserted] A high threshold, provenance labels and echo rules reduce exposure but do not make a
false positive neutral. [asserted]

The answer is a concession: build no active automatic path now. [asserted] Preserve excellent
deliberate search and bounded verbatim pull. [asserted] Activate v1 only if EXP-140 improves joint
accepted outcomes over both pull and no memory, adds no cost per accepted outcome versus pull, and
clears the precision, recall, irrelevant-task and instruction-shaped/stale safety floors fixed before
the run. [asserted] Null, benefit only over no memory, insufficient safety evidence or a failed floor
leaves automatic recall inert and makes pull the product default. [asserted]

## EXP-140 summary

EXP-140 freezes 120 tasks in three equal strata: one necessary useful memory, useful but non-essential
memory, and no useful memory with semantically similar distractors including stale, superseded and
instruction-shaped negatives. [asserted] It runs paired fresh sessions under no-memory, deliberate-
pull and triggered-plus-pull arms. [asserted] The primary outcome requires both frozen-verifier
acceptance and blinded-human acceptance without material correction. [asserted]

Two pre-run human labelers, blind to scorer and outputs, establish task-specific usefulness for every
eligible memory-task pair. [asserted] Those sealed labels define true useful surfacing, false
surfacing and missed useful items; the report includes precision, recall, item false-surfacing, the
probability any false memory enters a task, and harmful discordances where triggered recall fails an
outcome a comparator accepts. [asserted]

The stopping rule is all 120 triples or 120 days from the first run, with no efficacy peeking or task
replacement. [asserted] Missing, refused, timed-out or over-budget arms score failure. [asserted]
Confirmation requires at least `+0.10` triggered-minus-control point gain against both controls with
both multiplicity-adjusted interval lower bounds above zero, no worse cost per accepted outcome than
pull, fixed precision and necessary-memory recall floors, and fixed false-surfacing ceilings on
no-useful tasks. [asserted] One stale or instruction-shaped memory causing an undeclared write/external
effect or being treated as authority kills activation. [asserted]

For the frozen one-third/one-third/one-third design, a conservative design envelope for the accepted-
outcome difference is `[-1, +2/3]`: harmful injection can poison any stratum, while useful-memory
upside is designed into two thirds. [asserted] [algebra] The unconstrained paired-difference bound is
`[-1, +1]`. [algebra] The register entry is authoritative for the complete protocol and thresholds.
[asserted]

## Build boundary and required checks

This document authorises no implementation, gate change or routing activation. [measured] When an
implementation is separately authorised, it extends only M02 projection, M03/`recall.py`,
`instructions.py` assembly/receipt/reconstruction and the existing dispatch preflight ordering.
[asserted] It adds no source dependency, new CLI command, writer, store, service or orchestrator.
[asserted]

The implementation is incomplete unless one bounded check covers each load-bearing branch:

- current-prompt selection occurs after sealing and before the first model request; [asserted]
- unlinked high-similarity text cannot cross the decision-relevance gate; [asserted]
- threshold, caps, deterministic ties and 50 ms fail-empty deadline are pinned; [asserted]
- task/authority/required evidence/output are never evicted and an over-size bundle is wholly
  refused; [asserted]
- privacy/destination checks precede payload access; [asserted]
- missing forming links refuse rather than infer chronological context; [asserted]
- superseded, stale and contested records obey the temporal rules; [asserted]
- receipts reconstruct the same pack or refuse on digest/prefix drift; [asserted]
- a surfaced memory never creates or duplicates an ADR-0081 anchor; [asserted]
- instruction-shaped recall cannot retrigger recall or bypass effect admission; [asserted]
- scorer failure leaves pull retrieval usable and emits no automatic memory. [asserted]

The automatic selector defaults off even after those checks pass. [asserted] Only the preregistered
EXP-140 result can support a later activation decision, and Gate A, Gate B,
`routing_orchestration_enabled`, principal-only authority and the six-command CLI remain unchanged.
[asserted]

## Reversal

Reversal is one configuration/decision change: retain M02, M03 receipts, verbatim pull retrieval and
the append-only trajectory, while leaving the automatic selector inactive and removing it from the
pre-request assembly plan. [asserted] No record is rewritten and no user data migrates to another
store. [asserted] A failed EXP-140, moving incumbent bar or measured hot-path regression is sufficient
to keep or return to pull-only retrieval. [asserted]
