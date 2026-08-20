# We broke our own blind

### An experience report on testing a multi-agent independence claim inside the repository that recorded it, with two negative results about the measurement it was defending

**Joe Brown** — sole author and accountable principal
Consilience research programme
Draft of 20 August 2026 · **Experience report · Not submitted · Not peer reviewed**
Revision 2, after three independent hostile reviews. All figures are anchored to commit
`497cdd8` unless stated otherwise; the repository moved during drafting and §2.1 records what
that cost.

---

## Abstract

An earlier draft of this paper argued a position: that multi-agent verification is unsound unless
each structure names a *different class of facts*, after Whewell's 1840 criterion for the
consilience of inductions. Three reviews established that the position is a restatement. Campbell
and Fiske set the requirement out operationally in 1959 as the multitrait–multimethod matrix; the
software design-diversity and common-cause-failure literatures have priced forced diversity since
the 1980s; Huang et al. measured in 2023 that language models do not improve their own reasoning
without an external signal; and Kuai et al. published a statistical audit of behavioural
entanglement between models, with a diagnostic and a verifier-reweighting remedy, four months
before this draft. We withdraw the position and the contribution claim attached to it, and report
instead what survived: **one incident and two negative results**.

The incident. In August 2026 we claimed that two model families had independently located the same
defect in our own measurement instrument, and recorded it as the first occasion on which the
programme's central claim had been tested on itself and passed. We wrote the overturning test into
the same paragraph and ran it within about twenty minutes. It fired: a same-family arm found the
same defect, in the same file, at the same lines. Worse, the blind had leaked and we had built the
leak — the finding had been committed, in plain text with its figures, to an append-only trajectory
log inside the repository the control was instructed to read. The claim is withdrawn. We also state
plainly, against our own earlier framing, that one arm against one arm has essentially no power to
detect the effect the literature reports for cross-model diversity — Nogueira et al. measure
three- and five-version ensembles realising 0.43 and 0.44 of the reliability gain achievable under
independence, and below 0.3 when built from a single model — so this is an underpowered null, not
evidence that difference-of-class buys nothing.

The two negative results concern the measurement programme the incident was defending, and both
were produced by running arithmetic rather than by reasoning about it. **α, the verifier
false-reject rate, had one value anywhere in the programme — 0.03 — and it was invented.** On a
corpus of 356 merged pull requests the interval excludes 0.03 under every defensible treatment of
unrun and non-gating checks; taking the treatment the estimand is actually defined on gives 0.1591
with a 95% interval of [0.0972, 0.2495]. Every threshold derived from the assumed value is 12–27%
looser than it should be, in the optimistic direction. **And β, the quantity the programme is
organised around, has never been measured with sufficient data**: the meter returns *insufficient
data* with zero rows, and retrospective mining structurally cannot supply its denominator.

Evidence limits, stated here and not only in a limitations section. The corpus is 356 merged pull
requests from two private commercial repositories written largely by one developer with heavy AI
assistance — that description is the author's own knowledge, not a measurement — so external
validity is severely limited and the effective number of independent corpora is one, not two.
Every rate is conditioned on a human merge decision that depends on both artefact quality and the
CI verdict, which is a collider of unknown sign. Labels come from a keyword-and-file-overlap
heuristic whose audited precision is 1 in 15, and whose dependence structure means every interval
quoted is nominal and narrower than the truth. Nothing here is a rate: *n* is one in every
direction that matters.

**Keywords:** experience report · multi-agent systems · verification · negative results ·
experimental blinding · correlated errors

---

## 1. What this paper is, and four things it is not

This is an experience report from one research programme over two days.

It is **not** a position paper arguing that agreement between agents is weak evidence. That
argument is correct and it is not ours. §7 sets out who owns it, across five literatures, the
oldest of which is sixty-seven years old and the newest four months.

It is **not** a demonstration that cross-family verification beats same-family verification. Our
one controlled test refuted our own example, and §3.6 shows that the test could not have detected
the effect the literature reports even had that effect been present.

It is **not** a measurement of β. The programme's headline quantity has zero prospective rows.
What §2 reports is a retrospective proxy on a private corpus, with the label noise, selection
effect and treatment dependence stated in the same section rather than deferred to a limitations
list.

It is **not** a claim of priority on either methodological lesson in §4. We ran a prior-art search
for both after the first review, and it returned prior art for both. We report the lessons because
they bit us, and we report the search because an unrun search is how this programme twice produced
a "no prior art found" claim it later had to withdraw.

What is left is small: an incident worth reporting because it is cheap for others to avoid; two
measured negatives that move thresholds in a real system; and one arithmetic finding — §2.5 —
about two model families agreeing to four decimal places on a number whose inputs they disagree
about by sixteen items.

**Evidence discipline throughout.** Every claim below is one of *measured* (we or the repository
ran it and the artefact exists), *cited* (a source says so, at a declared read depth), *algebra*
(it follows from stated premises), or *judgement*. Where a figure is assumed, unfetched or
model-produced, the sentence carrying it says so. §7 records read depth per source. The first
review's most damaging finding was that the previous draft's read-depth table certified sources
that existed nowhere in the repository; §7 says what we did about that.

---

## 2. The setting, and the honest state of its measurement

The programme's object is **β**, the rate at which automated checks accept an artefact that is in
fact bad — acceptance sampling's consumer's risk, applied per repository to the fault distribution
a coding agent actually emits. β is the complement of a quantity software engineering has
measured, label-free and per repository, for decades: mutation score. That is not a footnote, it
is the honest frame, and §7 gives it properly.

### 2.1 β has never been measured with sufficient data

The programme's meter, run against the real trajectory on the day of this draft, returns:

```
beta [all]: insufficient data (0 human rejections, need 30)
```

Zero rows. [measured] The instrument exists — 972 lines across five modules with 62 test
functions at `497cdd8` — and has received no prospective data at all.

Two corrections to the previous draft belong here, because both are instances of the failure this
paper is about.

**The instrument is not `mypy --strict` clean, and has never been.** The previous draft asserted
that it was, twice. Running `python -m mypy --strict src/consilience` at `497cdd8` reports **21
errors in 3 files** (14 `type-arg`, 4 `no-untyped-def`, 3 `no-any-return`). [measured] The CI gate
runs `python -m mypy src/consilience` under the repository's own `mypy.ini`, which enables
`check_untyped_defs`, `strict_optional` and `warn_unreachable` and none of
`disallow_untyped_defs`, `disallow_any_generics` or `warn_return_any`; under that configuration
the gate reports success. [measured] A sibling draft from this programme catalogues this exact
claim as asserted in five internal documents and records 21 errors at the anchor commit and 19 at
the commit whose message is *"make the check permanent"*. This paper was the sixth document. The
gate that runs is not the gate the documents claim, and the ratchet was installed one notch below
the claim.

**Figures about a moving tree need their commit.** Two earlier drafts of this programme's novelty
assessment quote 789 lines / 47 tests and 924 lines / 51 tests; both were true when written, hours
apart. The previous draft of this paper stated 62 test functions in one section and 40 in another
for the same tree. Every count in this paper is anchored to `497cdd8`.

**Retrospective mining cannot close the gap.** The miner fetches *merged* pull requests, so every
retrospective row is a human accept, while the estimator's denominator is human rejections. Mining
more history adds accepts forever. [measured]

### 2.2 What does exist: a retrospective proxy, and what conditions it

**Table 1 — Aggregate contingency tables, 356 merged pull requests. [measured]** Labels are proxy
labels, not adjudicated defects. Reproduced live from retained records by a script in the
repository; the per-pull-request records are private and remain so.

| Repository (n merged PRs) | bad & green | bad & red | bad & no CI | good & green | good & red | good & no CI |
|---|---|---|---|---|---|---|
| Repository A (300) | 128 | 75 | 0 | 74 | 23 | 0 |
| Repository B (56) | 18 | 3 | 1 | 24 | 4 | 6 |

**Selection on merge is a collider, and it was not named in the previous draft.** Every cell is
conditioned on a human merge decision that depends on both artefact quality and the CI verdict —
the two variables the table cross-tabulates. Bad artefacts that CI caught, and that were
consequently closed rather than merged, are structurally absent, and those are exactly the
verifier's successes. So the quantities below are **P(CI red | good, merged)** and **P(CI green |
bad, merged)**, not repository-level verifier error rates, and conditioning on a common effect
induces association between quality and CI status inside the selected set. The sign of that bias
is unknown. This is not the estimand the programme's threshold arithmetic is defined on.
[judgement, from the design of the miner]

**Table 2 — Rates derived from Table 1, by treatment, with nominal Wilson 95% intervals.
[measured]** The treatment column is not decoration: the point estimate is treatment-dependent and
must never be quoted without it.

| Quantity | Treatment | Repository A | Repository B |
|---|---|---|---|
| α = P(red \| good, merged) | as recorded | 23/97 = 0.2371 [0.1635, 0.3307] | 4/28 = 0.1429 [0.0570, 0.3149] |
| α | cancelled runs excluded | 20/94 = 0.2128 [0.1422, 0.3059] | — |
| **α** | **unrun or non-gating = no verdict** | **14/88 = 0.1591 [0.0972, 0.2495]** | — |
| α | unrun counted as a rejection | — | 10/34 = 0.2941 [0.1683, 0.4617] |
| β = P(green \| bad, merged) | raw proxy labels, verdict-bearing only | 128/203 = 0.6305 [0.5623, 0.6939] | 18/21 = 0.8571 [0.6536, 0.9502] |
| β | cancelled runs excluded | 128/188 = 0.6809 [0.6112, 0.7433] | — |
| **β** | **adjudicated labels (§2.5)** | **[0.81, 0.93]** | — |
| Human override: merged over red CI | — | 98/300 = 0.3267 [0.2761, 0.3816] | 7/56 = 0.1250 [0.0619, 0.2363] |

