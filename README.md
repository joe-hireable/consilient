# Consilient

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

An open-source **Agent Command Post** (ADR-0061). Don't ask ChatGPT. Ask Consilient. It
sends **harnesses** — Claude Code, Codex, Cursor, Grok, opencode, Antigravity CLI, or any
other you favour — rather than replacing them, with a native path for open models
(OpenRouter or local) when no delegated harness fits. It is for **work in general** —
chats, projects, tasks, scheduled and background runs, parallel workflows — not coding
specifically. The command post is identical regardless of domain: one loader supplies
tools, skills, MCPs and connections dynamically per task. There is no "code mode". Child
runtimes are harnesses. Consilient is not.

Its distinguishing feature: it **measures whether your automated checks can be trusted**
before routing work to cheaper models or running agents in parallel.

MIT. Fully open source. No capability is ever withheld from the open-source version.

## Install and run

Python **3.13 or newer** — the only version the suite has been run on, and the version
`mypy.ini` type-checks against. No runtime dependencies: `consilient` is standard library
only.

```bash
git clone https://github.com/joe-hireable/consilient
cd consilient
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                            # drop [dev] if you only want the CLI

consil --help
consil beta        # -> "insufficient data (0 human rejections, need 30)" on a fresh clone
consil doctor      # gate status; exits non-zero while the gates are shut
```

`consil` is observe-only. It records trajectory events, projects them into SQLite and
computes β. It cannot route, block or accept anything, and a test asserts the CLI exposes
no surface that could.

Before proposing a change, run every gate at once:

```bash
python scripts/release_check.py
```

It reports PASSED, FAILED or **UNAVAILABLE** per gate and exits non-zero unless all of them
passed. `UNAVAILABLE` is deliberately not a pass — the private-corpus leak scan can only run
on the maintainer's machine, and a release approved without it running is not an approval.
Do not pipe it into `tail`; a pipeline's exit status is the last command's, and this project
has already lost a day to that.

**Cross-platform status.** `src/consilient/`, `tests/`, `scripts/` and `.github/scripts/`
are portable and CI runs them on Linux. The research instruments under
`docs/10-research/experiments/` are **Windows-only** in places — WSL invocation, `cmd.exe`,
`taskkill`, absolute `C:\` paths — and CI never executes them. See
`docs/00-context/cross-platform-status.md` for the itemised list. If you are on Linux or
macOS, the CLI, the suite and the gates work; the experiment runners may not.

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
much of your day you spend reviewing.

β has been measured before, and we should say so plainly: Reflexion reported its own
self-generated oracle's false-accept rate in 2023 (1.4% on HumanEval-PY, 16.3% on MBPP-PY);
Wang, Pradel & Liu (ICSE 2026, arXiv:2503.15223) found **7.8%** of accepted patches fail the
developer-written test suite (n=877, SWE-bench Verified); METR measured a **24.2pp** gap
between maintainer judgement and the grader (n=296). **What none of them does is act on it.**
Every one measures β, reports it, and recommends a human. **Nothing conditions its own routing,
its parallelism or its acceptance threshold on a measured β.** That is the gap this project is
built in.

A related gap exists one level up. Self-improving agent systems — Darwin Gödel Machine, SICA,
Huxley-Gödel, HyperAgents, Voyager, ADAS, Meta-Harness, Live-SWE-agent — accept a
self-modification when a test says it is better, and in a survey of eight, **none reports a
denominator-based false-acceptance rate for candidate promotion against independent truth**. In
an archive-based system that error compounds: DGM produced one evaluator-bypassing winner in a
150-iteration run, caught by manual audit rather than by a rate.

**Corrected 20 August 2026.** This previously read *"none measures how often that test is
wrong"*, which is now known to be false. **Ratchet** (arXiv:2605.22148v3, Apache-2.0) audits the
judge governing skill synthesis and survival, reporting false-pass ≈0.01 (n=210) and false-fail
≈0.95 (n=42, 95% CI 0.84–0.99). That is not pre-persistence β and the audit is not shipped in
the system, but the categorical claim does not survive it. The narrower statement above is what
the evidence supports.

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

## Status: v0 approved, observe-only increment shipped

The v0 specification was approved for implementation on 20 August 2026. `src/consilient/`
records trajectory events, projects them into SQLite and computes β — and does nothing else:
it cannot route, block or accept anything, and a test asserts the CLI exposes no surface that
could. Everything past instrumentation is gated on ADR-0015 Gate A, which has not been passed.

<!-- BEGIN GENERATED: scripts/build_counts.py#inventory -->
105 ADRs, 115 registered experiments, 13 invariant checks in CI.
<!-- END GENERATED: scripts/build_counts.py#inventory -->

## What it is for

The success condition, in the maintainer's words:

> *"Users like I am right now should be able to ramble visionary concepts into the chat and
> get world class execution fully autonomously within legal and ethical and security and
> safety boundaries."*

As stated that cannot fail, so it is restated in a form that can: **for a rambled intent, the
quality of the execution does not depend on the rambler's technical expertise, and the
failures are caught by the harness rather than by an attentive operator noticing.** On this
repository's own baseline, 2 errors out of 9 were caught by an enforced mechanism and 7 by
someone happening to look. That gap is the product.
[`docs/20-design/autonomous-execution-from-intent.md`]

Three consequences are already decided:

- **Decisive by default.** The harness decides and records how to reverse; it asks only in
  seven named classes — money, credentials, preferential questions, the safety floor, the β
  verdict, anything leaving the machine, and lifting a gate. An ask the user cannot afford to
  answer does not transfer a decision, it launders a machine's decision as a human's.
  [ADR-0033]
- **Verified human gain while preserving agency.** Quality, speed, cost, review burden,
  learning, self-efficacy and stress are reported **separately and never composited** —
  because satisfaction and quality are anti-correlated through a measured mechanism.
  [`docs/40-spec/v0-draft.md` §1.1]
- **Capacity-aware admission.** Subscription headroom and metered budget are structural
  vetoes before routing (ADR-0026). Local hardware fit is gated in policy
  (`local_fit.acquire_local_model`) against a probed profile: infeasible or unknown refuses
  before any downloader runs, but no product download path calls that chokepoint yet.
  [ADR-0026, ADR-0028]

Research is a first-class output. Every completed experiment gets a public disposition, and
negative or underpowered results ship as research notes rather than waiting for a paper.
[`docs/publications/README.md`]

## Start here

**If you just want to use it**, read
[`docs/00-context/getting-started.md`](docs/00-context/getting-started.md). Every command on that
page was run against this tree and its real output pasted in, including the ones that fail and how
to recover. It assumes none of the vocabulary below.

**If you want to understand why it is built this way**, read in order:

1. [`CONSILIENCE.md`](CONSILIENCE.md) — the definition everything derives from
2. [`docs/decisions/index.md`](docs/decisions/index.md) — the formal ADR index; the load-bearing four are
   marked
3. [`docs/10-research/findings.md`](docs/10-research/findings.md) — the simulations
4. [`docs/10-research/experiment-register.md`](docs/10-research/experiment-register.md) —
<!-- BEGIN GENERATED: scripts/build_counts.py#experiments -->
115 experiments with stopping rules
<!-- END GENERATED: scripts/build_counts.py#experiments -->
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
