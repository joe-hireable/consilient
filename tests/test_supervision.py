"""The cheap supervision floor: a dead dispatch is found from its artefact.

Unit N00 of the build plan, which is BU-0 of
`docs/20-design/supervision-escalation-and-sessions-2026-08-23.md`.

The failure it exists to stop is F-13 in
`docs/00-context/orchestration-failure-modes-2026-08-23.md`: six of six dispatches
died at startup seconds after the scheduler printed that the work had been sent, and
the loop went on reporting itself busy over work that was already dead. The detection
channel was a person looking at a usage graph. [measured, 23 August 2026]

Every check here holds ADR-0034: liveness is never resolved from a process identity, a
terminal record outranks a stale liveness signal, and detection diagnoses rather than
terminates. The last of those is why `start_failures` returns records and kills nothing.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import coordination
from consilient.events import read_all
from consilient.harness import harness_by_id, now_ts, record_outcome

DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"

NOW = datetime(2026, 8, 23, 21, 0, 0, tzinfo=timezone.utc)


def _script():
    name = "consilient_dispatch_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _dirs(tmp_path: Path) -> tuple[Path, Path]:
    log = tmp_path / "log"
    runs = tmp_path / "dispatch"
    log.mkdir()
    runs.mkdir()
    return log, runs


def _open(log: Path, *, run_id: str, cwd: Path, opened: datetime) -> None:
    coordination.open_claim(
        log,
        run_id=run_id,
        paths=[f"src/{run_id}.py"],
        cwd=cwd,
        timeout_s=600,
        harness="codex",
        now=opened,
    )


def _run_dir(runs: Path, run_id: str, *, transcript: bytes) -> Path:
    run_dir = runs / run_id
    run_dir.mkdir(exist_ok=True)
    # The dispatcher writes these before the child is spawned. They are its evidence
    # of having asked, never the child's evidence of having answered.
    (run_dir / "brief.md").write_text("a long brief\n" * 500, encoding="utf-8")
    (run_dir / "recall.md").write_text("a recall pack\n" * 50, encoding="utf-8")
    (run_dir / "stdout.txt").write_bytes(transcript)
    (run_dir / "stderr.txt").write_bytes(b"")
    return run_dir


def _live(log: Path, *, now: datetime = NOW) -> tuple[coordination.Claim, ...]:
    events, _rejected = read_all(log)
    return coordination.live_claims(events, now=now)


def test_six_dispatches_dead_at_startup_are_reported_without_a_person_looking(tmp_path):
    """F-13, replayed. Six open claims, six run directories, not one child byte.

    The brief and the recall pack are on disk and are large; they are the dispatcher's
    own output. If they counted as progress every dead dispatch would read healthy,
    which is the 23 August failure exactly.
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    opened = NOW - timedelta(minutes=10)
    for index in range(6):
        _open(log, run_id=f"dead{index}", cwd=tmp_path, opened=opened)
        _run_dir(runs, f"dead{index}", transcript=b"")

    failures = script.start_failures(_live(log), runs_dir=runs, now=NOW)

    assert sorted(item.run_id for item in failures) == [
        f"dead{index}" for index in range(6)
    ]
    one = failures[0]
    # ADR-0034 section 6: signal, threshold, observed value, action, or an operator
    # cannot dispute the decision from the record alone.
    assert one.signal == "no artefact within the start window"
    assert one.threshold_s == script.START_WINDOW_S
    assert one.observed_bytes == 0
    assert one.observed_s == pytest.approx(600.0)
    assert one.harness == "codex"
    # ADR-0034 section 3: killing is the irreversible half and needs its own authority.
    assert one.action == "diagnose"