The bolded rows are the ones to quote. The reconciled α at 14/88 is the treatment that counts an
unrun or non-gating check as *no verdict* rather than as a rejection, because that is the
conditional the threshold arithmetic is defined on; it survives three independent derivations
including a cross-family replication.

A figure of 18/22 = 0.8182 circulated for Repository B's β under the label "unrun checks counted
as a miss". It is not that: putting the `bad & no CI` row in the denominator only scores an unrun
check as a successful catch, which makes the verifier look *better*. Under the gloss the label
claims — how often did nothing stop a bad artefact — the figure is 19/22 = 0.8636 [0.6667,
0.9525]. We report the conditional the estimand is defined on, 18/21, and name the other two
rather than print a row that contradicts its own label.

**Six caveats travel with Table 2, and none is optional.**

1. **The labels are weak, and the weakness is named prior art.** All 225 bad labels (203 + 22, of
   which 224 carry a recorded verdict — the word "total" was doing two jobs in an earlier record)
   come from a hot-fix heuristic: a later pull request within 14 days whose title matches a fix-ish
   regex and whose changed files overlap. The revert arm fired zero times out of 356. A positive
   control establishes that this is a true negative: across 2,506 commits, six carried a
   revert-ish subject and none carried a pull-request reference, which is the detector's primary
   match path. [measured] These are fix-forward repositories, so the strong signal does not exist
   in the corpus at all. This is a keyword-based bug-fix classifier and its precision problem is
   quantified prior art: Herbold et al. find that only about half of the bug-fixing commits SZZ
   identifies are actually bug-fixing, across 398 releases of 38 Apache projects, and conclude
   that inaccurate defect labels are a severe threat to the validity of defect prediction.
   [cited, ABS] We should have read that before treating 1 in 15 as a local surprise.
2. **Audited precision is 1 in 15** (Wilson 95% [0.012, 0.298]) per repository, from a 40-label
   audit. The audit covered the bad-and-green cell only, and its correction was propagated to a
   denominator containing 75 unaudited bad-and-red rows whose median file count is 2.6× larger —
   the regime in which the heuristic's false-positive rate is highest. The audit was itself
   model-judged, in the same family as most of the rest of the programme. A later, larger
   adjudication of the bad-and-red cell (§2.5) confirms 29/75 and 45/75 of bad labels — six to
   nine times the audited 6.7%, on a different cell by a different method, and in the opposite
   direction to what the size bias predicts. Two estimates of the same construct differing by an
   order of magnitude both live in our tree; we quote both.
3. **A uniform precision correction cancels exactly, and this is why the transpose survived.** If
   a single label precision *p* applies to both bad cells, β = 128*p*/(128*p* + 75*p*) = 0.6305 for
   every *p* in (0, 1]. [algebra] Only a *differential* precision between the bad-and-green and
   bad-and-red cells, or a clean-miss term, can move β at all, and that differential has never
   been measured. It follows that the 1-in-15 audit, applied uniformly, does nothing whatever to
   β — and that the objection to the earlier correction is not that it was noisy, but that only
   the differential does any work.
4. **The originally published β was on the wrong axis.** The mining script computes P(bad | green),
   the transpose. On Repository A the two agree to 0.49% because the marginals 202 and 203 nearly
   coincide, which is precisely why the defect survived; on Repository B, against the primary row,
   they differ by a factor of 2.00. This is the defect at the centre of §3. Two corrected figures,
   0.12 and 0.14, are corrections to the *transpose* and must never be quoted as β.
5. **Every interval in Table 2 is nominal and is a lower bound on its true width.** Wilson
   intervals assume independent Bernoulli draws; the labelling procedure guarantees dependence.
   One later fix pull request can label many earlier ones bad, and labels are positively correlated
   across every pull request touching a shared manifest; CI health is serially correlated over
   time. The effective sample size has not been computed. The programme prescribes Kish's
   design-effect diagnostic for model panels in §9 and has never applied it to its own pull
   requests, which is the inconsistency a reviewer finds first.
6. **Analyst degrees of freedom are large, and were exercised after seeing the data.** Exclude
   versus include no-CI rows; exclude versus include cancelled runs; four treatments of α;
   transpose versus correct axis; four cross-combinations of two adjudications; audited versus
   raw. The cancelled-run correction was found by a post-hoc re-fetch. No interval in Table 2
   carries nominal 95% coverage under this path multiplicity. [judgement]

**The effective number of independent corpora is one, not two.** Both repositories were written
largely by one developer with heavy AI assistance — a description that rests on the author's
knowledge and is *judgement*, not measurement — and they share a CI convention, a
conventional-commit style (the direct cause of the fix regex misfiring), one 14-day window, one
labelling pass and one auditor family. Presenting them side by side implies a replication the
design does not contain. The intervals bear this out: α_A [0.1635, 0.3307] overlaps α_B [0.0570,
0.3149], and β_A [0.5623, 0.6939] overlaps β_B [0.6536, 0.9502]. **These data do not establish
that α or β differs between the repositories.** The one non-overlapping pair in Table 2 is the
human override rate, 0.3267 [0.2761, 0.3816] against 0.1250 [0.0619, 0.2363].

**And the checks are endogenous to the faults.** They were written by the same person, largely
with AI assistance, in a fix-forward regime, in response to the very faults being counted. β here
is not measured against a verifier that is independent of the fault distribution it is being
scored on.

### 2.3 The first negative result: α = 0.03 was invented

β\* = (1 − α)·e^(−kΔ), the threshold every simulation in the programme scaled by, has two inputs.
β had two mined estimates. **α had one value anywhere in the repository — 0.03, in one line of one
executable model — and it was invented.** [measured] It is named in three governing documents and
was never measured.

The reason it went unmeasured is a reasoning error rather than a data gap: α and β are the two
off-diagonal cells of *one* contingency table over *one* set of mined records. The miner filtered
to green and computed one rate over what survived. The rows it discarded as a nuisance are exactly
the rows α needs. Nothing had to be collected, and the scarcity even inverts — β wants human
rejections, which are scarce; α wants human accepts, which any merge-mined corpus has in
abundance.

**Under every treatment in Table 2, on both repositories, the entire interval lies above 0.03** —
including the lower bound of the weakest corpus, 0.0570. [measured] The assumed value is not
imprecise; it is outside the interval everywhere.

What that does to the thresholds, quoted with treatments rather than as one flattering number:

**Table 3 — Threshold rescaling by treatment. [algebra]**

| α, with treatment | β\* at Δ = 0.27 | rescale vs assumed |
|---|---|---|
| 0.03, assumed | 0.1119 | 1.0000 |
| 0.1429, Repository B as recorded | 0.0989 | 0.8837 |
| **0.1591, Repository A reconciled** | **0.0970** | **0.8669** |
| 0.2128, Repository A cancelled excluded | 0.0908 | 0.8115 |
| 0.2371, Repository A as recorded | 0.0880 | 0.7865 |
| 0.2941, Repository B unrun as rejection | 0.0814 | 0.7277 |

**Every threshold derived from β\* is 12% to 27% looser than it should be, and the error is in the
optimistic direction.** [algebra] The previous draft wrote this as "the system had been assuming
its verifiers were about 21% more reliable than the corpus says". That is a category slip and we
withdraw it: 0.7865 is the rescale of the *threshold*, not a reliability ratio. Assuming α = 0.03
against a measured 0.1591 to 0.2371 understates the false-reject rate by roughly **five- to
eightfold**. The previous draft also quoted 0.7865 — the most dramatic of five defensible
treatments — without naming the treatment, in a paper about naming the treatment.

Three things this result is not. It is **not novel**: the flaky-test literature owns α, and this
programme's bibliography contains zero flaky-test entries (§7). It is **not clean**: α's entire
numerator, the 23-PR good-and-red cell, was never label-audited when the figure was first
recorded, and the estimand does not match the one 0.03 was a parameter for — 0.03 stood for a
deterministic check suite, whereas the measured quantity is over a whole rollup including
non-blocking, informational, live-model-evaluation and cancelled checks. And it is **not free of
the collider** in §2.2. What survives all three objections is the sign, and the sign is what moves
the system.

### 2.4 The evidence floor is below every threshold it could be checked against

The estimator refuses to report a *measured* verdict below `MIN_REJECTIONS = 30`, a constant the
source itself tags as asserted rather than derived, against a governing decision record's own
50–200.

Thirty is below the smallest *n* at which even a flawless record could clear the derived
threshold, under every value of that threshold. [algebra]

**Table 4 — The evidence floor against each candidate threshold.**

| threshold | source | smallest n with 0 failures whose Wilson upper bound clears |
|---|---|---|
| 0.1119 | β\*(0.27) at the **assumed** α = 0.03 | **31** |
| 0.0970 | at the reconciled measured α = 0.1591 | **36** |
| 0.0880 | at Repository A's as-recorded α = 0.2371 | **40** |
| [0.0866, 0.1041] | across the reconciled α's Wilson interval | **34 to 41** |
| [0.0772, 0.0965] | across the as-recorded α's Wilson interval | **36 to 46** |

The previous draft reported only the first row and called the shortfall "one sample". That
computed the floor against the very threshold the same draft had just declared invented, and it is
the third of the previous draft's errors that ran in the programme's favour. The honest statement
is that **the enforced floor is one short of the assumed threshold and four to sixteen short of
the measured ones**, so no routing decision can be taken at the floor as configured under any
treatment. The "one sample below" flourish is spurious precision over two soft constants and is
withdrawn.

### 2.5 β on adjudicated labels, and why two families agreeing to four decimals is not evidence

