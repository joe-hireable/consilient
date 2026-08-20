# 0034. Detect stalls by artefact progress, and default to diagnosis rather than killing

- **Status:** PROVISIONAL — the design is well-sourced; its parameters are not yet measured here
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the requirement), Claude Opus 5 (the mechanism)
- **Inquiry tier reached:** T2 — prior art from systems that solved this, plus three measured
  failures in this repository tonight
- **Executable model:** none. The thresholds are preferential and are named as such.

## Context

Joe, 20 August 2026: *"Orchestrators/manager agents/leadership agents should be able to catch
and fix stalled agents etc. We waited ages on that."*

He is describing a real incident. Three orchestration failures occurred in this session, all
by the agent now writing this ADR: [measured]

1. **Wrong identity.** Liveness was bound to `codex.exe` PID 54404, taken to be the running
   experiment. It was the orchestrator's own session, started 18:58:59. The actual runner had
   exited cleanly at 01:27:38. A completed experiment looked alive for thirty minutes.
2. **False success.** A launcher exited 0 while the work never started: a directory change
   failed and a following `echo` succeeded, so the exit code reported success for nothing.
3. **Silent crash.** The relaunched run died immediately on a `UnicodeDecodeError`. A process
   watch would have reported it healthy for as long as the process took to exit.

## The finding that changed this decision

The obvious lesson from those three is "watch harder". The prior art says the opposite, and
this is the single most important thing in this ADR:

**The common, expensive production failure is a watchdog killing healthy or completed work —
not a supervisor waiting too long.** [cited]

- Airflow marked tasks that had already logged `Task exited with return code 0` as zombies and
  set them to *failed*, because zombie detection consulted a stale heartbeat rather than the
  task's own terminal record. [cited]
- LangGraph Cloud re-dispatches tool calls exceeding roughly 180 s from the last checkpoint
  while the original is still running, producing a reported *2–3× redundant work and cost*,
  with both copies completing successfully. The operator could not determine what criteria
  marked a run stale. [cited]
- Celery's Redis and SQS transports redeliver a task once the broker visibility timeout
  elapses — default one hour and thirty minutes respectively — even while the worker is still
  processing it. [cited]
- Ray marks healthy nodes dead on missed raylet heartbeats under heavy I/O and saturated CPU,
  which are exactly the conditions long agent work creates. [cited]
- Kubernetes' own documentation warns that incorrect liveness probes cause cascading failures,
  and that if a process crashes on its own when unhealthy *"you do not necessarily need a
  liveness probe"*. [cited]

Tonight's failure cost thirty minutes of waiting. The failure the literature documents costs
duplicated spend, destroyed results and false failure records. **The two are not symmetric,
and a design that optimises against tonight's embarrassment will buy the more expensive
error.** [asserted]

## Decision

### 1. Liveness is never bound to process identity

A PID is not a durable identifier: PIDs are recycled — the Linux default maximum is 32768 —
which is why `pidfd_open()` exists. [cited] Tonight's incident is the general case, not a slip.

Where a process handle is needed, use a handle that cannot be recycled onto a different
process. Where possible, do not use one at all.

### 2. Three questions, three signals

Kubernetes separates startup, readiness and liveness because one timeout cannot answer three
questions. [cited] The same split applies here:

| Question | Signal | On failure |
|---|---|---|
| Did it start? | The artefact exists, or the run declared itself begun | Fail fast; a launcher's exit code is not evidence |
| Is it progressing? | The artefact grew or changed since the last sample | Diagnose — see §3 |
| Is it finished? | The artefact declares its own terminal state | Trust the artefact over any external timer |

**A terminal record in the artefact always outranks a stale liveness signal.** That single rule
is what Airflow lacked. [cited]

### 3. Detection defaults to diagnosis, not to killing

The Linux kernel's hung-task detector — the most battle-tested stall detector in existence —
takes no heartbeat at all. It samples externally observable scheduler state, reports tasks
unchanged for `hung_task_timeout_secs` (default 120 s) with a stack trace, and **defaults to
emitting a diagnostic rather than panicking**. [cited] systemd's watchdog sends `SIGABRT`
rather than `SIGKILL`, deliberately producing a core dump before the process dies. [cited]

