# Architecture sketch

**Status: one turn old, one reviewer, conflict of interest declared. Expect to rewrite.**
This exists to be attacked in the brainstorm, not to be implemented.

---

## What v0 is, in one sentence

A β-meter with a cascade attached.

Not a router. Not an agent framework. An instrument that measures whether a repository's
automated checks can be trusted, and derives its own routing depth and parallelism ceiling
from that measurement.

## Domain posture (added 19 Aug 2026)

The harness is **domain-blind**. It orchestrates any agentic work — chats, projects,
tasks, scheduled and background runs, parallel workflows (`work-modes.md`) — through two
execution paths:

- **Delegated:** hand the task to whatever agent the user favours (Claude Code with their
  own credentials, Codex, Antigravity, any other). Context discipline is inherited there
  (Claude Code ships MCP tool search natively since v2.1.7 — `context-loading.md`).
- **Native:** execute directly against open models via OpenRouter or locally, with the
  harness supplying tools, skills, MCPs and context management (`capability-layer.md`,
  `context-loading.md`).

**One loader, task-appropriate context, no per-domain variants.** There is no "code mode"
and no "document mode"; a mode is a scheduling pattern, not an architecture
(`work-modes.md`). Coding is v0 because it is the only domain with a cheap automated
oracle — tests, typecheck, build — so it is where β can actually be measured. That is a
measurement decision, not an architectural one. Whether β survives outside coding is
**Q24**, and the architecture has no centre in oracle-free domains until it is answered.

## The five components, and nothing else

### 1. The β-meter
Instruments every run with `verifier_verdict` and `human_verdict`. β is the rate at which
those disagree in the *accept* direction — checks passed, human rejected the diff.

Gates everything downstream:
- refuse to cascade below a repo's measured β\* for the capability gap in play
  (`findings.md` §2)
- set parallelism at `T_cycle / T_eff_review` rather than letting the user pick a number

**Open:** how few samples give a usable estimate (Q2); whether β is one number or a vector
per check class (Q10); whether cheap proxy labels (reverted commits, follow-up fixes,
escaped bugs) can substitute for human verdicts.

### 2. The cascade
Cheap → verify → mid → verify → frontier. Three tiers minimum (`findings.md` §3).
Escalation on verifier failure, never on self-reported confidence (D12).
No learned prior in v0 (D6) — revisit only if escalation wall-clock cost proves ≥2× (§4a).

### 3. The ticket store
Native, agent-first, local-first. Git-backed or SQLite — **undecided (Q6)**.
Git-backed gives the trajectory record free: every state transition is a commit.
Optional one-way sync adapters out to Linear / ClickUp for humans who want to watch.
Build the state machine, not a Trello competitor.

### 4. Parallel orchestration
Across git worktrees on **independent work units**. This is the regime where the
multi-agent literature says parallelism actually helps — genuinely independent contexts,
no shared state to lose. Hard budget caps per session (63 documented production
budget-overrun incidents; see `literature-review.md` §7).

Bounded meetings only, never open-ended chat (D9). Each meeting must name its exogenous
signal (D10) or it doesn't ship.

### 5. The critic tier
Rejects bad diffs before the human sees them. The only lever that raises the parallelism
ceiling (`findings.md` §5). Critic recall ≡ 1 − β, which is why the same instrument
measures both.

---

## What is deliberately absent from v0

Learned router · trajectory corpus as an asset · debate / model battling · RL ·
multi-channel access · voice · on-device models · self-updating model catalogue ·
autonomous spending · CASB / ToS scanning / compliance trails · the Inquiry tier (Q14).

Each of these was argued through and cut or deferred. See `decisions-so-far.md`.

---

## The shape of the claim

```
       one measured quantity  β
              │
      ┌───────┼───────┐
      ▼       ▼       ▼
   routing  parallelism  human
   safety    ceiling     review load
```

Everything else in the design is downstream of that identity. If β is not measurable
(Q2) or the identity does not hold in practice, this architecture has no centre and
should be replaced rather than patched.

---

## Adopt, don't invent

From `literature-review.md`, these are solved elsewhere and should be taken wholesale:

- **Cascade mechanics** — FrugalGPT, Hybrid LLM, Dekoninck et al.'s routing/cascading
  continuum.
- **Context/skill evolution** — ACE's Generator / Reflector / Curator loop (ICLR 2026).
  This is what `/learn` should be.
- **Trajectory log invariant** — DeepSeek Harness's rule that everything reaching a model
  request must be rebuildable from an append-only log.
- **The verification pipeline shape** — Joe's own `CODEBASE_ASSESSMENT.md` method:
  independent discovery → independent verification of every lead → fabrication audit.
  Measured ~0.5% fabrication rate, caught. See `30-source-material/prior-repo-assets.md`.

## Do not compete with

**Meta-Harness** (Stanford/MIT, COLM 2026) already automates harness search end-to-end.
Any framing of this project as "the harness optimises itself" is walking into a
well-funded, well-cited incumbent. The differentiation, if it exists, is measuring the
*trustworthiness of the repo's own verification layer* — which is a different object from
optimising a harness against a benchmark. **Establish that honestly in Q1 before building.**