The previous draft stated that a label-corrected β on the correct axis "does not exist anywhere".
That was false at the moment of writing: the result had landed in the tree four minutes earlier.
It is reported here because it is both the largest measured result the programme has and a worked
instance of this paper's own subject.

The bad-and-red cell was adjudicated **twice, blind, by different model families**, over all 75
pull requests, from metadata only. [measured]

**Table 5 — Two blind adjudications of the same 75 pull requests.**

| | `gpt-5.6` | `gemini-3.7` |
|---|---|---|
| bad label confirmed | 29 | 45 |
| bad label refuted | 36 | 25 |
| bad unclear | 10 | 5 |
| red meaningful | 39 | 37 |
| red **not** meaningful | 33 | 38 |
| corrected β | 144/167 = 0.8623 | 155/178 = 0.8708 |

Two families reporting β within **0.0085** of each other while disagreeing by **16 pull requests**
on how many bad labels are genuine. That is the shape of a tight cross-validated estimate, and it
is not one. Recomputing β under every cross-combination of the two adjudications' inputs:

| promoted from | refuted from | β |
|---|---|---|
| `gpt-5.6` | `gpt-5.6` | 0.8623 *(as reported)* |
| `gpt-5.6` | `gemini-3.7` | **0.8090** |
| `gemini-3.7` | `gpt-5.6` | **0.9281** |
| `gemini-3.7` | `gemini-3.7` | 0.8708 *(as reported)* |

**Reported spread 0.0085. Cross spread 0.1192. The agreement is 14× narrower than the disagreement
in its inputs warrants.** [algebra] The mechanism is arithmetic, not epistemic: an adjudicator that
refutes more labels also promotes fewer, so a larger numerator trades against a smaller denominator
in roughly compensating amounts. β is stable while the labels underneath are not.

**So the interval to quote is [0.81, 0.93], not [0.862, 0.871].** Had only one family run, or had
the two been compared on β alone, this would have been published as a tight cross-validated
estimate. This is the clearest case in the programme of two agents agreeing without that agreement
being evidence — and, unlike §3, it comes with the arithmetic that says why.

**What it says.** On this corpus, once spurious labels and non-rejections are removed, the verifier
accepts roughly four in five to nine in ten of the bad artefacts it actually rules on, against a
recorded 0.63 and a design-time threshold near 0.09–0.11.

**What it is not.** The estimand changes: promoting confirmed-bad pull requests whose red was not
a meaningful rejection into the numerator estimates *P(not meaningfully rejected | bad, merged)*,
not *P(green | bad, merged)*. It is not a diff-level audit — no adjudicator read a patch. It is
not β for the project; it is β for one repository's CI on merged pull requests. It inherits every
proxy problem in §2.2, and the collider with them. The 10 and 5 `unclear` verdicts are unresolved.
**Falsifier:** a diff-level audit of any 20 of the 75 that disagreed materially with both metadata
adjudications would retire this estimate rather than adjust it.

An independent check from figures already in Table 1: applying the programme's own two audit
factors symmetrically gives a corrected β near 0.71, ranging 0.64 to 0.76 over the audit factors'
Wilson corners alone, before any sampling error in the cells. The Rogan–Gladen-style estimator we
hand-rolled is unbounded and can leave [0, 1] when sensitivity plus specificity falls below 1, and
n = 15 and n = 5 correction factors give it enormous variance. Both routes say the recorded 0.6305
is too low; they do not agree on how much.

---

## 3. The incident

### 3.1 The claim

On 20 August 2026 two arms attacked the programme's central measurement in parallel, blind to each
other and given the same five attack angles.

- **Arm 1** — a fourteen-agent workflow, one model family, including a skeptic instructed to
  refute — found that the mining script computes P(bad | accepted) rather than the defined
  P(accepted | bad), arguing from Bayes' rule.
- **Arm 2** — a single run in a different harness and a different model family — found that the
  estimator's denominator is "bad artefacts that reached a human", and argued it with a worked
  counterexample: 50 bad diffs, the verifier catches 45, the human sees 5 and rejects all 5, so the
  reported estimate is 5/5 = 1.00 against a true 5/50 = 0.10.

Two families, two harnesses, two different arguments, two different files, one underlying fault. We
wrote it up as *the first time this project's central claim has been tested on itself and passed*,
tagged it measured, and recorded the significance in the trajectory log.

### 3.2 The pre-registered overturning test, in the same paragraph

The same paragraph carried its own falsifier, written before the test was run:

> "**What would overturn it:** a same-family pair converging equally well on a defect of this
> severity, which would mean the convergence came from the corpus rather than from the difference.
> That is a cheap experiment and it should be run before this paragraph is quoted anywhere."

It was run within about twenty minutes.

### 3.3 It fired

A third arm, **the same model family as Arm 1**, was given the same five attack angles and the same
repository with the two write-ups withheld by name. It found the transpose defect — not a cousin of
it, the same defect in the same file at the same three line references — and independently
reproduced the concealment arithmetic to four decimal places: 128/202 = 0.6337 against 128/203 =
0.6305. [measured]

It then reproduced **Arm 2's separate contribution** as well, running the estimator over a
check-pre-filtered queue and printing `beta [all]: 1.000 [0.886, 1.000] from 30/30 rejections` —
the counterexample in executable form.

**One same-family run recovered both arms.** The claim that difference-of-family produced the
finding has no support and is withdrawn.

One attribution in the previous draft is corrected here. It credited the control with reproducing a
second pair of figures, 0.4286 against 0.8182, on the other repository. The record credits the
control only with 0.6337 against 0.6305; the second pair appears as *content of the leaked
trajectory event*. In a section whose whole subject is that the blind leaked, attributing leaked
figures to the control is the wrong way round.

### 3.4 Six reasons the claim was wrong, and the first is fatal

**Table 6 — Why the cross-family consilience claim did not survive its own control.**

| # | Defect in the claim | Evidence |
|---|---|---|
| 1 | **The blind leaked, and we built the leak.** | The control read the repository's append-only trajectory log and found an event stating the defect in plain text with its figures. Withholding two filenames from a git-tracked tree is not a blind. |
| 2 | The corpus was not the same corpus. | Three commits landed the earlier arms' conclusions into the tree before the control started. |
| 3 | The common cause may be the prompt, not the corpus. | All three arms received the same five attack angles, and angle 5 as written points at the denominator. This possibility was available before any of it ran. |
| 4 | Family was confounded with scaffold. | Arm 1: fourteen agents with a refuting skeptic. Arm 2: a different harness *and* a different family. Control: a single run. |
| 5 | *n* = 1 against *n* = 1 separates nothing. | Not family, not sampling variance, not run-to-run variance. |
| 6 | The adjudicator shared a family with the claimant. | Echo, by our own definition, in the act of testing for echo. |

### 3.5 What survives

**The defect survives and is stronger** for three independent hand-verifications; the axis decision
is recorded and the definition stands as P(accept | bad), with the transpose retained under its own
name and reported alongside. **The consilience claim does not survive.** The significance field in
the original trajectory event is withdrawn and downgraded from *measured* to *judgement*.

### 3.6 The correction the reviews forced: this is an underpowered null

The previous draft drew a standing conclusion from this — "there is no measured evidence that
difference-of-class does anything for this project" — and declined to soften it. That was the wrong
inference from the right data, and it is withdrawn in this form.

The relevant effect size is measured elsewhere and it is modest. Nogueira et al. evaluate 224
problems across twelve models, five languages and three prompting strategies, and report that
three- and five-version ensembles realise only 0.43 and 0.44 of the reliability gain achievable
under independence, falling below 0.3 when the versions come from a single model; manual fault
analysis finds that different failure patterns often share root causes. [cited, ABS] Ron, Baudry
and Monperrus revisit Knight and Leveson with 48 agent-written implementations against 10^6
randomised inputs and find substantial common-mode failure — *and also* that majority voting over
three-version units cuts mean failure counts from 387.44 to 130.99, which they characterise as the
strongest evidence to date that N-version programming with coding agents is a useful engineering
strategy. [cited, ABS] The previous draft cited that paper for the first half only. That is a
seventh error in the flattering direction, found while checking a citation the reviews had asked us
to fetch, and it ran against the diversity-buys-something reading rather than for it.

So the honest position is: **cross-model diversity buys roughly 1.4× the independence gain of
same-model diversity, and one arm against one arm has essentially no power to detect an effect that
size.** §3 is an underpowered null. What it demonstrates is not that difference-of-class buys
nothing; it is that our experiment could not have told us either way, and that our blind was broken
before it started.

---

## 4. Two methodological lessons, with no priority claim attached

### 4.1 A committed findings log inside the tree under study is a contamination channel

> **You cannot run a blind experiment inside the repository you are writing your findings into.**

The trajectory log is append-only, committed, and among the first things a thorough agent reads.
Every finding recorded there becomes corpus for every subsequent run. This is not an operational
slip to be avoided by being careful next time; it is a property of any project that keeps its
evidence and its instrument in one tree.

The previous draft claimed "we have not seen this stated elsewhere". **We had not searched.** We
have now, in the fields that could contain the answer, and it does: benchmark and training-data
contamination, agent state contamination, and blinding protocol. Wang et al. study persisted
transcripts and summaries becoming premises for later runs, under the name *memory laundering*,
with a metric for information that survives beneath a detection threshold — a safety framing rather
than an experimental-design one, but the same mechanism. [cited, ABS] Practitioner writing on
blinding agentic experiments already observes that contamination leaks through auxiliary channels
including log files, tool output, environment variables and even repository naming, and argues for
clinical-trial-style blinding protocols; agentic benchmark maintainers have logged repository-state
loopholes that let an agent see future state. [cited, SNIP] Contamination between arms is also a
textbook threat in cluster-randomised trials, and unmodelled cross-correlation from re-used
evidence is a thirty-year-old named problem in distributed data fusion — *data incest* — with
standard remedies such as covariance intersection. [cited, STD]

