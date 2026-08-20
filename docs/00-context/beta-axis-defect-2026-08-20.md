# The only empirical β this project has measured is conditioned the wrong way round

**Found 20 August 2026**, by an adversarial run against the β thesis. Two of five independent
attack angles converged on it from opposite directions. Verified by hand against the source
before this file was written. [measured]

**This is the most consequential defect recorded on this project so far.** It is not a bug in
the shipped code — `src/consilient/beta.py` is correct. It is in the only measurement that has
ever produced a β from a real repository, and therefore in the number every downstream document
quotes.

---

## The two quantities

`docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md` defines:

> **β = P(automated checks accept | the artefact is bad)**

`src/consilient/beta.py` implements exactly that. Its denominator is the set of artefacts the
**human rejected**:

```python
rejected = [r for r in selected if r.get("human_verdict") == "reject"]
n = len(rejected)
false_accepts = sum(1 for r in rejected if r["verifier_accept"])
```

`docs/10-research/experiments/exp01/mine_beta.py` computes something else, and says so in its
own output string:

```python
accepted = [p for p in prs if p["_ci"] == "green"]
k, n = len(bad_acc), len(accepted)
print(f"  beta-hat = P(bad | green):  {k}/{n} = ...")
```

Its denominator is the set of artefacts the **checks accepted**. `findings-exp01.md` carries the
conditioning openly in its table header — *"raw β̂ = P(bad-labelled | green)"* — so this was
never hidden. It was simply never noticed that it is the transpose of the definition. [measured]

The two are related by Bayes and coincide only when P(green) = P(bad). There is no reason for
that to hold, and nothing in the design assumes it.

---

## Why nobody caught it: the denominators happened to coincide

On `jobboard-v2` the numbers are:

| | value |
|---|---|
| CI green at merge | 202 |
| proxy-labelled bad | 203 |
| bad **and** green | 128 |
| **as recorded**, P(bad \| green) | 128/202 = **0.6337** |
| **on β's axis**, P(green \| bad) | 128/203 = **0.6305** |

The two denominators are **202 and 203**. The error moves the estimate by 0.49%,
which is invisible at two decimal places. [measured] An arithmetic error that hides itself
behind a coincidence is the hardest kind to find by review, and this one hid behind a coincidence
in the very repository chosen as the primary corpus.

On `hireable-platform` the coincidence does not hold:

| | value |
|---|---|
| CI green at merge | 42 |
| proxy-labelled bad | 22 |
| bad **and** green | 18 |
| **as recorded**, P(bad \| green) | 18/42 = **0.4286** |
| **on β's axis**, P(green \| bad) | 18/22 = **0.8182** |

**1.91× apart.** [measured] The second repository was in the corpus the whole time and
would have exposed this immediately had the two axes ever been computed side by side.

---

## What this contaminates

- **The headline β̂ ≈ 0.12 [0.02, 0.42].** That is the raw 0.63 corrected for label precision.
  The correction is sound; the axis it was applied to is not. Correcting the wrong quantity
  accurately still leaves the wrong quantity.
- **The comparison against β\* = 0.111.** β\* lives on the P(accept | bad) axis. The measured
  figure does not. They have been compared as though they did.
- **ADR-0002's PROVISIONAL status and ADR-0015 Gate A condition 1**, both of which wait on EXP-01.
- **The ~146-pair audit**, which is the next scheduled work on EXP-01 and would spend real
  agent-hours sharpening an interval on the wrong axis. **That audit should not start until this
  is resolved.** It is the one part of this that is time-critical. [asserted]

---

## What is *not* contaminated, and matters

The 98 red-CI merges — 33% of `jobboard-v2` — were treated as a nuisance to be excluded. On the
correct axis they are not noise: they are **the missing cell of the 2×2 table that makes β
identifiable at all.** You cannot estimate P(accept | bad) while discarding every bad artefact
the checks rejected, because those are precisely the true negatives in the denominator. [asserted]

