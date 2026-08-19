# Consilience

> **"The Consilience of Inductions takes place when an Induction, obtained from one class of
> facts, coincides with an Induction obtained from another different class. Thus Consilience
> is a test of the truth of the Theory in which it occurs."**
>
> — William Whewell, *The Philosophy of the Inductive Sciences*, Vol. II (1840)

Latin *con-* (together) + *salire* (to leap) — a **jumping together**. kən-SIL-ee-əns.

**→ [`CONSILIENCE.md`](CONSILIENCE.md) is the grounding document. Read it before designing
anything.** Every rule here derives from those three clauses: evidence carries its
provenance; convergence only counts when the classes of facts are *different*; and
convergence is a **test**, so its error rate must be measured.

---

## What this is

An open-source **meta-harness** — an orchestrator above existing agents (Claude Code,
Codex, opencode, Antigravity CLI, and any other the user favours) rather than a
replacement for them, with a native execution path for open models (OpenRouter or local)
when no delegated agent fits. It orchestrates **agentic work in general** — chats,
projects, tasks, scheduled and background runs, parallel workflows — not coding
specifically. The harness is identical regardless of domain: one loader supplies tools,
skills, MCPs and connections dynamically per task. There is no "code mode".

Its distinguishing feature: it **measures whether your automated checks can be trusted**
before routing work to cheaper models or running agents in parallel.

MIT. Fully open source. No capability is ever withheld from the open-source version.

## Scope — what v0 is, and what it is not

| | Scope | Gate |
|---|---|---|
| **v0** | **Coding, instrumentation only**: trajectory log, verdict prompt, β-meter (ADR-0015 Stage 2). No modes, no tool layer, no reasoning layer, no cascade until β is measured. | ADR-0015 |
| **The product** | General agentic work, all modes (`docs/20-design/work-modes.md`), dynamic capability loading (`docs/20-design/capability-layer.md`, `context-loading.md`, `reasoning-layer.md`) | β measured on ≥2 real repos (EXP-01), then per-component experiments |
| **The expansion risk** | Domains without an automated oracle | **Q24** — β is only defined where checks exist. Coding is v0 *because* tests/typecheck/build are the one cheap oracle; whether anything replaces it for a strategy memo is open, and the architecture has no centre outside coding until it is answered. |

Coding-first is a **measurement decision, not an architectural one**. Everything in
`docs/20-design/` beyond the instrumentation is v1+ and explicitly marked as such;
treat any scope drift past this table as a bug.

## The thesis in one paragraph

Model capability has converged; the harness around the model now decides outcomes. Every
harness routes work and runs agents in parallel, and every one assumes its verification layer
is sound. Define **β** = the rate at which automated checks *accept a bad artifact*.
Executed simulation shows β determines (a) whether cheap-first routing helps or silently
degrades quality, (b) how many agents you can run before human review saturates, and (c) how
much of your day you spend reviewing. **Nothing on the market measures it.**

The same gap exists one level up: every published self-improving agent system — Darwin Gödel
Machine, SICA, Huxley-Gödel, HyperAgents — accepts a self-modification when a test says it is
better, and **none measures how often that test is wrong**. In an archive-based system that
error compounds. β is the missing safety property of that entire literature.

**This is a hypothesis, not a finding.** It survived one round of simulation under assumed
functional forms. It has never met a real repository.

## The three results that matter

