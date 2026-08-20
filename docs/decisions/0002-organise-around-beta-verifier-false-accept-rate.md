# 0002. Organise the system around β, the verifier false-accept rate

- **Status:** PROVISIONAL
- **Date:** 2026-08-19 (materially updated same day — see "Update: closed form")
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T2 model — **T3 (measure) not yet reached, which is why this is
  PROVISIONAL rather than ACCEPTED**
- **Executable model:** `../10-research/experiments/simulations.py` (exp 1, 2, 5),
  `../10-research/experiments/q3_bimodal_and_q2_sample_complexity.py`

## Update: β* has a closed form, and it is distribution-free

`[algebra]` — derived and numerically verified 2026-08-19. This supersedes the
`[simulated]` threshold table below, which is now a special case.

For a task of difficulty *d*, write `p_c`, `p_f` for the probability the cheap and frontier
models solve it. The cascade's pointwise advantage over always-frontier is:

```
Δ(d) = p_c(1−α)(1−p_f) − p_f(1−p_c)β
```

Setting Δ(d) = 0 and rearranging gives an odds ratio. Under a logistic competence model —
`p_m = σ(k(s_m − d))`, i.e. log-odds of success linear in difficulty, which is exactly a
Rasch / 1PL item-response model — that odds ratio is `e^{k(s_c − s_f)}`, and **d cancels**:

```
β* = (1 − α) · e^(−kΔ)          where Δ = s_f − s_c is the capability gap
```

Verified against simulation to three significant figures at every gap tested:
(1−0.03)·e^(−8×0.27) = 0.1118 vs 0.112 measured; gap 0.42 → 0.0337 vs 0.034;
gap 0.10 → 0.4358 vs 0.436.

**Consequence, and it is the most important thing in this ADR:** β* is invariant to the
difficulty distribution. Tested across unimodal Beta(2,2) and bimodal mixtures from 30% to
90% easy, β* moved by ≤ 0.003 while the escalation rate swung from 18.8% to 63.5%.

**Safety and savings separate.** The β-meter does not need to characterise a repository's
task-difficulty distribution to say whether cheap-first routing is *safe* — only to say how
much it will *save*. This closes Q3 and removes the largest modelling risk in the project.

Remaining exposure: the result is exact *given* logistic competence. It is not free of
functional-form assumptions, only free of distributional ones. Precedent for the Rasch
framing in this setting exists (IRT-Router, Song et al. 2025).

## Update: β sample complexity (Q2)

`[algebra]` — β is a binomial proportion over diffs the checks **accepted**. Wilson 95%
intervals at true β = 0.05: n=50 → [0.011, 0.135]; n=100 → [0.022, 0.112];
n=200 → [0.027, 0.090].

Under a conservative decision rule (declare routing safe only if the upper 95% bound clears
β*), the **false-safe rate is near zero but not zero** — the rule is conservative, just
underpowered near the threshold.

> **Corrected 2026-08-20.** This sentence read *"the false-safe rate is **0** at every sample
> size tested"*. It is contradicted by the executable model this ADR names as its own source.
> Running `q3_bimodal_and_q2_sample_complexity.py` unchanged prints, for a genuinely unsafe
> repository at true β = 0.15: **0.003 at n = 50** and **0.001 at n = 100**. [measured] The
> script's own column note says the rate *"must be ~0"* — which is true, and is a different
> claim from *"is 0"*. A tilde was dropped in transcription and an approximation became a
> guarantee, on a safety property.
>
> The exact binomial confirms the simulation rather than the prose. At n = 50 the rule declares
> safe for k ≤ 1, and P(X ≤ 1 | n = 50, β = 0.15) = **0.0029055**; at n = 100 it declares safe
> for k ≤ 5, and P(X ≤ 5 | n = 100, β = 0.15) = **0.0015527**. Over the 8,000 draws the script
> uses, those predict 23.2 and 12.4 false-safes — and observing none at n = 50 would have
> probability 8 × 10⁻¹¹. [measured]
>
> **It is worse just above the threshold, which is the regime that matters.** At true β = 0.12,
> barely above β\* = 0.1119, the false-safe rate at n = 50 is **0.0131** — about 105 in 8,000.
> [measured] The rule is weakest exactly where a repository is marginally unsafe, which is
> precisely where a wrong answer is most likely and least detectable.
>
> **What is unchanged:** the decision rule itself, and the conclusion that it is conservative
> and underpowered near the threshold. What is withdrawn is the claim of a *zero* error rate.
> A conservative rule with a small, quantified error rate is honest; a rule advertised as
> having none is not, and this project's whole thesis is that tests have error rates.
>
> Found by Codex auditing numeric provenance across the decision records; the arithmetic was
> reproduced independently and against the script's own output before this correction was
> written. At true β = 0.04 against β* = 0.111, n≈200 declares safe
97% of the time. At true β = 0.08, even n=800 only reaches 84%.

