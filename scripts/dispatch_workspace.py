"""Prove a workspace before an agent is admitted to it, and probe what is installed.

Three forms are tried in order — linked worktree, isolated git environment, full clone —
and each must prove read, write, stage and object write in the workspace it has just
materialised before it is offered to anything. The first form that proves itself wins. A
directory that is not a git repository returns nothing at all; a git repository that can
prove no form returns a refusal string, so the caller records an adverse attempt and
skips the launch rather than admitting an agent to a workspace whose commits cannot
afterwards be harvested.

The installed-harness probe asks the same kind of question of the machine: claude,
cursor, grok and codex, each answered by running the binary rather than by looking for
it.

The supervision pass is detection only. It reads the trajectory, writes a started record
for any live claim that has since produced its line, and reports the open dispatches
that never started and those that stalled. It repairs nothing, releases nothing and
terminates nothing; until escalation and lease release land, a non-zero exit is the
whole alert, and saying so is cheaper than implying a channel that does not exist."""

from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import coordination
from consilient.events import (
    EventError,
    read_all,
)
from consilient.harness import (
    Probe,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dispatch_invocation import (
    _probe_read_write_stage_commit,
    probe_claude,
    probe_codex,
    probe_grok,
)

from dispatch_launch import (
    emit,
    start_failures,
)

from dispatch_preflight import (
    git_workspace,
)

from dispatch_progress import (
    _materialise_workspace_form,
    probe_cursor,
    stall_failures,
    workspace_index_path,
    write_started,
)

from dispatch_vocabulary import (
    IsolatedWorkspace,
    WORKSPACE_FORMS,
    WorkspaceProbeError,
)

__all__ = [
    "IsolatedWorkspace",
    "WORKSPACE_FORMS",
    "WorkspaceProbeError",
    "_materialise_workspace_form",
    "_probe_read_write_stage_commit",
    "emit",
    "git_workspace",
    "probe_all",
    "probe_claude",
    "probe_codex",
    "probe_cursor",
    "probe_grok",
    "probe_workspace_form",
    "provision_isolated_workspace",
    "stall_failures",
    "start_failures",
    "supervise",
    "workspace_index_path",
    "write_started",
]


def probe_workspace_form(
    form: str,
    source: Path,
    dest: Path,
    *,
    runtime_id: str,
    runtime_version: str,
) -> IsolatedWorkspace:
    """Prove one form with an actual read, write, stage and throwaway commit."""
    extra = dict(_materialise_workspace_form(form, source, dest))
    _probe_read_write_stage_commit(dest, extra_env=extra or None)
    workspace = git_workspace(dest)
    if workspace is None:
        raise WorkspaceProbeError("probed workspace is not a git work tree")
    git_dir, work_tree = workspace
    if extra.get("GIT_DIR"):
        git_dir = Path(extra["GIT_DIR"])
    index = workspace_index_path(dest, extra_env=extra or None)
    return IsolatedWorkspace(
        form=form,
        work_tree=work_tree,
        git_dir=git_dir,
        index_path=index,
        runtime_id=runtime_id,
        runtime_version=runtime_version,
    )


def provision_isolated_workspace(
    cwd: Path,
    *,
    run_id: str,
    dest_root: Path,
    runtime_id: str,
    runtime_version: str,
) -> IsolatedWorkspace | None | str:
    """Provision a proved isolated workspace, or None when cwd is not a git repo.

    A git repository that cannot prove any form returns a refusal string so the
    caller can record an adverse attempt and skip launch.
    """
    if git_workspace(cwd) is None:
        return None
    dest_root.mkdir(parents=True, exist_ok=True)
    last_error = "no workspace form was attempted"
    for form in WORKSPACE_FORMS:
        target = dest_root / form / run_id
        try:
            return probe_workspace_form(
                form,
                cwd,
                target,
                runtime_id=runtime_id,
                runtime_version=runtime_version,
            )
        except (WorkspaceProbeError, OSError) as exc:
            last_error = f"{form} failed: {exc}"
            continue
    return f"no runtime-conformant isolated workspace: {last_error}"


def probe_all() -> tuple[Probe, ...]:
    return (probe_claude(), probe_cursor(), probe_grok(), probe_codex())


def supervise(*, log_dir: Path, runs_dir: Path, as_json: bool) -> int:
    """The scheduled task behind BU-0. One pass, one report, no repair.

    Detection only: N00 reports what died. Delivering that to the principal is BU-7's
    single escalation emitter, and releasing the dead run's lease is BU-3. Until those
    land, a non-zero exit is the whole alert, and saying so is cheaper than implying a
    channel that does not exist.
    """
    now = datetime.now(timezone.utc)
    try:
        events, _rejected = read_all(log_dir)
    except (EventError, OSError) as exc:
        emit({"status": "refused", "reason": f"trajectory unreadable: {exc}"}, as_json)
        return 2
    live = coordination.live_claims(events, now=now)
    for claim in live:
        write_started(runs_dir, claim.run_id, now=now)
    failures = start_failures(live, runs_dir=runs_dir, now=now)
    stalls = stall_failures(live, runs_dir=runs_dir, now=now)
    emit(
        {
            "status": "supervised",
            "open_dispatches": len(live),
            "start_failed": [item.as_dict() for item in failures],
            "stalled": [item.as_dict() for item in stalls],
        },
        as_json,
    )
    return 1 if failures or stalls else 0