1. **β\* has a closed form: `β* = (1−α)·e^(−kΔ)`, distribution-free under its
   assumptions — which are fragile.** Verified across unimodal and bimodal difficulty
   distributions (β\* moved ≤0.003 while escalation swung 19%→64%), **but** the
   robustness sweep (`experiments/robustness_beta_star.py`, 19 Aug 2026) shows the
   property is a knife-edge: unequal competence slopes, non-logistic links, guessing
   floors, and — worst, because it errs false-safe — *correlated model successes* all
   break it (at correlation ρ=0.6, true β\* is ~0.03 against the formula's 0.11).
   Treat the closed form as sign-and-threshold reasoning, never as a number. The
   measurement programme, not the formula, is the product. [ADR-0002, incl. the Δ
   discipline section]
2. **Human review is the hard ceiling.** `n_max = T_cycle / T_review` — about 3 agents at
   realistic numbers. The only lever that raises it is a critic tier, and **critic recall
   ≡ 1 − β**. One measured quantity governs everything. [findings.md §5]
3. **The learned router isn't worth building.** ~5,000 trajectories to merely match plain
   cheap-first-then-escalate. The cascade already *is* adaptive routing. [ADR-0003]

## Status: pre-brainstorm. No code exists.

This repository is **context, not code** — assembled in one session on 19 Aug 2026 to hand a
design position to Claude Code. Nothing is built. Nothing is specified.

## Start here

**Read, in order:**

1. [`CONSILIENCE.md`](CONSILIENCE.md) — the definition everything derives from
2. [`docs/decisions/index.md`](docs/decisions/index.md) — the formal ADR index; the load-bearing four are
   marked
3. [`docs/10-research/findings.md`](docs/10-research/findings.md) — the simulations
4. [`docs/10-research/experiment-register.md`](docs/10-research/experiment-register.md) —
   15 experiments with stopping rules
5. [`docs/00-context/open-questions.md`](docs/00-context/open-questions.md) — what's still open

**Then do these two things, in this order:**

| | What | Why |
|---|---|---|
| **1** | **EXP-05** — write an adapter for Claude Code, then one for Codex *without refactoring the first*. Record what breaks. **One day.** | Highest-information hour available. If adapter #2 forces a redesign, ADR-0001 is in trouble. |
| **2** | **EXP-01** — measure β on `jobboard-v2` history: replay checks against known PR outcomes. | Promotes ADR-0002 from PROVISIONAL to ACCEPTED, or kills it. Needs no harness. |

Everything else is downstream of those two.

## Working principles

Full set in [`AGENTS.md`](AGENTS.md). The four that bite most often:

- **Claims carry evidence tags** — `[measured]` / `[simulated]` / `[cited]` / `[algebra]` /
  `[asserted]`. `[asserted]` is honest; mislabelling is not.
- **Sign and threshold, never point estimates** from simulations.
- **A chokepoint without an enforcement rule is not a chokepoint.** Any invariant ships with
  its check, in the same commit.
- **Multi-agent structures must name their different class of facts** — or they're echo.

## Repo map

```
CONSILIENCE.md                the definition and its three rules — READ FIRST
AGENTS.md · CLAUDE.md         working rules for any agent
CONTRIBUTING.md               DCO, contributor agreement position
.agents/skills/               portable skills (source of truth; .claude/ mirrors)
docs/
  decisions/                  ADRs + index.md
  publications/               publication policy (high bar) + candidates
  legal/                      MIT, ICLA, CCLA, Relicensing Promise, solicitor brief
  00-context/                 how we got here, open questions, friction log, bypass log
  10-research/                bibliography, findings, experiments, competitive landscape
  20-design/                  architecture sketch, inquiry tier, living system
  30-source-material/         Gemini session critique, prior-repo assets
```

## Sources

[`docs/10-research/bibliography.md`](docs/10-research/bibliography.md) holds every source with
a verification status. **Most are `[SNIP]` — snippet-only, unread.** No such source may be
cited publicly until fetched, read, and promoted. Several quoted figures are explicitly
flagged unverified.

## Contributing

See [`docs/00-context/ways-to-contribute.md`](docs/00-context/ways-to-contribute.md). Research,
experiments, evaluations and benchmarks matter more here than code. Review gates are strict
and scale with blast radius — [ADR-0023](docs/decisions/0023-pr-review-gates.md).

## Provenance and known bias

Assembled by Claude (Opus 5) in one chat session with Joe Brown, from web research, executed
simulations, and a read of `jobboard-v2`. **One model, one framing, one session, with a
declared conflict of interest** — Anthropic makes one of the four agents this would
orchestrate. Q19 in `open-questions.md` asks what was systematically missed as a result, and
that question cannot be answered by anyone who was in the room.
