"""S02 — the promote loop refuses from the command line, and leaves the scratch
directory untouched.

The two end-to-end runs, kept together and kept apart from the in-process tests because
their evidence is of a different kind: `scripts/promote_loop.py --evaluate-only` is
launched as a real subprocess, so the exit code, the JSON on stdout and the bytes
remaining in the scratch directory are all read from outside the process that produced
them. Nothing in these is mocked, which is the point — an in-process assertion cannot
show that the shipped entry point wires the refusal to a non-zero exit.

Both candidates, the helpful one and the Goodhart one, come back `refused` with reason
`candidate_unexecutable` and exit code 2: on the real execute path the containment probe
refuses before either is scored. In both runs `applied` and `activated` are false and
the scratch marker still reads `parent`. A refusal that quietly mutated the workspace
would be the reversal proof failing in the one place nothing is looking."""

import json
import subprocess
import sys
from pathlib import Path
from promote_instrument_helpers import (
    EXP78,
    _manifest_dict,
)


def test_promote_loop_evaluate_only_runs_scratch_reversal(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest_dict()), encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    log_dir = tmp_path / "log"
    marker = scratch / "state.txt"
    marker.write_text("parent", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/promote_loop.py",
            "--sealed-manifest",
            str(manifest_path),
            "--source",
            str(EXP78 / "helpful.py"),
            "--baseline",
            str(EXP78 / "solver.py"),
            "--scratch-dir",
            str(scratch),
            "--log",
            str(log_dir),
            "--evaluate-only",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 2, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["action"] == "refused"
    assert payload["reason"] == "candidate_unexecutable"
    assert payload["applied"] is False
    assert payload["activated"] is False
    assert marker.read_text(encoding="utf-8") == "parent"


def test_promote_loop_goodhart_refuses_without_mutating_scratch(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest_dict()), encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    log_dir = tmp_path / "log"
    marker = scratch / "state.txt"
    marker.write_text("parent", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/promote_loop.py",
            "--sealed-manifest",
            str(manifest_path),
            "--source",
            str(EXP78 / "harmful.py"),
            "--baseline",
            str(EXP78 / "solver.py"),
            "--scratch-dir",
            str(scratch),
            "--log",
            str(log_dir),
            "--evaluate-only",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 2, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["action"] == "refused"
    assert payload["reason"] == "candidate_unexecutable"
    assert marker.read_text(encoding="utf-8") == "parent"
