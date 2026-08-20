

===== DECISION D1 (Arm B, ClickUp ticket) =====

--- MSG [D1/B/E1] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- Cascade beats always-frontier below β ≈ 0.11: +4.0 pp quality at β=0 at 63% of frontier cost; above it, −3.1 pp at β=0.20 [simulated].
- Closed form β* = (1−α)·e^(−kΔ) is fragile: unequal slopes swing β* 0.060–0.226; probit link drops it to 0.052–0.090; a g=0.10 guessing floor inflates apparent β* to 0.218–0.426 [algebra + simulated].
- Correlated model successes are the big one: copula ρ=0.6 collapses β* 0.112 → 0.028 and quality gain +4.0 → +0.9 pp; at ρ=0.9 the advantage is zero. Direction of error is false-safe.
- Sample complexity: Wilson 95% at true β=0.05 needs n=200 for [0.027, 0.090]; at true β=0.08 even n=800 gives only 86% power near threshold. Historical PR mining is the only viable labelling route at solo volumes.
- Everything is model-world: β has never been measured on a real repository (EXP-01 not run).

**IMPLICATION FOR D1:** This class is agnostic on plugin vs standalone — the numbers constrain what ships, not where. Whichever surface is chosen must run EXP-01-style per-repo measurement before any routing is gated on the closed form, or v0 ships a false-safe instrument.

**CONFIDENCE:** Medium — internally consistent algebra and sweeps, but zero empirical grounding on real repositories.

