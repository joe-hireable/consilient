# The reasoning layer — detection first, scaffolding last

Status: **v1+ design documentation. Not v0** (ADR-0015 Stage 2). Sources verified at
origin 19 Aug 2026; every effect size below carries its vintage, because most of this
literature predates reasoning-trained models and does not transfer.

## The core problem is detection and non-duplication, not scaffolding

The requirement is a three-way dispatch, per model per task class:

| Native reasoning | Action | Evidence |
|---|---|---|
| Present and good | **Apply nothing.** Constrain if anything: cap thinking budget | R1's own authors: "Few-shot prompting consistently degrades its performance" (arXiv:2501.12948, Conclusion). OpenAI reasoning guidance: "Avoid chain-of-thought prompts". Anthropic: high-level "think deeply" beats prescriptive step-by-step. Overthinking is a measured cost: lowest-overthinking candidate selection improved SWE-bench agents ~30% while cutting compute 43% (arXiv:2502.08235). `[cited]` |
| Absent | Scaffolding *may* pay — see the survey, and note how little of it has small-model evidence | below |
| Present but weak (hybrid) | **The genuinely unclear case.** Best current evidence: control the *native* mode (thinking budget/toggle), do not prompt-scaffold — the one measured hybrid harmed by prompted CoT lost −3.3% average and −13.1% on answer consistency (Gemini Flash 2.5, Wharton Prompting Science Report 2, arXiv:2506.07142). OptimalThinkingBench (arXiv:2508.13141): no intervention yet balances over- and under-thinking. **Q25.** `[cited]` |

**Double-application is the named failure mode**, and the check for it ships with the
feature (I1): the dispatcher must consult a reasoning-capability field and refuse to
stack scaffolds on a model whose native mode is on.

### The registry exists — three times over. Do not build one. `[measured]`

Verified live 19 Aug 2026:

- **OpenRouter `/api/v1/models`** — the richest signal and exactly the needed tri-state:
  `reasoning: null` (non-reasoner) / `{mandatory: false}` (hybrid) / `{mandatory: true}`
  (always-on), plus default/supported efforts. 414 models: 129 null, 285 with the object
  (31 mandatory). Proprietary ToS data; consume live, don't redistribute.
- **models.dev** (SST, MIT, `github.com/sst/models.dev`) — open and redistributable:
  6,834 entries, `reasoning` bool + `reasoning_options` distinguishing toggle vs effort
  models. The right base for a shipped registry.
- **LiteLLM capability map** (MIT, updated daily) — `supports_reasoning` + effort flags.

Semantics trap all three share: the flag means *supports/accepts reasoning*, not
*reasoning-trained*; only OpenRouter's `mandatory` field or models.dev's
`reasoning_options` recover the tri-state. Hugging Face has no standard field (negative
result).

## Technique survey — with the vintage audit attached

| Technique | Headline result | Vintage / transfer to 2026 small models | Tokens |
|---|---|---|---|
| Few-shot CoT (Wei et al., NeurIPS 2022) | GSM8K ~18%→57% on PaLM-540B | **The famous small-model result cuts against us**: CoT was emergent at ~100B; sub-10B models scored at/below standard prompting with fluent-but-illogical rationales. But that is about 2022 base models; 2026 4B–14B instruct models are CoT-saturated in training, so the prompt adds little either way | ~2–5× out |
| Zero-shot CoT (Kojima et al. 2022) | MultiArith 17.7→78.7 (text-davinci-002) | Largely redundant on modern instruct models; interferes with trained thinking formats | ~2–5× |
| Task-scope meta-analysis (Sprague et al., ICLR 2025, arXiv:2409.12183) | CoT helps mainly **math/symbolic**; ~0 or negative elsewhere | Post-reasoning-era; replicated; safe to build on | — |
| Self-consistency (Wang et al., ICLR 2023) | +17.9pp GSM8K over CoT; helps down to 20B (variance reduction, not elicitation) | Mechanism is model-agnostic and current. Two harness problems: needs a *votable* answer (code artifacts have none), and see the β interaction below | k× (paper used k=40) |
| Tree-of-Thoughts (Yao et al. 2023) | Game of 24: 4%→74% on GPT-4 | Benchmark built to need search; and arXiv:2410.17820 shows small models fail at the *discrimination* step ToT depends on — cost multiplies, capability doesn't | ~100×+ |
| ReAct (Yao et al. 2022) | Mixed — beats CoT on grounded tasks, **loses** on HotpotQA | Format brittleness dominates for 7–13B open models (AgentBench) | per-loop |
| Reflexion (Shinn et al. 2023) / Self-Refine | HumanEval 80.1→91.0 (GPT-4) — **because the feedback was external (tests)** | Small models write weaker tests: feedback and fix degrade together. This is a β statement | 2–4×/retry |
| **Intrinsic self-correction** (Huang et al., ICLR 2024, arXiv:2310.01798) | **Negative result: degrades even GPT-4** — models talk themselves out of correct answers; prior positives used an oracle stop signal | Replicated; presume worse at 7B. **Do not ship self-critique without external feedback, at any tier** | 2×+ for harm |
| Budget forcing / s1 (Muennighoff et al. 2025) | AIME24 50→57 beyond natural stopping | **Requires a reasoning-fine-tuned model** — appending "Wait" to a stock instruct model is not this technique | dialled |
| Test-time scaling laws (Snell et al. 2024) | Small model + optimal test-time compute matches 14× larger — **gains vanish on the hardest bins** | Needs trained verifiers/PRMs; difficulty binning was oracle-ish | task-dependent |
| **Best-of-N + external verifier** (Cobbe et al. 2021; Lightman et al. 2023) | 6B generator + 6B verifier over 100 samples beats fine-tuned 175B — the strongest small-model result in the survey | **Best transfer to coding**: the external verifier we get free is the test suite. Its failure mode *is* β — see below | N× |
| **Distilled reasoning at 4–14B** (R1-Distill, Qwen3 hybrids, 2025) | R1-Distill-Qwen-7B: 55.5% AIME24; 14B: 69.7% — crushing any prompt scaffold on the non-reasoning base | **The 2025–26 answer.** Training-time reasoning beat inference-time scaffolding at this scale; overthinking-on-easy-inputs is the residual cost (5–20× tokens) | 5–20× |