This connects to something already recorded and unowned: the sweep's item P11 noted that the
direction EXP-01 actually measured — checks reject, human accepts — is not in β's denominator and
has no name. That observation and this one are the same observation, arrived at separately.

---

## What has deliberately **not** been done

`mine_beta.py` has not been touched. `findings-exp01.md` has not been touched. No recorded number
has been changed. [measured]

Three reasons, and the third is the real one:

1. `AGENTS.md` puts changes to `docs/10-research/` under **ask first**. This is the evidence base.
2. EXP-01 is `IN PROGRESS`. Repairing an instrument during a run, after seeing what it produced,
   is the outcome-aware tampering EXP-07 refused and EXP-31 refused again the same night.
3. **Which quantity the project wants is a design decision, not a repair.** P(accept | bad) is
   what ADR-0002 defines and what the architecture is built on. But P(bad | accept) is arguably
   the more decision-relevant number for a human deciding whether to trust a green build, and it
   is what a practitioner would ask for. Choosing between them, or carrying both, changes what
   v0 measures. That belongs to Joe.

---

## What Joe has to decide

1. **Which quantity is β**, or whether both are carried under distinct names. If both, each needs
   its own human verdicts and the sample-size problem roughly doubles.
2. **Whether the ~146-pair audit proceeds now or waits.** Recommendation: wait. It is the largest
   single block of agent-hours queued against EXP-01 and it is currently pointed at the wrong axis.
3. **Whether the 98 red-CI merges re-enter the denominator.** On the corrected axis they are not
   excludable, and including them is a change to what EXP-01 measures, not a bug fix.

## What would overturn this finding

A reading of ADR-0002 on which β is defined as P(bad | accept). I do not find one — the ADR, the
shipped implementation and the β\* algebra all sit on the P(accept | bad) axis, and they agree
with each other. If they did not, the code would be the defect rather than the mining script.
[asserted]


---

# The independent arm found the same defect from the other end

Two adversarial runs attacked the β thesis in parallel on the night of 20 August, from the same
corpus, **blind to each other**: a fourteen-agent Claude workflow, and a single Cursor
(Gemini 3.7 Flash) run given the same five attack angles. Neither could see the other's output,
and the briefs did not mention the specific defect above. [measured]

They converged. Not on the same sentence — on the same underlying fault, reached from opposite
directions and located in **different files**.

| | Claude arm | Cursor arm |
|---|---|---|
| Where it looked | `exp01/mine_beta.py` — the mining script | `src/consilient/beta.py` — the estimator |
| What it found | the script computes P(bad \| accepted), the transpose of the definition | the estimator's denominator is "bad artefacts that reached a human", not "bad artefacts" |
| How it argued | Bayes: the two conditionals differ unless P(green) = P(bad) | a worked counterexample on a censored review queue |
| Severity given | reshapes | fatal |

**These are one fault.** The denominator of β is never the set of bad artefacts. It is whichever
set the pipeline happened to surface — "green at merge" in EXP-01, "reached a human and was
rejected" in the estimator. Neither is the conditioning ADR-0002 specifies.

## The Cursor arm's counterexample, which is the sharper statement

> An agent generates 50 bad diffs. The verifier catches 45 and the agent retries; the human never
> sees those. Five reach the human, who rejects all five.
> `beta.py` takes `rejected = [r for r in rows if human_verdict == "reject"]`, giving `n = 5`, and
> all five have `verifier_accept == True`. **It reports β̂ = 5/5 = 1.00.**
> The true value is 5/50 = **0.10**.

Wherever the review queue is pre-filtered by the checks, the observed fraction is **1.00 by
construction**. [asserted]

## Where that argument is overstated, and it matters

The Cursor arm calls this *"fatal to the implementation of `compute()`"*. That is one step too
far, and the correction is worth stating precisely rather than waving through.

`compute()` is correct **given an unbiased sample of bad artefacts**. It takes rows carrying both
a `verifier_accept` and a `human_verdict`, and if rows exist where the verifier rejected and the
human still judged the artefact bad, the denominator is sound. The defect is not in the
arithmetic; it is that **nothing in this project ensures such a sample is ever collected**, and
the collection regime it describes systematically fails to produce one. [asserted]

