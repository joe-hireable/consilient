# 0107. A unit may merge into a red tree; nothing may publish from one

- **Status:** ACCEPTED — decided by the orchestrator on the principal's explicit delegation,
  25 August 2026: *"Make the decision yourself."* Recorded here rather than settled in code so
  the reasoning is attackable. It is reversible: the enforcement point is one predicate.
- **Date:** 2026-08-25
- **Deciders:** the orchestrator, under delegation from Joe Brown
- **Relates to:** plan unit BJ (which asks this question and now has its answer), V0-06,
  0012 (never multiply per-check rates), 0057 (append-only trajectory)
- **Answers:** BJ — "decide whether a unit may merge into a red tree, and enforce the answer"

## Context

`merge_unit_worktree` cherry-picks a unit's own commits onto HEAD. Nothing consults the suite
before it does. `publish_if_ready` does: it refuses while `suite_green()` is false and then runs
four leak gates. So today the tree may go red and work keeps landing on it, while nothing leaves
the machine. Whether that is correct has never been decided, and BJ was queued to decide it.

The question arrived attached to a stranded commit. `0369345ff`, "atomic state, parsed verdicts,
no cherry-pick onto red", is one of eight commits found stranded in dispatch workspaces on
25 August. Two of its three features are already in HEAD by other routes and better — state is
written through `os.replace`, and verdicts are read from a bound `<uid>-verdict.json` receipt
rather than parsed out of stdout. The third is this question. Its diff is 811 lines against
`build_driver.py` from an old base and does not apply; forcing it in would revert work landed
since. So the feature is decided here and implemented fresh, and the commit is superseded rather
than merged. Unit AI is escalated on exactly that conflict.

## Decision

**A unit may merge into a red tree. Nothing may publish from one.**

Enforcement stays where it already is for publication, and the merge path gains one obligation:
a merge performed while the suite is red records that fact in the trajectory alongside the merge,
with the failing count observed at the time.

## Why

**Publication is the irreversible step, and it is already gated.** [measured] What leaves this
machine is what needs a green tree; a cherry-pick onto a local branch is revertible with one
command. Spending the gate where the damage is recoverable, and not where it is not, gets the
protection backwards.

**A red suite here is frequently not about the code.** Measured this day: ten suite failures, of
which several were `test_v0_invariants` cases that shell out to git — while git in this repository
was broken by a `core.worktree = /mnt/c/...` line an agent wrote into the shared config. The same
run showed four failures at 35–54% that a re-run at identical progress did not reproduce, under
roughly fifty concurrent agent pytest processes on 32 cores. A gate that blocks on that signal
blocks on infrastructure, and it does so hardest exactly when the machine is least able to clear
it — which is the metastable shape this repository has already measured twice.

**Blocking would freeze the thing that produces the evidence.** 74 units are built and awaiting
merge or review. Refusing every merge until green stops all of them behind failures they did not
cause, and a build that lands nothing generates no verdicts, no β, and no way to discover that
the suite was red for an infrastructure reason in the first place.

**The QA gate is the review, not the suite.** A unit retires on a SOUND verdict bound to
`artefact_identity` — the hash of the exact committed blobs the review was permitted to judge.
That binding is what makes the verdict mean anything, and it is unaffected by the colour of tests
belonging to other units. Treating the suite as the retirement gate would quietly substitute a
weaker, shared signal for a stronger, bound one.

## Evidence against, and what would overturn this

**The strongest objection: attribution decays.** Merging onto red lets a unit's own regression hide
among pre-existing failures. Nobody can then say which merge broke what, and the longer the tree
stays red the worse it gets. This is a real cost and the decision does not eliminate it — it pays
for it with the recorded suite state, which preserves attribution after the fact rather than
preventing the confusion. That is weaker than refusing the merge, and it is chosen knowingly.

**Second objection: it removes pressure to fix red.** If work lands regardless, red stops being
urgent. The counter is that publication blocks, and publication is what the principal wants; but
if the tree is observed staying red for long periods with merging continuing, that is this
decision failing, not the suite failing.

**What would overturn it.** If a post-hoc audit finds a defect that reached HEAD and was masked by
a red tree — one a green-gate merge would have caught — this is wrong and should be superseded by
the strict rule. That audit is the killing experiment and it needs the recorded suite state to be
runnable at all, which is why the record is not optional.

**What was NOT decided.** Whether a unit may merge while ITS OWN tests fail. That is a narrower
and stronger gate, it is cheap to want and expensive to implement correctly (it needs a
test-to-unit mapping this repository does not have), and it is left open rather than assumed.

## Consequences

- BJ implements the recorded suite state at merge time; the question it was queued to answer is
  answered here. BJ is unblocked.
- AI's `0369345ff` is superseded, not merged. Its atomic-state and parsed-verdict features are
  already in HEAD by better routes; its third feature is this ADR.
- `publish_if_ready` is unchanged. It already does the right thing.
