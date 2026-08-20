# Triaging the audit: nine findings checked, and not one changes a decision

**20 August 2026.** Codex produced 33 findings on numeric provenance. Its own header says every
one is `[asserted]` until independently checked. Four were checked and acted on directly. Nine
more were handed to **Cursor — a third model family checking a second one's homework** — with an
explicit instruction that refutations were the valuable output.

| Finding | Codex severity | Verdict | Does a decision turn on it? |
|---|---|---|---|
| 1 — EXP-01 has three sample denominators | Material | `PARTLY` | **No** |
| 4 — the 84% power result uses a rounded threshold | Material | `CONFIRMED` | **No** |
| 5 — retained β\*=0.432 does not reproduce | Cosmetic | `CONFIRMED` | **No** |
| 6 — ADR-0011 turns 21 subprojects into 21 frameworks | Moderate | `CONFIRMED` | **No** |
| 8 — ADR-0019 repeats the same denominator | Moderate | `CONFIRMED` | **No** |
| 15 — the +0.123 trigger has no producer path | Material | `PARTLY` | **No** |
| 19 — ADR-0034's stall numbers have no sources | Material | **`REFUTED`** | **No** |
| 31 — ADR-0002 orders a test already DONE | Material | `CONFIRMED` | **No** |
| 32 — architecture numbers carry no evidence tags | Violation | `CONFIRMED` | **No** |

**Six confirmed, two partial, one refuted — and the last column reads *No* nine times.** [measured]

## Why that column is the point

A night of "here is what is broken" needs its counterweight stated as plainly as the breakage.
These are **documentation-accuracy defects, not decision defects.** Every architectural conclusion
they touch survives its own error.

The clearest case is finding 4, and Cursor did the arithmetic both ways. ADR-0002 says *"at true
β = 0.08, even n=800 only reaches 84%"*. That reproduces **only** against the rounded threshold
0.111 written in the prose. Against the exact closed form the script actually uses, 0.1118654,
k=72 is admitted and the power is **86.5%, i.e. 87%**. [measured] The number is wrong. The
sentence it supports — that prospective sampling near the threshold is severely underpowered and
the system must report insufficient data — is identical at 84% and at 87%.

That pattern repeats across all nine. The corpus is less precise than it claims; it is not less
correct than it claims.

**This is not a reason to relax.** A project whose thesis is that tests have error rates cannot
be casual about its own numbers, and finding 3 — the "zero" false-safe rate, corrected separately
— was a genuine safety overstatement. The distinction worth holding is between *a number that is
wrong* and *a conclusion that is wrong*, and tonight produced far more of the former.

## The refutation, which is why a third family was worth using

**Finding 19 is a category error, and Cursor caught it.** Codex classified ADR-0034's stall-detector
parameters as untraceable empirical claims. ADR-0034 labels them, at three separate points:

> *"Executable model: none. The thresholds are preferential and are named as such."*
> *"Every parameter here is preferential. 120 s, 900 s … none is derived. `[asserted]`"*

The prior-art figures it cites — LangGraph's ~180 s, Celery's 1 hr/30 min visibility timeouts, the
Linux 32,768 PID limit — are tagged `[cited]`, correctly. Nothing was presented as measured.
[measured]

So the auditor did not find an untagged claim; it found a **correctly tagged preferential
parameter and mistook the tag for a gap.** An auditor that penalises honest labelling teaches the
opposite of what this project wants, and it would have taught it here had a third family not
checked.

## What is now owed, and what is not

**Worth fixing, cheaply, none urgent:**
- EXP-01's audit denominators (32, 40, 30) should resolve to one number or explain three.
- ADR-0011 and ADR-0019 share a denominator that counts 21 subprojects as 21 orchestration
  frameworks — one error, laundered into a second document.
- ADR-0002 § *research priorities* still orders a test that EXP-04 completed, and still says β has
  never been measured.
