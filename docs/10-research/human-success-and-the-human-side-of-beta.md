# Human success, reliance, and the human side of β

**Status:** primary-source synthesis, 20 August 2026. Sixty-five sources were read across
eight disjoint topics by readers who did not see each other's material; 44 were read in full,
19 at abstract or landing page, and 2 are `[2ND]` vendor reports which are named here only to
be excluded. [measured] Nothing in this file is a Consilience measurement. [asserted]

This exists because the programme's stated outcome — verified human gain while preserving
agency — assumed instruments that mostly do not survive contact with the literature.
[asserted]

## Verdict

Three findings reshape the outcome definition, and the first is the one that matters. [asserted]

1. **β's own oracle is a test with an error rate, and its errors are correlated with the
   errors it grades.** [cited] The programme measures the automated checks against a human
   verdict; the human verdict is not ground truth.
2. **Sustained assistance should be expected to degrade the human capability β depends on.**
   [cited] That gives a falsifiable, apparently unmeasured claim — stated below as the
   β-drift hypothesis — which is the most publishable thing in this synthesis. [asserted]
3. **Every self-report in the outcome list is a broken sensor in exactly this population.**
   [cited] Speed, learning, self-efficacy and satisfaction are each wrong in sign under the
   conditions Consilience targets.

## 1. The correlated-oracle problem

`CONSILIENCE.md` clause 3 says convergence is a test and tests have error rates. It has been
applied to the automated checks and not to the human. [asserted]

- **Aligned error boundaries.** Zhang, Liao & Bellamy measured no significant improvement in
  AI-assisted accuracy from either confidence displays or explanations, and attributed it to
  the AI being uncertain exactly where the human was weak. [cited] If the checks fail on the
  same artefacts the reviewer fails on, calibrating the reviewer buys nothing, and a β
  measured against that reviewer understates the true false-accept rate. [asserted]
- **Completion is not comprehension.** Prather et al. report 20 of 21 novices completing the
  problem while the struggling subgroup finished believing they had done better than they
  had. [cited] A green verifier is the same class of completion signal: it can be correct
  about the artefact and complicit in a false sense of competence. [asserted]
- **In-session and unaided performance move in opposite directions.** Bastani et al. measured
  assisted practice performance up ~48% while unaided exam performance fell 17%. [cited]
  Every signal a harness collects during a session — tests passing, time to green, task
  completed — would have scored that arm a win. [asserted]

**Consequence for the programme.** β as defined is `P(automated checks accept | artefact
bad)`, with *bad* supplied by the human verdict. The above says that verdict is itself
error-prone, non-independent of the checks, and degrades under the very assistance being
measured. β is therefore a *lower bound on a joint error*, not a measurement of the checks
alone, and the repository should say so. [asserted]

## 2. The β-drift hypothesis

Three independent lines converge, from different populations and different decades. [cited]

- **The capability that degrades most is the one β depends on.** Shen & Tamkin found the
  largest AI-versus-control subscore gap on *debugging* questions and the smallest on code
  reading, because the control group resolved more errors unaided. [cited] The deficit was
  d=0.738 (p=0.010) with no significant completion-time gain (p=0.391). [cited]
- **Expert deskilling is measurable in months, in professionals with thousands of prior
  repetitions.** Budzyń et al. measured adenoma detection on standard non-AI colonoscopy
  falling from 28.4% to 22.4%, −6.0 points (95% CI −10.5 to −1.6, p=0.0089). [cited]
  Observational, so not causal — but the population was the one everybody assumes is immune.
  [asserted]
- **Earned trust reduces scrutiny.** Lee et al. found higher confidence in the AI associated
  with less critical engagement at b=−0.69 log-odds (p<0.001), the strongest effect in their
  model. [cited]

> **Hypothesis (falsifiable, and apparently unmeasured).** For a fixed repository, task family
> and verifier contract, β measured against a human verdict **rises over months of sustained
> assisted work**, because the reviewer's unaided error-detection ability decays while the
> checks stay fixed. [asserted]

This is a genuine candidate contribution. The self-improving-agent literature validates
modifications against a benchmark and does not measure whether the benchmark can be trusted
(`../20-design/living-system.md`); this adds that the *human* half of the acceptance signal
is not stationary either. [asserted] It is registered as EXP-32 rather than asserted here.

**What would kill it.** Kazemitabaar et al. found no retention harm at one week when AI was
confined to authoring tasks with manual modification always following, and high-prior-
competency learners did *better* with AI. [cited] Harm looks like a property of workflow
design, not of assistance as such — which is good news for a harness and fatal to any claim
that assistance is inherently corrosive. [asserted]

## 3. Self-report is a broken sensor here

