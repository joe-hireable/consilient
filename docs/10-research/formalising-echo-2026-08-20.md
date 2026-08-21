# Formalising the echo claim

**Date:** 20 August 2026
**Status:** `[algebra]` for the propositions and worked models; `[measured]` only for
repository results already produced by registered instruments; `[cited]` only for sources
listed in §9 as read at the stated depth; `[asserted]` for the proposed engineering rule and
its application.

## Finding

**The framing is wrong.** “Agreement between agents that share evidence carries no information
about the truth” is false in its operational reading and vacuous in its strongest
information-theoretic reading. Shared-evidence agents can improve a decision by averaging
independent interpretation error; what they cannot do is add information beyond the shared
evidence or remove a common error in that evidence. [algebra]

There is an exact zero-information statement. Let \(T\) be the truth, \(E\) the full shared
evidence, \(A_1,A_2\) the outputs and \(G=\mathbf 1[A_1=A_2]\). If

\[
T \longrightarrow E \longrightarrow (A_1,A_2)
\tag{1}
\]

is a Markov chain, then \(I(T;G\mid E)=0\). But this follows because *every* function of
outputs generated only from \(E\) is uninformative after conditioning on the full \(E\); it
does not identify a special defect in agreement. [algebra]

The condition suggested in the brief,
\(A_1\mathbin{\perp\!\!\!\perp}A_2\mid E\), is neither necessary nor sufficient for that
result. The relevant condition is the no-private-signal condition (1), not independence
between the agents. [algebra]

The closest prior result is not new. Dietrich and List model jurors who all observe the same
body of evidence, make votes independently conditional on that evidence, and are each better
than chance at its ideal interpretation. Their majority increasingly recovers the ideal
interpretation, but its truth-tracking probability converges only to the probability that the
shared evidence is not misleading. That is the precise version this project needs:
**more agents can remove interpretation noise, but cannot beat common-evidence error.**
[cited]

## 1. Four different claims have been collapsed

The current sentence conflates four propositions that have different truth values. [asserted]

1. **No new Shannon information:** after conditioning on the complete shared evidence, an
   output computed only from that evidence contains no additional information about truth.
   This is true under (1), for one agent just as much as for a panel. [algebra]
2. **No decision improvement:** aggregating several agents cannot outperform one agent. This
   is false without assumptions about competence, dependence, aggregation and budget.
   Condorcet-style results give elementary counterexamples. [algebra]
3. **No independent corroboration:** agreement derived from one common evidential source
   should not be counted as two independent tests of that source. This is the defensible
   Whewell rule. [asserted]
4. **No engineering value:** shared-context debate, sampling or decomposition is useless.
   This does not follow. Such structures may have computational value while supplying zero
   new evidential provenance. [algebra]

ADR-0010's cited delegation theorem concerns proposition 2 for an unrestricted central
Bayesian decision-maker with the same information. It does not prove a theorem specifically
about the evidential meaning of agreement, and it does not establish that a real bounded
agent can perform the central computation. The ADR already records both qualifications.
[cited]

Blackwell's comparison of experiments supplies the older decision-theoretic boundary: a
garbling of an observed signal cannot improve the expected utility of an unrestricted
Bayesian decision-maker for every decision problem. A model output computed from \(E\) is
such a garbling when the model has no private signal. A computationally bounded user may
still benefit because the model performs a calculation the user cannot cheaply perform;
Shannon information and computational assistance are not the same quantity. [cited]
[asserted]

## 2. The exact zero-information theorem

### Proposition 1 — no private signal, no conditional information

Assume finite-valued variables for simplicity and

\[
P(a_1,a_2\mid t,e)=P(a_1,a_2\mid e)
\quad\text{for all positive-probability }(t,e).
\tag{2}
\]

Then

\[
I(T;G\mid E)=0.
\tag{3}
\]

**Proof.** Equation (2) is \((A_1,A_2)\mathbin{\perp\!\!\!\perp}T\mid E\). Since
\(G\) is a deterministic function of \((A_1,A_2)\), conditional data processing gives

