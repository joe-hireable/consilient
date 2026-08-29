"""What is settled before a child is launched, and what git is asked rather than
assumed.

The brief is the task plus its assembled context, written into the run directory so the
child is not amnesiac; cross-harness memory is the trajectory, and until 21 August 2026
the brief was the task alone, so Cursor could not see what Codex had just done. The
recall pack is bounded, and the bound is the point, because an unbounded coordination
section crowds the task out of the context window. Beside it, the native cap flags apply
every hard bound the installed CLI actually exposes and leave the rest to the caller's
wall-clock timeout: the retained obligation is that no arm runs unbounded, not that a
particular flag spelling exists.

Git is interrogated, never delegated to the child. A linked worktree's .git is a file
containing a Windows path that WSL git cannot resolve (R4, measured again 21 August
2026), so dispatch owns the translation; and tracked paths that differ from HEAD are
read with porcelain v1 and untracked files excluded, because a failed inspection is not
a clean tree (F-09).

The two refusals here are the ones taken before anything runs. A second dispatch
claiming a path a live claim already holds is refused and the refusal recorded like
every other — the refusal is the coordination mechanism working. And the scratch
observer for an isolated recovery proof denies a write out of root, a network reach, a
credential read and a spawned child, and fails closed on a step kind it does not
recognise rather than letting it pass."""

from __future__ import annotations
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import coordination, instructions
from consilient.harness import (
    record_refusal,
)
from consilient.recall import pack as pack_recall

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_vocabulary
from dispatch_vocabulary import (
    GIT_ENV,
    RECALL_LIMIT_CHARS,
    _PROOF_ESCAPES,
    _exit_for,
    optional_flags,
    which_binary,
)

__all__ = [
    "GIT_ENV",
    "RECALL_LIMIT_CHARS",
    "_PROOF_ESCAPES",
    "_exit_for",
    "git_workspace",
    "inspect_uncommitted_tracked",
    "native_cap_flags",
    "optional_flags",
    "which_binary",
    "write_brief",
]


