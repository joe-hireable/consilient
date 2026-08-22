# Chat delivery: promise once, prove liveness, return the finished artefact

**Correction:** `scripts/run_loop.py` resumes accounting, not work: after a restart it marks an
unsettled tick `abandoned` and advances. This design retains that honest outcome and resumes the
deliverable from its last sealed checkpoint. [measured]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0071 is PROVISIONAL and EXP-98 can kill its duration and recovery
  mechanics. [asserted]
- **Author:** Codex dispatch `20260822T124219-d915c30c0f`; the product requirement is the
  principal's, while the mechanism below is this dispatch's provisional design. [measured]
- **Scope:** the back half of one chat request: estimate, quiet execution, liveness, recovery and
  delivery. Intake and clarification are out of scope. [asserted]

## 1. Contract boundary and success condition

This specification consumes the immutable commitment artefact produced by the separate intake
stream. It does not decide how questions are asked, how ambiguity is resolved or how that artefact
is created. Delivery requires only a stable commitment identity and digest, its success and non-goal
boundary, frozen verifier references, authority and expiry, and the work graph derived under
ADR-0068. The intake specification owns the final field names. [asserted]

The success condition is: before the first side effect, the user receives a dated delivery window
and the evidence behind it; while work runs, one quiet card distinguishes fresh checkpointed work
from recovery or failure; after every restart the organisation continues from the latest valid
checkpoint; and `done` is a replayable predicate over the frozen commitment and verifier evidence,
not an agent's assertion. [asserted]

One Delivery Owner remains accountable for the integrated artefact. A second member is admitted
only for a decision-changing evidence class under ADR-0067; delivery does not create a status-writer,
project manager or reviewer role. [cited: ADR-0067]

## 2. Incumbent bar and the proposed delta

Current agent control surfaces favour streaming. OpenAI Codex emits typed lifecycle events and binds
steering and interruption to the active turn; Anthropic Managed Agents exposes a durable event stream
and distinguishes non-authoritative preview deltas from authoritative buffered events; OpenCode and
Cursor expose session status, cancellation and terminal reasons. [cited: official sources marked
`[FULL]` in `docs/10-research/bibliography.md`, retrieved 2026-08-19 to 2026-08-22]

The frozen organisation bar adds one Owner, structured artefacts, hard termination and budget
bounds, and independent outcome evidence rather than confidence or completion prose. [measured:
`docs/00-context/agentic-organisation-bar-2026-08-22.md`]

The proposed delta is not total silence. It replaces pushed narrative progress with three smaller,
harder signals: an immutable delivery window, a pull-visible card backed by sealed checkpoints, and
one pushed exception whenever the commitment changes. It adds Consilient's frozen verifier and beta
record to the final delivery. Whether this produces more trust with less attention than streaming is
unmeasured. [asserted]

The plain alternative is to stream tokens, tool calls and milestone prose. That remains available
when the user explicitly selects a more verbose visibility level; it is not the default delivery
policy specified here. [asserted]

## 3. Estimate before work starts

### 3.1 The recorded estimate

Before any stream is claimable, `events.py` appends revision zero of one `delivery.estimate` record.
The record references rather than copies the intake commitment. It contains: [asserted]

| Field | Meaning |
|---|---|
| `delivery_id`, `commitment_id`, `commitment_digest`, `plan_digest` | Stable identities joining intake, plan, execution and delivery. [asserted] |
| `estimate_id`, `revision`, `predecessor_estimate_id` | An append-only chain; revision zero has no predecessor. [asserted] |
| `earliest_at`, `latest_at`, `issued_at` | An explicit-offset delivery window fixed before work. [asserted] |
| `evidence_class`, `analogue_ids`, `sample_size`, `method` | Why the window deserves its label. [asserted] |
| `stream_bounds`, `resource_snapshot_digest` | Per-stream bounds and the pool/slot state used by the schedule. [asserted] |
| `checkpoint_interval_s`, `recovery_allowance_s` | The liveness and restart assumptions already included in the window. [asserted] |
| `not_included` | Any known first-party wait that cannot honestly be predicted. [asserted] |

The event is appended and rendered to the user before `coordination.open_claim()` or
`scripts/dispatch.py` may launch work. A fixture must fail if ordering is reversed. [asserted]

The user-facing sentence is deliberately short: [asserted]

> I will return the finished artefact between **14:10 and 14:40**. I will only interrupt if this
> commitment changes or a decision only you can make becomes necessary.

### 3.2 Evidence hierarchy

The estimator uses the first rung that has evidence; it does not fit a learned model. [asserted]

1. **Comparable deliveries.** Join prior `delivery.outcome`, `dispatch.outcome` and
   `attempt.outcome` records by stable delivery, candidate and attempt identities. Comparability
   requires the same artefact kind, verifier contract, size band and route-capability class recorded
   in the frozen plan. The selected event identities and digests remain in the estimate. [asserted]
