# The only empirical β this project has measured is conditioned the wrong way round

**Found 20 August 2026**, by an adversarial run against the β thesis. Two of five independent
attack angles converged on it from opposite directions. Verified by hand against the source
before this file was written. [measured]

**This is the most consequential defect recorded on this project so far.** It is not a bug in
the shipped code — `src/consilience/beta.py` is correct. It is in the only measurement that has
ever produced a β from a real repository, and therefore in the number every downstream document
quotes.

---

## The two quantities

`docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md` defines:

> **β = P(automated checks accept | the artefact is bad)**

`src/consilience/beta.py` implements exactly that. Its denominator is the set of artefacts the
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
| Where it looked | `exp01/mine_beta.py` — the mining script | `src/consilience/beta.py` — the estimator |
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
