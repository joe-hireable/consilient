# Composite β under dependence: derive the bounds, and then admit whose theorem it is

**Date:** 20 August 2026
**Status:** `[measured]` for every EXP-47 count re-read from `experiments/exp47/results-exp47.json`;
`[algebra]` for the bounds, their sharpness and the identities derived from them, all computed in
exact rational arithmetic and cross-checked against an independent solver; `[cited]` for the
literature, at the read-depth recorded in § 11; `[asserted]` for the novelty verdict and the
recommendations.
**Reproduction:** every figure below comes from a single script over the EXP-47 result file. It
writes nothing and lives outside the tree; § 12 gives the reversal path and the reason it is not
committed.

---

## 0. Answer first

The brief asks: *what is the correct thing to write down when the joint distribution is unknown?*

**The bound is Fréchet–Hoeffding, it is sharp, it is 91 years old, and for this repository writing
it down is the wrong move.** With a cheap oracle you measure the composite directly and never need
a bound — which is what ADR-0012 already decided. The bound earns its place only where the
composite *cannot* be measured, and § 2 says exactly where that is.

Three results that were worth the derivation:

| | value |
|---|---|
| Sharp bound on composite β from **marginals only** | **[0.042465, 0.384775]** — width 0.342310 `[algebra]` |
| Sharp bound **adding the one measured 2×2 table** | **[0.297773, 0.338167]** — width 0.040394 `[algebra]` |
| Measured composite | 0.334542 — at **91.03%** of the tightened width `[measured]` |
| 3-check product estimator | 0.257755 — **outside** the tightened bound by 0.040018 `[algebra]` |

1. **The product estimator is not merely wrong here, it is infeasible.** No joint distribution
   consistent with the three measured marginals *and* the measured `pytest` × `mypy` table can
   produce 0.257755. Independence is refutable from one 2×2 table alone, without ever measuring
   the composite.
2. **One pairwise table collapses the bound width by 88.2%,** and turns ADR-0002's gate from
   *undecidable* into *decided*. On marginals alone the bound straddles β\* = 0.1118654 and the
   honest verdict is "insufficient data"; with the table the whole bound sits above it.
3. **The mathematics is not ours and neither is the software result.** The bound is Fréchet (1935),
   the method I used is Hailperin (1965), the tightening from pairwise information is Kwerel (1975),
   and *"independently built checkers do not fail independently, and the excess is a covariance"* is
   Eckhardt & Lee (1985) with Knight & Leveson (1986) as the experiment. § 10 grades what is left.

---

## 1. Provenance of every input

Re-read from `experiments/exp47/results-exp47.json`, not from the findings prose. `[measured]`

| quantity | count | rate | Wilson 95% |
|---|---|---|---|
| mutants, $n$ | 1,931 | — | — |
| `pytest` accepts | 743 | 0.384775 | [0.363323, 0.406684] |
| `mypy` accepts | 1,348 | 0.698084 | [0.677230, 0.718151] |
| `ruff` accepts | 1,853 | 0.959606 | [0.949874, 0.967514] |
| all three accept (composite) | 646 | 0.334542 | [0.313843, 0.355897] |
| `pytest` ∧ `mypy` accept | 653 | 0.338167 | — |

The 2×2 table's margins reproduce the univariate counts exactly (743, 1,348, 1,931), and each
stored point estimate matches the count ratio to machine precision. $\chi^2 = 187.27862$ recomputes
identically; $p = 1.248 \times 10^{-42}$ (df 1), odds ratio 5.1467 with 95% CI [4.0132, 6.6004],
$\phi = 0.31142$.

**Two arithmetic notes before anything is built on these numbers.**

**(a) The published comparison mismatches its arity.** `findings-exp47.md` § 3 and the brief both
set "the product estimator 0.2686" against "the measured composite 0.3345". But 0.2686 is
$\beta_{\text{pytest}} \times \beta_{\text{mypy}}$ — two checks — and 0.3345 is the *three*-check
composite. Like for like: `[algebra]`

| comparison | product | measured | understated by |
|---|---|---|---|
| 2 checks | 0.268605 | 0.338167 | 0.069562 |
| 3 checks | 0.257755 | 0.334542 | **0.076787** |

The error runs in the safe direction — the correct three-check gap is *larger* — so the conclusion
strengthens rather than weakens. It should still be fixed, because the mismatch is the kind that
usually runs the other way.

