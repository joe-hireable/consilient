# 0083. Expose squad state only on pull and record steering before it acts

**Correction:** ADR-0071 is PROVISIONAL rather than accepted, its sealed checkpoints and fencing are
future work, and today's killed claims were released by hand-authored terminal events before actual
expiry; none of those mechanisms may be described as working implementation. [measured]

- **Status:** PROVISIONAL — EXP-108 can remove live inspection; authenticated principal control and
  safe process displacement are not implemented
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product requirement only, quoted in the source context); Codex dispatch
  `20260822T140246-cabc030952` (provisional mechanism)
- **Supersedes:** [0053](0053-build-one-local-observability-surface-that-renders-the-record.md), in
  part — one logical projection may now be rendered inside the originating local chat as well as the
  offline dashboard, and a separate typed control boundary may act; the renderer still never decides
- **Inquiry tier reached:** T1 ground — current source and trajectory mechanics, ADR-0071, the frozen
  product bar and current primary incumbent documentation; EXP-108 is preregistered but unrun
- **Executable model:** none — the unresolved effect is behavioural and the decision is reversible;
  EXP-108 measures it directly

## Context

The principal asked for one primary chat response while retaining maximum observability and the
ability to enter a running agent process. The apparent conflict with ADR-0071 disappears only when
delivery and availability are separated: quiet delivery governs what the product sends, while this
decision governs what a user may deliberately pull. [measured: principal source context] [asserted]

The current runtime is not a steerable squad. `events.py` supplies one append-only writer;
`coordination.py` projects claims; work-item comments can carry an evidence class; and dispatch
preserves its initial brief, bounded recall and local output. The child receives no stdin, no
addressable process handle escapes the runner, successful dispatches omit considered alternatives,
and no attach, injection, stop, ownership-transfer, checkpoint or fencing path exists. [measured]

The writer is authoritative but not yet an actuation boundary: ordinary append has no cross-process
serialisation or durability acknowledgement, and the current private trajectory contains malformed
concurrent lines. A request can therefore fail admission while an independently invoked adapter acts.
Live mutation must refuse until durable write-ahead ordering is enforced. [measured] [asserted]

Four killed runs across two recovery incidents demonstrated the operational gap. They received
hand-authored terminal outcomes; at least one later dispatch recorded a claim-overlap refusal before
the first pair was closed. Without a terminal event, each claim would have remained live until its
timeout plus grace expired. Private identities and paths are withheld under ADR-0057. [measured]

The brief's candidate-ceiling equation is also stale. ADR-0077 now uses the distribution-free union
bound `n_max = floor(epsilon / beta_upper)` until dependence is measured. At the current trajectory,
human-labelled beta is `insufficient_data`, so routing refuses rather than producing a ceiling.
[measured] [algebra]

## Decision

Consilient will expose one same-machine, pull-only projection of the trajectory at attention, squad,
work-item and agent depth. The originating chat or local command-post client addresses entities by
stable ids and reuses the dashboard projection; it does not require the user to read a path. Opening
a view may refresh local state in place but sends no conversation message. [asserted]

Observation is read-only and non-authoritative. Redirecting, adding evidence, stopping a run or
taking ownership is a separate control action: it appends a typed `intervention.requested` through
`events.py` durably before any adapter action, acts only at a controller-proven safe boundary or under
a revoked fencing epoch, appends one terminal outcome, and changes the delivery's autonomy label.
[asserted]

Read-only attach and context inspection preserve in-flight work. Redirect and evidence addition take
effect at the next safe boundary; prior sealed checkpoints and tool results remain, while incompatible
unsealed output is quarantined. Stop revokes the epoch, kills and verifies the process tree, records
the terminal dispatch and releases the claim from a controller outside the child. Owner takeover
requires authenticated first-party authorship, transfers at a safe boundary under a higher epoch and
makes subsequent work `operator_controlled`. [asserted]

`safe` is not adapter testimony. For the target run and epoch, the trajectory must contain no
unmatched side-effecting tool/effect start, the controller registry must contain no live
mutation-capable child or lease, and reusable state must end at a digest-verified sealed checkpoint
or terminal tool result. Unknown effects make the predicate false. A lying adapter which reports
`safe` while any such effect or handle remains live is refused. The necessary effect, handle and
checkpoint chain does not exist today, so redirect, evidence injection and takeover remain
unavailable. [asserted]

