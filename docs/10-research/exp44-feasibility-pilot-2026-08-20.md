# EXP-44 feasibility pilot — runnable, but the era boundaries are wrong and the signal may be

**Date:** 20 August 2026
**Corpus:** `python/cpython`, chosen as EXP-44's designated human-review control
**Status:** `[measured]` for the counts; `[asserted]` for what they imply about the study's timing.
**The registered protocol is NOT amended here.** A protocol edited after seeing data is not a
protocol. What follows is a proposed amendment and a concern, both for a human to accept or reject.

---

## Why a pilot at all

EXP-44 asks whether revert-and-hotfix defect proxies decay as a repository's AI-authorship share
rises — which, if true, means the SZZ and defect-prediction literature rests on an expiring
assumption. It is a 30-repository longitudinal panel.

Before spending that, two of its measurement assumptions had never been tested once. The design
uses **a proxy for AI authorship to test a proxy for defects**, which is two proxies deep, and
nobody had checked whether the outer one carries any signal at all.

## What the pilot measured

**1. The AI signal exists, and it is recent.** [measured] Over 170,540 commits, 59,989 in the
2018–2026 study window:

| year | commits with a genuine AI co-author trailer |
|---|---|
| 2018–2024 | **0** (0.00%) |
| 2025 | 8 (0.09%) |
| 2026 | **782 (11.55%)**, reaching 31.2% in July |

**2. Two traps that would have corrupted the measurement.** [measured]

- **Maintenance bots are 30–41% of all commits** — automated backport cherry-picks, 20,873
  all-time. Counting them as AI authorship would have manufactured a large false signal in every
  era including the pre-AI baseline.
- **Name collision.** Keyword matching on a well-known agent's name matched four commits by a
  *human* core developer with that first name. A naive regex would have recorded AI authorship
  in 2019.

Both are exactly the failure mode of a proxy nobody validates, and both were found by looking.

**3. Ground truth is dense enough.** [measured] Issue or PR linkage on 97.7%, 99.0% and 98.9% of
commits across the three proposed eras; 28.8% carry defect-shaped titles; 412 explicit reverts.
Comfortably above the ≥60 audit pairs the design's power calculation requires.

**4. Cost is negligible.** [measured] 32.9 s per repository end to end — a blobless clone plus
classification. **16.5 minutes for the full 30-repository panel.** Compute is not the constraint.

## The registered era boundaries are contradicted by the data

The design partitions history into Pre-AI (2018–2021), Early Adoption (2023–2024) and High-AI
(2025–2026), with expected AI shares of 0%, 10–40% and >60%.

**Era 2 measures 0.0% declared AI share — identical to the Era 1 baseline.** [measured] The true
inflection is sharp and sits in mid-2026: 19.0% in June, 31.2% in July.

So the calendar partition is imposed from outside and the repository's own data refuses it.
**Proposed amendment, not applied:** replace the three-era calendar with direct commit-level
attribution — pre-2022 human baseline against 2025–2026 AI-trailed commits — plus a bot filter
and name-collision disambiguation.

## The concern that matters more than the amendment

**If the inflection is mid-2026, the high-AI era is roughly two months old.** The study wants to
compare proxy precision across eras; one of those eras has barely happened, and the defects it
would need to have surfaced have not had time to surface. A revert-or-hotfix proxy needs a
*window* after the change to observe the fix. Measuring proxy decay in a regime that started
eight weeks ago may be measuring the window, not the decay. [asserted]

And the pilot's own strongest caveat compounds it: **CPython has a conservative review culture
and enforces co-author trailers; faster-moving repositories likely adopted AI earlier and are far
less likely to declare it.** [asserted] So declared AI share is a *lower bound of unknown
tightness*, and the quantity the study can measure may be uncorrelated with the quantity it cares
about.

**That is the two-proxies-deep problem arriving exactly where it was predicted.** It does not kill
EXP-44, but it changes what an honest result would claim: not "proxy precision decays with AI
authorship" but "proxy precision decays with *declared* AI authorship in repositories that declare
it", which is a much narrower sentence.

## What this does to the paper

P1 carries the generalisation — that the human ground truth defect mining depends on is
disappearing — as a hypothesis with a registered design. **That framing survives and is now better
supported in one direction and worse in another.** Better: the signal is real, measurable and
rising steeply. Worse: it is two months old in the one repository checked, and the measurement
instrument sees only declarations.

P1 must not imply the study is close to answering the question. It is close to being *runnable*,
which is a different claim.

## Falsifier

Run the same 33-second pilot across five repositories with faster AI adoption and weaker
declaration culture. **If declared AI share is near zero there too while their commit velocity and
diff-size distributions have visibly shifted, the declaration signal is not measuring adoption**,
the outer proxy fails, and EXP-44 as designed cannot answer its question at any sample size.
That check costs under three minutes and should run before the panel does.
