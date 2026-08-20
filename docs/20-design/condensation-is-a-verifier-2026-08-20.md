# Condensation is a verifier, and β generalises to it

**Date:** 20 August 2026
**Status:** `[measured]` for the corpus facts; `[asserted]` for the architecture argument, which
is this project's inference and is the part to attack.

---

## The proposal

Joe, 20 August 2026:

> *"completely autonomous, dynamic context engineering … I have been out and about all over the
> place and working from my phone. In some cases keeping singular claude code chats live for
> weeks. It just auto condenses at like 90% context and you can carry on pretty reliably. I
> think we can actually build the harness around this premise. A user can maintain one perpetual
> chat/relationship … specific agentic project work can work autonomously on loops with
> perpetual perfect memory potentially using graph neural network architecture."*

## The observation that makes this measurable rather than aspirational

**He has been running the experiment for weeks and the data is on this machine.** [measured]

`~/.claude/projects/` holds **1,495 session transcripts, 654 MB**, the largest single session
**14 MB**. A probe of the six largest found condensation is explicitly recorded:

| record | count in the six largest sessions |
|---|---|
| `system/compact_boundary` | 6 |
| `isCompactSummary` / `compactMetadata` flagged records | 12 |
| `system/away_summary` | 27 |

So the boundary between "before condensation" and "after condensation" is machine-identifiable,
in real long-running agentic work, over a corpus nobody else has. That converts an anecdote into
a corpus.

## The architectural claim

**Condensation is a verifier.** It takes everything the session knows and decides what to keep.
Like every verifier, it has two off-diagonal error rates:

- **it discards something that later mattered** — the false-accept analogue, and the dangerous
  one, because the loss is silent and the session continues confidently;
- **it retains noise at the cost of signal** — the false-reject analogue, which shows up as
  context exhaustion sooner.

`CONSILIENCE.md` clause 3 says a test has an error rate and the project is obliged to measure
it. **If condensation is a test, β generalises to it, and the harness's memory becomes something
this project already knows how to instrument.** [asserted]

This is not a metaphor stretched to fit. The quantity has the same shape, the same failure mode
— silent acceptance — and, unusually, **a ground truth that needs no human**.

## Why the ground truth exists here and nowhere else

Today's largest finding was that β's human ground truth is unavailable on an AI-orchestrated
corpus: the maintainer cannot adjudicate his own pull requests. That constraint does **not** bind
here.

**The oracle is the session's own subsequent behaviour.** A fact present before a
`compact_boundary` either is or is not correctly used after it. Referenced-and-correct,
referenced-and-wrong, and re-derived-from-scratch are all observable in the transcript, without
asking anyone anything. [asserted]

That makes condensation the **first quantity in this project with a cheap, exogenous, automatic
oracle** — which by the argument in [`q24-oracle-latency`](q24-oracle-latency-2026-08-20.md) is
exactly what determines whether something can be measured at all. Its oracle latency is minutes,
not months.

## What to measure, in order of cost

1. **Condensation frequency and session longevity.** How often does a boundary fire, at what
   context fraction, and how long do sessions actually survive? Pure counting over 1,495
   transcripts.
2. **Retention rate.** Of the entities, decisions, file paths and constraints established before
   a boundary, what fraction is still correctly used after it? This is the β analogue and it is
   the headline number.
3. **Loss consequence.** Of the losses, how many caused an observable defect — a re-derivation,
   a contradiction, a repeated question, an undone decision? A discarded fact nobody needed
   again cost nothing. **The rate that matters is loss-that-bit, not loss.**
4. **What predicts survival.** Recency, repetition, position, whether it was in a tool result
   versus prose, whether it was ever acted on. This is where a learned component could earn its
   place — and only here, because only here is there a label.

## The honest problems with the proposal as stated

**"Perpetual perfect memory" is not achievable and the phrase should not survive contact with
this repository.** Condensation is lossy by construction; that is what it is for. What is
achievable, and what this architecture already has, is **lossless provenance with lossy recall**:
the append-only trajectory keeps everything, the working context keeps a summary, and the summary
is a *projection* of the record exactly as SQLite is (ADR-0006). Anything the summary drops
remains recoverable. **That is a stronger claim than "perfect memory" because it is true.**
[asserted]

**A graph neural network is a solution in search of its training signal, and the signal is the
whole difficulty.** Two questions must be answered before the architecture is chosen, not after:

1. *What is the learning task?* If it is retrieval, a GNN is heavy machinery against embedding
   search plus the existing SQLite projection, and the burden is on the GNN to beat that
   baseline. If it is **predicting which context will matter**, that is a genuine learning
   problem — and measurement (4) above is precisely its label set.
2. *What gates it?* **ADR-0003 excludes a learned routing policy from v0**, and EXP-07 tested
   reopening it: the single-attempt median multiplier was 1.69×, below the pre-registered 2×
   trigger, so the rule held. A learned memory is a learned component under the same reasoning
   and should face the same pre-registered trigger rather than arriving through a different door.

The honest sequence is therefore: **measure retention with no learning at all, establish the
baseline, and only then ask whether anything learned beats it.** A GNN that is not compared
against recency-plus-repetition is not a result.

**"Learning the user implicitly" already has a substrate and does not need new architecture.**
The trajectory is an append-only record of what the user accepted, corrected, reversed and
ignored. What is missing is not a model; it is that **the meter has never received a row**.
Implicit learning built on an empty record would be learning from nothing.

## What this changes

Condensation moves to the front of the research queue, ahead of anything requiring human
labels, for one reason: **it is the only place where this project can measure a verifier's error
rate today, automatically, on a corpus it already owns.** Every other β is blocked on ground
truth that is unavailable, expensive or two months old.

If the thesis is right — that a test's error rate must be measured before it is trusted — then
the harness's memory is the cheapest possible demonstration of it, and the most immediately
useful, because every long-running session depends on it.

## Privacy

These transcripts contain private repository content, credentials-adjacent material and
everything Joe has done on this machine. **They are mined locally and only aggregate counts
leave.** Same discipline as the private measurement corpora, and the same check applies: no
paths, no content, no excerpts in any tracked file.

## Falsifier

If retention rate turns out to be near 100% — condensation almost never drops anything that is
later needed — then it is not an interesting verifier, β does not usefully generalise to it, and
this entire direction should be abandoned in favour of the ordinary β work. **That is one
counting pass away and should be established before anything is built.**

Conversely, if retention is low but **loss-that-bit** is near zero, then condensation is
discarding freely and correctly, the architecture needs no memory layer at all, and "perpetual
memory" would be solving a problem that does not exist. Both outcomes retire the proposal, which
is why measurement (3) matters as much as (2).
