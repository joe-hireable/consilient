# 0077. Separate candidate-exposure unions from verifier-fusion intersections and measure both

- **Status:** PROVISIONAL — EXP-81 can falsify iid sizing on its frozen panels but cannot weaken the
  robust policy; EXP-80 can kill the squad-specific fusion mechanism
- **Date:** 2026-08-22
- **Deciders:** Codex dispatch `20260822T123354-4a727c9b2a` for the provisional mechanism. The
  principal's Machine correction is product input, not authorship of this decision.
- **Inquiry tier reached:** T2 algebra; T3 pre-registered as EXP-81, not run
- **Executable model:** none — the probability bounds are exact; the missing quantities are joint
  outcome distributions that must be measured, and an assumed executable model would conceal that

## Context

The incoming brief states that correlated verifiers may make a joint false-accept rate nearer
`beta` than `beta^n`, then concludes that the candidate ceiling
`1 - (1 - beta)^n` may be dangerously oversized. The premise concerns an intersection of verifier
passes on one artefact; the conclusion concerns a union of shippable candidate attempts. They are
different probability objects and the inference between them is invalid. [algebra]

ADR-0067 already distinguishes evidence-role count from candidate exposure, but its surrounding
records do not do so consistently. ADR-0051 says positive candidate correlation makes the iid union
an upper bound; that is exact for two equal-marginal attempts but is not established by pairwise
positive correlation for three or more. Both ADRs also say the measured result is `n_max = 1` for
every `epsilon <= 0.40`; the correct statement is `n_max <= 1`, because a ceiling below
`beta_upper` admits zero attempts. [algebra]

The current routing implementation already permits zero, consumes a measured composite beta and
does not multiply per-check rates. The defect is therefore in the governing explanation and in what
future measurements it requests, not in today's one-attempt result. [measured]

This ADR amends only ADR-0051 decision 5 and ADR-0067's “Composition and beta” clause. Every other
decision in those provisional ADRs stands. It extends ADR-0067's one-Owner composition rule; it does
not silently reinterpret or supersede it. [asserted]

## Decision

Consilient will keep three quantities separate. [asserted]

1. **Candidate exposure.** For candidate `i`, define `F_i` as “the candidate is bad and the frozen
   composite verifier accepts it”. The risk ceiling applies to
   `P(union_i F_i)`. Automatic exposure uses the dependence-robust ceiling
   `floor(epsilon / q_upper)`. Eventwise `q <= beta`; when `q` is unmeasured, policy sets
   `q_upper := beta_upper` as the conservative worst-case substitution. Measurement does not relax
   this without a separate coverage-valid pre-registration and ADR. [algebra] [asserted]
2. **Composite verification.** For one known-bad artefact, the composite beta is the intersection of
   component-verifier acceptances. It is measured directly on full same-artefact outcome vectors.
   Component marginals and correlations remain diagnostics and are never multiplied into an
   acceptance input. [algebra] [asserted]
3. **Evidence fusion.** One Owner combines independently acquired readings by calibrated likelihood
   ratios and measured joint outcome tables, not votes or self-reported confidence. Unknown
   dependence is not multiplied away. Quantitative convergence means the chosen action survives the
   full prior, calibration and dependence uncertainty set at the pre-committed loss/risk ceiling.
   [algebra] [asserted]

The exact candidate-attempt expression is: [algebra]

$$
P\left(\bigcup_{i=1}^{n}F_i\right)
=1-\prod_{i=1}^{n}\left(1-P(F_i\mid F_1^c,\ldots,F_{i-1}^c)\right).
$$

The iid formula and its inversion are retained as diagnostics for a frozen non-adaptive population,
not as the automatic ceiling. Any future exception is limited to the range directly supported by a
separately powered, coverage-valid experiment. [algebra]

$$
R_n^{iid}=1-(1-q)^n,
\qquad
n_{attempt}^{iid}=\left\lfloor
\frac{\log(1-\epsilon)}{\log(1-q_{upper})}
\right\rfloor.
$$

For arbitrary dependence with every marginal bounded by `q_upper`: [algebra]

$$
P\left(\bigcup_i F_i\right)\le nq_{upper},
\qquad
n_{attempt}^{robust}=\left\lfloor\frac{\epsilon}{q_{upper}}\right\rfloor.
$$

