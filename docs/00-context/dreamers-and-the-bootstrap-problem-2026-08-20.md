# Humans as dreamers — the vision, and the one thing standing in its way

**Date:** 20 August 2026
**Status:** the vision is `[measured]` as a first-party statement of intent; everything said
about whether it is *reachable* is held against today's measurements and tagged individually.

---

## The statement

Joe Brown, 20 August 2026:

> *"By design everything this harness does will be world-class by default. Every decision made
> will be backed by science, experimentation, mathematics, research, evidence, experience,
> learnings. Humans should rarely contribute meaningfully to anything granular. Humans should
> be turned into dreamers and the harness makes their dreams come true."*

This is not a mood. It is consistent with, and extends, ADR-0033, which already reserves the
human for irreversible and preferential decisions and makes escalating anything else a defect.
It is recorded here because a direction of travel that lives only in a chat log cannot be held
against evidence later, and the whole point of this repository is that claims can be.

## Taking it seriously first

Today produced evidence *for* it, and it is stronger than the argument usually is.

- The maintainer could not adjudicate 55 contested labels **in his own repository**, because
  the artefacts were produced entirely by AI orchestration. Human granular contribution was not
  expensive here; it was **unavailable**. [measured]
- Every substantive defect found today was found by machine and then verified by machine: a
  gate that could never fail, a gate that could never pass, a label proxy 33–48% wrong in its
  most contested cell, an apparent cross-model agreement that was arithmetic cancellation, and
  a private-corpus leak that the orchestrator's own search was structurally incapable of
  finding. [measured]
- The one thing a human supplied that no machine could was **an inconvenient fact about
  himself**, and it produced the most valuable finding of the day. That is a dreamer-level
  contribution, not a granular one, and it is exactly what the vision predicts.

So the direction is not naive. On this evidence it is closer to correct than the usual
human-in-the-loop default.

## The bootstrap problem, stated precisely

**A harness that is world-class by default has to know that it is, and today it cannot.**

β is the rate at which the harness's own checks accept a bad artefact. It is the only quantity
that distinguishes *"world-class by default"* from *"confident by default"*, and the two are
indistinguishable from the inside.

Today's measurement, on the one corpus examined and with the caveats that belong to it:
**β ∈ [0.81, 0.93]** once the two model adjudications are corrected for cancellation.
[measured, model-adjudicated, proxy labels, n=75, one repository]

Roughly four in five to nine in ten bad artefacts pass the checks that were supposed to stop
them. **A system with that verification error rate cannot currently substantiate a claim to
being world-class by default — not because the work is bad, but because it has no instrument
capable of telling.** [asserted]

And the circularity: measuring β has always required a human judging artefacts, which is
precisely the granular contribution the vision removes. Remove it and the harness loses the
only signal that tells it whether its verification works. It would still report success,
because a broken verifier reports success by construction.

## The resolution, and it is in the vision's own spirit

The circularity is real but not fatal, and the way out is better than the problem.

### 1. Take ground truth from the world, not from a human

Production incidents. Rollbacks. Error rates. Users retained. Revenue. A service that stayed up.
A test written six months later that fails on code which shipped green.

These are **exogenous** — a genuinely different class of facts, which is the one thing
`CONSILIENCE.md` insists on and the one thing model adjudication can never be. The world is an
oracle, it does not get tired, and it has no opinion about the code. [asserted]

This makes the retro-verifier and production-outcome grounding the **highest-priority work in
the project**, above interfaces and above more agents. Not because they are interesting, but
because they are the only known route to a β that survives the vision.

### 2. Relocate human judgement rather than removing it

*"Is this pull request defective?"* is a granular question and the maintainer could not answer
it. *"Did this achieve what I wanted?"* is the same judgement one level up, and he can answer
it instantly.

**The vision does not delete human judgement; it moves it to outcomes.** That is what "dreamers"
means operationally, and it is a design instruction rather than a slogan: every ask the harness
makes should be answerable by someone who has not read the code. If an ask fails that test, the
harness is asking the wrong person or the wrong question.

### 3. β is what *buys* autonomy — it is not a tax on it

The framing that matters. Every point of measured verification quality is a decision the human
never has to make again. A harness that knows its own error rate can be trusted further than one
that does not, precisely because it can say *"my verification is too weak here"* on the small
set of cases where that is true.

**Honest uncertainty is what earns autonomy everywhere else.** A harness that never says "I
don't know" has to be checked constantly; one that says it accurately can be left alone. That is
the product, and it is why the honest output is sometimes *"do not route here"*.

