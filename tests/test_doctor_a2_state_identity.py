"""What A2 compares, and when it declines to compare at all.

Distinct from the read window: none of these checks races the log. They pin the identity
of the projected state itself. The same refused line must have the same projected state
wherever its log lives, so a rejection's path is recorded relative to the log directory
- and normalising the directory away must not drop the filename from the digest, or a
file moved between names would silently read as no change. Both directions are asserted,
because the useful property is the pair: identical across locations, different across
filenames.

The projection-version pair belongs with them for the same reason. Compatibility is
decided by the SQLite header version, not by the ``projection_meta`` row, and a mismatch
is UNKNOWN with the exact reason "Projection version 1 rebuilt as 2; not compared." The
second of the pair pins the *absence* of work: on a version mismatch the pinned-prefix
rebuild must not run at all, because a prefix digest written by another projection
version is not evidence about this one."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import projection
from consilient import cli_replay
from doctor_a2_helpers import (
    _a2,
    _append_judged,
    _doctor,
    _seeded,
)


def test_a2_canonicalises_rejection_paths_across_log_locations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same refused line has the same projected state wherever its log lives."""
    first_log = tmp_path / "first" / "log"
    second_log = tmp_path / "second" / "log"
    name = f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    first_path = first_log / name
    second_path = second_log / name
    first_path.parent.mkdir(parents=True)
    first_path.write_text("{not valid JSON}\n", encoding="utf-8")
    _append_judged(first_path, "rejected-path", "t-rejected-path")
    second_path.parent.mkdir(parents=True)
    second_path.write_text(first_path.read_text(encoding="utf-8"), encoding="utf-8")

    first_db = tmp_path / "first.db"
    second_db = tmp_path / "second.db"
    first = projection.build(first_log, first_db)
    second = projection.build(second_log, second_db)
    try:
        first_rejections = projection.rejections(first)
        assert first_rejections == projection.rejections(second)
        assert first_rejections[0]["path"] == name
        assert first_rejections[0]["line"] == 1
        assert str(first_rejections[0]["reason"]).startswith("not valid JSON:")
        assert projection.state_digest(first) == projection.state_digest(second)
    finally:
        first.close()
        second.close()

    first_a2 = _a2(_doctor(first_log, first_db, capsys))
    second_a2 = _a2(_doctor(second_log, second_db, capsys))
    assert first_a2["status"] == "pass", first_a2["reason"]
    assert second_a2["status"] == "pass", second_a2["reason"]
    for condition in (first_a2, second_a2):
        reason = str(condition["reason"])
        assert "identical" in reason
        assert "diverged" not in reason
        assert "Compared" in reason


def test_a2_is_unknown_when_pragma_projection_version_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The SQLite header version, not projection_meta, decides compatibility."""
    old, new = 1, 2
    assert projection.PROJECTION_VERSION == new
    log, db, _path = _seeded(tmp_path)
    existing = sqlite3.connect(db)
    existing.execute(f"PRAGMA user_version = {old}")
    existing.execute(
        "UPDATE projection_meta SET value = ? WHERE key = ?", ("999", "version")
    )
    existing.commit()
    existing.close()

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "unknown", condition["reason"]
    assert condition["reason"] == "Projection version 1 rebuilt as 2; not compared."


def test_a2_does_not_prefix_digest_when_projection_version_differs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A version mismatch is unknown without comparing a prefix written by another projection."""

    log, db, _path = _seeded(tmp_path)
    existing = sqlite3.connect(db)
    existing.execute("PRAGMA user_version = 1")
    existing.commit()
    existing.close()

    def forbidden(*_args: object, **_kwargs: object) -> str:
        raise AssertionError(
            "pinned-prefix rebuild must not run on a projection-version mismatch"
        )

    monkeypatch.setattr(cli_replay, "_digest_of_pinned_prefix", forbidden)
    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "unknown", condition["reason"]
    assert condition["reason"] == "Projection version 1 rebuilt as 2; not compared."


def test_a2_rejection_filename_still_changes_the_digest(tmp_path: Path) -> None:
    """Normalising the path must not drop it from the digest: a moved file still changes state."""
    first_log = tmp_path / "first" / "log"
    second_log = tmp_path / "second" / "log"
    first_log.mkdir(parents=True)
    second_log.mkdir(parents=True)
    (first_log / "one.jsonl").write_text("{not valid JSON}\n", encoding="utf-8")
    (second_log / "two.jsonl").write_text("{not valid JSON}\n", encoding="utf-8")
    first = projection.build(first_log, tmp_path / "first.db")
    second = projection.build(second_log, tmp_path / "second.db")
    try:
        assert first.execute("SELECT path FROM rejections").fetchone()[0] == "one.jsonl"
        assert (
            second.execute("SELECT path FROM rejections").fetchone()[0] == "two.jsonl"
        )
        assert projection.state_digest(first) != projection.state_digest(second)
    finally:
        first.close()
        second.close()