The current `actor == principal` and `via == "cli"` checks authenticate nothing. Until a trusted
first-party ingress exists, a remote steer is an untrusted proposal and principal-only action or
Owner takeover refuses. No payload becomes authoritative because it names the principal. [measured]
[asserted]

The renderer derives four deterministic outcome labels from the event lineage: `autonomous` when no
post-commitment mutation occurred; `steered` after redirect, evidence addition or stop-and-continue;
`operator_controlled` after takeover; and `cancelled_by_user` after an unrestarted stop. An agent
cannot choose or downgrade that label. [asserted]

The existing dashboard remains an offline rendering of the same projection. This decision supersedes
ADR-0053's file-only and single-renderer restriction, but preserves its stronger boundaries: the
trajectory remains the record; displays are disposable; display state cannot decide, route, accept
or authorise; and no review verdict is collected there. [asserted]

ADR-0071 is not weakened. Its estimate and final delivery remain the ordinary conversation messages;
ordinary checkpoints, view refreshes and agent events stay unpushed. An unrecoverable failure,
estimate revision or principal-only block retains ADR-0071's exception treatment. [asserted]

## Evidence

- `[measured]` `events.py` is the validated append boundary and the JSONL is authoritative;
  projection, recall and dashboard are rebuildable readers. Its ordinary append is not
  cross-process serialised or durability-acknowledged, and malformed concurrent lines exist in the
  private trajectory.
- `[measured]` Claims currently release on work-item completion, a terminal dispatch event or expiry;
  they have neither atomic acquisition nor a fencing epoch.
- `[measured]` Dispatch uses `stdin=DEVNULL`, retains no external live handle and exposes no attach,
  redirect, evidence injection, per-run cancellation or takeover surface.
- `[measured]` The present trajectory has one human rejection, one false accept and six quarantined
  events; beta is `insufficient_data`, so a human-beta routing ceiling is unavailable.
- `[measured]` The identity check compares caller-controlled declarations and explicitly has no
  signature verifier. V0-18 and V0-28 therefore constrain the design but do not solve authentication.
- `[cited]` Claude Cowork exposes progress, visible approach and mid-task redirection; ChatGPT Work
  exposes progress review, direction change and approval; Nous Hermes Agent exposes steer/stop APIs,
  a durable Kanban and a Command Center; Gemini Spark exposes structured task progress, changed
  instructions and browser takeover. Primary sources were retrieved 2026-08-22 and are linked in the
  companion specification.
- `[measured]` The reviewed official sources do not document the narrower joined mechanism proposed
  here: calibrated verifier beta, distinct-class admission, append-only intervention lineage and
  authenticated principal authorship in one live projection. This is bounded to those pages, not a
  claim about private implementations or the whole market.
- `[asserted]` Pull-only availability can preserve quiet delivery while enabling correction without
  imposing monitoring work. EXP-108 tests this claim.

## Evidence against

**The strongest case is that observability is a trap and the honest product should show nothing
until the result.** [asserted] A glass box makes unfinished work salient and makes intervention cheap.
A strategic user who would otherwise judge the artefact can become a supervisor of partial states;
redirects invalidate work, contaminate autonomous provenance and consume the attention the product
was meant to save. [asserted]

There is evidence for the mechanism. Explanations have increased acceptance without improving
discrimination, reliance has moved without a corresponding self-reliance gain, and sustained
monitoring is measured as demanding work. [cited: Bansal et al. 2021; Schemmer et al. 2023; Warm,
Parasuraman & Matthews 2008, verified in `docs/10-research/bibliography.md`] A live reasoning stream
can therefore perform diligence rather than demonstrate quality. [asserted]

Every named incumbent exposes progress and control. That convergence makes streaming the market bar,
but vendor adoption is not an outcome experiment. [cited] No reviewed source shows that watching
improves independent acceptance, and a polished progress stream can make a weak verifier easier to
trust. [measured search boundary] [asserted]

