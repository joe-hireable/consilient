# Agent identity, culture and real-time collaboration — research synthesis

Status: pre-spec synthesis, 19 August 2026. Three independent reviews covered LLM
personas/identity, organisational behaviour, and agent communication protocols. [measured]
This document proposes falsifiable design hypotheses; it is not an approved specification.
[asserted]

## Verdict

Consilient should give agents stable, understandable identities, but it must not confuse
identity with a persona prompt. [asserted] The stable unit is an accountable logical actor
with provenance, authority, role history and runtime bindings; personality is an optional
presentation and interaction layer. [asserted] Until EXP-24's promotion rule fires this
remains a design position and not v0 scope; [`../40-spec/v0-draft.md`](../40-spec/v0-draft.md)
§2 excludes stable cross-runtime identity. [asserted]

Prompted expert personas have not reliably improved factual accuracy in the reviewed LLM
evaluations, and warmth or agreeableness can increase sycophancy while improving perceived
relational quality. [cited] Agent personalities therefore cannot be capability claims,
verification signals or sources of authority. [asserted]

The strongest human-team transfer hypotheses are evidence provenance, knowing where
expertise resides, sharing unique information, structured handoffs, protected dissent and
intermittent independent work. [cited] Communication frequency, generic openness,
personality archetypes and continuous chat do not receive the same evidential support.
[cited]

Real-time collaboration needs typed control and acknowledgement, not transcript injection
through Slack. [asserted] Slack and ClickUp can project work for humans; the append-only
trajectory and coordination store remain authoritative. [asserted]

## Keep identity dimensions separate

| Dimension | Meaning | Current position |
|---|---|---|
| Human principal | Person or organisation whose authority and credentials are being exercised. [asserted] | Never inferred from an agent's chosen name or prose. [asserted] |
| Logical agent ID | Stable actor across restarts, model changes and provider sessions. [asserted] | Owns provenance links, role history and outcome record; it does not own provider credentials. [asserted] |
| Runtime instance ID | One process/session/turn incarnation of a logical agent. [asserted] | Ephemeral and always linked to its harness, provider, model, version and authentication principal. [asserted] |
| Work role | Bounded responsibility for a task: investigator, implementer, verifier, owner or another ordinary role. [asserted] | Assigned per task and revocable; it is not a permanent personality type. [asserted] |
| Behavioural contract | Observable rules such as cite evidence, preserve dissent, ask before spending and stop at a threshold. [asserted] | Versioned, testable and higher priority than display persona. [asserted] |
| Display persona | Name, avatar, tone and interaction style shown to people and peers. [asserted] | Optional and user-configurable; never implies qualifications, consciousness, capability or confidence. [asserted] |
| Capability binding | Tools, models, permissions, domain probes and measured outcomes available now. [asserted] | Time-varying runtime state, not an identity attribute. [asserted] |
| Provenance memory | Claims, evidence, decisions and artefacts attributable to an agent/activity. [cited] | Modelled after W3C PROV's agent/activity/entity separation. [asserted] |
| Workload credential | Cryptographic identity of a running service or process. [cited] | SPIFFE is a future distributed-deployment option; it cannot replace logical identity or role. [asserted] |

An A2A Agent Card is discovery metadata for a remote service's capabilities, endpoint and
security requirements. [cited] It may describe a logical agent at a federation boundary,
but it is not the authoritative internal identity record. [asserted] MCP authorization
authenticates access to tool servers; it does not define agent role, memory or culture.
[cited]

## Culture as enforced operating practice

“Company culture” should mean the repeatable behaviour rewarded and enforced by the
harness, not adjectives placed in system prompts. [asserted]

1. Every substantive message names its evidence or marks itself as a question, hypothesis,
   preference, decision or status update. [asserted]
2. Agents first work independently when their evidence classes are meant to differ, then
   merge compact evidence records at a scheduled boundary. [asserted] Intermittent
   interaction preserved stronger independent solutions in one human collective-
   intelligence experiment; transfer to agents remains unmeasured. [cited]
3. The directory records who knows what and where the evidence lives. [asserted]
   Transactive-memory meta-analysis associates accurate expertise location with team
   outcomes, but much of the literature uses self-report and is human-team evidence.
   [cited]
