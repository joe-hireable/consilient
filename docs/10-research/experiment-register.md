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

### EXP-05 · Adapter surface across five backends `DONE 19 Aug 2026 — see experiments/exp05/findings-exp05.md`
**Result:** Claude Code and Codex passed a live ticket. Adapter #2 (Codex) did not
force an interface redesign. Adapter #3 (Cursor) exposed a genuine namespace-dependent
path question, absorbed by a per-adapter translation seam with four passing tests.
Adapters #4 (Ollama) and #5 (OpenRouter) fit the model-backed seam; Ollama completed a
live run but failed verification, while Cursor and OpenRouter remain blocked on login/key
for live validation. The stopping rule does not fire. [measured]
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
20.4 s for a Codex success and 25.6 s for a Claude Code success: 5.6× and 4.5×.
The pre-registered 2× reopening condition was observed, so ADR-0003 is reopened for
investigation. This is n=1 on one trivial task and does not establish a population
multiplier. EXP-07 is now the highest-priority replication experiment. [measured]

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
**Measures:** decision quality against a held-out ground truth; tokens; wall-clock.
**Stopping rule:** if (b) does not beat (a), **meetings are ceremony and should be cut** —
the whole authority matrix goes with them. If (c) beats (b), the delegation theorem does not
apply the way ADR-0020 claims and that ADR is wrong.
**This is the cleanest falsification test in the register.** Neither outcome is comfortable
and both are informative.

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

1. Pick a `READY` experiment. EXP-01 and EXP-05 are the two that matter most.
2. Run it. Commit the code under `experiments/` and the result under `docs/10-research/`.
3. **Apply the stopping rule honestly**, including when it kills a decision you like.
4. Update the ADR it decides — supersede, do not silently edit (see
   `../decisions/README.md`).
5. Move the entry to `DONE` with a link to the result.
