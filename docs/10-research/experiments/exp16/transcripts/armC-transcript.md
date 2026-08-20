

===== DECISION D1 (Arm C, free-form Slack thread) =====

--- MSG [D1/C/facilitator/r0] ---
**[ARM C · D1]** Should the β-meter ship as a plugin to HKUDS/OpenHarness, or as the standalone meta-harness ADR-0001 commits to?
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D1/C/E1/r1] ---
E1 here (simulation/algebra). From where I sit, the numbers argue *against* standalone-first. Our robustness sweep (19 Aug) showed the closed form β* = (1−α)e^(−kΔ) is a knife-edge: unequal slopes swing it 0.060–0.226, and correlated model successes (ρ=0.6 — realistic, models share training data) collapse it from 0.112 to 0.028 and wipe most of the quality gain. Direction of error is false-safe. So the one thing we must NOT ship yet is routing gated on the closed form — and a standalone meta-harness is exactly that commitment.

What β needs first is data: it's a binomial proportion over accepted diffs, and Wilson intervals say 50–200 diffs only settle it when you're far from threshold. A plugin riding an existing harness gets us accepted-diff volume and real per-repo curves fastest — that's EXP-01, which has never run. Everything I hold is model-world until then.

So my vote: whichever packaging gets β *measured* soonest wins. If OpenHarness gives us the diff stream cheaply, plugin first, standalone later if the measurements justify it. I can't speak to OpenHarness's API stability — that's E3/E4's evidence, and I'd weight it heavily.

--- MSG [D1/C/E2/r1] ---
E2 (literature). The published field backs E1's direction, with two additions.

First, the gap is real and nobody occupies it: I read Meta-Harness in full — it optimises harness code against a benchmark score it *trusts*; no concept of verifier false-accept rate. Meng et al.'s 111-page harness survey: the word "verifier" appears zero times across 23 systems. Dekoninck's cascade routing assumes β=0 on SWE-Bench by construction. So β-measurement is genuinely unclaimed — but the novelty is the *measurement*, not the harness packaging. A plugin loses none of it.

Second, ecosystem evidence β matters: METR data in the survey shows maintainer merge rates average 24.2pp *below* automated grader scores on the same PRs. Automated accept signals over-accept at scale; nobody measures the rate per repo. That's our claim, and it needs exactly what E1 says — accepted-diff volume.