The distinction is not pedantry. "Fix `compute()`" is the wrong instruction and would waste the
work. The instrument is fine; **the sampling frame is missing**, and that is a protocol problem
with a much larger cost.

`jobboard-v2` is the evidence that the censorship is not total: 98 of 300 merges (33%) went in
over red CI, so humans there did see verifier-rejected artefacts. [measured] The sample is not
empty. It is simply not random with respect to the verifier, and no one has characterised how it
is skewed.

## The other thing the independent arm hit that the first did not

**`lower_bound_on_joint_error` is not a lower bound.** [asserted]

The flag exists to record that β measures the human-plus-checks pair rather than the checks
alone, because the human oracle is fallible and correlated with the checks. That reasoning
addresses a bias that pushes β̂ **down** — defects the human also misses.

Verifier pre-filtering pushes β̂ **up**, toward 1.0.

Two unmeasured biases in opposite directions do not compose into a bound in either direction.
The field name asserts a mathematical property the quantity does not have, and every result
carries it, `True`, by default. I looked at that flag earlier the same night while tightening
`Beta.__post_init__` and did not question it. [measured]

**This is not fixed here.** Renaming a field is trivial; deciding what the quantity honestly is
called is not, and it is downstream of the axis decision above.

## Why this matters beyond β

`CONSILIENCE.md` says convergence between inductions from *different* classes of facts is a test
of truth, and `AGENTS.md` principle 6 says agreement between agents sharing evidence is echo.
Every prior structure on this project was justified by that argument and none had ever been
tested by it.

Two model families, given the same corpus and no sight of each other, independently located the
same fault in the project's load-bearing measurement — one in the mining script, one in the
estimator, by different arguments. That is the first time this project's central claim has been
tested **on itself** and passed. [measured]

The honest limit: **n = 1.** One convergence event is not a rate, and both arms also produced
findings the other did not, several of which will not survive checking. What this licenses is
that difference-of-class is worth the cost here — not that it always is.

**What would overturn it:** a same-family pair converging equally well on a defect of this
severity, which would mean the convergence came from the corpus rather than from the difference.
That is a cheap experiment and it should be run before this paragraph is quoted anywhere.


---

# WITHDRAWN: the consilience claim above did not survive its own control

The section above ends with a pre-registered overturning test:

> **What would overturn it:** a same-family pair converging equally well on a defect of this
> severity, which would mean the convergence came from the corpus rather than from the
> difference. That is a cheap experiment and it should be run before this paragraph is quoted
> anywhere.

It was run immediately. **It fired.** The claim that difference-of-model-family produced the
finding is **not supported**, and is withdrawn. [measured]

## What the control did

A third arm — **same model family** as the first — was given the same five attack angles and the
same repository, with the two write-ups withheld by name. It found the transpose defect. Not a
cousin of it; the same one, in the same file:

> *"`mine_beta.py:2` promises `P(checks accepted | artifact was bad)`. `mine_beta.py:135-137`
> computes `accepted = green PRs`, `bad_acc = bad ∧ green`, `k, n = len(bad_acc), len(accepted)` —
> and `mine_beta.py:158` prints its own label: `beta-hat = P(bad | green)`. That is the false-omission
> rate, the reverse conditional."*

Same lines, and independently the same concealment mechanism to four decimals: 128/202 = 0.6337
against 128/203 = 0.6305. [measured]

Worse for the claim: it also reproduced the **Gemini** arm's contribution, running `beta.py` over a
check-pre-filtered queue and getting `beta [all]: 1.000 [0.886, 1.000] from 30/30 rejections` —
the counterexample in executable form. **One same-family run recovered both arms.**

## Why the earlier claim was wrong, and it is not close

1. **The blind leaked, and I built the leak.** The control read
   `.harness/log/2026-08-20.jsonl` and found `measurement.axis_defect_found`, which states the
   defect in plain text including 202/203, 0.6337/0.6305 and 0.4286/0.8182. I had committed the
   finding to the trajectory **inside the repository the control was told to read**. Withholding
   two filenames from a git-tracked tree is not a blind. [measured]
