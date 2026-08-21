# EXP-78 findings — promoter false-accept rate

**Date:** 21 August 2026
**Status:** `[measured]` for the counts and verdicts in `results-exp78.json`; `[asserted]` for what they imply about opening the live loop.
**Stopping rule:** applied as pre-registered. It fired.

Every number below appears in `results-exp78.json`. Re-run `python docs/10-research/experiments/exp78/run_exp78.py` before relying on them.

## Verdict

`insufficient_evidence`. The live loop stays refuse-closed. `routing_orchestration_enabled` was not touched (`false` in the artefact as `routing_orchestration_enabled_touched: false`, `loop_open: false`).

## Counts `[measured]`

| Quantity | Value |
|---|---|
| candidates | 48 |
| true_defect | 24 |
| equivalent | 24 |
| unclassifiable | 0 |
| production false-accepts | 0 |
| counterfactual false-accepts | 0 |
| live β verdict | `insufficient_data` |
| live β n_rejected | 0 |

The stopping rule required `n_true_defect >= 30` before a point estimate. **24 < 30**, so no Wilson interval is reported. `production.point` and `counterfactual.point` are `null`.

## What the production arm showed anyway

Every true_defect was refused with reason `disabled`. That is the path that will run today: `ENABLED_BY_DEFAULT` is false and live β is `insufficient_data`. Zero promotions were recorded. It is **not** a measured promoter β. It is the refusal path working as designed on an underpowered sample.

## Why the counterfactual arm cannot be read

The pre-registration asked for a fabricated measured β of 0.19 from 30 rejections. `round(0.19 * 30)` is 6, and 6/30 is 0.20, which is not below ADR-0018's threshold. Every counterfactual row in the artefact is `beta_above_threshold`, including the helpful parent and the Goodhart parent (`harmful`, training 0.6, heldout 0.0). The inner predicate was never exercised. That is a protocol defect, not a finding about Goodhart resistance. A new experiment would be required to measure it; this one does not get a second look at the same data.

## What this cannot decide

Human-verdict promoter β; generalisation from the fixture to `src/consilient`; EXP-12's compounding claim; Gate A or Gate B. EXP-96's product-corpus mutation run was not imported.

## Live consequence

The promoter's error rate is unmeasured. The loop therefore refuses to promote.
