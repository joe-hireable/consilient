# 0105. Baseline the 22 August capture loss

- **Status:** **ACCEPTED 24 August 2026.** Accepted by Joe Brown, 24 August 2026, in the
  orchestration chat after unit AB shipped torn-append refusal. Extends ADR-0043 Gate A
  condition 3. The checks named in Enforcement ship with this acceptance.
- **Date:** 2026-08-24
- **Deciders:** Joe Brown (principal); proposed from measured A3 arithmetic
- **Relates to:** 0043 (Gate A3 counts new refusals, not historical ones), 0057 (append-only
  trajectory), codebase audit 2026-08-24 unit AB (torn-append refusal)
- **Inquiry tier reached:** T1 ground — one measured defect, exact digests, no controlled
  comparison
- **Executable model:** none. The condition is either satisfiable with the recorded history or
  it is not; that was settled by running `consil doctor`.

## Context

ADR-0043 amended Gate A3 so refusals already present when a capture run began are counted,
reported, and do not block the gate. It pinned three SHA-256 content digests from 2026-08-20 —
V0-18 violations appended between 09:41 and 09:56 that day, permanent because the log is
append-only.

On 22 August 2026 three more lines landed in `.harness/log/2026-08-22.jsonl` at lines 27, 35
and 45. Each is invalid JSON, quarantined by `read()` with its content digest recorded. They were
written by concurrent appends that tore the file before unit AB shipped refusal of a torn tail.
[measured — `tests/test_v0_invariants.py::PINNED_TRAJECTORY_REJECTIONS`; codebase audit
2026-08-24 unit AB]

Measured 24 August 2026: A3 is permanently unpassable under ADR-0043 alone. Pass requires
`run >= 7 AND new_refused == 0`. `run_start` walks backwards through consecutive capture days;
19–24 August are consecutive with no gap; the three 22 August refusals stay inside the window
forever while capture continues daily. The only way the current code passes is to stop capturing
for a day, which resets `run_start` past the 22nd — a capture gate you pass by breaking capture.
[measured]

## Decision

Extend the historical refusal baseline exactly as ADR-0043 did for the original three. Pin these
three content digests in `HISTORICAL_REFUSAL_DIGESTS`:

- `305cfe4853e3d9576fd186f86cac2f3900805c44a75a41b0642a27e1da5741d3` — `2026-08-22.jsonl` line 27
- `3769e62caa9131bb916fef24b40d46d70b49e19ee59a0686aa106b66eed15387` — `2026-08-22.jsonl` line 35
- `6511adf8d1b5ef4aea3f542d610d261572c6a103d630775ce785ab2395a187ec` — `2026-08-22.jsonl` line 45

A3 then measures **new** loss going forward, which is what the condition is for. Do not widen A3,
change its arithmetic, or replace the consecutive-day window with a trailing window. The condition
is right; the history under it was damaged.

**This acceptance is contingent on unit AB having shipped.** AB refuses a torn append and names
the byte offset rather than gluing a partial line. Without that fix live, baselining would turn A3
into a ratchet that absorbs every future corruption and detects nothing.

**Rule for any future baseline extension:** a loss may enter `HISTORICAL_REFUSAL_DIGESTS` only
when its cause has been fixed and that fix has shipped. Baselining a loss whose cause is still
live is refused.

## Evidence

- `[measured]` Three refusals on 2026-08-22 at lines 27, 35 and 45; digests pinned in
  `tests/test_v0_invariants.py::PINNED_TRAJECTORY_REJECTIONS`.
- `[measured]` A3 fails with `new_refused == 3` on the live trajectory while capture is
  consecutive 19–24 August; the only escape without this ADR is a capture gap.
- `[measured]` Unit AB landed torn-append refusal in `events._read_under_lock` before this ADR
  was accepted — partial lines raise `EventError` naming the byte offset.
- `[cited]` ADR-0043 — precedent for pinning exact digests and reporting historical count beside
  the verdict.

## Evidence against

- **Baselining makes a gate easier to pass, and it is proposed by the party the gate
  constrains.** Same conflict of interest ADR-0043 named. The mitigation is narrower: one new
  rejection inside the window still fails; only these six exact digests are tolerated.
- **A ratchet with a non-zero floor can normalise its floor.** ADR-0043's hazard applies at six
  lines instead of three. If the historical count never falls, tolerance becomes decoration.
- **Baselining before the cause is fixed turns detection off.** That is why this ADR must not
  land before AB. With AB live, new torn appends are refused at write time rather than quarantined
  as invalid JSON after the fact; baselining the three historical lines does not absorb future
  tears. **The rule stands: baseline only a loss whose cause has been fixed and shipped.**
- **The alternative — stop capture for a day to slide the window — was not taken.** It would pass
  A3 by breaking the thing A3 measures. This ADR records the loss honestly instead.

## Consequences

**Positive.** Gate A3 becomes satisfiable again under continuous capture. New refusals still fail
the gate; the six pinned lines are visible in every A3 reason string.

**Negative.** The tolerated refusal count rises from three to six. That is a boundary movement on
the initiative of the party the gate binds.

**Neutral but load-bearing.** Sets precedent that a second measured-unsatisfiable history under an
otherwise correct gate condition is baselined rather than worked around by stopping capture.

## Enforcement

- **Check:** `HISTORICAL_REFUSAL_DIGESTS` contains exactly the six digests from ADR-0043 and this
  ADR; `_capture_condition()` counts only rejections whose digests are not in that set as new.
- **Check:** `tests/test_doctor_a3_baseline.py` — tolerates the six-line baseline, fails on a
  seventh refusal, and ratchets `CAPTURE_REFUSAL_BASELINE` at six (may only fall).
- **Check:** `tests/test_v0_invariants.py::test_historical_refusal_digests_pin_real_log_rejections`
  — live trajectory pin stays aligned with the operational baseline.
- Fails CI: yes
- Added in the same commit as acceptance: yes

## What would overturn this

If capture runs seven consecutive days after acceptance and A3 still fails under the amended
baseline, the defect is not the one diagnosed here and this ADR should be withdrawn rather than
patched.

If a seventh refusal is baselined without naming a shipped fix for its cause, the rule in this ADR
was violated and the extension should be reverted.

## Publication candidate?

No.