Pull instead of push answers only forced attention. It does not answer invitation, self-selection or
meddling: the user who is most anxious may open the surface most often, then intervene on the hardest
tasks. A passive observational log cannot identify causation. [asserted]

We decide provisionally anyway because the requirement is explicit, the pure projection is
reversible, observation carries no authority and a randomised unavailable-versus-available trial is
registered. The objection wins if EXP-108 shows intervention, review burden or accepted outcomes
cross its adverse thresholds: live inspection is then removed, leaving post-hoc replay and finished
results. [asserted]

## Consequences

**Positive** — a user can inspect exact claims, evidence, alternatives and recorded context without
supervising by default; a steer becomes replayable input rather than invisible conversational drift;
and a killed process cannot depend on itself to release its claim. [asserted]

**Negative** — safe steering requires an authenticated local ingress, process-serialised durable
event admission, controller-tracked effects and handles, addressable adapter controls, atomic claims,
fencing and ADR-0071 checkpoints that do not exist. Until they do, the honest surface contains named
absences and mutating controls refuse. [measured] [asserted]

**Neutral but load-bearing** — watching is never consent; absence is never approval; view depth does
not change routing or acceptance; a result with any mutating intervention is not autonomous; and the
raw surface stays on the user's machine under ADR-0057. [asserted]

`routing_orchestration_enabled` stays `false`; Gate A and Gate B do not move; the six-command CLI is
unchanged; no dependency or product execution capability is added by this record. [asserted]

## Enforcement

This commit records a specification, ADR and preregistration only. It adds no runtime behaviour, so
the controls below are same-commit requirements for future implementation rather than claims of
present enforcement. [measured] [asserted]

- **Projection check:** the same event prefix produces deterministic attention, squad, work-item and
  agent views; unavailable source fields remain unavailable. [asserted]
- **Quiet check:** checkpoints, transcript events and local refreshes produce no conversational
  message under the default delivery policy. [asserted]
- **No implicit authority check:** injecting arbitrary view events, dwell times and silence leaves
  decisions, approvals, accepted attempts, gates, spend, ownership and actuation handles byte-identical.
  A timeout blocks or expires; it never approves. [asserted]
- **Write-ahead check:** no adapter mutation is reachable without an earlier matching
  durable `intervention.requested`, every request receives exactly one terminal outcome, concurrent
  large appends remain canonical and a failed flush/fsync prevents adapter invocation. [asserted]
- **Boundary check:** a lying adapter which reports `safe` while an effect event, child or lease is
  live cannot inject, redirect or transfer ownership. [asserted]
- **Lineage check:** redirect, evidence injection or takeover makes `autonomous` impossible for that
  delivery lineage. [asserted]
- **Displacement check:** stop/takeover revokes the prior epoch, prevents stale writes, records a
  terminal outcome and releases the claim without a manual event. [asserted]
- **Authorship check:** spoofed actor/principal/channel and replay attempts cannot exercise Owner or
  any V0-18 authority; those operations refuse while authentication is unavailable. [asserted]
- **Privacy check:** the surface opens no network path, remote resource, telemetry or tracked
  trajectory artefact. [asserted]
- **Composition check:** an added squad member without a distinct evidence class is refused, and
  absent human beta renders a routing refusal rather than a fabricated count. [asserted]

## What would overturn this

EXP-108 compares identical quiet-delivery work with the live pull surface unavailable versus
available-but-unpushed. It removes live inspection if the available arm materially raises mutating
intervention or principal review time, lowers independently accepted outcomes, or breaches privacy
or authority; it permits a benefit claim only if perceived trust or intervention improves past its
fixed threshold without an adverse outcome. [asserted: EXP-108 preregistration]

An implementation unable to authenticate takeover, fence stale writers or produce ADR-0071's sealed
checkpoint must retain read-only projection and refuse the corresponding mutation. It may not weaken
the guarantee to make the button work. [asserted]

A retrievable product demonstrating the same joined provenance, beta, evidence-class and
principal-authorship mechanism would erase the incumbent-gap claim, but would not by itself decide
whether pull availability helps users. [asserted]

## Publication candidate?

**No.** The interaction effect is unmeasured, the identity boundary is declarative and the control
mechanics are not implemented. [asserted]
