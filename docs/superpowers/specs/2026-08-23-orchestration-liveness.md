# Orchestration liveness: consume available evidence, isolate writers, interrupt on decision change

**Correction:** the brief's logarithmic squad-size formula is not the current automatic policy.
[ADR-0077](../../decisions/0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md)
uses the dependence-robust `floor(epsilon / beta_upper)` candidate-exposure ceiling until dependence
is measured; evidence-role count remains ADR-0067's one-Owner, distinct-anchor decision, and
human-labelled beta is currently unavailable. [measured] [algebra]

- **Decision:** [ADR-0095](../../decisions/0095-project-orchestration-from-consumed-evidence-and-interrupt-on-decision-change.md).
  [measured]
- **Killing experiment:** [EXP-138](../../10-research/experiment-register.md#exp-138--does-evidence-consuming-supervision-reduce-actionable-stall-exposure-and-avoidable-silence).
  [measured]
- **Status:** specification only; no product behaviour, gate, route or command changes here.
  [measured]

## 1. Outcome and boundary

Consilient will close the ten measured failures in
[`orchestration-failure-modes-2026-08-23.md`](../../00-context/orchestration-failure-modes-2026-08-23.md)
with three mechanisms: one trajectory-derived lifecycle projection, one isolated contribution
protocol, and one decision-changing attention outbox. [asserted] The three are smaller than ten
patches because F-01, F-02, F-05, F-06, F-08, F-09 and F-10 are failures to consume an available
signal; F-03, F-04 and F-07 are the existing isolated-workspace and claim boundary. [measured]

The implementation must extend `coordination.py`, `work_items.py`, `events.py` as the single writer,
`scripts/run_loop.py`, the existing dispatch/landing path and the existing originating-conversation
projector. [asserted] It must not create a second scheduler, task store, status database, notification
authority, CLI subcommand or gate condition. [asserted]

This record specifies future implementation and its checks. It claims no implementation path,
changes no source file, leaves `routing_orchestration_enabled` false and does not authorise unattended
dependence on another repository. [measured] [asserted]

## 2. Ground and incumbent bar

### 2.1 Measured ground

The ten failures are consumed as written, not re-derived. [measured] The operational scratch driver
now contains local repairs for worktree isolation, commit-only landing, in-flight and built-unlanded
tracking, artefact-specific commit detection and a fail-closed test-summary parser, but
`.harness/build_driver.py` is gitignored scratch rather than product design. [measured]

The product substrate is narrower: `coordination.py` projects claims and their three release paths
but not output ownership; `work_items.py` appends opened, comment and bare completion events;
`events.py` is the validated append-only writer; and the loop records ticks and transcript growth but
does not project a dependency backlog or the four no-running states. [measured]

This decision extends, rather than restates, these existing contracts: [measured]

- ADR-0034: progress comes from the declared artefact, terminal artefact evidence outranks stale
  liveness, and a stall is diagnosed before any separately authorised kill. [cited]
- ADR-0071: sealed checkpoint progress, evidence-bound delivery and quiet exception delivery are
  prospective; a transcript or dirty tree is not a checkpoint. [cited]
- ADR-0072: work-item closure is evidence-bearing and separate from a later human verdict. [cited]
- ADR-0075: principal escalation stays closed to six protected/preference classes, and friction is a
  replayed ratchet rather than a mutable counter. [cited]
- ADR-0083: detailed live state is available on pull; ordinary state changes do not create chat
  messages. [cited]
- ADR-0091: write attempts get isolated indexes, landing takes only worker-owned commits, declared
  claims remain authoritative and EXP-130's import closure is a warning check, not a replacement.
  [cited] [measured]

### 2.2 Retrieved bar

No single reviewed system establishes the joined mechanism below; the bar is a composite, not an
exhaustive state-of-the-art claim. [asserted]

| Source | Bar consumed | Limit retained |
|---|---|---|
| [Kubernetes Job API](https://kubernetes.io/docs/reference/kubernetes-api/batch/job-v1/) and [Job controller](https://kubernetes.io/docs/concepts/workloads/controllers/job/), retrieved 2026-08-23 | Jobs expose separate active, ready, succeeded, failed and terminating counts; current terminal conditions wait for descendants to terminate. [cited] | Kubernetes warns that even a one-completion Job may start the same program twice; process execution and logical completion are not identical. [cited] |
| [Temporal Event History](https://docs.temporal.io/encyclopedia/event-history), [workflow execution](https://docs.temporal.io/workflow-execution), [activity failure detection](https://docs.temporal.io/encyclopedia/detecting-activity-failures) and [workflow failure detection](https://docs.temporal.io/encyclopedia/detecting-workflow-failures), retrieved 2026-08-23 | Durable history and replay make lifecycle state a projection; timeouts make lost work actionable, while heartbeats carry progress rather than completion. [cited] | An unhandled workflow-task failure can leave work open but unable to complete; durable history alone does not classify an unclearable queue. [cited] |
| [git-worktree(1)](https://git-scm.com/docs/git-worktree), retrieved 2026-08-23 | Linked worktrees have separate `HEAD` and `index`, deleting the shared-index race by construction. [cited] | Refs and object storage remain shared; contribution landing still needs attribution and serialisation. [cited] |
| [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/), [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) and [HA semantics](https://prometheus.io/docs/alerting/latest/high_availability/), retrieved 2026-08-23 | Alert state and delivery are separate; grouping and stable identities deduplicate an at-least-once delivery path. [cited] | Fail-open HA may deliver duplicates, so notification delivery cannot become authoritative run state. [cited] |
| Google SRE, [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/), retrieved 2026-08-23 | Interruptions should be actionable and low-noise; state that does not require action belongs in a dashboard or record. [cited] | Per-task alerting can become unmaintainable and train operators to ignore real pages. [cited] |

The bounded search used the official documentation queries `Kubernetes Job conditions terminal`,
`Temporal activity heartbeat workflow failure`, `git worktree per-worktree index`, `Prometheus
Alertmanager deduplicate`, and `Google SRE actionable alert`. [measured] OpenTelemetry was omitted
because the selected sources already cover lifecycle authority, progress and delivery; no claim is
made that it is inferior. [asserted]

The delta is not another event log or alert manager. [asserted] It is a deterministic join between
Consilient's evidence-bearing work contract, attributable Git contribution, fresh observations and a
principal-next-action predicate, with a regression check for every measured failure. [asserted]

## 3. Mechanism A — one evidence-consuming lifecycle projection

The trajectory remains authoritative. [cited: ADR-0006] A pure replay over its accepted prefix, the
declared plan and an explicit clock derives lifecycle state; it writes no shadow database and accepts
no free-form worker status. [asserted] Every derived value retains the event or artefact references
that produced it, and an available required signal which is absent from the derivation is a failed
invariant rather than an optional field. [asserted]

### 3.1 Orthogonal axes, not one overloaded status

Each durable item/attempt projects these axes independently: [asserted]

| Axis | Exact values | Evidence |
|---|---|---|
| Execution | `not_started`, `active`, `terminal` | Atomic claim plus controller-observed terminal event; process presence is diagnostic only. [asserted] |
| Contribution | `none`, `dirty_uncommitted`, `committed_unlanded`, `landed`, `quarantined` | Controller-generated contribution manifest and serial landing receipt. [asserted] |
| Dependency | `ready`, `waiting`, `blocked` | Frozen predecessor contracts, actual accepted artefact digests and typed blocker ownership. [asserted] |
| Verification | `not_run`, `passed`, `failed`, `check_error` | Exact verifier contract, executed artefact digest and parseable terminal receipt. [asserted] |
| Record integrity | `current`, `defective`, `check_error` | Repository bookkeeping checks, separately from the candidate verifier. [asserted] |
| Resource | `available`, `starved`, `unknown` | Fresh typed observations consumed by admission. [asserted] |

`closed` is derived only when execution is terminal, contribution is `landed`, dependencies match,
verification is `passed`, and every required adverse outcome is attached. [asserted] Record integrity
is deliberately not folded into verification: a correct artefact can be `closed` while repository
release remains `record_defective`, and a bad artefact cannot become correct because the register is
current. [asserted]

A failure counter increments only on a typed work/verifier failure attributable to the candidate.
[asserted] Refusal, launcher failure, timeout before candidate production, transport failure,
claim conflict, stale observation and landing conflict remain adverse attempt outcomes but do not
consume the work-failure retry allowance. [asserted] They may have their own finite infrastructure
ceiling so a broken runner cannot retry forever. [asserted]

### 3.2 The four no-running states

The following projection is evaluated when there is no `active` attempt. [asserted] Let `remaining`
be non-terminal items plus every unlanded contribution obligation; let `ready` be items whose
dependency and authority predicates pass before resource admission; and let a `resolver` be a live or
ready owned item, or a predeclared future observation/lease boundary that can clear a blocker without
new principal authority. [asserted]

| State | Mutually exclusive predicate | Required controller action |
|---|---|---|
| `finished` | `remaining` is empty and no contribution, verifier, dissent or record-release obligation remains. [asserted] | Emit the evidence-bound terminal delivery once. [asserted] |
| `starved` | `ready` is non-empty, but every otherwise eligible route is unavailable or `unknown` under a fresh resource observation. [asserted] | Retain the ready work; probe only under the frozen policy. Interrupt only when the exhaustion changes the delivery commitment or leaves no route. [asserted] |
| `waiting_dependency` | `remaining` is non-empty, `ready` is empty, and every critical-path blocker has a named resolver plus a future re-evaluation boundary. [asserted] | Record the blocker and next observation; do not claim finished and do not spin without that boundary. [asserted] |
| `blocked` | `remaining` is non-empty, `ready` is empty, and at least one critical-path blocker has no live, ready or scheduled resolver under the current authority and contract. [asserted] | Append an adverse attention incident in the same supervision tick; do not tick quietly. Ask the principal only if the underlying cause independently matches ADR-0075's closed set. [asserted] |

The precedence is `finished`, then `starved`, then `waiting_dependency`, otherwise `blocked`; the
predicates above make the result unique. [algebra] A renderer may not collapse any of them into
`idle`, `working` or `nothing running`. [asserted]

ADR-0034's artefact rule remains load-bearing. [cited] A new sealed checkpoint, attributable worker
commit, accepted verifier receipt or terminal contribution manifest can advance progress; a PID,
process name, launcher exit, stdout heartbeat or unchanged re-write cannot. [asserted] No artefact
progress plus no startable work plus a non-empty backlog is a stall; `blocked` escalates immediately,
while `waiting_dependency` and `starved` must retain their named next observation rather than tick
without one. [asserted]

### 3.3 Terminal outcome accounts for output as well as the claim

Before appending a terminal dispatch outcome, the controller—not the worker—inspects the attempt's
isolated tree and records one contribution manifest with: [asserted]

- attempt, run, work-item, claim-epoch, base-commit and observed-head identities; [asserted]
- the ordered worker-owned commits reachable from the worker head but not the landing head;
  [asserted]
- every tracked uncommitted change as canonical path, Git status and content digest, or a typed
  deletion marker; [asserted]
- every declared untracked deliverable as canonical path and content digest; unexpected untracked
  output is quarantined and cannot satisfy delivery; [asserted]
- declared paths, actual changed paths, verifier/artefact references, landing owner and one landing
  disposition: `none`, `pending`, `landed`, `quarantined` or `abandoned_with_reason`. [asserted]

Failure to inspect the tree is `unknown` and therefore incomplete, never clean. [asserted] An exit
with any tracked uncommitted change is `dispatch.outcome=incomplete`, even when its process exited
zero or its prose says success. [asserted] The claim may still release through the existing terminal
path, but the landing obligation survives under the named owner until it is committed, deliberately
quarantined or abandoned with evidence. [asserted] This separates mutual exclusion from output
custody: a dead process does not hold a path claim forever, and its work does not disappear with the
claim. [asserted]

### 3.4 Fresh observations and three-valued checks

Every cached observation used for admission or routing records `source`, `observed_at`, `valid_for`,
`value|unknown` and the observing artefact/event identity. [asserted] The consumer records that
identity and evaluates expiry from `observed_at + valid_for`; file modification time, read time and
cache presence cannot refresh the observation. [asserted] Missing, unparsable or expired readings are
`unknown` and follow the existing fail-closed policy. [asserted]

Every verifier produces exactly `passed`, `failed` or `check_error`. [asserted] `failed` means the
executed checker completed its declared protocol and the exact artefact violated the predicate;
`check_error` means the predicate was not evaluated, including unsupported flags, usage errors,
missing summaries and parser failure. [asserted] Neither state is inferred from an exit code alone,
and an absent summary never passes. [asserted]

## 4. Mechanism B — isolated, attributable contributions

This mechanism adopts ADR-0091 rather than creating another workspace protocol. [cited] Every
write-admitted attempt receives a runtime-conformant isolated worktree and Git index; staging in the
shared main tree is refused while a write claim is active. [asserted] Claim admission remains atomic
at the single writer and the commit boundary rejects a stale fencing epoch. [asserted]

Landing is serial and contribution-based. [asserted] The controller computes the ordered commits
reachable from the worker head but not the current landing head and cherry-picks only those commits;
it never merges the worker snapshot. [asserted] A worker commit therefore carries additions it made,
not the absence of work landed after its base. [asserted] A complete worker whose commits cannot yet
land projects `committed_unlanded`, is excluded from dispatch candidates and keeps its commits safely
reachable. [asserted]

Declared claims remain the authority over code, documentation, generated files and failure branches.
[cited: ADR-0091] EXP-130's transitive import closure stays a warning check because it missed
non-Python and event-literal coupling and reduced measured safe width. [measured] At the execution
boundary, the actual contribution manifest must be a subset of the declared claim; an attempt that
needs another path stops before write/stage/commit and emits `claim_expansion_required`. [asserted]
The derived warning and actual-diff check are complementary: the former catches a likely omitted
Python consumer before work, while the latter rejects every undeclared path after observation.
[asserted]

## 5. Mechanism C — a consequential-transition outbox

Detailed state remains pull-only under ADR-0083. [cited] F-10 adds a narrower push rule: when a
trajectory transition changes what the principal should do next, the single writer atomically
appends an `attention.required` outbox record alongside the adverse transition before the supervisor
sleeps or starts unrelated work. [asserted] Delivery is at-least-once and records a separate
`attention.outcome`; it never decides run state, approval or acceptance. [asserted]

`attention.required` carries a stable incident id and deduplication key, causal event/artefact
references, prior and new principal-next-action, reason class, impact on the delivery commitment,
minimal secret-free message digest and `deliver_by`. [asserted] `attention.outcome` carries the same
incident id, `delivered|failed`, transport identity, attempt time and receipt or failure evidence.
[asserted] Duplicate delivery is tolerated and deduplicated by incident id; a new interruption is
earned only by a changed action, impact or evidence-bound terminal disposition. [asserted]

### 5.1 What earns interruption

An interruption is earned only when all four predicates hold: [asserted]

1. a typed transition changes principal-next-action from `wait` to `inspect_failure`, `replan`,
   `stop_waiting`, `choose_preference` or one of ADR-0075's protected authority actions, or invalidates
   the promised artefact/delivery window; [asserted]
2. the cause is unresolved at the accepted event prefix and is not merely a process, heartbeat or
   model assertion; [asserted]
3. the message states the changed fact, its evidence, what the system already tried, the current
   default and whether principal action is actually required; [asserted]
4. no delivered open incident already carries the same next action, impact and cause digest.
   [asserted]

The qualifying transitions are a queue entering `blocked`; an adversarial or frozen verifier
rejecting the candidate; every eligible resource pool becoming exhausted or `unknown`; a frozen
assumption being falsified so the plan or promise changes; a terminal incomplete contribution; an
unrecoverable failure; a commitment breach/revision; and a genuine ADR-0075 principal-only decision.
[asserted]

An unclearable queue is an adverse controller notice, not a seventh principal escalation class.
[asserted] The message may say `No action required; delivery cannot continue under the current
contract` when the correct next action is to stop waiting or inspect the failure. [asserted] It asks
the principal only when the blocker independently enters `money`, `credential`, `external_exposure`,
`unrecoverable_state_loss`, `principal_authority` or `preference`. [cited: ADR-0075]

Ordinary worker starts, checkpoints, self-clearing retries, successful landings, one exhausted pool
with another eligible route, refreshed observations, internal discussion and unchanged estimates stay
quiet. [asserted] A bookkeeping defect with a startable machine-owned repair stays quiet unless it
blocks the delivery commitment; if it does, the resulting `blocked` transition earns one notice.
[asserted] The expected final delivery remains ADR-0071's delivery message rather than an exception
interruption. [cited]

Quiet delivery and pull-only exposure therefore still govern what is sent. [asserted] The outbox
governs the exceptional transition that must interrupt; its minimal message links to the pull surface
for detail rather than streaming state. [asserted]

### 5.2 Silence and noise are paired ratchets

No mutable counter is added. [asserted] From replayed events, for each `attention.required` incident
`i`, let `D_i=1` when a matching delivery receipt exists by `deliver_by`, otherwise `0`. [algebra]

`avoidable_silence_count = sum(1 - D_i)` over required incidents. [algebra]

A principal status request after `attention.required` and before delivery is retained as direct
evidence that the silence reached the user, but the missed deadline already counts; transport failure
does not turn silence into success. [asserted] Zero required incidents is `unavailable`, not zero.
[asserted]

`unearned_interruption_count` is the number of delivered exception messages with no matching open
`attention.required` incident at delivery time. [algebra] This is the anti-noise half: lowering silence
by paging every event fails the mechanism. [asserted]

As in ADR-0075, consecutive non-overlapping windows of 30 required incidents ratchet the avoidable-
silence ceiling down to the lowest completed-window count; a later rise is a harness defect, not a
request for the principal to diagnose it. [asserted] Consecutive non-overlapping windows of 30
exception deliveries apply the same rule to unearned interruptions. [asserted] Both report raw
numerator and denominator, all delivery failures and all reason classes. [asserted]

## 6. One failing check for every measured failure

These checks are same-commit requirements on future implementation; none is claimed to exist in this
specification-only change. [measured] [asserted]

| Failure | Mechanism | Regression check that must fail |
|---|---|---|
| **F-01 — silent stall** | Lifecycle projection plus attention outbox. [asserted] | `test_f01_four_no_running_states`: replay four prefixes differing only in remaining work, resolvers and eligible resources; require exactly `finished`, `waiting_dependency`, `blocked`, `starved`. Vary process presence without changing the result, and require `blocked` to append one `attention.required` before the next tick. [asserted] |
| **F-02 — stranded output** | Terminal contribution manifest plus durable landing owner. [asserted] | `test_f02_dirty_exit_is_incomplete`: let a child exit zero after modifying seven tracked files; require exact path/status/digest entries, `incomplete`, a released claim, a surviving landing obligation and no success/closure projection. [asserted] |
| **F-03 — shared index** | Runtime-conformant per-attempt worktree/index. [cited: ADR-0091] | `test_f03_parallel_writers_have_distinct_indexes`: two concurrent writers must report different `git rev-parse --git-path index` values, stage only their files and commit successfully; staging a write attempt in the shared main tree must refuse. [asserted] |
| **F-04 — snapshot merge reverts unseen work** | Serial commit-only landing. [cited: ADR-0091] | `test_f04_landing_takes_only_worker_commits`: branch a worker, land an unrelated main commit, commit worker output, then land it; both changes must remain and any whole-head merge path must be structurally unreachable. [asserted] |
| **F-05 — duplicate dispatch and false retries** | Execution/contribution axes and typed failure accounting. [asserted] | `test_f05_active_and_built_unlanded_are_not_candidates`: replay one live attempt and one worker-owned unlanded commit; neither may dispatch, an infrastructure refusal must not increment work failures, and only a typed candidate/verifier failure may consume the retry allowance. [asserted] |
| **F-06 — bookkeeping masquerades as build failure** | Separate verification and record-integrity axes. [asserted] | `test_f06_record_defect_does_not_reclassify_candidate`: remove a nominated EXP heading from an otherwise accepted candidate; the item remains artefact-accepted, repository release becomes `record_defective`, a repair item is named, and neither `build_failed` nor a green release is permitted. [asserted] |
| **F-07 — under-declared claims** | Declared authority, EXP-130 warning and actual-diff subset enforcement. [cited: ADR-0091] | `test_f07_failure_branch_cannot_escape_claim`: exercise a failure branch that needs an undeclared file; it must stop with `claim_expansion_required` before write/stage/commit. A Python omitted-dependent fixture must also emit the warn-only coverage event without expanding authority. [asserted] |
| **F-08 — stale cache as truth** | Typed observation envelope consumed by reference. [asserted] | `test_f08_age_belongs_to_observation`: set an expired `observed_at`, then touch/rewrite the cache file; admission must still receive `unknown` and refuse. A fresh observation event, not file mtime, is the only recovery. [asserted] |
| **F-09 — proxy verification** | Artefact-bound three-valued verifier receipt. [asserted] | `test_f09_checker_error_is_not_false_or_pass`: run an unsupported checker flag and a zero-exit output with no required summary; both must be `check_error`. A real artefact predicate false must separately be `failed`; neither can be `passed`. [asserted] |
| **F-10 — user had to ask** | Consequential-transition outbox plus silence/noise ratchets. [asserted] | `test_f10_only_decision_change_interrupts_and_is_receipted`: replay quiet checkpoints plus one blocked queue, one failed adversarial review, one exhausted pool and one falsified assumption; require one deduplicated delivery per changed next action. Removing one receipt must raise avoidable silence by one; injecting a progress message must raise unearned interruption by one. [asserted] |

A source scan must also prove no second orchestration-state writer, landing path or principal-delivery
path bypasses these three mechanisms. [asserted]

## 7. Consilient-specific constraints

No monitoring agent is added. [asserted] The lifecycle projector is deterministic; a role exists only
when it introduces a different class of facts such as executing the artefact, driving a browser or
checking a citation against its primary source. [cited: `CONSILIENCE.md`] A reviewer reading the same
diff as the author remains echo. [cited]

Candidate exposure uses ADR-0077's dependence-robust ceiling; role composition uses ADR-0067's one
Owner and distinct-anchor rule. [cited] Human-labelled beta is unavailable, so no automatic numeric
relaxation or extra candidate is admitted by this specification. [measured]

Verdicts, approvals, gate lifts and spend remain principal-authored under V0-18. [cited] An
`attention.required` record may propose or report; neither it nor a manager/Owner can author the
principal's response. [asserted] The local authorship boundary remains incomplete until a trusted
first-party ingress exists, so a caller-declared principal field is not authentication. [measured]

## 8. Validation and stopping rule

EXP-138 is the prospective killing test. [measured] It pairs the pinned pre-decision supervisor with
the treatment on a frozen fault bank derived from F-01 to F-10, then runs the treatment with the
control in shadow on consecutive real local work. [asserted] It measures actionable-stall exposure,
avoidable silence, unearned interruptions, false terminal states and introspection overhead under a
fixed stopping rule; adverse and missing outcomes remain in their assigned arm. [asserted]

The design loses if any fixture can project false `finished`/success, any dirty tracked output can
close, any stale observation can become current through file mtime, any required interruption is
silenced, or treatment introspection exceeds its pre-registered overhead ceiling. [asserted] A null
or insufficient-data result cannot be upgraded into a benefit claim. [asserted]

## 9. Evidence against — the simpler scheduler may be the honest answer

The strongest objection is that this is over-instrumentation built from one bad afternoon of scratch
code. [measured] F-03 disappeared with worktrees; F-04 disappeared with cherry-pick; F-08 needs one
timestamp comparison; F-09 needs one parser result; and a small scheduler with `ready`, `running`,
`blocked`, `done`, a dirty-tree check and one actionable alert could cover most observed harm.
[asserted] Six axes, manifests, causal outbox records and two ratchets can spend more CPU, bytes,
implementation effort and maintainer attention describing work than doing it. [asserted]

Google SRE's warning supports the objection: component- or task-level alerts become noisy and
unmaintainable, while only urgent actionable symptoms should interrupt a person. [cited] Kubernetes,
Temporal and Alertmanager also separate lifecycle, replay and notification rather than offering one
giant self-observing scheduler. [cited] The ten incidents are one repository, two days and one scratch
driver; they do not establish a population rate. [measured]

The objection is conceded at the implementation boundary. [asserted] The six axes are pure fields in
one replayed projection, not services or agents; one contribution manifest replaces ad hoc Git probes;
one outbox record groups a causal incident; routine transitions stay pull-only; and no numeric tuning,
database, daemon, workflow engine or alerting dependency is added. [asserted] If the same guarantees
fit a smaller internal representation, that representation wins. [asserted]

EXP-138 gives the objection teeth: the treatment must reduce actionable-stall exposure and silence
without false terminal states, unearned interruptions or more than the frozen overhead ceiling.
[asserted] Failure removes the joined projection/attention claim and retains only the independently
necessary worktree, commit-only landing, dirty-exit and fresh-observation guards. [asserted]

## 10. Plain answer and delta

The plain answer is: give every writer its own worktree, cherry-pick only its commits, track active and
unlanded work, fail dirty exits, timestamp observations, distinguish check failure from checker error,
and page only on an actionable block. [asserted]

The delta is structural traceability: the plain guards share one evidence-replayed lifecycle, every
one of F-01 to F-10 has a named killing fixture, and a missed required notice is itself measured and
ratcheted without turning ordinary progress into noise. [asserted] If EXP-138 finds no measured delta,
the plain answer wins. [asserted]
