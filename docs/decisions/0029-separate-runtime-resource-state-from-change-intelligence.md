# 0029. Separate runtime resource state from vendor change intelligence

- **Status:** PROVISIONAL
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Extends:** ADR-0026 and ADR-0028
- **Inquiry tier reached:** T3 measure — first-party feeds and installed CLIs inspected;
  longitudinal recall remains unmeasured
- **Executable model:** none — EXP-27 measures event detection and invariant violations;
  no optimisation model is needed

## Context

Claude Code, Codex and Cursor change their models, command surfaces, quota policies and
service availability independently of Consilience. [measured] On 19 August 2026 their
first-party release and status surfaces were heterogeneous: Claude Code and Codex exposed
machine-readable release feeds, Cursor exposed an HTML changelog, and all three exposed
machine-readable status data. [measured]

The decider reports that included-capacity grants and resets can also change outside the
published schedule. [asserted] A release note or community message cannot prove the
remaining allowance for one authenticated account. [asserted] Conversely, a fresh quota
snapshot does not establish that an installed adapter still matches a changed command or
protocol. [algebra]

ADR-0026 therefore needs two different observations: account/resource state for admission,
and vendor-change intelligence for capability freshness. [asserted] Combining them would
allow a news item to manufacture headroom or a resource counter to conceal a breaking
adapter change. [asserted]

## Decision

Consilience records resource state and vendor-change intelligence as separate event
families with separate authority. [asserted]

### Resource state controls resource admission

Subscription state is keyed by account, provider, plan, native resource bucket and native
window; it retains source, observed time, units, reset time and whether the observation is
authoritative or estimated. [asserted] Multiple concurrent or nested windows remain
separate and are never collapsed into one reset timestamp. [asserted]

A fresh authenticated provider observation may increase or decrease admissible headroom.
[asserted] Local trajectory accounting may only lower the conservative estimate. [asserted]
A contemporaneous user attestation may authorise a bounded, supervised subscription run,
but it is recorded as user authority rather than provider truth and cannot admit unattended
work. [asserted]

### Change intelligence invalidates; it never creates headroom

First-party release feeds, changelogs, documentation and status surfaces may: [asserted]

- invalidate cached capability, protocol, model or accounting-schema knowledge;
  [asserted]
- place an explicitly affected service in a conservative unavailable state while a
  first-party incident is active; [asserted]
- require a dispatch-time version/capability probe before the composition can run again;
  [asserted]
- notify the operator that plan or quota documentation changed and request a fresh
  authenticated resource observation. [asserted]

They may not add allowance, move a reset time, infer an account tier or mark unknown
headroom usable. [asserted] A statement such as “limits increased” invalidates the cached
policy and requests a fresh account observation; it does not credit the ledger. [asserted]

Community channels, including official forums or Discord servers, are discovery hints only.
[asserted] A community event can open a grounding task but cannot change capability,
availability, headroom or budget state until a first-party source or direct probe confirms
it. [asserted]

### Source and event boundary

Each watched harness has a small allowlist of first-party sources and a dispatch-time
handshake. [asserted]

| harness | release/change source | operational source | dispatch authority |
|---|---|---|---|
| Claude Code | official changelog and `anthropics/claude-code` Atom feed. [cited] | Claude Status JSON/RSS. [cited] | installed version/control probe plus authenticated quota observation. [asserted] |
| Codex | official ChatGPT/Codex changelog and `openai/codex` releases Atom feed. [cited] | OpenAI Status JSON/RSS. [cited] | installed app-server capability and rate-limit query. [measured] |
| Cursor | official Cursor changelog HTML. [cited] | Cursor Status JSON/RSS. [cited] | installed CLI/ACP capability probe; individual headroom remains a dashboard/user observation. [measured] |

A change event records source URL and kind, publication and observation times, content
hash or upstream identifier, affected `(domain, harness, provider, model)` fields where
known, the invalidated knowledge class, and the required probe. [asserted] Unknown scope is
retained as unknown and causes a broader re-probe; a model must not invent affected
compositions from announcement prose. [asserted]

