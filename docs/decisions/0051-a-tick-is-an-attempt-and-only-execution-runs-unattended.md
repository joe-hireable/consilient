# 0051. A tick is an attempt, only execution-bearing work runs unattended, and there is no offline consolidation phase

- **Status:** **PROVISIONAL 21 August 2026.** Rests on `[asserted]` design over one `[measured]`
  β and one `[algebra]` identity. Named falsifiers: **EXP-70** (kills decision 2), **EXP-71**
  (constrains decision 5), **EXP-72** (would reverse decision 8), **EXP-73** (would reverse
  decision 7).
- **Date:** 2026-08-21
- **Deciders:** Joe Brown asked for loops, always-on agents, crons, heartbeats and "dreaming" to
  be theorised and then experimented on, with implementation not gated on long experiments. The
  mechanism, the two structures cut, and every objection below are mine.
- **Relates to:** [`0034`](0034-detect-stalls-by-artefact-progress-and-default-to-diagnosis.md)
  (the liveness signal this inherits), [`0039`](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md)
  (what unattended means and what still gates it),
  [`0049`](0049-experiments-inform-they-do-not-gate.md) and
  [`0050`](0050-gate-on-effect-size-not-on-uncertainty.md) (why this ships PROVISIONAL rather
  than waiting), [`0010`](0010-name-the-different-class-of-facts.md) (the class-of-facts test),
  [`0044`](0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md) (budgets),
  [`0007`](0007-cli-only-no-review-surface.md) and
  [`0036`](0036-upstream-first-adopt-contribute-never-silently-fork.md) (why no scheduler is built).
- **Inquiry tier reached:** T2 model — the load-bearing step is `[algebra]` over a `[measured]` β.
- **Executable model:** none. The closed form in decision 5 has no free parameter whose sign could
  flip: `n_max` is monotone decreasing in β by construction, so a CI sign check would assert an
  identity rather than a result. Gate G4 is also unsatisfied — nothing here is a one-way door, and
  EXP-70 names the deletion explicitly. [algebra]

## Update: 2026-08-22 — decision 5 superseded in part by ADR-0077

[ADR-0077](0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md) corrects the
candidate-exposure rule. The iid expression in decision 5 applies only to a measured, versioned,
non-adaptive dependence regime; otherwise the distribution-free ceiling is
`n_attempt_max = floor(epsilon / q_upper)`, with `q_upper := beta_upper` when bad-candidate
prevalence is unmeasured. [algebra] The recorded `epsilon = 0.40` result remains one candidate, but
the statement “one for any epsilon at or below 0.40” is false: `epsilon < beta_upper` admits zero.
[measured] [algebra] The rest of this ADR stands.

---

## Context

Joe wants the harness to keep working when he is not watching: loops, always-on agents, crons,
heartbeats, and the idea that a system might have an offline "dreaming" or consolidation phase.
He also wants the building not to wait on the experiments, which ADR-0049 and ADR-0050 have
already settled as the general rule.

Three things about this repository make the design less open than it looks.

**One.** Two scheduled sensing ticks already run on this machine. `Consilient-Capture-Health` and
`Consilience-EXP27-Collector` are both registered in Windows Task Scheduler and both report
`Ready` (queried 21 Aug 2026). [measured] The first invokes `scripts/capture_health.py`, whose own
docstring already draws the distinction this ADR generalises: *"This is deliberately a check and
not a heartbeat. A heartbeat asserts that a writer ran and proves nothing about the record."*
**The pattern is not being invented here. It is being named, bounded and given a falsifier.**

**Two.** `docs/20-design/work-modes.md` already carries the arithmetic that governs unattended
work, and it is unflattering. Unattended modes do not add human review capacity; they time-shift
when the review debt arrives. It calls "run more agents in the background" the feature that feels
productive while making the ceiling worse. [algebra] The same document registers the identity that
turns out to be decisive here: an unattended loop that resamples until the checks pass exposes the
verifier `n` times, so `P(bad ships) = 1 − (1−β)ⁿ`. [algebra]

**Three.** β is no longer unmeasured. EXP-47 measured composite β = **0.3132 [0.2926, 0.3346]** by
mutation testing in 104 seconds. [measured] That number turns the identity above from a warning
into a constraint with a value in it, and it is what decision 5 is built on.

