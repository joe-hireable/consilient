# 0042. Admit connectors by zero-inference capability probing, credential isolation, and fail-closed spend caps

- **Status:** **ACCEPTED 20 August 2026.** Accepted by Joe Brown, 20 August 2026, in the orchestration chat: *"I accept all the recommendations."* Recorded in the trajectory at `.harness/log/2026-08-20.jsonl` as a `decision.*` event authored by the principal.
  The spend half is further specified by ADR-0044: OpenRouter is the only permitted
  metered vendor, and weekly and monthly caps are a required capability.
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (credential, monetary spend, and network egress policy), Gemini 3.7 Flash (admission predicates, handshake mechanics, and failure invariants)
- **Extends:** [`0019`](0019-paid-capability-acquisition.md), [`0026`](0026-admit-only-budget-and-hardware-feasible-backends.md), [`0027`](0027-compose-domain-harness-provider-and-model.md), [`0029`](0029-separate-runtime-resource-state-from-change-intelligence.md), [`0033`](0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md)
- **Inquiry tier reached:** T3 measure — installed connectors inspected locally, zero-inference dispatch handshake validated in EXP-27, and 63 production budget-overrun incidents analysed from Khan (arXiv:2606.04056)
- **Executable model:** none — admission is a Boolean veto predicate over security, budget, and capability constraints; Gate G4 is not satisfied.

## Context

Joe's environment contains connectors and MCP plugins for diverse external services: Lucid, Supabase, Gmail, Slack, Linear, ClickUp, Figma, Twilio, and others. [measured] As measured during the 20 August design assessment, most of these connectors are currently unauthenticated or unverified locally. [measured]

ADR-0026 establishes admission criteria for coding backends (headroom, budget, hardware fit), while ADR-0029 separates resource state from change intelligence. [asserted] However, external service connectors introduce distinct risks:
1. **Unbounded spend and API consumption:** Connectors for paid services (e.g. Twilio SMS/voice, Supabase compute, paid APIs) can incur financial cost on every invocation. ADR-0019 is UNRESOLVED and binding: standing spend authorisation is forbidden, and per-transaction approval is required. [asserted]
2. **Credential and data leakage:** Connectors can access sensitive personal or business data (Gmail, Slack) or transmit private repository code (`hireable-3.0`, `jobboard-v2`) off the machine. [asserted]
3. **Silent failure and unobservable state:** External APIs enforce proprietary rate limits and brittle schemas. In EXP-16, ClickUp's MCP connector failed under rate limits while Linear silently coerced unsupported statuses without raising an error. [measured]

We must establish the exact criteria under which an external connector is admitted into an agent's feasible action set. [asserted]

## Decision

We establish four binding rules governing connector admission:

### 1. Admission criteria extending ADR-0026 and ADR-0029

For a connector $c$, task $x$, and dispatch time $t$, admission requires:

```text
admissible_connector(c, x, t) =
    authenticated(c, t)
    ∧ (rate_limit_headroom_known(c, t) ∨ bounded_task(x))
    ∧ spend_authorised(c, x)
    ∧ credential_scoped(c)
    ∧ (local_only(c) ∨ egress_authorised(c, x))
```

- **Authentication is mandatory:** An installed or configured connector whose authentication cannot be actively verified at dispatch is strictly ineligible. [asserted]
- **Unknown rate-limit headroom disqualifies unbounded work:** Extending the ADR-0026 update, a connector with unknown rate-limit headroom is excluded from unbounded unattended tasks. It is admissible for bounded unattended work only if all five ADR-0026 conditions hold (fixed input, hard turn cap, read-only/scratch writes, zero partial-state loss on mid-task failure, confirmed auth). [asserted]
- **Change intelligence invalidates; it never admits:** Per ADR-0029, a vendor announcement, status page, or documentation update can invalidate cached connector tools or force a re-probe; it can **never** mark an unauthenticated connector authenticated or credit rate-limit headroom. [asserted]

### 2. Dispatch-time capability probing (EXP-27 handshake)

Before any task dispatch, the harness executes a **zero-inference, zero-token capability probe** across candidate connectors, adopting the pattern proven in EXP-27 (`handshake.py`): [asserted]

1. Probe binary/plugin presence, protocol version, and authentication readiness without executing model prompts or consuming metered API credits. [measured]
2. Enumerate available tools, input schemas, and declared permission scopes. [asserted]
3. Validate against `validate_capability_record`: any capability that is unobservable, missing, or unauthenticated is recorded as `unobservable` and rejected from the active toolset. [measured]

### 3. What a connector may never do without Joe (ADR-0019 & ADR-0033 §2)

A connector is strictly forbidden from executing the following actions autonomously:

1. **Spend money:** ADR-0019 binds all connector operations. Any connector capable of incurring financial cost (e.g. Twilio SMS transmission, metered API calls, cloud infrastructure provisioning) requires all four ADR-0019 conditions: (1) user specifically enabled it, (2) user agreed to legal terms, (3) per-transaction approval naming provider, purpose, and exact amount, (4) enforced budget cap. Standing spend authorisation is banned. [asserted]
2. **Hold or manage ungranted credentials:** Connectors may not autonomously create accounts, accept Terms of Service on Joe's behalf, or store payment card details. Credentials must be held in the OS keychain or passed as scoped environment variables. [asserted]
3. **Transmit data outside the machine:** Sending emails (Gmail), posting to public channels (Slack), modifying external databases (Supabase), or calling remote endpoints is blocked unless explicitly authorised in the task contract. Private repository contents (`hireable-3.0`, `jobboard-v2`) and `.env` secrets may **never** be transmitted off the machine. [asserted]