2. **Comparable streams.** When the complete delivery has no analogue, use sealed stream outcomes
   with the same deliverable and verifier contract, then schedule them through the current DAG and
   resource limits. [asserted]
3. **Cold start.** With fewer than five comparable outcomes, use the Owner's frozen expected slice
   durations as the lower schedule and the enforced slice ceilings plus stated recovery allowance
   as the upper schedule. Label the estimate `[asserted: low evidence]` and require an earlier first
   checkpoint. [asserted]

Successful outcomes alone are not an estimate population. Refusals, timeouts, abandoned slices,
recovery time and verifier failures remain in the evidence set. A censored timeout cannot lower a
bound; it raises the upper bound to at least the observed elapsed time plus the recorded recovery
allowance. If the censoring cannot be bounded, the estimate remains low-evidence. [asserted]

With at least five comparable completed outcomes, the per-stream range is the nearest-rank empirical
10th to 90th percentile of actual elapsed duration. This is a target 80% interval, not a guarantee;
EXP-98 withholds the reliability claim unless at least 80% of original windows cover actual delivery.
[asserted]

For each end of the range, scheduling is deterministic: dependencies set earliest starts, available
pool and worker slots limit concurrency, parallel branches overlap, and integration plus final
verification remain serial. Elapsed wall time is the resource-constrained critical path; worker and
quota time still sum across parallel branches. [algebra]

The resource snapshot is part of the evidence. A route or pool change is new evidence and may cause
a revision; it may not be silently treated as though it was known at revision zero. [asserted]

### 3.3 Revision rule

The original estimate is never edited. After every sealed checkpoint, route change, dependency
failure or authorised commitment revision, the projector recomputes the remaining range using the
same method. It appends a new `delivery.estimate` revision when either: [asserted]

1. the recomputed latest delivery exceeds the current `latest_at`; [asserted]
2. the recovery allowance has been consumed and the current latest time is no longer achievable;
   or [asserted]
3. a new commitment digest changes work which lies on the remaining critical path. [asserted]

An earlier possible finish is not a revision; the artefact is simply delivered early. A range still
contained inside the current commitment is not a revision either. [asserted]

Every revision carries its predecessor, the unchanged original estimate, the new evidence, a
machine-readable cause (`scope_change`, `route_change`, `checkpoint_miss`, `dependency_failure` or
`estimate_error`) and whether notice preceded the old upper bound. The user who made the request is
told once in the originating conversation with the old range, new range and cause. Other transports
are projections, not new authority. [asserted]

Missing the bound without warning is recorded as an estimate breach, not repaired by backdating a
revision. The user is told immediately, the new range is appended, and work continues from the last
checkpoint unless spend, expiry or another principal-only boundary was reached. [asserted]

## 4. No progress reporting without abandonment

### 4.1 What the user sees

Long work occupies one pinned card in the conversation. It updates in place and sends no message for
ordinary checkpoint advancement. [asserted]

```text
Working · promised 14:10–14:40
Last verified checkpoint 7 minutes ago · no action needed
```

The card contains no percentage, token stream, worker transcript, internal reasoning, celebratory
milestone or estimate disguised as progress. Opening its details may show the immutable estimate
chain, checkpoint receipts and current verifier identifiers; the default conversation does not push
them. [asserted]

Only four events may create a new user-visible message before completion: the original estimate, a
delivery-window revision, a principal-only block, and an unrecoverable failure. The finished delivery
is the next ordinary message. Recovery inside the promised window updates the card and does not ask
the user to supervise it. [asserted]

### 4.2 Artefact-based liveness

`Working` means a valid checkpoint chain advanced within the frozen checkpoint interval. It does not
mean a PID exists, a process answered a heartbeat, stdout grew, a launcher exited zero or a model said
it was working. [asserted]

A checkpoint counts only after its manifest and every referenced immutable artefact exist, their
digests validate, its fencing epoch equals the live claim, and `events.append()` records it. Rewriting
the same digest or appending a manifest with no new sealed state does not advance liveness. [asserted]

The states are conservative: [asserted]

| Card state | Projector rule | User interruption |
|---|---|---|
| `Starting` | Estimate exists; no first checkpoint yet; first-checkpoint deadline has not passed. [asserted] | None. |
| `Working` | Latest valid checkpoint is within its interval and no terminal outcome supersedes it. [asserted] | None. |
| `Diagnosing` | Checkpoint is overdue but the claim has not expired; diagnostics are being captured and live work is not duplicated. [asserted] | None. |
| `Recovering` | The prior attempt is terminal or its claim expired; a higher fencing epoch resumed from the last valid checkpoint. [asserted] | Only if the window changes. |
| `Blocked` | A frozen dependency failed or a principal-only authority is required. [asserted] | One precise request only for the principal-only case. |
| `Done` | The predicate in section 6 passed. [asserted] | Final delivery. |

