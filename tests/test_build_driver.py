"""Regression checks for the local build driver."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import types
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import pytest


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("build_driver_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_stop_marker_blocks_publication_before_git_is_called(
    tmp_path: Path, monkeypatch
) -> None:
    driver = _load_driver()
    stop = tmp_path / "STOP-PUBLISH"
    stop.write_text("hold", encoding="utf-8")
    monkeypatch.setattr(driver, "PUBLISH_STOP", stop)

    def unexpected_git(_args):
        raise AssertionError("publication guard called git")

    monkeypatch.setattr(driver, "sh", unexpected_git)
    assert driver.publish_if_ready({}, True) == "publish held: STOP-PUBLISH is present"


# --------------------------------------------------------- suite_green, 25 August 2026
#
# `suite_green` decides whether anything may retire, merge or publish, and it judged the
# summary line with substring tests: `"passed" in last and "failed" not in last`. pytest's
# summary for a GREEN run of this repository reads
#
#     1761 passed, 3 skipped, 1 xfailed in 250.69s
#
# and "xfailed" contains "failed". So a suite with a single expected failure was reported red
# for ever, and the publication gate printed "publish held: 123 commit(s) ready, suite not
# green" tick after tick while public sat 123 commits behind. An xfail is a PASSING outcome.
#
# These cases are the real summary lines this repository produced on 24 and 25 August.
SUMMARY_CASES = [
    ("1761 passed, 3 skipped, 1 xfailed in 250.69s (0:04:10)", True),
    ("1739 passed, 3 skipped, 1 xfailed in 233.70s", True),
    ("1761 passed in 210.41s", True),
    ("5 xfailed, 10 passed in 1.0s", True),
    ("3 failed, 1758 passed, 3 skipped, 1 xfailed in 210.41s", False),
    ("18 failed, 1721 passed, 3 skipped, 1 xfailed in 179.74s", False),
    ("1 failed, 1760 passed in 201.34s", False),
    ("2 errors in 3.10s", False),
    ("1 error, 5 passed in 1.2s", False),
    ("no tests ran in 0.01s", False),
]


@pytest.mark.parametrize("summary, expected_green", SUMMARY_CASES)
def test_suite_green_counts_outcomes_rather_than_sniffing_substrings(
    summary: str, expected_green: bool, monkeypatch
) -> None:
    driver = _load_driver()

    class _Result:
        stdout = summary
        stderr = ""

    monkeypatch.setattr(driver, "sh", lambda _args, **_kw: _Result())
    assert driver.suite_green() is expected_green, summary


def test_an_xfail_alone_does_not_make_the_suite_red() -> None:
    r"""The specific regression: `\b\d+ failed` must not match inside "xfailed"."""
    green = "1761 passed, 3 skipped, 1 xfailed in 250.69s"
    assert re.search(r"\b\d+ (failed|error|errors)\b", green) is None
    assert re.search(r"\b\d+ passed\b", green) is not None
    # And the implementation this replaced got it wrong, which is why the check exists.
    assert not ("passed" in green and "failed" not in green)


def test_suite_green_fails_closed_when_pytest_printed_no_summary(monkeypatch) -> None:
    """An absent summary means the run did not complete. That is not the same as passing."""
    driver = _load_driver()

    class _Result:
        stdout = "ERROR: usage: pytest [options]\nunrecognised argument: --timeout=600"
        stderr = ""

    monkeypatch.setattr(driver, "sh", lambda _args, **_kw: _Result())
    assert driver.suite_green() is False


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


def test_review_cap_refuses_a_fourth_dispatch_and_escalates_once() -> None:
    """A review that has used its three permitted attempts may not launch again."""
    driver = _load_driver()
    state: dict[str, object] = {"review_attempts": {"U01": 3}}

    assert driver.review_dispatch_allowed(state, "U01") is False
    assert driver.review_dispatch_allowed(state, "U01") is False
    assert state["review_attempts"] == {"U01": 3}
    assert state["review_escalated"] == ["U01"]


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


# --- the loop must actually CALL its self-repair, 25 August 2026 ---------------
#
# `self_heal` was written on 24 August, documented at length, and NEVER CALLED. A WSL agent had
# written `core.worktree = /mnt/c/...` into the shared .git/config at 22:57 on the 24th and it
# was still there thirteen hours later, because the repair that exists for exactly that line
# had no call site.
#
# The cost was not cosmetic. `git worktree add` fails while that line is present, so every
# dispatch fell through to the isolated_git_env workspace form, which clones with
# --separate-git-dir; agent commits then landed in a different object store, invisible to the
# driver. Eleven commits of finished work were stranded and one unit was built twice.
#
# A defined-but-uncalled repair is indistinguishable from no repair, and nothing in the suite
# could tell the difference. This is that check.


def test_the_loop_calls_self_heal_every_tick() -> None:
    source = (ROOT / ".harness" / "build_loop.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    defined = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "self_heal" in defined, (
        "self_heal is gone; this test guards its call, not its name"
    )

    main = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    called = {
        node.func.id
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "self_heal" in called, (
        "build_loop.main() does not call self_heal. It was defined and never called for a "
        "full day, during which a /mnt/c path sat in .git/config breaking every worktree "
        "creation and stranding eleven commits of finished work."
    )

    # And inside the loop, not once before it: the corruption is written DURING operation by a
    # dispatched agent, so a repair that only runs at startup cannot fix it.
    loops = [node for node in ast.walk(main) if isinstance(node, (ast.While, ast.For))]
    assert any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Name)
        and inner.func.id == "self_heal"
        for loop in loops
        for inner in ast.walk(loop)
    ), (
        "self_heal is called outside the tick loop; a startup-only repair cannot fix a fault that appears after startup"
    )


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


# --- autonomous workspace pruning lives in the loop, 25 August 2026 ------------
#
# 547 worktrees and 673 stale branches accumulated with nothing pruning them, .git reached
# 136 MB, and provisioning began to fail -- which sent every dispatch to a fallback form whose
# commits cannot be harvested. Eleven commits of finished work were stranded and one unit was
# built twice.
#
# It sits in build_loop, not build_driver, because it is housekeeping and because a destructive
# git sweep has no business running inside the driver's unit tests -- the first attempt did
# exactly that and started removing real worktrees during a test run.


def _loop_source() -> str:
    return (ROOT / ".harness" / "build_loop.py").read_text(encoding="utf-8")


def test_the_loop_prunes_spent_workspaces_every_tick() -> None:
    tree = ast.parse(_loop_source())
    main = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "main"
    )
    loops = [n for n in ast.walk(main) if isinstance(n, (ast.While, ast.For))]
    assert any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Name)
        and inner.func.id == "prune_spent_workspaces"
        for loop in loops
        for inner in ast.walk(loop)
    ), (
        "build_loop.main() does not prune inside the tick loop; accumulation broke provisioning once already"
    )


def test_the_prune_refuses_to_touch_anything_but_a_dispatch_workspace() -> None:
    """The safety rules are what make an autonomous sweep acceptable at all."""
    source = _loop_source()
    start = source.index("def prune_spent_workspaces(")
    body = source[start : source.index("\ndef self_heal(", start)]

    assert "/.harness/dispatch/" in body, (
        "the prune no longer restricts itself to dispatch workspaces -- a unit worktree or the "
        "main tree could be removed"
    )
    assert "rev-list" in body and "ahead" in body, (
        "the prune no longer checks whether a workspace carries commits HEAD lacks; a cleanup "
        "that discards a commit is worse than no cleanup"
    )
    assert "status" in body and "--porcelain" in body, (
        "the prune no longer checks for uncommitted work"
    )
    assert "consilient-workspace-probe-" in body, (
        "the prune no longer ignores the provisioning probe marker, so every workspace will "
        "look dirty and nothing will ever be pruned"
    )


def test_the_prune_has_a_ceiling_so_an_ordinary_tick_pays_nothing() -> None:
    source = _loop_source()
    assert "PRUNE_CEILING" in source
    start = source.index("def prune_spent_workspaces(")
    body = source[start : source.index("\ndef self_heal(", start)]
    assert "PRUNE_CEILING" in body, "the ceiling is defined but not consulted"


# --- duplicate-subsystem serialisation and pre-merge rebasing, BN ----------------


def test_duplicate_subsystem_serialises_n03_and_t02_from_the_real_plan(
    capsys,
) -> None:
    driver = _load_driver()
    if not driver.UNITS.is_file():
        pytest.skip(
            "the real plan is instance data and is not tracked (Z04); this check reads it "
            "as evidence and cannot run without it"
        )
    units = json.loads(driver.UNITS.read_text(encoding="utf-8"))

    assert not driver.ready("T02", units["T02"], set(units), units, in_flight={"N03"})
    assert "serialising T02 behind N03" in capsys.readouterr().out
    assert driver.ready("T02", units["T02"], set(units), units, in_flight=set())


def test_duplicate_subsystem_threshold_is_configurable(monkeypatch) -> None:
    monkeypatch.setenv("CONSILIENT_SUBSYSTEM_JACCARD_THRESHOLD", "0.21")
    driver = _load_driver()
    if not driver.UNITS.is_file():
        pytest.skip(
            "the real plan is instance data and is not tracked (Z04); this check reads it "
            "as evidence and cannot run without it"
        )
    units = json.loads(driver.UNITS.read_text(encoding="utf-8"))

    assert driver.ready("T02", units["T02"], set(units), units, in_flight={"N03"})


def test_duplicate_subsystem_firing_rate_stays_below_five_percent() -> None:
    driver = _load_driver()
    if not driver.UNITS.is_file():
        pytest.skip(
            "the real plan is instance data and is not tracked (Z04); this check reads it "
            "as evidence and cannot run without it"
        )
    units = json.loads(driver.UNITS.read_text(encoding="utf-8"))
    sharing = [
        (left, right)
        for left, right in combinations(units, 2)
        if set(units[left]["claims"]) & set(units[right]["claims"])
    ]
    firings = [
        (left, right)
        for left, right in sharing
        if not driver.ready(left, units[left], set(units), units, in_flight={right})
    ]

    assert sharing
    assert len(firings) / len(sharing) <= 0.05, (
        f"duplicate-subsystem threshold fired for {len(firings)}/{len(sharing)} "
        "claim-sharing pairs"
    )


def _run_duplicate_subsystem_merge_tick(
    tmp_path: Path, monkeypatch, capsys, *, dispatcher_live: bool
) -> tuple[list[tuple[object, ...]], str]:
    driver = _load_driver()
    worktrees = tmp_path / "unit-worktrees"
    (worktrees / "U01").mkdir(parents=True)
    now = driver.time.time()
    state: dict[str, object] = {
        "in_flight": {"U01": (now, 3600.0)} if dispatcher_live else {},
        "attempts": {},
        "quarantined": ["U01"],
    }
    units = {
        "U01": {
            "title": "one bounded unit",
            "commit": "feat(unit): bounded work",
            "claims": [],
            "deps": [],
        }
    }

    class _GitResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_sh(args: list[str]) -> _GitResult:
        result = _GitResult()
        result.stdout = "one\ntwo\n" if "rev-list" in args else "head"
        return result

    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "record_tick_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(
        driver,
        "rebase_worktree",
        lambda uid, _path: calls.append(("rebase", uid)) or True,
    )
    monkeypatch.setattr(
        driver,
        "merge_unit_worktree",
        lambda uid, quiescent=False: (
            calls.append(("merge", uid, quiescent)) or "no commits"
        ),
    )

    assert driver.main() == 0
    return calls, capsys.readouterr().out


def test_duplicate_subsystem_rebases_quiescent_worktree_before_merge(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    calls, output = _run_duplicate_subsystem_merge_tick(
        tmp_path, monkeypatch, capsys, dispatcher_live=False
    )

    assert calls == [("rebase", "U01"), ("merge", "U01", False)]
    assert "2 commit(s) replayed" in output


def test_duplicate_subsystem_does_not_rebase_a_live_dispatcher(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    calls, _output = _run_duplicate_subsystem_merge_tick(
        tmp_path, monkeypatch, capsys, dispatcher_live=True
    )

    assert calls == [("merge", "U01", False)]


def test_duplicate_subsystem_candidates_do_not_launch_together(
    tmp_path: Path, monkeypatch
) -> None:
    driver = _load_driver()
    if not driver.UNITS.is_file():
        pytest.skip(
            "the real plan is instance data and is not tracked (Z04); this check reads it "
            "as evidence and cannot run without it"
        )
    units = {
        uid: {
            "title": "atomic coordination fencing",
            "commit": "feat(coordination): atomic fencing",
            "claims": ["shared.py"],
            "deps": [],
        }
        for uid in ("U01", "U02")
    }
    state: dict[str, object] = {"in_flight": {}, "attempts": {}}
    launched: list[list[str]] = []

    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "write_brief", lambda *_args: tmp_path / "brief.md")
    monkeypatch.setattr(driver, "pick_arm", lambda *_args: ("codex", None, 60))
    monkeypatch.setattr(driver, "unit_worktree", lambda _uid: None)
    monkeypatch.setattr(driver, "publish_if_ready", lambda *_args: "")
    monkeypatch.setattr(driver, "record_tick_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        driver.subprocess,
        "Popen",
        lambda args, **_kwargs: launched.append(args),
    )

    assert driver.main() == 0
    assert len(launched) == 1


def test_quarantine_still_blocks_dispatching_new_work(monkeypatch) -> None:
    """The half of quarantine that must stay: a unit dying the same way three times does not
    get handed more dispatches. Only the verdict path reopens."""
    source = DRIVER.read_text(encoding="utf-8")
    assert source.count('state.setdefault("quarantined", [])') >= 3, (
        "quarantine must still gate build selection and conflict resolution; only review "
        "was meant to reopen"
    )


def test_a_worktree_sitting_at_head_is_not_already_landed(monkeypatch) -> None:
    """Emptiness is not evidence of completion.

    MEASURED 25 August 2026: both halves of `_cherry_and_diff_match` pass trivially when the
    worktree head IS HEAD -- `git cherry` prints nothing and `git diff --quiet` exits 0 -- so
    the driver reported BN's work as present in HEAD while `rebase_mergeable_worktrees` and
    `SUBSYSTEM_JACCARD_THRESHOLD` were both absent from it. The unit was then dropped from
    `conflicts`, so the driver stopped trying to merge the work it had actually done.

    `_refresh_worktree` resets clean unit worktrees to HEAD every tick, so this is the ordinary
    state of a conflicted unit, not an edge case. A gate accepting an artefact that is not there
    is a false accept, which is the quantity this project exists to measure.
    """
    driver = _load_driver()
    head = "a" * 40

    def fake_sh(args: list[str], **_kw):
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        result = _R()
        if args[:2] == ["git", "rev-parse"]:
            result.stdout = head + "\n"
        return result

    monkeypatch.setattr(driver, "sh", fake_sh)
    assert driver._cherry_and_diff_match(head, [".harness/build_driver.py"]) is False, (
        "a worktree at exactly HEAD has done nothing and must not read as landed"
    )
    # A genuinely different head still reaches the real checks (which the stub passes).
    assert driver._cherry_and_diff_match("b" * 40, [".harness/build_driver.py"]) is True


def _verdict_fixture(
    tmp_path,
    monkeypatch,
    *,
    receipt_attempt,
    expected_attempt,
    receipt_artefact,
    expected_artefact,
    current_artefact,
    verdict="SOUND",
    findings=None,
):
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: current_artefact)
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": receipt_artefact,
                "attempt": receipt_attempt,
                "verdict": verdict,
                "findings": findings if findings is not None else [],
            }
        ),
        encoding="utf-8",
    )
    expected = {"artefact": expected_artefact, "attempt": expected_attempt}
    return driver._load_verdict_file("U01", {"claims": ["a.py"]}, expected)


def test_a_verdict_about_the_current_artefact_survives_a_stale_attempt_number(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026: nine of the ten most recent receipts were discarded, several with
    the artefact matching EXACTLY and only the attempt counter differing -- AL at 2 against an
    expected 3, AO at 1 against 2. A review takes ~20 minutes, the driver re-dispatches sooner,
    and the original agent's valid verdict arrives one attempt behind and is refused. Nothing
    could be verified while agents worked continuously.

    The attempt number says which dispatch spoke. The artefact says what was judged.
    """
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=2,
        expected_attempt=3,
        receipt_artefact="a" * 64,
        expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "SOUND", (
        "a verdict about the current artefact must not be lost to a counter"
    )


