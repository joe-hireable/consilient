# Observability and steering: pull the record, write every intervention before it acts

**Correction:** ADR-0071 is PROVISIONAL, not accepted; its checkpoint and fencing mechanism is not
implemented, ADR-0077 has superseded the brief's logarithmic candidate-ceiling formula with the
dependence-robust union bound `n_max = floor(epsilon / beta_upper)`, and the killed claims observed
today remained live until hand-authored terminal events rather than until their actual expiry.
[measured] [algebra]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0083 is PROVISIONAL and EXP-108 is registered but unrun. [measured]
- **Author:** Codex dispatch `20260822T140246-cabc030952`; the principal supplied the product
  requirement, while the mechanism and thresholds below are this dispatch's provisional design.
  [measured]
- **Scope:** the live, pull-only projection and the control semantics for one running squad. This
  specifies no visual design and implements no product behaviour. [asserted]

## 1. Answer first

Consilient will expose one local, live projection of the authoritative trajectory at four
addressable depths: attention, squad, work item and agent. Opening it is always a user pull; while it
is open, local state may refresh in place, but no refresh creates a chat message, notification or
approval. [asserted]

Mutating a run is different from observing it. Redirecting, adding evidence, stopping work or taking
ownership first appends a typed intervention to the trajectory through `events.py`, then reaches the
existing dispatcher and the selected harness's native control capability. The resulting delivery is
labelled `steered`, `operator_controlled` or `cancelled_by_user`; it may never be presented as an
autonomous result. [asserted]

ADR-0071's default remains unchanged: an estimate at the start, no narrative progress messages, an
exception only when its named commitment changes or a principal-only block occurs, and the finished
artefact at the end. The observability surface does not push itself merely because state changed.
[cited: ADR-0071]

## 2. What exists now, and what does not

The specification extends the current substrate instead of treating proposed checkpoints or
controls as present. [measured]

| Boundary | Current artefact | Consequence for this specification |
|---|---|---|
| Record | `events.py` validates and appends the authoritative JSONL; SQLite, recall and dashboard are projections. Its ordinary append has no cross-process serialisation or durability acknowledgement, and the current private trajectory contains malformed concurrent lines. [measured: details withheld under ADR-0057] | Every view is derived from that record. No squad database, transcript index or control ledger is added. Live mutation remains unavailable until the single writer provides serialised, flushed, fsynced admission before an adapter can act. [asserted] |
| Work | `work_items.py` records opened, commented and completed items; a comment carries an evidence class. It has no Owner-transfer or dependency event. [measured] | Reuse the ticket and evidence comment; extend the event vocabulary only for typed intervention and ownership state. [asserted] |
| Claims | `coordination.py` projects run, actor, paths, harness, opening and expiry; completion, a terminal dispatch event or timeout plus 300 seconds releases a claim. Acquisition is not atomic and has no fencing epoch. [measured] | Project those fields honestly. Atomic acquisition and fencing remain implementation prerequisites for displacement. [asserted] |
| Context | Each dispatch preserves `brief.md`, its bounded verbatim recall pack and local stdout/stderr. [measured] | Context inspection can expose those recorded inputs and outputs; it cannot infer hidden state. [asserted] |
| Process control | Dispatch starts the child with `stdin=DEVNULL`, retains no externally addressable process handle and tree-kills only on timeout. [measured] | Attach, redirect, evidence injection, per-run stop and takeover are absent today and must be adapter capabilities, not claims about the current script. [asserted] |
| Reasons and alternatives | `decision.autonomous` can carry reasoning, falsifier and reversal, but dispatch does not emit it; successful route outcomes omit considered alternatives. [measured] | A view says `not recorded` until material decisions and rejected alternatives are appended. It never manufactures a rationale from the final outcome. [asserted] |
| Checkpoints | ADR-0071 specifies sealed checkpoints, but no checkpoint writer, digest chain or fencing implementation exists. [measured] | No current run may be described as resumable. The survival guarantees below activate only with ADR-0071's checks. [asserted] |
| Identity | `events.py` checks declared `actor == principal` and `via == "cli"`; it authenticates neither. [measured] | A declared name is shown as declared. Principal-only control refuses until a trusted first-party ingress verifies authorship. [asserted] |

