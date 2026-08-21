# EXP-01's stopping rule fires — and the consequence it names does not follow

**Date:** 20 August 2026
**Status:** `[measured]` for every count, which is taken from `findings-alpha-2026-08-20.md`,
`findings-exp43.md` and `findings-exp47.md`; `[algebra]` for the sample-size arithmetic, which is
reproducible by `stopping_rule.py`; `[asserted]` for the reading of the rule and for what it means
for ADR-0002.
**No new mining was done.** This is arithmetic over counts already recorded.

---

## The rule, fixed on 19 August before any of this was known

> **Stopping rule:** if the interval cannot be narrowed below ±0.05 with all available history, β is
> not measurable at solo-founder volumes and ADR-0002 fails — the architecture needs a new centre,
> not a patch.

## Part 1 — it fires, and it is not close `[algebra]`

`jobboard-v2`'s metadata proxy gives β = 128/188 = 0.6809 [0.6112, 0.7433], a Wilson half-width of
**0.0661**. `hireable-platform` contributes 21 evaluable bad artefacts. Pooling both corpora gives
**209**.

At the measured rate, ±0.05 needs **n = 332**. At the worst case p = 0.5 it needs 381.

> **209 available against 332 required — 63.0% of what the rule demands, and there is no more
> history.** Both corpora are already in.

The rule fires. History mining cannot measure β to ±0.05 at these volumes, exactly as ADR-0013's
bias control anticipated it might.

## Part 2 — the precision was never the binding constraint `[measured]`

A second instrument exists that the rule's author did not have. EXP-43's executable retro-verifier
reports β = 0/50 = 0.0 [0.0, 0.0714], a half-width of **0.0357** — *below* ±0.05. Taken literally,
that satisfies the rule.

It should not be taken literally, for two reasons, and the second is the important one.

1. It is **censored on 72.8–75.9% of merges.** It cannot evaluate a commit that adds a new
   component, and most commits do. A narrow interval over a quarter of the population is not the
   precision the rule was asking for.
2. **The two instruments differ by 0.6809 on the same quantity.** The proxy says roughly two in
   three bad artefacts pass; the replay says none do.

> The rule's tolerance is ±0.05. **The disagreement between the two ways of measuring the same
> thing is 14 times larger than the tolerance.**

Narrowing an interval whose two methods differ by 0.68 is polishing the wrong number. **The rule
gates on precision when the binding constraint is validity** — which is the same defect shape found
today in Gate A3 and Gate B4: a pre-registered condition that does not measure the thing it was
written to protect.

## Part 3 — β *is* measurable to ±0.05, by an instrument that did not exist when the rule was written `[measured]`

EXP-47, 20 August: composite equivalence-corrected **β = 0.3132 [0.2926, 0.3346]** over 1,931
mutants. Half-width **0.0210** — comfortably inside ±0.05, with no proxy labels, no human
adjudication, no censoring, in **104 seconds**.

So the rule's antecedent — *"the interval cannot be narrowed below ±0.05"* — is **false of β** and
**true of history mining**. The rule silently assumed the two were the same thing. They are not, and
the assumption was reasonable on 19 August because mutation testing had not been considered.

## The verdict

| claim | verdict |
|---|---|
| History mining reaches ±0.05 with all available history | **No.** 209 of 332. The rule fires for this method. `[algebra]` |
| β is unmeasurable at solo-founder volumes | **No.** 0.3132 [0.2926, 0.3346], half-width 0.0210. `[measured]` |
| ADR-0002 fails and the architecture needs a new centre | **Does not follow**, and it is not mine to decide. |

**EXP-01 is recorded DONE with this verdict.** Its two-corpus requirement is satisfied — both were
mined, both carry Wilson intervals, and they are differently verified as ADR-0013 required. What is
retired is the **method**: recorded-CI-verdict mining is not the way this project measures β, and no
further history mining is planned.

**ADR-0002 stays PROVISIONAL.** The rule's stated consequence and the evidence now point in opposite
directions, and reconciling them is a decision about the architecture's centre. That belongs to Joe.
Promoting it on my reading of a rule I am also arguing was mis-specified would be exactly the
laundering this project exists to prevent.

## What this does to Gate A, stated plainly

`consil doctor` reads the register: `A1` passes when EXP-01's entry begins `DONE`. So recording this
verdict **flips A1 from FAIL to PASS.**

That movement is safe to make and I want the reason on the record rather than assumed:

- **Gate A does not open.** A3 remains permanently unsatisfiable
  (`gate-a-cannot-be-passed-either-2026-08-20.md`), so Gate A stays FAIL whatever A1 says. Nothing
  is crossed by inference because nothing is crossed at all.
- **A1's condition is factual, not judgemental.** It asks whether EXP-01 ran on two differently
  verified repositories and produced an interval. It did. Recording a fact the condition asks for is
  reporting, not gate-lifting.
- **It is one revert away.** If Joe judges the evidence insufficient, reverting this commit returns
  the entry to `IN PROGRESS` and A1 to FAIL.

## Reversal and falsifier

**Reversal:** `git revert` this commit. EXP-01 returns to IN PROGRESS, A1 returns to FAIL, and the
stopping rule returns to unadjudicated.

**Falsifier:** the load-bearing step is that mutation-measured β and history-measured β are the same
quantity. **They may not be.** If EXP-50 shows that faults an agent actually emits evade the checks
at a materially different rate from synthetic mutants, then EXP-47's 0.3132 does not stand in for
the corpus β at all, Part 3 collapses, and the rule fires with its stated consequence intact. That
experiment is registered and unrun, and this verdict should be revisited when it reports rather than
treated as settled.

A cheaper falsifier: if the pooled evaluable count is larger than 209 — if `hireable-platform`
yields more than 21, or a third corpus becomes available — recompute. `stopping_rule.py` takes the
counts at the top.
