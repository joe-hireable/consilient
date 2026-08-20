# CLAUDE.md

@AGENTS.md

`AGENTS.md` is the source of truth for project rules, working principles and boundaries.
Read it. This file adds session-start guidance only.

## Start here

The v0 specification is **approved** and the observe-only increment has shipped to
`src/consilience/`. The repository holds that increment, experimental adapters, research
instruments, CI invariants, 34 ADRs and 35 registered experiments. Routing, blocking and
orchestration are still gated on ADR-0015.

Read in this order before doing anything:

0. **`CONSILIENCE.md`** — the Whewell definition and the three rules derived from it.
   Everything else in the repo is downstream of this one sentence. If a brainstorm idea
   cannot be traced to it, say so out loud.
1. `AGENTS.md` — current phase, evidence discipline and hard boundaries
2. `docs/decisions/index.md` — current decision state and supersession trail
3. `docs/10-research/experiment-register.md` — runnable claims and stopping rules
4. `docs/20-design/backends.md` — measured adapter and admission state
5. `docs/40-spec/v0-draft.md` — the unapproved implementation boundary
6. `docs/00-context/conversation-summary.md` — origin and rejected alternatives

## Your job in the current phase

Brainstorm, adversarially. Specifically:

- **Hold every proposal against `CONSILIENCE.md`.** The most common failure mode in this
  design space is structures that look collaborative but are echo — agents agreeing about
  evidence they already shared. Name the different class of facts, or cut it.
- **Attack the β thesis.** It is the load-bearing claim and it has never met a real repo.
  The most valuable thing you can do is find the case where it's wrong or unmeasurable.
- **Check the novelty claim.** `literature-review.md` flags that Meta-Harness (Stanford/MIT,
  COLM 2026) already automates harness search, and several 2026 papers cover
  verification-gated orchestration. Establish honestly what is left that is genuinely new.
- **Resolve authorised evidence gaps.** Pre-register the stopping rule before a run and
  record insufficient data honestly.
- **Keep the gates honest.** The specification is approved for the observe-only
  increment only; do not let Gate A or Gate B be crossed by inference.

## What not to do

- Don't write product implementation code before explicit approval. Experimental adapters,
  research instruments and invariant checks remain permitted under `AGENTS.md`.
- Don't treat the current draft or a multi-agent agreement as evidence.
- Don't accept architecture in `docs/20-design/` as settled without a falsifiable claim and
  evidence-class-different challenge.
