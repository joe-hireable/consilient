# 0035. Visibility is a user-controlled rendering of the record, never a second record

*Intended path: `docs/decisions/0035-visibility-is-a-rendering-of-the-record.md`. Draft — not written to the repository.*

- **Status:** PROVISIONAL — the mechanism is forced by ADR-0006; every threshold in it is preferential and unmeasured. EXP-42 decides whether the dial earns more than a `--quiet` flag.
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the requirement), Claude Opus 5 (the mechanism)
- **Inquiry tier reached:** T1 ground — a construction plus published measurements, none of them on this system
- **Executable model:** none. There is nothing to model: the mechanism is a set predicate, and the parameters it exposes are preferential rather than derived.

## Context

Joe, on what the harness should feel like: *"maximum visibility or none at all or a mix depending on how they feel."*

Nothing in this repository captures that. ADR-0007 fixes the surface — CLI only, and build no review surface. ADR-0033 fixes **when the harness interrupts the user**. Neither says **how much the user sees while not being interrupted**, and they are different questions: an interrupt demands attention, a stream merely offers it. The repository currently has one output control, `--json` (V0-14), and no notion of level at all. [measured]

Two published results pull in opposite directions and both are load-bearing here.

**Turning visibility down has a measured cost.** Automating a navigation task with an expert system produced out-of-the-loop performance decrements in decision time following an expert-system failure, with low situation awareness corresponding to those decrements; the authors attribute the effect to the shift from active to passive information processing rather than to skill loss. `[cited]` — Endsley & Kiris (1995), *Human Factors* 37(2), 381–394, DOI 10.1518/001872095779064555.

**Turning visibility up has a measured cost too, and it is the more dangerous one for this project.** Explanations *"increased the chance that humans will accept the AI's recommendation, regardless of its correctness"*, while producing no complementary team improvement. `[cited]` — Bansal et al. (2021), CHI '21, arXiv:2006.14779. The mechanism is corroborated: feature-importance explanations raised Relative AI Reliance from 29.59% to 38.87% (p=.05) while Relative Self-Reliance was statistically unchanged, 71.87% to 69.45% (p=.54) — reliance moved, discrimination did not. `[cited]` — Schemmer et al. (IUI 2023, arXiv:2302.02187). And confidence displays shifted behaviour (p=.035) while local explanations produced no trust-calibration advantage over baseline (p=.66) and neither produced a joint-performance gain. `[cited]` — Zhang, Liao & Bellamy (FAT\* 2020, arXiv:2001.02114).

This is the sentence the ADR exists to obey: **every level above silence is an untested intervention on the human half of β.** β is the rate at which our checks accept a bad artefact, and the human verdict is the ground truth those checks are measured against (ADR-0002, ADR-0033 §2). A surface that raises acceptance without raising discrimination does not improve the system — it corrupts the instrument that tells us whether the system is improving.

The only manipulation known to actually reduce over-reliance is making verification genuinely cheap: over-reliance fell from ~69% to ~28% when a salient display surfaced the error itself, whereas written explanations moved it from ~68% to ~66% and higher pay moved it from ~58% to ~57%. `[cited]` — Vasconcelos et al. (CSCW 2023, arXiv:2212.06823). **Show state, not narrative.** That single finding decides the shape of everything below.

This is not a one-way door. It is close to one for the schema: once the visibility level is recorded on human decision events, removing it destroys the ability to stratify historical β by the conditions under which the verdict was produced.

## Decision

### 1. A level is a set of event kinds, and rendering is a pure function of the log

The trajectory JSONL is the record; SQLite and every display are projections of it (ADR-0006, V0-02). Visibility joins them. A visibility level is **nothing but a predicate over event kinds**, evaluated at render time.

Therefore, by construction and not by discipline:

- The dial changes **what is displayed**. It never changes what is recorded, which checks run, which route is taken, or what is accepted.
- Any level can be rendered over any past window at any time, because the log is complete regardless of what was shown.
- `--json` output is **level-invariant**. V0-14 says every command has one JSON contract; the dial must not fork it.

Nothing here transmits anything off the machine, so ADR-0024 is untouched.

