---
title: "Mining verifier false-accept rates from repository history: a method, and three measured ways the label proxy fails"
author: "Joe Brown"
date: "20 August 2026"
status: "DRAFT — not submitted, not published, not transmitted. Drafting artefact only."
venue-target: "MSR Registered Reports (Stage 1) → EMSE; arXiv cs.SE"
---

# Mining verifier false-accept rates from repository history: a method, and three measured ways the label proxy fails

**Joe Brown** (sole and accountable author)

> **Status.** This is an internal draft. Nothing here has been submitted, published or
> transmitted. The "AI assistance" section discloses how the draft was produced.

---

## Abstract

An automated check suite is a diagnostic test, and like any diagnostic test it has two
off-diagonal error rates: α = P(reject | good artefact) and β = P(accept | bad artefact).
β is the quantity that governs whether it is safe to let a cheap agent's work through on a
green build; α governs how much good work the gate destroys. Neither is normally measured
for a specific repository. We give a reproducible method for estimating both from ordinary
merged-pull-request history, using the CI verdict recorded at merge as the verifier's
decision and a revert-or-hotfix proxy as the artefact label — a close relative of SZZ — and
we apply it to 356 merged pull requests across two repositories.

**The headline is a method and three negative results, not a measurement of β.** We measure
α at 0.2371 (Wilson 95% [0.1635, 0.3307]) and 0.1429 ([0.0570, 0.3149]) on the two corpora,
against a value of 0.03 that had been assumed in the design this work supports and that lies
outside every interval under every treatment; because the threshold in that design has the
form (1 − α)·f(x), the substitution rescales every threshold by exactly 0.7865 on the
stronger corpus, in the optimistic direction. β, by contrast, is **not** measured here to a
useful precision, and the honest verdict recorded against the pre-registered stopping rule
is *insufficient data*.

We then measure three distinct ways the label proxy fails, each on both corpora.
(1) *The strong signal is absent.* All 224 bad labels come from the weak hotfix arm; the
revert arm fired zero times. A positive control shows this is a true negative rather than a
broken detector: 2 revert-ish commit subjects in 1,511 commits and 4 in 995, none carrying a
pull-request reference. Fix-forward repositories do not supply the signal the strong arm
needs. (2) *The proxy is differentially biased, and worst where it matters.* The
bad-and-red cell — 37% of β's denominator, and the only cell no audit examined — is 2.6× to
3.0× larger by median file count than the bad-and-green cell every audit did examine, and the
hotfix rule's false-positive rate rises with file count. A correction estimated in one cell
therefore cannot be propagated to a denominator containing the other. (3) *A no-verdict
state was silently counted as a rejection.* The green set omitted `CANCELLED`; 15 of 75 and
3 of 23 red pull requests failed only on cancelled runs. Correcting it moves β from 0.6305
to 0.6809 and α from 0.2371 to 0.2128 — **in opposite directions, from a single
reclassification.**

External validity is severely limited and we state it here rather than only in the
limitations section: two repositories, written largely by **one developer** with **heavy AI
assistance**, one labelling pass, and a corpus that essentially does not revert. The label
proxy is a close relative of SZZ and must be read against that literature, in which
proxy-label noise, non-random mislabelling, linkage bias and the commit-size effect are all
long established; our contribution is not that the labels are noisy but what that noise does
when the labels are used to estimate a verifier's own conditional error rate rather than to
train a predictor — where the bias is *differential across cells of the 2×2*, and where at
solo-developer data volumes the resulting interval spans the threshold the estimate exists to
test.

---

## 1. Introduction

Cascade architectures, verification-gated agent loops and automated harness search all rest
on the same unstated premise: that when the checks go green, the artefact is good. That
premise is a claim about a conditional probability — β = P(checks accept | artefact bad) —
and it is almost never measured for the repository it is being applied to. Instead it is
assumed, or borrowed from a benchmark, or replaced by a proxy such as test coverage.

This paper asks a narrow, empirical question: **can β be estimated from the history a
repository already has?** Merged pull requests carry, for free, the verifier's decision (the
CI status rollup recorded at merge) and, via a proxy, the artefact's eventual quality (was it
reverted or hot-fixed shortly afterwards?). Cross-tabulating the two gives a 2×2 from which
both off-diagonal rates fall out. Nothing has to be instrumented; nothing has to be replayed.

The answer we reached is: *α yes, β no, and the reasons β fails are more useful than the
number would have been.*

