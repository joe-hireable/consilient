---
name: writing-adrs
description: Use when recording any non-trivial architecture or design decision in a Joe Brown project. Covers the evidence-tag discipline, the required "Evidence against" section, when a decision needs an executable model, and when to supersede rather than edit. Trigger on "write an ADR", "record this decision", "we've decided X", or when a conversation settles a design question that will constrain later work.
---

# Writing ADRs

An Architecture Decision Record is the unit of record. Not a chat message, not a commit
message, not memory.

## When an ADR is needed

Write one when the decision **constrains later work**. Skip it for reversible, local,
low-blast-radius choices.

Quick test — write an ADR if any hold:
- It is a one-way door (schema, protocol, wire format, public API, licence, name).
- More than a handful of artefacts will depend on it.
- Someone in three months will ask "why on earth is it like this?"
- You changed your mind about something already recorded.

## The format

Copy `docs/decisions/_template.md`. Four digits, monotonic, never reused. Title states the
**decision**, not the topic: `0009-route-per-task-not-per-step.md`, not `0009-routing.md`.

## Evidence tags — the discipline that makes these worth reading

Every claim carries one:

| Tag | Means |
|---|---|
| `[measured]` | Observed in a real system we ran |
| `[simulated]` | Output of a model with assumed functional forms |
| `[cited]` | From a named source |
| `[algebra]` | Exact derivation from stated assumptions |
| `[asserted]` | Judgement, no evidence yet |

`[asserted]` is honest. Mislabelling is not. **Never upgrade a tag without new evidence.**
Downgrades are expected and healthy.

Do not report a `[simulated]` figure as a fact about the world. Simulations answer
*sign and threshold* — "does the answer flip, and where?" — never "what is the number?".

## "Evidence against" is required

An ADR citing only supporting work is advocacy, not a record. This section must contain:

- Sources that point the other way, and why you decided anyway.
- Weaknesses in your own evidence: sample size, assumed functional forms, single reviewer,
  conflict of interest, motivated reasoning.
- If you searched and found nothing against, say **what you searched**.

If you cannot write this section, you have not finished thinking.

## Does it need an executable model?

Gate it (`docs/20-design/inquiry-tier.md`): a one-way door **and** dispersed priors **and**
formalizable — meaning you can name a decision variable, an objective, and one unknown
parameter. If you cannot name all three, no model. Naming conventions do not get one;
routing thresholds do.

When it does: commit `NNNN-model.py` alongside. CI re-runs it. A sign flip fails the build.

## Enforcement section

If the ADR declares an invariant, boundary or chokepoint, it must name the check that makes
it real and confirm it ships in the same commit as the implementation.

**A chokepoint without a lint rule banning bypass is not a chokepoint.** This is not
theoretical — `jobboard-v2`'s documented "unified `llm()` boundary" fragmented into five
access paths because no rule forbade bypass, with the highest-cost paths escaping entirely.

## Superseding, not editing

Never rewrite an ACCEPTED ADR to reflect a changed mind. Write a new one that supersedes it
and say what changed and why. **The trail of reversals is the most valuable thing in the
directory** and it is the first thing people delete.

Exception: adding an `## Update:` section with new evidence to a PROVISIONAL ADR is fine,
and should be dated.

## Statuses

`PROPOSED` → `ACCEPTED` → (`SUPERSEDED by NNNN` | `DEPRECATED`)

Plus **`PROVISIONAL`**: accepted for now, resting on `[simulated]` or `[asserted]` evidence,
with a named experiment that would confirm or kill it. A PROVISIONAL ADR unconfirmed after
three months is a bug — chase it or downgrade the decision.