Consilience follows both. On detecting no progress, the supervisor:

1. records a stall event with the evidence that led to it;
2. captures whatever diagnostic state is available;
3. escalates to the owner;
4. **does not terminate**, unless termination is separately authorised for that task.

Killing requires stronger evidence than stalling, because killing is the irreversible half.
Under ADR-0033 an irreversible action with material stake is a user-only decision unless the
task carries a standing termination authority fixed before it started.

### 4. Progress beats heartbeat, and both beat presence

A heartbeat is a claim by the reporter about itself; a progress signal is a claim about the
work. Temporal's activity heartbeat carries caller-supplied progress state for exactly this
reason. [cited] It also carries the trap that if a heartbeat timeout is configured but the
activity never heartbeats, **the timeout is silently ignored** — so a configured-but-unfed
progress channel must fail loudly at configuration time, not quietly at runtime. [cited]

### 5. Never reclaim by timeout alone

Timeout-based reclaim duplicates live work rather than recovering dead work. [cited] A task is
reassigned only when its lease has expired **and** its fencing epoch has been incremented, so
the displaced worker's writes are rejected rather than racing. That is ADR-0020's lease
machinery doing the job it already exists for.

### 6. The recovery policy is observable

LangGraph's reporter *could not determine what criteria the server used to mark a run stale*.
[cited] Every stall decision here records the signal, the threshold, the observed value and the
action taken, so an operator can dispute it from the trajectory alone.

## Evidence against

- **Every parameter here is preferential.** 120 s, 900 s, "no progress" — none is derived, and
  the kernel's 120 s default is for a different workload entirely. They will be wrong at first.
  [asserted]
- **Artefact progress fails for work that legitimately produces nothing for a long time** — a
  long model call, a large download, a compile. This design will call that stalled. The
  mitigation is a declared expected-progress interval per task type, which is another
  preferential parameter and another thing to get wrong. [asserted]
- **A stall detector that only diagnoses can be ignored**, and an escalation nobody reads is
  indistinguishable from no detector. ADR-0033's ask budget applies: a stall escalation is an
  interrupt and is spent from the same finite attention. [asserted]
- **Tonight's three failures were all caught by a person looking**, which is precisely the
  autonomy gap recorded in `../20-design/autonomous-execution-from-intent.md`. This ADR
  converts three of the seven unenforced catches into enforced ones and does nothing for the
  other four. [measured]
- No agent framework surveyed does this well; the design is assembled from adjacent fields.
  That is a reason for humility about it, not confidence. [asserted]

## Consequences

**Positive.** The three failure modes measured tonight become detectable without introducing
the more expensive failure of killing healthy work.

**Negative.** More configuration surface, and a class of false stalls on legitimately quiet
work.

**Neutral but load-bearing.** Every long-running task must now declare what artefact
constitutes its progress. A task that cannot name one cannot be supervised, and that is
information worth having before it runs.

## Enforcement

- Check: a supervisor that resolves liveness from a PID alone fails a fixture.
- Check: a terminal record in an artefact overrides a stale liveness signal — the Airflow
  regression as a test.
- Check: a configured progress channel that is never fed fails at configuration load, not at
  runtime — the Temporal trap as a test.
- Check: a stall event without signal, threshold, observed value and action fails schema
  validation.
- Check: reassignment requires an expired lease *and* an incremented fencing epoch; a race
  fixture proves the displaced worker's writes are rejected.
- Check: termination without a standing authority for that task is rejected at the boundary.

## What would overturn this

- **EXP-34** already counts what catches errors. If stall detection lands and the enforced
  fraction does not move, this machinery is not doing the job.
- If false stalls on legitimately quiet work exceed genuine detections over a fixed window,
  the progress signal is the wrong signal and heartbeats-with-progress-state should replace it.
- If no stall occurs at all across a meaningful window once tasks declare their artefacts, this
  is over-engineering built from one bad night, and should be cut to the artefact-existence
  check alone.