One caution: our own lit review carried a fabricated Meta-Harness figure (the 19-task 28.5%→46.5% run doesn't exist) and it passed review. Our internal docs are not fully trustworthy — another reason to prefer the packaging that produces external, measured data soonest. Plugin first; standalone only if measurements justify ADR-0001.

--- MSG [D1/C/E3/r1] ---
E3 (landscape). I lean the same way, with market facts and two caveats.

For plugin: the harness layer is taken twice over — DeepSeek Harness (~135k stars in four days, MIT) and OpenHarness itself (14.8k stars, MIT). OpenHarness has exactly the surface a β-meter needs: PreToolUse/PostToolUse hooks to observe verifier invocations and outcomes, plugin system, tool registry, existing users. And it has *no* notion of verifier reliability — the β thesis is untouched. Plugin starts at a nonzero audience; standalone starts at zero, plus a permanent adapter tax across four independently evolving CLIs (ADR-0001's own "evidence against"). Also: "someone already built it, MIT-licensed" has been the correct answer three times running — model library, harness, harness optimisation. A standalone meta-harness should answer why it won't be the fourth.

Caveats: OpenHarness is v0.1.x (last release 7 May, 114 tests, 16% fork-to-star suggests reach not production use) — we'd bind to an unstable surface and another team's roadmap. And the name collision poisons anything nearby.

So: plugin first as the β-measurement vehicle, keep the meter's core harness-agnostic so it can eject if OpenHarness stalls. E4 — does the constraint side veto binding to v0.1.x?

--- MSG [D1/C/E4/r1] ---
E4 (constraints). No veto — the constraint side actively agrees, on three facts nobody else holds.

Economics: this is fully open source by Joe's explicit decision — donations, no hosted service, no revenue. The binding constraint is Joe's hours, not money. A standalone meta-harness plus a permanent adapter tax across four evolving CLIs is a platform commitment a solo founder on donations cannot service. Small core behind a plugin boundary is the only shape that fits.

Process state: ADR-0001 is one day old with one reviewer who had a declared conflict of interest, and E2 just showed our internal docs passed a fabricated figure. That ADR carries almost no evidential weight. Also EXP-01 (measure β on jobboard-v2 history) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments — and note EXP-01 needs no OpenHarness at all: the diff history exists locally, RTX 5090 rig ready. So don't bind before measuring; run EXP-01 now, spend EXP-05's one day probing OpenHarness's hook surface, and E3's v0.1.x worry becomes a measured answer, not a guess.

One warning: jobboard-v2 is a low-β repo — measuring only there flatters the thesis. hireable-3.0 as contrast repo is mandatory. And per Joe's standing rule: supersede ADR-0001, never silently edit it.

--- MSG [D1/C/E1/r2] ---
E1 again — we're converged, so let me just calibrate expectations for EXP-01 before we close.

One quantitative caveat on the two-repo plan: β is a binomial proportion, and Wilson intervals are wide at repo-history volumes. At true β=0.05, n=50 accepted diffs gives [0.011, 0.135] — that interval straddles most plausible β* values. Even n=800 only reaches 86% power near threshold. So EXP-01 on jobboard-v2 + hireable-3.0 will deliver a *sign and a contrast* (do the two repos differ, is either clearly above/below threshold), not a precise number. That's still the highest-information thing we can run, but nobody should expect it to license routing on its own — especially since the robustness sweep says β* itself moves 4x under realistic model correlation.

So the decision as I'd record it: plugin on OpenHarness as the β-measurement vehicle, harness-agnostic core (E3's eject clause), EXP-01 + EXP-05 before any binding, ADR-0001 superseded not edited. All four classes point the same way on genuinely different evidence — Whewell would call that consilience rather than echo, which is about the strongest verdict this group can produce. I'm done unless Joe objects.

--- MSG [D1/C/E2/r2] ---
E2, final note. I agree with E1's record and won't relitigate it. Two riders for the written decision, both from the literature side.

First, the "unclaimed gap" claim I made carries an asterisk: two adjacent papers surfaced during verification that I have _not_ read — EvoTrainer (arXiv:2606.03108) and "Adapting the Interface, Not the Model" (arXiv:2605.22166). Novelty isn't fully established until someone reads them. Cheap task, should be a named condition in the record, not folded silently into "novelty checked".

Second, a supporting point for the plugin-with-eject shape: under the delegation theorem's own formalism (Corollary 9), verifiers that actually run tests count as _exogenous_ signals — so a β-meter observing OpenHarness's verifier outcomes is adding a genuinely new signal class, not echoing the harness's beliefs. The theory is compatible with the packaging we've chosen; it's the closed-form routing E1 warned about that isn't licensed yet.

With those two lines in the record, I'm done.

--- MSG [D1/C/E3/r2] ---
E3, closing rider — I agree with E1's record. Two landscape facts for the written decision, neither yet in the thread.

First, the eject clause is not a retreat to nowhere: the meta-harness layer above the harnesses is thin but real — Omnigent (Databricks, Apache 2.0) exists but the category is unclaimed, and Meta-Harness itself _needs_ a trusted oracle to optimise against, which makes a measured β a complement to it, not a competitor. So "plugin now, standalone later if measurements justify" has a live upstream market, and the eject path stays credible.

Second, a concrete action item: "Consilience" was chosen (ADR-0008) but trademark clearance has not run and npm/PyPI/crates names are unreserved. If we're publishing a plugin into OpenHarness's ecosystem, the name ships with it — reserve the package names before the plugin lands, and keep the name well clear of "OpenHarness"/"OH", which are all taken. Cheap, hours not days, and irreversible if someone else grabs it first.

With those two lines in the record, I'm done.

--- MSG [D1/C/E4/r2] ---
E4, one last constraint fact for the record — it sharpens the "harness-agnostic core" clause from a nice-to-have into a requirement. The dogfooding gate (ADR-0015) says Consilience must be used to build Consilience, and the bootstrap harness (ADR-0017) is *Claude Code* — Graphify + MemPalace, git-hook updates — not OpenHarness. So our first live β observations will come off Claude Code hooks regardless of where the public plugin ships. That means the meter's core must be host-neutral from day one, not "eventually ejectable": OpenHarness plugin and Claude Code bootstrap are two thin shims over the same core, or the dogfooding gate and the packaging decision contradict each other.

Also worth a line in the record: the friction log carries a falsification clause — if it stays short for a month, Claude Code alone may already suffice, which would kill the standalone ambition entirely. The plugin path keeps that outcome cheap.

Otherwise I endorse E1's record as written, plus E2's two riders and E3's name-reservation item. Done.


===== DECISION D2 (Arm C, free-form Slack thread) =====

--- MSG [D2/C/facilitator/r0] ---
**[ARM C · D2]** What is v0's success condition — smallest thing worth a stranger's npm install vs smallest thing that makes Joe's week better; same artifact or not; which is being built?
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D2/C/E1/r1] ---
Opening position from the numbers side: v0 has to be "makes Joe's week better", and specifically it has to be EXP-01 — measure β on a real repo. Here's why the stranger-first framing is premature: every quantitative result we have is model-world. The closed form β* = (1−α)e^(−kΔ) looked distribution-free, but yesterday's robustness sweep broke it four ways — worst case, correlated model successes (Gaussian copula ρ=0.6) collapse β* from 0.112 to 0.028 and wipe out most of the quality gain. Direction of error is false-safe: the formula overstates the safe threshold. So a v0 that ships routing to strangers, gated on this maths before β has ever met a real repository, is shipping a false-safe instrument with an npm install command attached. The measurement itself is also cheap-ish at solo volumes: Wilson intervals say 50–200 accepted diffs only settle β when it's far from threshold, and historical mining of Joe's own PR/revert history is the only viable labelling route. That's inherently a Joe-week artifact. Same artifact later, maybe — the measurement harness generalises. But which is being built first: Joe's instrument. The stranger version before EXP-01 would be malpractice.

--- MSG [D2/C/E2/r1] ---
Literature side: I agree with E1's conclusion, and the published record makes it stronger than the simulations do. The METR data in Meng et al.'s survey shows maintainer merge rates averaging 24.2pp *below* SWE-bench automated grader scores for the same PRs — ecosystem-scale proof that automated accept signals over-accept. But nobody measures that rate *per repo*. That per-repo measurement is our actual novelty: Meta-Harness (the supposed threat) optimises harness code against a benchmark score it trusts blindly — no concept of verifier false-accept rate. Dekoninck's cascade routing assumes β=0 on SWE-Bench by construction. The gap is real, and it's a *measurement* gap, not a tooling gap.

So the stranger-npm-install framing has it backwards: a stranger has nothing to install until β has met one real repository. EXP-01 on Joe's PR/revert history is simultaneously the Joe-week artifact and the first datapoint the field lacks. Same artifact eventually, but the sequencing is forced.

One caution: our own lit review carried a fabricated Meta-Harness figure that passed review — a live demonstration of β in our own process. Build the instrument first.

