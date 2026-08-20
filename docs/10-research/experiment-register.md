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

### EXP-01 · Measure β on repository history `IN PROGRESS 19 Aug 2026 — see experiments/exp01/findings-exp01.md`
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
- If OpenRouter's automatic router produces any unattended false admit that Consilience's
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
Consilience needs typed `context_next`/`steer`/`interrupt` commands and staged ACKs in v0.
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

### EXP-27 · First-party change intelligence versus dispatch-time discovery `IN PROGRESS: phase A PASS; 30-day phase blocked on collector`
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
**Decides:** whether Consilience should default to a lean task contract, whether calibrated
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
> Both partial datasets are preserved outside the evidence base. **The run must be repeated** once
> the runner is append-only, carries a `run_id`, and takes a lock naming its PID.
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
