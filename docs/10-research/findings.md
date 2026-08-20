# Simulation findings

All five experiments were **executed**, not recalled. Code in `experiments/`. Re-run before
trusting any number here.

## Status labels

- `[simulated]` — result of a model with assumed functional forms. Tells you about the
  model, not the world.
- `[algebra]` — exact derivation, no simulation assumptions.

## Assumptions common to experiments 1–4a

Task difficulty `d ~ Beta(2,2)`; probability a model solves a task = `sigmoid(k·(s_m − d))`
with `k=8`; verifier false-reject `α=0.03`; costs in arbitrary units with frontier ≈ 25×
cheap. **These shapes were invented.** What survives them is the *existence and direction*
of thresholds, not the figures.

---

## 1. β flips the sign of the routing decision `[simulated]`

Cascade (cheap → verify → escalate on failure) vs always-frontier, sweeping
β = P(verifier accepts | artifact is bad):

| β | escalation rate | cascade quality − frontier quality | cost as % of frontier |
|---|---|---|---|
| 0.00 | 57% | **+4.0 pp** | 63% |
| 0.02 | 56% | +3.3 pp | 62% |
| 0.05 | 55% | +2.2 pp | 60% |
| 0.10 | 52% | +0.4 pp | 57% |
| 0.15 | 49% | −1.3 pp | 55% |
| 0.20 | 46% | −3.1 pp | 52% |
| 0.30 | 41% | −6.7 pp | 46% |
| 0.60 | 24% | −17.3 pp | 29% |

Below β ≈ 0.11 the cascade beats the frontier model on cost **and** quality at once —
it is a two-draw process, so the cheap model sometimes succeeds where frontier fails and
the verifier filters the rest. Above it, you are buying cost savings with silent defects.

## 2. The threshold tightens as the capability gap widens `[simulated]`

Solving for β* where cascade quality equals frontier quality:

| capability gap (s_frontier − s_cheap) | β* |
|---|---|
| 0.42 | 0.033 |
| 0.32 | 0.076 |
| 0.27 | 0.111 |
| 0.17 | 0.249 |
| 0.10 | 0.432 *(superseded: the closed form gives 0.4358 at gap 0.10 — see ADR-0002's update, which records the exact recomputation. Retained because this table is the simulation it superseded.)* |

**The cheaper the model you route to, the better your tests must be.** Haiku-tier routing
on a thinly-tested repo is strictly worse than not routing.

## 3. Escalation depth is nearly free `[simulated]`

Three tiers (cheap → mid → frontier, verified at each hop), β=0.10:
**43.9% of frontier cost at +4.1 pp quality**, vs two tiers at 57% cost and +0.4 pp.
Build the ladder, not the switch.

## 4. The learned router is not worth building `[simulated]`

Thompson sampling over per-task-class routing (8 classes), against the best fixed policy
(always-cheap-with-escalation):

| trajectories | utility vs best fixed |
|---|---|
| 500 | −0.014 |
| 2,500 | −0.005 |
| 5,000 | −0.0000 |
| 10,000 | +0.0001 |
| 25,000 | −0.0008 |

~5,000 trajectories to *draw level*; no gain after. **The cascade already is adaptive
routing** — escalation-on-failure does the work a learned prior would do.

### 4a. When learning *does* pay `[simulated]`

Oracle per-class routing vs plain cascade, by wasted-work multiplier on a failed cheap
attempt (1× = pure API cost; higher = wall-clock you care about):

| multiplier | headroom |
|---|---|
| 1.0× | +0.002 (noise) |
| 1.5× | +0.011 |
| 2.0× | +0.024 |
| 3.0× | +0.054 |
| 5.0× | +0.123 |

Route by prior only when escalation burns time, not just tokens.

## 5. Human review is the hard ceiling `[algebra]`

Exact, no simulation assumptions:

```
n_max = T_agent_cycle / T_effective_review
```

At a 25-min agent cycle and 8-min review: **3.1 agents**. Beyond that, throughput pins at
7.5 diffs/hr and queue wait diverges. Adding agents past saturation adds nothing but latency.

The only lever that raises the ceiling is a critic tier that rejects bad diffs pre-review:

| critic recall | max agents | good merges/hr |
|---|---|---|
| 0.00 | 3.1 | 4.1 |
| 0.50 | 4.0 | 5.3 |
| 0.85 | 5.1 | 6.7 |
| 0.95 | 5.5 | 7.2 |

**Critic recall = 1 − β.** One measured quantity governs routing safety, parallelism
ceiling, and human review load. That identity is the reason this project exists.

---

## What would falsify the thesis

- β turns out to be unmeasurable in practice (too few human-verdict samples per repo to
  estimate it before the models change underneath you).
- β turns out to be so low in well-tested repos that everyone is already safely in the
  dominant regime and the measurement is uninteresting.
- β turns out to be so high everywhere that cheap-first routing is simply never advisable
  and the answer is a one-line rule, not a product.
- Real task-difficulty distributions are bimodal rather than Beta-like, in which case the
  smooth thresholds above become cliffs and the design changes.

**Open the last one first.** It is the most likely to be true.