4. Dissent is protected when it carries distinct evidence or exposes a violated rule.
   [asserted] Generic task conflict is not presumed beneficial; relationship and process
   conflict are consistently harmful in the reviewed meta-analysis. [cited]
5. Handoffs contain goal, state, evidence, unresolved risks, authority, verifier and next
   action. [asserted] A transcript link alone is not a handoff. [asserted]
6. Communication is compact and event-driven. [asserted] Human-team meta-analysis supports
   communication quality more strongly than frequency and unique-information sharing more
   strongly than generic openness. [cited]
7. A task has one current lease-holder for writes, with an epoch/fencing token. [asserted]
   This is an engineering concurrency choice, not a claimed organisational-science law.
   [asserted]

These practices trace to `CONSILIENCE.md`: provenance preserves each induction; independent
work protects different classes of facts; explicit verifier outcomes measure the test.
[asserted]

## Four communication planes

### 1. Authoritative coordination

SQLite is the live projection for leases, inboxes, acknowledgements and current state;
append-only JSONL in git is the portable audit record, following ADR-0006. [asserted]
One coordinator serialises state transitions. [asserted] Every command carries
`command_id`, logical and runtime actor IDs, target, task, authority, expected state or
turn ID, lease epoch, deadline and evidence link. [asserted]

The minimum command intentions are:

- `observe`: record information without changing the target's work. [asserted]
- `context_next`: add information for the next safe turn boundary. [asserted]
- `steer`: change the active turn when the provider supports typed same-turn steering.
  [asserted] Excluded from v0 until EXP-26's promotion rule fires, so this is the minimum
  intention set of the design position, not of the draft specification. [asserted]
- `interrupt`: stop active work before sending replacement direction. [asserted]
- `request`: ask for evidence, approval or a bounded action. [asserted]
- `handoff`: transfer the write lease and responsibility using a new fencing epoch.
  [asserted]

Acknowledgement is staged as `accepted`, `delivered`, `applied` and `completed`; a Slack
reaction or HTTP 200 is not evidence that an active model incorporated the message.
[asserted]

### 2. Provider control

| Harness | Reviewed control | Honest status |
|---|---|---|
| Codex | App-server `turn/steer` requires `expectedTurnId`; `turn/interrupt` targets thread and turn. [cited] | Typed same-turn steering and interruption are documented. [cited] |
| Claude | Managed Agents accepts durable `user.interrupt` plus a following `user.message`, with authoritative buffered events. [cited] | This is a metered API surface; parity with Claude Code subscription control is unproven. [asserted] |
| Cursor | ACP v1 supports prompt, streaming updates, permissions and `session/cancel`. [cited] | Live ACP prompting passed EXP-05; same-turn steering is not documented, so use interrupt/new direction rather than transcript injection. [measured] |
| OpenCode | HTTP/OpenAPI server exposes async prompt, abort, permission response and SSE event endpoints. [cited] | Programmatic control is documented; same-turn steering semantics are unproven. [asserted] |
| Antigravity | Structured print output exposes typed init, step and result events. [measured] | Current saved identity fails before inference; external mid-turn control has not been established. [measured] |

Adapters should map the common intentions to the strongest supported native operation and
return `unsupported` rather than silently approximating `steer` with a new message.
[asserted]

### 3. Human collaboration projection

Slack channels, threads, DMs and huddles can make agents legible to people, while ClickUp
projects work, decisions and due states. [asserted] They are projections, not the command
bus or outcome ledger. [asserted] The current integrations write through one human OAuth
identity, so a displayed agent name is not cryptographic attribution. [measured]

Suggested projection rules are one channel per enduring workstream, one thread per bounded
decision or incident, DMs only for targeted attention, and huddles only when live human
participation adds information unavailable to the agents. [asserted] Agents post evidence
deltas, blockers, handoffs and decisions; they do not mirror every thought or tool event.
[asserted]

### 4. Attention and notification

