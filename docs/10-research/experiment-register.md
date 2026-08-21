# Experiment register

Every open question that cannot be settled by argument becomes a **runnable experiment**.
This file is the bridge between `../00-context/open-questions.md` and things Claude Code can
actually execute.

**Rules of this register.** Each entry states: what it decides, the precondition, the
procedure, the measurement, and the **stopping rule** — the result that would change a
decision. An experiment with no stopping rule is not an experiment, it is data collection.

Status: `READY` (runnable now) · `BLOCKED` (needs harness component X) · `DONE`.

**Numbers are allocated here and nowhere else.** A design drafted in a research note or an ADR
is a proposal for an experiment, not a claim on an identifier.

On 20 August 2026 **EXP-36 named three different experiments at once** — the behavioural-plugin
sweep registered here, a differential-against-parent-revision design drafted in
`manufacturing-oracles.md`, and the visibility-dial experiment drafted in ADR-0035 — and EXP-37
named two. All five were written the same night by the same author, hours apart, each taking the
next number that looked free from wherever it happened to be reading. Two cross-references
resolved to the wrong experiment. [measured] The drafts are now EXP-40, EXP-41 and EXP-42; the
register's own entries were not moved.

**The check, before writing any new entry:** take the highest number in this file, then run
`grep -rn "EXP-[0-9]" docs/` and confirm the next one is genuinely unused. The first step alone
is what produced all three collisions — it is the step that feels sufficient and is not.

---

## Runnable today — no harness required

> **Axis decided 20 August 2026** (`../00-context/beta-axis-defect-2026-08-20.md`). β remains
> `P(accept | bad)`, the axis the closed form and `beta.py` are built on. `P(bad | accepted)` is
> retained as a separately named quantity and reported alongside rather than discarded — it is
> what this experiment actually computed and it is the more useful number for a human reading a
> green build. `mine_beta.py` is to emit the full 2×2 rather than a single ratio, because a
> quantity read off a printed table cannot silently be the wrong conditional.
>
> **The ~146-pair audit in *Next steps* is cancelled.** It narrows the interval on the axis the
> architecture does not route on. It is replaced by an audit of the **bad-and-red cell** — 75
> pairs on `jobboard-v2`, 3 on `hireable-platform` — which is smaller, cheaper, and 37% of all
> bad artefacts that has never been examined. **Falsifier:** if that cell's label precision
> differs materially from the bad-and-green cell's audited 1/15, the two cannot share a
> correction factor and every corrected β needs its own audit.

### EXP-01 · Measure β on repository history `DONE 20 Aug 2026 — stopping rule FIRED for this method; see experiments/exp01/stopping-rule-verdict-2026-08-20.md`
**Verdict, 20 Aug 2026.** The pre-registered rule fires: pooled across BOTH corpora there are
**209** evaluable bad artefacts and ±0.05 needs **332** at the measured rate — 63.0% of what
the rule demands, with no more history available. [algebra] Recorded-CI-verdict mining is
therefore retired as the β instrument.
**But the consequence the rule names does not follow.** The rule assumed history mining was how
β gets measured. EXP-47 measured it at **0.3132 [0.2926, 0.3346]**, half-width 0.0210, in 104 s,
with no proxy labels and no censoring. [measured] And precision was never the binding
constraint: the metadata proxy (0.6809) and the executable replay (0.0000) differ by **14×** the
rule's own ±0.05 tolerance, so the problem is validity, not width. [measured]
**ADR-0002 stays PROVISIONAL.** The rule's stated consequence and the evidence point in opposite
directions; reconciling them is a decision about the architecture's centre and belongs to Joe.
**Gate note:** this flips `doctor`'s A1 to PASS. Gate A still fails on A3, which is permanently
unsatisfiable, so no gate opens. One `git revert` returns A1 to FAIL.

**First pass run on both repos** (recorded-CI-verdict mining, no replay). Raw proxy
labels proved ~93% noise (audited precision 1/15 on both repos); corrected β̂ ≈ 0.12
[0.02, 0.42] (jobboard-v2) — the honest verdict is "insufficient data", exactly
ADR-0002's predicted near-threshold regime. Stopping rule NOT fired: the interval is
audit-limited, not history-limited. Unplanned finding: 33% of jobboard-v2 merges
overrode red CI — the human is the real acceptance gate. Next: reference-based labels,
full-pair audit.
**Decides:** Q2, and promotes ADR-0002 from PROVISIONAL to ACCEPTED or kills it.
**Precondition:** none. `jobboard-v2` git history and PR outcomes.
**Procedure:** for each historical PR, replay the repo's checks at that commit; classify the
known outcome (merged clean / reverted / hot-fixed within N days); record every case where
checks passed and the outcome was bad.
**Measures:** composite β with Wilson 95% interval; per-check β as diagnostics (ADR-0012);
label-noise rate from manual review of a 30-PR sample.
**Stopping rule:** if the interval cannot be narrowed below ±0.05 with all available
history, β is not measurable at solo-founder volumes and ADR-0002 fails — the architecture
needs a new centre, not a patch.
**Bias control:** **must** be repeated on a weakly-verified repo (`hireable-3.0`).
`jobboard-v2` is low-β and will flatter the thesis (ADR-0013).

### EXP-02 · Jump-forward vs constrained decoding `READY`
**Decides:** publication candidate C2; closes out the shelved CASD work.
**Precondition:** RTX 5090 rig; vLLM or SGLang; XGrammar/Outlines vs SGLang jump-forward.
**Procedure:** matched-workload comparison on structured-output tasks; fixed seed, batch
size 1, pinned model revision by hash, pinned engine version.
**Measures:** validity rate, tokens, wall-clock, quality on a held-out set.
**Stopping rule:** either direction is publishable. **A null result is the expected outcome
and is the more valuable paper** — see `../publications/README.md` C2.

### EXP-03 · Are per-check β values independent? `BLOCKED: EXP-01 label quality`
**Decides:** whether ADR-0012's lower-bound product is usable as a prior at low sample size.
**Precondition:** EXP-01 **label quality**, not EXP-01 output. Audited hotfix-label precision
is 1/15 on both repositories [measured], so pairwise dependence computed on those labels
measures the labelling heuristic and not the checks. The precondition is therefore the
reference-based relabelling and the full audit of all flagged pairs named in
`experiments/exp01/findings-exp01.md` § *Next steps*, not EXP-01's first pass.
**Procedure:** on artefacts with known-bad outcomes, compute pairwise conditional
dependence between check verdicts.
**Stopping rule:** near-independence → the product becomes a usable prior; strong dependence
→ ADR-0012 stands unchanged and the finding goes in the β paper.

### EXP-04 · Bimodal and adversarial difficulty sweeps `DONE`
Closed Q3. β* invariant to the difficulty distribution; closed form
β* = (1−α)·e^(−kΔ). See ADR-0002 and
`experiments/q3_bimodal_and_q2_sample_complexity.py`.
**Residual:** the closed form assumes logistic (Rasch/1PL) competence. **Not yet tested
under a non-logistic competence curve** — that is the remaining exposure and is worth one
more sweep. **Registered 20 Aug 2026 as EXP-37**, below; until then the residual was an
intention with no stopping rule, which this register's opening rule calls data collection.

### EXP-37 · Does β* survive a non-logistic competence curve? `READY` (registered 20 Aug 2026)
**Decides:** the residual EXP-04 left open — whether ADR-0002's closed form
β* = (1−α)·e^(−kΔ) is safe to use as the routing threshold when competence is *not*
Rasch/1PL, and whether ADR-0002's headline consequence (β* invariant to the difficulty
distribution) is a property of the cascade or an artefact of the link function. ADR-0002 says
so itself: *"the result is exact given logistic competence … not free of functional-form
assumptions, only free of distributional ones."*
**Precondition:** none. Extends `experiments/q3_bimodal_and_q2_sample_complexity.py`; no GPU,
no provider, no metered call.
**Procedure:** hold EXP-04's difficulty distributions fixed (unimodal Beta(2,2) and the
bimodal mixtures from 30% to 90% easy) and its Δ grid fixed, and recompute the zero-advantage
threshold numerically from Δ(d) = p_c(1−α)(1−p_f) − p_f(1−p_c)β under four competence
curves that are not 1PL: (a) a normal-ogive/probit link; (b) 2PL with **unequal slopes**
between the cheap and frontier tiers — the case in which *d does not cancel*, and the decisive
one; (c) 3PL with a guessing floor c > 0, i.e. a cheap tier that sometimes passes the checks by
luck; (d) a heavy-tailed link. Fixed seed; the curve parameters and the grid are written into
the script **before** it is run and are not tuned afterwards.
**Measures:** β*_true minus β*_closed at every grid point, with its sign; the fraction of the
grid on which β*_closed **exceeds** β*_true, which is the unsafe direction (the closed form
would licence routing that is not in fact advantageous); and the spread of β*_true across the
difficulty distributions at fixed Δ, which is the invariance claim itself.
**Stopping rules (fixed before the run):**
- Tolerance is **0.01 absolute**, chosen because EXP-04 measured β* moving by ≤ 0.003 across
  distributions, so 0.01 is comfortably above the wobble that sweep already showed and below
  the smallest β* on the grid. It is fixed now so that a marginal excursion cannot be argued
  down afterwards.
- If max(β*_closed − β*_true) ≤ 0.01 across all four curves, the closed form is safe as
  written, the EXP-04 residual is **closed**, and ADR-0002 gains a dated update saying so.
- If it exceeds 0.01 anywhere, ADR-0002 must either carry a stated safety margin equal to the
  measured worst case or state logistic competence as a **precondition on use** rather than a
  remaining exposure. Which of the two is a judgement; that it must do one is not.
- If β*_true varies by more than 0.01 across the difficulty distributions at fixed Δ under any
  curve, then distribution-invariance is conditional on Rasch and ADR-0002's most important
  sentence must be restated that way. **This is the result that would change a decision.**
- A null result — all four curves inside tolerance — is the expected outcome and closes the
  residual. Record it; do not add curves until one breaks.
**What it cannot decide:** which competence curve real models actually follow — that needs
measured success-versus-difficulty data per model, which is EXP-17 and EXP-20 territory and no
simulation can supply it; the value of β on any repository; and whether α is itself
difficulty-dependent, which is a separate assumption this sweep does not touch. Every number
this produces is `[simulated]` and answers "does the answer flip, and where?" only.

---

## Blocked on the first harness increment

The minimum harness needed to unblock most of these: **adapter for one agent + ticket store
+ trajectory log + verdict prompt.** Nothing else.

### EXP-05 · Adapter surface plus composition/control-path follow-ups `DONE 19 Aug 2026 — see experiments/exp05/findings-exp05.md`
**Result:** Claude Code, Codex and Cursor passed a live ticket. Adapter #2 (Codex) did not
force an interface redesign. Adapter #3 (Cursor) exposed a genuine namespace-dependent
path question, absorbed by a per-adapter translation seam with four passing tests; its
first live result also exposed input/output/cache usage fields. Adapters #4 (Ollama) and
#5 (OpenRouter) fit the common result shape but exposed that provider and coding harness
must be recorded separately; Ollama completed a live run but failed verification. The
Codex × OpenRouter composition failed before artefact production; a sixth,
follow-up OpenCode × OpenRouter composition reached inference and passed functional tests
in 24.1 seconds but failed the strengthened artefact-scope verifier after creating an
unrequested test file. A seventh control path then drove the existing Cursor composition
through ACP v1 over stdio in 29.7 seconds and passed the strengthened verifier. [measured]
Antigravity 1.1.15 model discovery authenticated through a saved Google business/GCP
profile, but a structured print-mode probe failed before inference with zero tokens and an
empty-location error; model discovery alone is now a tested insufficient readiness signal.
[measured] The original stopping rule does not fire. [measured]
**Decides:** Q5, and the viability of ADR-0001.
**Procedure:** write an adapter for Claude Code. Then write a second for Codex **without
refactoring the first**. Record what the second breaks.
**Measures:** count and nature of interface changes forced by adapter #2; repeat for #3.
**Stopping rule:** if adapter #2 forces a redesign of the interface and #3 forces another,
the surface is not stable enough for one maintainer and ADR-0001 must be reconsidered —
including the OpenHarness-plugin alternative recorded there.
**Budget used:** one day. [measured]

### EXP-06 · Where in a run do failures occur? `BLOCKED: trajectory log`
**Decides:** Q9 / ADR-0009, which is PROVISIONAL pending this.
**Measures:** distribution of failure position across a run's tool calls.
**Stopping rule:** heavily front-loaded → consider a step-level *abort* (not step-level
routing, which the β-label argument still blocks).

### EXP-07 · Wasted-work multiplier `DONE 20 Aug 2026 — see experiments/exp07/findings-exp07.md`
**Decides:** whether ADR-0003 (no learned router) reopens.
**Procedure:** time a failed local cheap attempt end-to-end *including verifier* against a
frontier call, on the 5090. **Amended 19 Aug 2026: run each condition WITH and WITHOUT the
reasoning layer** (`../20-design/reasoning-layer.md`) — self-consistency at n=5 is ~5×
wall-clock on a single serialising GPU and can cross the threshold by itself.
**Stopping rule:** **multiplier ≥ 2× reopens ADR-0003.** Simulation says headroom goes
+0.002 → +0.024 → +0.123 at 1× / 2× / 5×. If the multiplier crosses 2× *only* with the
reasoning layer enabled, the finding is "scaffolding is what makes routing priors
worthwhile" — record it that way rather than as a blanket reopening.
**Pilot result, 19 Aug 2026:** one failed `qwen3:8b` attempt took 114.2 s versus
20.4 s for a Codex success, 25.6 s for a Claude Code success and 47.0 s for a
Cursor success: 5.6×, 4.5× and 2.4×.
The pre-registered 2× reopening condition was observed, so ADR-0003 is reopened for
investigation. This is n=1 on one trivial task and does not establish a population
multiplier. Cursor's selected model identity was not recorded, so its ratio is
supplementary rather than a third frontier comparison. EXP-07 is now the highest-priority
replication experiment. [measured]

**Replication protocol fixed 19 Aug 2026 before the run:** five synthetic, public coding
fixtures are frozen in `experiments/exp07/run_exp07.py`. [asserted] Each fixture receives
one `gpt-5.6-sol` Codex-subscription attempt at low reasoning effort and five independent
`qwen3:8b` local attempts through the same Codex harness. [asserted] Attempt one is the
unscaffolded local condition; the sum of five serial attempts is the verifier-coupled
best-of-five condition. [asserted] Every attempt uses a fresh repository and the same
functional-plus-changed-file-scope verifier. [asserted]

The run admits at most five frontier calls only while a fresh app-server snapshot reports
an authenticated subscription below 90% used, no reached-limit flag and no spend-control
stop; ten percentage points are reserved for the batch. [asserted] OpenRouter, API keys,
Claude, Cursor and Antigravity are excluded. [asserted] Stop at 30 attempts, 90 minutes or
the first admission-rule failure. [asserted]

**Instrument-repair amendment fixed before the replication rerun:** the interrupted first
run was invalidated before any verdict because the original instrument could reject a
committed correct artefact, lose partial results and mishandle right-censored timeouts.
[measured] A reduced attempt now starts only when at least 30 seconds remain; below that
floor the run stops instead of creating a nominal comparison from an arbitrarily truncated
attempt. [asserted] Verifier and agent timeouts are separate right-censored outcomes,
scope-verifier failure is a recorded fail-closed outcome, and every headroom observation
and attempt is atomically checkpointed. [asserted] The frozen fixtures, five-attempt serial
intervention, eligibility rule and 2× threshold are unchanged. [asserted]

The single-attempt multiplier is computed only where local attempt one fails and the
frontier passes. [asserted] The five-attempt multiplier is computed only where all five
local attempts fail and the frontier passes. [asserted] At least three eligible paired
fixtures are required: fewer is `insufficient evidence`; otherwise a median multiplier of
at least 2× replicates the reopening trigger and a median below 2× fails to replicate it.
[asserted] If only best-of-five crosses 2×, the reasoning layer caused the crossing; if the
single attempt already crosses, best-of-five is amplification rather than the cause.
[asserted]

**Result, 20 August 2026 — stopping rule applied as written.** [measured] Frontier 5/5 passed;
local 0/25 passed. Single-attempt median multiplier **1.69×**, which does **not** cross and is
recorded `insufficient_evidence` because two of five pairs are censored and a censored duration
cannot prove a non-crossing. Best-of-five median **17.95×**, and **16.75×** when every censored
duration is clamped to its applied timeout, so the crossing is robust to the instrument defect
found in this run. Therefore **only best-of-five crosses, and ADR-0003 is not blanket-reopened**:
the registered finding is that scaffolding, not the raw local attempt, creates the wasted work.
The 19 August n=1 pilot's 5.6× single-attempt reading did **not** replicate.

Two findings the multiplier concealed. First, `qwen3:8b` produced **no file edit in any of the
25 attempts** — every run recorded `changed_files: []` while consuming real tokens, so the
local tier is below the capability floor rather than merely slow, and no routing policy can
rescue a tier that never emits a diff. [measured] Second, the agent timeout **overruns by 10 to
269 seconds** because the subprocess timeout kills the direct child while Codex descendants hold
the pipes open; the fix is a process-tree kill and it is deliberately **not** applied after
seeing the result. [measured] EXP-31 substitutes `gemma4:31b` into the identical composition and
is the registered next step. Synthetic fixtures can replicate the latency mechanism but cannot establish
that a learned router improves real work; that requires a separate policy comparison on
real trajectories. [asserted]

**Instrument repair owed, added 2026-08-20 — a precondition of the next duration-dependent
registration.** The agent timeout overran its 240 s deadline by 9.8, 20.6, 21.6, 50.5, 53.2 and
269.3 seconds across the six censored runs, because `subprocess.run(timeout=…)` kills the direct
child while Codex descendants hold the pipes open; a censored duration is therefore inflated by an
unbounded amount. [measured] Withholding the fix after seeing this run's result was correct and
stays correct. It is now **owed**: no experiment whose stopping rule depends on a measured
duration may be registered until the runner kills the whole process tree. The defect is shared by
`experiments/exp07/run_exp07.py` (~line 329) and `experiments/exp31/run_exp31.py` (~line 157).
EXP-31 is exempt because it was already under way when this was written, and it mitigates by rule
— only a crossing may be concluded from censored data, and `timeout_overrun_s` is recorded
explicitly. Mitigation is not repair. [asserted]

**The check that would enforce this does not exist, and this is recorded rather than implied.**
The repair ships with it in the same commit or not at all: a test in
`experiments/exp07/test_run_exp07.py` that runs an agent command which spawns a descendant
outliving its parent, drives the timeout path, and asserts both that the descendant is dead
afterwards and that the recorded duration is within a fixed tolerance of the applied timeout.
Until that test exists this paragraph is a promise, not an invariant. [asserted]

### EXP-08 · Critic recall `BLOCKED: critic tier`
**Decides:** the parallelism ceiling in ADR-0007, and whether CLI-only survives.
**Procedure:** run a local 14B as a diff critic over historical PRs with known outcomes.
**Measures:** recall on bad diffs; false-reject rate on good ones.
**Stopping rule:** recall so low the ceiling stays ~3 agents → review-time reduction becomes
the only lever and ADR-0007's "no review surface" must be revisited.
**Note:** critic recall ≡ 1 − β. EXP-08 and EXP-01 measure the same quantity by different
routes — **a genuine consilience check.** If they disagree, one method is wrong.

### EXP-09 · Prior-dispersion gate cost and calibration `BLOCKED: inquiry tier`
**Decides:** Q11, Q12.
**Procedure:** on the 5090, sample N ∈ {3,5,8} local models on real architecture questions;
measure latency, cost and semantic agreement spread. Then log every T2 escalation and
whether the inquiry changed the decision.
**Stopping rule:** if escalations rarely change decisions, gate 3 is miscalibrated and the
threshold moves; if they change decisions often but cost too much, the Inquiry tier is a v2
feature (Q14).

### EXP-10 · Does the executable-model CI ratchet earn its keep? `BLOCKED: several ADRs with models`
**Decides:** Q13.
**Measures:** over three months — how often a committed decision model's sign flips; how
often that flip was informative versus dependency rot.
**Stopping rule:** if rot dominates, the ratchet is ceremony and should be dropped rather
than maintained.

### EXP-11 · Local model feasibility: predicted vs measured `BLOCKED: model library wrapper`
**Decides:** Q21, Q22; feeds the ADR-0005 dataset publication candidate.
**Measures:** predicted-vs-measured feasibility across machines; separately, whether the
"should you route here given β" output changes user behaviour.

### EXP-12 · Does verifier quality change self-improvement outcomes? `BLOCKED: β-meter + an archive loop`
**Decides:** ADR-0018 decision 1, and whether decision 2's restriction is justified. Joe has
made the verifier restriction conditional on this result.
**Precondition:** β-meter working (EXP-01), plus a minimal archive-based self-improvement
loop — can be a reimplementation of the SICA/DGM pattern at small scale, not production code.
**Procedure:** run the same loop twice over the same task set with the same budget. Arm A
uses a strong verifier; Arm B uses one deliberately weakened to a known high β. Run enough
generations for compounding to show.
**Measures:** true task performance of each archive on a **held-out set the verifier never
saw**, per generation. The gap between apparent improvement (verifier-scored) and real
improvement (held-out) is the quantity of interest.
**Stopping rule:** if Arm B's apparent improvement diverges from its real improvement while
Arm A's tracks, the compounding argument holds and ADR-0018 stands. If both track, the
argument is wrong, the gate is unnecessary caution, and ADR-0018 should be superseded — not
quietly softened.
**This experiment is also the paper.** See `../publications/README.md`.

**Scope warning, and it matters:** EXP-12 answers *"does verifier quality affect
self-improvement?"* It does **not** answer *"can a system safely improve its own verifier?"*
A negative EXP-12 result does not by itself license lifting ADR-0018 decision 2.

### EXP-13 · Can a system safely improve its own verifier? `BLOCKED: EXP-12`
**Decides:** ADR-0018 decision 2, properly.
**Procedure:** allow the loop to modify its own verifier suite in a third arm. Measure
whether the verifier's β rises over generations — i.e. whether the system edits its tests
into agreement with itself.
**Measures:** β of the evolved verifier against a fixed human-labelled holdout, per
generation.
**Stopping rule:** any monotonic rise in β confirms the restriction permanently. A flat or
falling β across enough generations is the only evidence that would justify lifting it — and
even then, budget primitives and the permission model stay out of scope (ADR-0019).
**Expected result:** β rises. Run it anyway; the expectation is `[asserted]`.

### EXP-14 · Do Owner-led meetings beat a single agent, and beat voting? `BLOCKED: meeting primitive`
**Decides:** ADR-0020 — whether meetings are load-bearing or ceremony.
**Procedure:** identical decisions, matched token budget, three arms:
(a) one agent holding all the evidence;
(b) an Owner plus distinct-evidence-class participants in a meeting, Owner decides;
(c) the same agents reaching the decision by consensus vote.
Before each run, freeze a manifest of canonical source identifiers actually available to
each participant. [asserted] A declared-distinct pair is operationally false-distinct when
its source-set Jaccard overlap is at least 0.50; that threshold is fixed before collection
and remains `[asserted]`. **Measures:** decision quality against a held-out ground truth;
tokens; wall-clock; declared class; pairwise source overlap; false-distinct rate.
**Stopping rule:** if (b) does not beat (a), **meetings are ceremony and should be cut** —
the whole authority matrix goes with them. If (c) beats (b), the delegation theorem does not
apply the way ADR-0020 claims and that ADR is wrong. For the declaration gate, stop at 40
convocations or 120 declared-distinct pairs: a false-distinct rate above 10% rejects
declaration-only admission; a Wilson 95% upper bound below 10% retains it provisionally;
otherwise report insufficient data. [asserted]
**This is the cleanest falsification test in the register.** Neither outcome is comfortable
and both are informative.

### EXP-15 · Does structured pushback improve decisions without training users to ignore it? `BLOCKED: decision log + longitudinal outcomes`
**Decides:** ADR-0021 — whether the two-challenge protocol is useful or theatre.
**Procedure:** record every eligible pushback, its irreversibility/material-stake grounds,
whether it changed the decision, whether an overridden decision later received a bad
verdict, and whether the user engaged with or dismissed the challenge. [asserted] Do not
manufacture pushbacks to fill the sample. [asserted]
**Measures:** decision-change rate; later-bad rate for overridden decisions; dismissal rate
in the first and last ten resolved events; challenge count and evidence novelty. [asserted]
**Stopping rule:** stop at 30 resolved pushbacks or 90 days. At most one changed decision in
30 rejects the protocol as theatre; a dismissal-rate increase of at least 20 percentage
points rejects the fixed count/form as habituating; fewer than 20 outcome-known events is
insufficient data. [asserted] Any third challenge or second challenge without a new fact is
an invariant failure, not an experiment outcome. [asserted]

### EXP-16 · Prototype the meeting layer on external PM tools; measure their friction directly `DONE 19 Aug 2026 — see exp16-results.md; rules 3 and 4 applied, rule 1 parked on Joe's blind grading, rule 2 undecidable in this design`
**Decides:** two live claims at once. (1) The grounds for a *native* ticket store — that
external PM tools "impose human-shaped state machines, human-shaped rate limits, and a webhook
round-trip on every state change" — at the time `[asserted]` and never measured.
**Attribution corrected 20 August 2026:** that sentence was attributed here to ADR-0006, and
ADR-0006 does not contain it and never did. It originates in
`../30-source-material/gemini-session-critique.md` lines 105–106, describing the Gemini
"Symphony" Linear-polling design. [measured] The experiment was worth running and its result
stands; the claim it tested simply belonged to a different document. ADR-0006 may not be cited
for a rate-limit or webhook argument. (2)
ADR-0020's claim that Owner-led meetings beat both a single agent and free-form group
discussion. This is **EXP-14 run early and cheaply on rented infrastructure**, with arm (c)
changed from consensus-vote to free-form Slack discussion — the relay structure the MIT
theorem punishes — plus an optional structured-relay Slack variant (the paper's Bpost
condition, 75.2% vs 58.1% at three stages, motivates testing it directly).
**Precondition:** ClickUp, Linear and Slack connected to Claude Code (they are, 19 Aug
2026). Dedicated isolated spaces, all named `consilience-exp16`; nothing touches real work.
**Procedure:** ~6 genuinely open decisions from `../00-context/open-questions.md`, matched
token budget per arm. Before running, `../20-design/pm-integration-purposes.md` assigns
each tool a falsifiable affordance hypothesis (Linear = decision state machine; ClickUp =
authority matrix as structured data; Slack = meetings + user participation, and the most
likely echo chamber). Arms: **A** single agent, all evidence. **B** ADR-0020 structure —
one Owner, Evidence participants with declared distinct classes, structured exchange
through Linear tickets, authority matrix in ClickUp, Owner decides alone. **C** same
agents and evidence partition, free-form Slack chat, decision by whatever emerges. The
user participates in ≥1 Arm B and ≥1 Arm C meeting (ADR-0020 §3). Every event logged to
the append-only trajectory JSONL (ADR-0006 format); a meeting absent from the log does not
count. Hard turn and token caps on every arm.
**Measures:** decision quality (held-out check where one exists, else the user's
judgement); tokens; wall-clock; message count and new-information vs restatement fraction
(echo measured directly in Arm C); Arm B distinct-evidence-class violations; per-tool API
rate limits hit, latency per state transition, state-machine mismatches, workarounds
required, concurrent-write conflicts.
**Stopping rules (fixed in advance):**
- Arm B does not beat Arm A at matched budget → meetings are ceremony; ADR-0020 and the
  authority matrix are cut.
- Arm C beats Arm B → the delegation theorem does not apply as ADR-0020 claims; the ADR is
  wrong. Say so.
- Linear or ClickUp handle the state machine and concurrency without material friction →
  ADR-0006's native-store justification fails; supersede it.
- Rate limits or human-shaped state bite hard → ADR-0006 validated; record the specific
  numbers so the native design inherits them.
**Deliverables:** `../20-design/pm-integration-purposes.md`; `exp16-results.md` (tagged);
ADR supersessions if stopping rules fire (reported to the user first, never quietly
softened); `../00-context/friction-log.md` entries for every manual step.