For two verifier false-accept events on one known-bad artefact: [algebra]

$$
P(V_1\cap V_2)=\beta_1\beta_2+
\rho_{12}\sqrt{\beta_1(1-\beta_1)\beta_2(1-\beta_2)}.
$$

Positive correlation is dangerous in this intersection and can make the independence product false
safe. For more than two verifiers, pairwise correlations do not identify the joint; measure the
composite directly, as ADR-0012 already requires. [algebra]

At EXP-47's recorded corrected `beta_upper = 0.334582` and `epsilon = 0.40`, both candidate ceilings
equal one. For `epsilon < beta_upper`, both equal zero. The current one-candidate policy therefore
survives arbitrary candidate dependence, conditional on the recorded beta transferring to the
candidate population. [measured] [algebra]

The operational protocol and record contract are specified in
`../superpowers/specs/2026-08-22-evidence-fusion.md`. This change adds a validated
`verification.outcome` event through the existing `events.append()` writer and reuses the existing
dispatch, coordination, recall, work-item, routing, budget and instruction boundaries. [measured]

## Evidence

- `[measured]` The committed EXP-47 result records corrected composite beta `0.3132015` with 95%
  interval `[0.2925865, 0.3345820]`; direct arithmetic gives one attempt at `epsilon = 0.40` under
  both iid and union-bound ceilings.
- `[measured]` The live `consil beta` path reports insufficient data: one human rejection against a
  minimum 30. It refuses routing and does not treat mutation beta as a human-labelled estimate.
- `[measured]` EXP-47 records dependent `pytest` and `mypy` outcomes on the same mutants and a joint
  acceptance above their independence product. The repository already consumes measured composite
  beta rather than the product.
- `[measured]` `events.py` is the single append-only writer and the generic projection preserves the
  canonical payload of every validated event. `attempt.outcome` is unique per attempt, so repeating
  it per verifier would corrupt the beta denominator rather than create a correlation record.
- `[algebra]` The union bound gives `P(union_i F_i) <= sum_i q_i` without an independence
  assumption. The Fréchet bounds give
  `max(0, sum_j beta_j-(m-1)) <= P(intersection_j V_j) <= min_j beta_j` for the verifier
  conjunction.
- `[algebra]` For two equal-marginal candidate attempts,
  `R_2 = 2q - q^2 - rho q(1-q)`. For `n >= 3`, pairwise correlations leave higher intersections
  unidentified, so pairwise positive correlation alone cannot license the iid ceiling.
- `[cited]` Ao, Gao and Simchi-Levi (2026), *On the Reliability Limits of LLM-Based Multi-Agent
  Planning*, arXiv:2603.26993, prove weak dominance of an ideal central Bayes decision-maker over a
  finite acyclic delegated network with the same exogenous signals. The theorem bounds information,
  not bounded-model performance under a computation budget.
- `[cited]` Kim et al. (2026), *Capable language models can outgrow the benefits of collaboration*,
  doi:10.1038/s42256-026-01268-y, find task-dependent gains and losses across 260 configurations;
  there is no universal team topology.
- `[cited]` Jwalapuram et al. (2026), *The Illusion of Multi-Agent Advantage*, arXiv:2606.13003,
  find generic multi-agent designs losing to a strong single-agent comparator while a deliberately
  separable specialist design wins on its synthetic task.
- `[asserted]` A calibrated likelihood protocol with explicit dependence blocks will preserve the
  value of genuinely different readings without laundering correlated agreement into confidence.
  EXP-80 and EXP-81 are the killing checks.

## Evidence against

- `[measured]` This repository's strongest direct organisational comparison favours the simple
  control: EXP-16's single-agent arm won 9 of 12 blind judgements while the Owner meeting won 2 of
  12 at 4.8 times the tokens and 3.7 times the wall time. A fusion protocol can rename the failed
  meeting while retaining its cost.
- `[cited]` Ao, Gao and Simchi-Levi give the strongest theoretical objection: when a capable Owner
  has the same sources, execution and tools, delegation adds no information. A different model
  family reading the same evidence is not an answer to that theorem.
