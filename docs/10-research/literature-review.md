# Literature review

Compiled 19 Aug 2026 from web research (DAIR.AI weekly papers, arXiv, lab blogs).
All entries `[cited]`. **Not all sources were read in full** — several are from search
snippets. Verify before relying on any specific number.

---

## 1. Harness engineering is now a named discipline — and crowded

- **OpenAI**, *Harness engineering: leveraging Codex in an agent-first world* (Feb 2026).
- **Anthropic**, *Effective Harnesses for Long-Running Agents*.
- **Li et al. 2026**, *Agent harness engineering: a survey*.
- **RUCAIBox/awesome-agent-harness** — companion to *Agent Systems with Harness Engineering*.
- **Ao et al. 2026**, *Building Effective AI Coding Agents for the Terminal* — introduces the
  scaffolding (pre-run assembly) vs harness (runtime orchestration) split.
- Practitioner claim in circulation: ~65% of enterprise agent failures trace to harness
  defects (context drift, schema misalignment, state degradation) rather than model
  reasoning. **Unverified — chase the primary source before quoting.**

**Implication:** "harness engineering matters" is not a differentiator in Aug 2026. It is
the consensus. Differentiation has to be sharper than that.

## 2. THE NOVELTY THREAT — Meta-Harness

**Lee, Nair, Zhang, Lee, Khattab & Finn (Stanford / KRAFTON / MIT), *Meta-Harness:
End-to-End Optimization of Model Harnesses*, arXiv:2603.28052, COLM 2026.**
Code: `github.com/stanford-iris-lab/meta-harness`. ~94 citations by Aug 2026.

An outer loop that searches over *harness code*. An agentic proposer (Claude Code) gets
unrestricted filesystem access to the source, scores and execution traces of every prior
candidate — up to 10M tokens per step, orders of magnitude beyond OPRO / TextGrad /
AlphaEvolve, all of which compress feedback aggressively. Results (verified against the
paper, 2026-08-19): +7.7 pts over ACE on online text classification at 4× fewer context
tokens; +4.7 pts on 200 IMO-level problems across five held-out models; on the full 89-task
TerminalBench-2 it reaches **76.4% vs Terminus-KIRA's 74.7%** with Opus 4.6 (ranked #2
behind ForgeCode at 81.8%), and **37.6% vs Goose's 35.5%** with Haiku 4.5 — #1 among
Haiku 4.5 agents. Framing claim: changing the harness around a fixed LLM can produce a
**6× performance gap** on the same benchmark — **a claim the paper cites ([47]), not one it
measures.**

> **Correction (2026-08-19).** This entry previously reported "on a hard 19-task
> Terminal-Bench subset it took Terminus-KIRA from 28.5% to 46.5% in seven iterations".
> **No such experiment exists in the paper.** There is no 19-task subset; "28.5" matches
> MCE's context-token count (28.5K) from the text-classification table; "46.5" appears in
> the paper only inside SVG path coordinates. The figure was a fabricated or garbled
> conflation produced in the original research session and sat here flagged `[ABS]` as if
> checked. Left visible rather than silently fixed: it is direct evidence for Q19 and for
> this repo's own thesis about unverified acceptance signals.

**This must be confronted directly in the brainstorm.** It is adjacent to, and in some
readings supersedes, parts of the position in `20-design/`. Note what it does *not* do:
it optimises a harness against a benchmark; it does not measure the trustworthiness of a
repository's own verification layer. That gap is where the β thesis would have to live —
but establish that honestly rather than assuming it.

Related and also in the space:
- *Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent
  Harnesses* (arXiv:2604.25850)
- *Self-Harness: Harnesses That Improve Themselves* (Aug 2026)
- *HarnessX: A Composable, Adaptive, and Evolvable Agent Harness Foundry* (Jul 2026)
- *VeRO: An Evaluation Harness for Agents to Optimize Agents* (ICML 2026)
- **Huang et al. 2026**, *Affordance agent harness: verification-gated skill orchestration*
  (arXiv:2605.00663) — **the name alone overlaps our core idea; read this first.**
