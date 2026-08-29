"""Where the pinned prefix is cut, once the log contains refused lines.

MEASURED 26 August 2026, three separate defects in ``_copy_event_prefix``, each of which
reported divergence against a log that had not actually diverged inside the pinned
window:

* it copied the WHOLE current file whenever the accepted count was still within the
mark, so a refused line appended after the mark, with the accepted count unchanged,
landed inside the reconstructed prefix anyway; * cutting the prefix at the Nth accepted
event's own line dropped a genuine refusal that predated the mark, whenever later
commits added MORE accepted events to the same file; * with remaining==0 it cut at
``file_events[-1].line``, dropping a trailing refusal that was already inside the
projection. A quiet log of 2 events plus 1 refused line, built as (2, 1), and doctor
reported "Compared 2 events; canonical state diverged."

The rule the repairs converge on: the log is append-only, so anything before the FIRST
accepted event beyond the mark is guaranteed to predate it, refusal or not - and
anything after the mark, refusal or not, is outside the comparison and is not evidence
of divergence.

Several of these run against a quiet log on purpose, because the quiet log is where the
defect lived; two keep the unit's concurrent obligation by appending while the check
runs; and the last holds the boundary in the other direction, since including refusals
in the pin must not widen what counts as identical - a refusal rewritten inside the pin
still fails."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import projection
from doctor_a2_helpers import (
    _a2,
    _append_judged,
    _doctor,
    _seeded,
)


def test_a2_is_pass_when_a_refusal_lands_after_the_mark_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: `_copy_event_prefix` copied the WHOLE current file
    whenever the accepted count was still within the mark, even if something had been
    appended since. A refused line added after the mark, with the accepted count
    unchanged, landed inside the reconstructed prefix anyway and read as divergence
    against a log that had not actually diverged within the pinned window.
    """
    log, db, path = _seeded(tmp_path)

    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_when_a_refusal_predates_events_added_after_the_mark(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: cutting the prefix at the Nth accepted event's own line
    dropped a genuine refusal that predated the mark whenever later commits added MORE
    accepted events to the same file. The log is append-only, so anything before the
    FIRST accepted event beyond the mark is guaranteed to predate it, refusal or not.
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    _append_judged(path, "grown-after-mark", "t-grown")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_on_a_quiet_trailing_refusal_inside_the_pin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: `_copy_event_prefix` pinned on accepted-event
    count only. When remaining==0 it cut at file_events[-1].line, dropping a
    trailing refusal that was already inside the projection. Quiet log of 2
    events + 1 refused line, built as (2, 1), doctor reported
    'Compared 2 events; canonical state diverged.'
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    conn = projection.build(log, db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM rejections").fetchone()[0] == 1
    finally:
        conn.close()

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_when_a_refusal_then_events_land_after_the_mark(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: seed 2/0, then one refused line then two accepted
    events. Cutting at the first accepted event beyond the mark pulled the
    post-mark refusal into the prefix. First doctor failed 'Compared 2 events;
    canonical state diverged.' The refusal is after the mark and is not evidence
    of divergence.
    """
    log, db, path = _seeded(tmp_path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    _append_judged(path, "grown-after-mark", "t-grown")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_on_a_trailing_refusal_inside_the_pin_while_the_log_grows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trailing refusal at the pin, plus events landing during the check.

    The quiet case is the defect; this one keeps the unit's concurrent
    obligation: the log is being written while A2 decides.
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    original_build = projection.build
    appended = {"n": 0}

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, f"race-trailing-{appended['n']}", "t-race")
            appended["n"] += 1
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert appended["n"] >= 1, (
        "the check never touched the live log; the race was not run"
    )
    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_still_fails_when_a_refusal_inside_the_pin_is_rewritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Including refusals in the pin must not widen what counts as identical."""
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE rejections SET reason = 'tampered'")
    drifted.commit()
    drifted.close()

    original_build = projection.build

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, "race-refusal-drift", "t-race")
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "fail", condition["reason"]
    assert "diverged" in str(condition["reason"])