### 2. Four levels, and the "mix" is the same mechanism, not a second one

| Level | Name | Renders |
|---|---|---|
| 0 | `silent` | The floor set only (§3). Run id at start, terminal line at end. |
| 1 | `milestones` | **Default.** Task state changes: dispatched, check outcome, decision taken, stall detected, finished. |
| 2 | `decisions` | Level 1, plus every autonomous decision with its evidence reference and reversal command, every check invocation and outcome, and every recorded divergence. |
| 3 | `firehose` | Level 2, plus per-step agent tool calls and sub-agent output as written to the log. |

A level is shorthand for a set of event kinds. The mix is expressed on the same scale: `--see +stall --see -tool_call` adds and removes kinds from whatever set the level names. There is no second subscription language, no channel taxonomy, and no new vocabulary — the channels *are* the event kinds already in the schema.

The default is level 1 deliberately. Level 1 reports **state transitions**; level 2 begins reporting **reasons**. Reasons are explanations, and explanations are the thing measured to raise acceptance without raising discrimination. `[cited]` The default therefore sits on the last rung before the amplifier.

### 3. The floor, which no level can dim

The floor set is unioned into the rendered set at every level including `silent`:

- Any ask in an ADR-0033 §2 class — money, credentials, preferential questions, the safety floor, the β verdict, anything leaving the machine, lifting a gate.
- Any safety-floor event (ADR-0022).
- Any stall escalation that has exhausted its escalation path (ADR-0034 §3).
- Any check that failed, and any check that was configured but did not run.

**The β verdict prompt renders identically at every level.** If the instrument varies with the dial, β stratified by level is uninterpretable and the one measurement this ADR justifies itself with is destroyed.

The floor is validated at **configuration load**, not at render time — the Temporal trap ADR-0034 §4 records: a configured-but-unfed channel must fail loudly when it is configured, not silently when it matters.

### 4. Changing level mid-task takes effect at the next event boundary, and backfills by reference

- **Lowering** takes effect at the next event boundary. The floor still applies.
- **Raising** takes effect at the next event boundary and prints exactly one line: how many events occurred at the lower level, and the command that renders them (`consil show --since <ts> --level N`). **It does not dump them.** An automatic replay at raise-time is an unbounded interruption spent from ADR-0033 §5's ask budget, and more text does not lower verification cost. `[cited]`
- The change is itself recorded as a `visibility_change` event carrying `from`, `to`, `scope` and `ts`, because the effective level at the moment of a human decision must be reconstructable from the log alone.
- Changing level is never a decision input. It cannot change routing, admission, acceptance or which checks run — and there is nothing to route yet, which is why the enforceable form of this today is an import-graph check (§Enforcement).

### 5. Re-entry after absence gets a brief with a fixed shape and no adjectives

Absence is detected from the log — elapsed wall time since the last user-authored event — never from a timer on a process (ADR-0034 §1). On the next interactive invocation, if the gap exceeds the re-entry threshold **and** the level is below 2, the harness renders a re-entry brief before anything else.

The threshold is **preferential**, defaulted at 20 minutes, and is named as preferential deliberately. The takeover-time and resumption-lag literature that would anchor it is not in this repository's bibliography and has not been read at source; until it is, this number has no empirical basis whatsoever. `[asserted]`

The brief has a fixed order, and the order is the design:

1. **How long you were away**, and how many events occurred at a level you were not shown.
2. **Unresolved divergences, failed checks, and checks that did not run** — first, before anything that reads as progress.
3. **Decisions taken in your absence**, each with its executable reversal command (V0-22, V0-24 — reused, not reinvented).
4. **What is pending**, and what happens if you do nothing.
5. **No quality assertion.** No adjective about the artefact, no "successfully", no summary judgement, no recommendation.

Rule 5 is the whole point. A summary is an explanation with the caveats removed, and explanations raise acceptance regardless of correctness. `[cited]` Situation-awareness recovery needs the state, not a story — and the one intervention measured to work is surfacing the error itself, not describing the work. `[cited]`