## What this changes, concretely

1. **Exogenous oracles move to the top of the queue.** Retro-verifier and production-outcome
   grounding before interfaces, before more adapters, before more agents.
2. **Every ask gets a test before it is asked**: could someone who has not read the code answer
   this? If not, redesign the ask or route it to a machine.
3. **"World-class by default" is not claimed until β supports it.** The claim is retained as the
   goal and tagged `[asserted]`; it is not written into the README, the papers or the product
   surface as a property. Advertising a verification quality this project has measured and
   found wanting is the exact error it exists to catch, and it would be caught — by us, in
   public, later, which is worse.
4. **The human-only class list in ADR-0033 §2 stands unchanged**, but the *granular* end of it
   should shrink as exogenous oracles land. That shrinkage is measurable and should be
   reported: the ask rate is already a required metric.

## The user cannot audit the reasoning, and that is the design

Joe, the same day:

> *"decisions are made based on all kinds of algebraic and scientific stuff in this harness
> that I am nowhere near smart enough to understand — by design 99.9% of it may be beyond the
> users understanding but they can communicate as a visionary, as I am."*

Accepted as the design. It also names the sharpest risk in the whole project, so it should be
stated rather than admired.

**If the user cannot follow the reasoning, "backed by science and evidence" is an unverifiable
claim from their side.** It is exactly the shape a confident wrong system takes: a system that
cites evidence to someone who cannot check the citation is indistinguishable from one that
fabricates it. This repository has already produced four instances of the failure in
miniature — a gate that could not fail, a gate that could not pass, a number wrong in
transcription that became a safety guarantee, and two agents agreeing by arithmetic
cancellation. Every one would have passed a reader who trusted the reasoning.

There is also measured evidence that this design *worsens* the user's ability to catch it.
ADR-0033 records that higher confidence in the AI is associated with less critical engagement
(b = −0.69 log-odds, p<0.001, the strongest effect in that model). [cited] A user told the
reasoning is beyond them, and that it is evidence-backed, will disengage further — which is the
correct response to a system they cannot audit, and it removes the last check.

### The resolution: you do not verify the reasoning, you verify the error rate

A user who cannot follow the algebra can still read *"decisions of this class have been wrong
three times in two hundred, and here is how that was counted."* That is checkable without
understanding a single derivation, because it is a claim about outcomes rather than about
logic.

**β is therefore not an internal metric. It is the trust interface for a system nobody can
audit** — the thing that lets a visionary rely on a harness they cannot follow. [asserted]

This is the same result the human-factors evidence already gave us, one level up. Explanations
barely moved over-reliance, ~70% to ~68%. What took it to **0%** was an error *detector*
rendered in the interface. The repository's own note is blunt about it: *"a verifier works, and
calling it an explanation obscures that."* [cited] At the level of a whole harness the
equivalent is not a better explanation of the reasoning — **it is a published scoreboard of how
often the reasoning was wrong**, broken down by decision class, with the counting method
inspectable by anyone who does want to look.

So the harness does not explain itself to the visionary. It shows its record, including the
parts that are bad, and it says *"do not rely on me here"* where that is true. That is the only
form of trust available to someone who cannot check the work, and it is the one this project
was named to provide.

### What it forbids

- **No confidence scores.** Working principle 5 already bans gating on self-reported model
  confidence; the same applies to what the user is shown. A number the system generates about
  its own certainty is the reasoning restated, not a check on it.
- **No "backed by evidence" as a badge.** Either the specific evidence is linked and tagged, or
  the claim is `[asserted]`. A harness that says "evidence-backed" to a user who will not read
  it has taught them a word, not a fact.
- **No hiding the bad numbers behind the good ones.** ADR-0021's outcome dimensions are reported
  separately and never composited, precisely so a poor one cannot be averaged away.

## Falsifier

If exogenous oracles turn out to be unavailable or uninformative — if the retro-verifier proves
to inherit the same survivorship bias as the hotfix proxy, and production outcomes prove too
sparse or too lagged to attribute — then β cannot be measured without human artefact judgement,
and the vision and the measurement are in genuine conflict rather than merely in tension. **In
that case the honest resolution is to say so publicly and keep a small, permanent, well-designed
human judgement loop**, rather than to quietly drop β and keep the word "world-class".

That is the outcome this document exists to make impossible to reach silently.
