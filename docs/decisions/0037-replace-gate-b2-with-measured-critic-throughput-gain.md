# 0037. Replace Gate B2 with measured critic review-throughput gain — supersedes 0015 Gate B2

- **Status:** ACCEPTED
- **Date:** 2026-08-20
- **Deciders:** Cursor / Gemini 3.7 Flash High (dispatched agent, technical authority), Joe Brown (intent)
- **Supersedes:** [0015](0015-dogfooding-gate.md) Gate B condition 2
- **Inquiry tier reached:** T2 model
- **Executable model:** `../10-research/experiments/gate_b2_throughput_gain.py`

## Context

ADR-0015 established a staged dogfooding gate for Consilience. Stage 3 (enabling autonomous
routing and multi-agent parallel orchestration on non-Consilience repositories) required four
conditions under Gate B. Condition 2 was specified as:

> *"EXP-08 complete: critic recall measured, and the derived parallelism ceiling is > 1."*

An audit on 20 August 2026 revealed that **Gate B2 cannot fail under any circumstances**. Under the
algebraic model in `findings.md` §5 and `simulations.py`:

```
frac_seen = p_good + (1 − p_good)(1 − recall) = p_good + (1 − p_good)β
T_eff     = frac_seen · T_r
n_max     = T_a / T_eff = T_a / ([p_good + (1 − p_good)β] · T_r)
```

Because $p_{\text{good}} \in [0, 1]$ and $\beta \in [0, 1]$, $\text{frac\_seen} \le 1.0$ identically.
Consequently, $T_{\text{eff}} \le T_r$ and:

$$n_{\text{max}} \ge \frac{T_a}{T_r} = \frac{25}{8} = 3.125 > 1.0 \quad \text{for every } \beta \in [0, 1]$$

Even if critic recall is zero ($\beta = 1.0$, a critic that catches zero bad diffs), $n_{\text{max}} = 3.125 > 1$.
The condition is a pure tautology: it passes before any measurement is taken and cannot discriminate
a working critic from a broken one. [algebra]

Furthermore, Gate B2 was the **only** gate condition across Gate A and Gate B that depended on $\beta$.
With Gate B2 non-discriminating by construction, $\beta$ gated nothing in the transition to Stage 3.
This defect left the core thesis of Consilience untested at the primary control boundary. [asserted]

## Decision

**Replace ADR-0015 Gate B condition 2 with a requirement that the critic tier demonstrates a measured
review-throughput gain of at least 20% over the unassisted baseline in EXP-08:**

> **Gate B Condition 2 (Superseding):**
> *EXP-08 complete: critic recall $R = 1 - \beta$ on historical bad PR diffs is measured, and the derived
> good-merge throughput $M(\beta)$ exceeds the unassisted baseline $M_0$ by at least 20% ($G(\beta) \ge 0.20$,
> requiring $\beta \le 0.6296$ under nominal $p_{\text{good}} = 0.55$), with the 95% Wilson confidence
> interval on recall excluding zero ($R_{\text{low}} > 0$).*

The unassisted baseline ($R=0, \beta=1, \text{frac\_seen}=1$) throughput is:
$$M_0 = \frac{p_{\text{good}}}{T_r} = \frac{0.55}{8/60} = 4.125\text{ good merges/hour}$$

The critic-assisted throughput is:
$$M(\beta) = \frac{p_{\text{good}}}{T_{\text{eff}}} = \frac{p_{\text{good}}}{[p_{\text{good}} + (1 - p_{\text{good}})\beta] T_r}$$

The relative gain $G(\beta) = \frac{M(\beta) - M_0}{M_0} = \frac{(1 - p_{\text{good}})(1 - \beta)}{p_{\text{good}} + (1 - p_{\text{good}})\beta}$
has an exact closed-form threshold for $\gamma = 0.20$:
$$\beta_{\text{crit}} = \frac{1 - (1 + \gamma)p_{\text{good}}}{(1 + \gamma)(1 - p_{\text{good}})} = \frac{1 - 1.20(0.55)}{1.20(0.45)} = \frac{0.34}{0.54} \approx 0.6296 \quad (R \ge 0.3704)$$

**Routing safety remains governed by ADR-0002.** Cheap-first cascade routing is enabled only where
measured $\beta \le \beta^* \approx 0.1118$. If Gate B2 passes but a specific repository has $\beta > \beta^*$,
Stage 3 parallel agents operate on frontier models rather than cheap models.

## Evidence

