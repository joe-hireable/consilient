"""Checks for the two instrument defects EXP-31 demonstrated on 20 August 2026.

Both run against real processes, not mocks. A mock of `subprocess` would have passed against
the broken implementation, because the defect is precisely that the real thing does not
behave the way the API suggests.

Sleeps are deliberately short. The first version of this file used 600-second sleeps — an
accurate reproduction of the defect and a test suite nobody would ever run. A check that
takes ten minutes is a check that gets skipped.

Run: python -m pytest docs/10-research/experiments/exp31/test_run_exp31.py -q
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

CAP_S = 2
GRANDCHILD_S = 12
CHILD_S = 30

# A child that spawns a grandchild inheriting its stdout, then sleeps. The grandchild holds
# the pipe open after the child is killed. This is the shape a Codex invocation takes, and it
# is what makes `subprocess.run(timeout=...)` fail to bound anything.
CHILD = (
    "import subprocess,sys,time;"
    f"subprocess.Popen([sys.executable,'-c','import time;time.sleep({GRANDCHILD_S})']);"
    f"time.sleep({CHILD_S})"
)


def _spawn() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", CHILD],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **({} if os.name == "nt" else {"start_new_session": True}),
    )


def test_the_broken_pattern_really_does_overrun():
    """The defect itself. If this ever stops failing, the fix is no longer needed.

    `subprocess.run(capture_output=True, timeout=T)` kills the direct child, then blocks in
    communicate() draining pipes the surviving grandchild still holds open. On 20 Aug 2026
    that turned a 240 s cap into a 2,011 s attempt — 8.4x.
    """
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [sys.executable, "-c", CHILD],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=CAP_S,
        )
    overrun = time.monotonic() - started - CAP_S
    assert overrun > 2.0, (
        f"expected the broken pattern to overrun its {CAP_S}s cap while the grandchild held "
        f"the pipe; it returned only {overrun:.2f}s past it. If this now passes cleanly, "
        "Python's behaviour has changed and kill_tree() should be re-examined, not trusted."
    )


def test_kill_tree_bounds_the_wait():
    """The fix. The whole tree dies, so the pipes close and communicate() returns promptly."""
    from run_exp31 import kill_tree

    proc = _spawn()
    started = time.monotonic()
    try:
        proc.communicate(timeout=CAP_S)
        pytest.fail(f"the child should not have exited within {CAP_S}s")
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.communicate(timeout=30)
    elapsed = time.monotonic() - started
    assert elapsed < GRANDCHILD_S, (
        f"kill_tree did not bound the wait: {elapsed:.1f}s against a {CAP_S}s cap, which is "
        f"past the grandchild's own {GRANDCHILD_S}s lifetime. The pipe is still held — that "
        "is the 20 Aug defect, unfixed."
    )
    assert proc.poll() is not None


def test_a_second_runner_refuses_to_start(tmp_path, monkeypatch):
    """The 20 Aug failure: two runners, each rewriting the whole file, last write wins."""
    import run_exp31

    monkeypatch.setattr(run_exp31, "LOCK", tmp_path / "run.lock")
    assert run_exp31.acquire_lock("run-a", cap_s=3600) is True
    assert run_exp31.acquire_lock("run-b", cap_s=3600) is False, (
        "a second runner started alongside a live one — exactly the 20 Aug incident"
    )
    held = json.loads((tmp_path / "run.lock").read_text(encoding="utf-8"))
    assert held["run_id"] == "run-a" and held["pid"] == os.getpid()

    run_exp31.release_lock()
    assert run_exp31.acquire_lock("run-c", cap_s=3600) is True
    run_exp31.release_lock()


def test_a_lock_older_than_the_wall_clock_cap_is_taken_over(tmp_path, monkeypatch):
    """A crashed runner must not block the rig forever."""
    import run_exp31

    lock = tmp_path / "run.lock"
    monkeypatch.setattr(run_exp31, "LOCK", lock)
    lock.write_text(
        json.dumps(
            {"pid": 999999, "run_id": "dead", "started_epoch": time.time() - 7200}
        ),
        encoding="utf-8",
    )
    assert run_exp31.acquire_lock("run-new", cap_s=3600) is True
    assert json.loads(lock.read_text(encoding="utf-8"))["run_id"] == "run-new"
    run_exp31.release_lock()


def test_a_corrupt_lock_does_not_wedge_the_runner(tmp_path, monkeypatch):
    import run_exp31

    lock = tmp_path / "run.lock"
    monkeypatch.setattr(run_exp31, "LOCK", lock)
    lock.write_text("{not json", encoding="utf-8")
    assert run_exp31.acquire_lock("run-new", cap_s=3600) is True
    run_exp31.release_lock()
