---
name: dispatching-workers
description: Use before fanning work out to any agent, subagent or second runtime — Claude Code, Codex, Cursor, Grok CLI or a background job. Covers the test that decides whether a second agent adds anything at all, the brief template, identifier allocation, how to tell that a worker ran rather than merely started, when to stop a line, and the report shape a worker owes back. Trigger on "dispatch", "spawn an agent", "run these in parallel", "delegate", "fan out", "get a second opinion", "kick off a worker", or a plan with more than one agent in it.
---

# Dispatching workers

```
VERIFY BY ARTEFACT.
AN EXIT CODE, A LIVE PROCESS AND A NON-EMPTY LOG ARE NOT EVIDENCE THAT WORK HAPPENED.
```

Three silent launch failures in two days on this machine: a launcher that exited 0 while the
work never started; three log redirects that resolved to a stale directory; and a runtime whose
interactive default hung quietly for twelve minutes — process alive, log **0 bytes**, exit code
**0** when killed. [measured] — R1, R13, `docs/20-design/dispatch-layer-requirements-2026-08-20.md`.

They share one property: **the absence of output was the only symptom, and absence is exactly
what a busy orchestrator reads as "still working".**

## First: does a second agent add anything?

**Name the different class of facts the second agent brings, or do not dispatch it.**

Whewell's test is *another different class*. Without new exogenous signals, a delegated network
cannot beat a single decision-maker holding the same information (Ao, Gao & Simchi-Levi 2026,
arXiv:2603.26993) `[cited]`. Agreement between agents that share evidence is **echo**.

This is not only our claim. An independent review-panel project reached the same rule from
production failures and states it as *"consensus does not compound on a shared artifact"* — N
reviewers agreeing after reading the same source lines is **one** source, not N `[cited]`.

Different classes that actually count here: a different model family; a runtime that can execute
what another only read; a corpus the first agent could not see; a measurement rather than a
reading. *Same model, same context, more copies* is not one of them.

Measured cost of ignoring this: EXP-16's convened-meeting arm lost to a single agent — 2 best
and 3 worst against 9 best and 1 worst — at 4.8× the tokens and 3.7× the wall-clock. [measured]

## Stopping rules for a line of work

- **Two no-delta rounds and the line stops.** A round that adds no new fact is the signal.
- **A refusal is a good result.** Distinguish `refused` from `failed` from `completed`. A
  runtime that says "I could not read the brief" is more valuable than one that guesses. Repair
  and re-dispatch; do not treat it as a bad worker. [measured] — R12.
- **Stalling never triggers termination.** A terminal record in the artefact outranks a stale
  liveness signal, and the expensive production failure is a watchdog killing healthy or
  completed work (ADR-0034). Diagnose first.
- **Identify before you terminate.** `pkill -f` on a brief name once failed to match while the
  duplicate had already exited and the survivors were a different task — a blind kill would have
  destroyed correct work. [measured] — R11.

## The brief

Every worker brief carries these, and this template is the portable artefact — paste it into
any runtime:

```
TASK: <one outcome, bounded, non-overlapping with every other live worker>
FILES YOU OWN: <exact paths — one writer per file, no exceptions>
IDENTIFIERS ASSIGNED: <EXP-NN / ADR-NNNN, allocated here. If you need one you were not
  given, STOP AND ASK. Do not read the current maximum and add one.>
EVIDENCE CLASS YOU BRING: <the different class of facts; if you cannot state it, this
  dispatch should not exist>
DONE MEANS: <the artefact that must exist, at what path, containing what — not "finished">
BUDGET: <wall-clock cap; and: no metered API call without a numeric hard cap stated here>
FORBIDDEN: <pushing; publishing; touching another worker's files; any repository other
  than this one>
REPORT: correct this brief in your first paragraph if it is wrong. Then: what you did,
  every claim tagged [measured] / [cited] / [asserted], the reversal path, the falsifier,
  and what you did not check.
```

Two rules about wording, because briefs travel between runtimes:

- **Talk about actions, not tools.** Write "open the file", not "use the Read tool" — other
  harnesses do not share that vocabulary. `[cited]` — the portability lint in
  `wshobson/agents`, MIT.
- **Non-interactive flags are per-invocation, not per-runtime.** A flag that worked this
  morning is not a flag that works now. Check the runtime's own `--help` for the
  script/non-interactive mode before every new invocation shape.

## Checking that a worker ran

In this order. Stop at the first failure.

1. **The named artefact exists at the named path.** Not the log. The artefact.
2. **It is not a stub.** A crashed worker writes a short file. Check size and that the required
   sections are present. An independent review-panel project measured **50 of 51 runs silently
   skipping a whole phase** while reporting success `[cited]`; a phase-existence check is what
   caught it.
3. **Its content answers the brief**, rather than describing the brief.
4. **Ask for the result on a second channel** — a written artefact and a returned summary. One
   channel failing silently is the common case. [measured] — R3.

If a phase is missing, say so loudly and proceed with the banner rather than pretending:
a partial result you have labelled beats a clean-looking result you have not checked.

## What you will be tempted to say

| Rationalisation | Reality |
|---|---|
| "Three agents agreed, so it's solid." | They read the same evidence. That is one source. |
| "The process is running, so it's working." | Alive, 0-byte log, exit 0. Measured here, twice. |
| "It exited 0." | A launcher exited 0 while the work never started. Measured here. |
| "More parallel agents will go faster." | The meeting arm cost 4.8× the tokens and lost. |
| "I'll just take the next free number." | Five agents did. All five chose EXP-58. |
| "I'll kill it and relaunch, it's stuck." | Identify first. A blind kill destroyed nothing only by luck. |

## Enforcement

Identifier collisions: `python .github/scripts/check_record_numbers.py`. Everything else here is
procedure that a dispatch layer should eventually own — R15's second check is exactly that, and
it does not exist yet. Until it does, allocation is a process control, and process controls are
what `dispatch-layer-requirements` exists to replace with checks. Do not mistake this file for
one.

## Harness support

Portable core: the brief template, the different-class test, the four verification steps. All of
it is text, and it works wherever a brief can be pasted — Claude Code, Codex, Cursor, Grok CLI,
or a human. Claude Code additionally has `.claude/agents/worker.md`, which is this contract
wired to a subagent type; the contract, not the wiring, is the part that matters.

## Adapted from

`obra/superpowers` (MIT, Jesse Vincent) — the iron-law/red-flag/rationalisation-table shape, the
capped-round loop, and the rule that a reviewer neither writes nor dispatches its own reviewers.
`wshobson/agents` (MIT) — "talk about actions, not tools", and globally-unique worker names.
`wan-huiyan/agent-review-panel` (MIT) — the phase-existence gate and the independently derived
"consensus does not compound on a shared artifact". Adapted, not copied.