### The version of the echo claim this ADR relies on, stated before it is used

`docs/10-research/formalising-echo-2026-08-20.md` found that the project's own sentence —
"agreement between agents that share evidence carries no information about the truth" — is **false
in its operational reading and vacuous in its strongest information-theoretic reading**. Shared-
evidence agents can improve a decision by averaging independent interpretation error; what they
cannot do is add information beyond the shared evidence, or remove a common error inside it.
[algebra] [cited]

**This ADR therefore does not claim that a reflection loop cannot help.** It claims the narrower
and defensible thing, which is that document's own proposed rule:

> Agreement is not independent corroboration unless each conclusion traces to a truth-relevant
> source signal whose incremental value or residual error dependence has been measured.

So a structure that produces no new source signal may still buy computation, and may still be a
useful aggregation method — but **it may not corroborate, may not accept, and may not be counted
as evidence.** Where such a structure also cannot be shown to buy computation for the same budget,
it is cut. That is the test applied below, and EXP-72 is the arm that would falsify the cut.

### The theorem, at the scope it actually has

The delegation theorem is cited in `AGENTS.md` working principle 6 and in the brief that produced
this ADR. It was verified against the source on 21 Aug 2026: Ruicheng Ao, Siyang Gao and David
Simchi-Levi, *On the Reliability Limits of LLM-Based Multi-Agent Planning*, arXiv:2603.26993,
submitted 27 March 2026. The abstract states that any delegated network is decision-theoretically
dominated by a **centralised Bayes decision maker with identical information access**. [cited]
`[ABS]`

**The object it dominates against is the unconstrained Bayes optimum.** What the abstract states
is a bound on *information*, not on *performance under a computation budget*, and it says nothing
about whether a bounded agent can perform the central computation. `formalising-echo` recorded the
same qualification independently. [cited]

The practical consequence, and the reason this is in the Context rather than a footnote: **"the
theorem shows an offline phase cannot help" is an over-reading and must not be written.** Decision
8 below declines the offline phase on different grounds, which are stated as such.

---

## Decision

### 1. A tick is an attempt, not a timer

**A tick is one bounded, budgeted, recorded attempt at a queued unit of work, whose contract is
fixed before it starts and which terminates in a recorded verifier outcome.** It is an ordinary
attempt under `v0-draft.md` §4.2 — goal, verifier contract, artefact boundary, budget, authority,
time bound and stopping rule fixed before work begins — and nothing else. A schedule decides only
*when* an attempt may start.

**There is no loop primitive, and no new event kind for one.** A loop is a schedule plus the
existing task machinery, which means loops inherit every invariant already enforced against
attempts (V0-03, V0-05, V0-20, V0-22, V0-25) instead of routing around them.

**A tick that cannot end in a recorded verifier outcome is not a tick.** That single sentence is
what excludes reflection loops, and it is mechanically checkable at the point a schedule is
registered.

### 2. Consilient does not build a scheduler

The operating system already has one. A tick is a CLI command; `cron`, `systemd` timers or Windows
Task Scheduler fire it. **No daemon**, consistent with ADR-0007's CLI-only surface and ADR-0036's
adopt-over-build rule.

Every tick command must be: **idempotent** (a double fire is not a defect), **non-zero on
failure** (a launcher's exit code is not evidence of the work, but it is evidence of the
launcher — ADR-0034's second measured failure), **self-recording** (it appends its own outcome, so
the artefact and not the scheduler is the record), and **invocable by hand** (a command that only
a schedule can run cannot be debugged).

The wrapper that already exists, `scripts/run-capture-health.cmd`, exists because *"a scheduled
task that fails silently is worse than none"*. That is the requirement, and it was learnt here
before this ADR. [measured]

### 3. Two classes of tick, and only one of them runs unattended today

| | **Class 1 — sensing** | **Class 2 — acting** |
|---|---|---|
| What it does | Executes a check and records the outcome | Dispatches a model against a queued task |
| New class of facts | The execution result: a fresh outcome nobody held | The **verifier outcome** at the end. The model's artefact is a hypothesis, not evidence |
| May dispatch a model | **No** | Yes |
| May write to the tracked tree | **No** — scratch worktree only | Yes, within its declared boundary |
| May accept an artefact | **No** | No. Only the verifier or the human accepts |
| Unattended today | **Yes** | **No** — supervised only, until Gate B |

