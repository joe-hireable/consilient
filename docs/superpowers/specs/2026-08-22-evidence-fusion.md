# Evidence fusion: independent readings, measured dependence, one decision

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** § 10 (EXP-81, EXP-80, and the echo/schema-incomplete cases named there).

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

**The dispatch brief is wrong about the dangerous direction: it conflates the union of several
candidate attempts with the intersection of several verifier passes.** Positive dependence can make
an independence product dangerously understate a composite verifier's false-accept rate; it does not
show that the current candidate-attempt ceiling is dangerously large. [algebra]

- **Date:** 2026-08-22
- **Status:** Specification. Decided provisionally by ADR-0077; EXP-81 can falsify an iid exception
  on its frozen panels but cannot weaken the dependence-robust policy. [asserted]
- **Author:** Codex dispatch `20260822T123354-4a727c9b2a`. The principal supplied the product
  correction quoted in the source document; the mechanism and algebra below are this dispatch's
  work and carry no claim on his authority. [measured]
- **Extends:** ADR-0067's one-owner, distinct-anchor composition rule. It does not replace the
  default of one Owner or turn evidence-role count into candidate count. [asserted]

## 1. Answer first: what survives

The present documented result survives, conditional on the mutation-derived bound transferring to
the candidate population: at the recorded EXP-47 corrected composite
`beta_upper = 0.334582` and exposure ceiling `epsilon = 0.40`, both the iid ceiling and the
dependence-robust ceiling admit one candidate. Dependence cannot change a one-attempt risk. The
committed EXP-47 result artefact is the measurement source. [measured] [algebra]

The live human-labelled meter does not authorise routing: `consil beta` reports one human rejection
against the minimum 30, so its result is `insufficient data`. The mutation result is not a substitute
human verdict, and the live path therefore refuses rather than assuming its value transfers.
[measured]

The iid formula does **not** survive as a general dependence-free sizing rule. Automatic exposure
uses the union-bound ceiling; measurement alone does not relax it. An iid exception would require a
separate coverage-valid pre-registration for the same generator, task stratum, verifier contract and
candidate range. [algebra] [asserted]

The existing prose also overstates the result as `n_max = 1` for every `epsilon <= 0.40`. The exact
statement is `n_max <= 1`: when `0 < epsilon < beta_upper`, zero attempts meet the ceiling; one is
admitted only when `epsilon >= beta_upper`. [algebra]

## 2. Two probabilities that must never share one symbol

Let `B_i` mean candidate `i` is bad and `A_i` mean the frozen composite verifier accepts it. Define
the bad-shipment event `F_i = B_i intersection A_i`. The risk from exposing `n` independently
shippable candidates is a **union**: [algebra]

$$
R_n = P\left(\bigcup_{i=1}^{n} F_i\right)
    = 1 - \prod_{i=1}^{n} (1-h_i),
\qquad
h_i = P(F_i \mid F_1^c,\ldots,F_{i-1}^c).
$$

Only when the `F_i` are iid with probability `q` does this reduce to: [algebra]

$$
R_n^{iid}=1-(1-q)^n,
\qquad
n_{attempt}^{iid}=\left\lfloor
\frac{\log(1-\epsilon)}{\log(1-q_{upper})}
\right\rfloor.
$$

The current rule substitutes composite `beta = P(A_i | B_i)` for `q = P(B_i intersection A_i)`.
That is conservative only because `q <= beta` treats every candidate as bad; it must be stated as a
worst-case substitution, not an identity about generated work. [algebra]

For exact marginal probabilities `q_i`, the sharp distribution-free bounds are: [algebra]

$$
\max_i q_i \le R_n \le \min\left(1,\sum_i q_i\right).
$$

For marginals bounded by `q_upper`, the dependence-robust policy ceiling is therefore: [algebra]

$$
n_{attempt}^{robust}=\left\lfloor\frac{\epsilon}{q_{upper}}\right\rfloor.
$$

For two equal-marginal attempt events with feasible Pearson correlation `rho`: [algebra]

$$
R_2=2q-q^2-\rho q(1-q).
$$

Positive correlation lowers this two-attempt union towards `q`; negative correlation raises it.
For three or more attempts, pairwise correlations do not identify the union because higher-order
intersections remain free. A pairwise-positive sample is therefore not authority to enlarge the
ceiling. [algebra]

