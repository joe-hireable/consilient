# 0078. Admit only gated typed effects and record every effect

**Corrections:** `events.py` is presently a cooperative append path, not an enforced durable single
writer, and existing message/browser adapters can act before appending. The brief's exposure claim
is also false below the applicable beta bound: the candidate ceiling becomes zero, not one.
Non-file effect provenance is incomplete and unestimated human beta authorises no live exposure
today. [measured] [algebra]

- **Status:** PROVISIONAL — EXP-35 and EXP-59 can kill the action-boundary mechanism
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (unconstrained-output direction, recorded in the source context); Codex
  dispatch `20260822T123850-9436cb33b5` (provisional mechanism)
- **Inquiry tier reached:** T1 ground; T3 registered as EXP-35 and EXP-59, not run for this decision
- **Executable model:** none — this decision defines exact admission and record invariants; the
  unknowns are crash and reversal error rates measured by the registered experiments

**PROPOSED alignment amendment (2026-08-23; principal acceptance required):** an admitted gate
carries exactly one `grant_kind`. `controller_baseline.local_restorable.v1` is mechanically
verified by an earlier `decision.autonomous` bound to one passing ADR-0075 recovery proof and scoped
to one single-use bounded local/restorable operation inside the committed workspace/authority
envelope. It grants no network, credential, spend, external exposure or protected reach.
`principal_authority` requires an exact authenticated first-party V0-18 event for scope widening or
any protected class. [cited: ADR-0075] [asserted]

## Context

The principal specified a general chief of staff whose output is unconstrained, with law as the
minimum boundary and user configuration above it. Giving an agent ambient filesystem, process,
network, message, money, publication, credential and external-system reach would turn that semantic
direction into unrestricted actuation. [measured: `docs/00-context/the-machine-2026-08-22.md`]

The current implementation cannot support that interpretation. Capability selection is inserted
into prompt text while child harnesses default to permission-bypass flags; SMTP, Twilio and browser
effects occur before their events are appended; event validation defines no generic effect contract;
and ordinary append is neither process-serialised nor fsynced. [measured:
`src/consilient/capabilities.py`, `scripts/dispatch.py`, `src/consilient/harness.py`,
`src/consilient_connectors/outbound.py`, `src/consilient_connectors/computer_use.py`,
`src/consilient/events.py`]

ADR-0075 already owns the canonical effect manifest, per-invocation reversibility proof, closed
escalation set and decision/reversal records. This decision must supply the action facts and effect
receipts that boundary consumes without creating a competing classifier or principal path.
[measured] [asserted]

The effect boundary adds no reviewer. One Owner and at most one candidate remain the structural
default, but unestimated human-labelled beta authorises no live candidate acceptance; provider
receipts, state readbacks and independent sensors contribute different execution facts without
becoming voters. Principal verdict, approval, consent, gate-lift and spend authority remain
first-party only. [algebra] [asserted: ADR-0067, ADR-0077, V0-18]

## Decision

Consilient will keep semantic generation and local drafting unconstrained by a second content
policy, but it will admit material actuation only through the existing capability inventory extended
with an explicit gate, ADR-0075's canonical typed effect manifest, and a single least-privilege
adapter boundary. That boundary will durably append `effect.intent` before reach and a linked
`effect.receipt` after refusal, success, failure or an unresolved observation. ADR-0075 supplies the
final disposition before a live handle is exposed. A present but unpermitted capability remains
visible as `available: true, gate.state: gated`; it is denied the actual handle, route, credential or
provider operation. [asserted]

The closed effect enum is `file.change`, `data.read`, `process.run`, `system.change`,
`network.call`, `external.change`, `message.send`, `content.publish`, `money.commit`,
`obligation.commit`, `authority.change` and `physical.actuate`. `message.send` includes local
terminal/UI/audio presentation to a person, not only remote transport; an unrendered artefact alone
is a local draft. Composite actions receive every matching value and inherit the least recoverable
atom and every protected residual. Raw shell and browser capabilities are wildcard-effect
capabilities unless an outer sandbox proves the classes they cannot reach. [asserted]

Class-level recovery is deliberately limited: file, system, external-state and access-control
changes are conditionally reversible only with immutable preimages plus fresh full-scope readback;
data reads, process execution and network calls cannot be unrun; messages, publications, committed
money, effective legal obligations and physical actions permit compensation but not restoration;
credential disclosure cannot be undone. The complete inverse and proof requirements are normative in
`docs/superpowers/specs/2026-08-22-action-surface.md`. ADR-0075 alone decides whether a concrete
invocation passes its executed recovery test. [asserted]

