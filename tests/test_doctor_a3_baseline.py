"""AO — baseline the 22 August capture loss once torn appends are refused.

ADR-0105 extends ADR-0043: three invalid JSON lines on 2026-08-22 (lines 27, 35,
45) are permanent refusals written before unit AB shipped torn-append refusal.
They join HISTORICAL_REFUSAL_DIGESTS so A3 measures new loss only.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from consilient.cli import CAPTURE_REFUSAL_BASELINE, HISTORICAL_REFUSAL_DIGESTS
from consilient.events import read_all
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
    real = {
        (Path(rejection.path).name, rejection.line, rejection.content_digest)
        for rejection in read_all(log)[1]
    }
    assert real == PINNED_TRAJECTORY_REJECTIONS, (
        "the trajectory's exact rejection set changed; inspect the quarantine before "
        "updating an immutable incident pin"
    )