--- MSG [D2/C/E3/r1] ---
Landscape view: I agree with the sequencing, and the market makes it non-optional. Everything a stranger might npm install already exists, MIT-licensed: DeepSeek Harness (~135k stars in four days) and OpenHarness (43 tools, hooks, MCP, subagent teams, plus ohmo running on existing Claude Code/Codex subscriptions). "Someone already built this" has been the correct answer three times running — model library, harness, harness optimisation. A stranger-facing v0 has to survive "why won't this be the fourth?", and right now it can't. But the one thing NOBODY has is exactly E2's gap: no notion of verifier reliability anywhere in the landscape. OpenHarness has zero concept of it; Meta-Harness needs a trusted oracle — that's our opening, not our rival. So: build Joe's instrument (EXP-01). Two landscape caveats. First, when the stranger version does come, consider shipping the β-meter as an OpenHarness plugin — its PreToolUse/PostToolUse hooks are precisely the surface a β-meter needs to observe verifier outcomes, and it starts at a nonzero audience. Risky (v0.1.x, another team's roadmap) but recorded as live in ADR-0001. Second, housekeeping: "Consilience" has no trademark clearance and no npm/PyPI reservations yet — cheap to fix now, before any artifact exists.

--- MSG [D2/C/E4/r1] ---
Constraints side: unanimous so far, and the economics close the argument. This is fully open source by Joe's explicit decision — no hosted service, no telemetry, no revenue. Nobody funds a stranger-facing platform on a donate button; the binding constraint is Joe's hours. "Worth a stranger's npm install" was never a viable v0 success condition for a solo founder regardless of the science.

So: Joe's instrument, and EXP-01 is already queued as the highest-information unrun experiment, with ADR-0002/0009 provisional pending exactly it. The dogfooding gate (ADR-0015) makes this the official sequencing anyway — Consilience builds Consilience, measured gates before any public claim.

Two constraints the consensus should absorb:

1. jobboard-v2 is a LOW-β repo — ~20 CI ratchets, 44 invariant probes, coverage floors. That's the regime where cascading looks best. EXP-01 there alone flatters the thesis; the weakly-verified contrast repo (hireable-3.0) is mandatory, not optional.

2. Success condition should be falsifiable against the friction log: if a month of dogfooding leaves the log short, Claude Code already suffices and that's a serious finding against the whole v0 premise. "Makes Joe's week better" must be allowed to come back false.

E3's name/npm reservation point: cheap, do it now.

--- MSG [D2/C/E1/r2] ---
Consensus holds, so let me just make the success condition operational, because "measure β" hides two traps.

1. EXP-01 must measure *two* quantities, not one: β̂ per repo AND the cheap/frontier success correlation ρ. The sweep shows ρ=0.6 alone collapses β* from 0.112 to 0.028 — a clean β̂ with unmeasured ρ is still a false-safe instrument. Historical mining gives both from the same PR/revert data if we log which model touched what.

2. Sample-size honesty in the success condition. Wilson at true β=0.05: n=200 gives [0.027, 0.090] — enough for a sign/threshold verdict, nowhere near a point estimate. And near threshold we're underpowered even at n=800 (86% at β=0.08). So E4's two-repo contrast works precisely *because* it's a sign test: jobboard-v2 vs hireable-3.0 should differ by enough that solo-volume n resolves it. If it doesn't, that itself is a finding.

Proposed wording: *v0 succeeds iff EXP-01 yields β̂ and ρ̂ with Wilson bounds on both repos, and a month of dogfooding produces a non-empty friction log.* Falsifiable both ways, Joe-week artifact, and it's the dataset a stranger version would need anyway.

--- MSG [D2/C/E2/r2] ---
E1's wording works for me — one amendment and one flag from the published record.

Amendment: the labelling step needs its own audit. Our fabricated Meta-Harness figure passed our review; the self-improvement literature (DGM, SICA) shows systems happily accepting modifications on an unmeasured acceptance signal. PR/revert mining is itself an acceptance signal — a revert isn't always "bad artifact" (perf rollbacks, dependency churn), and a non-reverted merge isn't always "good". If the labels are noisy, we've built a β-meter with its own unmeasured β. So add to the success condition: *a hand-audited sample of the mined labels (even n=30) with an error rate reported alongside β̂ and ρ̂.* Cheap, and it's exactly the discipline nobody in the 23 surveyed systems applies.

Flag: two adjacent papers surfaced during verification remain unread (EvoTrainer 2606.03108, "Adapting the Interface, Not the Model" 2605.22166). The novelty claim is solid against everything read in full, but the record should say "pending those two", not "established".

Otherwise: consensus. Joe's instrument, EXP-01 on both repos, falsifiable both ways.

--- MSG [D2/C/E3/r2] SKIPPED (passed) ---

--- MSG [D2/C/E4/r2] ---
Consensus stands and E1's wording plus E2's label-audit amendment both work. One constraint that undercuts part of it, though: E1's plan gets ρ̂ from historical mining "if we log which model touched what" — but the friction log records the opposite. Joe chose models by feel with no measurement, every task; jobboard-v2's history almost certainly has no per-model attribution. So β̂ can come from historical mining, but ρ̂ likely can't — it needs *prospective* logging during the dogfooding month. That's fine (the dogfooding gate, ADR-0015, runs anyway, and the bootstrap harness per ADR-0017 can log attribution via git hooks), but the success condition should say so honestly: β̂ retrospective with Wilson bounds on both repos; ρ̂ prospective, likely underpowered in month one, reported as such rather than faked from unlabelled history.

Also note EXP-05 (adapter surface, one-day budget) is the other highest-information unrun experiment and doesn't queue behind EXP-01 — it can run in the same week without touching the success condition.

With those two edits, agreed: Joe's instrument, EXP-01 both repos, label audit, falsifiable both ways.


===== DECISION D3 (Arm C, free-form Slack thread) =====

--- MSG [D3/C/facilitator/r0] ---
**[ARM C · D3]** Does the Inquiry tier (four-gate research trigger) belong in v0, or is it deferred?
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D3/C/E1/r1] ---
I'll open from the numbers, since nobody else has them. Nothing in our simulation work supports adding an Inquiry tier in v0 — and one result argues against it. Our robustness sweep (19 Aug) showed the closed form β* = (1−α)e^(−kΔ) is a knife-edge: correlated model successes at ρ=0.6 collapse β* from 0.112 to 0.028, and the quality gain at β=0 drops from +4.0 pp to +0.9 pp. β has never been measured on a real repo (EXP-01 not run). The one thing v0 must do is measure β properly, and even that is hard: Wilson intervals say 50–200 accepted diffs only settle the question when β is far from threshold.

So v0's scarce resource is labelled outcomes, not features. A four-gate research trigger adds a decision layer on top of an instrument we haven't calibrated. Also relevant: the three-tier depth sim (43.8% of frontier cost, +4.4 pp at β=0.10) says depth in the *routing ladder* is nearly free — if there's appetite for a tier, that's the cheap one, not Inquiry.