The out-of-the-loop decrement is measured in **decision time**. `[cited]` So the honest consequence is that the first decision after a re-entry brief should be *slower*, and a fast one is less trustworthy than usual: ADR-0033 §4's affordability floor applies to it at a raised multiplier, and an approval below it is stored `unread` exactly as §4 already specifies. This adds no new mechanism; it re-uses the one that exists.

### 6. The level is recorded on every human decision, so β can be stratified by it

Every `verdict` and `approval` event carries the effective visibility level at the time it was answered. This is the only claim in this ADR to any consilience value: the checks are an induction over the artefact; the recorded level is a fact about the **conditions under which the human test was performed**, which is a different class from anything the checks observe. Clause 3 of Whewell's sentence obliges us to measure the error rate of the test — this records one condition under which that rate may vary.

It introduces no agent and no new agent structure, so it introduces no echo. It is a covariate, not a voter.

## Evidence

- `[cited]` Explanations *"increased the chance that humans will accept the AI's recommendation, regardless of its correctness"*, with no complementary improvement; Team(Confidence) 0.89±0.05 vs Team(Explain-Top-1) 0.88±0.06, z=−1.18, p=.24, and similar nulls at p>.20 on two further tasks. — Bansal et al. (2021), CHI '21, arXiv:2006.14779.
- `[cited]` Explanations moved reliance without moving discrimination: RAIR 29.59%→38.87% (p=.05); RSR 71.87%→69.45% (p=.54). — Schemmer et al. (2023), IUI, arXiv:2302.02187.
- `[cited]` Over-reliance tracks verification cost, not information volume: ~69%→~28% when a display surfaced the error; ~68%→~66% for written explanations; ~58%→~57% for higher pay. — Vasconcelos et al. (2023), CSCW, arXiv:2212.06823.
- `[cited]` Confidence displays changed behaviour (p=.035); local explanations gave no trust-calibration advantage (p=.66); neither produced a joint-performance gain. — Zhang, Liao & Bellamy (2020), FAT\*, arXiv:2001.02114.
- `[cited]` Out-of-the-loop decrements appeared in **decision time** after an expert-system failure, with low situation awareness corresponding to them; level of operator control moderated the SA loss. — Endsley & Kiris (1995), *Human Factors* 37(2), 381–394.
- `[cited]` Automation complacency *"occurs under conditions of multiple-task load"*, is found in naive and expert participants alike, and *"cannot be overcome with simple practice"*. — Parasuraman & Manzey (2010), *Human Factors* 52(3), 381–410.
- `[cited]` Monitoring is not cheap: *"converging evidence using behavioral, neural, and subjective measures shows that vigilance requires hard mental work and is stressful"*. — Warm, Parasuraman & Matthews (2008), *Human Factors* 50(3), 433–441. A firehose is a vigilance task, and level 3 should be understood as expensive rather than as thorough.
- `[algebra]` Level-invariance is provable with machinery that already exists: `projection.build` plus `state_digest` already assert byte-identical rebuilds from the same log (`consil replay`). Rendering the same log at four levels and comparing digests is the same assertion with a fourth argument.
- `[asserted]` Four levels, the default at 1, the 20-minute re-entry threshold and the raised post-re-entry affordability multiplier are all preferential. None is derived.

## Evidence against

**This ADR may be over-engineering a stdout formatter, and that is the most likely way it is wrong.** ADR-0007 decided to *"emit to the reviewer the user already has: git worktrees, branches, pull requests, their editor"*. If acceptance is actually formed in the user's own diff viewer, then the harness's stdout is not where β is decided, the dial moves nothing, and everything here reduces to `--quiet`. That outcome is pre-registered as a stopping rule in EXP-42 rather than left as a caveat. `[asserted]`

**The level is self-selected, never randomised, so the β stratification can never establish causation.** The requirement is explicitly mood-driven — *"depending on how they feel"* — which confounds level with task difficulty, fatigue, time of day and how much the user already trusts the run. A user who picks `silent` on easy tasks and `firehose` on hard ones will produce a β difference by level that says nothing about visibility. This is the central weakness of §6, it is not fixable by instrumentation, and no result from EXP-42 may be reported as "visibility affects acceptance". `[asserted]`