2. **The corpus was not the same corpus.** Commits `153ca51`, `32eacb8` and `02913bb` landed the
   earlier arms' conclusions into the tree before the control started. [measured]
3. **All three arms were handed the same five angles**, and angle 5 as written points at the
   denominator. The common cause may not even be the corpus — **it may be the prompt.** That
   possibility was available before any of this ran and I did not see it.
4. **Family was confounded with scaffold.** Arm 1 was a fourteen-agent workflow with a refuting
   skeptic, arm 2 a different harness *and* a different family, the control a single run.
5. **n = 1 against n = 1 separates nothing** — not family, not sampling variance, not run-to-run
   variance.
6. **The adjudicator was same-family with the arm that made the claim.** Echo, by this project's
   own definition, in the very act of testing for echo.

## What survives, and what does not

**The defect survives, and is stronger.** Three independent hand-verifications now, and the
arithmetic reproduces every time. It was simply *there to be found* by anyone who read
`mine_beta.py:158` against `beta.py:172`.

**The claim about consilience does not.** Nothing about Whewell's second clause was demonstrated
on 20 August. The `significance` field in the 05:50 trajectory event is withdrawn and the event's
honest tag is `[asserted]`, downgraded.

## The lesson, which is worth more than the claim was

**You cannot run a blind experiment inside the repository you are writing your findings into.**
The trajectory log is append-only, committed, and the first thing a thorough agent reads. Every
finding recorded there becomes part of the corpus for every subsequent run. [asserted]

That is not a small operational slip; it is a structural property of a project that keeps its
evidence and its instrument in one tree, and it will recur every time an arm is asked to be
independent. Any future independence test needs a **frozen corpus snapshot taken before the first
arm runs**, and the angle text itself committed — because an unrecorded prompt makes no arm's
result interpretable.

**The cheapest honest repair**, if this is worth doing at all: freeze a snapshot, record the angle
text, run two more same-family and two more cross-family arms against it, and count. Until then
this project has **no measured evidence** that difference-of-class does anything for it, which is
exactly the position it was in yesterday.

---

# What the control found that neither earlier arm did

The control was a failure as a control and a success as an attack. Three findings, verified here.

## 1. `MIN_REJECTIONS = 30` is one sample below the smallest n that can ever clear β\*

Recomputed with the repository's own `wilson()` against its own β\* = 0.111: [measured]

| record | Wilson upper bound | clears β\*? |
|---|---|---|
| 0/29 | 0.11697 | no |
| **0/30** | **0.11352** | **no** |
| **0/31** | **0.11026** | **yes** |

At n = 30 **no outcome whatsoever, not even a flawless one, produces an interval clearing β\***.
The smallest n that can is 31.

**Stated fairly, because the temptation to overclaim is the thing being corrected here.** The
constant is not a bug. `MIN_REJECTIONS` gates the `measured` verdict, and a measured β at n = 30
is still a number; it is not a claim that routing is safe. What the arithmetic shows is that **no
routing decision can ever be taken at the evidence floor as set**, and nothing in the code or the
specification says so. The constant's own comment marks it `[asserted]` — it is derivable, and
the derivation gives 31 as an absolute floor.

And the realistic requirement is far higher. Rejections needed for the upper bound to clear β\*
at each true β: [measured]

| true β | rejections needed |
|---|---|
| 0.02 | 48 |
| 0.04 | 62 |
| 0.06 | 137 |
| 0.08 | 368 |
| 0.10 | 3,045 |
| ≥ 0.111 | **never** (searched to 200,000) |

EXP-01's corrected estimates are **0.12** and **0.14**. Both sit above β\* itself, so on the two
repositories actually measured, **no sample size clears the threshold at all.**

## 2. The retrospective mining route cannot supply β's denominator, structurally

