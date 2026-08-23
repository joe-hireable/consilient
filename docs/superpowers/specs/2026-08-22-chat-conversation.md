# Chat conversation: turn one sentence into committed work

**Correction:** the brief's three zero-byte attempts were not three scope-caused timeouts: one timed
out and two were refused before launch for unknown Cursor headroom; EXP-45 measured 59.29% loss of
mechanically extracted surface entities, not loss of “what mattered”, while its consequential-loss
proxy was 0.00% and silent semantic loss remained unmeasured. [measured: local trajectory census;
`docs/10-research/experiments/exp45/findings-exp45.md`; `docs/10-research/experiment-register.md`]

- **Date:** 2026-08-22. [measured]
- **Status:** proposed specification; the current tree has no conversation or commitment contract.
  [measured]
- **Scope:** intake from one user turn through a frozen commitment and the hand-off to ADR-0068's
  plan; estimate, liveness, recovery and delivery belong to
  `2026-08-22-chat-delivery.md`. [asserted]
- **Non-goals:** a second orchestrator, a seventh `consil` subcommand, a generic workflow editor,
  model-authored principal authority, or a claim that chat is already better than the command line.
  [asserted]

## 1. Decision in one paragraph

Treat chat as an evidence-bound compiler into the existing trajectory, not as a second state store.
Persist the user's sanitised words verbatim, resolve factual and reversible ambiguity without asking,
allow at most one question only for an otherwise-unresolvable principal-only decision, and append one
versioned `work_item.committed` event before planning or execution. ADR-0068 then appends a plan that
cites that commitment, plan streams become plan-bound `work_item.opened` events, and delivery
consumes a read-only `DeliveryIntake` projection of the commitment and plan. Corrections append a
superseding commitment; nothing rewrites the original. [asserted]

## 2. The bar and the narrower claim

The frozen product review names ChatGPT Work as the strongest general delegated-work product and
finds OpenClaw stronger for open, inspectable, always-on architecture and Microsoft Copilot Cowork
stronger in governed Microsoft 365 work. [asserted: ranking in
`docs/00-context/product-bar-2026-08-22.md`, frozen 2026-08-22] The frozen organisation review adds
one accountable Owner, structured persistent artefacts, bounded authority and termination, and
outcome evidence independent of agent confidence. [cited:
`docs/00-context/agentic-organisation-bar-2026-08-22.md`]

The immediate incumbent is narrower and harder to dismiss: the implemented command-line path accepts
an exact task string or file, writes inspectable run artefacts, and is scriptable and replayable.
[measured: `scripts/dispatch.py`] Its weakness is interaction cost: the user must know the command,
construct its arguments and reconstruct state across commands. [asserted]

This intake earns its existence only if, on matched real requests, it reduces user turns or elapsed
user attention without increasing material commitment errors, principal-authority violations,
refusals hidden as success, or failures to resume against the same commitment. [asserted] Until that
comparison is run, chat is a proposed convenience layer, not a demonstrated improvement. [asserted]

The strongest case against this design is therefore that chat inserts an unmeasured semantic compiler
between a technical user and an already explicit control plane; natural language can hide inferred
state that a command exposes. [asserted] The answer is architectural rather than rhetorical: retain
the command line as the automation and recovery control plane, make chat a projection over the same
events, and reject the chat default if the matched comparison above does not improve attention cost
without worsening commitment correctness. [asserted]

## 3. Conversation model

### 3.1 Turn identity

A turn is one final inbound or outbound message. Each turn has a stable `conversation_id`, unique
`turn_id`, `root_request_turn_id`, optional `reply_to_turn_id`, role, authenticated transport status
and receipt time. Streaming deltas are not turns; the sealed visible message is. A question, start
message, exception and final delivery may therefore be separate outbound turns linked to the same
root request. [asserted]

The conversation view is a projection of trajectory events. Closing a window, restarting a harness
or changing a client must not change the authoritative turn sequence. [asserted] A client-provided
history is untrusted input and cannot replace missing trajectory records. [asserted]

