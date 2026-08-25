"""Regression checks for the local build driver."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver():
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

    assert state["total_restarts"] == {"U01": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]}
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

    assert "ESCALATION -- U01 exceeded the restart intensity limit" in capsys.readouterr().out
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
    assert "self_heal" in defined, "self_heal is gone; this test guards its call, not its name"

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
    ), "self_heal is called outside the tick loop; a startup-only repair cannot fix a fault that appears after startup"


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

    _write_err(briefs, "U2", "Traceback (most recent call last):\nRuntimeError: first\n")
    assert [row[0] for row in driver.crashed_dispatches(state)] == ["U2"]
    assert driver.crashed_dispatches(state) == []

    # A later dispatch overwrites the file with a different failure: that IS new evidence.
    _write_err(
        briefs, "U2", "Traceback (most recent call last):\nValueError: second and different\n"
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
    ), "build_loop.main() does not prune inside the tick loop; accumulation broke provisioning once already"


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

    assert not driver.ready(
        "T02", units["T02"], set(units), units, in_flight={"N03"}
    )
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
        if not driver.ready(
            left, units[left], set(units), units, in_flight={right}
        )
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
        lambda uid, quiescent=False: calls.append(("merge", uid, quiescent))
        or "no commits",
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


def _verdict_fixture(tmp_path, monkeypatch, *, receipt_attempt, expected_attempt,
                     receipt_artefact, expected_artefact, current_artefact,
                     verdict="SOUND", findings=None):
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: current_artefact)
    (briefs / "U01-verdict.json").write_text(
        json.dumps({
            "v": 1, "unit": "U01", "artefact": receipt_artefact,
            "attempt": receipt_attempt, "verdict": verdict,
            "findings": findings if findings is not None else [],
        }),
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
        tmp_path, monkeypatch,
        receipt_attempt=2, expected_attempt=3,
        receipt_artefact="a" * 64, expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "SOUND", "a verdict about the current artefact must not be lost to a counter"


def test_a_verdict_about_a_different_artefact_is_still_refused(
    tmp_path: Path, monkeypatch
) -> None:
    """The binding that matters is unchanged: a verdict about other code is not evidence about
    this code, whatever its attempt number says."""
    outcome, _ = _verdict_fixture(
        tmp_path, monkeypatch,
        receipt_attempt=3, expected_attempt=3,
        receipt_artefact="b" * 64, expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "receipt_mismatched"


def test_a_verdict_is_refused_when_the_tree_has_moved_under_the_expectation(
    tmp_path: Path, monkeypatch
) -> None:
    """Both sides are still checked. If the unit's identity re-derived from the tree no longer
    equals what the review was told to judge, the verdict is stale and refused."""
    outcome, _ = _verdict_fixture(
        tmp_path, monkeypatch,
        receipt_attempt=3, expected_attempt=3,
        receipt_artefact="a" * 64, expected_artefact="a" * 64,
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
    assert driver.SUITE_TIMEOUT_S >= 600, "shorter than a clean run would fail closed constantly"
    assert driver.SUITE_TIMEOUT_S <= 1800, "must fire well before the 3000s tick abandonment"
