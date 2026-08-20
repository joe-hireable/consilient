# 0013. Evaluate on our own repository history, not a public benchmark

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — this ADR *is* an evaluation design; see EXP-01.

## Context

Q17. Meta-Harness evaluated on Terminal-Bench. Copying that instinct is the obvious move
and it is wrong for this project.

## Decision

Evaluate primarily on **historical repository data with known outcomes**. Public benchmarks
only later, only for the routing claim, and never for β.

The primary evaluation: take historical pull requests from `jobboard-v2` with known
outcomes — merged clean, merged then reverted, merged then hot-fixed — replay them through
the repository's checks, and compare the check verdict against the known outcome. Every
disagreement in the accept direction is a β event.

## Evidence

- `[algebra]` **β cannot be measured on a benchmark.** Benchmark tasks come with reference
  solutions, not human verdicts on diffs. β is defined as the rate at which checks accept an
  artefact a human would reject; a benchmark has no such human.
- `[measured]` The data exists and is free: `jobboard-v2` has 991 commits in 36 days, with
  PR outcomes, revert history and follow-up fix commits usable as proxy labels. No harness
  is required to run this — it is available today.
- `[cited]` Optimising against a benchmark is a documented failure mode in exactly this
  neighbourhood: *The Illusion of Multi-Agent Advantage* found automatic MAS-design
  frameworks producing architectural bloat while scoring well.
- `[cited]` SWE-bench Verified is contaminated for newer models by training-data overlap;
  the field has been moving to SWE-bench Pro partly for this reason. Benchmark scores would
  be a weak signal even if they were the right target.

## Evidence against

- **`jobboard-v2` is a low-β repository** — ~20 CI ratchets, 44 invariant probes, coverage
  floors. It sits in exactly the regime where cascading looks best. Evaluating only there
  will systematically flatter the thesis. **A weakly-verified contrast repository is
  mandatory, not optional** (`hireable-3.0` is the candidate).
- Single-author history. Joe's review verdicts are one person's standard, and β is defined
  relative to a human judgement that may not generalise.
- Proxy labels are imperfect: a revert may be operational rather than defect-driven; a
  follow-up commit may be a feature rather than a fix. Label noise will need bounding.
- Not comparable to anyone else's published numbers, which weakens the eventual paper.

## Consequences

**Positive.** Measures the actual quantity, on real data, with real labels, today, at zero
cost. Avoids benchmark-optimisation entirely.

**Negative.** No externally comparable score. Reviewers of any publication will ask for one.

**Neutral but load-bearing.** Makes the historical-mining pipeline a first-class artefact
rather than a one-off script — it is the evaluation harness.

## Enforcement

- Check: any published β figure states repository, sample size, label source and confidence
  interval. A test asserts no bare β figure appears in generated output.
- Check: results are reported per repository and never pooled across repositories of
  different verification quality without saying so.

## What would overturn this

- Proxy-label noise proves unboundable, forcing prospective human labelling and a much
  slower measurement path.
- A public benchmark emerges that carries human accept/reject verdicts on diffs — that would
  be directly usable and should be adopted.

## Publication candidate?

**Yes, as the method section of the β paper.** "How to measure verifier false-accept rate
from repository history" is reusable by anyone and is arguably more valuable than our
specific numbers.
