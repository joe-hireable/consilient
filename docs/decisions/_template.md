# NNNN. <The decision, stated as a decision>

- **Status:** PROPOSED | ACCEPTED | PROVISIONAL | SUPERSEDED by NNNN | DEPRECATED
- **Date:** YYYY-MM-DD
- **Deciders:** <who>
- **Inquiry tier reached:** T0 assert | T1 ground | T2 model | T3 measure
- **Executable model:** `NNNN-model.py` | none — <one line saying why none was needed>

## Context

What forces are in play. What makes this a decision rather than an obvious call.
If this is a one-way door, say so here.

## Decision

One paragraph. Active voice. State what we will do, not what we might.

## Evidence

Every line tagged. Group by tag; strongest first.

- `[measured]` …
- `[simulated]` … — from `../10-research/experiments/…`, re-run YYYY-MM-DD
- `[algebra]` …
- `[cited]` … — Author et al. (Year), *Title*, venue/arXiv:XXXX.XXXXX
- `[asserted]` …

## Evidence against

Required section. Not optional, not "N/A" unless you genuinely searched and found nothing —
in which case say what you searched.

- `[cited]` Work that points the other way, and why we decided anyway.
- Known weaknesses in our own evidence: sample size, assumed functional forms, single
  reviewer, conflict of interest.

## Consequences

**Positive** — what this buys.

**Negative** — what this costs. Be specific. "Some complexity" is not a consequence.

**Neutral but load-bearing** — what else is now constrained by this.

## Enforcement

*(Required if this ADR declares an invariant, a boundary, or a chokepoint.)*

The check that makes this real, and where it lives. A chokepoint without a rule banning
bypass is not a chokepoint — see `../30-source-material/prior-repo-assets.md` for the
worked example of how that fails.

- Check: `<script or lint rule>`
- Fails CI: yes/no
- Added in the same commit as the implementation: yes/no

## What would overturn this

Concrete and falsifiable. "New information" is not an answer. Name the experiment, the
measurement, or the paper that would change the decision.

## Publication candidate?

Would this decision plus its evidence be useful to anyone outside this project?
See `../publications/README.md` for the bar. Default answer is **no**.