Class 1 members today: the trajectory replay-and-digest check (`capture_health.py`), the
bare-agent fallback exercise (`run_fallback.py`, which ADR-0046 needs dated within 14 days),
mutation sweeps that measure β, provider headroom and watched-source freshness probes under
ADR-0029.

Class 2 is **built now and disabled now.** ADR-0039 permits construction and supervised exercise;
Gate B gates unattended and default operation, and it is not passed.
`routing_orchestration_enabled` stays `false` and is derived from the gate conditions, not from
this ADR.

**Headroom probes are exogenous for the capacity question only.** Provider state is a different
class of facts about *whether we can run*, and carries no information about whether an artefact is
good. It may never reach an acceptance path.

### 4. What may never happen inside a tick, attended or not

1. Accept an artefact on any self-report — the model's, the human's, or a process exit code.
2. Author a human decision: approval, gate lift, spend authorisation or β verdict (V0-18).
3. Spend metered credit without a provider-enforced cap (`v0-draft.md` §7.2).
4. Point at any repository other than this one. Under ADR-0039 that is no longer *Gate B's*
   prohibition — Gate B gates dependence — but it remains an **ask-first** item in `AGENTS.md`,
   and the private commercial repositories remain under an absolute publication ban.
5. Modify its own schedule, budget or admission rules. Self-modification is ADR-0018's subject and
   is gated on measured verifier reliability; at β = 0.3132 nothing here qualifies.
6. Terminate another agent's work without a standing termination authority fixed before that work
   started (ADR-0034 §3).

### 5. Termination: four terminators, and the retry ceiling is derived from β rather than chosen

**Per-tick:** the attempt's own stopping rule and budget. Existing machinery.

**Per-loop, and this is the one with a number in it.** A loop that generates candidates until one
passes the checks is **verifier shopping**. If each generated candidate that is bad is accepted
with probability β, then over `n` candidates

```
P(a bad artefact ships) = 1 − (1 − β)ⁿ
```

At the measured β = 0.3132 that is, for n = 1…5: **0.3132, 0.5283, 0.6760, 0.7775, 0.8472.**
[algebra] Computed 21 Aug 2026 over EXP-47's measured β. **A five-try retry loop ships a bad
artefact more often than not — it ships one 85% of the time.**

Inverting it, for a declared exposure ceiling ε:

```
n_max = ⌊ ln(1 − ε) / ln(1 − β) ⌋
```

**At every point in the measured interval [0.2926, 0.3346], and for any ε ≤ 0.40, n_max = 1.**
[algebra] So the ceiling is not a preference and is not tunable by whoever wants more attempts:
**at today's β a loop gets one candidate per verifier contract.** More attempts require a lower
measured β, and lowering β is the product.

**Per-schedule:** a schedule is **not self-renewing.** Every registered schedule carries an expiry
— a tick count or a wall-clock horizon — and re-arming is a human act. A cron that outlives the
reason it was created is the characteristic failure of always-on systems, and an expiry field is
one line.

**Global:** the budget ledger, in decision 6.

**None of these terminate by timeout.** Progress is judged on the declared artefact under
ADR-0034; a stall escalates and diagnoses, and does not kill.

### 6. A schedule is a budget principal in its own name, and exhaustion disarms it

**A per-attempt ceiling does not bound an attempt generator.** A schedule of `k` ticks in a period,
each holding a per-attempt ceiling `c`, has period exposure `k·c`, which is unbounded in `k`.
[algebra] A five-minute cron multiplies any per-task cap by 288 a day. Therefore:

1. **Every schedule holds its own period ceiling**, separate from the per-task and per-period caps
   ADR-0044 already requires, so one runaway loop cannot consume the period budget other work
   needs. Ledgers stay separate — subscription, metered, local — exactly as `v0-draft.md` §7 says.