- **METR:** experienced open-source developers on real issues in their own mature
  repositories were **19% slower** with early-2025 AI, and reported a **20% speedup** — a
  ~39-point sign error by experts about their own just-completed work. [cited] ML experts
  forecast +38% and economists +39%. [cited] Design intuition about where AI helps is not
  evidence, including this programme's. [asserted]
- **METR's own 2026 follow-up dissolves rather than confirms the headline:** +18% and +4%
  with confidence intervals crossing zero, its signal called unreliable, and 30–50% of
  developers withholding tasks they did not want to do without AI. [cited] A programme that
  measures gain must assume its subjects will refuse the control condition. [asserted]
- **Self-efficacy is not established.** Noy & Zhang's effect is +0.20 SD, p=0.060, 95% CI
  [−0.02, 0.42]. [cited] The interval includes zero and the repository must not cite it as a
  result. [asserted] Their job-satisfaction gain was a single item about a short writing task,
  with no difference in real job satisfaction after two weeks. [cited]
- **Satisfaction is anti-correlated with quality via a measured mechanism.** Cheng et al.
  measured sycophantic responses cutting conflict-repair intent by 28% and raising
  self-perceived rightness by 62%, while the *same* responses were rated 9% higher quality and
  13% more likely to be reused. [cited] Reporting Joe's outcomes separately is necessary but
  not sufficient: a rising satisfaction score is evidence to investigate, not evidence of
  gain. [asserted]
- **Self-reported trust does not predict behaviour.** Schimmelpfennig et al. (N=3,500, 10
  countries) got a clean anthropomorphism effect (β=0.386, p<0.001) beside a flat null on an
  incentivised trust game (p=0.97), with self-reported trust rising in Brazil and falling in
  Japan. [cited] Raees & Papangelis conclude across 22 studies that trust measurements do not
  inform appropriate reliance. [cited]

## 4. The counterfactual problem, which is a product problem

- **Marginal value collapses over an existing AI workflow.** Repositories adopting agents
  having already used AI IDEs gained +3.1% commits and −6.3% lines. [cited] The realistic
  counterfactual for a meta-harness is not "no AI" but "Claude Code as it ships". [asserted]
- **Velocity gains decay; quality costs do not.** Over 401 agent-first repositories, volume
  gains were front-loaded and faded while static-analysis warnings (+~18%) and cognitive
  complexity (+~39%) stayed elevated for six months — and the complexity rise appeared in
  IDE-first repositories that got essentially no velocity gain. [cited] Some populations pay
  the quality cost and receive no speed. [asserted]
- **The sign of the measured effect is set by task selection, not by the tool.** Greenfield
  toy task +55.8%; enterprise task counts +26.08% (n=4,867); synthetic enterprise task ~21%
  but p=.086 with a CI crossing zero; real issues on the developer's own mature repo −19%.
  [cited] A harness that evaluates itself on curated tasks will reproduce the +55% regime and
  learn nothing about the −19% regime, which is the one this project's users live in.
  [asserted] This is independent support for ADR-0013, evaluate on repository history rather
  than benchmarks. [asserted]
- **The cleanest metric in the literature does not survive this product.** METR states that
  time-spent measurement becomes unreliable for developers running multiple agents
  concurrently. [cited] That is Consilience's own design point, so wall-clock-per-task cannot
  be the primary outcome. [asserted]

## 5. What a CLI harness can actually measure

Ranked by value per unit of friction, from the readers' feasibility assessments. [cited]

| Instrument | Why it survives | Cost |
|---|---|---|
| Accepted-vs-discarded hunks, edit distance between proposed and merged diff, time from completion to accept | Fully behavioural, native to git and the transcript, no participant compliance. Measures *scrutiny*, not truth — an input to β, not β. [cited] | Free |
| Time-on-diff before approval, with an idle filter | Sub-second approval of a large diff is an unambiguous complacency signal. [cited] | Free |
| Survival of agent-authored lines in git history | Retrospective, zero burden. Churn is not wrongness; needs a within-repo human-authored baseline. [cited] | Free |
| Scripted-pushback flip rate on cases already known correct | The one place a coding harness beats a lab: the oracle already exists. Must hold the rebuttal's informational content constant and vary only tone. [cited] | One model turn |
| Predicted-minutes at start, felt-speedup at end | Produces a falsifiable residual against measured time, unlike a satisfaction score. Sample it; a harness that nags gets switched off. [cited] | Two prompts, sampled |
| Interaction-pattern signals from the transcript | The paper that found them used video; a harness gets them free. Cluster sizes were n=2–7, so this is a hypothesis to test, not a scoring function to ship. [cited] | Free |

