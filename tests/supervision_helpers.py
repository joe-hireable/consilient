"""Loading `scripts/dispatch.py` and building the run directories the supervision units
read.

Supervision is a script rather than a package module, so every check reaches it through
`importlib.util.spec_from_file_location`, cached so the five modules exercise one
instance.

The fixtures carry as much of the evidence as the loader does. `_run_dir` writes
`brief.md` and `recall.md` first and large on purpose: they are the *dispatcher's* own
output, written before the child is spawned, and treating them as progress is what made
six dead dispatches read healthy on 23 August 2026. A helper that quietly stopped
writing them would retire the failure these units exist to catch, so they stay here and
stay big.

`NOW` is a fixed instant so the artefact-age arithmetic is deterministic. The checks
that involve real commits deliberately do not use it — a commit carries a real committer
date and `git log --since` compares against it, so a fixed instant would make them pass
or fail depending on the wall time the suite happened to run at, which is the sort of
test that lies later."""

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from consilient import coordination
from consilient.events import read_all

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