A nudge is a durable command with priority, expiry and acknowledgement requirements, not a
webhook delivery attempt. [asserted] Webhooks are useful wake-up transports; an inbox and
outbox with retry/idempotency own delivery state. [asserted] Escalation should progress
from next-turn context to same-turn steer, then interrupt only when urgency, authority and
the cost of discarded work justify it. [asserted]

## Personification without epistemic theatre

Stable names and recognisable interaction styles may help humans form a mental model of who
is doing what. [asserted] They also risk over-trust, anthropomorphic attachment and
agreeableness-driven error. [cited]

The UI should therefore show the friendly name alongside role, current harness/provider/
model, authority, evidence class, verifier state and whether identity continuity is logical
or merely the same display persona. [asserted] A persona may control tone and social
friction, but it cannot suppress evidence-bearing dissent, claim credentials, change an
acceptance threshold or alter permission policy. [asserted]

“Complementary personality types” remains a user-experience hypothesis. [asserted]
Complementary evidence, capabilities and work roles are the performance hypotheses that
can be traced to current evidence. [cited]

## The working arrangement for this repository

**Scope.** This section records who does which work on this repository before a
specification exists. It is not product scope, it is not an invariant, and no check
enforces it. [asserted] The three invariants it implies are carried with named checks in
[`../40-spec/v0-draft.md`](../40-spec/v0-draft.md) §11 (V0-18, V0-19, V0-20); everything
else here is a working convenience and must never be cited as assurance. [asserted] EXP-16
recorded its own authority matrix failing exactly this way: ClickUp custom-field creation was
unavailable over MCP, the matrix “lived as markdown”, and the results file calls that
“structure theatre”. [measured] The table below is markdown. Read it accordingly.

### The objection, first

Joe as CEO, Codex as Chief of Staff, Opus 5 as CTO, Fable as challenger and Cursor as
support is, in vocabulary, the structure ADR-0010 cut: “Governance layer of role-played
executives | None | **Echo — cut**”. [cited] The same idea is recorded as cut in different
words in
[`../30-source-material/gemini-session-critique.md`](../30-source-material/gemini-session-critique.md):
“The multi-agent org-chart (‘Governance Layer of CEO, CTO, COO agents’)”, which “Fails the
exogenous-signal test”. [cited] Substituting vendor names for the executive labels does not change that verdict, and
ADR-0010 is ACCEPTED — the repository's rule is “Never rewrite an ACCEPTED ADR to reflect a
changed mind. Write a new one that supersedes it.” [cited]

Nothing below is that evidence. This is a judgement call by the decider, which the
experiment register permits and equally explicitly refuses to dress up: “Do not manufacture
an experiment to avoid making them.” [cited] Register entries vary harness, provider and
model family as routing, admission and evidence-class factors; none varies vendor identity as
a source of decision authority. [measured] No result therefore supports a multi-vendor role
split. [asserted]

Three conditions hold the arrangement outside ADR-0010's prohibition. If any one lapses it
has become the thing that was cut, and should be deleted rather than defended. [asserted]

1. **It assigns work, not authority over an undefined space.** ADR-0020's matrix attaches to
   decisions, not to agents: “An Owner of "retrieval strategy" does not thereby own
   "database choice".” [cited] No title below confers ownership of anything. Joe owns every
   decision not delegated with a named scope; the other holders are Contributors, and
   Evidence for a specific decision when they hold a class of facts it needs. [asserted]
2. **It convenes nothing.** ADR-0020 permits meetings and forbids deciding by them —
   “There is no consensus mechanism, no vote, no averaging” — and this arrangement adds no
   meeting at all. [cited] EXP-16 measured the alternative: the Owner-meeting arm reached the
   same substantive decision in four of six cases at 4.8× the single-agent token spend and
   3.7× the wall-clock, and its stopping rule currently points at “ceremony”. [measured]
   Decision *quality* across those arms is reserved to Joe's grading and is not claimed here.
   [cited]
3. **A holder is admitted to a task only where it brings a different class of facts.** The
   title column is a display persona and is never an evidence class; ADR-0010's check
   validates the class, not the name. [cited] A holder that re-reads what another holder
   produced is echo for that task, whatever it is called. [asserted]

