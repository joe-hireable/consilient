# 0041. Transports are lossy projections, not coordination authority — and untrusted channels cannot deliver human verdicts

- **Status:** PROPOSED
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (transport channel policy and security boundaries), Gemini 3.7 Flash (mechanism, proof boundaries, and invariant definitions)
- **Extends:** [`0006`](0006-ticket-store-sqlite-plus-git-log.md), [`0007`](0007-cli-only-no-review-surface.md), [`0020`](0020-meetings-and-authority-matrix.md), [`0033`](0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md), [`0035`](0035-user-controlled-visibility.md)
- **Inquiry tier reached:** T1 ground — measured single-identity failure and fabricated participation on external PM/chat tools (EXP-16), plus formal derivation from V0-18 and Whewell's clauses 1 & 3
- **Executable model:** none — whether a shared-credential third-party transport provides non-repudiable human authorship is a binary property ($P=1$ or $P<1$); Gate G4 is not satisfied.

## Context

Joe's operational vision is a unified chat interface — Slack first, followed by a Twilio SMS/voice number and a Google Workspace email endpoint — through which he can supervise and orchestrate work from a mobile device while away from his desk. [asserted]

The Consilient architecture already asserts in passing that Slack and external PM tools are projections rather than authoritative coordination state (V0-13, `v0-draft.md` §2, §4.3). [asserted] However, no ADR formalises the boundary between external transports and internal coordination, nor resolves the critical vulnerability identified during EXP-16: **how the system's human-authority invariant (V0-18) survives a transport Joe does not control**. [asserted]

Two empirical findings make this a structural security and measurement question rather than a UI preference:

1. **Third-party transports collapse multi-agent and human identity into a single token.** EXP-16 measured that every issue and comment on ClickUp and Slack was created under a single OAuth identity (`createdBy: Joe Brown`). [measured] On ClickUp, this laundered an agent-relayed proposal into a fabricated human-participation record in a meeting no human attended. [measured]
2. **$\beta$ is measured against the human verdict oracle.** Under ADR-0002 and ADR-0033 §2, $\beta$ is the rate at which automated verifiers accept an artefact the human rejects. If an untrusted transport allows an agent or automated webhook holding an OAuth token to submit an approval or verdict as "Joe", the ground truth oracle is poisoned, $\beta$ becomes unmeasurable, and the core instrument fails silently. [algebra]

## Decision

We establish four binding rules governing transports and projections:

### 1. Authoritative record versus projected rendering

The append-only JSONL trajectory log (`.harness/log/YYYY-MM-DD.jsonl`) committed to Git is the sole source of truth; SQLite (`.harness/state.db`) is its local deterministic projection (ADR-0006). [asserted]

All external chat, messaging, and ticketing surfaces (Slack, Twilio, Google Workspace, ClickUp, Linear) are **lossy external projections** when outbound, and **untrusted asynchronous input proposals** when inbound. [asserted]
- Outbound messages are rendering views of trajectory events. Retrying, editing, formatting, or deleting messages on external transports cannot rewrite, delete, or reorder events in the trajectory log. [asserted]
- Inbound messages are external events that must be validated and appended to the trajectory log via `events.append()` before they can mutate coordination state or prompt an agent. [asserted]

### 2. Inbound event ingestion and loss tolerance

Third-party transports introduce network latency, message drops, duplication, and out-of-order delivery. [asserted]

The harness handles transport faults as follows:
- **Tolerable faults:**
  - *Network latency and transient drops:* Fully tolerated. The local CLI remains the primary coordination driver; transport polling or webhook ingestion is decoupled from execution loops. [asserted]
  - *Duplication:* Fully tolerated. Inbound messages carry transport deduplication keys (`transport_name`, `channel_id`, `message_id`, `timestamp`) and duplicate deliveries are idempotently ignored. [asserted]
- **Intolerable faults (rejected at boundary):**
  - *Reordering and ambiguous causation:* Inbound commands must carry explicit target task identifiers and reference the active lease epoch (ADR-0020, V0-11). A command referencing an expired epoch or unrecognised task is rejected. [asserted]
  - *Ambient status leakage:* Presence, typing indicators, user read receipts, thread layouts, and emoji reactions are discarded at the transport adapter and **never enter model context** (V0-13). [asserted]

### 3. V0-18 enforcement: Untrusted transports cannot deliver human verdicts

V0-18 establishes that a human decision (`approval`, `gate_lift`, `spend_authorisation`, `verdict`) is valid only when the human principal authored it. [asserted]

On a third-party transport (Slack, SMS, Email), the fact that a payload originates from "Joe's user ID" or "Joe's phone number" is **insufficient evidence of human authorship**, because:
1. Any local agent holding a Slack/Twilio tool token or webhook integration can emit messages attributed to that account. [measured]
2. Transports provide no cryptographic proof of physical human touch or non-repudiable signing. [algebra]

**Therefore, in v0:**
- **No `HUMAN_ONLY` decision event (`verdict`, `approval`, `gate_lift`, `spend_authorisation`) may arrive over an untrusted third-party transport (Slack, Twilio, Email, ClickUp).** [asserted]
- Human verdicts and approvals must be authored directly through the local `consil` CLI on the workstation where the operating system user principal is established. [asserted]
- Third-party transports may deliver informational queries, advisory suggestions, wake-up requests, and draft proposals. Replying or clicking in Slack stages a candidate intent or notifies the local session, but **cannot satisfy V0-18 in the trajectory log**. [asserted]
- *Future exception:* A remote verdict may be admitted only if accompanied by an out-of-band cryptographic hardware attestation (e.g. WebAuthn/FIDO2 or an Ed25519 signature from a secure hardware enclave) whose private key is inaccessible to LLM agent tools. [asserted]

