"""BU-2 / N02: the agent writes the started line, or it never started.

N00 counted any child byte in the run directory as a start. That is startsecs by another
name — the wrong process was healthy because it wrote something, somewhere — and
`stdout.txt` is the wrapper's transcript, not a notification from the agent. s6's
notification-fd is mandatory for the same reason: surviving the start window is not a
start. [cited, skarnet.org/software/s6/servicedir.html]

So the four-field `started` record appears only when the agent itself has appended a
line to the *declared* path, it is idempotent once written, and absence of it inside the
window is a start failure that does not consume an attempt — an infrastructure death is
not the unit's fault.

The started line proves start, not health. A dispatch that notifies and then produces
nothing is `stalled`, not `started`-and-healthy; adopting startsecs would call it
healthy because the process survived. [measured, ADR-0034] The two detectors are
therefore kept honest against each other here rather than in separate modules: the
silent-exit case must be a start failure and no stall, the hang case a stall and no
start failure, and the scheduled command must print `stalled` with `start_failed: 0`
when it is the second."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from supervision_helpers import (
    NOW,
    _dirs,
    _live,
    _open,
    _run_dir,
    _script,
)


def _declare(script, runs: Path, run_id: str, *, artefact: str = "started") -> None:
    script.write_expected(
        runs,
        run_id=run_id,
        arm="codex",
        unit="N02",
        expected_artefact=artefact,
        start_window_s=script.START_WINDOW_S,
        progress_deadline_s=60,
    )


def test_agent_that_exits_before_writing_started_is_a_start_failure(tmp_path):
    """BU-2 / N02. Absence of the agent-written line within the window is a
    start failure, and an infrastructure death does not consume an attempt.

    s6's notification-fd is mandatory: surviving the start window is not a
    start. [cited, skarnet.org/software/s6/servicedir.html]
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(log, run_id="silent-exit", cwd=tmp_path, opened=NOW - timedelta(minutes=10))
    _run_dir(runs, "silent-exit", transcript=b"")
    _declare(script, runs, "silent-exit")

    failures = script.start_failures(_live(log), runs_dir=runs, now=NOW)

    assert [item.run_id for item in failures] == ["silent-exit"]
    one = failures[0]
    assert one.signal == "no started line within the start window"
    assert one.threshold_s == script.START_WINDOW_S
    assert one.observed_bytes == 0
    assert one.action == "diagnose"
    assert one.consumes_attempt is False
    assert script.stall_failures(_live(log), runs_dir=runs, now=NOW) == ()


def test_bytes_on_an_undeclared_path_are_not_a_start(tmp_path):
    """N00 counted any child byte in the run directory as a start. N02 does not.

    stdout.txt is the wrapper's transcript, not the declared started path. A
    dispatcher that treats it as notification re-creates startsecs: the wrong
    process was healthy because it wrote something, somewhere.
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(log, run_id="misdirected", cwd=tmp_path, opened=NOW - timedelta(minutes=10))
    _run_dir(runs, "misdirected", transcript=b"thinking about the brief\n")
    _declare(script, runs, "misdirected", artefact="started")

    failures = script.start_failures(_live(log), runs_dir=runs, now=NOW)

    assert [item.run_id for item in failures] == ["misdirected"]
    assert failures[0].consumes_attempt is False
    assert script.write_started(runs, "misdirected", now=NOW) is None
    assert not json.loads((runs / "misdirected.json").read_text(encoding="utf-8")).get(
        "started"
    )


def test_write_started_is_silent_until_the_agent_writes_a_line(tmp_path):
    """The four-field record is written by the wrapper, never by goodwill.

    Surviving the timer does not populate `started`. The field appears only
    when the agent itself has appended one line to the declared path.
    """
    script = _script()
    _log, runs = _dirs(tmp_path)
    _run_dir(runs, "waiting", transcript=b"")
    _declare(script, runs, "waiting")

    assert script.started_line_in(runs / "waiting", "started") is None
    assert script.write_started(runs, "waiting", now=NOW) is None
    payload = json.loads((runs / "waiting.json").read_text(encoding="utf-8"))
    assert "started" not in payload
    assert "expected" in payload


def test_write_started_records_the_agent_line_and_is_idempotent(tmp_path):
    script = _script()
    _log, runs = _dirs(tmp_path)
    _run_dir(runs, "ready", transcript=b"")
    _declare(script, runs, "ready")
    (runs / "ready" / "started").write_text("agent ready\n", encoding="utf-8")

    first = script.write_started(runs, "ready", now=NOW)
    later = NOW + timedelta(minutes=5)
    second = script.write_started(runs, "ready", now=later)

    assert first is not None and second is not None
    assert first == second
    payload = json.loads((runs / "ready.json").read_text(encoding="utf-8"))
    started = payload["started"]
    assert started["run_id"] == "ready"
    assert started["artefact"] == "started"
    assert started["line"] == "agent ready"
    assert started["at"] == NOW.isoformat()
    assert script.started_line_in(runs / "ready", "started") == "agent ready"


def test_agent_that_writes_then_hangs_is_stalled_not_started_and_healthy(tmp_path):
    """The started line proves start, not health.

    A dispatch that notifies and then produces nothing is `stalled`, not
    `started`-and-healthy. Adopting startsecs would call this healthy because
    the process survived. [measured, ADR-0034]
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(log, run_id="hung", cwd=tmp_path, opened=NOW - timedelta(minutes=10))
    _run_dir(runs, "hung", transcript=b"")
    _declare(script, runs, "hung")
    (runs / "hung" / "started").write_text("agent ready\n", encoding="utf-8")
    script.write_started(runs, "hung", now=NOW - timedelta(minutes=9))

    live = _live(log)
    assert script.start_failures(live, runs_dir=runs, now=NOW) == ()
    stalls = script.stall_failures(live, runs_dir=runs, now=NOW)
    assert [item.run_id for item in stalls] == ["hung"]
    one = stalls[0]
    assert one.signal == "no progress after started"
    assert one.threshold_s == 60
    assert one.action == "diagnose"
    assert one.observed_s == pytest.approx(600.0)


def test_supervise_reports_a_hang_after_start_as_stalled(tmp_path, capsys):
    script = _script()
    log, runs = _dirs(tmp_path)
    opened = datetime.now(timezone.utc) - timedelta(minutes=10)
    _open(log, run_id="hung0", cwd=tmp_path, opened=opened)
    _run_dir(runs, "hung0", transcript=b"")
    _declare(script, runs, "hung0")
    (runs / "hung0" / "started").write_text("agent ready\n", encoding="utf-8")

    code = script.main(["--supervise", "--log", str(log), "--runs", str(runs)])

    assert code == 1
    out = capsys.readouterr().out
    assert "stalled" in out
    assert "hung0" in out
    assert "start_failed: 0" in out
    payload = json.loads((runs / "hung0.json").read_text(encoding="utf-8"))
    assert payload["started"]["line"] == "agent ready"
