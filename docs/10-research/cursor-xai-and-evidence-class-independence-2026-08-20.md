# Cursor is now owned by the company that makes Grok, and its data trains Grok

**Date:** 20 August 2026
**Status:** `[cited]` for the acquisition and the training-data claim, from press reporting read on
20 August 2026; `[measured]` for this repository's own results; `[asserted]` for the consequence and
the proposed check.
**Raised by Joe**, who noted the acquisition and that Grok models are also available inside Cursor.

---

## The fact

SpaceX completed a **$60 billion all-stock acquisition of Anysphere, the maker of Cursor, on
14 August 2026**, folding it into a SpaceXAI division — following SpaceX's merger with xAI in
February 2026. [cited]

One line in the reporting matters more than the price:

> *"Cursor coding data feeds Grok's training pipeline."* [cited]

## Why this project cares, and it is not about ownership

This programme's central constraint is Whewell's second clause and the theorem behind it: agreement
between agents that share evidence is **echo**, not consilience. Every multi-agent structure here
must name the different class of facts it introduces (ADR-0010). Cross-family dispatch — Claude,
Codex, Cursor, and now Grok — is how that difference is currently obtained.

Common ownership alone does not collapse an evidence class. A Gemini model served through Cursor is
still Google's model, trained on Google's data, and Cursor is a harness rather than a model. **The
acquisition does not, by itself, make Cursor and Grok the same class.**

Two things follow from it anyway, and the second is the serious one.

### 1. The served model can drift beneath a fixed request

An xAI-owned Cursor has an obvious incentive to route requests to xAI models. If a request for
`gemini-3.7-flash-high` is ever served by a Grok model, every cross-family result taken through
Cursor since that change is contaminated, and nothing in the result would say so.

**This is the same hazard already recorded against OpenRouter in ADR-0044** — *"the model actually
serving a request may change beneath a fixed model string"* — arriving from a second direction.

The mechanism to detect it already exists and was built for the general case. `adapter_cursor.py`
separates the two:

```python
def model_fields(requested_model, result):
    """Keep a request separate from evidence of the model actually selected."""
    ...
    "model": selected_model or "unknown:not-reported-by-runtime",
    "model_requested": requested_model,
    "model_selected": selected_model,
```

**What is missing is that this is hygiene rather than a gate.** A run that reports
`unknown:not-reported-by-runtime` is currently recorded and used. It should not be usable as
cross-family evidence.

### 2. Work done in Cursor becomes training data for Grok

This is the sharper one, and it has no analogue in the OpenRouter case.

If Cursor's coding data trains Grok, then **the output of one runtime enters the training corpus of
another.** That is a contamination path between two members of the panel whose independence this
project relies on — not today's weights, but a standing pipeline in one direction.

It bears directly on the fourth-runtime admission argument
(`fourth-runtime-admission-2026-08-20.md`), which asked the right question in advance:

> *"The honest test: does Grok fail differently from Codex and Cursor on the same task, or merely
> differently from Claude?"*

That question now has a mechanism attached to it, and a reason to expect the answer to change over
time rather than stay fixed.

## What this does not justify

**It does not justify dropping Cursor or refusing Grok.** Both are paid for, both work, and a
contamination *path* is not a measured contamination. Acting on the mechanism without measuring the
effect would be deciding from a plausible story, which is the failure mode this repository
deprecated an entire ADR over.

It also does not justify treating the panel as three families instead of four. It justifies
**measuring** whether it is.

## The check, and the experiment

**Check, buildable now and small:** a cross-family result may not be taken from a run whose
`model_selected` is absent. Today `"unknown:not-reported-by-runtime"` is recorded and then used;
it should disqualify the run from counting as a *different class*, because an unidentified model
cannot be shown to be a different one. This is ADR-0010's requirement applied to the field that
already exists.

**Experiment, worth registering:** run the same task set through Cursor and through Grok Build, and
through Codex as the control. If Cursor–Grok agreement materially exceeds Cursor–Codex agreement on
the same items, the panel has three effective families and not four, and the fourth-runtime
admission argument loses its main justification. The measurement is the same
inter-instrument-agreement analysis EXP-01 already used when two oracles differed on 16 of 75
labels — the instrument exists.

**Pre-registered reading, fixed before the run:** a raised Cursor–Grok agreement is *evidence of*
shared class, not proof — two systems can agree because both are right. The reading only holds if
agreement is elevated on the items where the families **disagree with the control**, which is where
shared error would show and shared correctness would not.

## Reversal and falsifier

**Reversal:** `git revert`; this document is the whole of the change and nothing was altered in the
adapters or the panel.

**Falsifier:** the training-data claim is `[cited]` from press reporting, not from xAI or Anysphere
documentation, and press summaries of what feeds a training pipeline are frequently loose. If the
data flow is opt-in, excluded for paying customers, or simply not happening, consequence 2 collapses
and only consequence 1 — the served-model drift, which was already a known hazard — remains. That is
worth checking against Cursor's own privacy and data-use terms before this is cited anywhere.
