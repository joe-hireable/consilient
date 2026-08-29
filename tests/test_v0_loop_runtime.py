"""The loop runtime — V0-29, V0-25 and V0-30 — verified by artefact rather than by an
exit code. Every tick is written through `append()` and read back off the trajectory
file on disk, never off a return value. Exit 0 is not evidence that the work happened:
two dispatches on this machine returned 0 immediately and never started, and a third was
alive for twelve minutes with a 0-byte log because a runtime's interactive default was
waiting for a terminal, so `silent` is a distinct outcome from `completed` and liveness
is computed from bytes produced since the tick started rather than from a process
identity — which the loop's own source is forbidden by name from consulting, since a
process check reported that twelve-minute silence as healthy. The kill switch is checked
inside the tick and kills the tree, because a stop checked only between ticks cannot
stop a tick that never returns and a `subprocess` timeout does not reach grandchildren:
overruns of 10 to 269 seconds past the deadline have been measured here. A standing stop
is not lifted by a restart, or a scheduled restart would lift the kill switch by itself.
A real loop is killed as a tree mid-tick and restarted, and the side-effect file still
holds exactly one mark — at-most-once, not exactly-once, and the docstring says which.
Gate B still governs where this may point: a workspace that is not this repository, or a
command reaching outside it, is refused."""

import subprocess
import sys
from pathlib import Path
import pytest
from consilient import events as events_mod
from v0_invariants_helpers import (
    _loop,
    _loop_events,
    _loop_runner,
    _spend_scripts,
    _workspace,
)


def _wait_for(predicate, seconds=60):
    import time

    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if predicate():
            return True
        time.sleep(0.1)
    return False


def test_every_loop_tick_is_recorded_through_the_single_append_writer(tmp_path):
    """V0-29. A loop whose activity is invisible to the trajectory is worthless here.

    Both halves matter: the events are present, and they came through `append()`. 92 of the
    93 events in the real trajectory were written straight to the file by something else,
    which is how three events V0-18 forbids reached an authoritative record whose sole
    writer rejects them. `bypassed()` is the check that would have caught it.
    """
    from consilient import loop as loop_mod

    runner = _loop_runner()
    loop = _loop(tmp_path, "print('tick')", max_ticks=2)

    runner.run(loop)

    kinds = [(e.kind, e.data["tick"]) for e in _loop_events(loop.log_dir)]
    assert kinds == [
        (loop_mod.TICK_STARTED, 1),
        (loop_mod.TICK_FINISHED, 1),
        (loop_mod.TICK_STARTED, 2),
        (loop_mod.TICK_FINISHED, 2),
        (loop_mod.LOOP_STOPPED, 3),
    ]
    assert events_mod.bypassed(loop.log_dir) == [], "a tick was written past append()"
    for finished in _loop_events(loop.log_dir, loop_mod.TICK_FINISHED):
        assert finished.data["outcome"] == "completed"
        assert finished.data["produced_bytes"] > 0


def test_a_tick_that_exits_zero_without_producing_anything_is_recorded_as_silent(
    tmp_path,
):
    """R1 and R13. Exit 0 is not evidence that the work happened.

    Two dispatches on this machine returned 0 immediately and never started; a third was
    alive for twelve minutes with a 0-byte log because a runtime's interactive default was
    waiting for a terminal. `silent` is a distinct outcome from `completed` so that the
    liveness signal is about produced work rather than about a return code.
    """
    from consilient import loop as loop_mod

    runner = _loop_runner()
    loop = _loop(tmp_path, "pass")

    result = runner.run(loop)

    finished = _loop_events(loop.log_dir, loop_mod.TICK_FINISHED)[0]
    assert finished.data["exit_code"] == 0
    assert finished.data["produced_bytes"] == 0
    assert finished.data["outcome"] == "silent"
    assert result["ticks_silent"] == 1
    assert result["working"] is False


