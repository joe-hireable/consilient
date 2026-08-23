# Open weights: what they actually buy, 23 August 2026

Twelve agents on activation steering, model merging, adapter composition, weight editing,
constrained decoding, test-time adaptation and serving -- with the autonomy requirement binding:
a technique earns its place only if the system can decide WHEN to apply it without a human.

**Two corrections carried from the research, both load-bearing.** The RTX 5090 has **32 GB**, not
64. And the measured composite verifier false-accept rate is **0.3132 [0.2926, 0.3346]** against a
required 3.3% at a 0.42 capability gap.

**The answer to the question asked: custody of a fixed instrument.** Everything else is a
technique; this is the precondition for any technique having a stable meaning. Hosted snapshots
have a median measured lifetime of 14.5 months, and one model's classification accuracy moved 84%
to 51% in three months under an unchanged name. An instrument swapped every fourteen months does
not produce a measurement series -- it produces anecdotes with decimal points.

Grammar-constrained decoding is the one item that is faster AND better AND fully autonomous.
Direct weight editing is not ready and the evidence against it comes from the papers arguing for
it.

---

# Capability Map: Open Weights in Consilient

**Scope.** Ten research angles, one hardware budget, one verifier. This map keeps what survives all three.

**Two corrections carried from the research, both load-bearing.** The RTX 5090 has **32 GB** of VRAM, not 64 [cited, six angles independently]. And measured composite verifier false-accept rate is **β = 0.3132 [0.2926, 0.3346]** (EXP-47, ADR 0018) against a required **β\* = 3.3%** at a 0.42 capability gap [measured, `src/consilient/routing.py` and `docs/10-research/local-experimentation.md`]. The second number decides more of this document than any paper cited in it.

---

## What open weights actually buy

**One answer: custody of a fixed instrument.** Everything else on the impossible list is a technique; this is the precondition for any technique having a stable meaning.

Consilient's deliverable is an error rate. Hosted snapshots have a median measured lifetime of **14.5 months** (range 12.0–25.5, n=10 Anthropic snapshots) with 60–62 days' notice on the last four retirements [cited, arithmetic mine]. `gpt-5-2025-08-07` was announced for shutdown six months out [cited]. Anthropic names the harm itself: "Researchers lose access to models for ongoing and comparative studies" [cited]. Retirement is the loud failure. The quiet one: GPT-4 prime classification measured at 84% then 51% three months later under an unchanged name [cited, arXiv:2307.09009]. The quietest: `temperature`, `top_p` and `top_k` now return HTTP 400 on Claude Opus 4.7 and later [cited] — greedy decoding, the cheapest variance reduction in any harness, is no longer available to hosted callers at all.

An instrument swapped every fourteen months does not produce a measurement series. It produces anecdotes with decimal points.

Ranked below custody, genuinely API-impossible and permanently so — merely the *output* logit layer leaks enough to reconstruct a production model's embedding projection for ~$20 [cited, arXiv:2403.06634], so no provider will ever expose the residual stream:

| Rank | Capability | Why it matters here |
|---|---|---|
| 1 | Indefinite checkpoint custody | No forced discontinuity in the error series |
| 2 | Hidden-state reads (SEPs) | Per-answer error at ~1× cost vs 5–10× sampling [cited, arXiv:2406.15927] |
| 3 | Arbitrary per-token logit masks | Parse failure becomes structurally impossible |
| 4 | Full logit vector | OpenAI caps `top_logprobs` at 20 of ~200k; Anthropic exposes none [cited] |
| 5 | Activation/weight intervention | Real, but fails autonomy — see below |

Determinism is **not** on this list as a free property. Stock vLLM at temperature 0 produced 80 distinct completions from 1000 samples, first divergence at token 103, weights already frozen [cited, Thinking Machines]. Determinism is a kernel property, bought with batch-invariant ops at ~1.6× wall-clock (26 s → 42 s measured on their hardware) [cited, MIT licence].

---

## Ready now