`consil beta --json` on this worktree reports one human rejection, one false accept, six quarantined
lines and `insufficient_data`; therefore `routing.py` must refuse a measured human-beta ceiling.
[measured: 2026-08-22] The EXP-47 mutation proxy gives one candidate at `epsilon = 0.40` under
ADR-0077's union bound, but it is not human-labelled beta and does not authorise routing. [algebra]
The composition baseline is one Owner; adding another member still requires a different class of
facts and an admissible exposure ceiling, not enthusiasm for a larger squad. [asserted]

## 3. One projection, four depths

The depth is a query over the same immutable event prefix, not four data models. Every entity has a
stable selector (`delivery_id`, `squad_id`, work-item `ticket`, `run_id` and runtime/session identity)
which the originating chat or local command-post client can open directly. The user never has to
find or type a filesystem path. [asserted]

| Depth | Question answered | Required projection |
|---|---|---|
| **Attention** | Does anything need me? [asserted] | `action_required` is true only for an unresolved principal-only decision, a safety stop, an unrecoverable failure or an estimate breach requiring notice. Otherwise show the delivery state, current window, age of the latest valid checkpoint and `No action needed`. No quality adjective or progress percentage is permitted. [asserted] |
| **Squad** | What work exists and why is each member present? [asserted] | Commitment and Owner; work-item/dependency counts; live/diagnosing/recovering/terminal claims; each member's runtime, harness and distinct evidence class; beta ceiling or refusal; budget/quota state; checkpoints; adverse counts; unresolved dissent and asks. A member with no different evidence class is marked echo and inadmissible, not shown as useful agreement. [asserted] |
| **Work item** | What is this stream doing, against which check? [asserted] | Ticket, accountable Owner, responsible runtime, claim paths and epoch, dependencies, immutable success contract and verifier, exact recorded current action, evidence references, material decisions, considered and disposed alternatives, checkpoints, tool outcomes, spend/usage, blockers, refusals and quarantine. Missing fields read `not recorded`. [asserted] |
| **Agent** | What context and evidence is this process acting on? [asserted] | Recorded instruction layers and digests, commitment and plan revisions, bounded verbatim recall, declared tools/skills/model/session, current safe-boundary action, recent authoritative tool/result events, evidence sources, material decision records and rejected alternatives. Adapter-native transcript attachment is optional and labelled unavailable when absent. [asserted] |

“Reasoning” means the rationale, evidence references, falsifier and alternatives deliberately written
to the trajectory. It does not promise hidden chain-of-thought, reconstruct a model's private
scratchpad or treat fluent post-hoc prose as evidence. [asserted]

Opening a depth starts a local read subscription over the trajectory prefix and clock-based claim
projection. Closing it ends the subscription. Updates inside that user-opened surface are pull
continuations, not pushed conversation turns; ordinary checkpoint advancement still emits no chat
message. [asserted]

## 4. The incumbent bar and the surviving delta

The prototype's claim that all four incumbents are merely a chat column plus “thinking theatre” is
too broad. All four expose live progress and mid-run steering, while Nous Hermes Agent and Gemini
Spark already expose structured multi-task control surfaces. [cited: primary sources below,
retrieved 2026-08-22]