**Design position the survey forces:** for the local cheap tier, the reasoning layer is
primarily a *model-selection* decision (registry says non-reasoner → prefer a distilled
reasoner of the same size) and only secondarily a scaffolding decision. Where scaffolding
is applied at all, only verifier-coupled forms (best-of-N against tests,
Reflexion-with-tests) have small-model evidence — and those are exactly the forms that
interact with β. `[cited]` throughout; nothing here is measured by us yet.

## The Δ question — answered, and the frame did not fully survive

Asked directly (prompt 5, Task 3) whether "narrows Δ, loosens β*" is one mechanism or a
frame being overextended. Full derivations:
`../10-research/experiments/capability_context_beta_star.py`; ADR-0002 § Δ discipline.
Verdict, stated plainly:

- **Three different mechanisms were being forced into one frame.** Tools change the
  *feasible set* (structural zeros — not Δ; different formula, derived). Context
  discipline changes competence on the same task (the one genuine Δ claim — survives,
  directionally). Reasoning scaffolds change the *shape* of the competence curve, not
  its position: majority-of-5 steepens the logistic slope ×1.875 at the midpoint, which
  is the exact unequal-slopes case that destroys β*'s distribution-freeness. Computed
  consequence: β* under a scaffolded cheap tier ranges **0.024–0.233 across difficulty
  distributions** (flat 0.112 unscaffolded), and aggregate success can go *down*
  (0.439→0.429 on Beta(2,2)) at 5× cost. The same intervention loosens or tightens the
  threshold depending on task mix. `[algebra]` The survey independently corroborates the
  shape claim: test-time compute gains concentrate at mid difficulty and vanish at the
  hard end (Snell et al.) — a slope change, not a shift. `[cited]`
- **Verifier-shopping.** Any scaffold that resamples until checks pass exposes the
  verifier n times: P(bad ships | task beyond the model) = 1−(1−β)ⁿ — 41% at β=0.10,
  n=5. Best-of-N "plus tests" is not free safety; it is a β multiplier. `[algebra]`
- **β\* was drifting from prediction to explanation.** The discipline adopted in
  ADR-0002: "narrows Δ" may only be claimed for an intervention shown to produce a
  *uniform log-odds shift*; anything else must be named as what it is (feasibility mass,
  slope change, floor change), each with different — already computed — β* behaviour.
  Predictive restatements exist for context discipline (EXP-18) and scaffolding
  (EXP-07 extension); the tool claim needed a different formula, not a Δ.

## Boundary: reasoning layer ≠ Inquiry tier

| | Reasoning layer | Inquiry tier (`inquiry-tier.md`) |
|---|---|---|
| Level | **Task** — help a weak model produce a better artifact | **Decision** — escalate an architectural choice to modelling/measurement |
| Trigger | Model registry (tri-state) × task class | Four gates: reversibility, blast radius, prior dispersion, formalizability |
| Output | The artifact itself | An executable model committed beside the ADR |
| Cost unit | Tokens per task (k× multipliers above) | An inquiry budget per decision |
| Failure mode | Wasted tokens; degraded output on native reasoners; verifier-shopping | Simulating the unsimulable; ceremony (Q13) |

They share one shape (escalating compute when cheap answers are inadequate) and nothing
else; conflating them would put four-gate triggers on every task or CoT prompts on every
ADR, both absurd.

## Cost: folded into EXP-07, and it can reopen ADR-0003 by itself

Self-consistency at n=5 is 5× tokens — and on a single serialising local GPU, ≈5×
**wall-clock**. ADR-0003's overturn condition is a wasted-work multiplier ≥2×. A
reasoning layer on the local cheap tier can cross that line alone. EXP-07 is amended
(experiment register) to measure the failed-cheap-attempt multiplier **with and without
the reasoning layer**; crossing 2× reopens ADR-0003. No new experiment — same
instrument, one more condition.
