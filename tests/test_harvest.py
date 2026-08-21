"""ADR-0057: the harvest dest cannot be a path git would publish."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient.harvest import HarvestError, assert_unpublishable, harvest
from consilient.harness import harness_by_id, record_outcome


ROOT = Path(__file__).resolve().parent.parent


def test_default_training_dir_is_gitignored_and_untracked() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/training/" in ignored
    import os
    import subprocess

    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "ls-files", ".harness/training/"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    ).stdout.split()
    assert tracked == []


def test_assert_unpublishable_refuses_a_tracked_path(tmp_path: Path) -> None:
    inside = ROOT / "docs" / "harvest-must-not-land-here"
    with pytest.raises(HarvestError, match="permits only"):
        assert_unpublishable(inside, root=ROOT)


def test_assert_unpublishable_allows_the_default_training_dir() -> None:
    dest = ROOT / ".harness" / "training"
    assert assert_unpublishable(dest, root=ROOT) == dest.resolve()


def test_assert_unpublishable_refuses_other_ignored_directories() -> None:
    with pytest.raises(HarvestError, match="permits only"):
        assert_unpublishable(ROOT / ".harness" / "log" / "training", root=ROOT)


def test_assert_unpublishable_allows_a_path_outside_the_repository(tmp_path: Path) -> None:
    dest = tmp_path / "durable"
    dest.mkdir()
    assert assert_unpublishable(dest, root=ROOT) == dest.resolve()


def test_harvest_writes_dispatch_outcomes_and_skips_duplicates(
    tmp_path: Path,
) -> None:
    log = tmp_path / "log"
    runs = tmp_path / "runs"
    dest = tmp_path / "training"
    log.mkdir()
    grok = harness_by_id("grok")
    assert grok is not None
    ts = datetime.now(timezone.utc).isoformat()
    recorded = record_outcome(
        log,
        ts=ts,
        run_id="run-harvest-1",
        task="reply pong",
        cwd=str(tmp_path),
        harness=grok,
        status="ok",
        reason="produced an artefact",
        exit_code=0,
        artefact_bytes=5,
        diff_bytes=0,
        timed_out=False,
        duration_s=0.1,
        command=("grok", "-p", "pong"),
    )
    run_dir = runs / "run-harvest-1"
    run_dir.mkdir(parents=True)
    (run_dir / "brief.md").write_text("reply pong\n", encoding="utf-8")
    (run_dir / "stdout.txt").write_text("pong\n", encoding="utf-8")
    first = harvest(log_dir=log, runs_dir=runs, dest=dest, root=ROOT)
    assert first["written"] == 1
    assert first["skipped"] == 0
    second = harvest(log_dir=log, runs_dir=runs, dest=dest, root=ROOT)
    assert second["written"] == 0
    assert second["skipped"] == 1
    rows = [
        json.loads(line)
        for line in (dest / "harvest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["kind"] == "harvest.example"
    assert row["run_id"] == "run-harvest-1"
    assert row["harness"] == "grok"
    assert row["brief"] == "reply pong\n"
    assert row["stdout"] == "pong\n"
    assert row["source"] == "consilient.dispatch"
    assert recorded["event"] == "dispatch.outcome"


def test_harvest_cli_refuses_docs_as_dest() -> None:
    import importlib.util
    import sys

    path = ROOT / "scripts" / "harvest.py"
    spec = importlib.util.spec_from_file_location("consilient_harvest_cli", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["consilient_harvest_cli"] = module
    spec.loader.exec_module(module)
    code = module.main(["--out", str(ROOT / "docs")])
    assert code == 2