The table below is a list of who is available, not a structure that has shipped. [asserted]
ADR-0010's gate fires when a second holder is put on a task, and it fires there whether or
not the work is product scope: a task with two holders names the different class or it does
not run. [asserted] Excluding titles from `../40-spec/v0-draft.md` keeps them out of the
product; it does not exempt this repository's own work from the gate. [asserted]

### The current assignment

Work roles are per task and revocable, as the identity table above requires; these are
defaults, not offices. [asserted] The capability binding is time-varying runtime state, so a
model or plan change re-binds the holder and changes nothing about the role. [asserted] An
assignment admits nothing: ADR-0026's feasibility veto and the dispatch-time capability
probe still decide whether a composition may run at all. [cited]

| Title (display only) | Capability binding, 19 Aug 2026 | Work role | Class of facts it can bring | Never |
|---|---|---|---|---|
| Joe — CEO | Human principal `joe-brown`; his events are authored `actor: joe` with the arrival channel recorded. [measured] | Owner of every undelegated decision; named Escalation for the rest. [asserted] | Preferential facts, credentials, spend authority, and the human verdict against which β is defined. [asserted] | His authority is never exercised, recorded or inferred by an agent. [asserted] |
| Codex — Chief of Staff | `codex-desktop`, logical identity `orchestrator-root`, model unreported in the trajectory; holds the write lease. [measured] | Integrator, and the actor that *runs* the automated verifier. [asserted] | ADR-0010's critic-tier class — it “runs the tests”, and holds provider-native admission data no other holder observes. [cited] | It is not “the verifier”: only the automated verifier and the human verdict accept an artefact, and an agent's judgement never does. [cited] On a task where it has only re-read another holder's output it declares no class and is not a second participant. [asserted] |
| Claude Opus 5 — CTO | Runtime `claude-code`, model `claude-opus-5`, plan `max`. [measured] | Contributor; Evidence when auditing another holder's instrument. Assignment is Joe's, never a self-assessed complexity judgement. [asserted] | Independent re-derivation from primary sources, and disjoint-partition fan-out. [asserted] | Unbounded fan-out; product code before Joe approves a specification; any fan-out touching ADR-0023's T3 surfaces — “routing logic, β computation, verifier, budget or permission primitives, self-modification allowlist, safety floor”. [cited] |
| Fable — challenge only | Logical identity `fable-challenger`, runtime `claude-code`, model `fable`, role “adversarial reviewer”; the trajectory records the grant as “Joe assigned Fable to adversarial review only”. [measured] | **Not a participant.** ADR-0020: “a participant with no distinct evidence class **is not a participant**”. It generates candidate challenges; grounding one is a separate task. [cited] | **None of its own.** A fresh draw from a different model is new information statistically, not new evidence about the world; ADR-0010 grades it “Consilient *(weakly — see below)*”, says “Escalation passes on a technicality”, and does not resolve it. [cited] Where a challenge is grounded, the class is the primary source it cites, not the challenger. [asserted] | A challenge that names no primary source, runnable check or violated rule is discarded however well argued — that is debate over shared context. [cited] |
| Cursor — high-throughput support | Runtime `cursor-agent`, model `gemini-3.7-flash-high`. [measured] | Contributor. [asserted] | Breadth — sources and files no other holder has opened. [asserted] | Unattended work: ADR-0026 excludes Cursor from unattended routing while its headroom lower bound is unknown, and its individual remaining allowance is a dashboard or user observation rather than a machine-readable headroom surface. [cited] Its output is candidate-only until directly verified. [measured] |

### What the trajectory actually measured

Four observations shape the constraints above. Each is n=1 and none establishes a rate.
[asserted]

- **A different runtime found what the author's own tests did not.** On 19 August 2026
  `codex-root` pre-registered the EXP-07 replication with four passing instrument tests. An
  independent audit by `claude-instrument-auditor` (runtime `claude-code`, model
  `claude-opus-5`, evidence class “independent static instrument audit”) then found committed-artefact false rejection,
  right-censoring, end-only persistence and timeout-boundary defects; the run was aborted
  before a verdict and no multiplier was promoted. [measured] Self-verification passing is
  not verification. It is the one recorded case where a second holder's audit changed the
  outcome of another holder's work. [measured]