def git_workspace(cwd: Path) -> tuple[Path, Path] | None:
    """Return (absolute git dir, work tree) for cwd, or None if git cannot answer.

    A linked worktree's `.git` is a file containing a Windows path. WSL git cannot
    resolve that path (R4, measured again 21 August 2026 on a jobboard worktree).
    Dispatch owns the translation; the child is not asked to.
    """
    git = which_binary("git")
    if git is None:
        return None
    try:
        completed = subprocess.run(
            [
                git,
                "-C",
                str(cwd.resolve()),
                "rev-parse",
                "--absolute-git-dir",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=dispatch_vocabulary.GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    lines = [
        line.strip() for line in (completed.stdout or "").splitlines() if line.strip()
    ]
    if len(lines) < 2:
        return None
    git_dir = Path(lines[0])
    work_tree = Path(lines[1])
    try:
        git_dir = git_dir.resolve()
        work_tree = work_tree.resolve()
    except OSError:
        return None
    if not git_dir.exists() or not work_tree.is_dir():
        return None
    return git_dir, work_tree


def native_cap_flags(
    harness_id: str,
    help_blob: str,
    *,
    max_turns: int,
    max_tokens: int,
) -> list[str] | str:
    """Return whatever native hard-cap flags the installed CLI actually exposes.

    R11's attribution was withdrawn on 21 August 2026. The retained engineering
    obligation is that **no arm runs unbounded** -- not that a particular flag spelling
    exists.

    Until 21 August 2026 this demanded `--max-turns` AND `--max-tokens` natively and refused
    the launch otherwise. Measured against the installed CLIs that day: grok exposes
    `--max-turns` only; codex exposes neither. So the condition could never pass for two of
    the three subscription harnesses, and the harness had locked itself out of two of the
    plans it exists to spend. That is the wall-not-gate defect catalogued in
    `docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`: a condition
    that cannot pass teaches people to bypass it, and it contradicted the principal's other
    standing instruction to use every subscription.

    So: apply every native cap the CLI does offer, and let the caller bound the rest. The
    caller already enforces a wall-clock timeout and kills the process tree, which is what
    actually makes an arm bounded on a CLI with no native flag.

    **What this does NOT achieve, stated rather than implied:** no installed CLI exposes a
    real per-run token cap, so token bounding is only available through the pool ceiling in
    `budget.py`, not per arm. A wall-clock bound is also strictly weaker than a turn cap --
    an arm can burn many turns quickly inside its window. Both gaps are real and neither is
    closed here.
    """
    if max_turns <= 0 or max_tokens <= 0:
        return (
            f"refusing {harness_id}: hard turn and token caps must be positive integers"
        )
    present = set(optional_flags(help_blob, "--max-turns", "--max-tokens"))
    flags: list[str] = []
    if "--max-turns" in present:
        flags += ["--max-turns", str(max_turns)]
    if "--max-tokens" in present:
        flags += ["--max-tokens", str(max_tokens)]
    return flags


def inspect_uncommitted_tracked(cwd: Path) -> tuple[bool, tuple[str, ...]]:
    """Tracked paths that differ from HEAD. Untracked files are not output.

    The incumbent is `git status --porcelain --untracked-files=no`, already
    used here by EXP-96 to refuse a dirty measurement corpus. [measured]
    A failed inspection is not a clean tree (F-09).
    """
    git = which_binary("git")
    if git is None:
        return False, ()
    try:
        completed = subprocess.run(
            [
                git,
                "-C",
                str(cwd.resolve()),
                "-c",
                "core.quotepath=false",
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=dispatch_vocabulary.GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ()
    if completed.returncode != 0:
        return False, ()
    paths: set[str] = set()
    for raw in (completed.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        remainder = raw[3:]
        if " -> " in remainder:
            left, right = remainder.split(" -> ", 1)
            paths.add(left)
            paths.add(right)
        else:
            paths.add(remainder)
    return True, tuple(sorted(paths))


def write_brief(
    run_dir: Path,
    task: str,
    *,
    log_dir: Path | None = None,
    in_flight: str = "",
    claim_run_id: str | None = None,
    assembly: instructions.Assembly | None = None,
) -> Path:
    """Write the task plus its assembled context so the child is not amnesiac.

    Cross-harness memory is the trajectory. Until 21 August 2026 this function
    wrote the task alone, so Cursor could not see what Codex had just done.

    The pack is written to `recall.md` beside the brief and referenced from it,
    and also embedded — the embed is what a child that reads only its brief still
    sees. Both are bounded at RECALL_LIMIT_CHARS; the bound is the point, because
    an unbounded coordination section crowds the task out of the context window.
    An assembly supplies the same pack without a second trajectory read and adds
    the other instruction layers. `in_flight` is the live-claims table rendered
    by the caller.

    `claim_run_id` is the run id the claim covering this work was opened under
    (the parent's, for a fan-out child). The pre-commit gate refuses a commit
    that does not name its committer while claims are live, so the brief hands
    the run its badge; the gate, not this paragraph, is the enforcement.
    """
    path = (run_dir / "brief.md").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = task if task.endswith("\n") else task + "\n"
    if claim_run_id is not None:
        body += (
            "\n---\n\n## Your commit badge\n\n"
            "This run's work is claimed in the trajectory under run id "
            f"`{claim_run_id}`. While any dispatch claim is live in this "
            "worktree, the pre-commit gate refuses a commit that does not name "
            "its committer, and a commit staging a path another live run claims "
            "is refused. Commit with:\n\n"
            f"    CONSILIENT_RUN_ID={claim_run_id} git commit ...\n\n"
            "If this dispatch declared no --claim paths, the gate also needs the "
            "paths you are committing: CONSILIENT_COMMIT_PATHS=path/one,path/two. "
            "Stage only paths you created or this brief named; never "
            "`git add -A`.\n"
        )
    if assembly is not None:
        recall = assembly.recall_pack
        body += "\n---\n\n"
        if recall.strip() and "No events in log" not in recall:
            recall_path = (run_dir / "recall.md").resolve()
            recall_path.write_text(recall, encoding="utf-8", newline="\n")
            body += (
                "## Context from the trajectory\n\n"
                "A verbatim recall pack is recorded at `recall.md` beside this brief "
                f"(bound: {assembly.recall_limit_chars} characters) and assembled below.\n\n"
            )
        if in_flight.strip():
            body += in_flight.strip() + "\n\n"
        body += "---\n\n" + assembly.text.rstrip() + "\n"
    elif log_dir is not None:
        try:
            recall = pack_recall(
                Path(log_dir), query=task[:240], limit_chars=RECALL_LIMIT_CHARS
            )
        except (OSError, ValueError):
            recall = ""
        if recall.strip() and "No events in log" not in recall:
            recall_path = (run_dir / "recall.md").resolve()
            recall_path.write_text(recall, encoding="utf-8", newline="\n")
            body += (
                "\n---\n\n## Context from the trajectory\n\n"
                "A verbatim recall pack is recorded at `recall.md` beside this brief "
                f"(bound: {RECALL_LIMIT_CHARS} characters) and embedded below.\n\n"
            )
            if in_flight.strip():
                body += in_flight.strip() + "\n\n"
            body += "---\n\n" + recall
            if not body.endswith("\n"):
                body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def _claim_conflict_refusal(
    *,
    log_dir: Path,
    ts: str,
    run_id: str,
    task: str,
    cwd: Path,
    hit: tuple[coordination.Claim, str, str],
    live: tuple[coordination.Claim, ...],
) -> tuple[dict[str, object], int]:
    """A second dispatch claiming an overlapping path is refused, and the refusal is
    recorded like every other — the refusal IS the coordination mechanism working."""
    claim, requested, held = hit
    reason = (
        f"claims overlap a live dispatch: {claim.ticket} (run {claim.run_id}, "
        f"{claim.actor}) holds {held!r} until {claim.expires_at}; this dispatch asked "
        f"for {requested!r}. Refusing rather than admitting two agents to the same "
        "path — re-dispatch when the live claim completes or expires."
    )
    considered = [
        f"{item.ticket} holds {list(item.paths) or ['(no paths declared)']}"
        for item in live
    ]
    recorded = record_refusal(
        log_dir,
        ts=ts,
        run_id=run_id,
        task=task,
        cwd=str(cwd),
        reason=reason,
        considered=considered,
        attempted=f"dispatch claiming {requested!r}",
    )
    payload = {
        "status": "refused",
        "reason": reason,
        "considered": considered,
        "run_id": run_id,
        "cwd": str(cwd),
        "conflict": {"ticket": claim.ticket, "requested": requested, "held": held},
        "recorded": str(log_dir / f"{ts[:10]}.jsonl"),
        "event": recorded["event"],
    }
    return payload, _exit_for("refused")


class _ProofObserver:
    """The outer sandbox. It records and refuses; the adapter cannot see it."""

    def __init__(
        self, scratch: Path, enclosing: Path, verifier_policy_digest: str
    ) -> None:
        self.scratch = scratch
        self.enclosing = enclosing
        self.observed_verifier_policy = verifier_policy_digest
        self.escaped: list[str] = []
        self.residuals: list[str] = ["elapsed_time"]
        self.log: list[dict[str, object]] = []

    def _deny(self, kind: str, label: str) -> None:
        self.escaped.append(label)
        self.log.append({"step": kind, "allowed": False, "detail": label})

    def run(self, steps: object) -> str:
        denied = False
        for step in steps if isinstance(steps, Sequence) else ():
            item = step if isinstance(step, Mapping) else {}
            kind = str(item.get("kind", ""))
            if kind == "write":
                target = (self.scratch / str(item.get("path", ""))).resolve()
                if not target.is_relative_to(self.enclosing):
                    self._deny(kind, "out_of_root")
                    denied = True
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(item.get("content", "")), encoding="utf-8")
                self.log.append(
                    {
                        "step": kind,
                        "allowed": True,
                        "detail": target.relative_to(self.enclosing).as_posix(),
                    }
                )
            elif kind == "process":
                residuals = item.get("residuals", ())
                self.residuals.extend(
                    str(name)
                    for name in (residuals if isinstance(residuals, Sequence) else ())
                )
                self.log.append(
                    {"step": kind, "allowed": True, "detail": "residual_only"}
                )
            elif kind == "change_verifier_policy":
                self.observed_verifier_policy = str(item.get("digest", ""))
                self.log.append(
                    {"step": kind, "allowed": True, "detail": "verifier_policy"}
                )
            elif kind in _PROOF_ESCAPES:
                self._deny(kind, _PROOF_ESCAPES[kind])
                denied = True
            else:
                # ponytail: an unknown step kind fails closed rather than passing.
                self._deny(kind, "unknown_step")
                denied = True
        return "failed" if denied else "succeeded"
