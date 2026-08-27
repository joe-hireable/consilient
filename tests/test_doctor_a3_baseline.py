"""AO — baseline the 22 August capture loss once torn appends are refused.

ADR-0105 extends ADR-0043: three invalid JSON lines on 2026-08-22 (lines 27, 35,
45) are permanent refusals written before unit AB shipped torn-append refusal.

BOTH HALVES ARE NOW APPLIED. RESOLVED 26 August 2026.

ADR-0105 conflates two separate acts:

  * PINNING the incident — recording the exact file, line and digest of the three
    torn lines so the quarantine cannot drift silently. Applied since 24 August,
    enforced below by `test_real_trajectory_rejections_still_match_the_pin`, and
    never in dispute.
  * WIDENING the operational A3 tolerance — adding those digests to
    `cli.HISTORICAL_REFUSAL_DIGESTS`, which raises the number of refusals Gate A
    condition 3 forgives from three to six. Applied 26 August 2026.

What was checked, 24 August 2026, rather than assumed:

  * All six digests are real. Each hashes a genuine line of `.harness/log/`, verified
    with the reader's own rule (`content_digest` is taken BEFORE `line.strip()`, so it
    includes the trailing newline; hashing the stripped line matches nothing and briefly
    made these look fabricated). The 22 August three pin lines 27, 35 and 45, and those
    lines are genuinely torn.
  * The contingency holds. Unit AB, "refuse a torn append and name the offset", is in
    the tree: `events.py` now writes under a kernel-backed per-log lock, fsyncs, and
    rolls back a partial line so it is never acknowledged. Its test passes.

So the FACTS behind ADR-0105 were sound from 24 August. What could not be corroborated
until 26 August was the AUTHORISATION. An earlier version of the ADR claimed "Accepted
by Joe Brown, 24 August 2026, in the orchestration chat"; the available transcript
contained no such acceptance, and the nearest candidate, "a3. Yes I accept", followed a
menu about merge-conflict resolution rather than Gate A condition 3. That claim was
withdrawn, and the widening below was withheld pending a real principal event.

RESOLVED 26 August 2026: Joe authorised the widening directly ("Set it back to
accepted."), recorded as `decision.gate_amendment` in `.harness/log/2026-08-26.jsonl`,
actor and principal "joe-brown", via "cli" (V0-28: only a locally-recorded event is
accepted; the chat source is named in the event's own `source` field). `cli.
HISTORICAL_REFUSAL_DIGESTS` now carries all six digests, and `test_v0_invariants.py::
test_the_capture_refusal_baseline_may_only_fall` and
`test_historical_refusal_digests_pin_real_log_rejections` are updated to permit and
verify six rather than three, citing ADR-0105.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from consilient.cli import CAPTURE_REFUSAL_BASELINE, HISTORICAL_REFUSAL_DIGESTS
from consilient.events import EventError, read_all
from tests.test_v0_invariants import (
    HISTORICAL_REFUSAL_LINES,
    PINNED_TRAJECTORY_REJECTIONS,
    _a3,
    write_capture_days,
)

AUGUST_20_DIGESTS: frozenset[str] = frozenset(
    {
        "0fb234324063389745b5e79be163b8b6e3988a955d2a2fbd19f4036e225a7b90",
        "6921e71b2c687dd2f1f816410d20f53e106db1126bbf39fceeec02e33204f260",
        "65df9c30eeaf7095072eaada45ce276cbaca877b9540c48c519bcfdc729eb300",
    }
)

AUGUST_22_DIGESTS: frozenset[str] = frozenset(
    {
        "305cfe4853e3d9576fd186f86cac2f3900805c44a75a41b0642a27e1da5741d3",
        "3769e62caa9131bb916fef24b40d46d70b49e19ee59a0686aa106b66eed15387",
        "6511adf8d1b5ef4aea3f542d610d261572c6a103d630775ce785ab2395a187ec",
    }
)

BASELINE_DIGESTS = AUGUST_20_DIGESTS | AUGUST_22_DIGESTS


def test_historical_refusal_digests_cover_both_baselines():
    """ADR-0043 pins three refusals from 2026-08-20; ADR-0105 adds three from 2026-08-22."""
    assert HISTORICAL_REFUSAL_DIGESTS == BASELINE_DIGESTS
    assert CAPTURE_REFUSAL_BASELINE == len(HISTORICAL_REFUSAL_DIGESTS) == 6
    for line in HISTORICAL_REFUSAL_LINES:
        digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
        assert digest in HISTORICAL_REFUSAL_DIGESTS


def test_pinned_trajectory_rejections_match_operational_baseline():
    """Every pinned rejection digest must be in the operational tolerance, and no others."""
    pinned_digests = {digest for _file, _line, digest in PINNED_TRAJECTORY_REJECTIONS}
    assert pinned_digests == HISTORICAL_REFUSAL_DIGESTS


def test_a3_still_passes_when_only_august_20_baseline_refusals_are_present(tmp_path, capsys):
    """Extending the baseline to six digests must not break tolerance of the original three."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        for line in HISTORICAL_REFUSAL_LINES:
            fh.write(line)

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]
    assert "historical baseline" in condition["reason"]
    assert "0 are new" in condition["reason"]


def test_a3_still_fails_on_one_refusal_above_the_six_line_baseline(tmp_path, capsys):
    """The amendment is not a removal. One refusal above the six-line baseline still fails."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(17, 24)]
    write_capture_days(log, *days)
    with (log / "2026-08-22.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("{not json}\n")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "1 are new" in condition["reason"]


def test_the_capture_refusal_baseline_may_only_fall_from_six():
    """ADR-0105 raised the floor once; the ratchet still forbids quiet widening."""
    assert CAPTURE_REFUSAL_BASELINE <= 6, (
        "the A3 refusal tolerance was raised without ADR-0105; "
        "ADR-0043 and ADR-0105 permit the count to fall only"
    )


def test_real_trajectory_rejections_still_match_the_pin():
    """Repository-only: the live quarantine set must not drift silently."""
    log = Path(".harness/log")
    if not log.exists():  # pragma: no cover - repository-only check
        pytest.skip("no repository trajectory in this checkout")
    if not (log / "2026-08-20.jsonl").exists():
        pytest.skip("historical repository trajectory is not present in this checkout")
    # An access denial is INFRASTRUCTURE, not evidence about drift. This reads the LIVE
    # trajectory while up to 36 dispatchers append to it, and on Windows a writer denies every
    # reader while it holds the file. Failing here is a false alarm, and an expensive one: a red
    # suite blocks retirement, merging and publication together. Skips ONLY on a denial -- a log
    # that reads cleanly and HAS drifted still fails, which is the whole point of the pin.
    try:
        rejections = read_all(log)[1]
    except EventError as exc:
        if "observed access denial" not in str(exc):
            raise
        pytest.skip(f"the live trajectory was held by another process: {exc}")
    real = {
        (Path(rejection.path).name, rejection.line, rejection.content_digest)
        for rejection in rejections
    }
    assert real == PINNED_TRAJECTORY_REJECTIONS, (
        "the trajectory's exact rejection set changed; inspect the quarantine before "
        "updating an immutable incident pin"
    )