**Operational rule:** 50–200 accepted diffs suffice when β is far from β*; near it, report
"insufficient data" rather than a verdict. Prospective labelling is too slow; **historical
mining is the route** — PR outcomes, reverts and follow-up fix commits as proxy labels.
`jobboard-v2` (991 commits in 36 days) is the first corpus.

**Sampling bias warning:** `jobboard-v2` has ~20 CI ratchets, 44 invariant probes and
coverage floors. It is a *low-β* repo, which is the regime where cascading looks best.
Measuring only there will flatter the thesis. Measure a weakly-verified repo as a contrast
case before believing the numbers.


## Update: Δ discipline — what may and may not be called a capability-gap change

Added 2026-08-19, after three separate proposals arrived claiming "X narrows Δ and
therefore loosens β*" (native tools; context discipline; a reasoning layer). Each was
derived and attacked in `../10-research/experiments/capability_context_beta_star.py`
before anything was written here. **A formula that explains every improvement explains
none of them; the three turned out to be three different curve deformations, and only
one is a Δ change.**

1. **Native tools do not narrow Δ.** `[algebra]` Missing capabilities are structural
   zeros — tasks the cheap tier cannot attempt at any difficulty — not a competence
   deficit; a 4B model with a browser is still a 4B model. The correct object is the
   blocked-task fraction φ and the catch rate of capability failures: with
   β_blocked = r·β,  β*_eff = (1−α)(1−φ)·E[p_c(1−p_f)] / ((1−φ)·E[p_f(1−p_c)] + φ·r·E[p_f]).
   At r=0 (capability failures always caught) the threshold is **unchanged** and the
   tool layer is a cost lever; at r=1 it drops (0.112 → 0.059 at φ=0.3) and the closed
   form is **false-safe about tasks it does not model**. Which regime holds is a
   per-check-class measurement (`0012`), `[asserted]` until measured.
2. **Context discipline is the one genuine Δ mechanism.** `[algebra]` given the mapping;
   the causal step is `[asserted]`. Irrelevant loaded tools degrade success *on the same
   task* — a real competence term — so disciplined loading narrows Δ and loosens β*
   directionally. The asymmetry assumption is load-bearing: the delegated path already
   has progressive disclosure (Claude Code tool search, v2.1.7 `[measured]`), so clutter
   taxes the native/cheap path more. Magnitude unmeasured — the best public number
   (Opus 4 49%→74% with deferred loading) has an **undefined metric** at source and is
   illustrative only. EXP-18 measures the slope for local models.
3. **Reasoning scaffolds change the curve's shape, not its position.** `[algebra]`
   Majority-of-5 self-consistency steepens the cheap tier's logistic slope ×1.875 at the
   midpoint — precisely the unequal-slopes violation under which β* is **not**
   distribution-free (`robustness_beta_star.py` V1). Computed: β* under a scaffolded
   cheap tier spans 0.024–0.233 across difficulty distributions while aggregate success
   moves 0.439→0.429 on Beta(2,2) at 5× cost. The β* effect of scaffolding has no
   distribution-independent sign; "scaffolding narrows Δ" is rejected as not
   well-formed. Cost side folded into EXP-07 (≥2× wall-clock multiplier reopens `0003`).
4. **Verifier-shopping.** `[algebra]` Any retry/best-of-n loop that samples until the
   checks pass exposes the verifier n times: P(bad ships | task beyond the model)
   = 1−(1−β)ⁿ — 0.41 at β=0.10, n=5. Every resampling scheme must budget against this,
   including the cascade's own retries if any are ever added.

