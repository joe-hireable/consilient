# Agent identity, culture and real-time collaboration — research synthesis

Status: pre-spec synthesis, 19 August 2026. Three independent reviews covered LLM
personas/identity, organisational behaviour, and agent communication protocols. [measured]
This document proposes falsifiable design hypotheses; it is not an approved specification.
[asserted]

## Verdict

Consilience should give agents stable, understandable identities, but it must not confuse
identity with a persona prompt. [asserted] The stable unit is an accountable logical actor
with provenance, authority, role history and runtime bindings; personality is an optional
presentation and interaction layer. [asserted]

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
  [asserted]
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

## Pre-registered tests

EXP-24 tests whether stable logical identity improves attribution, handoff comprehension and
error recovery enough to justify its complexity. [asserted] EXP-25 separates persona
effects from genuinely different evidence classes. [asserted] EXP-26 compares typed native
control with transcript/message injection for latency, incorporation, token cost and lost
work. [asserted] Their fixed procedures and stopping rules are in `experiment-register.md`.
[measured]

The current design position is therefore provisional: identity ships only as accountable
structure; personality and richer social simulation must earn their place experimentally.
[asserted]
