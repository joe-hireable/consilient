# Ruflo: what we adopt, what we measure first, and what we could give back

**Date:** 20 August 2026
**Status:** `[cited]` for both licences, read from the repositories on 20 August 2026; `[measured]`
for this project's own results; `[asserted]` for the plan.
**Governs:** the adoption path under [ADR-0036](../decisions/0036-upstream-first-adopt-contribute-never-silently-fork.md)
(upstream-first — adopt over build, PR rather than fork). ADR-0036 is PROPOSED, so this plan is a
proposal under a proposal and nothing here is authorised to be sent anywhere.

---

## The licence question, settled

Joe asked what happens *"if licensing doesn't allow"* direct adoption. **It does allow it.**

| | licence | copyright |
|---|---|---|
| `ruvnet/ruflo` | **MIT**, standard, no riders | `Copyright (c) 2024-2026 ruvnet` |
| this repository | **MIT** | `Copyright (c) 2026 Joseph Brown` [ADR-0004] |

Verified by reading Ruflo's `LICENSE` rather than its README badge: *"standard MIT license with no
additional clauses, commercial-use restrictions, riders, or dual-licensing terms."* [cited]

So both branches Joe named are open, and the constraint is evidence rather than law:

- **Direct adoption is permitted**, requiring only that the copyright notice and licence text travel
  with any copied code. MIT-into-MIT is the cleanest case there is.
- **Upstream contribution is permitted**, and ADR-0036 prefers it to building.

**The fallback branch — "if licensing doesn't allow, use it to inspire and build better custom" —
does not fire.** Anything we decline to take, we decline on the evidence, and we must say that
rather than implying our hand was forced.

## Three buckets, and the middle one is the point

### Refused on our own measurements — no experiment needed

| item | why, and it is not an opinion |
|---|---|
| ReasoningBank / persistent trajectory memory | EXP-45: retention **40.71%**, consequential loss **0.00%**, median session **2.7 minutes** rather than weeks. [measured] |
| HNSW sub-millisecond retrieval | Same experiment. Retrieval latency was never the bottleneck; a faster index over a store measured as unnecessary is speed applied to the wrong problem. |

These are settled by evidence this project already produced. Re-opening them needs new evidence, not
a new reading of the same README.

### Adopted after measurement — EXP-53

**ed25519 signed events at the `append()` chokepoint.** This is the one mechanism in Ruflo worth
taking, because it is the exact hole three of our invariants share: V0-18, V0-28 and the
budget-state ingress all protect *declared* provenance and each says so in its own docstring.

**It is not adopted yet, and that is deliberate.** EXP-53 asks four questions whose answers change
the design and one that could kill it — whether a reader **without** the key can still audit the
log. If it cannot, the cure fails rule one: provenance means the record can be checked, and a record
only its author can check is not a record.

It also asks the question nobody enjoys: EXP-16 measured **structural confusion**, not forgery, and
a signature stops forgery. **This may close a hole nothing has ever come through.** Better to know
that before building than after.

### Refused on theory, now to be measured — EXP-52

**Swarm consensus** — Queen-led hierarchy with Raft, Byzantine and Gossip topologies — is Ruflo's
largest mechanism, and `ruflo-assessment-2026-08-20.md` refused it citing a theorem and a
cancellation measurement. Joe's objection to that is correct and is the reason EXP-52 exists:

> *"If we feel like some of the more elaborate ruflo stuff is unproven we can create experiments to
> decide what to adopt and what not to."*

A refusal derived from a theorem is a prediction. EXP-52 runs it over four arms on EXP-47's mutant
corpus, and **it can go against us**: if voting over shared evidence materially beats a single
agent, ADR-0010 is too strong, the refusal is withdrawn, and Ruflo's mechanism comes back onto the
table. That outcome has a stopping rule requiring it be reported as loudly as the favourable one.

The same experiment settles the tool-surface and agent-count questions indirectly. If arm 3
(cross-family, identical evidence) matches arm 2 (same family, identical evidence), then adding
*kinds* of agent without adding *classes of evidence* buys nothing — which is the general form of
the objection to 100+ named roles and 210 tools, tested rather than cited.

## What we could give back, and why it is the obvious thing

ADR-0036 requires outbound PRs to meet the same bar as inbound. The honest question is what we have
that Ruflo does not, and there is exactly one answer.

Its documentation reports success rates and speedups, and **discloses no false-accept rate,
precision, or validation methodology for its quality gates, swarm consensus, or agent
decisions.** [cited] It grades agent setups 1–100 with nothing stating how often a gate passes
something bad.

We have that instrument, it is small, and it is MIT.

**Proposed contribution, scoped but not started:** mutation-testing-based false-accept measurement
for Ruflo's quality gates — the EXP-47 method, which needs no human labels and ran 1,931 mutants in
104 seconds. A gate that reports *"grade 87/100, measured β = 0.31 [0.29, 0.33]"* says something the
grade alone cannot.

**Three reasons to be careful before offering it:**

1. **It is a criticism arriving as a gift.** The PR's substance is "your gates have an unmeasured
   error rate", and maintainers of a 68.5k-star project may reasonably read it that way. It should
   be offered as an addition, with their framing, not ours.
2. **Our own number would be under the same scrutiny.** EXP-49 measured this project's *research
   instruments* at β = 0.6825 against its product code's 0.3345, with **32.7% of mutants in
   functions where nothing is caught at all.** [measured] Arriving with an instrument while that
   sits in our own repository is fair game, and we should say it first.
3. **It is outward-facing and it is Joe's.** Opening a PR against another organisation's repository
   is publication. Nothing here does that, and nothing will without him.

## What this document does not do

No code was copied, no PR opened, no dependency added, nothing sent anywhere. Two experiments are
registered and unrun. **The adoption decisions are deferred to their results**, which is the whole
point of registering them.

## Reversal and falsifier

**Reversal:** `git revert`; the plan and both registrations disappear and Ruflo remains assessed but
un-acted-on.

**Falsifier:** the licence reading is from Ruflo's `LICENSE` file at one commit. If any component is
separately licensed — the Rust backend, `Cognitum.One`, the npm plugins, the hosted services — the
per-component terms govern and this plan's "MIT into MIT" simplicity is wrong. **Check the specific
file's header before copying any specific line**, which is the ordinary discipline and not a
special caution.
