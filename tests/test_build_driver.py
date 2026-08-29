"""What a death costs a unit — restart intensity, quarantine, and the counting of
crashes.

A seventh restart inside ten minutes is terminal, old timestamps may age out without
refunding history, and the transition must be announced exactly once rather than once
per tick — whether it is reached by reclamation, by a crash, or by a review that
completed malformed in the same tick that would have re-dispatched it. Quarantine
survives ordinary reclamation and is cleared only by a landed check, and a quarantined
unit must never reach the dispatch caller at all.

The crash cases carry the measurement. `crashed_dispatches` reads `<stem>.err` from disk
and that file persists until the next dispatch for the same unit overwrites it, so every
tick re-read the same stale traceback and reported it as a fresh death: driver state
recorded 4,531 "crashes" across 99 units, AL at 102 and AJ at 95 — tick counts, not
failures [measured, 25 August 2026]. That was not merely noise. The three-identical-
deaths rule stops auto-repair and escalates, so one historical crash re-read three times
permanently escalated a unit and removed it from the retry pool. One event wearing many
hats is the false-accept shape this repository exists to detect, and here it was
occurring in the repository's own supervisor. Deduplication must not blind the
supervisor to a genuinely new failure, and the counted set must not grow without bound."""

import json
from pathlib import Path
import pytest
from build_driver_helpers import (
    DRIVER,
    _load_driver,
)


def test_restart_window_quarantines_once_without_refunding_history() -> None:
    """A seventh restart in ten minutes is terminal, while old timestamps may age out."""
    driver = _load_driver()
    state: dict[str, object] = {}

    for now in range(100, 107):
        driver.record_restart(state, "U01", now=float(now))

    assert state["total_restarts"] == {
        "U01": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]
    }
    assert state["quarantined"] == ["U01"]
    assert state["quarantine_escalated"] == ["U01"]

    driver.record_restart(state, "U01", now=1000.0)
    assert state["total_restarts"] == {"U01": [1000.0]}
    assert state["quarantine_escalated"] == ["U01"]


def test_live_dispatchers_ignores_unrelated_processes(monkeypatch) -> None:
    """Only work recorded by this driver contributes to its liveness count."""
    driver = _load_driver()

    def unexpected_process_scan(_args):
        raise AssertionError("driver inspected machine-wide process state")

    monkeypatch.setattr(driver, "sh", unexpected_process_scan)
    assert driver.live_dispatchers({"in_flight": {"U01": (1.0, 60.0)}}) == 1


def test_reclamation_does_not_clear_quarantine_but_landed_check_does(
    monkeypatch,
) -> None:
    """Quarantine survives ordinary reclamation and is cleared only after a landed check."""
    driver = _load_driver()
    state: dict[str, object] = {
        "in_flight": {"U01": (0.0, 1.0)},
        "quarantined": ["U01"],
    }
    monkeypatch.setattr(driver, "run_dir_progress", lambda _uid, _started: 0.0)
    monkeypatch.setattr(driver, "BRIEFS", Path("missing-briefs"))

    driver.reclaim_expired_slots(state)

    assert state["quarantined"] == ["U01"]
    driver.clear_quarantine_after_landed_check(state, "U01")
    assert state["quarantined"] == []


def test_main_escalates_when_reclamation_crosses_restart_limit(
    monkeypatch, capsys
) -> None:
    """The caller must announce the quarantine transition caused by reclaimed work."""
    driver = _load_driver()
    now = driver.time.time()
    state: dict[str, object] = {
        "in_flight": {"U01": (0.0, 1.0)},
        "attempts": {"U01": 3},
        "total_restarts": {"U01": [now - offset for offset in range(6)]},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: {} if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "run_dir_progress", lambda _uid, _started: 0.0)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)

    assert driver.main() == 0

    assert (
        "ESCALATION -- U01 exceeded the restart intensity limit"
        in capsys.readouterr().out
    )
    assert state["attempts"] == {"U01": 2}
    assert state["quarantined"] == ["U01"]