My vote: defer Inquiry until EXP-01 gives us a measured β. Open to E2/E3 telling me the gates serve something the numbers can't see.

--- MSG [D3/C/E2/r1] ---
Literature agrees with E1's deferral, and sharpens why. The 111-page harness survey (Meng et al., 23 systems): the word "verifier" appears zero times — nobody measures verifier reliability or conditions orchestration on it. Meta-Harness optimises against a benchmark score it trusts blindly; Dekoninck's cascade routing assumes the test oracle is perfect (β=0 by construction). So the unclaimed spot in the field is exactly one thing: measuring the false-accept rate per repo. That's what v0 buys us novelty-wise. An Inquiry tier buys nothing the literature hasn't already covered or warned against.

And it warns: Kim et al. (NMI 2026) find single-agent capability is the best predictor of whether coordination helps, with MAS costing 1.6–6.2× tokens at matched performance; the auto-MAS frameworks in the "illusion" study collapse back to one agent. A four-gate decision layer is precisely the structure that tends to be echo unless it introduces an exogenous signal — and per the delegation theorem's Corollary 9, verifiers that run tests ARE the exogenous signal. Inquiry gates aren't.

One supporting datum for v0's real job: METR — maintainer merge rates average 24.2 pp below SWE-bench grader scores on the same PRs. β is real at ecosystem scale and nobody measures it per repo. Defer Inquiry; spend v0 on EXP-01.

--- MSG [D3/C/E3/r1] ---
Landscape view: defer, and I'd go further — the market actively punishes shipping Inquiry in v0.

The pattern in this space has repeated three times running: "someone already built it, MIT-licensed" (model library → LM Studio; harness → DeepSeek Harness at ~135k stars in four days, plus OpenHarness with 43 tools, hooks, subagent teams; harness optimisation → Meta-Harness). Any v0 component has to survive "why won't this be the fourth?" A four-gate research trigger is generic orchestration machinery — exactly the kind of thing OpenHarness or DeepSeek could add as a plugin in a weekend. It won't differentiate us.

What the incumbents demonstrably do NOT have: any notion of verifier reliability. I've been through OpenHarness's surface — no measurement of whether automated checks can be trusted, no routing derived from it. Meta-Harness needs a trusted oracle; that's our opening, not our rival. So E1 and E2's conclusion holds from a third, independent class of facts: β measurement is the only unclaimed ground, and v0 should be all of it.

One addition: OpenHarness's hooks are precisely the integration surface a β-meter needs (ADR-0001 leaves the plugin route open). Spending v0 effort there beats spending it on gates.

Consensus so far is 3–0 defer.

--- MSG [D3/C/E4/r1] ---
Constraints view: I make it 4–0 defer, but with one honest complication the numbers can't see.

The complication: the Inquiry tier isn't speculative — it came from the friction log. "Decided research-vs-priors by feel, several times per session" is a real, recurring cost. So deferral shouldn't mean deletion; it means the friction log keeps accumulating instances, and if research-by-feel stays the top friction after a month, the trigger earns its way back — probably as something far smaller than four gates.

Why defer anyway: the binding constraint here is Joe's hours, not money. Fully open source, donation-funded, no hosted service — nobody funds a solo founder on donations, so v0 must be a small sharply-scoped core. EXP-01 (measure β on jobboard-v2 history) and EXP-05 (adapter surface, one-day budget) are the two highest-information unrun experiments and everything queues behind them. A four-gate layer competes for exactly those hours. And per invariant I1 (the jobboard-v2 lesson), any gate we ship needs its enforcement check in the same commit — four gates is four checks, quadrupling the v0 build.

One caution on EXP-01 alone: jobboard-v2 is a low-β repo, the regime that flatters the thesis. Pair it with hireable-3.0.

Defer, log, revisit against measured friction.

--- MSG [D3/C/E1/r2] ---
Closing from my side: 4–0 defer, and I'll add one number to E4's two points rather than repeat myself.

On pairing jobboard-v2 with a higher-β repo — the sample-complexity algebra says this is not optional. A low-β repo settles quickly (Wilson at true β=0.05, n=200 → [0.027, 0.090]), but it never exercises the threshold regime: at true β=0.08 near β*, even n=800 accepted diffs gives only ~86% power. So EXP-01 on jobboard-v2 alone would produce a confident-looking "safe" verdict that tells us nothing about where routing actually breaks. Second repo in, agreed.

On E4's revisit criterion: make it quantitative now, so it's not relitigated by feel later. Something like — Inquiry earns reconsideration when (a) research-by-feel is still the top friction-log entry after a month AND (b) we have a measured β with a Wilson upper bound, so any gate can be evaluated against a calibrated instrument rather than the closed form (which the robustness sweep showed overstates the safe threshold under correlation — false-safe direction).

Decision as I read it: defer Inquiry, v0 = EXP-01 (two repos) + EXP-05, friction log keeps the tier's case alive.

--- MSG [D3/C/E2/r2] ---
Nothing to add on D3 itself — defer stands, and Joe's quantitative revisit criterion is the right closure. Two housekeeping items from verification that belong on the record before we scope v0:

1. Our lit review carries a fabricated Meta-Harness figure — the "19-task 28.5%→46.5%" run does not exist in the paper (real result: 76.4% vs 74.7% on full TerminalBench-2, #2 behind ForgeCode). It passed our own review. That is a live instance of exactly the false-accept failure v0 exists to measure, in our own pipeline — worth fixing in `literature-review.md` and worth remembering when we design EXP-01's acceptance criteria.

2. The "unclaimed ground" claim isn't fully closed: two adjacent papers surfaced during verification and remain unread — EvoTrainer (arXiv:2606.03108) and "Adapting the Interface, Not the Model" (arXiv:2605.22166). Cheap to check before we stake v0's novelty on β measurement.

Neither changes the vote. 4–0 defer, v0 = EXP-01 (two repos) + EXP-05.

--- MSG [D3/C/E3/r2] SKIPPED (passed) ---

--- MSG [D3/C/E4/r2] SKIPPED (passed) ---


===== DECISION D4 (Arm C, free-form Slack thread) =====

--- MSG [D4/C/facilitator/r0] ---
**[ARM C · D4]** Candidate v0 list: β-meter + cascade + parallel worktrees + budget primitives + critic tier. Too much for one person? What gets cut?
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D4/C/E1/r1] ---
Opening position from the simulation side: the list has a dependency order, and that decides the cut.