\[
I(T;G\mid E)\le I(T;A_1,A_2\mid E)=0.
\]

Therefore (3) follows. [algebra]

A sufficient generative form is

\[
A_i=f_i(E,R_i),\qquad (R_1,R_2)\mathbin{\perp\!\!\!\perp}T\mid E,
\]

where \(R_i\) contains sampling randomness. The \(R_i\) need not be independent of each
other; even perfectly coupled agents add no truth information conditional on the complete
\(E\) if their joint randomness is independent of \(T\). [algebra]

This theorem is stronger than the project's phrase in one sense and weaker in the useful
sense. It applies to all computed summaries, not only agreement; but it says nothing about
whether those summaries help a bounded decision-maker use \(E\). [algebra]

### Conditional independence between agents is insufficient

Let \(E\) be constant, \(T\sim\operatorname{Bernoulli}(1/2)\), and
\(U\sim\operatorname{Bernoulli}(1/2)\) independent of \(T\). Define

\[
A_1=U,\qquad
A_2=
\begin{cases}
U,&T=1,\\
1-U,&T=0.
\end{cases}
\]

The four pairs \((A_1,A_2)\) are marginally equiprobable, so
\(A_1\mathbin{\perp\!\!\!\perp}A_2\mid E\). Yet
\(G=\mathbf 1[A_1=A_2]=T\), and therefore

\[
I(T;G\mid E)=H(T)=1\ \text{bit}.
\]

The agents' outputs are independent after marginalising over \(T\), while their *pattern of
dependence* reveals \(T\). This counterexample was also enumerated locally before this
document was written. [algebra]

Conditional independence given \(E\) therefore cannot carry the claimed theorem. The
additional screening-off condition \(T\perp(A_1,A_2)\mid E\) is what does the work.
[algebra]

## 3. Agreement alone is not the operational signal

The indicator \(G\) throws away the value on which the agents agreed. That makes
\(I(T;G\mid E)\) a poor formalisation of how agreement is used. A real aggregator observes
at least \((A_1,A_2)\), or the common verdict \(V\) together with \(G\), and asks whether the
agreed verdict is likely to be correct. [asserted]

Consider a uniformly distributed binary truth and symmetric independent error channels:

\[
A_i=T\oplus N_i,\qquad N_i\sim\operatorname{Bernoulli}(q_i),
\]

with \(N_1,N_2\) independent of each other and of \(T\). Then

\[
P(G=1\mid T)
=(1-q_1)(1-q_2)+q_1q_2,
\]

which does not depend on \(T\). Thus \(I(T;G)=0\): agreement alone does not reveal whether
the truth value is zero or one. [algebra]

But when the agents agree on \(V\),

\[
P(T=V\mid G=1,V)
=
\frac{(1-q_1)(1-q_2)}
{(1-q_1)(1-q_2)+q_1q_2}.
\tag{4}
\]

For equal error \(q_1=q_2=q<1/2\), (4) is strictly greater than the individual accuracy
\(1-q\). Agreement is uninformative about the *label of truth in isolation* while being
informative about the *correctness of the agreed label*. The current English claim erases
that distinction. [algebra]

This is the two-voter core of the Condorcet result. For odd \(n\ge3\), independent voters with
common error \(q<1/2\) have majority error

\[
q_n=\sum_{k=(n+1)/2}^{n}\binom nk q^k(1-q)^{n-k}<q,
\]

and \(q_n\to0\). The same-evidence qualification changes the limiting target, not the
elementary fact that independent interpretation noise can be averaged away. [algebra]

That distinction can be shown inside the shared-evidence Markov structure. Let
\(P(E=T)=r>1/2\), and let each agent independently misinterpret \(E\) with probability
\(q<1/2\). A single agent has truth accuracy

\[
r(1-q)+(1-r)q=r+(1-2r)q.
\]

An odd majority has interpretation error \(q_n<q\) and truth accuracy

\[
r+(1-2r)q_n>r+(1-2r)q.
\]

