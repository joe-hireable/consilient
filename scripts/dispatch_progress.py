"""What a dispatch promised to produce, whether it produced it, and how it ended.

Three records are written around a run, and each refuses to be inferred. The expected
record names the artefact the supervisor will watch and is refused before spawn when
that artefact is empty, blank or one the dispatcher writes itself — an expected record
with no artefact is the silent channel this exists to make impossible. The started
record is written only once the agent has appended a line to the declared path, because
surviving a timer is not a start. The terminal record lists the tracked paths still
uncommitted when the child exited, and an exit with uncommitted tracked changes is an
incomplete outcome rather than a success. Between them sits the stall check: a hang
after notification is stalled, never started-and-healthy.

`--cwd` accepts this repository (root, a git worktree of it, or a directory inside one
of those) and, additionally, any directory named in the instance file
`.harness/allowed-cwds.json` (ADR-0063). Any other path is refused, including on
`--dry-run`. There is no override flag: Gate B, which governs *depending* on this
harness for work on another repository, is not passed. Listing a root is supervised
dispatch, not a gate pass.

The rest of the file prepares the ground a run needs: materialising one workspace form,
resolving its git index, probing cursor-agent, capturing a finished run's outputs, and
refreshing the headroom snapshot through a bounded, non-inference probe. A failed
refresh does not refuse the work — a readable but stale snapshot is still refused
downstream by its own freshness check, so a transient write collision costs no dispatch,
while an unreadable one refuses here."""

from __future__ import annotations
import shutil
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


import dispatch_launch
import dispatch_vocabulary
from dispatch_boundaries import (
    _cursor_help_and_about,
    _listed_artefact_bindings,
    load_allowed_roots,
)

from dispatch_evidence import (
    _capture_source,
    _load_dispatch_record,
    repo_roots,
    started_line_in,
)

from dispatch_invocation import (
    _progressed_after_start,
    _run_git,
    _store_dispatch_field,
)

from dispatch_launch import (
    DEFAULT_ALLOWED_CWDS,
    DEFAULT_HEADROOM,
    run_process,
)

from dispatch_preflight import (
    inspect_uncommitted_tracked,
)

from dispatch_supervision import (
    Stall,
)

from dispatch_vocabulary import (
    ExpectedArtefactError,
    ROOT,
    START_WINDOW_S,
    WorkspaceProbeError,
    _DISPATCHER_WRITTEN,
    _dispatch_record_path,
)

__all__ = [
    "DEFAULT_ALLOWED_CWDS",
    "DEFAULT_HEADROOM",
    "ExpectedArtefactError",
    "ROOT",
    "START_WINDOW_S",
    "Stall",
    "WorkspaceProbeError",
    "_DISPATCHER_WRITTEN",
    "_capture_source",
    "_cursor_help_and_about",
    "_dispatch_record_path",
    "_listed_artefact_bindings",
    "_load_dispatch_record",
    "_progressed_after_start",
    "_run_git",
    "_store_dispatch_field",
    "inspect_uncommitted_tracked",
    "load_allowed_roots",
    "probe_cursor",
    "refresh_default_headroom",
    "repo_roots",
    "resolve_cwd",
    "run_process",
    "stall_failures",
    "started_line_in",
    "workspace_index_path",
    "write_expected",
    "write_started",
    "write_terminal",
]

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import coordination
from consilient.harness import (
    Probe,
    headroom_freshness_refusal,
    load_pools,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def workspace_index_path(
    work_tree: Path, extra_env: Mapping[str, str] | None = None
) -> Path:
    completed = _run_git(
        work_tree, "rev-parse", "--git-path", "index", extra_env=extra_env
    )
    if completed.returncode != 0:
        raise WorkspaceProbeError(completed.stderr or "could not resolve git index")
    raw = (completed.stdout or "").strip()
    index = Path(raw)
    if not index.is_absolute():
        index = (work_tree / index).resolve()
    return index


def _materialise_workspace_form(
    form: str, source: Path, dest: Path
) -> Mapping[str, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    if form == "linked_worktree":
        branch = f"consilient-ws-{dest.name}"
        completed = _run_git(source, "worktree", "add", "-b", branch, str(dest))
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "linked worktree add failed")
        return {}
    if form == "isolated_git_env":
        git_dir = dest.parent / f"{dest.name}.git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        completed = _run_git(
            source, "clone", "--separate-git-dir", str(git_dir), str(source), str(dest)
        )
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "isolated git clone failed")
        return {"GIT_DIR": str(git_dir.resolve()), "GIT_WORK_TREE": str(dest.resolve())}
    if form == "full_clone":
        completed = _run_git(source, "clone", str(source), str(dest))
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "full clone failed")
        return {}
    raise WorkspaceProbeError(f"unknown workspace form {form!r}")


