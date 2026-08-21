# Ruflo: what to take, what to refuse, and the one comparison that matters

**Date:** 20 August 2026
**Status:** `[cited]` for everything attributed to Ruflo's own documentation, read on 20 August 2026;
`[measured]` where this repository's own results are quoted; `[asserted]` for the judgements.
**Subject:** [`ruvnet/ruflo`](https://github.com/ruvnet/ruflo), MIT, 68.5k stars, 8.2k forks, 7,376
commits.
**Requested by Joe**, with his prior stated up front: *"I feel it's a mess and overengineered and
overthought and we want better control and our own proprietary agent orchestration harness but take
any good elements."* That prior is not treated as the conclusion below; where the evidence supports
it, it is said so, and where it does not, that is said too.

---

## The one comparison that matters, and it is not about features

Ruflo is a meta-harness. So is this. It has 68.5k stars, ~210 MCP tools, 100+ specialised agents,
Queen-led swarm hierarchy with Raft, Byzantine and Gossip consensus topologies, an HNSW vector
memory, a self-optimising neural architecture, and a security layer. It is, by any measure of
adoption, the field.

I asked its documentation one question: **does it measure the error rate of its own verification?**

> *"The documentation reports success rates and performance speedups, but does not disclose false
> positive/negative rates, precision, or validation methodology for its core mechanisms (swarm
> consensus, security gates, or agent decisions)."* [cited]

It has "quality gates" that grade agent setups 1–100. It has `ruflo verify`, which cryptographically
proves installed bytes match a signed witness — real, and useful, and a statement about *supply
chain* rather than about *work*. It reports `recall@10 ~0.99` for vector retrieval, which is an
accuracy figure for a search index and not for a decision.

**Nothing states how often a gate passes something bad.**

That is this programme's entire thesis, restated by the largest system in the category. It is the
second independent data point on the axis: the first was **Ratchet** (arXiv:2605.22148v3), which
*does* measure its judge's error rate and which refuted this repository's founding novelty claim.
Ruflo goes the other way. **The honest position after both: measuring β is not unprecedented, but it
is not the norm either, and the norm at 68.5k stars is not to.** That belongs in `P3-echo.md`'s
related work, stated exactly that carefully.

## What is worth taking, and one item is worth more than the rest combined

### 1. Signed agent identity — take this, it is the hole we have

> *"Zero-trust federation via mTLS + ed25519 signatures for cross-machine collaboration. Agents on
> different machines, orgs, or cloud regions can discover each other, prove who they are, and
> collaborate on tasks."* [cited]

**This is precisely what three of this repository's invariants lack.** V0-18 (only the principal may
author their own decision), V0-28 (a human decision must arrive by a declared local channel), and
the budget-state ingress all protect **declared** provenance. Each carries the same caveat in its
own docstring: `actor`, `via` and the `openrouter-probe` identity are strings in a JSON field, and a
hand-written line defeats all three.

Ed25519 signatures over trajectory events are the missing half. This is not a large piece of work
and it is the single highest-value thing in Ruflo for this project. It should become an ADR and an
experiment rather than a vague intention — the specific question being whether signing at the
`append()` chokepoint closes the gap without making the log unreadable by anything that lacks the
key.

### 2. Cross-machine agent discovery — take the shape, defer the need

Relevant when Joe's Slack, phone and email connectors arrive (ADR-0041/0042), and irrelevant before
then. Worth reading their federation handshake when that work starts, not now.

### 3. Trajectory-based learning into a "ReasoningBank" — **already refuted here**

Ruflo learns from trajectories into a persistent reasoning store. This project **measured** that
idea and retired it: EXP-45 found condensation retention of **40.71%** with consequential loss of
**0.00%**, over a median session of **2.7 minutes** rather than the weeks the design assumed.
[measured]

Adopting it would be adopting an idea our own evidence rejects. Recorded here so it is not
re-proposed in six months by someone who read the same README.

## What to refuse, with the reason rather than the reflex

### Byzantine consensus between agents is echo with extra steps

Ruflo's swarm coordination uses Raft, Byzantine and Gossip consensus among agents. **This is the
clearest example available of a structure that looks collaborative and is not.**