ADR-0078 resolves reach and gate state, then emits the one manifest ADR-0075 consumes. The manifest
also receives the existing inventory digest, grant kind, authority-event reference where applicable,
exact scope/operations/effect classes, expiry, gate snapshot and applicable legal-rule references.
ADR-0075 runs any isolated recovery proof and returns autonomous execution, local reshaping, refusal
or principal escalation before live reach. **ADR-0079 supersedes the older post-receipt decision
order:** durable decision or protected proposal/authority, intent, reach, receipt, then outcome.
Only a live-authorised disposition exposes the handle, and replay joins later receipt/outcome facts
without copying them backwards into the earlier decision. [cited: ADR-0079] [asserted]

`effect.intent` contains stable operation/decision/work-item/attempt identity; Owner and actor; the
canonical secret-free ADR-0075 manifest once, inline or by immutable artefact reference and digest;
its final ADR-0075 disposition; and inventory, gate, authority and law snapshots not already in that
manifest. `effect.receipt` links to it and records status, protected provider references, protected
request/response/content commitments, actual resource/money/scope use, post-state readback,
residuals and child operation ids. Low-entropy private values use opaque instance-private broker
references or domain-separated keyed MACs whose key stays outside the trajectory; credentials use
broker references only. An `unknown` receipt is an unresolved observation which a non-forking
`supersedes` chain may resolve to one final status; an irreconcilable head remains visibly unknown.
Non-idempotent effects are never blindly retried. [asserted]

Current `actor: principal, via: cli` validation is caller-supplied metadata, not authentication. No
such current event can admit a capability. ADR-0075's one first-party ingress must eventually expose
fresh human-presence proof bound to the exact manifest digest, scope, expiry and nonce, with its
signing/verification capability inaccessible to a dispatched process even under the same OS user.
OS identity alone is insufficient. This ADR consumes the verified result and creates no second ingress.
[measured: `src/consilient/events.py:890-978`] [asserted]

Law is structural only where it can be expressed as an exact reach, target, scope, expiry, authority,
data-classification, resource or money predicate, or as a jurisdiction-specific typed rule grounded
in current primary authority. Most legal questions remain contextual review. No numeric ratio is
known because no labelled denominator exists. Code can require and enforce a current scoped review
record; it cannot prove the review's legal interpretation. User configuration cannot lower the law
floor, and clearly unlawful action is refused rather than laundered through approval. [asserted]

Gate status never grants an action capability. Today Gate A and Gate B fail and routing remains
disabled; this ADR authorises specification and construction only. Gate A may later permit use of
its measured evidence inside the existing admitted surface. Gate B may make unattended/default
dependence eligible for a principal-named instance root, but only capabilities with an accepted
closed grant kind and passing boundaries open. Neither gate grants network, message, money, legal-obligation,
publication, credential, external-system or physical reach. ADR-0063 remains supervised cwd admission, not a gate
pass. [measured: `consil doctor`, 2026-08-22] [asserted]

## Evidence

- `[measured]` `capabilities.py` fails closed on missing/unavailable selections, but dispatch only
  serialises the selection into task text and harness defaults retain permission-bypass flags.
- `[measured]` SMTP/Twilio send and browser navigate/fill/click paths can precede event append, so a
  crash can occupy the effect/receipt ambiguity window.
- `[measured]` The current outbound event embeds the raw recipient, message text and free-text
  authorisation note; it is not the privacy-preserving receipt this ADR specifies.
- `[measured]` `events.validate()` has no generic effect contract and reversal validation checks
  syntax rather than executing an inverse or proving restoration.
- `[measured]` `events.py` itself records that canonical direct writers can evade the current bypass
  proxy; ordinary append lacks full process serialisation and fsync.
- `[measured]` Current first-party validation trusts caller-supplied `actor`/`via` fields and states
  that no signature verifier exists; no present authority event can safely open a gate.
- `[measured]` `consil doctor` reported Gate A FAIL, Gate B FAIL and
  `routing_orchestration_enabled: false` on 2026-08-22.
- `[measured]` The frozen external bar requires one Owner, provenance-bearing artefacts, exogenous
  verification and outcome measurement; another same-evidence reviewer is not the missing signal.
- `[cited]` Magentic-One uses task/progress ledgers but reports risky web actions and verification
  failures. Microsoft et al. (2024), *Magentic-One*, https://arxiv.org/html/2411.04468.
