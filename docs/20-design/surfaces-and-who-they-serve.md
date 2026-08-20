# Surfaces — CLI now, what unlocks a frontend, and who it would serve

**Status:** design position, 20 August 2026. Nothing here is approved and nothing here is
scheduled. [asserted] ADR-0007 — *CLI only, and build no review surface* — is **ACCEPTED and
still governs**. This document exists so the surface roadmap is derived from the measurements
that would unlock it, rather than from enthusiasm. [asserted]

Joe's ambition, in his words, recorded once and not repeated: a project that is
*"world class, world leading, industry moving, life changing, business transforming"*. [asserted]
What follows is what would have to be **true and measured** for any of that to be earned.

## 1. Why the CLI is not a limitation

ADR-0007's reasoning is arithmetic, not taste. The system's ceiling is

> `n_max = T_agent_cycle / T_effective_review` [algebra]

At realistic numbers — 25-minute cycles, 8-minute reviews — that is roughly **three agents**.
[algebra] It does not matter how many agents run or how cheap they are: production above the
review rate makes a queue, not progress. `work-modes.md` records the second-order effects that
make it worse, since queued diffs against one repository invalidate each other. [asserted]

There are exactly **two levers** on that ceiling:

1. **Reduce what needs reviewing** — a critic tier that filters bad diffs before a human sees
   them. This is EXP-08, and critic recall ≡ 1 − β. [algebra]
2. **Reduce the cost of each review** — `T_effective_review`. **That is what a surface is for.**

A frontend is therefore not a nicety bolted onto a CLI tool. It is one of the two things that
can move the only quantity capping the entire system. [asserted] But it is the *second* lever,
and ADR-0007's position is that the first should be measured before the second is built.

## 2. What actually unlocks a surface

ADR-0007 names its own reopen conditions, and both are already registered experiments:

| Condition | Experiment | Status |
|---|---|---|
| Measured critic recall leaves the ceiling at ~3 agents, so review-time reduction is the only lever left | **EXP-08** | `BLOCKED: critic tier` |
| The β-verdict prompt has unacceptable completion rates, so the human touchpoint needs a richer surface | **EXP-19** | `BLOCKED: feedback prompts` |

**Nothing is designed before one of those fires.** [asserted] This is not procedural caution:
a review surface built before EXP-08 would be built without knowing how much review it needs
to absorb, which is the one number that determines what it should be.

## 3. Who the surfaces would serve, and what gates each

### Developers — gated on EXP-08 or EXP-19

The nearest surface. Its job is narrow and measurable: **lower the wall-clock and cognitive
cost of accepting or rejecting an artefact**, without raising the rate at which bad artefacts
are accepted. Both halves matter, and the second is the trap — see §5.

### Non-developers — gated on Q24, not on design effort

The architecture is domain-blind; coding is v0 only because tests, typecheck and build are a
cheap automated oracle. [asserted] A non-developer surface is the same harness pointed at work
that **has no such oracle**, which runs directly into Q24: β is only defined where checks
exist. [measured]

So the blocker on a non-developer product is not design or engineering. It is that **nobody
knows what β means for a strategy memo**, and the honest answer today is that it may be
unmeasurable there. [asserted] A beautiful interface over an unmeasured oracle is the exact
failure this project exists to name.

### Contributors — available now

Lucy and Chris were asked on 20 August 2026, and were given the real open problem rather than
a decorative one: how to hand control back to someone who stopped watching an hour ago and has
lost context; when an interruption is worth its cost, given that asking too often measurably
backfires; and how to surface that something went wrong without burying it or crying wolf.
[measured] Those are design questions with evidence behind them and no answers yet.

## 4. QA automation, user research and A/B testing are one thing

Joe listed these separately. They are the same mechanism, and naming it is the most useful
thing in this document: **each manufactures an oracle where none existed.** [asserted]

- **QA automation** manufactures an oracle for code behaviour.
- **User research** manufactures an oracle for whether a design serves a person.
- **A/B testing** manufactures an oracle for whether a change helped, at population scale.
- **Synthetic users and sandboxes** manufacture the conditions under which any of the above
  can run cheaply and repeatedly.

That is the same mechanism by which fuzzing found defects experts had missed — cheap iteration
against a cheap oracle, not insight. [cited] It is also why this is not a separate product
line: **β is the rate at which an oracle accepts bad work, so building oracles and measuring
oracles are the same programme viewed from two ends.** [asserted]

The danger is recorded in Q32 and must not be lost in the enthusiasm: **a system that
generates its own tests and then measures how often those tests accept bad work is grading its
own homework.** EXP-13 already pre-registers the hazard that a system edits its tests into
agreement with itself. [cited] Every oracle this project manufactures needs its own β, and the
regress has to stop somewhere a human stands.

## 5. What must not be built, and why the evidence says so

These are not stylistic preferences. Each has a measurement behind it from 20 August 2026.

- **No surface that shows model reasoning without measuring its effect on acceptance.**
  Explanations raised relative reliance on the model from 29.59% to 38.87% while leaving the
  ability to *reject* it statistically unchanged. [cited] A "show your working" panel is an
  acceptance amplifier until proven otherwise.
- **No confidence display, and no surfaced token-level uncertainty.** Uncertainty highlighting
  reduced over-reliance only by increasing under-reliance, lowered perceived accuracy across
  every category, and produced the largest confidence increases exactly when participants chose
  wrongly. [cited]
- **No composite score, dashboard health-index or single quality number.** Satisfaction and
  quality are anti-correlated through a measured mechanism: sycophantic output was rated 9%
  higher quality and 13% more likely to be reused while degrading the outcome. [cited] V0-21
  forbids compositing.
- **No thumbs-up, no "did that help?", no satisfaction rating as an outcome.** Developers
  reported a 20% speedup after a measured 19% slowdown. [cited] It is a broken sensor in
  exactly this population.
- **No always-on visibility as a default.** More watching is not better watching; the
  interventions that most reduce over-reliance are the ones users found harder, preferred less
  and trusted less, and their benefit fell unevenly. [cited]

## 6. The falsifiable claim

> A review surface earns its place only if it **reduces `T_effective_review` without raising
> β** for the same repository, task family and verifier contract. [asserted]

Both halves are measurable with instruments this project already has: the trajectory records
time from artefact completion to human acceptance, and β is the product. A surface that halves
review time while doubling the false-accept rate has made the system worse and would look like
a success on every metric a normal product team would collect. [asserted]

## What would overturn this document

- EXP-08 measures critic recall high enough that the parallelism ceiling rises well above
  three. Review-time reduction stops being a binding lever, and the developer surface drops
  down the priority list rather than up it. [asserted]
- Q24 resolves against β outside coding. The non-developer product does not become harder — it
  becomes a different product, and this project should say so plainly rather than build toward
  it. [asserted]
- A surface is built and measured to reduce review time while raising β. The claim in §6 is
  then wrong in its optimistic direction, and the honest response is to stop building surfaces,
  not to adjust the metric. [asserted]
