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

---

## What this adds up to

Twelve requirements, all measured in one day, and **not one is about model capability.** Every
failure was in the plumbing: permissions, workspaces, encodings, paths, process identity,
delivery. The models did their work; the harness around them is what failed, repeatedly.

That is the meta-harness thesis stated as an incident log rather than an argument, and it is the
strongest evidence this project has produced for its own existence. It also sets the honest
expectation for scaling: **increased AI workload is not gated on the agents. It is gated on
twelve boring things, each of which now has a check.**

## Falsifier

If a dispatch layer implementing all twelve still shows the same rate of lost work over the next
fifty dispatches, then the failures were not the plumbing and this analysis is wrong. The
measurement is cheap: lost-work rate per dispatch, before and after, on the same task mix.
