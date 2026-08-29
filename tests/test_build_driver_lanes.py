"""Which units are allowed to occupy the lane at the same time.

Two units that touch the same subsystem are serialised rather than dispatched together,
on the Jaccard overlap of their claims. The threshold is environment-configurable, and
the firing rate against the real plan is held below five per cent of all claim-sharing
pairs — a serialisation rule that fires on everything is a stop, not a schedule. The
plan is instance data and is not tracked (Z04), so the checks that read it as evidence
skip rather than fail on a fresh checkout; the two candidates the rule was written for,
N03 and T02, are named because they are the case it was measured on.

Holding a unit back only pays if its work is still merged when the lane clears, so the
same tick rebases a quiescent worktree before merging it and leaves a live dispatcher's
worktree alone — rebasing under a running agent is how a merge loses commits.

The resolve lane is the other half of admission. MEASURED 28 August 2026: `done` sat at
31 for two hours while conflicts climbed from 8 to 16 and exactly one resolver ran.
Resolvers had just been made to count against the build lane — correct, they had been
running 34 at a time on a lane of 12 — but the loop still admitted on builds alone, so
builds took all twelve slots first and resolve got the remainder, which with 116 units
left to build is always zero. A conflict cannot clear itself and every failed merge adds
one, so a starved resolve lane is a pile that only ever grows. The reserve has to leave
real room: a build admitted into a reserved slot makes the reservation decorative, which
is why admission is asserted against the reserve and not merely the count."""


import json
from itertools import combinations
from pathlib import Path
import pytest
from build_driver_helpers import (
    _load_driver,
)

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
    assert driver.resolve_slots_reserved({"A": "x"}, []) == 1
    many = {chr(65 + i): "x" for i in range(16)}
    assert driver.resolve_slots_reserved(many, []) == driver.RESOLVE_RESERVE

    # A conflict already being resolved is not also reserved for.
    assert driver.resolve_slots_reserved({"A": "x", "B": "x"}, ["A", "B"]) == 0

    # The reserve must leave real room: builds admitted against a full-but-for-reserve lane
    # have to shed, or the reservation is decorative.
    reserved = driver.resolve_slots_reserved(many, [])
    # builds occupying every non-reserved slot must be refused the next one
    builds = driver.MAX_BUILDS - reserved
    assert driver.admit_build(builds + reserved) is False, (
        "a build was admitted into a slot reserved for resolve"
    )
    # and one fewer build still fits
    assert driver.admit_build(builds - 1 + reserved) is True