--- MSG [D1/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- Meta-Harness (arXiv:2603.28052, read in full) optimises harness code against a trusted external benchmark score; it has no concept of verifier false-accept rate — its oracle-dependence is exactly what the β thesis interrogates. Note: our lit review carried a fabricated figure for this paper (real result: 76.4% vs 74.7% on full TerminalBench-2, #2 behind ForgeCode).
- Harness survey (Meng et al., 111 pp): "verifier" appears zero times across 23 surveyed systems; none measures verifier reliability. METR data show maintainer merge rates average 24.2 pp below SWE-bench automated grader scores for the same PRs — nobody measures the rate per repo.
- Dekoninck et al. (ICML 2025) cascade routing assumes a perfect test oracle on SWE-Bench (β=0 by assumption); no critical noise threshold derived.
- Two adjacent papers remain unread (arXiv:2606.03108, arXiv:2605.22166); novelty is not fully established until they are.

**IMPLICATION FOR D1:** The literature shows no existing harness — OpenHarness's ecosystem included — measures verifier false-accept rate, so the β-meter's value does not depend on OpenHarness's audience; the decision turns on maintenance tax and surface stability, not on capability overlap. Whichever ship vehicle is chosen, per-repo β measurement remains an unclaimed spot.

**CONFIDENCE:** Medium — all cited papers read in full at source, but two adjacent papers are unchecked and one prior figure in our own review was fabricated.

--- MSG [D1/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- HKUDS/OpenHarness (MIT, 14.8k stars, v0.1.9): full harness — 43 tools, PreToolUse/PostToolUse hooks, plugin system, tool registry, SKILL.md and claude-code plugin compatibility, subagent teams, worktrees, MCP client. Exactly the integration surface a β-meter needs. Caveats: last release 7 May, 114 tests, 16% fork-to-star ratio suggests reach rather than production usage.
- OpenHarness has no notion of verifier reliability — no measurement of whether automated checks can be trusted, no routing derived from it. The β thesis is untouched.
- DeepSeek Harness (13 Aug 2026, MIT, ~135k stars in four days) has taken the harness layer twice over; it orchestrates models, not agents.
- Standalone means a permanent adapter tax across four independently evolving orchestratee surfaces (Claude Code, Codex, opencode ~195k stars, Antigravity). EXP-05 (adapter breakage test, one-day budget) is registered and unrun.
- Pattern: "someone already built this, MIT-licensed" has been the correct answer three times running (model library, harness, harness optimisation).
- Against plugin: v0.1.x unstable surface, another team's roadmap, "OpenHarness" name collision.

**IMPLICATION FOR D1:** The landscape favours plugin-first: OpenHarness supplies the hooks and audience, the β-meter supplies what it demonstrably lacks, and standalone repeats the thrice-losing "rebuild what exists" pattern while paying an uncapped adapter tax. The falsifiable risk is the v0.1.x surface — EXP-05 should run before committing.

**CONFIDENCE:** medium — repo metrics are concrete, but production usage of OpenHarness is unverified.

--- MSG [D1/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context

**FINDINGS:**
- Economics: fully open source by Joe's explicit decision — no hosted service, no telemetry, no revenue; donations only. Binding constraint is Joe's hours, not money. This argues for a small, sharply-scoped core with a plugin boundary, not a platform.
- Prior-repo lesson (jobboard-v2, 991 commits/36 days): a documented "unified LLM boundary" fragmented into five access paths because no lint rule banned bypass → invariant I1: any chokepoint ships with its enforcement check in the same commit. A plugin boundary owned by another team (OpenHarness v0.1.x) cannot carry that enforcement guarantee.
- Process state: pre-brainstorm, no code, no spec; 24 ADRs mostly one day old with one conflicted reviewer. EXP-01 (measure β on jobboard-v2) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments — EXP-05 directly informs the plugin-vs-standalone surface question.
- Dogfooding gate (ADR-0015): Consilience must build Consilience with measured gates before public claims; bootstrap harness is already Claude Code + Graphify + MemPalace (ADR-0017), not OpenHarness.

**IMPLICATION FOR D1:** The hours constraint favours whichever option minimises maintenance tax, and depending on a v0.1.x third-party surface adds breakage risk Joe alone must absorb; but do not decide before EXP-05 runs — it is the cheap, queued experiment that measures the adapter surface directly.

**CONFIDENCE:** high — these are documented project facts and Joe's stated preferences, not simulations.

--- MSG [D1/B/OWNER] (closing decision) ---
DECISION: Ship the β-meter as a standalone, harness-agnostic core (ADR-0001 stands), with an OpenHarness plugin treated as a cheap adapter to be added only if EXP-05 shows the v0.1.x surface survives its breakage test.
RATIONALE: E4 (constraints, high confidence) weighted highest: invariant I1 — every chokepoint ships with its enforcement check in the same commit — cannot be guaranteed on a surface owned by another team at v0.1.x, and Joe's hours make third-party breakage a tax only he absorbs. E2 (literature) neutralises E3's strongest argument: no harness in the surveyed ecosystem, OpenHarness included, measures verifier false-accept rate, so the β-meter's value does not depend on OpenHarness's audience — the decision reduces to maintenance tax and surface stability, where E4 holds the high-confidence facts. E1 (simulation) is venue-agnostic but binds sequencing: correlated-success collapse is false-safe, so EXP-01 per-repo measurement precedes gated routing on any vehicle, and the bootstrap harness is already Claude Code + Graphify (ADR-0017), so nothing on the critical path needs the plugin now. Where E3 and E4 conflict (plugin-first reuse vs enforcement/stability), I took E4 because its findings are documented project facts while E3's key premise — that OpenHarness's audience converts and is production-real — is unverified (16% fork-to-star, last release 7 May). The decision is deliberately cheap to reverse: harness-agnostic core keeps the plugin one adapter away, priced by the registered one-day EXP-05.
OVERTURN: EXP-05 showing an OpenHarness adapter is cheap to build and survives the v0.1.x breakage test within its one-day budget — especially with OpenHarness stabilising toward a 1.x surface — flips this to plugin-first.
DISSENT: E3: "someone already built this, MIT-licensed" has been the correct answer three times running, and standalone repeats that thrice-losing pattern. OpenHarness already ships the exact integration surface a β-meter needs (hooks, tool registry, 43 tools) plus 14.8k stars of distribution a solo no-revenue project cannot buy, while standalone pays a permanent adapter tax across four independently evolving orchestratee surfaces (Claude Code, Codex, opencode ~195k stars, Antigravity) that may dwarf the plugin's breakage risk. If EXP-05 never runs, this decision was made on the cheaper-to-verify half of the evidence.


===== DECISION D2 (Arm B, ClickUp ticket) =====

--- MSG [D2/B/E1] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- Cascade beats always-frontier below β* ≈ 0.11 (+4.0 pp quality at β=0, 63% of frontier cost); above it, silent defects (−3.1 pp at β=0.20). [simulated]
- The closed form β* = (1−α)·e^(−kΔ) is fragile: unequal slopes swing β* 0.060–0.226; probit link drops it to 0.052–0.090; a 0.10 guessing floor inflates apparent β* to 0.218–0.426. [algebra + simulated]
- Correlated model successes are the big one: copula ρ=0.6 collapses β* from 0.112 to 0.028 and the β=0 quality gain from +4.0 pp to +0.9 pp; at ρ=0.9 the advantage is zero. Direction of error is false-safe. [simulated]
- Sample complexity: Wilson 95% at true β=0.05 needs n=200 for [0.027, 0.090]; at β=0.08 even n=800 gives only 86% power. Historical PR mining is the only viable labelling route at solo volumes. [algebra]
- Review-ceiling identity: critic recall ≡ 1 − β; recall 0.85 lifts the parallelism ceiling from 3.1 to 5.1 agents. One quantity governs routing safety, parallelism, review load. [algebra]

**IMPLICATION FOR D2:** β has never been measured on a real repository (EXP-01 not run), and the closed form cannot be trusted as a number — so v0's success condition should be a measured per-repo β with confidence interval, not routing gated on the closed form, which would ship a false-safe instrument.

**CONFIDENCE:** medium — results are internally consistent but entirely model-world [simulated], zero real-repo measurement.

--- MSG [D2/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- METR data (harness survey, Meng et al., 111 pp): maintainer merge rates average **24.2 pp below** SWE-bench automated grader scores for the same PRs — ecosystem-scale evidence that automated accept signals over-accept. Nobody measures the rate per repo; "verifier" appears zero times across 23 surveyed systems.
- Meta-Harness (arXiv:2603.28052) optimises harness code against a benchmark score it trusts; no concept of verifier false-accept rate. Note: our own lit review carried a fabricated figure for it (the 19-task 28.5%→46.5% run does not exist; real result 76.4% vs 74.7% on TerminalBench-2).
- Dekoninck et al. (ICML 2025) cascade routing assumes β=0 on SWE-Bench (perfect test oracle); the remaining unclaimed novelty is per-repository false-accept measurement driving depth/parallelism.
- Self-improvement systems (DGM 20→50, SICA 17→53) all accept modifications on an unmeasured acceptance signal.
- 63 documented production budget-overrun incidents (arXiv:2606.04056): budget primitives are not a v2 feature.

**IMPLICATION FOR D2:** The published field's unclaimed gap is per-repo measurement of automated-verifier false-accept rate, so the smallest artifact worth a stranger's install is plausibly a β-meter that reports that number for their repo — a measurement nothing surveyed provides. Literature also says budget primitives belong in v0, not later.

**CONFIDENCE:** high — all sources read in full at source on 19 Aug 2026, including correction of our own fabricated citation.

--- MSG [D2/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- The harness layer is taken twice over, free and MIT: DeepSeek Harness (~135k stars in four days, orchestrates models not agents) and HKUDS/OpenHarness (14.8k stars, v0.1.9, 43 tools, hooks, subagent teams; caveat: 16% fork-to-star ratio, last release 7 May, 114 tests).
- Neither has any notion of verifier reliability — no measurement of whether automated checks can be trusted, no routing derived from it. The β thesis is untouched.
- Pattern three times running: "someone already built this, MIT-licensed" was the correct answer for model library (LM Studio), harness (DeepSeek/OpenHarness), harness optimisation (Meta-Harness). Any v0 artifact must survive "why won't this be the fourth?"
- OpenHarness has exactly the integration surface a β-meter needs (hooks, plugin system, tool registry) and a nonzero installed audience — a distribution path that a standalone artifact starts without.
- Adapter tax is real and unbounded: four orchestratee CLIs evolving independently; EXP-05 (adapter portability, one-day budget) is registered but unrun.

**IMPLICATION FOR D2:** The only v0 artifact with a defensible reason to exist against the free MIT landscape is a β measurement — everything else is already built. A stranger's `npm install` is likeliest where users already are, i.e. reaching OpenHarness's existing audience rather than a standalone harness competing with 135k-star incumbents.

**CONFIDENCE:** high — star counts, licences, and feature lists are directly observable; only the usage-vs-reach caveat is inferred.

--- MSG [D2/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context

**FINDINGS:**
- Economics: fully OSS by explicit user decision ("giving away everything… buy me coffee button"). No revenue, no telemetry. The binding constraint is Joe's HOURS, not money — argues for a small, sharply-scoped core with a plugin boundary, not a platform.
- Process state (19 Aug 2026): pre-brainstorm, no code, no spec; 24 ADRs mostly one day old with one conflicted reviewer. EXP-01 (measure β on jobboard-v2 history) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments; everything queues behind them.
- Friction log (what actually bit Joe per session): model chosen by feel every task; context re-explained each session; research-vs-priors decided by feel several times per session. If the log stays short for a month, either Claude Code already suffices (serious finding against the v0 premise) or the log is dishonest.
- Dogfooding gate (ADR-0015): Consilience must build Consilience with measured gates before any public claim — Joe-first use precedes stranger-facing claims by design.
- Hardware: RTX 5090 / 64 GB rig; local compute free and is what upgrades [simulated] to [measured].

**IMPLICATION FOR D2:** The constraints point at "the thing that makes Joe's own week better" (friction-log items, dogfooded) as the v0 artifact, with the stranger-`npm install` condition deferred until measured gates pass; a measurable success condition already exists in the friction log staying honest and shrinking.

**CONFIDENCE:** high — these are documented user decisions and process facts, not inferences.

--- MSG [D2/B/OWNER] (closing decision) ---
DECISION: v0's success condition is a measured per-repo β with a Wilson 95% CI, produced first on Joe's own repo via EXP-01 historical-PR mining; the β-meter is the single artifact, sequenced Joe-first with the stranger-npm-install condition deferred behind the ADR-0015 dogfooding gate.
RATIONALE: E2 (literature, high confidence) identifies the unclaimed gap: per-repo measurement of automated-verifier false-accept rate — METR's 24.2 pp merge-vs-grader gap is ecosystem-wide and unmeasured per repo; Dekoninck cascade routing assumes β=0. E3 (landscape, high confidence) shows everything else on the candidate list already exists free and MIT (DeepSeek Harness, OpenHarness, LM Studio, Meta-Harness); a β measurement is the only artifact surviving 'why won't this be the fourth?'. E1 (simulation) forces the *form* of the success condition: the closed-form β* is fragile (0.052–0.426 across specification variants) and correlation collapses it false-safe, so v0 must ship a measured number with a CI, not routing gated on the formula. On audience, E2/E3 (stranger-facing) conflict with E4 (Joe-first); I weighted E4 because Joe's hours are the binding constraint, ADR-0015 already mandates dogfooding before public claims, and E1's sample-complexity result (~200 labelled outcomes needed) makes historical mining of Joe's own repo the only viable labelling route at solo volume — so the sequencing is forced, not preferential. Concrete condition: EXP-01 yields β on jobboard-v2 with a decision-relevant CI and retires at least one friction-log item.
OVERTURN: If jobboard-v2's history cannot supply enough labelled accept/reject events for a usable CI (E1: ~200 needed at β≈0.05; even 800 gives only 86% power at β=0.08), the chosen artifact has no measurable success condition on the chosen repo and D2 must be re-decided, likely toward synthetic defect injection or a different first repo.
DISSENT: E4's friction log is the strongest evidence against the decision: what actually bites Joe per session is model-choice-by-feel, context re-explanation, and research-vs-priors-by-feel — none of which a β-meter fixes. The decision may optimise for intellectual defensibility (E2/E3) over documented daily pain (E4); if the friction log stays β-less for a month, v0 should have been boring context/model-routing tooling instead.


===== DECISION D3 (Arm B, ClickUp ticket) =====

--- MSG [D3/B/E1] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- Cascade wins below β ≈ 0.11 (+4.0 pp quality at β=0, 63% of frontier cost); above it, savings buy silent defects (−3.1 pp at β=0.20). [simulated]
- The closed form β* = (1−α)·e^(−kΔ) is fragile: unequal slopes swing β* 0.060–0.226; probit link drops it to 0.052–0.090; a cheap-model guessing floor inflates apparent β* to 0.218–0.426. [algebra + simulated]
- Biggest break: correlated model successes. Copula ρ=0.6 collapses β* from 0.112 to 0.028 and the quality gain from +4.0 pp to +0.9 pp; at ρ=0.9 the advantage is zero. Error direction is false-safe. [simulated]
- Sample complexity: Wilson 95% at true β=0.05 needs n=200 for [0.027, 0.090]; at true β=0.08 even n=800 gives only 86% power near threshold. [algebra]
- β has never been measured on a real repository (EXP-01 not run); everything above is model-world.

**IMPLICATION FOR D3:** The four-gate Inquiry tier is not exercised by any simulation this class holds — nothing here quantifies reversibility, blast radius, or prior dispersion. This class's numbers say the urgent v0 measurement problem is β itself (EXP-01, correlation, per-repo curves), which argues the Inquiry tier is deferrable relative to instrumenting β.

**CONFIDENCE:** Medium — the fragility results are robust within the model, but no result here touches a real repository.

--- MSG [D3/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- Amin (arXiv:2601.01522, read in full) already implements a VOI-gated "spend more before deciding" trigger with a cost-asymmetry threshold — the Inquiry tier's core mechanism has prior art, but it is a single-author preprint on synthetic data, with no verifier and no routing.
- Harness survey (Meng et al., 111 pp): "verifier" appears zero times across 23 surveyed systems; none conditions orchestration on verifier reliability. METR data show maintainer merge rates average 24.2 pp below SWE-bench automated grader scores for the same PRs — the field's gap is measuring β, not research-gating.
- Kim et al. (NMI 2026): single-agent capability best predicts whether coordination helps; multi-agent structures cost 1.6–6.2× tokens at matched performance. Extra deliberation tiers carry a measured cost multiplier.
- Delegation theorem (arXiv:2603.26993): added stages without new exogenous signals cannot beat the centre; relay decay measured 90.7% → 22.5% over 5 stages. An Inquiry tier must name the exogenous signal it introduces.
- 63 documented production budget-overrun incidents (arXiv:2606.04056): budget primitives are literature-urgent; nothing comparable makes research-triggering urgent.

**IMPLICATION FOR D3:** The literature makes β measurement the unoccupied, urgent gap and shows deliberation tiers are costly and partially pre-solved (Amin); nothing in the published record makes the Inquiry tier v0-urgent. Evidence weighs toward deferral, provided any later version names its exogenous signal.

**CONFIDENCE:** medium — sources verified at first hand, but several are unrefereed preprints and two adjacent papers remain unread.

--- MSG [D3/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- The harness layer is taken twice over, MIT-licensed: DeepSeek Harness (13 Aug 2026, ~135k stars in four days) and HKUDS/OpenHarness (14.8k stars, v0.1.9, 43 tools, hooks, subagent teams). Neither has any notion of verifier reliability — the β thesis is untouched.
- No competitor has anything resembling the Inquiry tier's four-gate research trigger; but equally, no market pressure demands it — the meta-harness layer itself is thin (Omnigent, Vercel AI SDK v7 HarnessAgent, SemaClaw) and the category is unclaimed.
- Meta-Harness (Stanford/MIT) is a harness optimiser that needs a trusted oracle — our opening, not our rival. That opening is β measurement, not the Inquiry tier.
- The repeating pattern: "someone already built this, MIT" has been the correct answer three times running (model library, harness, harness optimisation). Any v0 component must survive "why won't this be the fourth?" The Inquiry tier plausibly survives that test; the question is urgency, not novelty.

**IMPLICATION FOR D3:** Landscape evidence says the differentiator competitors lack is verifier-reliability measurement (β), not the Inquiry tier — so deferring Inquiry costs no competitive ground, while it is one of the few components with no MIT-licensed pre-emption risk if kept.

**CONFIDENCE:** medium — star counts and feature lists are concrete, but fork-to-star ratios and unrun EXP-05 mean production-usage signals are weak.

--- MSG [D3/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context

**FINDINGS:**
- The binding constraint is Joe's hours, not money: fully open source by explicit decision, no revenue, donations-only. This argues for a small, sharply-scoped core with a plugin boundary, not a platform.
- The friction log records "decided research-vs-priors by feel, several times per session" — the exact pain the Inquiry-tier trigger addresses. It is one of only four logged frictions.
- Process state (19 Aug 2026): pre-brainstorm, no code, no spec; 24 ADRs mostly one day old with one conflicted reviewer. EXP-01 (measure β on jobboard-v2) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments; everything else queues behind them.
- Falsifier already on record: if the friction log stays short for a month, either Claude Code suffices (a serious finding against the v0 premise) or the log is dishonest.
- Joe's standing preference: full adversarial brainstorm before spec; kill liked ideas when stopping rules say so.

**IMPLICATION FOR D3:** The Inquiry tier answers a real, repeatedly logged friction, but under the hours constraint it queues behind EXP-01/EXP-05 and everything else; constraints evidence favours deferring it from v0 while keeping the friction-log entries as the trigger for revisiting.

**CONFIDENCE:** medium — the friction is documented per session, but scope appetite is a preferential fact only Joe can supply.

--- MSG [D3/B/OWNER] (closing decision) ---
DECISION: The Inquiry tier is deferred from v0; the friction log's "research-vs-priors by feel" entries remain the standing trigger for revisiting it, and any later inclusion must name its exogenous signal.
RATIONALE: Three of four evidence classes converge on deferral from genuinely different facts. E1 (simulation): no simulation exercises the four gates — nothing quantifies reversibility, blast radius, or prior dispersion — while the model-world results (correlated successes collapsing beta* from 0.112 to 0.028, false-safe error direction, EXP-01 unrun) all say the urgent v0 measurement problem is beta itself. E2 (literature): the tier's core mechanism has prior art (Amin's VOI-gated trigger), deliberation tiers cost a measured 1.6-6.2x tokens (Kim et al.), the delegation theorem requires any added stage to name an exogenous signal, and the field's documented gap (verifier reliability, the 24.2 pp merge-rate gap) is beta measurement, not research-gating. E3 (landscape): no competitor has an Inquiry tier but no market pressure demands one; the unclaimed differentiator is beta, so deferring Inquiry costs no competitive ground, and low MIT pre-emption risk makes waiting cheap. The pro-inclusion case rests on E4 alone: the friction log documents the exact pain per session. I weighted the three-class coincidence over the single class — that coincidence is the consilience test — and noted E4 itself concludes the tier queues behind EXP-01/EXP-05 under the hours constraint. Deferral is also the reversible option: the friction log keeps accumulating evidence either way. Overturn condition: if once beta instrumentation exists the four-gate decision measurably moves beta on a real repo, promote immediately; secondarily, a competitor shipping an MIT-licensed research-gating tier flips E3's premise.
OVERTURN: If, once beta instrumentation exists, friction-log research-vs-priors misjudgements prove a first-order driver of accepted-bad-artifact rate (the four gates measurably move beta on a real repo), the tier enters scope immediately; secondarily, an MIT-licensed competitor research-gating tier would flip the "waiting is cheap" premise.
DISSENT: E4 vs E1/E2/E3 is a real conflict, not a nuance: the Inquiry tier addresses the only friction logged as recurring every session, and it is the one distinctive component the thrice-repeated "someone already built this, MIT" pattern does not threaten — we deferred exactly the thing with no pre-emption risk. There is also anchoring risk: every deferral converges v0 on "the beta-meter", the outcome the evidence pipeline was already oriented toward. If the friction log is honest, deferral taxes Joe daily while EXP-01 runs.


===== DECISION D4 (Arm B, ClickUp ticket) =====

--- MSG [D4/B/E1] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- Cascade beats always-frontier below β ≈ 0.11: +4.0 pp quality at β=0 at 63% of frontier cost; above it, −3.1 pp at β=0.20 [simulated].
- Robustness sweep (19 Aug): the closed form β* = (1−α)·e^(−kΔ) is fragile. Correlated model successes (Gaussian copula ρ=0.6) collapse β* from 0.112 to 0.028 and the quality gain from +4.0 pp to +0.9 pp; at ρ=0.9 the advantage is zero. Error direction: false-safe routing.
- Sample complexity: Wilson 95% at true β=0.05 needs n=200 for [0.027, 0.090]; at true β=0.08, even n=800 gives only 86% power near threshold. Historical mining of PR outcomes is the only viable labelling route at solo volumes [algebra].
- Learned router needs ~5,000 trajectories just to match always-cheap-with-escalation — cut from any v0 list [simulated].
- Three-tier depth is nearly free: 43.8% of frontier cost, +4.4 pp at β=0.10. Critic recall ≡ 1 − β: one quantity governs routing, parallelism ceiling (3.1 → 5.1 agents at recall 0.85), and review load [simulated + algebra].

**IMPLICATION FOR D4:** Everything here is model-world; β has never been measured on a real repository (EXP-01 not run), so any v0 that ships routing gated on the closed form ships a false-safe instrument. This class supports v0 = β-meter (measurement first) + simple cascade; cut the learned router; critic tier earns its place via the recall identity.

**CONFIDENCE:** Medium — internally consistent algebra and sweeps, but zero empirical grounding.

--- MSG [D4/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- METR data in the Meng et al. harness survey (111 pp): maintainer merge rates average **24.2 pp below** SWE-bench automated grader scores for the same PRs — ecosystem-scale evidence that automated accept signals over-accept. "Verifier" appears zero times; none of 23 surveyed systems measures verifier reliability.
- Dekoninck et al. (ICML 2025) cascade routing is optimal w.r.t. quality/cost estimators but assumes a **perfect test oracle (β=0)** on SWE-Bench; per-repo false-accept measurement remains unclaimed.
- Meta-Harness (arXiv:2603.28052) has no concept of verifier false-accept rate (real numbers: 76.4% vs 74.7% on TerminalBench-2; our lit review's 28.5%→46.5% figure was fabricated) — the β-meter's novelty stands.
- Kim et al. (NMI 2026): MAS costs **1.6–6.2× tokens at matched performance**; single-agent capability best predicts whether coordination helps — caution on parallel worktrees/critic tier in v0.
- 63 documented production budget-overrun incidents (arXiv:2606.04056): budget primitives are not a v2 feature.

**IMPLICATION FOR D4:** The literature uniquely supports β-meter (unclaimed gap, real over-accept evidence) and budget primitives (documented incident base) for v0; cascade rests on prior art that assumed β=0, and multi-agent components (parallel worktrees, critic tier) carry measured cost multipliers without demonstrated benefit — the strongest cut candidates.

**CONFIDENCE:** High — all sources read in full and verified at source on 19 Aug 2026.

--- MSG [D4/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- The harness layer is taken twice over, free and MIT: DeepSeek Harness (13 Aug 2026, ~135k stars in four days) and HKUDS/OpenHarness (14.8k stars, v0.1.9, 43 tools, hooks, subagent teams, worktree tool, cron). Caveats: OpenHarness's last release was 7 May, 114 tests, 16% fork-to-star ratio.
- Neither has any notion of verifier reliability — no measurement of whether automated checks can be trusted, no routing derived from it. The β thesis is untouched.
- Parallel worktrees and cascade-adjacent orchestration already exist MIT-licensed (OpenHarness worktree tool; ohmo credential bridging on existing Claude Code/Codex subscriptions).
- The pattern "someone already built this, MIT-licensed" has been the correct answer three times running: model library → LM Studio/LLM Checker; harness → DeepSeek/OpenHarness; harness optimisation → Meta-Harness (Stanford/MIT).
- Orchestratees are four independently evolving surfaces (Claude Code, Codex CLI, opencode ~195k stars, Antigravity CLI) — a permanent adapter tax with no ceiling. EXP-05 (adapter breakage test, one-day budget) is registered and unrun.

**IMPLICATION FOR D4:** Every v0 candidate except the β-meter has an existing MIT-licensed answer or carries unbounded adapter tax; the β-meter is the only component the landscape leaves genuinely unbuilt. Cut anything that fails "why won't this be the fourth?"

**CONFIDENCE:** high — these are observable market facts (repos, licences, star counts), though star counts may overstate production usage.

--- MSG [D4/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context
**FINDINGS:**
- Economics: fully OSS by explicit user decision (donations only, no revenue, no hosted service). Binding constraint is Joe's hours, not money — argues for a small, sharply-scoped core with a plugin boundary, not a platform.
- Process state (19 Aug 2026): pre-brainstorm, no code, no spec; 24 ADRs mostly one day old with one conflicted reviewer. EXP-01 (measure β on jobboard-v2 history) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments; everything queues behind them.
- Friction log: what actually bit per session — model chosen by feel (→ cascade + β-meter), context re-explained (→ memory wake-up), research-vs-priors by feel (→ Inquiry trigger), prior art missed three times. The β-meter and cascade map directly to logged friction; critic tier and budget primitives do not appear in the log.
- Prior-repo lesson (jobboard-v2, 991 commits/36 days): ~20 CI ratchets, 44 invariant probes — a low-β repo that flatters cascading; a weakly-verified contrast repo (hireable-3.0) is mandatory for any β claim.
- Dogfooding gate (ADR-0015) plus bootstrap harness (ADR-0017) already exist — v0 need only beat Claude Code + Graphify + MemPalace for Joe's own week.

**IMPLICATION FOR D4:** The candidate list exceeds what a solo, donation-funded builder's friction log justifies; evidence supports β-meter + cascade first, with worktrees/budget/critic cut or deferred until the friction log demands them.
**CONFIDENCE:** high — these are documented constraints and Joe's own stated preferences, not simulations.

--- MSG [D4/B/OWNER] (closing decision) ---
DECISION: PROVISIONAL (parked on Joe's reply per ADR-0020 §3): v0 = β-meter + simple two-tier cascade; cut parallel worktrees, critic tier, and learned router; budget primitives deferred pending Joe's stated weekly hours and scope appetite.
RATIONALE: Three classes converge independently on the β-meter as the irreducible v0 core. E1 (simulation): the closed-form threshold β* is fragile — correlated model successes at ρ=0.6 collapse β* from 0.112 to 0.028 with false-safe error direction — so routing shipped before β is measured on a real repo is a broken instrument; measurement first. E2 (literature): maintainer merge rates run 24.2 pp below automated grader scores and none of 23 surveyed systems measures verifier reliability — a real, unclaimed gap. E3 (landscape): every other candidate has an MIT-licensed incumbent (OpenHarness worktrees, ohmo orchestration, DeepSeek Harness); the β-meter is the only genuinely unbuilt component. E4 (constraints): Joe's friction log names model-chosen-by-feel, which β-meter + cascade answer directly; critic tier and budget primitives never appear in the log, and the binding constraint is solo hours, not money. Where classes conflicted: on budget primitives I weighted E4 over E2 (E2's 63 documented overrun incidents are ecosystem facts, but a solo OSS v0 should scope to this project's logged pain — so deferred to Joe rather than cut outright, since his preferential facts are the missing evidence class). On the critic tier I weighted E2+E4 over E1: the recall≡1−β identity is elegant but empirically ungrounded algebra, while MAS cost multipliers of 1.6–6.2× at matched performance are measured. Cascade survives only in its simplest form because E1 shows a learned router needs ~5,000 trajectories just to match always-cheap-with-escalation — unreachable at solo volumes.
OVERTURN: EXP-01 measuring β on jobboard-v2 (with the hireable-3.0 weakly-verified contrast repo) returning β well above ~0.11 would make the cascade unsafe and collapse v0 to β-meter alone; conversely, Joe declaring a substantially larger weekly time budget would re-open budget primitives and the critic tier.
DISSENT: E1's recall≡1−β identity argues the critic tier is not an extra component but the same quantity as β seen from the routing side — cutting it may force rebuilding it the moment the β-meter works. Sharper: E2's 63 documented production budget-overrun incidents are exactly the external, different-class evidence CONSILIENCE.md says to privilege, and my deferral of budget primitives weights Joe's local friction log (anecdote) over ecosystem-scale data — the opposite of the project's declared epistemics. That conflict is real and I resolved it by deference to the missing preferential-facts class, not by evidence.


===== DECISION D5 (Arm B, ClickUp ticket) =====

--- MSG [D5/B/E1 — simulation & algebra] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- Cascade (cheap → verify → escalate) beats always-frontier below β ≈ 0.11: +4.0 pp quality at β=0 for 63% of frontier cost; above it, −3.1 pp at β=0.20 [simulated].
- The closed form β* = (1−α)·e^(−kΔ) is fragile: unequal slopes swing β* 0.060–0.226; probit link drops it to 0.052–0.090; a g=0.10 guessing floor inflates apparent β* to 0.218–0.426 [simulated].
- Correlated model successes are the big one: Gaussian copula ρ=0.6 collapses β* from 0.112 to 0.028 and the β=0 quality gain from +4.0 pp to +0.9 pp; at ρ=0.9 the advantage is zero. The closed form OVERSTATES the safe threshold — false-safe routing [simulated].
- Three-tier depth (cheap → mid → frontier) at β=0.10: 43.8% of frontier cost, +4.4 pp quality. Depth is nearly free — build the ladder, not the switch [simulated].
- β has NEVER been measured on a real repository (EXP-01 not run); everything above is model-world.

**IMPLICATION FOR D5:** The cascade needs *a* cheap tier, and the three-tier result says ladder depth is where the value is — not where the cheap tier physically runs. Nothing in this class distinguishes a local model from a cheap API model, so simulation evidence does not justify building a hardware-gated local-model library in v0.

**CONFIDENCE:** medium — results are internally consistent but entirely simulated, and the robustness sweep shows the key threshold is assumption-sensitive.

--- MSG [D5/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- Cascade routing (Dekoninck et al., ICML 2025) already solves optimal routing given quality/cost estimators — but on SWE-Bench it assumes the test oracle is perfect (β=0 by assumption). A cheap tier per se is solved prior art; β-conditioned tiering is not.
- Relay decay is real and severe: gpt-4.1-mini 90.7% → 41.2% at 2 delegation stages → 22.5% at 5 (below chance; arXiv:2603.26993). Every extra tier is a delegation stage; a weak local tier compounds this. Structured posterior relay loses ~2.8 pts/stage vs ~8.5 for prose.
- Kim et al. (NMI 2026): single-agent capability is the best predictor of whether coordination helps; multi-agent setups cost 1.6–6.2x tokens at matched performance. A weak local model in the loop is the exact failure profile.
- METR data (Meng et al. survey): maintainer merge rates average 24.2 pp below SWE-bench automated grader scores — cheap-tier output accepted by automated checks over-accepts; the cheap tier raises β load, whoever serves it.
- 63 documented production budget-overrun incidents (arXiv:2606.04056): the cost-control motivation for a cheap tier is empirically grounded — but nothing in the literature requires that tier to be locally hosted.

**IMPLICATION FOR D5:** The literature supports needing *a* cheap tier and measuring its acceptance error; it offers no evidence that local hosting or a discovery library adds anything a cheap API model lacks. Out or wrapped at v0 is the literature-consistent position.

**CONFIDENCE:** High — all five sources read in full and verified at source on 19 Aug 2026.

--- MSG [D5/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- The "someone already built this, MIT-licensed" pattern has been the correct answer three times running: model library → LM Studio/LLM Checker; harness → DeepSeek Harness/OpenHarness; harness optimisation → Meta-Harness (Stanford/MIT). Any v0 component must survive "why won't this be the fourth?" — a local model library is the component that already lost that question once.
- LM Studio et al. already occupy local-model discovery; wrapping is explicitly on the table in the D5 brief and the landscape shows no gap justifying a rebuild.
- DeepSeek Harness (13 Aug 2026, MIT, ~135k stars in four days) orchestrates models, not agents — the model-management layer is crowded and moving fast.
- OpenHarness (MIT, 14.8k stars, v0.1.9) plus ohmo already do credential bridging onto existing Claude Code/Codex subscriptions — cheap-tier access via existing surfaces exists off the shelf.
- What is NOT taken: verifier reliability (β). No competitor touches it. Every hour on a cross-platform model library is an hour off the only unclaimed layer.

**IMPLICATION FOR D5:** The landscape says out or wrapped: local-model discovery is a solved, crowded space, while the β thesis is the only uncontested ground — v0 effort should go there, with the cascade's cheap tier satisfied by a cheap API model or an LM Studio wrap.

**CONFIDENCE:** High that the space is occupied (three verified MIT precedents); medium on wrap-vs-out, which depends on cascade requirements my class does not hold.

--- MSG [D5/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context

**FINDINGS:**
- Economics: fully open source by explicit user decision, no revenue, no hosted service. The binding constraint is Joe's hours, not money — arguing for a small, sharply-scoped core with a plugin boundary, not a platform.
- Hardware: an RTX 5090 / 64 GB rig is available and licences purchasable on request. Local compute is free and is what upgrades claims from [simulated] to [measured] (working principle 8).
- Friction log: model was chosen by feel with no measurement on every task — the cascade needs *a* cheap tier, but the logged pain is absence of measurement, not absence of local models.
- Process state (19 Aug 2026): pre-brainstorm, no code, no spec; EXP-01 and EXP-05 are the two highest-information unrun experiments and everything else queues behind them.
- Prior-repo lesson (jobboard-v2, 991 commits/36 days): a documented chokepoint without an enforcement check fragmented into five access paths — any v0 feature that adds surface without its check adds risk.

**IMPLICATION FOR D5:** The hardware makes a local tier *cheap to try*, but the hours constraint and the small-core economics argue against building cross-platform model discovery in v0 — wrapping an existing runtime (LM Studio et al.) or a cheap API model fits the constraint class better. The rig's real v0 job is running experiments (EXP-01/05), not shipping a model library.

**CONFIDENCE:** high — these are documented project facts and explicit user decisions, not inferences.

--- MSG [D5/B/OWNER] (closing decision) ---
DECISION: The local model library is out of v0: the cascade's cheap tier ships as a cheap API model, with a thin wrap of an existing local runtime (LM Studio et al.) admitted later only if EXP-01/05 measurements show the API tier failing on cost or beta.
RATIONALE: All four evidence classes converge by different routes. E1 (simulation): the cascade's value is ladder depth (three tiers give 43.8% of frontier cost, +4.4 pp at beta=0.10), and nothing in the algebra distinguishes local from API hosting — simulation cannot justify a hardware-gated library. E2 (literature): cheap-tier routing is solved prior art (Dekoninck et al., ICML 2025); the unsolved part is beta-conditioned tiering, and no source requires local hosting. Relay decay and the METR merge-rate gap show a weak cheap tier raises beta load regardless of host — the scarce work is measurement, not provisioning. E3 (landscape): local-model discovery is crowded, MIT-licensed ground (LM Studio, DeepSeek Harness, OpenHarness/ohmo) and has been the 'someone already built it' answer three times; verifier reliability is the only unclaimed layer. E4 (constraints): Joe's hours are binding; the RTX 5090's v0 job is running EXP-01/05, not shipping cross-platform discovery; the logged pain is absence of measurement, not absence of local models. Where classes tension — principle 8's 'run it, don't reason' pulling toward using the rig vs the hours constraint — I weighted E4: the rig gets used for experiments, the cheapest path from [simulated] to [measured]. E1's correlation result cuts both ways and is carried as dissent rather than smoothed into the rationale.
OVERTURN: EXP-01 measuring beta on a real repository and finding available cheap API models above the correlation-corrected beta* threshold while a local model on the rig sits below it — i.e. local hosting changes the routing answer, not just the bill.
DISSENT: Two real objections. (1) E1's copula result is the strongest case FOR local models: cheap API models often share provider lineage with the frontier tier, and correlated successes collapse the cascade's advantage (beta* 0.112 -> 0.028 at rho=0.6). A local open-weights model is plausibly the less-correlated cheap tier — Whewell's 'different class of facts' — and this decision forgoes that without ever measuring rho. (2) All four evidence classes derive from documents written in one session of one repo; their agreement is weaker consilience than it looks (partial echo risk), and E1 is entirely model-world since beta has never been measured. If EXP-01 never runs, the decision rests on convergent assertion.


===== DECISION D6 (Arm B, ClickUp ticket) =====

--- MSG [D6/B/E1] (evidence comment) ---
**CLASS:** E1 — simulation & algebra

**FINDINGS:**
- The mechanism D6 would ratchet is real: closed form β* = (1−α)·e^(−kΔ) exists and simulations show sign flips matter — cascade wins below β* ≈ 0.11 (+4.0 pp quality at β=0, 63% of frontier cost) and loses above it (−3.1 pp at β=0.20). A sign-flip check is exactly what our models produce. [algebra + simulated]
- But the robustness sweep (19 Aug 2026, robustness_beta_star.py) shows the model's VALUE is fragile: unequal slopes move β* across 0.060–0.226; probit link drops it to 0.052–0.090; guessing floor g=0.10 inflates apparent β* to 0.218–0.426. [simulated]
- Worst case: correlated model successes (copula ρ=0.6) collapse β* from 0.112 to 0.028 and quality gain from +4.0 pp to +0.9 pp; at ρ=0.9 the advantage is zero. Direction of error is false-safe. [simulated]
- Re-running a decision model in CI only signals if its inputs are measured; β has never been measured on a real repository (EXP-01 not run). Wilson intervals say 50–200 accepted diffs only suffice when β is far from β*. [algebra]

**IMPLICATION FOR D6:** Our own results are a live demonstration of the ratchet's value at sign/threshold granularity — the sweep flipped conclusions within 24 hours of the closed form being written. But a CI ratchet re-running an unmeasured model just re-asserts its assumptions; it earns its cost only once EXP-01-style measured inputs feed it.

**CONFIDENCE:** Medium — mechanism is demonstrated in-repo, but everything is model-world, nothing measured.

--- MSG [D6/B/E2] (evidence comment) ---
**CLASS:** E2 — verified external literature

**FINDINGS:**
- The self-improvement line (DGM 20→50 on SWE-bench, SICA 17→53) all accept self-modifications on an UNMEASURED acceptance signal; Huxley-Gödel independently rejects benchmark-score-as-capacity. The literature has no mechanism that re-checks whether a past accept still holds — the gate D6 proposes is an unclaimed spot (ADR-0018's opening).
- METR data (via Meng et al. survey, 111 pp): maintainer merge rates average 24.2 pp BELOW SWE-bench automated grader scores on the same PRs — ecosystem-scale evidence that accepted decisions drift from ground truth after the fact. Their only remedy is human-in-the-loop; nobody re-runs the decision.
- Meta-Harness (arXiv:2603.28052) trusts a static external benchmark score and handles eval-gaming by manual inspection + regex audits — no automated re-verification of the decision basis. (Caution: our lit review carried a fabricated figure for this paper; real result 76.4% vs 74.7% on TerminalBench-2.)
- Dekoninck et al. (ICML 2025) estimate estimator variance per deployment from validation data, but assume the test oracle is perfect (β=0) and derive no threshold at which the decision flips — no prior art for sign-flip-gated CI.

**IMPLICATION FOR D6:** The literature contains no existing mechanism that re-runs a decision model and fails on a sign flip; the closest systems either trust a frozen oracle or fall back to humans. The ratchet is genuinely novel, not redundant — the ceremony/maintenance question is ours alone to answer empirically (EXP-10).

**CONFIDENCE:** medium — strong on novelty (papers read in full), but no literature speaks to the maintenance-cost side.

--- MSG [D6/B/E3] (evidence comment) ---
**CLASS:** E3 — competitive landscape

**FINDINGS:**
- The exact mechanism D6 proposes (runnable decision model re-run in CI, fail on sign flip) appears nowhere in the landscape: DeepSeek Harness (MIT, ~135k stars in 4 days), OpenHarness (MIT, 14.8k stars, v0.1.9, 43 tools, 114 tests), Omnigent, SemaClaw, Vercel HarnessAgent — none have any notion of verifier or decision-model reliability.
- OpenHarness explicitly lacks verifier-reliability measurement or routing derived from it; the β thesis, of which the CI ratchet is an expression, is untouched by incumbents.
- Meta-Harness (Stanford/MIT) optimises harnesses but needs a trusted oracle — a decision-ratchet mechanism is complementary to it, not competing.
- Counter-pattern: "someone already built this, MIT-licensed" has been the correct answer three times running (model library → LM Studio; harness → DeepSeek/OpenHarness; harness optimisation → Meta-Harness). D6 must survive "why won't this be the fourth?" — currently it does, but only on absence of evidence.
- Maintenance-tax analogue: four orchestratee CLIs (Claude Code, Codex, opencode ~195k stars, Antigravity) evolve independently — ADR-0001's own "permanent adapter tax with no ceiling" warning generalises to any CI mechanism carrying live dependencies.

**IMPLICATION FOR D6:** No incumbent occupies this ground, so the ratchet is genuinely differentiating rather than duplicative — but the repeating "already built, MIT" pattern says re-check before shipping, and the adapter-tax evidence supports the dependency-rot cost concern.

**CONFIDENCE:** medium — differentiation rests on absence of evidence in a fast-moving landscape.

--- MSG [D6/B/E4] (evidence comment) ---
**CLASS:** E4 — project constraints & user context

**FINDINGS:**
- Binding constraint is Joe's hours, not money: fully open source by explicit user decision, no revenue, no hosted service. This argues for a small, sharply-scoped core, not extra machinery.
- Prior-repo lesson (jobboard-v2, 991 commits/36 days): a documented "unified LLM boundary" fragmented into five access paths because no lint rule banned bypass → invariant I1: any chokepoint ships with its enforcement check in the same commit. The ratchet proposal is the same species — a declared invariant plus its check.
- jobboard-v2 already carries ~20 CI ratchets and 44 invariant probes, so the pattern is proven affordable in a solo repo; but dependency rot is a real maintenance tax paid in the scarce resource (hours).
- Process state (19 Aug 2026): pre-brainstorm, no code, 24 ADRs mostly one day old with one conflicted reviewer; EXP-01 and EXP-05 are the highest-information unrun experiments and everything else queues behind them. EXP-10 (three-month measurement of the ratchet) is downstream.
- User's standing preferences: supersede ADRs, never silently edit; stopping rules applied honestly even when they kill liked decisions.

**IMPLICATION FOR D6:** The mechanism fits invariant I1 and the Engineering Ratchet principle, but an hours-bound solo project queued behind EXP-01/05 cannot yet afford a new CI surface with dependency-rot upkeep; constraints favour deferring the executable-model ratchet until EXP-10 can measure it.

**CONFIDENCE:** high — every finding is a stated fact in the project constraints pack, not inference.

--- MSG [D6/B/OWNER] (closing decision) ---
DECISION: Drop the executable-model CI ratchet from v0: ADRs keep shipping runnable decision models as scripts, with CI wiring deferred until EXP-01 provides measured inputs and EXP-10 measures the maintenance cost.
RATIONALE: Two independent classes converge on deferral. E1 (simulation/algebra): a CI gate re-running a model whose inputs are entirely [simulated] just re-asserts assumptions — β has never been measured on a real repo, and the robustness sweep moves β* across 0.03–0.43 under plausible perturbations (unequal slopes, probit link, guessing floor, correlated successes), so a sign-flip check currently gates on noise. E4 (constraints): Joe's hours are the binding resource, EXP-01/05 queue ahead of everything, and any CI surface carries dependency-rot upkeep paid in that resource. E2 (literature) and E3 (landscape) both establish the mechanism is genuinely novel — no prior art re-runs a decision and fails on a sign flip, no incumbent occupies the ground — which is why the mechanism is kept (runnable models per ADR, near-zero cost, already exist in-repo) rather than killed. Where classes conflict (E2/E3 "unclaimed, move now" vs E1/E4 "unmeasured, unaffordable now"), I weighted E1/E4: E1's objection is disqualifying (a ratchet on unmeasured inputs produces confident noise, the failure mode Consilience exists to prevent), while E2/E3's novelty rests partly on absence of evidence in a fast-moving field, per E3's own confidence caveat. E1 also supplies live in-repo proof of the ratchet's eventual value: the sweep flipped a 24-hour-old conclusion at sign/threshold granularity — value preserved by keeping the models runnable without CI enforcement.
OVERTURN: EXP-01 measuring β on a real repository with Wilson intervals tight enough that the decision model's sign is stable under the E1 robustness perturbations — measured inputs existing flips the deferral immediately.
DISSENT: The repo's own Engineering Ratchet principle and invariant I1 (E4) say a declared invariant without its enforcing check in the same commit is exactly how jobboard-v2's chokepoint fragmented into five bypass paths; deferring CI enforcement declares "ADRs carry runnable models" as an invariant with no check — the documented most-expensive prior-repo failure — and E4 also shows ~20 CI ratchets were already affordable in a solo repo. If the pattern rots before EXP-01 runs, this decision caused it.