### 3.2 Persistence boundary

| Class | Treatment |
|---|---|
| User turns | Preserve sanitised text verbatim, including typos, order, turn identity and transport provenance. A secret span is the sole content exception: replace it before append with a fixed redaction marker and opaque broker reference; store neither the secret nor its hash in the trajectory. [asserted] |
| Visible machine turns | Preserve the final question, commitment/start message, correction, refusal and delivery message verbatim with the event references from which each was projected. [asserted] |
| Commitments and decisions | Preserve every commitment revision, success/non-goal boundary, assumption, autonomous-decision reference, principal-authority reference, dissent, adverse outcome and verifier reference verbatim. [asserted] |
| Tool and harness evidence | Preserve the authoritative artefact or receipt in its existing store and keep its locator, media type, byte count and digest in the trajectory. Conversation need not copy bulky output. [asserted] |
| Derived summaries | They may exist as disposable display caches with source-event identities and an omission count. They cannot author authority, replace user words, change a goal, alter a verifier or become the source of a commitment. [asserted] |
| Ephemera | Discard typing indicators, duplicate acknowledgements, preview deltas, hidden reasoning and presentation caches after the final message is sealed. [asserted] |

`recall.pack()` remains the bounded context mechanism: it retains selected whole event fields verbatim
and drops the oldest whole selected events when the bound is exceeded. [measured: `src/consilient/recall.py`]
The active commitment, all later corrections, unresolved principal decisions, current dissent and
adverse outcomes become always-include classes; direct lookup by `commitment_id` is the fallback when
the bounded pack omits history. [asserted] `instructions.assemble()` records the identities and digest
of the context actually supplied, so a later replay can distinguish missing context from model
behaviour. [measured: `src/consilient/instructions.py`]

EXP-45 supports aggressive pruning of transient surface detail, not permission to summarise away
constraints: its observable consequential-loss proxy missed silent semantic errors and paraphrased
retention by design. [measured: `docs/10-research/experiment-register.md`] That limitation is why
user words, commitments, corrections and authority records remain verbatim. [asserted]

## 4. From one sentence to a commitment

### 4.1 Resolution procedure

For each user turn, the Intake Owner performs these steps in order. [asserted]

1. Authenticate the transport status, remove secret material through the broker, and append the
   sanitised verbatim `conversation.turn`. An append or redaction failure stops intake. [asserted]
2. Recover the live commitment and bounded verbatim context from the trajectory; never ask the user
   to restate machine-held state. [asserted]
3. Resolve factual ambiguity by reading the repository, running a safe check, or retrieving an open
   source. Resolve reversible technical ambiguity by choosing the best supported option and appending
   the existing `decision.autonomous` record with reasoning, falsifier and executable reversal.
   [cited: working principles 8, 10 and 11; ADR-0033]
4. Locate the incumbent bar. Freeze its name, version or retrieval date, source references, bounded
   search digest, the measurable delta and the check that would kill the claim. If no incumbent is
   found, record the search and use the strongest available baseline tagged `[asserted]`; do not
   block work merely because the answer is uncertain. [cited: working principles 9 and 11]
5. Ask only under the rule below. Otherwise freeze the commitment without a confirmation turn.
   [asserted]
6. Append the commitment, let ADR-0068 freeze the minimum verifiable plan against its digest, let the
   task kernel materialise its plan-bound work items, then hand `DeliveryIntake` to the delivery
   stream. No candidate claim, dispatch or external side effect may precede matching commitment,
   plan, work-item and delivery-estimate revision-zero records. [asserted]

### 4.2 Question budget

**Maximum: one question before work starts; the expected count is zero.** [asserted]

A question is permitted only when the missing answer is a decision for which the principal is the
sole valid source—spend, credentials, external exposure, an irreversible action, gate/spec approval,
a final truth verdict, or a genuine preference no evidence settles—and no safe reversible default
can satisfy the request. [measured: `USER_ONLY` and human-decision validation in
`src/consilient/events.py`; asserted extension to this surface]