| Incumbent | What it exposes now | What the reviewed source does not demonstrate |
|---|---|---|
| **Claude Cowork** | Per-step progress, visible approach, mid-task course correction and cross-device redirection; Dispatch adds child-task states and inspectable sessions. [cited: [Cowork guide](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork), [Dispatch guide](https://claude.com/docs/cowork/guide/dispatch), retrieved 2026-08-22] | A joined view of measured verifier error, distinct evidence classes and authenticated principal authorship was not documented in the reviewed pages. [measured search boundary] |
| **ChatGPT Work** | Progress review, questions, direction changes, approvals and cross-device continuation. [cited: [operational guide](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex), [launch record](https://openai.com/index/chatgpt-for-your-most-ambitious-work/), retrieved 2026-08-22] | The reviewed pages publish no hash-linked causal replay or verifier false-accept projection for a running squad. [measured search boundary] |
| **Nous Hermes Agent** | Active-turn queue/interrupt/steer, tool updates, SSE run events, stop and approval endpoints, a durable multi-profile Kanban and an explicit Command Center. [cited: [messaging](https://hermes-agent.nousresearch.com/docs/user-guide/messaging), [API server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), [Kanban](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban), [desktop](https://hermes-agent.nousresearch.com/docs/user-guide/desktop), retrieved 2026-08-22] | Generic “command post”, timelines, live control and run history are therefore not novel. The reviewed pages do not document calibrated verifier beta or principal-bound event authorship. [measured search boundary] |
| **Gemini Spark** | A task view and fleet-level task list; completed/current/planned steps, files touched, changed instructions, schedule control and browser takeover/return. [cited: [task guide](https://support.google.com/gemini/answer/17094507?hl=en), [task management](https://support.google.com/gemini/answer/17094196?hl=en), retrieved 2026-08-22] | The reviewed pages do not document distinct-class admission, verifier beta or an append-only intervention lineage. [measured search boundary] |

The surviving delta is not another timeline, Kanban board, transcript stream or stop button. It is the
join: each displayed claim resolves to the append-only trajectory; each added role names a different
class of facts; candidate exposure shows measured beta or refusal; every steer is write-ahead and
changes the autonomy label; and principal-only authority requires authenticated first-party
authorship. [asserted]

The search covered the four named products' current operating, task-control and run-control pages,
plus the frozen product-bar and prototype documents. It did not establish a global absence across
private implementations or every product. [measured search boundary]

## 5. What “jump into a running agent process” means

Every operation targets a stable `run_id` plus its live claim epoch. If the harness adapter does not
declare the necessary native capability, the operation refuses and says which capability is absent;
the dispatcher must not emulate an attach by guessing from a PID. [asserted]

| Operation | Mechanical meaning | Work already in flight | What survives |
|---|---|---|---|
| **Attach** | Subscribe read-only to adapter-native run events or transcript output. No bytes enter the agent context. [asserted] | The current tool and slice continue without pause. [asserted] | All state is unchanged; only an optional local `observability.pull` event records that the depth was opened. [asserted] |
| **Read context** | Render the recorded commitment, instruction assembly, recall pack, tools, evidence, decisions and latest checkpoint for the target run. [asserted] | Execution continues. A read never changes a deadline, claim or verifier. [asserted] | The event prefix and immutable input artefacts; absent live context remains explicitly unavailable. [asserted] |
| **Redirect** | Append `intervention.requested(action=redirect)` and deliver the new instruction at the next controller-proven safe boundary. If live injection is unavailable, interrupt and resume the same candidate from the last valid checkpoint under a higher epoch. [asserted] | A running irreversible tool is allowed to reach its safe result unless a safety stop requires tree kill. New work cannot start under the old instruction revision. Incompatible unsealed output is quarantined from admission. [asserted] | Every earlier sealed checkpoint, completed tool result, transcript and old instruction revision. Compatible checkpoints may be reused; the delivery estimate and plan revise when the commitment changed. [asserted] |
| **Add evidence** | Append a source reference with evidence class, provenance, retrieval date, licence where applicable and digest, then inject its reference at the next safe boundary. [asserted] | The current operation completes; the agent must acknowledge the evidence revision before another operation starts. Decision-changing evidence follows the redirect/replan path. [asserted] | The original and added evidence, their order and every conclusion produced before the addition. The final lineage is `steered`. [asserted] |
| **Stop / kill** | A controller outside the child writes the intent, revokes the write epoch, kills the process tree, verifies termination, appends the terminal `dispatch.outcome` and closes the claim. It never waits for the killed child to report its own death. [asserted] | No automatic restart. A later continue is a new run of the same candidate from the last valid checkpoint. [asserted] | Trajectory, immutable tool results, transcript and the last sealed checkpoint survive. The current unsealed slice is diagnostic only and may be lost; the record says so. [asserted] |
| **Take over as Owner** | After authenticated first-party authorship, stop the agent at a safe boundary, seal or quarantine its current slice, append the Owner transfer and issue a higher claim epoch to the principal's local session. [asserted] | Unchanged independent streams may continue; the transferred stream cannot complete autonomously. Returning it to an agent is another explicit transfer and epoch. [asserted] | The whole event/checkpoint chain and all attributable artefacts. Subsequent work is `operator_controlled`, never autonomous. [asserted] |

An adapter does not get to declare its own work safe. A controller-verifiable safe boundary exists
only when the trajectory projects no unmatched side-effecting tool/effect start for the target
`(run_id, claim_epoch)`, the controller's child/lease registry contains no live mutation-capable
handle for that epoch, and the last reusable state is a digest-verified sealed checkpoint or a
terminal tool result. Any unknown or untracked effect makes the predicate false. A lying-adapter
fixture which reports `safe` while one effect or child remains live must be refused before injection
or transfer. These effect events, handles and checkpoints do not exist end to end today, so redirect,
evidence injection and takeover are unavailable rather than approximately safe. [asserted]

The current killed-claim defect fixes at the control boundary. Today a killed run can remain projected
live until expiry unless somebody supplies a terminal event. Four killed runs across two recovery
incidents received hand-authored terminal outcomes; at least one later dispatch recorded a claim-
overlap refusal before the first pair was closed. [measured: private local trajectory, identities and
paths withheld under ADR-0057] The controller which owns the stop must also own terminal recording,
claim release and epoch revocation. A terminal event from an unauthorised actor or with no matching
live intervention must not release another run's claim. [asserted]

ADR-0071's checkpoint promise is conditional. Before its manifest, digest, atomic ref and fencing
checks ship, redirect-resume and takeover-resume must refuse rather than claim that a working directory
or transcript is a checkpoint. [asserted]

## 6. Steering is a recorded input, not an invisible edit

Two typed events are the minimum control record. They are appended through `events.py`; adapters and
renderers never write the JSONL directly. [asserted]

| Event | Required content |
|---|---|
| `intervention.requested` | `intervention_id`; delivery/squad/ticket/run/session/claim-epoch targets; action; actor; ingress; authentication status and mechanism; request time; instruction revision or evidence references; requested safe boundary; latest valid checkpoint digest; causation id. [asserted] |
| `intervention.outcome` | The same id; applied/refused/failed status; applied time and boundary; pre/post instruction, plan, claim and checkpoint identities; terminal dispatch reference when any; preserved and quarantined artefact references; Owner before/after; reason. [asserted] |

`work_item.owner_changed` is the work projection of an applied takeover; ordinary evidence continues
to use `work_item.comment` with an evidence class and immutable source references. Material choices
and rejected alternatives use the existing `decision.autonomous` contract rather than a new
reasoning store. [asserted]

The controller order is fixed: verify the ingress to the extent currently possible; durably admit the
request through a cross-process serialised append; validate target and claim epoch; prove the safe-
boundary predicate above or revoke the epoch; preserve or quarantine the in-flight slice; invoke the
adapter; durably append the outcome and any terminal dispatch; then reproject. A failed or
unacknowledged request append refuses the mutation. An adapter call with no earlier matching durable
request is a bypass and fails the check. [asserted]

Remote messages remain untrusted proposals until a trusted local ingress accepts them. The current
check `actor == principal` plus `via == "cli"` is declared provenance, not authentication; it cannot
authorise Owner takeover, a verdict, spend, gate lift, publication or any other principal-only act.
[measured] A steer containing the word “approved” is still a steer and carries no approval. [asserted]

The delivered lineage is deterministic: [asserted]

- `autonomous` — no mutating intervention occurred after the immutable intake commitment; a read-only
  pull does not change this label. [asserted]
- `steered` — redirect or evidence addition changed the run, including a stop followed by agent
  continuation. The final outcome lists every intervention id. [asserted]
- `operator_controlled` — the principal took ownership of any required stream. [asserted]
- `cancelled_by_user` — the user stopped the delivery and did not continue it. [asserted]

An outcome may never select the least involved label supplied by an agent. The projector derives it
from the immutable intervention lineage. [asserted]

## 7. Watching never becomes approving

**Rule:** a view, attach, dwell time, cursor action, closed view, unread notification or absence of
intervention is observational only. None may satisfy a pending ask, approve an artefact, author a
verdict, lift a gate, reserve spend, transfer ownership or permit an otherwise forbidden effect.
[asserted]

If `observability.pull` is recorded for local instrumentation, its schema rejects
`human_decision`, `human_verdict`, approval, consent, authority, owner and effect fields. It records
only target depth, stable selector, local time and experiment arm when applicable. [asserted]

The enforcing property test inserts arbitrary pull events, view durations and periods of silence
into a fixed trajectory. The projected decisions, authority grants, accepted attempts, actuation
handles, Owner and gate state must remain byte-identical. A second test proves that every permitted
effect cites an explicit typed authority event and that a timeout on an unanswered ask blocks or
expires; it never accepts. [asserted]

This is deliberately stronger than “the agent should not assume approval”. It bans the source-to-sink
path by event kind and makes the projection invariant to observation. [asserted]

## 8. Privacy boundary

ADR-0057 makes the trajectory the user's private data: untracked, unpublished and shared only by
explicit consent. The consent/export path is not implemented, so this surface is same-machine only.
[cited: ADR-0057]

That forbids: [asserted]

- a hosted dashboard, remote transcript URL, cloud synchronisation, analytics beacon, crash upload,
  support bundle, external font/script, public share link or automatic clipboard/export containing
  trajectory material; [asserted]
- sending raw events, agent context, transcripts, evidence or local paths through the originating
  remote chat transport merely because the chat asked to render a depth; [asserted]
- exposing another user's, workspace's or tenant's trajectory through a selector, cache or stale
  local session; [asserted]
- treating redaction as consent. A redacted trajectory remains the user's data. [asserted]

The local client may render the projection itself from `.harness`; a remote client with no trusted
local renderer reports the capability unavailable. Existing `.harness/dashboard.html` may remain an
offline rendering of the same projector, but it is not an export and stays ignored by Git. [asserted]

EXP-108 does not create an implicit research exception. Before recruitment it must freeze an
explicit-consent, participant-initiated derived-data export which excludes raw events, run ids,
instructions, paths, transcripts, evidence and artefact content; blinded reviewers receive only the
final task artefact. Raw trajectories stay on their owners' machines. The register fixes the allowed
derived fields, withdrawal and deletion rules; until that mechanism exists, the experiment is
blocked. [asserted]

## 9. Reuse boundary and required checks

No second orchestrator, seventh CLI subcommand, dependency, gate change or routing enablement is
introduced. `routing_orchestration_enabled` stays `false`. [asserted]

| Existing component | Smallest required extension |
|---|---|
| `events.py` | Validate intervention, pull and Owner-transfer events; remain the only append writer. [asserted] |
| `dashboard.py` / chat projector | Produce one typed depth projection; render named absences; never decide. [asserted] |
| `coordination.py` | Add atomic claim acquisition, epoch fencing and authorised terminal release. [asserted] |
| `work_items.py` | Project Owner transfer, dependencies and current instruction/evidence revisions. [asserted] |
| `scripts/dispatch.py` | Keep orchestration ownership; expose adapter-native inspect/inject/stop capabilities and an external stop controller. [asserted] |
| `recall.py` | Continue bounded verbatim context; never become state, summary authority or checkpoint storage. [asserted] |
| `routing.py` / `budget.py` | Expose measured ceiling/refusal and existing budget state; neither becomes active because it is displayed. [asserted] |
| `instructions.py` | Describe the portable intervention contract; prompts do not enforce it. [asserted] |

Implementation is incomplete until the smallest runnable checks prove: [asserted]

1. one event prefix produces deterministic attention/squad/work-item/agent projections, and missing
   source fields render unavailable rather than inferred; [asserted]
2. checkpoint and pull events create no conversation message under quiet delivery; [asserted]
3. arbitrary observation and silence leave every authority and acceptance projection identical;
   [asserted]
4. concurrent large appends from independent processes remain valid canonical events in causal order,
   and a failed flush/fsync prevents the mocked adapter mutation; [asserted]
5. no adapter mutation occurs without an earlier durable matching `intervention.requested`, and every
   request receives one terminal outcome; [asserted]
6. a lying adapter cannot declare a boundary safe while the event projection or controller registry
   contains a live side-effecting effect, child or lease; [asserted]
7. mutating intervention deterministically prevents an `autonomous` outcome label; [asserted]
8. stop and takeover revoke the old epoch, prevent stale writes, record a terminal outcome and release
   the claim without a manual event; [asserted]
9. spoofed principal, actor, channel and replay inputs cannot exercise Owner or principal-only
   authority; while authentication is absent those operations refuse; [asserted]
10. the surface opens no network path, loads no remote resource, emits no telemetry and tracks no
   trajectory artefact; and [asserted]
11. every admitted squad member exposes a distinct evidence class, while absent human beta renders a
   routing refusal rather than a fabricated candidate count. [asserted]

## 10. Evidence against: the strongest case for showing nothing

The strongest alternative is a finished-result product with no live surface at all. A strategic user
who can watch acquires a standing invitation to supervise; supervision becomes vigilance, every
rough intermediate state becomes salient, and the cheap availability of redirect and stop can turn
reversible uncertainty into repeated intervention. The glass box can manufacture the micromanager it
claims to free. [asserted]

The evidence is not friendly to explanation surfaces. Bansal et al. found explanations could raise
acceptance without raising discrimination; Schemmer et al. measured reliance moving without a
corresponding self-reliance improvement; and the vigilance literature describes monitoring as hard,
stressful work. [cited: sources verified in `docs/10-research/bibliography.md` and analysed in
ADR-0035] A live rationale may therefore look like diligence while merely performing diligence, and
an attentive user may intervene more often without improving the artefact. [asserted]

Every named incumbent streams or exposes progress because progress makes latency legible and gives
users control. Vendor convergence establishes the interaction bar; it does not establish that
watching improves independently judged outcomes. [cited] [asserted] The more honest product may show
nothing until it can present the result, verifier evidence, adverse outcomes and cost together.
[asserted]

This objection is conceded as a live possibility, not answered by taste. Pull-only access removes
forced attention but does not remove invitation or self-selection. EXP-108 therefore compares the
same quiet delivery with the live surface unavailable versus available-but-unpushed. If availability
raises intervention or review burden, or lowers accepted outcomes beyond its fixed thresholds, live
inspection is removed and only post-hoc replay survives. [asserted]

## 11. Validation and plain delta

EXP-108 is registered in `docs/10-research/experiment-register.md` with fixed arms, adverse-outcome
retention, stopping rule and largest plausible effect. It gates the live default and any trust claim;
it does not block recording the schema or building a local inert projector. [measured]

The plain answer would be a task list, progress stream, transcript viewer and stop button. [asserted]
The delta is that the list is a pure projection of one append-only record, “more agents” requires a
different class of facts and an admissible beta ceiling, every mutation is write-ahead and fenced,
watching has no authority semantics, and a steered outcome cannot masquerade as autonomous.
[asserted]