β-meter first, non-negotiable. Everything else is gated on it. Our robustness sweep (19 Aug) showed the closed-form β* = (1−α)·e^(−kΔ) is a knife-edge: correlated model successes at ρ=0.6 collapse it from 0.112 to 0.028, and the quality gain at β=0 drops from +4.0 pp to +0.9 pp. Real models share training data, so shipping cascade routing gated on the closed form before β is measured on a real repo (EXP-01 has never run) is shipping a false-safe instrument.

Cascade second — the simulated upside is real (+4.0 pp at 63% of frontier cost below β*), but only after the meter exists.

Cut the learned router if anyone's tempted: Thompson sampling needs ~5,000 trajectories just to match always-cheap-with-escalation.

Parallel worktrees: the review ceiling is ~3 agents at realistic cycle times without a critic, ~5 with one. So worktrees and critic tier are a package — ship both or neither, and I'd defer both to v0.1. Budget primitives are cheap plumbing; keep.

Proposed v0: β-meter + cascade + budgets. Anyone disagree on the ordering rather than the list?

--- MSG [D4/C/E2/r1] ---
Literature backs that ordering almost exactly.

β-meter first: the 111-page harness survey mentions "verifier" zero times across 23 systems — nobody measures verifier reliability. And the METR data in it is the killer motivation: maintainer merge rates run *24.2 pp below* SWE-bench automated grader scores on the same PRs. Automated accept signals over-accept at ecosystem scale, and nobody measures the rate per repo. That's the unclaimed spot; it's also why Dekoninck et al. (ICML 2025) doesn't cover us — their cascade routing is optimal, but on SWE-Bench they assume the test oracle is perfect. β=0 by assumption. So cascade-without-meter isn't just risky, it's literally the published state of the art's blind spot. Ship them as a pair, meter first.

Budgets: keep — 63 documented production budget-overrun incidents (arXiv:2606.04056). Not a v2 feature.

Cutting worktrees+critic to v0.1: Kim et al. (NMI 2026) supports it — multi-agent costs 1.6–6.2× tokens at matched performance, and single-agent capability best predicts whether coordination helps at all. The delegation theorem's only exemption is new exogenous signals; verifier outcomes qualify (Corollary 9), agent parallelism per se doesn't.

So: agree with the list and the ordering. β-meter + cascade + budgets.

--- MSG [D4/C/E3/r1] ---
Landscape view agrees with the cut, and sharpens it with a filter: every v0 component should survive "why won't someone MIT-license this first?" — that answer has been correct three times running (model library → LM Studio; harness → DeepSeek Harness, 135k stars in four days; harness optimisation → Meta-Harness).

Run the list through it:
- β-meter: the only genuinely unclaimed piece. OpenHarness (14.8k stars, 43 tools, hooks, subagent teams) has literally no notion of verifier reliability. Meta-Harness needs a trusted oracle — that's our opening, not a rival. Keep, first.
- Parallel worktrees: OpenHarness ships a worktree tool today, MIT. Building our own is being the fourth casualty. Cut from v0; adopt, don't build, if v0.1 needs it. Same for critic-tier plumbing — subagent teams exist off the shelf.
- Budget primitives: nobody in the meta-harness layer ships them; cheap; keep.
- Cascade: fine second, but note the adapter tax — four independently evolving orchestratee CLIs, and EXP-05 (Claude Code adapter → Codex without refactor) is registered and unrun. I'd want EXP-05 run before cascade hardens.

One live alternative worth deciding explicitly: ship the β-meter as an OpenHarness plugin (hooks observe verifier outcomes, nonzero audience day one) vs standalone. ADR-0001 leaves it open. Otherwise: β-meter + cascade + budgets, agreed.

--- MSG [D4/C/E4/r1] ---
Constraints view: same cut, and the economics make it harsher than you're all being. This is fully open source by Joe's explicit decision — donations, no hosted service, no revenue. The binding constraint is his hours. That means v0 isn't "what's valuable", it's "what one person can keep alive". Three components is already ambitious; five is a graveyard.

Two constraint facts that sharpen the plan:

1. EXP-01 (measure β on jobboard-v2 history) and EXP-05 (adapter portability) are the two highest-information unrun experiments — everything queues behind them. E3's "run EXP-05 before cascade hardens" is already the registered plan. But note: jobboard-v2 is a low-β repo (~20 CI ratchets, 44 probes) — the regime where cascading looks best. Measuring only there flatters the thesis; the weakly-verified contrast repo (hireable-3.0) is mandatory before any public number.

2. The friction log supports exactly this cut: what actually bit Joe was choosing models by feel (→ cascade + meter) and no budget guardrails. Nothing in the log demands worktrees or a critic.

On E3's plugin question: solo-founder economics argue for the OpenHarness plugin route — small core, someone else maintains the platform, audience day one. I'd decide that yes, now.

So: β-meter + cascade + budgets, meter first, agreed — plus contrast-repo measurement as a hard gate.

--- MSG [D4/C/E1/r2] ---
Consensus holds — β-meter + cascade + budgets, meter first, contrast repo as a gate. Two numbers nobody's used yet that should shape the build:

1. Sample complexity makes E4's gate concrete. β is a binomial proportion over accepted diffs. Wilson 95% at true β=0.05: n=50 gives [0.011, 0.135] — spans the decision threshold; n=200 gives [0.027, 0.090]. And near the threshold you're underpowered: at true β=0.08 even n=800 only reaches 86% power. Consequence: prospective logging alone won't get a solo dev a usable β for months. Historical mining (PR outcomes, reverts, fix-commits) isn't a nice-to-have, it's the only viable labelling route at solo volumes — the meter's v0 core is a git-history miner, not a live hook. Live hooks can be the OpenHarness plugin layer on top.