Four items. All autonomous, all gated by something that **executes** rather than something that opines.

**1. Grammar-constrained decoding.** Grammar derived mechanically from the schema the caller already holds — there is no selection step for a human to occupy. JSONSchemaBench: 100% validity by construction, **6.37 ms TPOT (Guidance) vs 15.40 ms unconstrained**, GSM8K **83.8% vs 80.1%** [cited, arXiv:2501.10868]. Faster, because deterministic structural tokens skip the forward pass. VRAM: **zero** — host-side. Licences: llama.cpp MIT, XGrammar Apache-2.0, llguidance MIT [measured].
*Enforcement rule:* every schema places an unconstrained reasoning field **before** any constrained answer field, or the constraint is scoped via `structural_tag`. This is the variable that flipped arXiv:2408.02442's degradation result [cited]. Assert it at schema-registration time, not by convention.
*Coverage caveat:* on GitHub-Hard schemas, engine coverage is 41%/39%/28%/3% [cited]. The retry fallback is load-bearing, not ceremonial.

**2. Speculative decoding.** Verified speculation is output-distribution-preserving, so there is no quality decision to make. ~2× latency, zero risk. llama.cpp `--spec-draft-*`, MIT. Draft model 0.5–0.6B at Q8 ≈ 0.7 GB [simulated].
*Enforcement rule:* measure draft acceptance online; disable below the break-even threshold. Self-governing.

**3. Prefix/KV cache reuse.** On by default, no policy to set. RadixAttention reports up to **6.4× throughput** on agent-control and structured-output workloads — exactly Consilient's shape [cited, arXiv:2312.07104]. Apache-2.0.

**4. Surprisal-guided selection.** Among candidates the **test suite has already marked passing**, take the highest-surprisal one, not the most confident. Measured 80% vs 50%; top-3 recovers 100% oracle at zero cost [cited, arXiv:2602.07670]. Ground truth does the filtering; surprisal only orders the survivors — so its gate executes.
*Cost:* one scalar per candidate, already returned by every local backend. Stdlib-only, fits the product core (ADR 0031). A few lines of diff against a 30-point effect.
*Honest weight:* single author, no venue, n=20, on a 120B model that does not fit this card. Validate on Consilient's own repo-history evaluation before it becomes default. Cheap, because it reuses candidates already generated.

---

## Ready but needs a human to choose

**Steering vectors.** Derivation is automatable (mean-difference over contrastive pairs, ~700 pairs, under 60 s [cited]). Cost is negligible: 0.64 MB, 5×10⁻⁶ of the forward pass [simulated]. Stacking evidence is real: hallucination-avoidance 0.52 prompt-only → 0.87 prompt+vector [cited, arXiv:2312.06681].

What is **not** automatable is strength and target. CAST is offered as the answer, and it is one paper, one lab, one number (83.3%/2.4%), never replicated, never deployed — and the same angle cites Tan et al. finding steerability "highly variable across different inputs" and "brittle to reasonable changes in the prompt" [cited, arXiv:2407.12404], which is a direct refutation of a cosine-threshold gate over prompt activations. Both quoted; neither reconciled.
*What would make it autonomous:* an external verifier supplying bandit reward on a steered-vs-null A/B, plus an off-target panel. Anthropic measured a pro-life feature moving anti-immigration responses **21.6%** where the immigration feature itself moved them 3.9% [cited] — a panel is mitigation, not detection.