def test_a_killed_loop_loses_no_record_and_never_re_executes_the_tick(tmp_path):
    """V0-29, verified by artefact rather than by an exit code.

    A real loop process is killed as a tree, mid-tick, after its side effect has run. Two
    properties are then read off the trajectory file on disk — never off a return value:

    1. the intent record for the interrupted tick is still there, because it was appended
       and closed before the side effect started;
    2. restarting does not run that tick again. The side-effect file still holds exactly
       one mark, and the tick is recorded as abandoned with its outcome unknown.

    What is NOT guaranteed, and is deliberately not asserted: that the outcome of the
    interrupted tick was recorded. The process died before it could write one. This is
    at-most-once, not exactly-once.
    """
    from consilient.loop import TICK_ABANDONED, TICK_FINISHED, TICK_STARTED

    runner = _loop_runner()
    root, log = _workspace(tmp_path)
    marker = root / "side-effect.txt"
    slow = (
        "import pathlib, sys, time\n"
        "target = pathlib.Path(sys.argv[1])\n"
        "target.write_text((target.read_text() if target.exists() else '') + 'x')\n"
        "print('working', flush=True)\n"
        "time.sleep(600)\n"
    )
    argv = [
        sys.executable,
        str(Path("scripts/run_loop.py").resolve()),
        "--root",
        str(root),
        "--log",
        str(log),
        "--name",
        "probe",
        "--interval",
        "0",
        "--timeout",
        "600",
        "--max-ticks",
        "5",
        "--",
        sys.executable,
        "-c",
        slow,
        str(marker),
    ]
    first = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert _wait_for(lambda: marker.exists()), "the tick never ran"
    finally:
        runner.kill_tree(first)
        first.wait(timeout=60)

    started = _loop_events(log, TICK_STARTED)
    assert [e.data["tick"] for e in started] == [1], "the intent record did not survive"
    assert _loop_events(log, TICK_FINISHED) == [], (
        "the tick was not actually interrupted"
    )
    assert marker.read_text(encoding="utf-8") == "x"

    argv[argv.index("--max-ticks") + 1] = "1"
    second = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    assert marker.read_text(encoding="utf-8") == "x", (
        f"the interrupted tick was executed a second time: {second.stdout}"
    )
    assert [e.data["tick"] for e in _loop_events(log, TICK_STARTED)] == [1]
    abandoned = _loop_events(log, TICK_ABANDONED)
    assert [e.data["tick"] for e in abandoned] == [1]
    assert abandoned[0].data["outcome"] == "unknown"


def test_the_stop_file_ends_a_tick_that_is_already_wedged(tmp_path):
    """The kill switch has to work when the loop is stuck, or it is decoration.

    A stop checked only between ticks cannot stop a tick that never returns, and a
    `subprocess` timeout does not reach grandchildren — overruns of 10 to 269 seconds past
    the deadline have been measured on this machine. The stop is checked inside the tick
    and the kill is a tree kill.
    """
    import threading

    from consilient import loop as loop_mod

    runner = _loop_runner()
    loop = _loop(
        tmp_path,
        "import time\nprint('up', flush=True)\ntime.sleep(600)\n",
        timeout_s=600.0,
    )

    thread = threading.Thread(target=runner.run, args=(loop,), daemon=True)
    thread.start()
    try:
        assert _wait_for(
            lambda: loop.transcript.exists() and loop.transcript.stat().st_size > 0
        ), "the wedged tick never produced its first byte"

        live = loop_mod.status(loop)
        assert live["in_flight"] is True and live["ticks_finished"] == 0
        assert live["working"] is True and live["bytes_since_tick_started"] > 0

        loop.stop_file.parent.mkdir(parents=True, exist_ok=True)
        loop.stop_file.write_text("stop\n", encoding="utf-8")
        thread.join(timeout=120)
        assert not thread.is_alive(), "the stop file did not end a wedged tick"
    finally:
        loop.stop_file.unlink(missing_ok=True)

    finished = _loop_events(loop.log_dir, loop_mod.TICK_FINISHED)
    assert [e.data["outcome"] for e in finished] == ["killed"]
    stopped = _loop_events(loop.log_dir, loop_mod.LOOP_STOPPED)
    assert stopped and "mid-tick" in stopped[0].data["reason"]


def test_a_standing_stop_is_not_cleared_by_restarting_the_loop(tmp_path):
    """A kill switch a scheduled restart lifts by itself is not a kill switch."""
    runner = _loop_runner()
    loop = _loop(tmp_path, "print('tick')")
    loop.stop_file.parent.mkdir(parents=True, exist_ok=True)
    loop.stop_file.write_text("stop\n", encoding="utf-8")

    with pytest.raises(runner.LoopError, match="a stop is in force"):
        runner.run(loop)

    assert _loop_events(loop.log_dir) == []


