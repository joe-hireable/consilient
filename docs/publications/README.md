# Publication policy

We publish rarely. The default answer to "should this be a paper?" is **no**.

## Why the bar is high

Publishing "as we go" is how you build a reputation for noise. arXiv cs.AI receives
thousands of submissions a month and most sink without trace; a stream of thin preprints
from one author is read as volume, not contribution, and it is *harder* to recover from
than silence. One well-cited paper does more for an open-source community than ten
forgettable ones — and this project's entire strategy depends on community.

A useful reference point: Meta-Harness (arXiv:2603.28052) reached ~94 citations in five
months because it made one clean, surprising, reproducible claim with released code. That
is the shape to aim for.

## The four gates

A result publishes only if it clears **all four**:

**G1 — Is it true?** Reproduced from a seed. Code released. A second party re-derived the
conclusion from the artefact without seeing our writeup. `[measured]` or `[algebra]`
evidence, not `[simulated]` alone.

**G2 — Is it new?** A real literature search, documented, including the near misses. If
someone did it already, cite them and move on — that is a *win*, not a loss, because it
means we can adopt instead of build.

**G3 — Is it useful to someone who is not us?** Would a stranger change what they build
because of it? "We built a thing and here is its architecture" fails this. "Here is a
measurement everyone assumed and nobody checked" passes.

**G4 — Is it honest about its limits?** Sample sizes, assumed functional forms, conflicts of
interest, the experiments we did not run. Every claim tagged as in `../decisions/README.md`.

## Negative results count

A well-executed null result clears the gates as readily as a positive one, and there are
fewer of them, so they are often more valuable. "We tried X, it did not beat the baseline
under conditions Y, here is the code" saves other people months. Do not treat a failed
hypothesis as an unpublishable one.

## Practical notes on arXiv

- **cs.AI, cs.LG, cs.SE all require endorsement for first-time submitters** without an
  institutional affiliation. Joe has no academic affiliation, so an endorser is needed
  before the first submission. Plan for that lead time — it is usually the binding
  constraint, not the writing. Ask a co-author, or someone who has cited or engaged with
  the work.
- Consider **co-authoring with someone already endorsed**. It solves the endorsement
  problem, adds the independent verification G1 requires, and materially improves the
  paper.
- Licence: arXiv's non-exclusive licence is compatible with everything here. Use CC BY 4.0
  for the paper; code stays MIT.
- **Hugging Face** is the right venue for artefacts — datasets, trace corpora, evaluation
  harnesses — not for the paper itself. A dataset with a good card is often more used than
  the paper describing it.
- A repo-local `docs/publications/NNNN-title/` with the paper source, code and data is the
  minimum. arXiv is optional on top; not every write-up needs to leave the repo.

## Candidate list

Ordered by how close they are to clearing the gates. Nothing here is committed.

### C1. Verifier reliability as a control parameter for agent orchestration
**Status: not ready — needs T3.** The β work (`../decisions/0002-*`). Clears G3 and possibly
G2, fails G1 today (simulation only) and cannot pass G2 until arXiv:2605.00663 is read.
Ready when: β measured on ≥3 real repositories, the β ≡ 1 − critic-recall identity holds
empirically, and the bimodal-difficulty check (Q3) has been run.

### C2. CASD / constrained decoding — **a null result**
**Status: closest to ready, and it should be written as a negative.**

The honest state of that work: the replication landed marginal on clean inputs, bimodal
across cases, and the comparison against the real production baseline — jump-forward
decoding — was never run. Written up as "constrained decoding did not beat jump-forward
under conditions X, here is the code and the traces", it clears G1 (if the missing
comparison is finally run), G2 (null results here are scarce), G3 (people are actively
building on the assumption it wins) and G4 (the limits are the point).

Written up as a success it would clear none of them, and would be found out.

**The missing experiment is the whole paper.** Run the jump-forward comparison first.

### C3. Escalation-on-verification vs learned routing in the coding domain
**Status: bundle into C1.** Too small alone, and simulation-only today.

### C4. Meta-harness adapter interface across heterogeneous coding agents
**Status: speculative.** Only interesting if the interface turns out to be non-obvious and
we have run it against four real CLIs. More likely a good blog post than a paper.

## Format

`docs/publications/NNNN-short-title/` containing `paper.md` (or `.tex`), `code/`, `data/`,
and a `README.md` stating which gates it clears and which it does not.
