# 0109. Bind a review verdict to the unit's own diff, not to every blob it claims

- **Status:** ACCEPTED
- **Date:** 2026-08-27
- **Deciders:** Joe Brown (principal — chose this option from three put to him), orchestrator
  (the measurement, the options, the mechanism)
- **Supersedes:** none. It narrows what `retired_units` binds to; ADR-0037's requirement that a
  unit retire only on a current, consumed SOUND review is unchanged.
- **Inquiry tier reached:** T1 ground — a measured defect with a mechanism, no free parameter.
- **Executable model:** `deliverable_present()` in `.harness/build_driver.py`. Two tests state the
  claim as a pair, and the second is the one that can refute this ADR.

## Context

A unit retires only on a SOUND review whose recorded artefact still matches the tree. Until today
that artefact was `artefact_identity()`: a hash over **every claimed blob** in HEAD.

So a verdict died whenever *any* claimed file changed, for *any* reason — including a change made
by a different unit, to a different part of the file, having nothing to do with the reviewed work.

**How bad that is, measured on 27 August 2026:**

| claimed path | units claiming it |
|---|---|
| `src/consilient/events.py` | **67** |
| `src/consilient/projection.py` | 40 |
| `scripts/dispatch.py` | 32 |
| `src/consilient/work_items.py` | 26 |
| `src/consilient/instructions.py` | 18 |

Every one of the 67 units landing work in `events.py` killed the standing SOUND verdict of the
other 66. At the moment of measurement **ten** SOUND verdicts were dead of exactly this — `A01 A03
AE AF AO B01 B03 BA BF C02` — and **all ten of ten** claimed a file another unit also claimed. The
review lane holds six slots. [measured]

That is a treadmill, and it accelerates: the more units land, the faster standing verdicts are
invalidated, so verdicts can be destroyed faster than six slots can earn them. 31 units had passed
review; 21 could retire.

## Decision

**A verdict binds to the lines the unit's own commits added, and asks whether those lines are
still in HEAD.**

At review dispatch, the unit's own commits (`HEAD..worktree_head`) are reduced to a set of short
line hashes per path and stored on the dispatch record, then carried onto the verdict. At
retirement, `deliverable_present()` asks only whether those lines are still present.

Three details that are load-bearing rather than incidental:

**Captured at dispatch, not at retirement.** A unit's own commits are `HEAD..worktree_head`, which
is **empty once the unit has merged** — precisely the units that reach retirement. Deriving the
fingerprint later is impossible for the only cases that matter, so it is taken while the answer
still exists and travels with the verdict.

**Line hashes, not lines.** Sixteen hex characters per unique added line. Cheap in state, and it
keeps verbatim source out of a file that gets copied into dispatch workspaces.

**The thresholds are `_content_landed`'s, deliberately.** 99% of lines present, minimum twenty
added lines. Two ways of asking "did this work land" that disagreed about how much drift counts as
drift would be worse than either alone. Below twenty lines a diff cannot be told from coincidence,
so such a unit **falls back to the old blob binding** rather than being waved through on a weak
signal — as does any verdict recorded before this existed.

## The claim, and how to refute it

**Claim.** Binding to the unit's own added lines does not admit a unit whose deliverable has been
broken. [measured]

Stated as a pair, because only the second half protects β:

- `test_a_verdict_survives_an_unrelated_edit_to_a_shared_file` — thirty of our lines in HEAD
  alongside forty someone else added afterwards; the verdict **survives**. This is the fix.
- `test_a_verdict_dies_when_the_units_own_work_is_removed` — our lines deleted, and separately a
  fifth of them removed; the verdict **dies** in both cases. **If this ever passes wrongly, this
  ADR is refuted and the binding goes back to blobs.**
- `test_a_diff_too_small_to_identify_falls_back_to_blob_binding` — under twenty lines takes the
  stricter path.

## Evidence against, recorded rather than argued away

**This is a loosening, and it is worth naming as one.** The old binding certified "the reviewer
saw these exact bytes." The new one certifies "the reviewer's finding about this unit's work still
holds." The second is weaker, and the case where the difference bites is real: a unit's lines can
survive verbatim while surrounding code changes their meaning — a guard removed above them, a
signature changed beneath them. Blob binding would have caught that; this does not.

Three things bound the damage, none of which make it disappear:

1. `check_merge_acceptance` already exists to catch semantic breakage a parser misses, and it runs
   at the merge chokepoint rather than depending on a verdict.
2. The alternative is not a stricter system, it is a **stalled** one. Verdicts being invalidated
   faster than they can be earned does not make β better measured; it makes it unmeasured, because
   nothing retires.
3. β is measured over verdicts that were *consumed*, and this changes which verdicts survive to be
   consumed, not what a reviewer was asked. If the measured β moves after this lands, that is a
   finding about this ADR and belongs in the register.

**What would overturn this.** The refutation test passing wrongly. Or a measured rise in β
attributable to units retiring on stale verdicts — in which case the honest response is to narrow
`claims` so units stop claiming files they merely touch, which was the second option put to the
principal and remains available.

## Alternatives rejected

- **Narrow the `claims` lists** so a unit claims only what it owns. Better in principle and it
  attacks the same root cause, but it is 147 hand-edits to a plan file that something is currently
  deleting, and it would invalidate every standing verdict on the way through. Still available if
  this ADR is overturned.
- **Accept re-review as the cost and raise throughput elsewhere.** Rejected on arithmetic: the
  invalidation rate scales with units landed, and `MAX_REVIEWS` is pinned by
  `test_ceilings_are_not_raised_to_paper_over_contention` because raising it was measured worse
  twice.