The majority improves the decision while every agent output still has zero conditional
mutual information about \(T\) once \(E\) is given. Its accuracy approaches \(r\), the
reliability of the common evidence, rather than one. [algebra]

Dietrich and List make that qualification explicit with the graph

\[
T\longrightarrow E\longrightarrow A_1,\ldots,A_n.
\]

Votes are independent conditional on \(E\), and the vector of votes is independent of
\(T\) conditional on \(E\). Majority voting converges to the ideal interpretation \(f(E)\);
its correctness converges to \(P(f(E)=T)\), not to one. This is both a direct formalisation
of shared-evidence agreement and a refutation of the claim that such a panel necessarily
adds nothing. [cited]

## 4. Correlated bias: agreement can indicate bias and truth

“If both agents share a systematic bias, agreement is evidence of the bias, not of the
truth” is also too strong. Agreement can update both hypotheses; which update dominates
depends on a model that agreement alone does not identify. [algebra]

Let \(Z=1\) denote a common-bias regime with prior probability \(\lambda\). In that regime
both agents always return the same wrong answer. When \(Z=0\), they make independent
symmetric errors with probability \(q<1/2\). Put
\(s=(1-q)^2+q^2<1\). Then

\[
P(Z=1\mid G=1)
=\frac{\lambda}{\lambda+(1-\lambda)s}
>\lambda.
\tag{5}
\]

Agreement is evidence for the existence of the common-bias regime in this specified
mixture. [algebra]

At the same time, the probability that the agreed verdict is true is

\[
P(T=V\mid G=1)
=\frac{(1-\lambda)(1-q)^2}
{\lambda+(1-\lambda)s}.
\tag{6}
\]

An individual agent's accuracy is \((1-\lambda)(1-q)\). The agreement in (6) improves on
that accuracy exactly when

\[
\lambda < \frac{1-2q}{2(1-q)}.
\tag{7}
\]

So agreement is simultaneously evidence of a common-bias regime and, when that regime is
sufficiently rare, evidence that the common answer is correct. “Bias, not truth” is a false
dichotomy. [algebra]

More importantly, the latent mixture is not identifiable from agreement alone. A high
agreement rate can be generated by accurate independent agents, common copying, a shared
misleading input, or a mixture of easy and hard items. Without labelled outcomes or strong
model assumptions, the same output table supports incompatible stories about truth and
reliability. Dawid and Skene note the corresponding label-switching and latent-class
identifiability problem in their observer-error model. [cited]

The measurable object is therefore not raw agreement. With known truth, define
\(C_i=\mathbf 1[A_i=T]\) and retain the full pair table
\((C_1,C_2)\): correct-correct, correct-wrong, wrong-correct and wrong-wrong. The
wrong-wrong or “double-fault” cell directly records coincident error; overall agreement
mixes that cell with correct-correct convergence and is confounded by competence.
[algebra]

Classifier-ensemble work has used the double-fault rate, pairwise correlation, disagreement,
Yule's \(Q\), inter-rater agreement and item-difficulty measures for this reason. It also
finds that no single diversity statistic has a generally reliable relationship with ensemble
accuracy outside restricted models. [cited]

## 5. A formal working definition of “different class of facts”

The definition should concern **source signals**, not model names, prompts, roles or final
answers. Let \(S_i\) be the provenance-bearing observation available only through source
mechanism \(i\), and let \(E\) be the common record. A second source is a different
truth-relevant class for a proposition \(T\) only if

\[
I(T;S_2\mid E)>0
\quad\text{and}\quad
I(T;S_2\mid E,S_1)>0.
\tag{8}
\]

For symmetric treatment require the analogous two inequalities for \(S_1\). Equation (8)
says that the source is truth-relevant on its own and still contributes non-redundant
information after the other source is known. This is the proposed formal meaning of a “new
exogenous signal”. [asserted]

The second term has an exact log-score interpretation:

\[
I(T;S_2\mid E,S_1)
=
\mathbb E\!\left[
\log
\frac{P(T\mid E,S_1,S_2)}
{P(T\mid E,S_1)}
\right].
\]