2. **Exhausting a schedule's ceiling disarms the schedule and escalates once.** It does not skip
   the tick and try again next time. A loop that hits its cap every tick generates one refusal per
   tick for the rest of the period, and under ADR-0033 an escalation nobody reads is
   indistinguishable from no detector.

### 7. There is no heartbeat, and the reason is a rule this project already holds

**A heartbeat is a self-report.** It is the reporter's claim about itself, carrying no observation
of the work. Working principle 5 and V0-21 already forbid self-reports as acceptance signals; the
same reasoning forbids them as liveness signals, and ADR-0034 already decided that progress beats
heartbeat and both beat presence.

So: **no heartbeat event kind exists.** Liveness is sampled externally from the artefact each tick
declares as its progress. A tick that cannot name such an artefact cannot be scheduled — which,
per ADR-0034, is information worth having before it runs.

The one case that would justify reopening this is work whose progress genuinely cannot be observed
from outside the process. EXP-73 measures whether the artefact signal is good enough; its kill
condition is what would bring heartbeats-carrying-progress-state back.

### 8. There is no offline consolidation phase, and no ADR-0052 is written

The "dreaming" idea does not survive the class-of-facts test, and the reason is that **it
decomposes without remainder.**

Enumerate what an offline phase could actually do:

| Candidate activity | New class of facts? | Where it lands |
|---|---|---|
| Re-read the trajectory and emit reflections or lessons | **No.** A function of the existing record | Cut |
| Condense or summarise accumulated context | **No.** And EXP-45 already measured condensation retention and consequential loss | Not a phase; a function call |
| Replay past accepted work against the *current* verifier | **Yes.** The checks changed; the execution outcome is new | Already a class-1 tick. EXP-43 did exactly this |
| Mutation sweep to re-measure β | **Yes.** Fresh execution outcomes against injected faults | Already a class-1 tick. EXP-47 |
| Exercise the bare-agent fallback | **Yes.** A real invocation on a real machine | Already a class-1 tick. ADR-0046 |
| Distil solved problems into reusable abstractions | Only in the half that **tests** the abstraction by running it | The test half is a class-1 tick; the distillation half is a function call |

**Every part that introduces exogenous facts is already a class-1 sensing tick. Every part that
does not is echo.** There is no residue that needs a decision record of its own, so writing one
would be recording a name rather than a decision. **ADR number 0052 is left unclaimed and returns
to the pool.**

Three further things make the cut, rather than merely permitting it.

**Idleness is a scheduling input, not a phase.** The one genuinely distinct argument for an offline
phase is that spare subscription capacity expires unused. ADR-0028 already decided that question
in the opposite direction: capacity is allocated by incremental verified value per human review
hour, **never by raw token use**. "Burn the quota because it is there" is the thing that ADR
forbids by name.

**Self-review as an acceptance mechanism is measured to fail in the direction that matters.**
Training a model against its own reference-free judgments drove the judge's pass rate from 0.72 to
0.94 while true accuracy stayed at 0.20, across three seeds. [cited] `[ABS]` That is a rubber-stamp
regime: the acceptance signal improved and the artefact did not. A consolidation phase whose output
feeds acceptance is the same shape.

**And consolidation is a variance-destruction step, which is adverse to this project's own
objective.** β is estimated from the disagreement between independent records. A phase whose
purpose is to compress many records into one distilled account removes exactly the variation the
estimate is made of. **It would manufacture the appearance of Whewell's test while deleting the
thing that measures it.** [asserted]

**What would reverse this is registered, not hypothetical.** EXP-72 runs a consolidation arm and a
matched-token-budget verification arm against the same items. If consolidation beats baseline
beyond the pre-registered margin *and* the same tokens spent on verification do not match it,
**ADR-0052 gets written** — and the honest reading then available is the bounded one: the phase
removed interpretation noise, not common-evidence error.

---

## The test every structure had to pass

