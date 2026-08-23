# 0095. Project orchestration from consumed evidence, isolate contributions, and interrupt on decision change

**Correction:** the incoming brief's logarithmic squad ceiling is not current policy; ADR-0077 uses
the dependence-robust `floor(epsilon / beta_upper)` candidate-exposure ceiling until dependence is
measured, while evidence-role count remains ADR-0067's one-Owner, distinct-anchor decision.
[measured] [algebra]

- **Status:** PROVISIONAL — EXP-138 can remove the joined lifecycle/attention mechanism; ADR-0091's
  independently grounded workspace and claim decisions do not depend on that result. [asserted]
- **Date:** 2026-08-23
- **Deciders:** Joe Brown supplied the requirement and the ten measured failures; Codex dispatch
  `20260823T132214-2271877ec3` owns this provisional mechanism, which he has not reviewed. [measured]
- **Inquiry tier reached:** T1 ground — current source, ten measured failures and retrieved primary
  system documentation; T3 is pre-registered as EXP-138 and unrun. [measured]
- **Executable model:** none — this selects discrete state, custody and interruption invariants;
  EXP-138 measures the uncertain operational effect directly. [asserted]

## Context

On 22–23 August 2026, orchestration in this repository produced ten failures in which work appeared
finished while blocked, output survived without an owner, parallel writers shared one Git index, a
worktree merge carried stale absence, live/built work was re-dispatched, bookkeeping impersonated
candidate failure, claims omitted reachable paths, stale observations drove routing, proxy checks
misclassified artefacts and the principal had to ask for material status. [measured:
`../00-context/orchestration-failure-modes-2026-08-23.md`]

Nine failures shared one shape: evidence already existed but the scheduler did not consume it.
[measured] F-03 was a shared-state constraint and was removed operationally by per-writer worktrees.
[measured] Treating the incidents as ten patches would preserve the same omission at ten boundaries.
[asserted]

The current product already has the right authorities but not the joined projection.
`coordination.py` projects claims and three release paths; `work_items.py` carries trajectory-backed
items; `events.py` is the single append-only writer; and `scripts/run_loop.py` records tick outcomes
without process-identity liveness. [measured] ADR-0034 owns artefact progress; ADR-0071 owns sealed
checkpoint liveness and quiet delivery; ADR-0072 owns evidence-bound closure; ADR-0075 owns the closed
principal escalation set and friction ratchet; ADR-0083 owns pull-only detailed state; and ADR-0091
owns isolated write workspaces, declared claims and EXP-130's warn-only coverage check. [cited] F-04
supplies the separate commit-only landing requirement consumed by this decision. [measured]

The operational repairs in `.harness/build_driver.py` are evidence, not a product boundary.
[measured] The full contract is
[`2026-08-23-orchestration-liveness.md`](../superpowers/specs/2026-08-23-orchestration-liveness.md).
[measured]

### Incumbent bar

The retrieved bar is composite rather than a claim that one system is best. [asserted] Kubernetes
Jobs separate active/ready/succeeded/failed/terminating state and delay terminal conditions until
descendants terminate; Temporal replays durable history and treats heartbeat as progress rather than
completion; Git worktrees isolate `HEAD` and `index`; Prometheus/Alertmanager separates alert state
from at-least-once grouped delivery; and Google SRE limits interruption to actionable low-noise
symptoms. [cited: official sources linked in the companion specification, retrieved 2026-08-23]

Those mechanisms do not by themselves join evidence-bound work closure, attributable Git output,
fresh resource observations and a principal-next-action predicate. [asserted] That join, and its
failure-by-failure checks, is the proposed delta. [asserted]

## Decision

Consilient will use three mechanisms, all extending existing boundaries. [asserted]

### 1. Project lifecycle from consumed evidence

A pure replay over the accepted trajectory prefix, declared work graph and explicit clock will
project independent execution, contribution, dependency, verification, record-integrity and resource
axes. [asserted] No worker may set a free-form status and no second state store becomes authoritative.
[asserted]

At a settled boundary with no active or startable attempt, let `R` mean remaining work or contribution
custody, `Q` mean dependency/authority-ready work, and `C` mean that every critical blocker has both a
named resolver and a future re-evaluation boundary. The projection exposes exactly one of: [asserted]

