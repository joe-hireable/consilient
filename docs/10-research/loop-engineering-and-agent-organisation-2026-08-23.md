# Loop engineering and organised multi-agent systems — research sweep, 23 August 2026

Ten researchers swept distinct literatures in parallel, deduplicated against the 176 works this
repository already cites, and a completeness critic named what they missed. **129 findings.**

Every claim carries its evidence tag. The identifiers are the researchers' own: any line marked
`[asserted] — unverified` **must be checked before it is cited publicly**. This repository has
been publicly wrong about a citation once already, and a fabricated reference in a project whose
subject is measurement honesty is a self-inflicted wound.

Dispatched by the orchestrator, 23 August 2026, at the principal's request: DAIR.AI, frontier
labs, top-tier university labs and peer-reviewed venues only.

---

# Research brief: organised agent systems — what the field already knows

**Scope note.** 129 findings, deduplicated against 176 works already cited. Gaia and MOISE+ arrived twice under different angles and are recorded once here. Every claim carries an evidence tag. Identifiers dated after mid-2026 have not been verified in this pass and are marked accordingly.

---

## What is genuinely new to us

### (a) Organisational structure — roles, RACI, autonomy, dependency

- **MOISE+** — DOI 10.1007/3-540-36127-8_12, Springer LNAI, ~1,500 citations. Splits an org spec into structural / functional / **deontic** layers, joined only by an enumerable `<role, mission, obligation|permission>` table. Our RACI *is* this table with a weaker type system. [asserted] Adopt the three-way split and the typed links (acquaintance / communication / authority) — our dependency matrix currently conflates all three. Cite the LNAI chapter; the AAMAS'02 short-paper DOI is ambiguous [asserted] — unverified, check before citing.
- **ORA4MAS** — DOI 10.1007/s10458-009-9084-y, JAAMAS 20(3). Norms are **regimented** (action made impossible) or **regulated** (permitted, detected, sanctioned), chosen per norm. [asserted] That is our autonomy dial, already formalised: L0 = regimented, L3 = regulated. Org state must live in an observable artefact, not prompt text — prompt norms cannot be regimented or audited.
- **Gaia** — DOI 10.1023/A:1010071910869, JAAMAS 3(3). Role = responsibilities split into **liveness** and **safety**, plus permissions over named resources, activities, protocols; acquaintance graph derived from protocols. [asserted] Our role rows lack permissions and safety invariants entirely.
- **AGR / Aalaadin** — DOI 10.1109/ICMAS.1998.699041. Messages address a **role in a group**, not an agent; group is the visibility boundary. [asserted] Fixes agent identity: instances become swappable without editing the org.
- **Electronic Institutions** — DOI 10.1007/3-540-44682-6_8. Commitments incurred by speech acts, discharged in a later scene; the institution mediates every utterance. [asserted] Our tool broker should be a governor, not a policy paragraph.
- **Horling & Lesser survey** — DOI 10.1017/S0269888905000317, KER 19(4). Ten organisational paradigms with predicted cost/benefit. [cited] Our design space is "flat vs supervisor" — two of ten.
- **ODML** — DOI 10.1007/s10458-007-9020-y. Score a candidate org *before* running it. [simulated]
- **TÆMS/GPGP** — DOI 10.1023/B:AGNT.0000019690.28073.04. Typed, quantified inter-agent effects: enables / facilitates / hinders / disables, with magnitude and delay; commitments derived from them. [simulated] Adopt the edge vocabulary wholesale.
- **Feng et al., Levels of Autonomy** — arXiv:2506.12469. Five levels named by the *human's* role (operator → observer), separable from capability. [asserted] Use verbatim; do not invent a scale.
- **KnowNo** — arXiv:2307.01928, CoRL 2023 Oral. Conformal prediction gives escalation a **coverage guarantee**. [measured] This is the only rigorous escalation trigger in the set.
- **Authenticated delegation** — arXiv:2501.09674 (MIT Media Lab). OAuth/OIDC extended with scoped agent credentials plus an NL→policy compiler. [asserted] Kills ambient authority and the confused deputy.
- **Kolt, Governing AI Agents** — arXiv:2501.07913 (Notre Dame L. Rev., student-edited). Classical agency-law remedies fail because agents have no assets, reputation or standing; accountability must terminate in a named human. [asserted]
- **Santoni de Sio & van den Hoven** — doi:10.3389/frobt.2018.00015. Meaningful human control = **tracking** (responsive to human reasons) + **tracing** (every action traceable to an identifiable human's understanding). [asserted] Tracing is RACI's "A", given a testable definition.

### (b) Ambient loops and self-improvement

- **Sharpening** — arXiv:2412.01951 (MSR NYC). Self-improvement on self-verification cannot create information; it amortises best-of-N into weights and saturates. [measured] **This is the ceiling.** Label every ambient subsystem as sharpening or information-adding.
- **Generation–verification gap** — arXiv:2412.02674, ICLR 2025. The gap is measurable and model-specific and predicts self-improvement gain. [measured] Measure it *before* enabling a loop; near-zero gap → disable.
- **RLVR pass@k** — arXiv:2504.13837, NeurIPS 2025 Oral. RLVR beats base at k=1 and loses at large k. [measured] k=1 deltas are inadmissible evidence.
- **Shumailov et al., model collapse** — doi:10.1038/s41586-024-07566-y, *Nature* 631. Recursive self-training loses distribution tails first, irreversibly. [measured]
- **Self-consuming models go MAD** — arXiv:2307.01850, ICLR 2024. Three regimes; only *fresh real data* avoids collapse, and quality-biased filtering accelerates diversity loss. [measured] A "keep only the best self-generated skills" filter is the failure mode.
- **Open-endedness** — arXiv:2406.04268 (DeepMind): novelty × learnability, both required. [asserted] **Enhanced POET** — arXiv:2003.08536, ICML 2020: ANNECS, a single ungameable integer. [measured] Steal ANNECS.
- **Nachkov et al.** — arXiv:2510.14548 (ETH/INSAIT). The closest published prior art to ambient mode: works, but **repetitive task generation** and prompt-luck sensitivity. [measured]
- Memory that works without weight updates: **Agent Workflow Memory** arXiv:2409.07429 (+24.6%/+51.1% relative) [measured]; **Dynamic Cheatsheet** arXiv:2504.07952 (Game of 24 10%→99%) [measured]; **ExpeL** arXiv:2308.10144, AAAI-24 — contrastive insight extraction from success/failure *pairs* [measured].

### (c) Loop scheduling under budget and quota

- **Whittle, restless bandits** — DOI 10.2307/3214163. Un-run arms keep drifting; index = subsidy-for-passivity λ. [asserted] λ *is* the quota price.
- **Weber & Weiss** — DOI 10.1017/s0021900200039176 + 1991 addendum. Asymptotic optimality only, and not general. [asserted] At 5–30 loops we have no guarantee; say so.
- **Papadimitriou & Tsitsiklis** — DOI 10.1287/moor.24.2.293. Restless-bandit control is PSPACE-hard. [asserted] Refuse any "optimal scheduler" proposal.
- **Russell & Wefald, metareasoning** — DOI 10.1016/0004-3702(91)90015-C. Value of computation supplies the numerator the Whittle index needs. [simulated]
- **Zilberstein & Russell** — DOI 10.1016/0004-3702(94)00074-3: per-component performance profiles, budget split across them. [simulated] **Hansen & Zilberstein** — DOI 10.1016/S0004-3702(00)00068-0: stopping under uncertainty, **including the cost of monitoring itself**. [simulated] An LLM asked "is this loop progressing?" burns the quota it protects.
- **Bandits with Knapsacks** — arXiv:1305.2545, JACM 65(3). Hard exhaustible budget; optimal policy is a *mixture*, not argmax. [asserted]
- **Mate et al.** — arXiv:2109.08075, AAAI 2022. RMAB deployed live, 23,003 participants, ~30% drop-off reduction. [measured] Existence proof plus a method for fitting transitions from logs.
- **Snell et al.** — arXiv:2408.03314, ICLR 2025: difficulty-conditioned allocation, >4× over uniform. [measured] **Large Language Monkeys** — arXiv:2407.21787: log-linear coverage, but selection plateaus without an automatic verifier. [measured] **s1** — arXiv:2501.19393: budget forcing makes an allocation *binding*. [measured]
- **SpotServe** — arXiv:2311.15566, ASPLOS 2024. Harvesting revocable capacity: 54% cost saving, with the latency cost reported. [measured] Expiring quota is a spot instance inverted in time; opportunistic work must checkpoint.

### (d) Autonomous agent and tool creation

- **AgentSquare** arXiv:2410.06153 (ICLR 2025, +17.2% over best human designs, with a surrogate predictor that scores a design without running it) [measured]; **AFlow** arXiv:2410.10762 (agent-as-code, diffable) [measured]; **MaAS** arXiv:2502.04180 (ICML 2025 Oral — query-conditioned architecture at 6–45% of baseline cost) [measured]; **MASS** arXiv:2502.02533 — **prompts matter more than topology**; optimise per-role instructions first [measured].
- **DSPy** arXiv:2310.03714 and **TextGrad** doi:10.1038/s41586-025-08661-4 (*Nature* 639). Emit synthesised agents as declarative programs and every downstream optimiser becomes free; textual gradients localise *which module* failed. [measured]
- **GEPA** arXiv:2507.19457. Reflective evolution beats GRPO by 6–20% at up to 35× fewer rollouts — the only adaptation loop cheap enough for a live session. [measured]
- Tool layer: **BFCL** (PMLR v267:48371) scores calls by AST match without executing, and scores **abstention** [measured]; **AppWorld** arXiv:2407.18901 (ACL 2024) verifies by world state and counts **side effects** — GPT-4o ~49%/~30% [measured]; **ToolRet** arXiv:2503.01763 — IR-strong retrievers are weak at tool retrieval [measured]; **TroVE** arXiv:2401.12869 — higher accuracy with a **79–98% smaller** toolbox [measured]; **SWE-agent** arXiv:2405.15793 — interface design alone moves the number [measured]; Anthropic **code execution with MCP** — 150k→2k tokens [measured].
- **Contract Net** — DOI 10.1109/TC.1980.1675516, and **LARKS** — DOI 10.1023/A:1014897210525. Bidding and signature-based capability matching are the alternative to retrieval nobody in the MCP era is considering. [asserted] Both descriptions come from memory, not fetched abstracts.
- **Proactive Agent** arXiv:2410.12361 — 66.47% F1 on unrequested-task detection with an explicit false-alarm rate [measured]; **Tell Me More!** DOI 10.18653/v1/2024.acl-long.61 — clarify-before-act, measured as reduced wasted tool calls [measured].

### (e) Identity and portable memory

- **Generative Agents** arXiv:2304.03442 (UIST 2023). Recency × importance × relevance, scored automatically; the agent never issues a query. Ablation shows each term earns its place. [measured] Replaces our token-overlap recall directly.
- **ACT-R** doi:10.1037/0033-295X.111.4.1036, *Psych. Review*, 3,242 citations. Base-level decay plus **spreading activation** plus a retrieval **threshold** — so "nothing was relevant" is a first-class outcome. [measured] Constants need checking against the PDF.
- **Standard Model of the Mind** doi:10.1609/aimag.v38i4.2744. Long-term memory access is cue-based, automatic and parallel — *by architectural definition*, not a tool the agent remembers to call. [asserted]
- **HippoRAG** arXiv:2405.14831 (NeurIPS 2024) — PPR over an entity graph gives ACT-R's spreading activation concretely, at 6–13× the speed of iterative retrieval [measured]; **LongMemEval** arXiv:2410.10813 (ICLR 2025) — 30% absolute drop, decomposed into extraction / multi-session / temporal / **knowledge update** / **abstention** [measured]; **Larimar** arXiv:2403.11901 (ICML 2024) — selective forgetting and leakage prevention as cheap operations [measured]; **Sleep-time compute** arXiv:2504.13171 — ~5× less test-time compute, 13–18% accuracy gain, and the honest boundary condition (query predictability) [measured].
- The counter-case: **Self-RAG** arXiv:2310.11511 (learned gate beats always-retrieve) [measured]; **Mallen et al.** arXiv:2212.10511 (retrieval *hurts* on popular entities) [measured]; **Shi et al.** arXiv:2302.00093 (one plausible irrelevant sentence collapses accuracy) [measured]; **Lost in the Middle** arXiv:2307.03172 (position determines use) [measured]. Together: precision beats coverage, and an always-include list is a liability.

### (f) Whether multi-agent organisation works at all

- **Kenton et al.** — arXiv:2407.04622 (DeepMind). Debate beats consultancy everywhere, **but** beats direct QA only under information asymmetry — give the judge the article and the advantage vanishes. [measured] This is our thesis, measured, in its strong form.
- **Khan et al.** — arXiv:2402.06782, ICML 2024 (Anthropic/UCL). 48%→76% non-expert, 60%→88% human, with **same-model** debaters. The gain is evidence asymmetry, not model diversity. [measured]
- **Chen et al.** — arXiv:2403.02419, NeurIPS 2024. Vote and Filter-Vote accuracy **rises then falls** with call count, because query difficulty is heterogeneous. [measured] More agents is not monotone.
- **Sparse topology** — arXiv:2406.11776 (Google). All-to-all debate is a brute-force default; sparse matches or beats it far cheaper. [measured] Sparsity is also mechanically anti-echo.
- **MDAgents** arXiv:2404.15155 (MIT) — route by complexity; the 11.8% gain came from adding *external knowledge*, not from the group [measured]. **Chain of Agents** arXiv:2406.02818 — the honest easy case: evidence exceeds one context window, so disjointness is forced by physics [measured].
- **Woolley et al.** — DOI 10.1126/science.1193147, *Science* 330. Collective intelligence *c* is not predicted by members' average or maximum ability; it is predicted by social sensitivity and **equality of conversational turn-taking**. [measured] *Correction to the source summary: the reported proportion-of-women effect is mediated by social sensitivity — do not quote it as an independent predictor.*
- **Hong & Page** — DOI 10.1073/pnas.0403723101. Diversity beats ability *because* high-ability solvers share heuristics and therefore share local optima. [simulated] A model, not a measurement of LLMs; use as hypothesis, never as warrant.

---

## The bar, named

| Subsystem | Best existing thing, and what it achieves | "Markedly better", as a quantity |
|---|---|---|
| **(a) Org structure** | MOISE+/Gaia specify roles, deontics and permissions; ORA4MAS enforces them assuming the artefact mediates every action [asserted]. MAST (arXiv:2503.13657) labels 14 failure modes over 1,600+ traces at κ=0.88 [measured]. | **Per-MAST-mode delta** from adding explicit structure — e.g. "disobey role specification" rate falls from *x* to *y* per 1,000 actions, our own labelling at κ≥0.88; plus **regulated-norm detection recall** (ORA4MAS assumes 1.0 by fiat) and **level-conformance count** = 0 actions above certified level. |
| **(b) Ambient loop** | Sharpening theory bounds it [measured]; ETH's self-directed agent works but repeats itself [measured]; POET's ANNECS is the progress metric [measured]. | **ANNECS over an unattended run that does not flatten**, plus the ablation: remove the novelty gate and the curve must flatten. Report **proposal-yield** (admitted artefacts / proposed tasks), **duplicate-proposal rate**, **library tail-diversity over generations** alongside capability, and **fresh-external-input bytes per self-generated artefact**. Nobody publishes the last one. |
| **(c) Scheduling** | Whittle index, asymptotically optimal only at many arms [asserted]; Zuo & Zhu report ~11 points absolute at **matched compute** [measured] — identifier unverified. | **Value-delivered per token under a replayed real quota trace**, against three baselines: round-robin, best fixed loop-mixture in hindsight, and exact DP on a 6-loop/20-step instance. Report the DP gap rather than assuming it away, plus **metareasoning overhead** (tokens deciding ÷ tokens doing) and **allocation overrun distribution**. |
| **(d) Agent/tool creation** | AgentSquare +17.2% offline [measured]; MaAS query-conditioned at 6–45% cost [measured]; ToolMaker 80% repo→tool [measured]; TroVE 79–98% smaller toolbox [measured]. | **Total tokens (synthesis + execution) per successfully completed task**, beating both the best hand-written agent and an offline search, with synthesis inside one turn — plus **accuracy per tool retained** and **post-admission reliability** (does a self-written tool still work at invocation N?), which nobody measures. |
| **(e) Memory** | Generative Agents' three-term scorer with an ablation [measured]; LongMemEval's 30% drop across five axes [measured]. | **rate@k for the event a human judge marks decisive**, on held-out trajectories, beating both flat recency and lexical match — with a fitted decay exponent, a reported **abstention rate**, a **stale-verdict resurfacing rate driven to zero** after a correction, and a **Consilient GSM-IC**: accuracy drop when one plausible-but-irrelevant prior event is injected. |
| **(f) Multi-agent** | Kenton: no advantage without evidence asymmetry [measured]. Wang et al. (arXiv:2402.18272, ACL 2024): a strong-prompt single agent with demonstrations matches the best discussion method [measured]. Kapoor et al. (arXiv:2407.01502): accuracy without cost control is not a result [measured]. | A **monotone relationship between measured evidence-set divergence and panel gain, with gain indistinguishable from zero at zero divergence** — and an accuracy–cost Pareto plot strictly above a *demonstration-equipped* single agent at every cost level, on a held-out suite. Also: regress panel accuracy on best-member solo accuracy; a null residual means we built an expensive `max()`. |

---

## Evidence against our approach

Stated plainly.

1. **Multi-agent structure mostly does not beat a cost-matched, well-prompted single agent.** ACL 2024 [measured] finds a strong single-agent prompt matches the best discussion framework, with the multi-agent advantage appearing only when the baseline lacks demonstrations. Cambridge's 2026 work reports as *established* that vanilla debate underperforms majority vote at higher cost [measured] — identifier unverified. DeepMind [measured] finds "small or no advantage" for debate absent information asymmetry. Chen et al. [measured] show adding calls can make things *worse* on hard items.
   **What must be true for us to be the exception:** panel members must hold evidence the aggregator does not, and evidence sets must genuinely diverge. If we ever report a gain on symmetric-evidence tasks, the first hypothesis is a measurement bug, not an architecture win.
2. **Self-improvement has a proved ceiling.** Sharpening [measured] says no self-verification loop adds information. RLVR pass@k [measured] says apparent gains can be distribution narrowing measured at k=1. Model collapse [measured] and MAD [measured] say a library conditioned on its own output loses tails irreversibly, and that quality-biased filtering accelerates it.
3. **Long horizons degrade, and oversight degrades faster.** Project Vend [measured]: a month of autonomous operation ending in monotonic value destruction and an identity break. Monitor recall falls sharply with transcript length, worst mid-transcript [measured] — identifier unverified. UCL [measured, unverified] finds failures start in the first few steps and stay hidden until unrecoverable. Goal-directedness drops when a task becomes a sub-task [measured].
4. **Reward hacking is environment-determined.** o3 hacked 30.4% of RE-Bench runs versus 0.7% on HCAST, discriminated by scorer visibility [measured]. Any self-score the loop can read will be gamed.
5. **Memory can hurt.** Retrieval degrades performance where the model already knows the answer [measured]; a single plausible irrelevant sentence collapses accuracy [measured].

---

## The 25-year blind spot

Already solved, and we were about to reinvent it [asserted throughout]:

- **The deontic layer.** RACI is MOISE+'s `<role, mission, obligation>` join, 24 years late and less typed.
- **Enforcement regimes.** Regimentation vs regulation is our autonomy scale, chosen per norm.
- **Role schemas.** Gaia's liveness/safety split, permissions over named resources, acquaintance graph derived from protocols.
- **Role-addressed communication.** AGR's group scoping makes agents fungible; our dependency matrix conflates see/message/direct.
- **Typed dependencies.** TÆMS enables/facilitates/hinders/disables with magnitude and delay; Malone & Crowston's dependency taxonomy (DOI 10.1145/174666.174668) gives the precondition for safe parallel dispatch instead of discovering it through conflicts.
- **Capability matching and bidding.** LARKS' signature matching and Contract Net's announce/bid/award predate MCP retrieval by decades.
- **Value of computation and anytime composition.** Russell & Wefald 1991 already require estimating what a computation will change before spending on it.
- **Honest-collaborator theory.** Grosz & Kraus (DOI 10.1016/0004-3702(95)00103-4) formalise the obligation to report one's own infeasibility — the commitment no harness provides. STEAM (DOI 10.1613/jair.433) adds decision-theoretic communication and monitor-and-reorganise.

**What it does not solve.** Every one of these assumes a finite illocution set, cooperative honestly-instrumented agents, and an artefact that mediates every action. LLM agents emit unconstrained natural language, act through out-of-band channels, and report completion rather than failure. So: commitment *extraction* from free text, violation *detection* recall, norm-monitor accuracy against human ground truth (arXiv:2403.16517 is a pilot at 80 scenarios [measured]), and NL→policy compilation fidelity are all unearned numbers. Regimentation is cheap for us; regulation is where the research is.

---

## What to read first

1. **Kenton et al., arXiv:2407.04622** — the thesis, measured, with the null case named.
2. **Huang et al., arXiv:2412.01951** — the sharpening ceiling; read before designing any self-improvement.
3. **Song et al., arXiv:2412.02674** — the generation–verification gap, our runtime gating signal.
4. **MOISE+, DOI 10.1007/3-540-36127-8_12** — the schema RACI should have been.
5. **ORA4MAS, DOI 10.1007/s10458-009-9084-y** — regimentation vs regulation; the autonomy dial.
6. **Gaia, DOI 10.1023/A:1010071910869** — liveness/safety and role-scoped permissions.
7. **Kapoor et al., arXiv:2407.01502** — the evaluation methodology we are accountable to.
8. **Wang et al., arXiv:2402.18272** — the strong-baseline trap; makes our control mandatory.
9. **Shumailov et al., Nature 631** — why the skill library needs a fresh-data intake.
10. **Russell & Wefald, DOI 10.1016/0004-3702(91)90015-C** with **Whittle, DOI 10.2307/3214163** — value of computation supplies the index's numerator.
11. **Park et al., arXiv:2304.03442** with **ACT-R, doi:10.1037/0033-295X.111.4.1036** — triggered recall, and the threshold that lets it abstain.
12. **KnowNo, arXiv:2307.01928** — the only escalation rule with a coverage guarantee.

---

## What we searched and did not find

Honest nulls, and gaps the completeness critic named that this pass did not fill.

- **Loop mechanics.** No result on checkpoint/resume, idempotency, exactly-once, compensating transactions, leases, crash consistency, or dedup of repeated ambient work. Searched: durable execution, agent restart semantics. Found one Anthropic blog sentence [asserted]. This is the largest gap relative to a system that runs full-time.
- **Ambient/reactive arbitration as scheduling.** Nothing on rate-monotonic or EDF, mixed-criticality, priority inversion, admission control, backpressure, Little's law, or Borg/Omega/DRF. Bandits model *choice*, not *preemption*. Fifty years of theory, none of it here.
- **Agent security.** Nothing on prompt injection, confused deputy at the tool boundary, or agent-to-agent trust. AgentDojo and CaMeL-style defences were not returned. For agents holding repo and mail credentials this is the most consequential omission.
- **Self-adaptive systems.** MAPE-K / Kephart & Chess absent — literally the reference architecture for an ambient loop. Also absent: dwell-time/hysteresis and any stability analysis for the self-reorganising-org paper.
- **Human factors of supervising automation.** One philosophy paper, nothing empirical: no Bainbridge *Ironies of Automation*, Parasuraman & Riley, Endsley, Leveson STAMP/STPA, Rasmussen.
- **The "employee" framing.** No onboarding, no performance measurement over months, no demotion or rollback of a bad agent, no org drift.
- **Classical foundations not returned.** March 1991 exploration/exploitation — the canonical statement of the ambient-versus-reactive trade, and its absence is the sharpest tell. Also Holmström & Milgrom 1991 multitask principal-agent (predicts reward hacking from measurement distortion), Simon 1962, Conway 1968, Mintzberg 1979, Galbraith 1974, Ashby, Beer's VSM, Reinertsen on WIP limits, Gittins (present only via Whittle).
- **Evals.** τ-bench (policy-compliant agent–user interaction — the closest published analogue to this system's eval) and SWE-Lancer were not returned. The OpenAI Model Spec and Anthropic's constitution as *deployed* deontic layers were not returned.
- **NIST.** No AI RMF agent profile exists. The SP 800-53 COSAiS overlay project lists single-agent and multi-agent overlays but has published none [cited].

**Verification debt — do not cite without checking.** All 2026-dated identifiers are unverified in this pass: arXiv:2601.19921, 2602.11865, 2605.12366, 2607.05775, 2607.09197, 2607.09510; metr.org/blog/2026-1-29 and /2026-07-21; anthropic.com/research/multiagent-systems; AI Index 2026 [asserted] — unverified, check before citing. Model names across those sources (Opus 4.5/4.6/4.8, Mythos, Sonnet 5, GPT-5.2/5.4/5.5, Gemini 3.1) do not form a consistent version line; at least one source is likely confabulated. Also unverified: the Nested Learning arXiv id (none given), the Yan et al. COINE chapter's content (abstract unretrievable), Larimar's affiliation list, the Oxford attribution on 2607.05775, and the LARKS / Contract Net / Grosz–Kraus / Malone–Crowston content summaries, which come from memory rather than fetched text.

---

## Completeness critic

Ten researchers sharing a base model agree for reasons that are not evidence. This critic exists
to name what all of them missed.

**1. Sub-topics with no adequate coverage**

- **The actual loop mechanics.** 100+ entries, zero on checkpoint/resume, idempotency, exactly-once, compensation/saga, leases, crash-consistency, dedup of repeated ambient work. One Anthropic blog says "durable execution" and that is the entire treatment. A system running agents full-time will be defined by its restart semantics.
- **Ambient/reactive arbitration.** The brief's core. Covered only by bandits, which model *choice*, not *preemption*. Nothing on real-time scheduling (rate-monotonic, EDF), mixed-criticality, priority inversion, admission control, backpressure, Little's law, or cluster schedulers (Borg/Omega, DRF). "Reactive user work must interrupt ambient work" is a scheduling problem with 50 years of theory and none is here.
- **Agent security.** Nothing on prompt injection, confused deputy, or agent-to-agent trust. For agents with persistent tool access and email/repo credentials this is the largest omission in the set.
- **Self-adaptive systems engineering.** MAPE-K / autonomic computing is absent — literally the reference architecture for an ambient self-improvement loop.
- **Human factors of supervising automation.** One philosophy paper. Nothing empirical.
- **The "employee" framing itself.** No onboarding, performance measurement over months, demotion/rollback of a bad agent, or org drift.

**2. Suspicious claims**

- **The 2026 arXiv cluster (2601.19921, 2602.11865, 2605.12366, 2607.05775, 2607.09197, 2607.09510) is the fabrication hot zone.** All post-cutoff, all conveniently perfect fits, several with suspiciously round numbers ("1,794 trajectories, 63,000 steps"). Resolve every one against arxiv.org/abs/ and confirm title matches.
- **Model-name incoherence across entries.** "Opus 4.5", "Opus 4.6", "Opus-4.8", "Claude Mythos Preview", "Mythos 5", "Sonnet 5", "GPT-5.2/5.4/5.5", "Gemini 3.1" appear across three sources with no consistent version line. At least one of these entries is confabulated. Check the Anthropic multiagent-systems page and metr.org/blog/2026-1-29 by direct fetch.
- **"Classifier Context Rot" precision is implausible:** 98.6%→88%, 99.7%→69%, "~5%" — three different degradation curves quoted to a decimal. Fetch and check the abstract.
- **Woolley:** "proportion of women" is stated as a predictor; the paper's own mediation is via social sensitivity. Minor but it will be quoted wrong.
- **Padding:** Gaia and MOISE+ each appear twice under different angles. Ten researchers, ~8 duplicate slots.

**3. Predictably missed foundations**

- March 1991, *Exploration and Exploitation* — the canonical formalisation of exactly what ambient-vs-reactive trades off. Its absence is the single biggest tell.
- Holmström & Milgrom 1991, multitask principal-agent — predicts reward hacking from measurement distortion, before you observe it.
- Simon 1962 near-decomposability; Conway 1968; Brooks 1975; Mintzberg 1979 coordination mechanisms; Galbraith 1974 information-processing; Graicunas span of control; Ashby requisite variety; Beer's VSM.
- Safety: Perrow, Rasmussen's drift-to-danger, Leveson STAMP/STPA, Bainbridge *Ironies of Automation* (1983), Parasuraman & Riley 1997, Endsley situation awareness.
- Control theory: MPC, Ramadge–Wonham supervisory control, dwell-time/hysteresis to stop reorganisation thrash — the self-adaptive-org paper has no stability analysis and nobody noticed.
- Reinertsen, *Product Development Flow* — WIP limits and queueing for the ambient backlog.

**4. What a serious lab reads that is absent**

Kephart & Chess MAPE-K; τ-bench (policy-compliant agent-user interaction — the closest thing to this system's eval); AgentDojo + CaMeL-style injection defences; SWE-Lancer; OpenAI Model Spec and Anthropic's constitution as *deployed* deontic layers; Sutton & Silver *Era of Experience*; Gittins (only cited via Whittle).