2. Build the cascade as a ladder, not a switch. Three-tier (cheap → mid → frontier) at β=0.10 simulates at 43.8% of frontier cost with +4.4 pp quality — depth is nearly free. Costs nothing extra to design for N tiers from the start.

One caution on scope creep back in: the critic isn't a separate thesis — critic recall ≡ 1−β. When v0.1 revisits worktrees+critic, it's the same meter pointed at a different verifier, not a new component.

--- MSG [D4/C/E2/r2] ---
Consensus stands; three closing notes from the literature side before we call it.

1. A caution that strengthens E4's "hard gate before any public number": our own lit review carried a fabricated Meta-Harness figure (a 19-task 28.5%→46.5% run that doesn't exist; the real result is 76.4% vs 74.7% on TerminalBench-2). It passed our review process — a false-accept in our own pipeline. The project that measures β should treat its own claims as artifacts under the same meter.

2. Novelty isn't fully closed: two adjacent papers surfaced during verification and are unread — EvoTrainer (arXiv:2606.03108) and "Adapting the Interface, Not the Model" (arXiv:2605.22166). Cheap to read; do it before the positioning hardens.

3. On the historical-mining pivot in point 1 above: agreed, and it matches the METR finding's shape — maintainer merge outcomes vs automated grader scores is exactly a git-history signal. For the /learn-style context layer later, ACE (ICLR 2026) is solved prior art; adopt, don't invent.

Decision as I read it: β-meter (git-history miner core) + cascade (post EXP-05) + budgets; worktrees+critic to v0.1 via OpenHarness; contrast repo gates any public figure.

--- MSG [D4/C/E3/r2] ---
One brake before E4's "decide the plugin route yes, now" becomes the decision. The case for the OpenHarness plugin is real, but three landscape facts cut against committing today: it's v0.1.9 with an unstable surface, last release 7 May — three months quiet; the test suite is modest (114 tests); and the 16% fork-to-star ratio suggests institutional reach rather than proven production usage. Binding a solo project's fate to another team's roadmap is exactly the kind of dependency a one-person maintainer can't absorb if it moves.

E1's git-history-miner pivot actually dissolves the urgency: the meter's v0 core needs no hooks at all, so the plugin question only bites at the live-hook layer. Proposal: build the miner core harness-agnostic, and gate the plugin decision on a cheap probe — does OpenHarness ship a release in the next month, and does EXP-05's adapter tax look worse than plugin lock-in? Decide then, not now.

Housekeeping while we're closing: "Consilience" trademark clearance hasn't run and npm/PyPI/crates names aren't reserved. Cheap, do before anything public. Otherwise: β-meter + cascade + budgets stands.

--- MSG [D4/C/E4/r2] ---
Conceding the plugin point — E3's staleness facts (three months since a release, unstable surface) are exactly the dependency risk a solo maintainer can't absorb, and the miner-core pivot removes my urgency argument. Harness-agnostic core, probe-gated plugin decision: agreed.

One constraint fact that seals the miner-first design: the dogfooding gate (ADR-0015) says Consilience must build Consilience with measured gates before any public claim. A git-history miner satisfies that on day one — this repo and jobboard-v2 are its first inputs — whereas a live-hook meter would need weeks of prospective volume E1 just showed we don't have. So the miner isn't only the viable labelling route, it's the only route that clears our own gate.

And to close the loop on Joe's standing preferences: this cut supersedes nothing silently — ADR-0002/0009 stay PROVISIONAL pending EXP-01/06, and the worktrees+critic deferral should be recorded as a superseding ADR, not an edit.

Final as I read it: β-meter (git-history miner, harness-agnostic) + cascade (post EXP-05) + budgets. Worktrees+critic → v0.1, adopt-don't-build. Contrast repo (hireable-3.0) gates any public figure. Trademark/name checks before anything ships. Done from my side.


===== DECISION D5 (Arm C, free-form Slack thread) =====

--- MSG [D5/C/facilitator/r0] ---
**[ARM C · D5]** Does the local model library belong in v0 — in, out, or wrapped? (Null option: a cheap API model as the cheap tier.)
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D5/C/E1/r1] ---
Opening with what the numbers say, because they cut against the local library harder than you'd expect. The cascade only wins below β* ≈ 0.11 — and our robustness sweep (19 Aug) showed that threshold is a knife-edge: correlated model successes (Gaussian copula ρ=0.6) collapse β* from 0.112 to 0.028, and at ρ=0.9 the quality advantage of a cheap tier is *zero*. Local models fine-tuned on the same public code as frontier models are exactly the high-ρ case. So the simulation doesn't just fail to justify local models in v0 — it warns that any cheap tier is unsafe until we've measured β and cross-model correlation on a real repo (EXP-01, never run).

The maths is indifferent to *where* the cheap model runs; a cheap API model exercises the identical routing logic with none of the library surface. My vote: out of v0, null option in, and the local rig's v0 job is measurement — generating the per-repo β curves — not serving inference. Wrap later only if measured ρ leaves any headroom worth capturing.

--- MSG [D5/C/E2/r1] ---
The literature backs "out, null option in" — and adds a reason the simulation can't. Dekoninck et al. (ICML 2025) already solved optimal cascade routing, but on SWE-Bench they assume the test oracle is perfect: β=0 by assumption. Nobody has published a critical-noise threshold. Meanwhile the METR data in Meng et al.'s survey shows maintainer merge rates run 24.2pp *below* automated grader scores for the same PRs — automated accept signals over-accept at ecosystem scale. So the field's own state of the art says: the routing maths is a solved commodity, the unmeasured quantity is β. Our differentiation is measuring it, which supports E1's "the rig's v0 job is measurement".

Two more nails: Kim et al. (NMI 2026) find MAS/tiering costs 1.6–6.2× tokens at matched performance unless single-agent capability already suffices — a cheap tier that can't clear the task isn't cheap. And a cheap API model exercises the identical cascade code path Dekoninck formalises, so we lose no generality by deferring local.

