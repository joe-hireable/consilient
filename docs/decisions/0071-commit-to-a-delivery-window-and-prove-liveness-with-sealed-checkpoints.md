# 0071. Commit to a delivery window, prove liveness with sealed checkpoints, and send only exceptions before delivery

**Correction:** `scripts/run_loop.py` resumes accounting, not work: it marks an interrupted tick
abandoned and advances. Recovery specified here starts a new run from the last sealed checkpoint and
never claims that the old process resumed. [measured]

- **Status:** PROVISIONAL — EXP-98 can kill the estimate and checkpoint mechanics; the trust effect
  of quiet delivery remains unmeasured
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product direction only, quoted in the source note); Codex dispatch
  `20260822T124219-d915c30c0f` (provisional mechanism)
- **Inquiry tier reached:** T1 ground — current code, trajectory, frozen external bar and retrieved
  primary product sources; EXP-98 is registered but unrun
- **Executable model:** none — ADR-0068 already owns the critical-path arithmetic, while the open
  streaming-versus-quiet question is behavioural and has no defensible numeric model

## Context

Joe Brown said that Consilient may advise that work will take a while and then return the finished
better-than-best product. He did not specify the event schema, estimator, checkpoint format or
notification policy below. [measured: `../00-context/the-machine-2026-08-22.md`]

No user-visible duration commitment exists in current code. `dispatch.py` records actual
`duration_s` only after a run; `work_items.py` carries no estimate; and repository search found no
delivery estimate event or projection. [measured]

The current runtime supplies useful but incomplete primitives. `loop.resume()` records an unsettled
tick as abandoned and does not re-execute it; `coordination.py` releases path claims on completion,
terminal dispatch outcome or expiry; `events.py` is the single validated append-only writer; and
`dispatch.py` kills a process tree at its wall. None records a resumable delivery checkpoint.
[measured]

ADR-0068 already decides that one request becomes the fewest independently verifiable dependent
streams, that duration follows the resource-constrained critical path, and that each bounded slice
seals a checkpoint. [cited: ADR-0068] This ADR extends that decision at the conversational delivery
boundary; it does not redefine intake or decomposition. [asserted]

ADR-0067 still governs composition. One Delivery Owner integrates one candidate; another member is
admitted only for a material evidence anchor unavailable to the current composition. A progress
reporter, middle manager or second reviewer reading the same state adds no evidence and is cut.
[cited: ADR-0067]

### Incumbent bar

OpenAI Codex exposes typed streamed lifecycle events plus turn-bound steering and interruption;
Anthropic Managed Agents exposes durable session events and distinguishes preview deltas from
authoritative buffered events; OpenCode and Cursor expose session status, cancellation and terminal
reasons. [cited: official sources marked `[FULL]` in `../10-research/bibliography.md`, retrieved
2026-08-19 to 2026-08-22]

The frozen organisation bar requires structured artefacts, one accountable owner, explicit budget
and termination, and independent artefact outcomes rather than confidence or completion prose.
[measured: `../00-context/agentic-organisation-bar-2026-08-22.md`]

The bar is therefore streaming control plus durable authoritative events, constrained by one-owner
accountability and independent verification. [asserted] The proposed delta is an evidence-backed
delivery window and sealed-checkpoint liveness that consume less principal attention than pushed
progress while retaining an explicit verbose visibility override. The delta is not yet measured.
[asserted]

## Decision

For quiet asynchronous work, Consilient will append and show one delivery window before execution,
render one in-place liveness card from sealed checkpoint evidence, push only commitment-changing
exceptions, recover a new run from the last valid checkpoint, and deliver only when a deterministic
predicate over the intake commitment and frozen verifier evidence passes. [asserted]

### 1. Estimate is a commitment, not mutable status

Before the first claim or side effect, `events.py` appends revision zero of `delivery.estimate`,
referencing the immutable commitment and ADR-0068 plan digests. It records the delivery range,
evidence class, selected analogue identities, per-stream bounds, resource snapshot, checkpoint
interval and recovery allowance. [asserted]