**We therefore make no priority claim.** The narrow instantiation we would still put on the record
is that a *committed, human-authored, prose findings log* is a worse channel than the memory
buffers the agent-contamination literature studies, precisely because it is prose, is in version
control, and is the artefact a diligent agent is *instructed* to read first. That is a two-sentence
observation, not a contribution.

The repair is specified and has **not** been run: freeze a corpus snapshot before the first arm,
commit the angle text verbatim, place the trajectory log outside the snapshot, and run further arms
against it.

### 4.2 A blind grader must not be asked for a tally over randomised labels

This is the smallest item in the paper and the one we would defend hardest.

In a blind grading exercise elsewhere in the programme, labels were randomised independently per
decision so that each letter carried each arm exactly twice. Both graders reported a nearly flat
letter tally and both concluded the spread was noise. **Flat is exactly what a dominant arm
produces** under that randomisation. Both graders were right about what they could see and wrong
about the world; the signal existed only after the key was applied, and the graders were correctly
forbidden the key.

The rule: **a blind grader must not be asked to report a tally over independently randomised
labels, because that statistic is flat by construction.** The grader must report per-item
judgements and let the unblinding compute the aggregate. Both graders did supply per-item
judgements, which is the only reason the result was recoverable at all.

We did not search for prior art on this either before the reviews; searching afterwards turned up
the general blinding literature but nothing stating this specific trap for randomised-label tallies.
That is a weak negative from one search and we claim nothing from it.

---

## 5. When difference did buy something, and what the difference actually was

The programme's rules forbid publishing anything from two private commercial repositories used as
measurement corpora: their names and aggregate measured metrics may appear, their content,
excerpts and detailed paths may never. The rule was declared in the initial commit and enforced by
nothing. It had been violated in that same commit.

A cross-family pre-publication audit — a different model family, in a different harness, under a
different operating environment — cross-referenced **5,256 real paths from the two private
repositories** (a count taken on 20 August 2026; the gate as it now stands reports 2,854
*distinctive* paths, a filtered quantity and not the same measure) against this repository's
tracked tree, and found two blockers plus seven files naming a private document by filename.
Described only in class: detailed internal paths, function and script identifiers, hook filenames,
a verbatim quotation from a private assessment document, and a commercial product identity, sitting
in tracked files.

Our own sweep for the same class of violation had run and returned clean. It searched for paths
**prefixed** with a repository name. The leak was the same paths written **bare**, with no prefix to
search for. That angle could not have found the leak however carefully it was run. The auditor
introduced an **exogenous signal**: the actual file inventory of the private repositories.

**The mechanism is a tooling difference, not a model-family difference, and the previous draft
filed it under the wrong heading.** An inventory-grounded oracle beats a prefix regex. That is the
test-oracle problem, and the pattern-versus-inventory result is the standard finding in secret
scanning. Family, harness, operating environment, search strategy *and* needle corpus all differed;
we attribute the finding to the grounding on mechanistic grounds and cannot separate the factors
with one run. *n* = 1.

The repair is a local pre-publication gate, deliberately not a CI job (the private repositories are
absent from a CI runner, so a CI version would silently no-op, and a check that silently no-ops is
worse than none). It was proven to fail before it was trusted: run against the pre-scrub tree it
reports all five path references, and the first threshold chosen caught only two of five. Its
ceiling is documented rather than hidden — it matches file paths only, so a leaked function name,
CI job name or commit subject passes.

Two operational facts the previous draft omitted, both unflattering. In the same episode the gate
was piped into `tail`, which discarded its exit code, so a **failing gate reported success** — the
previous draft called `tail` "a formatter", which reads as a tooling nicety rather than the
exit-code-swallowing pipe it was. And **the leaked material is repaired at the tip and is still
present in the repository's git history, in the initial commit.** Scrubbing the tip does not remove
it from a clone. A paper that is a step towards publication has to say so.

---

## 6. Enforcement: the check fires on three events in ninety-six

The programme's third working principle says a chokepoint without an enforcement rule is not a
chokepoint. The lesson came from a prior commercial codebase in which a documented unified
model-access boundary was in practice five access paths, because no lint rule banned bypass.

**The different-class rule violated that principle inside the project named after it.** The
governing decision record declares two checks on a per-role `evidence_class` attribute, to be
validated at configuration load. The string appeared **zero times** in the source tree and zero
times in the tests while at least four multi-agent structures ran, including those in §3 and §5.

A check shipped on the day of this draft, and its coverage is thinner than the previous draft
reported. Measured against the real trajectory log at `497cdd8`: there are **96 events**, of which
**9 declare a `contributors` field**, and of those **3 have more than one contributor**. The check
returns early both when the field is absent *and* when the list has a single element, so **it fires
on 3 events and 93 are exempt.** [measured] The previous draft said "87 events are structurally
exempt", which overstates the escape: most of the 87 are single-actor events for which the invariant
is vacuous rather than multi-agent structures that dodged a gate. The defensible claim is that the
invariant is **opt-in** and cannot see a multi-contributor event that declines to declare its
contributors. How many of the 87 fieldless events describe a substantively multi-agent structure has
not been adjudicated, and we decline to substitute a keyword count for that adjudication.

Two further honest qualifications. The single-contributor exemption is asserted as intended
behaviour by a passing test, so "the identical early-return bypass found in the human-authority
guard" is an argument to be made rather than a measurement. And the check gates on the *declared*
class and cannot verify that the declaration is true.

A related count from the same programme: across nine errors in one instrumented session, **two**
were caught by an enforced mechanism and seven only because an agent happened to look. Because the
denominator is agent-*noticed* errors, 9 is a lower bound on errors and **2/9 is an upper bound on
the enforced fraction** — the register's own stopping rule anticipates this, noting that a rising
enforced fraction with a rising audit count means errors are being reclassified rather than caught.

**One live overclaim in our own tree, which we name rather than let a reviewer find.** The
repository still contains an unretracted sentence calling a different *n* = 1 convergence "the first
genuine consilience event this project has recorded about itself", tagged measured. It is
structurally identical to the claim withdrawn in §3. We do not rely on it, its *measured* tag should
be challenged, and it is on the list to be retracted or controlled.

Two internal-catalogue figures are corrected here against a sibling draft that anchors the same
catalogue: this programme's audit of its own tree records **twenty-four** instances of a check, gate
or invariant that was structurally incapable of failing, **sixteen** of them on a single day. The
previous draft said "at least twenty ... fourteen of them". Two drafts in one tree disagreeing about
one catalogue is exactly the traceability failure this paper is about.

---

## 7. Related work: the rule is a restatement, and the read-depth table was not honest

### 7.1 The read-depth failure, first

The previous draft carried a table certifying read depth per source, and marked several sources †,
meaning "read by an assisting agent rather than by the author". The first review established that
**every †-marked source was untraceable in the repository**: no bibliography entry, no fetched
artefact, no occurrence of the author name, the identifier or the quoted figures anywhere in the
tree outside the publication drafts. By this programme's own discipline a figure produced by a model
with no retained artefact is not *cited*; it is closer to *simulated*. The table's assurance that
"no source at SNIP or STD depth carries a load-bearing claim on its own" was circular, because the
FULL-depth support it appealed to was itself in the untraceable set.

**We fetched them.** Every †-marked source in the previous draft has now been retrieved at abstract
level directly from the publisher, and the results are reported below with the corrections that
fetching produced. Two figures did not survive: an inter-model error correlation of r = 0.77 and an
implied effective ensemble size near 1.3, both attributed to *Correlated Errors in Large Language
Models*, appear nowhere in the source we could retrieve. **They are withdrawn.** The figures that
source does support are that models agree about 60% of the time when both err, and that larger and
more accurate models show *more* correlated errors even across distinct architectures and providers.

### 7.2 The rule is Campbell and Fiske's, applied at design time

The previous draft's contribution #1 was "an operational rule with a taxonomy that decides cases,
stated as a ship/no-ship gate rather than a caution". We withdraw it as a contribution.

**Campbell and Fiske (1959)** set out the requirement operationally sixty-seven years ago: in the
multitrait–multimethod matrix, convergence validates a construct only across maximally *different
methods*, and their explicit contribution was putting method on an equal footing with trait. That is
Whewell's second clause turned into a procedure, and it is the canonical citation for our rule. Our
taxonomy — critic tiers that run the tests and worktrees on different repository states are
consilient; debate over shared context and planner-to-implementer handoffs are echo — is that
criterion applied to agent structures. It is a teaching aid, and we now label it one. A gate has to
decide cases the incumbent criterion does not; we cannot show a row that does, and we had already
conceded in the previous draft that one row ("escalation to a stronger model") was undecided while
still marking it *Consilient*. A gate with an admitted undecided row is a heuristic.

**Reliability engineering has priced forced diversity for decades.** Knight and Leveson (1986) had
27 independently developed programs fail together far more often than independence predicts;
Eckhardt and Lee (1985) gave the theoretical account of coincident failure; Littlewood and Miller
(1989) and Littlewood, Popov and Strigini (2001) analyse software design diversity and common-cause
failure directly. There is an embarrassing collision worth naming: the common-cause-failure
literature's coupling parameter is itself called β.

**The empirical LLM version is measured and was sitting uncited in our own bibliography.** Huang et
al. (arXiv:2310.01798, ICLR 2024) report that language models cannot reliably self-correct reasoning
without external feedback; Reflexion works because it consumes execution results. That *is* our
sentence "structures that touch the world are consilient; structures that only talk are echo",
measured. It has been in this repository's bibliography at abstract level, cited zero times, since
19 August. Reading the paper you have already logged is the cheapest possible form of the discipline
this paper claims.

