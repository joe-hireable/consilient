"""One argv per harness, built from what the installed CLI actually exposes.

The differences between harnesses are not cosmetic. claude takes an instruction naming
the brief; grok takes the brief by path with an explicit cwd; codex runs exec with its
extra flags placed before the prompt so they are not eaten as the task; cursor-agent
runs natively or through the WSL bridge, where the task body never enters the shell and
only paths we created do. A model whose reasoning capability is unknown is refused, and
the default cursor model is refused when it would draw on the Cursor Other Models pool —
spending that pool has to be asked for explicitly.

Probing applies the same discipline to installation. A binary is asked for its version
and a version token is parsed out of the answer; anything else is not installed,
whatever the exit code said.

The git plumbing here exists because a workspace must be proved without side effects.
Read, write, stage and object write are proved with write-tree and commit-tree rather
than commit: it moves no ref, leaves no throwaway commit in the history and runs no
hooks, because it asks git for an object and not for a commit against a branch. The
probe file is unstaged before it is removed, so the workspace is left exactly as it was
found."""

from __future__ import annotations
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import cast

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import coordination
from consilient.harness import (
    DEFAULT_PERMISSION_MODE,
    MODELS,
    Harness,
    PermissionMode,
    PoolState,
    Probe,
    cursor_pool_for_model,
    permission_flags,
    select_model,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_evidence
import dispatch_launch
from dispatch_evidence import (
    _git_identity_env,
    _load_dispatch_record,
    committed_since,
    find_grok,
    git_diff_bytes,
    metered_grok_reason,
)

from dispatch_launch import (
    HELDOUT_ISOLATION_CHECKER,
    cursor_native,
    find_claude,
    find_codex,
    help_text,
    wsl_bridge,
)

from dispatch_preflight import (
    git_workspace,
    native_cap_flags,
)

from dispatch_vocabulary import (
    DEFAULT_CURSOR_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_TURNS,
    WorkspaceProbeError,
    _dispatch_record_path,
    _nonempty_line_count,
    _run_probe,
    _version_from,
    optional_flags,
    to_wsl_path,
    which_binary,
)

__all__ = [
    "DEFAULT_CURSOR_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_TURNS",
    "HELDOUT_ISOLATION_CHECKER",
    "WorkspaceProbeError",
    "_dispatch_record_path",
    "_git_identity_env",
    "_load_dispatch_record",
    "_nonempty_line_count",
    "_run_probe",
    "_version_from",
    "build_command",
    "committed_since",
    "cursor_native",
    "find_claude",
    "find_codex",
    "find_grok",
    "git_diff_bytes",
    "git_workspace",
    "heldout_contract_refusal",
    "help_text",
    "metered_grok_reason",
    "native_cap_flags",
    "optional_flags",
    "probe_claude",
    "probe_codex",
    "probe_grok",
    "to_wsl_path",
    "which_binary",
    "wsl_bridge",
    "wsl_git_exports",
]


def heldout_contract_refusal(
    contract: str,
    *,
    brief: str = "",
    worktree: str = "",
    claims: tuple[str, ...] = (),
) -> str | None:
    spec = importlib.util.spec_from_file_location(
        "check_heldout_isolation", HELDOUT_ISOLATION_CHECKER
    )
    if spec is None or spec.loader is None:
        return "held-out isolation checker is unavailable; refusing before child launch"
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    refusal_reason = cast(Callable[..., str | None], checker.refusal_reason)
    return refusal_reason(contract, brief=brief, worktree=worktree, claims=claims)


def _run_git(
    cwd: Path,
    *args: str,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    git = which_binary("git")
    if git is None:
        raise WorkspaceProbeError("git is not installed")
    env = _git_identity_env()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [git, "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )


def _probe_read_write_stage_commit(
    work_tree: Path, extra_env: Mapping[str, str] | None = None
) -> None:
    tracked = _run_git(work_tree, "ls-files", extra_env=extra_env)
    if tracked.returncode != 0:
        raise WorkspaceProbeError(tracked.stderr or "read probe failed")
    names = [line for line in (tracked.stdout or "").splitlines() if line.strip()]
    if not names:
        raise WorkspaceProbeError("read probe found no tracked file")
    sample = work_tree / names[0]
    sample.read_bytes()
    probe = work_tree / f".consilient-workspace-probe-{os.getpid()}"
    probe.write_text("probe\n", encoding="utf-8")
    added = _run_git(work_tree, "add", probe.name, extra_env=extra_env)
    if added.returncode != 0:
        raise WorkspaceProbeError(added.stderr or "stage probe failed")
    # PLUMBING, NOT PORCELAIN, AND THIS IS THE WHOLE OF THE BUG IT FIXES.
    #
    # This used to run `git commit`. MEASURED 25 August 2026: that single choice was silently
    # losing every agent's work, and the mechanism is entirely self-inflicted.
    #
    # `_git_identity_env` sets GIT_AUTHOR and GIT_COMMITTER but never CONSILIENT_RUN_ID. A
    # LINKED WORKTREE inherits `core.hooksPath` from the shared .git/config, so this
    # repository's own pre-commit commit-attribution gate runs against the probe -- and
    # refuses it, because an unattributed commit is refused whenever any live claim's cwd
    # overlaps the tree. Review dispatches record cwd as the repository root, which overlaps
    # every workspace beneath it. A CLONE gets a fresh config with no hooksPath, so no gate
    # runs and the probe passes.
    #
    # So "linked_worktree fails under load" was never slowness or lock contention. "Load" is
    # the number of concurrent live claims, and the fallback ladder was selecting, with
    # perfect reliability, for the one form whose commits CANNOT be harvested: a clone made
    # with --separate-git-dir puts every agent commit in a different object store, invisible
    # to the driver's merge path. Eleven commits and about 3,300 insertions were stranded that
    # way, and one unit was built twice because the first result could not be seen.
    #
    # The probe exists to prove read, write, stage and object-write. `write-tree` plus
    # `commit-tree` proves all four: it builds a real tree from the index and writes a real
    # commit object. It moves no ref, leaves no throwaway commit in the history, and runs no
    # hooks -- because it asks git for an object, not for a commit against a branch.
    #
    # This does NOT weaken the commit gate. The gate exists to stop a RUN committing paths
    # another run has claimed. A plumbing object write commits nothing to any branch and
    # claims nothing; asking the gate for permission here was the category error.
    tree = _run_git(work_tree, "write-tree", extra_env=extra_env)
    if tree.returncode != 0:
        raise WorkspaceProbeError(tree.stderr or "write-tree probe failed")
    tree_sha = (tree.stdout or "").strip()
    if not tree_sha:
        raise WorkspaceProbeError("write-tree probe produced no tree")
    parent = _run_git(work_tree, "rev-parse", "HEAD", extra_env=extra_env)
    args = ["commit-tree", tree_sha, "-m", "consilient workspace probe"]
    if parent.returncode == 0 and (parent.stdout or "").strip():
        args[2:2] = ["-p", (parent.stdout or "").strip()]
    written = _run_git(work_tree, *args, extra_env=extra_env)
    if written.returncode != 0 or not (written.stdout or "").strip():
        raise WorkspaceProbeError(written.stderr or "commit-tree probe failed")
    # Unstage before removing the file, so the workspace is left exactly as it was found. The
    # old probe committed and then unlinked, leaving a tracked deletion in every workspace --
    # which gave `git diff --stat` a permanent 72-byte floor and made `terminal.outcome` read
    # "incomplete" for a run that committed correctly and one that committed nothing alike.
    _run_git(work_tree, "reset", "-q", "HEAD", "--", probe.name, extra_env=extra_env)
    probe.unlink(missing_ok=True)


def wsl_git_exports(cwd: Path) -> str:
    workspace = git_workspace(cwd)
    if workspace is None:
        return ""
    git_dir, work_tree = workspace
    return (
        f"export GIT_DIR={shlex.quote(to_wsl_path(git_dir))} "
        f"GIT_WORK_TREE={shlex.quote(to_wsl_path(work_tree))}; "
    )


def probe_claude() -> Probe:
    binary = dispatch_launch.find_claude()
    if binary is None:
        return Probe("claude", False, None, "claude is not on PATH")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("claude", False, None, err or out or f"exit {code}")
    return Probe("claude", True, version, binary)


def probe_codex() -> Probe:
    binary = dispatch_launch.find_codex()
    if binary is None:
        return Probe("codex", False, None, "codex is not on PATH")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("codex", False, None, err or out or f"exit {code}")
    return Probe("codex", True, version, binary)


def probe_grok() -> Probe:
    binary = dispatch_evidence.find_grok()
    if binary is None:
        return Probe("grok", False, None, "grok is not on PATH or in ~/.grok/bin")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("grok", False, None, err or out or f"exit {code}")
    return Probe("grok", True, version, binary)


def _store_dispatch_field(
    runs_dir: Path, run_id: str, field: str, value: object
) -> Path:
    path = _dispatch_record_path(runs_dir, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _load_dispatch_record(runs_dir, run_id)
    payload[field] = value
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(encoded, encoding="utf-8")
    os.replace(tmp, path)
    return path


def _progressed_after_start(
    claim: coordination.Claim, runs_dir: Path, artefact: str
) -> bool:
    if _nonempty_line_count(runs_dir / claim.run_id, artefact) > 1:
        return True
    tree = Path(claim.cwd) if claim.cwd else None
    if tree is None:
        return False
    return dispatch_evidence.git_diff_bytes(tree) > 0 or committed_since(tree, claim.opened_at)


def build_command(
    harness: Harness,
    *,
    task: str,
    cwd: Path,
    brief: Path,
    model: str | None,
    permissions: PermissionMode = DEFAULT_PERMISSION_MODE,
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[str] | str:
    """Return argv, or a refusal reason string."""
    cwd = cwd.resolve()
    if model is not None:
        selected = select_model(harness.id, pools=pools, requested=model)
        if isinstance(selected, str):
            return selected
        attended_cursor_other = (
            harness.id == "cursor-composer"
            and cursor_pool_for_model(model) == "cursor-other"
        )
        if (
            selected.reasoning_capability == "unknown"
            and selected not in MODELS
            and not attended_cursor_other
        ):
            return (
                f"refusing {harness.id} model {model!r}: reasoning capability is "
                f"unknown ({selected.reasoning_provenance})"
            )
    brief = brief.resolve()
    bypass = list(permission_flags(harness.id, permissions))
    instruction = (
        f"Read the file {brief.as_posix()} and do exactly that task. "
        "Do not wait for confirmation."
    )
    if harness.id == "claude":
        binary = dispatch_launch.find_claude()
        if binary is None:
            return "claude is not on PATH"
        caps = native_cap_flags(
            harness.id,
            dispatch_launch.help_text([binary]),
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        return [binary, *bypass, *caps, "-p", instruction]
    if harness.id == "grok":
        metered = dispatch_evidence.metered_grok_reason()
        if metered is not None:
            return metered
        binary = dispatch_evidence.find_grok()
        if binary is None:
            return "grok is not on PATH or in ~/.grok/bin"
        help_blob = dispatch_launch.help_text([binary])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(help_blob, *bypass)
        return [
            binary,
            "--prompt-file",
            brief.as_posix(),
            "--cwd",
            str(cwd),
            *caps,
            *extra,
        ]
    if harness.id == "codex":
        binary = dispatch_launch.find_codex()
        if binary is None:
            return "codex is not on PATH"
        help_blob = dispatch_launch.help_text([binary, "exec"])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(help_blob, "--skip-git-repo-check")
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        # Insert extra flags before the prompt so they are not eaten as the task.
        return [binary, "exec", "-C", str(cwd), *caps, *extra, instruction]
    if harness.id == "cursor-composer":
        chosen = model or DEFAULT_CURSOR_MODEL
        if model is None and (pools or family is not None):
            selected = select_model(harness.id, pools=pools, family=family)
            if isinstance(selected, str):
                return selected
            chosen = selected.id
        if cursor_pool_for_model(chosen) == "cursor-other" and model is None:
            return (
                f"refusing default cursor model {chosen!r}: it draws on the Cursor Other "
                "Models pool (claude-*/gpt-*/gemini-*). Automatic selection avoids that "
                "pool; pass --model explicitly if you mean to spend it."
            )
        native = dispatch_launch.cursor_native()
        extra: list[str] = []
        if native is not None:
            help_blob = dispatch_launch.help_text([native])
            caps = native_cap_flags(
                harness.id,
                help_blob,
                max_turns=max_turns,
                max_tokens=max_tokens,
            )
            if isinstance(caps, str):
                return caps
            extra = optional_flags(help_blob, "--force", "--trust")
            for flag in bypass:
                if flag not in extra:
                    extra.append(flag)
            return [
                native,
                "-p",
                "--model",
                chosen,
                "--output-format",
                "json",
                *caps,
                *extra,
                instruction,
            ]
        bridge = dispatch_launch.wsl_bridge()
        if bridge is None:
            return "cursor-agent is not reachable (no native binary and no wsl)"
        wsl_cwd = to_wsl_path(cwd)
        wsl_brief = to_wsl_path(brief)
        wsl_instruction = (
            f"Read the file {wsl_brief} and do exactly that task. "
            "Do not wait for confirmation."
        )
        help_blob = dispatch_launch.help_text([bridge, "-e", "bash", "-lc", "cursor-agent --help"])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(
            help_blob,
            "--force",
            "--trust",
        )
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        extra_s = " " + " ".join([*caps, *extra])
        # The task body never enters the shell: only paths we created do.
        # GIT_DIR/GIT_WORK_TREE are WSL paths so linked worktrees are repositories
        # to WSL git (R4). Native cursor-agent is unchanged — it already sees NT paths.
        inner = (
            f"{wsl_git_exports(cwd)}cd {shlex.quote(wsl_cwd)} && cursor-agent -p "
            f"--model {shlex.quote(chosen)} --output-format json{extra_s} "
            f"{shlex.quote(wsl_instruction)}"
        )
        return [bridge, "-e", "bash", "-lc", inner]
    return f"no invocation for harness {harness.id}"