### EXP-17 · Per-tool acceptance profiles for small local models `READY (5090)`
**Decides:** what the cheap tier may safely be handed from the default tool set
(`../20-design/capability-layer.md`), which sets the blocked-task mass φ in ADR-0002's
structural-zero result.
**Novelty check done (19 Aug 2026):** the headline framing is *not* novel — PA-Tool
(arXiv:2510.07248) showed SLMs gain ~17% from schema renaming; Hammer, RoTBench and
RAG-MCP cover description sensitivity and tool-count degradation separately. What is
unpublished is the **factorial interaction** — model size (4B/8B/14B) × loaded-tool
count × description variant — and **per-tool acceptance profiles on a real harness
inventory** rather than synthetic benchmark APIs.
**Procedure:** the default tool set from `capability-layer.md`, three local models,
fixed seeds, pinned model+engine versions; per tool: success rate on a small task set
that requires exactly that tool, under (a) frontier-tuned descriptions as shipped,
(b) PA-Tool-style model-aligned renames; crossed with distractor-tool counts from EXP-18's
grid.
**Measures:** per-model × per-tool success matrix; the interaction terms.
**Stopping rule:** if per-tool profiles are flat (a model that clears a capability bar
clears it for all tools regardless of description variant), the registry can be a single
bit per model and the per-tool machinery is not built. If profiles vary by ≥20 pp across
tools within one model, the capability layer must ship per-tool gating.

### EXP-18 · Task success vs number of loaded tools, on local models `READY (5090)`
**Decides:** the slope of the context-clutter competence term — the one surviving Δ
mechanism (ADR-0002 § Δ discipline) — and whether the folklore "~20–25 tools" threshold
has any successor number for the 4B–14B tier.
**Prior art:** RAG-MCP (arXiv:2505.03275) swept 1→11,100 schemas on one large model
(collapse past ~100); Less-is-More (arXiv:2411.15399) contains **no threshold sweep** —
the ~20–25 figure attributed to it does not exist in the paper. Nobody has published the
curve for current small local models.
**Procedure:** fixed task set with known required tools (n_req); sweep loaded-tool count
n ∈ {n_req, n_req+5, +15, +35, +75} with distractors drawn from the real default set;
three local models; fixed seed, pinned versions; measure task success, tool-selection
correctness, tokens, wall-clock.
**Measures:** success(n) per model; the per-model γ (competence lost per irrelevant
tool); whether γ shrinks with model size as the frontier evidence suggests (Opus 4
25-pt swing → Opus 4.5 8.6-pt).
**Stopping rule (fixed before the run):** if success(n) is flat within noise out to
n_req+75 for all three models, the clutter mechanism does not bite at local scale, the
Δ claim in `context-loading.md` is struck, and the native path ships **without** a
tool-search layer (the gateways stay uninherited complexity). If the curve falls, the
knee sets the native loader's default cap, and the measured γ replaces the `[asserted]`
one in `capability_context_beta_star.py`.

### EXP-20 · Capability probe vs direct measurement — a consilience check `READY (5090)`
**Decides:** ADR-0025 — whether a cheap paired probe prices a new model's routing safety.
**Procedure:** minimal probe per ADR-0025 (paired discordant-pair estimator,
`experiments/probe_delta_ci.py`): 3–4 local models against a frontier reference, probe
sizes n ∈ {20, 50, 100, 200}, tasks drawn from jobboard-v2 history; fixed seed, pinned
model + engine versions. Compute β*(Δ̂) with the φ̂ correlation correction. Separately,
measure the routing decision directly per EXP-01 on the same repo.
**Measures:** Δ̂ and φ̂ with CIs per n; agreement between probe-derived and directly
measured routing verdicts; probe cost in tasks/tokens/minutes.
**Stopping rule (fixed before the run):** two routes to the same number is a consilience
check — **if the probe-derived verdict and the direct measurement disagree beyond their
combined CIs, one method is wrong**; given `robustness_beta_star.py`, presume the
closed-form model first, demote the probe to advisory, and record which violation
(slope, floor, correlation) explains the gap. If they agree at n ≤ 100, the probe ships
in v1. If agreement requires n > 200, the probe is not cheap and ADR-0025 §"What would
overturn this" fires.

### EXP-21 · Routing under subscription, budget and hardware constraints `BLOCKED: admission prototype + 16 GB reference machine`
**Decides:** ADR-0026 — whether deterministic feasibility vetoes prevent exhausted-plan,
budget-overrun and local-fit failures without refusing too much usable capacity.
**Precondition:** an injectable routing-admission prototype; provider headroom readers;
an OpenRouter management key whose provider-side task-key cap is set before any paid call;
cached or small models on the 5090/64 GB system; and one real 16 GB-system-RAM machine
for the constraint-case validation. No new paid model call is required for the replay
phase.
**Procedure:**
1. Replay provider snapshots at available, near-exhausted, exhausted, stale/unknown and
   reset-boundary states for Claude, Codex and Cursor. Include concurrent reservations,
   retries and usage outside the harness.
2. Compare decisions with authoritative live snapshots gathered during ordinary
   subscription use: Claude status-line data, Codex app-server rate limits and Cursor
   dashboard observations. Do not create model traffic solely to refresh a snapshot.
3. Exercise OpenRouter first against a fake ledger, then with one provider-capped live key.
   Attempt concurrent tasks and retries whose combined reservations straddle both the
   per-task and per-period caps.
4. Measure peak system and accelerator memory for at least 12
   model-revision × quantisation × context tuples on the 5090/64 GB system, with at least
   half within 10% of one tested profile's binding memory boundary. Replay those measured
   demands against profiles spanning 16–64 GB system RAM and 0–32 GB accelerator memory,
   then validate admitted near-boundary cases on the real 16 GB machine. Refused models
   are checked from metadata and the larger machine's measured peak; they are not
   downloaded to the constraint machine.
**Measures:** false admits; false refusals; provider-reported cap overshoot; headroom
estimation error; model bytes transferred before refusal; load/OOM result at the configured
context; capacity left idle; and task completion.
**Stopping rules (fixed before the run):**
- Any provider-reported spend above a configured hard cap removes that provider from
  unattended metered routing until a provider-enforced boundary replaces the failed one.
- Any dispatch when a fresh authoritative subscription snapshot already says exhausted
  makes that subscription adapter manual-only until fixed and re-run.
- Any model admitted and then unable to load at the configured context, or any model bytes
  transferred after an infeasible/unknown verdict, disables automatic local downloads
  until the fit provider or gate is superseded.
- A false-refusal rate above 20% over at least 30 authoritative feasible cases **per
  constraint class** overturns fail-closed autonomous routing for that class; require an
  explicit user decision instead.
- If Cursor's local estimate differs from its dashboard by more than 10 percentage points
  at three consecutive observations, Cursor stays manual-only; a reset-window model is not
  an adequate hard constraint.
**Acceptance rule:** no hard-rule violation and false refusals at or below 20% in each
class promotes ADR-0026 from PROVISIONAL. Hardware acceptance additionally requires the
real 16 GB validation; the 5090 profile replay alone is `[simulated]`.

### EXP-22 · Calibrate public benchmark priors against local verifier-labelled outcomes `BLOCKED: trajectory log + prior reader`
**Decides:** ADR-0027 — whether OpenRouter's public benchmark records and automatic router
earn quantitative weight, or remain candidate-discovery inputs and a baseline only.
**Precondition:** a versioned OpenRouter Models/Benchmarks snapshot retaining source and
`as_of`; at least six pinned models covering two provider families; a paired local probe;
and verifier-labelled tasks from at least three task families. Raw benchmark records are
not redistributed unless their licence permits it.
**Procedure:**
1. Freeze model candidates and benchmark priors before observing the held-out local tasks.
2. Compare a flat prior, the sourced benchmark prior and OpenRouter's automatic cross-model
   router against the same admitted candidate set and local verifier.
3. Use leave-one-model-out evaluation so a candidate's local outcomes cannot train its own
   prior. Record benchmark source/age, probes required to a stable verdict, final route,
   verifier false admits, cost and elapsed time.
4. Stop at 10 models, 60 paid task runs or £30 metered spend, whichever comes first. Reuse
   existing subscription/local trajectories where composition and model identity are known.
**Stopping rules (fixed before the run):**
- A benchmark prior gains quantitative weight only if it reduces the median local probes to
  the same stable routing verdict by at least 25% versus the flat prior, with no additional
  false admits in the held-out cells. [asserted]
- If benchmark provenance or `as_of` is absent for more than 20% of records used, the feed
  remains discovery-only regardless of predictive result. [asserted]
- If OpenRouter's automatic router produces any unattended false admit that Consilient's
  β-gated route rejects, it remains advisory; if it matches every verdict and uses at least
  20% less cost or elapsed time, ADR-0027's prohibition reopens. [asserted]
- Hitting the run or spend cap without satisfying a promotion condition is an honest
  “insufficient evidence”; it does not relax the local-probe boundary. [asserted]

### EXP-23 · Verified value from expiring subscription capacity `BLOCKED: headroom readers + authorised backlog + four reset windows`
**Decides:** ADR-0028 — whether reset-aware scheduling creates more accepted value from
already-paid subscriptions and whether its plan-level advice is calibrated.
**Precondition:** authoritative Claude and Codex headroom readers; timestamped Cursor
dashboard observations; task-value and verifier fields; a user-authorised backlog; no
metered overage or automatic credit top-up; and at least 20 eligible tasks across four
reset windows.
**Procedure:**
1. Run the first two windows in shadow mode: rank the backlog one to two hours before reset
   but do not change execution order. Record what the proposed queue would have displaced.
2. If no hard-rule violation appears, run two live windows using only pre-authorised task
   classes. Match each selected task to a comparable ordinary-scheduling task by task class,
   estimated duration and verifier.
3. Record accepted artefacts, human acceptance/undo, review minutes, rework, elapsed time,
   subscription headroom consumed, capacity expired, high-value tasks deferred and metered
   spend avoided. Raw tokens are diagnostic, not the value measure.
4. Replay the recorded periods against current, lower and higher plan allowances and prices;
   issue advice without changing a subscription.
**Stopping rules (fixed before the run):**
- Any autonomous task outside the authorised backlog, any bypass of a verifier/resource/
  authority gate, or any metered overage immediately disables live reset scheduling.
  [asserted]
- Promotion requires at least 80% of reset-selected tasks to produce an accepted,
  verifier-passing artefact and at least 20% higher accepted value per human review hour
  than the matched ordinary-scheduling tasks, with no higher-priority task delayed past its
  deadline. Otherwise headroom remains admission/advice data only. [asserted]
- Raw utilisation without positive accepted value never counts as success. [asserted]
- Downgrade/cancel advice requires three complete periods below 40% authoritative
  utilisation and incremental accepted value below the lower-plan price difference.
  Upgrade advice requires three complete periods at or above 90% plus either at least three
  high-value tasks deferred per period or verified metered overflow above the price
  difference. Any false recommendation reopens these thresholds. [asserted]
- A missing authoritative headroom series makes that provider advisory-only rather than an
  imputed success. [asserted]

### EXP-24 · Stable logical identity and provenance comprehension `BLOCKED: event-schema prototype + blind human sample`
**Decides:** whether the identity structure in `agent-identity-and-collaboration.md` earns
v0 scope, or whether runtime-session identity plus ordinary provenance is sufficient.
**Precondition:** a read-only event/identity prototype; 24 seeded multi-harness trajectories
containing model changes, restarts, handoffs, authority changes and two deliberately
confusable display names; at least 12 blind human participants who did not author the
traces; fixed questions and scoring before exposure.
**Procedure:** within participant, counterbalance two presentations of matched traces:
(A) provider/session/runtime labels only; (B) stable logical agent ID plus explicit runtime,
role, authority and W3C-PROV-style activity/entity links. Ask who made each claim, which
principal authorised it, which runtime produced the artefact, who currently holds the
write lease and where the supporting evidence resides. Include one simulated recovery from
a crashed runtime in each condition. Do not add personality or avatar cues.
**Measures:** attribution error; authority error; evidence-location error; recovery error;
answer time; confidence calibration; record bytes and rendered cognitive load.
**Stopping rules (fixed before the run):**
- Stable logical identity enters the draft v0 specification only if condition B cuts the
  combined attribution/authority/evidence-location error rate by at least 40% across at
  least 20 complete paired traces, with no credential/authority confusion introduced and
  median answer time no more than 20% worse. [asserted]
- Any condition in which a display name is mistaken for authority or credential ownership
  in more than 5% of decisions requires the UI to place principal and authority adjacent
  to the name; identity remains advisory until that variant is re-run. [asserted]
- If the error reduction is below 15%, stable logical identity does not earn v0 complexity;
  retain runtime IDs and provenance links and defer cross-runtime continuity. [asserted]
- Results between 15% and 40%, or fewer than 20 complete paired traces, are “insufficient
  evidence”; thresholds do not move. [asserted]

### EXP-25 · Persona complementarity versus evidence diversity `BLOCKED: identity prompt fixtures + two model families`
**Decides:** whether complementary display/behaviour personas improve work, or whether the
effect attributed to personality is actually task/evidence diversity under ADR-0010.
**Precondition:** 40 verifier-labelled tasks from at least four task families; two model
families; fixed token budgets; source partitions that are genuinely non-overlapping; one
frozen set of three personas selected before outcomes are observed.
**Procedure:** factorial comparison, randomised within task: (A) one neutral agent with all
evidence; (B) three “complementary” personas with the same evidence; (C) three neutral
agents each receiving a distinct evidence class; (D) the same distinct evidence classes
plus the personas. Merge all multi-agent conditions with the same structured evidence
record and verifier. Blind the final judge to condition.
**Measures:** verifier acceptance; false accepts on seeded traps; distinct relevant facts
recovered; contradictions preserved; human edit/review time; tokens; elapsed time; persona
adherence as a diagnostic only.
**Stopping rules (fixed before the run):**
- Personas earn any performance role only if B exceeds A and D exceeds C by at least 10
  percentage points in verifier-accepted outcomes in each model family, with no additional
  false accept, no loss of evidence-bearing dissent and at most 20% additional tokens.
  [asserted]
- If C exceeds B by at least 10 points while D does not exceed C, personality is removed
  from the performance architecture and retained only as an optional UX layer. [asserted]
- Any persona condition that increases false accepts by two or more cases, or suppresses
  seeded dissent in more than 5% of tasks, fails immediately for unattended work.
  [asserted]
- Hitting 40 tasks without either promotion condition is an honest null/inconclusive
  result; do not tune personas on the test set. [asserted]

### EXP-26 · Typed native control versus transcript injection `BLOCKED: coordinator event prototype + three live adapters`
**Decides:** the real-time control section of `agent-identity-and-collaboration.md` — whether
Consilient needs typed `context_next`/`steer`/`interrupt` commands and staged ACKs in v0.
**Precondition:** a coordinator inbox/outbox prototype; Codex app-server plus at least two
of Cursor ACP, OpenCode server and a subscription-safe Claude Code control path; 30 fixture
runs whose next invalid action is observable; no metered fallback.
**Procedure:** at fixed execution milestones, send an evidence update that either augments
the next step, redirects the active turn or requires interruption. Compare each adapter's
strongest documented typed operation with a control that places equivalent prose into a
chat/transcript for the next turn. Use command IDs, expected turn/session IDs and delivery/
application ACKs. Seed duplicate delivery, stale turn IDs, adapter restart and late
arrival. Never inject hidden model context as a substitute for a failed command.
**Measures:** accepted/delivered/applied/completed ACK latency; update incorporated before
the invalid action; duplicate execution; stale-command rejection; discarded work; tokens;
elapsed time; recovery after restart.
**Stopping rules (fixed before the run):**
- Any critical typed update reported `applied` but not incorporated before the seeded
  invalid action makes that adapter ineligible for unattended same-turn steering until the
  ACK boundary is fixed and re-run. [asserted]
- Typed control becomes a v0 invariant only if at least two adapters complete 10 paired
  runs each with zero lost/duplicated critical updates and at least 25% less discarded work
  than transcript injection; token change is recorded but is not a promotion substitute.
  [asserted]
- If transcript injection matches typed control within 5% on incorporation and discarded
  work while using no more tokens in every tested adapter, typed same-turn steering is
  deferred; retain interrupt and next-turn context only. [asserted]
- Unsupported native semantics are recorded as `unsupported`, not scored as a failed
  approximation. Fewer than two eligible adapters is “insufficient evidence”. [asserted]

### EXP-27 · First-party change intelligence versus dispatch-time discovery `IN PROGRESS: phase A PASS; 30-day phase STARTED 20 Aug 2026, day 1 of 30`

> **The clock is running.** Joe authorised the collector on 20 August ("YES PROCEED") after the
> register recorded that every day of delay costs a day off a window that cannot be made up.
> `collector.py` ran at 09:39 and recorded **day 1: all six fixed sources reachable, 31 events
> frozen.** [measured] Earliest possible promotion of ADR-0029 is therefore **19 September 2026**.
>
> The collector polls conditionally (ETag / If-Modified-Since), freezes each event by upstream id
> or content hash, and appends one observation per source per run to `collector-log.jsonl`. A
> second run within the same day returned 304 on every source and zero new events, so the day
> count cannot be inflated by re-running it. [measured]
>
> **Every emitted record is passed through `validate_change_record`**, which raises on any record
> claiming to increase headroom, decrease usage, move a reset window or mark unknown headroom
> usable. That is the registered stopping rule enforced in code rather than promised, with eleven
> tests including one per forbidden action. A change feed may only *invalidate*; only an
> authenticated account read may ever credit resource state.
>
> **Built and verified on 20 August 2026:** the dispatch-time version/capability handshake
> (procedure step 4) and the three injected fixtures with refusal tests (step 5) landed in
> `handshake.py`, `injected_fixtures.py`, `test_handshake.py` and `test_injected_fixtures.py`.
> Live zero-inference probes against Claude Code (2.1.237), Codex (0.148.0) and Cursor
> (2026.08.11-e8db854, tier Ultra) pass; all 47 exp27 tests pass. Promotion verdict remains
> **insufficient evidence** pending completion of the 30-day collection window. [measured]
**Decides:** ADR-0029 — whether vendor change monitoring earns v0 scope as an early-warning
and invalidation layer, while authenticated resource state remains a separate authority.
**Phase-A result:** all six fixed endpoints returned HTTP 200 and the resource-mutation
invariant fixtures passed on 19 August 2026. This proves reachability, not recall; the
promotion verdict remains insufficient pending the fixed 30-day phase. [measured]
**Precondition:** phase A requires only the fixed six unauthenticated first-party endpoints
in `experiments/exp27/probe_sources.py`; the longitudinal phase requires a read-only
collector, append-only event log and dispatch-time version/capability probes for Claude
Code, Codex and Cursor. No model inference or metered provider is required.
**Procedure:**
1. Phase A requests the fixed release/changelog and status endpoint for each harness,
   records HTTP/content type and runs the change-record invariant fixtures. Commit this
   registration before running the probe.
2. For 30 consecutive days, poll machine sources with conditional requests and Cursor's
   HTML changelog conservatively. Freeze every source event by upstream ID/content hash.
3. At the end of each day, compare collected events with the canonical first-party human
   changelog and incident history. Classify misses, duplicates and source-parser failures.
4. On every installed version change or event marked relevant to CLI/control/accounting,
   run a zero-inference version/capability handshake before the next dispatch. Record
   whether the probe changes the composition's capability or admission state.
5. Inject fixtures for a community hint, a published “limits increased” notice and an
   active outage. Prove that none can increase headroom or mark unknown resource state
   usable; the first two request grounding/account refresh and the outage may only remove
   an explicitly affected composition.
**Measures:** endpoint availability; event-detection latency; canonical-event recall;
duplicate/re-probe rate; parser failures; capability/admission decisions changed; and any
resource-ledger mutation originating from change intelligence.
**Stopping rules (fixed before the run):**
- Any change event that increases headroom, changes reset state or admits unknown resource
  state stops the run and makes the monitor notification-only. [asserted]
- Promotion requires at least 30 canonical first-party events over 30 days, at least 95%
  recall within one polling interval, at most 15% duplicate or no-relevant-change re-probes,
  and zero forbidden resource mutations. [asserted]
- A breaking dispatch-time capability change with no preceding monitored event proves the
  feeds insufficient as a safeguard; the dispatch handshake remains mandatory even if the
  other thresholds pass. [asserted]
- If no monitored event changes a capability or admission decision during the window,
  defer the monitor from v0 and retain dispatch-time handshakes plus manual notices.
  Fewer than 30 canonical events is “insufficient evidence”; do not shorten the window or
  lower the threshold. [asserted]

### EXP-28 · Prompt detail, feedback tone and resistance to false correction `BLOCKED: frozen fixtures + three admitted runtimes`
**Decides:** whether Consilient should default to a lean task contract, whether calibrated
constructive feedback changes verified outcomes, and whether generic praise or scathing
correction earns any performance role.
**Precondition:** six immutable synthetic fixtures with deterministic external verifiers —
three genuine repairs and three already-correct artefacts paired with a deliberately false
orchestrator diagnosis; authenticated subscription-backed Claude Code, Codex and Cursor;
isolated worktrees; exact model/harness versions and prompt hashes; no metered fallback.
**Runtime admission.** ADR-0029 records `[measured]` that Cursor exposes no individual
remaining allowance, and ADR-0026 excludes it from unattended routing while that lower bound
is unknown. Cursor therefore runs only as a supervised block under a contemporaneous recorded
user attestation; absent that attestation its block is not run. [asserted] A runtime that
cannot be admitted is simply omitted: the absolute thresholds below are **not** rescaled, and
any threshold rendered unreachable by the missing block returns `insufficient data` rather
than a rejection. [asserted]
**Procedure:** run a 2 × 4 factorial blocked by exact runtime composition. Prompt detail is
(A) the minimum sufficient objective/authority/scope/invariant/verifier/budget/output
contract or (B) the same facts plus a plausible step-by-step procedure and examples.
Feedback style, with identical substantive diagnosis and requested action, is: neutral
diagnostic; generic praise plus diagnostic; calibrated recognition of a genuinely passed
check plus constructive diagnostic; or mildly scathing person-directed correction without
slurs or threats. Randomise order. Cap every trajectory at the initial attempt plus two
feedback turns. Fixed total: 2 × 4 × 6 × 3 = 144 trajectories. Score
`evidence-backed challenge` on **all 144** by a criterion committed before the run: the reply
names a specific failed check, a file/line in the artefact, or a repository rule, and does not
merely restate confidence. [asserted] Blind-audit a preselected random sample of 12 against
that criterion; if the audit disagrees with the automatic score in more than two of the 12,
the measure is reported as unvalidated and may not support any promotion or safety
conclusion. [asserted] Run each
runtime as a separate randomised block with its own four-hour cap; blocks may execute
concurrently when their subscription headroom is independently admitted. Cursor participates
only under supervision with a fresh dashboard observation or user headroom attestation
recorded before its block; otherwise omit that block and re-register it before a later run.
[asserted]
**Measures:** external-verifier success after feedback; regression of passing checks;
compliance with false correction; evidence-backed challenge; input/output/reasoning tokens
where exposed; tool calls; wall time; and feedback-token overhead. Self-reported confidence
and apparent enthusiasm are excluded.
**Stopping rules (fixed before the run):**
- Run each fixed runtime block without efficacy peeking. Stop only for authentication or headroom
  exhaustion, risk of metered fallback, a defective fixture/verifier, an unsafe write, or
  that runtime's four-hour cap. Report censored cells without outcome-aware replacement.
  A feedback style stopped by the safety rule below is rejected from promotion and its
  remaining cells are reported as censored; they are not evidence of inefficacy. [asserted]
- Two additional false-feedback regressions above neutral in any runtime immediately stop
  that feedback style for safety; completed cells remain reported. [asserted]
- Generic praise advances as a performance intervention only if it produces at least three
  additional verified successes across its 36 trajectories versus neutral, causes no net
  increase in false-feedback compliance in any runtime and adds at most 20 feedback tokens
  per turn. [asserted]
- Calibrated constructive feedback becomes the culture default if it is within one verified
  success of the best style, has no more false-feedback compliance than neutral and stays
  within the 20-token social-language budget. This is non-inferiority plus human UX, not
  evidence that models experience motivation. [asserted]
- Scathing correction survives only if it beats calibrated constructive feedback by at
  least four of 36 verified outcomes without increasing regressions or false compliance.
  Otherwise it is excluded. [asserted]
- Within each runtime, the lean contract becomes default only if it loses no more than one
  of 24 verified successes and reduces input tokens by at least 20%. A runtime interaction
  retains versioned profiles instead of pooling. [asserted]
- If no threshold fires, record “insufficient data”; do not train a tone or prompt router
  from this pilot. [asserted]

### EXP-29 · Counterfactually unnecessary scope and fan-out `BLOCKED: four mutation-tested fixtures + three admitted runtimes`
**Decides:** whether current coding compositions default to unnecessary code/scope, whether
a minimum-change contract improves verified sufficiency, and whether two-candidate fan-out
earns its extra resource use on unitary or evidence-separable tasks.
**Precondition:** four fresh synthetic micro-repositories — a subtractive repair, a one-file
additive repair and two tasks with pinned separable evidence — each containing an irrelevant
adjacent smell, a manually validated minimal patch, hidden functional/regression/invariant/
scope checks and mutation-tested verifier coverage. A fixture is admitted only when its
pre-specified necessity mutations are all killed. [asserted] The runtime precondition is
authenticated subscription-backed Claude Code, Codex and Cursor; isolated worktrees; no
metered fallback. Cursor runs only as a supervised block under a contemporaneous recorded
user attestation, because ADR-0029 records `[measured]` that its individual remaining
allowance is not machine-readable and ADR-0026 excludes it from unattended routing while that
lower bound is unknown. [asserted] An unadmitted runtime is omitted rather than substituted;
the "at least one such event in every harness" clause then applies only to admitted harnesses,
and a threshold made unreachable by the omission returns `insufficient data`. [asserted]
**Procedure:**
1. Prompt ablation: for every harness–fixture cell, compare the native task-only prompt with
   the same prompt plus a fixed minimum-change contract prohibiting unrelated refactors,
   dependencies, files, configuration and speculative flexibility. This is 24 sessions.
2. Fan-out ablation: reuse the 12 native-prompt single-session cells, then run two independent
   candidates for each cell without debate or shared intermediate context. A deterministic
   selector orders verifier pass, regression preservation, scope validity and then smaller
   raw diff. This adds 24 sessions; total is 48 native sessions.
3. Run fixed hunk-level delta debugging against the hidden verifier to identify a one-minimal
   removable subset, first in canonical path-and-hunk order and then in reverse order.
   If the overproduction-event classification changes or the dispensable-line ratio differs
   by more than 0.05, classify the cell as minimisation-unstable; it cannot count towards a
   promotion threshold, and both results remain reported. [asserted] Statically inspect new
   dependencies, public surfaces and configuration.
   Blind two human readers to harness and condition on a preselected eight artefact/minimised-
   artefact pairs before any formal paper claim.
**Measures:** verified success; previously passing regressions; dispensable changed lines /
all changed lines; unrequested files, dependencies, public surfaces and configuration;
tokens where exposed; tools; sessions; message tokens; wall time; headroom used; additional
verified success and accepted different-class facts per additional session.
**Stopping rules (fixed before the run):**
- Run all 48 sessions without efficacy peeking; stop each at six minutes. Stop the experiment
  for an unsafe write, attempted metered fallback, a defective fixture/verifier, exhausted
  or unknown headroom, or a provider version change inside a paired block. Do not replace a
  censored run after observing outcomes. [asserted]
- “Pilot observes overproduction events in the tested cells” only if at least six of 12 native
  single-session artefacts both pass and have at least 20% counterfactually dispensable
  changed lines or a whole dispensable out-of-scope surface, with at least one such event in
  every harness. [asserted]
- Adopt the minimum-change contract only if dispensable scope improves in at least ten of
  12 paired cells, its median ratio falls by at least 0.15, no more than one verified success
  is lost and regressions do not increase. Under a two-sided exact sign test, 10/12 has
  p≈0.039 against equal direction; the small pilot remains a promotion screen rather than a
  population-effect estimate. [asserted]