def test_a_verdict_about_a_different_artefact_is_still_refused(
    tmp_path: Path, monkeypatch
) -> None:
    """The binding that matters is unchanged: a verdict about other code is not evidence about
    this code, whatever its attempt number says."""
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=3,
        expected_attempt=3,
        receipt_artefact="b" * 64,
        expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "receipt_mismatched"


def test_a_verdict_is_refused_when_the_tree_has_moved_under_the_expectation(
    tmp_path: Path, monkeypatch
) -> None:
    """Both sides are still checked. If the unit's identity re-derived from the tree no longer
    equals what the review was told to judge, the verdict is stale and refused."""
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=3,
        expected_attempt=3,
        receipt_artefact="a" * 64,
        expected_artefact="a" * 64,
        current_artefact="c" * 64,
    )
    assert outcome == "receipt_mismatched"


def test_suite_green_fails_closed_when_the_run_does_not_finish(monkeypatch) -> None:
    """MEASURED 25 August 2026, 21:36: a tick sat THIRTY-FIVE MINUTES on the suite having burned
    29 seconds of CPU -- starved, not computing -- because `sh()` passes no timeout. The only
    bound was the loop abandoning the whole tick at 3000s, which also leaks grandchildren.

    The starvation is self-inflicted: the same tick dispatches its agents and then runs the full
    suite against the load it just created. Since the suite is the last gate before publication,
    a tick that never finishes it never publishes -- thirty commits sat behind exactly this.

    An unfinished run is "not evaluated", which is not "passing".
    """
    driver = _load_driver()

    def _timeout(*_args, **kwargs):
        assert "timeout" in kwargs, "the suite call must carry a timeout"
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=kwargs["timeout"])

    monkeypatch.setattr(driver, "sh", _timeout)
    assert driver.suite_green() is False


