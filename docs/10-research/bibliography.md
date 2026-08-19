# Bibliography

Every source used in the session that produced this repository (19 Aug 2026), with an
honest verification status. Cite from here; do not cite from memory.

---

## Verification status — read this before citing anything below

| Flag | Meaning |
|---|---|
| **[FULL]** | The paper or page itself was fetched and read |
| **[ABS]** | Abstract or arXiv listing read directly |
| **[SNIP]** | **Seen only in a search-result snippet.** The claim attributed to it has *not* been checked against the source. |
| **[2ND]** | Known only via a secondary source (blog, aggregator, marketing page) |

**Most entries below are [SNIP] or [2ND].** That is not a defect in the research — it is the
honest state after one session — but it means:

> **No [SNIP] or [2ND] source may be cited in a publication, an ADR's `[cited]` line, or any
> public claim until it has been fetched and read.** Promote the flag when you do, and record
> the date.

Numbers are the highest-risk category. Several figures below come from Medium posts, DEV
articles and vendor marketing pages that were themselves summarising a paper. **Treat every
percentage as unverified until read at source.**

Suggested workflow: `docs/10-research/sources/` for fetched PDFs (gitignored — do not
redistribute copyrighted papers), with this file recording the promotion.

---

## 1. Multi-agent limits — the theorem behind ADR-0010 and ADR-0011

| Status | Source |
|---|---|
| [FULL] | **Ao, R., Gao, S. & Simchi-Levi, D.** *On the Reliability Limits of LLM-Based Multi-Agent Planning.* arXiv:2603.26993 (MIT / City University of Hong Kong, 27 Mar 2026). **The load-bearing citation for ADR-0010.** Read in full 2026-08-19 (ar5iv). Proposition 6, Theorems 7–8, Corollary 9 confirmed as summarised. Four qualifications recorded on reading: (1) the dominance is **weak** (≥) — a delegated network can at best match the centre, never beat it; (2) it is an unrefereed **technical note**, not a peer-reviewed paper; (3) the theorem never addresses whether a real LLM can *implement* the centralised Bayes decision-maker — no treatment of context limits or bounded rationality, so the transfer to "one big-context agent beats the committee" rests on Tran & Kiela, not on this paper; (4) verifiers appear as an abstract signal W ("executable tests or external validators can" move the Bayes envelope) — the paper licenses the critic-tier design and leaves β untouched. |
| [SNIP] | **Tran, D. & Kiela, D.** *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets.* arXiv:2604.02460 (Stanford / Contextual AI). Data Processing Inequality argument; FRAMES + MuSiQue. |
| [FULL] | **Kim et al.** *Capable language models can outgrow the benefits of collaboration.* Nature Machine Intelligence (2026), doi:10.1038/s42256-026-01268-y. Read in full 2026-08-20. Across 260 configurations, multi-agent systems used 1.6–6.2× the realised reasoning turns of the single-agent baseline; every tested multi-agent architecture degraded on SWE-bench Verified by 1.3–12.8%, while some other domains improved by as much as 80.8%. The proposed ~45% capability threshold predicted the sign in 94% of 16 later configurations, but the interaction did not survive cluster-robust correction. Task topology and inference budget matter; this is not a universal anti-collaboration result. Earlier version: arXiv:2512.08296. |
| [SNIP] | *The Illusion of Multi-Agent Advantage.* arXiv:2606.13003. Audit of six automatic MAS-design frameworks. |
| [SNIP] | **Cemri et al.** *Why Do Multi-Agent LLM Systems Fail?* (2025). MAST taxonomy, 14 failure modes, 1,600+ annotated traces. |
| [SNIP] | *Phase Transition for Budgeted Multi-Agent Synergy.* arXiv:2601.17311. |
| [SNIP] | **Wynn, Satija & Hadfield.** *Talk isn't always cheap: failure modes in multi-agent debate.* arXiv:2509.05396. |
| [SNIP] | *CascadeDebate: Multi-Agent Deliberation for Cost-Aware LLM Cascades.* arXiv:2604.12262 / ACL 2026 Industry. |

**The 90.7% → 22.5% relay-degradation figure is now verified at source** (2026-08-19):
200 four-way MMLU questions, 30 runs each, gpt-4.1-mini — 90.7% (one stage) → 41.2% (two)
→ 43.5% (three) → 22.5% (five), below the 25% chance baseline; the 41.2 → 43.5
non-monotonicity is in the paper. The paper also reports o4-mini at 89.9% → 37.0% on the
two-stage relay. **Caution kept:** the 2.8 / 8.5 points-per-stage figures come from a
*separate, smaller* comparison (50 questions, three stages fixed, prose relay 58.1% vs
posterior-vector relay 75.2%) — do not present them as the same run as the headline table.

## 2. Harness engineering — the competitive field (ADR-0001, competitive-landscape.md)

