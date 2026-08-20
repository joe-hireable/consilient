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
