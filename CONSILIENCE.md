# Consilience — the definition this project is grounded in

**Read this before ideating, designing, or building anything here.**
Every architectural rule in this repository is derived from the sentence below. Where a
proposal cannot be traced back to it, that is a signal the proposal does not belong.

---

## The definition

> **"The Consilience of Inductions takes place when an Induction, obtained from one class
> of facts, coincides with an Induction obtained from another different class. Thus
> Consilience is a test of the truth of the Theory in which it occurs."**
>
> — William Whewell, *The Philosophy of the Inductive Sciences, Founded Upon Their History*,
> Vol. II (London: John W. Parker, 1840). Restated in *Novum Organon Renovatum* (1858),
> pp. 70–71.

**Etymology:** Latin *con-* (together) + *salire* (to jump, to leap) — literally a
**jumping together**. Whewell coined it in 1840. Revived by E. O. Wilson in *Consilience:
The Unity of Knowledge* (1998), who glossed it as <cite index="214-1">a "jumping together" of knowledge across disciplines to build a common groundwork of explanation</cite>.

**Pronunciation:** kən-SIL-ee-əns · /kənˈsɪli.əns/ · con‧si‧li‧ence

---

## The three clauses, and what each one commands

Whewell's sentence has three parts. Each maps onto a design rule that is already load-bearing
in this repository.

### 1. *"an Induction, obtained from one class of facts"*

A conclusion is only as good as the evidence it came from, and that evidence has a
**provenance**. An agent's output is an induction over the facts it observed — its context,
its tool results, its test run.

**Rule:** every conclusion in this system carries its evidence with it. That is why the
trajectory record is append-only and why every claim in `docs/` carries an evidence tag
(`[measured]` / `[simulated]` / `[cited]` / `[algebra]` / `[asserted]`). A conclusion whose
provenance has been discarded cannot participate in consilience at all.

### 2. *"coincides with an Induction obtained from another different class"*

**This is the load-bearing clause, and "different" is the load-bearing word.**

Two agents agreeing about the same evidence is not consilience. It is echo. Whewell's whole
point is that convergence is only informative when the inductions came from *classes of
facts that are altogether different*.

**Rule (the exogenous-signal rule):** every multi-agent structure must name the *new*
evidence it introduces, or it does not ship. This is not a stylistic preference — it is
forced by Ao, Gao & Simchi-Levi (arXiv:2603.26993), who prove that without new exogenous
signals a delegated network is decision-theoretically dominated by a single decision-maker
with the same information, and measure a model degrading from 90.7% to 22.5% as relay
stages are added.

Applied:

| Structure | Different class of facts? | Verdict |
|---|---|---|
| Critic tier | Yes — it *runs the tests* | Consilient |
| Parallel worktrees | Yes — different repository states | Consilient |
| Discovery agents on separate sources | Yes | Consilient |
| Independent verification of a lead | Yes — re-derives from primary evidence | Consilient |
| Debate over shared context | **No** | Echo |
| Planner → implementer handoff | **No** | Echo |
| A "summit" where everyone read the same brief | **No** | Echo |

The pattern: **structures that touch the world are consilient; structures that only talk are
echo.** A convened panel of Nobel laureates is worth something because Curie brought
radioactivity data and Bragg brought crystallography — not because they were clever.

### 3. *"Thus Consilience is a test of the truth"*

A **test**. Not a proof, and not a guarantee. Convergence raises confidence; it does not
establish truth, and a test can be wrong.

**Rule:** this is exactly what **β** measures — the rate at which our tests accept something
false. A project named after a test of truth is obliged to measure how good its tests are.
That is the entire product, and it is why the honest output is sometimes *"your verification
is too weak; do not route here."*

It is also why this repo forbids gating on a model's self-reported confidence. Confidence is
not a second class of facts. It is the same induction, restated.

---

## What the name commits us to

1. **Evidence over authority.** Not "the best model said so" — *these independent lines
   converged*.
2. **Independence is the scarce resource.** More agents are cheap; genuinely different
   classes of facts are not. Design for the latter.
3. **Convergence is a test, and tests have error rates.** Measure them. Publish them.
4. **Honest disagreement is information.** Where independent lines fail to converge, that is
   a finding, not a failure to be smoothed over. Report the divergence.

If the architecture ever drifts toward "more agents talking to each other produces better
answers", the name has become a lie and one of the two must change.

---

## Where this is referenced

`README.md` · `AGENTS.md` · `CLAUDE.md` · `docs/decisions/0008-name-the-project-consilience.md`
· `docs/decisions/0010` (exogenous-signal rule) · `docs/20-design/architecture-sketch.md`