- Natural-language agent harnesses (arXiv:2603.25723)

## 3. THE THEOREM — multi-agent has a hard ceiling

**Ao, Gao & Simchi-Levi (MIT / City University of Hong Kong), *On the Reliability Limits of
LLM-Based Multi-Agent Planning*, arXiv:2603.26993 (27 Mar 2026). Unrefereed technical
note; read in full 2026-08-19.**

Models an agent system as a finite acyclic delegated decision network. Result: **without
new exogenous signals, any delegated network is decision-theoretically dominated by a
centralised Bayes decision maker observing the same information.** In the common-evidence
regime, optimising a multi-agent DAG under a finite communication budget reduces to
choosing a budget-constrained stochastic experiment on the shared signal. Under proper
scoring rules the centralised-vs-communicated gap is an expected posterior divergence —
conditional mutual information under log loss, expected squared posterior error under Brier.

Reported empirics on a controlled four-way task (verified at source, 2026-08-19): 200
MMLU questions, 30 runs each — gpt-4.1-mini went 90.7% (one stage) → 41.2% (two) → 43.5%
(three) → 22.5% (five), i.e. *below* the 25% chance baseline; o4-mini fell 89.9% → 37.0%
at two stages. Interface form mattered — but note this is a *separate, smaller* experiment
(50 questions, three stages fixed): posterior-vector relay 75.2% vs prose relay 58.1%,
i.e. ~2.8 vs ~8.5 pts lost per stage. Two caveats from the full read: the dominance result
is **weak** (the network can match the centre, never beat it), and the paper never shows a
real LLM can implement its centralised Bayes decision-maker — the case for "one big-context
agent" over a committee rests on Tran & Kiela's context-degradation result, not on this
theorem.

**Design consequence, and it is a hard rule:** every multi-agent structure in this project
must name the *exogenous* signal it introduces. A "meeting" that only reprocesses shared
context is provably a lossy compression of information you already had. A critic that runs
tests, or an agent working an independent repo, adds exogenous signal. Debate does not.

## 4. Supporting empirical evidence against naive multi-agent

- **Tran & Kiela (Stanford), arXiv:2604.02460** — single agents match or beat multi-agent
  on multi-hop reasoning at matched thinking-token budgets; information-theoretic argument
  from the Data Processing Inequality. Predicts MAS becomes competitive precisely when
  single-agent context utilisation degrades. *That prediction is our justification for
  parallel work across independent repos, and against debate.*
- **Kim et al., Nature Machine Intelligence (2026)** — 260 configurations, six benchmarks,
  five architectures, three model families, compute matched. Single-agent baseline
  performance is the most robust predictor of whether coordination helps; identifies a
  capability-saturation threshold; predicts the sign of the multi-agent effect on
  SWE-bench Verified and Terminal-Bench in 94% of validation configs. MAS overheads
  1.6–6.2× tokens at matched performance.
- ***The Illusion of Multi-Agent Advantage*** (arXiv:2606.13003) — audit of six automatic
  MAS-design frameworks; architectural bloat and functional collapse back to one agent.
- **Cemri et al. 2025**, *Why Do Multi-Agent LLM Systems Fail?* — MAST taxonomy,
  14 failure modes over 1,600+ annotated traces; conclusion that many failures are
  structural, not prompt-fixable.

## 5. Routing and cascades — mostly solved, EXCEPT the signal

The cascade design is well-trodden. Do not reinvent:

- **FrugalGPT** (Chen et al., TMLR 2024) — matches best single model at up to 98% cost
  reduction via learned confidence thresholds.
- **Hybrid LLM** (Ding et al., ICLR 2024) — quality-aware small/large router.
- **RouteLLM** (Ong et al., ICLR 2025) — routers from preference data.
- **AutoMix** (Aggarwal et al. 2024) — self-verification + POMDP routing.
- **Dekoninck, Baader & Vechev (ICML 2025)** — unified theory; optimal serving lies on a
  continuum between pure routing and pure cascading.
