# 0048. Open source first, and paid facilitation is prepaid — never in arrears

- **Status:** **ACCEPTED 20 August 2026.** Decided by Joe Brown across several messages this
  evening. This ADR records his decision; it does not make one.
- **Date:** 2026-08-20
- **Deciders:** Joe Brown. The constraints are his; the mechanism, the objections and the failure
  modes below are mine.
- **Relates to:** [`0004`](0004-licence-mit-dco-and-the-cla-question.md) (MIT),
  [`0024`](0024-commercialisation-and-telemetry.md),
  [`0044`](0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md) (the budget
  primitive this depends on), [`0036`](0036-upstream-first-adopt-contribute-never-silently-fork.md)
- **Inquiry tier reached:** T0 assert — a commercial policy, correctly the principal's.
- **Executable model:** none. No dispersed prior; the parameters are preferences with one hard
  arithmetic constraint.

## Context

Joe, 20 August 2026, across four messages:

> *"Some of the front end stuff we can charge for if we are facilitating certain things for
> users — primarily everything is open source but we can offer cloud plans to users to make
> management easier etc. like Roo Code and Cline etc have done."*

> *"We're not after making loads of money so be as minimal pricing as possible but we do need to be
> profitable for anything that costs on my cloud or anything. We can use Firebase/GCP etc, offer
> hosting."*

> *"we can offer premium facilitation such as model training for users that don't have the capacity
> etc but do it on Fireworks or Google Cloud or whatever and **only when users have covered the cost
> and margin up front. Open source always comes first.**"*

> *"open source first though"*

He said it three times unprompted. It is the constraint, not the caveat.

## Decision

1. **Open source first, and that is a test the product must pass, not a licence line.** Every
   capability must be fully usable by someone who pays nothing, runs locally, and never contacts a
   server we operate. A feature that only works hosted is a feature built wrong. MIT throughout
   (ADR-0004).
2. **We charge only for facilitation** — running something on our infrastructure that the user could
   run themselves but does not want to, or cannot. Never for the capability itself, never for a
   licence key, never for a limit lifted.
3. **Prepaid, always. Never in arrears.** Cost *and* margin are collected before the work starts.
   No invoicing, no overage, no credit. This is Joe's constraint, and it happens to eliminate the
   entire class of risk that killed the one metered composition this project attempted.
4. **Minimal margin, sized to cover cost plus variance — not to maximise revenue.** The target is
   solvency, not profit. Where a number is needed, it is the smallest one that survives a bad month.
5. **Local training is free and unfacilitated.** A user training an open-weight model on their own
   data, on their own device, pays nothing and tells us nothing. Hosted training (Fireworks, GCP)
   exists only for users without the hardware, and is prepaid like everything else.
6. **Domain: `consilient.dev`.**

## Why prepaid is the load-bearing clause

It looks like a billing preference. It is the strongest engineering constraint in this ADR.

**A prepaid system cannot overspend on a user's behalf.** The budget primitive shipped today
(ADR-0044) is refuse-only by construction — no HTTP client, no credential read, no code path that
performs a call — and it defaults to refusing: a configuration with no ceiling means **no**, not
unlimited. Prepaid facilitation is the same shape one level up. The ledger cannot go negative
because nothing starts until it is positive.

Compare the alternative this project has already measured. The one metered composition attempted
here *"failed before artefact production with no diff or usage telemetry; delayed cumulative billing
prevents per-run attribution."* [measured] **Billing in arrears requires attribution to work
perfectly. Billing in advance does not.**

## Evidence against

- **Prepaid is worse for users and will cost adoption.** Every competitor bills after use. Asking for
  money before a job runs is friction at the exact moment of intent, and some users will simply
  leave. That is a real cost, accepted for a real property.
- **"Cost plus margin" is not computable in advance for a training run.** Fireworks and GCP price by
  consumed compute, and a fine-tune's duration is not known before it starts. **So the quoted price
  must be a ceiling, with the unused remainder refunded or credited** — which is harder to build than
  a meter, and this ADR does not pretend otherwise.
- **Open-source-first and hosted convenience pull against each other over time.** Every open-core
  company has felt the pull toward making the hosted path quietly better. The stated test — *fully
  usable by someone who pays nothing and contacts no server* — is the defence, and it needs to be a
  CI check rather than an intention, or it will erode exactly as this project's documented `llm()`
  chokepoint eroded into five access paths.
- **Roo Code and Cline are cited as the model but have not been studied.** Their pricing, their
  open-core boundary and whether either is solvent are all unexamined here. Citing a precedent
  without reading it is the failure this project recorded when a founding claim was refuted by an
  unread paper.
- **Nobody has costed anything.** There is no GCP or Fireworks quote, no unit-economics model, and no
  measured demand. Every number implied by this ADR is a placeholder and none may be quoted as a plan.

## Consequences

**Positive.** The architecture is forced local-first, which is also what makes offline operation and
user-owned training coherent rather than bolted on. And the system cannot lose money on a user.

**Negative.** Prepaid metering with refunds is more machinery than post-billing, and it must be built
before the first paid run rather than after.

**Neutral but load-bearing.** This makes the open-source path the **product** and the hosted path an
accessory. Any future decision that inverts that is a supersession, not an adjustment, and should be
written as one.

## Enforcement

Every rule ships with its check. **None of these exist yet — nothing commercial has been built — and
they are named here so that the first commit which needs them cannot pretend they were not required:**

- **Check:** a test asserting no capability requires a network call to a Consilient-operated service.
  This is open-source-first expressed as code, and it is the one that will come under pressure.
- **Check:** no facilitated job may start without a settled prepayment covering its ceiling. The
  budget primitive's shape — refuse by default, no ceiling means no — extends directly.
- **Check:** the quoted ceiling and the actual consumed cost are both recorded per job, so the refund
  path has an auditable basis and margin can be measured rather than assumed.
- **Check:** a test asserting the local training path never transmits user data off-device.

## What would overturn this

If costing shows minimal margin cannot cover variance at any realistic volume, the choice is a higher
margin or no hosted offering — **not** billing in arrears, which trades a solvency problem for an
attribution problem this project has already measured itself failing.

If the open-source-first test ever has to be weakened in order to ship a hosted feature, that is the
moment this ADR is being abandoned, and it should be superseded openly rather than quietly qualified.
