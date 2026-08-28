# 0110. Record the in-place rewrite of ADR-0105, and advance the history pin over it

- **Status:** ACCEPTED 28 August 2026. Accepted by Joe Brown, who chose this remedy from two
  put to him ("1. write the superceding adr"), the alternative being to revert the edit.
- **Date:** 2026-08-28
- **Deciders:** Joe Brown (principal — chose the remedy); orchestrator (the measurement and
  this record)
- **Relates to:** 0105 (the record that was rewritten), 0015 (Gate A condition 3), 0043
- **Supersedes:** nothing. ADR-0105 stands as it is; this records how it got there.

## Context

`tests/test_adr_trail.py::test_history_leg_runs_and_reports_without_failing_prepin` has been
failing with a single item:

    d1c7e9fda silently edits settled ADR docs/decisions/0105-baseline-the-22-august-capture-loss.md

The check is `.github/scripts/check_adr_trail.py::check_history`. Its rule is narrow and
correct: an edit that REMOVES a non-blank line from an ADR whose status is ACCEPTED or
SUPERSEDED is a violation, unless the commit sits at or before a pin. The pin is how a
reviewed edit is acknowledged; everything after it must be clean.

**What the commit actually did.** [measured 28 August 2026] `d1c7e9fda`, 26 August 2026,
titled "docs(adr): propose the 22 August capture loss under its own ratchet", rewrote
ADR-0105 with 199 lines added and 85 removed. Among the removed lines was the status:

    - **Status:** **ACCEPTED 24 August 2026.** Accepted by Joe Brown, 24 August 2026, in the
      orchestration chat after unit AB shipped torn-append refusal.

It converted an ADR recorded as accepted by the principal back into a proposal.

## The finding, and it is not what the failure looks like

**The edit was substantively RIGHT.** ADR-0105 says so itself today, and the reasoning is
already in the record:

> This is the second acceptance claim this ADR has carried; the first ("Accepted by Joe
> Brown, 24 August 2026, in the orchestration chat") **named no matching trajectory event and
> was withdrawn** on 26 August 2026 before this one was recorded. [measured 2026-08-26]

So the removed acceptance had no evidence behind it. Under V0-18 a human decision requires
the human principal as author of a trajectory event, and there was none. Withdrawing an
unbacked acceptance claim is exactly what this project's rules demand — the alternative is a
decision record asserting a human said something no event shows they said, which is the
failure mode the whole trajectory exists to prevent.

The ADR was then accepted properly: Joe Brown, 26 August 2026, "Set it back to accepted.",
recorded as a `decision.gate_amendment` event in `.harness/log/2026-08-26.jsonl`, `event_id`
`080a88db-7cb9-493e-ba14-388d3559c291`, actor and principal `joe-brown`, `via: "cli"`.

**What was wrong was the PROCEDURE, not the content.** The rewrite happened in place, in one
commit, with no marker declaring it. `check_adr_trail` recognises `supersed|update:|corrected|
erratum` in an added line; `d1c7e9fda` added none, so the checker could not tell a correction
from a quiet rewrite — which is precisely its job, and it was right to refuse.

## Decision

**Advance `HISTORY_PIN` from `1db009b` to `d1c7e9fd`, and record the edit here.**

The pin moves over exactly one commit. `d1c7e9fda` was the only violation the check reported,
so advancing to it excuses that edit and nothing else; every later edit remains subject to the
rule unchanged.

The pin is not a loosening. Its meaning in this checker is "reviewed by a human and
acknowledged", and that is now true: the edit has been read, its substance found correct, its
procedure found wanting, and both written down where the next reader will find them.

**Rejected: reverting the edit.** It would restore an acceptance claim that names no
trajectory event, to satisfy a test about honest records. That is the wrong trade in a
repository whose subject is measurement honesty, and Joe chose against it.

## The rule this leaves behind

An in-place edit of a settled ADR must add a line carrying one of `supersed`, `update:`,
`corrected` or `erratum`. That is not decoration: it is the difference between an edit the
checker treats as declared and one it treats as laundering, and it decides which pin governs.

Anyone withdrawing an acceptance claim in future should say so IN the ADR, in those words, in
the same commit. Had `d1c7e9fda` written "Update: the 24 August acceptance named no matching
trajectory event and is withdrawn", the checker would have classified it as declared and no
pin move would have been needed.

## Evidence

- `d1c7e9fda3dc701ac732e5f65a2f9c00c6815650`, 26 August 2026 — the rewrite. 199 added, 85
  removed on `docs/decisions/0105-...md`; `marker_added` computes False. [measured]
- ADR-0105 as it stands: ACCEPTED 26 August 2026 with a named `event_id`. [measured]
- `check_adr_trail.py::classify_edit` — a settled ADR plus any removed non-blank line is a
  violation; `check_history` then consults `SETTLED_RECORD_PIN` when a marker was added and
  `HISTORY_PIN` when it was not.
