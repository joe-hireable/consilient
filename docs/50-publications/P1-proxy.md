---
title: "Mining verifier false-accept rates from repository history: a method, two disagreeing oracles, and missing human ground truth"
author: "Joe Brown"
date: "20 August 2026"
status: "DRAFT — not submitted, not published, not transmitted. Drafting artefact only."
venue-target: "Research note; pilot motivation for an EXP-44 MSR 2027 Registered Report (Stage 1) → EMSE"
---

# Mining verifier false-accept rates from repository history: a method, two disagreeing oracles, and missing human ground truth

**Joe Brown** (sole and accountable author)

> **Status.** This is an internal draft. Nothing here has been submitted, published or
> transmitted. The "AI assistance" section discloses how the draft was produced.

---

## Abstract

Automated checks have α = P(reject | good artefact) and β = P(accept | bad artefact). We apply
retrospective estimators to 356 merged pull requests. [measured]

**This is a method plus negative results, not a β measurement.** History mining refutes the
assumed α = 0.03 and finds no revert signal, change-size bias and a no-verdict state counted as
rejection. Two blind metadata adjudications put corrected-label β in the **cross-combination
sensitivity range [0.81, 0.93]**. Their 16-label disagreement makes the spread 14× wider than
reported; only the sign — above 0.6305 — is robust. [measured]

A mechanically different later-test replay returns pilot 0/15 = 0.0 [0.0, 0.2039] and primary
0/50 = 0.0 [0.0, 0.0713] (Wilson 95%), disjoint yet *inconclusive*. A parent control prevents
five drifted pairs yielding a counterfactual naïve β = 1.0. The primary samples chronological
merges against one subsystem; only 15.4% of repository merges touch it, so the zero may measure
uncoupling. [measured] [asserted]

The worst limitation: **the human-ground-truth fallback was unavailable.** The sole maintainer
could not adjudicate entirely AI-orchestrated changes; no contemporaneous verdicts exist.
[measured] (first-party) We display a diagnostic bracket and never pool. [asserted]

We hypothesise that ground truth becomes unavailable as **agent-authored** commits rise, and we
state that scope deliberately rather than claiming the broader one. A five-repository check
across 293,846 commits found declared AI authorship **≤0.03% throughout 2023–2024** while
behavioural indicators shifted markedly over the same window, then **13–61% in 2025–2026**,
driven by agent trailer insertion rather than IDE assistance. [measured] **Declaration therefore
measures autonomous agent authorship, not AI adoption**, so the general claim is not testable by
this instrument and we do not make it. EXP-44 registers the narrowed, unrun test; a dated search
found no direct prior study. [cited] [asserted]

---

## 1. Introduction

Cascade architectures, verification-gated agent loops and automated harness search all rest
on the same unstated premise: that when the checks go green, the artefact is good. That
premise is a claim about a conditional probability — β = P(checks accept | artefact bad) —
and it is almost never measured for the repository it is being applied to. Instead it is
assumed, or borrowed from a benchmark, or replaced by a proxy such as test coverage.

This paper asks a narrow, empirical question: **can β be estimated from the history a
repository already has?** Merged pull requests carry the CI status rollup recorded at merge
and, via a proxy, a putative label for eventual quality. Cross-tabulating the two gives a 2×2;
forward test replay supplies a second oracle from executable behaviour rather than metadata.

The answer is: *α can be estimated against the proxy; β remains oracle-conditioned; and the
absence of a human ground truth with which to settle the disagreement is the larger result.*
[measured] for these corpora; [asserted] beyond them.

### 1.1 Contributions

1. **A method and released instruments** (Appendix A) that print the whole contingency table,
   adjudicate its cells and replay later tests with a parent control. [measured]
2. **A corrected-label sensitivity result whose apparent precision fails its own control.**
   Across all cross-combinations of two blind metadata adjudications, β lies in [0.81, 0.93].
   The two reported ratios appeared 0.0085 apart despite a 16-label disagreement because
   numerator and denominator changes compensated. [measured]
3. **A mechanically different oracle that diverges.** Forward replay moves from pilot
   0/15 [0.0, 0.2039] to primary 0/50 [0.0, 0.0713], but only 15.4% of repository merges touch
   the tested subsystem. A parent control prevents a counterfactual naïve β = 1.0 on five
   drifted monolithic-suite pairs. [measured]
4. **A missing ground truth, and a registered test of the generalisation.** The sole
   maintainer reports that the human audit cannot be supplied because the corpus was entirely
   AI-orchestrated. [measured] (first-party) EXP-44 is registered and unrun; it tests the
   hypothesis that defect-proxy reliability degrades with AI-authorship share. [asserted]
5. **A measured α and three measured proxy failures.** α = 0.2371 [0.1635, 0.3307] and
   0.1429 [0.0570, 0.3149], refuting the assumed 0.03. The revert arm is absent, the hotfix arm
   is differentially biased by change size, and a no-verdict CI state counted as a rejection
   moves α and β in opposite directions. [measured]
6. **Two structural negative results.** Retrospective merge-mining cannot supply the
   prospective denominator because every selected row is a human accept; and the original
   output transposed β as P(bad | green). [measured]

### 1.2 What this paper does not claim

It does not claim that proxy-label noise is new; that is established at larger scale in the
SZZ and defect-prediction literature (§2.2). It does not claim a first measurement of verifier
false accepts on agent-produced artefacts; SWE-Bench+ reports 31.08% of passed patches as
suspicious (§2.7). It does not claim that either oracle has measured *the* β: one conditions on
metadata-adjudicated proxy labels; the other samples chronological merges but can expose only
failures covered by a compatible later test suite.
It does not claim that human ground truth has disappeared generally. That is the registered,
unrun EXP-44 hypothesis. The measured corpus remains two private repositories maintained by
one developer, who reports that the analysed changes were entirely AI-orchestrated. [measured]
(first-party)

---

## 2. Background and related work

### 2.1 The estimand

For a gate that admits an artefact when a check suite passes, the two error rates are the
consumer's and producer's risk of acceptance sampling (Neyman & Pearson, 1933) [SNIP]:
β = P(accept | bad) is the consumer's risk, α = P(reject | good) the producer's. In the
agentic-coding setting β is exactly one minus the check suite's recall against the fault
distribution the agent actually emits, and it is the quantity a cascade needs in order to
know whether cheap-first routing is safe.

The design this work supports derives a threshold β\* = (1 − α)·e^(−kΔ) from a logistic
(Rasch/1PL) competence model, with Δ the capability gap between the cheap and frontier
model [algebra, on an assumed functional form]. The only structural feature we use here is
that **β\* is linear in (1 − α)**, so an error in α rescales every threshold by a constant.
Neither k nor the competence model is measured; nothing in this paper depends on them beyond
that linearity.

### 2.2 SZZ, proxy labels, and why the noise is not our finding

Our label proxy — a later "fix"-titled pull request whose changed files intersect an earlier
one, within a window — is a close relative of SZZ. That literature has already established,
at greater scale, the results that would otherwise look like our contribution:

- Only about half the bug-fixing commits SZZ identifies are actually bug-fixing; with a
  six-month window, one file is incorrectly labelled defective for every file correctly
  labelled, and two defective files are missed for every one found (Herbold, Trautsch,
  Trautsch & Ledel, EMSE / arXiv:1911.08938) [ABS].
- Mislabelling is **not random**, and models trained on noisy labels achieve only 56–68% of
  clean-data recall (Tantithamthavorn et al., ICSE 2015; Herzig, Just & Zeller, ICSE 2013)
  [SNIP].
- Bug-fix links are a biased sample of fixed bugs, because developers do not always record
  them — *linkage bias* (Bird et al., FSE 2009; Bachmann et al., FSE 2010) [SNIP]. Our
  finding that a fix-forward repository yields no revert labels at all (§4.5) is linkage
  bias restated for a modern workflow.
- Large and bulk commits are a known source of SZZ false positives, which is why
  implementations routinely filter commits above a file or line threshold (Rezk, Kamei &
  McIntosh, TSE 2021; Rosa et al., arXiv:2102.03300) [SNIP]. Our 2.6×–3.0× size ratio
  (§4.6) is that effect, localised to a cell of our table.