def test_a_healthy_replay_reports_nothing(tmp_path):
    """The expensive error is a watchdog acting on live work, not a slow supervisor.

    ADR-0034 collected five production systems that made it: Airflow, LangGraph,
    Celery, Ray and Kubernetes. [cited, ADR-0034]
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    opened = NOW - timedelta(minutes=10)
    for index in range(6):
        _open(log, run_id=f"live{index}", cwd=tmp_path, opened=opened)
        _run_dir(runs, f"live{index}", transcript=b"thinking about the brief\n")

    assert script.start_failures(_live(log), runs_dir=runs, now=NOW) == ()


def test_a_dispatch_inside_its_start_window_is_not_yet_a_failure(tmp_path):
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(log, run_id="young", cwd=tmp_path, opened=NOW - timedelta(seconds=30))
    _run_dir(runs, "young", transcript=b"")

    assert script.start_failures(_live(log), runs_dir=runs, now=NOW) == ()


def test_a_terminal_record_outranks_the_absent_artefact(tmp_path):
    """The Airflow regression: a task that had already logged its own clean exit was
    marked failed, because zombie detection consulted a stale liveness signal instead
    of the task's terminal record. [cited, ADR-0034]

    V0-25 has declared this clause since 19 August with no check on the dispatch path;
    `tests/test_v0_invariants.py` records it as unenforced. This is the check.
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    opened = NOW - timedelta(minutes=10)
    _open(log, run_id="finished", cwd=tmp_path, opened=opened)
    _run_dir(runs, "finished", transcript=b"")
    codex = harness_by_id("codex")
    assert codex is not None
    record_outcome(
        log,
        # Stamped from the clock, as `events.append` requires; the claim's own
        # `opened_at` is what carries the fixture's chosen occurrence time.
        ts=now_ts(),
        run_id="finished",
        task="a task",
        cwd=str(tmp_path),
        harness=codex,
        status="ok",
        reason="produced an artefact",
        exit_code=0,
        artefact_bytes=12,
        diff_bytes=0,
        timed_out=False,
        duration_s=1.0,
        command=["codex"],
    )

    assert script.start_failures(_live(log), runs_dir=runs, now=NOW) == ()


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_the_working_tree_and_the_commit_log_rescue_a_run_with_no_transcript(tmp_path):
    """The transcript alone is not enough, and this is measured, not feared.

    The first version of this unit was run against the live trajectory on 23 August
    2026 and flagged six open dispatches, one of which was the run building this unit
    — alive, working, and 46 minutes into a transcript still holding zero bytes. Of
    224 real run directories, 195 carry a transcript and 29 do not, and the empty ones
    are the open and the crashed alike. A live `claude -p` child therefore writes
    nothing to its transcript until it exits, so the transcript is a terminal signal
    and not a progress one. [measured, 23 August 2026]

    So the progress test is Hadoop's disjunction over the three artefacts this
    repository already produces: the transcript, the working tree, the commits. A run
    that has none of the three has produced nothing observable, and that is the only
    case this reports.
    """
    script = _script()
    log, runs = _dirs(tmp_path)

    # The real clock throughout: a commit carries a real committer date and
    # `git log --since` compares against it, so the claim must be stamped on the same
    # clock. A fixed NOW here would pass or fail depending on the wall time the suite
    # happens to run at, which is the sort of test that lies later.
    now = datetime.now(timezone.utc)
    before = (now - timedelta(hours=2)).isoformat()

    def git(repo: Path, *args: str, dated: str | None = None) -> None:
        env = dict(os.environ)
        if dated is not None:
            env["GIT_AUTHOR_DATE"] = dated
            env["GIT_COMMITTER_DATE"] = dated
        done = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        assert done.returncode == 0, done.stderr

    def repo_at(name: str) -> Path:
        """A tree the run inherited: one commit, landed before the claim opened."""
        repo = tmp_path / name
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "Fixture")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "base.txt")
        git(repo, "commit", "-q", "-m", "base", dated=before)
        return repo

    committed = repo_at("committed")
    (committed / "landed.txt").write_text("work\n", encoding="utf-8")
    git(committed, "add", "landed.txt")
    git(committed, "commit", "-q", "-m", "landed")

    edited = repo_at("edited")
    (edited / "base.txt").write_text("edited but not yet committed\n", encoding="utf-8")

    silent = repo_at("silent")

    for name, tree in (
        ("committed", committed),
        ("edited", edited),
        ("silent", silent),
    ):
        _open(log, run_id=name, cwd=tree, opened=now - timedelta(minutes=10))
        _run_dir(runs, name, transcript=b"")

    live = _live(log, now=now)
    assert {item.run_id for item in live} == {"committed", "edited", "silent"}

    failures = script.start_failures(live, runs_dir=runs, now=now)

    # Only the tree that produced nothing at all. The other two are the false stalls
    # the live run actually made.
    assert [item.run_id for item in failures] == ["silent"]