ADR-0002 records the plan: *"Prospective labelling is too slow; historical mining is the route."*
But `mine_beta.py` fetches with `--state merged`, so **every row is a human accept**, while
`compute()` counts `human_verdict == "reject"`. `n_rejected` over the entire corpus is **zero**.
[asserted — the control ran it; I have confirmed the `--state merged` argument and the `compute`
filter by reading, not by re-running the miner]

Mining more history adds accepts forever. The rejections — PRs abandoned, force-pushed away,
never opened — left no artefact to mine. This is a different and deeper problem than the axis
defect: fixing the conditional does not create a denominator that was never collected.

## 3. β\* is in neither the specification nor the code

`β*` appears **zero times** in `docs/40-spec/v0-draft.md` and zero times in `src/consilient/`.
[asserted — from the control's grep, not re-run here] The threshold every β must be compared
against lives only in research notes and one ADR.

## Also raised, not verified here

That **Gate B2 cannot fail** — it requires a parallelism ceiling "greater than one", and
`findings.md` puts critic recall 0.00 at 3.1 agents, so the threshold sits below the floor of the
quantity. If it holds it is the most consequential item after the axis defect, because Gate B2 is
the project's only claim that β is load-bearing on a decision. **It is unverified and should be
checked before it is repeated.** [asserted]


---

# Settled against the raw labels: both conditionals, and the cell that was thrown away

The sections above computed both conditionals from the **published aggregates**. EXP-01's raw
mining output was then found still on disk in the main checkout — gitignored, as the privacy rule
requires, which is why an auditor working from a `docs/` snapshot reported it absent. It is not
absent; it was simply outside that corpus. [measured]

Recomputing directly from the retained labels reproduces every predicted figure exactly.
**Aggregate counts only below**, as the privacy rule permits; no record, title or path from either
repository is reproduced anywhere.

| | `jobboard-v2` | `hireable-platform` |
|---|---|---|
| merged PRs | 300 | 56 |
| CI green | 202 | 42 |
| CI red, merged anyway | 98 | 7 |
| no recorded checks | 0 | 7 |
| proxy-labelled bad | 203 | 22 |
| bad **and** green | 128 | 18 |
| **bad and red** | **75** | **3** |

**As recorded** — P(bad \| green):

- `jobboard-v2` 128/202 = **0.6337**, Wilson [0.5653, 0.6970]
- `hireable-platform` 18/42 = **0.4286**, Wilson [0.2912, 0.5779]

**On β's axis** — P(green \| bad):

- `jobboard-v2` 128/203 = **0.6305**, Wilson [0.5623, 0.6939] — a ratio of **0.9951**
- `hireable-platform` 18/22 = **0.8182**, Wilson [0.6148, 0.9269] — a ratio of **1.9091**

Every figure predicted from the published aggregates reproduces to four decimal places. [measured]

## The number that changes what to do next

**75 bad artefacts on `jobboard-v2` were rejected by the checks — 37% of every bad artefact in
the corpus.** [measured]

That is the cell EXP-01 discarded as a nuisance, and it is **more than a third of the denominator
β actually needs.** β = P(checks accept \| artefact bad) is estimated over *all* bad artefacts,
both the ones the checks let through and the ones they caught. The material is not missing and it
never was: it has been sitting in the mining output since 19 August, excluded by a filter rather
than by a lack of data.

On `hireable-platform` the same cell holds 3 of 22, or 14%.

## What this does and does not settle

**It settles that the axis error is real, and that its size is repository-dependent.** On
`jobboard-v2` it moves the estimate by 0.5% — invisible, which is why nobody caught it. On
`hireable-platform` it is a factor of **1.91**.

**It settles that the correct axis is computable today**, from data that already exists, without
the ~146-pair audit. The audit's purpose was to sharpen an interval; the axis question does not
need it.

**It does not produce a corrected β̂, and I have deliberately not manufactured one.** The
published estimates of 0.12 and 0.14 come from applying audited label-precision and miss-rate
corrections to the raw figures. Those corrections were audited **on the bad-and-green cell
specifically** — 15 sampled bad pairs and 5 cleans per repository. Propagating them to a
denominator that now includes 75 previously unexamined bad-and-red PRs would assume the label
noise is the same in a cell nobody audited. It may not be: a PR that was reverted *and* had red
CI is a different population from one that was reverted *and* passed.

**So the honest position is:** the raw figures above are sound, the label-corrected figures on the
new axis are unknown, and closing that gap needs an audit of the bad-and-red cell — which is
smaller, cheaper and more decision-relevant than the ~146-pair audit currently queued. [asserted]

## Why this was findable only by reading the private data

Two independent auditors reported EXP-01's raw labels as absent. Both were right about their
corpus and wrong about the world, because the privacy rule correctly keeps that data out of the
repository and therefore out of every snapshot staged for an agent. [measured]

That is a permanent structural feature of this project, not a one-off: **the most decision-relevant
data is the data agents will always report as missing.** Any audit of EXP-01 conducted by a scoped
agent will produce this false negative, every time, and the finding will look identical to a real
one. The mitigation is not to relax the privacy rule; it is to state in the dispatch that the
corpus excludes gitignored data, and to treat any absence claim about it as unevaluable.


---

# DECIDED — 20 August 2026

Joe delegated this: *"I DON'T KNOW I WILL TAKE YOUR RECOMMENDATION. DECIDE FOR ME."* Under
ADR-0033 as updated the same day, a technical question with a defensible answer is the harness's,
and it carries the reasoning, the reversal and the falsifier rather than an ask.

## 1. β stays `P(checks accept | artefact is bad)`

**Not because it is the better quantity, but because it is the one everything else is already
built on.** ADR-0002's closed form `β* = (1 − α)·e^(−kΔ)` is derived on this axis; `beta.py`
implements it; the α relationship — the two off-diagonal cells of one 2×2 — only holds on it.
Redefining β would invalidate the algebra and gain nothing the second quantity cannot supply
under its own name.

## 2. `P(bad | accepted)` is kept, named, and reported alongside

It is not an error to be deleted. **It is the more decision-relevant number for a human looking
at a green build** — "given the checks passed, how likely is this bad?" — and it is what EXP-01
actually computed. It gets a name of its own rather than being conflated with β or thrown away.

The two are related by base rates and coincide only by accident. On `jobboard-v2` they agree to
0.5% because the marginals happen to nearly match (202 green against 203 bad); on
`hireable-platform` they differ by 1.91×. **Reporting both makes that visible instead of leaving
it as a trap.**

## 3. `mine_beta.py` is corrected to report both, on the full 2×2

The table is already computable from labels on disk, and building it is what caught two separate
conditional errors — one in EXP-01, one of mine. **The instrument should emit the table, not a
single ratio.** A quantity read off a printed 2×2 cannot silently be the wrong conditional.

## 4. The ~146-pair audit is cancelled

It exists to narrow the interval on `P(bad | accepted)` — the axis the architecture does not
route on. **Replaced by an audit of the bad-and-red cell: 75 pairs on `jobboard-v2`, 3 on
`hireable-platform`.** Smaller, cheaper, and on the axis β actually needs, because that cell is
37% of all bad artefacts and has never been examined.

## Why this ordering and not the obvious one

The obvious move is to fix the estimator and re-run the big audit. That spends the largest block
of queued agent-hours sharpening a number the architecture does not consume. The cheap move —
build the table, audit the unexamined cell — answers the question that was actually open.

## Reversal

`git revert` of this commit and the register entry. **No recorded result is changed by this
decision**, and no raw data is touched; `findings-exp01.md`'s published aggregates stand exactly
as measured.

## Falsifier

**If the bad-and-red cell's label precision differs materially from the bad-and-green cell's
audited 1/15, the two cannot share a correction factor** — and every corrected β on the new axis
would need its own audit rather than inheriting one. That is checkable by the 75-pair audit this
decision schedules, and it is the specific way this decision could be wrong.

A second, cheaper falsifier: if `P(bad | accepted)` turns out to be the quantity every downstream
consumer actually wants, then keeping β as the primary was the wrong call and the two should swap
billing. That would show up as documents reaching for the secondary quantity — which is a
grep, not a study.