The estimator reuses real trajectory outcomes. With at least five comparable completed outcomes it
uses the nearest-rank empirical 10th-to-90th-percentile interval; adverse and censored outcomes remain
in the population and cannot lower the upper bound. With fewer than five, it schedules the Owner's
frozen expected slice durations against enforced slice ceilings and labels the range
`[asserted: low evidence]`. [asserted]

Dependency and pool constraints are applied to both ends of the range. Wall duration is the
resource-constrained critical path plus serial integration and final verification; parallel quota
and worker time still sum. [algebra]

After a checkpoint or material evidence change, the same projector recomputes the remaining range.
A new append-only revision is required when the projected latest time exceeds the current commitment,
the recovery allowance is consumed, or a changed commitment affects the remaining critical path.
The original estimate is never overwritten. [asserted]

Every revision names its predecessor, cause and new evidence. The user who made the request receives
one exception notice in the originating conversation with the old range, new range and cause. A miss
without prior notice is recorded as a breach and reported immediately, not repaired by backdating a
revision. [asserted]

### 2. Quiet does not mean absent

While work runs, the conversation contains one pinned card: state, original/current delivery window,
age of the last verified checkpoint, and whether user action is required. Ordinary checkpoint
advancement updates the card in place and sends no message. [asserted]

The default sends no percentages, token or tool streams, worker transcripts, reasoning, milestone
prose or repeated “still working” messages. Before completion, only an estimate revision, an
unrecoverable failure or a principal-only block creates a new message. An explicit user visibility
override may reveal streamed detail without changing the estimate, liveness or done predicates.
[asserted]

The card states `Starting` until the first checkpoint, `Working` only while a valid checkpoint chain
is fresh, `Diagnosing` when it is overdue but the claim remains live, `Recovering` after a terminal or
expired claim resumes under a higher fencing epoch, and `Blocked` only for a failed required
dependency or principal-only authority. [asserted]

### 3. Liveness is sealed artefact advancement

A checkpoint advances liveness only when its immutable manifest and referenced artefacts exist,
their digests validate, its sequence advances, and its fencing epoch equals the live claim when the
checkpoint event is appended. Repeated bytes, a repeated digest or a self-reported heartbeat do not
count. [asserted]

A PID, live process, exit code, launcher status, stdout growth or model statement is never the
liveness signal. Raw transcripts remain diagnostics. A terminal artefact record outranks a stale
checkpoint, and an overdue-but-unexpired claim is diagnosed rather than declared dead. [asserted]

This is ADR-0034's artefact-progress rule narrowed for delivery: the declared progress artefact is a
durable checkpoint capable of restarting work, not any file whose byte count changed. [asserted]

### 4. Checkpoints survive the failures in scope

Each bounded slice seals delivery, commitment, plan, stream, candidate and attempt identities; a
monotonic sequence and fencing epoch; predecessor and dependency digests; reachable local Git objects
or content-addressed non-Git artefacts; verifier receipts and adverse states; and one terminal state
or exact next action. [asserted]

Sealing writes and validates immutable objects, moves the manifest atomically, advances a local
checkpoint ref under a kernel-released lock, then appends the checkpoint event. Transcript bytes and
an uncommitted worktree are not checkpoints. Nothing is pushed. [asserted]

After restart, existing loop accounting keeps the killed tick `abandoned/outcome=unknown`. The
delivery projector validates the checkpoint chain and asks the existing `dispatch.py` path for a new
run identity, the same candidate identity and a higher fencing epoch. A completed stream is not
rerun; a stale worker cannot seal after displacement. [asserted]

Current claim completion, terminal-event release and timeout-plus-grace expiry are reused. Claim
acquisition must become atomic before parallel mutation, and reassignment requires terminal/expired
ownership plus an incremented epoch. [asserted]

A timeout may lose the current unsealed slice; it may not lose an earlier sealed checkpoint. A stream
which cannot emit an externally verifiable durable checkpoint within a bounded interval is not
eligible for quiet asynchronous delivery. [asserted]

The process-crash guarantee does not include sudden power loss: `events.append()` currently closes
without `fsync`. [measured]

### 5. Done has separate owners for readiness, verification and human truth