One honest caveat: verifiers that run tests are exogenous signals under the delegation theorem (Corollary 9), so a cheap tier *plus a measured verifier* could be principled later. But "later" means after per-repo β exists. Vote: out of v0, cheap API as null tier, wrap only if measured β/ρ leaves headroom.

--- MSG [D5/C/E3/r1] ---
Landscape view: I agree — out of v0, and the market makes the case even more bluntly than the maths. "Someone already built this, MIT-licensed" has been the correct answer three times running: model library → LM Studio/LLM Checker; harness → DeepSeek Harness (135k stars in four days) and OpenHarness; harness optimisation → Meta-Harness (Stanford/MIT). A local model library in v0 would be the fourth. Any v0 component should survive "why won't this be the fourth?", and this one plainly doesn't.

What nobody has built is verifier reliability: OpenHarness has 43 tools, hooks, plugins — and no notion of whether automated checks can be trusted. The β thesis is untouched by the entire field. Every hour of v0 spent wrapping llama.cpp is an hour not spent on the one thing with no incumbent. E1's "the rig's job is measurement" fits: measurement produces the trusted oracle that even Meta-Harness needs and lacks — that's our opening, not a rival.

So: out, cheap API as null tier, and if we ever want local we wrap LM Studio rather than build. Sounds like three votes converged already — Joe, any reason to hold it open?

--- MSG [D5/C/E4/r1] ---
Constraints view: fourth vote for out, and the project's actual situation closes the loop. The binding constraint isn't money or maths — it's Joe's hours. This is fully open source by explicit decision (donate button, no hosted service, no revenue), so nobody is funding platform surface. That argues for a small, sharply-scoped core with a plugin boundary, and a local model library is exactly the kind of surface a solo founder can't carry.

Two constraint facts that sharpen E1/E3's "the rig's job is measurement": EXP-01 (measure β on jobboard-v2 history) is one of the two highest-information unrun experiments, and everything else queues behind it. And a warning — jobboard-v2 is a low-β repo (~20 CI ratchets, 44 invariant probes), the regime where cascading looks best. Measuring only there flatters the thesis; the weakly-verified contrast repo (hireable-3.0) is mandatory before anyone claims headroom for a cheap tier.

Last thing: the friction log that motivated this — "chose model by feel, no measurement" — is an argument for the β-meter, not for local inference. A cheap API model exposes the same friction at zero build cost. Joe's standing preference is to kill liked ideas early; this one's killed. Consensus: out, null option in, wrap LM Studio later only if measured β/ρ says so.

--- MSG [D5/C/E1/r2] SKIPPED (passed) ---

--- MSG [D5/C/E2/r2] SKIPPED (passed) ---

--- MSG [D5/C/E3/r2] SKIPPED (passed) ---

--- MSG [D5/C/E4/r2] SKIPPED (passed) ---


===== DECISION D6 (Arm C, free-form Slack thread) =====

--- MSG [D6/C/facilitator/r0] ---
**[ARM C · D6]** Should ADRs ship runnable decision models re-run in CI (sign flip fails the build), or is that ceremony?
Four participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class.

--- MSG [D6/C/E1/r1] ---
E1 here. Not ceremony — my own results this week are the strongest argument for it. The closed form β* = (1−α)e^(−kΔ) said 0.112; the robustness sweep broke every assumption in turn and the *value* moved everywhere (0.052–0.426 across link/slope/guessing variants). But the *sign and threshold structure* survived until we hit correlated model successes: copula ρ=0.6 collapses β* to 0.028 and the quality gain at β=0 from +4.0 pp to +0.9 pp. That is exactly a sign-flip-class event: a decision (cascade wins) reverses under a parameter we hadn't modelled. If the ADR that adopted the cascade had shipped its model, adding the correlation parameter would have failed the build and forced the re-decision — instead of it living in my head.

Two caveats from my side. (1) Gate on *sign flip only*, never on the point value — my numbers demonstrate the values are knife-edge and link-specific; failing CI on value drift would be noise. (2) Only decisions with a quantitative model qualify. D6 shouldn't mandate models for prose decisions — that would be ceremony. Rule I'd propose: if an ADR cites a number, the number's generator ships and re-runs; if it doesn't, no model required.

--- MSG [D6/C/E2/r1] ---
E2 (literature). Agree with E1, and the literature gives two independent reasons this isn't ceremony.