The one question asks one decision, states the recommended choice and the concrete consequence of no
answer, and never asks for a secret value in chat. It may link to a trusted credential broker.
[asserted] It must not bundle several approvals, ask the user to choose between equally acceptable
technical options, request confirmation of the machine's interpretation, or follow an ambiguous
answer with another question. [asserted]

Zero would force the machine either to fabricate a rare principal-only decision or to refuse without
giving the principal the cheapest resolving action. More than one recreates the interrogation and
approval load this surface exists to remove. [asserted] If the sole question remains unanswered, the
affected commitment is recorded as blocked and no affected claim or side effect starts; independent
read-only preparation may proceed only under a separate safe commitment. [asserted]

An answer counts as principal authority only when an authenticated ingress proves the principal and
the authority record is accepted at the central event validator. [asserted] The current code accepts
human authority only through locally declared CLI provenance and does not authenticate chat; until a
trusted ingress is implemented, chat may draft or request protected decisions but cannot author them.
[measured: `src/consilient/events.py`]

## 5. Commitment artefact

### 5.1 Authoritative location and schema

The authoritative artefact is a new `work_item.committed` event in the existing trajectory, not the
chat transcript, `brief.md`, a task card or a second database. [asserted] It stays in the existing
work-item domain but has a distinct kind because `work_item.opened` is plan/stream-bound under the
task-management contract and legacy dispatch claims must remain replayable. [cited:
`2026-08-22-task-management.md`; ADR-0072]

Pure `events.validate()` enforces event shape, actor class and content digests. Cross-event rules—one
revision per commitment, exact supersession, current authority and revision fencing—run inside
`events.append()` under one per-log lock, against state projected again while that lock is held.
[asserted] The locked writer delegates those domain rules to `work_items.validate_transition()` so
generic `events.append()` and `consil record` cannot bypass them. [measured: central append currently
omits `work_items.validate()` and general transition locking; asserted enforcement]

Each commitment revision contains: [asserted]

| Field | Contract |
|---|---|
| `commitment_id`, `revision`, `supersedes_commitment_digest` | `commitment_id` remains stable for the request; positive `revision` is never reused; revisions after one name the immediately prior digest. [asserted] |
| `commitment_digest` | SHA-256 over canonical UTF-8 JSON for the frozen contract with the digest field omitted. The digest changes on every contract revision. [asserted] |
| `conversation_id`, `source_turn_ids`, `source_turn_digest` | Join the interpretation to ordered verbatim source turns and detect substitution or reordering. [asserted] |
| `request_text`, `goal_text` | The sanitised user request verbatim and the Owner's explicit interpretation; neither silently replaces the other. [asserted] |
| `success_criteria`, `success_digest`, `non_goals` | Ordered, independently checkable acceptance criteria and explicit exclusions. The digest covers both lists. [asserted] |
| `incumbent` | Name, source/version, retrieval date, search digest, evidence tag, measurable delta and killing check. [asserted] |
| `deliverable_contract` | Expected artefact kind, hand-off schema and allowed locator set, without pretending to know the future content digest. [asserted] |
| `accountable`, `composition` | Exactly one Owner; every additional member names one non-overlapping, decision-changing evidence anchor under ADR-0067. [cited: ADR-0067] |
| `assumptions`, `autonomous_decision_refs`, `reserved_decisions` | Every consequential assumption has an evidence tag, falsifier and reversal; protected decisions remain reserved to the principal. [cited: ADR-0033; working principle 11] |
| `authority_ref`, `verifier_contracts` | Frozen authority envelope and ordered verifier `{id, digest, task_family, required_outcome}` records. [asserted] |
| `mutation_scope`, `budget_ref`, `expires_at` | Canonical request-level mutation envelope, reference to the existing budget decision and a timezone-aware upper bound; the plan later assigns exact owned paths. [asserted] |
| `question_count`, `question_turn_id` | Zero or one; the turn reference is absent when the count is zero. [asserted] |

