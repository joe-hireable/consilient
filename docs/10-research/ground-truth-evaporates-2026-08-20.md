# The ground truth β needs does not exist on an AI-orchestrated corpus

**Date:** 20 August 2026
**Status:** `[measured]` for the corpus facts; `[asserted]` for the generalisation, which is
this project's inference and is the part most likely to be wrong.

---

## The statement that produced this

Joe Brown, 20 August 2026, asked to adjudicate 55 contested labels from his own repository:

> *"Honestly I do not have the technical expertise to answer these questions because all of
> these PRs and commits were entirely AI orchestrated."* [measured — first-party]

He is the sole maintainer of both measurement corpora and the only human who could supply the
ground truth. He is saying it is not available, and the reason is not time or willingness.

## Why it matters more than it looks

EXP-01's design has a hidden premise. It labels a merged artefact **bad** when the maintainer
reverted or hot-fixed it, on the reasoning that the maintainer's later behaviour proxies for
their judgement. When the proxy is doubted — and it is now measured at 33–48% false positive in
its most contested cell — the stated remedy is a **human audit**: ask the maintainer.

**That remedy was never available on this corpus.** No human verified any artefact at the time,
and the maintainer cannot verify them now. So:

- β's ground truth here is a proxy with **no human fallback**, not a proxy pending audit.
- The 55-question audit was cancelled rather than attempted. ADR-0033 §3 is explicit about why:
  an ask the user cannot cheaply answer *"does not transfer the decision — it launders an agent
  decision as a human one"*. Pressing would have produced rubber-stamps and a β that looked
  measured and was not.
- The revert arm of the proxy already fired **zero times in 224 bad labels**, so the strong
  signal was absent too. Both grounds are gone at once.

## What survives, and what it must be called

Two blind cross-family adjudications of the 75 contested PRs give corrected
**β ∈ [0.81, 0.93]** once the reported agreement is corrected for arithmetic cancellation.
That number stands, and it is the largest result the project has.

**It must be reported as model-adjudicated β, not as β.** The adjudicators read the same
metadata the CI outcome came from. Under `CONSILIENCE.md` clause 2 that is not a different
class of facts, so their agreement with the verifier is not a test of the verifier. Calling it
β without the qualifier would be the exact substitution this project exists to catch.

Joe asked, on the same day, for an agent to author his judgement so the work could proceed.
**The adjudication he wants already exists and is authorised** — EXP-01 label adjudication is
research data, and agents have done it. What is refused is filing it as a first-party
`human_decision` under V0-18, because that would make an agent-derived label indistinguishable
from human ground truth in the record, permanently. The distinction is kept so a later reader
can tell which numbers rest on what. [asserted]

## The generalisation, which is the publishable claim

As more code is produced by AI orchestration, **the human ground truth that verifier-reliability
measurement depends on evaporates.** Not "gets expensive" — ceases to exist. The maintainer of
an AI-orchestrated repository is not a lapsed expert on their own codebase; they were never in
that position.

Every method for estimating verifier error from repository history — SZZ and its descendants
included — assumes a human somewhere in the loop whose behaviour encodes judgement. That
assumption is load-bearing and it is expiring. [asserted]

This is a stronger and more useful claim than the method paper it replaces, and it is only
available because the maintainer said something inconvenient rather than guessing.

## What to do instead — oracles that need no code expertise

**1. The retro-verifier.** Check out an old merge commit; run a *later* test suite against it.
A test that exists today failing on code that shipped green is a defect the contemporaneous
verifier accepted — which is β, mechanically, with no human. Registered and piloted separately;
**its own strongest objection is that later tests are written to catch bugs that were found, so
it may inherit the same survivorship bias as the hotfix proxy rather than introducing a
different class.** That objection is fatal if it holds, and the pilot must answer it before any
number is quoted. A parent-commit control is mandatory: if the parent fails the same test, the
failure is not attributable.

**2. Production outcomes.** Not *"was this PR defective?"* but *"did anything break that week,
did we roll back, did users complain?"* Incidents, error rates and rollbacks are observable
without reading code, and the maintainer can answer them. This is the same move that collapsed
55 individual judgements into 8 policy questions: **change the question to one the human can
actually answer.**

**3. First-party verifier characterisation.** The maintainer states the CI is noisy — bloated,
with live-model evaluation suites that are nondeterministic by construction. [asserted,
first-party] That is legitimate evidence *about the verifier*, which is what α and β describe,
without being a per-artefact verdict. It is recorded as his impression, tagged as such, and it
is not a substitute for either oracle above.

## Falsifier

A second corpus with genuine human code review — a repository where a competent maintainer
reviewed and judged artefacts contemporaneously — would show whether the proxy's failure rate
here is a property of AI orchestration or a property of these two repositories. **Without that
comparison the generalisation is one corpus wide and should not be published as more.** Finding
such a corpus, public and minable, is the highest-value next step for the paper.