def test_main_refunds_crash_that_crosses_restart_limit_once(
    monkeypatch, capsys
) -> None:
    """Restart quarantine reports once without changing the independent attempt budget."""
    driver = _load_driver()
    now = driver.time.time()
    state: dict[str, object] = {
        "in_flight": {"U01": (now, 3600.0)},
        "attempts": {"U01": 3},
        "crash_history": {"U01": ["first", "second"]},
        "total_restarts": {"U01": [now - offset for offset in range(6)]},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: {} if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "run_dir_progress", lambda _uid, _started: 0.0)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U01", "third", False)]
    )
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "save_state", lambda _state: None)

    assert driver.main() == 0

    output = capsys.readouterr().out
    assert output.count("ESCALATION -- U01 exceeded the restart intensity limit") == 1
    assert state["attempts"] == {"U01": 2}
    assert state["quarantined"] == ["U01"]


def test_main_does_not_refund_identical_crash_at_restart_limit(
    monkeypatch, capsys
) -> None:
    """An identical third death stays terminal even when it also crosses restart intensity."""
    driver = _load_driver()
    now = driver.time.time()
    state: dict[str, object] = {
        "in_flight": {"U01": (now, 3600.0)},
        "attempts": {"U01": 3},
        "crash_history": {"U01": ["same", "same"]},
        "total_restarts": {"U01": [now - offset for offset in range(6)]},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: {} if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "run_dir_progress", lambda _uid, _started: 0.0)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U01", "same", False)]
    )
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "save_state", lambda _state: None)

    assert driver.main() == 0

    output = capsys.readouterr().out
    assert output.count("ESCALATION -- U01 exceeded the restart intensity limit") == 1
    assert state["attempts"] == {"U01": 3}
    assert state["quarantined"] == ["U01"]


def test_main_does_not_dispatch_a_quarantined_unit(monkeypatch) -> None:
    """Quarantine prevents a unit from reaching the build dispatch caller."""
    driver = _load_driver()
    units = {"U01": {"title": "held", "claims": []}}
    state: dict[str, object] = {
        "in_flight": {},
        "attempts": {},
        "quarantined": ["U01"],
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(
        driver.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("quarantined unit was dispatched"),
    )

    assert driver.main() == 0


def test_main_quarantines_malformed_review_before_same_tick_redispatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A completed malformed review counts before its check-error retry can be dispatched."""
    driver = _load_driver()
    now = driver.time.time()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    (briefs / "U01-verify.out").write_text("{}", encoding="utf-8")
    units = {"U01": {"title": "held", "claims": []}}
    state: dict[str, object] = {
        "in_flight": {},
        "attempts": {},
        "built": ["U01"],
        "review_dispatched": ["U01"],
        "review_expected": {"U01": {"artefact": "digest", "attempt": 1}},
        "total_restarts": {"U01": [now - offset for offset in range(6)]},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _outcome: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(
        driver.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("quarantined review was redispatched"),
    )

    assert driver.main() == 0

    output = capsys.readouterr().out
    assert output.count("ESCALATION -- U01 exceeded the restart intensity limit") == 1
    assert len(state["total_restarts"]["U01"]) == 7
    assert state["review_results"]["U01"]["outcome"] == "dispatch_failed"
    assert state["quarantined"] == ["U01"]


def test_defective_review_records_restart_before_rejection(
    tmp_path: Path, monkeypatch
) -> None:
    """A valid DEFECTIVE receipt is a counted failed review, not an attempt refund."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    receipt = {
        "v": 1,
        "unit": "U01",
        "artefact": "digest",
        "attempt": 1,
        "verdict": "DEFECTIVE",
        "findings": ["fault"],
    }
    (briefs / "U01-verify.out").write_text(
        json.dumps({"status": "ok", "stdout_tail": "reviewer finished"}),
        encoding="utf-8",
    )
    (briefs / "U01-verdict.json").write_text(json.dumps(receipt), encoding="utf-8")
    state: dict[str, object] = {
        "built": ["U01"],
        "review_dispatched": ["U01"],
        "review_expected": {"U01": {"artefact": "digest", "attempt": 1}},
    }
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _outcome: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "digest")

    assert driver.consume_review_verdict(state, "U01", {}) == "DEFECTIVE"

    assert len(state["total_restarts"]["U01"]) == 1
    assert state["built"] == []
    assert state["rejected_artefacts"] == {"U01": "digest"}