`AGENTS.md` working principle 6 and ADR-0010 rest on a theorem (Ao, Gao & Simchi-Levi 2026,
arXiv:2603.26993): *without new exogenous signals, a delegated agent network cannot beat a
centralised decision-maker with the same information.* Byzantine fault tolerance is designed for
nodes with **independent inputs** and the possibility of adversarial ones. Agents reading the same
repository, given the same context, are neither. Running consensus over them multiplies cost and
produces agreement that is a *property of the shared input*, not evidence about the world.

This repository measured that failure mode directly on 20 August: two model families reported β
within **0.0085** of each other while differing on **16 of 75** underlying labels. The apparent
agreement was arithmetic cancellation, **14× narrower than the inputs warranted.** [measured]
Consensus machinery would have reported that as convergence.

**Do not adopt agent consensus. The different class of facts is the scarce resource, and no
consensus protocol creates one.**

### "89% routing accuracy" — accuracy against what oracle?

An accuracy figure needs a ground truth, and a ground truth needs its own error rate. On 20 August
this project had two oracles disagree on 16 of 75 labels, and the disagreement was the finding. A
routing accuracy quoted without naming its oracle is exactly the claim β exists to interrogate.

### "1.3×–1953×" — a range spanning three orders of magnitude

That is not a measurement, it is a selection of favourable cases presented as a range. Working
principle 2 applies: sign and threshold, never point estimates, and never a headline number whose
generating conditions are unstated.

### ~210 MCP tools and 100+ agents — the literature is already against this

`bibliography.md` carries PA-Tool (arXiv:2510.07248) and *How Many Tools Should an LLM Agent See?*
(arXiv:2605.24660). Tool-selection quality degrades with surface area. A catalogue of 210 tools is a
liability presented as a feature, and 100+ named agent roles is taxonomy rather than capability
unless each role introduces a different class of facts — which is ADR-0010's test, and which
role-naming alone does not pass.

### HNSW sub-millisecond retrieval — solving the part that was not the bottleneck

Retrieval latency was never what made memory hard here. EXP-45 measured what did: consequential
recall was 0.00% lost, and sessions are minutes rather than weeks. A faster index over a store we
measured as unnecessary is speed applied to the wrong problem.

## Joe's prior, assessed rather than echoed

He called it *"a mess and overengineered and overthought"*. On the evidence: **the architecture is
over-scaled for its measured evidence base**, which is a sharper and more defensible claim than
"a mess". The engineering is real — 7,376 commits, a Rust backend, a WASM gallery, working
federation — and dismissing it would be as unserious as adopting it wholesale.

The defensible criticism is specific: **its most elaborate machinery (consensus topologies,
100+ agents, 210 tools) is the part with the least evidence behind it, and its best idea (signed
cross-machine identity) is the part this project actually needs.** An architecture that inverts
that ratio is what "overengineered" means precisely.

## What this changes here

1. **Write an ADR for signed trajectory events**, naming ed25519 at the `append()` chokepoint, and
   an experiment measuring what it costs and what it breaks. This is the recommendation.
2. **Add Ruflo to `P3-echo.md`'s related work** as the second data point on whether measuring
   verifier error is standard practice. It is not, and Ratchet shows it is not unprecedented either.
3. **Record the consensus refusal in the design record**, so the next reader of a popular swarm
   framework has the theorem and the 14× cancellation measurement to hand rather than re-deriving
   the objection.

## Reversal and falsifier

**Reversal:** `git revert`; this document is the whole of the change, and nothing was adopted.

**Falsifier:** this assessment rests on Ruflo's own documentation, read once, not on running it.
If its repository contains a measured false-accept rate for its quality gates that the README does
not surface, the central comparison above is wrong and should be withdrawn rather than softened.
**The cheap check is to run its own test suite and look for the number** — which has not been done,
and which is the honest limit of this document.

A second falsifier, on the consensus refusal: if a swarm consensus protocol can be shown to
aggregate agents that genuinely hold *different* evidence — different corpora, different tools,
different retrieval — then it is not echo and the objection does not apply to that configuration.
Nothing in Ruflo's documentation establishes that its agents do, but nothing establishes that they
cannot.