- `[algebra]` The proof that ADR-0015 Gate B2 is a tautology: $\min_{\beta \in [0, 1]} n_{\text{max}}(\beta) = T_a / T_r = 25/8 = 3.125 > 1.0$.
- `[algebra]` Exact closed form for critical $\beta$ at relative throughput gain $\gamma$:
  $\beta_{\text{crit}} = \frac{1 - (1+\gamma)p_{\text{good}}}{(1+\gamma)(1-p_{\text{good}})}$.
- `[measured]` Output of `../10-research/experiments/gate_b2_throughput_gain.py` showing mechanical discrimination:
  - **Pass case:** $\beta = 0.30$ (recall $0.70$) $\implies M = 6.022\text{ merges/hr}$, Gain $= +45.99\% \ge +20\% \implies \textbf{PASS}$.
  - **Fail case:** $\beta = 0.85$ (recall $0.15$) $\implies M = 4.424\text{ merges/hr}$, Gain $= +7.24\% < +20\% \implies \textbf{FAIL}$.
  - **Zero-recall case:** $\beta = 1.00$ (recall $0.00$) $\implies M = 4.125\text{ merges/hr}$, Gain $= +0.00\% < +20\% \implies \textbf{FAIL}$.
- `[simulated]` EXP-08 sample complexity: evaluating a local 14B model on $N=60$ historical bad PR diffs yields a Wilson 95% interval width of $\approx \pm 0.12$. A true recall $R \ge 0.50$ clears $R_{\text{low}} > 0$ and $\beta \le 0.6296$ unambiguously.

## Evidence against

- **Deleting Gate B2 was considered:** If parallel orchestration in Stage 3 is viable without critic filtering
  (relying solely on the human to absorb diffs serially at $n_{\text{max}} = 3.125$), Gate B2 could be dropped entirely.
  *Why we replaced instead:* Deleting Gate B2 leaves $\beta$ gating zero control boundaries across the entire project,
  abandoning the core architectural premise of `CONSILIENCE.md`. Replacing it provides an operative, falsifiable gate.
- **Requiring $\beta \le \beta^*$ for Gate B2 was considered:** Setting Gate B2 to $\beta \le \beta^* \approx 0.1118$
  was evaluated.
  *Why not adopted:* Prospective sample complexity at $N=30$ human rejections makes the Wilson 95% upper bound
  mathematically unable to clear $\beta^*$ even with 0 false accepts ($[0.0, 0.1135] > 0.1119$). A gate that cannot
  open during solo dogfooding gets waived. Separating critic throughput gain ($G(\beta) \ge 20\%$ via EXP-08)
  from per-task cascade admission ($\beta \le \beta^*$ via ADR-0002) ensures the gate is reachable and meaningful.
- `[asserted]` The 20% throughput threshold relies on nominal point estimates $p_{\text{good}} = 0.55$ and
  $T_r = 8\text{ min}$. If base rate $p_{\text{good}} > 0.80$, the maximum possible critic gain is small ($\le 14\%$),
  meaning high-quality repositories would struggle to show a 20% gain.

## Evaluation Cost

- **EXP-08 evaluation cost:** A local 14B parameter model running over 50–100 historical PR diffs on the local RTX 5090
  costs **$0.00 in API spend** and approximately 10–15 minutes of GPU compute.
- It requires no prospective production traffic and no waiting for 30 human rejection events. It is entirely reachable
  before Stage 3 deployment.

## Consequences

**Positive.** Replaces a non-discriminating tautology with a mechanically falsifiable condition that directly connects $\beta$
to human review throughput. Restores $\beta$ as an operative gate on multi-agent orchestration.

**Negative.** Stage 3 cannot be entered without executing EXP-08.

**Neutral but load-bearing.** Gate B2 specifically validates the *critic tier's review-filtering leverage*. Model routing
safety remains independently bounded by ADR-0002's $\beta \le \beta^*$ check.

## Enforcement

- Check: `docs/10-research/experiments/gate_b2_throughput_gain.py` computes the threshold and validates pass/fail behavior.
- Check: `consil doctor` (ADR-0015 debt) will evaluate Gate B2 from recorded EXP-08 outcome logs before unlocking
  multi-agent orchestration flags.

## What would overturn this

- EXP-08 demonstrates that 14B local models achieve near-zero recall ($R < 0.10, \beta > 0.90$) on code diffs,
  falsifying the assumption that local critic tiers provide meaningful human review reduction.
- Empirical measurement on target repositories shows $p_{\text{good}} \ge 0.85$, demonstrating that human review is
  not bottlenecked by bad diffs and review-surface tooling is the binding constraint (overturning ADR-0007).

## Reversal Path

```bash
git revert <this-commit-hash>
```

Restores ADR-0015 Gate B2 text or deletes Gate B2.

## Publication candidate?

No.