- `architecture-sketch.md` carries numbers with no evidence tag, including the ≥2× routing
  trigger.

**Not owed:** finding 19, refuted. And finding 5 — β\*=0.432 against the closed form's 0.4358 — is
already handled: ADR-0002 states that the closed form supersedes the simulated table and records
the exact recomputation on the same page.

**Still unchecked: 20 of the 33.** They are in `codex-numbers-audit-2026-08-20.md` and remain
`[asserted]`. On this sample the base rate is roughly two-thirds real, one-third overstated or
wrong — which is a useful prior for reading the rest, and not a substitute for checking them.

## The method note

Three model families were used tonight in one chain: **Claude wrote, Codex audited, Cursor
adjudicated.** The adjudication step changed the outcome — one finding refuted, two narrowed, and
the decision-impact column added, which no auditor had supplied and which turned out to be the
most useful thing on the page.

That said the same caution applies here as everywhere tonight: **n = 1**, the arms were not run
under matched conditions, and the earlier attempt to claim difference-of-class was doing the work
did not survive its own control. This is a description of what happened, not evidence that the
chain is better than one careful reader would have been.


---

# Round two — the remaining twenty, and the pattern behind the auditor's errors

The other twenty findings went back to the same third family. Verdicts: **7 confirmed, 5 partial,
3 refuted, 3 already resolved, 2 unevaluable.** [measured]

Across both rounds, **29 of 33 findings triaged: 13 confirmed, 7 partial, 4 refuted, 3 already
resolved, 2 unevaluable.** Roughly 45% confirmed outright — which happens to match Codex's own
headline count of 13 non-reproducing claims, though the sets are not identical.

## What the auditor systematically got wrong

This is worth more than any individual verdict, because it tells us how to brief the next audit.
Four patterns, all recurring:

**1. Conflating a corpus boundary with non-existence.** Repeatedly reported items as absent or
untraceable when they were excluded from the staging snapshot *by design* — EXP-01's raw labels in
gitignored `data/`, the private repository histories, the raw session logs. **An agent in a partial
snapshot cannot distinguish "outside this snapshot by privacy policy" from "missing from the
universe".** This is the same failure that made an earlier auditor report `src/consilience/` as
phantom code, and it is the orchestrator's fault both times for not declaring the boundary.

**2. Confusing its own sandbox limits with artefact absence.** When its execution sandbox blocked
Python, it classified deterministic, committed, correctly-`[simulated]`-tagged simulation scripts
as untraceable claims with no results artefact. The script was right there.

**3. Penalising honest labelling.** It treated deliberate, transparent tags — `[ABS]`, `[2ND]`,
`[asserted]` — and problem statements in Context sections as evidence failures. **Honest labelling
is this project's core discipline, not a defect**, and an auditor that scores it as one teaches
precisely the wrong lesson. This is the same category error that produced the refutation in round
one.

**4. Mistaking preserved historical context for an active contradiction.** It read an explicit
supersession notice — old pilot retained alongside the new replication, both drawing the same
conclusion — and reported a contradiction.

## How to brief the next audit

Three things the prompt must carry, none of which the first one did:

1. **The privacy boundaries and the gitignored paths**, explicitly, with the instruction that
   absence within them is unevaluable rather than a finding.
2. **That a blocked execution sandbox is a limit on the auditor, not a provenance failure in the
   repository** — and that saying so is the correct response, as this auditor did honestly about
   its Python substitution.
3. **The distinction between a documentation-level rounding or stale note and a
   decision-invalidating error**, since the decision-impact column turned out to be the most
   useful output and no auditor supplied it unprompted.

## The standing figure

**Four findings remain untriaged**, and everything untriaged stays `[asserted]`. On 29 triaged the
base rate is roughly 45% confirmed outright, 24% partial, and 31% refuted, already resolved or
unevaluable. That is a useful prior for reading an unaudited claim in this file — and not a
substitute for checking it.