def test_a_missing_run_directory_is_a_failure_not_a_pass(tmp_path):
    """F-09: a checker that cannot distinguish a false condition from a failed check
    fails closed. An absent summary is not a pass.
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(log, run_id="vanished", cwd=tmp_path, opened=NOW - timedelta(minutes=10))

    failures = script.start_failures(_live(log), runs_dir=runs, now=NOW)

    assert [item.run_id for item in failures] == ["vanished"]


def test_supervision_never_resolves_liveness_from_a_process_identity(tmp_path):
    """ADR-0034 section 1 and V0-25. A PID is not a durable identifier, and a process
    check has reported dead work healthy three times on this machine. [measured]

    Names, not prose: the docstrings may say the word, the code may not.

    The discriminator is sharpened rather than loosened (F-12). `subprocess.run` is
    permitted here because the process it starts is a fresh `git`, which is an
    artefact reader, not the dispatched child. What stays banned is any name for the
    child's own process: a pid, a handle, a `Popen`, a process-table library. Honest
    limit: this is a name test, so a liveness check hidden behind a neutral name would
    pass it.
    """
    script = _script()
    source = "\n".join(
        inspect.getsource(item)
        for item in (
            script.start_failures,
            script.artefact_bytes_in,
            script.committed_since,
            script.StartFailure,
            script.write_expected,
            script.ExpectedArtefactError,
            script.write_started,
            script.started_line_in,
            script.stall_failures,
            script.Stall,
            script.write_terminal,
            script.inspect_uncommitted_tracked,
        )
    )
    tree = ast.parse(source)
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    banned = ("pid", "popen", "psutil", "is_running", "tasklist")
    process_shaped = sorted(
        name
        for name in identifiers
        if any(token in name.lower() for token in banned)
        or ("process" in name.lower() and "subprocess" not in name.lower())
    )
    assert not process_shaped, (
        f"supervision resolves liveness from a process identity: {process_shaped}"
    )


def test_the_scheduled_task_exists_and_reports_the_dead_runs(tmp_path, capsys):
    """Verify by artefact: the function is not the deliverable, the command is.

    BU-0 is one scheduled task. This is the command that task runs. It exits non-zero
    on a detection, so `dispatch.py --supervise && ...` stops.
    """
    script = _script()
    log, runs = _dirs(tmp_path)
    _open(
        log,
        run_id="dead0",
        cwd=tmp_path,
        opened=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    _run_dir(runs, "dead0", transcript=b"")

    code = script.main(["--supervise", "--log", str(log), "--runs", str(runs)])

    assert code == 1
    out = capsys.readouterr().out
    assert "start_failed" in out
    assert "dead0" in out

    (runs / "dead0" / "stdout.txt").write_bytes(b"a first byte\n")
    assert script.main(["--supervise", "--log", str(log), "--runs", str(runs)]) == 0


def test_dispatch_with_no_expected_artefact_raises(tmp_path, monkeypatch):
    """BU-1 / N01. A dispatch that names no progress artefact is refused before spawn.

    The Temporal trap ADR-0034 §4 records: a configured-but-unfed progress channel
    must fail at configuration time, not quietly at runtime. Whitespace is not a
    declaration. Nothing is written, because an expected record with no artefact
    is the silent channel this unit exists to make impossible.
    """
    script = _script()
    _log, runs = _dirs(tmp_path)
    spawned: list[object] = []

    def fake_run_process(*_a, **_k):
        spawned.append(True)
        return 0, False, 0.1, None

    # Direct construction: the named parameter is empty or absent.
    for artefact in ("", None, "   "):
        with pytest.raises(script.ExpectedArtefactError):
            script.write_expected(
                runs,
                run_id="n01-empty",
                arm="codex",
                unit="N01",
                expected_artefact=artefact,
                progress_deadline_s=600,
            )
    assert not (runs / "n01-empty.json").exists()

    # The spawn path raises the same way and does not start the child.
    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(script, "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    with pytest.raises(script.ExpectedArtefactError):
        script.run_harness(
            harness,
            task="pong",
            cwd=tmp_path,
            run_dir=runs / "n01-empty",
            timeout_s=5,
            model=None,
            run_id="n01-empty",
            expected_artefact="",
        )
    assert spawned == []


def test_expected_record_is_written_before_spawn(tmp_path, monkeypatch):
    """The wrapper writes `expected` before Popen, never after, never by goodwill.

    If this fails because the record appears after `run_process` returns, spawn
    happened unsupervised — F-13 with a file name on it.
    """
    script = _script()
    seen: dict[str, object] = {}
    run_id = "n01-before"
    record_path = tmp_path / f"{run_id}.json"

    def fake_run_process(*_a, **_k):
        seen["exists"] = record_path.exists()
        if record_path.exists():
            seen["record"] = json.loads(record_path.read_text(encoding="utf-8"))
        return 0, False, 0.1, None

    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(script, "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=tmp_path / run_id,
        timeout_s=90,
        model=None,
        run_id=run_id,
        expected_artefact="stdout.txt",
        unit="N01",
    )

    assert seen.get("exists") is True
    expected = seen["record"]["expected"]  # type: ignore[index]
    assert expected["run_id"] == run_id
    assert expected["arm"] == "codex"
    assert expected["unit"] == "N01"
    assert expected["artefact"] == "stdout.txt"
    assert expected["start_window_s"] == script.START_WINDOW_S
    assert expected["progress_deadline_s"] == 90
    assert expected["grace_s"] == coordination.CLAIM_GRACE_S


def test_dispatcher_written_files_are_not_a_progress_artefact(tmp_path):
    """N00 measured this: brief.md and recall.md are the dispatcher's own output.

    If they count as the declared progress artefact, every dead dispatch reads
    healthy — the 23 August failure exactly. Declaring one is the same as
    declaring none.
    """
    script = _script()
    _log, runs = _dirs(tmp_path)
    for name in ("brief.md", "recall.md", "nested/brief.md", "BRIEF.MD"):
        with pytest.raises(script.ExpectedArtefactError):
            script.write_expected(
                runs,
                run_id="n01-self",
                arm="codex",
                unit="N01",
                expected_artefact=name,
                progress_deadline_s=600,
            )
    assert not (runs / "n01-self.json").exists()


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


def _git(repo: Path, *args: str) -> None:
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert done.returncode == 0, done.stderr


def _repo_with_tracked_file(root: Path, name: str = "worker") -> Path:
    repo = root / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_dirty_worker_terminal_records_uncommitted_paths(tmp_path, monkeypatch):
    """BU-4 / N04. F-02 is a missing field: worker exits dirty, terminal names
    the uncommitted tracked paths and marks the outcome incomplete.

    Exit zero is not success. Seven tracked files sat modified with no
    dispatcher running because the streams that wrote them completed and
    exited without committing. [measured, F-02]
    """
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)
    (repo / "tracked.txt").write_text("stranded\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("noise\n", encoding="utf-8")

    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(script, "run_process", lambda *_a, **_k: (0, False, 0.1, None))
    harness = harness_by_id("codex")
    assert harness is not None
    result = script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / "n04-dirty",
        timeout_s=5,
        model=None,
        run_id="n04-dirty",
        expected_artefact="stdout.txt",
        unit="N04",
        claim_run_id="n04-dirty",
    )

    # classify_artefact may still say ok: the child produced an artefact and
    # exited 0. The terminal record is the field F-02 was missing.
    record = json.loads((tmp_path / "n04-dirty.json").read_text(encoding="utf-8"))
    terminal = record["terminal"]
    assert terminal["exit_code"] == 0
    assert terminal["uncommitted_tracked_paths"] == ["tracked.txt"]
    assert terminal["outcome"] == "incomplete"
    assert terminal["claim_disposition"] == "held"
    assert result.exit_code == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_clean_worker_terminal_is_complete(tmp_path, monkeypatch):
    """A clean tree is a complete outcome, or dirty would be unfalsifiable."""
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)

    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(script, "run_process", lambda *_a, **_k: (0, False, 0.1, None))
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / "n04-clean",
        timeout_s=5,
        model=None,
        run_id="n04-clean",
        expected_artefact="stdout.txt",
        unit="N04",
    )

    terminal = json.loads((tmp_path / "n04-clean.json").read_text(encoding="utf-8"))[
        "terminal"
    ]
    assert terminal["uncommitted_tracked_paths"] == []
    assert terminal["outcome"] == "complete"
    assert terminal["claim_disposition"] == "none"
    assert terminal["exit_code"] == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_terminal_is_written_by_the_wrapper_after_exit(tmp_path, monkeypatch):
    """The wrapper writes `terminal` after the child exits, never by goodwill.

    If the record appears before `run_process` returns, we are inventing an
    ending. If it never appears, F-02 is still a missing field.
    """
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)
    (repo / "tracked.txt").write_text("still stranded\n", encoding="utf-8")
    run_id = "n04-after"
    record_path = tmp_path / f"{run_id}.json"
    seen: dict[str, object] = {}

    def fake_run_process(*_a, **_k):
        payload = (
            json.loads(record_path.read_text(encoding="utf-8"))
            if record_path.exists()
            else {}
        )
        seen["terminal_during"] = "terminal" in payload
        return 0, False, 0.1, None

    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(script, "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / run_id,
        timeout_s=5,
        model=None,
        run_id=run_id,
        expected_artefact="stdout.txt",
        unit="N04",
    )

    assert seen.get("terminal_during") is False
    terminal = json.loads(record_path.read_text(encoding="utf-8"))["terminal"]
    assert terminal["uncommitted_tracked_paths"] == ["tracked.txt"]
    assert terminal["outcome"] == "incomplete"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_inspection_failure_is_incomplete_not_clean(tmp_path):
    """F-09: a checker that cannot inspect is not a pass. No git, no repo,
    unreadable tree — the outcome is incomplete, not an empty path list
    dressed as complete.
    """
    script = _script()
    missing = tmp_path / "not-a-repo"
    missing.mkdir()
    path = script.write_terminal(
        tmp_path,
        run_id="n04-unknown",
        exit_code=0,
        cwd=missing,
        claim_disposition="none",
    )
    terminal = json.loads(path.read_text(encoding="utf-8"))["terminal"]
    assert terminal["outcome"] == "incomplete"
    assert terminal["uncommitted_tracked_paths"] == []
    assert terminal["inspected"] is False