- SZZ variants defined over pull requests exist (PR-SZZ, arXiv:2206.09967; "SZZ in the Time
  of Pull Requests", arXiv:2209.03311) [SNIP], as do LLM-assisted variants claiming
  state-of-the-art link recovery (LLM4SZZ, arXiv:2504.01404; AgentSZZ, arXiv:2604.02665)
  [SNIP]. **A reviewer will ask why we hand-rolled a regex-plus-overlap heuristic instead of
   using one of these. The honest answer is that we did not know they existed**; a public
   replication should compare the heuristic with PR-SZZ directly (§8).

What is different is the **use**. That literature studies proxy-label noise as a threat to a
*trained predictor*, where noise degrades recall. We use the labels to estimate the
verifier's own conditional error rate, where the same noise biases the estimand — and, as
§4.6 shows, biases it *differently in different cells of the 2×2*. That is differential
misclassification, a named phenomenon in epidemiology, and naming it is preferable to
letting a reviewer supply the name.

### 2.3 Correcting a rate for an imperfect labeller

The correction applied to the raw rates in the source record — raw counts multiplied by
audited precision and miss rates — is a hand-rolled special case of the Rogan–Gladen (1978)
estimator, π̂ = (p_obs + Sp − 1)/(Se + Sp − 1), which has corrected observed prevalences for
imperfect test sensitivity and specificity for nearly fifty years [SNIP]. Two consequences
follow and we accept both. First, the correction is not novel. Second, and more seriously,
**the published intervals on those corrected rates are wrong**: they propagate Wilson bounds
on the *raw* counts and do not account for uncertainty in the correction factors themselves,
which were estimated from n = 15 and n = 5. The known undercoverage of naïve Rogan–Gladen
intervals, and the Bayesian alternatives that address it, apply directly. We therefore
report corrected figures only as they exist in the record, with their axis stated, and do
not build on them.

### 2.4 "Can this check fail?" — vacuity, mutation, oracle assessment

The question of whether a passing check is informative is old. *Vacuity* names a check that
passes for a reason that makes it uninformative (Beer, Ben-David, Eisner & Rodeh, CAV 1997;
Kupferman & Vardi) [SNIP]. Mutation testing has measured whether a suite can detect
injected faults since 1978, and already fails builds on the result (PIT `mutationThreshold`,
Stryker `thresholds.break`) [WEB]. OASIs assesses oracle false negatives specifically and
reports a 48.6% average increase in fault detection after improvement (Jahangirova, Clark,
Harman & Tonella, ISSTA 2016) [SNIP]; checked coverage is a cheaper indicator of the same
property (Schuler & Zeller, ICST 2011) [SNIP].

This matters for positioning. Mutation testing already measures a per-repository, label-free
false-negative rate. The residual empirical question — and it is the only one that justifies
history mining over an off-the-shelf mutation tool — is whether **a check suite's
false-negative rate against the faults an LLM agent actually emits differs from its rate
against synthetic mutants.** That question is not answered here, and its cheapest test (run
a mutation tool per check on the same repository and compare the ordering) has not been run.
We state that as an open weakness, not a defence.

### 2.5 Flaky tests, and where α belongs

α — the rate at which a good artefact is rejected — sits inside a large flaky-test
literature we had not cited before this work. Roughly 25% of failures in Microsoft's
large-scale CI are attributed to flakiness and ~16% of Google's tests show some flakiness
(widely reported; traced here only to secondary sources) [2ND]; there is dedicated work on
discerning flaky from fault-triggering failures in Chromium CI (arXiv:2302.10594) [SNIP].
Note that the conditionals differ: that literature's quantity is P(flaky | failure); ours is
α = P(reject | good). They must not be quoted interchangeably. Our α is honest and it moves
every threshold in the design it feeds, but **it is not novel** — the flaky-test literature
owns it.

### 2.6 CI mining data quality

Mining CI outcomes has known hazards: build status is standardly partitioned into
passed/failed/errored/**cancelled**; developers re-run builds so a later result overrides an
earlier one; force-pushes corrupt build linearisation (TravisTorrent, MSR 2017, and the
threats sections of the literature derived from it) [SNIP]. The *hazard* is known. We could
find no paper quantifying what conflating a no-verdict state with a rejection does to an
*estimated verifier error rate*, which is the small residual our §4.7 occupies. There is
also a live practitioner-reported form of the same conflation in GitHub branch protection,
where a required check that is skipped is not reported as failing and the pull request
remains mergeable (github/community discussions; actions/runner #2566) [WEB, practitioner
sources only].

### 2.7 Verifier weakness on agent-emitted artefacts

β has already been measured on the benchmark the field grades itself against: SWE-Bench+
reports 31.08% of passed patches as suspicious because the tests were too weak, 32.67%
involving solution leakage, and a drop from 12.47% to 3.97% for one agent after correcting
both (arXiv:2410.06992) [ABS]. Independent work reports maintainer merge rates averaging
24.2 percentage points below automated grader scores for the same pull requests (Meng et
al.) [FULL]. Verifier weakness for coding agents is a crowded 2026 area with
better-resourced numbers than we can produce. **We claim per-repository and per-check-class
estimation, never a first measurement of verifier false accepts on agent output.**

A 2026 literature on agent-authored pull requests on public GitHub now exists at far larger
scale, including a dedicated MSR 2026 Mining Challenge with measured per-agent corrective
rates [SNIP]. This is simultaneously the strongest threat to our external validity and the
clearest repair: the same instruments run on a public agentic-PR corpus would fix external
validity, reproducibility and artefact availability at once (§8).

### 2.8 AI authorship and the ground-truth assumption

Recent work argues that software-measurement constructs fracture when development traces no
longer represent human effort or intent (Vasilescu et al., ASE 2026 NIER) [FULL]. Public
agent-PR datasets record tool identities and merge outcomes but do not supply causal
bug-introducing links or maintainer defect audits (AIDev / MSR 2026 Mining Challenge) [ABS].
The closest large agent census we found applies a temporal file-adjacency SZZ proxy to agent
commits; it assumes rather than tests whether that proxy remains valid as AI authorship rises
(arXiv:2606.24429) [ABS]. [cited]

Our literature search completed 20 August 2026 found no study directly evaluating defect-proxy
or SZZ reliability as a function of AI-authorship share. This was a documented near-miss search,
not a systematic review: no database/query/screening protocol was retained. EXP-44 registers a
longitudinal public-corpus test of that interaction and is unrun. [cited] [asserted]

### 2.9 What is left

One sentence, written to be conceded by a hostile reviewer:

> The SZZ and defect-prediction literature studies proxy-label noise as a threat to a trained
> predictor, where it degrades recall; we report what the same noise does when the labels are
> instead used to estimate a verifier's own conditional error rate, where it biases the
> estimand differentially by cell of the 2×2; on these corpora, metadata adjudication and
> later-test replay then disagree, and neither supplies the missing human ground truth needed
> to name its conditioned result *the* β.

---

## 3. Method

### 3.1 Corpora

Two private commercial repositories, referred to by name only: `jobboard-v2` (300 merged
pull requests analysed; 1,511 commits in full history as of 20 August 2026) and
`hireable-platform` (56 merged pull requests; 995 commits). Both are maintained by one
developer, who reports that the analysed pull requests and commits were entirely
AI-orchestrated. [measured] (first-party) `jobboard-v2` is the strongly-verified corpus (on the
order of twenty CI ratchets, dozens of invariant probes and coverage floors);
`hireable-platform` is the weakly-verified contrast. No code, file content, path, check
name, pull-request title or commit message from either repository appears in this paper;
only aggregate counts and coarse classes. This is a hard constraint, not a courtesy, and it
is also the paper's most serious reproducibility limitation (§7.3).

**A sampling bias worth naming immediately:** the strongly-verified repository was selected
as a nominally low-β case, which is the exact regime in which cascading looks best. Measuring
there flatters the thesis the measurement exists to test. [asserted]

### 3.2 The verifier and its recorded decision

The verifier is the CI suite as GitHub recorded it. For each merged pull request we fetch
`statusCheckRollup` and reduce it to a ternary:

```
green  iff every check conclusion ∈ {SUCCESS, NEUTRAL, SKIPPED, None}
none   iff the rollup is empty
red    otherwise
```

Three properties of this definition are load-bearing and all three turn out to matter.
`CANCELLED`, `STALE` and `TIMED_OUT` fall through to `red` (§4.7). The rollup was collapsed
to the ternary and **per-check identities were discarded**, so "was this red meaningful?"
was unanswerable from the stored records until a separate re-fetch (§4.8). And the rollup
reflects only what GitHub recorded: any check the developer ran locally before pushing is a
verifier whose decisions left no artefact at all (§7.4).

### 3.3 The label proxy

A merged pull request is labelled **bad** if either arm fires:

- **revert (strong):** a later commit subject matching `/revert/i` that also contains
  `#<PR-number>` or the first 8 characters of the merge SHA;
- **hotfix (weak):** a later pull request merged within 14 days whose title matches
  `\b(fix|hotfix|bug|regress|revert|broke|repair)\b` and whose changed file set intersects
  this one's.

Otherwise it is **good** (it survived the window untouched). The window and the regex are
the instrument's only tunable parameters; both are at their defaults.

### 3.4 Estimands

Read off one contingency table over one set of records:

| | verifier accepts (green) | verifier rejects (red) |
|---|---|---|
| artefact bad | **false accept** | true reject |
| artefact good | true accept | **false reject** |

- **β = P(green | bad)** = (bad ∧ green) / bad — the consumer's risk, the quantity of
  interest;
- **α = P(red | good)** = (good ∧ red) / good;
- **P(bad | green)** — the transpose, reported under its own name because an earlier version
  of this work published it *as* β (§4.4).

All intervals are Wilson score intervals at 95%. Wilson is used rather than Wald because
several cells are small and one is zero.

**The axis matters and it nearly did not get caught.** On `jobboard-v2` the marginals 202 and
203 nearly coincide, so β = 128/203 = 0.6305 and P(bad | green) = 128/202 = 0.6337 agree to
0.49%; on `hireable-platform` the same two quantities are 0.8571 and 0.4286, a factor of
1.91. A transposed conditional can survive review indefinitely on a corpus where the
marginals happen to match. The structural fix is not vigilance: it is to make the
instrument print the entire table so that no conditional is ever read off a remembered
marginal.

### 3.5 The treatment of unrun checks, stated in the same sentence as every number

`hireable-platform` has 7 pull requests with no recorded checks (1 bad, 6 good). The
verifier neither accepted nor rejected them. Three treatments are internally coherent and
they answer different questions:

| treatment | β (`hireable`) | α (`hireable`) | question answered |
|---|---|---|---|
| **A. exclude unrun rows** | 18/21 = 0.8571 | 4/28 = 0.1429 | when the verifier ran, how often was it wrong? |
| **B. retain, count as neither** | 18/22 = 0.8182 | 4/34 = 0.1176 | over all merged work, how often did the verifier err? |
| **C. retain, count unrun as a miss** | 18/22 = 0.8182 | 10/34 = 0.2941 | how often did nothing stop a bad artefact? |

We report **A** as primary, because β\* models the error rate of a verifier that ran.
`jobboard-v2` has no unrun rows, so its figures are identical under all three. The failure
mode this table exists to prevent is *asymmetry*: taking β from one treatment and α from
another means the two rates describe different worlds. Three unlabelled values for
`hireable` α circulated in the source record before the treatments were named, which is the
whole reason this subsection exists.

### 3.6 Protocol: the miner was deliberately not amended

`mine_beta.py` has never been amended. It still prints only the single transposed ratio,
still classifies `CANCELLED` as red, and still discards per-check identities. Every
correction in §4 lives in a separate read-only script that recomputes from the retained
per-PR records without touching the miner or its recorded outputs.

This is a deliberate protocol choice and we recommend it: repairing an instrument mid-run,
after seeing what it produced, is outcome-aware tampering. The cost is that the raw
recorded outputs and the current best estimates live in different files, and a reader must
be told which is which. That is the trade we took.

### 3.7 The label audit

40 labels were audited: 15 flagged bad-pairs plus 5 clean labels per repository, across two
repositories, one LLM judge per sampled label, verdicts recorded at abstract level only.
Three different denominators for this audit circulated in the source record (32, 40 and 30);
the retained sampling artefact says 40, and the 30 was a prospective protocol that was never
drawn. Results:

- **Hotfix-label precision: 1/15 ≈ 0.0667 on both repositories** (Wilson 95% [0.0119,
  0.2982]). The regex fires on conventional-commit `fix(...)` titles and the overlap fires on
  shared configuration and manifest files, so the proxy measured development velocity rather
  than defect escapes.
- **Clean-label miss rate: ~1/5 per repository** (n = 5 each; [0.0362, 0.6245]).

Two caveats travel with these and must not be dropped. The audit is LLM-judged, by the same
model family as the rest of the work — the labels and their audit are not an independent
class of evidence. And, decisively, **it was measured on the bad-and-green cell only** and
propagated to a denominator containing 75 unaudited bad-and-red pull requests whose size
profile is 2.6× different (§4.6).

### 3.8 Corrected-label adjudication and the cross-combination control

The 75 bad-and-red pull requests were subsequently adjudicated twice, blind, by different
model families from metadata only. Each adjudicator separately classified whether the bad
label was genuine and whether the recorded red was a meaningful rejection. [measured] For an
adjudication that refutes `r` bad labels and promotes `p` confirmed-bad but non-meaningful-red
rows into the numerator, the corrected conditional is

`β = (128 + p) / (203 − r)`.

The two adjudicators disagreed by 16 pull requests on how many bad labels were genuine while
their reported ratios appeared only 0.0085 apart. We therefore crossed each adjudicator's
promotion count with the other's refutation count. The resulting **sensitivity range is
[0.81, 0.93]**, width 0.1192, or 14× the apparent spread. [measured] It is not a confidence
interval and the within-family point pair is not reported: compensating numerator and
denominator judgements make those points look more stable than their inputs. No adjudicator
read a diff; unresolved verdicts remain; and this is model-adjudicated β, not human ground
truth. [measured]

### 3.9 The retro-verifier and its parent-commit control

The second oracle replays a later test suite against a historical child commit and its parent.
`parent PASS, child FAIL` is an attributable defect escape; `parent PASS, child PASS` is clean;
and a parent failure censors the pair as drift rather than attributing a failure the child did
not introduce. [asserted] method; [measured] implementation.

This is mechanically different evidence from title regexes, file overlap and CI metadata, but
only partially independent epistemically. It can detect only regressions that surfaced and later
received tests; latent defects remain invisible. Under this parent-control design, a new
component is also unevaluable when the parent lacks the symbols required by the later test.
[asserted] The parent control is not optional: §5 reports the maximally wrong result the pilot
would otherwise have produced.

The 15-pair pilot and 50-pair primary runs take chronological merge commits; they do not select
commits that touched the tested subsystem. Only 25 of 162 repository merges (15.4%) touched
that subsystem. [measured] A separate file-status proxy marks 123/162 (75.9%) as adding any
file and 118/162 (72.8%) as adding a code file. Those are not semantic greenfield labels: the
proxy has both false positives and false negatives, so the measured percentages indicate the
scale of the possible blindness but do not identify an evaluable fraction. [measured]
[asserted]

---

## 4. Results

All figures in this section were re-derived from the retained per-PR records on the day of
writing by running the released instruments, and reproduce the recorded values exactly
unless stated.

### 4.1 The contingency tables

**`jobboard-v2`, 300 merged pull requests** [measured]

| | CI green | CI red | no CI | verifier ran | total |
|---|---|---|---|---|---|
| **bad** | 128 | 75 | 0 | 203 | 203 |
| **good** | 74 | 23 | 0 | 97 | 97 |
| total | 202 | 98 | 0 | 300 | 300 |

**`hireable-platform`, 56 merged pull requests** [measured]

| | CI green | CI red | no CI | verifier ran | total |
|---|---|---|---|---|---|
| **bad** | 18 | 3 | 1 | 21 | 22 |
| **good** | 24 | 4 | 6 | 28 | 34 |
| total | 42 | 7 | 7 | 49 | 56 |

Every history-miner rate in §§4.1–4.9 is a ratio of these cells. Base rate P(bad) = 203/300 = 0.6767
[0.6218, 0.7271] and 21/49 = 0.4286 [0.3002, 0.5673] — high, and a direct consequence of the
proxy's precision (§3.7), not of the repositories being unusually broken.

**The human override rate.** 98 of 300 `jobboard-v2` merges (0.3267, [0.2761, 0.3816]) went
in over red CI; `hireable-platform`'s rate is 7/56 = 0.1250 [0.0619, 0.2363]. On these
repositories the *human*, not the CI, is the acceptance gate, and the checks are advisory.
This is both a finding in its own right and the structural precondition that makes β
identifiable at all: without those 98 rows there is no bad-and-red cell and no denominator
for P(accept | bad). It must not be confused with α — it is P(red | merged), selected on the
merge decision, and it mixes both red cells. That confusion happened once in the source
record and was withdrawn.

### 4.2 α is measured, and the assumed value is refuted

| corpus | α = P(red \| good) | Wilson 95% |
|---|---|---|
| `jobboard-v2` | **23/97 = 0.2371** | [0.1635, 0.3307] |
| `hireable-platform` (A) | **4/28 = 0.1429** | [0.0570, 0.3149] |
| `hireable-platform` (B) | 4/34 = 0.1176 | [0.0467, 0.2662] |
| `hireable-platform` (C) | 10/34 = 0.2941 | [0.1683, 0.4617] |

The design this work supports carried exactly one α anywhere: **0.03, and it was invented** —
a hard-coded constant in a simulation script, never measured, propagated into every
threshold. Every interval above excludes it, including the lowest bound of the weakest
treatment on the weakest corpus (0.0570). The assumed value is not imprecise; it is outside
the interval on both repositories under all three treatments.

The two point estimates differ by a factor of 1.66, but their intervals overlap
substantially: **these data do not establish that α differs between repositories.** They
establish that it is not 0.03. A per-verifier α needs a larger sample per verifier, not
this one.

α is measured *against the proxy labels* and therefore inherits exactly the label noise β
does, from the same single labelling pass. The two rates carry correlated noise.

### 4.3 What the correction does to a threshold of the form (1 − α)·f(x)

Because β\* = (1 − α)·e^(−kΔ) is linear in (1 − α), substituting a measured α rescales the
threshold by a constant at every capability gap [algebra]:

| α | β\* at Δ=0.17 | Δ=0.27 | Δ=0.42 | scale vs assumed |
|---|---|---|---|---|
| 0.03, assumed, invented | 0.2490 | 0.1119 | 0.0337 | 1.0000 |
| **0.2371 (`jobboard-v2`)** | **0.1958** | **0.0880** | **0.0265** | **0.7865** |
| 0.1429 (`hireable`, A) | 0.2200 | 0.0989 | 0.0298 | 0.8837 |
| 0.2941 (`hireable`, C) | 0.1812 | 0.0814 | 0.0245 | 0.7277 |

Propagating the `jobboard-v2` Wilson interval on α gives β\*(0.27) ∈ [0.0772, 0.0965] —
the entire interval below the assumed 0.1119.

**Every threshold derived from β\* was roughly 21% looser than it should have been, and the
error ran in the optimistic direction:** the system believed its verifiers were more reliable
than they are. This is tagged `[algebra]`, not `[measured]` — it is one linear rescaling of
an assumed model with one measured input. k and the logistic competence model remain
unmeasured assumptions, and nothing else in this paper depends on them.

### 4.4 β under raw and corrected proxy labels

| corpus | β = P(green \| bad) | Wilson 95% |
|---|---|---|
| `jobboard-v2` | 128/203 = 0.6305 | [0.5623, 0.6939] |
| `hireable-platform` (A) | 18/21 = 0.8571 | [0.6536, 0.9502] |
| `hireable-platform` (B/C) | 18/22 = 0.8182 | [0.6148, 0.9269] |

These are **raw proxy-label figures with no label correction applied**. The first label audit's
1/15 hotfix precision applies only to bad-and-green; it cannot be propagated across the 2×2
because the bad-and-red cell differs systematically (§4.6). [measured]

A correct-axis result now exists for the primary corpus. Two blind metadata adjudications of
all 75 bad-and-red rows, crossed as specified in §3.8, give corrected-label β in the
**sensitivity range [0.81, 0.93]**. [measured] This range is not a confidence interval. The
adjudicators differed by 16 pull requests on genuine bad labels, yet their reported ratios
were only 0.0085 apart; crossing the inputs yields a 0.1192 spread, 14× wider. Compensating
changes to numerator and denominator created the apparent agreement. The only
qualification-free result is the sign: every cross-combination is far above the recorded
0.6305. [measured]

The estimate remains metadata-only and model-adjudicated. No adjudicator read a diff, 10 and 5
bad-label verdicts respectively remain unclear, and the human-ground-truth fallback was
unavailable (§6). It is therefore not *the* β and is not decision-grade. [measured] [asserted]

For completeness, the transposed quantity is P(bad | green) = 128/202 = 0.6337 [0.5653,
0.6970] and 18/42 = 0.4286 [0.2912, 0.5779].

**Against the pre-registered prospective stopping rule, the recorded verdict for both
repositories remains "insufficient data — do not route cheap yet."** The metadata sensitivity
range does not manufacture the missing human-rejection denominator (§4.10) and does not turn
model adjudication into ground truth. [measured]

One further arithmetic fact, because it bears on whether any β estimate could clear the
threshold. The evidence floor in the corresponding meter is 30 rejections. A Wilson upper
bound on 0/30 is 0.11352 and on 0/31 is 0.11026, against β\*(0.27) = 0.1119 at the assumed
α. **At the floor as set, no outcome whatsoever — not even a flawless one — produces an
interval that clears the threshold**; 31 is the smallest n that can. The rejections needed at
each true β are 48 at 0.02, 62 at 0.04, 137 at 0.06, 368 at 0.08, 3,045 at 0.10, and never at
β ≥ 0.111 (searched to 200,000). This is not a defect — the floor gates a *measured* verdict,
not a routing decision — but it means the corrected-label sensitivity range, entirely above
β\* itself, describes a regime in which **no sample size clears the threshold at all.** That
is an algebraic result on model-adjudicated labels, not a routing decision. [algebra]

### 4.5 Failure mode 1 — the strong signal is absent, and the zero is a true negative

| corpus | bad PRs | labelled by revert | labelled by hotfix |
|---|---|---|---|
| `jobboard-v2` | 203 | **0** | 203 |
| `hireable-platform` | 22 | **0** | 22 |

**All 225 bad labels across both corpora come from the weak circumstantial arm. The revert
arm did not fire on a single pull request out of 356.**

A detector returning zero on 356 subjects has two readings — the repositories genuinely
never revert, or the detector is broken — and it deserves a positive control before either is
believed. We ran one:

| corpus | commits | subjects matching `/revert/i` | of those, carrying a `#<PR>` reference |
|---|---|---|---|
| `jobboard-v2` | 1,511 | **2** (0.0013, [0.0004, 0.0048]) | **0** |
| `hireable-platform` | 995 | **4** (0.0040, [0.0016, 0.0103]) | **0** |

Six revert-ish commits in 2,506 (0.0024, [0.0011, 0.0052]), and not one references a pull
request number — the detector's primary match path. **The zero is a true negative.** These
are fix-forward repositories.

That is the more useful answer and it is worse news than a defect would have been. A defect
can be fixed. This says the strong signal does not exist in this corpus at all, so β here is
not resting on the weak proxy through an implementation oversight — it has no alternative.
"Evaluate on repository history" therefore buys a weaker label than it appears to, and any
future β mined from a fix-forward repository inherits the same constraint.

Two notes on positioning. First, this is linkage bias (§2.2) restated for a modern workflow
— the concept is not ours. Second, what *is* worth keeping is methodological rather than
conceptual: the positive control was **run**, not recommended, and it converts an ambiguous
zero into a measured property of the corpus. That control is cheap, is rarely reported, and
is a paragraph rather than a paper.

### 4.6 Failure mode 2 — the proxy is differentially biased, and worst where β leans hardest

The hotfix rule's false-positive rate rises with the number of files a pull request touches,
because file-set overlap with some later "fix" gets easier the more files there are. A
100-file pull request overlaps almost anything.

| corpus | bad-and-green: median (mean) files | bad-and-red: median (mean) | ratio of medians |
|---|---|---|---|
| `jobboard-v2` | 5 (9.4) | **13 (26.7)** | **2.60** |
| `hireable-platform` | 2 (8.7) | **6 (22.3)** | **3.00** |

Same direction on both corpora. For contrast, the good-and-red cell on `jobboard-v2` — α's
entire numerator — has a median of 2 files (mean 4.1, max 16), which is what genuine flaky or
lint-only failures ought to look like.

**The bad-and-red cell is 75/203 = 0.3695 [0.3061, 0.4377] of β's denominator on
`jobboard-v2` (3/22 = 0.1364 [0.0475, 0.3334] on `hireable-platform`).** The original audit
covered bad-and-green only. The two later metadata adjudications cover all 75 primary-corpus
rows and refute 25 and 36 bad labels respectively — 33–48% — confirming that the first
cell's precision could not simply be propagated. [measured] The cross-combination correction
in §4.4 makes that disagreement explicit rather than selecting one adjudicator's point.

This is still not the pre-registered ground-truth audit. The human fallback proved unavailable
(§6), and no adjudicator read a diff. A diff-level audit of 20 of the 75 that disagrees
materially with both metadata adjudications would falsify the corrected-label method; it has
not been run. [asserted]

### 4.7 Failure mode 3 — a no-verdict state was counted as a rejection

`CANCELLED` is not in the green set, so a cancelled run — which produced no verdict at all —
counted as the verifier rejecting the artefact. This is precisely the error the code was
careful to avoid for pull requests with no checks, which it excluded as `none`. It arrived
through a conclusion value nobody enumerated.

| cell | n | failing only on cancelled runs |
|---|---|---|
| bad-and-red | 75 | **15 (20.0%)** |
| good-and-red | 23 | **3 (13.0%)** |

Moving them out of "red", because no decision was taken on them:

| | as recorded | cancelled excluded |
|---|---|---|
| β = P(green \| bad) | 128/203 = 0.6305 [0.5623, 0.6939] | **128/188 = 0.6809** [0.6112, 0.7433] |
| α = P(red \| good) | 23/97 = 0.2371 [0.1635, 0.3307] | **20/94 = 0.2128** [0.1422, 0.3059] |

**Both rates move, in opposite directions, from a single corrected classification.** β rises:
the checks accepted a larger share of the bad artefacts they actually ruled on. α falls:
fewer good artefacts were genuinely rejected. The optimistic reading of the verifier gets
worse while its flakiness gets better. α remains an order of magnitude above the assumed
0.03 under either treatment.

We believe this is the paper's one genuinely new empirical contribution, and it is small: the
CI-mining literature knows that cancelled is a distinct build state (§2.6), but we could find
no quantification of what conflating it with a rejection does to an *estimated verifier error
rate*. The direction is the interesting part. A single misclassification that inflates one
off-diagonal cell deflates the other, so it cannot be dismissed as conservative in either
direction.

This correction is **mechanical, not adjudicated.** It settles only the cancelled runs.
Whether a genuine `FAILURE` on any particular suite means the artefact was bad still requires
per-PR judgement.

### 4.8 What "red" actually meant: no failing check was a required gate

Per-check identities were re-fetched for 98 of 98 red `jobboard-v2` pull requests, giving 242
non-passing check instances (186 in bad-and-red, 56 in good-and-red; 201 `FAILURE`, 41
`CANCELLED`).

**All 242 carry `required = false`.** On this corpus, "CI red" never meant that a required
status check blocked the merge. This strengthens the override finding of §4.1 and weakens any
reading of red as a rejection at all. One caution travels with it: the `required` flag in the
rollup reflects branch-protection state *at fetch time*, not at merge time, so this is
evidence about the repository's configuration today.

We also re-examined a claim made in the source record that one end-to-end suite "accounts for
91% of bad-and-red failures against 52% of good-and-red", offered as evidence that red is
discriminating in the bad cell. Recomputed here, that suite is non-passing on 68/75 = 0.9067
[0.8197, 0.9541] of bad-and-red and 12/23 = 0.5217 [0.3296, 0.7076] of good-and-red **only
when cancelled runs are counted as failures** — the very conflation §4.7 corrects. Restricted
to genuine `FAILURE` conclusions, the same suite is failing on 34/75 = 0.4533 [0.3457,
0.5655] and 5/23 = 0.2174 [0.0966, 0.4190].

The absolute gap therefore narrows from 38.5 to 23.6 percentage points, while the *ratio*
rises from 1.74× to 2.09×. The claim survives in weakened form, with wide overlapping
intervals on a 23-PR cell. We report the corrected figures and note that any argument built
on the uncorrected ones is built on the error the same section identified.

A further class of failure in the same cell is nondeterministic by construction —
live-model evaluation suites — and one check reporting `FAILURE` is explicitly labelled
informational, i.e. non-blocking, and was counted as a rejection. No pull request, however,
failed *only* on informational checks, so this moves no pull request out of the red cell and
implies no further correction to α or β.

### 4.9 An independent adjudication of α's numerator

A second model family (a GPT-class model, distinct from the family that produced the labels
and the label audit) independently adjudicated all 23 good-and-red `jobboard-v2` pull
requests and judged **9 of 23** (0.3913, [0.2216, 0.5921]) to be non-meaningful reds. The 3
cancelled-only pull requests identified mechanically in §4.7 are a **strict subset** of those
9; the remaining 6 are non-blocking live-model suites and lint or CI-infrastructure failures.
Three further pull requests were flagged as boundary cases.

| treatment | k / n | α | Wilson 95% |
|---|---|---|---|
| raw proxy | 23/97 | 0.2371 | [0.1635, 0.3307] |
| cancelled-only removed, denominator reduced | 20/94 | 0.2128 | [0.1422, 0.3059] |
| 9 non-meaningful removed, denominator reduced | 14/88 | 0.1591 | [0.0972, 0.2495] |
| 9 non-meaningful removed, denominator retained | 14/97 | 0.1443 | [0.0880, 0.2278] |
| strictest (12 removed, denominator retained) | 11/97 | 0.1134 | [0.0645, 0.1917] |

**Under every candidate treatment the entire 95% interval lies above 0.03**; the lowest bound
across all of them, 0.0645, is more than twice the assumed value. The refutation of α = 0.03
does not depend on which adjudication is preferred.

We deliberately do **not** present this cross-family agreement as independent corroboration
in the sense the surrounding programme uses that word. The two arms shared the same primary
records and the same framing; a previous cross-family claim in this programme was withdrawn
after its own pre-registered same-family control fired, and we will not repeat that error
here. The adjudication is reported as a second opinion on one cell, with the arms' shared
evidence stated.

### 4.10 The structural negative result: retrospective mining cannot supply the prospective denominator

The prospective definition of β counts artefacts a human rejected and the checks had
accepted. The retrospective miner fetches with `--state merged`, so **every row is a human
accept**. The number of human rejections in the entire corpus is zero, and the corresponding
meter reports, verbatim, `beta [all]: insufficient data (0 human rejections, need 30)` — a
result reproduced on the day of writing.

Mining more history does not help. It adds accepts forever. Fixing the conditional does not
create a denominator that was never collected. The 2×2 above is a *different* estimator of
the same quantity, identified only because 98 pull requests were merged over red CI; that
override channel is what makes β identifiable at all here, and a repository with strict
branch protection would have no bad-and-red cell and therefore no retrospective β.

A second structural bias runs the other way and is worth stating because it defeats a
tempting claim. Where a verifier pre-filters the review queue, β̂ computed over what reaches a
human is biased toward 1.0 by construction: 50 bad diffs, the verifier catches 45, the human
sees 5 and rejects all 5 gives a reported 5/5 = 1.00 against a true 5/50 = 0.10. Two
unmeasured biases in opposite directions — human misses push β̂ down, pre-filtering pushes it
up — **do not compose into a bound in either direction.** Any implementation flagging such an
estimate as a lower bound on joint error is asserting a property the quantity does not have.

---

## 5. Two mechanically different oracles diverge

### 5.1 The result

| oracle | β | n | conditioning |
|---|---|---|---|
| revert-or-hotfix proxy, cross-family metadata adjudication | **[0.81, 0.93]** sensitivity range | 75 contested of 203 proxy-bad rows | title regex, file-set overlap, CI rollup and metadata adjudication |
| retro-verifier pilot, later subsystem tests with parent control | **0/15 = 0.0**, Wilson 95% **[0.0, 0.2039]** | 15 chronological parent-pass pairs | later subsystem suite; not selected for subsystem contact |
| retro-verifier primary, later subsystem tests with parent control | **0/50 = 0.0**, Wilson 95% **[0.0, 0.0713]** | 50 chronological parent-pass pairs | later subsystem suite; not selected for subsystem contact |

Neither retro-verifier Wilson interval intersects the proxy's cross-combination sensitivity
range. Both stopping verdicts nevertheless record *inconclusive*. The primary run narrows
binomial uncertainty for this chronological sample, but it does not repair the sample's domain
sparsity: only 25/162 repository merges touch the tested subsystem. [measured] The mechanisms
are a different class of facts — metadata association versus executable behaviour — but the
oracles still share a surfaced-defect channel because later fixes and regression tests are both
written for problems that became visible. [asserted]

### 5.2 Reconciliation without pooling

The metadata proxy over-includes putative defects: its strong revert arm fires zero times and
the two adjudications refute 33–48% of bad labels in the contested cell. [measured] This is a
specificity defect in the label set; it does **not**, by itself, establish the direction of bias
in conditional β. The retro-verifier under-samples by construction: latent defects without a
later regression test are invisible, and the parent control censors additions whose required
symbols do not exist in the parent. [asserted]

Both conditioned estimates may therefore be right on their own terms. We display a diagnostic
bracket — proxy [0.81, 0.93], retro 0.0 [0.0, 0.0713] — but **not** a statistical bound on a
single latent quantity and never a pooled number. [asserted] The
divergence is the difference-of-class test producing a negative result, not an inconvenience
to average away.

### 5.3 The parent control prevents a maximally wrong answer

All five historical commits in the monolithic arm failed 3–7 of the later suite's tests. A
naïve replay would therefore have labelled 5/5 as escaped defects and reported β = 1.0.
Their parents failed the same later suites, so the control classified all five pairs as drift;
that arm's measured drift rate is 100% and its stopping verdict is `rejected_high_drift`.
[measured] The β = 1.0 is a counterfactual naïve result, not an observed corpus estimate.

The control costs one extra checkout and test run per pair. Without it, a method paper would
have reported the maximally alarming answer from pure interface and suite drift. That control
is part of the method, not a robustness appendix. [asserted]

### 5.4 Falsifier

The original numerical falsifier was a larger subsystem-suite run whose Wilson interval
overlapped [0.81, 0.93]. The 50-pair run was completed and its interval did not overlap, so that
falsifier did not fire. [measured] It exposed a stronger selection objection instead: the
chronological sample was not selected for contact with the tested subsystem. A replay restricted
to merges that touched that subsystem, or spanning representative subsystem suites, whose
Wilson interval overlaps the proxy sensitivity range would falsify the structural-divergence
reconciliation. [asserted]

---

## 6. The human-ground-truth fallback was unavailable

### 6.1 The corpus fact

Asked to adjudicate contested labels from his own repositories, the sole maintainer stated:

> “Honestly I do not have the technical expertise to answer these questions because all of
> these PRs and commits were entirely AI orchestrated.” [measured] (first-party)

The stated remedy when EXP-01's proxy was doubted was human audit. On these corpora that
fallback was never available: no contemporaneous human artefact-level verdicts exist, and the
maintainer reports that he cannot reconstruct them now. The proposed human-ground-truth audit
was cancelled rather than converted into rubber-stamped answers. [measured] (first-party)

This distinction is load-bearing. The two model adjudications are authorised research data,
but they cannot be relabelled as human ground truth. The paper therefore retains their
provenance in the estimand's name: **model-adjudicated β**, not β. [asserted]

### 6.2 The larger claim is registered, not established

We hypothesise that as AI authorship rises, the human judgement on which historical
defect-proxy validation depends becomes unavailable rather than merely expensive. [asserted]
Our literature search completed 20 August 2026 found no study directly evaluating defect-proxy
or SZZ reliability as a function of AI-authorship share; the closest work either critiques SZZ
on human corpora, records agent provenance without defect ground truth, or applies an SZZ-like
proxy to agent commits without validating that proxy under AI authorship. [cited]

EXP-44 is the registered, unrun test: a longitudinal public-corpus comparison of proxy
reliability across authorship eras using developer-informed links, triaged bug reports and
retro-verification as separate oracles. [asserted] If precision is invariant to AI share within
the registered five-percentage-point band, the generalisation is refuted and this paper must
cut back to its corpus-specific finding. If the study cannot obtain enough unambiguous ground
truth, its verdict is *insufficient evidence*, not support. [asserted]

---

## 7. Threats to validity

Ordered worst first.

### 7.1 Human ground truth is unavailable (fatal for β)

The sole maintainer reports that he cannot adjudicate the contested artefacts because the
changes were entirely AI-orchestrated, and no contemporaneous human artefact-level verdicts
exist (§6). [measured] (first-party) The proxy can be model-adjudicated and the later tests can
be replayed, but neither operation recovers a missing human judgement. This is fatal to
presenting either conditioned estimate as *the* β. It is not evidence that the same problem
holds outside these corpora. [asserted]

### 7.2 Neither estimator observes the target population; the retro sample is domain-sparse

The history miner cannot supply its prospective denominator: because it selects merged pull
requests, every row is a human accept and there are no human rejections (§4.10). [measured]
The 50-pair primary sample comprises chronological, parent-pass merges; it was not selected for
contact with the tested subsystem, and only 25/162 merges in the repository's history touch that
subsystem. [measured] Its narrower interval may therefore describe subsystem uncoupling rather
than verifier reliability. [asserted] Separately, later tests can expose only regressions that
surfaced and received compatible tests; latent defects remain invisible. Under this
parent-control design, additions whose required symbols are absent from the parent are censored
as drift. [asserted]

The file-status proxy finds that 123/162 merges add any file and 118/162 add a code file, but it
has false positives and false negatives for semantic greenfield work and does not identify the
evaluable fraction. [measured] [asserted] The metadata oracle instead conditions on rows selected
by a title-and-overlap proxy. [measured] The results are disjoint, but neither population is
known to equal all bad artefacts. The bracket in §5 displays disagreement; it is not an
identified statistical bound. [asserted]

### 7.3 The corpus cannot be released, so nothing here is independently reproducible

Both repositories are private commercial code. Their per-PR records are gitignored and will
never be published. We release the instruments, aggregate contingency tables and current
50-pair retro-verifier result records. An independent party can audit the arithmetic and method
and re-derive that replay aggregate, but cannot reproduce the history-mined rates or rerun the
replay against its source history. That fails the data-availability expectations of the
technical tracks this work would otherwise target. [measured] The recommended route is a
registered report centred on public EXP-44, with these results as pilot motivation. [asserted]

### 7.4 The verifier we measured is not the verifier that operated

`statusCheckRollup` reflects only what GitHub recorded. On the primary corpus roughly forty
check scripts run locally, outside CI. Every accept or reject those made left no artefact.
The estimated verifier is therefore weaker than the acceptance process actually was, in an
unmeasured direction. Relatedly, §4.8 shows that no failing check in the corpus was a
*required* status check, so "red" here does not mean "blocked".

### 7.5 The labels are a close relative of SZZ and fail differently by cell

The initial bad-and-green audit measured hotfix-label precision at 1/15 ≈ 0.0667 [0.0119,
0.2982]. In bad-and-red, the later adjudicators refuted 25 and 36 of 75 labels and disagreed by
16 on how many were genuine. [measured] Those are different cells with different size
profiles, and neither audit read diffs. The [0.81, 0.93] range is therefore a sensitivity
analysis over model judgements, not a corrected ground-truth interval.

### 7.6 The adjudications share evidence

The initial labels, their first audit and most analysis came from one model family. The two
later families shared the same metadata and framing, and their apparent ratio agreement is
14× narrower than the disagreement exposed by crossing their inputs. [measured] That is a
second opinion, not corroboration. Retro-verification adds executable behaviour, but shares
the surfaced-defect channel through later test writing (§5.1). [asserted]

### 7.7 The proxy's window and regex are unvalidated hyperparameters

14 days and a seven-word regex. No sensitivity analysis over either was run. The window
governs the miss rate and the regex governs the false-positive rate, and both were set once
and never varied. PR-level SZZ implementations and LLM-assisted variants exist that would
have supplied better labels (§2.2) and were not used.

### 7.8 β\*'s functional form is assumed

k = 8, a logistic competence model, and the capability gaps in §4.3 are all unmeasured. Only
the linearity of β\* in (1 − α) is used, and only the *scale factor* and its *sign* should be
read from that table. The absolute β\* values are `[algebra]` on `[asserted]` inputs.

### 7.9 Multiple analyses on one dataset

Cancelled-run reclassification, size analysis, two adjudications and their cross-combination
control were performed on the same 356 records after the initial result was known, with no
multiplicity adjustment. [measured] Each was motivated by a named mechanism and §3.6 records
that the miner was not amended, but this is a defensive protocol, not pre-registration.

### 7.10 Numbers in the underlying record disagreed with each other

While preparing this paper we resolved seven conflicts in the source record: a transposed
axis; label corrections propagated across axes under the wrong name; three values for one α;
two unlabelled denominators for one β; a headline correction of "31% tighter" to "21%" that
left a stale document behind; two commit counts for one repository; and three denominators
for one audit. All are resolved above and all are recorded as corrections rather than quietly
fixed. A reader should conclude that this dataset was harder to keep straight than its size
suggests, and that **printing the whole contingency table is the only structural defence** we
found against reading a conditional off a remembered marginal. The later 14×
cross-combination spread adds an eighth warning: matching output ratios can conceal
incompatible inputs. [measured]

---

## 8. What a practitioner should do differently

Each follows from a measured failure or an explicitly labelled limitation above.

1. **Print the table, never the conditional.** The transposed-axis defect survived because
   two marginals happened to differ by one. An instrument that emits the full 2×2, both
   off-diagonals under their own names, and the transpose under *its* own name, cannot make
   that mistake. This is the single highest-value change and it is about twenty lines.
2. **Enumerate every conclusion value your verifier can emit, and decide the no-verdict class
   explicitly.** `CANCELLED`, `STALE`, `TIMED_OUT` and skipped-but-required are not
   rejections. Conflating them with rejections moved α and β in opposite directions here.
   Assert on unknown conclusion values rather than defaulting them into a class.
3. **State the treatment of unrun checks in the same sentence as the number.** Three coherent
   treatments give three different α on the same data. Never take α from one treatment and β
   from another.
4. **Run a positive control on any detector that returns zero.** Ours cost one `git log` and
   converted an ambiguous zero into a measured property of the corpus — the difference between
   "the instrument is broken" and "the signal does not exist here".
5. **Audit every cell you intend to correct, using evidence that does not simply repeat the
   proxy.** Precision measured in bad-and-green does not transfer to bad-and-red when the two
   differ 2.6× in size. Metadata adjudication exposes sensitivity; it does not create human
   or diff-level ground truth.
6. **Correct with a named estimator.** Raw counts × audited rates is Rogan–Gladen; use it
   under that name, and use an interval that accounts for uncertainty in the correction
   factors, not just in the raw counts.
7. **Do not amend the instrument mid-run.** Put corrections in separate read-only scripts that
   recompute from retained records, and tell the reader which file holds the recorded output
   and which holds the current best estimate.
8. **Check `required`.** If no failing check was a required gate, you are not measuring a
   gate. You are measuring an advisory signal that a human overrode a third of the time.
9. **Do not expect retrospective merge-mining to give you a prospective β.** Every merged row
   is an accept. If you need P(accept | bad) with human rejections in the denominator, you
   must collect prospectively, and you must characterise the pre-filtering bias before you
   call any resulting figure a bound.
10. **Pair every forward replay with its parent.** Five of five monolithic historical commits
    failed later tests, but their parents failed too. Without that control the method would
    have returned the counterfactual β = 1.0 from suite drift.
11. **Cross the inputs behind agreeing ratios.** Two adjudicators can trade numerator against
    denominator and appear to agree. Here the cross-combination spread was 14× the reported
    spread.
12. **Establish ground-truth provenance when the artefact is created.** A later request to the
    nominal maintainer cannot recover a judgement that was never made. Store human, model,
    proxy and executable-oracle outcomes as different classes.

**The highest-value action for this work specifically is to run EXP-44 as registered:** a
longitudinal public-corpus test of whether proxy reliability changes with AI-authorship share,
compare the heuristic with PR-SZZ, and then demote the private 356-PR corpus to a contrast case.
[asserted] The second-highest is
to run a mutation-testing tool per check and ask whether mutation score reproduces the
per-check ordering — because if it does, the instrument was already off-the-shelf and
forty-eight years old (§2.4).

---

## 9. Conclusion

We set out to measure β on real repositories and obtained two oracle-conditioned answers that
do not agree. Metadata-adjudicated proxy labels put β in the sensitivity range [0.81, 0.93];
forward replay returned 0/15 = 0.0 [0.0, 0.2039] in the pilot and 0/50 = 0.0 [0.0, 0.0713]
in the primary run. [measured] The primary sample was chronological rather than selected for
subsystem contact, and only 15.4% of repository merges touch that subsystem; its zero may measure
uncoupling rather than verifier reliability. [measured] [asserted] The parent-commit control
prevents the method from reporting a counterfactual β = 1.0 on five monolithic-suite pairs whose
parents also fail. [measured] The estimates are not pooled because they condition on different
selected populations. [asserted]

The history miner also measures α against its proxy, refutes the assumed 0.03, and exposes
three failures: no revert signal, change-size-dependent hotfix labels and a no-verdict state
counted as rejection. [measured] The corrected-label sensitivity range lies far above the raw
0.6305, but matching ratios hid a 16-label cross-family disagreement; the sign survives and
the apparent precision does not. [measured]

The largest result is that no human ground truth exists to settle the oracles on these
AI-orchestrated corpora. [measured] (first-party) Whether this is a wider consequence of rising
AI authorship remains a hypothesis. EXP-44 is registered and unrun, and until it supplies a
public comparison this draft reports a method and negative results, not *the* measurement of
β. [asserted]

---

## Data availability

- **Instruments:** released. The relevant dependency-free Python instruments are listed in
  Appendix A; publication-facing tables contain aggregates only.
- **Corpora:** **not available and never will be.** `jobboard-v2` and `hireable-platform` are
  private commercial repositories. Their per-PR records (four JSON files) are gitignored and
  are not part of any release. No code, file content, path, check name, pull-request title or
  commit message from either repository appears in this paper.
- **Aggregates and trace:** the contingency tables (§4.1, Appendix B), corrected-label
  sensitivity script and EXP-43 findings are published; Appendix C maps every new result to
  an aggregate source. A current tracked EXP-43 pair-level artefact exists. [measured] It is
  outside the aggregate-only publication boundary and must be removed or sanitised before
  release; this paper neither reproduces its fields nor treats it as available data. [asserted]
  The 15-pair pilot and five-pair monolithic arm survive only as aggregate findings. [measured]
- **Consequence, stated plainly:** a reader can audit the arithmetic and the method but
  cannot independently reproduce the history-mined rates or rerun the replay against the source
  history. A public replication is required before this work should clear a technical track,
  and it is the first item of future work.

## AI assistance

This draft was produced with substantial AI assistance, disclosed here in the form arXiv and
the target venues expect. Large language model agents (Anthropic Claude, GPT-class models and
Gemini-class models) were used to: search and summarise literature; write and run the analysis
instruments; propose and check the arithmetic; adjudicate labels and CI failures; execute the
retro-verifier; and draft and revise this prose. The cross-combination sensitivity result was
re-executed during this revision; the retro-verifier numbers were checked against the retained
findings and result artefacts, not rerun against the private corpus. [measured]

AI systems are not authors and are not listed as such. The load-bearing limitations are stated
in §§7.2 and 7.6: the adjudicators shared metadata and framing, apparent ratio agreement
concealed disagreement in their inputs, and even the mechanically different retro-verifier
shares the surfaced-defect channel through later test writing. [measured] [asserted]

## Author statement

Joe Brown is the sole and accountable human author, and the sole submission principal. He is
responsible for the originality, accuracy, rights, privacy and ethics of this content, and
for any correction to it. No AI system holds authorship. This draft is not submitted.

---

## References

Read-depth is stated for every entry, because this programme's own evidence discipline
distinguishes a source that was read from one that was seen in a search result, and it would
be incoherent to drop that distinction in a paper. **[FULL]** = full text read; **[ABS]** =
abstract page read; **[SNIP]** = search-snippet level only; **[2ND]** = secondary source;
**[WEB]** = practitioner or vendor documentation. `[SNIP]` and `[2ND]` entries make the
associated draft claims non-citable and must be fetched in full or removed before this draft
is submitted anywhere.

1. Bachmann, A., Bird, C., Rahman, F., Devanbu, P., & Bernstein, A. (2010). The missing
   links: bugs and bug-fix commits. *FSE*. [SNIP]
2. Beer, I., Ben-David, S., Eisner, C., & Rodeh, Y. (1997). Efficient detection of vacuity in
   ACTL formulas. *CAV*; *Formal Methods in System Design* 18(2), 2001. [SNIP]
3. Beller, M., Gousios, G., & Zaidman, A. (2017). TravisTorrent: synthesizing Travis CI and
   GitHub for full-stack research on continuous integration. *MSR*. [SNIP]
4. Bird, C., Bachmann, A., Aune, E., Duffy, J., Bernstein, A., Filkov, V., & Devanbu, P.
   (2009). Fair and balanced? Bias in bug-fix datasets. *ESEC/FSE*. [SNIP]
5. DeMillo, R., Lipton, R., & Sayward, F. (1978). Hints on test data selection: help for the
   practising programmer. *IEEE Computer*. [SNIP]
6. Herbold, S., Trautsch, A., Trautsch, F., & Ledel, B. Problems with SZZ and features: an
   empirical study of the state of practice of defect prediction data collection.
   *Empirical Software Engineering*; arXiv:1911.08938. [ABS]
7. Herzig, K., Just, S., & Zeller, A. (2013). It's not a bug, it's a feature: how
   misclassification impacts bug prediction. *ICSE*. [SNIP]
8. Jahangirova, G., Clark, D., Harman, M., & Tonella, P. (2016). Test oracle assessment and
   improvement. *ISSTA*. [SNIP]
9. Kupferman, O., & Vardi, M. Vacuity detection in temporal model checking. [SNIP]
10. Lam, W., et al. (2019). RootFinder: finding root causes of flaky tests. [SNIP]
11. Meng, et al. Maintainer merge rates versus automated grader scores on agent-authored pull
    requests. [FULL]
12. Neyman, J., & Pearson, E. S. (1933). On the problem of the most efficient tests of
    statistical hypotheses. *Phil. Trans. R. Soc. A*. [SNIP]
13. Rezk, C., Kamei, Y., & McIntosh, S. (2021). The ghost commit problem when identifying
    fix-inducing changes. *IEEE TSE*. [SNIP]
14. Rogan, W. J., & Gladen, B. (1978). Estimating prevalence from the results of a screening
    test. *American Journal of Epidemiology*. [SNIP]
15. Rosa, G., Pascarella, L., Scalabrino, S., Tufano, R., Bavota, G., & Lanza, M. (2023).
    A comprehensive evaluation of SZZ variants through a developer-informed oracle.
    *Journal of Systems and Software*, 202, 111729; arXiv:2102.03300. [FULL]
16. Rosa, G., et al. (2022). SZZ in the time of pull requests. arXiv:2209.03311. [SNIP]
17. PR-SZZ. arXiv:2206.09967. [SNIP]
18. Schuler, D., & Zeller, A. (2011). Assessing oracle quality with checked coverage. *ICST*;
    *STVR* 2013. [SNIP]
19. SWE-Bench+: enhanced coding benchmark for LLMs. arXiv:2410.06992. [ABS]
20. Tantithamthavorn, C., McIntosh, S., Hassan, A. E., Ihara, A., & Matsumoto, K. (2015). The
    impact of mislabelling on the performance and interpretation of defect prediction models.
    *ICSE*. [SNIP]
21. The importance of discerning flaky from fault-triggering test failures: a case study on
    the Chromium CI. arXiv:2302.10594. [SNIP]
22. LLM4SZZ. arXiv:2504.01404 (PACMSE / FSE 2025). [SNIP]
23. AgentSZZ. arXiv:2604.02665. [SNIP]
24. Lee, Nair, Zhang, Lee, Khattab & Finn. Meta-Harness: end-to-end optimisation of model
    harnesses. arXiv:2603.28052, COLM 2026. [FULL]
25. MSR 2026 Mining Challenge: behind agentic pull requests; and arXiv:2601.17581,
    arXiv:2605.06464, arXiv:2601.16809 on agent-authored PR modification, maintenance and
    survival. [SNIP]
26. PIT `mutationThreshold`; Stryker `thresholds.break`. [WEB]
27. github/community discussions #102709 and #48751; actions/runner issue #2566 — skipped
    required status checks do not block merge. [WEB]
28. Vasilescu, B., et al. (2026). The ground is shifting: a reflection on the foundations of
    software measurement. *ASE 2026 NIER*. [FULL]
29. AIDev Dataset / MSR 2026 Mining Challenge. The rise of AI teammates in software
    engineering (SE) 3.0. [ABS]
30. Detecting AI coding agents in open source: a validated multi-method census of 180 million
    repositories. arXiv:2606.24429. [ABS]

**Positioning note.** An earlier version of the surrounding programme recorded "no prior art
found" for measuring a repository's own verifier reliability. That claim is withdrawn and
must not be restored: the search that produced it covered eight LLM-routing sources and zero
software-engineering or statistics venues, and the fields that own this subject matter — SZZ,
mutation testing, flaky tests, acceptance sampling — were entirely unsearched. The honest
position is that this is a well-engineered instance of a known idea carried by an unusual
evidence discipline, and that automated harness search (ref. 24) is a complement rather than a
rival: it optimises a harness against an objective signal and audits that signal for leakage,
while ignoring its *weakness*, which is what β measures.

---

## Appendix A — Instruments

The relevant instruments are dependency-free Python 3. Publication-facing outputs are
aggregate-only; the current EXP-43 pair-level artefact is excluded pending privacy remediation.
Its source checkout and the older pair-level records stay private. [asserted] Line counts are
as released.

| file | lines | role |
|---|---|---|
| `mine_beta.py` | 169 | The miner. Lists merged PRs via `gh`, fetches files and `statusCheckRollup` per PR, derives the ternary CI verdict, applies the revert/hotfix label from the local clone's `git log`, writes the per-PR record and prints one aggregate ratio. **Never amended** (§3.6): it still prints the transposed conditional, still classes `CANCELLED` as red, and still discards per-check identities. |
| `two_by_two.py` | 111 | Prints the entire contingency table and every conditional off it — α, β, the transpose and the base rate, with Wilson intervals — plus both treatments of unrun checks for any corpus that has them. Exists because a conditional read off a remembered marginal is how the axis defect happened. |
| `proxy_diagnostics.py` | 86 | Per-cell breakdown of *which arm* of the label detector fired, and the file-count distribution (median, mean, max) per cell. Produces §4.5 and §4.6. Its stated test: if the revert share differs between cells, the cells were not labelled by the same instrument and a correction audited in one cannot transfer. |
| `red_cell_adjudication.py` | 102 | Reclassifies cancelled-only failures out of "red" and reports both readings of α and β side by side. Produces §4.7. Reads a separately gathered evidence file of re-fetched per-check conclusions; never prints a check name. |
| `alpha_sensitivity.py` | 64 | Evaluates β\* = (1 − α)·e^(−kΔ) at every candidate α and prints the exact scale factor and the Wilson-propagated interval. Produces §4.3. Lists the merge-selected 0.3267 explicitly flagged **not α**, to show the direction of the error does not depend on which wrong quantity is substituted. |
| `independent_replicate.py` | 370 | A second-family re-derivation of the headline claims directly from the primary records (§4.9). |
| `beta_convergence.py` | 62 | Recomputes corrected-label β under every cross-combination of the two metadata adjudications' promotion and refutation counts. Produces the [0.81, 0.93] sensitivity range and the 14× spread (§3.8, §4.4). |
| `run_exp43.py` | 509 | Replays a later test target against child/parent commit pairs, classifies only parent-pass/child-fail as an attributable defect, kills timed-out process trees and writes retained results (§3.9, §5). |
| `test_exp43.py` | 142 | Exercises the Wilson calculation, parent/child outcome classification, lock and high-drift stopping rule. |

History-miner reproduction requires per-PR JSON records in the layout `mine_beta.py` writes;
retro-verification requires the private repository and sampled commit pairs. Those inputs are
private (see Data availability). One history script also hard-codes an absolute input path and
would need editing. This is itself a reproducibility defect: the most decision-relevant inputs
are exactly those every reader will correctly report as missing.

## Appendix B — Complete rate table

`jobboard-v2` (n = 300; no unrun rows, so all treatments coincide):

| quantity | k/n | value | Wilson 95% |
|---|---|---|---|
| α = P(red \| good) | 23/97 | 0.2371 | [0.1635, 0.3307] |
| α, cancelled-only removed | 20/94 | 0.2128 | [0.1422, 0.3059] |
| α, 9 non-meaningful removed, denom. reduced | 14/88 | 0.1591 | [0.0972, 0.2495] |
| α, 9 non-meaningful removed, denom. retained | 14/97 | 0.1443 | [0.0880, 0.2278] |
| α, strictest (12 removed, denom. retained) | 11/97 | 0.1134 | [0.0645, 0.1917] |
| β = P(green \| bad) | 128/203 | 0.6305 | [0.5623, 0.6939] |
| β, cancelled-only removed | 128/188 | 0.6809 | [0.6112, 0.7433] |
| transpose P(bad \| green) | 128/202 | 0.6337 | [0.5653, 0.6970] |
| base rate P(bad) | 203/300 | 0.6767 | [0.6218, 0.7271] |
| human override rate P(red \| merged) — **not α** | 98/300 | 0.3267 | [0.2761, 0.3816] |
| bad-and-red share of β's denominator | 75/203 | 0.3695 | [0.3061, 0.4377] |
| top suite non-passing, bad-and-red (incl. cancelled) | 68/75 | 0.9067 | [0.8197, 0.9541] |
| top suite non-passing, good-and-red (incl. cancelled) | 12/23 | 0.5217 | [0.3296, 0.7076] |
| top suite `FAILURE` only, bad-and-red | 34/75 | 0.4533 | [0.3457, 0.5655] |
| top suite `FAILURE` only, good-and-red | 5/23 | 0.2174 | [0.0966, 0.4190] |
| revert-ish commit subjects | 2/1,511 | 0.0013 | [0.0004, 0.0048] |

`hireable-platform` (n = 56; 7 unrun rows, so the treatment must be stated):

| quantity | treatment | k/n | value | Wilson 95% |
|---|---|---|---|---|
| α | A (exclude unrun) | 4/28 | 0.1429 | [0.0570, 0.3149] |
| α | B (retain, neither) | 4/34 | 0.1176 | [0.0467, 0.2662] |
| α′ | C (unrun = miss) | 10/34 | 0.2941 | [0.1683, 0.4617] |
| β | A | 18/21 | 0.8571 | [0.6536, 0.9502] |
| β | B/C | 18/22 | 0.8182 | [0.6148, 0.9269] |
| transpose P(bad \| green) | — | 18/42 | 0.4286 | [0.2912, 0.5779] |
| base rate P(bad) | A | 21/49 | 0.4286 | [0.3002, 0.5673] |
| human override rate — **not α** | — | 7/56 | 0.1250 | [0.0619, 0.2363] |
| bad-and-red share of β's denominator | B/C | 3/22 | 0.1364 | [0.0475, 0.3334] |
| revert-ish commit subjects | — | 4/995 | 0.0040 | [0.0016, 0.0103] |

Label audit (both corpora, 40 sampled labels: 15 bad-pairs + 5 cleans per repository):

| quantity | k/n | value | Wilson 95% |
|---|---|---|---|
| hotfix-label precision (each corpus) | 1/15 | 0.0667 | [0.0119, 0.2982] |
| clean-label miss rate (each corpus) | 1/5 | 0.2000 | [0.0362, 0.6245] |

Label-arm attribution: revert 0/203 and 0/22; hotfix 203/203 and 22/22. File counts by cell
(median, mean, max): `jobboard-v2` bad-and-green 5, 9.4, 100; bad-and-red 13, 26.7, 100;
good-and-green 3, 6.6, 100; good-and-red 2, 4.1, 16. `hireable-platform` bad-and-green 2,
8.7, 100; bad-and-red 6, 22.3, 57; good-and-green 3, 8.0, 41; good-and-red 9, 9.0, 17
(n = 4; the direction reverses here on four observations and should not be read as a
counterexample to §4.6).

Corrected-label sensitivity and retro-verification (primary corpus):

| quantity | value | status |
|---|---|---|
| corrected-label β, all cross-combinations | **[0.81, 0.93]** | sensitivity range, not a confidence interval; metadata-only, n = 75 contested rows |
| reported-ratio spread | 0.0085 | not reported as a point pair because the inputs disagree |
| cross-combination spread | 0.1192 | 14× the reported spread |
| retro-verifier pilot β | **0/15 = 0.0** | Wilson 95% [0.0, 0.2039]; subsystem suite; `inconclusive` |
| retro-verifier primary β | **0/50 = 0.0** | Wilson 95% [0.0, 0.0713]; chronological pairs, subsystem suite; `inconclusive` |
| monolithic replay with parent control | 0/5 attributable defects | 5/5 drift; `rejected_high_drift` |
| monolithic replay without parent control | counterfactual β = 1.0 | naïve result prevented by the control, not an observed estimate |

## Appendix C — Provenance for the new results

| claim | evidence tag | retained source |
|---|---|---|
| [0.81, 0.93], 0.0085 versus 0.1192, 14×, and the 16-label disagreement | `[measured]` | `docs/10-research/experiments/exp01/beta_convergence.py`; `docs/10-research/experiments/exp01/findings-alpha-2026-08-20.md` §9 |
| retro pilot β = 0/15 [0.0, 0.2039] and primary β = 0/50 [0.0, 0.0713], both `inconclusive` | `[measured]` | `docs/10-research/two-oracles-disagree-2026-08-20.md`; `docs/10-research/experiments/exp43/findings-exp43.md` |
| file-status proxy: 123/162 add any file, 118/162 add a code file; 25/162 touch the subsystem | `[measured]` | `docs/10-research/experiments/exp43/findings-exp43.md`, N=162 merges |
| the file proxy is not a semantic greenfield label or evaluability fraction; absent parent symbols can censor additions under this design | `[asserted]` | `docs/10-research/experiments/exp43/findings-exp43.md`; `docs/10-research/two-oracles-disagree-2026-08-20.md` |
| five monolithic drift pairs, 3–7 later-test failures, and the prevented naïve β = 1.0 | `[measured]` | `docs/10-research/experiments/exp43/findings-exp43.md`; `docs/10-research/two-oracles-disagree-2026-08-20.md` |
| non-pooling reconciliation and targeted-rerun falsifier | `[asserted]` | `docs/10-research/two-oracles-disagree-2026-08-20.md`; `docs/10-research/experiments/exp43/findings-exp43.md` |
| maintainer statement and unavailable human fallback | `[measured]` (first-party) | `docs/10-research/ground-truth-evaporates-2026-08-20.md` |
| no directly matching study found; EXP-44 design and five-percentage-point falsifier | `[cited]` `[asserted]` | `docs/10-research/public-corpus-study-design.md`; `docs/10-research/experiment-register.md` EXP-44; `docs/10-research/bibliography.md` §15 |

<!--
Draft revision decision record, 20 August 2026.
Reasoning: the corrected-label sensitivity result, retro-verifier divergence and missing human
fallback supersede the draft's categorical claim that no correct-axis corrected beta existed.
Alternative not taken: pool the oracles or select either as the beta; rejected because they
condition on different selected populations and neither has human ground truth.
Reversal: git restore --source=baadc8740d34f13a35a1058c54f463f390adfc96 -- docs/50-publications/P1-proxy.md
Falsifiers: a diff audit of 20 contested labels that materially disagrees with both metadata
adjudications; a replay restricted to subsystem-touching merges or representative suites whose
interval overlaps [0.81, 0.93]; or EXP-44 finding proxy precision invariant within five
percentage points across authorship eras.
-->