**The takeover-time and resumption-lag literature is named but not held.** It does not appear in `docs/10-research/bibliography.md` and has not been fetched and read here, so under that file's own rule it cannot appear on a `[cited]` line. Everything in §5 that depends on it — the 20-minute threshold, the raised affordability multiplier, the premise that re-entry needs a procedure at all — is `[asserted]`. `[measured]` that the gap exists; `[asserted]` that the design is right. `[asserted]`

**Endsley & Kiris is abstract-only and 1995.** No n, no decision-time figures, no effect sizes; a single-session expert-system study whose measured outcome was recovery time, not defect detection. Whether reading an agent's diff is the "passive processing" the authors describe — when the reader must actively reconstruct intent — is an assumption, not a finding. `[asserted]`

**A no-adjectives lint does not touch the actual amplifier, which is ordering and selection.** A brief that is scrupulously neutral in vocabulary while listing four completed checks before one failure still amplifies acceptance. §5's ordering rule addresses this, but the ordering rule is testable only against fixtures we wrote, and we are the party that would fail it. Q19's rule applies. `[asserted]`

**The re-entry brief is itself an interrupt** and is spent from ADR-0033 §5's finite ask budget. A brief that fires on every twenty-minute coffee break trains the user to skip it, and a skipped brief is worse than none because it looks like recovery occurred. `[asserted]`

**`silent` plus the out-of-the-loop result predicts the worst β of any setting** — a user who sees nothing accepts on trust, and earned trust already associates with less critical engagement at b=−0.69 log-odds (p<0.001). `[cited]` This ADR ships that setting anyway, because Joe asked for it and because removing authority is itself a measured cost (autonomy was the strongest resource against developer burnout, B=−0.13, p<.001). `[cited]` The trade is deliberate and it may be the wrong one.

**This ADR was written by the harness and it makes the harness's own output surface configurable by the person the harness is trying not to mislead.** The party that produced the material cannot certify what it left out. `[asserted]`

## Consequences

**Positive.** The requirement is captured with one mechanism and no new subsystem: a predicate over event kinds, evaluated at render time, over a log that already exists. Re-entry after absence has a defined procedure instead of a scroll-back. The level becomes a recorded covariate on every human verdict, at zero marginal cost, which is the cheapest instrumentation this project has yet acquired.

**Negative.** Four levels plus per-kind overrides is real configuration surface on a CLI that had one flag. The re-entry brief is another interrupt competing for the same finite attention. The floor set must be maintained by hand and will drift as event kinds are added — a new kind that belongs in the floor and is not added to it silently degrades `silent` mode, and no test can know that on its own. And the ordering rule in §5 gives the harness editorial control over what the user notices first, which is precisely the power the Bansal result says is dangerous.

**Neutral but load-bearing.** Every human decision event now carries the effective visibility level. That is a schema commitment and a public interface under ADR-0023 T2. Every new event kind must declare its floor membership at the time it is added.

## Enforcement

Every rule ships with its check in the same commit as the code implementing it (I1). Two invariants are declared.

- **V0-26** — *Visibility is a rendering only.* The dial changes what is displayed, never what is recorded, checked or decided; the floor set renders at every level; `--json` is level-invariant.
- **V0-27** — *Re-entry and level are recorded.* Every human decision event carries the effective level; the re-entry brief has a fixed shape, a fixed order, and asserts nothing about quality.

