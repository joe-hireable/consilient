---
name: running-experiments
description: Use before registering, running or reporting any experiment in this repository. Covers the five required register fields, the stopping rule you must write before you look, who allocates the experiment number, when an experiment may legitimately block a build, and the rule that a figure with no producing script is not a result. Trigger on "run an experiment", "register EXP-", "measure whether", "let's test that", "stopping rule", "what does the data say", or any proposal to settle a question by running something.
---

# Running experiments

The register (`docs/10-research/experiment-register.md`) is the unit of record. A run that
was not registered first is data collection wearing an experiment's clothes.

## The entry, before anything runs

Five fields, exact names, in this order:

**Decides** · **Precondition** · **Procedure** · **Measures** · **Stopping rule**

> *"An experiment with no stopping rule is not an experiment, it is data collection."*
> — the register's own header

A sixth is now required by ADR-0050 if the experiment is to hold anything up:
**Largest plausible effect.** An entry that does not state it **cannot be cited as blocking a
build.** Most current registrations do not state it, which means most cannot block.

Status is `READY` · `BLOCKED` · `DONE`.

## The number is given to you, not taken

**Do not read the highest number and add one.** Six agents did exactly that from clones cut at
the same commit and five of them chose EXP-58; the merge was then resolved with "keep both
sides" and duplicated EXP-56 and EXP-57. [measured] — R15,
`docs/20-design/dispatch-layer-requirements-2026-08-20.md`.

- If your brief carries an experiment number, use it.
- If it does not, **stop and ask.** Do not allocate one yourself.
- Where two versions of one record collide, **supersede by key**. Never keep both sides.

Check: `python .github/scripts/check_record_numbers.py`. It fails on a duplicate `EXP-NNN`
heading in the register or a duplicate ADR number in `docs/decisions/`. Run it after any merge
into the register — that is where the second half of the R15 incident happened. It currently
reports three pre-existing duplicates, which is the state it was written to expose.

## Experiments inform; they do not gate

ADR-0049 and ADR-0050. A registered-but-unrun experiment is a reason to record a `PROVISIONAL`
assumption with a falsifier and a reversal path — not a reason to stop building. Before
claiming an experiment blocks something, answer three questions in writing:

1. What is the largest effect it could plausibly show?
2. Would that effect change **what** gets built, or only **how well** it works? An experiment
   that can only tune a component never gates it; one that could show the component should not
   exist does.
3. What does the delay cost?

The guess in (1) is made by the party who wants to proceed, and writing it down *before* the
run is the only mitigation — so write it down before the run.

## Apply the stopping rule honestly, including against yourself

The rule fires on the result, not on how you feel about the result. Two things this repository
has done wrong and you must not repeat:

- **An instrument that refuses is giving you the result.** EXP-49 emitted
  `comparison_with_exp47: "not_permitted"`, `complete: false`, `verdict: insufficient_evidence`,
  and a human made the comparison anyway with a side calculation that never addressed the
  reason for the refusal. [measured]
- **Do not change the protocol once you can see the outcome.** If a run has to stop for a
  reason the entry did not pre-register, that is a new experiment, recorded as one.

`insufficient_data` is a publishable result here. A null result is often the more valuable one.

## Reporting: the producing script is part of the claim

Commit the code under `docs/10-research/experiments/expNN/` and the result beside it. Then:

- **Every number in `findings-expNN.md` must appear in the committed result artefact.** Check
  it by grepping the artefact for the digits, not by remembering.
- Re-run the producing script before relying on a number. If there is no script to run, the
  figure is not a result and may not be tagged `[measured]`.
- A figure that came from a mutation run measures a **proxy** oracle. Say so; do not let it
  stand in for a human verdict.
- Update the ADR it decides by **superseding**, not by silent edit. Move the entry to `DONE`
  with a link.

This is not hypothetical. "EXP-43 measured the retro-verifier blind to 72.8–75.9% of merges"
reached six documents including a draft paper. Neither figure appears anywhere in
`results-exp43.json`, and `run_exp43.py` contains no code that could produce it. [measured] —
`docs/00-context/corrections-2026-08-21.md` C1.

## Harness support

Portable core: the six fields, the allocation rule and the reporting discipline — plain
procedure, no tooling. Read as `SKILL.md` by Claude Code, and reachable from `AGENTS.md` in
Codex, Cursor and Grok CLI. `check_record_numbers.py` is dependency-free Python 3.13 and runs
on any of them.

## Adapted from

`obra/superpowers` (MIT, Jesse Vincent) — the description-states-triggers-only rule and the
rationalisation framing. The register discipline itself is this repository's, from R15 and
`docs/00-context/corrections-2026-08-21.md`. No public skill for experiment pre-registration was
found with evidence of adoption `[asserted]` — absence of evidence, not evidence of absence.