def test_the_suite_bound_is_well_inside_the_tick_abandonment(monkeypatch) -> None:
    """The bound only helps if it fires before the loop gives up on the whole tick. The loop
    abandons at 3000s; a clean run of this suite is about seven minutes."""
    driver = _load_driver()
    assert driver.SUITE_TIMEOUT_S >= 600, (
        "shorter than a clean run would fail closed constantly"
    )
    assert driver.SUITE_TIMEOUT_S <= 1800, (
        "must fire well before the 3000s tick abandonment"
    )


def test_a_valid_verdict_receipt_is_consumed_even_with_an_empty_envelope(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, 21:50 -- why the day produced so few verdicts.

    AE and AA both held well-formed `<uid>-verdict.json` receipts bound to their unit's CURRENT
    artefact; the driver's own `_load_verdict_file` returned SOUND and DEFECTIVE for them when
    called directly. Both sat unconsumed because `<uid>-verify.out` was ZERO BYTES. A finished
    review with a valid verdict was ignored because a DIFFERENT file was empty.

    The `.out` is the dispatch envelope; the verdict is what the reviewer wrote. The envelope can
    be truncated by a re-dispatch or never written if the wrapper died after the reviewer had
    already produced its verdict.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    artefact = "d" * 64
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: artefact)
    (briefs / "U01-verify.out").write_text("", encoding="utf-8")  # the empty envelope
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    outcome, _findings = driver._load_verdict_file(
        "U01", {"claims": ["a.py"]}, {"artefact": artefact, "attempt": 1}
    )
    assert outcome == "SOUND"

    # The completion gate itself: an empty envelope must not hide a present, BOUND receipt.
    # (Superseded assertion once here checked for a literal source string; that string moved
    # when the gate was extracted into `review_receipt_is_finished` to fix the stale-receipt
    # regression below, so this now calls the real function instead of grepping for its shape.)
    assert (briefs / "U01-verify.out").stat().st_size == 0
    assert (briefs / "U01-verdict.json").stat().st_size > 0
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": artefact, "attempt": 1})
        is True
    )


def test_a_stale_verdict_receipt_from_a_prior_attempt_is_not_evidence_this_one_finished(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:00 -- a REGRESSION in the very fix that let a receipt count
    as completion evidence. `open(path, "w")` truncates `.out` to 0 bytes the instant a
    re-dispatch launches, but nothing clears the OLD `<uid>-verdict.json` from the attempt
    before. A01, AB and AC were each re-dispatched at a fresh attempt after their artefact
    changed; their stale verdict.json (wrong attempt/artefact) still had bytes in it, so the
    naive "verdict.json exists" check fired immediately -- before the new review had produced
    anything -- and the resulting `no_dispatch` was memoised PERMANENTLY. The real verdict,
    written minutes later, was never looked at again.

    A verdict.json only counts as evidence THIS review finished if its own (unit, attempt,
    artefact) matches what the driver currently expects.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text(
        "", encoding="utf-8"
    )  # freshly truncated by re-dispatch
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": "OLD" + "a" * 61,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    current_expectation = {"artefact": "NEW" + "b" * 61, "attempt": 2}
    assert driver.review_receipt_is_finished("U01", current_expectation) is False, (
        "a verdict.json from a DIFFERENT attempt/artefact must not count as this review "
        "having finished"
    )


def test_a_verdict_receipt_matching_the_current_attempt_still_counts_as_finished(
    tmp_path: Path, monkeypatch
) -> None:
    """The case `review_receipt_is_finished` exists to preserve: an empty envelope must not
    hide a genuinely current, valid verdict (the original AE/AA fix)."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text("", encoding="utf-8")
    artefact = "c" * 64
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    assert (
        driver.review_receipt_is_finished("U01", {"artefact": artefact, "attempt": 1})
        is True
    )


def test_a_non_empty_envelope_counts_as_finished_regardless_of_the_receipt(
    tmp_path: Path, monkeypatch
) -> None:
    """The other half: a real, completed envelope is proof enough on its own, whatever state
    the verdict.json is in -- including absent."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text("status: ok\n", encoding="utf-8")
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": "x", "attempt": 1})
        is True
    )