ADR-0067—not `routing.py`—sets the default of one Owner. [measured] `routing.py` computes a ceiling on
candidate attempts against one verifier contract and currently refuses a real-trajectory ceiling
while human beta is unmeasured; `dispatch.py` deliberately does not import it. [measured:
`src/consilient/routing.py`; `scripts/dispatch.py`] This specification neither turns that refusal into
a squad-size claim nor silently wires routing into dispatch. [asserted]

The commitment is appended before decomposition so ADR-0068's plan can cite its digest without a
hash cycle. [cited: ADR-0068] The subsequent plan event supplies `plan_id`, `plan_digest` and its own
event reference; those fields are deliberately not retrofitted into the earlier commitment.
[asserted]

Each stream produced by that plan then becomes a durable `work_item.opened` carrying
`item_schema: "native.v1"`, ADR-0072's required plan and stream fields, and
`{commitment_id, commitment_revision, commitment_digest}`. [asserted] Pure read validation recognises
that schema and the frozen legacy dispatch-claim shape so history remains replayable; after the
native schema is activated, central `events.append()` admits only the discriminated shape and
`scripts/dispatch.py` must migrate in the same commit. [asserted] A legacy event without
`item_schema` is read-only and generic append refuses it; no timestamp heuristic silently turns old
shape into new authority. [asserted] The distinct `work_item.committed` kind therefore avoids a
third overloaded shape rather than pretending the two existing opened shapes are identical.
[asserted]

### 5.2 Tamper evidence, stated narrowly

Every plan, estimate, claim, attempt, verifier receipt, outcome, correction and visible start/done
message cites the exact `commitment_id` and `commitment_digest`. [asserted] The plan record also pins
the trajectory prefix count and `events.prefix_digest()` through the commitment, and the visible
start message shows a short form of the commitment digest. [asserted] An edit, substitution or
reorder at or before the commitment is therefore detectable whenever the plan, start message or
another externally retained anchor survives. [algebra]

This is tamper-evidence against accidental or outcome-aware partial rewriting, not cryptographic
authorship or attacker-proof immutability. [asserted] The current log is unsigned; actor, principal
and transport fields are self-declared strings; a canonical direct writer can evade `bypassed()`;
and a whole-log rewrite can recompute unanchored hashes. [measured: `src/consilient/events.py`]
The commitment anchor alone does not detect a reorder among attempts or outcomes appended after it;
that requires a retained anchor after those events or a predecessor-prefix chain. [algebra]
EXP-53 is READY but unrun and decides the cost and limits of signing. [measured:
`docs/10-research/experiment-register.md`] No surface may call the commitment cryptographically
tamper-proof until a trusted signing or external anchoring scheme is measured and implemented.
[asserted]

### 5.3 What the user sees before execution

Delivery appends estimate revision zero after the plan and before the first claim, as specified by
`2026-08-22-chat-delivery.md`. [asserted] The machine then renders one start message from the sealed
records: the understood goal; success and important non-goals; incumbent and measurable delta;
delivery window; material assumptions; decisions delegated to the machine; principal-reserved
boundaries; and the short commitment digest. [asserted]

That message is a projection, not a confirmation question and not the authoritative store. It may
not introduce a fact absent from the commitment, plan or estimate. [asserted] Work starts
automatically after the required event ordering succeeds. [asserted]

ADR-0068's frozen stream-duration ranges remain scheduling inputs with their evidence and derivation;
they are not a second user promise. [cited: ADR-0068] `delivery.estimate` revision zero cites those
inputs, adds the delivery resource snapshot and becomes the sole rendered delivery window and
revision chain. [cited: ADR-0071; `2026-08-22-chat-delivery.md`] [asserted]

## 6. Delivery interface

The named boundary is `DeliveryIntake`, a read-only projection rather than a new persisted object.
[asserted]

