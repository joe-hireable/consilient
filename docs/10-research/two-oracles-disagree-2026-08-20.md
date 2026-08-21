# Two oracles, two orders of magnitude apart

**Date:** 20 August 2026
**Status:** `[measured]` for both estimates and their conditions; `[asserted]` for the
reconciliation, which is an argument and not yet a measurement.

---

## The numbers

Two independent oracles have now produced a β on `jobboard-v2`. They do not agree, and the gap
is not small.

| oracle | β | n | what it conditions on |
|---|---|---|---|
| revert-or-hotfix proxy, cross-family adjudicated | **0.81 – 0.93** | 75 contested of 203 bad | metadata: a title regex, a file-set intersection, and a CI rollup |
| retro-verifier, forward test replay with parent control | **0.0** [0.0, 0.2039] | 15 subsystem pairs | bytecode: does a later test fail on this commit and pass on its parent |

The proxy says the checks accept roughly nine in ten bad artefacts. The retro-verifier found
**zero** defects in fifteen pairs. Its own stopping rule fired `inconclusive`, correctly.

**Their intervals do not overlap.** [measured] That is either a contradiction or a sign the two
are not measuring the same quantity, and the second is much more likely.

## Why this is progress rather than a problem

`CONSILIENCE.md` says convergence between different classes of facts is a test of truth. It does
not say what to do when they diverge — but ADR-0010 and the founding principle both do:
**divergence is a finding, not a failure to be smoothed over.** These two oracles share nothing.
One reads commit messages; the other executes code. A number that survived both would have been
worth a great deal, and a number that does not survive both is worth knowing about now rather
than after publication.

Had only the proxy run, β ≈ 0.87 would be in a paper. Had only the retro-verifier run, β ≈ 0.0
would be. **Neither would have been flagged, and each would have looked well-evidenced.**

## The reconciliation, and it is not a compromise

The two quantities are genuinely different and both estimates may be correct on their own terms.

**The proxy over-labels.** Cross-family adjudication refuted 33–48% of the labels in the cell it
examined, and every label in the corpus came from the weak hot-fix arm — the revert arm fired
zero times in 2,506 commits. [measured] A proxy that flags a defect whenever a later PR with a
fix-shaped title touches a shared file will flag a great deal that is not a defect. β computed
over inflated "bad" labels is inflated.

**The retro-verifier under-samples, and says so.** Its own findings record it measuring
**β restricted to regressions that later tests were written to catch**, not general β. Tests are
written for defects that surfaced; latent defects nobody found are invisible to it by
construction. It also has a near-fatal structural blindness the pilot discovered: **a commit that
introduces a new component cannot be evaluated at all**, because the parent lacks the symbols and
the later tests fail on it with an import error, which the control correctly classifies as drift
rather than defect. So it can only judge modifications to interfaces that already existed.

So: the proxy's numerator contains things that are not defects, and the retro-verifier's
denominator excludes most of the places defects live. **One is biased up, the other down, and
the true β is bracketed rather than pinned.** [asserted]

## The single most valuable thing the pilot established

**Without the parent-commit control, the retro-verifier would have reported β = 1.0.** [measured]

On the monolithic suite, all five historical commits failed 3–7 tests when replayed against
HEAD's tests. A naive retro-verifier — check out the old commit, run today's tests, count
failures — would have classified 100% of them as defects the checks let through. The parent
control showed the parents failed identically, so the failures were test-suite drift and not
attributable to any artefact.

That is a check that could have produced a maximally alarming, entirely wrong number, caught
before it was ever quoted, by a control that cost one extra checkout per pair. It belongs in the
guards paper.

## What follows

1. **Neither β may be published as *the* β.** Each is reported with its conditioning, its n and
   its bias direction, or not at all.
2. **The retro-verifier must run on subsystem-scoped suites, never the monolith.** Measured drift
   rate: 0% on an isolated subsystem, 100% on the full suite. The monolithic arm is not a weaker
   version of the experiment; it is uninformative.
3. **n = 15 decides nothing.** EXP-43's primary evaluation is n = 50 and even that yields a wide
   interval at a low event rate. The measured cost is ~1.5 s per commit pair on a subsystem
   suite, so a much larger n is affordable — the constraint is which commits are *evaluable*,
   not the compute.
4. **The greenfield blindness bounds the whole method.** Quantify it before scaling: what share
   of the corpus's merges add new components rather than modify existing ones? If it is most of
   them, the retro-verifier can never be more than a narrow supplement, and that should be
   established with a count rather than assumed.

## Falsifier

If a larger retro-verifier run on subsystem suites returns a β whose interval overlaps
[0.81, 0.93], the reconciliation above is wrong: the two oracles would agree after all, the
proxy's refuted labels would not have mattered, and the divergence would have been small-sample
noise dressed up as a structural argument. **That is the cheap test and it should be run before
this document is cited.**