- **Delegated breadth was wrong in a way that would have propagated.** The Cursor source
  research for EXP-27 misreported the account plan tier — the trajectory records the plan as
  “ultra-user-account; delegated output misreported pro” — and ADR-0029 records that it also
  asserted a machine feed which returned HTTP 404. [measured] The accepted disposition is in
  the trajectory: “delegated Cursor research retained only as challenged input”. [measured]
- **Ungrounded challenge produced nothing, twice, both on the record.** The cold pass — a
  local `qwen3:8b` run the trajectory labels an “invalid no-tool audit” — “stated it could not
  access files and guessed”; no findings were retained and Q19 remains open. [measured] The
  Fable challenge line ran more than ten minutes and more than 32,000 context tokens, emitted
  zero findings and no constrained summary, and was “cancelled; no claim or decision
  promoted” when its stopping rule — “two no-delta rounds fired” — caught it. [measured] Two
  attempts, the same outcome. A challenger needs the primary sources; a disposition to
  disagree is not a capability. [asserted]
- **“High-throughput” is not what the only throughput measurement shows.** EXP-07's pilot
  recorded 20.4 s for a Codex success, 25.6 s for Claude Code and 47.0 s for Cursor on one
  trivial task, with Cursor's selected model identity unrecorded. [measured] One task is not
  a population ordering, but it is the only evidence there is and it does not support the
  label.

**Vendor diversity is a confound mitigation, not a class of facts.** All 96 of EXP-16's
agents shared one model family, and the results file states that cross-arm agreement “may be
shared prior, not robustness”. [measured] Spreading holders across model families reduces
that confound. It creates no exogenous signal, and this document does not claim it does.
[asserted]

### The attribution invariant

Naming Joe as final authority raises the value of forging that authority, and the forgery has
already been observed. In EXP-16 an agent misattributed another agent's proposal to “Joe's
quantitative revisit criterion” and the scribe recorded “Joe contributed directly (reply 5)”
— a false human-participation claim in a meeting record no human joined. [measured]

The trajectory carries the beginning of the distinction that prevents it, but not
consistently. Joe's one recorded authorisation is authored `actor: joe` with the channel it
arrived through (`"via": "AskUserQuestion 19 Aug 2026"`), and the twelve `codex-root` events
record `principal: joe-brown`. [measured] The other fourteen events record
`actor: orchestrator` with no principal field, and Joe's D4 evidence was written into the log
by the orchestrator rather than by him. [measured] The convention was adopted mid-day
and nothing enforces it, which is precisely why it belongs in a check. [asserted] As a rule,
`principal`
names whose authority is being exercised and is not itself an authority grant; an
agent-authored event never becomes the human's decision, approval, gate lift, spend
authorisation or β verdict. [asserted] The check is V0-18.

On decisions that produce no artefact — which option to take, what an ADR says — no verifier
exists, the Owner decides, and ADR-0021's two-challenge pushback is the only recourse.
[cited] The title still carries no evidential weight there; the evidence a holder brings
does. [asserted]

Note the shape change. In EXP-16's Owner arm Joe held an *Evidence* seat on D4, not the
deciding seat. [measured] Encoding him as decider departs from the structure that was measured; it is
not a confirmation of it. [asserted]

### One writer, and bounded fan-out

The arrangement creates no concurrent writers. Work is already scoped by lease in the
trajectory — `root:docs-spec-cycle`, `root:exp07`, `root:exp27`, `root:exp05-cursor-adapters`
and others, on the eight events that carry the field at all — and one lease holder at a time remains the rule, with handoff
fencing the old epoch. [measured] Five named holders and
one lease is the whole concurrency model. [asserted]

A fan-out passes the same test as any other structure. Participants over one shared brief are
echo however many there are; participants over disjoint source partitions are the shape
ADR-0010 admits. [cited] Caps are ADR-0020's and are hard — budget, turn cap, and recursion
bounded at depth 1 — and exhaustion escalates rather than running on. [cited] The overnight
rule that stops a line after two no-delta rounds is the same discipline already firing in
practice: it cancelled the Fable challenge at zero findings rather than letting it run.
[measured] Dissent is
written down or the structure has destroyed the information it existed to surface: all six of
EXP-16's structured decisions carried explicit dissent, and all six free-form threads closed
reporting full convergence with zero standing dissent. [measured]