- **UniRoute** (Jitkrittum et al., ICLR 2026) — routing when unseen models appear at test time.
- Surveys: RouterBench, RouterArena, LLMRouterBench, *Dynamic Model Routing and Cascading*
  (arXiv:2603.04445).

**The unsolved part, repeatedly named across this literature, is the deferral signal.**
LLM self-reported confidence is badly calibrated; naive cascades escalate easy queries the
cheap model got right while keeping confidently-wrong answers. Mitigations in the
literature: GATEKEEPER (fine-tuned confidence), UCCI (token-margin + isotonic regression,
ECE 0.03), conformal risk control (RouteNLP), semantic agreement for open-ended settings
(Soiffer/Kolawole), hidden-state probes.

> **Explicitly noted in this literature:** cascades are well-established where outputs are
> *objectively assessable* and remain fundamentally harder in open-ended settings.
> Coding has an oracle. That is the opening — if it is still open after checking §2.

Also relevant: **Act or Escalate?** (arXiv:2604.08588) — escalation behaviour is a
*model-specific property* that must be characterised before deployment; miscalibration
direction varies by model and domain; SFT on chain-of-thought targets produces near-optimal
escalation that generalises to held-out domains.

## 6. Context engineering (the memory/skills layer)

- **ACE — Agentic Context Engineering** (Zhang et al., ICLR 2026, arXiv:2510.04618).
  Generator / Reflector / Curator loop; context as an evolving playbook, not a static
  prompt. +10.6% agent tasks, +8.6% finance, **no gradient updates**. This is what `/learn`
  should look like.
- *A Survey of Context Engineering for LLMs* (arXiv:2507.13334).
- *Context Engineering for AI Agents in Open-Source Software* (arXiv:2510.21413, MSR 2026).
- Manus, *Context Engineering for AI Agents: Lessons from Building Manus*.
- DAIR.AI flagged a study with 288 gold-test-evaluated runs across Claude Code and Codex,
  17 tasks, 3 repos, with context-injection strategy as the only variable — **directly
  relevant to how this project should structure AGENTS.md; track it down.**

## 7. Adjacent systems worth reading before designing anything

- **SemaClaw** (Midea AIRC, arXiv:2604.11548) — DAG-based two-phase hybrid agent-team
  orchestration, PermissionBridge behavioural safety, three-tier context management,
  agentic-wiki skill. Open source. Closest thing to a complete comparable.
- **DeepSeek Harness** (13 Aug 2026, MIT) — everything-is-a-plugin on the Cordis kernel;
  append-only session log with a runtime invariant that everything reaching a model request
  is rebuildable from the log; imports Claude Code sessions. The trajectory substrate,
  given away.
- **Omnigent** (Databricks, Apache 2.0, Jun 2026) and **Vercel AI SDK v7 HarnessAgent API** —
  the meta-harness category, unclaimed.
- **Token Budgets** (arXiv:2606.04056) — catalogue of **63 confirmed production
  budget-overrun incidents** across 21 orchestration frameworks, 2023–2026. Budget
  primitives are not a v2 feature.

---

## Honest assessment of what is left

| Component | Prior art status |
|---|---|
| Cascade + verifier routing | **Solved.** Adopt, don't invent. |
| Learned router | Solved *and* our simulation says not worth it. |
| Harness auto-optimisation | **Solved by Meta-Harness.** Do not compete. |
| Multi-agent orchestration theory | **Settled, and it constrains us.** Obey the theorem. |
| Context/skill evolution | Solved by ACE. Adopt the Generator/Reflector/Curator shape. |
| Trajectory logging substrate | Given away by DeepSeek Harness. |
| Budget primitives | Documented need; implementations exist. |
| **Measuring β per repository, and deriving routing depth + parallelism ceiling from it** | **No prior art found.** ← the only candidate novelty |
| **The identity β ≡ 1 − critic recall as a single control parameter** | **No prior art found.** ← ditto |

Two candidate contributions, both unverified. The first job of the brainstorm is to try
hard to kill them — starting with `Affordance agent harness: verification-gated skill
orchestration` (arXiv:2605.00663), which is the nearest-named threat and was not read.