| Structure | Different class of facts | Verdict |
|---|---|---|
| Class-1 tick: mutation sweep | Execution outcomes of injected faults against the current checks — an oracle no model authored | **Ships** |
| Class-1 tick: replay and digest | The projector's execution result against the log; catches projector defects, which are facts about the code | **Ships** |
| Class-1 tick: fallback exercise | A real invocation of the bare agent on a real machine | **Ships** |
| Class-1 tick: headroom / change-feed probe | Authenticated provider state (ADR-0029) — exogenous for the *capacity* proposition only | **Ships, barred from acceptance** |
| Class-2 tick: dispatch a queued task | The verifier outcome that terminates it. The patch itself is a hypothesis | **Built, disabled until Gate B** |
| Heartbeat | **None.** A self-report about the reporter | **Cut** (decision 7) |
| Reflection tick over its own trajectory | **None.** A function of the existing record | **Cut** (decision 1) |
| Offline consolidation / "dreaming" phase | **None that is not already a class-1 tick** | **Cut** (decision 8) |
| Watchdog terminating on a timeout | **None.** A timer is not an observation of the work | **Cut** — ADR-0034 decided it |

---

## Evidence

- `[measured]` Two scheduled sensing ticks exist on this machine and are registered with the OS
  scheduler: `Consilient-Capture-Health` and `Consilience-EXP27-Collector`, both `Ready`, queried
  21 Aug 2026. `.harness/capture-health.log` records one run at `2026-08-20T21:36:42+01:00` which
  replayed the trajectory to an identical canonical state — 104 events, 3 refused, 92 recorded as
  having bypassed `append()`, digest `9e0b1613…`. **One recorded run is one data point:** it
  evidences that the pattern produces an artefact, not that the schedule is reliable.
- `[measured]` Composite β = **0.3132 [0.2926, 0.3346]**, EXP-47, mutation testing, 104 s, no
  proxy labels and no censoring.
- `[algebra]` `P(bad ships) = 1 − (1−β)ⁿ` — the verifier-shopping identity already registered in
  `../20-design/work-modes.md`. Evaluated at the measured β on 21 Aug 2026: 0.3132, 0.5283,
  0.6760, 0.7775, 0.8472 for n = 1…5.
- `[algebra]` `n_max = ⌊ln(1−ε)/ln(1−β)⌋`, and `n_max = 1` at every point of the measured interval
  for any ε ≤ 0.40.
- `[algebra]` A per-attempt ceiling `c` over `k` scheduled ticks admits `k·c` of period exposure,
  unbounded in `k`. A schedule therefore needs a ceiling in its own name.
- `[algebra]` Unattended work time-shifts review debt rather than adding review capacity;
  `n_max = T_cycle / T_review` (`work-modes.md`, `findings.md` §5).
- `[cited]` `[ABS]` Ao, Gao & Simchi-Levi, *On the Reliability Limits of LLM-Based Multi-Agent
  Planning*, arXiv:2603.26993, 27 Mar 2026. Abstract fetched and read 21 Aug 2026. States that a
  delegated network is decision-theoretically dominated by a **centralised Bayes decision maker
  with identical information access** — an information bound against an unconstrained optimum.
- `[cited]` `[ABS]` Zhou, *More Convincing, Not More Correct: Self-Play Reward Hacking of
  Reference-Free LLM Judges*, arXiv:2607.05904, 7 Jul 2026. Abstract fetched and read 21 Aug 2026.
  On GSM8K with Qwen3 policies, self-play drove the judge's pass rate from 0.72 to 0.94 while true
  accuracy stayed at 0.20, three seeds.
- `[cited]` `[ABS]` Rajan, *Auditing Reward Hackability in Code RL Training Environments*,
  arXiv:2606.16062, 14 Jun 2026. Abstract fetched and read 21 Aug 2026. On a 49-task sample of
  SWE-bench Verified, **28.5%** of tasks have test suites weak enough that a Docker-verified
  incorrect patch passes them.
- `[cited]` `[FULL]` Dietrich & List, *A Model of Jury Decisions Where All Jurors Have the Same
  Evidence*, *Synthese* 142(2), 2004 — read and recorded in `formalising-echo-2026-08-20.md` §9.
  Shared-evidence panels remove interpretation noise; their accuracy converges to the reliability
  of the common evidence, not to one.
- `[asserted]` The class-1/class-2 split, the never-list, the schedule expiry, and the judgement
  that the offline phase decomposes without remainder.

## Evidence against