```text
DeliveryIntake = {
  conversation_id, source_turn_ids,
  commitment_id, commitment_revision, commitment_digest,
  commitment_event_ref, prefix_anchor,
  goal_text, success_digest, non_goals,
  deliverable_contract, accountable,
  authority_ref, verifier_contracts, expires_at,
  plan_id, plan_digest, plan_event_ref
}
```

`commitment_event_ref` and `plan_event_ref` each identify the trajectory, line and canonical event
SHA-256; `prefix_anchor` carries the line count and prefix digest through the commitment. [asserted]
Delivery dereferences the immutable records and refuses missing fields or digest mismatches. It
receives no transcript summary and may not reinterpret the goal. [asserted]

The boundary ends when delivery has appended estimate revision zero referring to both digests.
Estimate calculation, quiet progress, checkpoint recovery, reforecasting and the `done` predicate
remain wholly owned by the delivery specification. [asserted]

## 7. Correction mid-flight

A correction is a new user turn, not an edit. If it changes no frozen field, the turn cites the live
commitment and work continues without a new revision. [asserted] Otherwise intake appends a new
`work_item.committed` revision carrying `supersedes_commitment_digest`, a structured contract diff
and one disposition: `pause`, `cancel` or `replan`. [asserted]

From the moment the new revision is accepted: [asserted]

1. no new claim may bind the old digest, and a stale attempt cannot seal completion for it;
   [asserted]
2. affected work stops at the next safe checkpoint and releases its old claim; it can resume only
   after a new plan/work-item revision atomically claims that sealed checkpoint under the new
   digest, while cancellation stops as soon as the harness can do so without corrupting an
   artefact; [asserted]
3. the original turns, old commitment, attempts, costs, artefacts, verifier evidence, dissent and
   adverse outcomes remain append-only and attributable to the old digest; [asserted]
4. a sealed result is reusable only when its consumed inputs, deliverable contract, verifier
   contract and relevant digests are byte-identical under the new revision; affected verification
   runs again; [asserted]
5. `pause` projects the new revision as task state `blocked` with typed cause
   `commitment_paused` and leaves it unclaimable; `cancel` makes it terminal, and `replan` invokes
   ADR-0068 before delivery owns any estimate revision; and [asserted]
6. the user receives one concise delta message with the new short digest, not another confirmation
   loop. [asserted]

Claim acquisition and revision fencing must be one locked state transition at the trajectory write
boundary. The current check-then-append claim path and ticket-only completion projection do not
provide that guarantee.
[measured: `src/consilient/coordination.py`; `src/consilient/work_items.py`]

## 8. Components and reuse

| Existing component | Intake responsibility or required extension |
|---|---|
| `events.py` | Remains the single append writer; pure validation checks shape/digests, while one per-log locked transition checks history before append. [asserted] |
| `work_items.py` | Constructs request-level `committed`, plan-bound `opened` and evidence-bound completion events and supplies domain transition validation to the writer. [asserted] |
| `recall.py` | Adds commitments, corrections, unresolved authority, dissent and adverse outcomes to the protected verbatim set and reports omissions. [asserted] |
| `instructions.py` | Supplies the bounded pack and records its source identities and digest. [asserted] |
| ADR-0068 plan | Decomposes only after commitment and cites its digest. [cited: ADR-0068] |
| `coordination.py` | Atomically fences claims by ticket, revision and commitment digest. [asserted] |
| `scripts/dispatch.py` | Remains the sole orchestrator and receives only sealed, claimable work; it does not parse chat. [asserted] |
| `routing.py` | It does not determine Owner/member count. [measured] It may later bound candidate attempts when its verifier beta contract is measurable. [asserted] |
| `budget.py` | Supplies a necessary reservation reference, not principal authority to spend; dispatch does not currently call it. [measured: `src/consilient/budget.py`; `scripts/dispatch.py`] |

No second coordinator, task database, delivery loop or CLI subcommand is needed. [asserted]