Polling cadence is a resource decision, not a truth claim. [asserted] v0 prefers public
machine feeds, conditional requests and provider-native webhooks where documented;
HTML-only pages are polled conservatively. [asserted] Dispatch-time handshakes remain
mandatory because no feed is assumed complete. [asserted]

## Evidence

- `[measured]` Direct requests on 19 August 2026 returned HTTP 200 for the Claude Code
  first-party feed, Codex GitHub releases Atom feed, and the Claude, OpenAI and Cursor
  Status JSON and RSS endpoints.
- `[measured]` Cursor's official changelog returned HTML; the delegated claim that
  `forum.cursor.com/c/changelog.rss` supplied its machine feed was false because that URL
  returned HTTP 404.
- `[measured]` Claude Code 2.1.236 advertises a first-party changelog, remote control and
  subscription status surfaces; Codex app-server exposes `account/rateLimits/read`; Cursor
  2026.08.11 exposes login, version, plan tier and control surfaces but not individual
  remaining allowance.
- `[cited]` Anthropic publishes the Claude Code changelog, release feed and Claude Status
  API; OpenAI publishes the Codex changelog, GitHub releases and OpenAI Status API; Cursor
  publishes its changelog and Cursor Status API.
- `[algebra]` An event with no authenticated account measurement contains no information
  that can increase that account's remaining allowance.
- `[asserted]` Early invalidation can reduce avoidable adapter failures without becoming a
  second admission authority.

## Evidence against

- `[measured]` One delegated primary-source pass misidentified the Cursor account tier and
  asserted two nonexistent/incorrect release surfaces, showing that monitoring output also
  needs verification.
- `[asserted]` A dispatch-time version and capability handshake may catch every relevant
  change cheaply enough that longitudinal feed monitoring earns no v0 complexity.
- `[asserted]` HTML changelogs can change structure without changing product semantics,
  creating re-probe noise.
- `[asserted]` First-party release notes can omit regressions or publish after users receive
  a rollout; a monitor cannot replace direct execution evidence.
- `[asserted]` User attestations enable useful supervised work when no machine quota surface
  exists, but they can be stale by the time a long task starts.

## Consequences

**Positive** — a provider announcement cannot manufacture subscription headroom, while a
real version or outage event can invalidate stale adapter knowledge before another task is
dispatched. [asserted]

**Negative** — source allowlists, content hashes, event deduplication and dispatch probes
add maintenance surfaces for each harness. [asserted]

**Neutral but load-bearing** — ADR-0026 still decides resource feasibility and ADR-0028
still allocates expiring included capacity; this ADR decides when their capability and
policy inputs have become stale. [asserted]

## Enforcement

The pre-spec research check in `experiments/exp27/change_record.py` rejects every change
record that claims permission to mutate headroom. [measured] The product implementation
must retain that check and add source-authority and dispatch-handshake tests in the same
commit as the monitor. [asserted]

- Check: change-intelligence fixtures cannot increase allowance, move reset times or mark
  unknown headroom usable.
- Check: community hints have no direct state-transition authority.
- Check: a relevant release/status event invalidates capability knowledge and forces the
  named probe before dispatch.
- Check: dispatch still fails closed when feeds are unavailable or stale.
- Fails CI: the research invariant check does now; product checks must when implementation
  exists. [measured]
- Added in the same commit as the invariant: yes for the research record; required again
  for product implementation. [measured]

## What would overturn this

EXP-27 decides whether the monitor earns product scope. [asserted]

- Any change event that increases headroom, changes reset state or admits unknown resource
  state fails the design immediately; the monitor becomes notification-only. [asserted]
- If fewer than 95% of canonical first-party release/status events are detected within the
  fixed observation window, feeds remain advisory and dispatch-time probes are the only
  capability safeguard. [asserted]
- If more than 15% of emitted events are duplicates or cause a re-probe with no relevant
  source-state change, remove that source or restrict it to a human digest. [asserted]
- If no monitored event changes a capability or admission decision during 30 days, defer
  the monitor from v0 and retain a dispatch-time handshake plus manual update notices.
  [asserted]

## Publication candidate?

**No.** [asserted] This is operational integration design unless EXP-27 exposes a
generalisable result across substantially more harnesses and release systems. [asserted]