It is the expected posterior log-score gain from the second source. A restatement,
deterministic transform or duplicate of \(S_1\) has zero gain. [algebra]

Equation (8) is not directly estimable without repeated labelled outcomes. Before such
measurement, a declared `evidence_class` is a hypothesis about provenance, not proof of
independence or incremental truth information. [asserted]

Residual dependence must be measured separately. A useful ideal is

\[
S_1\mathbin{\perp\!\!\!\perp}S_2\mid(T,E,C),
\tag{9}
\]

where \(C\) contains registered common causes such as item difficulty, shared tests,
training lineage or a common upstream source. Equation (9) makes likelihood contributions
factor after known common causes are held fixed. It is not part of the definition in (8):
dependent signals may still carry incremental truth information, and conditionally
independent coin flips may carry none. [algebra]

The alternatives in the brief fail as stand-alone definitions:

- **Conditional independence given \(T\)** is useful for Condorcet and Dawid–Skene models,
  but uninformative signals satisfy it, as do duplicate deterministic reports once \(T\) is
  fixed. It needs relevance and non-redundancy conditions. [algebra]
- **Distinct sufficient statistics** is too strong and can point backwards: if \(S_1\) is
  already sufficient for \(T\), a second statistic may have no incremental information by
  definition. [algebra]
- **Non-overlapping information sets** is syntactic. Two disjoint documents can copy one
  upstream error; two overlapping sources can each contain unique observations. [asserted]
- **Different model families** is a development-history label, not an observed evidence
  relation. Large cross-provider studies find substantial coincident LLM errors even across
  distinct architectures and providers. [cited]

The practical rule should therefore be narrower:

> **Agreement is not independent corroboration unless each conclusion traces to a
> truth-relevant source signal whose incremental value or residual error dependence has
> been measured. A shared-evidence panel may reduce interpretation noise, but it does not
> multiply the evidential strength of the shared record.** [asserted]

## 6. Audit of this project's structures

The current binary verdicts in ADR-0010 do not survive the definition above unchanged.
[asserted]

| Structure | Result under (8) | Reason |
|---|---|---|
| Critic runs tests the worker did not run | **Conditional pass** | The new execution result is a source signal if it is relevant to \(T\). If the worker already saw the same test output, a second reading is not a new fact. [asserted] |
| Parallel worktrees | **Fail as currently named** | Different candidate repository states are different artefacts, not independent evidence that any one artefact is correct. Fresh verifier outcomes on them may qualify; the worktrees themselves do not. [asserted] |
| Discovery agents on separate primary sources | **Conditional pass** | They qualify only if provenance shows distinct upstream sources and each adds truth-relevant information. Different URLs relaying one source fail. [asserted] |
| Independent verification of a lead | **Pass when genuinely re-derived** | Blinding the first write-up and returning to primary evidence or execution can introduce \(S_2\). Re-reading the lead does not. [asserted] |
| Escalation to a different model family | **Fail by label alone** | It may supply useful computation or a differently distributed error, but “family” does not establish a new fact or low residual co-failure. [asserted] |
| Shared-context debate or model battling | **No independent corroboration** | It may improve search or interpretation, but agreement cannot be counted as an additional evidential source. [asserted] |
| Planner → implementer hand-off | **No independent corroboration** | The hand-off can decompose computation. It adds evidence only when implementation produces new execution or artefact observations. [asserted] |
| EXP-52 arm 4: diff / tests / specification views | **Conditional pass** | The views are distinct observables, but each must retain competence and add information about the same verdict. Artificially withholding necessary context can make a “different” view worse than the common view. [asserted] |

The strongest correction is the parallel-worktree row. Variation in generated solutions can
reduce common implementation errors, but a generated alternative is not a class of facts
about the correctness of another alternative. Calling repository states “evidence classes”
confuses hypothesis generation with hypothesis testing. [asserted]

