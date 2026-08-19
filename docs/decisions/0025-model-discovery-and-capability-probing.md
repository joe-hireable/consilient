# 0025. Model discovery and capability probing — listen, probe, derive; no learned router, no GNN

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (proposal), Claude (design + verification)
- **Inquiry tier reached:** T2 — executable models exist and were run
- **Executable model:** `../10-research/experiments/probe_delta_ci.py` (probe CI),
  `../10-research/experiments/capability_context_beta_star.py` (correlation correction)

## Context

New models appear weekly across OpenRouter, Ollama, vLLM, Hugging Face and lab
announcements. The cascade needs to know, for each candidate cheap tier: is routing to
this model safe *on this user's repository*? The learned-router answer was already
rejected on sample-complexity grounds (ADR-0003). The question is whether a cheap,
local, on-demand **probe** can estimate the capability gap Δ directly, so that the
threshold algebra — with its measured corrections — prices a new model the day it lands.

Prior-art verdict (verified at origin, 19 Aug 2026): the pieces exist, the assembly does
not. **IRT-Router** (Song et al., ACL 2025, arXiv:2506.01048) is the mature academic
version of ability-estimation routing — and its own held-out experiment documents the
hole this ADR fills: a new model's ability, inferred from its *text-profile embedding*
rather than its behaviour, scores ACC 0.67, which the paper itself calls "limited
generalization to unseen LLMs". Its training regime (~24k queries × 20 models graded)
is exactly what a solo user does not have. **Generic per-model scores are commoditised
and ingestible** (Artificial Analysis API — fresh within ~a day, attribution-required;
Epoch's CC-BY feed; frozen research snapshots: RouterBench, LLMRouterBench, metabench's
fitted IRT abilities). **Nobody publishes abilities on a user's own task distribution,
and no maintained ability feed exists.** OpenRouter's Ori Eval (Aug 2026) is the
nearest commercial neighbour — eval-on-release against your own prompts — but is
platform-tied and not local-first.

## Decision

Three parts, all local-first (ADR-0024: no phone-home; feeds are *polled*, results stay
on the machine).

### 1. Listen

Poll release sources the user enables (OpenRouter models API, Ollama registry, HF, lab
feeds). Ingest commoditised generic scores as **advisory priors only** (Artificial
Analysis / Epoch, licences respected). A generic score never gates routing — it decides
whether a model is *worth probing*.

### 2. Probe — the paired discordant-pair estimator

Run the candidate and the frontier reference on the **same** n probe tasks, drawn from
the user's own trajectory log (fallback: a seed set, replaced as the log accumulates).
Under the Rasch model, difficulty cancels from the conditional likelihood exactly as it
does from β*:

```
P(frontier wins | pair discordant) = e^(kΔ) / (1 + e^(kΔ))
⇒  Δ̂ = (1/k)·logit( m_f / (m_f + m_c) )
```

`[algebra]` — no per-task difficulty estimates, no calibrated item bank, no fitting:
count frontier-only successes and cheap-only successes. Monte Carlo CI
(`probe_delta_ci.py`, at true Δ=0.27): `[simulated]`

| n | β* 68% band (independent outcomes) | verdict |
|---|---|---|
| 20 | [0.064, 0.310] | coarse screen (~2× band) — enough to rule out obviously unsafe routing |
| 100 | [0.064, 0.193] | usable band |
| 200 | [0.077, 0.164] | approaching decision grade |

Two design facts that matter:

- **The same 2×2 outcome table yields φ̂, the outcome correlation** — the quantity that
  collapses β* (ADR-0002 Δ-discipline; β* 0.112→0.028 at ρ=0.6) and that no published
  benchmark score can provide, because published scores are per-model, never paired.
  One probe, both parameters. SE(φ̂) ≈ 0.07–0.10 at n=100 — coarse, but the only local
  estimate there is. `[simulated]`
- **Under correlation the naive Δ̂ is biased upward** (0.34 vs true 0.27 at ρ=0.6) —
  conservative in direction but insufficient: the probe band still overstates the safe
  threshold relative to the correlation-corrected truth. **Rule: the routing verdict
  uses β*(Δ̂) corrected by φ̂, never the raw closed form.** `[simulated]`
- Cheapness levers, in order: draw tasks from the trajectory log (the distribution that
  matters); concentrate items where discordance is likely (CAT-style adaptive selection —
  IRT-Router's machinery is the natural fit here, used *for* the probe rather than
  instead of it); pair tightly (discordant pairs carry all the information).

### 3. Derive

Δ̂ + φ̂ + the repo's measured β̂ (EXP-01) → route / do-not-route / insufficient-data,
by the ADR-0002 rules. No learned policy anywhere. **Insufficient-data is an honest
verdict**, reported as such (probe CIs at n=20 will often produce it near the
threshold — that is the instrument working, not failing).

### Staleness

Models change behind stable names (provider quantisation changes, silent updates).
Re-probe triggers: version/hash change where detectable; otherwise a 10-task drift
subset on a weekly cadence, escalating to a full re-probe when the subset's discordance
pattern shifts beyond its CI. Cadence numbers `[asserted]` until EXP-20 reports.

## Considered and rejected: graph neural networks

Recorded because it will come up again; silence would be worse than a decision.

**Routing.** GraphRouter (Feng, Shen & You, ICLR 2025, arXiv:2410.03834) is the serious
version: heterogeneous task/query/LLM graph, routing as edge prediction, +12.3% over
the best bandit baseline. Read honestly, it does not fit here:

- Data appetite: ~1,680 labelled training queries with per-LLM outcomes over a fixed
  10-model pool. EXP-03 showed Thompson sampling needs ~5,000 trajectories to *match*
  the plain cascade; a GNN learns edge structure on top of per-arm means. At
  solo-founder volumes it never leaves initialisation. `[simulated]` + `[cited]`
- Its "unseen model" pitch is a cold-start *mitigation*, not elimination: the few-shot
  variant still requires **80 logged interactions per new model** and trails its own
  fully-trained variant. The probe needs ~20–100 *paired* tasks and no training phase.
- **The decisive absence:** no published result anywhere — confirmed against the 2026
  routing survey (arXiv:2603.04445) — compares a learned router against the natural
  baseline in this domain: try-cheap-then-escalate gated by *executed tests*. Routers
  beat confidence-gated cascades (arXiv:2605.06350); verifier-gated cascades beat
  routers where verification is cheap. Nobody has published the head-to-head this
  rejection turns on, and every routing paper avoids that baseline. `[cited]`
- Honest counterweight, so the rejection is not overclaimed: the structural-cost
  argument survives a perfect verifier — a cascade pays the wasted cheap attempt on
  every escalated task, a pre-generation router does not. **The rejection is therefore
  conditional on cheap verification AND a non-trivial cheap-tier solve rate**, and on
  EXP-07's wasted-work multiplier staying under 2×.

**Memory.** ADR-0017's stack (Graphify AST graph; MemPalace temporal entity graph) is
already graphs — structural, local, training-free. A GNN adds learned embeddings over
that structure, requiring training data that does not exist, to improve retrieval that
is not a measured bottleneck. Through Aug 2026 the LongMemEval/LoCoMo record contains
**no case of learned graph embeddings beating structural temporal-KG memory** — every
top system is LLM extraction + structural retrieval. (Absence of published attempts,
not a measured negative. `[cited]`)

**Correction recorded while checking this** (the bibliography entry was wrong): the
"Graphiti 63.8% vs mem0 49% on LongMemEval temporal" figure is a **mashup** — 63.8% is
Zep's *overall* score from its own vendor paper (arXiv:2501.13956); 49.0% is mem0's
*overall* score from an unrelated third party (arXiv:2603.04814); no head-to-head
temporal comparison exists. Real vendor-measured temporal numbers: Zep 54.1%/62.4% vs
full-context 36.5%/45.1% — and the Zep-vs-mem0 comparison is an unresolved two-sided
dispute in which both vendors have corrected their own numbers, with mem0 claiming
94.4% by 2026. Per working principle 2: cite the sign and the dispute, never the
points. The *qualitative* claim survives: the temporal gains came from modelling time
structurally, not from neural machinery.

**Reopen conditions, concrete:**

1. The trajectory log passes ~5,000 labelled routing outcomes (EXP-03's break-even) —
   and EXP-07 shows a wasted-work multiplier ≥2×, so prediction starts paying.
2. Measured evidence that *retrieval* (not structure) is the memory bottleneck — a
   recall/precision measurement on the user's own log, not a benchmark.
3. A published learned-router result beating cascade-with-oracle in a domain with cheap
   verification. None exists as of Aug 2026; one paper would reopen this.

## Evidence

- `[algebra]` The discordant-pair estimator and its difficulty cancellation — the same
  cancellation as the closed form, so the probe is honest exactly where the routing
  rule is honest, and dishonest in exactly the same places (the point of EXP-20).
- `[simulated]` CI table and correlation bias above; `probe_delta_ci.py`, seeded.
- `[cited]` IRT-Router's model-cold-start failure (ACC 0.67, its own appendix);
  its ~489k-interaction training regime. Read in full 19 Aug 2026.
- `[cited]` Consumable-feed landscape as in Context; RouterArena's labels carry an
  eval-only clause (a legal blocker on fitting anything to them).
- `[measured]` EXP-16's demonstration that this repo's own review process produced a
  fabricated figure — motivating probe-over-trust for *our own* numbers too.

## Evidence against

- The probe inherits every closed-form fragility (unequal slopes, links, floors —
  `robustness_beta_star.py`). It measures Δ *within a model family that is known to be
  wrong in the tails*. EXP-20's consilience check is the only defence: two routes to
  the same number, disagreement means the model is at fault.
- Probe tasks from the trajectory log are non-stationary; Δ̂ ages with the work mix.
- A 20-task screen will be quoted as a measurement by someone. The output schema must
  carry the CI and refuse to print a point estimate without it (same contract as the
  Inquiry tier's sign/threshold rule).
- Frontier-reference drift: Δ is measured against a moving reference; a frontier
  upgrade silently widens every gap. The reference version is pinned per probe and
  recorded in the log.

## Enforcement

- Check: routing verdicts derive from (Δ̂, φ̂, β̂) only; a config key naming a model as
  "safe" without a probe record fails lint (extends ADR-0002's enforcement).
- Check: probe outputs without CIs fail schema validation.
- Check: no network call in the listener beyond user-enabled feeds; asserted by the
  ADR-0024 no-outbound test class.

## What would overturn this

- EXP-20's stopping rule firing (probe-vs-direct disagreement beyond CIs).
- The probe needing >200 tasks in practice to clear insufficient-data at typical gaps —
  at which point it is not cheap, and ingested generic priors + direct β measurement
  alone must carry v1.

## Publication candidate?

Possibly, folded into the β paper: "a 100-task paired probe prices a new model's
routing safety, and measures the correlation term benchmark scores cannot see" is a
small clean claim with EXP-20 as its experiment. Not standalone.