- `finished`: `not R`; [asserted]
- `starved`: `R and Q`; at a settled boundary every otherwise eligible route is unavailable or
  unknown; [asserted]
- `waiting_dependency`: `R and not Q and C`; [asserted]
- `blocked`: `R and not Q and not C`, including a resolver with no re-evaluation boundary. [asserted]

A fresh available route must dispatch or yield a typed failure before classification; the four rows
are disjoint and exhaustive. [algebra] A renderer may not collapse them into `idle`, `working` or
`nothing running`. [asserted]
No artefact progress plus no startable work plus a non-empty backlog is a stall. [cited: ADR-0034]
`blocked` records an adverse attention incident in the same supervision tick; it asks the principal
only when the blocker independently matches ADR-0075's closed six-class set. [asserted]

The same projection separates candidate verification from repository bookkeeping, counts only typed
candidate/verifier failures against the work retry allowance, evaluates cache age from the
observation timestamp rather than file metadata, and represents verifier results as
`passed|failed|check_error`. [asserted] An absent summary or failed checker is never a pass or a
candidate failure. [asserted]

### 2. Make contribution custody explicit and keep writers isolated

Every terminal dispatch records a controller-derived contribution manifest: attempt/base/head
identities, ordered worker-owned commits, every tracked dirty path/status/content digest, declared
untracked deliverables, actual-versus-claimed paths, landing owner and disposition. [asserted] An
inspection failure is unknown/incomplete, and any tracked uncommitted change makes the terminal
outcome incomplete even after exit zero. [asserted] Claim release and output custody are separate:
the claim may release while a durable landing obligation remains. [asserted]

The attempt/root identity is durable before child start. [asserted] Restart or claim-expiry handling
reconciles every non-terminal attempt root and appends its manifest and landing owner before the item
can redispatch or close. [asserted] A controller crash after a dirty write therefore cannot turn
absence of a terminal event into absence of output. [asserted]

ADR-0091's isolated runtime-conformant worktree/index remains the write boundary. [cited] Landing is
serial and cherry-picks only commits reachable from the worker head but not the current landing head;
the worker snapshot is never merged. [asserted] Active and committed-unlanded attempts are not
dispatch candidates. [asserted]

Declared claims remain authoritative. [cited: ADR-0091] EXP-130's import closure remains a warning,
not an automatic authority expansion. [measured] Each write-admitted route must enforce the declared
repository-path set before mutation or be ineligible; both cooperative and direct shell/tool attempts
outside it are refused with `claim_expansion_required`. [asserted] This mediates only repository
writes, not reads, network or external effects, and therefore does not add the general hermetic
sandbox rejected by ADR-0091. [cited] [asserted] The terminal actual-diff subset check quarantines a
confinement defect before stage, commit or landing. [asserted]

### 3. Interrupt on a changed principal-next-action, not on activity

Detailed state remains pull-only under ADR-0083. [cited] A pure projection over causal transitions
derives each expected incident and deadline independently of the outbox. [asserted] In the same
single-writer transaction as a decision-changing adverse transition, Consilient appends the stable
`attention.required` outbox incident before the supervisor sleeps or begins unrelated work.
[asserted] A separate `attention.outcome` records at-least-once delivery; delivery never changes run
state, acceptance, authority or a human verdict. [asserted]

An interruption is earned only when evidence changes the principal's next action or invalidates the
promised artefact/delivery window, remains unresolved, states what changed and what the system tried,
and is not a duplicate incident. [asserted] Qualifying transitions are a blocked queue, failed frozen
or adversarial verification, exhaustion/unknown state across every eligible pool, falsified frozen
assumption, terminal incomplete output, unrecoverable failure, commitment change and a genuine
ADR-0075 principal-only decision. [asserted]

Worker starts, checkpoints, self-clearing retries, ordinary landings, one exhausted pool with a live
alternative and unchanged commitments stay quiet. [asserted] The minimal exception links to the
pull surface for detail, resolving the apparent tension with ADR-0083: pull governs state exposure;
the outbox governs an exception that earns interruption. [asserted]