The critic row also needs an explicit seam. “Runs the tests” is a different fact only when
the result was not already in the worker's evidence and the tests have measured sensitivity
to the defect class at issue. A second agent running the same weak checks can reproduce the
same false acceptance; the number of runners does not reduce the checks' \(\beta\).
[algebra]

## 7. What the repository's measured convergence establishes

Two model families produced corrected \(\beta\) values 0.0085 apart while disagreeing on 16
of 75 underlying bad-label decisions. Cross-combining their numerator and denominator
judgements widened the range from 0.0085 to 0.1192, fourteen times the reported spread.
[measured]

That is a clean warning against treating convergence of a derived statistic as agreement on
its inputs. It is not evidence that the two model families shared one systematic
item-level bias: there is no gold label for the 75 decisions, and the families disagreed
substantially. The measured mechanism was arithmetic cancellation between promoted
numerators and removed denominators. [measured]

The honest lesson is narrower and stronger: **agreement must be tested at the level where an
error could coincide.** For EXP-52 that means per-item correctness and the double-fault
table, not closeness of arm-level \(\beta\) point estimates. [asserted]

## 8. Pre-run predictions and required interpretation for EXP-52

No new experiment is registered here because EXP-52 already asks the empirical question.
The following predictions are recorded before any EXP-52 arm is run. [asserted]

### Predictions

1. **Arm 2 can beat arm 1 without new evidence.** If same-family samples have individual
   false-accept probability below \(1/2\) and enough residual independence conditional on
   item difficulty, odd-\(N\) majority voting reduces \(\beta\). Such a result would refute
   ADR-0010's blanket “shared evidence adds nothing” wording, but would be consistent with
   Condorcet and Dietrich–List: the panel averaged interpretation noise. [algebra]
2. **Arm 2 has a shared-evidence floor.** Increasing \(N\) cannot remove errors caused by a
   misleading common task record, shared test weakness or common model blind spot. Under the
   Dietrich–List model the limiting majority accuracy is the probability that the common
   evidence points to truth, not one. [cited]
3. **Arm 3 is not guaranteed to beat arm 2.** Cross-family voting helps only if it lowers
   residual co-failure or raises competence. Family count alone predicts neither. Recent
   cross-family LLM measurements make a large independence gain doubtful, but that is a
   prior, not a verdict on this corpus. [cited]
4. **Arm 4 is not guaranteed to win.** Distinct views help only if their signals are
   individually relevant and jointly incremental. If a diff-only, test-only or
   specification-only view omits information required for competence, evidence separation
   can lower accuracy. [algebra]
5. **Residual coincident error predicts gain better than raw agreement.** Holding individual
   \(\beta\) and \(\alpha\) fixed, arms with lower wrong-wrong dependence should obtain more
   majority-vote gain. Correct-correct agreement is not a failure signal and should not be
   mixed into that predictor. [algebra]
6. **The repository's arithmetic-cancellation failure can recur across arms.** Similar
   arm-level \(\beta\) values can conceal different per-item labels, so every comparison
   must report paired changes and the item-level contingency table. [measured]

### Measurements needed to test them

For each agent pair and arm, retain the \(2\times2\) correctness table, double-fault rate,
pairwise \(\phi\) correlation and agreement conditional on both agents being wrong. Report
the same measures by pre-registered item-difficulty strata so common hard items are not
mistaken for residual dependence. [asserted]

For an exchangeable panel with \(N\) error indicators and mean pairwise correlation
\(\rho\), the variance of the mean error is

\[
\operatorname{Var}(\bar C)
=\frac{\sigma^2}{N}\{1+(N-1)\rho\},
\]

giving the familiar diagnostic

\[
N_{\mathrm{eff}}=\frac{N}{1+(N-1)\rho}.
\]

This is an exchangeable-correlation summary, not a proof that a heterogeneous panel literally
contains \(N_{\mathrm{eff}}\) independent agents. Kohli uses it alongside item-aware
Condorcet simulation and reports severe effective-size loss in a nine-model panel.
[algebra] [cited]