def probe_cursor() -> Probe:
    ok, version, detail = _cursor_help_and_about()
    return Probe("cursor-composer", ok, version, detail)


def refresh_default_headroom(path: Path) -> str | None:
    """Refresh the default snapshot through the bounded, non-inference probe."""
    if path != dispatch_launch.DEFAULT_HEADROOM.resolve():
        return None
    if path.exists():
        try:
            current = load_pools(path)
        except ValueError:
            pass
        else:
            if (
                headroom_freshness_refusal(current, now=datetime.now(timezone.utc))
                is None
            ):
                return None
    with tempfile.TemporaryDirectory(prefix="consilient-headroom-") as directory:
        temporary = Path(directory)
        code, timed_out, _duration, _timing = dispatch_launch.run_process(
            [
                sys.executable,
                str(dispatch_vocabulary.ROOT / "scripts" / "headroom.py"),
                "--output",
                str(path),
                "--timeout",
                "5",
            ],
            cwd=dispatch_vocabulary.ROOT,
            stdout_path=temporary / "stdout.txt",
            stderr_path=temporary / "stderr.txt",
            timeout_s=45,
        )
    if timed_out:
        return "headroom refresh timed out; process tree killed"
    if code != 0:
        # A failed refresh must not refuse the work. The probe succeeds standalone and fails under
        # concurrency: nineteen dispatchers refreshing one snapshot on Windows collide on the write,
        # and on 23 August 2026 that refused two dispatches outright with "headroom refresh failed
        # (exit 1)" while the probe returned zero when run by hand. [measured]
        #
        # F-08 says a stale reading must never silently become a value, and that still holds — the
        # snapshot below is returned to the caller with its own freshness refusal intact, so a
        # consumer that needs current data still refuses. What changes is that a transient write
        # collision no longer costs a dispatch: an unreadable snapshot refuses, a readable stale one
        # proceeds and is treated as stale by everything downstream.
        if path.exists():
            try:
                load_pools(path)
            except ValueError:
                return f"headroom refresh failed (exit {code}) and the snapshot is unreadable"
            return None
        return f"headroom refresh failed (exit {code}) and no snapshot exists"
    return None


def write_expected(
    runs_dir: Path,
    *,
    run_id: str,
    arm: str,
    unit: str,
    expected_artefact: str | None,
    start_window_s: int = START_WINDOW_S,
    progress_deadline_s: int,
    grace_s: int = coordination.CLAIM_GRACE_S,
) -> Path:
    """Write `dispatch/<run_id>.json` `expected` before spawn, or refuse.

    BU-1 / N01. The record names what the supervisor will watch. An empty, blank
    or dispatcher-written artefact is not a declaration: brief.md and recall.md
    are our own output, and counting them as progress is the 23 August failure
    [measured, N00]. Nothing is written on refusal, because an expected record
    with no artefact is the silent channel this exists to make impossible.
    """
    artefact = "" if expected_artefact is None else str(expected_artefact).strip()
    name = Path(artefact.replace("\\", "/")).name.casefold()
    if not artefact or name in _DISPATCHER_WRITTEN:
        raise ExpectedArtefactError(
            "a dispatch that declares no artefact is refused at dispatch time"
        )
    record = {
        "run_id": run_id,
        "arm": arm,
        "unit": unit,
        "artefact": artefact,
        "start_window_s": start_window_s,
        "progress_deadline_s": progress_deadline_s,
        "grace_s": grace_s,
    }
    return _store_dispatch_field(runs_dir, run_id, "expected", record)


def write_terminal(
    runs_dir: Path,
    *,
    run_id: str,
    exit_code: int | None,
    cwd: Path,
    claim_disposition: str,
) -> Path:
    """Write `dispatch/<run_id>.json` `terminal` after the child exits.

    BU-4 / N04. F-02 measured a worker exiting with output uncommitted and
    the queue reading idle: the claim released, the paths did not. The
    wrapper writes the list; an exit with uncommitted tracked changes is
    an incomplete outcome, not a success. [measured]
    """
    inspected, paths = inspect_uncommitted_tracked(cwd)
    record = {
        "exit_code": exit_code,
        "uncommitted_tracked_paths": list(paths),
        "claim_disposition": claim_disposition,
        "outcome": "complete" if inspected and not paths else "incomplete",
        "inspected": inspected,
    }
    return _store_dispatch_field(runs_dir, run_id, "terminal", record)