Now take one known-bad artefact and let `V_j` mean verifier `j` accepts it. The composite
false-accept rate is an **intersection**: [algebra]

$$
\beta_{comp}=P\left(\bigcap_{j=1}^{m}V_j\mid B\right).
$$

For two verifiers: [algebra]

$$
\beta_{comp}=\beta_1\beta_2+
\rho_{12}\sqrt{\beta_1(1-\beta_1)\beta_2(1-\beta_2)}.
$$

Here positive correlation is dangerous: it raises the joint false acceptance from the independent
product towards the smaller marginal, which belongs to the stronger verifier. For arbitrary
dependence: [algebra]

$$
\max\left(0,\sum_j\beta_j-(m-1)\right)
\le \beta_{comp}\le \min_j\beta_j.
$$

Pairwise `rho` still does not identify an `m > 2` intersection. Consilient must continue ADR-0012's
rule: measure the composite on the same known-bad artefacts and retain component outcomes as
diagnostics; never multiply marginal verifier betas. The current beta consumer and ADR-0012 are the
repository evidence. [measured] [algebra]

The complete risk is `P(union_i (B_i intersection intersection_j V_ij))`. [algebra] One measurement of
same-artefact verifier correlation can populate the inner intersection; it cannot decide the outer
candidate-attempt union.
The duplicate-numbered READY entry titled *Where inside its sharp bound does composite beta actually
land?* proposes the first measurement but explicitly records that EXP-47 discarded most full outcome
vectors; it is not a result or a reusable instrument. EXP-81 requires full vectors and records both
axes. It can show that iid understated the realised union on its frozen non-adaptive panels; its
small sample cannot establish a safe iid exception, even for `n <= 5`. [measured] [asserted]

An outcome-adaptive repair or retry changes the conditional hazards `h_i` by feeding earlier
artefacts or verifier results into later generation. EXP-81's sealed slots do not observe that
process, and five-slot vectors do not identify higher-order unions. Any adaptive retry or proposed
`n > 5` therefore remains on the robust ceiling. [algebra] [asserted]

`work-modes.md` formerly used `n_max` for both review-capacity concurrency and candidate exposure. It
now uses `n_review_capacity` for `T_cycle / T_review` and `n_attempt_max` for the risk ceiling above;
future code follows those names when the unwired router is integrated. [measured] [algebra]

## 3. The bar and what this adds

The external bar was frozen before this design was read. It requires the smallest bounded structure
that adds a task-relevant fact unavailable to a capable single Owner, preserves one accountable
Owner and the principal's authority, and beats the same-budget single-owner control on independent
artefact verdicts without unacceptable beta, cost or latency. The frozen bar records those criteria.
[measured] [asserted]

The strongest retrieved constraints are not pro-squad claims: Ao, Gao and Simchi-Levi prove that an
ideal central Bayes decision-maker weakly dominates a finite acyclic delegated network with the same
exogenous signals; their theorem bounds information, not the performance of a bounded model under a
computation budget. Kim et al. found task-dependent gains and losses across 260 configurations, and
Jwalapuram et al. found generic multi-agent designs losing to a strong single-agent comparator while
a deliberately separable specialist design won on a synthetic task. The sources are
arXiv:2603.26993, doi:10.1038/s42256-026-01268-y and arXiv:2606.13003. [cited]

The search, exclusions and near misses are the frozen record in
`docs/00-context/agentic-organisation-bar-2026-08-22.md`; this specification adds no later source to
move that yardstick. [measured] The delta over the plain answer is narrow: it separates the two
dependence problems, gives fusion a calibrated likelihood mechanism rather than a vote, and names
the event fields and experiment that make the dependence measurable. [asserted]

## 4. What counts as a different class

A reading is an observation produced by a frozen acquisition contract. An agent message, role name
or opinion is not a reading. A reading earns evidence credit only when its truth-relevant anchor is
new to the current composition, acquired without seeing peer outputs, retained by immutable locator
and hash, and capable of changing the scoped decision. [asserted]