### 4. Failure closed

The admission boundary fails closed across all connector operations: [asserted]
- An unobservable capability is treated as unknown, and unknown is never usable. [asserted]
- Unauthenticated connectors installed on the machine (e.g. Lucid, Figma, Supabase) remain purely structural references and cannot be passed to an agent. [asserted]
- If a connector's authentication expires, its rate limit is exceeded, or its schema drifts mid-execution, the connector is immediately quarantined and the task escalates rather than retrying blindly. [asserted]

## Evidence

- `[measured]` Probed installed connectors on 20 August 2026: Figma, Lucid, and Claude Design connectors are unauthenticated locally (`docs/20-design/design-capability-assessment-2026-08-20.md`).
- `[measured]` EXP-27 (`handshake.py`) proved zero-inference capability probing across installed harnesses and validated fail-closed rejection (`validate_capability_record`) when capabilities are unobservable or unauthenticated (`findings-exp27.md`).
- `[measured]` EXP-16 measured that ClickUp's MCP connector hit `RATE_LIMIT_EXCEEDED` and failed schema modification loudly, while Linear silently failed status transitions without error (`exp16-results.md`).
- `[cited]` Khan (2026), *Token Budgets: An Empirical Catalog of 63 LLM-Agent Budget-Overrun Incidents*, arXiv:2606.04056: 63 production incidents across 21 subprojects demonstrate that retry loops and ad-hoc connector wrappers cause catastrophic budget overruns; hard structural caps are required.
- `[cited]` Model Context Protocol (2025-06-18), *Authorization Specification*: client-server authorization requires explicit resource-owner scoping.
- `[algebra]` An agent with unconstrained access to a paid API connector executing an un-capped retry loop produces unbounded financial loss: $\lim_{n \to \infty} \sum_{i=1}^n \text{cost}_i = \infty$.

## Evidence against

- `[asserted]` **High friction for standard developer tooling:** Joe has installed many connectors (Lucid, Supabase, Gmail, Figma, Twilio). Failing closed on unauthenticated connectors renders them entirely inert until Joe manually configures and authenticates each one, reducing out-of-the-box utility.
- `[asserted]` **Per-transaction spend destroys unattended external automations:** Requiring per-transaction approval for every paid connector call (such as a 2p Twilio SMS notification or a metered search API) halts overnight unattended runs and forces user interruptions for trivial sums.
- `[asserted]` **Probing overhead:** Running dispatch-time schema and auth probes for dozens of MCP connectors adds startup latency to every agent dispatch (though measured at $<1.3\text{ s}$ in EXP-27).
- `[asserted]` What was searched: Evaluated MCP tool-discovery protocols and examined Khan's catalogue of overrun mechanisms; no standard tool framework provides safe default spending boundaries without structural isolation.

## Consequences

**Positive** — Connectors cannot autonomously spend money, leak private codebase assets, or crash tasks due to stale/unauthenticated credentials. Budget overruns via tool retry loops are structurally prevented.

**Negative** — Unauthenticated connectors cannot be used opportunistically by models. Every new integration requires an authenticated credential check and an explicit blast-radius declaration. Unattended tasks cannot perform paid external operations.

**Neutral but load-bearing** — Connectors are admitted through the same central admission chokepoint as coding backends (ADR-0026), unifying the feasibility boundary across models and tools.

## Enforcement

Invariant **V0-29** (*Connector admission fails closed on unauthenticated, unobservable, or unbudgeted capabilities*):

- Check: `handshake.probe_connectors()` runs before dispatch with zero model inference tokens and marks unauthenticated connectors (Lucid, Figma, Supabase) as ineligible.
- Check: Boundary test asserts that attempting to invoke an unauthenticated or unknown connector raises an admission refusal before tool execution.
- Check: Spend-gate test proves that any connector action incurring a monetary cost is blocked unless linked to an explicit `spend_authorisation` event satisfying all four ADR-0019 conditions.
- Check: Egress filter test asserts that connector payloads containing paths or content from private repositories (`../hireable-3.0`, `../jobboard-v2`) or `.env` files are rejected before network transmission.
- Check: Rate-limit test asserts that an unbounded task dispatched to a connector with unknown headroom is rejected at admission.
- Fails CI: Yes, once connector integration code is implemented.
- Added in the same commit as implementation: Required (I1).

## What would overturn this

1. **Provider-enforced hardware budget enclaves:** A connector framework providing hardware-enforced cryptographic spend limits at the operating system or kernel level, eliminating the need for application-level per-transaction human approval.
2. **Joe relaxing ADR-0019:** An explicit user policy decision authorising standing monetary caps for specific trusted connectors (e.g. a £5.00/day standing allowance for Twilio SMS notifications).

## Publication candidate?

**No.** This is operational security and resource engineering.