- `[cited]` OpenHands documents persistence for delegated conversations and warns that parallel tool
  execution risks races, ordering faults, deadlocks and resource exhaustion.
  https://docs.openhands.dev/sdk/guides/task-tool-set and
  https://docs.openhands.dev/sdk/guides/parallel-tool-execution.
- `[asserted]` A write-ahead intent plus least-privilege reach and provider/state receipt is a
  stronger, more testable effect boundary than a task ledger followed by a best-effort event.

## Evidence against

- `[asserted]` Finch's narrow output is the stronger architecture. It prevents whole classes of
  action rather than asking a manifest and inverse to describe them correctly. The source is
  fictional, so it cannot establish an empirical “only system ever demonstrated” claim. The frozen
  pre-registered corpus supplies no real-system evidence that provenance and undo are an equivalent
  safety property.
- `[asserted]` Most real-world effects are not reversible once observed. A recipient can remember a
  message; a secret can be copied; a payment can create reliance; public material can be cached; a
  physical event consumes time. Retraction, rotation, refund, takedown and compensation do not
  restore the prior world.
- `[asserted]` Provenance is forensic. It can attribute harm after the boundary fails, but cannot
  prevent the harm. A manifest, adapter and verifier may share one omitted scope and “prove” the
  wrong boundary exactly.
- `[measured]` Current send and browser paths act before record append, capability selection is
  advisory prompt text, and canonical direct event writers remain detectable only cooperatively.
  The implementation already demonstrates the chokepoint risk which this ADR proposes to solve.
- `[asserted]` Expanding typed adapters creates a broader attack surface than Finch's pinhole and a
  permanent maintenance obligation: every provider change can invalidate classification,
  idempotency or proof.
- `[asserted]` This ADR therefore concedes the core objection. It does not allow unconstrained
  actuation; it constrains all material output to typed least-privilege channels. Only internal
  semantics and local drafts remain unconstrained, and no safety claim exists until bypass and
  crash-window tests pass.

## Consequences

**Positive** — capability and permission cease to be conflated; every admitted effect has a durable
pre-effect intent, terminal receipt or explicit unknown; non-file effects become first-class in the
trajectory; and widening is reconstructible rather than configuration drift. [asserted]

**Negative** — raw shell/browser use becomes local or wildcard-gated unless an outer sandbox
confines it; provider adapters, reconciliation and legal-rule provenance add work; many useful
one-way effects remain protected because no honest undo exists. [asserted]

**Neutral but load-bearing** — `capabilities.py` remains the inventory, ADR-0075 remains the sole
reversibility/escalation controller, `events.py` remains the trajectory authority, `dispatch.py`
remains the outer runner, and the existing budget, routing, work-item and coordination substrates
remain in place. [asserted]

## Enforcement

This commit adds documentation only. It changes no gate, product code, source AST policy, routing
flag or six-command CLI, and it does not claim that the boundary exists. [measured]

Future implementation must add, in the same commit as each behaviour: an exact effect-enum test;
inventory state/grant tests; an outer source/sandbox bypass test including every human-facing render
sink; per-adapter manifest and escaped-effect fixtures; durable process-serialised append/fsync;
pre-reach ADR-0075 disposition and crash/reconciliation/idempotency/late-completion fixtures;
non-forking receipt-chain tests; law/gate/scope/expiry tests; authenticated first-party tests which
refuse same-OS dispatched-process mint, replay and scope widening; and projection-delete/replay
equality. [asserted]

- **Check:** none in this documentation-only commit; the normative check list is above. [measured]
- **Fails CI:** no — no implementation ships here. [measured]
- **Added in the same commit as the implementation:** required. [asserted]

## What would overturn this

EXP-59 rejects the boundary if one side effect is duplicated, lost, contradicted or recoverable only
from a private framework store at any registered crash cut. EXP-35 rejects a widened reversible
class if an inverse escapes its admitted root or crosses its fixed misclassification threshold.
[asserted]

One cheaper counterexample contracts the surface immediately: an unmanifested effect reaches the
world, a durable intent is absent, a principal-reserved authority is satisfied by an agent, or an
adapter's proof passes while an applicable protected effect is omitted. The affected capability
returns to gated until a structurally independent check exists. [asserted]

## Publication candidate?

**No.** The effect boundary is unimplemented, the current non-file record is incomplete, the event
writer is not yet durable under concurrency and neither named experiment has established the safety
claim. [measured] [asserted]
