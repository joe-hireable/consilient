# Experiment register

Every open question that cannot be settled by argument becomes a **runnable experiment**.
This file is the bridge between `../00-context/open-questions.md` and things Claude Code can
actually execute.

**Rules of this register.** Each entry states: what it decides, the precondition, the
procedure, the measurement, and the **stopping rule** — the result that would change a
decision. An experiment with no stopping rule is not an experiment, it is data collection.

Status: `READY` (runnable now) · `BLOCKED` (needs harness component X) · `DONE`.

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

### EXP-03 · Are per-check β values independent? `READY`
**Decides:** whether ADR-0012's lower-bound product is usable as a prior at low sample size.
**Precondition:** EXP-01 output.
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
more sweep.

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

### EXP-07 · Wasted-work multiplier `IN PROGRESS: n=1 pilot crossed the threshold`
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
[asserted] Synthetic fixtures can replicate the latency mechanism but cannot establish
that a learned router improves real work; that requires a separate policy comparison on
real trajectories. [asserted]

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

### EXP-16 · Prototype the meeting layer on external PM tools; measure their friction directly `READY`
**Decides:** two live claims at once. (1) ADR-0006's grounds for a *native* ticket store —
that external PM tools "impose human-shaped state machines, human-shaped rate limits, and a
webhook round-trip on every state change" — currently `[asserted]`, never measured. (2)
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
**Procedure:** run a 2 × 4 factorial blocked by exact runtime composition. Prompt detail is
(A) the minimum sufficient objective/authority/scope/invariant/verifier/budget/output
contract or (B) the same facts plus a plausible step-by-step procedure and examples.
Feedback style, with identical substantive diagnosis and requested action, is: neutral
diagnostic; generic praise plus diagnostic; calibrated recognition of a genuinely passed
check plus constructive diagnostic; or mildly scathing person-directed correction without
slurs or threats. Randomise order. Cap every trajectory at the initial attempt plus two
feedback turns. Fixed total: 2 × 4 × 6 × 3 = 144 trajectories. Blind-audit a preselected
random sample of 12 for whether any disagreement was genuinely evidence-backed. Run each
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
metered fallback.
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

### EXP-30 · Usable context for senior and middle-management orchestration `BLOCKED: frozen fixtures + OpenRouter hard cap`
**Decides:** ADR-0030 — whether Opus 5 earns the senior-orchestrator default, whether
OpenRouter Gemini 3.7 Flash at high effort earns a bounded middle-management role and
whether full-history context beats a compact manifest with retrieval.
**Precondition:** 24 immutable synthetic programme-state fixtures split evenly between
cross-workstream decisions and bounded delegated decisions; deterministic checks for goal,
authority, constraints, provenance, current decision, lease, resource state and correct
next action; authenticated subscription-backed Claude Code Opus 5; a pinned OpenRouter
`google/gemini-3.7-flash` record; and a separately user-authorised provider-side hard cap.
No OpenRouter call runs before that numeric cap exists. [asserted]
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

### EXP-31 · Local 30B-class qualification against the frozen EXP-07 fixtures `READY: blocked only while EXP-07 holds the GPU`
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
