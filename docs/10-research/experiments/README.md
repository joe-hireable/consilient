# Experiments

`simulations.py` contains all five simulations behind `../findings.md`.

```bash
pip install numpy scipy
python simulations.py
```

## Before you trust anything in findings.md

**Run this first (Q3 in the brainstorm agenda):** replace the difficulty distribution
`rng.beta(2, 2, N)` with a bimodal mixture — say 70% `Beta(5,2)` (easy) and 30% `Beta(2,5)`
(hard) — and see whether the smooth β thresholds survive. If real coding tasks are bimodal,
the thresholds become cliffs and the whole design changes shape.

## What these can and cannot tell you

**Can:** whether an answer flips sign, and roughly where the boundary sits, robustly to the
exact parametric form.

**Cannot:** any number about the real world. β* = 0.111 is a property of an invented
sigmoid-over-Beta model, not a measurement. Experiment 5 is the exception — it is exact
queueing algebra with no simulation assumptions.

## Provenance

Written and executed by Claude (Opus 5) on 19 Aug 2026 in the same session that formed the
hypothesis they test. **They have not been independently reviewed.** That is a real
weakness: the same party designed the model and interpreted the result. Attack them.