| # | Check | Fails CI | Same commit |
|---|---|---|---|
| 1 | Replay-equivalence property test: the same log rendered at levels 0–3 produces byte-identical JSONL and an identical `state_digest`. Reuses `projection.build` + `state_digest`. | yes | yes |
| 2 | Floor test: a fixture asserts every floor event class renders at level 0, including with `--see -<kind>` set against it. | yes | yes |
| 3 | Configuration-load test: a level or override whose rendered set does not contain the floor set is rejected **at load**, not at render. | yes | yes |
| 4 | `--json` invariance test: JSON output for each command is byte-identical across all four levels. Extends the existing V0-14 contract tests. | yes | yes |
| 5 | Schema test: a `visibility_change` event lacking `from`, `to`, `scope` or `ts` is rejected before append. | yes | yes |
| 6 | Schema test: a `verdict` or `approval` event without the effective level at answer time is rejected before append. | yes | yes |
| 7 | Import-graph test: no module reachable from routing, admission or acceptance imports the visibility module — the enforceable form of "the level is never a decision input" while routing is still gated. Mirrors V0-19's persona property test. | yes | yes |
| 8 | Re-entry brief lint: a banned-vocabulary list (quality adjectives, "successfully", recommendation verbs) plus an ordering fixture asserting divergences, failed checks and unrun checks precede completed work. | yes | yes |
| 9 | Registry test: every event kind declares floor membership; a new kind without a declaration fails the build. | yes | yes |

Check 8 is the weakest of the nine and is known to be so: it constrains wording and ordering, not selection. See Evidence against.

## What would overturn this

**EXP-42 · Does the visibility dial change acceptance, and does anyone use it?** *(drafted as EXP-36 on 20 Aug 2026; renumbered the same day — that number had already been issued in the register, and by two other drafts besides. Numbers are allocated in `../10-research/experiment-register.md` and nowhere else.)* `BLOCKED: ADR-0015 Gate A trajectory capture + the dial shipped`

**Decides:** whether the dial earns its configuration surface, or reduces to `--quiet` plus the floor.

**Precondition:** Gate A trajectory capture live; `visibility_change` recorded; effective level recorded on every `verdict` and `approval`. No new prompts are added for this experiment — it instruments what the harness already renders. `[asserted]`

**Procedure:** 30 consecutive days of ordinary working with no change to the dial's behaviour or defaults. `[asserted]`

**Measures:** level-change events per working day and their direction; time spent at each level; β stratified by effective level at verdict time, reported with n and interval per stratum; re-entry briefs rendered versus followed by an action within the session; approval latency on the first decision after a brief against all other decisions; and the count of floor events rendered at level 0.

**Stopping rules, fixed before the run:**
- Run the full 30 days. Stop early only for a safety-floor event or the user withdrawing. Report a truncated window as truncated. `[asserted]`
- **The dial earns its place** only if the user changes level at least 10 times in the window **and** at least two distinct levels each accumulate 20 or more recorded verdicts. Anything less means there is one working level and three ornaments. `[asserted]`
- **Cut to `--quiet` plus the floor** if fewer than 3 level changes occur, **and** no re-entry brief is followed by an action within the session. In that case delete §2's levels, §4 and §5, keep §1, §3 and §6, and record the deletion rather than deprecating quietly. `[asserted]`
- **The acceptance-amplifier concern is live** if β at levels 2–3 exceeds β at level 1 by more than the wider of the two intervals, across at least 20 verdicts per stratum. The required response is to lower the default, never to add a confirmation step. `[asserted]`
- Anything else, or fewer than 20 verdicts in any stratum, is `insufficient evidence`. Do not re-cut the strata after seeing the distribution. `[asserted]`

**What it cannot decide:** whether visibility *causes* the acceptance difference, because the level is self-selected and confounded with task difficulty, fatigue and existing trust — no result may be reported as a causal claim about visibility; whether the four levels are the right four, since it can find an unused level but never a missing one; whether the re-entry threshold is correct, since it measures against the threshold rather than validating it; whether the brief restored situation awareness, since a following action is a behavioural proxy and not a comprehension measure; and anything about users other than this maintainer, because n=1. `[asserted]`

**Other things that would overturn this:**
- If a decision anywhere in the system is ever found to depend on what the user was shown, §1 is false and this ADR must be rewritten rather than patched — the dial would have become a second record.
- If the takeover-time and resumption-lag literature, once fetched and read at source, gives a threshold materially different from 20 minutes, §5's default changes and the `[asserted]` tags on it are promoted.
- If EXP-32 finds unaided defect detection decaying, the level at which that decay occurred becomes the primary question and this ADR's default moves to whichever level the decay did not occur at.

## Publication candidate?

No. The construction is specific to a system with an append-only trajectory, and the measurement is n=1 and confounded by design.