- `[cited]` Kim et al. report multi-agent degradation on SWE-bench Verified, and Jwalapuram et al.
  report generic systems costing up to roughly ten times their strong comparator. The positive
  specialist result is synthetic and deliberately separable.
- `[asserted]` One capable Owner with retrieval, a real browser, execution and primary-source
  checking may already fuse more evidence classes than a squad does. Partitioning those tools can
  replace direct evidence with summaries, lose context and add coordination failure.
- `[asserted]` Likelihood calibration can create mathematical ceremony around sparse or shifted
  data. A precise posterior over the wrong task population is worse than an honestly asserted
  decision.

The objection is conceded unless evidence defeats it. One Owner remains the strongest baseline;
no reader is added without a new truth-relevant anchor; uncalibrated agreement has zero numeric
weight; and EXP-80 must show a same-budget gain after the new-anchor contribution is ablated.
Otherwise the squad-specific fusion mechanism is removed while the one-owner record survives.
[asserted]

## Consequences

**Positive** — the current one-attempt policy remains intact for the right reason; correlated
component verifiers can no longer be confused with correlated candidate attempts; and future
ceilings have an assumption-free fallback. [algebra] [asserted]

**Negative** — a dependence-robust ceiling may be tighter than the iid ceiling, and calibrated
joint tables require grouped bad artefacts, human verdicts and explicit non-completion records.
[asserted]

**Neutral but load-bearing** — beta conditions shippable candidate exposure, not evidence-role
headcount. ADR-0067's default one Owner and distinct-anchor test remain the composition rule.
Principal-only authority never becomes evidence weight. [asserted]

## Enforcement

This decision changes documentation, pre-registers EXP-81, adds the component-verification event
contract and makes the unwired routing helper dependence-robust. It changes no gate, CLI, projection
table or current operational one-candidate ceiling at `epsilon = 0.40`. [measured]

- Check: `verification.outcome` validates identifiers, artefact hash, verifier contract/version,
  evidence class, terminal status and the conditional Boolean before append; its invariant test
  reconstructs all four same-attempt contingency cells through append/replay and detects bypasses.
  The EXP-81 analyser must reject duplicate verification identities or
  `(protocol_id, attempt_id, verifier_id, verifier_version)` component keys before any
  estimate. Grouped candidate bad-shipment vectors remain a runner precondition. [measured] [asserted]
- Check: future routing tests distinguish zero from one attempt, use `n_attempt_max`, refuse an iid
  ceiling without a matching measured protocol, and prove the robust ceiling never exceeds
  `floor(epsilon / q_upper)`. [asserted]
- Check: future fusion tests prove that self-reported confidence and reader count never enter a
  weight, unknown dependence is not multiplied, every required refusal/quarantine/timeout remains
  visible, and only the Owner emits the candidate. [asserted]
- Fails CI: yes — `tests/test_v0_invariants.py` rejects incomplete or ambiguous component outcomes
  and proves paired outcomes survive the sole writer; `tests/test_coordination.py` proves the robust
  helper does not admit the iid second candidate at `epsilon = 0.60`. [measured]
- Added in the same commit as the implementation: planned for this decision commit. [asserted]

## What would overturn this

EXP-81 records `observed_false_safe` if the empirical candidate-union rate exceeds the iid prediction
for any `k` on its complete frozen panels. That bars an iid exception for the affected protocol. A
zero or negative difference is descriptive only: with 15 panels per stratum, percentile bootstrap
coverage fails at sparse boundaries and cannot establish safety. Every result therefore keeps the
robust ceiling; any future iid exception requires a separately powered, coverage-valid
pre-registration. Adaptive retry and proposed `n > 5` remain robust regardless. [algebra] [asserted]

EXP-80 kills squad-specific fusion if the smallest evidence-grounded squad fails to beat the
same-budget capable Owner on independent artefact and human verdicts, or if the gain disappears when
the added anchor is ablated. [asserted]

If `verification.outcome` cannot reconstruct both dependence axes from the append-only record, its
schema is incomplete and must be replaced before any correlation claim. [asserted]

## Publication candidate?

**No.** The union/intersection correction is elementary probability and the fusion mechanism is
unmeasured. A publication candidate would require EXP-81 outcome vectors and an EXP-80 result that
beats the single-owner control without hidden extra information or budget. [asserted]