| Candidate source | Honest independence assessment | Operational admission |
|---|---|---|
| Execute the artefact: tests, compiler, sensor or other runtime | **High exogeneity from prose reasoning; dependence magnitude unmeasured.** It observes behaviour the author did not possess, but tests derived from the same mistaken specification can share the error. Execution is necessary, not a perfect oracle. [measured] [asserted] | Admit the frozen execution result. Calibrate its composite beta for the task family; retain every component outcome and non-completion. [asserted] |
| Drive a real browser | **High for rendered/runtime behaviour, conditional on the driver.** It adds browser state, layout and interaction facts, but a selector or assertion copied from the implementation can fail with it; cross-browser correlation is unmeasured. [asserted] | Admit only screenshots, accessibility tree, network/console observations or executed interactions tied to browser/version and artefact hash. A prose visual review alone is not this class. [asserted] |
| Check a citation against its actual source | **High for what the source says; none for whether the source is true.** A second reader of the same abstract is not a new class. [asserted] | Admit a fetched `[FULL]` or claim-bounded `[ABS]` source with locator and retrieval date. Selection by the claimant remains a bias to preserve. [asserted] |
| Read a corpus not previously in context | **Moderate to high if independently selected and non-derived; otherwise low.** Corpus overlap, shared provenance and model-training overlap are unmeasured. [asserted] | Admit only with source, licence, retrieval date, selection rule and content hash. A paraphrase of an existing corpus is the same class. [asserted] |
| Use a different model family | **Low as exogeneity and unmeasured as error decorrelation.** Families plausibly vary in computation, but training data and evaluation priors overlap. Without a new anchor the exogenous contribution is zero. [asserted] | Record family/model as correlation metadata. Never award an evidence-class slot for the family label alone. [asserted] |
| Obtain a human verdict | **High and unique for preference, authority and lived impact; unmeasured for objective truth.** A human shown the candidate or the same checks can share their error boundary. [asserted] | The principal alone supplies reserved authority. For empirical truth, record the human's pre-advice position, arrival channel, artefact exposure and later verdict where available; never turn satisfaction or confidence into a weight. [asserted] |

An asserted label, job title, persona, separate system prompt, extra pass over shared context or vote
adds no class. It is cut. Ao, Gao and Simchi-Levi (arXiv:2603.26993) supply the information-bound
source; the operational cut is this specification's decision. [cited] [asserted]

## 5. When fusion is warranted

Task difficulty is not an admission field. Before work, the Owner freezes the action set, loss of a
wrong action, irrecoverable remainder after reversal, reversal cost, delay cost, risk ceiling and
the cost of each proposed reading. [asserted]

For a proposed reading `E`, fusion is warranted only when both conditions hold: [algebra]

1. the action is irreversible or outward-facing, **or** the frozen worst-case loss plus reversal
   cost exceeds the task's loss ceiling; and
2. a conservative lower bound on the expected value of sample information from `E` exceeds its
   acquisition and delay cost, and some possible outcome of `E` would change the action.

An EVSI upper bound at or below cost rejects the reading immediately. An interval that merely reaches
above cost is not admission: it leaves the value unmeasured and keeps one Owner. The second condition
also rejects ceremonial checking because if no possible observation changes the action, its
information value is zero. [algebra] [asserted]

| Consequence and reversibility | Composition |
|---|---|
| Reversible inside the task's loss and reversal budgets | One Owner with all ordinary tools. Decide at the best available estimate, record reversal and falsifier; do not convene because the work appears difficult. [asserted] |
| Consequential or expensive to reverse, with a truth-relevant reading whose conservative value bound exceeds its cost | One Owner plus the smallest set of sealed acquisition contracts needed to cross the pre-committed risk threshold. Each added contract names its anchor. [asserted] |
| Irreversible, outward-facing or principal-reserved | Fusion may improve the recommendation but cannot supply authority. No amount of agreement approves spend, publication, credentials, gate lifts or the principal's preferences. [asserted] |

If no genuinely exogenous reading is available, adding agents is refused. For a reversible action the
Owner still decides under labelled uncertainty; for an irreversible action the system returns
unresolved or asks the principal only where ADR-0033 reserves the decision. [asserted]

## 6. Fusion mechanism: calibrated readings, not votes

For a binary claim `H`, every admitted instrument is calibrated on held-out labelled cases from the
same task family and frozen contract. An observed outcome `o_i` contributes the measured likelihood
ratio: [algebra]

$$
\Lambda_i(o_i)=\frac{P(o_i\mid H)}{P(o_i\mid \neg H)}.
$$