### 1.1 Contributions

1. **A method and five short instruments** (Appendix A) that estimate α and β from merged-PR
   history by printing the whole contingency table rather than a single conditional. The
   instruments are dependency-free Python and are released.
2. **A measured α, and the refutation of an assumed one.** α = 0.2371 [0.1635, 0.3307] and
   0.1429 [0.0570, 0.3149]. The assumed 0.03 lies outside every interval on both corpora and
   under all three treatments of unrun checks. Because the design's threshold is linear in
   (1 − α), the correction is an exact constant rescaling: 0.7865 and 0.8837.
3. **Three measured failure modes of the standard label proxy**, each reproduced on both
   corpora: absence of the strong signal (with a positive control), differential
   misclassification by change size, and a no-verdict CI state counted as a rejection. The
   third is, to our knowledge, the first quantification of what conflating *no verdict* with
   *reject* does to an estimated verifier error rate — and it moves α and β in opposite
   directions.
4. **A negative result about measurability, honestly reported.** At 356 merged PRs from two
   repositories, with an audited label precision of 1/15, β cannot be estimated to a
   precision that decides anything. The pre-registered stopping rule did not fire and the
   recorded verdict is *insufficient data*. We also report a structural result: retrospective
   merge-mining cannot supply β's denominator at all for the *prospective* definition,
   because `--state merged` makes every row a human accept.
5. **An axis defect, found and recorded.** The originally published figure was the
   transpose, P(bad | green). On one corpus the two agree to 0.49% — which is why it survived
   review — and on the other they differ by 1.91×. We report both, under their own names.

### 1.2 What this paper does not claim

It does not claim that proxy labels being noisy is a new finding; that is established, at
larger scale and with a stronger design, in the SZZ and defect-prediction literature
(§2.2). It does not claim a first measurement of verifier false-accepts on agent-produced
artefacts; SWE-Bench+ reports 31.08% of passed patches as suspicious (§2.7). It does not
claim that β is measured here. And it does not claim generality: the corpus is two
repositories written largely by one developer.

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
  using one of these. The honest answer is that we did not know they existed**; the
  correction is registered as future work (§6).

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
validity, reproducibility and artefact availability at once (§6).

### 2.8 What is left

One sentence, written to be conceded by a hostile reviewer:

> The SZZ and defect-prediction literature studies proxy-label noise as a threat to a trained
> predictor, where it degrades recall; we report what the same noise does when the labels are
> instead used to estimate a verifier's own conditional error rate, where it biases the
> estimand differentially by cell of the 2×2, and we report the negative result that at
> solo-developer data volumes the resulting interval spans the decision threshold the
> estimate exists to test.

---

## 3. Method

### 3.1 Corpora

Two private commercial repositories, referred to by name only: `jobboard-v2` (300 merged
pull requests analysed; 1,511 commits in full history as of 20 August 2026) and
`hireable-platform` (56 merged pull requests; 995 commits). Both were written largely by one
developer with heavy AI assistance. `jobboard-v2` is the strongly-verified corpus (on the
order of twenty CI ratchets, dozens of invariant probes and coverage floors);
`hireable-platform` is the weakly-verified contrast. No code, file content, path, check
name, pull-request title or commit message from either repository appears in this paper;
only aggregate counts and coarse classes. This is a hard constraint, not a courtesy, and it
is also the paper's most serious reproducibility limitation (§5.2).

**A sampling bias worth naming immediately:** the strongly-verified repository is a low-β
repository, which is the exact regime in which cascading looks best. Measuring there
flatters the thesis the measurement exists to test.

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
verifier whose decisions left no artefact at all (§5.5).

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

Every rate in this paper is a ratio of these cells. Base rate P(bad) = 203/300 = 0.6767
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

### 4.4 β as recorded, and why it is not decision-grade

| corpus | β = P(green \| bad) | Wilson 95% |
|---|---|---|
| `jobboard-v2` | 128/203 = 0.6305 | [0.5623, 0.6939] |
| `hireable-platform` (A) | 18/21 = 0.8571 | [0.6536, 0.9502] |
| `hireable-platform` (B/C) | 18/22 = 0.8182 | [0.6148, 0.9269] |

