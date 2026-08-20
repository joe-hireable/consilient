# The other half of β\* is invented, and the real value moves every threshold

**20 August 2026.** Produced by the agent assigned P11 — the override channel — several hours
before I read its report. It is the most decision-relevant thing found overnight after the axis
defect, and it sat unread while I worked on smaller things. That delay is mine. [measured]

## What the sweep got wrong, and why the correction matters

The post-experiment sweep recorded (item P11) that the converse of β — *checks reject, human
accepts* — **"has no name"** and appears nowhere as owed work.

**It has a name. It is α**, defined in `simulations.py` as `P(verifier rejects | artefact is
good)` — the flaky-test rate — and it is not peripheral. It is the other factor in the closed form
the entire architecture turns on:

```
β* = (1 − α) · e^(−k·Δ)
```

It appears in ADR-0002's closed-form update and in its falsifiability paragraph as an explicit
lever — *"lowering α (deflaking tests) enters β\* through the other factor"* — in ADR-0026's
consequences, and twice in `v0-draft.md` as one axis of the `(Δ, α, β, ρ)` surface. [cited]

So it is named, modelled, and load-bearing. What it is **not** is measured. There is no denominator
for it in `beta.py`, no consumer in `projection.py`, no line in EXP-01's *Measures*, no register
entry, and no Q-number. [measured]

**Its only value anywhere in this repository is `α = 0.03`, invented in `simulations.py` and
repeated in `findings.md`.**

## What the real value looks like

`jobboard-v2` merged **98 of 300** pull requests over red CI — an override rate of **0.3267**,
Wilson 95% [0.2761, 0.3816]. `hireable-platform` gives **7 of 49** with recorded checks, 0.1429
[0.0710, 0.2667]. [measured]

Substituting the first into the closed form, with the ADR's own k = 8:

| capability gap Δ | β\* at α = 0.03 (assumed) | β\* at α = 0.327 (measured override) |
|---|---|---|
| 0.42 | 0.0337 | **0.0234** |
| 0.27 | 0.1119 | **0.0776** |
| 0.10 | 0.4358 | **0.3024** |

