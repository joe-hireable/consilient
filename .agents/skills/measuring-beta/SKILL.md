---
name: measuring-beta
description: Use before quoting, computing or acting on β — the rate at which the automated verifier accepts an artefact the human rejected. Covers the minimum sample, the sampling condition that silently makes β equal 1, why per-check rates may never be multiplied, and who is allowed to author the verdict β is measured against. Trigger on "beta", "β", "false accept", "verifier accuracy", "how good are the checks", "consil beta", "consil doctor", or any claim that a gate catches some percentage of bad work.
---

# Measuring β

β is the load-bearing number in this project and it is the easiest one to fabricate. Four
defects have already been found in the code that computes it, each of which produced a
plausible figure. [measured] — `src/consilient/beta.py` module docstring.

**Run it; do not reason about it.**

```
PYTHONPATH=src python -m consilient.cli --json beta
PYTHONPATH=src python -m consilient.cli --json doctor
```

`consil doctor` is the authority on gate state. `routing_orchestration_enabled` reports the
gates; it does not open them.

## The five refusals

Each of these is a place to stop, not a caveat to add at the end.

**1. Under 30 human rejections there is no number.** `MIN_REJECTIONS = 30` in `beta.py`, and
the dataclass refuses to construct a `measured` β below it. Report `insufficient_data`.
An underpowered β is worse than none because it is quotable. The floor itself is
`[asserted]`, not derived — ADR-0002 puts verifier calibration at 50–200 labels.

**2. If artefacts only reach the human after the checks accepted them, β is 1 by
construction.** This is the one that matters. The arithmetic in `compute` is correct; the
exposure is entirely in *which rows exist*. `lower_bound_on_joint_error` is `False` by
default and stays false unless you can state the sampling protocol and show it does not
condition on the verifier's own outcome. Do not set it because the bound is convenient.

**3. Never multiply per-check rates.** ADR-0012 assumed dependence is unknown and warned
against multiplying; EXP-47 vindicated it. Over 1,931 mutants, joint survival was 33.82%
[31.74%, 35.96%] against 26.86% predicted by independence — outside the interval, odds ratio
5.15 [4.01, 6.60]. Multiplying understates the gate's false-accept rate by about 19.7%.
[measured] Per-check β is a diagnostic; the composite is the only routing input (V0-06).

**4. An agent may not author the verdict β is measured against.** V0-18. A model scoring its
own work and calling the result β is the echo failure this project exists to detect,
arriving through the data layer. `attempt.outcome` carries the checks; a separate
`attempt.verdict` carries the human decision, authored by the principal. The event layer
refuses the combination — do not look for a way round it.

**5. β measures the pair, not the checks.** The human verdict is fallible, is not independent
of the automated checks, and may not be stationary (Q30). Every report of β carries that
caveat. `consil beta --json` emits it; keep it when you quote the number.

## Reporting it

State: point, interval, `n_rejected`, `verifier_version`, task family, window, and whether a
sampling protocol was declared. A β without its sample count is a rumour.

Tag it `[measured]` only if it came out of the trajectory. A β from a mutation run
(EXP-47/EXP-49) measures a *proxy* oracle, not a human one — say which.

Do not compare two β figures computed over different check sets. EXP-49's pytest-only 0.6825
against EXP-47's pytest+mypy+ruff 0.3345 was reported as "twice as weakly guarded"; the
like-for-like ratio is 1.77×, and EXP-49's own summary carried
`comparison_with_exp47: "not_permitted"`. [measured] — `docs/00-context/corrections-2026-08-21.md`
C2. **The instrument refused the comparison and a human argued past it.** If an instrument
refuses, the refusal is the result.

## Enforcement, so this file is not a prompt pretending to be a check

Every rule above is already enforced in code, which is why this skill may state them:
`Beta.__post_init__` (rules 1 and 5), the default of `lower_bound_on_joint_error` (rule 2),
`V0-06` and ADR-0012 (rule 3), `events.py` `HUMAN_ONLY` and V0-18 (rule 4). If you find
yourself wanting a rule here that no check enforces, write the check instead.

## Harness support

Portable core: the five refusals and the reporting shape — they are arithmetic and policy,
and need no tooling. Claude Code, Codex, Cursor and Grok CLI all read this file as
`SKILL.md`; Codex and Cursor reach it through `AGENTS.md`. The two CLI commands need only
Python 3.13 and the repository, so they run anywhere a shell does.

## Adapted from

`obra/superpowers` (MIT, Jesse Vincent) — the "state the refusals, not the caveats" shape, and
its measured finding that a positive recipe changes behaviour where a prohibition list does not.
The content is this repository's own `beta.py` defect record.