These are **raw proxy-label figures with no label correction applied**, and given an audited
hotfix precision of 1/15 they should not be read as estimates of the true false-accept rate.
A label-corrected figure exists in the source record — approximately 0.12 with an honest
interval of roughly [0.02, 0.42] on `jobboard-v2`, and approximately 0.14 on
`hireable-platform` — but it is a correction of **P(bad | green)**, the transpose, not of β.
No label-corrected β on the correct axis exists anywhere in the record, and we decline to
manufacture one here: the correction factors were estimated on one cell only (§4.6), and the
interval arithmetic behind them is the naïve Rogan–Gladen propagation criticised in §2.3.

For completeness, the transposed quantity is P(bad | green) = 128/202 = 0.6337 [0.5653,
0.6970] and 18/42 = 0.4286 [0.2912, 0.5779].

**Against the pre-registered stopping rule, the recorded verdict for both repositories is
"insufficient data — do not route cheap yet."** The interval is audit-limited rather than
history-limited: the path to a decision-grade estimate exists and is enumerable, and it has
not been walked. We report that rather than a number.

One further arithmetic fact, because it bears on whether any β estimate could clear the
threshold. The evidence floor in the corresponding meter is 30 rejections. A Wilson upper
bound on 0/30 is 0.11352 and on 0/31 is 0.11026, against β\*(0.27) = 0.1119 at the assumed
α. **At the floor as set, no outcome whatsoever — not even a flawless one — produces an
interval that clears the threshold**; 31 is the smallest n that can. The rejections needed at
each true β are 48 at 0.02, 62 at 0.04, 137 at 0.06, 368 at 0.08, 3,045 at 0.10, and never at
β ≥ 0.111 (searched to 200,000). This is not a defect — the floor gates a *measured* verdict,
not a routing decision — but it means the two corrected estimates in the record, both above
β\* itself, describe a regime in which **no sample size clears the threshold at all.** That
is a real result and we publish it as one.

### 4.5 Failure mode 1 — the strong signal is absent, and the zero is a true negative

| corpus | bad PRs | labelled by revert | labelled by hotfix |
|---|---|---|---|
| `jobboard-v2` | 203 | **0** | 203 |
| `hireable-platform` | 22 | **0** | 22 |

**All 224 bad labels across both corpora come from the weak circumstantial arm. The revert
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
`jobboard-v2` (3/22 = 0.1364 [0.0475, 0.3334] on `hireable-platform`), and it has never been
label-audited.** Every published label correction was measured on bad-and-green. The two
cells are enriched for different populations by a mechanism we can measure, so **a precision
correction estimated in one cell is not valid when propagated to a denominator containing the
other.** That is differential misclassification, and it is measurable here rather than merely
arguable.

Which way it moves the answer, if the audit is run: if x of the 75 bad-and-red pull requests
are false positives they move to the good row, and then β = 128/(203 − x) **rises** while
α = (23 + x)/(97 + x) **also rises**. Both move in the pessimistic direction. This is not a
correction that would let the design relax; the size bias predicts the audit makes both
numbers worse. **The audit is the pre-registered falsifier for this section and it has not
been run.**

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

## 5. Threats to validity

Ordered worst first.

### 5.1 The corpus cannot support the claim the method exists to make (fatal for β; severe for α)

356 merged pull requests, two repositories, **written largely by one developer with heavy AI
assistance**, one labelling pass, one LLM family for both the labels and their audit, and a
corpus that essentially does not revert. The stronger corpus is also the more heavily
verified one, which is precisely the regime in which the routing conclusion looks best — so
the sample is biased toward the thesis being tested. β is not measured to a useful precision
by these data and we do not claim it is. α is measured, but a single-developer,
two-repository α is a fact about this developer's CI, not about CI.

### 5.2 The corpus cannot be released, so nothing here is independently reproducible

Both repositories are private commercial code. Their per-PR records are gitignored and will
never be published. We release the instruments and the aggregate contingency tables, which
means an independent party can audit the *arithmetic* and the *method* but cannot reproduce a
single number. That fails the data-availability expectations of the technical tracks this
work would otherwise target, and it is the reason the recommended venue is a registered
report and the recommended next step (§6) is a public corpus.

### 5.3 The labels are a close relative of SZZ and are ~93% noise where audited

Audited hotfix-label precision is 1/15 ≈ 0.0667 [0.0119, 0.2982]. Every headline β in §4.4 is
computed over labels of that quality, and the base rate P(bad) = 0.6767 is an artefact of it.
The correction that exists is a hand-rolled Rogan–Gladen estimator whose intervals do not
account for uncertainty in the n = 15 and n = 5 correction factors, is computed on the
transposed axis, and was measured in a cell that differs by 2.6× in size profile from a third
of the denominator it was applied to (§4.6). We therefore treat every corrected figure as
provisional and build nothing on it.