### 4. Adoption of the five-stage progression

We formally adopt the repository's five-stage progression for all cross-boundary communications, replacing any ad-hoc delivery semantics: [asserted]

1. `persisted`: Written and validated in the append-only JSONL trajectory log (`events.append()`).
2. `projected`: Rendered to an external transport, UI, or database table (e.g. Slack thread, CLI output, SQLite row).
3. `adapter-accepted`: Received and acknowledged by the target runtime or connector adapter.
4. `model-included`: Incorporated into the model's active context window or prompt.
5. `effect-evidenced`: Confirmed by observable artefact modification or deterministic verifier outcome.

A message being `projected` to Slack creates zero execution authority; an inbound message is not `model-included` until it is `persisted` and passes admission. [asserted]

## Evidence

- `[measured]` EXP-16 measured that all comments and issues across ClickUp and Slack were created under a single OAuth identity (`createdBy: Joe Brown`), causing an agent-relayed proposal to be recorded as a direct human contribution in a meeting no human joined (`exp16-results.md`).
- `[measured]` EXP-16 Arm C observed that free-form Slack discussions among agents caused echo in the form of dissent-smoothing and provenance loss rather than independent verification (`exp16-results.md`).
- `[measured]` `src/consilient/events.py` enforces V0-18 by asserting `event["actor"] == event["data"]["principal"]` and requiring `via`, but string actor matching cannot prevent forgery when external transports relay messages over shared tokens.
- `[algebra]` An external transport lacking per-event cryptographic signing yields $P(\text{human authored} \mid \text{token} = \text{Joe}) < 1.0$ whenever agents possess tool access to that transport.
- `[cited]` Ao, Gao & Simchi-Levi (2026), *Can LLM Agents Collaborate? A Decision-Theoretic Perspective*, arXiv:2603.26993: multi-agent relay networks without exogenous signals degrade from 90.7% to 22.5% and produce echo.
- `[cited]` Model Context Protocol (2025-06-18), *Authorization Specification*: transport auth governs connection channels, not end-user non-repudiation.
- `[asserted]` The append-only trajectory log is the only substrate preserving Whewell clause 1 (provenance).

## Evidence against

- `[asserted]` **Severely degrades mobile ergonomics:** Joe's explicit goal is to steer runs and approve actions from his phone while travelling. Requiring local CLI invocation for verdicts prevents "one-tap mobile approvals" in Slack, forcing him to VPN/SSH into the host machine or defer verdicts until returning to his desk.
- `[asserted]` **Consumer tools accept Slack approvals without issue:** Commercial orchestrators (e.g. Claude Code Remote Control, Slack approval bots) treat Slack interactive button payloads as valid human approvals. Our restriction is significantly more conservative than standard industry practice.
- `[asserted]` **Single-user threat model may be overstated:** In a single-maintainer setup where Joe is the only human and local agent tools are sandboxed, the risk of an agent deliberately forging a Slack approval to poison $\beta$ could be considered an edge case. However, EXP-16 proved this occurs via structural confusion and single-token attribution rather than malicious intent.
- `[asserted]` What was searched: Reviewed MCP authorization specifications, Slack API interactive messaging documentation, and EXP-16 transcripts; no third-party transport provides out-of-the-box hardware-isolated human non-repudiation.

## Consequences

**Positive** — The human verdict oracle is protected from token-sharing forgery and agent self-approval. $\beta$ remains an untainted measurement of automated verifiers against genuine human judgement. The append-only trajectory log remains the uncompromised source of truth.

**Negative** — Mobile orchestration over Slack/Twilio is restricted to observation, advisory input, and task dispatch; critical gates and verdicts cannot be resolved remotely without local terminal access or future cryptographic signing infrastructure.

**Neutral but load-bearing** — Formally establishes the 5-stage communication model (`persisted`, `projected`, `adapter-accepted`, `model-included`, `effect-evidenced`) across all adapters and transports.

## Enforcement

Invariant **V0-28** (*Transports are lossy projections, and human decisions require authenticated local authorship*):

- Check: `events.validate()` rejects any `HUMAN_ONLY` decision (`verdict`, `approval`, `gate_lift`, `spend_authorisation`) where `via` indicates an untrusted third-party transport (`slack`, `twilio`, `email`, `webhook`) unless accompanied by a verified cryptographic signature.
- Check: Replay-equivalence test asserting that mutating, deleting, or reordering projected transport messages causes zero change to SQLite `state_digest()`.
- Check: Inbound deduplication test proving that re-sending identical transport payloads produces exactly one trajectory event.
- Check: Ambient isolation test proving that transport-level metadata (typing indicators, presence, reactions) cannot be projected into `model-included` context.
- Fails CI: Yes, once transport ingestion code is introduced.
- Added in the same commit as implementation: Required (I1).

## What would overturn this

1. **Hardware-backed mobile signing:** Integration of a secure-enclave cryptographic signing client (e.g. WebAuthn/Passkey on iOS/Android) that signs verdict payloads with a private key inaccessible to Slack bots or LLM agents.
2. **Empirical proof of zero-risk token isolation:** An experiment demonstrating that transport-level permissions can perfectly isolate human-originated webhooks from agent tool invocations without cryptographic signatures (unlikely given hosted PM OAuth architectures).

## Publication candidate?

**No.** This is internal safety and measurement discipline derived from the Whewell provenance and $\beta$ requirements.