- **The schedule may find nothing, and today I cannot tell.** One recorded tick run exists, and it
  reports green. A battery that only ever reports green is indistinguishable from no battery, and
  nothing here establishes that a *standing* schedule beats invoking the same commands on demand.
  EXP-70 exists because I cannot answer this, and its kill condition deletes decision 2 outright.
  [measured]
- **The retry ceiling rests on an independence assumption this repository has already refuted next
  door.** `1 − (1−β)ⁿ` assumes each generated candidate is accepted independently with probability
  β. Candidates from the same model on the same task are plausibly positively correlated, which
  makes the identity an **upper bound** — real exposure would be lower and `n_max = 1` would be
  conservative, possibly severely. And `composite-beta-under-dependence-2026-08-20.md` showed that
  independence *between checks* is refutable from a single 2×2 table, with the product estimator
  landing outside the sharp bound. **I have not measured dependence between candidates, and no
  registered experiment does. This is the weakest load-bearing step in the ADR.** [algebra]
  [measured]
- **It forbids, on one instrument, the retry loop that most agent harnesses ship.** β = 0.3132 is
  one oracle on one repository. `two-oracles-disagree-2026-08-20.md` records two oracles for β
  differing by 14× the tolerance under discussion. If mutation-derived β overstates the β that
  matters for shipped work, `n_max = 1` is a severe restriction derived from the wrong number.
  [measured]
- **The literature this ADR declines to follow reports large gains from loops.** The Darwin Gödel
  Machine (SWE-bench 20.0 → 50.0) and SICA (17 → 53%) are in this repository's own bibliography.
  Both are recorded there at `[ABS]`/`[SNIP]` and **I have not read either in full.** My reading is
  that both obtain their gains through an execution boundary — they are scored by running
  benchmarks — which is consistent with decision 8 rather than against it. **If either turns out
  to obtain its gain from a text-only consolidation step, decision 8 is wrong.** [cited]
  [asserted]
- **The prior-art pattern I was handed, I did not verify.** A second agent reported that across the
  surveyed literature *every* offline phase producing a durable verified gain had an execution
  boundary and every text-only phase did not. I verified three of its citations directly
  (2603.26993, 2606.16062, 2607.05904) and **failed to verify a fourth** — Reflexion's
  self-generated-test false-accept rates of 1.4% / 16.3%, which do not appear in the paper's
  abstract and which I did not find in the PDF I fetched. **A pattern claimed to be exceptionless,
  reported by one reader, is the exact shape of the unsupported figure that reached six documents
  in this repository this week.** It is not relied on here. [asserted]
- **An execution boundary is necessary, not sufficient — which cuts against my own criterion.**
  Rajan's 28.5% is a measurement of an *executing* oracle accepting incorrect patches on 49 tasks.
  "Does it execute something?" is a cheap admission test and this ADR uses it as one, but passing it
  says nothing about β. **If decision 8 is read as "execution makes an offline phase safe", it is
  wrong. It makes it eligible.** [cited]
- **This ADR builds the machinery `work-modes.md` warns about.** That document's arithmetic says
  unattended work accumulates review debt rather than eliminating it, and names "run more agents in
  the background" as the feature that feels productive while making the ceiling worse. My defence
  is that class 1 produces evidence rather than diffs and therefore adds no review debt — **which
  is precisely the kind of exception every such warning gets argued around.** Class 2 has no such
  defence, which is why it is disabled. [algebra]
- **Written by the party it grants latitude to.** The design, the decision to cut two structures,
  and EXP-70's single-reviewer adjudication are all mine. Q19's rule — the party that produced the
  material cannot certify what it missed — applies and is **not** satisfied. [asserted]
- **Searched and not found.** I searched the repository for prior loop, cron, always-on and
  offline-phase decisions before writing (`docs/`, all ADRs, `work-modes.md`,
  `dreamers-and-the-bootstrap-problem-2026-08-20.md`) and found the arithmetic but no decision.
  I did **not** search the external literature on scheduler design, and the operational sources
  behind decision 7 are ADR-0034's, read by its author and not re-verified by me. [asserted]

## Consequences

**Positive.** Always-on work becomes buildable immediately without a new primitive, a daemon or a
scheduler, because a tick is an attempt and the OS already schedules. Two structures that would
have cost time and produced echo are cut before they are built. The retry ceiling stops the
single highest-exposure pattern in the product — the overnight loop that keeps trying until the
checks go green — with a number rather than a warning.