**Model merging.** Selection is claimed solved; it is not. mergekit-evolve turns the crank, but a human authors the search set, the *disjoint* accept set, the safety canaries, the promotion threshold, and the entropy alarm level that the angle admits "is not established in any paper I verified" [asserted, that angle's own tag]. That is the decision.
*The one merge worth building:* **task-vector negation** — a single subtraction with a mechanical λ rule (largest λ retaining ≥95% control accuracy), no search loop. Toxic generations 4.8% → 0.8%, WikiText perplexity 16.4 → 16.9 [cited, arXiv:2212.04089]. mergekit is **LGPL-3.0** [measured, LICENSE read] — CLI subprocess only, never an import.

**Adapter minting.** The angle states plainly: "NO published system does this end-to-end… calling it validated would be dishonest" — then ships it as step 4. Trigger is computable; the decision is not.

---

## Not ready, and why

| Technique | Giveaway |
|---|---|
| **Direct weight editing** | In-context editing scores **82.5%** on RippleEdits; ROME scores **48.7%** on the same model [cited]. The free, reversible method wins by 33.8 points. Editing accuracy 96.8% → **38.5%** once teacher forcing is removed [cited, arXiv:2502.11177]. Best-in-field AlphaEdit reports specificity **67.88** — a third of neighbouring facts corrupted, in the paper arguing for it [cited]. |
| **SAE feature steering** | AxBench: prompt 0.894, DiffMean 0.239, SAE **0.165** [cited]. Anthropic's own verdict: "not yet ready" [cited]. Width-1M SAE ≈ 9.7 GB fp16 [simulated] and Gemma terms are not OSI-approved. Dead twice over. |
| **Test-time training** | Best-of-N with test selection: **90%**. TTT: **30.6%**; "equivalent K" below 1 [cited]. Same verifier, same compute. |
| **Architecture surgery** | No quadrant wins. What beats a downloaded checkpoint needs 8×A100 [cited]; what runs on a 5090 merely ties one you could download. |
| **Merging as multitask compression** | Eight task vectors retain **91.2%** normalised accuracy [cited]. LoRA hot-swap retains 100% at ~3.4 ms [simulated]. |

**The literature-eats-itself pattern, stated once.** Sakana's EvoLLM-JP (MGSM-JA 52.0 vs best-parent 30.0) is quoted four times across the research as proof merging creates capability. It is the output of **1000 CMA-ES trials whose fitness function was MGSM** [cited]. The merging angle notices this and keeps the number as headline evidence anyway. Same failure: AlphaEdit's 98.90 (teacher-forced), SEAL's ARC 72.5% (RL'd against ARC), TTRL's +211% (majority-vote reward, i.e. intrinsic, i.e. the case predicted to rise then fall [cited, arXiv:2603.08660]). And the calibrating number: GRPO with **random** rewards moved MATH-500 by **21.4 points** [cited, arXiv:2506.10947]. A gate a random signal can move by 21 points is not a gate.

---

## The memory arithmetic

The union of the research's six adopt-recommendations, costed together for the first time [simulated, arithmetic]:

| Item | GB |
|---|---|
| 8B base FP8 (serving) | 8.0 |
| 64 × rank-16 adapters | 5.4 |
| Draft model | 0.7 |
| 14B Q8 second tier | 14.0 |
| Frozen 32B Q4 reference | 19.0 |
| Independent-family judge, 8B 4-bit | 5.0 |
| KV, 32 × 4k, FP8 | 8.6 |
| **Total** | **60.7** |

**1.9× over 32 GB. 2.5× over 24 GB.** Add a QLoRA run (12–18 GB peak) and it is 3×.

**Resolution: only serving is resident. Everything else is scheduled and serial.** The reference instrument runs on a fixed probe set, not concurrently. Training runs when serving is stopped. That was never stated because every angle costed itself alone.

| Card | Resident set | GB | What you lose |
|---|---|---|---|
| **24 GB** | 8B FP8 + 16 adapters + KV 16×4k | 13.6 | The judge. Kills the only independent evaluator. |
| **32 GB** | 8B FP8 + 16 adapters + judge + KV 32×4k | 22.9 | Nothing critical; 9 GB headroom |
| **64 GB** | Not available on one card | — | Second card, pro card, or host RAM at a ~28× bandwidth cliff |

*Working, 32 GB row:* 8.0 + (16 × 0.084) + 5.0 + 8.6 = 22.9 GB [simulated]. Adapters are rank-16 all-linear on an 8B: 41.94 M params, 84 MB bf16.

