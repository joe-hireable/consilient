# Dispatch layer — requirements measured from a day of hand orchestration

**Date:** 20 August 2026
**Status:** `[measured]` — every requirement below is traced to an incident that happened on
this machine on 20 August 2026, during roughly fifteen real agent dispatches across Codex
(`gpt-5.6-sol`) and Cursor (`gemini-3.7-flash-high`). Nothing here is anticipated.

---

## Why this document exists

Joe, 20 August 2026:

> *"We need to build for increased AI workloads and reducing the need for human interaction
> beyond vision and direction of travel."*

The orchestrator spent the day being that layer by hand. It worked, and it failed in specific,
repeatable ways. **Each failure is a requirement, and each requirement ships with the check
that would have caught it** — working principle 3, applied to orchestration rather than to
code.

This is the highest-value input the dispatch layer has, because it is the only measured one.

## R1 — A launcher's exit code says nothing about whether the agent ran

**Incident.** Every backgrounded dispatch returned exit 0 immediately, because that is the
launcher exiting, not the agent. **Two dispatches silently never started** and were discovered
only when their output files were still zero bytes minutes later. One had a missing
`--skip-git-repo-check`; one had a brief written to the wrong directory.

**Requirement.** Liveness is established from the artefact the work produces, never from the
launcher. A dispatch is `started` only once its transcript is non-empty or its process is
identified. This is ADR-0034 and V0-25 arriving from a second direction.

**Check.** A dispatch with no artefact growth within a configured interval is reported as
`never_started`, distinctly from `failed` and from `running`.

## R2 — Narrowing a sandbox can break it silently

**Incident.** The user's own Codex configuration is `sandbox_mode = "danger-full-access"`.
Passing `-s workspace-write` **narrowed** it into a state where every file write failed while
the agent otherwise ran normally. Two completed audits — 75 PRs and 23 PRs — produced their
results and could not write them. Both survived only because the agents printed summaries to
stdout before reporting the refusal.

**Requirement.** The dispatch layer does not override a runtime's configured permissions
without establishing that the narrowed configuration can still perform the task. Capability is
**probed, not assumed** — write a token file, read it back, delete it.

**Check.** A pre-flight write probe per dispatch. Failure blocks the dispatch rather than
discovering it an hour later.

## R3 — Always require the result on two channels

**Incident.** As R2. The only reason a completed 75-PR adjudication was not lost entirely is
that the brief said *"put everything decision-relevant in stdout as well as in files."*

**Requirement.** Every dispatch declares its result artefact **and** must emit the
decision-relevant summary to the transcript. One channel is a single point of failure and it
failed twice in one day.

**Check.** A dispatch whose declared artefact is absent but whose transcript contains a
parseable result is recorded as `degraded`, not `failed`, and the transcript result is retained.

## R4 — A linked git worktree is not a repository to every runtime

**Incident.** Codex degrades to read-only inside a linked worktree, because a worktree's `.git`
is a **file**, not a directory. Cursor under WSL fails outright with `fatal: not a git
repository`, because that file contains a Windows absolute path WSL cannot resolve — fixable
by exporting `GIT_DIR` and `GIT_WORK_TREE`, which every brief then has to remember.

**Requirement.** The dispatch layer owns workspace provision and picks the form each runtime can
actually use: a linked worktree, an exported environment, or a full clone. The agent is never
asked to work around the boundary. This is EXP-05's finding — *"contained inside the adapter"* —
generalised from paths to workspaces.

**Check.** Per-runtime workspace probe: can it read, write and commit here? Recorded once per
runtime version, not per dispatch.

## R5 — Clones go stale while the trunk moves

**Incident.** A clone was made for one agent at commit `33b753e`. Three branches were merged
into trunk while that agent worked. Its branch, fetched back, would have **reverted 5,838 lines
across 29 files**, including a `mypy.ini` change and three merges. Caught only by reading the
diff instead of trusting a report of "66 passed".

**Requirement.** An isolated workspace records the commit it was cut from. On return, the layer
reports divergence and refuses a merge that would revert trunk commits the workspace never saw.

**Check.** Compare the workspace's base against trunk on return; a merge whose diff deletes
lines the workspace never touched is refused and reported.

## R6 — Line endings destroy reviewability across the WSL boundary

**Incident.** Git inside WSL has no `core.autocrlf`, so agent branches committed the CRLF
working tree verbatim. Three branches returned diffs of **913, 2,691 and 1,814 lines whose real
content was 1, 9 and 48**.

**Requirement.** The layer normalises at the boundary. Fixed by `.gitattributes` with
`* text=auto eol=lf`, which overrides configuration on both sides.

**Check.** A returned branch whose diff shrinks by more than an order of magnitude under
`--ignore-cr-at-eol` is flagged as unnormalised before review. **A diff nobody can read is a
review nobody performs**, and review attention is the scarce resource this whole design is
trying to conserve.

## R7 — Verification is platform-scoped

**Incident.** An agent reported *"47 passed"* honestly. Four of those tests **failed on
Windows**, because the capability they probe exists only inside WSL. The code was wrong; both
observations were correct.

