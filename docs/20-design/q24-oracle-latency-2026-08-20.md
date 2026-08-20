# Q24 — β outside coding. The axis is oracle latency, not oracle existence

**Date:** 20 August 2026
**Status:** `[asserted]` throughout unless marked. This is a design argument, not a
measurement. It is offered as a candidate answer to an open question and it should be attacked.

---

## The open question, as the repository states it

`architecture-sketch.md` §36–39:

> Coding is v0 because it supplies cheap automated oracles — tests, typecheck and build —
> against which β can be measured. **Whether β survives outside coding is Q24, and the
> architecture has no measured centre in oracle-free domains until it is answered.**

Joe, 20 August 2026, stating the product:

> *"Humans should be free to dream and not worry about granularity. Focus on the big picture,
> goals, health, career, fun, projects, learning, whatever."*

That makes Q24 load-bearing rather than academic. If β dies outside coding, the harness has a
measured centre in one domain and an unmeasured one everywhere else — which is precisely the
"confident by default" failure it exists to prevent, wearing a wider remit.

## The claim

**The question is not whether a domain has an oracle. Every domain the harness would serve has
one: the world answers back. The question is how long the answer takes, and how hard it is to
attribute.** Coding is not the only domain with an oracle. It is the domain with the *fastest*
one.

Reframed that way, Q24 stops being "does β generalise?" and becomes "what is β's measurement
latency in this domain, and can attribution survive it?" That is an engineering question with a
number attached, which is the kind this project can hold.

## The axis

| domain | exogenous oracle | latency | attribution difficulty |
|---|---|---|---|
| coding — tests | suite passes or fails | seconds | trivial: it names the artefact |
| coding — production | incident, rollback, error rate | hours to weeks | moderate: deploys bundle changes |
| document, memo, plan | was it acted on; did the decision hold | days to months | hard: many inputs |
| learning | can the person now do the thing, unaided | weeks | moderate: testable directly |
| career | did the role, raise or move happen | months to years | very hard: confounded by everything |
| health | measured marker moved and stayed moved | weeks to years | hard, but instruments exist |
| fun, meaning | did the person do it again, and choose it freely | days to months | hard, and self-report is compromised |

Two things fall out immediately.

**1. Every row has an oracle.** None of them requires the human to judge the *artefact*. Each
asks whether the world changed, which is exactly the property `CONSILIENCE.md` demands of a
different class of facts: structures that touch the world are consilient; structures that only
talk are echo.

**2. The rows differ by orders of magnitude in latency, and that is what makes coding v0.**
A test answers in seconds, so β is measurable in a session. A career decision answers in years,
so β on career advice is measurable in principle and useless as a control loop for a system
that has to act this week.

## What this means for the architecture

**β\* — the threshold — should be a function of oracle latency, not a constant per domain.**
Where the oracle is fast, the harness may act on thin evidence, because a wrong decision is
caught quickly and reversal is cheap. Where the oracle is slow, either the harness demands more
evidence before acting, or it acts and *marks the decision unverified for the duration of the
lag*, which is a different and honest thing.

That gives a rule the harness can apply anywhere: **the further the oracle is from the action,
the more conservative the routing, and the longer the decision stays labelled unverified.**
That is one mechanism, domain-blind, matching the architecture's stated posture — rather than
one β-meter for coding and hand-waving elsewhere.

It also predicts, testably, that a harness which ignores this will look best exactly where it is
worst: in long-latency domains nothing contradicts it for months.

## The honest problems, which are not small

**Attribution is the real barrier, not latency.** A test failure names the artefact. A career
outcome does not name the advice. In every slow domain the harness would be claiming credit or
blame for outcomes with many causes, and the naive version of this is astrology with a
changelog. Any implementation must state its attribution method and its error rate, or it is
worse than no measurement.

**Self-report is compromised and it is most tempting exactly where the oracle is slowest.**
ADR-0033 records developers reporting a 20% speedup after a measured 19% slowdown. [cited] In
health, learning and fun the easy instrument is asking the person, and it is the one instrument
this project has already ruled out for tuning. Where only self-report is available, β is not
measurable and the harness must say so rather than substitute satisfaction for verification.

**Some domains may genuinely have no admissible oracle.** If a domain's only available signal is
self-report, the honest posture is that the harness operates there *without* a measured β and
says so at the point of use — not that it invents one. **A domain where β cannot be measured is
not forbidden; it is unverified, and must be labelled unverified.** That is the same discipline
as `insufficient data`, applied to a domain rather than a sample.

## What would make this real

1. **Pick the second domain by latency, not by interest.** The cheapest non-coding oracle is
   *production outcome*, which is already needed for β on code and is days-to-weeks rather than
   months. It is the natural EXP after the retro-verifier.
2. **Write the attribution method down before measuring anything**, with its own error rate. An
   unattributable outcome is not evidence, however clean the number looks.
3. **Report β per domain with its latency**, never pooled. A pooled β across domains with
   different lags is a number with no referent, and it would be the most convincing wrong
   number this project could produce.

## Falsifier

If the production-outcome oracle cannot attribute a defect to an artefact at better than chance
— because deploys bundle many changes and incidents have many causes — then the latency axis is
irrelevant, since even the *second-fastest* oracle fails on attribution. That would mean β is
special to domains with artefact-level oracles, Q24's pessimistic answer is correct, and the
domain-blind claim in `architecture-sketch.md` should be withdrawn rather than defended.

**That test is cheap and it should be run before this document is cited by anything.**