**Plainly: local open weights are a genuine differentiator for a narrow band, and not a frontier substitute.** 32 GB holds a 32B dense at Q4 (~19 GB) or a 30B MoE. A 70B at Q4 is ~40 GB and does not fit; offloading costs ~28× bandwidth and yields single-digit tokens/second [simulated]. The band that is genuinely differentiated: classification, extraction, routing, structured transformation, drafting, self-consistency fan-out at ~£0.05/M output tokens all-in [simulated]. That is most of the *call volume* and little of the *hard reasoning*. Anyone claiming local replaces the API is wrong on arithmetic.

---

## Evaluating a self-modification

**Nothing makes it worth anything unless the gate executes.** This is not caution; it is the measured position.

β = 0.3132 [measured]. A gate wrong 31% of the time cannot certify a weight change. Worse, self-preference rises **linearly** with self-recognition ability, established causally by fine-tuning to move self-recognition and watching self-preference follow [cited, arXiv:2404.13076] — so the bias grows exactly as the system improves. Averaging does not help; the error is systematic and correlated with the optimisation target.

Two escapes, and only two:

1. **Executable ground truth.** Tests, compilers, schema validators, checkable answers. Not subject to Gao's overoptimisation law, because they are not learned proxies [cited, arXiv:2210.10760].
2. **A different-family frozen judge.** Affordable — GPT-4o successfully monitored o3-mini, so the gate may be weaker than what it gates [cited, arXiv:2503.11926]. 5 GB at 8B 4-bit. Fits at 32 GB; does **not** fit at 24 GB alongside serving.

**Consequence, stated because it is the whole finding:** every recommendation whose gate is model judgement collapses. Steering strength, merge promotion, adapter A/B on "diff-accepted", knowledge-edit targeting — four of the research's six adopt-recommendations. What survives is precisely the list in *Ready now*, because each of those is gated by execution or needs no gate at all.

---

## The safety architecture

Each rule states its enforcement mechanism. A chokepoint without one is decoration.

| Must | Enforced by |
|---|---|
| Base weights immutable | Filesystem read-only; SHA-256 in every measurement record |
| All modification is a named adapter delta | CI assertion: no write to base path outside the pinned-download script |
| Corpus append-only, provenance-tagged | Dataset-build assertion on synthetic ratio; 1% is not a safe floor [cited, arXiv:2410.04840] |
| Real-data anchor never dropped | Accumulate-not-replace gives error "bounded independent of iterations" [cited, arXiv:2404.01413] |
| Six things versioned: base hash, adapter hash + parent, corpus manifest, LR schedule, evaluator identity, held-out consumption | Manifest checksum verified before every gate run |
| Gate never feeds training | Monitor-in-objective produces obfuscated hacking with a clean-looking signal [cited, arXiv:2503.11926]. No best-of-N against your own gate. |
| Search set disjoint from accept set | Separate files, separate hashes, assertion on intersection |
| Never automated: evaluator, held-out sets, thresholds, promotion script | Separate user account, no write permission. Retraining does **not** remove reward-tampering once it generalises [cited, arXiv:2406.10162] — this is permissions, not disposition. |
| Never automated: adapter merge-down, checkpoint deletion, anything safety-relevant | Ten adversarial examples and under $0.20 stripped GPT-3.5's guardrails; benign fine-tuning degraded alignment unintentionally [cited, arXiv:2310.03693]. Safety eval gates **every** adapter. |

**Two contradictions in the research, resolved here.** Decoding says delete the retry loop; self-improvement says loud failure is your only detector. Resolution: delete the loop, keep the signal — log the probability mass the grammar mask discards per step. Free, sharper than "the JSON did not parse", API-impossible [asserted, mechanism from arXiv:2405.21047]. Second: test-time says pick the lowest-confidence passing sample; decoding constrains the tail. Resolution: they operate on different objects — the grammar constrains *form*, surprisal ranks *content* among form-valid, test-passing candidates. No conflict once the reasoning field is unconstrained.

---

## Build units