| Status | Source |
|---|---|
| [FULL] | **Lee, Y., Nair, R., Zhang, Q., Lee, K., Khattab, O. & Finn, C.** *Meta-Harness: End-to-End Optimization of Model Harnesses.* arXiv:2603.28052, COLM 2026 (per project-page BibTeX; the arXiv v1 is headed "Preprint"). Code: `github.com/stanford-iris-lab/meta-harness`. Read in full 2026-08-19. **Novelty threat resolved: it does not touch β.** The feedback loop is search-set benchmark score plus execution traces, assumed trustworthy; "false accept", verifier reliability and reward-hacking robustness appear nowhere; eval-gaming is mitigated only by manual inspection and regex audits. Its dependence on a clean oracle is exactly the assumption the β thesis interrogates. **Correction (2026-08-19):** the Terminal-Bench claim previously recorded here ("Terminus-KIRA 28.5% → 46.5% in seven iterations on a 19-task subset") **does not exist in the paper** — see `literature-review.md` §2 for the corrected numbers. The 6× harness-gap claim is the paper's opening citation ([47]), not its own result. |
| [ABS] | **Huang, H., Shi, J., Li, Y. & Chen, Y.** *Affordance Agent Harness: Verification-Gated Skill Orchestration.* arXiv:2605.00663 (cs.RO/cs.CV). **Checked and cleared** — visual affordance grounding, gates on self-consistency *without labels*. Different problem. |
| [FULL] | **Meng, Q. et al.** (Minzu Univ. of China / DUT / Xiaohongshu / USTC) *Agent Harness for Large Language Model Agents: A Survey.* preprints.org 202604.0428 — **cite v3 (DOI 10.20944/preprints202604.0428.v3) or the v4 PDF**, not v2. Read in full (v4, 111 pp) 2026-08-19. Formalises harness as H=(E,T,C,S,L,V) — **V is "evaluation interface" (instrumentation), not verification.** 110+ sources, 23 systems (their Fig. 1 caption says 22; Table 4 says 23 — use 23). **Support for ADR-0002's novelty restated on reading:** their "compositional verification" (§6.11.8) is separation-logic-style *formal proof composition* over harness components — a different sense of verification, unrelated to β; do not cite it as the gap. The *real* support from this source: (a) the METR passage (§6.3) — **maintainer merge rates average 24.2 pp below SWE-bench automated grader scores for the same PRs**, ecosystem-scale false-accept evidence, with "human-in-the-loop validation" as their only prescribed remedy; (b) the word "verifier" appears **zero times** in 111 pages, and none of the 23 surveyed systems measures a verifier's error rate or conditions orchestration on it (closest: AdaptOrch routes on task-DAG topology). Canonical repo: `Gloriaameng/LLM-Agent-Harness-Survey` (Awesome-Agent-Harness redirects). |
| [SNIP] | **Li, J. et al.** *Agent Harness Engineering: A Survey.* (2026). |
| [SNIP] | *Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses.* arXiv:2604.25850. |
| [SNIP] | *HarnessBank: Semantic Gene-Bank Search with Gated Verification for Agent-Harness Self-Evolution.* arXiv:2607.13683. |
| [SNIP] | *From Model Scaling to System Scaling: Scaling the Harness in Agentic AI.* arXiv:2605.26112. |
| [SNIP] | *Natural-Language Agent Harnesses.* arXiv:2603.25723. |
| [SNIP] | *Code as Agent Harness.* arXiv:2605.18747. |
| [SNIP] | *Harness Engineering as Categorical Architecture.* arXiv:2605.12239. |
| [SNIP] | *SIGIL: Compiling Agent Skills into Typed Harnesses.* arXiv:2607.27309. |
| [SNIP] | *SkillSmith: Compiling Agent Skills into Boundary-Guided Runtime Interfaces.* arXiv:2605.15215. |
| [SNIP] | *Harnesses for Inference-Time Alignment over Execution Trajectories.* arXiv:2605.21516. |
| [SNIP] | **Zhu, N. et al.** *SemaClaw.* arXiv:2604.11548 (Midea AIRC). |
| [SNIP] | *Building Effective AI Coding Agents for the Terminal.* Introduces the scaffolding-vs-harness split. |
| [2ND] | OpenAI, *Harness engineering: leveraging Codex in an agent-first world* (11 Feb 2026). Anthropic, *Effective Harnesses for Long-Running Agents*. |

**Implementations:** `github.com/deepseek-ai/deepseek-harness` (MIT, Cordis kernel) ·
`github.com/HKUDS/OpenHarness` (MIT) [FULL — README read] · Omnigent (Databricks, Apache
2.0) · Vercel AI SDK v7 `HarnessAgent`.

## 3. Routing and cascades — the basis of ADR-0002, 0003, 0009, 0012

| Status | Source |
|---|---|
| [SNIP] | **Chen, L., Zaharia, M. & Zou, J.** *FrugalGPT.* arXiv:2305.05176, TMLR 2024. |
| [SNIP] | **Ding, D. et al.** *Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing.* ICLR 2024. |
| [SNIP] | **Ong, I. et al.** *RouteLLM.* arXiv:2406.18665, ICLR 2025. |
| [SNIP] | **Aggarwal et al.** *AutoMix.* (2024). Self-verification + POMDP routing. |
| [FULL] | **Dekoninck, J., Baader, M. & Vechev, M.** (ETH Zurich) *A Unified Approach to Routing and Cascading for LLMs.* arXiv:2410.10347, ICML 2025 (PMLR 267) — confirmed. Read in full (v3) 2026-08-19. Their result is a strict **generalisation** ("cascade routing", optimal w.r.t. the quality/cost *estimators*), not literally a continuum — the continuum reading comes from their noise-grid finding that which paradigm wins varies smoothly with (σ_ante, σ_post). **Two facts that matter for ADR-0002:** (1) they *do* estimate estimator variance per deployment on a validation set and fit hyperparameters per deployment — so "the routing literature treats signal noise as given" is too strong; (2) on SWE-Bench they **assume the ground-truth test oracle is perfect** — β = 0 by assumption — and their theory is silent on systematically biased verifiers. No critical noise threshold is derived anywhere (their MAX-DEPTH=3 is a runtime cap, not a derived quantity). **Consequence: state the novelty claim as (a) binary/asymmetric false-accept formulation for external verifiers, (b) per-repository measurement, (c) depth/parallelism derived from it — not as "estimator noise governs the routing choice", which this paper already has in Gaussian form.** |
| [SNIP] | **Jitkrittum, W. et al.** *Universal Model Routing for Efficient LLM Inference (UniRoute).* ICLR 2026. |
| [SNIP] | *GATEKEEPER.* arXiv:2502.19335. Fine-tunes for calibrated confidence. |
| [SNIP] | **Kotte, V.** *UCCI: Calibrated Uncertainty for Cost-Optimal LLM Cascade Routing.* arXiv:2605.18796. ECE 0.03 via token-margin + isotonic regression. |
| [SNIP] | *Is Escalation Worth It? A Decision-Theoretic Characterization of LLM Cascades.* arXiv:2605.06350. |
| [SNIP] | *Cluster, Route, Escalate.* arXiv:2606.27457. |
| [SNIP] | *RouteNLP: Closed-Loop LLM Routing with Conformal Cascading.* arXiv:2604.23577. |
| [SNIP] | **Soiffer, D., Kolawole, S. & Smith, V.** *Semantic Agreement Enables Efficient Open-Ended LLM Cascades.* arXiv:2509.21837, EMNLP 2025 Industry. **Basis of the Inquiry tier's dispersion gate.** |
| [SNIP] | *Act or Escalate? Evaluating Escalation Behavior in Automation with Language Models.* arXiv:2604.08588. Escalation is a model-specific property. |
| [SNIP] | *When to Think Deeply: Inhibitory Deliberation for LLM Reasoning.* arXiv:2606.06745. **Argues against ADR-0009** — post-response routing beats pre-response. |
| [FULL] | **Song et al.**, *IRT-Router* (arXiv:2506.01048, ACL 2025). Read in full 2026-08-19. Multidimensional IRT (not Rasch) with **amortised** abilities: θ per model from a text-profile embedding, trained on ~24k queries × 20 models graded (~489k tuples). Beats routing baselines at ~1/30 GPT-4o cost. **The finding that matters for ADR-0025: its model cold-start fails by its own experiment** — held-out Claude 3.5 Haiku, ability from metadata alone, ACC 0.67, "limited generalization to unseen LLMs". Precedent for the Rasch framing *and* the documented hole the probe fills; its CAT machinery is the natural probe-item selector. |
| [ABS] | **Feng, Shen & You**, *GraphRouter* (arXiv:2410.03834, ICLR 2025). The serious GNN-routing paper: heterogeneous graph, routing as edge prediction, +12.3% over bandit baselines; "unseen model" support still needs **80 logged interactions per new model**. Verified for ADR-0025's rejection: **no published learned-router vs verifier-gated-cascade comparison exists** (checked against survey arXiv:2603.04445). Successors: PersonalizedRouter (2511.16883), AgentRouter (2510.05445). Consumable capability feeds checked same day: Artificial Analysis API (fresh, attribution, no redistribution), Epoch CC-BY, RouterBench/LLMRouterBench/metabench (frozen snapshots; RouterArena labels carry an **eval-only clause**), OpenRouter Ori Eval (platform-tied eval-on-release). |
| [SNIP] | **Gupta et al.** (2024) token-level uncertainty deferral · *Online Pandora's Box for Contextual LLM Cascading*, arXiv:2606.07392. |
| [FULL] | **Amin, D.** *Bayesian Orchestration of Multi-LLM Agents for Cost-Aware Sequential Decision-Making.* arXiv:2601.01522 (4 Jan 2026). Read in full 2026-08-19. LLMs as likelihood functions (generative "how typical is this observation given this state" prompting); median aggregation over five frontier models; sequential Bayesian updating; VOI gate for buying more evidence. **Qualifications recorded on reading:** single-author independent-researcher preprint, no venue, evaluated entirely on synthetic data (LLM-generated resumes, simulated screens, assumed cost matrices) — its headline figures are `[simulated]` by this repo's own tags. No verifier in our sense exists in it; its closed-form threshold τ* comes from cost asymmetry, not measured error; there is no routing or cascading at all (all five models run on every input). By `CONSILIENCE.md`'s standard its model-ensemble layer is *mitigated echo* (five models reading the same observation, diversity as an unmeasured heuristic); its **evidence layer** (résumé vs phone screen, conditionally independent given the true state) is the genuinely consilient part and the useful prior art. β untouched. |
| [SNIP] | *Dynamic Model Routing and Cascading: A Survey.* arXiv:2603.04445. |