Because every arm sees the same mutant items, compare arm and baseline outcomes as *paired*
data. Report a confidence interval for
\(\Delta\beta=\beta_{\text{arm}}-\beta_{\text{single}}\) using a paired bootstrap over
items or an exact paired test where its assumptions fit. Separate intervals for two
proportions discard the pairing. [asserted]

EXP-52's current stopping rule says overlapping Wilson intervals imply that voting “adds
nothing”. That inference is invalid: overlap fails to reject a difference and does not
establish equivalence. “Adds nothing” needs a pre-registered equivalence margin on paired
\(\Delta\beta\); without one, the honest verdict is “difference unresolved”. This document
does not amend the registered protocol, but its result must not be interpreted as an
equivalence result under the existing overlap rule. [algebra]

Use odd panel sizes or pre-register a deterministic tie rule. Report \(\alpha\) beside
\(\beta\): a rule can reduce false acceptance by rejecting everything, which is not a useful
consensus gain. Cost and matched inference budget remain required because repeated sampling
can buy improvement at \(N\) times the work. [asserted]

### Falsifying observations

- If arm 2 produces a paired reduction in \(\beta\) beyond a pre-registered equivalence
  margin at matched decision rule, while retaining \(\alpha\), the blanket echo claim is
  empirically false on this corpus. The narrower common-evidence-floor claim remains.
  [asserted]
- If arm 4's independently relevant views have no detectable incremental truth information
  and no lower residual co-failure across a decision-grade corpus, equation (8) is not an
  operationally useful gate in this setting and should not replace the current rule.
  [asserted]
- If majority accuracy exceeds the measured accuracy of the ideal full-evidence
  interpretation under a design satisfying the Markov structure in (1), either the
  measurement of the ideal interpretation is wrong or the agents have an unrecorded private
  signal; the model itself would be falsified. [algebra]

## 9. Literature boundary and novelty

The clean negative is that the theory is established. Condorcet-style aggregation,
shared-evidence jury models, correlated-voter extensions, latent observer-error models,
classifier diversity, opinion pooling, source-reliability models and recent LLM error audits
already cover the mathematical territory. [cited]