**And the operational treatment exists.** Kuai et al. (arXiv:2604.07650) audit behavioural
entanglement among 18 LLMs from six model families with two information-theoretic metrics — a
Difficulty-Weighted Behavioural Entanglement Index and a Cumulative Information Gain measure — find
statistically significant entanglement associated with judge over-endorsement bias (ρ = 0.508 and
0.520, p < 0.01 on one benchmark; 0.441 and 0.457, p < 0.05 on a second), and demonstrate
de-entangled verifier-ensemble reweighting with 3.5 and 2.6 percentage-point gains in accuracy and
precision over majority voting. [cited, ABS — fetched for this revision] That is measurement, a
diagnostic and a remedy for exactly the question our rule gates on, four months earlier. The
previous draft cited it at abstract level saying "extraction failed" and "nothing in this paper
rests on it", while §3 and contribution #1 rested on nobody having operationalised it. Note also
that the previous draft gave the paper's title incorrectly; the title above is the one on the
listing.

**Kohli (arXiv:2605.29800) supplies the panel diagnostic**, and it checks out on fetching, with one
correction. Nine frontier models from seven families supply about two effective independent votes;
roughly three-quarters of the panel's nominal independence is lost to shared mistakes on shared
items; actual accuracy falls **8 to 22** percentage points short of the independent-voting ideal
(the previous draft wrote 7.6–22.0, which we could not confirm at abstract level); the best single
judge matches or outperforms the full panel across all conditions; established aggregation methods
close at most 11% of the gap. The design-effect machinery is **Kish's (1965)** effective sample size
and the intraclass correlation; Kohli applies it to judges. Credit belongs to Kish, and the previous
draft gave it to Kohli.

**The multi-agent-debate failure modes are measured at far greater n than ours.** Bertalanič and
Fortuna (arXiv:2605.00914) test teams of ten identical models over three debate rounds and report
sycophantic conformity with modal adoption up to 85.5%, contextual fragility destabilising correct
answers at up to 70.0%, and consensus collapse in which correct answers are generated and then
discarded, with oracle gaps up to 32.3 percentage points; isolated self-correction outperforms
debate while using 2.1–3.4× fewer tokens. [cited, ABS] Two smaller observations from our own
programme are consistent with that and are not findings of ours: a single-agent arm matched or beat
a structured meeting arm on six design decisions while the meeting spent 4.8× the tokens and 3.7×
the wall-clock; and all six structured decisions carried standing dissent while all six free-form
threads closed in reported full convergence with none. §8 states why neither supports an inference.
On the human side, both observations are anticipated by Janis on groupthink (1972) and by Nemeth's
work on authentic versus contrived dissent (2001), which finds specifically that role-played dissent
does not deliver the benefit genuine dissent does.

**Ao, Gao and Simchi-Levi (arXiv:2603.26993)** give the decision-theoretic version: for a delegated
acyclic network with a fixed information set and no new exogenous signals, the network is weakly
dominated by a centralised Bayes decision-maker on the same information. Read in full, with four
qualifications recorded on 19 August 2026: the dominance is *weak*; the paper is an unrefereed
technical note; it never addresses whether a real language model can *implement* the centralised
decision-maker; and verifiers enter only as an abstract signal, with executable tests explicitly
allowed to move the Bayes envelope — which is why a blanket "cut all multi-agent structures" does
not follow. The previous draft also compressed two of that paper's experiments into one sentence:
the 90.7% → 22.5% degradation is one model over 200 questions at one and five stages, while the
per-stage prose-versus-structured comparison comes from a separate, smaller experiment, and the
"2.8 versus 8.5 points per stage" figures are our own reader's approximations, not figures the
paper reports.

### 7.3 Both of our measured quantities belong to older literatures

**β is the complement of mutation score.** Mutation testing measures a suite's false-negative rate
label-free, per repository, with build-failing thresholds, and has done for decades (Jia and Harman
2011; Just et al. 2014 on whether mutants substitute for real faults; Petrović and Ivanković on
mutation testing at scale). Our own novelty assessment already says this — "Consilience is an
orchestration front-end for mutation testing" — and the previous draft did not carry it across. The
one empirical residue is whether a check suite's false-negative rate against faults an LLM agent
actually emits differs from its rate against synthetic mutants; that experiment is not registered
and has not been run.

**α is the flaky/false-alarm rate**, measured on millions of builds by the flaky-test literature
(Luo et al. 2014; Micco and colleagues at Google; Labuschagne, Inozemtseva and Holmes 2017; Durieux
et al. 2020). Two private repositories add nothing against those. We deliberately do **not** quote
the specific percentages from that literature here, because we have not fetched them for this draft
and the whole subject of §7.1 is what happens when you quote a figure you have not retrieved.

**Our labelling is SZZ-adjacent and its precision problem is quantified.** Beyond Herbold et al.
(§2.2), Herzig, Just and Zeller (2013) found large-scale misclassification in bug reports, and Rosa
et al. (2021) evaluated SZZ implementations against a developer-informed oracle of over two thousand
annotated instances. Our hot-fix heuristic is a keyword-based bug-fix classifier and should have
been positioned inside that literature from the start.

**Selection, verifier weakness and leakage are all saturated.** SWE-Bench+ found 31.08% of passed
patches suspicious and 32.67% involving solution leakage, with correction dropping one agent from
12.47% to 3.97%. A read-in-full survey in our bibliography records maintainer merge rates averaging
24.2 percentage points below automated grader scores on the same pull requests. (An independence
ratio of 24.2% was attributed to Kohli in the previous draft. It is not in the abstract we
retrieved, which gives "about two" effective votes and "roughly three-quarters" of independence
lost; the figure is **withdrawn** pending a full read, and a reader who saw two 24.2s in one paper
was right to be suspicious.) Meta-Harness (arXiv:2603.28052, COLM 2026, read in full) already
automates harness search and audits its objective signal for regex leakage — it mitigates *leakage*
while ignoring *weakness*. Guo et al.'s SEAL (arXiv:2607.24300) names the verifier–deployment gap,
shows self-authored constraints cannot close it, and proposes a sealed exogenous acceptance loop
whose conclusion is that reliable self-improvement "requires at least one deployment-acceptance
signal outside the agent's control" — an independent derivation of the exogenous-signal rule, a
month before this draft. [cited, ABS — fetched for this revision] Wang et al.'s *Verification
Horizon* (arXiv:2606.26300) argues that verification has become the harder problem and that no fixed
reward function stays effective as policy capability grows. [cited, ABS — fetched for this revision]

### 7.4 What is left

Three things, and each is small.

1. **An incident report.** A pre-registered falsifier for a multi-agent-independence claim, written
   into the same paragraph as the claim, run within the hour, refuted, and published with the
   mechanism — including that the team built the leak that broke its own blind. We make no priority
   claim; we report it because it is cheap for others to avoid and because §3.6 shows how little a
   one-against-one design could ever have established.
2. **The cancellation finding (§2.5).** Two model families agreeing on a number to 0.0085 while
   their inputs disagree by sixteen items, with the arithmetic showing why the agreement is
   compensating rather than corroborating, and a cross-combination spread 14× wider than the
   reported one. We have not looked for prior art on this specific arithmetic and make no claim
   about it; we report it because it is the only place in the programme where "agreement is not
   evidence" is demonstrated rather than asserted.
3. **The flat-tally trap (§4.2).** Small, general, transferable and, as far as one search goes,
   unstated.

We explicitly do **not** claim: that cross-family verification outperforms same-family verification;
that the different-class rule is new; that agreement is never informative; that multi-agent systems
are generally worse than single agents; or that any prior-art search here was exhaustive. Two
earlier "no prior art found" claims in this programme were withdrawn after a later search
established that the original search had been run in the one field that could not contain the
answer — all LLM-routing sources, zero software-engineering or statistics venues. The previous draft
of this paper repeated the pattern with two "we are not aware" claims that had no search behind
them. Both are withdrawn in §4.

**Table 7 — Read depth of external sources. FULL** = read in full by this programme; **ABS** =
abstract or listing page retrieved directly; **SNIP** = search-snippet level; **STD** = standard
reference not fetched for this draft.

| Source | Depth | Note |
|---|---|---|
| Ao, Gao & Simchi-Levi, arXiv:2603.26993 | FULL | four qualifications recorded 19 Aug 2026 |
| Lee et al., Meta-Harness, arXiv:2603.28052 | FULL | |
| Kim et al., *Nature Machine Intelligence* 2026 | FULL | |
| Kohli, arXiv:2605.29800 | ABS | fetched for this revision; 8–22 pp, not 7.6–22.0 |
| Kuai et al., arXiv:2604.07650 | ABS | fetched for this revision; title corrected |
| Nogueira et al., arXiv:2607.02808 | ABS | fetched for this revision |
| Bertalanič & Fortuna, arXiv:2605.00914 | ABS | fetched for this revision |
| Ron, Baudry & Monperrus, arXiv:2606.20158 | ABS | fetched for this revision; previously cited one-sidedly |
| Wang et al., arXiv:2605.16746 | ABS | fetched for this revision |
| Guo et al., SEAL, arXiv:2607.24300 | ABS | fetched for this revision |
| Wang et al., arXiv:2606.26300 | ABS | fetched for this revision |
| Herbold et al., arXiv:1911.08938 | ABS | fetched for this revision |
| Kim et al., *Correlated Errors in LLMs*, arXiv:2506.07962 | ABS | fetched; r = 0.77 and n_eff ≈ 1.3 **withdrawn** |
| Huang et al., arXiv:2310.01798 | ABS | in our bibliography since 19 Aug, cited here for the first time |
| SWE-Bench+, arXiv:2410.06992 | ABS | |
| Campbell & Fiske 1959; Kish 1965; Knight & Leveson 1986; Eckhardt & Lee 1985; Littlewood & Miller 1989; Littlewood, Popov & Strigini 2001; Janis 1972; Nemeth 2001; Jia & Harman 2011; Just et al. 2014; Herzig et al. 2013; Rosa et al. 2021; Luo et al. 2014; Labuschagne et al. 2017; Durieux et al. 2020; Julier & Uhlmann 1997; Whewell 1840; Rogan & Gladen 1978 | STD | standard references, not fetched for this draft; no figure is quoted from any of them |

