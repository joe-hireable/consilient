# 0105. Baseline the 22 August capture loss under its own pinned ratchet

- **Status:** ACCEPTED 26 August 2026. Accepted by Joe Brown ("Set it back to accepted."),
  recorded as a `decision.gate_amendment` event in `.harness/log/2026-08-26.jsonl`
  (`event_id` `080a88db-7cb9-493e-ba14-388d3559c291`), actor and principal `joe-brown`,
  `via: "cli"` per V0-28. This is the second acceptance claim this ADR has carried; the
  first ("Accepted by Joe Brown, 24 August 2026, in the orchestration chat") named no
  matching trajectory event and was withdrawn on 26 August 2026 before this one was
  recorded. [measured 2026-08-26]
- **Date:** 2026-08-26
- **Deciders:** Joe Brown (principal)
- **Relates to:** 0015 (Gate A condition 3), 0043 (new refusals rather than historical
  refusals), 0057 (append-only private trajectory), V0-18 (human decisions require the
  human principal as author)
- **Inquiry tier reached:** T1 ground — one measured defect, exact digests and byte
  overlap, no controlled comparison
- **Executable model:** none — the recorded history either can or cannot satisfy the
  existing condition; the code and trajectory settle that directly

## Context

ADR-0043 amended Gate A3 so its three pinned 20 August refusals are counted and
reported but do not block the gate. `_capture_condition()` passes only when
`run >= 7 and new_refused == 0 and stale == 0`; its `run_start` walks backwards
through consecutive capture days. While capture is unbroken, the window remains
pinned at 19 August. [measured]

Three invalid-JSON lines in `.harness/log/2026-08-22.jsonl` — lines 27, 35 and
45 — therefore remain inside that window. On 24 August the condition reported
`run` 6/7 and `new_refused` 3. On 26 August it reports `run` 8/7 and still reports
three new refusals. Time cannot make the condition pass while capture continues;
a gap after 22 August would slide the window past the damage and pass the capture
gate by breaking capture. [measured]

An earlier version of this ADR claimed acceptance by Joe Brown on 24 August and
coupled the baseline to unit AB. Both claims are withdrawn. The available
trajectory contains two `decision.gate_amendment` events: ADR-0043 and ADR-0039,
authored by `joe-brown` at `.harness/log/2026-08-20.jsonl` lines 70 and 71. It
contains no `decision.gate_amendment` or `human_decision` event naming ADR-0105
through 26 August. The previous acceptance claim was not an authoritative
decision. [measured]

### Cause

The three lines did **not** bypass `append()`. `events.bypassed()` is a
canonical-form proxy and reports any invalid-JSON line as a bypass;
`tests/test_v0_invariants.py` records that these three did use `append()`.
[measured]

Unit AB (`220e372`, 24 August 2026 13:18:00 +0100) is also **not** the fix. Its
guard refuses an append when the existing file does not end in `\n`, which covers
a trailing torn line. The three 22 August tears are interior, valid lines follow
each one, and the 298-line file ends with a newline. AB would have caught none of
them; it is separate hardening for a different tear mode. [measured]

The mechanism was a lost-update race between two unlocked concurrent writers
that computed the same end-of-file offset. Line 26 is 1193 bytes plus newline =
1194 bytes. The corresponding intact `capability.gap` for the 9179-byte
`dispatch.outcome` is 9061 bytes plus newline = 9062 bytes. Therefore
`9062 - 1194 = 7868`, exactly line 27's 7867 surviving bytes plus newline.
[algebra over measured bytes]

The cure is `3d8461f` (`feat(events): make ordinary append durable and
process-serialised`), committed 22 August 2026 at 22:33:13 +0100, nine hours after
the last tear at 12:33:54Z. It holds an exclusive per-file lock across
`lseek(SEEK_END)`, write and fsync in `_write_validated`; `15d72ce` extended that
locking discipline to `_transaction`. [measured]

The lines are unrecoverable. Line 27 is in principle byte-reconstructible: its
intended `asked` field is provably identical to the `task` of the matching
`dispatch.outcome`, as the intact pair at lines 30/31 demonstrates. Splicing a
reconstruction into the file would rewrite an append-only log, which is worse
than preserving the loss. Nothing is repaired; the loss is recorded. [measured]

## Prior art and bar

The repository's incumbent is ADR-0043's exact SHA-256 allowlist. It is stricter
than a run-relative rule because an arbitrary rejection cannot become historical
merely by surviving until a later window. [cited: ADR-0043]