def test_neither_file_present_is_not_finished(tmp_path: Path, monkeypatch) -> None:
    """The ordinary, most common state: a review genuinely still running. Must not be treated
    as finished, or its eventual real verdict is exposed to the same permanent-memo hazard."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": "x", "attempt": 1})
        is False
    )


def test_consume_review_verdict_only_memoises_a_terminal_outcome(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:15, from the trajectory itself: A01's history shows
    `attempt=1 artefact=6e826... outcome=no_dispatch`, and the SAME (attempt, artefact) pair
    was never looked at again -- because the memo used to be written for EVERY outcome, and
    F-05 refunds an infrastructure loss's attempt counter so a retry reuses the identical pair.

    SOUND and DEFECTIVE must still be remembered, so a re-dispatch under the same pair cannot
    double-apply a real verdict.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _record: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)

    unit = {"claims": ["a.py"]}

    state: dict[str, object] = {
        "review_expected": {"U01": {"attempt": 1, "artefact": "x" * 64}}
    }
    driver.consume_review_verdict(state, "U01", unit)  # no files -> no_dispatch
    assert state["review_results"]["U01"]["outcome"] == "no_dispatch"
    assert "U01" not in state.get("review_consumed", {}), (
        "a non-terminal outcome must not be memoised"
    )

    artefact = "y" * 64
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: artefact)
    (briefs / "U02-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U02",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    state2: dict[str, object] = {
        "review_expected": {"U02": {"attempt": 1, "artefact": artefact}}
    }
    driver.consume_review_verdict(state2, "U02", unit)
    assert state2["review_results"]["U02"]["outcome"] == "SOUND"
    assert state2["review_consumed"]["U02"] == {"attempt": 1, "artefact": artefact}, (
        "a terminal SOUND outcome must still be memoised"
    )


def test_clear_stale_review_memos_recovers_units_stuck_by_the_old_semantics(
    tmp_path: Path,
) -> None:
    """The one-time migration for memos written before outcome-gating existed. A01, AB and AC
    were exactly this: a real SOUND/DEFECTIVE receipt sat on disk, unreachable because a
    non-terminal memo from an earlier tick had already frozen their (attempt, artefact) pair."""
    driver = _load_driver()
    state: dict[str, object] = {
        "review_consumed": {
            "A01": {"attempt": 1, "artefact": "a" * 64},  # stuck: non-terminal
            "AF": {
                "attempt": 1,
                "artefact": "f" * 64,
            },  # correctly terminal, must survive
            "GONE": {
                "attempt": 1,
                "artefact": "g" * 64,
            },  # not a real unit; must not be re-queued
        },
        "review_results": {
            "A01": {"outcome": "no_dispatch"},
            "AF": {"outcome": "SOUND"},
            "GONE": {"outcome": "no_dispatch"},
        },
        "review_dispatched": [],
    }
    units = {"A01": {"claims": []}, "AF": {"claims": []}}

    cleared = driver.clear_stale_review_memos(state, units)

    assert sorted(cleared) == ["A01", "GONE"]
    assert "A01" not in state["review_consumed"]
    assert "A01" in state["review_dispatched"], (
        "must be re-queued so it is looked at again"
    )
    assert "AF" in state["review_consumed"], "a terminal memo must not be disturbed"
    assert "AF" not in state["review_dispatched"], (
        "a correctly-consumed unit is not re-queued"
    )
    assert "GONE" not in state["review_dispatched"], (
        "a uid absent from the plan must not be queued for review"
    )


def test_clear_stale_review_memos_is_a_no_op_once_nothing_is_stale(
    tmp_path: Path,
) -> None:
    """Safe to run every tick: once every memo is terminal, this changes nothing."""
    driver = _load_driver()
    state: dict[str, object] = {
        "review_consumed": {"AF": {"attempt": 1, "artefact": "f" * 64}},
        "review_results": {"AF": {"outcome": "SOUND"}},
        "review_dispatched": [],
    }
    units = {"AF": {"claims": []}}
    assert driver.clear_stale_review_memos(state, units) == []
    assert state["review_consumed"] == {"AF": {"attempt": 1, "artefact": "f" * 64}}
    assert state["review_dispatched"] == []


def test_a_rebuilt_unit_gets_a_fresh_review_budget(monkeypatch) -> None:
    """DECIDED BY THE PRINCIPAL, 25 August 2026: AL, AO and AP were each escalated -- "reached
    3 attempts, refusing another dispatch" -- while each held a DIFFERENT, newer artefact than
    the one their three attempts had actually been spent against. `review_attempts` was a pure
    LIFETIME counter, unrelated to which code was under review: a unit rebuilt after a genuine
    DEFECTIVE finding, each time addressing what the review found, accumulated exactly as fast
    as one stuck reviewing the SAME broken code three times over -- and both landed on the
    identical "it needs a person," even though only the second is actually stuck.
    """
    driver = _load_driver()
    old_artefact = "a" * 64
    new_artefact = "b" * 64
    state: dict[str, object] = {
        "review_attempts": {"U01": 3},
        "review_escalated": ["U01"],
        "review_expected": {"U01": {"artefact": old_artefact, "attempt": 3}},
    }
    assert driver.review_dispatch_allowed(state, "U01") is False, (
        "sanity: three attempts against the old artefact must still be escalated"
    )

    changed = driver.reset_review_attempts_on_new_artefact(state, "U01", new_artefact)
    assert changed is True
    assert state["review_attempts"]["U01"] == 0
    assert "U01" not in state["review_escalated"]
    assert driver.review_dispatch_allowed(state, "U01") is True, (
        "a rebuilt unit's new code must be reviewable again"
    )


def test_reset_is_a_no_op_when_the_artefact_has_not_changed(monkeypatch) -> None:
    """The other half: F-05 refunds an infrastructure-loss retry WITHOUT changing
    `review_expected`, and three genuine attempts against the SAME code must still escalate."""
    driver = _load_driver()
    artefact = "c" * 64
    state: dict[str, object] = {
        "review_attempts": {"U01": 3},
        "review_escalated": ["U01"],
        "review_expected": {"U01": {"artefact": artefact, "attempt": 3}},
    }
    changed = driver.reset_review_attempts_on_new_artefact(state, "U01", artefact)
    assert changed is False
    assert state["review_attempts"]["U01"] == 3
    assert "U01" in state["review_escalated"]


def test_reset_does_nothing_for_a_unit_never_dispatched_before(monkeypatch) -> None:
    """No `review_expected` entry yet -- a first-ever dispatch -- must not be treated as a
    reset event (nothing to report, nothing to change)."""
    driver = _load_driver()
    state: dict[str, object] = {"review_expected": {}}
    assert driver.reset_review_attempts_on_new_artefact(state, "U01", "x" * 64) is False
    assert state.get("review_attempts", {}).get("U01") is None


def test_a_crash_during_review_dispatch_refunds_the_review_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:30: AL and AO, freshly reset for review, crashed on a
    workspace-setup timeout (`git clone --separate-git-dir`) before a reviewer ever ran. The
    crash-handling loop refunded `state["attempts"]` -- the BUILD counter -- unconditionally,
    for every crash, regardless of whether the dead run belonged to the build pool or the
    review pool. A crash during a REVIEW dispatch never had its review attempt refunded at
    all: F-05 says an infrastructure death must not spend a retry, and this path was spending
    one silently.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    (briefs / "U01.err").write_text("boom\n", encoding="utf-8")
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U01", "boom", False)]
    )
    monkeypatch.setattr(driver, "record_restart", lambda *_a, **_k: False)
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "quarantine_unit", lambda *_a, **_k: False)

    state: dict[str, object] = {
        "in_flight": {},
        "review_dispatched": ["U01"],
        "review_attempts": {"U01": 2},
        "attempts": {"U01": 5},
        "crash_history": {},
    }
    driver._handle_crashed_dispatches(state)

    assert state["review_attempts"]["U01"] == 1, "the REVIEW attempt must be refunded"
    assert state["attempts"]["U01"] == 5, (
        "the unrelated BUILD counter must be untouched"
    )
    assert "U01" not in state["review_dispatched"]


def test_a_crash_during_build_dispatch_still_refunds_the_build_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """The other half: a crash while a unit is being BUILT must keep refunding the build
    counter exactly as before -- this fix must not touch that path."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    (briefs / "U02.err").write_text("boom\n", encoding="utf-8")
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U02", "boom", False)]
    )
    monkeypatch.setattr(driver, "record_restart", lambda *_a, **_k: False)
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "quarantine_unit", lambda *_a, **_k: False)

    state: dict[str, object] = {
        "in_flight": {"U02": (0.0, 0.0)},
        "review_dispatched": [],
        "review_attempts": {},
        "attempts": {"U02": 3},
        "crash_history": {},
    }
    driver._handle_crashed_dispatches(state)

    assert state["attempts"]["U02"] == 2, "the BUILD attempt must still be refunded"
    assert "U02" not in state["in_flight"]


