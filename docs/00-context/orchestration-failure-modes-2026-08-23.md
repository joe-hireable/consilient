# Orchestration failure modes measured on 22–23 August 2026

Every failure below was **observed in this repository while orchestrating real work**, not imagined.
Each cost time, quota, or the principal's attention. Each is recorded here as a **requirement on
Consilient**, because the orchestrator repaired them one at a time and moved on — which is how a
system ends up shipping with its own failures built in.

The principal, 23 August 2026: *"Make sure these are all logged and you are not just working around
errors without specifically instructing the build of consilient to be immune to these common errors
we have experienced multiple times."*

**The test for every entry: would Consilient, as specified today, still do this?** Where the answer is
yes, the entry names what must change.

---

## F-01 — A stalled loop is indistinguishable from a finished one

**Measured.** The build loop ran **120 ticks**, found nothing startable each time, and reported
`working: true`. It was deadlocked: three units were built and could never merge. The status surface
said "idle, nothing running", which reads as *done*. The principal asked for an update; that is how it
was found.

**Requirement.** A loop must distinguish **finished**, **waiting on a dependency**, **blocked on a
condition it cannot clear itself**, and **starved**. "Nothing running" is not a state — it is four
states wearing one label. A loop that cannot make progress and cannot clear the reason **must escalate
rather than tick quietly**. ADR-0034 already says stalls are detected by artefact progress, never by
process identity; this extends it: **no artefact progress plus no startable work plus a non-empty
backlog is a stall, and must be reported without being asked.**

## F-02 — A finished worker can strand its output forever

**Measured.** Seven tracked files sat modified with **no dispatcher running**. The streams that wrote
them completed and exited without committing. Because the merge-back defers on dirty paths, those
paths could never become clean, so three units stayed permanently unmerged and forty downstream units
stayed blocked.

**Requirement.** A dispatch's terminal event must account for **its output as well as its claim**. The
claim already has three release paths; uncommitted output has none. **Either the worker commits, or
the terminal outcome records precisely what it left behind and who owns landing it.** An exit with
uncommitted tracked changes is an incomplete outcome, not a success.

## F-03 — One shared index makes parallel writers collide

**Measured.** `git add` is global. Two agents staging concurrently captured each other's files; the
attribution gate refused the commit, and clearing the index unstaged a live agent's work mid-flight.

**Requirement.** **Isolation beats coordination.** Each worker gets its own tree; only the merge-back
is serial. This was adopted from the principal's own repository layout — roughly a hundred trees, one
per workstream. **Where two workers contend for one resource, ask first whether they need to share it
at all.** Claims then guard genuine file contention only.

## F-04 — Merging a worktree reverts work the worktree never saw

**Measured.** `git merge <worktree-head>` carries the **absence** of every commit landed since that
worktree branched. L01 and L03 conflicted on `events.py` and `effects.py` having edited neither.

**Requirement.** Take **only the commits the worker made** — `HEAD..worker`, cherry-picked — never its
whole tree state. A worker's contribution is its commits, not its snapshot.

## F-05 — Completed work re-dispatched because nothing tracked "in flight"

**Measured.** The driver had no memory of what it had started, so each tick re-dispatched running
units until they tripped the retry cap. F02, F03, F04, F05 and R01 all reached `attempts=3` **while
succeeding**. Roughly three dispatches were spent per unit.

**Requirement.** A scheduler must track **dispatched-and-alive** and **built-but-unlanded** as distinct
states from **not started**. A unit whose output already exists is not a candidate. **Retry counters
must count genuine failures only** — an attempt consumed by infrastructure is not evidence about the
work.

## F-06 — A bookkeeping gate blocked every unit of real work

**Measured.** ADR-0090 named EXP-133 and EXP-134 and wrote neither into the register. A shipped
invariant failed, `suite_green()` gates unit retirement, and **one unregistered experiment held four
completed units** and produced a stall the monitor reported as inactivity.

**Requirement.** Separate **"is this work correct"** from **"is the repository's bookkeeping current"**.
Both must be enforced; they must not share a chokepoint. A documentation defect must not masquerade as
a build failure, and the report must say which it is.

## F-07 — Under-declared claims

**Measured.** F04 changed behaviour that broke `tests/test_coordination.py`, outside its claim set.
F05's failure branch would have edited `harness.py`, undeclared. L01 and L03 both touched files their
claims did not name. **The orchestrator wrote all four claim sets.**

**Requirement.** A claim must cover the **transitive** surface a unit can touch, including its failure
branches. A worker that needs an unclaimed path **stops and says so**; it does not take it. EXP-130
already measured derived claim sets as *a check, not a replacement* — use it as the check.

## F-08 — A stale cache read as current truth

**Measured.** `.harness/headroom.json` was an hour old and reported Codex 94% used and exhausted. A
live probe read **0.0%**. A working arm was benched on a cached number, and work was routed around it
for hours.