A terminal artefact record always outranks a stale checkpoint signal. An attempt is dead only when it
has a terminal failure, refusal or timeout, or its claim expired without a newer valid checkpoint.
The overdue-but-unexpired state is `Diagnosing`, not a guessed death. [asserted]

Raw transcript growth remains useful diagnostic evidence but cannot make the card say `Working`.
This narrows ADR-0034's generic artefact-progress rule for delivery work: durable checkpoint
advancement is the declared progress artefact. [asserted]

## 5. Checkpointing and recovery

### 5.1 Sealed checkpoint

Each bounded execution slice ends by sealing one checkpoint with: [asserted]

- delivery, commitment, plan, stream, candidate and attempt identities; [asserted]
- monotonically increasing sequence and fencing epoch; [asserted]
- predecessor checkpoint digest and dependency artefact digests; [asserted]
- base tree, owned paths, reachable local Git object/ref or content-addressed non-Git artefacts;
  [asserted]
- verifier receipts already obtained, refusals and quarantines; [asserted]
- terminal state or one exact next action; and [asserted]
- creation time, next-checkpoint deadline and manifest digest. [asserted]

Transcript bytes and an uncommitted working directory are not checkpoints. Git-backed work is kept
reachable by a local per-stream checkpoint ref; other artefacts live in the existing private
`.harness` instance store under content-addressed names. Nothing is pushed. [asserted]

The seal order is: write immutable objects, validate them, move the manifest into place atomically,
advance the local checkpoint ref under a kernel-released lock, then append the checkpoint event. A
crash before the append leaves the prior checkpoint authoritative; a crash after the append finds
all referenced objects already present. [asserted]

`events.append()` currently closes writes without `fsync`, so this promises survival from process,
dispatcher and operating-system restart, not from sudden power loss or storage corruption.
[measured]

### 5.2 Restart, crash and timeout

On restart, `run_loop.py` keeps its existing `abandoned/outcome=unknown` record for the interrupted
tick. A delivery projector reads the work item and plan, validates the latest checkpoint chain, and
asks `scripts/dispatch.py` for a new run with the same candidate identity and a new run identity.
This is recovery from evidence, not a claim that the old process resumed. [asserted]

`coordination.py` remains the only claim path. Its existing terminal-event and expiry releases are
reused; acquisition is extended atomically and recovery increments a fencing epoch so a displaced
worker cannot publish a later checkpoint. Reassignment requires both an expired or terminal claim
and the higher epoch. [asserted]

A completed stream is never rerun. A failed current slice may be repeated from its predecessor
checkpoint, but it does not become a second candidate or a second verifier exposure: candidate
identity is stable across execution slices and only a submitted integrated artefact creates an
acceptance attempt. [asserted]

The working deadline for a slice precedes the dispatcher's hard wall by a declared sealing margin.
If a timeout still lands first, the current slice may be lost; every earlier sealed checkpoint
survives. A stream unable to produce a durable externally verifiable checkpoint inside a bounded
interval is not admitted to quiet asynchronous delivery. [asserted]

## 6. What `done` means

The Owner decides that a candidate is ready to test; the Owner does not decide truth. The frozen
executing verifier decides its own check outcome. A deterministic projector marks the delivery
`Done` only when all of these are true: [asserted]

1. the active commitment and plan digests are the ones the candidate was built against; [asserted]
2. every required stream has a terminal valid checkpoint and every dependency digest matches;
   [asserted]
3. the integrated artefact is sealed and attributable to the one Delivery Owner; [asserted]
4. every frozen verifier executed against that exact artefact and appended an accepting
   `attempt.outcome`; [asserted]
5. every refusal, timeout, quarantine and material dissent is attached and dispositioned rather
   than omitted; [asserted]
6. candidate exposure is inside the ceiling returned by `routing.py`; an unmeasured relevant beta
   refuses automatic acceptance rather than inventing a safe value; and [asserted]
7. no unresolved principal-only decision remains. [asserted]

The final `delivery.outcome` references the original and current estimate, actual elapsed time,
artefact digests and links, checkpoint-chain digest, verifier receipts, beta state, cost, dissent and
adverse counts. It does not copy a human verdict or call verifier acceptance human approval.
[asserted]

Ordinary delivery does not require a ceremonial approval. Only the principal may later author the
human verdict used as beta ground truth, through the trusted first-party path enforced by V0-18 and
V0-28. [measured] `consil beta --json` on 2026-08-22 reports one human rejection and
`insufficient_data`; verifier acceptance therefore cannot be described as known human reliability.
[measured]