The STD row is the honest form of what the previous draft's table tried to do. **No percentage in
this paper is attributed to an STD-depth source.** Where a literature is invoked for its existence
and its ownership of a quantity, that is what the sentence says.

---

## 8. Threats to validity

Worst first.

**T1. The paper's own arithmetic was checkable in an hour and was wrong in at least eight places,
all in the programme's favour.** The previous draft asserted `mypy --strict` clean against 21
reproducible errors; asserted that a label-corrected β on the correct axis did not exist four
minutes after one landed in the tree at 0.81–0.93; computed its evidence floor against a threshold
it had itself declared invented; converted a threshold rescale into a claim about verifier
reliability; quoted the most dramatic of five treatments of α without naming the treatment;
described an experiment as run "at matched budget" when the record says budgets were deliberately
unmatched; reported a corrected discriminating gap that was out by a factor of eight and reached the
opposite conclusion to the sibling draft computing it from the same evidence; and cited an N-version
paper for its negative half only. Not one ran against the programme's interest. Six further
misstatements of the same kind are corrected in §3.3, §6, §7.2 and §7.3. Separately, its two
most quantitatively load-bearing external claims had **no retained artefact**; they have now been
fetched (§7.1), two figures were withdrawn as unsupported and one title was wrong. A subagent's
report of a number is not a citation. This is §3 happening again, to the document that reports §3.

**T2. The single controlled test refuted our own central example, and it had no power anyway.** §3.6.
Everything positive we report is uncontrolled *n* = 1 anecdote of exactly the kind §3 shows to be
unreliable. The specified repair — frozen snapshot, committed angle text, further arms per family —
is cheap and has not been run. *n* is one everywhere else too: one leak audit, one invariant audit,
one three-arm decision experiment, one blind grading with twelve judgements from two graders. **No
rate in this paper is a rate.**

**T3. The decision experiment does not license the inference the previous draft drew, and its
protocol was misdescribed.** Budgets were **deliberately not matched** across arms — "at matched
budget" is the wording of the pre-registered *stopping rule*, not a description of the protocol, and
matching was rejected as distorting, so the condition the rule names was never instantiated. Arm A
was six agents, one per decision with no communication layer, not "a single agent". The source says
in terms: "n = 6 decisions, one replication, no statistical power". On the arithmetic: treating the
twelve grader judgements as independent gives 9/12, Wilson [0.468, 0.911], exact binomial p = 0.0039
against chance 1/3 — but that independence assumption is the one this paper's own subject says is
false for a two-model panel. Taking the decision as the unit gives 4/6, Wilson [0.300, 0.903],
p = 0.100, and the source's own material-decision subgroup, omitted by the previous draft, is also
4/6 with the same interval. The graders' agreement corresponds to κ = 0.50, which by Kish's design
effect makes twelve judgements worth eight. **The favourable framing was reported and the
unfavourable subgroup was not.** The honest statement is that a single-agent arm was not beaten by
an arm spending 4.8× the tokens and 3.7× the wall-clock — a harder result than the one claimed — and
that nothing here is significant at the decision level. The 0.60 and 0.48 new-information fractions
used to excuse that experiment from the theorem's punished regime are, per their own source, **upper
bounds**; under a whole-arm reading cross-decision recycling puts the free-form arm's yield nearer
0.25–0.30, and the echo classifier was the same model family as the participants.

**T4. The measurement corpus is severely limited and cannot be released.** 356 merged pull requests,
one labelling pass, a proxy whose strong arm never fired, audited precision of 1 in 15, effectively
one corpus rather than two, and a merge collider on every cell. The corpus cannot be published,
cannot be independently replicated, and cannot satisfy the data-availability expectations of a
technical software-engineering track. Public agent-authored pull-request corpora now exist at larger
scale and are the correct next substrate.

**T5. The headline quantity has never been measured.** §2.1 and §2.4. Separately, one field on every
result asserts that the quantity is a lower bound on a joint error, and a passing test enforces that
assertion; it is not a lower bound, because two unmeasured biases run in opposite directions — human
misses push the estimate down, verifier pre-filtering pushes it toward 1.0 — and do not compose into
a bound in either direction. That defect is open at the time of writing, in the project that
measures false certification.

**T6. Our own enforcement mechanism is opt-in and fires on three events in ninety-six** (§6), and it
validates a *declared* class it cannot verify.

**T7. Self-audit bias.** Almost every artefact here was produced by, and then audited by, systems
from one model family, working inside the repository that contains the findings. The audits that
found the most came from outside that tree — which is either the paper's former thesis quietly
confirming itself, or selection on our part. We cannot distinguish those with the evidence we have.

**T8. Instrument non-amendment.** The mining instrument still prints only the transposed ratio,
still classifies cancelled runs as red, and still discards per-check identities. That was a
deliberate protocol choice — repairing an instrument mid-run after seeing what it produced is
outcome-aware tampering — and the corrections live in separate read-only scripts. The consequence is
that raw recorded outputs and current best estimates sit in different files.

**T9. Figures in our own history that do not reproduce.** A scrub commit says a leak survived 75
commits; the count is 100 over 16 h 08 m on a linear history with zero merges. A claim in our records
that one end-to-end suite accounts for 91% of failures in one cell against 52% in another holds only
when cancelled runs are counted as failures; restricted to genuine `FAILURE` conclusions, the suite
is non-passing on 34/75 = 0.4533 [0.3457, 0.5655] of bad-and-red and 5/23 = 0.2174 [0.0966, 0.4190]
of good-and-red, so the absolute gap narrows from 38.5 to 23.6 percentage points while the ratio
*rises* from 1.74× to 2.09× — the claim survives in weakened form. The previous draft of this paper
reported that correction as "50.7% and 47.8%, and a 39-point gap becomes 3 points", which is a factor
of eight out and reaches the opposite conclusion; it is withdrawn, and the figures above are the ones
a sibling draft computes from the same re-fetched evidence. In a section about a figure that does not
reproduce, our replacement figure did not reproduce either.

**T10. Pseudonymisation is cosmetic if the repository is released.** Tables 1 and 2 name Repository A
and Repository B, but the in-tree findings documents this paper's Data Availability section points at
name both corpora. Either the pseudonyms go or the pointer does, before anything is published.

---

## 9. What would change our minds

Falsifiers, in cost order. None has been run.

1. **Replicate the independence test with power.** Freeze a corpus snapshot before any arm runs,
   commit the prompt text verbatim, place the trajectory log outside the snapshot, then run *k* ≥ 3
   same-family and *k* ≥ 3 cross-family arms and count findings and overlaps. This is no longer an
   original experiment: it is a replication in the code-review and audit task family of Nogueira et
   al.'s methodology, and the expected effect size should be taken from there rather than assumed.
   **State the power honestly before running it**: at three arms per group, an overlap-rate
   difference of the size that literature reports is close to undetectable, so the design should
   either be sized against that effect or presented as a pilot.
2. **Compute the effective sample size on our own arms** using Kish's design effect rather than
   asserting difference from model names. If our "different families" produce n_eff/k < 0.5, our
   cross-family structures are monoculture by measurement. Kuai et al.'s entanglement index is the
   better-developed instrument and should be used in preference to a hand-rolled one.
3. **Compute the effective sample size on our own pull requests.** Every interval in Table 2 assumes
   independence that the labelling procedure violates. A bootstrap clustered on the labelling fix
   pull request is one script, and the per-PR records exist on the machine.
4. **Replace the model-family axis with the evidence axis.** §5's mechanism suggests the productive
   variable is the evidence base and search strategy, not the lineage. A matched design — same
   family, deliberately different grounding — is the direct test, and if it reproduces §5's result
   then "cross-family" is the wrong knob and should be dropped from the vocabulary.
5. **Run the cheap half of the mutation-testing comparison.** If mutation score reproduces the
   per-check ordering of β on this repository, the instrument was already free, off the shelf and
   decades old, and this programme is an orchestration front-end for mutation testing. That is the
   single most decisive falsifier available and it is a day's work.
6. **Close the enforcement hole and measure what it rejects.** Make the different-class check
   mandatory for any event with more than one contributor rather than opt-in, then report what
   fraction of real multi-agent structures it refuses. A gate that rejects nothing is not a gate.
7. **Re-run the instrument on a public agent-authored corpus.** This repairs external validity,
   reproducibility and artefact availability at once, and demotes the private corpus to a contrast
   case.

---

## 10. Conclusion

We set out to argue that agreement between agents is evidence about the agents rather than about the
artefact, and that a multi-agent structure must name the different class of facts it introduces. The
argument is right and it is not ours: Campbell and Fiske stated it operationally in 1959, the
design-diversity literature priced it in the 1980s, Huang et al. measured it for language models in
2023, and Kuai et al. shipped a diagnostic and a remedy for it in April 2026. We withdraw the
position and the contribution.

