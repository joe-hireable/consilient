# 0099. Fund by sponsorship alone, and stay outside trader status

- **Status:** ACCEPTED
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision turns on a legal threshold, not an unknown parameter.

## Context

The principal asked for a commercial model with no risk of costing him anything not covered by the
user, aimed at facilitating capability rather than making money: "I dont care if I make no money but
I dont want any risk of it costing me anything not covered by the user themself."

Eight research angles answered how to monetise. The adversarial review observed that **none asked
whether to**, and surfaced a threshold nobody had framed as a decision.

While Consilient is gratuitous MIT software, its author is very likely not a trader. **The first
affiliate commission plausibly makes him one** under the Consumer Rights Act 2015 s.2, and consumer
protection duties then attach to the whole product, for every user, permanently. Twenty-five pounds
of referral revenue buys an unbounded and irreversible consumer-law surface.

## Decision

Consilient is funded by **sponsorship alone** — a route that sells nothing, takes no commission and
does not create trader status. No affiliate revenue, no consolidated billing, no hosted paid tier
and no advertising is implemented. The commercial designs stay documented as an end state so a later
decision is cheap; none is built.

Advertising is refused outright rather than reconciled. An equal-rate affiliate structure was
proposed as a way to hold both revenue and neutrality, and it is rejected: **fixing the price of
influence is still a price.**

## Evidence

- `[cited]` Consumer Rights Act 2015 s.2 (trader definition) and s.49 (reasonable care and skill,
  non-excludable). Analysis in `../00-context/commercial-model-2026-08-23.md`.
- `[measured]` Consolidated billing fails four independent tests — Payment Services Regulations 2017
  Sch 1 Pt 2 para 2(b), FCA PERG 15.5 Q33A, Electronic Money Regulations 2011 reg 2(1), and HMRC's
  deemed-supplier treatment. Quoted with sources in the commercial model document.
- `[measured]` GitHub Sponsors charges 0% and involves no sale, so it does not create trader status.
- `[asserted]` The principal has said he will accept making no money, which makes this route a fit
  rather than a compromise. That is unusual and worth stating plainly.

## Evidence against

- `[asserted]` Sponsorship funds very few maintainers at a level that sustains full-time work. If
  Consilient succeeds and needs sustained maintenance this decision comes under real pressure, and
  pressure is when promises break rather than when they are tested.
- `[measured]` Six research agents asked to verify one checkable figure — OpenRouter's valuation —
  returned six different answers, each stated confidently, while agreeing with one another on
  everything unfalsifiable. **The consensus in the underlying research is style, not evidence**, and
  this ADR discounts it accordingly.
- `[asserted]` Deferring forecloses nothing permanently, but it means no revenue funds the hosted
  conveniences that would help users who cannot self-host. Those users are worse off under this
  decision than under a paid tier.

## Consequences

**Positive** — no trader status, no consumer-law duties, no payment regulation, no disclosure
obligation, no third-party security assessment, and no incentive anywhere in the system to prefer
one tool over another.

**Negative** — no revenue. Hosted inference and managed storage are not funded and therefore not
offered.

**Neutral but load-bearing** — the moment any commission is accepted this ADR must be superseded
rather than quietly departed from, because the threshold it protects is crossed once and never
recrossed.

## Enforcement

- Check: `.github/scripts/check_no_paid_placement.py` — refuses any ranking, ordering or default
  that varies with a commercial relationship.
- Check: `.github/scripts/check_no_funds_custody.py` — refuses code that collects user funds for
  onward payment.
- Fails CI: yes, both.
- Added in the same commit as the implementation: **no — neither check exists today.** Until they
  run in `invariants.yml` these prohibitions are documentation, and this ADR says so rather than
  implying otherwise.

## What would overturn this

A measured finding that sponsorship cannot fund the maintenance the project actually needs, together
with a specific revenue route whose consumer-law consequences have been priced by a solicitor rather
than estimated here. The trigger is a funding shortfall with numbers, not an opportunity.