**Requirement.** A verification claim carries the platform it was produced on. `47 passed` is
not a result; `47 passed under WSL` is. Where a project targets more than one platform — and
this one does, by release condition — a claim is complete only when it names them.

**Check.** Verification records include platform, and a release gate requires the matrix the
specification demands rather than any single pass.

## R8 — Prompt delivery is a boundary, and shells eat prompts

**Incident.** A prompt passed as `"$(cat brief.md)"` was **partially executed by the shell**
before reaching the agent, because the brief contained backticks. Passing a *path* and letting
the agent read the file worked every time thereafter.

**Requirement.** Briefs are delivered by reference, never by interpolation. The layer writes the
brief and passes its path.

**Check.** A dispatch whose command line exceeds a threshold, or contains shell
metacharacters, is refused.

## R9 — Relative paths after a directory change

**Incident.** Twice in one day. A brief was written to a worktree root instead of the dispatch
directory, leaving one agent unable to read its own instructions; and three log redirections
resolved to a directory that no longer existed, so three dispatches produced no transcript at
all.

**Requirement.** Absolute paths everywhere in the dispatch layer. The shell's working directory
is not state the layer may depend on.

**Check.** A lint rule over the dispatcher banning relative paths in dispatch construction.

## R10 — Text output on Windows is cp1252 and will crash on real data

**Incident.** Three times. Rendering a review queue crashed on a `γ` in a pull-request title.
The rule was already written down in this repository, for `subprocess`, and did not generalise
to `stdout`.

**Requirement.** UTF-8 with a replacement policy is set once, at the layer boundary, for
subprocess text mode **and** for the process's own streams.

**Check.** A startup assertion on encoding rather than a convention in a document.

## R11 — Identify before you terminate

**Incident.** Two agents were found running the same task in the same workspace after a failed
relaunch. `pkill -f` on the brief name did not match. Enumerating and identifying the processes
first showed the duplicate had already exited and the survivors were a different task — a blind
kill would have destroyed correct work.

**Requirement.** No termination without identification. This is the previously recorded finding
*detection without identification is half a control*, and it is now the second incident.

**Check.** The layer records a dispatch's process identity at launch and refuses to terminate
anything it cannot match to a dispatch record.

## R12 — Agents refuse honestly, and that is a signal to route on

**Incident, and it is the good news.** When Codex could not read its brief, it said so and
**declined to guess**. When it could not write its output, it reported `n_completed: 0` rather
than extrapolating from a partial audit. When the sandbox blocked it, it named the blocker.
Every failure above was recoverable because the agent did not paper over it.

**Requirement.** The layer distinguishes *refused* from *failed* from *completed*, and treats a
refusal as a repairable dispatch fault rather than a bad result. A runtime that refuses cleanly
is more valuable than one that produces something.

**Check.** Refusals are recorded with their stated reason and re-dispatched after repair, and
the refusal rate per runtime is reported — it is a measure of the layer's own quality, not the
agent's.

## R13 — A runtime's interactive default will hang forever, and it hangs *quietly*

**Incident.** A Cursor dispatch was launched as `cursor-agent --force --model ...` with stdin at
`/dev/null`. Twelve minutes later: the process was alive, the log file was **0 bytes**, and the
clone was untouched. `cursor-agent --help` shows why — `-p, --print` is documented as *"for
scripts or non-interactive use"*, and without it the tool starts a TUI that waits for a terminal
that will never arrive. [measured]

Three details make this worse than an ordinary mistake. The process was **alive**, so a liveness
check passed (R1 again, from the other side). The exit code was **0** when it was finally killed.
And the same runtime had completed dispatches earlier in the day, so the invocation *looked*
proven. **A flag that worked in one invocation is not a flag that works in this one.**

This is the third silent launch failure recorded on this machine in two days: a launcher that
exited 0 while the work never started; three log redirects that resolved to a stale directory; and
now an interactive default. They share one property — **the absence of output was the only
symptom, and absence is exactly what a busy orchestrator reads as "still working".**

**Requirement.** The layer holds, per runtime, the **verified** non-interactive invocation, and
never composes one from memory. Before a dispatch is considered launched, the layer requires a
first artefact — any byte on the result channel — within a bounded window, and treats silence past
that window as a launch failure rather than as progress. The window is per-runtime and measured,
not guessed.

**Check.** Two, because one is not enough here:

1. `exp27/handshake.py` — which already probes the installed harnesses at zero inference — records
   the non-interactive flag for each runtime and fails the dispatch if the flag it holds is absent
   from that runtime's `--help`. A flag the tool no longer documents is a flag that no longer
   works.
2. A first-output deadline per dispatch. **Zero bytes at the deadline is a failure, not a wait.**
   This is R1's requirement — verify by artefact — applied to the moment of launch rather than to
   completion, which is where all three of these incidents actually happened.

**Cost of not having it, measured today:** twelve minutes of wall clock and one wasted dispatch
slot. Cheap this time only because something else was being worked on in parallel; a serial
orchestrator would have waited on it indefinitely.

---

## R14 — The orchestrator's own working directory is shared mutable state