Model self-confidence never appears. If an instrument has no calibration, its reading may expose a
deterministic counterexample or remain visible qualitative evidence; it contributes no numeric
weight. [asserted]

Readings sharing an artefact source, derivation chain, context, generator, verifier contract or
pre-seal access path form one **dependence block**. Where the block has a measured joint outcome
table, use its joint likelihood ratio. Where it does not, do not multiply its members: a primary
reading selected before outcomes represents the block numerically and the rest remain diagnostics.
This deliberately discards apparent weight rather than manufacture independence. [asserted]

For blocks demonstrated conditionally independent for the frozen population, posterior log-odds
add: [algebra]

$$
\log O(H\mid o)=\log O(H)+
\sum_g \log\frac{P(o_g\mid H)}{P(o_g\mid\neg H)}.
$$

If cross-block dependence is unmeasured, compute a posterior interval across the admissible sharp
joint bounds rather than use the sum as a point value. A prior is a retrieved base rate or a labelled
`[asserted]` interval; it is never the Owner's feeling or a model's confidence. [asserted]

The protocol is: [asserted]

1. **Freeze.** Record `H`, alternatives, loss matrix, prior, risk ceiling, required anchors,
   calibration versions, dependence blocks, budget, expiry and verifier before candidate work.
2. **Acquire and seal.** Each reader sees only its assigned sources/tools and seals its raw outcome,
   anchor and limits before any peer output is released. Refusal, timeout and `not_run` are outcomes.
3. **Calibrate and fuse once.** The Owner joins each outcome to the pre-committed calibration and
   combines blocks as above. No count of agents or agreeing strings enters the calculation.
4. **Resolve disagreement with facts.** A pre-committed necessary-condition failure is a veto, not a
   vote to average. Otherwise acquire one decisive exogenous reading if its information value still
   exceeds cost; if not, preserve the conflict as unresolved.
5. **Emit one candidate.** The Owner disposes of every material conflict and exposes the frozen
   composite verifier once. Evidence-role count does not increase `n_attempt_max`.

**Quantitative convergence.** Propagate calibration sampling intervals, the prior interval and all
admitted dependence bounds into `[p_L, p_U] = P(H | readings)`. Converge on `H` only when
`p_L >= 1-epsilon`; converge on `not H` only when `p_U <= epsilon`. For several actions, converge
only when the same action minimises expected loss across the entire uncertainty set and its maximum
regret is below the frozen regret ceiling. Otherwise the result is `unresolved`. [algebra]

This is fusion because evidence changes odds by its measured discrimination and provenance. Ten weak
readings can add less than one executed counterexample; ten agreeing but uncalibrated agents add
exactly zero numeric weight. [algebra] [asserted]

## 7. Make correlation computable in the existing record

This change adds one validated `verification.outcome` event kind to `events.py` and writes it through
the existing `append()` chokepoint. It does not repeat `attempt.outcome`, add a second writer, add a
SQLite authority table or add a CLI command. The generic projection already preserves canonical
event payloads, so correlation is computed from replayed events. [measured]

Each `verification.outcome.data` requires: [measured]

- `verification_id`: stable invocation/result identifier;
- `attempt_id`: join to task, candidate, composite outcome and later human verdict;
- `protocol_id`: frozen sampling population, normally the registered experiment identifier;
- `artefact_sha256`: lowercase SHA-256 of the exact artefact;
- `verifier_id` and `verifier_version`: stable contract identity and pinned version;
- `evidence_class`: the fact class actually observed;
- `status`: `completed`, `error`, `timeout`, `refused` or `not_run`;
- `verifier_accept`: Boolean, present only for `completed`.

The existing event envelope supplies append time. The immutable protocol manifest referenced by
`protocol_id` supplies the sampling window, `task_id`, candidate panel and index, generator, seed,
instruction/context digest and source-set hashes; `attempt_id` joins the composite outcome and human
verdict. Harness, provider, model/revision and anchor hashes remain separate optional metadata: if a
claimed exogeneity analysis needs one and it is absent, that exogeneity is unmeasured rather than
inferred from `verifier_id`. [asserted]