First, we have direct evidence our own review process needs it: the lit review carried a fabricated Meta-Harness figure (a 19-task 28.5%→46.5% run that doesn't exist; the real result is 76.4% vs 74.7% on TerminalBench-2). A prose claim citing a number sailed through review. E1's rule — "if an ADR cites a number, the number's generator ships and re-runs" — would have caught that class of failure, because a number without a runnable generator becomes visibly second-tier.

Second, the field systematically doesn't do this and pays for it. The 111-page harness survey: "verifier" appears zero times across 23 systems; METR data shows maintainer merge rates averaging 24.2 pp below automated grader scores on the same PRs. Dekoninck et al. assume β=0 by fiat on SWE-Bench. Unexamined quantitative assumptions frozen into decisions is the norm, and it's exactly the gap this project claims to fill — so eating our own cooking is coherence, not ceremony.

Endorse both of E1's caveats, especially sign-flip-only gating. Prose ADRs stay exempt.

--- MSG [D6/C/E3/r1] ---
E3 (landscape). I'll support E1's rule, and add a market reason nobody's said yet: differentiation. Nothing in the field does this. DeepSeek Harness and OpenHarness — the two MIT projects that already ate the harness layer — have no notion of verifier reliability at all; Meta-Harness optimises harnesses but needs a trusted oracle it doesn't have. Our recurring failure pattern is "someone already built this, MIT-licensed" (three times running: model library, harness, harness optimisation). ADRs that ship their own falsifiable decision models is one of the few practices where the honest answer to "why won't this be the fourth?" is: nobody else does it, and it's directly downstream of the β thesis rather than adjacent to it.

Concrete case it would bite now: ADR-0001 keeps "build standalone vs OpenHarness plugin" open, and part of that call rests on quantitative claims — adapter tax across four independently evolving orchestratee surfaces, OpenHarness's health signals (16% fork-to-star, 114 tests, last release May). EXP-05 is registered and unrun. Under E1's rule, an ADR closing that decision couldn't cite the adapter-tax number without shipping its generator. That's exactly the discipline we want before committing to a layer.

Sign-flip-only, prose exempt: agreed. Sounds like three of four are converged.

--- MSG [D6/C/E4/r1] ---
E4 (constraints). I'll make it four — with two constraint-side reasons and one guard.

First, this isn't a new practice for us, it's an existing invariant applied to ADRs. I1 (from jobboard-v2's most expensive lesson: a documented chokepoint fragmented into five bypass paths because no lint rule enforced it) already says any invariant ships with its enforcement check in the same commit. E1's rule is just I1 for quantitative decisions. Rejecting it here would be incoherent with our own working principles.

Second, the binding constraint is Joe's hours, not compute — the 5090 makes re-running models free, but *maintaining* them isn't. So the guard: the gate must stay cheap. Sign-flip-only (agreed), models are the experiment scripts we're writing anyway (EXP-01/05 style, seconds not hours), and a hard runtime budget per model in CI. If a model needs babysitting, it gets superseded with the ADR, never patched to pass.

One live datum: our 24 ADRs are one day old with one conflicted reviewer, and two are PROVISIONAL pending exactly these experiments. Runnable models are the only second reviewer we can actually afford. Converged: adopt, sign-flip-only, prose exempt, runtime-budgeted.

--- MSG [D6/C/E1/r2] SKIPPED (passed) ---

--- MSG [D6/C/E2/r2] SKIPPED (passed) ---

--- MSG [D6/C/E3/r2] SKIPPED (passed) ---

--- MSG [D6/C/E4/r2] SKIPPED (passed) ---

--- MSG [D1/C/SCRIBE] ---
Ship the β-meter as a plugin on OpenHarness first, standalone later only if measurements justify it. Conditions the group attached: a harness-agnostic/host-neutral core (required, not optional, because the ADR-0017 bootstrap runs on Claude Code); run EXP-01 (with hireable-3.0 as mandatory contrast repo) and EXP-05 before binding; supersede ADR-0001 rather than edit it; treat EXP-01 output as sign/contrast only; read EvoTrainer (2606.03108) and 2605.22166 before claiming novelty; reserve package names and run trademark clearance before the plugin lands.
DISSENT RECORDED: None. E3 raised OpenHarness v0.1.x instability as a caveat and E4 answered it (probe via EXP-05, host-neutral core); it was folded into conditions rather than remaining a disagreement.

--- MSG [D2/C/SCRIBE] ---
The group unanimously converged: v0 is Joe's instrument, not a stranger-facing npm artifact. Build EXP-01 first — measure β on real repos. Success condition as finalised: v0 succeeds iff EXP-01 yields β̂ (retrospective, Wilson bounds) on both jobboard-v2 and hireable-3.0, ρ̂ prospectively logged during the dogfooding month (reported as underpowered rather than mined from unattributed history), a hand-audited sample (~n=30) of mined labels with error rate reported alongside β̂ and ρ̂, and a month of dogfooding producing a non-empty friction log. Falsifiable both ways. Same artifact as the stranger version eventually, but sequencing is forced. Side agreements: reserve npm/PyPI names now; EXP-05 can run in parallel; novelty claim recorded as pending two unread papers.
DISSENT RECORDED: No open dissent. Refinements absorbed into consensus: E4 insisted the two-repo contrast is mandatory and that "makes Joe's week better" must be allowed to come back false; E2 added the label-audit amendment and flagged the novelty claim as pending two unread papers; the final reply corrected that ρ̂ cannot come from historical mining (no per-model attribution exists) and must be prospective.

--- MSG [D3/C/SCRIBE] ---
Defer the Inquiry tier from v0 (4-0 unanimous). v0 = EXP-01 measuring β on two repos (jobboard-v2 plus a higher-β repo, e.g. hireable-3.0) + EXP-05. Deferral is not deletion: the friction log keeps the tier's case alive, with a quantitative revisit criterion — reconsider only if research-by-feel is still the top friction-log entry after a month AND a measured β with a Wilson upper bound exists.
DISSENT RECORDED: None. One caveat (E4): the tier originated from a real friction-log cost, so it may earn its way back in smaller form; group adopted a quantitative revisit criterion rather than dissenting.

--- MSG [D4/C/SCRIBE] ---
v0 = β-meter (git-history miner core, harness-agnostic) + cascade (gated on β-meter existing and EXP-05) + budget primitives. Worktrees + critic tier deferred to v0.1 as adopt-don't-build, recorded via a superseding ADR. Contrast repo (hireable-3.0) is a hard gate before any public β figure. OpenHarness plugin decision deferred to a probe (release activity + EXP-05 adapter tax), not taken now. Trademark/name checks before anything public.
DISSENT RECORDED: Transient only: E4 initially pushed to commit to the OpenHarness plugin route immediately; E3's staleness evidence led E4 to concede to a probe-gated deferral. No dissent remained at close.

--- MSG [D5/C/SCRIBE] ---
Local model library is out of v0; the null option (a cheap API model as the cheap tier) is in. The local rig's v0 job is measurement (per-repo β curves via EXP-01, including the weakly-verified contrast repo hireable-3.0), not inference. If local is ever wanted, wrap LM Studio rather than build, and only if measured β/ρ leaves headroom.
DISSENT RECORDED: None. All four participants (E1–E4) voted out/null-option-in. Caveats, not dissent: measuring only jobboard-v2 (low-β) would flatter the thesis, and a cheap tier plus a measured verifier could be principled after β is measured.

--- MSG [D6/C/SCRIBE] ---
Adopt: ADRs that cite a number must ship the number's runnable generator, re-run in CI, gating on sign flip only (never point-value drift); prose-only ADRs exempt; hard per-model runtime budget, and a model needing maintenance is superseded with the ADR rather than patched to pass. All four participants (E1-E4) endorsed this rule explicitly.
DISSENT RECORDED: None. All four endorsed; the only qualifications were caveats folded into the rule (sign-flip-only gating, prose exemption, runtime budget).