**Incident.** A block of product changes — an ADR's enforcement checks, `cli.py` amendments, seven
new tests, a register entry — was committed into `consilient-clone-strict`, the clone a dispatched
Codex agent was working in at that moment. Nothing about the commands looked wrong. They used no
relative paths. Every check passed. `git add -A` additionally swept up four untracked dispatch
briefs. [measured]

The cause was a `cd` issued several commands earlier to run one verification, whose effect persisted
across every command after it. **The clone is a valid checkout of the same base commit**, so
`pytest`, `mypy --strict` and `ruff` all reported clean — they were clean, in the wrong repository.
The only symptom was the push failing, and it failed for the right reason by luck: the clone's
`origin` is the local repository rather than the forge, so the non-fast-forward was refused.

This is R9 (*never use a relative path after a directory change*) in a form R9 does not cover.
**R9 protects the path; nothing protected the repository.** The two failures share a cause — the
shell's working directory is state that persists between commands and belongs to no one — and the
existing requirement addresses only the half that produces visible symptoms.

Worse, it is a *concurrency* fault. A dispatched agent held that working tree. Had it written a file
before the `git add -A`, its half-finished work would have been committed under an unrelated message,
and the eventual harvest would have carried both.

**Requirement.** Every git operation the layer performs names its repository explicitly — `git -C
<absolute path>` — and never relies on the ambient working directory. A repository under dispatch is
**owned by that dispatch** for its lifetime: the layer records which clone each running dispatch
holds and refuses its own writes there until the dispatch returns. Staging is explicit; `git add -A`
in a workspace the layer does not exclusively own is banned outright, because its blast radius is
whatever anyone else happened to leave lying around.

**Check.** Two:

1. Every git invocation carries `-C` with an absolute path. This is greppable and therefore
   enforceable in a way "remember to check the CWD" is not.
2. A commit whose worktree is a dispatch-owned clone is refused before it is written. The layer
   already knows which clone each dispatch holds — it created them.

**Cost of not having it, measured today:** one misplaced commit, four briefs nearly committed, and a
near miss on entangling a running agent's work. Recovered in full only because the agent had not yet
written its first file.

---

## R15 — Concurrent dispatches allocate the same identifier

**Incident.** Six agents ran in parallel tonight, each dispatched from a clone cut at roughly the
same commit. Each read `docs/10-research/experiment-register.md`, took the next free experiment
number, and registered its work. **Five of them chose EXP-58.** [measured]

Nothing was wrong with any individual agent. Each did exactly the right thing — read the current
state, allocate the next free identifier — and the result is five distinct experiments sharing one
number, in the document external contributors will read first.

The same class produced a second defect the same night: resolving the resulting merge conflicts with
"keep both sides" **duplicated** EXP-56 and EXP-57 rather than superseding them, so the register
gained stale `READY` copies of experiments that had already run. The merge strategy was mine and it
was wrong for a file whose entries are records rather than lines.

**This is not a git problem.** Git merged the text correctly; the register has no allocation
mechanism, and read-then-write from N concurrent workers on a shared counter is the oldest race
there is. The trajectory log solved it — `append()` is the sole writer and holds a lock for budget
events (R14's neighbour). The register did not, because nobody had run six agents at it before.

**Requirement.** Any identifier a dispatched agent must allocate is allocated by the **layer**, not
by the agent: the dispatch reserves the ID before the agent starts and passes it in the brief. An
agent that needs an ID and was not given one **stops and asks**, rather than reading the current
maximum and adding one.

Where a shared document accumulates records rather than lines, the merge strategy is **supersede by
key**, never "keep both sides". A conflict between two versions of the same record is a question
about which is current, and the answer is not "both".

**Check.** Two:

1. A test asserting `docs/10-research/experiment-register.md` contains no duplicate `### EXP-NNN`
   heading. `grep -oE '^### EXP-[0-9]+' … | sort | uniq -d` must print nothing. Cheap, and it would
   have caught this the moment the second agent's work was harvested.
2. The dispatch layer allocates and records experiment IDs, so two concurrent briefs cannot carry
   the same one. Until that exists, the orchestrator assigns the number in the brief — which is a
   process control, and process controls are what this document exists to replace with checks.

**Cost of not having it, measured tonight:** five colliding registrations and two duplicated
entries, discovered only because a duplicate-count was run by hand before inviting contributors.

---

---

## What this adds up to

Fifteen requirements, all measured in two days, and **not one is about model capability.** Every
failure was in the plumbing: permissions, workspaces, encodings, paths, process identity,
delivery. The models did their work; the harness around them is what failed, repeatedly.

That is the meta-harness thesis stated as an incident log rather than an argument, and it is the
strongest evidence this project has produced for its own existence. It also sets the honest
expectation for scaling: **increased AI workload is not gated on the agents. It is gated on
fifteen boring things, each of which now has a check.**

## Falsifier

If a dispatch layer implementing all fifteen still shows the same rate of lost work over the next
fifty dispatches, then the failures were not the plumbing and this analysis is wrong. The
measurement is cheap: lost-work rate per dispatch, before and after, on the same task mix.