The deadline is projected from the causal event, not chosen by the outbox: the production default is
five minutes after acceptance. [asserted] Existing and already-missed commitments remain breach
evidence but do not create a retroactive transport deadline. [asserted] From
replay, `avoidable_silence_count` left-joins expected incidents to outbox rows and receipts; an omitted
row, a late/missing receipt or a first-party status request before receipt each counts as silence.
[algebra] Zero expected incidents is unavailable. [asserted] `unearned_interruption_count` counts
delivered exceptions with no expected causal incident. [algebra] Consecutive non-overlapping windows
of 30 expected incidents ratchet silence down to the lowest completed-window count; windows of 30
exception deliveries apply the same ratchet to noise. [asserted] A later rise is a harness defect and
never a request for the principal to diagnose it. [asserted]

## Evidence

- `[measured]` Ten observed failures, recorded in the named context document, each expose an available
  but unconsumed process, artefact, commit, register, claim or observation signal; only F-03 requires
  deletion of shared index state.
- `[measured]` Current claims release through work-item completion, terminal dispatch or expiry, but
  terminal dispatch has no contribution-custody contract.
- `[measured]` Current loop status consumes tick events and transcript bytes rather than a PID, but
  has no work graph from which to distinguish the four zero-active states.
- `[measured]` EXP-130 found import-derived coverage useful only as a check: it missed non-Python and
  event-literal coupling and reduced measured safe concurrency.
- `[measured]` The current beta projection has insufficient human-labelled evidence, so no numeric
  relaxation of automatic candidate exposure or composition is licensed.
- `[cited]` Kubernetes, Temporal, git-worktree, Prometheus/Alertmanager and Google SRE supply the
  retrieved lifecycle, isolation and actionable-notification bar linked in the specification.
- `[algebra]` Keeping verification and record integrity as independent axes prevents either predicate
  from changing the truth value of the other; closure is their conjunction with contribution and
  dependency acceptance.
- `[algebra]` `avoidable_silence_count = sum(1 - D_i)` over causally expected incidents, where `D_i`
  requires both the materialised incident and delivery before its deadline and any first-party status
  request; omission cannot shrink the denominator.
- `[asserted]` One evidence projection, one contribution protocol and one outbox will prevent the
  measured recurrences with less complexity than ten independent fixes. EXP-138 tests that claim.

## Evidence against

**The strongest case is that this is over-instrumentation and the honest answer is a smaller
scheduler.** [asserted] Most failures occurred during one bad afternoon of scratch orchestration;
F-03 and F-04 already reduce to worktrees and cherry-pick, F-08 to a timestamp comparison, F-09 to a
three-valued parser, and F-02 to a dirty-tree check. [measured] A scheduler with `ready`, `running`,
`blocked`, `done`, one contribution check and one actionable notification could cover most harm
without six projected axes, causal outbox records and two ratchets. [asserted]

The scheduler watching itself this closely may spend more CPU, trajectory bytes and maintainer time
on introspection than on useful work. [asserted] A detailed state vocabulary can also produce a false
sense of control: the projector may classify its own incomplete evidence precisely while the
artefact remains wrong. [asserted] More instrumentation creates more schemas and parsers that can
themselves fail F-06 or F-09. [asserted]

Google SRE supplies evidence for the objection: task-level alerts become noisy and unmaintainable,
and pages should be reserved for urgent actionable symptoms. [cited] The ten incidents are one
repository over two days; their rate and transfer are unknown. [measured]

The objection is conceded unless the mechanism stays a projection and wins EXP-138. [asserted] The
decision adds no monitor agent, daemon, database, dependency, adaptive numeric tuning policy or raw
progress notification. [asserted] The six axes are fields of one replay, the contribution manifest replaces
ad hoc Git probes, one incident groups causal transitions, and routine state remains pull-only.
[asserted] A smaller internal representation which passes all ten fixtures is compliant and should
replace this vocabulary. [asserted]

EXP-138 removes the joined lifecycle/attention claim if it fails to reduce actionable-stall duration
and avoidable silence, emits false terminal success, exceeds its registered noise ceiling, or exceeds
its frozen supervisor-CPU ceiling. [asserted] The independently necessary worktree, commit-only landing,
dirty-exit and fresh-observation guards survive because their correctness does not depend on an
aggregate benefit claim. [asserted]

## Consequences

**Positive** — every terminal claim has output custody; zero-active work has a precise state;
bookkeeping cannot impersonate candidate quality; stale data and checker errors fail closed; and a
decision-changing silence becomes a measured regression. [asserted]