def test_merge_unit_worktree_signs_off_the_cherry_pick(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: CI's DCO check failed on every recent push with "no sign-off
    found" for every commit. A dispatched worker's own commit is not guaranteed to carry a
    Signed-off-by trailer -- workers run arbitrary shells across several harnesses, and
    asking each one to remember `--signoff` is a prompt-level fix. The sign-off is stamped
    at the one chokepoint all unit work must pass through instead: the cherry-pick that
    merges a unit's commits into the shared branch.
    """
    driver = _load_driver()
    worktrees = tmp_path / "worktrees"
    worktrees.mkdir()
    (worktrees / "U01").mkdir()
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(driver, "gate_merged_tree", lambda _touched, _baseline: "")

    calls: list[list[str]] = []

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        calls.append(args)
        if "-C" in args and "rev-parse" in args:
            return _Result("unit-head-sha\n")
        if args[:2] == ["git", "rev-parse"]:
            return _Result("main-head-sha\n")
        if "rev-list" in args:
            return _Result("abc123\n")
        if args[:3] == ["git", "show", "--name-only"]:
            return _Result("some/file.py\n")
        if "diff" in args and "--numstat" in args:
            return _Result("")
        if "cherry-pick" in args:
            return _Result("", 0)
        return _Result("")

    monkeypatch.setattr(driver, "sh", fake_sh)

    result = driver.merge_unit_worktree("U01")

    assert result == "applied 1 commit(s) from U01"
    cherry_pick_calls = [c for c in calls if "cherry-pick" in c]
    assert cherry_pick_calls, "expected a cherry-pick call"
    assert "--signoff" in cherry_pick_calls[0]


def test_every_documented_infrastructure_loss_refunds_the_review_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: `_INFRASTRUCTURE_LOSS` only ever refunded two of the six
    outcomes `clear_stale_review_memos`'s own docstring names as infrastructure losses.
    Two live units (AC, AT) had a real verdict silently orphaned this way: AC's DEFECTIVE
    receipt arrived after the driver had already recorded `dispatch_failed`; AT's SOUND
    was lost to a WSL path-translation failure and recorded as `no_receipt_file`. Neither
    is evidence about the code -- F-05 says an infrastructure death must not spend a retry,
    for all six outcomes it names, not just two.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _record: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "z" * 64)

    unit = {"claims": ["a.py"]}
    cases = {
        "U_FAILED": ("status: failed\n", None),
        "U_NORECEIPT": ("status: ok\n", None),
        "U_UNPARSEABLE": ("status: ok\n", "not json"),
        "U_MISMATCHED": (
            "status: ok\n",
            '{"v": 1, "unit": "WRONG", "artefact": "%s", "attempt": 1, '
            '"verdict": "SOUND", "findings": []}' % ("z" * 64),
        ),
    }
    for uid, (envelope, verdict_body) in cases.items():
        (briefs / f"{uid}-verify.out").write_text(envelope, encoding="utf-8")
        if verdict_body is not None:
            (briefs / f"{uid}-verdict.json").write_text(verdict_body, encoding="utf-8")
        state: dict[str, object] = {
            "review_expected": {uid: {"attempt": 1, "artefact": "z" * 64}},
            "review_attempts": {uid: 2},
        }
        outcome = driver.consume_review_verdict(state, uid, unit)
        assert outcome in (
            "dispatch_failed",
            "no_receipt_file",
            "receipt_unparseable",
            "receipt_mismatched",
        ), f"{uid}: unexpected outcome {outcome!r}"
        assert state["review_attempts"][uid] == 1, (
            f"{uid}: outcome {outcome!r} must refund the review attempt, not spend it"
        )


def test_clear_unjustly_escalated_reviews_frees_the_three_named_units() -> None:
    """MEASURED 26 August 2026: AC, AT and B01 each reached the 3-attempt cap entirely on
    infrastructure losses (a late-arriving receipt, a WSL path-translation failure, a dead
    dispatch) against an unchanged artefact -- not a genuine repeated defect. Un-escalating
    them gives each a fresh, real review rather than leaving a code bug's damage standing.
    """
    driver = _load_driver()
    state: dict[str, object] = {
        "review_escalated": ["AC", "AT", "B01", "AJ", "AP"],
        "review_attempts": {"AC": 3, "AT": 3, "B01": 3, "AJ": 3, "AP": 3},
    }
    cleared = driver.clear_unjustly_escalated_reviews(state)

    assert sorted(cleared) == ["AC", "AT", "B01"]
    for uid in ("AC", "AT", "B01"):
        assert uid not in state["review_escalated"]
        assert state["review_attempts"][uid] == 0
    for uid in ("AJ", "AP"):
        assert uid in state["review_escalated"], (
            "genuinely escalated units must be untouched"
        )
        assert state["review_attempts"][uid] == 3


def test_clear_unjustly_escalated_reviews_is_a_no_op_once_cleared() -> None:
    driver = _load_driver()
    state: dict[str, object] = {"review_escalated": [], "review_attempts": {}}
    assert driver.clear_unjustly_escalated_reviews(state) == []
    assert state["review_escalated"] == []


def test_mypy_gate_does_not_refuse_a_files_own_pre_existing_debt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: bare zero-tolerance mypy meant a file carrying pre-existing type
    debt (build_driver.py itself, ~87 long-accepted errors) could never pass this gate for ANY
    commit that touched it, regardless of whether the commit fixed, worsened, or never touched
    the debt at all. BO's own verified-zero-delta fix was refused by this exact gate. The fix
    compares against the tree the cherry-pick started from and refuses only a genuine increase.
    """
    driver = _load_driver()

    calls: list[list[str]] = []

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        calls.append(args)
        if "worktree" in args and "add" in args:
            # _mypy_gate checks (scratch / path).exists() on real disk, so the fake
            # worktree needs the same file physically present to be treated as
            # carrying the same pre-existing debt as the working tree.
            scratch = Path(args[args.index("--detach") + 1])
            (scratch / "some").mkdir(parents=True)
            (scratch / "some" / "file.py").write_text("", encoding="utf-8")
            return _Result("", 0)
        if "worktree" in args and "remove" in args:
            return _Result("", 0)
        if "mypy" in args:
            # Both the "after" and any "before" mypy invocation land here; both see the
            # same pre-existing debt, so no new error is introduced by this merge.
            return _Result(
                "some/file.py:1: error: fake pre-existing debt  [no-untyped-def]\n"
                "Found 1 error in 1 file (checked 1 source file)\n",
                1,
            )
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is None, (
        f"pre-existing debt with no new errors must not refuse the merge: {result}"
    )
    mypy_calls = [c for c in calls if "mypy" in c]
    assert len(mypy_calls) == 2, "expected one 'after' and one 'before' mypy invocation"


def test_mypy_gate_refuses_a_genuine_regression(tmp_path: Path, monkeypatch) -> None:
    """The other half: if the touched file's error count is actually HIGHER than at the
    baseline, the gate must still refuse -- this fix narrows what counts as a failure, it does
    not remove the check.
    """
    driver = _load_driver()

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        if "worktree" in args and "add" in args:
            scratch = Path(args[args.index("--detach") + 1])
            (scratch / "some").mkdir(parents=True)
            (scratch / "some" / "file.py").write_text("", encoding="utf-8")
            return _Result("", 0)
        if "worktree" in args and "remove" in args:
            return _Result("", 0)
        if "mypy" in args:
            # The "before" call's file arguments point inside the scratch worktree
            # (named "gate-baseline-<hex>"); the "after" call uses the plain relative
            # path. That is the only reliable way to tell them apart here, since the
            # scratch dir never actually gets its own mypy.ini written to disk.
            if any("gate-baseline-" in arg for arg in args):
                return _Result(
                    "some/file.py:1: error: one pre-existing error  [no-untyped-def]\n",
                    1,
                )
            return _Result(
                "some/file.py:1: error: one pre-existing error  [no-untyped-def]\n"
                "some/file.py:2: error: a brand new one  [no-untyped-def]\n",
                1,
            )
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is not None, (
        "a genuine error-count increase must still refuse the merge"
    )
    assert "regressed" in result


def test_mypy_gate_fails_closed_when_the_baseline_worktree_cannot_be_created(
    tmp_path: Path, monkeypatch
) -> None:
    """If the baseline can't be established at all, refuse rather than silently let anything
    through -- the whole point is comparing against a known-good state, not skipping the check.
    """
    driver = _load_driver()

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        if "worktree" in args and "add" in args:
            return _Result("fatal: could not create worktree", 1)
        if "mypy" in args:
            return _Result("some/file.py:1: error: whatever  [no-untyped-def]\n", 1)
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is not None, (
        "an unestablished baseline must fail closed, not pass silently"
    )


def test_main_merges_a_built_units_worktree_when_it_gains_new_commits(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: `mergeable` excluded any uid already in `built`, so a unit
    whose worktree gained a genuinely new commit after being marked built (a fork's
    conflict-resolution or review fix landing after the plan commit already merged) was
    never revisited by any later tick. AN, AJ and AL each sat this way -- `built: true`, a
    real new commit sitting in the worktree, zero merge attempts logged since. Excluding
    built units from the merge loop was never the right check: `merge_unit_worktree`'s own
    `HEAD..head` rev-list is the cheap no-op guard for a unit with nothing new to merge.
    """
    driver = _load_driver()
    worktrees = tmp_path / "unit-worktrees"
    (worktrees / "U01").mkdir(parents=True)
    state: dict[str, object] = {
        "in_flight": {},
        "attempts": {},
        "built": ["U01"],
        "review_dispatched": ["U01"],
    }
    units = {
        "U01": {
            "title": "already built, worktree has a newer commit",
            "commit": "feat(unit): already built",
            "claims": [],
            "deps": [],
        }
    }
    calls: list[str] = []
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "record_tick_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        driver,
        "merge_unit_worktree",
        lambda uid: calls.append(uid) or "no commits",
    )

    assert driver.main() == 0

    assert calls == ["U01"], (
        "a built unit's worktree must still be checked for new commits to merge"
    )


# --- BL: classify conflicts by content, clear them on retirement, gate merges --
#
# The already-landed detector used to grep commit SUBJECTS. Over 646 commits this
# repository reused 14 subjects; 9 of the top 12 reused subjects carry different
# patch content [measured, 24 August 2026]. A subject hit retired the unit. That
# is a false-accept in the driver's own classifier, and it is how harness.py
# acquired a duplicate 313-line block.
#
# These four tests are the unit's done criteria (A1, A2, A5-driver-half, F).


_GIT_ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in {"GIT_DIR", "GIT_WORK_TREE"}
}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_GIT_ENV,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "bl@test")
    _git(path, "config", "user.name", "BL")


def _commit_file(repo: Path, rel: str, body: str, subject: str) -> str:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _isolate_driver(
    driver: object, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver, "ROOT", repo)
    monkeypatch.setattr(driver, "WORKTREES", repo / ".harness" / "unit-worktrees")
    monkeypatch.setattr(driver, "STATE", repo / ".harness" / "driver-state.json")

    def isolated_sh(args: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_GIT_ENV,
            **kw,
        )

    monkeypatch.setattr(driver, "sh", isolated_sh)


def test_classifier_does_not_retire_on_subject_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A1: identical subject, different content — the second stays escalated."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "mod.py", "base = 0\n", "init")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    first_lines = "\n".join(f"FIRST_{i} = {i}" for i in range(25)) + "\n"
    second_lines = "\n".join(f"SECOND_{i} = {i}" for i in range(25)) + "\n"
    _git(repo, "checkout", "-b", "first")
    _commit_file(repo, "mod.py", first_lines, "feat: shared subject")
    _git(repo, "checkout", default)
    _git(repo, "checkout", "-b", "second")
    second_sha = _commit_file(repo, "mod.py", second_lines, "feat: shared subject")
    _git(repo, "checkout", default)
    _git(repo, "merge", "--no-ff", "first", "-m", "land first")

    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)
    state: dict[str, object] = {
        "conflicts": {
            "U2": f"CONFLICT cherry-picking {second_sha[:9]} for U2 (0 applied); needs resolution"
        },
        "force_done": [],
        "built": [],
        "done": [],
    }
    retired = driver.retest_conflicts(state)
    assert retired == 0
    assert "U2" in cast("dict[str, str]", state["conflicts"])


def test_conflict_cleared_on_retire() -> None:
    """A2: no uid may sit in both conflicts and force_done — that was K01 live."""
    driver = _load_driver()
    state: dict[str, object] = {
        "conflicts": {"K01": "CONFLICT cherry-picking deadbeef for K01"},
        "force_done": ["K01", "T01"],
        "built": [],
        "done": [],
    }
    driver.clear_retired_conflicts(state)
    overlap = set(cast("dict[str, str]", state["conflicts"])) & set(
        cast("list[str]", state["force_done"])
    )
    assert overlap == set(), overlap


def test_failed_gate_reverts_cherry_pick(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cherry-pick whose result fails the gate is undone and the unit escalates."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    pre = _commit_file(repo, "ok.py", "VALUE = 1\n", "init")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    _git(repo, "checkout", "-b", "unit")
    _commit_file(repo, "ok.py", "VALUE = 2\n", "feat: change value")
    _git(repo, "checkout", default)
    worktree = repo / ".harness" / "unit-worktrees" / "U1"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", str(worktree), "unit")

    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)
    monkeypatch.setattr(
        driver,
        "gate_merged_tree",
        lambda _touched, _baseline: "ruff: simulated gate failure",
    )

    msg = driver.merge_unit_worktree("U1")
    assert msg.startswith("CONFLICT"), msg
    assert "gate" in msg.lower()
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == pre


def test_classifier_does_not_grep_subjects() -> None:
    """The false-accept path was `git log --grep <subject>`. It must stay gone."""
    source = DRIVER.read_text(encoding="utf-8")
    assert "--grep" not in source
    assert "--merge-base=" in source
    assert "retired without review" in source
    assert "--config-file" in source and "mypy.ini" in source
    gate = source.split("def gate_merged_tree", 1)[1].split("\ndef ", 1)[0]
    assert "--config-file" in gate and "mypy.ini" in gate
    assert "--strict" not in gate.replace("never bare `--strict`", "")


def test_content_landed_is_indentation_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MEASURED 26 August 2026: `.strip()` on both sides discarded leading whitespace too, so
    a commit that only re-indents an existing block (moves it into a loop or a conditional,
    changing what it means) read as "already present". 25 unindented lines on HEAD, the same
    25 lines each indented by 4 spaces in the unit's commit, must NOT be classified as landed.
    """
    repo = tmp_path / "repo"
    _init_repo(repo)
    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)

    flat_lines = "\n".join(f"LINE_{i} = {i}" for i in range(25)) + "\n"
    indented_lines = "\n".join(f"    LINE_{i} = {i}" for i in range(25)) + "\n"
    _commit_file(repo, "mod.py", flat_lines, "feat: flat lines land on HEAD")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    _git(repo, "checkout", "-b", "reindented")
    sha = _commit_file(repo, "mod.py", indented_lines, "feat: same lines, now indented")
    _git(repo, "checkout", default)

    assert driver._content_landed(sha) is False, (
        "re-indented lines are not the same code and must not read as already landed"
    )


def test_escalation_banner_counts_retirements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """F: the banner grows when the classifier retires, it does not shrink."""
    driver = _load_driver()
    units = {f"E{i}": {"title": "held", "claims": []} for i in range(5)}
    units["T02"] = {"title": "landed", "claims": []}
    units["K01"] = {"title": "landed", "claims": []}
    remaining = {
        f"E{i}": f"CONFLICT cherry-picking {'abcdabcd'[:7]}{i} for E{i}"
        for i in range(5)
    }
    state: dict[str, object] = {
        "conflicts": {
            **remaining,
            "T02": "CONFLICT cherry-picking deadbee1 for T02",
            "K01": "CONFLICT cherry-picking deadbee2 for K01",
        },
        "force_done": [],
        "built": [],
        "done": [],
        "in_flight": {},
        "attempts": {},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "live_dispatchers", lambda _state: 1)
    monkeypatch.setattr(driver, "publish_if_ready", lambda _state, _green: "")
    monkeypatch.setattr(driver, "ready", lambda *_a, **_k: False)
    monkeypatch.setattr(driver.subprocess, "Popen", lambda *_a, **_k: None)
    monkeypatch.setattr(driver, "rebase_mergeable_worktrees", lambda *_a, **_k: None)
    # Isolates this test from whatever real unit worktrees the live driver has actually
    # created on disk in this checkout -- without this, main()'s built-unmerged scan
    # (WORKTREES / uid).exists() sees real T02/K01 worktrees and calls the real `sh()`,
    # which crashes because `subprocess.Popen` above is mocked to return None.
    monkeypatch.setattr(driver, "WORKTREES", tmp_path / "unit-worktrees")

    def fake_retest(current: dict[str, object]) -> int:
        for uid in ("T02", "K01"):
            cast("dict[str, str]", current.get("conflicts", {})).pop(uid, None)
            built = cast("list[str]", current.setdefault("built", []))
            if uid not in built:
                built.append(uid)
        return 2

    monkeypatch.setattr(driver, "retest_conflicts", fake_retest)
    monkeypatch.setattr(driver, "clear_retired_conflicts", lambda _state: None)
    monkeypatch.setattr(
        driver,
        "merge_unit_worktree",
        lambda uid: current_conflict(uid),
    )

    def current_conflict(uid: str) -> str:
        if uid in ("T02", "K01"):
            return "no worktree"
        return cast("dict[str, str]", state["conflicts"]).get(uid, "CONFLICT leftover")

    assert driver.main() == 0
    out = capsys.readouterr().out
    assert "5 escalated, 2 retired without review" in out


def test_an_originally_empty_unit_commit_lands_no_commit_at_all(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 27 August 2026, against real git, not a fake `sh`.

    Two units (W07 among them) generated dozens of zero-diff commits -- at one point 189 of
    the last 200 commits on this branch were two empty messages repeating. The cause is not
    the one first suspected. `--allow-empty` does NOT make git swallow a commit whose content
    is already in HEAD: that case still exits non-zero with "the previous cherry-pick is now
    empty", which the already-applied branch below handles correctly. What `--allow-empty`
    does is let a source commit that was empty *to begin with* be replayed as a fresh empty
    commit, exit 0, and be counted as `applied`.

    That one then cannot terminate. The replayed commit gets a new sha, so `HEAD..unit_head`
    still lists the original on the next tick, and there is no content for git to recognise as
    already present -- so it is cherry-picked again, and again, once per tick, forever.

    Dropping the flag routes an empty source commit into the same already-applied path the
    content case uses: git exits non-zero, the driver skips it, and nothing lands.
    """
    driver = _load_driver()

    root = tmp_path / "main"
    root.mkdir()

    def git(*args: str, cwd: Path = root) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        ).stdout

    git("init", "-q", "-b", "main", ".")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "Test")
    git("config", "commit.gpgsign", "false")
    (root / "f.txt").write_text("base\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "base")

    worktrees = tmp_path / "worktrees"
    worktrees.mkdir()
    unit = worktrees / "U01"
    git("worktree", "add", "-q", "-b", "unit", str(unit))
    # The one thing this unit ever committed carries no content.
    git("commit", "-q", "--allow-empty", "-m", "no-op from the harness", cwd=unit)

    monkeypatch.setattr(driver, "ROOT", root)
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(driver, "gate_merged_tree", lambda _touched, _baseline: "")

    before = git("rev-parse", "HEAD").strip()
    result = driver.merge_unit_worktree("U01")
    after = git("rev-parse", "HEAD").strip()

    assert after == before, (
        f"an empty unit commit must not land a commit; HEAD moved {before[:9]} -> {after[:9]}\n"
        f"driver said: {result}"
    )
    assert "applied 1" not in result, (
        f"a commit that changed nothing must not be reported as applied: {result!r}"
    )
    # And it must be reported, not silently dropped -- the driver has to be able to say why a
    # unit with commits merged nothing.
    assert "already" in result or "no commits" in result, result


class _Res:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _publish_harness(driver, monkeypatch, tmp_path, ident: str):
    """Drive `publish_if_ready` over a fake git, recording every command."""
    calls: list[list[str]] = []
    squash_sha = "a" * 40

    def fake_sh(args, **_kw):
        calls.append(list(args))
        if args[:3] == ["git", "rev-list", "--count"]:
            return _Res("7\n")
        if args[:3] == ["git", "var", "GIT_AUTHOR_IDENT"]:
            return _Res(f"{ident} 1787841088 +0100\n")
        if args[:2] == ["git", "commit-tree"]:
            return _Res(squash_sha + "\n")
        return _Res("")

    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "PUBLISH_STOP", tmp_path / "absent")
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    for script, _args in [
        (".github/scripts/check_foreign_identifiers.py", []),
        (".github/scripts/check_secrets.py", []),
        (".github/scripts/check_private_corpus.py", []),
        (".github/scripts/check_private_repo_names.py", []),
        (".github/scripts/check_generated_documents.py", ["--check"]),
    ]:
        path = tmp_path / script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return calls, squash_sha


def test_publication_never_pushes_the_branch_itself(tmp_path, monkeypatch) -> None:
    """MEASURED 27 August 2026, on a push that was about to happen.

    This path read `git push public HEAD:main`. What that would have sent was 294 commits of
    which 275 carried a `Signed-off-by` naming `fixture@example.invalid` -- an RFC 2606 address
    reserved so it can never resolve to anyone -- and 240 had no sign-off matching their author
    at all, because this worktree's local git config had been written by a test fixture.

    CONTRIBUTING.md requires a real name and email; the DCO workflow requires a sign-off
    matching the author. A sign-off is a certification of ORIGIN, so pushing the branch would
    have filed 240 false certifications in a public repository whose declared subject is
    provenance -- and publishing is one-way.

    Rewriting the commits was measured and rejected: 283 of 635 refs are based inside the
    unpublished range, with 455 worktrees checked out against them. So the tree is published
    under one commit whose author, committer and sign-off are the same real identity.
    """
    driver = _load_driver()
    calls, squash_sha = _publish_harness(
        driver, monkeypatch, tmp_path, "Joe Brown <joe@example.com>"
    )

    result = driver.publish_if_ready({}, True)

    pushes = [c for c in calls if c[:3] == ["git", "push", "public"]]
    assert pushes, f"nothing was pushed: {result}"
    assert ["git", "push", "public", "HEAD:main"] not in calls, (
        "the branch itself was pushed; every fixture-signed commit in it travels"
    )
    assert pushes[0][3] == f"{squash_sha}:main", pushes[0]

    tree = [c for c in calls if c[:2] == ["git", "commit-tree"]]
    assert tree and "public/main" in tree[0], (
        "the squash must be parented on public/main so the push fast-forwards"
    )
    assert "Signed-off-by: Joe Brown <joe@example.com>" in tree[0][-1], (
        "the published commit must carry a sign-off naming its own author"
    )
    assert any(c[:4] == ["git", "merge", "-s", "ours"] for c in calls), (
        "public/main must be recorded as an ancestor, or every later tick re-publishes"
    )


def test_publication_refuses_to_certify_origin_as_a_fixture(tmp_path, monkeypatch) -> None:
    """The identity that signs is the identity that is configured, so the check belongs here
    too -- a repository whose config has been poisoned must not publish at all, rather than
    publish one commit that certifies origin as somebody who does not exist."""
    driver = _load_driver()
    calls, _ = _publish_harness(
        driver, monkeypatch, tmp_path, "Fixture <fixture@example.invalid>"
    )

    result = driver.publish_if_ready({}, True)

    assert "REFUSED" in result, result
    assert not [c for c in calls if c[:3] == ["git", "push", "public"]], (
        "it published anyway under an identity that cannot certify anything"
    )


def test_an_open_receipt_does_not_kill_the_tick(tmp_path: Path) -> None:
    """A receipt another process still holds open must not reach __main__.

    MEASURED 27 August 2026. `preserve_review_artefacts` renamed the previous attempt's
    receipts aside with a bare `src.replace(dst)`. A reviewer subprocess that had not yet
    closed its stdout still held `N02-verify.out`, Windows refused the rename with WinError
    32, and the PermissionError travelled to `raise SystemExit(main())` -- killing a tick
    that had already dispatched work and merged nothing.

    The rename is history-keeping. It is allowed to fail; the tick is not.
    """
    driver = _load_driver()
    briefs = tmp_path / 'briefs-driver'
    briefs.mkdir()
    driver.BRIEFS = briefs

    held = briefs / 'N02-verify.out'
    held.write_text('first attempt receipt', encoding='utf-8')
    (briefs / 'N02-verdict.json').write_text('{}', encoding='utf-8')

    handle = open(held, 'a', encoding='utf-8')  # noqa: SIM115 - it must stay open
    try:
        driver.preserve_review_artefacts('N02', 2)  # must not raise
    finally:
        handle.close()

    # The receipt that COULD be renamed still was: one failure must not abandon the rest.
    assert (briefs / 'N02-verdict-1.json').exists()


def test_a_wsl_git_pointer_is_normalised_before_anything_prunes_it(tmp_path: Path) -> None:
    """The guard that stops a WSL dispatch from getting a live worktree deleted.

    MEASURED 27 August 2026: 37 of 41 built-and-unmerged units had lost their git metadata.
    cursor-agent runs under WSL, so its git rewrote each worktree's pointer to /mnt/c/...,
    Windows git could then not read the worktree, and the loop's disposal paths take an
    unreadable worktree for an empty one -- `worktree remove --force` skips its has-work
    guard and `worktree prune` drops the registration. The work becomes unmergeable forever.

    Rewriting the path back is lossless. Not rewriting it costs the unit.
    """
    spec = importlib.util.spec_from_file_location(
        "build_loop_test", ROOT / ".harness" / "build_loop.py"
    )
    assert spec is not None and spec.loader is not None
    loop = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loop
    spec.loader.exec_module(loop)

    root = tmp_path / 'cto'
    (root / '.harness' / 'unit-worktrees' / 'N02').mkdir(parents=True)
    (root / '.git').write_text(
        'gitdir: /mnt/c/Users/x/repo/.git/worktrees/cto' + chr(10), encoding='utf-8'
    )
    unit = root / '.harness' / 'unit-worktrees' / 'N02' / '.git'
    unit.write_text('gitdir: /mnt/c/Users/x/repo/.git/worktrees/N02' + chr(10), encoding='utf-8')
    healthy = root / '.harness' / 'unit-worktrees' / 'N03'
    healthy.mkdir()
    (healthy / '.git').write_text(
        'gitdir: C:/Users/x/repo/.git/worktrees/N03' + chr(10), encoding='utf-8'
    )

    loop.ROOT = root
    class _Log:
        def __init__(self) -> None: self.text = ''
        def write(self, s: str) -> None: self.text += s
        def flush(self) -> None: pass
    log = _Log()
    fixed = loop.normalise_wsl_gitdirs(log)

    assert fixed == 2, f'expected both WSL pointers rewritten, got {fixed}'
    assert 'C:/Users/x/repo' in (root / '.git').read_text(encoding='utf-8')
    assert '/mnt/' not in (root / '.git').read_text(encoding='utf-8')
    assert '/mnt/' not in unit.read_text(encoding='utf-8')
    # the already-correct one must be left exactly alone
    assert (healthy / '.git').read_text(encoding='utf-8').startswith('gitdir: C:/')
    assert 'normalised 2 WSL-form' in log.text


def test_the_resolve_lane_is_not_starved_by_builds() -> None:
    """Conflicts must be able to get a slot even when builds could fill the lane.

    MEASURED 28 August 2026: `done` sat at 31 for two hours while conflicts climbed from 8 to
    16 and exactly ONE resolver ran. Resolvers had just been made to count against the build
    lane -- correct, they had been running 34 at a time on a lane of 12 -- but the build loop
    still admitted on builds alone, so builds took all twelve slots first and resolve got the
    remainder, which with 116 units left to build is always zero.

    A conflict cannot clear itself and every failed merge adds one, so a starved resolve lane
    is a pile that only ever grows.
    """
    driver = _load_driver()

    # Nothing waiting: builds get the whole lane, which must not regress.
    assert driver.resolve_slots_reserved({}, []) == 0
    assert driver.resolve_slots_reserved(None, None) == 0

    # Conflicts waiting: slots are held back, capped at the reserve.
    assert driver.resolve_slots_reserved({'A': 'x'}, []) == 1
    many = {chr(65 + i): 'x' for i in range(16)}
    assert driver.resolve_slots_reserved(many, []) == driver.RESOLVE_RESERVE

    # A conflict already being resolved is not also reserved for.
    assert driver.resolve_slots_reserved({'A': 'x', 'B': 'x'}, ['A', 'B']) == 0

    # The reserve must leave real room: builds admitted against a full-but-for-reserve lane
    # have to shed, or the reservation is decorative.
    reserved = driver.resolve_slots_reserved(many, [])
    # builds occupying every non-reserved slot must be refused the next one
    builds = driver.MAX_BUILDS - reserved
    assert driver.admit_build(builds + reserved) is False, (
        'a build was admitted into a slot reserved for resolve'
    )
    # and one fewer build still fits
    assert driver.admit_build(builds - 1 + reserved) is True