## 9. Data flow and failure handling

```text
authenticated ingress
  -> sanitised conversation.turn
  -> bounded verbatim recall + instruction assembly
  -> one Owner resolves facts/defaults; <= 1 principal-only question
  -> validated work_item.committed request revision
  -> ADR-0068 frozen plan
  -> plan-bound work_item.opened stream revisions
  -> DeliveryIntake
  -> delivery.estimate revision 0
  -> visible start projection
  -> atomic claim -> dispatch -> delivery stream
```

No arrow may be skipped or inferred from a mutable run file. [asserted]

| Failure | Required outcome |
|---|---|
| Unauthenticated or replayed principal answer | Record an untrusted proposal or refusal; never create protected authority. [asserted] |
| Secret cannot be brokered/redacted | Refuse before trajectory append and identify the safe credential route without echoing the value. [asserted] |
| Turn, commitment or anchor append fails | No plan, claim, dispatch or side effect. Preserve the explicit failure if a safe append path remains. [asserted] |
| No incumbent found | Record the bounded search and strongest `[asserted]` baseline; continue. [cited: working principles 9 and 11] |
| Recall bound omits relevant history | Direct lookup by commitment identity; expose omission count; never grant a summary authority. [asserted] |
| Commitment or plan digest mismatches | Quarantine the projection and refuse delivery intake. [asserted] |
| Question unanswered | Block the affected protected action; do not invent consent or ask a second question. [asserted] |
| Correction races an attempt | Revision fencing prevents old-digest closure; retain the stale attempt as an adverse outcome. [asserted] |
| Refusal, timeout, quarantine, missing artefact or stale revision | Record the distinct terminal class; none is projected as success. [asserted] |

## 10. Verification required with implementation

The implementation is incomplete until the smallest checks below fail on the broken behaviour and
pass through the central writer. [asserted]

1. Generic `events.append()` rejects a malformed commitment, duplicate commitment revision, invalid
   supersession, changed digest and unauthorised actor; concurrent appends prove the history check and
   write share one lock, while testing only a work-item helper is insufficient.
   [asserted]
2. `events.read()` accepts a frozen legacy dispatch-claim fixture, while generic append refuses that
   shape after activation and accepts only `item_schema: "native.v1"`; dispatch migrates in the same
   implementation commit. [asserted]
3. Canonical commitment hashing is deterministic across key order and changes for any success,
   non-goal, source-turn or authority edit. [asserted]
4. A retained downstream prefix anchor detects an edit or reorder inside its anchored prefix; the
   test does not claim detection for later events, signing or authorship. [asserted]
5. A property test generates factual, reversible and principal-only ambiguity and proves zero
   questions for the first two, at most one non-bundled question for the last, and no second question
   after an unclear or absent answer. [asserted]
6. Unauthenticated chat, replay and self-declared principal strings cannot author any protected
   decision; secret fixture bytes and their hashes never appear in trajectory or run artefacts.
   [asserted]
7. No claim or dispatch is possible before a valid commitment, ADR-0068 plan, plan-bound work item
   and delivery estimate revision zero cite matching digests. [asserted]
8. Bounded recall and restart preserve verbatim source turns, active commitment, corrections,
   dissent and adverse outcomes; direct lookup recovers an omitted active commitment. [asserted]
9. A correction racing completion fences the old digest, preserves the old attempt and reuses only
   byte-compatible sealed work. [asserted]
10. A contract test freezes every `DeliveryIntake` field against
   `2026-08-22-chat-delivery.md`; delivery refuses a transcript summary in place of references.
   [asserted]
11. End-to-end fixtures cover a one-sentence phone request with typos, a genuine preference, an
    unanswered principal-only decision, a mid-flight goal correction, a refusal, a timeout, a
    quarantine and a missing artefact. [asserted]

The brief's 891-test baseline must remain green, and the same commit that implements each invariant
must add its bypass test at the central chokepoint. [asserted]
