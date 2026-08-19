# 0022. Safety floor, maximal configurability above it, and an honest account of moderation

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none. Preferential and legal, not empirical.

## Context

`0021` ends with the harness complying after two pushbacks — "within baseline/minimal safety
protocols". This ADR defines that floor.

Joe's specification: safety should be **maximally configurable** but keep a **baseline
minimum** — no assistance with weapons, explosives and equivalents. Such requests may be
escalated for human review and shared with enforcement agencies at moderator discretion,
**only in prevention of loss of life or severe destruction**. Users are trusted beyond that.

## Decision

### 1. The floor — small, fixed, not configurable

A short list of categories the harness will not assist with regardless of configuration:
weapons and explosives, chemical/biological/radiological/nuclear weapon development, and
material that sexually exploits children.

**The floor is deliberately narrow.** It is not a content policy, a taste filter, or a
liability shield. Everything not on it is configurable. A floor that grows becomes a
restriction users route around, at which point it protects nobody.

### 2. Everything above the floor is configurable, defaulting to permissive

Destructive commands, network egress, spend, file scope, autonomy level, tone: all
user-configurable. **Defaults are minimal-restriction, not maximum-caution.** A tool that
asks permission for everything trains users to approve everything, which is worse than
asking rarely and meaning it.

### 3. Moderation — what is actually true

**This section corrects an assumption in the requirement, and the correction matters.**

Consilience is MIT-licensed, local-first, with no telemetry (`0004`, `0006`). Therefore:

| Surface | Is there a moderator? | Can anything be escalated? |
|---|---|---|
| A local install | **No.** No telemetry, no server, nobody watching. | **No.** |
| A fork | **No**, and the floor can be deleted in one commit. | **No.** |
| Community surfaces — repo, issues, skill registry, any hosted service | **Yes** | **Yes** |

So the honest position:

- **The floor prevents casual misuse and states a norm. It does not prevent determined
  misuse, and the project must not imply otherwise.** Anyone can fork and remove it. Claiming
  security we do not have is worse than admitting the limit, and a project whose thesis is
  measuring whether checks can be trusted cannot overstate its own.
- **Escalation applies only where a moderator exists** — community surfaces. A refused
  request on a local install is refused and logged locally. Nothing is transmitted, because
  there is nothing to transmit it to.
- If a hosted service ever exists (`0004`'s deferred commercial path), it carries a separate,
  clearly-stated policy. **Do not write hosted-service policy into a local-first tool's
  documentation** — that is the mismatch this section exists to prevent.

### 4. The disclosure standard, where it applies

On community surfaces, moderator disclosure to authorities is limited to **prevention of
imminent loss of life or severe destruction**. Not convenience, not liability management, not
"seemed suspicious". This is a high bar and should be published as one.

Documentation must say plainly, before use: what is refused, what is logged, what is
retained, what could be disclosed and under what standard. **Users are trusted beyond that
line**, and surveillance-by-default would contradict the local-first design.

## Evidence

- `[asserted]` Permission fatigue: a tool that interrupts constantly trains users to approve
  reflexively, degrading the value of the interruptions that matter. This is why defaults are
  permissive rather than cautious.
- `[cited]` `0019` already establishes the pattern for genuinely consequential actions —
  off by default, explicitly enabled, per-transaction approval. Payments are legally distinct
  and correctly sit outside the "permissive defaults" rule.
- `[asserted]` The fork argument is decisive on enforceability and is not a reason to drop
  the floor: a stated norm shapes the default population's behaviour even when it cannot
  bind the determined minority.

## Evidence against

- **A narrow floor will be criticised as insufficient**, particularly by anyone evaluating
  the project against enterprise or regulatory expectations. The counter is that broad
  content restrictions in a local, forkable tool are theatre — but that argument will not
  satisfy everyone and should not be expected to.
- **The floor is genuinely unenforceable locally.** Everything in section 1 is a norm, not a
  control. Stating this honestly is right and also removes any claim of protection.
- Regulatory exposure is unassessed. The EU AI Act's obligations for general-purpose AI
  systems, and whether a local-first orchestrator carries any, **has not been checked**. This
  belongs in the solicitor pass alongside `0004`.
- "Severe destruction" is undefined and doing real work in a disclosure standard. It needs
  legal drafting, not engineering drafting.

## Consequences

**Positive.** Users get a tool that trusts them, with one small honest boundary. The project
avoids claiming safety properties it cannot deliver.

**Negative.** Some organisations will not adopt a tool with a floor this narrow. Accepted.

**Neutral but load-bearing.** Because the floor is not configurable, it sits **outside the
self-modification allowlist** (`0018`) permanently, alongside budget primitives and the
permission model. Nothing in EXP-12 or EXP-13 bears on it.

## Enforcement

- Check: floor categories are not readable from user configuration. A test asserts no config
  key can disable them.
- Check: the floor list is outside the self-modification allowlist (`0018`).
- Check: refusals are logged locally with reason, and **a test asserts no refusal event is
  transmitted anywhere** from a local install. The privacy guarantee is a test, not a promise.
- Check: documentation states the refusal, logging, retention and disclosure position before
  first use.

## What would overturn this

- Legal advice on EU AI Act or equivalent obligations requiring a different structure.
- A hosted surface existing, which needs its own policy rather than an extension of this one.

## Publication candidate?

No. But *"what a local-first open-source agent can and cannot promise about safety"* is an
honest short post the field could use, and most projects in this space are vaguer about it
than they should be.