| Source read | What it establishes here |
|---|---|
| Dietrich & List, *A Model of Jury Decisions Where All Jurors Have the Same Evidence*, *Synthese* 142(2), 175–202 (2004), doi:10.1007/s11229-004-1276-z. `[FULL]` | The exact shared-evidence graph, conditional independence given evidence, interpretation-noise gain and common-evidence error floor. [cited] |
| Dietrich & Spiekermann, *Jury Theorems* (2016 manuscript; current Stanford Encyclopedia entry read in full). `[FULL]` | Conditional jury theorems, shared evidence as a common cause, and the tension between conditioning richly enough for independence and retaining competence. [cited] |
| Ladha, *The Condorcet Jury Theorem, Free Speech, and Correlated Votes*, *AJPS* 36 (1992), doi:10.2307/2111584; and *Information Pooling through Majority-Rule Voting*, *JEBO* 26 (1995), doi:10.1016/0167-2681(94)00068-P. `[ABS]` | Correlated-voter generalisations exist; increasing positive correlation weakens majority-vote gains in the models studied. No claim here relies on an unread proof detail. [cited] |
| Dawid & Skene, *Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm*, *Applied Statistics* 28(1), 20–28 (1979), doi:10.2307/2346806. `[FULL]` | Conditional independence given latent truth, observer confusion matrices, weighted consensus and latent-class identifiability limits. [cited] |
| Kuncheva & Whitaker, *Measures of Diversity in Classifier Ensembles and Their Relationship with the Ensemble Accuracy*, *Machine Learning* 51, 181–207 (2003), doi:10.1023/A:1022859003006. `[FULL]` | Ten error-diversity measures including double fault; no generally accepted diversity definition; weak general relation between a diversity statistic and ensemble accuracy. [cited] |
| Genest & Zidek, *Combining Probability Distributions: A Critique and an Annotated Bibliography*, *Statistical Science* 1, 114–148 (1986), doi:10.1214/ss/1177013825. `[ABS]` | Opinion pooling and dependent expert information were already a mature literature by 1986. [cited] |
| Blackwell, *Equivalent Comparisons of Experiments*, *Annals of Mathematical Statistics* 24(2), 265–272 (1953), doi:10.1214/aoms/1177729032. `[ABS]`; Ao, Gao & Simchi-Levi, arXiv:2603.26993. `[FULL in repository bibliography]` | Garbling cannot improve an unrestricted decision-maker; the modern delegation result applies that boundary to acyclic agent networks, not specifically to observed agreement. [cited] |
| Landes, *The Variety of Evidence Thesis and Its Independence of Degrees of Independence*, *Synthese* 198, 10611–10641 (2021), doi:10.1007/s11229-020-02738-5. `[FULL]`; Merdes, von Sydow & Hahn, *Formal Models of Source Reliability*, *Synthese* 198, 5773–5801 (2021), doi:10.1007/s11229-020-02595-2. `[FULL]` | Formal epistemology already models independent sources, common reliability causes, systematic bias and the difficulty of learning source reliability without external outcomes. [cited] |
| Kim, Garg, Peng & Garg, *Correlated Errors in Large Language Models*, ICML 2025, PMLR 267, arXiv:2506.07962. `[FULL]` | Across more than 350 models, wrong-answer coincidence is substantial; shared provider and architecture matter, while accurate cross-provider models can still share errors. [cited] |
| Kohli, *Nine Judges, Two Effective Votes*, arXiv:2605.29800. `[FULL]` | A nine-model, seven-family judge panel was measured at roughly two to two-and-a-half effective votes on the studied NLI data, with item-aware simulations and explicit limits. [cited] |
| Kuai et al., *How Independent are Large Language Models?*, arXiv:2604.07650. `[FULL]` | Residual co-failure conditional on item difficulty can be tested, and dependence-aware verifier weighting can beat unweighted majority voting on the studied data. [cited] |
| Eckhardt & Lee, *A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors*, IEEE TSE (1985), doi:10.1109/TSE.1985.231895; Knight & Leveson, *An Experimental Evaluation of the Assumption of Independence in Multi-Version Programming*, IEEE TSE 12(1), 96–109 (1986), doi:10.1109/TSE.1986.6312924. `[ABS]` | Software engineering has modelled and measured coincident failure among independently produced versions for four decades. [cited] |

No original theorem remains to claim. The potentially project-specific contribution is an
enforceable provenance gate tied to measured per-item residual error and \(\beta\), plus the
EXP-52 application to agentic mutation detection. Even that novelty must be stated as an
engineering application until the literature search covers current verifier-ensemble work
beyond the sources above. [asserted]

## 10. Decision, reversal and falsifier

**Decision proposed:** retain “echo” as a provenance classification, not a prediction of zero
performance gain. Shared-evidence agreement may not be counted as independent corroboration
or as an acceptance signal; it may still be used as a measured aggregation method. Replace
the unique-string `evidence_class` test, when ADR-0010 is next superseded, with provenance
checks and empirical residual-error admission. [asserted]

**Option rejected:** keep the existing sentence and reinterpret “information” informally.
That would preserve a memorable slogan at the cost of contradicting the shared-evidence jury
theorem and making EXP-52's possible arm-2 gain look paradoxical when it is not. [asserted]

**Reversal:** revert the commit that introduced this finding with:

```bash
git revert "$(git log -1 --format=%H -- docs/10-research/formalising-echo-2026-08-20.md)"
```

This removes the document; it does not silently restore confidence in ADR-0010. [asserted]

**Falsifier:** the central correction is wrong if a proof shows that, under shared evidence,
competent conditionally independent interpretations cannot improve a finite majority over
one interpreter, or if the Dietrich–List assumptions used here do not imply their stated
interpretation-noise gain and common-evidence limit. The algebra above supplies a direct
counterexample to the first possibility; EXP-52 tests whether its conditions occur in this
repository. [algebra]