What we can report is smaller and, we think, still worth four pages. We believed two model families
had independently found the same defect in our own instrument. We wrote the overturning test into the
same paragraph, ran it within the hour, and it fired — and the blind it depended on had been broken
by our own committed findings log, which is a contamination channel with no analogue in the memory
literature precisely because it is prose, is in version control, and is the first thing a diligent
agent reads. Reviewing that incident forced us to say what we had not: one arm against one arm could
never have detected the effect the literature measures, so this is an underpowered null and not a
refutation of difference-of-class.

Along the way the programme's assumed verifier false-reject rate turned out to be invented, by a
factor of five to eight, in the optimistic direction; its evidence floor turned out to sit below
every threshold it could be checked against; and its best cross-validated number turned out to be
two adjudications whose agreement was compensating arithmetic rather than corroboration. Those are
the results.

The one thing we would defend at full strength is the practice, not the thesis: when you believe
agents agreed for a good reason, write down the observation that would show they did not, and go and
make it. This revision exists because three reviewers did that to us and found seven arithmetic
errors that all flattered us; an eighth surfaced while we were checking a citation they had told us
to fetch, and it flattered us too. That is the argument for the practice, and it is equally the
argument for not trusting the paper that makes it until someone has checked the numbers.

---

## Data availability

**Released.** The instruments are in the repository this paper comes from: the retrospective mining
script and the read-only recomputation scripts (contingency tables, α sensitivity, proxy diagnostics,
red-cell adjudication, β cross-combination); the estimator, event log and projection modules with
their test suite; the private-corpus pre-publication gate; and the executable models behind the
threshold arithmetic. The findings documents, decision records, experiment register and the
append-only trajectory log are in the tree, including the withdrawal in §3 in its original position
beneath the claim it withdraws.

**Published in aggregate.** The contingency tables (Table 1) and every rate derived from them
(Table 2 and Table 3), the two blind adjudications (Table 5), the trajectory-event counts of §6, and
the aggregate positive-control counts for the revert detector.

**Not released, and it cannot be.** The two measurement corpora are private commercial repositories.
Per-pull-request records, file paths, check names, pull-request titles and commit subjects are
excluded from the repository by policy and by a gitignore, and are excluded from this paper. Four raw
artefacts — the two pull-request record sets, the audit sample and the re-fetched check evidence —
live gitignored on one machine, which means **no number in Table 1 or Table 2 can be reproduced from
the public tree alone**. A reader can reproduce the arithmetic from the published cells and nothing
further. Two independent auditors reported those artefacts as absent, which is itself a
reproducibility finding.

**A caution about the pseudonyms.** Repository A and Repository B are pseudonyms in this paper, but
the in-tree documents named above identify both corpora. If the repository is released alongside this
paper the pseudonymisation is cosmetic; that has to be resolved before publication, not after.

A public replication on an agent-authored pull-request corpus is required before any of the §2
material is offered as a technical result.

---

## AI assistance and human accountability

**Joe Brown is the sole author, the accountable human, and the only submission principal.** No AI
system is an author.

Generative AI systems assisted materially with this work: Anthropic Claude models under the Claude
Code harness (ideation, literature research, methods, implementation, orchestration, analysis and
drafting, including this manuscript and this revision); Google Gemini models under the Cursor agent
harness (adversarial audit of documents and code, the pre-publication leak audit of §5, one of the
two blind adjudications in §2.5, and blind grading); and OpenAI GPT models under the Codex harness (a
numbers audit of the repository's claims, the other blind adjudication in §2.5, and blind grading).
All access dates are 19–20 August 2026. The three hostile reviews that produced this revision were
also model-generated, under separate harnesses, and their findings were verified against the
repository before being accepted; §7.1 records where a model-reported figure was accepted without an
artefact and what that cost. The multi-agent structures reported in §3, §5 and §6 are themselves the
objects of study, and their provenance is recorded in the repository's append-only trajectory log
rather than reconstructed from memory for this disclosure.

The following are stated as facts about this draft and not as claims of completed human review. Joe
Brown approved the research questions, the stopping rules quoted here and the withdrawal in §3. He
has not yet performed the final claim-by-claim, table-by-table review that this programme's own
publication policy requires before a formal submission, and this document is therefore a **draft, not
an approved manuscript**. Nothing in it has been submitted, transmitted or published outside the
authoring machine.

---

## References

Read-depth flags per Table 7. Entries marked *fetched 20 Aug 2026* were retrieved directly from the
publisher during this revision; before that revision they had no retained artefact in this
repository.

1. Ao, R., Gao, S. & Simchi-Levi, D. *On the Reliability Limits of LLM-Based Multi-Agent Planning.*
   arXiv:2603.26993, 2026. [FULL]
2. Bertalanič, B. & Fortuna, C. *The Cost of Consensus: Isolated Self-Correction Prevails Over
   Unguided Homogeneous Multi-Agent Debate.* arXiv:2605.00914, 2026. [ABS — fetched 20 Aug 2026]
3. Campbell, D. T. & Fiske, D. W. *Convergent and discriminant validation by the multitrait-multimethod
   matrix.* Psychological Bulletin 56(2):81–105, 1959. [STD]
4. Durieux, T., Le Goues, C., Hilton, M. & Abreu, R. *Empirical study of restarted and flaky builds on
   Travis CI.* MSR, 2020. [STD]
5. Eckhardt, D. E. & Lee, L. D. *A theoretical basis for the analysis of multiversion software subject
   to coincident errors.* IEEE TSE, 1985. [STD]
6. Guo, D., Cao, C., Yuan, F., Wang, Y., Wang, Y. & Wang, D. *Self-Authored Verification Is Unreliable
   in Heuristic Self-Improving Agents* (SEAL). arXiv:2607.24300, 2026. [ABS — fetched 20 Aug 2026]
7. Herbold, S., Trautsch, A., Trautsch, F. & Ledel, B. *Problems with SZZ and Features: an empirical
   study of the state of practice of defect prediction data collection.* Empirical Software
   Engineering; arXiv:1911.08938. [ABS — fetched 20 Aug 2026]
8. Herzig, K., Just, S. & Zeller, A. *It's not a bug, it's a feature: how misclassification impacts bug
   prediction.* ICSE, 2013. [STD]
9. Huang, J. et al. *Large Language Models Cannot Self-Correct Reasoning Yet.* arXiv:2310.01798; ICLR
   2024. [ABS]
10. Janis, I. L. *Victims of Groupthink.* Houghton Mifflin, 1972. [STD]
11. Jia, Y. & Harman, M. *An analysis and survey of the development of mutation testing.* IEEE TSE,
    2011. [STD]
12. Julier, S. J. & Uhlmann, J. K. *A non-divergent estimation algorithm in the presence of unknown
    correlations.* ACC, 1997. [STD]
13. Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R. & Fraser, G. *Are mutants a valid
    substitute for real faults in software testing?* FSE, 2014. [STD]
14. Kim, E., Garg, S. et al. *Correlated Errors in Large Language Models.* arXiv:2506.07962; ICML 2025.
    [ABS — fetched 20 Aug 2026]
15. Kim, J. et al. *(Multi-agent architectures across 260 configurations.)* Nature Machine
    Intelligence, 2026. [FULL]
16. Kish, L. *Survey Sampling.* Wiley, 1965. [STD]
17. Kleinberg, J. & Raghavan, M. *Algorithmic monoculture and social welfare.* PNAS, 2021. [STD]
18. Knight, J. C. & Leveson, N. G. *An experimental evaluation of the assumption of independence in
    multiversion programming.* IEEE TSE, 1986. [STD]
19. Kohli, G. *Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels.*
    arXiv:2605.29800, 2026. [ABS — fetched 20 Aug 2026]
20. Kuai, C., Jiang, J., Zhu, Z., Wang, H., Wu, K., Li, Z., Zhang, Y., Liu, C., Tu, Z., Fan, Z. &
    Zhou, Y. *A Statistical Framework for Auditing Behavioral Dependence and Induced Bias in LLM
    Judges.* arXiv:2604.07650, 2026. [ABS — fetched 20 Aug 2026]
21. Labuschagne, A., Inozemtseva, L. & Holmes, R. *Measuring the cost of regression testing in
    practice.* FSE, 2017. [STD]
22. Lee, Y., Nair, R., Zhang, Q., Lee, K., Khattab, O. & Finn, C. *Meta-Harness: End-to-End
    Optimization of Model Harnesses.* arXiv:2603.28052; COLM 2026. [FULL]
23. Littlewood, B. & Miller, D. R. *Conceptual modeling of coincident failures in multiversion
    software.* IEEE TSE, 1989. [STD]
24. Littlewood, B., Popov, P. & Strigini, L. *Modeling software design diversity: a review.* ACM
    Computing Surveys, 2001. [STD]
25. Luo, Q., Hariri, F., Eloussi, L. & Marinov, D. *An empirical analysis of flaky tests.* FSE, 2014.
    [STD]
26. Nemeth, C. J., Brown, K. & Rogers, J. *Devil's advocate versus authentic dissent: stimulating
    quantity and quality.* European Journal of Social Psychology, 2001. [STD]
27. Nogueira, R. P., Pattabiraman, K., Vieira, M. & Campos, J. R. *A Systematic Methodology for
    Evaluating Failure Independence in LLM-Generated Code.* arXiv:2607.02808, 2026. [ABS — fetched
    20 Aug 2026]
28. Rogan, W. J. & Gladen, B. *Estimating prevalence from the results of a screening test.* American
    Journal of Epidemiology, 1978. [STD]
29. Ron, J., Baudry, B. & Monperrus, M. *N-Version Programming with Coding Agents.* arXiv:2606.20158,
    2026. [ABS — fetched 20 Aug 2026]
30. Rosa, G. et al. *Evaluating SZZ implementations through a developer-informed oracle.* ICSE, 2021.
    [STD]
31. *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992, 2024. [ABS]
32. Wang, B., Zhang, C., Liu, D. et al. *The Verification Horizon: No Silver Bullet for Coding Agent
    Rewards.* arXiv:2606.26300, 2026. [ABS — fetched 20 Aug 2026]
33. Wang, Y., Goyal, A., Chen, Y. & Sundaram, H. *State Contamination in Memory-Augmented LLM Agents.*
    arXiv:2605.16746, 2026. [ABS — fetched 20 Aug 2026]
34. Whewell, W. *The Philosophy of the Inductive Sciences, Founded Upon Their History*, Vol. II.
    London: John W. Parker, 1840; restated in *Novum Organon Renovatum*, 1858, pp. 70–71. [STD]

Entries present in the previous draft's reference list but never cited in the body — Neyman & Pearson
(1933), Tantithamthavorn et al. (2015), Bovens & Hartmann (2003), Ladha (1992), Berg (1993), Tran &
Kiela, Bommasani et al., Qwen Team, and Jwalapuram et al. — have been removed rather than retained
for ornament. Where the underlying literature is still invoked (acceptance sampling, defect-label
noise, Bayesian coherence) it is invoked by name in the text without a figure attached.

---

## Response to reviewers

Three independent hostile reviews were received: **MAJOR REVISION**, **REJECT as a position paper**,
and **MAJOR REVISION**. All three are substantially right and this revision accepts nearly all of
them. What follows records what changed, and the four places where a reviewer is wrong.

### Structural change

Reviewer 2's core finding is accepted: **the position is pre-empted and the paper cannot be a
position paper.** Campbell and Fiske (1959) own the rule; the design-diversity and common-cause-failure
literatures own the engineering; Huang et al. (2310.01798), sitting uncited in our own bibliography,
own the measured LLM version; and Kuai et al. (2604.07650) — fetched for this revision, and it is
real and it does what the reviewer said — own the operational verifier-ensemble treatment. Contribution
#1 is **withdrawn**. The taxonomy is relabelled a teaching aid. The paper is retitled around the
incident and restructured as an experience report, and reviewer 2's venue advice (a
verification-of-agents workshop or ICSE-NIER) is accepted in principle.