# --- a crash is evidence once, not once per tick, 25 August 2026 ---------------
#
# crashed_dispatches reads `<stem>.err` from disk, and that file persists until the next
# dispatch for the same unit overwrites it. Every tick re-read the same stale traceback and
# reported it as a fresh death: driver state recorded 4,531 "crashes" across 99 units, AL at
# 102 and AJ at 95 -- tick counts, not failures.
#
# It is not just noise. The three-identical-deaths rule stops auto-repair and escalates, so one
# historical crash re-read three times permanently escalated a unit and removed it from the
# retry pool. That is one event wearing many hats, which is the false-accept shape this
# repository exists to detect, occurring in its own supervisor.


def _write_err(briefs, stem: str, text: str):
    briefs.mkdir(parents=True, exist_ok=True)
    (briefs / f"{stem}.err").write_text(text, encoding="utf-8")


def test_an_unchanged_crash_file_is_counted_once(tmp_path, monkeypatch) -> None:
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    _write_err(briefs, "U1", "Traceback (most recent call last):\nRuntimeError: boom\n")

    state = {"in_flight": {"U1": (0.0, 3600.0)}, "review_dispatched": []}

    first = driver.crashed_dispatches(state)
    assert [row[0] for row in first] == ["U1"], first

    # Same file, three more ticks. Under the old behaviour this reported three more deaths and
    # tripped the escalation that stops auto-repair.
    for _ in range(3):
        assert driver.crashed_dispatches(state) == []


def test_a_new_crash_is_counted_again(tmp_path, monkeypatch) -> None:
    """Deduplication must not blind the supervisor to a genuinely new failure."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    state = {"in_flight": {"U2": (0.0, 3600.0)}, "review_dispatched": []}

    _write_err(
        briefs, "U2", "Traceback (most recent call last):\nRuntimeError: first\n"
    )
    assert [row[0] for row in driver.crashed_dispatches(state)] == ["U2"]
    assert driver.crashed_dispatches(state) == []

    # A later dispatch overwrites the file with a different failure: that IS new evidence.
    _write_err(
        briefs,
        "U2",
        "Traceback (most recent call last):\nValueError: second and different\n",
    )
    again = driver.crashed_dispatches(state)
    assert [row[0] for row in again] == ["U2"], "a new crash must still be reported"


def test_the_counted_set_does_not_grow_without_bound(tmp_path, monkeypatch) -> None:
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    _write_err(briefs, "U3", "Traceback\nRuntimeError: x\n")

    state = {"in_flight": {"U3": (0.0, 3600.0)}, "review_dispatched": []}
    driver.crashed_dispatches(state)
    assert "U3" in state["crash_counted"]

    # U3 is no longer watched; its marker must be dropped rather than accumulating for ever.
    state["in_flight"] = {}
    driver.crashed_dispatches(state)
    assert "U3" not in state["crash_counted"]


def test_quarantine_still_blocks_dispatching_new_work(monkeypatch) -> None:
    """The half of quarantine that must stay: a unit dying the same way three times does not
    get handed more dispatches. Only the verdict path reopens."""
    source = DRIVER.read_text(encoding="utf-8")
    assert source.count('state.setdefault("quarantined", [])') >= 3, (
        "quarantine must still gate build selection and conflict resolution; only review "
        "was meant to reopen"
    )
