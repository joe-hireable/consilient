# CLAUDE.md

@AGENTS.md

`AGENTS.md` is the source of truth for project rules, working principles and boundaries.
Read it. This file adds session-start guidance only.

## Start here

**Stage 3 was entered on 20 August 2026** by Joe, under ADR-0039, which reserves entry to
the principal. Routing, blocking and orchestration behaviour may now be built and run. The
repository holds the observe-only increment in `src/consilient/`, experimental adapters,
research instruments, CI invariants, 45 ADRs and 47 registered experiments.

**Entering the stage is not passing the gates**, and the distinction is the whole of your job
here. `consil doctor` reports `routing_orchestration_enabled: false` and will keep doing so
until every condition passes. Gate B governs *depending* on the harness for work on another
repository — nothing may be pointed at `../hireable-3.0` or `../jobboard-v2`.

Read in this order before doing anything:

0. **`CONSILIENCE.md`** — the Whewell definition and the three rules derived from it.
   Everything else in the repo is downstream of this one sentence. If a brainstorm idea
   cannot be traced to it, say so out loud.
1. `AGENTS.md` — current phase, evidence discipline and hard boundaries
2. `docs/decisions/index.md` — current decision state and supersession trail
3. `docs/10-research/experiment-register.md` — runnable claims and stopping rules
4. `docs/20-design/backends.md` — measured adapter and admission state
5. `docs/40-spec/v0-draft.md` — the approved implementation boundary, and § 3's gates
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
- **Keep the gates honest.** Stage 3 permits building orchestration; it passes nothing.
  Four of the seven conditions were found unpassable on 20 August and three have been repaired
  by ADR-0043 and ADR-0045 — which means the remaining failures are real work, not walls. Do
  not let a gate be crossed by inference, and do not repair a condition by loosening it
  without an ADR the principal accepts.

## What not to do

- Don't point the harness at any repository other than this one. Building orchestration is
  authorised; depending on it elsewhere is Gate B, and Gate B is not passed.
- **Don't put a secret anywhere a public repository can reach it** — not a commit, not
  repository settings, not Actions secrets. A capability needing one runs locally or not at
  all. (Joe, 20 Aug 2026.)
- Don't treat the current draft or a multi-agent agreement as evidence.
- Don't accept architecture in `docs/20-design/` as settled without a falsifiable claim and
  evidence-class-different challenge.