### 5.4 The audit is not an independent class of evidence

The labels, the audit of the labels and most of the analysis come from one model family. The
one cross-family arm (§4.9) shared the same primary records and framing. In a programme whose
organising principle is that convergence between sources sharing evidence is echo rather than
corroboration, we must apply that standard to ourselves: this paper contains **no measured
evidence that difference of model family did any work.** An earlier claim to the contrary in
the same programme was withdrawn after its own control fired, for six recorded reasons of
which the first was fatal — the blind leaked, because the finding had been committed to a log
inside the repository the control was told to read.

### 5.5 The verifier we measured is not the verifier that operated

`statusCheckRollup` reflects only what GitHub recorded. On the primary corpus roughly forty
check scripts run locally, outside CI. Every accept or reject those made left no artefact.
The estimated verifier is therefore weaker than the acceptance process actually was, in an
unmeasured direction. Relatedly, §4.8 shows that no failing check in the corpus was a
*required* status check, so "red" here does not mean "blocked".

### 5.6 The proxy's window and regex are unvalidated hyperparameters

14 days and a seven-word regex. No sensitivity analysis over either was run. The window
governs the miss rate and the regex governs the false-positive rate, and both were set once
and never varied. PR-level SZZ implementations and LLM-assisted variants exist that would
have supplied better labels (§2.2) and were not used.

### 5.7 β\*'s functional form is assumed

k = 8, a logistic competence model, and the capability gaps in §4.3 are all unmeasured. Only
the linearity of β\* in (1 − α) is used, and only the *scale factor* and its *sign* should be
read from that table. The absolute β\* values are `[algebra]` on `[asserted]` inputs.

### 5.8 Multiple analyses on one dataset

Three corrections (cancelled runs, the size bias, the adjudication) were performed on the
same 356 records after the initial result was known, and no multiplicity adjustment was
applied. Each correction was motivated by a mechanism identified in the instrument rather
than by a search over outcomes, and §3.6 records that the miner was deliberately not amended;
but this is a defensive protocol, not a pre-registration, and it should be read as such.

### 5.9 Numbers in the underlying record disagreed with each other

While preparing this paper we resolved seven conflicts in the source record: a transposed
axis; label corrections propagated across axes under the wrong name; three values for one α;
two unlabelled denominators for one β; a headline correction of "31% tighter" to "21%" that
left a stale document behind; two commit counts for one repository; and three denominators
for one audit. All are resolved above and all are recorded as corrections rather than quietly
fixed. A reader should conclude that this dataset was harder to keep straight than its size
suggests, and that **printing the whole contingency table is the only structural defence** we
found against reading a conditional off a remembered marginal.

---

## 6. What a practitioner should do differently

Each of these is cheap, and each follows from a measured failure above.

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
5. **Audit every cell you intend to correct, not the convenient one.** Precision measured in
   bad-and-green does not transfer to bad-and-red when the two differ 2.6× in size. If you can
   only audit one cell, report the correction for that cell alone and say so.
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

**And the highest-value action for this work specifically:** re-run these instruments on a
public corpus of agent-authored pull requests, of which several now exist at far larger scale
(§2.7), and demote the private 356-PR corpus to a contrast case. That single move repairs
external validity, reproducibility and artefact availability at once. The second-highest is
to run a mutation-testing tool per check on the same repository and ask whether mutation
score reproduces the per-check ordering — because if it does, the instrument was already
off-the-shelf and forty-eight years old (§2.4).

---

## 7. Conclusion

We set out to measure β on real repositories. We measured α instead, refuted an invented
value of it that had been rescaling every threshold in the design by 21% in the optimistic
direction, and found three distinct, measurable ways the standard label proxy fails: the
strong arm never fires in a fix-forward repository, the weak arm is differentially biased
toward exactly the cell no audit examined, and a no-verdict CI state counted as a rejection
moves both off-diagonal rates in opposite directions.

β itself remains unmeasured to any useful precision. The stopping rule did not fire and the
recorded verdict is *insufficient data*. We are publishing the method, the instruments, the
aggregate tables and the negative results, because the failure modes are reproducible, the
corrections are mechanical, and the shape of the answer — that at solo-developer data volumes
the interval spans the threshold the estimate exists to test — is itself the result.

