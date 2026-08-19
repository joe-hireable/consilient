# CLAUDE.md

@AGENTS.md

`AGENTS.md` is the source of truth for project rules, working principles and boundaries.
Read it. This file adds session-start guidance only.

## Start here

This repo is **context, not code**. It was assembled in a single chat session on
19 August 2026 to hand off a design position to Claude Code for brainstorming.

Read in this order before doing anything:

0. **`CONSILIENCE.md`** — the Whewell definition and the three rules derived from it.
   Everything else in the repo is downstream of this one sentence. If a brainstorm idea
   cannot be traced to it, say so out loud.
1. `docs/00-context/conversation-summary.md` — how the position was reached, including
   the ideas that were killed and why
2. `docs/10-research/findings.md` — the simulations and what they showed
3. `docs/10-research/literature-review.md` — prior art; several parts of the idea are
   already solved by others, and one central claim of novelty needs checking
4. `docs/10-research/competitive-landscape.md` — who else is building in this space
5. `docs/20-design/architecture-sketch.md` — the current position
6. `docs/00-context/open-questions.md` — the brainstorm agenda

## Your job in the first session

Brainstorm, adversarially. Specifically:

- **Hold every proposal against `CONSILIENCE.md`.** The most common failure mode in this
  design space is structures that look collaborative but are echo — agents agreeing about
  evidence they already shared. Name the different class of facts, or cut it.
- **Attack the β thesis.** It is the load-bearing claim and it has never met a real repo.
  The most valuable thing you can do is find the case where it's wrong or unmeasurable.
- **Check the novelty claim.** `literature-review.md` flags that Meta-Harness (Stanford/MIT,
  COLM 2026) already automates harness search, and several 2026 papers cover
  verification-gated orchestration. Establish honestly what is left that is genuinely new.
- **Work `open-questions.md`** with the user. Nineteen open questions, ordered by how much
  they change the shape of the thing.
- **Do not converge early.** The user has explicitly asked for full brainstorm before spec.

## What not to do

- Don't write implementation code.
- Don't produce a spec document until the brainstorm is finished and the user says so.
- Don't accept the architecture in `20-design/` as settled — it is one turn old and
  has had one reviewer.