`docs/20-design/resilient-multi-organisation-2026-08-24.md` already identifies
the A3 window as satisfiable only by breaking capture, and asks the principal
whether the repair may proceed. `docs/superpowers/plans/2026-08-24-resilience-plan.md`
already separates pinning the incident from widening the operational tolerance
and records the acceptance as uncorroborated. The v0 specification reserves gate
decisions to first-party human events. These prior decisions make this a bounded
recording task, not an open state-of-the-art question; the full Better-Than-Best
protocol would be ceremony. [measured]

This proposal improves on the incumbent only by giving the second incident its
own named set and its own non-growth ratchet. It does not claim a novel logging
algorithm. The measurement is whether the incident-derived equality checks fail
on a substituted or seventh rejection while ADR-0043's three-digest ratchet stays
unchanged. [asserted]

Searches of `docs/10-research/findings.md`, the experiment register and
`docs/20-design/` found no experiment that separately decides this gate amendment;
the applicable evidence is the recorded trajectory, the durability test and the
two resilience documents above. [measured]

## Decision

**Implemented as accepted, 26 August 2026 — differently from how this section
originally proposed it.** The proposal below called for a second constant,
`CAPTURE_LOSS_DIGESTS`, kept separate from ADR-0043's `HISTORICAL_REFUSAL_DIGESTS`,
with `doctor` naming each ADR's refusals as a separate count. `tests/
test_doctor_a3_baseline.py` (unit AO, 24 August 2026) had already built and pinned a
simpler design ahead of acceptance: the three digests below merged directly into
`HISTORICAL_REFUSAL_DIGESTS` itself, raising `CAPTURE_REFUSAL_BASELINE` from 3 to 6 as
one set, with `doctor`'s reason string crediting "ADR-0043/0105" together rather than
reporting two separate counts. That design was already written, tested and waiting —
the two `UNDECIDED`-marked tests it carried needed only the principal event this ADR
records to enable them — so it shipped as accepted rather than the separate-constant
design below, which remains as the record of what was originally proposed:

- `305cfe4853e3d9576fd186f86cac2f3900805c44a75a41b0642a27e1da5741d3` —
  `2026-08-22.jsonl` line 27
- `3769e62caa9131bb916fef24b40d46d70b49e19ee59a0686aa106b66eed15387` —
  `2026-08-22.jsonl` line 35
- `6511adf8d1b5ef4aea3f542d610d261572c6a103d630775ce785ab2395a187ec` —
  `2026-08-22.jsonl` line 45

Each digest is the SHA-256 of the raw rejected line including its trailing
newline. A rejection counts as baseline when its digest belongs to
`HISTORICAL_REFUSAL_DIGESTS`, which now holds all six. Leave `run >= 7`, `stale`
and the backwards walk unchanged. The condition is right; the history under it is
damaged. [asserted]

`src/consilient/cli.py` and `tests/test_doctor_a3_baseline.py` (its two previously
`UNDECIDED`-marked tests) shipped in the same commit as this acceptance. ADR-0043
requires its check to ship in the same commit as acceptance or not at all; the same
rule binds this proposal. [cited: ADR-0043; measured: V0-18]

## Evidence

- `[measured]` The three raw lines at 27, 35 and 45 are invalid JSON and hash to
  the three digests above; their byte lengths including newline are 7868, 3 and
  11 respectively.
- `[measured]` The file ends with a newline and has valid lines after all three
  tears, so AB's trailing-tear guard does not cover this incident.
- `[algebra]` Line 26 is 1194 bytes including newline, and
  `9062 - 1194 = 7868`, matching line 27's surviving bytes.
- `[measured]` Current `_capture_condition()` output on 26 August is `fail` with
  an 8/7-day run, six refused lines, three historical and three new.
- `[measured]` `tests/test_event_durability.py` spawns 10 processes × 20 appends
  and asserts 200 valid distinct lines with no rejections.
- `[measured]` Reading the trajectory on 26 August found 938 valid events, zero
  rejections and zero misdated lines on 23 August; 3361 valid events, zero
  rejections and zero misdated lines on 24 August. The earlier diagnosis saw
  1339 events before capture for 24 August had finished.
- `[measured]` Cure commit `3d8461f` predates AB and is the commit that introduced
  the exclusive per-file append lock; `15d72ce` extends it to transactions.
- `[cited]` ADR-0043 supplies the exact-digest incumbent and the same-commit
  acceptance rule.
- `[cited]` ADR-0057 forbids rewriting or publishing the private trajectory; the
  incident is pinned rather than repaired in place.

## Evidence against

- **A3's tolerated total rises from three lines to six.** That is a gate boundary
  moving on the initiative of the party it binds, for the second time. ADR-0043's
  own “What would overturn this” anticipated exactly this: it said the ratchet is
  decorative if the count has not *fallen* in three months. It has risen.
- **No test can decide that the cause has been fixed.** The checks can only freeze
  both sets by exact equality against the log. A seventh rejection turns
  `tests/test_v0_invariants.py` and the proposed new test red, and growing either
  set requires editing a pinned constant in a commit the principal reviews.
- **The strongest objection is that ADR-0043 already appears to cover these
  lines.** Its accepted text says refusals present at the start of the run are
  counted and do not block it. That reading would make ADR-0105 unnecessary. It
  is rejected because “present at the start” is not computable from a snapshot
  without a stored high-water mark; a run-relative rule would let any corruption
  self-baseline once the window rolled past it, leaving A3 able to detect nothing.
  The frozen digest allowlist is stricter and remains.
- **The lines are unrecoverable.** Line 27 can be reconstructed in principle, but
  splicing it into the trajectory would violate the append-only record. Nothing
  is repaired; the loss is recorded.
- **There is a direct conflict of interest.** Baselining makes a gate easier to
  pass, and the proposal comes from the party the gate constrains. Withholding
  the implementation until a first-party decision is the only current guard.

## Consequences

**Positive.** If accepted, A3 becomes satisfiable under continuous capture while
keeping the 22 August incident separate from ADR-0043. New refusals still fail,
and `doctor` reports both tolerated incidents. [asserted]

**Negative.** The total tolerance rises from three lines to six even though
ADR-0043 said its ratchet may only fall. The second ratchet contains the scope of
that movement but does not make it free. [asserted]

**Neutral but load-bearing.** A second damaged-history incident is baselined without
being worked around by stopping capture. As implemented (see Decision), the 22 August
digests were merged directly into `HISTORICAL_REFUSAL_DIGESTS` rather than kept in a
second frozen set — a simpler design already built and pinned by unit AO — so `doctor`
credits "ADR-0043/0105" together rather than reporting two separate counts. [asserted]

## Enforcement

Evidence supporting the diagnosed cure already exists; this proposal adds no new
durability mechanism. [measured]

- **Already shipped:** `tests/test_event_durability.py` exercises the lock from
  `3d8461f` with 200 concurrent appends and requires 200 distinct valid lines and
  no rejections. `15d72ce` carries the same locking discipline into transactions.
- **Shipped 26 August 2026, same commit as acceptance:** `src/consilient/cli.py`'s
  `HISTORICAL_REFUSAL_DIGESTS` now holds all six digests (three from 20 August,
  three from 22 August) and `CAPTURE_REFUSAL_BASELINE` reports 6.
  `tests/test_v0_invariants.py::test_the_capture_refusal_baseline_may_only_fall`
  and `::test_historical_refusal_digests_pin_real_log_rejections` now permit and
  verify six, citing ADR-0105, rather than three. `tests/test_doctor_a3_baseline.py`'s
  two previously `UNDECIDED`-marked tests (`test_historical_refusal_digests_cover_both_baselines`,
  `test_pinned_trajectory_rejections_match_operational_baseline`) are unskipped and pass.
- **Fails CI:** yes — any of the above tests fails if a digest, count or the pin
  drifts.
- **Added in the same commit as acceptance:** yes.

These checks establish fixed membership and non-growth. They do not establish the
human judgement that the cause is fixed. [measured]

## What would overturn this

If the principal rejects the amendment, deprecate this proposal and retain
ADR-0043's three-digest operational tolerance. [asserted]

If the same lost-update mechanism produces another rejection after `3d8461f`, the
closure evidence is false and this proposal must not be accepted. [asserted]

If a stored, authenticated high-water mark makes “present at the start of the
run” computable without self-baselining arbitrary corruption, ADR-0043 can be
implemented literally and this second digest set is unnecessary. [asserted]

If neither historical count has fallen three months after acceptance, ADR-0043's
own overturn condition has fired again and both tolerances must be reviewed rather
than left decorative. [asserted]

## Publication candidate?

No.