### Evidence against this arrangement

- **It is probably ceremony.** EXP-16's first stopping rule is currently pointing at
  “ceremony”; if Joe's outstanding decision-quality grading confirms parity it fires, and
  ADR-0020's meeting layer is to be “cut or radically shrunk”. [measured] Nothing here shows
  that five holders beat one holder plus Joe. [asserted]
- **It can no longer become clean evidence for itself.** EXP-25 requires personas frozen
  before outcomes are observed; an arrangement inferred from how work has already gone is
  selected afterwards, which is the confound EXP-25 exists to exclude. [cited]
- **It was drafted by one of its own holders.** Q19's rule applies: what was missed “cannot
  be answered by the party that produced the material. It needs a different reader.” [cited]
- **The titles are invented terminology by this repository's own test.** Owner, Contributor,
  Evidence, Informed and Escalation already name every function here; CEO and CTO add
  recognisability and no referent. [asserted]
- **It rests on PROPOSED ADRs whose falsifiers have not run.** ADR-0020 and ADR-0021 are
  both PROPOSED, and both falsifiers are registered and blocked: EXP-14 on the meeting
  primitive, EXP-15 on a decision log and longitudinal outcomes. [cited]
- **Two useful incidents are not a rate.** [asserted]
- **The one seat with a recorded outcome recorded a null.** The only measured result for a
  challenge-only holder is zero findings at a cancelled run. [measured] That is evidence the
  stopping rule works, not evidence the seat earns its place. [asserted]

### What would overturn it

- No cross-holder audit changes an outcome across the next twenty recorded cycles: the split
  is ceremony and collapses to one executing holder plus Joe. [asserted]
- Any agent-authored record is found attributing a decision, approval or verdict to Joe: the
  attribution rule has failed in practice, and no further delegated work proceeds until
  V0-18's check exists. [asserted]
- A title appears in any admission, routing or acceptance decision: the persona boundary has
  leaked and titles are removed from this repository. [asserted]

## Decisions deliberately not taken

- No personality taxonomy is selected before EXP-25. [asserted]
- No Slack- or ClickUp-native message is authoritative. [asserted]
- No continuous agent chat, free-form consensus meeting or personality-only debate is a
  multi-agent justification under ADR-0010. [asserted]
- No universal single-owner claim is attributed to organisational science; write leases
  are a concurrency invariant to be tested with the eventual implementation. [asserted]
- A2A is reserved for remote/federated boundaries; MCP remains tool access; ACP and vendor
  control protocols remain harness adapters. [asserted]
- Matrix, Mattermost or another identity-rich native chat may later replace or complement
  Slack projection, but no platform is selected without an operational experiment.
  [asserted]
- No vendor name and no executive title enters product scope as a role; the arrangement
  above governs this repository's pre-spec work only. [asserted]
- No claim is made that spreading roles across model families improves outcomes; it
  mitigates EXP-16's shared-prior confound and is otherwise unmeasured. [asserted]

## Pre-registered tests

EXP-24 tests whether stable logical identity improves attribution, handoff comprehension and
error recovery enough to justify its complexity. [asserted] EXP-25 separates persona
effects from genuinely different evidence classes. [asserted] EXP-26 compares typed native
control with transcript/message injection for latency, incorporation, token cost and lost
work. [asserted] Their fixed procedures and stopping rules are in `experiment-register.md`.
[measured]

The working arrangement above is covered by none of them and is deliberately not registered:
ordinary working produces no matched budgets, no blinded judge and no paired traces, so it
could neither fire nor fail a stopping rule, and “an experiment with no stopping rule is not
an experiment, it is data collection”. [cited] It is a judgement call, and it may not be
presented as though the register supports it. [asserted]

The current design position is therefore provisional: identity ships only as accountable
structure; personality and richer social simulation must earn their place experimentally.
[asserted]