| # | Deliverable | Done when | Depends on | Principal? |
|---|---|---|---|---|
| **0** | Settle whether β and β\* are the same quantity | One-paragraph note in ADR form, cited to both source documents | — | **Yes** — twenty minutes, gates units 3–6 |
| **1** | Surprisal ordering over test-passing candidates | Replayed on repo-history eval; measured delta with paired CI | — | No |
| **2** | Grammar-constrained decoding on schema-bearing call sites, retry fallback retained, mask-rejection logged | Zero parse failures on constrained paths over one week; fallback rate recorded | — | No |
| **3** | Frozen reference instrument: pinned checkpoint + batch-invariant kernels + fixed probe set | Two runs byte-identical; every measurement stamped (weights, kernel, engine, batch, sampling) | 0 | **Yes** — which checkpoint |
| **4** | **Count the data.** Open the trajectory log: contrastive pairs available, same-base fine-tunes held, per-role verified trajectories | A number for each | — | No |
| **5** | One adapter for the highest-volume role, A/B against its prefix-cached prompt on test-pass rate | Clears +3 points paired, or the programme is correctly abandoned | 0, 4 | No |
| **6** | Independent-family judge sidecar (8B 4-bit) | Runs; disagreement rate with composite critic measured | 0, 3 | No |

Units 1 and 2 are afternoons against measured effects and depend on nothing. Unit 0 is twenty minutes and may cancel half the list — which is why it is first.

---

## Open questions

- **β vs β\*.** If commensurable, downsizing is unjustified by an order of magnitude, unit 3 is the only survivor of the local programme, and the finding is that verification — not capability, not VRAM — was always the constraint. Unresolved.
- **Does the data exist?** Steering needs ~700 pairs; merging needs ≥2 same-base fine-tunes; adapters need per-role verified trajectories. Nobody opened the log. If thin, three angles are dead on arrival.
- **Does one process share a graph allowance across two loaded models?** `fit()` does not model it; the 16k co-residency figure fails if the allowance is per-model [asserted]. One hour on the hardware.
- **Joe's review budget was never costed.** Six monitored subsystems, each with a harness, canary suite and threshold, on a one-person project where review time is the stated bottleneck. The build order above assumes that cost is real and orders accordingly, but no angle priced it.
- **Ten angles, ten adopt-recommendations.** Only weight-editing said no, and it left a revisit trigger. A brief that wanted yes got yes ten times. That distribution is itself a finding about the method, and this map does not fix it — it only re-scores the outputs.
- **One measurement in the entire research corpus.** Everything else is a fetched abstract or arithmetic. The single executed check found the binding constraint. Unit 0 and unit 4 exist because of that lesson, and neither is research.
- **What else did the brief get wrong?** Six angles independently corrected 32 GB vs 64 GB. None asked the follow-up. Unanswered.

*~3,850 words.*

---

## Adversarial critic

## 1. Research result that has never survived production

**CAST (conditional activation steering, arXiv:2409.05907).**

The steering angle's entire autonomy claim rests on it — its own words: "the finding that saves the angle." Giveaway: one paper, one lab, one number (83.3%/2.4% on Hermes-2-Pro-8B), no independent replication, no deployment anywhere, and the metric is measured *on the gating task the authors chose*. Worse, the same angle cites Tan et al. (2407.12404) finding steerability "highly variable across different inputs" and "brittle to reasonable changes in the prompt" — which is a direct refutation of a cosine-threshold gate over prompt activations. The angle quotes both and reconciles neither.