The Delivery Owner decides when the integrated candidate is ready to test, not whether it is true.
The frozen executing verifier writes `attempt.outcome`. A deterministic projector marks `Done` only
when: the active commitment and plan digests match; every required stream and dependency is sealed;
the integrated artefact is attributable; every frozen verifier ran and accepted that exact artefact;
all refusals, timeouts, quarantines and dissent are attached and dispositioned; candidate exposure is
inside `routing.py`'s beta-derived ceiling; and no principal-only decision remains. [asserted]

The final `delivery.outcome` references the estimate chain, actual duration, artefact and checkpoint
digests, verifier receipts, beta state, cost and adverse counts. It does not carry a human verdict.
[asserted]

Only the principal may later author the human `attempt.verdict` used as beta ground truth, through the
trusted first-party path enforced by V0-18 and V0-28. Ordinary delivery asks for no ceremonial
approval. [measured] The current trajectory has one human rejection and `consil beta` reports
`insufficient_data`; verifier acceptance is not known human reliability. [measured: `consil beta
--json`, 2026-08-22]

If the verifier accepts a bad artefact, the later human rejection remains paired with that accepted
attempt and increases the beta evidence. It is never rewritten. Further work requires a newly frozen
verifier or success contract derived from the rejection; the organisation may not shop another
candidate against the same check. If no stronger check can be named, the terminal result remains
rejected/incomplete. [asserted]

### Reuse boundary

Future implementation extends `scripts/dispatch.py`, `coordination.py`, `work_items.py`, `loop.py`,
`events.py`, `recall.py`, `routing.py`, `budget.py` and `instructions.py` along the exact boundaries in
the companion specification. No second orchestrator, seventh CLI command, dependency, gate change or
product-code execution capability is introduced. [asserted]

`routing_orchestration_enabled` stays `false`. Gate A and Gate B do not move. [asserted]

## Evidence

- `[measured]` Current dispatch outcomes record actual duration after execution, but no current
  event, work-item field or user projection records a delivery estimate before work.
- `[measured]` `loop.resume()` marks unsettled ticks abandoned and advances; it resumes accounting,
  not a deliverable. `coordination.py` supplies expiring claims but no checkpoint identity or fencing
  epoch.
- `[measured]` One timed-out local dispatch recorded 3,492,819 output bytes while its useful
  worktree artefact survived separately; byte growth did not make the execution result resumable.
  The trajectory observation is recorded in ADR-0068.
- `[measured]` `consil beta --json` reports one false accept among one human rejection, six
  quarantined lines and `insufficient_data`; a human-labelled reliability point is unavailable.
- `[cited]` OpenAI Codex, Anthropic Managed Agents, OpenCode and Cursor expose streamed lifecycle,
  session, cancellation or terminal-state controls in official `[FULL]` sources recorded in the
  bibliography.
- `[cited]` ADR-0067 requires one Owner and distinct evidence for any added member; ADR-0068 requires
  a minimum verifiable stream graph, visible duration range and sealed checkpoints.
- `[algebra]` Parallel branches overlap in elapsed time but sum in quota; a resource-constrained
  critical path, not total worker time, determines the delivery window.
- `[asserted]` A checkpoint-backed quiet card will reduce principal attention without increasing
  abandonment or human rejection. EXP-98 tests only the operational half of that claim.

## Evidence against

- `[asserted]` **The strongest case is that streaming progress beats silence:** successful agent
  products stream because visible actions make latency legible, expose wrong direction early and let
  the user interrupt before more work is wasted. Silence is easily read as abandonment and loses
  trust. The frozen sources do not provide a success-ranked market census, so “most successful” is
  not upgraded beyond this asserted market argument.
- `[cited]` The objection has real mechanism behind it: Codex emits typed lifecycle events,
  Anthropic exposes durable session streams, and OpenCode and Cursor expose live status and control.
  All four incumbents favour inspectability over a quiet black box.
- `[asserted]` A pinned card centralises trust in another projector. If its checkpoint validation is
  wrong, `Working` is a more polished falsehood than a spinner, and sparse checks delay detection of
  a wrong direction which streaming would expose immediately.
- `[asserted]` Estimate revisions can become respectable-looking excuses. A wide cold-start range
  is less useful than candid uncertainty, while repeated exception notices recreate progress noise.