For same-attempt verifier correlation, group by `(protocol_id, attempt_id)` and pair completed
outcomes by verifier/version to compute the full contingency table, covariance, phi and joint false
accept. For attempt correlation, group composite bad-shipment indicators by
`(protocol_id, task_id, candidate_panel_id)` and retain the ordered full vector. [algebra]

Every planned verifier emits a terminal status. Timeouts, refusals, errors and missing labels are
reported separately in every result, including when zero; they are never silently cast to rejection
or used to support an iid claim through a selected complete-case subset. EXP-81 requires every frozen
panel in a stratum to have binary component, composite and human outcomes for a dependence
classification; otherwise it reports only descriptive complete-case tables beside the missingness
table. The dependence-robust ceiling remains under every result. [asserted]

The implementation validates every field before append, accepts paired outcomes for one artefact,
rejects malformed hashes, versions, statuses and conditional booleans, and proves append/replay can
form all four contingency cells without bypassing the writer. `verification.outcome` cannot carry a
human verdict through the existing authority checks. Repeated `evidence_class` values across
observations remain legal because measuring their dependence is the point. [measured]

Validation is structural, not a global uniqueness claim: the append-only writer holds no cross-file
identity index. Any correlation analysis must refuse a repeated `verification_id` or more than one
outcome for the same `(protocol_id, attempt_id, verifier_id, verifier_version)`; it may not
deduplicate after looking at values. EXP-81 treats the affected panel as protocol-invalid and therefore
cannot admit iid sizing. [asserted]

## 8. Reuse and authority boundaries

`dispatch.py` remains the fan-out boundary; `coordination.py` retains claims; `recall.py` supplies
bounded verbatim context; `work_items.py` remains task state; `routing.py` owns beta ceilings;
`budget.py` owns spend; `instructions.py` layers context; and `events.py` remains the sole append-only
writer. No second orchestrator, seventh CLI command, gate change, new dependency or new product-tree
I/O capability is introduced. `routing_orchestration_enabled` stays `false`. [measured] [asserted]

The principal's authority is not a likelihood term. An agent may recommend after fusion; it cannot
author a verdict, approval, gate lift, spend, credential disclosure or outward publication in his
name. [asserted]

## 9. Evidence against: one capable Owner may already be the fusion engine

The strongest objection is that a capable Owner with retrieval, execution, a browser and source
checking already integrates more genuinely different classes than a squad of agents usually does.
Partitioning those tools across agents can replace direct observations with lossy hand-offs, hide a
shared mistaken specification behind several role labels, multiply context and coordination cost,
and spend the same budget that the Owner could use on deeper checking. [cited] [asserted]

Ao, Gao and Simchi-Levi make the information objection exact for an ideal centre with the same
signals; they do **not** prove that one bounded model can realise the ideal centre under a fixed
computation budget. Kim et al. and Jwalapuram et al. nevertheless show that the empirical burden is
on the organisation, not the single-owner control. [cited]

This specification concedes most of the objection. One Owner is the default; tools remain available
to that Owner; an added reader with no new calibrated anchor is cut; and EXP-80, not agreement, must
show that isolated evidence acquisition beats the strongest same-budget Owner. If it does not, keep
the event schema and one-owner protocol and remove squad-specific fusion. [asserted]

## 10. Validation and falsifiers

EXP-81 measures the two dependence axes on frozen candidate panels. Its stopping rule is registered
before any panel is inspected. Until it reports, `n_attempt_max` uses the dependence-robust union
bound and no component-verifier product is an acceptance input. A positive empirical `D_k` falsifies
iid on the frozen sample; zero or negative `D_k` does not prove safety and cannot license iid sizing.
[asserted]

The affected provisional mechanism is cut or revised if any of the following occurs: [asserted]

- EXP-81 finds the iid candidate formula false-safe for a frozen stratum, which permanently removes
  an iid exception for that protocol;
- EXP-80 finds no quality or safety gain over the same-budget capable Owner after ablating extra
  facts, so the fusion organisation is cut;
- a supposedly different class changes no accessible fact when removed, so that class is relabelled
  echo; or
- the proposed event set cannot reconstruct both a same-artefact contingency table and a grouped
  candidate-union rate without another writer, in which case the schema is incomplete.

The plain answer would have been “use one Owner and measure composite beta directly”. That remains
the default. The added mechanism applies only when consequence, reversibility and measured
information value justify more than one independently acquired reading. [asserted]