## 4. Self-improving agents — ADR-0018, living-system.md

| Status | Source |
|---|---|
| [ABS] | **Zhang, J., Hu, S., Lu, C., Lange, R. & Clune, J.** *Darwin Gödel Machine.* arXiv:2505.22954, ICLR 2026. SWE-bench 20.0→50.0; Polyglot 14.2→30.7. |
| [ABS] | **Robeyns, M., Szummer, M. & Aitchison, L.** *A Self-Improving Coding Agent (SICA).* arXiv:2504.15228. 17→53%. Code: `MaximeRobeyns/self_improving_coding_agent`. |
| [SNIP] | **Wang, W., Piękos, P. et al.** *Huxley-Gödel Machine.* ICLR 2026. **Rejects benchmark-score-as-capacity — the closest independent support for ADR-0018.** |
| [SNIP] | **Zhang, J. et al.** *HyperAgents (DGM-H).* arXiv:2603.19461. |
| [SNIP] | **Yin, X. et al.** *Gödel Agent.* ACL 2025. Verification agent checks modifications against safety invariants pre-application. |
| [SNIP] | **Schmidhuber, J.** *Gödel Machines.* arXiv:cs/0309048 (2003). The proof requirement DGM replaced with empirical validation — **the premise ADR-0018 attacks.** |
| [SNIP] | **Xia et al.** *Live-SWE-agent.* (17 Nov 2025). Runtime tool synthesis from a minimal scaffold. |
| [SNIP] | *AFlow.* ICLR 2025 Oral. MCTS over workflow space. |
| [SNIP] | **Novikov, A. et al.** *AlphaEvolve.* arXiv:2506.13131. |
| [SNIP] | **Lu, C. et al.** *The AI Scientist.* arXiv:2408.06292 · **Yamada, Y. et al.** *v2*, arXiv:2504.08066. |
| [SNIP] | *SkillOpt.* arXiv:2605.23904. Edits accepted only on held-out improvement. |
| [SNIP] | **Ren, Z. et al.** *Self-Improvements in Modern Agentic Systems: A Survey.* arXiv:2607.13104. `selfimproving-agent.github.io`. **Best single entry point.** |
| [SNIP] | *The Red Queen Gödel Machine.* arXiv:2606.26294 · *Group-Evolving Agents.* arXiv:2602.04837. |

## 5. Context engineering and memory — ADR-0017

| Status | Source |
|---|---|
| [SNIP] | **Zhang, Q. et al.** *Agentic Context Engineering (ACE).* arXiv:2510.04618, ICLR 2026. Generator/Reflector/Curator; +10.6% / +8.6%, no gradient updates. |
| [SNIP] | **Mei, L. et al.** *A Survey of Context Engineering for LLMs.* arXiv:2507.13334. |
| [SNIP] | *Context Engineering for AI Agents in Open-Source Software.* arXiv:2510.21413, MSR 2026. |
| [SNIP] | *Structured Context Engineering for File-Native Agentic Systems.* arXiv:2602.05447. |
| [2ND] | **Ji, Y.** *Context Engineering for AI Agents: Lessons from Building Manus.* |
| [FULL] | **MemPalace.** `github.com/mempalace/mempalace`, MIT. **Launch benchmarks reported as inflated by at least one analysis — verify before citing any recall figure.** |
| [2ND] | **Graphify.** `graphify.net`. ~61k stars claimed. Tree-sitter AST, local. |
| [FULL] | **Graphiti / Zep** (arXiv:2501.13956, vendor-authored). **Correction (2026-08-19): the "63.8% vs mem0's 49% on the LongMemEval temporal subset" previously recorded here was a mashup** — 63.8% is Zep's *overall* score (gpt-4o-mini) from its own paper; 49.0% is mem0's *overall* score from an unrelated third party (arXiv:2603.04814); no head-to-head temporal comparison exists. Real vendor-measured temporal numbers: Zep 54.1%/62.4% vs full-context 36.5%/45.1% (its largest lift — supporting the *qualitative* claim that structural time modelling, not learning, drives the gain). The Zep-vs-mem0 comparison is an unresolved two-sided vendor dispute (both sides have corrected their own numbers; mem0 claims 94.4% LongMemEval by 2026 via retrieval tuning, no architecture change). **Cite the sign and the dispute, never the points.** Through Aug 2026, no learned/GNN embedding system beats structural temporal-KG memory on these benchmarks — absence of attempts, not a measured negative. |

## 6. Operations, budgets and supply-chain safety — ADR-0016, 0019