**Requirement.** Every cached observation carries its **observation time**, and any consumer that acts
on it must state that time or refuse. **Staleness is a property of the reading, not of the file.** An
absent or expired reading is `unknown` and must fail closed — never silently become a value.

## F-09 — Verification by proxy instead of artefact

**Measured, three times in one day.** `committed()` searched for a unit id in commit subjects, but the
plans' commit messages contain no ids — a finished unit read as unfinished. `suite_green()` passed
`--timeout=600`, unsupported here, so pytest exited on a usage error and **every unit read as
not-green for 66 ticks**. A capability survey grepped for `module.` and missed every
`from module import symbol`.

**Requirement.** This project's own rule, applied to the orchestrator itself: **verify by the artefact
the work was asked to produce.** A checker that cannot distinguish "condition false" from "check
failed" must fail closed. **An absent summary is not a pass.**

## F-10 — The user had to ask

**Measured.** Across this session the principal asked *"how is it going"* repeatedly, and each time the
answer contained something he should have been told unprompted: a deadlock, a red gate, a benched arm,
a defective assumption.

**Requirement, and it is the one that matters most.** **Consilient reports before it is asked.** The
threshold is not "something happened" — it is **"something happened that changes what he would do
next"**: a blocked queue, a failed adversarial review, an exhausted pool, an assumption falsified. The
friction ratchet already counts avoidable escalations downward; **this is its mirror — avoidable
silences must fall too.** A system whose status must be pulled has moved work onto the person it
exists to serve.

## F-11 — Isolation did not remove the collision, it deferred it to a worse place

**Measured.** F-03 was repaired by giving every unit its own worktree. On the strength of that
repair the orchestrator then deleted 18 dependency edges classified ORDERING-ONLY — edges that
existed so two units would not edit the same file — reasoning that isolation made them
meaningless. The critical path fell from 24 levels to 16. It was wrong. **Worktree isolation
removes contention over the git *index*; it does nothing about two units changing the same
file.** The collision simply moves to merge time, where it costs more because both units have
already finished. S01 and S02 both claim `src/consilient/promote.py`, neither declares a
dependency on the other, both were dispatched, and S01's commit would not apply. A survey of the
whole graph then found **667 live unit pairs that share a claimed file with no ordering between
them — 442 of them on `events.py`.** [measured 23 Aug 2026]

**The self-deception is the part worth keeping.** The orchestrator repaired one failure and
treated the repair as licence to delete a safeguard against a *different* failure, because both
wore the phrase "two units, one file". The 16 edges classified UNJUSTIFIED are the same error
with less excuse: **"no reason found" was recorded as "no reason exists".**

**Requirement.** **A unit is verified against the tree it will land on, not the tree it was born
on.** Re-running its own tests in its own worktree proves nothing about an integration that has
moved underneath it. Before a unit counts as built, its commits are replayed onto current head
**inside its own tree**, where the code that caused a conflict is next to the agent that wrote
it — and never under a live worker, which would rewrite the branch beneath it. Where a
constraint is removed because a mechanism made it unnecessary, **the removal must name the
mechanism and state the case the mechanism does not cover.**

**And the conflict is the good case, because it is loud.** A unit forked from a stale base whose
diff happens to apply cleanly lands silently, carrying its own tests, which certify the world it
was born into. **Textually clean, green, and stale is the outcome this requirement exists to
catch**; the merge conflict merely announced that the class of failure was present.

## F-12 — A verifier was widened instead of sharpened, and the loosening was documented

**Measured.** A gate counts occurrences of private repository identifiers in the public tree.
Legitimate citations of *public* upstream projects trip it, because a citation embeds a repository
name inside a URL. Rather than teach the check the difference between a bare identifier — which is
what the original leak looked like — and one inside a public forge URL that names its own
repository, the orchestrator **raised the ceiling and wrote a comment explaining why**, three
times, and recorded that the ceiling now rises once per research stream. [measured 23 Aug 2026]

**Requirement.** In a project whose subject is **β — the rate at which a check accepts a bad
artefact — widening a check's acceptance region is an increase in β, and writing it down is not a
mitigation.** The slack between count and ceiling is precisely the quantity of undetected leak the
gate now admits. A ratchet that only ever moves one way is not a ratchet. **Where a check fires on
a legitimate case, the response is to sharpen the discriminator; raising the threshold requires
naming the β it buys and the date the discriminator lands.** Documentation of a loosening reads,
later, as evidence the loosening was considered — which is exactly why it is dangerous.

---

## What this set has in common

**Ten of the twelve are the same failure**: a signal that was *available* was not *consumed* — the
process list, the observation timestamp, the artefact, the unit's own commits, the register. Only
F-03 is a genuine architectural constraint, and even that dissolved once the sharing was removed
rather than arbitrated.

**The orchestrator repaired each one and continued.** That is the behaviour this document exists to
stop: a repair that lands in a driver script teaches nobody, and Consilient would ship with every one
of these intact. **Each entry above is a requirement, and each should be traceable to a check that
fails if it regresses** — working principle 3, applied to orchestration itself.