The scale factor is exactly **(1 − 0.327)/(1 − 0.03) = 0.6938**, at every gap, because β\* is
linear in (1 − α). [measured — recomputed here with the repository's own `wilson()` and k = 8]

**Every threshold in this project may be roughly 31% tighter than the documents assume, and the
error runs in the optimistic direction:** the invented α makes routing look safer than the
measured override rate suggests.

## The caveat, which is not optional

**0.327 is not α, and must not be quoted as α.**

It is red-merged over merged, so it is selected on the merge decision, and it uses *"the human
merged it"* as the proxy for *"the artefact is good"*. That carries the joint-error caveat β
already carries, **plus** a selection bias β does not. [asserted]

What it is, honestly: `[measured]` evidence that α on a real repository is **an order of magnitude
away** from the value the closed form is evaluated at. It establishes that the assumption is
wrong and which way; it does not establish the replacement.

## Why this is cheap to fix, which is the surprising part

α and β are the two off-diagonal cells of one 2×2 table — `verifier_accept × human_verdict` — and
their denominators **partition** the labelled set. Every artefact with a human verdict lands in
exactly one.

So the sample-size consequence runs **opposite** to intuition:

- **α does not need its own verdicts. It needs the ones β discards.**
- `projection.py` already stores both columns, so the `(verifier_accept=False, human_verdict=
  'accept')` cell is already in `outcomes`. α is a `SELECT` over data the observe-only increment
  already records. [measured]
- And the scarcity inverts: `MIN_REJECTIONS` wants 30 human **rejections**; α wants 30 human
  **accepts**. On any corpus mined from merges, accepts dominate overwhelmingly.

**α is measurable today on the corpus where β is not.** That is the finding worth acting on.

## And it reached the axis defect first

The same report, hours before the adversarial workflow did, enumerated **three non-equivalent
definitions of β in circulation**:

| Where | Denominator | Quantity |
|---|---|---|
| ADR-0002 § Context | artefacts that are actually bad | P(accept \| bad) |
| ADR-0002 § β sample complexity | accepted diffs | P(bad \| accept) |
| `beta.py` | human rejections | P(accept \| reject) |

EXP-01 reports the second. **They agree numerically on `jobboard-v2` only because the marginals
coincide** — 203 bad-labelled against 202 green — which is exactly the coincidence recorded
separately in `beta-axis-defect-2026-08-20.md`. Four independent routes have now reached the same
place. [measured]

It also drew a consequence none of the others did: `MIN_REJECTIONS = 30` cites ADR-0002's *"50–200
labels"*, but **that range was sized for the accepted-diffs denominator, not the human-rejections
one**. Nothing dishonest is claimed — the constant is tagged `[asserted]` — but the citation
points at the wrong denominator.

## What Joe has to decide

1. **Does α get measured?** It is a `SELECT` away and it moves every threshold by ~31%. My
   recommendation is yes, and first, because it is cheaper than anything else on the list and its
   absence silently biases every safety comparison optimistically.
2. **Does α enter v0's scope as a reported quantity**, alongside β? The 2×2 argument says the
   marginal cost is close to zero once verdicts are being recorded at all.
3. **What replaces `α = 0.03`** in the interim — the invented value, the measured override rate
   with its caveat, or an explicit "unmeasured, do not evaluate the closed form" until it is?
   Continuing to evaluate β\* at an invented α is the option I would not choose.


---

# Correction — I conditioned α on the wrong thing, in the document about conditioning on the wrong thing

The figure above, **0.327**, is not α. It is `red / all merged PRs` — the **marginal** rejection
rate. α is defined as `P(verifier rejects | artefact is good)`, which needs the **conditional**:
the good-and-red cell over all good artefacts. [measured]

Found by an adversarial run this morning; recomputed here from the raw labels before recording.

## The full 2×2, which nobody had ever built

Aggregate counts only, as the privacy rule permits.

**`jobboard-v2`** (300 merged PRs)

| | green (accepted) | red (rejected) |
|---|---|---|
| **good** | 74 | **23** |
| **bad** | 128 | 75 |

**`hireable-platform`** (56 merged PRs, 7 with no recorded checks)

| | green (accepted) | red (rejected) |
|---|---|---|
| **good** | 24 | **4** |
| **bad** | 18 | 3 |

## What α actually is

| | `jobboard-v2` | `hireable-platform` |
|---|---|---|
| **α = P(reject \| good)** | **23/97 = 0.2371**, Wilson [0.1635, 0.3307] | **4/34 = 0.1176**, Wilson [0.0467, 0.2662] |
| what I wrote — `red / all` | 98/300 = 0.3267 | 7/56 = 0.1250 |
| β = P(accept \| bad) | 128/203 = 0.6305 | 18/22 = 0.8182 |

## What that does to the claim

The direction survives and the magnitude does not.

| α | β\*(k=8, Δ=0.27) |
|---|---|
| 0.03, assumed and invented | 0.1119 |
| **0.2371, the correct proxy** | **0.0880** |
| 0.327, what I wrote | 0.0777 |

The scale factor against the assumed value is **0.7865**, not the 0.6938 recorded above. So the
honest statement is that thresholds are roughly **21% tighter**, not 31%. [measured] **α is still
an order of magnitude above the invented 0.03, still measured, and still moves every threshold in
the optimistic direction.** The overstatement was mine and it was material.

## The part worth keeping

**I made the same class of error I had spent the night documenting.** The β axis defect is that
`mine_beta.py` conditions on "accepted" where the definition needs "bad". My α figure conditioned
on "all PRs" where the definition needs "good". Both substitute a marginal for a conditional; both
survive casual reading because the numbers are plausible; and mine appeared in the very document
correcting the other. [measured]

That is not a coincidence to be noted and moved past. **A 2×2 table has four cells and this
project keeps reaching for the wrong denominator**, which suggests the defence is not care but
structure: *build the table first, then read quantities off it.* The table above took minutes
from labels that had been on disk since 19 August, and neither error would have survived it.

**And building it closed the first item of the measurement order for free.** The good-and-red cell
— 23 artefacts the checks rejected and the human then merged anyway — is the material α needs, and
it was always there.

**One caveat that does not change with the arithmetic.** These are proxy labels with 1/15 audited
precision, and "the human merged it" stands in for "the artefact is good". This is `[measured]`
evidence that α is far from 0.03 and which way. It is still not an estimate of α.