**Explicitly rejected as instruments.** Self-reported trust scales, satisfaction scores,
thumbs-up, "did that help?", model-surfaced uncertainty, and any composite of the above.
Uncertainty highlighting reduced over-reliance only by increasing under-reliance, lowered
perceived accuracy across every category, and produced the largest confidence increases
precisely when participants chose wrongly. [cited] Token-probability surfacing is not a
calibration mechanism. [asserted]

**Explanations are an acceptance amplifier until proven otherwise.** LIME explanations raised
relative AI reliance from 29.59% to 38.87% (p=.05) while relative self-reliance stayed flat
(71.87% → 69.45%, p=.54). [cited] Any harness feature that shows its reasoning should be
assumed to raise acceptance, and therefore β, until measured. [asserted]

## 6. What cannot be measured, and should stop being promised

- **Appropriate-reliance metrics need a pre-commitment step.** RAIR and RSR require the
  human's independent answer *before* seeing the agent's, plus ground truth. [cited] Neither
  is normally observable in an agentic workflow; obtaining them means a cognitive forcing
  function, which Buçinca et al. show users find harder, prefer less and trust less, with the
  benefit accruing disproportionately to high Need-for-Cognition participants. [cited] Viable
  only as a sampled opt-in probe, never as always-on telemetry. [asserted]
- **Under-reliance is unmeasurable without silently evaluating rejected candidates**, which
  costs compute and raises a consent question. [cited] Until then every intervention will look
  better than it is. [asserted]
- **Unaided capability cannot be measured by a harness that cannot enforce "no AI".**
  25–35% of participants cheated when merely asked not to. [cited] The only version that
  survives contact is real work done assistant-off, not a test. [asserted]
- **Sycophancy is not yet a metric.** Expert agreement that it matters is 94.3% with
  individual-rater reliability ICC2=.184, and SycEval and ELEPHANT produce *inverted* model
  rankings. [cited] Committing to one benchmark would bake in a choice another reverses.
  [asserted]

## 7. Two things this changes elsewhere in the repository

- **ADR-0002 and the β definition.** β should be stated as conditional on a human verdict
  that is itself a fallible, non-independent and non-stationary test. This is a clarification
  of scope, not a change of decision, and belongs in ADR-0002's evidence section when someone
  next opens it. [asserted]
- **Working principle 5.** "Self-reported model confidence is not a signal" should be read as
  the special case of a wider rule: *no self-report is an acceptance signal, including the
  human's.* [cited] METR is the measured case for the human half. [asserted]

## Evidence against this synthesis

- Almost none of it is about code. Of the strongest results here, Zhang, Vasconcelos, Buçinca,
  Bo, Cheng, Schimmelpfennig and Ibrahim used no code and no artefact with an automated
  oracle. [measured] "A warm agent gets more bad diffs accepted" remains an inference across
  two population gaps, not a finding. [asserted]
- The coding-specific results are small. Perry et al. is n=47, mostly students, on
  codex-davinci-002. [cited] Shen & Tamkin is one randomised study. [cited]
- The deskilling result has a clean counterexample in Kazemitabaar et al., and the strongest
  deskilling evidence (Budzyń) is observational. [cited]
- The generation effect cannot carry the mechanistic argument: Bertsch et al.'s d=.40 is
  memory for word lists in undergraduates, and there is no meta-analytic evidence of a
  comparable advantage in programming. [cited] Citing it as warrant for "make the human write
  it" would be exactly the laundering `AGENTS.md` forbids. [asserted]
- The warmth→error result may not apply to the deployment path: Ibrahim et al. obtained
  7.43 points of average error increase from *fine-tuning* for warmth, and explicitly reported
  system-prompt-only warmth as weaker and less consistent. [cited] Every CLI coding agent sets
  manner by system prompt, i.e. the weak condition. [asserted]
- Widely circulated developer-wellbeing percentages — "60–75% report AI fatigue", "67% spend
  more time debugging AI code" — trace to vendor reports. [measured] They are `[2ND]`, are
  named here only so nobody re-imports them, and may never appear as measured facts. [asserted]
- No study here uses a validated burnout instrument on AI-assisted developers. The largest
  (n=442, PLS-SEM) built its own four-item construct and used a single item for AI perception.
  [cited] "AI reduces developer burnout" rests on one non-validated cross-sectional path
  coefficient. [asserted]

## Publication disposition

**Research-note candidate now; paper candidate only if EXP-32 fires.** [asserted] The
synthesis itself is a literature review and clears no gate on its own. [asserted] The β-drift
hypothesis is novel as far as these eight independent searches reached, is falsifiable, and
has an obvious experiment; if measured it would bear on the whole self-improving-agent
literature rather than on this product. [asserted] G2 requires a documented novelty search
including near misses before any such claim is made. [asserted]