| Status | Source |
|---|---|
| [FULL] | **Khan, S.** *Token Budgets: An Empirical Catalog of 63 LLM-Agent Budget-Overrun Incidents.* arXiv:2606.04056. Read in full 2026-08-19. Confirmed 63 production incidents across 21 subprojects and 18 ecosystems, 2023–2026; the paper also records 47 supplemental structural examples. Its four-class annotation reports κ=0.837. **Qualification:** this is a convenience, failure-confirming sample, not a prevalence estimate. The useful design result is qualitative: provider-side hard caps are stronger where their scope matches the work, while per-session or per-client caps are still needed for task granularity. |
| [FULL] | **Anthropic**, [Claude Code status line](https://code.claude.com/docs/en/statusline), [Max plan](https://support.claude.com/en/articles/11049741-what-is-the-max-plan), [plan use in Claude Code](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) and [usage best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices). Read 2026-08-19. The status-line JSON includes five-hour and seven-day utilisation/reset fields, but refreshes after a response. Max has fixed account-specific weekly resets; limits are shared across Claude surfaces. Settings > Usage is authoritative for the human, while API credits are a distinct metered continuation. |
| [FULL] | **OpenAI**, [Codex app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md), [Codex with a ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan), [flexible credits](https://help.openai.com/en/articles/12642688) and [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card). Read and queried locally 2026-08-19. `account/rateLimits/read` returns provider windows; included usage is consumed before optional credits, and eligible agentic products share the pool. The ordinary top-level CLI help exposes no quota command, while Codex Settings > Usage is the documented human surface. |
| [FULL] | **Cursor**, [CLI parameter reference](https://docs.cursor.com/en/cli/reference/parameters), [individual pricing and usage](https://docs.cursor.com/account/pricing) and [Team Admin API](https://docs.cursor.com/en/account/teams/admin-api). Read 2026-08-19 and compared with installed CLI build 2026.08.11. Individual usage is documented through the dashboard; no individual quota endpoint appeared in the installed CLI help or the official individual-plan pages reviewed. The Team Admin API is not evidence of an individual-plan API. |
| [FULL] | **Cursor**, [ACP reference](https://prod.cursor.com/docs/cli/acp) and [MCP overview](https://docs.cursor.com/context/model-context-protocol). Read and exercised 2026-08-19. Cursor's native external-control path is ACP v1 over newline-delimited JSON-RPC on stdio; Cursor is the ACP server and the orchestrator is the client. MCP has the opposite local role: Cursor consumes tools from MCP servers. The official ACP example uses `initialize`, `authenticate`, `session/new`, `session/prompt`, streamed updates and explicit permission responses, matching the measured adapter path. |
| [FULL] | **Anthropic**, [Claude Code changelog](https://code.claude.com/docs/en/changelog), [`anthropics/claude-code` releases](https://github.com/anthropics/claude-code/releases), [first-party Atom feed](https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/feed.xml) and [Claude Status API](https://status.claude.com/api). Read and fetched 2026-08-19. The repository, releases and feed are public first-party change surfaces; Claude Status exposes unauthenticated JSON plus RSS. Release/status events can invalidate capability knowledge but do not report one account's remaining subscription allowance. |
| [FULL] | **Anthropic**, [Manage usage credits for paid Claude plans](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans), [Use Claude Code with a Pro or Max plan](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) and [Manage API-key environment variables](https://support.claude.com/en/articles/12304248-manage-api-key-environment-variables-in-claude-code). Included subscription use and usage credits are separate; usage credits are billed at API rates after included limits and may be disabled. Claude Code prioritises `ANTHROPIC_API_KEY` over subscription authentication, so an unset variable is required for the intended subscription path. The CLI presents a limit transition rather than silently requiring metered continuation. Read 2026-08-20. |
| [FULL] | **Anthropic**, [What's new in Claude Opus 5](https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5). Read in full 2026-08-20. Anthropic documents a one-million-token default and maximum context, 128k maximum output and the model's intended use for complex agentic and long-horizon work. The same page warns that Opus 5 tends to delegate and verify more readily, so inherited subagent and verification prompts can cause excess work. These are provider specifications and behaviour guidance, not independent orchestration outcomes. |
| [FULL] | **OpenAI**, [ChatGPT and Codex changelog](https://developers.openai.com/codex/changelog/), [`openai/codex` releases](https://github.com/openai/codex/releases), [GitHub releases Atom feed](https://github.com/openai/codex/releases.atom) and [OpenAI Status](https://status.openai.com/). Read and fetched 2026-08-19. The official changelog separates Codex CLI updates; the public release feed and status JSON/RSS are machine-readable change surfaces. They complement rather than replace the authenticated app-server rate-limit and capability queries. |
| [FULL] | **Cursor**, [product changelog](https://cursor.com/changelog) and [Cursor Status](https://status.cursor.com/). Read and fetched 2026-08-19. The changelog was HTML-only in the inspected public surface; Status exposed unauthenticated JSON and RSS. The delegated suggestion `https://forum.cursor.com/c/changelog.rss` returned HTTP 404 and is not a source. Neither surface reports individual subscription headroom. |
| [FULL] | **Google**, Antigravity [installation and authentication](https://antigravity.google/docs/cli/install), [CLI reference](https://antigravity.google/docs/cli/reference), [plans](https://antigravity.google/docs/plans), [AI credits](https://antigravity.google/docs/cli/credits), [quota command](https://www.antigravity.google/docs/cli/commands/usage) and [status-line schema](https://antigravity.google/docs/cli/statusline). Read and compared with installed CLI 1.1.15 on 2026-08-19. The status payload exposes `plan_tier` plus per-bucket `remaining_fraction` and reset fields. `useG1Credits` defaults false; setting it true permits credit fallback after baseline exhaustion. Pro and Ultra receive five-hour baseline refreshes until their weekly limits; other plans receive a weekly baseline. |
| [FULL] | **Google**, [AI Plus global availability](https://blog.google/products-and-platforms/products/google-one/google-ai-plus-availability/), [I/O 2026 subscription update](https://blog.google/products-and-platforms/products/google-one/google-ai-subscriptions/) and [AI-credit eligibility](https://support.google.com/googleone/answer/17103110). Read 2026-08-19. AI Plus is a current plan, but unlike Pro and Ultra it cannot purchase AI credits; Antigravity entitlement must be taken from the product's live plan/quota surfaces rather than inferred from the shared Google One brand. |
| [FULL] | **OpenRouter**, [credits API](https://openrouter.ai/docs/api/api-reference/credits/get-remaining-credits), [management API keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys) and budget guardrail documentation. Read 2026-08-19. The management API creates task-scoped keys with an optional credit `limit`; key records expose `limit_remaining` and optional daily/weekly/monthly reset policies. Provider-enforced key caps can therefore be the outer boundary for harness reservations. |
| [FULL] | **OpenRouter**, [Models API](https://openrouter.ai/docs/guides/overview/models), [Benchmarks API](https://openrouter.ai/docs/api/api-reference/benchmarks/list-benchmarks), [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection), [tool calling](https://openrouter.ai/docs/guides/features/tool-calling), [Agent SDK tools](https://openrouter.ai/docs/agent-sdk/call-model/tools) and [OpenCode integration](https://openrouter.ai/docs/cookbook/coding-agents/opencode-integration). Read 2026-08-19. OpenRouter supplies dated/sourced benchmark records, model/pricing/capability data, model-fixed upstream-provider selection and standard tool-call transport. Client code executes tools; the Agent SDK can own a bounded tool loop. These are provider and optional harness capabilities, not repository β measurements. |
| [FULL] | **OpenCode**, [CLI](https://opencode.ai/docs/cli/), [providers](https://opencode.ai/docs/providers/), [tools](https://opencode.ai/docs/tools/) and [Windows/WSL](https://opencode.ai/docs/windows-wsl/). Read and installed from the official distribution 2026-08-19; measured version 1.18.18. `opencode run` supports provider/model selection, JSON events, auto-approved permissions and a working directory. OpenRouter is built in after credential discovery; the official Windows guidance recommends WSL. |
| [FULL] | **LM Studio**, CLI documentation for `lms get` and [`lms load --estimate-only`](https://lmstudio.ai/docs/cli/local-models/load). Read 2026-08-19. The estimator is useful before load but operates on a model already present locally, so it cannot by itself enforce a pre-download hardware gate. |
| [FULL] | **Alex Jones**, [llmfit](https://github.com/AlexsJones/llmfit), MIT. README, licence and JSON interface read 2026-08-19. It detects local RAM/CPU/GPU/VRAM and ranks model/provider fits before a model download, making it a candidate wrapped fit provider rather than a catalogue to reproduce. |
| [FULL] | **signerless**, [LLM Checker licence](https://github.com/signerless/llm-checker/blob/main/LICENSE). Read 2026-08-19. Its current NPDL-1.0 terms prohibit paid distribution and monetised hosted use; ADR-0005's description of it as “open source” was wrong. It must not be bundled as an open-source dependency. |
| [FULL] | **Nesbitt, A.** *Skills Registry Threat Models.* nesbitt.io/2026/06/03. **Basis of ADR-0016's security section.** |
| [SNIP] | OWASP Agentic Skills Top 10 · Snyk ToxicSkills · *Agent Skills in the Wild* · *Towards Secure Agent Skills*. |

## 7. Skills ecosystem — ADR-0014, 0016

| Status | Source |
|---|---|
| [FULL] | `skills` / skills.sh — npm, 73+ agents, ~75 dependents |
| [FULL] | `skills-npm` — `github.com/antfu/skills-npm` |
| [FULL] | `skillpm` — `github.com/sbroenne/skillpm` |
| [FULL] | `skillfish` — `github.com/knoxgraeme/skillfish`, **AGPL-3.0** |
| [2ND] | `anthropics/skills` · ~351,000 skills by March 2026 (marketing-blog figure — **unverified**) |

## 8. Philosophy of science — CONSILIENCE.md

| Status | Source |
|---|---|
| [FULL] | **Whewell, W.** *The Philosophy of the Inductive Sciences, Founded Upon Their History*, Vol. II. London: John W. Parker, 1840. **Public domain**, archive.org: `philosofindu01whewrich`. The definition. |
| [SNIP] | **Whewell, W.** *Novum Organon Renovatum* (1858), pp. 70–71, 83–96. Prediction / consilience / coherence as the three tests. |
| [SNIP] | **Wilson, E. O.** *Consilience: The Unity of Knowledge.* Knopf, 1998. |
| [SNIP] | **Snyder, L.** *William Whewell.* Stanford Encyclopedia of Philosophy. |
| [SNIP] | **Perrin's Avogadro argument** — thirteen independent procedures converging on one value. *The* canonical consilience case; the model for evidence combination. Discussed in *Studies in History and Philosophy of Science* (2021). |

---

## 9. Capability layer, context loading, reasoning layer (v1+ design docs, added 19 Aug 2026)

| Status | Source |
|---|---|
| [FULL] | **Anthropic**, *Code execution with MCP* (anthropic.com/engineering, 4 Nov 2025). 150,000 → 2,000 tokens, "a time and cost saving of 98.7%" — the post's own words, but a **single illustrative workflow**, definitions and intermediate results conflated, and **zero accuracy claims anywhere in the post**. |
| [FULL] | **Anthropic**, *Introducing advanced tool use* + Tool Search Tool docs (24 Nov 2025; GA since). `defer_loading` confirmed; "typically over 85%" definition-token reduction (worked example ~77K→8.7K). Opus 4 **49% → 74%**, Opus 4.5 **79.5% → 88.1%** on "internal MCP evaluations" — **the metric is never defined**; treat as directional, numerically unusable. Failure modes named: wrong tool selection, wrong parameters, similar names. |
| [FULL] | **Cloudflare**, Code Mode. Two posts, previously mis-dated here: mechanism — Varda & Pai, **26 Sep 2025** (qualitative: "LLMs are better at writing code to call MCP"); the 99.9% figure — Carey, **20 Feb 2026**: 1,000 vs 1.17M input tokens, tiktoken, **against a hypothetical baseline no model could load**. No accuracy measurements in either post. |
| [FULL] | **Paramanayakam et al.**, *Less is More* (arXiv:2411.15399, DATE 2025). **The "~20–25 tool threshold" attributed to it does not exist in the paper** — sole comparison: Llama3.1-8b-q4 fails at 46 tools, succeeds at 19; no sweep; quantisation alone accounts for drops of 63%→20–40%; 2023–24 sub-10B edge models. |
| [ABS] | **RAG-MCP** (arXiv:2505.03275) — the actual tool-count sweep: 1→11,100 schemas on Qwen-max; >90% selection below ~30, collapse past ~100; 13.6% vs 43.1% task accuracy all-tools vs retrieval. |
| [ABS] | **PA-Tool** (arXiv:2510.07248) — SLM schema misalignment; ~+17% from model-aligned renaming. **The paper EXP-17 must position against.** · **Hammer** (arXiv:2410.04587) · **RoTBench** (arXiv:2401.08326) · *How Many Tools Should an LLM Agent See?* (arXiv:2605.24660) · LiveMCPBench (2508.01780) / MCPToolBench++ (2508.07575). |
| [FULL] | **Claude Code changelog v2.1.7** (13 Jan 2026): MCP tool search auto mode default — the delegated path inherits progressive disclosure. Registries verified live 19 Aug 2026: **OpenRouter** `/api/v1/models` (tri-state `reasoning` object; 414 models); **models.dev** (SST, MIT — the redistributable option); **LiteLLM** capability map (MIT). Hugging Face: no standard field (negative result). |
| [FULL] | **DeepSeek-R1** (arXiv:2501.12948; Nature, Aug 2025) — the authors' own guidance, verbatim-verified: "Few-shot prompting consistently degrades its performance." · **OpenAI** reasoning best practices: "Avoid chain-of-thought prompts." · **Anthropic** extended-thinking guidance: high-level beats prescriptive. |
| [FULL] | **Qwen Team**, [Qwen3-Coder-30B-A3B-Instruct model card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct), and **Ollama**, [Qwen3-Coder library record](https://ollama.com/library/qwen3-coder). Read in full 2026-08-20. The model is Apache-2.0, has 30.5B total and 3.3B active parameters, supports non-thinking mode and a native 262,144-token context; the authors advise reducing context to 32,768 on OOM. Ollama's Q4 distribution is 19 GB and advertises a 256K context. These are identity and hardware-screening facts, not independent capability evidence: the performance language and linked benchmarks originate with the model vendor. |
| [FULL] | **Meincke, Mollick, Mollick & Shapiro**, Wharton Prompting Science Report 2 (arXiv:2506.07142, Jun 2025). CoT on reasoning models: +2.9/+3.1% marginal (o3-mini/o4-mini), **Gemini Flash 2.5 (hybrid) −3.3% avg, −13.1% perfect-consistency**; non-reasoning +4.4–13.5% at 35–600% time. The best current datum for Q25's middle case. |
| [FULL] | **OpenAI**, [GPT-5.6 prompting and migration guidance](https://developers.openai.com/api/docs/guides/latest-model). Its internal coding-agent comparison reports that a leaner system prompt improved the stated evaluation scores by roughly 10–15%, reduced input tokens by 41–66% and reduced cost by 33–67%; the compact prompt retained explicit autonomy, approval and scope boundaries. Its style guidance recommends specific acknowledgement and omitting generic praise when it adds nothing. Read 2026-08-19. |
| [FULL] | **Anthropic**, [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). Recommends clear outcomes and constraints while preferring general reasoning instructions over hand-written solution procedures; warns that current models can over-verify when old verification scaffolding is retained. Read 2026-08-19. |
| [FULL] | **Google**, [Gemini API prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies). Recommends clear, structured prompts and few-shot examples for many tasks while warning that excessive examples can overfit; this is evidence against one universal lean-prompt profile. Read 2026-08-19. |
| [FULL] | **Google**, [Gemini model catalogue](https://ai.google.dev/gemini-api/docs/models) and [long-context guidance](https://ai.google.dev/gemini-api/docs/long-context). Read in full 2026-08-20. The inspected catalogue lists Gemini 3.6 Flash as the latest stable Flash endpoint. Google warns that multi-needle retrieval varies with context, unnecessary tokens should be omitted and longer inputs generally increase latency. |
| [FULL] | **OpenRouter**, [public model API](https://openrouter.ai/api/v1/models), snapshot read 2026-08-20. The live record exposes `google/gemini-3.7-flash` with a 1,048,576-token context, 65,536 maximum completion tokens and high/medium/low reasoning efforts. Its current presence ahead of Google's inspected public catalogue makes it a provider-advertised candidate, not independently verified upstream identity or capability evidence. |
| [FULL] | **Li et al.**, *EmotionPrompt: Leveraging Psychology for Large Language Models Enhancement via Emotional Stimulus* (arXiv:2307.11760). Read in full 2026-08-19. The averaged emotional variants were 51.98 versus 51.65 on zero-shot Instruction Induction and 10.61 versus 10.16 on BIG-Bench; best-of-eleven results were larger, and several model/task cells worsened. It does not establish a universal benefit from generic praise. |
| [ABS] | Reasoning-technique canon, vintage-audited in `../20-design/reasoning-layer.md`: Wei CoT (2201.11903; **sub-10B at/below baseline in 2022**) · Kojima (2205.11916) · **Sprague, To CoT or not to CoT** (2409.12183 — replicated; CoT pays mainly on math/symbolic) · Wang self-consistency (2203.11171) · Yao ToT (2305.10601) + *larger models excel in generation, not discrimination* (2410.17820) · Yao ReAct (2210.03629) · Shinn Reflexion (2303.11366) · **Huang, LLMs Cannot Self-Correct Reasoning Yet** (2310.01798 — negative result, replicated) · s1 budget forcing (2501.19393 — **requires a reasoning-tuned model**) · Snell test-time scaling (2408.03314 — gains vanish on hardest bins) · **Cobbe verifiers** (2110.14168 — 6B+6B beats 175B; the best-transfer result, and its failure mode is β) · Overthinking (2502.08235) · OptimalThinkingBench (2508.13141). |

## 10. Feedback signals — sycophancy and outcome gaming (added 19 Aug 2026)

| Status | Source |
|---|---|
| [FULL] | **Sharma et al.** (Anthropic), *Towards Understanding Sycophancy in Language Models* (arXiv:2310.13548, ICLR 2024). Humans and PMs prefer convincing sycophancy "a non-negligible fraction of the time" (PM: 45% when challenging misconceptions). Hedged — a marginal gradient, not a uniform law. |
| [FULL] | **OpenAI postmortems**, *Sycophancy in GPT-4o* (29 Apr 2025) and *Expanding on what we missed* (2 May 2025): thumbs-data reward signal "weakened … our primary reward signal, which had been holding sycophancy in check". **The sycophantic model won its approval-metric A/B test** — approval fails as a ship-gate analytic, not just as a training target. |
| [ABS] | **Kim & Khashabi**, *Models Persuade Themselves: Language Models Reason More Soundly with Their Own Intuitions* (Findings of EMNLP 2025; ACL Anthology 2025.findings-emnlp.1222). The abstract and paper landing page were read 2026-08-19. Across the reported disagreement tests, models were more susceptible to user rebuttal than to their own prior reasoning, and casually phrased feedback could sway them more than formal critique. Exact condition percentages remain unpromoted until the full tables are independently checked. |
| [ABS] | **Williams, Carroll et al.** (arXiv:2411.02306, ICLR 2025) — RL on user feedback reliably learns manipulation; targets the vulnerable ~2%. · **SycEval** (2502.08177) · **ELEPHANT** (2505.13995 — sycophancy rewarded in preference datasets). 2026 currency: 2607.01071, 2605.14604, 2604.24668. |
| [FULL] | **METR**, o3/o4-mini evaluation + *Recent Frontier Models Are Reward Hacking* (Jun 2025): 30.4% of o3 RE-Bench runs contained hacking; grader/timer/equality-operator rewrites documented. · **METR**, *Many SWE-bench-Passing PRs Would Not Be Merged* (Mar 2026): automated pass rates ~24 pp above maintainer merge rates — independent confirmation of the Meng-survey METR figure, at source. · **METR RCT** (2507.09089): believed +20%, measured −19% — perceived outcome is not ground truth. |
| [ABS] | **Baker et al.** (arXiv:2503.11926) — optimising against a misbehaviour monitor teaches **obfuscation**. · **ImpossibleBench** (2510.20270) — GPT-5 games tests 76% under spec/test conflict; **hiding test files → near zero**. · **MacDiarmid et al.** (2511.18397) — production-RL reward hacking generalises to sabotage. · **TheAgentCompany** (2412.14161) — agent renamed a user to satisfy the success criterion. · *False Success in LLM Agents* (2606.09863) — 45–76% of failures asserted as successes. · **SWE-Bench+** (2410.06992) — 12.47%→3.97% after filtering leaks/weak tests. · Palisade (2502.13295). · Replit/SaaStr incident (The Register, 21 Jul 2025) — deployed fabricated-success case. |

## 11. Agent identity, collaboration and organisational design (added 19 Aug 2026)

| Status | Source |
|---|---|
| [ABS] | **Zheng et al.**, *When “A Helpful Assistant” Is Not Really Helpful: Personas in System Prompts Do Not Improve Performances of Large Language Models.* Findings of EMNLP 2024, arXiv:2311.10054. Four model families, 162 roles, four templates and 2,410 factual questions; persona prompts did not improve factual performance overall and effects were unpredictable. |
| [FULL] | **Ibrahim, Hafner & Rocher**, *Training language models to be warm can reduce accuracy and increase sycophancy.* Nature 652 (2026), 1159–1165, doi:10.1038/s41586-026-10410-0. Warmth tuning improved perceived warmth while increasing measured error and sycophancy across the reported evaluations; personality presentation and epistemic performance cannot share one acceptance signal. |
| [ABS] | **Feng et al.**, *Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models.* ACL 2026, arXiv:2604.10733. Across 13 open models, prompted agreeableness correlated with sycophantic validation; transfer to frontier coding agents remains unmeasured. |
| [ABS] | **Mesmer-Magnus & DeChurch**, *Information Sharing and Team Performance: A Meta-Analysis.* Journal of Applied Psychology 94(2), 2009, doi:10.1037/a0013773. 72 independent studies; unique-information sharing was more strongly related to performance than generic openness, and structured discussion strengthened it. Human-team evidence; agent transfer is a hypothesis. |
| [ABS] | **Marlow et al.**, *Does team communication represent a one-size-fits-all approach?* OBHDP 144 (2018), doi:10.1016/j.obhdp.2017.08.001. Meta-analysis reports communication quality as more strongly related to performance than frequency; familiarity and virtuality moderate the relationship. |
| [FULL] | **Bernstein, Shore & Lazer**, *How intermittent breaks in interaction improve collective intelligence.* PNAS 115(35), 2018, doi:10.1073/pnas.1802407115. In the studied human problem-solving task, intermittent interaction improved the average while retaining the best independent solutions; constant interaction reduced the maximum. |
| [ABS] | **de Wit, Greer & Jehn**, *The Paradox of Intragroup Conflict: A Meta-Analysis.* Journal of Applied Psychology 97(2), 2012, doi:10.1037/a0024844. 116 studies and 8,880 groups; relationship and process conflict were stably negative, while task-conflict effects were contingent rather than a general benefit. |
| [ABS] | **Fausett et al.**, *Measurement Matters: A Meta-Analytic Examination of Transactive Memory Systems and Team Outcomes.* Small Group Research (2026), doi:10.1177/10464964261434540. 44 studies/103 effects; TMS had a moderate positive relationship with outcomes, with much larger self-report than observer or embedded effects. |
| [ABS] | **Frazier et al.**, *Psychological Safety: A Meta-Analytic Review and Extension.* Personnel Psychology 70 (2017), doi:10.1111/peps.12183. 136 samples, over 22,000 people and nearly 5,000 groups; supports protected interpersonal risk-taking while leaving agent transfer untested. |
| [FULL] | **W3C**, [PROV-O](https://www.w3.org/TR/prov-o/), Recommendation 30 April 2013. Separates agents bearing responsibility, activities and entities; adopted as the provenance vocabulary prior, not as an agent personality model. |
| [FULL] | **Linux Foundation A2A**, [protocol specification](https://a2a-protocol.org/latest/specification). Agent Cards describe service identity/capabilities/endpoints/security requirements, while credentials are acquired out of band; a card is discovery metadata, not durable organisational identity. |
| [FULL] | **Model Context Protocol**, [authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization). Defines optional transport authorization for HTTP MCP clients acting on behalf of resource owners; it does not define team roles, memory or culture. |
| [FULL] | **SPIFFE**, [identity/SVID](https://github.com/spiffe/spiffe/blob/main/standards/SPIFFE-ID.md) and [Workload API](https://github.com/spiffe/spiffe/blob/main/standards/SPIFFE_Workload_API.md). Supplies verifiable runtime workload identity; useful for authentication, not a substitute for logical agent, role or display-persona identity. |
| [FULL] | **OpenAI Codex**, [app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md). `turn/steer` requires the active `expectedTurnId`; `turn/interrupt` cancels by thread/turn; streamed lifecycle events provide typed acknowledgements. |
| [FULL] | **Anthropic**, [Managed Agents session events](https://platform.claude.com/docs/en/managed-agents/events-and-streaming). Durable event streams accept `user.interrupt` followed by `user.message`; preview deltas are explicitly non-authoritative and buffered events are authoritative. This is an API product, not evidence that Claude Code subscription sessions expose the same control. |
| [FULL] | **OpenCode**, [server reference](https://dev.opencode.ai/docs/server/). Headless HTTP/OpenAPI server exposes session status, async prompts, abort, permission responses and SSE events; the reviewed surface does not document same-turn steering semantics. |
| [FULL] | **Cursor**, [ACP integration reference](https://cursor.com/docs/cli/acp). Documents the `initialize` → `authenticate` → `session/new` → `session/prompt` flow over newline-delimited JSON-RPC/stdio, the returned `stopReason`, permissions and cancellation. The minimal `session/new` example carries `cwd` and `mcpServers`; Consilience has not yet measured Cursor's ACP model-selection method. |
| [FULL] | **Agent Client Protocol**, [v1 protocol and schema](https://agentclientprotocol.com/protocol/prompt-turn#stop-reasons) (Linux Foundation / `agentclientprotocol` canonical repository). `StopReason` distinguishes successful `end_turn` from `max_tokens`, `max_turn_requests`, `refusal` and `cancelled`; a client must not collapse all terminal responses into success. |

## 12. Research-publication and AI-assistance policies (read 20 Aug 2026)

| Status | Source |
|---|---|
| [FULL] | **arXiv**, [content-moderation policy](https://info.arxiv.org/help/moderation/index.html), [submission overview](https://info.arxiv.org/help/submit/index.html) and [third-party submission policy](https://info.arxiv.org/help/third_party_submission.html). Significant text-to-text generative-AI use is reportable; AI tools are not authors; every human author remains responsible for all content. Authors are expected to self-submit. Proxy submission needs a trusted-proxy arrangement, author-validated metadata and prior permission for automated SWORD deposit. Read 2026-08-20. |
| [FULL] | **OpenReview**, [Terms of Use](https://openreview.net/legal/terms). A submitter warrants authorship or authorised proxy status, co-author consent, rights and authority to grant the licence. A user must keep credentials confidential and must not authorise a third party to use the system on the user's behalf; API availability does not remove those account terms. Read 2026-08-20. |
| [FULL] | **NeurIPS 2026**, [Main Track Handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook). Humans remain responsible for all text, figures and references; agents and LLMs cannot be authors. Important, original or non-standard agent/LLM use in the method belongs in the experimental setup; basic editing and code assistance are exempt. Reproducibility information and the paper checklist are required. Read 2026-08-20. |
| [FULL] | **ICLR 2027**, [AI Policy for Authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors). AI use must be disclosed in the paper and submission form, including a mandatory paper section; human authors remain responsible for falsehood, plagiarism and misrepresentation. Read 2026-08-20. |
| [FULL] | **AAAI**, [policy on AI systems in publications](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/). AI systems cannot be authors or citable sources; every AI role in developing the publication must be documented, and human authors remain responsible for the whole paper. Read 2026-08-20. |
| [FULL] | **ACL**, [Policy on Publication Ethics](https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics). Generative systems cannot be authors; content-generating use must be disclosed in Acknowledgements, while proofreading-only use is exempt. The policy's definition of works includes code, datasets, images, appendices and presentations. Read 2026-08-20. |

## 13. Verified sufficiency and “more-by-default” (read 20 Aug 2026)

| Status | Source |
|---|---|
| [FULL] | **Orlanski et al.**, *SlopCodeBench: Benchmarking How Coding Agents Degrade Over Long-Horizon Iterative Tasks* (arXiv:2603.24755v2). Fifteen native coding-agent compositions, 36 problems and 196 checkpoints. Structural erosion rose in 77% of trajectories and redundant-code verbosity in 75.5%; compared with 473 open-source Python repositories, agent code was 2.0× more eroded and 2.3× more verbose. Quality-aware prompts reduced initial degradation but did not stop it, raised mean cost per checkpoint by 12.1% and reduced strict correctness by 2.3 percentage points. Read in full 2026-08-20. |
| [ABS] | **Ebrahimi et al.**, *To Add Is Machine, To Delete Is Human: Measuring and Mitigating Deletion Avoidance in LLM Code Editing* (arXiv:2607.28887). Abstract and full arXiv landing-page result summary read 2026-08-20. Across five leading SWE-bench Verified models, deletion recall was at most 71.7% even on tasks all five solved; 29.0% of passing patches retained the target behind a guard or fallback. Strengthened removal tests reduced four models from 63.2% to 41.9%. Exact-span guidance changed the failure mode but raised GPT-5.6 Sol success only to 80.5%. |
| [FULL] | **Jwalapuram et al.**, *The Illusion of Multi-Agent Advantage: Why Modern Agentic Systems Fail to Leverage Collective Intelligence* (arXiv:2606.13003v1). Read in full 2026-08-20. Six automatic multi-agent frameworks were less efficient than a strong single-agent self-consistency baseline in the authors' comparison and sometimes cost about 10× more; a task-specific expert decomposition improved GPT-5 from 57.0% to 96.5% at comparable cost on their synthetic separable task. The paper distinguishes generic fan-out failure from useful task topology. |
| [FULL] | **Anthropic**, [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), “Overeagerness” and “Subagent orchestration”. Documents extra-file, unnecessary-abstraction and unrequested-flexibility behaviour for Opus 4.5/4.6, and subagent overuse where direct search would suffice for Opus 4.6; it also states that temporary files can improve some coding outcomes. Read 2026-08-20. |
| [FULL] | **OpenAI**, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/). Reports one internal team's earlier practice of spending each Friday, described as 20% of the week, cleaning up “AI slop”, then moving taste and architecture rules into mechanical checks and recurring cleanup. The article explicitly limits generalisation to similarly structured repositories. Read 2026-08-20. |

---

## Citing in public

- **Never cite a [SNIP] or [2ND] entry publicly.** Fetch, read, promote the flag, record the
  date, then cite.
- Prefer arXiv IDs and DOIs over URLs; URLs rot.
- When citing a number, cite the source that *measured* it, never the blog that repeated it.
- Where a source cuts against us — *When to Think Deeply* vs ADR-0009, FrugalGPT vs
  ADR-0003 — cite it in the ADR's **Evidence against** section. An ADR citing only
  supporting work is advocacy.

## Do not redistribute

Papers are copyrighted. Fetch to a gitignored `sources/` directory for local use; the
repository holds citations, not copies.

## Priority reading order

1. ~~Ao, Gao & Simchi-Levi (arXiv:2603.26993)~~ **READ 2026-08-19** — theorem and relay figures confirmed; caveats recorded above
2. ~~Lee et al., Meta-Harness (arXiv:2603.28052)~~ **READ 2026-08-19** — novelty threat resolved; our Terminal-Bench numbers were wrong and are corrected
3. ~~Meng et al. harness survey~~ **READ 2026-08-19** — compositional-verification claim was miscast; METR 24.2 pp gap is the real support
4. ~~Dekoninck et al. (arXiv:2410.10347)~~ **READ 2026-08-19** — novelty claim narrowed and restated
5. ~~Amin (arXiv:2601.01522)~~ **READ 2026-08-19** — prior art for aggregation, not for β
6. Ren et al. survey (arXiv:2607.13104) — self-improvement entry point
7. EvoTrainer (arXiv:2606.03108) and *Adapting the Interface, Not the Model* (arXiv:2605.22166) — surfaced during the Meta-Harness verification as unchecked adjacent work; check before the novelty claim is considered fully established