- `[asserted]` Checkpoint boundaries can distort the work, create Git/object clutter and encourage
  agents to optimise for visible sealed state rather than final quality.
- `[measured]` EXP-98 is blocked and cannot support the mechanism today; current human-labelled beta
  is insufficient, and no quiet-versus-streaming trust comparison is registered.

The total-silence objection is conceded. The decision is quiet **narrative** progress plus visible
checkpoint liveness, not absence. If streaming catches more bad direction or reduces abandonment
without increasing principal attention, the default changes to streamed milestones and the durable
estimate/checkpoint/done core remains. [asserted]

## Consequences

**Positive** — the user receives one evidence-labelled promise, can distinguish fresh work from
recovery without supervising it, and gets a finished artefact with replayable verifier evidence.
[asserted]

**Negative** — every long stream pays checkpoint, projection and recovery-state overhead; indivisible
quiet work is refused; estimate breaches and recovery failures are visible rather than smoothed over.
[asserted]

**Neutral but load-bearing** — one Owner remains accountable; process restart is not candidate retry;
human verdict remains separate from verifier acceptance; verbose visibility is an override, not a
different execution protocol. [asserted]

## Enforcement

This commit records a specification and decision only. It changes no product behaviour, gate, CLI or
research evidence. [measured]

- Check now: the provisional ADR names live EXP-98; ADR number collision and document invariants run
  through existing repository checks. [measured]
- Future same-commit checks must prove estimate-before-claim ordering; append-only revision and one
  exception notice; no PID/exit/heartbeat/byte-growth liveness; valid checkpoint sequences, digests
  and fencing; kill-and-restart recovery without rerunning completed work; and at-most-current-slice
  loss on timeout. [asserted]
- Future done-predicate checks must reject changed commitments, missing dependencies, unexecuted
  verifiers, omitted adverse outcomes, unresolved principal decisions and candidate-ceiling breaches.
  A human rejection after verifier acceptance must remain the beta false-accept pair. [asserted]
- A source scan must prove no second orchestration or user-message path bypasses `dispatch.py`, work
  items and the originating conversation projector. [asserted]
- Fails CI today: only record-level checks; implementation checks await the code they constrain.
  [measured]
- Added in the same commit as implementation: no implementation is added; every future invariant
  above is a same-commit condition. [asserted]

## What would overturn this

EXP-98 kills the estimate/checkpoint mechanism for its frozen mixture on any checkpoint loss, early
dependent execution or completed-stream rerun. It withholds the estimate claim unless at least 80% of
original delivery windows cover actual duration and every predicted miss is revised before breach.
[asserted: EXP-98 preregistration]

A matched quiet-card versus typed-streaming trial would overturn the notification default if
streaming reduces abandonment, wrong-direction waste or human rejection without increasing principal
interruptions or review minutes. Until that is run, the low-attention benefit remains `[asserted]`.

An implementation that cannot fence stale workers or make checkpoint objects reachable must fall
back to supervised bounded execution; it may not keep the quiet surface while dropping survival.
[asserted]

## Publication candidate?

**No.** Duration calibration, checkpoint recovery and the quiet-versus-streaming trade-off are
unmeasured, and the current beta evidence is insufficient. [asserted]

## Update: 2026-08-22 — declared provenance is not authentication

Lines 166–168 overstate the current boundary. `events.py` requires the caller-declared `actor` to
equal the caller-declared `principal` and `via` to equal `"cli"`, but explicitly says that this is
declared provenance and that no signature verifier exists. `scripts/verdict.py` also accepts
`--principal` from the caller. V0-18 and V0-28 therefore enforce payload consistency and reject
declared non-local channels; they do not authenticate that the principal authored the verdict.
[measured: `src/consilient/events.py:957-978`; `scripts/verdict.py:116-118`]

The decision's policy remains that only the principal may author human `attempt.verdict` ground
truth. Until trusted first-party ingress authenticates authorship, the present CLI path is not that
trust boundary and its records must not be described as authenticated principal verdicts. [asserted]

This dated update is appended because the ADR is PROVISIONAL; the original evidence overclaim
remains visible in the decision trail. [asserted]
