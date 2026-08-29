"""The cheap supervision floor: a dead dispatch is found from its artefact.

Unit N00 of the build plan, which is BU-0 of `docs/20-design/supervision-escalation-and-
sessions-2026-08-23.md`.

The failure it exists to stop is F-13 in `docs/00-context/orchestration-failure-
modes-2026-08-23.md`: six of six dispatches died at startup seconds after the scheduler
printed that the work had been sent, and the loop went on reporting itself busy over
work that was already dead. The detection channel was a person looking at a usage graph.
[measured, 23 August 2026]

These checks hold ADR-0034 in three of its clauses. A terminal record outranks the
absent artefact — the Airflow regression is the cited case, a task that had already
logged its own clean exit marked failed because zombie detection consulted a stale
liveness signal instead; V0-25 has declared that clause since 19 August with no check on
the dispatch path, and this is the check. Detection diagnoses rather than terminates,
which is why `start_failures` returns records and kills nothing, and why each record
carries signal, threshold, observed value and action, so an operator can dispute the
decision from the record alone. And the expensive error is a watchdog acting on live
work rather than a slow supervisor: ADR-0034 collected five production systems that made
it — Airflow, LangGraph, Celery, Ray and Kubernetes. [cited, ADR-0034]

The transcript alone is not enough, and that is measured rather than feared. The first
version of this unit was run against the live trajectory on 23 August 2026 and flagged
six open dispatches, one of which was the run building the unit — alive, working, and 46
minutes into a transcript still holding zero bytes. Of 224 real run directories, 195
carry a transcript and 29 do not, and the empty ones are the open and the crashed alike:
a live `claude -p` child writes nothing until it exits, so the transcript is a terminal
signal and not a progress one. [measured, 23 August 2026] The progress test is therefore
Hadoop's disjunction over the three artefacts this repository already produces — the
transcript, the working tree, the commits — and only a run with none of the three is
reported. An absent run directory is still a failure, not a pass: F-09, a checker that
cannot distinguish a false condition from a failed check fails closed.

The last check verifies by artefact rather than by function: BU-0 is one scheduled task,
and the command that task runs exits non-zero on a detection, so `dispatch.py
--supervise && ...` stops.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    The failure it exists to stop is F-13 in
    `docs/00-context/orchestration-failure-modes-2026-08-23.md`: six of six dispatches
    died at startup seconds after the scheduler printed that the work had been sent, and
    the loop went on reporting itself busy over work that was already dead. The detection
    channel was a person looking at a usage graph. [measured, 23 August 2026]

    Every check here holds ADR-0034: liveness is never resolved from a process identity, a
    terminal record outranks a stale liveness signal, and detection diagnoses rather than
    terminates. The last of those is why `start_failures` returns records and kills nothing.
"""

import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from consilient.harness import harness_by_id, now_ts, record_outcome
from supervision_helpers import (
    NOW,
    _dirs,
    _live,
    _open,
    _run_dir,
    _script,
)


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