### 6.1 When the verifier passes a bad artefact

A later human rejection appends a separate `attempt.verdict` against the same stable attempt. The
delivered outcome remains in history as verifier-accepted and human-rejected, and beta incorporates
it; neither the Owner nor a projection may rewrite it to incomplete or accepted. [asserted]

The rejection reopens work only after a changed verifier or success contract is frozen from the new
evidence. It is not permission to shop a second candidate against the same check. If no stronger
check can be named, the honest terminal state is rejected/incomplete rather than an automatic retry
loop. [asserted]

## 7. Reuse boundary

No second orchestrator, seventh command, dependency or gate change is introduced. Future
implementation extends the existing components only: [asserted]

| Existing component | Extension |
|---|---|
| `scripts/dispatch.py` | Enforce estimate-before-claim ordering, bounded slices and one recovery entry point. [asserted] |
| `coordination.py` | Keep trajectory claims and expiry; add atomic acquisition and fencing epoch. [asserted] |
| `work_items.py` | Bind delivery, plan, stream, Owner and terminal identities. [asserted] |
| `scripts/run_loop.py` / `loop.py` | Keep abandoned-tick accounting; project the next ready slice from the last checkpoint. [asserted] |
| `events.py` | Remain the single writer; validate estimate chains, checkpoints and delivery outcomes. [asserted] |
| `recall.py` | Supply bounded verbatim context; never become checkpoint storage or authority. [asserted] |
| `routing.py` | Apply the existing beta ceiling to candidate exposure, not process restarts. [asserted] |
| `budget.py` | Supply the existing spend and period ceilings; no delivery ledger duplicates them. [asserted] |
| `instructions.py` | Explain the contract portably; prompts do not enforce it. [asserted] |

`routing_orchestration_enabled` stays `false`; the six-command CLI remains unchanged; product code
retains its AST restrictions. [asserted]

## 8. Checks that must ship with implementation

The minimum check set is: [asserted]

1. estimate revision zero is append-only and precedes every claim and side effect; [asserted]
2. a revision retains the original, names new evidence and produces exactly one exception notice;
   [asserted]
3. PID presence, exit zero, heartbeat text and transcript growth cannot produce `Working`;
   [asserted]
4. a forged, repeated-digest or stale-epoch checkpoint is rejected; [asserted]
5. a process-tree kill preserves the prior checkpoint, records the attempt unknown, resumes under a
   higher epoch and never reruns a completed stream; [asserted]
6. a timeout before sealing loses at most the current slice, not the previous checkpoint; [asserted]
7. `Done` fails on a changed commitment, missing dependency, unexecuted verifier, omitted adverse
   outcome, unresolved principal decision or exceeded candidate ceiling; [asserted]
8. a verifier pass followed by human rejection remains the beta false-accept pair and cannot be
   overwritten; and [asserted]
9. ordinary checkpoints emit no conversational message under the default delivery policy. [asserted]

EXP-98 supplies the first operational test: duration-window coverage, every reforecast, checkpoint
loss, duplicate work, timeouts, refusals and human-plus-verifier outcomes across its frozen request
mixture. It does not establish the trust effect of quiet delivery. [measured: EXP-98 preregistration]

## 9. Strongest case for streaming

Streaming is the strongest objection because it makes latency visibly causal. The user can see a
tool call start, notice a wrong direction, interrupt immediately and distinguish a slow worker from a
dead surface without trusting another status projector. Current Codex, Anthropic, OpenCode and Cursor
control protocols all expose lifecycle or session events, so streaming is the incumbent interaction
pattern, not a straw proposal. [cited: official `[FULL]` sources in the bibliography]

Silence also has a known psychological cost: a static card can feel like abandonment, and a faulty
checkpoint projector can say `Working` with the same misplaced authority as a spinner. This design
has no measured evidence that users will trust the card, check less often or wait longer. [asserted]

The concession is explicit: **streaming beats total silence**. This design does not choose total
silence; it chooses durable liveness over narrative progress and retains an explicit verbose
visibility override. It wins only if users interrupt and poll less without more abandoned work or
human-rejected deliveries. If a matched trial shows the streaming arm reduces abandonment or catches
bad direction without increasing principal attention, streaming milestones become the default while
the estimate, checkpoint and done predicates remain. [asserted]

## 10. Plain answer and delta

The plain answer would be: show an ETA, run in the background, send status updates and reply when
done. [asserted]

The delta is four enforceable statements: the ETA is an append-only evidence record; working means a
fresh sealed checkpoint; a restart continues the same candidate from that checkpoint; and done means
the frozen verifier predicate passed while preserving the later human verdict that measures beta.
[asserted]