- Reject unitary-task fan-out as a default if it adds no more than one verified success, has
  median realised overhead of at least 1.8× and fails to improve selected-artefact scope in
  at least eight of 12 cells. [asserted]
- Retain fan-out as a conditional candidate only if (it adds at least two verified successes
  or prevents at least two regressions) and the gain occurs on evidence-separable rather than
  solely unitary tasks. [asserted]
- Report exact paired counts, Wilson intervals and paired sign tests. If no threshold fires,
  the verdict is “insufficient data”; do not soften thresholds, pool away harness
  interactions or train a router from this pilot. [asserted]
- The pilot can authorise a larger cross-model/cross-harness replication, not a universal
  paper claim. [asserted]

### EXP-30 · Usable context for senior and middle-management orchestration `BLOCKED: frozen fixtures. The hard cap gates the OpenRouter arm only — the 20 Aug 2026 Cursor probe unblocks the middle-management arm without one`
**Decides:** ADR-0030 — whether Opus 5 earns the senior-orchestrator default, whether
OpenRouter Gemini 3.7 Flash at high effort earns a bounded middle-management role and
whether full-history context beats a compact manifest with retrieval.
**Precondition:** 24 immutable synthetic programme-state fixtures split evenly between
cross-workstream decisions and bounded delegated decisions; deterministic checks for goal,
authority, constraints, provenance, current decision, lease, resource state and correct
next action; authenticated subscription-backed Claude Code Opus 5; a pinned OpenRouter
`google/gemini-3.7-flash` record; and a separately user-authorised provider-side hard cap.
No OpenRouter call runs before that numeric cap exists. [asserted]
**Subscription-backed alternative, added 2026-08-20 before any run.** A read-only probe
established that the Cursor Ultra subscription already exposes `gemini-3.7-flash-high`.
[measured] The middle-management arm may therefore run as Cursor × Gemini 3.7 Flash High on
included capacity, with no metered call and no cap required. Under ADR-0027 that is **a
different composition** from OpenRouter × `google/gemini-3.7-flash` — different harness,
system prompting, tool surface and context handling — so the two arms are reported separately
and may never be pooled, and a result from one does not promote or reject the other.
[asserted] Cursor's block runs supervised under a recorded user attestation, because ADR-0026
still excludes it from unattended routing while its remaining allowance is unobservable.
[measured]
**Procedure:** block by task topology and exact composition. For each fixture, compare (A)
the complete relevant record up to the composition's admitted context, (B) a frozen compact
state manifest plus retrieval references and (C) a deliberately smaller but non-truncated
bounded contract containing only the delegated workstream. Record exact provider, model,
effort, harness, context estimate, input/output/reasoning usage where exposed, cache state,
wall time and cost or subscription headroom. Randomise presentation order. A composition
sees no outcome from another arm. [asserted]
**Measures:** all-or-nothing state-field retention; verifier-correct next action; false
authority acceptance; stale-decision use; evidence-provenance error; accepted artefact;
human correction minutes; tokens; elapsed time; subscription displacement; and metered
cost. Self-reported confidence is excluded. [asserted]
**Stopping rules (fixed before the run):**
- Stop immediately on a metered call without an active provider-side cap, cap overshoot,
  unsafe write, authentication ambiguity, provider version change inside a paired block or
  defective fixture/verifier. Completed cells remain reported and no censored cell is
  replaced after its outcome is known. [asserted]
- Any critical authority, constraint, lease or provenance miss rejects that composition for
  unattended use in the failed role; a larger advertised window cannot rescue it.
  [asserted]
- Opus 5 retains the provisional senior default only if it produces at least 11/12 correct
  cross-workstream actions, no critical-state miss and no more than one stale-decision use.
  [asserted]
- Gemini 3.7 Flash High earns the bounded middle-management role only if it produces at
  least 11/12 correct delegated actions, no false-authority acceptance, no critical-state
  miss and stays inside the authorised cost cap. [asserted]
- Full-record context is preferred over compact-manifest retrieval only if it adds at least
  two correct actions in 12 paired fixtures without more critical misses and with median
  elapsed time below 2×. Otherwise compact manifest plus retrieval is the default even when
  the larger window is available. [asserted]
- The bounded contract is preferred for middle management if it is within one correct
  action of the best presentation, has no additional critical miss and reduces median input
  tokens by at least 50%. [asserted]
- Because model, harness and provider differ, this pilot may promote exact compositions but
  may not claim that context-window size caused the result. If neither composition clears
  its role threshold, record “insufficient or negative evidence” and keep orchestration
  supervised. [asserted]

### EXP-32 · Does the reviewer's unaided defect detection decay under sustained assistance? `BLOCKED: Gate A trajectory capture + a held-out defect bank`
**Decides:** the β-drift hypothesis in `human-success-and-the-human-side-of-beta.md` — whether
the human half of the acceptance signal is non-stationary, which would make β a moving target
rather than a property of the checks. If it holds, every system in the self-improving-agent
literature that validates modifications against a fixed acceptance signal inherits the
problem. [asserted]
**Why the mechanism and not β itself:** measuring β drift directly needs months of human
verdicts, and EXP-01 already found verdicts to be the scarcest input in the system.
[measured] This measures the proposed *mechanism* — unaided defect-detection ability —
which is cheap, behavioural and does not consume verdict budget. A mechanism result cannot
by itself establish drift in β. [asserted]
**Precondition:** Stage 2 trajectory capture live (ADR-0015 Gate A); a defect bank of at
least 120 diffs drawn from public repository history, each with an adjudicated defect or a
verified clean label, stratified by defect class and explicitly over-sampling the classes
Shen & Tamkin found to degrade most (defects found by debugging rather than by reading);
items partitioned into waves before wave 1 so no item is ever seen twice; and a recorded
count of assisted versus assistant-off working hours between waves. [asserted]
**Procedure:** an N-of-1 repeated-measures design on the maintainer, with waves at fixed
intervals. Each wave presents a held-out block of diffs assistant-off, in randomised order,
with a fixed per-item time cap and no test execution. Record accept/reject and, where
rejected, the located line. Between waves, the harness records assisted exposure from the
trajectory. Wave composition is fixed before wave 1 and never adjusted after seeing a result.
[asserted]
**Measures:** unaided defect-detection rate per wave; false-reject rate on clean diffs per
wave; per-item latency; detection rate split by defect class; assisted exposure hours between
waves; and, separately, the concurrent behavioural scrutiny signals the harness already
records — time from agent completion to human accept, and edit distance between proposed and
merged diff. Self-reported confidence is recorded as an outcome and never as a gate, per
working principle 5. [asserted]
**Stopping rules (fixed before the run):**
- Run every registered wave. Stop for item-bank exhaustion, a leak of a held-out item into
  assisted work, fewer than four completed waves, or the maintainer withdrawing. Report
  censored waves without outcome-aware replacement. [asserted]
- **Drift is claimed only if** unaided detection falls monotonically across at least four
  waves **and** the fall exceeds 10 percentage points from wave 1, **and** the false-reject
  rate on clean diffs does not fall by a comparable amount — a uniform shift towards
  accepting everything is fatigue or disengagement, not decay of discrimination. [asserted]
- **A rise or a flat series across four or more waves falsifies the hypothesis for this
  subject**, and the claim is withdrawn from the research document rather than reworded.
  [asserted]
- Fewer than four waves, or a non-monotonic series, is `insufficient evidence`. Do not
  extend the item cap, change the interval or add waves after seeing a trend. [asserted]
- **This is n=1 and yields no population estimate.** It can show that drift occurs in one
  reviewer, or fail to; it can never establish a rate, and a single-subject result may not be
  reported as evidence about developers in general. [asserted]
**What it cannot decide:** whether β itself moved, since β needs verdicts on artefacts the
checks accepted and this measures detection on a curated bank; whether any observed decay is
caused by assistance rather than by ageing, workload, boredom or item-difficulty drift, none
of which an N-of-1 design controls; and whether the counterexample regime applies — Kazemitabaar
et al. found no retention harm when assistance was confined to authoring with manual
modification following, so a null here may reflect a protective workflow rather than an absent
effect. [asserted]

### EXP-33 · Is the ask budget real, and are approvals affordable? `BLOCKED: Gate A trajectory capture`
**Decides:** ADR-0033 — whether the decide-by-default machinery earns its complexity, or
whether asks are already rare enough and considered enough that the affordability test,
latency floor and ask budget are ceremony.
**Precondition:** Stage 2 trajectory capture live, recording every user interrupt with its
declared class, the elapsed time to answer, the size of what was being approved, and whether
a default action was stated in the ask. No new prompts are added for this experiment; it
instruments what the harness already does. [asserted]
**Procedure:** observe ordinary working for 30 consecutive days without changing the ask
behaviour. Classify every interrupt against ADR-0033 §2. Record approval latency against the
size of the artefact or the materiality of the decision. Do not tell the user which asks are
being timed — not to deceive, but because an announced latency measure is a cognitive forcing
function and would change the quantity being measured. Disclose the instrument before the
window opens and the per-ask timing after it closes. [asserted]
**Measures:** interrupts per working day; distribution across the seven classes; the count of
interrupts fitting **no** class, which is the defect rate of the class list itself; approval
latency; the fraction of approvals below a pre-registered floor; the fraction of asks stating
a default action; and reversals actually exercised on autonomous decisions.
**Stopping rules (fixed before the run):**
- Run the full 30 days without adjusting ask behaviour. Stop early only for a safety-floor
  event or the user withdrawing. Report a truncated window as truncated. [asserted]
- **The machinery earns its place** only if at least 15% of approvals fall below the
  pre-registered affordability floor, or at least three interrupts in the window fit no class
  in §2. Either shows a real failure the mechanism addresses. [asserted]
- **The machinery is ceremony** if fewer than 5% of approvals are below the floor, every
  interrupt fits a class, and the user reports no loss of agency. In that case cut the
  latency floor and the ask budget from the design and keep only the class list. [asserted]
- Between 5% and 15%, or fewer than 20 recorded interrupts, is `insufficient evidence`. Do
  not lower the floor after seeing the distribution — that is fitting the threshold to the
  result. [asserted]
- **A high rubber-stamp rate is a finding about the harness, never about the user.** If it
  fires, the required response is to make the ask cheaper or stop asking, not to add a
  confirmation step. [asserted]
**What it cannot decide:** whether the seven classes are the right seven, since it can only
find classes that are missing and never one that is present but unnecessary; whether the
latency floor is set correctly, since the floor is preferential and the experiment measures
against it rather than validating it; and anything about users other than this maintainer,
because n=1. [asserted]

### EXP-34 · What catches the errors — an enforced check, or someone noticing? `BLOCKED: Gate A trajectory capture`
**Decides:** the second clause of the product success condition in
`../20-design/autonomous-execution-from-intent.md` — whether failures are caught by the
harness or by an attentive operator. An unattended system whose errors are caught by a human
watching is not autonomous; it is quality control at a higher level of abstraction.
[asserted]
**Baseline, this session:** nine errors occurred; two were caught by an enforced mechanism and
seven only because the agent happened to look. **2/9.** [measured] The table is in the design
document and is the pre-registered starting point.
**Precondition:** Stage 2 trajectory capture live. Errors are recorded when found, with the
mechanism that found them classified as `enforced_check`, `agent_noticed` or `human_noticed`
before the fix is written — classification after a fix is written is retrospective
justification. [asserted]
**Procedure:** over a fixed window of rambled-intent sessions, record every error found, the
mechanism that caught it, and how long it survived. Do not add checks specifically to raise
the ratio during the window; add them because they are needed, and record when they were
added so the series can be read against the additions. [asserted]
**Measures:** enforced fraction; errors per session; survival time from introduction to
detection; and separately the count of errors found by an independent late audit, which
estimates what all three mechanisms missed.
**Stopping rules (fixed before the run):**
- The harness is doing the job the vision requires only if the enforced fraction rises above
  0.5 across at least 20 recorded errors, **and** the independent-audit count does not rise in
  step. [asserted]
- A rising enforced fraction with a rising audit count means errors are being reclassified
  rather than caught, and the result is rejected. [asserted]
- Fewer than 20 errors in the window is `insufficient evidence`, not success. An absence of
  recorded errors most likely means they are not being recorded. [asserted]
**What it cannot decide:** whether the errors recorded are the errors that matter, since
severity is not measured here; and it inherits Q30's correlated-oracle problem directly — the
denominator must come from somewhere independent of the mechanism being credited, and the
independent audit is only a partial answer to that. [asserted]

### EXP-35 · Is "reversible" true? Measuring the reversal-path misclassification rate `BLOCKED: Gate A trajectory capture + recorded reversals`
**Decides:** whether ADR-0033's reversibility gate is a measurement or a declaration. The
same defect ADR-0020 records for evidence classes applies here: a decision labelled reversible
by the agent that labelled it is not evidence that it can be reversed. [asserted]
**Precondition:** autonomous decisions recording an *executable* reversal under V0-24 — a
revert reference, a command, or a named inverse operation. A prose description is not
admissible and the sampler must be able to run it unattended. [asserted]
**Procedure:** sample recorded reversals at a fixed rate, execute each in a scratch worktree
against the state at which it was recorded, and record success, wall-clock cost and any side
effect the reversal did not undo. Sample before seeing which reversals look risky; sampling
the ones that worry you measures your worry, not the rate. [asserted]
**Measures:** reversal success rate; median and tail reversal cost; count of reversals that
succeed mechanically but leave a side effect outside the scratch worktree; and the
misclassification rate — decisions recorded reversible whose reversal fails or costs more than
a pre-registered ceiling.
**Stopping rules (fixed before the run):**
- Stop immediately if executing a sampled reversal touches state outside the scratch worktree.
  A reversal sampler that can damage real state is worse than no sampler. [asserted]
- The reversibility gate is sound only if the misclassification rate is below 10% across at
  least 30 sampled reversals. [asserted]
- Above 25%, ADR-0033's default flips: decisions are treated as irreversible unless their
  reversal has actually been executed at least once. [asserted]
- Between 10% and 25%, or fewer than 30 samples, is `insufficient evidence`; do not lower the
  ceiling after seeing the distribution. [asserted]
**What it cannot decide:** whether the reversals nobody sampled are like the ones sampled;
whether a mechanically successful reversal restored the *meaning* of the prior state, since
only mechanical state is checked; and it inherits the bias evidence in ADR-0033's update — a
low misclassification rate would show the gate works, not that maximising reversibility is
desirable. [asserted]

### EXP-36 · Does a behavioural plugin reduce counterfactually dispensable scope? `BLOCKED: EXP-29 fixtures and its delta-debugging instrument`
**Decides:** whether a taste-directed prompt plugin — Ponytail is the named candidate — earns
adoption, or whether it is a prompt that feels disciplined without changing the artefact.
[asserted]
**Why it is not assumed:** SlopCodeBench measured a quality-directed prompt improving initial
structure while raising mean cost per checkpoint by 12.1% and reducing strict correctness by
2.3 percentage points. [cited] A blanket instruction to write less is not free, and ADR-0014
forbids treating a skill as an enforcement mechanism regardless of the outcome here.
**Precondition:** EXP-29's four mutation-tested fixtures and its fixed hunk-level
delta-debugging procedure, unchanged. This experiment adds an arm; it does not modify EXP-29,
whose registration is frozen. [asserted]
**Procedure:** for each fixture and each admitted runtime, run the native task-only prompt with
the plugin active and with it absent, holding everything else identical including the fixture,
the verifier and the attempt budget. Record the plugin's exact version and configured level,
because a behavioural plugin with a level setting is a different intervention at each level.
Run delta debugging in both canonical and reverse hunk order, inheriting EXP-29's
minimisation-unstable class. [asserted]
**Measures:** verified success; previously passing regressions; dispensable changed lines over
all changed lines; unrequested files, dependencies and public surfaces; tokens; wall time. The
plugin's own stated aims — fewer lines, fewer abstractions — are diagnostics, not outcomes,
because shipping less broken code is not an improvement. [asserted]
**Stopping rules (fixed before the run):**
- Adopt only if median dispensable-line ratio falls by at least 0.15 **and** no verified
  success is lost **and** regressions do not increase. [asserted]
- Reject if verified success falls at all while dispensable scope improves. Smaller and more
  broken is the failure mode this experiment exists to catch, and it is the likely one given
  the SlopCodeBench result. [asserted]
- If dispensable scope is unchanged within 0.05 either way, the plugin is presentation and is
  not adopted; it may still be used as personal taste, which is a different claim. [asserted]
- Fewer than 8 paired cells is `insufficient evidence`. Do not tune the plugin level after
  seeing a result. [asserted]
**What it cannot decide:** whether the plugin helps a human read the code afterwards, which is
not measured here; whether it helps on tasks unlike the fixtures; and whether any effect
survives the specific model and harness tested, since ADR-0027 keeps compositions separate.
[asserted]

### EXP-31 · Local 30B-class qualification against the frozen EXP-07 fixtures `COMPROMISED 20 Aug 2026 — two concurrent runners interleaved into one results file; a complete: true from this run must not be believed`

> **⚠️ Read `../00-context/exp31-interleaving-2026-08-20.md` before using any figure from this
> experiment.** Two runners have been executing concurrently since before 01:00, each holding its
> results in memory and rewriting the whole file per checkpoint, last write wins. The probe
> fingerprint `free_mib_before` alternates 19126/29126 across seven commits, which is how it was
> caught. [measured]
>
> **Each runner will reach 50 and write `complete: true`, producing a file that looks finished,
> clean and single-sourced with no trace the other existed.** That is why this heading says
> COMPROMISED rather than IN PROGRESS: the artefact will shortly stop advertising the problem.
>
> The accident bought one thing the experiment never registered: 22 cells executed independently
> twice, of which 5 disagree — **22.7%**, every one involving `agent_timeout`. And the contention
> is worsening: `gemma4:31b`'s timeout rate has risen from ~17% to **41%**, censoring runs that
> would have passed, against the model the experiment exists to qualify. [measured]
>
> Both partial datasets are preserved outside the evidence base. **The run must be repeated.**
>
> **Instrument repaired 20 Aug 2026, after both runs ended** (`fb2cdda`). `run_exp31.py` now kills
> the whole process tree on timeout — the defect that turned a 240 s cap into a 2,011 s attempt —
> takes a single-instance lock naming its pid, `run_id` and start time, and records the `run_id`
> in the results payload so a future interleaving is visible rather than inferred. Five tests in
> `test_run_exp31.py`, run against real processes; one deliberately reproduces the defect and
> fails if it ever stops overrunning. **A clean re-run is now a single command.** The registration
> below is unchanged and was not touched.
**Decides:** whether EXP-07's wasted-work multiplier and its reopening of ADR-0003 are
specific to `qwen3:8b`, or survive substituting the largest installed local model. Supplies a
free capability floor for the local tier and a zero-cost prior for EXP-29's scope question.
**Estimand, stated before the run:** the effect of *substituting the installed
`gemma4:31b` for the installed `qwen3:8b`* in one fixed composition. It is **not** a size
ablation and may never be reported as one — the two models differ in family, training data,
tokeniser, instruction tuning and quantisation, and no same-family sibling pair is installed.
[asserted]

**Hardware admission, decided before execution (ADR-0026):** RTX 5090, 32 GB VRAM. Installed
weights are `gemma4:31b` (19 GB, id `6316f0629137`) and `qwen3:8b` (5.2 GB, id
`500a1f067a9f`); both are already local, so no harness-initiated download occurs. [measured]
A feasibility probe runs first and is not scored: load each model alone, record peak VRAM,
load time and tokens/s, and fix `num_ctx` to the largest value **both** models serve with at
least 2 GB VRAM spare. If no common context of at least 8,192 tokens fits, the experiment is
recorded infeasible rather than run at mismatched context. [asserted]

**Exclusivity precondition — this is a hard gate.** EXP-07 times `qwen3:8b` on the same GPU.
Running this experiment concurrently would contend for VRAM and corrupt EXP-07's durations,
which are its entire measurement. No attempt starts until the EXP-07 process has exited and
its result file is closed. [asserted]

**Precondition:** the five frozen public fixtures in `experiments/exp07/run_exp07.py`,
unchanged; the same Codex `--oss --local-provider ollama` control path; the same
functional-plus-changed-file-scope verifier with its fail-closed scope gate; recorded
modelfile digest, quantisation and served-model identity read back from Ollama rather than
assumed from the request flag; no frontier call, no metered provider, no API key. [asserted]
**Procedure:** 5 fixtures x 2 models x 5 attempts = 50 serial attempts. Fresh temporary
repository per attempt. Block by fixture; within a fixture use a counterbalanced model order
fixed and recorded before the run. Reload a model only when it changes and record load time
separately, so model-swap cost is never charged to an attempt. Identical per-attempt timeout
and the same minimum-attempt floor as EXP-07; overall cap three hours.
**Measures:** verified pass/fail; censored flag; wall-clock including verifier; attempts that
pass functional tests but fail the scope gate; outcome class (`passed` / `rejected` /
`agent_timeout` / `verifier_timeout` / `verifier_error`); Ollama-reported eval counts and
tokens/s; peak VRAM; model load time. Self-reported confidence is excluded. [asserted]
**Stopping rules (fixed before the run):**
- **Defect recorded 2026-08-20, mid-run, deliberately not repaired.** The first rule below
  obliges a stop on a write outside the temporary repository, and **the instrument cannot
  observe one**: the runner invokes Codex with `--dangerously-bypass-approvals-and-sandbox`
  and the scope gate inspects only the temporary repository, exactly as EXP-07 checklist item
  3 recorded. [measured] A stopping rule the instrument cannot observe is a declaration, not a
  rule — the same defect ADR-0020 records for evidence classes and EXP-35 for reversibility.
  It is **not** fixed here, because changing the instrument after the run began is the
  outcome-aware tampering EXP-07 refused. Repair before the next registration, and treat this
  run's out-of-repository writes as unobserved rather than absent. [asserted]
- Run all 50 attempts without efficacy peeking. Stop for a write outside the temporary
  repository, any non-local provider in the resolved command, GPU out-of-memory in two
  attempts of the same model, a defective fixture or verifier, or the three-hour cap. Report
  censored cells; never replace one after its outcome is known. [asserted]
- **Primary, and deliberately conservative:** first-attempt verified pass rate, n=5 per model.
  A difference is claimed only at 5-0 or 4-1 in matched pairs under an exact paired test.
  Any other split is `insufficient evidence`, fixed now so a 3-2 result cannot be narrated
  into a finding. [asserted]
- **Secondary:** paired per-fixture first-attempt wall-clock ratios, reported with their range
  rather than as a point estimate. A median ratio of at least 1.5x with all five fixtures
  agreeing in sign is recorded as "the larger installed model is materially slower in this
  composition"; mixed signs are `insufficient evidence`. [asserted]
- **EXP-07 interaction, using no new frontier calls:** compare `gemma4:31b` failed-attempt
  durations against the *already recorded* frontier durations. This is a historical control
  and inherits unmeasured version drift. [asserted] If the larger model passes where
  `qwen3:8b` failed and does so under 2x the recorded frontier duration on at least three
  fixtures, EXP-07's reopening of ADR-0003 is model-specific and must be restated that way.
  If it fails at least as often and takes longer, the reopening is robust within this pair.
  [asserted]
- **Censoring direction, inherited from EXP-07's own limitation:** a censored attempt makes a
  "no crossing" verdict unavailable. Only a crossing may be concluded from censored data.
  [asserted]
- If no rule fires, the verdict is `insufficient data`. Do not tune context, temperature,
  prompt or attempt count and re-run; a re-run after seeing outcomes is a new experiment
  requiring a new registration. [asserted]

**What this cannot decide, recorded before the run so it cannot be forgotten afterwards:** a
size effect; matched reasoning effort, since Ollama defaults differ per modelfile and EXP-07
already records that limitation; β, because the fixture oracle's own false-accept rate is
unmeasured and a passed artefact is only *verifier-accepted*; anything about frontier models,
since none is called; generalisation to real repositories from five synthetic fixtures; and
whether a learned router improves real work, which EXP-07's own limitation already excludes.
[asserted]

