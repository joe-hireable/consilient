# Autonomous execution from rambled intent — the claim, and what it actually requires

**Status:** product success condition, stated 20 August 2026 by Joe. The baseline observation
below is `[measured]` from this session; everything derived from it is `[asserted]` until
EXP-34 runs. [asserted]

> *"Users like I am right now should be able to ramble visionary concepts into the chat and
> get world class execution fully autonomously within legal and ethical and security and
> safety boundaries."* — Joe, 20 August 2026

This is the success condition. It is also, as stated, unfalsifiable — "world class" and
"visionary" are not measurable. This document turns it into something that can fail.

## The falsifiable form

> For a rambled intent, the quality of the resulting execution **does not depend on the
> rambler's technical expertise**, and the failures that occur are caught by **the harness**
> rather than by an attentive operator noticing.

Two clauses, both testable. The first is the value proposition. The second is the one that
decides whether it is a product or an anecdote, because an unattended system whose errors are
caught by a human watching is not autonomous — it is a human doing quality control at a
higher level of abstraction.

## Baseline observation: this session

Over roughly six hours on 19–20 August 2026, rambled intents produced: a language decision
overturning the agent's own recommendation, an experiment closed with its stopping rule
applied against the closer's preference, three ADRs, a shipped observe-only increment with 27
invariant checks, and a research synthesis over 65 primary sources. [measured] Joe's
assessment of the language decision — *"a decision I would never be able to make alone
without AI's help"* — is direct evidence for the first clause. [measured]

**The second clause failed.** Nine errors occurred. Two were caught by an enforced mechanism;
seven were caught only because the agent happened to look. [measured]

| Error | What caught it | Enforced? |
|---|---|---|
| `beta.render()` unpacked a possibly-null interval; 24 tests missed it | `mypy --strict`, run on a whim during an unrelated assessment | **Now yes** — CI gate |
| A TypeScript recommendation resting on a factually false premise | A delegated lens reading registry metadata | Structure existed; running it was a choice |
| Liveness bound to the wrong process; 30 minutes lost on a finished experiment | The agent eventually checking the artefact | No |
| A launcher exiting 0 while the work never started | Checking the artefact | No |
| A run dying instantly on a `UnicodeDecodeError` | Checking the artefact | No |
| A VRAM probe reporting more free memory while loaded than before loading | The agent noticing the number was impossible | No |
| An experiment result that the closer would have preferred to read differently | The closer's own discipline in applying a pre-registered rule | No |
| An ambiguous "that is approved now" that did not lift a gate | The gate's text plus the agent declining to infer | Partly |
| A message to a paid contractor about unpaid work, nearly sent unilaterally | ADR-0033, written three hours earlier | Rule, not check |

**Two of nine.** That is the measured autonomy gap, and it is the product.

## What this says about the product

The ramble-to-execution loop already works when a sufficiently careful agent is driving. What
does not yet exist is the part that makes it work when one is not — or when the same agent has
an off hour, a longer context, or a result it would rather were different.

Every row in that table is a candidate harness mechanism, and the three liveness rows collapse
into one rule that tonight paid for the hard way:

> **Verify by artefact, never by process identity or exit code.**

A process can be the wrong process. An exit code can report success for work that never
started. Only the thing the work was supposed to produce is evidence that it was produced.
That rule alone would have caught three of the seven unenforced failures.

The remaining four are subtler and matter more, because each is a case where the agent's own
judgement was the only thing standing between a plausible output and a wrong one: an
implausible number, a stopping rule pointing the wrong way, an ambiguous approval, and an
ethically loaded message. Those are exactly the situations in which an agent under time
pressure, or optimising for the user's evident enthusiasm, would go the other way.

## Why the boundaries are not a tax on this

The clause *"within legal and ethical and security and safety boundaries"* reads like a
constraint on the vision. This session is evidence that it is a component of it. [measured]

Four boundaries bound real behaviour tonight, and in each case the constrained output was the
better one:

- The **pre-spec gate** stopped implementation until an explicit approval existed, and the
  first thing implementation authority did was expose a circularity in the specification that
  had just been approved.
- **V0-18** stopped the agent authoring Joe's approval, so the record says "observation of a
  decision" rather than manufacturing the decision itself.
- **ADR-0033** stopped a message being sent to a paid contractor about unpaid work without the
  principal seeing it — where the ethical issue (a financially dependent relationship, and a
  request that would have recruited a third party into unpaid work) was the substance, not a
  formality.
- A **pre-registered stopping rule** produced "the pilot did not replicate" instead of a
  headline the closer would have preferred.

None of these slowed the work down measurably. All of them changed the output. An
unconstrained version of this session would have shipped a spec with a circular gate, a
falsely-attributed approval, a message that put a contractor in an awkward position, and a
replication claim that the data does not support. [asserted]

That is the argument for the boundaries being load-bearing rather than decorative: **they are
what makes "fully autonomously" a claim anyone should accept.**

## What would falsify this

**EXP-34**, to be registered before it runs: over a fixed window of rambled-intent sessions,
count every error and classify what caught it — an enforced check, or a person or agent
noticing. The ratio in this session is 2/9. If the enforced fraction does not rise as the
harness is built, the harness is not doing the job the vision requires, whatever else it
measures. [asserted]

The honest failure mode to watch for: the fraction rising because errors stop being *counted*
rather than because they stop happening. The denominator has to come from somewhere
independent of the mechanism being credited — which is the same correlated-oracle problem
already recorded as Q30. [asserted]