**The rule going forward:** "narrows Δ" may be claimed only for an intervention shown to
produce a *uniform log-odds shift* of the competence curve. Feasibility changes, slope
changes and floor changes must be named as such — each has different, already-computed
β* behaviour — and every such claim must be stated as a prediction ("this should move
β* to Y, measurably") rather than an explanation. This subsumes the "Remaining exposure"
paragraph above: the closed form's fragility is not a residual caveat, it is the reason
this rule exists.

**Falsifiability check on the frame itself** (added same day, after a fourth Δ-framed
proposal — model probing, which *measures* Δ rather than moving it): the abstraction
passes the "name something outside it" test, which is what keeps it a theory rather than
a vocabulary. Routing demonstrably improves through levers that are **not** Δ changes:
lowering α (deflaking tests) enters β* through the other factor; lowering β itself
(better verifiers) moves the measured side of the comparison; **reducing model-failure
correlation ρ** — choosing a cheap tier with *different* failure modes at the same
competence — restores both the quality advantage and the threshold (V4: β* 0.028→0.112
as ρ→0) while leaving Δ untouched, and is the largest unexploited lever this analysis
has found; and structural levers (escalation-ladder depth, wasted-work cost, difficulty
triage, label-collection speed) sit outside the formula entirely. Δ is one axis of a
(Δ, α, β, ρ)-plus-structure safety surface. Proposals pitched "because Δ" get checked
against this list first. Note the ρ lever is CONSILIENCE.md clause 2 in routing form:
a decorrelated second model is worth more than a slightly stronger correlated one —
different class of facts, again.

## Context

Every harness routes work to cheaper models and runs agents in parallel. Every one assumes
its verification layer is sound. The routing literature is explicit that the deferral signal
is the unsolved part, and that cascades work well where outputs are *objectively assessable*
and are much harder in open-ended settings. Coding is the domain where an oracle exists —
tests, typecheck, build.

Define **β = P(automated checks accept | artifact is actually bad)**.

## Decision

Make β the organising parameter of the system. Measure it per repository. Derive routing
depth and the parallelism ceiling from it rather than exposing them as user configuration.
Refuse to cascade below the measured β\* for the capability gap in play.

## Evidence

- `[algebra]` The parallelism ceiling is exact: `n_max = T_agent_cycle / T_effective_review`.
  At a 25-min cycle and 8-min review, 3.1 agents. Beyond saturation, throughput pins and
  queue wait diverges.
- `[algebra]` Critic recall ≡ 1 − β. The same quantity governs routing safety **and** the
  parallelism ceiling **and** human review load. This identity is the whole claim.
- `[simulated]` Cascade beats always-frontier on cost *and* quality below β ≈ 0.11
  (+4.0 pp quality at β=0, +0.4 pp at β=0.10, −1.3 pp at β=0.15). Sign flip is robust to
  parametric choice; the threshold value is not.
- `[simulated]` β\* tightens as the capability gap widens: gap 0.42 → β\* 0.033;
  gap 0.27 → 0.111; gap 0.10 → 0.432. The cheaper the model you route to, the better your
  tests must be.
- `[cited]` No prior art found for measuring a repository's own verifier reliability and
  deriving configuration from it. Searched: FrugalGPT, Hybrid LLM, RouteLLM, AutoMix,
  UniRoute, Dekoninck et al. (ICML 2025), RouterBench/RouterArena/LLMRouterBench,
  arXiv:2603.04445 survey.

## Evidence against

- `[cited]` **`Affordance agent harness: verification-gated skill orchestration`**
  (Huang, Shi, Li & Chen, arXiv:2605.00663). **Not read.** The title alone overlaps the core
  idea. This is the single largest open risk to this ADR.
- `[cited]` Meta-Harness (arXiv:2603.28052) may subsume this by searching harness code
  directly, without needing an explicit β measurement.
- `[cited]` The literature's mitigations for the deferral-signal problem (GATEKEEPER,
  UCCI's isotonic calibration at ECE 0.03, conformal risk control, semantic agreement,
  hidden-state probes) all attack calibration of *model confidence* rather than reliability
  of an *external verifier*. That is either the gap, or evidence that people who thought
  hard about this went elsewhere for a reason.
- All simulation results assume difficulty `~ Beta(2,2)` and sigmoid competence. **Both
  invented.** If real coding-task difficulty is bimodal, smooth thresholds become cliffs and
  the design changes shape (Q3).
- **β has never been measured on a real repository.** The entire ADR rests on a quantity
  whose measurability is unestablished (Q2).
- The simulations were written by the same party that formed the hypothesis, with no
  independent review.

## Consequences

**Positive.** Gives the project a single falsifiable centre. Produces a genuinely useful
output even in the negative case ("your tests are too weak to route cheap on this repo, and
you can safely run 2 agents, not 8" is advice nothing else gives).

**Negative.** Everything is downstream of one number. If β is unmeasurable at solo-founder
data volumes, the architecture has no centre and must be replaced, not patched.

**Neutral but load-bearing.** Requires human verdicts on diffs the checks passed —
so the trajectory record and the review UI are now on the critical path, not optional.

## Enforcement

- Check: routing depth and parallelism must be **derived** from measured β, never read from
  user config. A lint rule must ban a config key that sets either directly.
- Fails CI: yes, once implementation exists.
- Same commit as implementation: **required** (invariant I1).

## What would overturn this

1. arXiv:2605.00663 already does this → rewrite or abandon the novelty claim.
2. β needs more human-labelled diffs per repo than a solo developer produces in a quarter,
   and proxy labels (reverted commits, follow-up fix commits, escaped bugs) don't
   substitute → the instrument is unbuildable.
3. Real difficulty distributions are bimodal → thresholds become cliffs; the product becomes
   a one-line rule rather than a measured instrument.
4. β turns out near-zero in every well-tested repo → everyone is already safely in the
   dominant regime and the measurement is uninteresting.

**Run test 3 first.** It is the cheapest and the most likely to be true.

## Publication candidate?

**Yes, conditionally** — and only after T3. If β is measured on ≥3 real repositories and the
identity β ≡ 1 − critic recall holds empirically, that is a short, useful, honest paper.
If β proves unmeasurable, *that is also publishable* and arguably more useful.
See `../publications/README.md`.
