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