Runners-up with the same signature: Arrow routing (66.6% vs 63.8%, one paper, and the "novelty detector" built on it is tagged `[asserted]` by its own author); surprisal-guided selection (single author, no venue, n=20, and it's the *only* evidence killing TTT).

## 2. Autonomy hand-wave

**Model merging.** Verdict given: "Selection: yes, already solved, no human needed." False. mergekit-evolve optimises a fitness function; a human must author the search task set, the *disjoint* accept set, the safety canary prompts, the promotion threshold, and the entropy alarm level — which the angle itself admits "is not established in any paper I verified." That is the whole decision. CMA-ES just turns the crank on a judgement someone already made.

Second: **adapter minting.** "When a new adapter is warranted: NO published system does this end-to-end… calling it validated would be dishonest" — then the recommendation ships it anyway as step 4.

## 3. Memory — the arithmetic nobody did across angles

Always-resident set implied by the six adopt-recommendations, 32 GB card:

| Item | GB |
|---|---|
| 8B base FP8 (serving) | 8.0 |
| 64 × rank-16 adapters | 5.4 |
| Draft model, spec decode | 0.7 |
| 14B Q8 second tier (architecture-surgery) | 14.0 |
| Frozen 32B Q4 reference instrument (what-frontier-cannot) | 19.0 |
| Independent-family judge, 8B 4-bit (self-improvement-limits) | 5.0 |
| KV, 32 streams × 4k, FP8 | 8.6 |
| **Total** | **60.7** |

**1.9× over a 32 GB card. 2.5× over 24 GB.** Add the QLoRA training run (12–18 GB peak) and it's 3×.

Minimum honest subset that fits 32 GB: base + 16 adapters + judge + KV = 22.9 GB. That buys you no frozen reference, no second tier, no local training — i.e. you lose the #1 recommendation from *two* angles. On 24 GB the judge goes too, which kills the only independent evaluator.

Every angle costed itself alone. None costed the union.

## 4. Self-evaluation

Worth approximately nothing, and the report contains the proof: measured composite verifier **β = 0.3132 [0.2926, 0.3346]**. A gate wrong 31% of the time cannot certify a weight change. arXiv:2404.13076 makes it worse — self-preference scales *linearly* with self-recognition, so the bias grows exactly as the system improves.

The only escapes are (a) executable ground truth and (b) a different-family frozen judge — and per §3 the judge doesn't fit alongside the rest. So: for any recommendation whose gate is model judgement (steering strength, merge promotion, adapter A/B on "diff-accepted"), the evaluation is worthless and the recommendation collapses with it. That is four of six.

## 5. Benchmark in the objective

**Sakana EvoLLM-JP: MGSM-JA 52.0 vs best-parent 30.0.** Quoted four times across the report as the proof that merging creates capability. It is the output of **1000 CMA-ES trials whose fitness function was MGSM**. The merging angle *notices* this ("1000 opportunities to overfit that benchmark") and then keeps using the number as headline evidence in its own `bar` section.

Also compromised: AlphaEdit's 98.90 efficacy (teacher-forced protocol, −58 points under WILD); SEAL's ARC 72.5% (RL'd against ARC); every mergekit-evolve gain by construction.

## 6. What all ten missed

- **Ten angles, ten adopt-recommendations.** Only weight-editing said no, and it left a revisit trigger. A brief that wants yes got yes ten times. That distribution is the finding.
- **Nobody costed Joe.** Six new monitored subsystems, each with a harness, canary suite and threshold, on a one-person project where review time is the stated bottleneck. Net effect: strictly negative.
- **Nobody checked whether the data exists.** Steering needs ~700 contrastive pairs; merging needs ≥2 same-base fine-tunes; adapters need per-role verified trajectories. Nobody opened the trajectory log to count. If it's thin, all three are dead on arrival.
- **Nine of ten never mentioned β vs β\*.** One angle ran actual code, found `β = 0.3132` against a required `β* = 3.3%`, and flagged it as gating *everything*. It gates the other nine too. They never looked.
- **Six independently corrected 32 GB vs 64 GB.** Six people found the brief's author didn't know the hardware, and none asked what else the brief got wrong.
- **Two recommendations contradict.** Decoding says delete the retry loop; self-improvement says loud failure is the only detector you have. Test-time says pick the *lowest-confidence* passing sample; decoding says constrain the tail away. Nobody noticed.
- **One measurement in the whole report.** Everything else is a fetched abstract or arithmetic. The single executed check found the binding constraint. That's the whole lesson.