def write_started(runs_dir: Path, run_id: str, *, now: datetime) -> Path | None:
    """Write `started` only when the agent has appended a line to the declared path.

    BU-2 / N02. Surviving a timer is not a start. The wrapper observes the
    line; it does not invent one. s6's notification-fd is the incumbent and
    is mandatory. [cited, skarnet.org/software/s6/servicedir.html]
    """
    record = _load_dispatch_record(runs_dir, run_id)
    expected = record.get("expected")
    if not isinstance(expected, dict):
        return None
    artefact = expected.get("artefact")
    if not isinstance(artefact, str) or not artefact.strip():
        return None
    existing = record.get("started")
    if isinstance(existing, dict) and str(existing.get("line") or "").strip():
        return _dispatch_record_path(runs_dir, run_id)
    line = started_line_in(runs_dir / run_id, artefact)
    if line is None:
        return None
    started = {
        "run_id": run_id,
        "artefact": artefact,
        "line": line,
        "at": now.astimezone(timezone.utc).isoformat(),
    }
    return _store_dispatch_field(runs_dir, run_id, "started", started)


def stall_failures(
    claims: tuple[coordination.Claim, ...],
    *,
    runs_dir: Path,
    now: datetime,
) -> tuple[Stall, ...]:
    """Open dispatches that notified start and then produced nothing further.

    The started line answers "did it start?", not "is it healthy?". A hang
    after notification is `stalled`, never `started`-and-healthy.
    """
    found: list[Stall] = []
    for claim in sorted(claims, key=lambda item: item.run_id):
        opened = datetime.fromisoformat(claim.opened_at).astimezone(timezone.utc)
        age_s = (now.astimezone(timezone.utc) - opened).total_seconds()
        record = _load_dispatch_record(runs_dir, claim.run_id)
        expected = record.get("expected")
        if not isinstance(expected, dict):
            continue
        artefact = expected.get("artefact")
        if not isinstance(artefact, str) or not artefact.strip():
            continue
        started = record.get("started")
        line = (
            str(started.get("line") or "").strip() if isinstance(started, dict) else ""
        )
        if not line:
            observed = started_line_in(runs_dir / claim.run_id, artefact)
            if observed is None:
                continue
        try:
            deadline = int(expected.get("progress_deadline_s"))
        except (TypeError, ValueError):
            continue
        if age_s < deadline:
            continue
        if _progressed_after_start(claim, runs_dir, artefact):
            continue
        found.append(
            Stall(
                run_id=claim.run_id,
                harness=claim.harness,
                signal="no progress after started",
                threshold_s=deadline,
                observed_s=round(age_s, 2),
                action="diagnose",
            )
        )
    return tuple(found)


def resolve_cwd(value: str | None, *, allowed_file: Path | None = None) -> Path:
    """Resolve the working directory, refusing unnamed foreign roots.

    Default is this repository and its worktrees. Extra roots come only from the gitignored
    instance allowlist (ADR-0063). There is deliberately no override flag — a second path
    to the same state is the same hole. Naming a root is supervised dispatch under
    ADR-0039; it does not pass Gate B.
    """
    path = (Path(value) if value else Path.cwd()).resolve()
    roots = list(repo_roots())
    roots.extend(load_allowed_roots(allowed_file))
    for root in roots:
        if path == root or root in path.parents:
            return path
    raise ValueError(
        f"refusing to dispatch with cwd {path}: this harness runs only inside its own "
        f"repository ({dispatch_vocabulary.ROOT}), a git worktree of the same repository, a directory "
        "within one of those, or a root named in the instance allowlist "
        f"({DEFAULT_ALLOWED_CWDS.name}). Gate B — depending on this harness for work on "
        "another repository — is not passed. Listing a root is supervised dispatch "
        "(ADR-0039/ADR-0063), not a gate pass, and no command-line flag reopens Gate B."
    )


def _capture_run_outputs(
    run_dir: Path, stdout_path: Path, stderr_path: Path, workspace: Path
) -> dict[str, object]:
    manifest_path = run_dir / "artefact-manifest.json"
    verifier_path = run_dir / "verifier-outcome.json"
    listed: list[dict[str, object]] = []
    if manifest_path.is_file():
        listed = _listed_artefact_bindings(manifest_path, workspace)
    return {
        "stdout": _capture_source(
            stdout_path, workspace=workspace, media_type="text/plain"
        ),
        "stderr": _capture_source(
            stderr_path, workspace=workspace, media_type="text/plain"
        ),
        "artefact_manifest": _capture_source(
            manifest_path, workspace=workspace, media_type="application/json"
        ),
        "verifier_outcome": _capture_source(
            verifier_path, workspace=workspace, media_type="application/json"
        ),
        "listed_artefacts": listed,
    }