---

## Data availability

- **Instruments:** released. The five scripts are listed in Appendix A and are
  dependency-free Python 3, ~900 lines in total. They read a directory of per-PR JSON records
  and print aggregates only.
- **Corpora:** **not available and never will be.** `jobboard-v2` and `hireable-platform` are
  private commercial repositories. Their per-PR records (four JSON files) are gitignored and
  are not part of any release. No code, file content, path, check name, pull-request title or
  commit message from either repository appears in this paper.
- **Aggregates:** the complete contingency tables (§4.1, Appendix B) are published, together
  with every derived rate and its Wilson interval. Every number in this paper is a function of
  those tables and can be re-derived by a reader with a calculator.
- **Consequence, stated plainly:** a reader can audit the arithmetic and the method but
  **cannot reproduce a single number from primary data.** A public replication is required
  before this work should clear a technical track, and it is the first item of future work.

## AI assistance

This draft was produced with substantial AI assistance, disclosed here in the form arXiv and
the target venues expect. Large language model agents (Anthropic Claude, and for the
independent adjudication in §4.9 a GPT-class model, and for one audit pass a Gemini-class
model) were used to: search and summarise literature; write and run the analysis instruments;
propose and check the arithmetic; adjudicate labels and CI failures; and draft and revise this
prose. Every quantitative claim in this paper was re-derived by executing the released
instruments against the retained records on the day of writing.

AI systems are not authors and are not listed as such. Two limitations of this arrangement
are load-bearing rather than boilerplate and are stated in §5.4: the proxy labels and their
audit were produced by the same model family, so the audit is not an independent class of
evidence; and the cross-family adjudication in §4.9 shared primary records and framing with
the arm it was checking, so it is a second opinion rather than corroboration.

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
**[WEB]** = practitioner or vendor documentation. `[SNIP]` and `[2ND]` entries are not relied
on for any claim in this paper beyond the existence and general subject of the work, and
every such entry must be fetched in full before this draft is submitted anywhere.

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
15. Rosa, G., et al. (2021). Evaluating SZZ implementations through a developer-informed
    oracle. arXiv:2102.03300. [SNIP]
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

All five are dependency-free Python 3 and print aggregates only; per-PR records stay
gitignored. Line counts are as released.

| file | lines | role |
|---|---|---|
| `mine_beta.py` | 169 | The miner. Lists merged PRs via `gh`, fetches files and `statusCheckRollup` per PR, derives the ternary CI verdict, applies the revert/hotfix label from the local clone's `git log`, writes the per-PR record and prints one aggregate ratio. **Never amended** (§3.6): it still prints the transposed conditional, still classes `CANCELLED` as red, and still discards per-check identities. |
| `two_by_two.py` | 111 | Prints the entire contingency table and every conditional off it — α, β, the transpose and the base rate, with Wilson intervals — plus both treatments of unrun checks for any corpus that has them. Exists because a conditional read off a remembered marginal is how the axis defect happened. |
| `proxy_diagnostics.py` | 86 | Per-cell breakdown of *which arm* of the label detector fired, and the file-count distribution (median, mean, max) per cell. Produces §4.5 and §4.6. Its stated test: if the revert share differs between cells, the cells were not labelled by the same instrument and a correction audited in one cannot transfer. |
| `red_cell_adjudication.py` | 102 | Reclassifies cancelled-only failures out of "red" and reports both readings of α and β side by side. Produces §4.7. Reads a separately gathered evidence file of re-fetched per-check conclusions; never prints a check name. |
| `alpha_sensitivity.py` | 64 | Evaluates β\* = (1 − α)·e^(−kΔ) at every candidate α and prints the exact scale factor and the Wilson-propagated interval. Produces §4.3. Lists the merge-selected 0.3267 explicitly flagged **not α**, to show the direction of the error does not depend on which wrong quantity is substituted. |
| `independent_replicate.py` | 370 | A second-family re-derivation of the headline claims directly from the primary records (§4.9). |

Reproduction requires a directory of per-PR JSON records in the layout `mine_beta.py` writes.
Those records are private (see Data availability). One script hard-codes an absolute path to
that directory and would need editing; the others take it as `argv[1]`. This is itself a
reproducibility defect worth stating: the most decision-relevant data in this study is data
every reader will correctly report as missing.

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