def test_loop_liveness_is_computed_from_produced_work_not_a_process_identity(tmp_path):
    """V0-25, which the specification has declared since 19 August with no check.

    No process exists anywhere in this test. The loop reports `working` from the bytes the
    current tick has put on its transcript and from the outcomes already recorded, so a
    live process producing nothing reads as not working — which is the state a process
    check reported as healthy for twelve minutes on this machine.

    Honest limit: this covers V0-25's first clause. "A terminal artefact record outranks a
    stale liveness signal" and "detection escalates rather than terminating" remain
    unenforced.
    """
    import ast
    import inspect

    from consilient import loop as loop_mod

    loop = _loop(tmp_path, "pass")
    loop.log_dir.mkdir(parents=True, exist_ok=True)
    loop.transcript.parent.mkdir(parents=True, exist_ok=True)
    loop.transcript.write_text("", encoding="utf-8")

    assert loop_mod.status(loop)["working"] is False

    loop_mod.record(loop, loop_mod.TICK_STARTED, 1, {"transcript_bytes": 0})
    in_flight = loop_mod.status(loop)
    assert in_flight["in_flight"] is True
    assert in_flight["working"] is False, in_flight["reason"]
    assert "produced nothing" in in_flight["reason"]

    with loop.transcript.open("ab") as sink:
        sink.write(b"progress\n")
    producing = loop_mod.status(loop)
    assert producing["working"] is True
    assert producing["bytes_since_tick_started"] == len(b"progress\n")

    # Names, not prose: the docstring is allowed to say the word, the code is not.
    tree = ast.parse(inspect.getsource(loop_mod))
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    process_shaped = {
        name
        for name in identifiers
        if "pid" in name.lower() or "process" in name.lower()
    }
    assert not process_shaped, (
        f"the loop resolves liveness from a process identity: {sorted(process_shaped)}"
    )


def test_the_loop_refuses_a_workspace_that_is_not_this_repository(tmp_path):
    """V0-30. Gate B forbids pointing the harness at any repository other than this one."""
    import dataclasses

    from consilient import loop as loop_mod
    from consilient.loop import Loop

    elsewhere = tmp_path / "another-repo"
    (elsewhere / "src").mkdir(parents=True)
    workspace = tmp_path / "repo"
    workspace.mkdir()
    foreign = Loop(
        name="probe",
        root=elsewhere,
        log_dir=elsewhere / "log",
        command=(sys.executable, "-c", "pass"),
        interval_s=0.0,
        timeout_s=60.0,
    )

    refused = loop_mod.refusal(foreign)
    assert refused is not None and "Gate B" in refused and "V0-30" in refused

    reaching_out = dataclasses.replace(
        _loop(workspace, "pass"),
        command=(sys.executable, "-c", "pass", str(elsewhere / "src")),
    )
    outward = loop_mod.refusal(reaching_out)
    assert outward is not None and "outside the workspace" in outward


def test_a_command_that_will_not_start_is_refused_not_retried_forever(tmp_path):
    """R12. A refusal is a repairable dispatch fault, and it is not a failure.

    Without this the loop would spin: a mistyped command raises on every `Popen`, the tick
    is recorded as started and never settled, and an always-on runtime turns into an
    always-on crash loop that fills the trajectory with abandoned ticks.
    """
    import dataclasses

    from consilient import loop as loop_mod

    runner = _loop_runner()
    loop = dataclasses.replace(
        _loop(tmp_path, "pass"), command=("consilient-no-such-executable",)
    )

    runner.run(loop)

    finished = _loop_events(loop.log_dir, loop_mod.TICK_FINISHED)
    assert [e.data["outcome"] for e in finished] == ["refused"]
    stopped = _loop_events(loop.log_dir, loop_mod.LOOP_STOPPED)
    assert stopped and "will not start" in stopped[0].data["reason"]


def test_only_one_instance_of_a_loop_can_hold_it_at_a_time(tmp_path):
    """The other half of no-double-execution: two supervisors are two side effects.

    The lock is an OS lock rather than a file that exists, because a lock a crash leaves
    behind would stop the loop restarting — which is the failure mode an always-on runtime
    can least afford. `test_a_killed_loop_...` restarts after a kill and proves it.
    """
    runner = _loop_runner()
    loop = _loop(tmp_path, "pass")
    loop.log_dir.mkdir(parents=True, exist_ok=True)

    with runner.single_instance(loop):
        with pytest.raises(runner.LoopError, match="already holds"):
            with runner.single_instance(loop):
                pass  # pragma: no cover - the guard above is what is under test

    with runner.single_instance(loop):
        pass  # the lock is released when the holder lets go


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)