**It did not get shorter, and that is the honest report.** Reviewer 2 asked for a four-to-six-page
experience report; the body of this revision is about 12,700 words against the previous draft's
10,000, measured rather than estimated. Withdrawing the position saved roughly 1,500 words;
correcting eight quantitative claims, naming the collider, adding the treatment and floor tables,
adding §2.5, and fetching and re-reporting twelve sources cost more than that. We are not going to
hit the length by deleting evidence the same reviewers demanded. The cut that would actually work
is to reduce §2 to its two results and a pointer at the companion draft in this repository that
already carries the proxy apparatus in full — which would land the body near 7,000 words and lose
nothing that is not recorded elsewhere. **That cut has not been made**, because it trades
self-containment for length and that is the author's call, not a drafting decision.

### Blockers accepted and fixed

- **`mypy --strict` clean** (R1). False; 21 errors reproduced. §2.1 now reports the measured position,
  names the gate that actually runs, and cites the sibling catalogue's "it has never been clean". The
  40-versus-62 test-count inconsistency is fixed and every count anchored to `497cdd8`.
- **"A label-corrected β on the correct axis does not exist anywhere"** (R1, R3). False four minutes
  after it was written. §2.5 now reports [0.81, 0.93] with its estimand change and all caveats, plus
  the cancellation finding, which is promoted to one of the paper's three remaining contributions.
  R3's symmetric-correction cross-check (≈0.71, range 0.64–0.76) is included, as is the note that the
  Rogan–Gladen form is unbounded.
- **The evidence floor** (R1, R3). Recomputed against every threshold: 31 assumed, 36 reconciled, 40
  as-recorded, 34–46 across intervals, against an enforced 30. The "one sample below" flourish is
  withdrawn.
- **The α caveat** (R1, R3). Both defects accepted. 0.7865 is a threshold rescale, not a reliability
  ratio; the understatement is five- to eightfold. The headline is now 0.1591 [0.0972, 0.2495] with
  its treatment named, and Table 3 gives the full spread.
- **"At matched budget"** (R1, R3). Contradicted by the record. T5 now states that budgets were
  deliberately unmatched, that the stopping rule's condition was never instantiated, and that Arm A
  was six agents.
- **The 91%/52% correction** (R1). Our 50.7/47.8 figures are withdrawn and replaced with 34/75 and
  5/23 from the sibling draft's recomputation on the same evidence, with intervals, in T9.
- **Untraceable †-sources** (R1). Accepted in full and the most damaging finding in any of the three
  reviews. Every one has been fetched; §7.1 reports it as a failure, two figures (r = 0.77, effective
  size ≈ 1.3) are **withdrawn** as unsupported, one title was wrong, Kohli's gap is 8–22 not 7.6–22.0,
  and credit for the design effect moves from Kohli to Kish.
- **Priority claims with no search** (R1, R2). Both withdrawn. A search was run and returned prior art
  for the contamination lesson; §4.1 now cites it and claims only the narrow instantiation.
- **Kuai, Campbell & Fiske, Huang, Nogueira, Bertalanič, state contamination** (R2). All accepted and
  cited; §3.6 restates §3 as an underpowered null with the effect size taken from Nogueira et al.;
  §7.2 cites the debate-failure literature and deletes our two decision-experiment findings as
  findings.
- **Mutation testing and flaky tests** (R2). Accepted; §2.3 and §7.3 now say that β is the complement
  of mutation score and α belongs to the flaky-test literature, and §9 makes the mutation comparison
  the single most decisive falsifier.
- **Merge collider, clustering, α′/β′ rows, non-differences, analyst degrees of freedom, missing
  interval on 7/56, endogeneity, "effectively one corpus"** (R3). All accepted; §2.2 and Table 2
  rewritten accordingly, and the contradictory β′ row removed.
- **Enforcement margins** (R1, R3). Corrected to 3 fires and 93 exempt, with the adjudicated
  multi-agent denominator stated as not computed and the test asserting the singleton exemption
  acknowledged.
- **Smaller accepted items**: `tail` not "a formatter"; the leak is unrepaired in history; the 5,256
  path count dated and the current gate figure given; 2/9 stated as an upper bound; the control
  credited only with the figures it produced; 24 and 16 in the internal catalogue, not 20 and 14; 225
  labels of which 224 carry verdicts; the 1.91 ratio recomputed as 2.00 against the primary row; the
  uncited references removed; the spurious 24.2 independence ratio withdrawn; the pseudonymisation caution added; and
  §4.2 promoted out of the anecdote section.

### Where a reviewer is wrong

1. **R2: "delete §7.1 and §7.2 as findings and keep two sentences."** Accepted as to the deletion. But
   R2's supporting citation for the human side, that Nemeth's authentic-versus-contrived-dissent
   result is "precisely the role-played-governance row", is a looser fit than stated: Nemeth
   measures the quality of divergent thinking a devil's advocate produces, not whether a role-played
   layer introduces new evidence. We cite it as a related human-subjects result, not as a
   pre-emption.
2. **R2: "arXiv:2606.20158 reports substantial common-mode failure", used against diversity.** The
   previous draft made this error and R2 repeats it. On fetching, Ron, Baudry and Monperrus conclude
   the *opposite* overall: majority voting over three-version units cut mean failures from 387.44 to
   130.99, and they call it the strongest evidence to date that N-version programming with coding
   agents is useful. §3.6 now carries both halves and counts our one-sided citation as a seventh
   error in our own favour.
3. **R2: "α most plausibly sits near 0.327, so the rescale is 0.694."** Rejected. 98/300 = 0.3267 is
   P(CI red | merged) — selected on the merge decision and mixing the bad-and-red and good-and-red
   cells. It is a marginal, not a conditional, and the repository's own record already says in terms
   that it must not be quoted as α. The label-noise objection R2 raises is real and is now caveat 2
   and caveat 3 of §2.2, but the remedy is a differential precision estimate, not substituting a
   marginal. R2's broader point — that the label-noise caveat had been applied to β and not to α —
   is accepted and §2.3 now says so.
4. **R3: "print 19/22 for β′ ... recompute the 1.91 against the primary row."** Accepted on the
   second half; on the first, we take R3's own preferred option and drop the β′ row entirely rather
   than print a third treatment, while naming 19/22 = 0.8636 in prose. R3 also computes n_eff for the
   twelve grader judgements as "8 of 12 (ratio 0.67)" using κ = 0.50 at k = 2; the ratio 0.67 is the
   per-pair design effect and 8 is its application to twelve judgements. Both are right; we state the
   derivation rather than the bare numbers to avoid the ambiguity.

### One blocker not fully closed

R2 asks for a full-text read of Kuai et al. and of Nogueira et al. before their contributions are
characterised. Both were retrieved at **abstract level only** for this revision. The characterisations
above are therefore ABS-depth and are flagged as such in Table 7. This matters most for Kuai: the
withdrawal of contribution #1 is based on the abstract's description of the entanglement index, the
information-gain metric and the reweighting result. Withdrawing a claim on abstract-level evidence is
the conservative direction, so we have withdrawn now and will not restore the claim on a full read;
but a reader should know that the pre-emption argument rests on an abstract.

R2's remaining 2026 citations (arXiv:2604.26561, 2608.02827, 2510.07517, 2510.20963, 2607.22962,
2607.03174, 2607.01600, 2607.11022) were **not** fetched and are **not** cited here. Adding sources we
have not retrieved is the exact failure §7.1 reports, and we decline to repeat it in the revision that
reports it.

---

*Draft. Nothing in this document has been submitted or published. Private-corpus content is excluded
by policy and by an automated pre-publication gate; the measurement repositories are referred to as
Repository A and Repository B in all tables.*
