# Corrections — six defects a thirteen-agent adversarial audit found, two of them mine tonight

**Date:** 21 August 2026 (00:15)
**Status:** `[measured]` for every count and file reference below, each re-derived from committed
artefacts; `[asserted]` for the judgement about what follows.
**Source:** an overnight workflow that surveyed the evidence base across five disjoint slices,
ranked fifteen candidate publishable claims down to six, and adversarially verified each with a
novelty search and a refutation attempt.

**Zero of six survived.** That is the headline and it is the correct outcome for a programme that
has been running for two days.

---

## The two I am personally responsible for

I quoted both of these to the principal tonight, repeatedly, in commit messages and in summaries.
Neither is supported.

### C1 — the greenfield blindness figure has no producing script

I wrote, more than once, that *"EXP-43 measured the retro-verifier blind to 72.8–75.9% of merges."*

Checked tonight against the committed artefacts: [measured]

- `results-exp43.json` top-level keys are `run_id, protocol, limitations, complete, stop_reason,
  elapsed_s, records, summary`. **Neither `72.8` nor `75.9` nor `118` appears anywhere in the file.**
- The word `greenfield` appears **only inside a `limitations` string** — prose, not a result.
- `run_exp43.py` contains no classification code that could produce the figure. Its only mention of
  greenfield is the same limitations sentence.

`AGENTS.md` requires re-running the producing script before relying on a number in a findings file.
**There is no script to run.**

The figure is load-bearing in six places: `findings-exp43.md`, `ADR-0040`, `P1-proxy.md` (a draft
paper), `experiment-register.md`, `exp01/stopping_rule.py`, and
`exp01/stopping-rule-verdict-2026-08-20.md` — the last of which I wrote tonight, and in which the
figure supports the argument that the executable replay route is censored.

**This is the exact defect class P2 catalogues, committed by the party who spent the evening
cataloguing it.** A number with no provenance, repeated confidently, propagating into a draft paper.

### C2 — "twice as weakly guarded" compares one check against three

I wrote that the research instruments are *"twice as weakly guarded as the code they measure"*,
citing EXP-49's 0.6825 against EXP-47's 0.3345.

Checked tonight: [measured]

- **EXP-49 ran `pytest` only.** EXP-47's composite is `pytest` **and** `mypy` **and** `ruff`.
- Like-for-like — EXP-49's pytest-only 0.6825 against EXP-47's **pytest-only** 0.3848 — the ratio is
  **1.77×**, not 2×.
- EXP-49's own summary carries `verdict: insufficient_evidence`,
  `comparison_with_exp47: "not_permitted"`, `complete: false`.

**The instrument explicitly refused the comparison and I made it anyway.** My commit argued past the
refusal with an equivalence-sensitivity calculation — that 75.4% of survivors would have to be
equivalent to close the gap. That argument is correct *about equivalence* and never addressed the
check-count mismatch, which is the actual reason the instrument withheld the comparison.

The finding underneath survives in weakened form: the research instruments are **more permissive**
than the product code on a like-for-like single-check basis, 1.77× on an incomplete five-of-six
census. That is still worth knowing. It is not what I said.

---

## Four more, found the same way

| # | defect | evidence |
|---|---|---|
| **C3** | `docs/decisions/index.md` line 3 reads *"39 ADRs, 20 Aug 2026 `[measured]`"*. The directory holds **48** numbered ADRs, and the table carries duplicate rows for 0002 and 0027. **A stale count wearing a `[measured]` tag, in the index of a repository whose first rule is evidence tagging.** | [measured] |
| **C4** | `P3-echo.md` states EXP-47 *"empirically refuted ADR-0012's check-independence assumption"*. Both ADR-0012 itself and `findings-exp47.md` say the opposite and are right: ADR-0012 **assumed unknown dependence and warned against multiplying**. EXP-47 **vindicated** it. Refuting an assumption nobody made is the fastest way to lose a reviewer. I repeated the inverted version tonight too. | [measured] |
| **C5** | `findings-exp43.md` reports *"Tests executed per run: 48"*. `results-exp43.json` records **44** tests in **44 of 50** parent runs and 48 in only six. | [measured] |
| **C6** | EXP-49's census covered **five** targets, not six — `per_target.exp27_handshake` is all zeros. The one instrument that probes what other runtimes can do is unmeasured, and the findings document says so, but summaries elsewhere have described it as a six-target census. | [measured] |

---

## What actually survived, and it is smaller than anyone wanted

One claim, and it is a calibration result rather than a discovery:

> In this codebase `pytest` and `mypy --strict` fail together far more often than independence
> predicts. Over 1,931 mutants, joint survival was **33.82%** [31.74%, 35.96%] against **26.86%**
> predicted by the product — the prediction falls **outside** the interval. χ² = 187.28 (df 1),
> odds ratio **5.15** [4.01, 6.60]. Estimating a two-check gate by multiplying per-check rates
> understates its false-accept rate by **19.7%**.

It is the only quantitative result in the programme that needs **no proxy label, no adjudicator, no
equivalent-mutant correction and no human judgement anywhere in the chain**. The audit also
stratified by source file tonight and refuted the obvious confound: the CLI-formatting mass that
neither check exercises explains only **1.8%** of the association, so 98.2% is within-file. That
stratification is new and was not previously answered.

**And its novelty is 1986.** Knight & Leveson, *An experimental evaluation of the assumption of
independence in multiversion programming*, IEEE TSE. The honest home for this is a calibration
paragraph inside a paper about something else, or a short note positioned explicitly as *"the
modern magnitude of a forty-year-old effect, for a Python gate"*. **It is not a headline and must
never be written as one.**

This is the **third** time in two days that this repository's novelty search has been shown to have
searched the wrong field. ADR-0002's own update already concedes it; the composite-β work found
Eckhardt & Lee (1985) missing from the bibliography; this makes three.

---

## What this says about the method, which is the only good news

A programme that spends two days producing evidence, then spends one night trying to destroy it,
and destroys six of six candidate claims, is working. The failure would have been publishing any of
them.

**The instruments also refused correctly and were overridden by a human — me.** EXP-49 set
`comparison_with_exp47: not_permitted` and I argued past it. EXP-08 refused to emit a marker and
preserved its failed attempt. The machinery was more disciplined than its operator, twice in one
night.

## What happens next

1. **C1 blocks everything.** Either write the script that produces the greenfield census and re-run
   it, or strike the figure from all six locations and mark every claim resting on it as
   unsupported. **Striking it is the default**; producing it after the fact, to justify a number
   already published, is the worse option and should be resisted.
2. C2, C4 and C5 are wording corrections against artefacts that already exist. Cheap.
3. C3 is a generated index that drifted; it should be generated, not maintained.
4. C6 needs `exp27_handshake` measured or the census described honestly as five targets everywhere.

## Reversal and falsifier

**Reversal:** `git revert`; this document is the whole of the change and nothing else was altered.

**Falsifier:** every defect above rests on my reading of committed artefacts tonight. If a producing
script for the greenfield census exists somewhere I did not look — a notebook, an untracked file, a
different branch — then C1 is wrong and the figure has provenance after all. **That is worth
checking before the figure is struck**, and it is the one correction here that destroys information
if I am wrong.