**Negative** — replay and terminal inspection cost time and bytes; contribution manifests expose
more local state to the private trajectory; delivery needs stable incident identities and receipts;
and the projection itself becomes a tested product boundary. [asserted]

**Neutral but load-bearing** — `events.py` remains the sole writer; `dispatch.py` and
`scripts/run_loop.py` remain the execution boundary; detailed state remains pull-only; no seventh CLI
command, second orchestrator, dependency, gate change or routing enablement is introduced. [asserted]

One Owner remains the default. [cited: ADR-0067] Every added role must name a different class of
facts; same-evidence review is echo. [cited: `CONSILIENCE.md`] Verdicts, approvals, consent, gate lifts
and spend remain principal-authored, and an informational block notice does not manufacture a new
authority class. [cited] [asserted]

## Enforcement

This specification-only commit adds no product implementation. [measured] Future implementation is
incomplete until the ten named fixtures in the companion specification all fail on regression and a
source scan proves no second state writer, staging/commit/landing path or principal-delivery path
bypasses them.
[asserted]

- **F-01 check:** the complete `R/Q/C` truth table projects exactly
  finished/waiting/blocked/starved; a startable item dispatches, process presence is irrelevant and
  blocked appends attention before the next tick. [asserted]
- **F-02 check:** crash after tracked writes but before accounting is reconciled on restart/expiry as
  incomplete, fully manifested and still owned before redispatch. [asserted]
- **F-03 check:** concurrent writers have different real indexes; shared-main staging refuses.
  [asserted]
- **F-04 check:** landing a stale-base worker takes only its commits and preserves newer main work.
  [asserted]
- **F-05 check:** active and built-unlanded work cannot redispatch; infrastructure faults do not
  consume work retries. [asserted]
- **F-06 check:** a missing register entry marks record integrity defective without calling an
  accepted candidate failed or allowing repository release. [asserted]
- **F-07 check:** cooperative and direct shell writes outside the declared set are refused before
  mutation; an injected confinement defect is quarantined before stage/commit/landing; EXP-130
  coverage stays warn-only. [asserted]
- **F-08 check:** touching an expired cache does not refresh its observation; admission sees unknown.
  [asserted]
- **F-09 check:** checker usage error and absent summary are `check_error`, never false or pass.
  [asserted]
- **F-10 check:** decision changes deliver one deduplicated exception; an omitted outbox row, missing
  receipt or asked-first request raises silence, a payload deadline cannot defer the projected one,
  a past commitment still gets a non-zero transport bound, and successive 30-event windows ratchet
  silence/noise ceilings and flag a later rise. [asserted]
- **Check:** `python .github/scripts/check_record_numbers.py`, direct exactly-one searches for
  ADR-0095 and EXP-138, the generated ADR-index check and the provisional-ADR experiment invariant.
  [asserted]
- **Fails CI:** record-level checks only in this commit; the F-01–F-10 checks must fail CI with their
  future implementation. [measured] [asserted]
- **Added in the same commit as the implementation:** required; no implementation ships here.
  [asserted]

## What would overturn this

EXP-138 is the killing experiment. [measured] The joined projection/outbox survives only if it beats
the fixed byte-frozen `ready|running|blocked|done` alternative across F-01/F-05/F-06/F-10 while
the six independently retained guards stay identical, and the treatment-only prospective window
meets the silence, asked-first, noise and supervisor-CPU ceilings with no false terminal success or
dirty closure. [asserted] Shadow prospective output is descriptive and supplies no causal effect.
[asserted]

The disposition is exhaustive and loss-first: any false `finished` result, dirty-output success,
stale-observation admission, verifier-error pass, omitted/late/asked-first expected interruption,
authority/privacy violation, missing treatment outcome or failed quantitative threshold is `loss`;
aggregate improvement cannot average it away. [asserted] With no loss, an incomplete horizon,
comparison, common instrument or minimum incident/CPU denominator is `insufficient_evidence`; the ADR
remains provisional and the operational default is the simpler scheduler plus independent guards.
[asserted] Only complete evidence satisfying every registered condition is `confirmed`. [asserted]

## Publication candidate?

**No.** The failure set is one repository over two days, the synthesis is unimplemented and EXP-138
has not run. [measured] [asserted] A publication candidate would require reproduced benefit and low
noise/overhead on a second public, permissively licensed orchestration corpus without weakening any
failure fixture. [asserted]