**(b) All bound arithmetic below uses raw counts.** EXP-47's equivalence correction (60 mutants)
was applied to the composite only, and only among composite survivors; the three marginals are
uncorrected, and mutants killed by some check were never assessed for equivalence. So
$\beta_{\text{corr}} = 0.3132$ has no marginals to be bounded against, and comparing it to bounds
built from raw marginals would be comparing two different populations. It happens to fall inside
the tightened bound; that is not a validation and is not used as one.

---

## 2. The framing correction, stated before the derivation

The brief invites me to say first if the framing is wrong. It is half wrong, in a way that matters.

**Bounding the composite is the wrong instrument for the case that produced the question.** EXP-47
measures every mutant against every check at 0.0539 s per mutant. Anyone who can compute the three
marginals has, by construction, already computed the composite — it is the same pass over the same
data. Deriving a bound and then reporting it, when the quantity itself is sitting in the same
result set, would be replacing a measurement with an inequality. ADR-0012 decided this in the right
direction on 19 August: *measure the composite directly, keep per-check β as diagnostics, never
compose them analytically.* Nothing here disturbs that, and § 9 records where ADR-0012's reasoning
is nonetheless wrong.

**The bound is decision-relevant in three cases, none of them this one.** `[asserted]`

1. **Composing β measured on different corpora.** Per-check rates published by different projects,
   or measured at different times on different defect populations, have no joint distribution to
   measure. The bound is then the only honest statement.
2. **Predicting the effect of adding a check before running it.** § 7 shows the answer is sharp and
   cheap: the most a check can buy is its own kill rate.
3. **Consuming someone else's numbers.** A repository that publishes per-check β and a threshold
   invites a reader to multiply. The bound is what stops them, and § 8 quantifies what happens if
   they do not.

The honest one-line answer to the brief's question is therefore: **when the joint distribution is
unknown *and unobtainable*, write down the sharp bound and evaluate decisions at its conservative
end. When it is merely unknown, go and measure it.**

---

## 3. The derivation

Let $A_1, \dots, A_k$ be the events "check $i$ accepts", all conditioned throughout on the artefact
being bad, and write $\beta_i = P(A_i)$. The quantity wanted is
$\beta_{\text{comp}} = P(\bigcap_i A_i)$.

**Not identified.** The marginals fix $k$ numbers; the joint distribution over $\{0,1\}^k$ has
$2^k - 1$ free parameters. For $k = 3$ that is 3 constraints against 7 unknowns, so
$\beta_{\text{comp}}$ is a set, not a number. `[algebra]`

**Upper bound.** $\bigcap_i A_i \subseteq A_j$ for every $j$, so by monotonicity
$P(\bigcap_i A_i) \le \min_i \beta_i$.

