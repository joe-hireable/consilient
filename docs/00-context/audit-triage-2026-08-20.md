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