**Negative.** `n_max = 1` at today's β is a hard restriction on the most familiar agent pattern,
and it will feel wrong to anyone who has watched a second attempt succeed. It rests on an
independence assumption nobody has measured. **Schedules also add operational surface that lives
outside the repository** — a Windows scheduled task is not in git, cannot be reviewed in a PR, and
the wrapper already in the tree resolves its target between two checkouts at run time, so which
code a tick executes depends on which working tree happens to exist. That is a provenance gap in
a project whose first principle is provenance, and this ADR does not close it.

**Neutral but load-bearing.** Every scheduled unit must now declare a progress artefact, a period
ceiling and an expiry before it may be registered. A task that cannot name its progress artefact
cannot be scheduled at all — which is ADR-0034's consequence inherited, and it will exclude some
work people expect to schedule.

## Enforcement

Every check below is owed by the commit that implements the behaviour it constrains, not by this
ADR — `v0-draft.md` §11's rule. Where a check cannot be built today, that is stated.

| Invariant | Check | Buildable? |
|---|---|---|
| A schedule declares a period ceiling, an expiry and a progress artefact | Schema validation at schedule load rejects a record missing any of the three. Same shape as `_check_attempt_contract` in `src/consilient/events.py`, which already rejects incomplete dispatch | **Yes**, today |
| A class-1 tick never dispatches a model | Admission test at the single dispatch boundary. **This is only a chokepoint if V0-08's lint banning direct dispatch lands with it.** The dispatcher does not exist yet; if it ships without that lint, this decision is unenforced and must be recorded as such | **Conditionally** — depends on V0-08 |
| Candidates per verifier contract are capped at `n_max` derived from the recorded β | Fixture: a seeded loop at the recorded β attempts `n_max + 1` and is **refused**, not silently truncated. A second fixture asserts `n_max` falls when β rises | **Yes** |
| Exhausting a schedule's period ceiling disarms it | Fixture: the next scheduled fire after exhaustion is refused, one escalation event is appended, and **no second escalation is appended on the following tick** | **Yes** |
| No heartbeat exists | Test asserting the accepted event kinds contain no liveness self-report. It is a list; the check is a membership assertion | **Yes**, today |
| A tick that cannot end in a verifier outcome cannot be registered | Schedule-load test rejects a tick whose contract names no verifier | **Yes** |
| No duplicate experiment identifiers (R15) | `grep -oE '^### EXP-[0-9]+' docs/10-research/experiment-register.md \| sort \| uniq -d` prints nothing | **Yes, and it fails today.** EXP-56, EXP-57 and EXP-58 are duplicated from 20 August. Not repaired here: the fix is supersede-by-key on records this ADR did not write |

## What would overturn this

- **EXP-70** — ≤1 tick-unique finding in 30 daily ticks deletes decision 2. The commands survive;
  the schedule does not.
- **EXP-71** — fixed-seed β drift beyond 0.0210 on an identical tree digest means a stored β is not
  a routing input, and every tick consuming β must re-measure inside itself.
- **EXP-72** — a consolidation arm beating baseline beyond ±0.02 while a matched-token verification
  arm does not match it **writes ADR-0052** and reverses decision 8.
- **EXP-73** — false stalls outstripping genuine detections at 20 verdicts reverses decision 7
  toward heartbeats carrying progress state.
- **A measurement of dependence between generated candidates.** Strong positive correlation raises
  `n_max` above 1 and makes decision 5's ceiling too tight. **No experiment currently measures it,
  and that gap is the first thing a reader should hold against this ADR.**
- **A reading of the Darwin Gödel Machine or SICA showing a text-only consolidation step producing
  the gain.** That falsifies decision 8 from the literature rather than from a run, and it is
  cheaper than EXP-72.

## Publication candidate?

**No.** The retry ceiling is a two-line inversion of an elementary identity that
`work-modes.md` already carried, and its only novelty is having a locally measured β to put in it.
The publishable object, if one exists here, is the β measurement itself and the mutation instrument
behind it — not this decision.