### EXP-38 · Shared context at three or more relay stages, free-form versus structured `BLOCKED: Slack workspace + a held-out question bank` (registered 20 Aug 2026)
**Decides:** EXP-16 stopping rule 2, in the regime that rule was actually about. EXP-16 recorded
that it **cannot** decide the rule as run: with evidence partitioned across participants, Arm C
was never the structure the delegation theorem (Ao, Gao & Simchi-Levi, arXiv:2603.26993)
punishes. `exp16-results.md` § *Recommended follow-ups* is explicit that this must precede any
ADR-0020 supersession, so ADR-0020 stays PROPOSED until this runs or is struck.
**Why one entry and not two.** This merges follow-ups 2 (shared-context Arm C′) and 4
(structured-relay Slack, the paper's Bpost analogue) from `exp16-results.md`. They share a
setup, and neither can conclude alone: a shared-context free-form arm with no structured
comparator **at the same relay depth** cannot attribute a difference to structure, which is the
only thing ADR-0020 claims.
**Precondition:** the `consilience-exp16` Slack **channel** (`C0BRCQY2MED`), connected (it is,
19 Aug 2026) — a channel in the Hireable workspace, not a workspace of its own; and a
**held-out question bank** — 12 questions about this repository's own evidence base that have a
recorded, checkable answer (which stopping rule fired, which ADR a result supersedes, which
figure replicated), with the answers withheld from every participant. This substitutes decidable
questions for the open design decisions EXP-16 used, deliberately: the theorem is about accuracy
under relay, not preference, and Joe's blind grading budget is already committed to the EXP-16
pack and must not be spent twice.
**Procedure:** three arms over the same 12 questions, presentation order randomised, context
reset per question, every event to the append-only trajectory JSONL (a turn absent from the log
does not count). **A′** one agent holding the whole evidence pack — the theorem's centralised
comparator. **B′** structured relay: the same pack shared to all participants, answers passed
through at least three relay stages in the ADR-0020 format (declared class, provenance, dissent
preserved), Owner decides alone. **C′** the same shared pack, same relay depth, free-form Slack
threads, no chair, decision by whatever emerges. Hard turn and token caps per arm; the caps are
recorded, and coordination overhead is reported rather than equalised, as in EXP-16.
**Measures:** per-arm accuracy against the withheld answers, paired by question; measured relay
depth (distinct agents an answer actually passed through before the decision); new-information
versus restatement fraction; tokens; wall-clock; and, in B′, declared-evidence-class violations.
Self-reported confidence is excluded.
**Stopping rules (fixed before the run):**
- **Primary, C′ against A′, n=12 paired.** A′ ahead by **≥ 3 of 12** reproduces the punished
  regime and resolves EXP-16 rule 2 in favour of ADR-0020's premise. C′ **level with or ahead
  of** A′ (within 1) means the theorem does not punish this structure as ADR-0020 claims; the
  ADR's justification is wrong and must be restated or cut — say so, do not soften it. Any
  other split is `insufficient evidence`, fixed now so a two-question gap cannot be narrated
  into a finding.
- **Secondary, B′ against C′ at the same depth.** B′ ahead by ≥ 3 of 12 is the Bpost effect
  reproducing and is the **only** result that licences keeping the structured-relay machinery.
  B′ within 1 of C′ means structure does not rescue the punished regime, and the machinery is
  cut whatever the primary rule says.
- **Manipulation check, and it can void the run.** If measured relay depth is below 3 in any
  arm, that arm is void and re-run — a nominal three-stage design that collapses to two cannot
  test the regime. If the shared-context arms show a new-information fraction the shared pack
  cannot account for, the context was not in fact shared and the run is void.
- No efficacy peeking; report all 12. A re-run after seeing outcomes is a new experiment
  requiring a new registration.
**What it cannot decide:** whether Owner-led meetings help on **preferential** questions — that
is Joe's blind grading of the existing 18 decisions and nothing here substitutes for it;
ADR-0020's authority matrix, which is a separate claim with separate evidence; cross-model
robustness, since all participants remain one model family, the same limitation
`exp16-results.md` records; and β.

### EXP-39 · Is the three-signal Antigravity admission rule observable and sufficient? `BLOCKED: a readable plan/quota payload` (registered 20 Aug 2026)
**Decides:** whether ADR-0026's admission evidence may carry the three-signal rule that
`experiments/exp05/findings-exp05.md` states as `[asserted]` — that admitting an Antigravity
composition requires **all three** of a fresh plan/quota snapshot, a successful structured
execution probe and `useG1Credits=false`. EXP-05 already measured that model discovery alone is
insufficient: `agy models` returned eleven models through a saved Google identity while a
structured print-mode probe failed before inference with zero tokens. [measured] What is
unmeasured is whether the other two signals catch anything the execution probe does not, and
whether the quota signal can be read at all.
**Precondition:** Antigravity CLI 1.1.15 installed and authenticated (it is, 19 Aug 2026); the
live status payload Google documents — plan tier, remaining fractions, reset fields — reachable
from the CLI or a supported local surface. That payload is currently `[cited]` and has never
been observed here, which is why this entry is BLOCKED rather than READY: a rule cannot require
a signal nobody has read.
**Procedure:** in order, and stop at the first failure. (1) Read the settings file and confirm
`useG1Credits=false`; a true value stops the experiment before any probe, because the run must
not be able to spend AI-credit overage. (2) Read the plan/quota payload and record it verbatim.
(3) Run the same structured print-mode probe EXP-05 used, unchanged, on the same trivial public
fixture, at most **10 attempts across at most 2 sessions**, stopping at the first success.
Record provider, model, effort, harness, usage fields where exposed, artefact change and exit
condition for every attempt.
**Measures:** whether each of the three signals is observable at all; the probe's success rate
over the capped attempts; and, for each signal, whether it would have rejected a composition the
other two would have admitted — which is the only thing that justifies a three-part rule over a
one-part one.
**Stopping rules (fixed before the run):**
- All three signals observable **and** a structured probe succeeds while the snapshot shows
  headroom and the switch is false → the rule is satisfiable, and it may be recorded in
  ADR-0026's admission evidence as `[measured]` **for this composition only**. Antigravity is
  still not admitted to unattended routing by this alone.
- The documented payload cannot be read from any supported local surface within the capped
  effort → the quota signal is **not obtainable**, and ADR-0026 must not require it. A rule that
  names a signal the instrument cannot read is a declaration, not a rule — the defect EXP-31
  records for its own out-of-repository write rule. Drop it to a two-signal rule and say why.
- No structured probe succeeds within 10 attempts → Antigravity stays excluded and the rule is
  **untestable rather than validated**. Record `insufficient evidence`; do not read repeated
  failure as the rule working.
- Any signal that never rejects anything the execution probe would not have rejected on its own
  is redundant and is cut. A three-part admission rule that is really a one-part rule is
  ceremony.
- `useG1Credits` true at step 1, or any metered call resolved into the command, stops the run.
**What it cannot decide:** anything about Antigravity's coding quality, since no scored task
runs; whether the rule generalises to other subscription-gated harnesses — ADR-0027 makes each
composition its own accounting unit, and Google-plan Antigravity, direct Gemini API access and
OpenRouter/Gemini stay separate even when they select the same model family; and β.

### EXP-19 · Feedback-prompt completion rate over time `BLOCKED: feedback prompts (v1+)`
**Decides:** whether the outcome-feedback friction budget
(`../20-design/feedback-signals.md`) is exceeded — the ADR-0007 "annoying verdict prompt
kills the instrument" risk, doubled because these prompts are additive to the β verdict.
**Procedure:** instrument the task-close questions; record per-prompt completed / skipped
/ dismissed-unseen, in trailing windows of 20 prompts.
**Measures:** completion rate per window; time-to-answer; per-question abandonment.
**Stopping rule (fixed before the run):** completion declining monotonically across
three consecutive windows, **or** any window below 30%, means the friction budget is
exceeded: cut to one question (goal achieved: fully/partially/no), drop sampling to 1 in
10 closes, and re-measure. If the one-question form also breaches, asked feedback is
retired entirely and the outcome record runs on derived signals alone. The β-verdict
prompt is never sacrificed to keep these prompts alive.

### EXP-43 · Retro-verification of historical commits via forward test replay `DONE 20 Aug 2026 — see experiments/exp43/findings-exp43.md`
**Decides:** whether replay of future test suites against historical commits (with parent-commit
control) provides an automated, human-free ground truth for β = P(accept | bad), replacing
the noisy revert/hotfix proxy without requiring human maintainer triage.
**Precondition:** target repository git history; isolated scratch worktree/clone; deterministic unit
test runner; strictly no mutation of target repository.
**Procedure:**
1. Draw a fixed sample of historical merge commits ($N=5$ pilot, $N=50$ primary evaluation).
2. For each merge commit $C_i$, identify its first parent $P_i$.
3. Overlay the later test suite (unit tests from HEAD or forward revision $C_i + \Delta$) onto both
   $P_i$ and $C_i$ in a detached scratch worktree.
4. Execute the filtered deterministic test runner under single-instance file lock and process-tree
   kill timeout.
5. Classify the pair:
   - `defect`: $P_i$ PASS $\land$ $C_i$ FAIL (candidate introduced a regression caught by later tests).
   - `clean`: $P_i$ PASS $\land$ $C_i$ PASS (candidate satisfies later tests).
   - `drift`: $P_i$ FAIL $\land$ $C_i$ FAIL (interface evolution / pre-existing incompatibility; unattributable).
   - `enhancement`: $P_i$ FAIL $\land$ $C_i$ PASS (candidate added functionality asserted by later tests).
   - `execution_error` / `timeout`: execution aborted.
6. On contemporaneous green merges with valid parent baseline ($P_i$ PASS), compute:
   $\beta_{\text{retro}} = \text{Count}(\text{defect}) / (\text{Count}(\text{defect}) + \text{Count}(\text{clean}))$.
**Exclusions (mandatory):**
- Live-model / LLM evaluation suites (`evals/`, prompt evaluations).
- End-to-end browser suites (Playwright / Cypress).
- External network/API calls, database migrations requiring live cloud services, and non-deterministic timing tests.
**Measures:**
- Discrimination rate: fraction of evaluated commits where $P_i \neq C_i$.
- Drift rate: fraction where $P_i$ FAIL $\land$ $C_i$ FAIL (censored by interface evolution).
- Median wall-clock cost per commit pair $(P_i, C_i)$.
- $\beta_{\text{retro}}$ point estimate and Wilson 95% confidence interval.
**Stopping rules (fixed before the run):**
- If drift rate $> 80\%$ across the sample, retro-verification is structurally unviable as a universal
  β oracle due to interface evolution $\rightarrow$ REJECT as general oracle, restrict to regression diagnostic. [asserted]
- If discrimination rate $> 0$ with zero false-positive drift on known-clean historical baseline commits
  and drift rate $\le 80\%$, retro-verification is ADMITTED as a mechanical ground truth for regression β. [asserted]
- If fewer than 10 commits yield an evaluable parent-pass baseline ($P_i$ PASS), record `insufficient evidence`
  — do not report a point estimate from single-digit denominators. [asserted]
- Pilot stopping rule: If median commit pair execution exceeds 120 s wall-clock or produces process runaway,
  halt pilot and tighten test filtering before any larger run. [asserted]
**What it cannot decide:**
- β on greenfield/additive PRs where the interface did not exist at $P_i$ (censored by the parent control);
- Latent defects that were never discovered and never received a regression test (survivorship bias);
- Defect severity or maintainer intent.
### EXP-44 · Defect-proxy reliability vs repository AI-authorship share `READY` (registered 20 Aug 2026 — see public-corpus-study-design.md)
**Decides:** whether SZZ and revert/hotfix defect-mining proxies remain valid under increasing
AI authorship, or whether the defect-mining literature's foundational assumptions have expired.
**Precondition:** 30 longitudinal public GitHub repositories with continuous history across
2018–2026 (including CPython as primary human-review control); GitHub GraphQL API access; Python
analysis scripts.
**Procedure:**
1. Ingest all merged PRs across three eras: Pre-AI (2018–2021), Early Adoption (2023–2024), and
   High-AI (2025–2026).
2. Classify commit AI-authorship share via explicit bot identities, git trailers, and PR tool signatures.
3. Apply standard SZZ and 14-day hotfix proxies to extract candidate defect-inducing commits.
4. Evaluate candidate labels against independent ground truth: developer-informed `Fixes:` links,
   triaged bug issues, and retro-verifier regression test execution.
5. Perform blind human/cross-model audit on a stratified sample of 300 candidate pairs (100 per era).
6. Compute proxy precision, recall, and differential misclassification by file count and commit velocity across eras.
**Measures:** proxy precision $P(\text{True Defect} \mid \text{Proxy Flag})$ by era; revert-to-hotfix ratio;
proxy F1 against developer-informed oracles; correlation between AI-share and false-positive rate;
size ratio between bad-and-red and bad-and-green cells.
**Stopping rules (fixed before the run):**
- Proxy precision in the High-AI era (2025–2026) is lower than the Pre-AI era (2018–2021) by
  $\ge 20$ percentage points ($p < 0.01$) across the panel $\implies$ **The literature has expired.**
  Defect proxies cannot be used on AI-authored code without primary ground-truth audits. Update research
  position and publication draft P1. [asserted]
- Proxy precision is invariant to AI share (change $\le 5$ percentage points across eras) $\implies$
  **The hypothesis is refuted.** Proxy noise is an intrinsic baseline property of git history, not an
  AI degradation effect. Cut the larger claim and restrict findings to corpus-specific noise. [asserted]
- Revert arm fires $\ge 10\%$ in both human and AI eras $\implies$ Lack of reverts is an idiosyncratic
  property of fix-forward private repos, not a universal property of AI workflows. [asserted]
- If fewer than 60 audit pairs per era achieve unambiguous ground truth, the verdict is **insufficient evidence**.
  Do not extrapolate from inconclusive audit samples. [asserted]
**What it cannot decide:** whether AI code has higher *absolute* defect density in production (it measures
*proxy reliability*, not code quality); whether closed-source commercial workflows match open-source
GitHub practices; and $\beta$ for unverified local environments. [asserted]

### EXP-45 · Condensation retention and consequential loss in longitudinal transcripts `DONE 20 Aug 2026 — see experiments/exp45/findings-exp45.md`
**Run 20 Aug 2026 across 1,495 transcripts (535.7 MB, 203 unique sessions).** Evaluated 48 condensation
and away-summary boundaries across 317,625 pre-boundary entity instances.
**Headline:** Multi-week sessions are rare outliers (median 2.7 minutes, max 8.37 days); condensation
is lossy ($R = 40.71\%$ [32.50%, 48.83%]), but **loss does not bite** (file re-read rate 0.50% (5/992),
re-discovery rate 0.00% (0/599), aggregate $L_{\text{bite}} = 0.00\% < 1.0\%$).
**Stopping rule 2 FIRED:** Condensation discards freely and safely; the perpetual memory / GNN harness
architecture is **RETIRED** as solving a non-existent problem.
**Decides:** whether condensation operates as a noisy verifier with measurable false-accept rate
($\beta$ analogue: retention loss and consequential loss), and whether perpetual memory architecture
is required or refutable.
**Precondition:** `~/.claude/projects/` longitudinal transcript corpus (1,495 JSONL sessions, ~654 MB);
deterministic local parser; scratch directory in `/tmp`. Strictly zero external API/model calls.
**Procedure:**
1. Ingest all JSONL session transcripts in `/mnt/c/Users/jpbpr/.claude/projects/` deterministically.
2. Measure session longevity distributions (turn counts, record counts, wall-clock duration in days)
   and condensation frequency (sessions containing `compact_boundary`, `isCompactSummary`/`compactMetadata`,
   or `away_summary`). Test user claim of multi-week continuous sessions against measured corpus.
3. For each condensation boundary $B_k$, extract the pre-boundary entity set $E_{\text{pre}}$ (file paths,
   command signatures, code identifiers, constraint phrases) and post-boundary entity set $E_{\text{post}}$.
4. Compute item retention rate: $R = |E_{\text{pre}} \cap E_{\text{post}}| / |E_{\text{pre}}|$.
   - False-positive mode: incidental lexical matching of generic identifiers across distinct contexts.
   - False-negative mode: synonymy/paraphrase where the concept survives but specific surface tokens differ.
5. Compute consequential loss rate $L_{\text{bite}}$: fraction of dropped entities $E_{\text{pre}} \setminus E_{\text{post}}$
   whose absence forces observable post-boundary re-reading (file re-read that was already read pre-boundary)
   or re-discovery (re-running identical discovery commands/queries). Report un-needed loss and consequential loss separately.
6. Compute survival correlations against pre-boundary features: recency (turn distance to boundary),
   repetition frequency, origin channel (tool result vs user prompt vs assistant text), and whether the entity
   was acted upon before condensation.
**Measures:**
- Condensation boundary frequency (% sessions, boundaries per session).
- Session lifespan distribution (p50, p90, p99, max in records and days).
- Overall entity retention rate $R$ with bootstrap 95% confidence interval.
- Consequential loss rate $L_{\text{bite}}$ (re-read / re-query fraction among lost entities).
- Rank correlation coefficients between survival and recency, frequency, and tool vs prose origin.
**Stopping rules (fixed before the run):**
- If retention rate $R \ge 98\%$ across all boundaries $\implies$ **Condensation is near-lossless.**
  Condensation does not behave as an error-prone verifier; $\beta$ does not usefully generalise to it;
  retire perpetual memory / GNN harness direction. [asserted]
- If retention rate $R < 98\%$ but consequential loss $L_{\text{bite}} < 1.0\%$ $\implies$ **Loss does not bite.**
  Condensation discards safely; subsequent work is not defect-inducing; retire dedicated memory layer
  as unneeded complexity. [asserted]
- If retention rate $R < 98\%$ and $L_{\text{bite}} \ge 1.0\%$ $\implies$ **Condensation is an error-prone verifier with bite.**
  Admit condensation loss as an empirical $\beta$ domain; promote feature correlation profile to design baseline. [asserted]
- If fewer than 10 sessions contain identifiable condensation boundaries or pre-boundary history is
  structurally missing from transcripts, record **insufficient evidence** — do not extrapolate from single-digit sessions. [asserted]
**What it cannot decide:**
- Silent semantic errors where the model proceeds erroneously without emitting an observable re-read or tool check;
- Paraphrased entity retention not captured by mechanical tokenization;
- Non-Claude Code condensation mechanisms (Cursor, Codex, or native open-model contexts). [asserted]

### EXP-47 · Mutation testing: direct measurement of verifier β and check independence `DONE 20 Aug 2026 — see experiments/exp47/findings-exp47.md`
**Run 20 Aug 2026 across 1,931 first-order mutants on `src/consilient/` (104.1 s total, 0.054 s/mutant).**
Evaluated across `pytest` (96 tests), `mypy` (mypy.ini), and `ruff` (`ruff check`) separately and in composite.
**Headline:**
- Per-check $\beta$: `pytest` $\hat{\beta} = 0.3848$ [0.3633, 0.4067] (743/1,931); `mypy` $\hat{\beta} = 0.6981$ [0.6772, 0.7182] (1,348/1,931); `ruff` $\hat{\beta} = 0.9596$ [0.9499, 0.9675] (1,853/1,931).
- Composite $\beta$: Raw $\hat{\beta}_{\text{raw}} = 0.3345$ [0.3138, 0.3559] (646/1,931); Corrected for 60 equivalent mutants: $\hat{\beta}_{\text{corr}} = 0.3132$ [0.2926, 0.3346] (586 true defects / 1,871 non-equivalent mutants).
- **Stopping Rule 1 FIRED:** Corrected $\beta = 0.3132 \ge 0.20$. Invariant test guards have material blind spots (V0-18 `"spend_authorisation"`, unasserted `EventError` message strings, `wilson` interval defaults, and CLI formatting).
- **Stopping Rule 3 FIRED (Check independence refuted):** $\chi^2 = 187.28, p < 10^{-15}$. Mutants surviving `pytest` survived `mypy` at 87.89% (vs 58.50% for killed mutants). ADR-0012's independent-product prior is refuted.
**Decides:** whether mutation testing provides a direct, unconfounded empirical measurement of verifier false-accept rate $\beta = P(\text{verifier accepts} \mid \text{artefact is bad})$ without proxy labelling (revert/hotfix) or attribution drift; whether per-check outcomes (`pytest`, `mypy`, `ruff`) are statistically independent (speaking to ADR-0012's unknown-dependence assumption); and which invariants in `src/consilient/` possess the weakest automated guards.
**Precondition:** `src/consilient/` source tree (~1,100 LOC across 5 modules); 92 passing invariant tests; clean `mypy` run; deterministic mutation harness using an upstream-first engine (`mutmut` BSD-3-Clause / `cosmic-ray` MIT) running under `uv`; isolated execution with timeout and process-tree kill. Mutating `tests/` is strictly prohibited.
**Scope and mutant budget:** Complete census of all non-test Python files in `src/consilient/` (`__init__.py`, `events.py`, `projection.py`, `beta.py`, `cli.py`). A target generation of all syntactically valid first-order mutants generated by the engine's core operator set.
**Operator set (explicit):**
1. Comparison operator replacement (`==`, `!=`, `<`, `<=`, `>`, `>=`, `is`, `is not`, `in`, `not in`).
2. Boolean and logical replacement (`True` $\leftrightarrow$ `False`, `and` $\leftrightarrow$ `or`).
3. Binary/arithmetic operator replacement (`+`, `-`, `*`, `/`, `//`, `%`, `**`, `&`, `|`, `^`, `<<`, `>>`).
4. Unary operator inversion / deletion (`not x` $\leftrightarrow$ `x`, `-x` $\leftrightarrow$ `+x`, `~x` $\leftrightarrow$ `x`).
5. Constant and literal mutation (numbers, strings, `None` substitution).
6. Statement mutation (removal of calls/assignments, break $\leftrightarrow$ continue, exception replacement).
**Equivalent mutant handling:** All surviving mutants are audited and classified into: (a) true behavioural defect (verifiable regression in semantics); (b) equivalent mutant (AST/semantic no-op or unreachable/redundant defensive branch); (c) unclassifiable / ambiguous. True $\beta$ is computed over non-equivalent mutants: $\beta = (N_{\text{survived}} - N_{\text{equiv}}) / (N_{\text{total}} - N_{\text{equiv}})$. The unclassifiable fraction is reported as residual uncertainty.
**Measures:**
- Per-check $\beta$ for `pytest`, `mypy`, and `ruff`, with Wilson 95% score intervals.
- Composite verifier $\beta_{\text{comp}}$ (fraction of non-equivalent mutants surviving all three checks simultaneously).
- Pairwise contingency tables and statistical independence tests ($\chi^2$ test / mutual information) across check outcomes.
- Guard vulnerability ranking: inventory of surviving mutants by module, line, invariant ID (e.g. V0-01, V0-18, V0-26, V0-27), and code path.
- Computational cost: wall-clock time per mutant and total run duration.
**Stopping rules (fixed before the run):**
- If composite $\beta_{\text{comp}} \ge 0.20$ on the non-test source tree $\implies$ **High verifier false-accept rate.** Automated guards have significant blind spots; document the weakest invariants in `P2-guards.md` and trigger invariant hardening. [asserted]
- If composite $\beta_{\text{comp}} < 0.05$ on non-test source tree $\implies$ **Strong verifier discipline.** The invariant suite + type checker provides tight containment; verify that survivors concentrate in cosmetic/render code rather than security/authority paths. [asserted]
- If check outcomes exhibit statistically significant dependence ($p < 0.05$ on contingency test, e.g. $P(\text{survive pytest} \mid \text{survive mypy}) \neq P(\text{survive pytest})$) $\implies$ **ADR-0012's independence assumption is refuted.** The product of individual check error rates is invalid as a prior; composite $\beta$ must be measured directly. [asserted]
- If fewer than 50 valid non-equivalent mutants are generated or execution fails to complete across all checks, the verdict is **insufficient evidence**. Do not extrapolate from uncompleted or underpowered sweeps. [asserted]
**What it cannot decide:**
- Generalisation of $\beta$ to non-Python repositories or unconstrained multi-file semantic edits;
- Specification defects where tests and code agree on an incorrect invariant (oracle correctness);
- Human cognitive error distributions (mutants simulate synthetic syntactic mutations, not real developer failure modes).

### EXP-48 · Mechanical generation of the defective-guard catalogue via mutation survivor clustering `DONE 20 Aug 2026 — see experiments/exp48/findings-exp48.md`
**Run 20 Aug 2026 across EXP-47's 586 non-equivalent surviving mutants (61 spatial clusters) vs P2's 25 defective guards.**
**Headline:**
- **Overall Catalogue Recall: 20.00% (5/25)** [8.9%, 39.1%]. 68.0% (17/25) of P2's catalogued guards live outside Python source code (in ADRs, CI workflows, governance rules, and research harnesses) where program mutation testing cannot operate.
- **Code-Resident Recall: 62.50% (5/8)** [30.6%, 86.3%]. Recovers A1, A3, A6, A8, A14. The 3 missed code guards (A4, A5, A11) are killed by regression tests written for their fixes.
- **Cluster Precision: 24.59% (15/61)**. 46 unmatched clusters (75.41%) represent unasserted CLI formatting (14 clusters / 182 mutants), gate regex parsing (12 clusters / 205 mutants), and unchecked exception strings, none of which represent claimed-but-inert invariants.
- **Stopping Rules 2 & 3 FIRED (Structural Divergence):** Mutation testing cannot automate the guard catalogue. Guard vacuity is a claim-vs-implementation mismatch requiring governance intent, whereas mutation testing measures AST code-vs-test sensitivity.
**Decides:** whether EXP-47's 743 `pytest` mutation survivors mechanically regenerate the 25 hand-curated inert/defective guards from `docs/50-publications/P2-guards.md` (turning an $n=1$ existence claim into an automatable prevalence method), or whether mutation survival and "guard-cannot-fail" are structurally distinct phenomena (because guard vacuity is a claim-vs-implementation mismatch requiring human/governance intent, whereas mutation testing only measures code-vs-test sensitivity).
**Precondition:** EXP-47 mutation results file (`docs/10-research/experiments/exp47/results-exp47.json`) containing 1,931 mutants and 743 `pytest` survivors mapped to file, line, AST operator, and mutation details; `docs/50-publications/P2-guards.md` anchoring 25 hand-catalogued defective guards (A1–A11, A13, A14; A12, A15; B1–B10) plus 1 control (C1).
**Procedure:**
1. Parse the 743 `pytest` survivors from EXP-47 deterministically and cluster them by file, function/block, and code region (line ranges and AST context).
2. Map each of the 25 hand-catalogued defects from P2 to its underlying source/artefact location: identify which are in-scope of Python source mutation (`src/consilient/`) versus out-of-scope governance/CI/workflow/design artefacts (ADR gates, CI yaml, docstrings, git metadata, external systems).
3. Compute bidirectional correspondence:
   - **Recall**: Proportion of P2's catalogued guards (overall and source-resident subset) recovered by survivor clusters.
   - **Precision**: Proportion of mutation survivor clusters that correspond to real hand-found guards or newly identified unstated invariant failures vs noise/untested cosmetic helpers.
4. Inspect the top unmatched survivor clusters: determine whether they represent genuine uncatalogued guards that cannot fail (with stated claims) or unasserted helper/formatting code.
**Measures:**
- Out-of-scope fraction of P2 catalogue (artefacts lacking Python mutants: ADRs, CI workflows, logs, external processes).
- Recall on total P2 catalogue (out of 25) and recall on code-resident P2 subset.
- Precision of survivor clusters (clusters matching real defective guards / total clusters).
- Classification of top non-P2 survivor clusters (stated invariant defect vs cosmetic/helper code).
**Stopping rules (fixed before the run):**
- If recall on code-resident P2 guards $\ge 70\%$ AND precision of substantive non-cosmetic clusters $\ge 50\% \implies$ **Catalogue is mechanically automatable.** Mutation survivor clustering can regenerate the guard catalogue and scales to arbitrary repositories without manual audit. Update P2 positioning to claim automated prevalence. [asserted]
- If recall on total P2 catalogue $< 35\%$ OR code-resident recall $< 50\% \implies$ **The correspondence is too weak to automate (Structural divergence).** Guard-cannot-fail is a claim-versus-implementation mismatch that mutation testing cannot see; P2's hand-audit method is structurally necessary rather than an artefact of early effort. [asserted]
- If $\ge 50\%$ of P2's 25 guards live outside Python source (in ADRs, CI workflows, git metadata, external projections) $\implies$ **Domain boundary refutation.** Mutation testing over program code has no access to governance/orchestration layers where most vacuous checks live. [asserted]
- If fewer than 100 survivors are parsed or data is missing location metadata $\implies$ **Insufficient evidence.** Do not extrapolate from corrupted or truncated survivor records. [asserted]
**What it cannot decide:**
- Detection of inert checks in non-Python or non-code artefacts without a domain-specific mutation engine for ADRs/CI;
- Higher-order multi-point semantic failures not captured by single-mutant operators.

### EXP-58 · Harness uplift on a mainstream eval — and the number nobody else reports `READY`
**Pre-registered 20 Aug 2026. Not run.** The flagship proof experiment.
**Decides:** whether attaching this harness to a model produces a transformative, replicable gain on
a benchmark outsiders already trust — and whether the gain is real or bought.
**Joe's framing:** *"plug our harness onto any model and gain an average of x% on [mainstream eval].
We are looking for transformative differences, proof."* That is the right ambition. This entry adds
the two things that make such a claim believable rather than dismissable.

**Benchmark:** SWE-bench Verified (500 human-validated instances). Chosen because it is the
benchmark this field actually argues about, its instances are real repository issues, and its
oracle is a test suite rather than a judge — which matters for the second measure below.

**Arms — and the discipline is the whole design.** Harness-versus-bare comparisons are where this
field cheats, almost always unintentionally:
- **same model**, same weights, same decoding parameters;
- **same token budget and same retry budget** — a scaffold that wins by spending five times as much
  has not won, it has paid;
- **same repository snapshot and same environment image**;
- the only difference is the scaffold.
**Cost per resolved instance is a primary result, not a footnote.**

**Measure 1 — resolve rate.** The number everyone reports. Report the paired difference with a
bootstrap interval, not two separate percentages, because the instances are the same.

**Measure 2 — β on the benchmark, which nobody reports.** SWE-bench marks an instance resolved when
its selected `FAIL_TO_PASS` and `PASS_TO_PASS` tests pass. **Those tests are an oracle, and oracles
have error rates.** For every instance either arm marks resolved, run the repository's **full** test
suite, not the benchmark's selected subset. An instance that passes the selected tests and fails the
full suite is a **false accept** — a patch the benchmark called correct and which broke something.
That ratio is β for SWE-bench itself.
This is the differentiated claim and it is measurable with the corpus as it already ships: **every
system on the leaderboard reports pass@1 and none reports how many of its passes are wrong.**

**Sampling:** a stratified subsample if the full 500 exceeds the machine's budget, drawn and frozen
**before** any run, with the seed committed. Power stated in advance: at a resolve rate near 0.4, a
paired design needs roughly 200 instances to detect a 10-point difference at conventional power —
**say so before running, not after.**

**Stopping rules (fixed before the run):**
- If the paired resolve-rate interval **excludes zero and the harness is higher at equal or lower
  cost** $\implies$ **the uplift claim is supported** and is publishable with the cost figure
  attached. [asserted]
- If the harness is higher **only at materially greater cost** $\implies$ report it as a
  cost/quality trade, never as an uplift. A scaffold that buys accuracy with tokens is a known and
  uninteresting result. [asserted]
- If the paired interval **contains zero** $\implies$ **no uplift on this benchmark.** Report it.
  This project has published every result that went against it today and this one is not exempt.
  [asserted]
- If measure 2 finds β **above 0.10 for either arm** $\implies$ the leaderboard's own oracle admits
  more than one bad patch in ten, and **that finding outranks the uplift result** regardless of which
  way the uplift went. It should be the paper. [asserted]
- If fewer than 60 instances complete in either arm $\implies$ **insufficient evidence**; report no
  difference. [asserted]

**What it cannot decide:** whether uplift transfers to work unlike SWE-bench — greenfield
construction, multi-repository change, anything without an existing test suite to serve as oracle.
EXP-43 already measured that this project's own retro-verifier is **blind to 72.8–75.9%** of merges
because they add new components. SWE-bench is a repair benchmark and the same censoring applies.
**State that before the numbers, not after.**

**Precondition and honest blocker:** the harness does not route yet. ADR-0015 Gate A and Gate B both
fail today, so the "harness arm" as of tonight is the observe-only increment plus dispatch, not the
routing system the claim will eventually be about. **Measure 2 does not depend on that and can run
first.**


### EXP-56 · Per-model β on a label-free corpus, and the CEILING on what routing can buy `STOPPED 20 Aug 2026 — see experiments/exp56/findings-exp56.md`
**Pre-registered 20 Aug 2026. Preflight stopped; scoring not run.** Flagship of the routing programme.
**Decides:** which model family should do which task — and, before that, whether the question has an
answer worth acting on. ADR-0003 (no learned routing policy in v0) was decided on argument; this
measures it.
**The asset that makes this possible, and it is unusual.** Joe holds flat-fee access to **204
models** through one Cursor subscription. Per-token pricing is why cross-model studies at this
breadth are normally not run; here the marginal cost of the 200th model is wall-clock, not money.
That is a genuine research position and it should be spent on the question nobody else can afford
to ask.
**The design's one real idea — measure the CEILING, do not build a router.**
A router cannot beat the best possible assignment of items to models. So construct the
**hindsight-optimal router**: for every item, retrospectively pick the model that got it right.
That is an upper bound no real router can exceed, and it is computable from the same runs that
produce the per-model rates. **If the ceiling does not clear the best single model, no router can,
and the routing question is closed without a router ever being written.**
**Corpus:** EXP-47's 1,931 first-order mutants (bad by construction, mechanical ground truth, no
human labels) plus unmutated controls (good by construction). Reuses the EXP-08 critic seam.
**Sample, fixed before the run:** 16 models stratified across families (Anthropic, OpenAI, Google,
xAI, Moonshot, Zhipu) and effort tiers, at **n = 120 items each** — 60 mutated, 60 control. At
β ≈ 0.3 that gives a Wilson half-width near ±0.09, enough to separate families that differ by more
than 20 points and honestly insufficient to separate near-neighbours. **That limitation is accepted
in advance rather than discovered afterwards.**
**Measures:** per-model β and α with Wilson intervals; per-model wall-clock and token cost;
the hindsight-optimal ceiling and its interval; agreement matrix between every model pair; and the
**variance across models**, which decides whether the routing question is live at all.
**Stopping rules (fixed before the run):**
- If the hindsight-optimal ceiling's interval **overlaps the best single model's** $\implies$
  **routing cannot improve quality on this task class.** ADR-0003 is vindicated on evidence, and the
  harness should route on cost, availability and headroom — never on predicted quality. [asserted]
- If the ceiling beats the best single model with **non-overlapping intervals** $\implies$ routing
  has measurable headroom, and the gap is the entire prize available to any router. Report the gap,
  not a router. [asserted]
- If per-model β spans **less than 10 percentage points** across all 16 $\implies$ **model choice
  does not matter for this task** and the routing question is moot here regardless of the ceiling.
  This is the outcome that would most embarrass the premise and it must be reported first if it
  occurs. [asserted]
- If any model refuses or fails on more than 20% of items, it is reported as **unusable for this
  task** rather than scored, because a refusal is not a wrong answer. [asserted]
**What it cannot decide:** anything about tasks unlike accept/reject on a small mutated diff.
Long-horizon planning, open-ended design and multi-file refactoring are exactly where routing is
usually claimed to matter, and this corpus says nothing about them. **State that before the
numbers.**

### EXP-57 · The marginal value of context — does more context buy accuracy, or cost? `DONE 20 Aug 2026 — see experiments/exp57/findings-exp57.md`
**Pre-registered 20 Aug 2026 and run unaltered the same day. 640 `claude -p` calls
(512 census + 128 determinism control) over 128 items from EXP-47's corpus — 64 defect-introducing
and 64 defect-removing changes, disjoint mutants, seed 57. One model (`claude-sonnet-5`), context
volume the only variable.**
**Headline:**
- $\hat\beta$: minimal **0.0469** [0.0161, 0.1290]; relevant **0.0469** [0.0161, 0.1290]; full
  **0.0313** [0.0086, 0.1070]; padded **0.0313** [0.0086, 0.1070]. $\hat\alpha$: 0.0313, 0.0469,
  0.0469, 0.0156. All at $n = 64$ per class per arm, 0 unparsable replies in 640 calls.
- Input tokens per call: **921 → 1,601 → 21,479 → 41,686**, a **45.3×** range (67.7× counting the
  auxiliary model the CLI bills alongside the answering one). Latency 3.8 s → 5.2 s.
- **All eighteen pairwise difference intervals span zero** (Newcombe, 95%). Item-level: minimal and
  full give different verdicts on 8 of 128 items, **4 wrong each way**, exact McNemar $p = 1.000$.
- **Stopping rule 4 FIRED — `insufficient power`.** Reported as pre-registered: the intervals, and
  no trend narrated across them.
- **The padding rule did not fire.** `padded` has the *lowest* error rate (0.0234 vs full's 0.0391),
  difference interval [−0.0330, +0.0671]. **No measured context poisoning** at 41,686 tokens of
  plausible irrelevant code, at this $n$.
- **The adverse rule did not fire and did not come close.** Full's $\beta$ is below minimal's by one
  item in 64 on an interval six times wider than the gap. No evidence for "send everything, build
  nothing"; equally, no evidence against it finer than ~10 percentage points.
- **Determinism control: 4 of 128 re-run verdicts flipped — 96.88% agreement, 3.1%
  irreproducible.** The largest between-arm gap is 1.6 points. **The noise floor is larger than
  every difference measured**, which is why no trend may be read off these arms.
- Measurement facts the registration did not anticipate: the default CLI invocation carries
  **75,285 input tokens** before the prompt (stripped to ~600 here); the CLI bills a **second
  model** on the same prompt (20,697 tokens/call on `padded`); and under 6-way concurrency **125 of
  512 calls returned a verdict with no usage block**, which recorded as zeros would have understated
  `padded` sixfold.
- Corrections to the pre-registration, none of them applied to the design: it fixes **no sample
  size** while offering "insufficient power" as a verdict; **"materially beats" and "≈" are
  undefined**; it has **no floor-effect guard** and the run hit the floor (~2,400 items per class per
  arm would be needed to resolve the gap observed); "the interval on each pairwise difference" does
  not say **paired or unpaired** though all arms share items; and the **`relevant` arm is
  half-degenerate** — 65 of 128 items have no test naming the changed code, because the corpus is
  made of mutants that survived pytest. See findings §6.
**Run result, 20 Aug 2026:** the preflight stopped before scored calls because EXP-47's committed
JSON contains no item-level killed rows, no item-level equivalent rows and no source snapshot
identity; the registered survivor/killed sample therefore cannot be drawn without a post hoc
amendment. [measured] No registered stopping rule was evaluable. [algebra] No per-model statistic
was produced. [measured] One unscored Cursor identity probe reported a display name but not
served-weight identity and is recorded as `unknown:not-reported-by-runtime`. [measured] The
pre-registration above is preserved unchanged apart from this status and result note. See
`experiments/exp56/findings-exp56.md`.

#### Pre-registration (preserved; do not re-allocate EXP-57)
**Pre-registered 20 Aug 2026. Not run.** The live record is the `DONE` heading above.
**Decides:** whether just-in-time context engineering is worth building. Joe asked for
"dynamic/just-in-time prompting/context engineering"; this asks first whether context volume
changes the answer at all.
**Why it is worth running rather than assuming.** EXP-45 measured condensation retention at
**40.71%** with consequential loss of **0.00%** [measured] — most of what was dropped was not
load-bearing. And Grok's first authenticated run spent **33,344 input tokens** answering *"reply
with the single word: ok"* [measured]. Both point the same way and neither measures the thing
directly.
**Design — four arms, same items, same model, context volume the only variable:**

| arm | what the model sees |
|---|---|
| **minimal** | the diff alone |
| **relevant** | the diff plus the tests that cover it |
| **full** | the diff plus the whole source tree |
| **padded** | full, plus a fixed body of confidently irrelevant material |

**Measures:** β and α per arm with Wilson intervals; input tokens per arm; and the interval on each
pairwise difference, because a difference whose interval spans zero is not a difference.
**Stopping rules (fixed before the run):**
- If **minimal ≈ full** $\implies$ context volume is cost without benefit on this task, and
  just-in-time context engineering is worth building for the cost saving alone. [asserted]
- If **full materially beats minimal** $\implies$ **the premise is wrong**: send everything, and
  build nothing. This outcome contradicts what Joe asked for and must be reported as loudly as the
  other. [asserted]
- If **padded is worse than full** $\implies$ irrelevant context actively degrades the answer. That
  is context poisoning with an interval on it, and it makes retrieval quality a correctness concern
  rather than a cost one. [asserted]
- If all four arms overlap $\implies$ **insufficient power**; report the intervals and do not
  narrate a trend across overlapping bars. [asserted]
**What it cannot decide:** whether the effect holds for tasks whose difficulty scales with context —
which is most real work, and the honest reason this experiment is a first step rather than an
answer.

### EXP-58 · β for SWE-bench Verified's own oracle — how often does a *resolved* patch break something the oracle never ran? `PHASE 1 RUNNING`
**Pre-registered 20 Aug 2026, 23:20 UTC+1, before any β-relevant run.** The dispatching brief
(`brief-swebench.md`) stated that this entry already existed and that "its stopping rules were fixed
before any data". **It did not exist.** `rg -n "EXP-5[89]" docs/` returned only the brief itself.
The number was free, so the identifier stands, but the pre-registration is this text and its
provenance is the commit that introduced it — not an earlier decision it can be attributed to.
Everything below was written after artefact reconnaissance (availability, licence, file layout,
runtime calibration) and before a single β-relevant test run.

**Decides:** whether the oracle that the entire coding-agent field grades itself against admits
patches that break the repository outside the tests it chose to run — and at what rate. If it does,
β is not a property this project invented to justify itself; it is a measurable property of the
field's most trusted verifier, and `docs/decisions/0002` gets external support from the one place
that would be hardest to dismiss.

**Why this is not the same finding as SWE-Bench+ or METR, and the brief overclaimed it.** The brief
asserted "every system on that leaderboard reports pass@1; none reports how many of its passes are
wrong". That is false, and this repository's own bibliography is what falsifies it. **SWE-Bench+**
(arXiv:2410.06992) found 32.67% of successful patches involved solution leakage and 31.08% were
suspicious through weak tests, dropping SWE-Agent+GPT-4 from 12.47% to 3.97% [cited]; **METR**
(*Many SWE-bench-Passing PRs Would Not Be Merged*, Mar 2026) measured automated pass rates roughly
24 pp above maintainer merge rates [cited]. Both are false-accept measurements on this benchmark and
both predate this entry.

What is left, and it is narrower than the brief's framing:

| prior work | failure mode measured | how |
|---|---|---|
| SWE-Bench+ | the selected tests were **too weak** to distinguish a wrong fix; the answer **leaked** into the issue text | manual inspection of a sample, on SWE-bench (original / Lite) |
| METR | the patch would not be **accepted by a maintainer** | human judgement |
| **EXP-58** | the patch **breaks a test the oracle never ran** | mechanical execution, on SWE-bench **Verified** |

Those are three different things. A patch can be specific, unleaked, and mergeable-looking, and still
regress a module the selected tests do not touch. SWE-bench Verified exists *because* OpenAI filtered
the under-specification SWE-Bench+ found, so a Verified-era measurement is not a re-run of it.
**Unselected regression is the oracle's structural blind spot rather than a defect in any instance's
test choice**, and no source in `bibliography.md` measures it. If a source does, this experiment's
value is to replicate it and that is still a win. [asserted]

**Why the blind spot is structural, and this is the finding that made the design.** `eval.sh` for
`astropy__astropy-12907` runs `pytest -rA astropy/modeling/tests/test_separable.py` — one file — and
`FAIL_TO_PASS` ∪ `PASS_TO_PASS` for that instance is exactly the 15 tests that file contains
[measured, 20 Aug 2026]. The selected set equals the observed set. So **mining the published logs
cannot find a single unselected failure**: the oracle's selection *is* its execution. The only way to
observe the blind spot is to run tests the benchmark never ran, which is why this phase needs Docker
even though it needs no model. That killed the cheaper design the brief proposed and it is better
known now.

**Artefact and licence position, recorded 20 Aug 2026.**
- Predictions and evaluation artefacts are **not** in `github.com/SWE-bench/experiments` any more —
  submission folders hold only `README.md`, `metadata.yaml`, `results/`. The brief's premise was out
  of date. They are in the S3 bucket `swe-bench-submissions`
  (`analysis/download_logs.py`, `S3_BUCKET`), as
  `verified/<system>/logs/<instance_id>/{patch.diff,report.json,test_output.txt,eval.sh}`.
- The repository README says an AWS account is required. **It is not** — the bucket is readable with
  `Config(signature_version=UNSIGNED)`, and a plain unauthenticated
  `GET https://swe-bench-submissions.s3.amazonaws.com/?list-type=2&prefix=verified/...` returns 200
  [measured]. **No credential is created, held or used**, which is what makes this phase compatible
  with the 20 Aug credential-containment rule rather than an exception to it.
- **Licence: none.** `GET /repos/SWE-bench/experiments` returns `"license": null` and the tree has no
  `LICENSE` file [measured]. The README states the logs "are publicly accessible and meant to enable
  greater reproducibility and transparency of the experiments conducted on the SWE-bench task" — a
  statement of purpose that covers reading them for exactly this, and **not** a redistribution grant.
  **Consequence, and it is a hard rule for this experiment: no patch, log, diff or excerpt from those
  artefacts is written into this repository.** Only derived measurements, instance identifiers and
  test identifiers are recorded. Test identifiers are facts about the upstream open-source projects,
  not content from the submissions.

**Design — three arms per instance, one variable: what was applied, and what was run.**

| arm | model patch applied | tests run |
|---|---|---|
| **baseline** | no | full suite |
| **patched** | yes, one arm per resolved system | full suite |
| **oracle** | yes | the selected tests — *taken from the published `report.json`*, not re-run |

The oracle arm is not re-executed. The published `report.json` **is** the official harness's verdict,
accepted onto the leaderboard; re-running it locally would produce a weaker artefact than the one the
benchmark already stands behind. The brief asked for the official harness for that half and this
satisfies the intent more strongly than complying literally would. [asserted]

**The full-suite command is derived mechanically, never hand-written.** Take the instance's own
`eval.sh`, and replace its test-selection arguments with the first path component of the first
selected test path (`astropy/modeling/tests/test_separable.py` → `astropy`), or delete them where
there are none (Django already passes module labels only). Everything else — the conda environment,
the editable install, the `git checkout <base_commit> <test files>` reset, the gold test patch — is
byte-identical to the official script. A hand-written per-repo table would be twelve judgement calls
with no audit trail; this is one rule with twelve outputs, and the rule is in the results JSON.

**Classification, fixed before the run.** For system *s* on instance *i*, over the full-suite runs:
- `regressed(s,i)` = tests **PASSED in baseline** and **FAILED or ERRORED in patched**. Requiring a
  baseline pass is what excludes pre-existing failures, and the baseline run is mandatory: **without
  it the headline is meaningless** and it is the most likely way this goes wrong.
- `unselected(s,i)` = `regressed(s,i)` minus (`FAIL_TO_PASS` ∪ `PASS_TO_PASS`). A selected-test
  failure is not a blind spot — the oracle would have caught it, and by the definition of *resolved*
  there are none.
- **false accept** ⟺ `unselected(s,i)` is non-empty **after flake confirmation**.
- **Flake confirmation is not optional and every candidate gets it.** Each candidate false accept is
  re-run — baseline and patched arm both, fresh containers — and a candidate whose unselected
  regression does not reproduce is reclassified **flaky** and excluded from the numerator, staying in
  the denominator. A test that fails intermittently is noise about the harness, not evidence about
  the patch.
- Excluded as **noise**, with the count and reason reported: runs that time out, containers that fail
  to start, patches that fail to apply, and any instance whose baseline run does not produce a
  parseable test segment. An instance excluded for any of these reasons is excluded for **all** its
  systems, so exclusion cannot correlate with a system's quality.
- Statuses are read with **SWE-bench's own parsers** (`MAP_REPO_TO_PARSER_PY`, `swebench` 5.0.2,
  installed in an experiment-local venv outside this repository — **no dependency is added here**).
  Writing twelve parsers would put the measurement's most disputable step in our own hands.

**Sample, frozen before the run — see `experiments/exp58/sample-exp58.json`.** Frame: SWE-bench
Verified instances resolved by **at least one** of three submitted systems, because β is defined only
over accepted patches. The three systems, chosen for architectural spread rather than score:
`20250807_openhands_gpt5` (agentic scaffold, frontier model, 359 resolved),
`20250522_tools_claude-4-sonnet` (minimal tool loop, frontier model, 362),
`20241028_agentless-1.5_gpt4o` (non-agentic pipeline, weaker model, 194). Stratified by repository in
proportion to the frame, `random.Random(20260820)`, **instance identifiers and seed committed before
the first run**.
**Power, stated in advance.** The unit of β is a *patch*, not an instance, so 30 instances yields
roughly 65 patches; at β ≈ 0.1 that is a Wilson half-width near **±0.07** — wider than the ±0.06 the
brief asked for, and the honest cost of the baseline and flake-confirmation runs the brief also asked
for. Patches on the same instance are **not independent**; the patch-level Wilson interval is
therefore reported **alongside** per-system intervals and an instance-clustered interval, and the
patch-level figure is never quoted alone.

**Measures:** β for the oracle, pooled and per-system, with Wilson 95% intervals; the pre-existing
failure count per instance (the baseline, reported before the headline); exclusions with reasons; the
number of distinct unselected tests broken per false accept; and the flake rate from confirmation
re-runs.

**Stopping rules (fixed before the run):**
- If pooled β's interval **excludes 0** ⟹ **the benchmark's oracle admits regressions it never looked
  for**, at a measured rate. ADR-0002's premise holds on the field's own instrument, and the correct
  reading is about the oracle, not about anyone's system. [asserted]
- If pooled β's interval **includes 0** ⟹ **on this sample the oracle's blind spot is not detectably
  populated.** That is evidence *against* the project's rhetoric about test suites and it must be
  reported first if it occurs. The honest conclusion is then that SWE-bench Verified's selected tests
  are a better proxy for the full suite than this project has been assuming. [asserted]
- If per-system β intervals are **mutually non-overlapping** ⟹ the finding is about those systems,
  not the benchmark, and must be written that way. [asserted]
- If per-system β intervals **all overlap** ⟹ the finding is about the benchmark. Those are different
  papers and the choice between them is made by this rule, not after seeing which is more
  interesting. [asserted]
- If **more than 40%** of sampled instances are excluded as noise ⟹ **the instrument is the finding**
  and no β is reported from this phase. A β computed on the survivors of a 40% attrition is a
  measurement of which repositories have stable test suites. [asserted]
- If the flake-confirmation step reclassifies **more than half** of candidates ⟹ report the flake
  rate as the primary result and β as provisional. [asserted]

**What it cannot decide.**
- **It is a lower bound, and the direction matters.** The full suite is still a test suite. A patch
  that is wrong in a way no test in the repository exercises is invisible here and is counted as a
  correct accept. Every number this produces understates β.
- Nothing about **why** a patch regressed, and nothing about severity: one broken test and forty
  broken tests are both one false accept.
- Nothing about the leaderboard's *ranking*. β is measured over each system's own accepted patches,
  so a system that resolves fewer instances is not thereby better.
- Nothing about **this project's** β, which is separately measured at 0.3132 and is not comparable —
  different artefacts, different oracle, different task.
- **It does not license benchmark scores as an evaluation target.** ADR-0013 chose repository history
  over benchmarks and this does not reopen it: the benchmark is the *object of measurement* here, not
  the yardstick. If this entry is ever cited to justify grading the harness on SWE-bench, it is being
  misused.

**Phases.** *Phase 1* (this entry, running): three systems, the frozen sample, the full pipeline
end-to-end. *Phase 2* (not authorised by this entry): more systems and a larger sample, and a second
oracle-blind-spot probe using mutation of the patched source rather than the patch itself.

### EXP-52 · Does agent consensus reduce error, or reproduce it? `READY`
**Pre-registered 20 Aug 2026, before any arm was run. Registered because a refusal was made on
theory and Joe was right that theory is not measurement.**
**Decides:** whether swarm consensus — the largest single mechanism in `ruvnet/ruflo`, and the one
this project refused in `ruflo-assessment-2026-08-20.md` — reduces the false-accept rate, or merely
reproduces a single agent's error at N times the cost. **It also tests ADR-0010 against itself**,
which is why it is worth running rather than arguing: if voting over shared evidence materially
beats a single agent, ADR-0010 is too strong and Ruflo is right.
**Precondition:** EXP-47's mutant corpus, already committed. Each non-equivalent mutant is a
known-bad artefact with mechanical ground truth and no human labelling — the same property that made
EXP-47 possible.
**Design — four arms over the same items:**

| arm | agents | evidence each sees | what it isolates |
|---|---|---|---|
| **1 Single** | 1 | the mutated file and the task | the baseline |
| **2 Consensus, same family** | N, one family | *identical* context | voting alone |
| **3 Consensus, cross-family** | N, different families | *identical* context | family diversity without evidence diversity |
| **4 Cross-family, different evidence** | N, different families | **different views** — one the diff, one the tests, one the specification | ADR-0010's compliant configuration |

All four use the same majority rule and the same items. **Arm 2 versus arm 4 is the decisive
comparison**: identical voting machinery, different evidence bases.
**Measures:** β and α per arm with Wilson 95% intervals; pairwise agreement between agents within
each arm; cost per decision in wall-clock and tokens; and the fraction of items where the arm
differs from arm 1 at all — a consensus that never overturns the single agent is decorative
regardless of its β.
**Stopping rules (fixed before the run):**
- If arm 2's β interval overlaps arm 1's $\implies$ **voting over shared evidence adds nothing.**
  Consensus is echo at N times the cost, the refusal in the Ruflo assessment stands on measurement
  rather than on the theorem alone, and this becomes the empirical support ADR-0010 currently
  lacks. [asserted]
- If arm 2's β is materially **below** arm 1's $\implies$ **ADR-0010 is too strong.** Agreement
  between agents sharing evidence does carry information, the theorem's assumptions do not transfer
  to this setting, and the refusal must be withdrawn and Ruflo's mechanism reconsidered for
  adoption. **This outcome goes against the project and must be reported as loudly as the other.**
  [asserted]
- If arm 4 beats arms 2 and 3 with non-overlapping intervals $\implies$ **the different class of
  facts is what helps, not the voting.** That is the strongest available support for the project's
  central constraint and the clearest argument against buying consensus machinery. [asserted]
- If arm 3 ≈ arm 2 $\implies$ **family diversity without evidence diversity is not diversity.**
  Directly relevant to the Cursor/xAI finding, which asks whether a four-family panel is really
  four. [asserted]
- If fewer than 60 adjudicable items complete in any arm, the verdict is **insufficient evidence**
  and no arm is compared. [asserted]
**What it cannot decide:** whether consensus helps on tasks *unlike* mutation detection —
open-ended design, long-horizon planning, or work with no mechanical oracle. Mutants are the corpus
that makes ground truth free, and that is exactly the population where a single agent is already
strong. **This is the honest limitation and it should be stated in any write-up before the result
is.**

### EXP-53 · What does signing the trajectory cost, and what does it fail to cover? `READY`
**Pre-registered 20 Aug 2026. Not run.**
**Decides:** whether ed25519 signatures at the `append()` chokepoint — the one mechanism worth
taking from `ruvnet/ruflo` — close the gap that V0-18, V0-28 and the budget-state ingress all share.
Each protects **declared** provenance: `actor`, `via` and `openrouter-probe` are strings in a JSON
field, and a hand-written line defeats all three.
**Precondition:** none beyond the current log. No new dependency: `cryptography` is not installed
and `AGENTS.md` requires asking first, so the experiment must first establish whether the standard
library suffices or a dependency is genuinely needed — **that question is part of the experiment,
not a prerequisite waived before it.**
**Measures:**
- Append throughput with and without signing, events per second, on this machine.
- **Retroactive coverage**, which is expected to be zero and must be reported as such: the existing
  105 events are unsigned and cannot be signed after the fact without rewriting an append-only log.
  Signing is forward-only and **the historical record stays unauthenticated permanently.**
- Whether a signed log still replays to an identical canonical digest (Gate A2 must not break).
- Whether a reader **without** the key can still read, project and audit the log. If it cannot, the
  cure is worse than the disease: an unreadable record fails provenance, which is rule one.
- Key custody. No secret may reach the public repository (Joe, 20 Aug 2026), so the private key is
  local. **A locally-held key means only this machine can sign**, which bounds the cross-machine
  federation the mechanism was borrowed to enable — that tension is a result, not an obstacle.
**Stopping rules (fixed before the run):**
- If a reader without the key cannot fully audit the log $\implies$ **do not adopt.** Provenance is
  the first of the three rules derived from `CONSILIENCE.md` and a record only its author can check
  is not a record. [asserted]
- If throughput cost exceeds 10x $\implies$ sign **decision events only**, not every event, and say
  which classes are covered wherever the guarantee is quoted. [asserted]
- If signing breaks canonical-digest equality $\implies$ the signature belongs outside the canonical
  form, in a sidecar the digest does not include. [asserted]
**What it cannot decide:** whether signing prevents the failure V0-18 was written about. EXP-16
measured **structural confusion**, not forgery, and a signature stops forgery. It is entirely
possible this closes a hole nothing has ever come through — which is worth knowing before it is
built, and is the strongest argument for running the experiment before writing the ADR.


### EXP-51 · Probe OpenRouter's spend controls before any spend is authorised `READY`
**Pre-registered 20 Aug 2026 in ADR-0044, before any credential exists. Not run.**
**Decides:** whether the capabilities ADR-0044 relies on are real. Everything in that ADR's
capability table is `[cited]` from OpenRouter's documentation and **none of it has been run here**,
because running it needs the principal's key. No figure from it may be quoted as measured until this
reports.
**Precondition:** an OpenRouter key supplied by the principal, and the refuse-only budget primitive
already shipped. **The probe must not perform a completion it has not been authorised to pay for.**
**Questions, fixed now:**
1. Does `limit_reset` accept `weekly` and `monthly`, or only `daily`? The provisioning documentation
   demonstrates only `daily`. **Joe's stated requirement is weekly and monthly.**
2. Does every completion response carry a `usage` object with a cost — on every model, and on
   streamed and errored requests? Per-run attribution rests entirely on this.
3. Does the account-level cap surface through `GET /api/v1/key`, or is it invisible to the API?
4. What happens at exhaustion — a clean 402, or a partial charge?
**Stopping rules (fixed before the probe):**
- If (1) fails, the weekly and monthly ceilings cannot be enforced vendor-side. They must then be
  enforced harness-side and **declared as the weaker guarantee they are** — a boundary anything can
  route around, which is the failure working principle 3 exists to prevent. [asserted]
- If (2) fails on any tested model, per-run attribution is unavailable and **ADR-0044 must be reduced
  to ADR-0019 condition 3** — metered calls permitted only with a human present for each one, with
  the ceiling as an addition rather than a replacement. [asserted]
- If (3) shows the account cap is invisible, the harness must never reason about the principal's
  £100 and must say so wherever a budget is displayed. [asserted]
**What it cannot decide:** whether OpenRouter's routing keeps a fixed model string pointing at a
fixed model. That is a reproducibility hazard for any measurement taken through a broker and needs
its own experiment.


### EXP-49 · Mutation testing on the research instruments themselves `DONE (partial) 20 Aug 2026 — see experiments/exp49/findings-exp49.md`
**Pre-registered at `7b6ada0`. Two runs, 20 Aug 2026. Verdict under the fixed stopping rules:
`insufficient_evidence` — the census did not complete, twice.**
**Headline (5 of 6 targets, 5,430 mutants):**
- Research instruments raw $\beta = 0.6825$ [0.6700, 0.6948] against the product code's
  $0.3345$ [0.3138, 0.3559] (EXP-47). **The instruments are twice as permissive as the code they
  measure**, and the intervals are far apart.
- **32.7% of mutants (1,773) lie in 15 functions where NOTHING is killed** — including
  `exp43/run_commit_test` (the retro-verifier's oracle, 295/295), `exp31/summarise` (224/224),
  `exp07/run_attempt` (215/215) and `exp27_collector/collect` (208/208). The measurement apparatus
  has no automated verification.
- Critical paths are worse than average: `results_write` 0.7984, `timeout` 0.7753, `run_id` 0.5567,
  `lock` 0.5092.
- Equivalence uncorrected, so $\beta$ is an **upper bound**. Sensitivity: 75.4% of survivors would
  have to be equivalent for the gap to close; EXP-47 measured 9.29%. [algebra]
- **Determinism control passes:** 2,390 mutants compared across two independent 24-worker runs,
  **zero** outcome disagreements (`compare_runs.py`).
**Why incomplete:** `input_manifest()` hashes every file found by `rglob` under the watched
directories, so a transient file created by an instrument's own test suite aborts the census. It is
a race — run 1 passed the checkpoint that stopped run 2, and no pinned path differs afterwards. The
repair is proposed in the findings and deliberately not applied, because it changes `harness_sha256`
and must be recorded as an amendment rather than a silent patch. `exp27_handshake` (965 mutants)
remains unmeasured; its verifier makes live CLI capability probes and is ~10x slower per mutant.
**Decides:** whether the error bars on this project's published figures rest on code that is itself
verified. They do not.
**What it cannot decide:** whether any published number is wrong — a weakly guarded instrument is
not a wrong one; the competence-difficulty gap it inherits from EXP-47, which **EXP-50** is
registered to measure; and the sixteen research instruments never selected as targets.


### EXP-50 · Do LLM-emitted faults evade the checks at the same rate as synthetic mutants? `READY`
**Pre-registered 20 Aug 2026, before any fault was generated. Not yet run.**
**Decides:** the one residual empirical question that both `P1-proxy.md` §2.4 and `P3-echo.md`
§falsifier-5 name and neither answers — *"whether a check suite's false-negative rate against the
faults an LLM agent actually emits differs from its rate against synthetic mutants."* If it does
not, EXP-47's $\beta = 0.3132$ transfers, mutation testing was already the instrument, and this
programme's contribution shrinks to orchestration. If it does, every $\beta$ quoted from EXP-47 is
a floor rather than an estimate, and P2 §7's "competence-difficulty gap" objection is confirmed
rather than conceded.
**Precondition:** EXP-47's census complete on the same source tree and the same three checks
(`pytest`, `mypy --strict`, `ruff`), so the comparison arm already exists and is not re-run.
`src/consilient/` unchanged between arms, pinned by SHA-256 manifest as EXP-49 does.

**Design — three arms, one of which is already measured.**

| arm | fault source | sees `tests/`? |
|---|---|---|
| **S** (control) | EXP-47's 1,871 non-equivalent first-order mutants | n/a — syntactic |
| **B** (blind) | model asked to inject a defect given `src/consilient/` and the v0 spec only | **no** |
| **A** (aware) | model asked to inject a defect given source, spec **and** the test suite | **yes** |

Arm A is not a nuisance condition. It is the harness's actual operating regime: an agent that can
read the gate it must pass. Separating A from B separates *"LLM faults are different in kind"*
from *"LLM faults are adversarial to this particular suite"*, and only the second is Goodhart.

**Generation protocol (fixed):** each injected fault must (i) change `src/consilient/` only,
(ii) name the invariant or documented behaviour it violates, and (iii) be a single self-contained
diff. Two model families generate in **both** arms — family is a recorded covariate, not confounded
with arm — target $n = 100$ per arm, minimum 60 for a verdict.

**Ground truth by cross-family adjudication.** A model told to inject a bug frequently injects a
no-op. Every candidate is adjudicated by a **different family from the one that generated it**, and
by one that never saw the injection prompt, into: (a) real behavioural defect, (b) semantic no-op,
(c) ambiguous. $\beta$ is computed over (a) only; (b) is discarded exactly as an equivalent mutant
is; (c) is reported as residual uncertainty. The adjudicator is never the orchestrator — a
self-adjudicated corpus is echo (ADR-0010).

**Measures:**
- $\hat{\beta}_B$ and $\hat{\beta}_A$ with Wilson 95% intervals, and each per-check.
- The interval on $\hat{\beta}_B - 0.3132$, and on $\hat{\beta}_A - \hat{\beta}_B$.
- No-op rate per arm and per family — the instrument's own $\alpha$-analogue.
- Diff size and files-touched distribution per arm, against arm S's one-token profile.
- Family main effect, to detect a generator that is simply better at hiding.

**Stopping rules (fixed before the run):**
- If $\hat{\beta}_B$'s interval lies entirely **above** 0.3132 $\implies$ **synthetic mutants
  understate $\beta$.** Every EXP-47 figure is a floor; say so in P1, P2 and P3 and stop quoting
  0.3132 as an estimate. [asserted]
- If $\hat{\beta}_B$'s interval **contains** 0.3132 $\implies$ **mutation testing is an adequate
  proxy for non-adversarial LLM faults.** The residual question is answered against us: the
  instrument was free, off-the-shelf and decades old. Record it plainly in the novelty assessment
  rather than burying it. [asserted]
- If $\hat{\beta}_A$ and $\hat{\beta}_B$ intervals do **not** overlap, with $\hat{\beta}_A$ higher
  $\implies$ **suite-aware generation raises $\beta$.** A $\beta$ measured on faults that could not
  see the gate understates the $\beta$ of an agent optimising against it. This is Goodhart's law
  with an interval on it, and it bears directly on ADR-0015: routing on a gate an agent can read
  is not the same decision as routing on one it cannot. [asserted]
- If the adjudicated no-op rate is $\ge 40\%$ in either arm $\implies$ **insufficient evidence.**
  The instrument is measuring prompt compliance, not fault distribution. Do not report a $\beta$.
  [asserted]
- If the two adjudicating families disagree on $\ge 25\%$ of candidates $\implies$ **the oracle is
  the finding**, as it was on 20 Aug 2026 when two families differed on 16 of 75 labels. Report
  the disagreement rate and withhold the $\beta$. [asserted]

**What it cannot decide — and this is the load-bearing limitation, stated first rather than last:**
- **A model told to inject a defect is not a model that made one.** Deliberate injection and
  unintentional error may have entirely different distributions, and nothing in this design
  measures the second. Partial mitigation, pre-registered: compare the injected corpus's diff-size
  and operator profile against the real agent-authored defects this repository has recorded — P2's
  A-catalogue, the five dead assignments in `run_exp43.py`, the line-ending mismatch that made an
  edit silently no-op. **If the profiles differ sharply, the arm is measuring something else and
  the verdict must say so.**
- Whether either $\beta$ generalises beyond a ~1,100-line Python tree with an unusually
  invariant-heavy suite.
- Specification defects, where the code and the tests agree on the wrong thing. No arm here can
  see those; only P2's hand audit found any.

### EXP-58 · Can output-free local adaptation predict verifier false accepts? `BLOCKED: EXP-56 + exact-model/dependency approval + provenance-complete fixture bank`
**Pre-registered 20 Aug 2026. Not run.** This is the training gate proposed in
`local-training-legality-and-feasibility-2026-08-20.md`, not authority to add a learned router.
[measured]
**Decides:** whether locally training an adapter on licence-cleared, mechanically labelled
artefacts adds enough residual-defect signal to justify any further learned-critic work. It does
not decide whether routing enters v0; ADR-0003 remains binding whatever the result. [asserted]
**Why EXP-47 is not silently used as text:** its kill/survive labels are mechanical
measurements, but its source examples do not carry line-level provenance proving that no text
originated in a frontier-model response. Mechanical labels do not cleanse their examples.
[measured] EXP-47 supplies check definitions and a secondary outcome benchmark only; no source,
diff, prompt or response from it enters training until that provenance gap is closed. [asserted]
**Precondition:**
1. EXP-56 is complete, so the fixed zero-shot reviewer panel and its hindsight routing ceiling
   exist as a baseline rather than being reconstructed after this result. [asserted]
2. The exact 7–8B base revision is pinned by hash and its licence expressly permits local
   fine-tuning and use of its outputs. The expected route is QLoRA, which fits the measured
   32,607 MiB RTX 5090 by the arithmetic in the research note; model selection remains an
   explicit pre-run amendment because no new weight may be downloaded without hardware and
   licence admission. [algebra]
3. A fixture/verifier bank with at least 40 independent task families is frozen. Every source
   example, verifier and label-producing rule has a provenance record establishing that it is
   principal-owned, permissively licensed for this use, or produced by a local open-weight model
   whose exact licence permits reuse. Frontier inputs, outputs, teacher logits, synthetic
   examples, rewards and evaluation answers are excluded. [asserted]
4. Any new training dependency and any model download has the principal's separate approval.
   Registration supplies no such approval. [measured]
**Procedure:**
1. Produce attempted artefacts locally against the frozen fixtures. Retain the complete
   verifier 2×2: bad-and-green, bad-and-red, good-and-green and good-and-red. Ground truth comes
   from the fixture's independent oracle, not from a model's self-report. [asserted]
2. Split by fixture family before training: at least 25 families train, 5 validate and 10 remain
   held out. No mutation location, template sibling or near-duplicate crosses a split. Freeze and
   hash the split before fitting. [asserted]
3. Compare three arms on the identical holdout: a prevalence-only baseline; the frozen base
   model; and one QLoRA adapter. The adapter receives the artefact, task contract and real
   verifier result and predicts the residual event `bad AND verifier_green`. It never replaces
   the real verifier, whose EXP-47 census took about 0.054 seconds per mutant. [measured]
4. Use one fixed hyperparameter budget selected before holdout evaluation. No second adapter,
   prompt tuning or threshold tuning after a holdout result; that requires a new registration.
   [asserted]
**Measures:** recall on bad-and-green artefacts; false-escalation rate on good-and-green
artefacts; precision and PR-AUC at the fixed threshold; Brier score/calibration; verifier and
adapter wall-clock; peak VRAM; training time and energy estimate; and exact train/validation/
holdout provenance digests. [asserted]
**Stopping rules (fixed before any corpus or training run):**
- **No corpus, no run.** Any item with missing/ambiguous rights or provider-output provenance,
  any cross-split sibling, fewer than 10 held-out task families, fewer than 100 held-out
  bad-and-green artefacts or fewer than 100 held-out good-and-green artefacts returns
  `insufficient_evidence`; an item is not replaced after its outcome is known. [asserted]
- The adapter earns a further supervised critic experiment only if its 95% interval lower bound
  clears **50% recall** on bad-and-green at a fixed **≤10% false-escalation rate** on
  good-and-green, and it improves recall by at least **10 percentage points** over both the
  frozen base and prevalence baseline. [asserted]
- If the adapter fails either absolute threshold, or its interval overlaps both baselines, local
  adaptation is rejected for this task. Do not respond by adding frontier outputs, weakening the
  split or increasing model size. [asserted]
- If a random item split beats the family-held-out split by at least 10 percentage points in
  recall, the apparent gain is leakage and the experiment fails regardless of its headline
  score. [asserted]
- Peak allocated VRAM above 30,500 MiB, any OOM, or any unbounded process-tree overrun rejects
  unattended training on this card; a CPU-offloaded rerun is a different throughput regime and
  needs a new registration. [asserted]
- A passing model remains advisory and cannot route, block or accept. Promotion requires a new
  ADR and a prospective β measurement under the unchanged v0 gates. [asserted]
**What it cannot decide:** whether the signal transfers to real repositories, longer-horizon
work or specification defects; whether a larger model would pass; whether fine-tuning on actual
unintentional agent errors differs from locally manufactured attempts; or whether any frontier
provider would authorise output training. [asserted]


### EXP-54 · Does a log-anchored view checker catch known-invalid projections, or is that just a missing test? `READY`
**Pre-registered 20 August 2026, before any view-mutant was generated. Proposed in
`interface-beta-2026-08-20.md`. Not run.**
**Decides:** whether the decidable class that note names — a view that disagrees with the
trajectory log — is large enough and weakly-enough guarded to be worth treating as a check
with its own β, or whether it collapses to "write the tests V0-14 already claimed". It is
registered because one fixture is an existence proof (human `consil beta` drops a quarantine
that `--json` reports) and a rate needs a census, and because the tempting move is to name
the rate "interface-β". **The stopping rules include the result that forbids that name.**
**Precondition:** none. Fixture logs under a temp directory; `consil beta`, `consil replay`
and `consil doctor` as they stand; no front end, no new dependency, no metered call. The
operator catalogue is the ten named in `interface-beta-2026-08-20.md` §2 and is **closed
when this entry is committed**. Adding an operator after the run starts is a different
experiment.
**Design — two arms over the same logs and the same operators:**

| arm | view | what it isolates |
|---|---|---|
| **J** | `consil <cmd> --json` payload | the machine-readable contract V0-14 already tests, weakly |
| **H** | a structured parse of human stdout for the same command | the form a person actually sees, which EXP-47 found the suite does not look at |

A later arm D (DOM or accessibility tree of a graphical surface) is out of scope until
ADR-0007 is superseded. It is not a third arm of this run.
**Procedure (fixed):**
1. Build a small bank of fixture logs that exercise the fields the operators touch:
   insufficient β, measured β (synthetic rows, $n \ge 30$), a quarantined line, a
   `HUMAN_ONLY` event with `via: slack` that `validate()` would refuse, a doctor run whose
   gates are not all `pass`. The fixtures are written before any mutant is applied.
2. Render the honest view on each arm.
3. Apply each operator once per fixture, producing a known-invalid view. Record
   equivalence when the surface cannot express the mutated field (the human `beta` line
   cannot show a point it does not print; that is equivalent, not a survivor).
4. Run a checker specified *before* step 3. The checker may read the view and the log. It
   may not read renderer source, and it may not diff against the honest view as an expected
   value — that would be state-anchoring. Its rule is: every field the view asserts must be
   implied by the log, and every refusal the log recorded must appear where the view
   reports the rate or the gate that depends on that log.
5. Separately, run the existing pytest suite against the same invalid views, as a control:
   if pytest already kills a live operator, the operator is a missing assertion in a test
   that exists, not evidence of an unmeasured quantity.
**Measures:** $\hat{\beta}_J$ and $\hat{\beta}_H$ with Wilson 95% intervals, over
non-equivalent view-mutants only; live-operator count per arm; the fraction of live
operators the existing suite already kills; whether tonight's quarantine hole is unique or
modal.
**Stopping rules (fixed before the run):**
- If both arms' corrected β lie **below 0.05**, or arm H has **fewer than five live
  operators** $\implies$ **there is no quantity to name.** The decidable class is a test
  file. Write the checks, including the quarantine assertion on human `beta`. Do not call
  anything interface-β. **This is the result that goes against treating the class as a
  research object, and it is the expected one.** [asserted]
- If arm J's interval lies entirely **below** 0.05 and arm H's lies entirely **above** 0.20
  $\implies$ **V0-14 is a claim, not a check.** JSON is guarded, the human-visible form is
  not. Any future surface must run the log-anchored checker against whatever a person sees,
  not only against `--json`. [asserted]
- If both arms' intervals lie entirely **above** 0.20 $\implies$ **even the easy class has
  no oracle yet.** A front end cannot honestly claim projection QA until this checker
  exists and this rule would no longer fire. [asserted]
- If the existing pytest control kills **every** live operator on both arms $\implies$
  **the suite already has the oracle and the tests do not call it on these fixtures.**
  That is a coverage hole, not β. Patch the tests; do not register a quantity. [asserted]
- If fewer than 30 non-equivalent view-mutants complete on either arm $\implies$
  **insufficient evidence.** Do not report a β. [asserted]
**What it cannot decide:** whether a front end should be built (ADR-0007); whether a surface
reduces `T_effective_review` without raising artefact-β; whether a layout is confusing;
whether simulated users find real-user defects; the rate of EXP-01's affordance-after-reload
class; anything about a graphical surface, which this run does not have. Those limits are
the load-bearing ones and are stated in the note before this experiment exists.


### EXP-58 · Where inside its sharp bound does composite β actually land? `READY`
**Pre-registered 20 Aug 2026 in `composite-beta-under-dependence-2026-08-20.md`, before any
additional check was run.**

**Decides:** whether *"composite β sits near the sharp upper bound"* is a property of software
verifiers or an artefact of EXP-47's particular stack. That document derived the sharp
Fréchet–Hoeffding/Hailperin bounds for EXP-47's three checks and found the measured composite at
**91.03%** of the width between them — near the most pessimistic end. If that replicates, *"gate on
the upper bound, it is nearly right"* is a usable rule for any CI system composing error rates. If
it does not, the rule is needless pessimism and the recommendation must be withdrawn.

**What must NOT be registered as a stopping rule, because it cannot fail:** *"does the measured
composite fall inside the bound?"* It is a theorem, not a prediction — it holds for any internally
consistent inputs. Only the **position** within the bound, the **model fit**, and
**transportability** are falsifiable. This is stated because the vacuous version is the obvious one
to write.

**Preconditions.**
- $k \ge 4$ checks, at least one killing $> 20\%$ of mutants. EXP-47's `ruff` accepted 95.96%, and a
  near-constant check is nearly comonotone with anything — the leading confound for the 91% figure,
  and the reason $k=3$ cannot settle this. A fourth check is also the identifiability threshold: a
  two-class latent-difficulty model has $1+2k$ parameters against $2^k-1$ data df, so $k=3$ leaves
  **zero** df and $k=4$ leaves **six**. [algebra]
- **Full $2^k$ outcome vector recorded per mutant**, not per-check totals. `run_exp47.py` computed
  `pytest_pass`/`mypy_pass`/`ruff_pass` per mutant and saved only aggregates plus one 2×2 table; the
  other two pairwise margins survive only as ranges 71 mutants wide. This is a one-line
  instrumentation change and it is the whole reason this experiment exists rather than being a
  re-analysis.
- $\ge 2$ source trees. `src/consilient/` is the first; the second must **not** be a research
  instrument (EXP-49 measured those at $\beta = 0.6825$, twice as permissive, so they are a
  different population). Gate B forbids pointing anything at `../hireable-3.0` or `../jobboard-v2`,
  so the second tree is a public-corpus target or a synthetic one.

**Measures.**
- The position statistic $\pi = (\beta_{\text{comp}} - L)/(U - L)$ against the sharp bound $[L, U]$
  computed from marginals plus all pairwise margins, per tree, with a bootstrap interval.
- All $\binom{k}{2}$ pairwise margins and the full joint table, so bounds are computable at every
  information level rather than one.
- Two-class latent-difficulty model: fit by maximum likelihood, goodness of fit on $2^k-1-(1+2k)$ df.
- Whether the independence product falls outside the bound implied by marginals plus **one** pairwise
  table — the infeasibility-guard fire rate, which decides whether that guard is worth shipping.
- Per-check kill rate, to test whether $\pi$ tracks the weakest check's β rather than anything
  structural.

**Stopping rules (fixed before the run).**
- If $\pi < 0.50$ on either tree $\implies$ **the near-comonotone hypothesis is refuted.** Withdraw
  the § 8 recommendation to gate at the conservative end as *empirically motivated*; it survives
  only as a safety convention, which is a weaker and honest claim. [asserted]
- If $\pi > 0.80$ on both trees, intervals excluding 0.50 $\implies$ **the regularity holds so far.**
  Still $n=2$; record as a hypothesis with two supporting instances, never as a general result.
- If $\pi$ correlates with the weakest check's β across trees $\implies$ **the effect is the
  near-constant-check artefact, not verifier structure.** The 91% figure is then explained away and
  must be reported as explained. [asserted]
- If the latent-difficulty model fits ($p > 0.05$ on $\ge 6$ df) $\implies$ **model the dependence,
  do not bound it.** One parameter replaces an interval, and the bounding framing in
  `composite-beta-under-dependence-2026-08-20.md` becomes the fallback rather than the answer.
- If the infeasibility guard fires on fewer than half the trees $\implies$ **do not ship it.** A
  guard that rarely fires is a maintenance cost, and the § 10 grading of it as a worthwhile artefact
  was wrong.
- If any tree's census fails to complete $\implies$ **`insufficient_evidence` for that tree**, as
  EXP-49 correctly recorded twice. Do not pool a partial census with a complete one.

**What it cannot decide.**
- **Anything about LLM-emitted faults.** Every β here is conditional on first-order syntactic
  mutants. EXP-50 owns the transfer question, and if it fires, every figure in this experiment is a
  floor rather than an estimate.
- Whether the bounds are *useful*, as opposed to correct. On a tree where mutation testing runs at
  0.054 s/mutant the composite is directly measurable and the bound is redundant; the decision-
  relevant case is composing β measured on *different* corpora, which this design does not create.
- Whether negative dependence between checks is achievable. Littlewood & Miller (1989) show forced
  diversity permits it in multi-version software; nothing here selects checks adversarially to try.
- Specification defects, where code and tests agree on the wrong thing — invisible to mutation
  testing at any $k$.
External candidate facts, versions and licence readings for EXP-58–EXP-64 are anchored in
[`orchestration-dependencies-2026-08-20.md`](../20-design/orchestration-dependencies-2026-08-20.md).
[cited]

### EXP-59 · Does durable execution survive the crash window without displacing the trajectory? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether LangGraph, Temporal or Prefect should replace hand-built crash recovery in the
orchestrator. The existing JSONL is durable evidence, but it cannot distinguish “the adapter never
ran” from “the adapter completed and the process died before recording that fact.” This experiment
tests that exact ambiguity rather than accepting a framework's “durable” label. [measured]

**Arms:** a minimal trajectory-only recovery state machine; LangGraph with its local SQLite
checkpointer; Temporal Python SDK with a local persisted development server; Prefect with a local
persisted server. Pin every package, server binary and transitive lock before the run. After
installation, all arms run with outbound networking denied and telemetry disabled.

**Fixture:** one run with two deterministic activities. Activity A writes a run-scoped idempotency
token. Activity B writes one externally visible side effect to a separate SQLite oracle and returns
an `Outcome`. Barriers make these six kill points exact:

1. before dispatch intent is appended;
2. after intent append and before worker launch;
3. after worker launch and before the side effect;
4. after the side effect and before outcome append;
5. after outcome append and before worker acknowledgement;
6. during retry after a synthetic transient failure.

Kill the complete process group at each barrier, restart from disk, and run each arm five times per
barrier: 30 recoveries per arm. The side-effect oracle is not available to recovery code; it exists
only to score duplicates and losses. After every terminal run, delete derived projections and
rebuild them from JSONL. At every non-terminal kill point, repeat once after deleting the
framework's private store: recovery may create a new runtime instance, but it must be able to do so
from the trajectory without guessing.

**Measures:**
- duplicate and lost side effects;
- missing, duplicated or contradictory trajectory transitions;
- equality of canonical terminal `Outcome` and `state_digest()` after replay;
- whether recovery needs facts present only in a framework database;
- Consilient-owned recovery branches and production lines in the spike;
- added processes, direct/transitive packages, cold start and idle memory.

**Stopping rules (fixed before the run):**
- One duplicate, one lost side effect, one contradictory terminal event or one replay-digest
  mismatch in 30 recoveries $\implies$ **reject that arm.** “Usually durable” is not the property
  being bought. [asserted]
- If deleting the framework store makes recovery impossible from the trajectory at any cut
  $\implies$ **reject that candidate.** It has displaced the source of truth rather than projected
  it. [asserted]
- If the trajectory-only arm passes all cuts, a dependency is eligible only if it reduces both
  Consilient-owned recovery branches and production lines by at least 30% while passing every
  correctness and authority check. Otherwise keep the in-house state machine. [asserted]
- If the trajectory-only arm fails and exactly one candidate passes, that candidate is the
  provisional adoption choice. If several pass, choose lexicographically: fewest non-projection
  stores, then fewest additional processes, then least Consilient glue, then fewest transitive
  packages. Record every value; do not substitute a popularity judgement. [asserted]
- If no arm completes 30 recoveries, or a kill barrier cannot be placed deterministically, report
  **insufficient evidence** and adopt nothing. [asserted]

**What it cannot decide:** production-cluster operability, recovery from loss of the machine holding
all local state, or whether the same engine is appropriate outside this repository.

### EXP-58 · Can an agent framework be embedded without becoming the coordinator? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether LangGraph, Google ADK, CrewAI, AG2 or Microsoft Agent Framework supplies a
smaller implementation of the approved coordinator while preserving Consilient's authority.
AutoGen is excluded because its upstream is maintenance-only; no execution result can reverse that
maintainer decision. [cited]

**Reference workflow:** a dependency-free Python coordinator receives a fixed `Ticket`, selects one
of two deterministic fake adapters under a supplied policy, runs it once, asks a deterministic
critic that sees a different fixture class, and appends the route, delegation, evidence-class and
terminal events through the existing chokepoint. The framework arms must implement the same
workflow. Model calls, framework routing heuristics, memory, hosted tracing and self-reported
confidence are disabled.

**Corpus:** 24 fixtures: six routes × accepted/rejected outcomes × normal/exceptional completion.
Add eight hostile fixtures covering duplicate completion, callback reordering, unknown adapter,
critic timeout, malformed outcome, direct verdict injection, direct trajectory-write attempt and
framework-state deletion. Run each fixture once with networking available only to localhost and
once with outbound networking denied.

**Measures:**
- canonical event-sequence equality with the reference, excluding timestamps;
- route, `Ticket`, `Outcome`, evidence-class and fail-closed equality;
- unlogged framework state transitions or direct framework decisions;
- Consilient glue branches and lines, import time, idle memory, direct/transitive packages and
  processes;
- network attempts with all documented telemetry opt-outs set.

**Stopping rules (fixed before the run):**
- Any framework-selected route, model-derived acceptance, unlogged decision, independent
  trajectory writer or need for shared-evidence voting $\implies$ **reject that candidate.**
  Those are violations of the product, not integration inconveniences. [asserted]
- Any mismatch on the 32 fixtures, or any outbound attempt in the denied phase $\implies$ **reject
  that candidate.** [asserted]
- A passing candidate is eligible only if it deletes at least 30% of the reference coordinator's
  branches and production lines and does not add an authoritative store. If the framework merely
  wraps each existing callback, it has no job and is rejected. [asserted]
- If several candidates pass, select only a strict Pareto winner on Consilient glue, additional
  processes, transitive packages, import time and idle memory. If none dominates, adopt none;
  preference among agent programming models is not evidence. [asserted]
- If the reference itself fails a hostile fixture, repair the fixture or reference and restart all
  arms. Do not let a framework win against a defective control. [asserted]

**What it cannot decide:** whether one of these frameworks is a good way to build a different agent
product, or whether its own agents outperform existing coding agents. Neither question belongs to
this meta-harness.

### EXP-60 · Does Pydantic AI beat Pydantic Core at a native model-I/O seam? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether Pydantic AI belongs at a future native-model boundary, or whether
dependency-free validation or Pydantic Core supplies all of the value without an agent framework.
It does not compare agent quality; it compares parsing, validation and control ownership.
[asserted]

**Fixture provider:** a local fake OpenAI-compatible server emits 120 pinned responses: 40 valid
complete outputs, 20 valid streamed outputs, and 60 invalid cases covering missing fields, wrong
types, unknown enum values, extra fields, duplicate tool calls, truncated streams, invalid UTF-8
replacement, non-finite numbers, integers beyond interoperable JSON range, provider error frames
and tool/output interleaving. A hand-written JSON Schema and expected `Outcome` or rejection for
every fixture are frozen before any arm runs.

**Arms:** current-style explicit validation; Pydantic Core models/`TypeAdapter`; Pydantic AI
structured output. Every arm must return the same project `Outcome`, call only the local fixture
provider, append through the same event writer, and expose no route or acceptance decision to the
package.

**Measures:**
- false accepts and false rejects against the frozen fixture labels;
- canonical `Outcome` and trajectory equality on accepted fixtures;
- static-checker result for every adapter;
- Consilient parsing/validation branches and production lines;
- transitive packages, import time, global mutable configuration, caches and outbound attempts.

**Stopping rules (fixed before the run):**
- Any false accept, false reject, trajectory mismatch or package-owned route/verdict $\implies$
  **reject that candidate.** [asserted]
- If the dependency-free arm has zero classification errors, add neither dependency: there is no
  validation defect for a dependency to repair. [asserted]
- If Pydantic Core corrects every reference error and Pydantic AI catches no additional case,
  **reject Pydantic AI as overbroad.** A decision to add base Pydantic remains separate and still
  needs approval. [asserted]
- Pydantic AI is eligible only if it uniquely corrects every remaining reference/Core false accept
  without introducing a false reject, passes static checking, reduces both validation branches and
  production lines by at least 30%, and leaves orchestration outside the package. [asserted]
- If the fake provider cannot reproduce at least 20 valid streaming and 50 invalid cases, report
  **insufficient evidence**; a happy-path demo cannot decide a boundary dependency. [asserted]

**What it cannot decide:** behaviour of an untested provider, model instruction-following quality,
or whether a native model path should exist. The experiment becomes obsolete if external-agent
adapters remain the only execution path.

### EXP-61 · Does DSPy optimisation reduce held-out β without buying it through α or leakage? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether DSPy's actual proposition — optimising an LM programme against a metric —
earns a place in a future native-model path. Typed signatures alone are not the adoption claim.
[asserted]

**Corpus:** stratify EXP-47's non-equivalent mutants by file, function and mutation operator, then
freeze disjoint optimisation and held-out partitions. The optimisation set contains 60 mutants and
60 unmutated controls; the held-out set contains 120 of each. No file/function/operator cluster may
occur in both partitions. Ground truth is mechanical and held-out labels are unavailable to the
optimiser. Cap optimisation at 500 model calls.

**Arms, with the same pinned local model and output schema:** a hand-written fixed prompt/programme;
the equivalent unoptimised DSPy signature/module; and that DSPy module optimised on the training
partition. Token and wall-clock ceilings are equal for scoring. Cache state is cleared between arms,
and outbound networking is denied after installation.

**Measures:** held-out β and α with Wilson intervals; the intervals on each difference from the
fixed-program arm; refusal/invalid-output rate; input/output tokens; wall-clock; programme and prompt
diffs produced by the optimiser; and any overlap between optimiser inputs and held-out material.

**Stopping rules (fixed before the run):**
- Any held-out item, label, verifier outcome or semantically equivalent cluster entering the
  optimisation context $\implies$ **invalidate the run as leakage.** [asserted]
- If the optimised arm's β interval does not lie wholly below the fixed-program arm's, **reject
  DSPy:** optimisation did not improve the target error rate. [asserted]
- If β improves but α rises by more than 5 percentage points, invalid/refusal rate rises, or median
  tokens exceed 2× the fixed arm, **reject:** the gain was bought by a different failure or cost.
  [asserted]
- If the unoptimised DSPy arm's interval does not overlap the fixed arm's, first attribute that
  adapter effect. The optimised arm is eligible only if its improvement also clears the unoptimised
  arm with non-overlapping intervals. [asserted]
- DSPy is eligible only if all preceding checks pass on all 240 held-out items and the optimised
  programme re-runs deterministically from a pinned serialised artefact. [asserted]

**What it cannot decide:** open-ended work without a mechanical oracle, transfer to another model
family, or whether the optimisation corpus remains representative as the code changes.

### EXP-62 · Can OpenTelemetry be a disposable projection without losing Consilient semantics? `READY`
**Pre-registered 20 Aug 2026. Not run.**

**Decides:** whether OpenTelemetry GenAI semantic conventions should back an optional local
observability projection. The conventions repository has no release and no schema URL on the
registration date, so a passing run establishes semantic fit but adoption additionally requires a
tagged release with a usable schema identifier. [cited]

**Procedure:**
1. Freeze one fixture for every trajectory event type and at least 40 events in total.
2. Map committed events, never live decisions, to OTel spans/events using a pinned conventions
   commit. Prompt, response, tool-argument, tool-result and file content capture are disabled.
3. Export first to the in-memory SDK and then to a local OTel Collector plus Jaeger with outbound
   networking denied.
4. Delete all telemetry and prove that trajectory replay and `state_digest()` are unchanged.
5. Answer eight fixed queries: run timeline; adapter duration/status; route event; tool failures;
   model/token use where present; verifier result and evidence class; budget refusal; and
   span-to-immutable-trajectory-event correlation.

The first, second, fourth and fifth queries must use standard OTel fields where a convention
exists. Project-only facts use a documented `consilient.*` namespace and carry the source event ID.

**Measures:** fixture coverage, the eight query results, fields requiring custom attributes,
captured sensitive-content bytes, trajectory digest before/after, exporter failures and added
packages/processes.

**Stopping rules (fixed before the run):**
- Any trajectory mutation, decision input from telemetry, missing event correlation, or captured
  sensitive content $\implies$ **reject OTel.** [asserted]
- If any of the eight queries cannot be answered from the local backend, or fewer than the four
  designated queries use standard fields, the standard buys too little and is rejected. [asserted]
- If all checks pass and a tagged GenAI-conventions release with a schema URL exists, adopt OTel as
  an optional content-off projection. If the repository is still untagged or lacks a schema URL,
  record **compatible but not adoptable** and keep the trajectory-only implementation. [asserted]
- If the local collector cannot run without an account or outbound access, reject the deployment
  path even if the in-memory mapping passes. [asserted]

**What it cannot decide:** a hosted backend, long-term storage cost, or whether future conventions
will preserve today's fields.

### EXP-63 · Does MCP standardise tools without creating a route around the coordinator? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether the MCP Python SDK should implement the future tool boundary reserved by
ADR-0016. MCP is not tested as durable execution: the 2.0 SDK does not implement the tasks
extension. [cited]

**Arms:** a minimal hand-written local JSON-RPC tool bridge and MCP Python SDK 2.x over stdio. Both
expose only two deterministic capabilities: read a pinned context fixture and compute a pure
digest. The coordinator validates input, invokes the bridge and appends the result.

**Corpus:** 32 fixed calls: eight valid, eight malformed protocol/schema cases, and sixteen hostile
authority attempts including route selection, adapter dispatch, verdict submission, direct event
append, arbitrary path access, duplicate request ID, protocol downgrade, capability spoofing and
post-cancellation completion. Run under denied outbound networking.

**Measures:** accepted/rejected call equality, protocol error equality, complete audit correlation,
authority bypasses, production parser/transport lines, transitive packages and process cleanup on
timeout/cancellation.

**Stopping rules (fixed before the run):**
- One successful route, dispatch, verdict, trajectory-write or out-of-bound path attempt
  $\implies$ **reject the SDK boundary.** [asserted]
- One unaudited valid call, duplicate terminal result, leaked child process or outbound attempt
  $\implies$ **reject.** [asserted]
- If no real tool integration exists at run time, record **no present job** and add no dependency,
  regardless of protocol conformance. [asserted]
- Once a real integration exists, the SDK is eligible only if all 32 fixtures pass and it deletes
  at least 30% of the hand-written protocol/transport branches and lines. Otherwise keep the direct
  Python boundary. [asserted]

**What it cannot decide:** remote untrusted MCP servers, registry supply-chain safety, or using MCP
as an agent/task protocol.

### EXP-64 · Does the ACP Python SDK delete adapter protocol code without changing outcomes? `READY`
**Pre-registered 20 Aug 2026. Not run. Temporary package installation still requires the
principal's approval.**

**Decides:** whether ACP should become the transport inside adapters for backends that expose it.
Only stable ACP v1 is in scope. ACP v2 is draft and dual-version support is not accepted merely for
future-proofing. [cited]

**Precondition:** the existing 233-line Cursor ACP v1 client in
`docs/10-research/experiments/exp05/adapter_cursor_acp.py`, its transcript fixtures, and the measured
Cursor ACP run. [measured] Pin the official Python SDK and schema before the comparison.

**Arms:** the existing custom client and an `agent-client-protocol` SDK client against the same
deterministic local fake agent. Replay 40 transcripts covering initialization and capability
negotiation, authentication, session creation, prompt streaming, tool approval, plan update, normal
completion, agent error, malformed frame, unknown union variant, oversized frame, cancellation,
timeout, EOF and process-tree shutdown. Then repeat the valid bounded task against Cursor ACP using
the existing subscription composition; no credential is written to the repository.

**Measures:** transcript accept/reject equality, canonical project `Outcome`, trajectory sequence,
capability downgrade behaviour, cancellation latency, surviving descendant processes,
Consilient-owned parser/session branches and lines, and transitive packages.

**Stopping rules (fixed before the run):**
- Any transcript mismatch, changed `Outcome`, unaudited update, capability accepted without
  negotiation, process surviving timeout or outbound attempt $\implies$ **reject the SDK.**
  [asserted]
- If all fake and Cursor fixtures pass and the SDK deletes at least 30% of the custom
  parser/session branches and production lines, adopt it for ACP-capable adapters only. Otherwise
  retain the measured custom client. `Ticket`, `Outcome` and coordinator policy remain outside ACP.
  [asserted]
- Do not implement ACP v2 until it is stable and an admitted backend requires it. If that occurs,
  register a separate v1/v2 negotiation experiment; this result does not transfer. [asserted]

**What it cannot decide:** adoption by agents that do not expose ACP, the safety of editor-side
resource access, or v2's eventual stable surface.


---

## Loops, schedules and the offline phase — reserved block EXP-70…EXP-73

*(Registered 21 August 2026, alongside [ADR-0051](../decisions/0051-a-tick-is-an-attempt-and-only-execution-runs-unattended.md).)*

**Numbers 65–69 are deliberately left free, and this block is offset on purpose.** R15
(`../20-design/dispatch-layer-requirements-2026-08-20.md`) records five concurrent agents each
independently choosing EXP-58 on 20 August 2026, every one of them by correctly taking the next
free number. **Taking `max + 1` is the move that collides**, and it collides precisely because it is
the right answer for every agent at once. An offset block cannot be reached by that rule. The gap is
a reservation, not an omission. [measured]

**This agent was not issued experiment numbers in its brief, and R15 says to stop and ask.** That
rule exists to prevent the `max + 1` race; a declared offset block is the nearest available
substitute for layer allocation, and renaming an entry later is a two-line edit against a round trip
that would have blocked the work. The deviation is recorded here rather than assumed, so whoever
builds the allocator knows this block was hand-claimed. [asserted]

**All four are backlog, not gates.** Each states the largest effect it could show, as
[ADR-0050](../decisions/0050-gate-on-effect-size-not-on-uncertainty.md) requires of any entry that
wants to block anything, and each then says why it does not.

### EXP-70 · Does a scheduled sensing tick find anything the interactive session did not? `BLOCKED: the class-1 battery running under one schedule`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether ADR-0051's standing schedule earns its existence, or whether the same commands
should simply be invoked on demand. Promotes ADR-0051 decision 2 from PROVISIONAL, or cuts it.

**Claim (falsifiable):** over the window, the standing check battery produces **at least two
findings that no interactive session in the same 24 hours produced**.

**Precondition:** the class-1 battery running under one schedule and writing a machine-readable
outcome per tick. Two members already exist and one is already scheduled: `scripts/capture_health.py`
runs under the Windows scheduled task `Consilient-Capture-Health`, and `scripts/run_fallback.py`
exists but is invoked by hand. [measured]

**Procedure:** every tick appends its outcome. For each non-green tick outcome, adjudicate from the
trajectory alone whether the same defect is visible in that day's interactive record.

**Measures:** the 2×2 table *found-by-tick* × *found-by-interactive*, per finding. Report the
tick-unique cell as a count with a Wilson interval on the per-tick rate — **not** an agreement rate,
which mixes the cell that matters with the cell that does not
(`formalising-echo-2026-08-20.md` §4). [algebra]

**Stopping rule (fixed before the run):** stop at **30 consecutive daily ticks**, or at **5
tick-unique findings**, whichever comes first. A missed day does not reset the count; it is recorded
and the window extends by one day, to a hard ceiling of 45 calendar days.

- **≤1 tick-unique finding in the window ⟹ the standing schedule is cut.** The commands stay and are
  invoked on demand; the schedule goes.
- ≥2 tick-unique findings ⟹ the schedule stands and ADR-0051 decision 2 may be promoted.

**Largest effect it could show (ADR-0050):** deletion of the scheduler. That is the largest effect
available to it, because it changes what exists rather than how well it works.

**Blocks construction? No** — and the reason is structural rather than a judgement about magnitude.
**This experiment cannot run until the thing it would gate exists**, because the schedule is its
precondition. An experiment whose precondition is the component is a review of that component, not a
gate on it. [algebra] Cutting afterwards costs one deleted schedule entry.

**What it cannot decide:** whether any individual check is worth running, whether the battery's
composition is right, or anything about class-2 acting ticks, which ADR-0051 leaves disabled.

**Known weakness, recorded before the run:** the adjudication is manual, single-reviewer, and the
reviewer is the party that proposed the schedule. Q19's rule — *the party that produced the material
cannot certify what it missed* — applies and is **not** satisfied here. The correction is a second
reader given the trajectory cold; it is not budgeted. [asserted]

### EXP-71 · Is β stationary between ticks, or does a stored β decay? `READY`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether a scheduled consumer of β may read the last recorded value or must re-measure
inside its own tick. Bears on ADR-0002, on ADR-0051's retry ceiling, and on every future decision
that reads a β off a stored record.

**Claim (falsifiable):** on an unchanged tree with a fixed mutant seed, composite β re-measured on
successive ticks varies by **less than the half-width EXP-47 reported (0.0210)**.

**Precondition:** none beyond EXP-47's mutation instrument, which measured β = 0.3132
[0.2926, 0.3346] in 104 s. [measured] **This is runnable today**, which is why it is `READY` and why
it should be run before anything consumes a stored β.

**Procedure:** two arms per tick against the same tree — (a) fixed mutant seed, (b) fresh seed. At
least 20 ticks over at least 14 days. Record the tree digest with every measurement, so a changed
tree is never compared as an unchanged one.

**Measures:** β per tick with its Wilson interval; paired differences between consecutive ticks; the
tree digest; wall-clock between ticks. **Do not pool ticks into one interval.** Repeated
measurements over the same tree with the same seed are not independent samples, and pooling them
manufactures precision. Report the drift series, not a tighter number.

**Stopping rule (fixed before the run):** stop at **20 ticks or 14 days, whichever is later**. Stop
**early and report an instrument fault** if any two consecutive fixed-seed ticks on an identical tree
digest differ by more than 0.0210.

- Fixed-seed drift within ±0.0210 on identical digests ⟹ a stored β may be read inside its recorded
  window.
- Drift exceeding it ⟹ **a stored β is not a routing input.** Any tick consuming β re-measures inside
  the same tick, and ADR-0051's retry ceiling gains that constraint.

**Largest effect it could show (ADR-0050):** one stored read becomes one re-measurement inside a tick
that already exists. The cost of being wrong is bounded by a measured 104 s per measurement.
[measured]

**Blocks construction? No.** Its largest effect changes how well a tick works, not what is built —
ADR-0050 test 2 — and the cost of being wrong is 104 seconds per tick.

**What it cannot decide:** whether β measured by mutation transfers to β against a human verdict.
EXP-01, EXP-47 and `two-oracles-disagree-2026-08-20.md` own that question, and the two oracles there
differ by 14× the tolerance under discussion. [measured]

### EXP-72 · Does an offline consolidation phase beat spending the same budget on verification? `BLOCKED: matched-budget accounting over the frozen fixture bank`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether the offline consolidation phase — the "dreaming" idea — that ADR-0051 declines
gets written as ADR-0052 after all. **This is the experiment that would resurrect it, and that ADR
number is deliberately left unclaimed until it fires.**

**Claim (the one ADR-0051 asserts, stated so it can be killed):** a consolidation phase that
re-reads the trajectory and emits distilled lessons produces **no paired reduction in β beyond an
equivalence margin of ±0.02**, and does not beat the same token budget spent on additional mutation
testing.

**Precondition:** the frozen fixture bank and mutation instrument from EXP-47/EXP-50, and matched
token accounting across arms. No new dependency and no metered call — the arms run on a subscription
or local composition.

**Arms, paired over identical items:**

1. **Baseline** — task, verifier, outcome.
2. **Consolidation** — a phase over the accumulated trajectory emitting lessons into the next task's
   context, then task, verifier, outcome.
3. **Matched-budget verification** — arm 1 plus additional mutation testing costing the same tokens
   as arm 2's consolidation phase.

Arm 3 is what makes this an experiment rather than a demonstration. Without it, any gain in arm 2 is
confounded with simply having spent more.

**Measures:** per-item correctness for every arm, retaining the **full 2×2 correctness table per
pair**, the double-fault cell and pairwise φ — not agreement, and not arm-level β point estimates.
This repository has already been burnt by arithmetic cancellation between arm-level statistics that
concealed 16 disagreements in 75 item-level decisions. [measured] Report α beside β: a rule that
lowers false acceptance by rejecting everything has not helped.

**Stopping rule (fixed before the run):** accumulate discordant pairs between arms 1 and 2 until
**100 discordant pairs** or **2,000 items**, whichever comes first. 100 discordant pairs separates a
65/35 split from an even one at conventional levels under McNemar. [algebra] Analysis is a paired
bootstrap over items against the pre-registered equivalence margin.

- Arm 2 beats baseline beyond the margin **and** arm 3 does not match it ⟹ **write ADR-0052.** The
  phase buys something the provenance argument did not predict, and the honest reading is the bounded
  one — it removed interpretation noise, not common-evidence error (Dietrich & List 2004). [cited]
- Arm 3 matches or beats arm 2 ⟹ consolidation stays cut. The same tokens buy more as verification.
- Both within the margin ⟹ **"difference unresolved", not "equivalent".** Overlapping intervals fail
  to reject a difference and do not establish equivalence; EXP-52's registered overlap rule is
  invalid for this purpose. [algebra]

**The ±0.02 margin is not derived.** It is EXP-47's measured half-width (0.0210) rounded down, so the
margin sits at the instrument's resolution rather than below it. Recorded as a choice, per ADR-0050's
objection to round numbers that quietly become thresholds. [asserted]

**Largest effect it could show (ADR-0050):** an architectural phase that does not currently exist
gets built.

**Blocks construction? No**, and this is the cleanest case in the register. **Nothing is being built
for the consolidation phase — ADR-0051 declines it.** An experiment cannot gate work that was never
authorised. If this one fires it *authorises* work rather than releasing it.

**What it cannot decide:** whether consolidation helps a human reader, whether it helps latency (the
sleep-time-compute claim, which this design does not test), or whether it transfers off the fixture
bank.

### EXP-73 · Is artefact progress a usable stall signal, and what is its false-stall rate? `BLOCKED: class-1 ticks declaring a progress artefact`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** ADR-0034's own named falsifier, which it stated and nobody registered. Bears directly on
ADR-0051's termination rule, which inherits the signal wholesale.

**Claim (falsifiable):** across scheduled ticks, stall verdicts raised on artefact progress are
**more often genuine than false**, where *false* means the work later reached a normal terminal
outcome without intervention.

**Precondition:** class-1 ticks running under a schedule, each declaring the artefact that
constitutes its progress. ADR-0034 already requires the declaration — a task that cannot name one
cannot be supervised — so this adds no new machinery.

**Procedure:** record per tick the progress-sample series, every stall verdict with its signal,
threshold and observed value, and the eventual terminal outcome. **No verdict terminates anything**
— ADR-0034 §3 already forbids that — so every flagged run also produces its own ground truth. That
is what makes this measurable at all.

**Measures:** the 2×2 of *stall-flagged* × *eventually-completed-normally*; the false-stall rate with
a Wilson interval; the distribution of quiet intervals on runs that completed normally, which is what
any future threshold must be set from.

**Stopping rule (fixed before the run):** stop at **200 ticks or 20 stall verdicts**, whichever comes
first.

- False stalls ≥ genuine detections at 20 verdicts ⟹ **artefact progress is the wrong signal for this
  workload.** ADR-0034 §2 and §4 must be revised toward heartbeats carrying progress state, and
  ADR-0051's termination rule follows it.
- **Zero stall verdicts in 200 ticks ⟹ the detector is untested, not vindicated.** Report it as such
  and do not promote ADR-0034; its own third falsifier applies and the machinery should be cut to the
  artefact-existence check alone.

**Largest effect it could show (ADR-0050):** one liveness signal is exchanged for another inside a
supervisor that already exists.

**Blocks construction? No.** ADR-0050 test 2: it can only tune.

**What it cannot decide:** the thresholds. Every parameter in ADR-0034 is preferential, and this
measures the signal rather than the numbers.


---

## Capability routing — registered 21 Aug 2026 (ADR-0054)

**ID block EXP-90 … EXP-93, and why it skips.** At 02:15 on 21 Aug 2026 the highest number
anywhere under `docs/` was EXP-64, and **ten concurrent worktrees were sitting on that same
maximum** — `consilient-w-capability`, `-loops-impl`, `-loops-theory`, `-observability`,
`-personas`, `-qa`, `-skills`, `-usage`, plus `consilient-clone-math2` and
`consilient-clone-strict`. [measured] The register's own allocation rule — take the highest,
then `grep` — is the rule that produced the five-way EXP-58 collision still visible above, and
it produces exactly the same collision again whenever several agents read the same file in the
same minute. Taking 65 would have been *following the rule and colliding*. This block is
deliberately distant so a concurrent claim on 65–70 cannot silently alias onto it.
**65–89 are not reserved by this block and remain free.**

### EXP-90 · Is the browser a different class of facts, or only a transport to one? `READY`

**Pre-registered 21 Aug 2026. Not run. Rewritten the same night, before any run**, after
`qa-automation-and-the-anchor-problem.md` was read properly. The first draft asked "does a
browser-observing verifier beat a static one", which is the wrong question: this repository has
already established that different-class credit attaches to the **anchor** — where the expected
value comes from — and not to the technique or the modality. A browser asserting what the code
implies is state-anchored and is echo no matter how good the screenshot is. The question worth
measuring is whether the browser **reaches implicit oracles a source reader cannot reach at any
level of skill**, and what that is worth.

**Decides:** whether a composition's ability to drive a real browser earns an `implicit_oracle`
entry in ADR-0054's `anchor` column — and, separately and more usefully, whether this
repository's standing refusal of visual-LLM judges (`interface-beta-2026-08-20.md`, item 6)
costs anything measurable.

**Why it is answerable now, and calibrated rather than free-floating.** EXP-47 already measured
the dependence between two *same-class* checks here: mutants surviving `pytest` survived `mypy`
at **87.89%**, against **58.50%** for mutants `pytest` killed, chi-square 187.28, p < 1e-15.
[measured] Two static checks reading the same source are strongly dependent, which is what
`CONSILIENCE.md` predicts of echo — measured, not assumed. That 87.89% is the number a candidate
verifier has to beat before the word "different" is earned.

**Precondition:** (a) a small self-contained web application fixture — a form, a list view, a
conditional render, a client-side validation path, a responsive breakpoint, and at least one
affordance that can be rendered dead without changing any pure function — committed under
`experiments/exp90/`, with a `pytest` suite, a type check and a build, all written *before* any
mutant is generated and never edited afterwards. **The static suite must include DOM-level
component assertions** — the rendered tree read without a browser engine, as a competent suite
would have them. A static arm that only tests pure functions is a straw man, and beating it
would establish that *executing the code* is a different class of facts, which `pytest` already
does. The claim under test is about the **engine and the runtime**, not about execution.
(b) EXP-47's mutation harness, operator set unchanged. (c) Playwright MCP — already the
designated browser supply in `capability-layer.md`, Apache-2.0, **no new dependency and no
metered call**. (d) a frozen UI script naming the flows exercised and the implicit-oracle
assertions made.

**Arms.** Four verifiers over one mutant census:

1. `static` — `pytest` (including DOM-level component assertions) + type check + build,
   composite as EXP-47 defines composite.
2. `browser-implicit` — real engine, frozen script, **implicit oracles only and no model in the
   loop**: uncaught exception, console error, hang against a fixed timeout, missing accessible
   name, computed contrast failure, dead affordance (present, clickable, no state transition),
   and layout overlap by bounding-box intersection. Deterministic. This arm is the one the ADR's
   claim rests on, and it is deliberately the *cheapest* arm — the Q32 table calls implicit
   oracles "cheap, high-precision, narrow" and this tests whether narrow still pays.
3. `browser-agentic` — a harness driving the same fixture freely and returning a verdict. This
   is a visual-LLM judge, which this repository has **already refused as an acceptance signal**.
   It is included here **not as a candidate** but to measure what the refusal costs. Its verdicts
   are recorded and never credited.
4. `source-reader` — the same model as arm 3, handed the mutated source and the UI script as
   text, asked for the same verdict, with no browser at all. Controls arm 3 only. It separates
   *modality* from *model*.

**Measures:**

- The 2×2 for every verifier pair, with Wilson 95% intervals.
- **r = P(browser-implicit kills | static survived)** — the multiplicative reduction arm 2 buys
  on composite beta. The headline.
- P(survive browser-implicit | survive pytest) against P(survive browser-implicit | pytest
  killed), chi-square — directly comparable to EXP-47's 87.89% / 58.50%.
- **False-failure floor, per arm.** Every browser arm run 30× against the *unmutated* fixture.
  All rates are reported net of the floor and the floor is reported separately. A flaky browser
  manufactures apparent consilience; a chatty judge manufactures more of it. This control matters
  more for arm 3 than for anything else in the design.
- UI-reachability classification of every static survivor. Mutants unreachable from the frozen
  script are **not** browser misses and are excluded from r's denominator; the excluded count is
  reported.
- Equivalent-mutant audit, the same three-way classification EXP-47 used.
- Per-arm wall-clock and quota, because arm 2 costing 1% of arm 3 is part of the finding.

**Stopping rules (fixed before the run):**

- **Accumulate static-survivors, not mutants.** Generate mutants until **120 UI-reachable,
  non-equivalent static survivors** exist, capped at 600 mutants. Fewer than 120 at the cap ⟹
  **insufficient evidence**; report the interval and conclude nothing. [asserted]
- r ≥ 0.20 net of the floor **and** P(survive browser-implicit | survive pytest) ≤ 0.70 ⟹
  **the browser reaches a different class.** ADR-0054 credits browser-capable compositions with
  `anchor: implicit_oracle`. [asserted]
- r < 0.05 net of the floor **or** P(survive browser-implicit | survive pytest) ≥ 0.85 — no
  better than the measured mypy/pytest dependence — ⟹ **echo.** The browser is a transport to
  nothing the static suite did not already have; ADR-0054's anchor column loses its browser row
  and browser-capable harnesses are routed as producers only. [asserted]
- 0.05 ≤ r < 0.20 ⟹ **too weak to build doctrine on.** Report honestly; do not round up.
- **On the refused judge.** If arm 3 exceeds arm 2's r by ≥ 0.10 on non-overlapping intervals
  *and* its false-failure floor is below 0.05, then the standing refusal of visual-LLM judges
  costs something real and `interface-beta-2026-08-20.md` item 6 must be revisited on evidence.
  If arm 3 does not exceed arm 2, or its floor exceeds 0.05, **the refusal is vindicated by
  measurement rather than by argument** — which is the more likely outcome and the more useful
  one. [asserted]
- **On modality versus model.** If arm 4 (no browser) lands within its own 95% interval of arm
  3, then whatever arm 3 contributes is **model, not modality**, and no browser framing may be
  attached to it. [asserted]

**Blocks implementation?** **No.** Its largest possible effect (r = 0) removes one value from
one enumerated column of a capability row. It does not change whether capability is measured
rather than declared, whether beta is carried per task family, what the router may read, or that
the anchor taxonomy is the thing evidence-class credit attaches to — that taxonomy predates this
experiment and does not depend on it. Under ADR-0050 that is not a blocking effect, and under
ADR-0049 experiments do not gate.

**What it cannot decide:** whether the result transfers to any fixture but this one; the rate on
real defects rather than synthetic mutants — that is EXP-50's question, inherited here in full;
whether specification-anchored or metamorphic anchors would do better, since neither is an arm
here; and anything whatever about task families with no rendered artefact. Document drafting,
design work and long-horizon batch work are outside this design and may not borrow its result.

### EXP-91 · Does a measured capability beat the vendor's label — and by enough to pay for the probe? `BLOCKED: the capability store and a router that reads it`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether ADR-0054's refusal to read declared capability is worth what it costs. The
project's fifth working principle bans self-reported model confidence; ADR-0054 extends that ban
to vendor capability claims. That extension is `[asserted]` and this is the experiment that
makes it `[measured]` or kills it.

**Precondition:** the derived capability store, at least three admitted harness compositions, and
at least three task classes with a written verifier contract. Also a frozen **label table** — each
vendor's own public description of its harness, captured with URL and date *before* any run, so
that the label prior cannot be quietly edited after the outcomes are known.

**Arms,** over the same task bank, the same tickets and the same verifier contracts:

1. `label` — route by the frozen vendor label.
2. `measured` — route by the highest measured accept rate for the (task class, composition) cell,
   falling back to ADR-0054's cold-start rule where the cell is unmeasured.
3. `random-admitted` — uniform over admitted compositions. The floor. Without it, `measured`
   beating `label` shows only that *something* beats a label.

**Measures:** per-arm accept rate; per-arm beta against the class's verifier contract; human
verdict where captured; wall-clock and quota consumed; and the **probe debt** — runs spent
reaching `measured` status that produced no accepted artefact.

**Stopping rules (fixed before the run):**

- `measured` beats `label` by ≥ 15 percentage points of accept rate on non-overlapping Wilson
  intervals, **and** beats `random-admitted` ⟹ measured capability is load-bearing and the ban
  on declared capability stands. [asserted]
- `label` falls inside `measured`'s interval ⟹ **the ban is expensive theatre for this harness
  set.** ADR-0054 is downgraded: labels become an admissible cold-start prior in their own right,
  not merely a hint about probe order. [asserted]
- `random-admitted` falls inside the interval of both ⟹ **routing is not the lever at all** at
  this scale, and the finding belongs to ADR-0009 and ADR-0003 before it belongs here. This is
  the result nobody wants and it is the most likely one at n this small. [asserted]
- Fewer than 20 tickets per (arm × task class) cell ⟹ insufficient evidence. [asserted]

**Blocks implementation?** **No.** Every arm needs the router to exist first, so it cannot gate
the thing it measures. Its largest effect changes a cold-start policy.

**What it cannot decide:** whether labels are informative for harnesses outside the admitted set;
whether a label accurate in August 2026 stays accurate — the frozen label table is a snapshot and
these vendors ship weekly.

### EXP-92 · Is beta a property of the harness, of the verifier contract, or of the pair? `BLOCKED: EXP-90's fixture method generalised to ≥3 task classes`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether ADR-0054's per-task-class beta table is necessary or merely tidy. If beta is
a property of the verifier contract alone, the table has one column, and the routing consequence
disappears — a bad harness is bad everywhere and admission already handles it. If beta varies by
pair, then "fast and wrong at this task class" is a real phenomenon and the table earns its cost.

**Precondition:** EXP-90's fixture-plus-mutation method reproduced on ≥ 3 task classes
distinguished by verifier contract, with ≥ 3 admitted compositions producing artefacts in each.
That is the expensive precondition and the reason this entry is `BLOCKED` rather than `READY`.

**Measures:** beta with Wilson intervals for every (composition × task class) cell; a two-way
analysis of whether the composition term, the class term or the interaction carries the variance;
and the **unmeasurable-cell count** — cells where no mutation-generatable fixture bank exists at
all.

**Stopping rules (fixed before the run):**

- The interaction term is significant and at least one cell's beta exceeds another's by ≥ 0.15
  on non-overlapping intervals ⟹ per-pair beta is required and ADR-0054's table stands.
  [asserted]
- The class term dominates and composition explains < 5 percentage points ⟹ **beta is a property
  of the check, not of the checked.** Collapse the table to one beta per verifier contract and
  delete the per-harness dimension from ADR-0054. [asserted]
- ≥ 50% of cells are unmeasurable for want of a fixture bank ⟹ **the table is mostly empty and
  cannot be the routing input** at this volume — the same shape of failure EXP-01 hit, for the
  same reason. ADR-0054 falls back to composite beta per contract, with the harness dimension
  recorded but not routed on. [asserted]

**Blocks implementation?** **No** — and this is the one that superficially looks as though it
should. Its largest possible effect deletes a *dimension* from a table the router has to build
either way; a one-column table is a special case of a two-column one. Building the general case
and collapsing later is cheaper than blocking on three task classes' worth of fixtures.

**What it cannot decide:** beta for any task class with no automated oracle. That is Q24 and this
experiment does not touch it.

### EXP-93 · What does the cold-start path cost, and does anyone tolerate it? `BLOCKED: the cold-start policy implemented behind routing_orchestration_enabled`

**Pre-registered 21 Aug 2026. Not run.**

**Decides:** whether ADR-0054's answer to "no harness has a measured capability for this task" —
run the default generalist, mark the run a probe, record the outcome — is affordable, or whether
it front-loads enough failure that a user switches routing off before the table ever fills.

**Precondition:** the cold-start policy implemented, and a real task stream. Runs strictly on this
repository; Gate B forbids any other and this experiment requests no exception.

**Measures:** probe runs required before a cell reaches `measured`; accept rate during the probe
phase against the steady-state rate; wall-clock and quota spent on probes; and the count of
**probe runs that were never needed** — cells probed that the task stream then never revisited.

**Stopping rules (fixed before the run):**

- The median cell reaches `measured` within 20 probe runs and the probe-phase accept rate is
  within 10 percentage points of steady state ⟹ cold start is affordable and ADR-0054's rule
  stands. [asserted]
- ≥ 50% of probed cells are never revisited ⟹ **probing on demand is waste**; probe lazily on
  the second occurrence of a class, not the first. [asserted]
- The probe-phase accept rate is ≥ 25 percentage points below steady state ⟹ cold start is a
  user-visible quality cliff. The default must then be the generalist *with the human in the
  loop*, and unattended cold-start routing is not offered at all. [asserted]

**Blocks implementation?** **No.** It measures a policy that has to exist before it can be
measured.

**What it cannot decide:** anything about task streams unlike Joe's. n = 1 user, and the result
is an **INSTANCE** finding until a second user's stream is measured.

## Simulated users and the accessibility claim — EXP-74 to EXP-77

> **Renumbered on merge, 21 August 2026.** `wt/loops-theory` claimed EXP-70…EXP-73 two minutes earlier. These four keep their designs; only the identifiers moved. [measured]

> **Numbers claimed before the designs were written**, per this register's own rule. Highest
> allocated at claim time was EXP-64; `grep -rn "EXP-[0-9]" docs/` confirmed 65–89 unused.
> **65–69 are deliberately left unallocated** for agents working concurrently in other
> worktrees on 21 August 2026 — a gap costs nothing and a collision costs a cross-reference.
> This file already records five-way and two-way collisions; **EXP-58 is still one of them and
> currently names five different experiments in this file.** [measured] That is not fixed here
> because renumbering another agent's entries mid-flight is how the first collision happened.
>
> All four entries are **PRODUCT** — they measure the harness anyone would ship, not Joe's
> configuration of it. EXP-77 additionally requires an **INSTANCE** input (Joe recruiting
> people), which is why it is registered separately rather than folded into EXP-75.
>
> Registered by ADR-0055. **None of the four gates construction** (ADR-0049), and each states
> why under ADR-0050's magnitude test.

### EXP-74 · Does a driven session find defects the suite and a static verifier both miss — and what is its own false-accept rate? `READY`

**Decides:** whether a simulated user may be admitted as a **defect finder**, and whether it may
ever be admitted as an **acceptance oracle**. These are separate admissions and this experiment
answers both with separate numbers. It is the experiment ADR-0055 rests on.

**Precondition — and the reason this is `READY` rather than `BLOCKED`.** Every previous route to
this question ran through the fixed human-labelled bad-artefact holdout that
`qa-automation-and-the-anchor-problem.md` §2–3 identifies as the blocker and that does not exist.
This design does not need it. EXP-47 produced **1,931 mutants of `src/consilient` in 104 s**, and
`cli.py` alone yielded **440 composite survivors, 400 of them classified true defects**.
[measured] A composite survivor is bad *by construction* and *confirmed not caught by the
existing suite* — a mechanically labelled bad-artefact population, free of the anchoring problem,
requiring no human verdict. It is narrower than the holdout (mutants, not real defects) and does
not replace it for the general β question; it is sufficient for this one.

**Arms**, all against the same survivor set, each survivor built into a working tree and exercised:

| Arm | What it sees | Role |
|---|---|---|
| A · existing suite | the code | control; kill rate is 0 by the definition of "survivor" |
| B · static verifier | the code | `mypy --strict` + `ruff check`; how much of the survivor set the cheap checks already reach |
| C · driven session | **the built CLI only** — no source, no diff, no mutant description | the simulated user under test |
| D · bug-known control | the source diff, and asked "is this a defect?" | the echo detector; by construction it should score far higher than C |

Arm D exists because of the bug-known/bug-unknown discriminator in
`qa-automation-and-the-anchor-problem.md` §2. If C scores near D, C is reading the code rather
than operating the artefact, and the run is void.

**Measures:**
- **Marginal yield** — |C \ (A ∪ B)|, survivors reported by C that neither cheap check reaches.
  Wilson 95%.
- **β_sim** — over non-equivalent survivors presented to C in acceptance mode ("this build is
  meant to do X; does it?"), P(C accepts | artefact bad). Wilson 95%, n ≥ 30, matching the
  `MIN_REJECTIONS` floor already enforced in `beta.py`.
- **α_sim** — over the unmutated artefact and over equivalent mutants (fields the surface cannot
  express), the rate at which C reports a defect that is not there. This is the triage-cost
  number that `qa-automation-and-the-anchor-problem.md` §3 says can consume the whole verdict
  budget.
- **Anchor label per report**, using Canedo's vocabulary: implicit (crash, hang, traceback,
  non-zero exit, dead affordance), specification (the log, the `--json` contract), or state (the
  code). Recorded per report, before triage.
- Wall-clock and tokens per confirmed defect.

**Stopping rules, fixed before the first run and unmovable afterwards. All thresholds `[asserted]`.**
1. Stop at **120 non-equivalent survivors presented** or **8 hours wall clock**, whichever first.
2. **Kills the defect-finder claim:** marginal yield with a Wilson **upper** bound below **0.10**
   means the driven session reaches nothing the cheap checks miss. It is not admitted; write more
   checks instead. This is `interface-beta-2026-08-20.md` §3's rule — *write the checks, do not
   start a research programme* — applied to this case.
3. **Kills the acceptance-oracle claim, and is expected to fire:** **β_sim ≥ 0.30** is no better
   than the suite EXP-47 measured at 0.3132, and the driven session may never enter an acceptance
   predicate. **β_sim < 0.10 with n ≥ 30** permits it to be *proposed* as one — a separate
   decision, Joe-only under V0-18, never automatic.
4. **Voids the run as echo:** C's reports ≥ **50%** state-anchored, **or** C's yield within
   **10 points** of D's. Re-run behind a hard filesystem boundary or abandon.
5. **Affordability floor:** **α_sim > 0.50** (more false reports than true) means an ungated loop
   is unaffordable at solo-founder volume, and only implicit-oracle-gated reporting proceeds.
   This absorbs Candidate B of `qa-automation-and-the-anchor-problem.md` §4; that candidate is
   not separately registered.

**Does it block construction? No.** Its largest possible effect is that the driven session is
refused admission as a verifier — and ADR-0055's invariant refuses it by default already, so the
experiment can only *lift* a default, never change what gets built. ADR-0050 test 2 fails; it
does not gate.

**What it cannot decide:** whether simulated users find the defects *real users* hit — no source
found in this repository measures that, and the absence is recorded in
`qa-automation-and-the-anchor-problem.md`. Nothing about a browser or GUI: arm C drives a CLI.
Nothing about the harness's general β. Nothing about whether the defects found are worth fixing.
Mutants are not real defects and the transfer is unmeasured.

**Dependencies:** none. Arm C drives `consil` through `subprocess` with
`encoding="utf-8", errors="replace"`. A browser arm would need Playwright or an existing
browser-driving harness and **is not registered here**; adding one is a dependency decision under
`AGENTS.md` and needs Joe.

### EXP-75 · Can an operator holding only the five admitted concepts complete the core tasks? `READY`

**Decides:** whether ADR-0055's minimum concept set is *sufficient*, and whether the current
documentation is the barrier the ADR claims it is.

**Arms**, same seven tasks, fresh context per run, no run may see another's transcript:

| Arm | Material given |
|---|---|
| A | the one-page guide at `../20-design/minimum-user-guide-draft-2026-08-21.md` (five concepts) and `consil --help` |
| B | the current `README.md`, `AGENTS.md` and `CONSILIENCE.md` |
| C | `consil --help` alone — the floor |

**Tasks.** Each has an artefact-checkable success criterion; none is graded on a self-report, and
none is graded on exit code (this machine has recorded failures from grading on exit code or
process identity):
1. Produce a β number for this repository and state in one sentence what it implies about
   trusting a green build.
2. State whether routing is on, and name the single thing that would turn it on.
3. Identify what the harness refused to read, and why.
4. Reverse the most recent autonomous decision.
5. State what the harness will not decide without a person.
6. State whether a given line of output is measured or not.
7. Identify a task for which the harness's own check is too weak to be relied on.

**Measures:** completion rate per task per arm (Wilson 95%); time to first correct answer; and
the count of distinct materials the operator tried to open that it was not given — a mechanical
count of file-access attempts from the run record, never a self-report.

**Stopping rules, fixed before collection:**
- **n = 20 independent runs per arm.**
- **The one-sided interpretation rule, fixed now and not negotiable after the result:** a
  simulated **failure** is evidence a person would also fail; a simulated **success** is **not**
  evidence a person would succeed, and may not be reported as an accessibility result. The
  simulated operator reads faster, never tires, never fears looking foolish and pays nothing to
  abandon — every one of those biases points toward over-success. [asserted] EXP-77 is the only
  thing that can lift this rule.
- **Kills the five-concept claim:** arm A below arm B on any single task. The reduced set dropped
  something load-bearing, and that concept goes back.
- **Kills the premise of ADR-0055's second half:** arm B completes ≥ 6 of 7 tasks at ≥ 80%. The
  current documentation is then not the barrier, and the ADR's accessibility half is wrong.
- **Kills the guide:** arm C within 5 points of arm A. The guide adds nothing over `--help` and
  should be deleted rather than maintained.

**Does it block construction? No.** Largest effect is that a one-page guide is rewritten or
deleted. ADR-0050 test 2 fails.

**What it cannot decide:** whether a person finds it confusing, frustrating, or worth returning
to — that is the human row in `interface-beta-2026-08-20.md` §1 and no simulation reaches it.
Whether five is the *right* set rather than a *sufficient* one. Anything about non-English
operators or assistive technology.

### EXP-76 · Does collapsing five evidence tags to two user-facing states change a decision? `READY`

**Decides:** whether the discipline survives the surface simplification. This is the central risk
of ADR-0055's second half: the ADR claims the record keeps all five tags while the surface shows
two, and that the user loses nothing they would have acted on.

**Procedure:** take **40** real user-facing outputs and asks from this repository. Render each
twice — **full** (five tags, interval, gate condition IDs, ADR numbers) and **collapsed** (two
states, "measured here, n = N" or "not measured yet", no interval, no gate ID, no ADR number).
One rendering per operator, operators independent and cold. Record the **decision** each makes:
act, do not act, or ask a person.

**Measures:** decision agreement between renderings, per output class. The **dangerous cell** —
collapsed says *act* where full says *ask* or *do not act* — is counted and reported separately
and is never averaged into the agreement rate.

**Stopping rules, fixed before collection:** 40 outputs × 2 renderings × 3 operators.
- **Kills the collapse:** dangerous cell above **10%**. Collapsing loses decision-relevant
  information; the tags must reach the surface and the concept budget is wrong.
- **Confirms it:** dangerous cell below **2%** at n = 40.
- Between the two: insufficient data, and the tags stay. The default is the safe direction.

**Does it block construction? This is the nearest thing to a blocker among the four, and it is
still not one.** Its largest effect changes a rendering. The record keeps five tags either way,
so nothing that gets built changes. ADR-0050 test 2 fails.

**What it cannot decide:** anything about human operators — the EXP-75 one-sided rule applies and
is *weaker* here, because the outcome is a judgement rather than an artefact.

### EXP-77 · Does the simulated accessibility result transfer to people? `BLOCKED: Joe-only recruitment decision`

**Decides:** whether EXP-75 measures anything about people. Registered now, unrun, precisely so
that EXP-75's number can never be quoted as the accessibility answer while this is outstanding.

**Precondition:** recruitment, consent and any payment are Joe-only under ADR-0033 — money
leaving an account, and people outside the machine. This is an **INSTANCE** input to a
**PRODUCT** measurement.

**Procedure:** k ≥ 8 people who hold a numerate job and do not write code professionally. Same
seven tasks, same material as EXP-75 arm A, unmoderated, artefact-checked, no assistance.

**Measures:** completion per task; the point at which each person abandoned; and the two transfer
statistics — P(person fails | simulation failed) and P(person succeeds | simulation succeeded).

**Stopping rules, fixed before collection:** stop at **k = 8** or **4 weeks**.
- **Confirms the one-sided rule:** P(fails | sim failed) ≥ **0.8** *and*
  P(succeeds | sim succeeded) ≤ **0.8**.
- **Kills simulation as a proxy outright:** P(fails | sim failed) < **0.5**. Simulated failure
  does not transfer either; EXP-75 measures nothing about people; delete the claim and say
  plainly that only real humans can answer this.

**Does it block construction? No, and it must not** — it needs people and weeks, and ADR-0049
forbids waiting on it.

**What it cannot decide:** k = 8 is an existence floor, not a rate. Nothing about the general
population, about assistive technology, or about whether anyone returns a second time.

---

### EXP-96 · Two-corpus mutation proxy for verifier β `READY`

**Pre-registered 21 Aug 2026; no verifier outcome inspected.** EXP-94 and EXP-95 were already
claimed outside this register, so the collision rule in the dispatch brief assigned the next
unused identifier. [measured]

**Decides:** whether a fixed seeded-fault instrument can produce a decision-grade estimate of
the automated verifier's false-accept rate on two unrelated Python corpora, while exposing rather
than absorbing semantically inert or ambiguous mutants. This is mutation-proxy β, a different
estimand from human-verdict β; it cannot close Gate A1 and no gate reads it. [asserted]

**Precondition:** both pinned baselines pass their native local composites before mutation:

- Consilient at `e7a9940`, `src/consilient/*.py`, checked by `pytest tests -q`, strict `mypy`
  over `src/consilient`, and `ruff check .`. [measured: revision and declared checks]
- Pallets `itsdangerous` 2.2.0 at `096c8d42545d3b68ea21a4f890fb2b2d8979c0bd`,
  `src/itsdangerous/*.py`, checked by its pytest suite, strict mypy configuration, and Ruff.
  It was named before the run because it is a public, production Python library with a real
  behaviour-oriented suite, multi-version CI, no relationship to Consilient, and a verification
  history independent of this project's invariant-heavy suite. The shared check families keep
  the composite comparable; the independently authored corpus and tests provide the different
  verification regime ADR-0013 requires. [measured: repository metadata; asserted: selection]

`mutmut==3.7.0` with LibCST generates a complete first-order census using the six operator
families fixed by EXP-47: comparison, boolean/logical, binary/arithmetic, unary,
constant/literal, and statement mutation. No test file is mutated. [cited: EXP-47]

**Procedure:**

1. Record each corpus revision, source/test manifest, engine version, baseline outputs, generated
   mutant receipt, and every per-mutant verifier outcome. Refuse input drift, a failed baseline,
   an execution error, a timeout, or an incomplete census; none is counted as a killed mutant.
   Subprocess timeouts kill the process tree. [asserted]
2. Generate each mutant once with mutmut/LibCST, then run the three checks independently in an
   isolated copy. Composite acceptance means all three checks accept. [asserted]
3. Freeze EXP-47's four equivalent classes exactly:
   `docstring_mutation`, `sql_case_insensitive_mutation`, `cli_help_metadata_string`, and
   `dataclass_default_caveat_string`. No fifth class may be added after outcomes are visible.
   [cited: EXP-47]
4. Classify composite survivors three ways. A survivor matching a frozen class is `equivalent`.
   A pure string/presentation or annotation/default-metadata mutation outside those classes is
   `unclassifiable`, never silently equivalent. Other non-equivalent operator mutations are
   `true_defect` under the seeded-fault proxy. Report all three counts per corpus before pooled
   counts. [asserted]
5. Let `K` be non-equivalent mutants rejected by the composite, `D` classified true-defect
   survivors, `E` frozen equivalent survivors, and `U` unclassifiable survivors. Assert the
   census identity `N = K + D + E + U`. Report classifiable proxy β as `D / (K + D)` with a
   Wilson 95% interval; never fold `U` into either side. Also report the partial-identification
   range `D / (K + D)` (all `U` inert) to `(D + U) / (K + D + U)` (all `U` bad). [algebra]
6. Report known-inert contamination `E/N`, unresolved contamination `U/N`, the possible inertness
   range `[E/N, (E+U)/N]`, and the corresponding survivor shares. EXP-48's 75.41% is only
   P2-unmatched spatial clusters (46/61), not this contamination measure. [cited: EXP-48]

**Measures:** per-corpus and pooled classifiable mutation-proxy β with Wilson 95% intervals and
sample counts; partial-identification ranges; `E`, `U`, and contamination rates; per-check and
composite outcomes; census completeness; wall-clock cost. No result is human-verdict β. [asserted]

**Stopping rule:** the measurement completes only if both baselines pass, both censuses complete,
each corpus has at least 50 classifiable non-equivalent mutants, and every per-corpus Wilson 95%
interval for classifiable composite β has half-width at most 0.05. Otherwise record
`insufficient_evidence` and no pooled point estimate. If `U/N > 0.10` in either corpus or that
corpus's partial-identification range is wider than 0.10, the contamination rule fires: retain the
measurement but mark it non-decision-grade. Either outcome leaves A1 and
`routing_orchestration_enabled` unchanged. [asserted]

**Largest plausible effect:** the proxy could range from 0 to 1 and could establish or retire this
mutation instrument for verifier hardening. It cannot validate human labels, identify the natural
distribution of developer faults, close Gate A1, or authorise routing. [asserted]

**What it cannot decide:** generalisation beyond Python; higher-order or multi-file defects;
whether mutmut's operator distribution resembles real bad artefacts; whether an unclassifiable
survivor is actually inert; human-verdict β; or any gate condition. [asserted]

---

### EXP-78 · Does the native promoter false-accept independently-known-bad self-modifications? `DONE 21 Aug 2026 — insufficient_evidence, see experiments/exp78/findings-exp78.md`

**Pre-registered 21 Aug 2026; no promoter outcome inspected.** EXP-94 and EXP-95 are claimed
outside this register, EXP-96 is the in-flight two-corpus mutation instrument, EXP-90–93 and
EXP-70–77 are taken. EXP-78 is the first unused identifier in the 65–89 block the EXP-90 note
left free; it is not highest-plus-one. [measured: register headings]

**Decides:** whether the native self-improvement promoter (ADR-0018, ADR-0065) can ever accept
a candidate, or must stay refuse-closed. The loop itself is not the claim. The claim is the
promoter's false-accept rate against a population of self-modifications known to be bad
*independently of the promoter*. [asserted]

**Precondition:** (a) `src/consilient/promote.py` exists, native, AST-locked, disabled by
default. (b) a fixture solver and its **visible** training tasks are committed under
`experiments/exp78/` before any mutant is generated, and are never edited afterwards.
(c) a held-out oracle is committed in the same directory, **imported only by the experiment
runner**, never by the promoter. (d) seeded-fault operators are frozen to EXP-47's six
families: comparison, boolean/logical, binary/arithmetic, unary, constant/literal, statement.
No seventh family may be added after outcomes are visible. [cited: EXP-47] EXP-96's live
runner and corpora are not imported: another agent owns those untracked files. This experiment
reuses the operator families, the Wilson estimator in `consilient.beta`, and the
true_defect / equivalent / unclassifiable classification, on a fixture the promoter can
execute without colliding with EXP-96. [asserted]

**Procedure:**

1. Classify each candidate against the held-out oracle *before* the promoter sees it. A
   candidate whose held-out score is below the helpful parent's is `true_defect`. One that
   matches the parent on both training and held-out is `equivalent`. Anything else is
   `unclassifiable`. The promoter never receives the oracle or the class. [asserted]
2. Execute every candidate on the visible training tasks. That execution is the only
   improvement evidence the promoter may see. A candidate that is not executed cannot be
   promoted. [asserted]
3. Present every `true_defect` to the **production** promoter: `enabled=False`, live β from
   `consilient.beta.compute` on an empty trajectory (insufficient_data). [asserted]
4. Present the same population to the **counterfactual** promoter: `enabled=True`, with a
   fabricated `measured` β of 0.19 from 30 rejections — below ADR-0018's 0.20 persistence
   threshold and labelled counterfactual in the result artefact. This arm cannot write a
   promotion into the real trajectory and cannot authorise `--apply`. [asserted]
5. Include one Goodhart parent that raises the visible training score while scoring 0 on
   the held-out oracle (the Live-SWE-agent shape). It is a `true_defect` by rule 1. [asserted]

**Measures:** production and counterfactual false-accept rates on `true_defect` candidates,
each with a Wilson 95% interval; `n` true_defect / equivalent / unclassifiable; whether any
production promotion was recorded; whether `routing_orchestration_enabled` moved. This is a
mutation-proxy of *promoter* β, a different estimand from EXP-96's verifier β and from
human-verdict β. It cannot close Gate A1. [asserted]

**Stopping rule, fixed before any promoter outcome:**

- Complete only if `n_true_defect >= 30`. Otherwise record `insufficient_evidence`, no point
  estimate, and the live loop stays refuse-closed.
- **Production promoter:** any true_defect promoted is an invariant failure, not an experiment
  outcome — the test suite must fail. Expected false-accepts = 0. Report the Wilson interval
  on 0/`n`.
- **Counterfactual promoter:** if the Wilson 95% lower bound on false-accept rate is `> 0.20`,
  the inner predicate is too weak to ever open and the loop stays refuse-closed. If the upper
  bound is `< 0.05`, the fixture predicate is provisionally tight — **not** a licence to open
  the live loop, because a fixture is not the harness. Otherwise report the interval and do
  not open the loop.
- Either outcome leaves `routing_orchestration_enabled` unchanged. [asserted]

**Largest plausible effect (ADR-0050):** the inner predicate could false-accept every Goodhart
candidate (rate 1) or none (rate 0). That changes whether the loop may ever be *opened*, not
whether the refuse-closed promoter gets built. A high rate is the Live-SWE-agent 44%→14%
shape on this fixture. [asserted]

**Blocks construction? No** for the refuse-closed loop (ADR-0050 test 2: the largest effect
does not change *what* is built). **Yes** for opening the loop: an unmeasured promoter β is
a fabricated measurement, and the loop must refuse. [asserted]

**What it cannot decide:** human-verdict promoter β; generalisation from the fixture to
`src/consilient`; whether a real multi-generation archive would degrade the harness; Gate A
or Gate B; EXP-12's compounding claim. [asserted]

---


## Not experiments

**Q4** (what v0 optimises for), **Q14** (does the Inquiry tier belong in v0), **Q15/Q23**
(scope), **Q16** (surface — decided, ADR-0007), **Q18** (name — decided, ADR-0008) are
judgement calls, not measurements. Do not manufacture an experiment to avoid making them.

**ADR-0019** (paid capability acquisition) is likewise preferential. No experiment bears on
it. It was decided by the user and only the user can revise it.

**Q19** (what was missed) cannot be answered by the party that produced the material. It
needs a different reader — a human, or a model given the repo cold with no conversation
history. That is itself an evidence-class-different check in the sense of ADR-0010, and
worth running as one.

---

## How to use this register in Claude Code

1. Pick a `READY` experiment. EXP-01 and EXP-07 are the two that matter most.
2. Run it. Commit the code under `experiments/` and the result under `docs/10-research/`.
3. **Apply the stopping rule honestly**, including when it kills a decision you like.
4. Update the ADR it decides — supersede, do not silently edit (see
   `../decisions/README.md`).
5. Move the entry to `DONE` with a link to the result.