**Lower bound.** By complementation and the union bound (Boole's inequality),

$$P\Big(\bigcap_i A_i\Big) = 1 - P\Big(\bigcup_i \bar{A_i}\Big) \ge 1 - \sum_i (1 - \beta_i) = \sum_i \beta_i - (k-1),$$

and probabilities are non-negative, giving
$P(\bigcap_i A_i) \ge \max\big(0, \sum_i \beta_i - (k-1)\big)$. Together:

$$\max\Big(0, \textstyle\sum_i \beta_i - (k-1)\Big) \;\le\; P\Big(\bigcap_i A_i\Big) \;\le\; \min_i \beta_i .$$

**Assumptions.** Only that the $\beta_i$ are marginal probabilities of events on a common
probability space. No independence, no exchangeability, no distributional form, and nothing about
the defect population beyond its being the population the $\beta_i$ were measured on. That last
clause is not a technicality — see § 6.

**Sharpness, and why copulas are the wrong frame here.** The general Fréchet–Hoeffding lower bound
$W_d(u) = \max(0, \sum u_i - (d-1))$ is famously *not* a copula for $d \ge 3$, which invites a
worry about attainability. The worry does not arise for this problem, because the events are
**binary** and the question is pointwise. For binary events the whole problem is a linear programme
over the $2^k$ joint cell probabilities — non-negativity, total mass one, and one equality per
known margin — and the optimum of a bounded LP in standard form is attained at a basic feasible
solution. **That LP is Hailperin's (1965) formulation of Boole's problem, and his Theorem 3.1 is
exactly the statement that the resulting bounds are best possible and computable by linear
programming.** `[cited]` I did not need to import the copula machinery and have not.

Both endpoints are attained here by explicit construction, which is more reviewable than a solver
result: `[algebra]`

- **Upper**, 743 of 1,931: nest the acceptance sets, $A_{\text{pytest}} \subset A_{\text{mypy}}
  \subset A_{\text{ruff}}$. Feasible because $743 \le 1{,}348 \le 1{,}853$.
- **Lower**, 82 of 1,931: make the three *rejection* sets pairwise disjoint. They contain
  $1{,}188 + 583 + 78 = 1{,}849$ mutants, which fits inside 1,931, leaving
  $1{,}931 - 1{,}849 = 82$ accepted by all three. The clamp at zero is precisely the case where the
  kill counts overrun $n$.

---

## 4. Checked against the measured numbers

Marginals only, $k = 3$: `[algebra]` over `[measured]` inputs

$$\max(0,\, 0.384775 + 0.698084 + 0.959606 - 2) = 0.042465 \;\le\; \beta_{\text{comp}} \;\le\; 0.384775$$

- Closed form and exact-rational LP agree on both endpoints: [82, 743] of 1,931.
- Measured 0.334542 lies inside, at **85.33%** of the width — near the upper, most pessimistic end.
- The 3-check product 0.257755 also lies inside, so **marginals alone cannot refute independence.**
- Width 0.342310 spans a factor of 9.06. Useless for gating on its own, exactly as the brief
  anticipated.

---

## 5. Adding the one measured pairwise margin

Add the constraint $P(A_{\text{pytest}} \cap A_{\text{mypy}}) = 653/1931$ to the LP. Exact rational
vertex enumeration returns **[575, 653] of 1,931 = [0.297773, 0.338167]**, and an independent
float solver (SciPy HiGHS) agrees to $< 10^{-9}$. `[algebra]`

The endpoints have closed forms worth stating, because they generalise. For a subset $S$ of checks
whose **joint** acceptance rate $\beta_S$ is known and the rest known only marginally:

$$\max\Big(0,\; \beta_S - \sum_{i \notin S}(1-\beta_i)\Big) \;\le\; P\Big(\bigcap_i A_i\Big) \;\le\; \min\Big(\beta_S,\; \min_{i \notin S} \beta_i\Big)$$

The lower bound is the same union-bound step as § 3, applied inside $\bigcap_S$. Two consequences:

- **The Fréchet lower bound is this formula with $S$ a singleton** — $\beta_j - \sum_{i \ne j}(1-\beta_i)$
  is $\sum_i \beta_i - (k-1)$ rearranged. One family, not two. `[algebra]`
- **The width of the bound is at most $\sum_{i \notin S}(1-\beta_i)$: the total kill rate of the
  checks left out.** Here $S = \{\texttt{pytest}, \texttt{mypy}\}$ and the omitted check is `ruff`,
  whose kill rate is $78/1931 = 0.040394$ — which is the observed width, exactly. `[algebra]`

Results:

| | marginals only | + one 2×2 table |
|---|---|---|
| bound | [0.042465, 0.384775] | [0.297773, 0.338167] |
| width | 0.342310 (661 mutants) | 0.040394 (78 mutants) |
| measured 0.334542 sits at | 85.33% | **91.03%** |
| contains the product 0.257755? | yes | **no** |

**The infeasibility result is the useful one.** The product estimator falls 0.040018 *below* the
sharp lower bound. There is no joint distribution over three checks consistent with the measured
marginals and the measured `pytest` × `mypy` table that yields 0.257755. So a project need not
measure its composite to know that multiplying is wrong — **one 2×2 contingency table is
sufficient to prove the independence-composed figure impossible.** `[algebra]`

I checked that this machinery can fail, on inputs it should reject: `[measured]`

| input | expected | observed |
|---|---|---|
| pairwise count 744 > $\min$(marginal) 743 | infeasible | infeasible |
| three checks at β = 0.25 each (kills overrun $n$) | lower bound clamps to 0 | 0.000000 |
| asserted composite = 497, the product's implied count | infeasible | infeasible |
| asserted composite = 646, the measured count | feasible | feasible |

The third and fourth rows are the pair that matters: the same guard rejects the independence figure
and accepts the truth.

---

## 6. Why the truth sits near the top, and whose result that is

The excess of the joint over the product is a covariance, identically:
$\operatorname{Cov}(\mathbb{1}_{A_1}, \mathbb{1}_{A_2}) = P(A_1 \cap A_2) - \beta_1\beta_2$. For
`pytest` × `mypy` that is $0.338167 - 0.268605 = 0.069562$ — **the product estimator's error and the
covariance are the same number.** `[algebra]`

There is a mechanism, and it is not ours. Eckhardt & Lee (1985) formalised a *difficulty function*
$\theta(x)$: the probability that a version fails on input $x$. Conditioning on $x$ may make two
versions independent, but the marginal joint failure rate is
$E_x[\theta_A(x)\theta_B(x)] = E[\theta_A]E[\theta_B] + \operatorname{Cov}(\theta_A, \theta_B)$, so
**conditional independence does not give unconditional independence**, and the system is less
reliable than the product whenever the difficulty functions are positively correlated. Littlewood &
Miller (1989) generalised it and showed that *forced* methodological diversity can in principle
make the covariance negative — better than independent — while noting such a claim is hard to
justify. `[cited]`

Transposed to verifiers rather than versions: mutants vary in detectability, and a subtle mutant is
subtle for `pytest` and for `mypy` at once. The mechanism therefore **predicts the sign** —
positive dependence is the generic case, and independence is a knife-edge, not a default.

**It does not predict the magnitude, and 91% of the bound width is a magnitude claim.** The
mechanism is consistent with a covariance of 0.0696 and equally consistent with 0.0069. Nothing in
this document establishes that verifiers sit near comonotone generally.

**Does it generalise?** `[asserted]` My confidence, stated on its basis:

- **That the product understates composite β for real check stacks: high.** Two independent
  grounds — the covariance mechanism above, which is general, and a 40-year-old experimental
  literature that found the same thing for redundant program versions. This repository's own
  measurement is the third, and it is the weakest of the three because it is $n = 1$.
- **That the composite lands near the sharp upper bound: low, and it is a hypothesis, not a
  finding.** One source tree, ~1,100 lines, three checks, one defect generator, an unusually
  invariant-heavy suite. `ruff` is nearly a constant function on this corpus — it accepts 95.96% of
  mutants — and a near-constant check is close to comonotone with anything by construction. That
  alone could produce most of the 91% without saying anything about verifiers in general.

The regularity is worth registering as a claim rather than asserting as a result, which is what
§ 13 does.

---

## 7. What a check is worth, and the duality

`ruff` is the whole marginal-value experiment, already run. `[measured]` / `[algebra]`

| | value |
|---|---|
| composite before adding `ruff` (`pytest` ∧ `mypy`) | 0.338167 |
| composite after | 0.334542 |
| reduction delivered | 0.003625 — **7 mutants** |
| reduction independence predicts ($\times \beta_{\text{ruff}}$) | 0.013660 |
| fraction of the predicted benefit delivered | **26.5%** |
| the most any check with this β could deliver, $1-\beta_{\text{ruff}}$ | 0.040394 |
| fraction of its own ceiling delivered | **9.0%** |

Of the 653 mutants that survived both `pytest` and `mypy`, `ruff` killed seven.

This gives the memorable form of § 5's width result: **the most a check can improve the composite is
exactly the most it can surprise you** — both equal its kill rate $1 - \beta_i$. A weak check
contributes little benefit *and* little uncertainty; a strong one contributes both. So the
uncertainty a project carries by not measuring a joint distribution is bounded by the very thing it
was hoping the extra checks would buy. `[algebra]`

**On modelling rather than bounding.** The brief asks whether the dependence should be modelled. The
natural model is Eckhardt & Lee's: a latent difficulty factor with the checks conditionally
independent given it. It **cannot be tested on three checks.** A two-class latent model over $k$
binary items has $1 + 2k$ parameters against $2^k - 1$ degrees of freedom in the data: at $k = 3$
that is 7 against 7, leaving **zero** degrees of freedom for a goodness-of-fit test. At $k = 4$ it
is 9 against 15, leaving 6. `[algebra]` So *"model it"* is not available at present and becomes
available on adding a fourth check — a concrete, cheap prerequisite rather than a preference, and
the reason EXP-58 is registered with $k \ge 4$.

---

## 8. What this changes for the gate

ADR-0002 gates routing on β against $\beta^* = (1-\alpha)e^{-k\Delta}$, which recomputes to
**0.1118654** at the ADR's own $\alpha = 0.03$, $k = 8$, $\Delta = 0.27$, and its operational rule
is conservative: declare safe only if the **upper** 95% bound clears $\beta^*$.

**For this repository the dependence question changes nothing, and that should be said plainly.**
The measured composite's Wilson upper limit is 0.355897 — **3.18× $\beta^*$**. Routing fails the
gate by a factor of three, and would fail it under any dependence assumption whatever. `[measured]`

**Where it changes everything is when the composite is not measured.** `[algebra]`

| available evidence | bound on composite | verdict against β\* = 0.1118654 |
|---|---|---|
| three marginals | [0.042465, 0.384775] | **undecidable** — straddles β\*; ADR-0002 requires "insufficient data" |
| + one 2×2 table | [0.297773, 0.338167] | **unsafe**, at 2.66× β\* even at the optimistic end |
| composite measured | 0.334542 [0.313843, 0.355897] | unsafe, 3.18× β\* conservatively |

So a single contingency table converts an undecidable gate into a decided one, without measuring
the composite. And carrying the sampling error through the bound rather than the point estimate:
the upper bound is $\min_i \beta_i$, whose conservative value is `pytest`'s Wilson upper limit
0.406684 — a marginals-only ceiling of 3.64× β\*.

**The false-safe construction, which is the reason any of this matters.** Suppose $k$ equal-β checks
and a project that multiplies. The product clears β\* at per-check β = $\sqrt[k]{\beta^*}$, while
the sharp upper bound is β itself: `[algebra]`

| $k$ | per-check β at which the product exactly equals β\* | truth if nested | multiple of β\* |
|---|---|---|---|
| 2 | 0.3345 | 0.3345 | **2.99×** |
| 3 | 0.4818 | 0.4818 | **4.31×** |
| 4 | 0.5783 | 0.5783 | **5.17×** |

At $k = 3$, applying not perfect nesting but the 91% bound position measured here gives 0.4386, or
**3.92× β\***. A project stacking three checks each accepting roughly half of all bad artefacts
would compute a composite of 0.1119, declare routing safe with margin, and be wrong by a factor of
four in the dangerous direction. This is the concrete form of ADR-0012's warning, and it is a
larger number than that warning implies.

**Consequence for the records, stated as a recommendation and not enforced.** Any β compared against
β\* should be the conservative end of whatever is known: the Wilson upper limit when the composite
is measured, and the sharp upper bound when it is not. `consil doctor` reports
`routing_orchestration_enabled: false` today for reasons that have nothing to do with this, so
nothing about the flag changes. I am deliberately **not** declaring this a repository invariant,
because this brief permits me to write two files and an invariant declared without its check is the
failure mode `brief-common.md` names. The check, when written, belongs beside the composite
computation in `src/consilient/beta.py`, and is one comparison: reject any composite figure that
falls outside the sharp bound implied by the recorded per-check margins.

---

## 9. Corrections owed to existing records

**(a) ADR-0012's lower-bound claim is mis-tagged and false as stated.** The ADR's evidence section
reads, tagged `[algebra]`:

> **Independence is certainly false.** […] So the product is a **lower bound** on the true
> composite, and using it would systematically overstate how safe routing is.

The *decision* ADR-0012 reaches is right and this document supports it. The *reasoning* is not
algebra. The product is a lower bound only under positive dependence, which is an empirical premise
about the world, not a consequence of stated ones. Counterexample: two checks with
$\beta_1 = \beta_2 = 0.5$ and perfect negative dependence — each accepts exactly what the other
rejects — give $P(\text{both accept}) = 0$ against a product of 0.25, so the product
**overestimates**. That is the Fréchet lower bound at work, and Littlewood & Miller (1989) show
negative dependence is theoretically reachable through forced diversity. `[algebra]` / `[cited]`

The honest tags: *"independence is false for this repository's three checks"* is `[measured]` since
EXP-47; *"positive dependence is the generic case"* is `[cited]` to Eckhardt & Lee via the
covariance mechanism; *"the product is a lower bound"* is `[asserted]` and universally false. The
distribution-free statement is the bound. ADR-0012's 20 August update is careful about this; the
original evidence line is not, and it is the line a reader will quote.

**(b) EXP-47 computed the full joint distribution and discarded it.** `run_exp47.py` records
`pytest_pass`, `mypy_pass` and `ruff_pass` per mutant, then `compute_statistics` aggregates to
per-check totals plus a single `pytest` × `mypy` table. The other two pairwise tables and the
three-way table were in memory and are not in the result file. Given everything that *was* saved,
they are only partially identified: `[algebra]`

| unrecorded margin | feasible range | width |
|---|---|---|
| `pytest` ∧ `ruff` | [665, 736] of 1,931 = [0.344381, 0.381150] | 71 mutants |
| `mypy` ∧ `ruff` | [1,270, 1,341] of 1,931 = [0.657690, 0.694459] | 71 mutants |

This is the provenance rule in `brief-common.md` costing something real: a conclusion's evidence was
computed and thrown away, and recovering it costs a 104-second re-run rather than a new experiment.
The fix is one dictionary per mutant instead of four counters — record the full outcome vector, not
per-check totals. It is registered as EXP-58 rather than applied, because applying it means editing
`run_exp47.py` and its result file, which this brief does not authorise.

---

## 10. Novelty: is this a contribution?

The brief asks me to say honestly whether this is a general result about composing software
verifiers or textbook applied statistics that happens not to be applied here. **It is the second,
and the honest answer is more useful than a strained claim to the first.** `[asserted]`

**The mathematics is between 51 and 91 years old, and I used the canonical method without knowing
it.** `[cited]`

| what I did | whose it is |
|---|---|
| the bound $\max(0,\sum\beta_i-(k-1)) \le P(\bigcap) \le \min\beta_i$, and its sharpness | Fréchet (1935); the pairwise case appears in Boole (1854) |
| LP over the $2^k$ joint cells, marginals as equality constraints, max/min the target cell | **Hailperin (1965)** — his Theorem 3.1 states the bounds are best possible and LP-computable |
| tightening the bound on the **intersection** using pairwise information | **Kwerel (1975)**, twice: bounds on $P_{[m]}$ from $S_1, S_2, S_3$, and the generalisation to $S_1 \dots S_k$ |
| noticing the general problem is hard | the union bounding problem; NP-hardness pointers via probabilistic satisfiability, and still an active area in 2023 |

At $k = 3$ the LP is eight variables and solvable by hand; there is no computational contribution
either.

**The software-engineering result is 40 years old and this repository's bibliography did not
contain it.** Eckhardt & Lee (1985) proved that identically-processed independent versions cannot be
expected to fail independently; Knight & Leveson (1986) tested the axiom on 27 versions under a
million tests and found coincident failures substantially in excess of the independent prediction;
Littlewood & Miller (1989) generalised the model. Substituting "verifier" for "version" changes the
application, not the mathematics. ADR-0002's 20 August update already concedes that the novelty
search was run in the one field that could not contain the answer — software engineering and
statistics were not searched. **This is a second instance of that same gap, found the same way.**

**What survives, graded honestly:** `[asserted]`

1. **The measurement.** Sharp bounds and a covariance for a modern static-plus-dynamic verifier
   stack (`pytest`, `mypy`, `ruff`) against a mutation-generated defect population. New numbers,
   old instrument, one repository. **Modest and real.**
2. **The infeasibility guard as an artefact.** "Measure one 2×2 table and prove your
   independence-composed β impossible" is a two-line CI check with, as far as I searched, no
   equivalent in a build tool. It is an application of Hailperin, not a result. **Engineering, not
   science** — and worth shipping precisely because it is cheap.
3. **The near-comonotone observation.** If composites land near the sharp upper bound across
   repositories, *"use the upper bound, it is nearly right"* would be a genuinely useful empirical
   regularity for CI design. At $n = 1$, with a near-constant third check, it is a **hypothesis**.

**What I searched, so that absence is not claimed from a partial search.** Targeted searches for the
Fréchet–Hoeffding bounds and their sharpness; Boole's problem and Hailperin's LP formulation;
Bonferroni-type and degree-2 bounds on intersections (Kwerel, Sobel & Uppuluri, Dawson & Sankoff,
Galambos, Prékopa); Fréchet bounds with known bivariate margins; and the N-version
programming/coincident-failure literature. **I did not search** for prior work applying any of this
to mutation testing specifically, to LLM-judge or verifier-ensemble correlation, or to CI gate
design; nor for whether any build tool already implements a feasibility check. Claim 2's "no
equivalent" is therefore weakly evidenced and should not be repeated without that search.

---

## 11. Sources, at the read-depth I actually reached

Per `.agents/skills/citing-sources/SKILL.md`: `[FULL]` fetched and read, `[ABS]` abstract or
listing read directly, `[SNIP]` search-result snippet only, `[2ND]` known via a secondary source.
**`[SNIP]` and `[2ND]` may not carry a load and are listed as pointers only.**

| source | identifier | status | what I read |
|---|---|---|---|
| Hailperin, *Best Possible Inequalities for the Probability of a Logical Function of Events*, Amer. Math. Monthly 72(4):343–359, 1965 | doi:10.1080/00029890.1965.11970533 | `[ABS]` + `[FULL]` on the restatement | Listing/abstract direct. **Theorem 3.1 and the LP construction read in full** in a later Hailperin exposition (*Probability Logic*, fetched as PDF; venue not confirmed), and independently restated in the 2023 paper below. Two independent restatements of the same theorem. |
| Boros et al., *Boole's Probability Bounding Problem, Linear Programming Aggregations…*, Math. of OR, 2023 | doi:10.1287/moor.2023.0019 | `[FULL]` abstract + introduction | The union bounding problem, Hailperin's LP in the exact form I used, "turns out to be quite difficult", and the NP-hardness pointers. |
| Eckhardt & Lee, *A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors*, IEEE TSE SE-11(12):1511–1517, 1985 | doi:10.1109/tse.1985.231895 | `[ABS]` | Abstract direct: the intensity-of-coincident-errors function, and that the model differs from one assuming independent failures. |
| Knight & Leveson, *An Experimental Evaluation of the Assumption of Independence in Multiversion Programming*, IEEE TSE SE-12(1):96–109, 1986 | doi:10.1109/tse.1986.6312924 | `[ABS]` | Abstract direct: 27 versions, one million tests, multi-version failures "substantially more than expected". The PDF I fetched was a course critique containing the abstract, **not the paper**; no figure from it is used. |
| Littlewood & Miller, *Conceptual Modeling of Coincident Failures in Multiversion Software*, IEEE TSE 15(12):1596–1614, 1989 | doi:10.1109/32.58771 | `[ABS]` | Abstract direct: forced diversity can yield better-than-independent behaviour. |
| The difficulty-function covariance identity | — | `[FULL]` on an extract | Read in an open-access City, University of London note deriving $E[\theta_A\theta_B] = E[\theta_A]E[\theta_B] + \operatorname{Cov}$ and stating that positive correlation makes the system less reliable than under independence. Attributed there to the Eckhardt–Lee and Littlewood–Miller models. |
| Kwerel, *Bounds on the probability of the union and intersection of m events*, Adv. Appl. Prob. 7:431–448, 1975 | doi:10.2307/1426084 | `[ABS]` | Abstract direct: most stringent bounds on $P_{[m]}$, the simultaneous occurrence, from $S_1, S_2, S_3$. This is the load-bearing prior-art claim in § 10 and the abstract states it. |
| Kwerel, *Most stringent bounds … partially specified by $s_1 \dots s_k$*, J. Appl. Prob. 12(3):612–619, 1975 | doi:10.2307/3212879 | `[ABS]` | Abstract direct: the generalisation to $k$ sums. |
| Fréchet, *Généralisation du théorème des probabilités totales*, Fundamenta Mathematicae 25:379–387, 1935 | doi:10.4064/fm-25-1-379-387 | `[2ND]` | **Not read.** Its content and the sharpness result are known here via Hailperin's and Wagner's descriptions. Pointer only. |
| Boole, *An Investigation of the Laws of Thought*, 1854 | — | `[2ND]` | **Not read.** Pointer only. |
| Sobel & Uppuluri 1972 (doi:10.1214/aoms/1177692387); Dawson & Sankoff 1967 (doi:10.1090/s0002-9939-1967-0211424-0); Galambos 1977; Prékopa 1988; Kavvadias & Papadimitriou 1990 | as listed | `[SNIP]` | Reference lists only. Named as the closed-form degree-2 and LP-bound literature a proper treatment must engage; **no claim here rests on them.** |

**Owed and not done.** These belong in `docs/10-research/bibliography.md` with the flags above; that
file currently contains **zero** entries for any of them. This brief authorises two files and the
bibliography is not one, so the promotion is outstanding. Until it happens, § 10's `[cited]` lines
rest on the read-depths in this table and nowhere else.

---

## 12. Limits, and what I did not check

`[asserted]` unless marked.

1. **β is conditional on a defect population, and mine is mutants.** Every bound here is a statement
   about the (verifier stack, defect distribution) pair, not about the stack. Transporting it to
   LLM-emitted faults is not licensed by anything in this document; EXP-47 § 7's
   competence-difficulty gap and EXP-50 own that question.
2. **$n = 1$ repository, $k = 3$ checks, one generator.** § 6 grades the generalisation claims.
3. **`ruff` is nearly a constant function on this corpus** (accepts 95.96%). A near-constant check is
   nearly comonotone with anything, which may account for much of the 91% bound position. This is
   the strongest objection to the near-comonotone hypothesis and I have not controlled for it.
4. **Equivalence correction is asymmetric** (§ 1b) and no corrected bound is computable from the
   saved data.
5. **I did not re-run EXP-47.** Its counts are taken as given, verified only for internal
   consistency. The three-way table remains unmeasured, and the ranges in § 9b are what a re-run
   would replace with numbers.
6. **No sampling theory for the bounds themselves.** § 8 propagates uncertainty by plugging Wilson
   limits into the endpoints, which is a conservative device, not a joint confidence region. A
   proper simultaneous interval over a partially identified set is a real statistical problem and I
   have not solved it.
7. **The false-safe table in § 8 is a construction, not an observation.** It shows what the product
   estimator *can* do at a gate, using ADR-0002's own β\*. No repository was measured at those
   values.
8. **Not searched:** § 10 lists it explicitly.

**Reversal path.** This commit adds one research document and one register entry, and changes no
code, no ADR and no gate. To undo it entirely: `git revert <commit-sha>`. To undo only the register
entry, delete the `### EXP-58` block. Nothing else in the tree references either.

**The option not taken.** I considered re-running EXP-47 with full outcome capture, which would have
replaced § 9b's ranges with measured numbers and made the near-comonotone claim testable at $k \ge 4$.
I did not, because it writes `results-exp47.json` and `run_exp47.py`, and the brief names the two
files I may write. Registering EXP-58 preserves the work at the cost of a delay; the alternative
was to exceed the brief.

---

## 13. Falsifiers

Stated as observations that would show this document wrong, not as caveats.

1. **On the near-comonotone hypothesis.** Measure the full $2^k$ table on a second repository with
   at least four checks, at least one of which kills more than 20% of mutants. If the composite's
   position within the sharp bound falls below 50% of the width, *"verifiers sit near the upper
   bound"* is refuted and the § 8 recommendation to gate at the conservative end becomes needlessly
   pessimistic rather than merely safe. **This is the cheap test and EXP-58 pre-registers it.**
2. **On the infeasibility guard's usefulness.** If, across repositories, the independence product
   almost always falls *inside* the bound implied by marginals plus one pairwise table, then the
   guard fires rarely and is not worth shipping. It fired here with a margin of 0.040018; one
   instance is not a rate.
3. **On the mechanism.** If a check stack is found with a reliably *negative* covariance — the
   forced-diversity case Littlewood & Miller allow — then "positive dependence is the generic case"
   is wrong, and the product would overstate β rather than understate it. This would matter most
   for deliberately decorrelated verifiers, which is ADR-0002's ρ lever in verifier form and
   CONSILIENCE.md's *different class* clause applied to checks rather than agents.
4. **On the framing.** If a case arises in this project where per-check β is available and the
   composite is genuinely unobtainable, § 2's claim that bounding is the wrong instrument here is
   wrong in that case, and the bound becomes the primary reporting form rather than a guard.

---

## 14. Traceability to CONSILIENCE.md

The bound is not a new structure and adds no surface; it is a constraint on how an existing number
may be reported. It serves the founding sentence in the third clause specifically: **consilience is
a test, and tests have error rates.** The composite β *is* that error rate for a stack of checks,
and this document establishes that the arithmetic almost everyone uses to compose it — multiply the
parts — is not merely approximate but provably infeasible against the repository's own measured
data. Clause two appears in § 13's third falsifier: two checks blind to the same class of defect are
echo, and their agreement buys 26.5% of what independence promises.
