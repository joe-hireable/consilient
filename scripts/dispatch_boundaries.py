"""The lines this harness will not cross, and the surface that cannot reopen them.

The instance cwd allowlist is read here. A missing file means no extra roots, a
malformed file fails closed, and a filesystem root in the list is refused so a typo
cannot authorise the machine. The principal names supervised roots under ADR-0039 and
ADR-0063; the product default is still refuse-everything-else, and naming a root does
not pass Gate B.

The held-out audit runs after a child exits. It writes the checker's explicit local
inputs — stdout, stderr and the diff — and returns a VOID measurement rather than a pass
whenever any of them cannot be produced, because an audit that cannot see its inputs has
audited nothing.

The isolated recovery proof is handed a new scratch root and a verifier log and nothing
else. No live target, network, credential, provider or spend handle is reachable from
that signature, which is what makes it a proof rather than a rehearsal against the thing
it is meant to protect; the pure verdict belongs to the product package, which is given
observations and never the adapter's own account of what it did.

The argument parser belongs with them for the same reason. It is the whole surface a
user can reach, and what it deliberately does not offer — an override for the working
directory — is as much a boundary as any check above it."""

from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
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

from consilient.effects import (
    EffectManifest,
    ProofObservation,
    RecoveryProof,
    canonical_state_digest,
    evaluate_recovery_proof,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_launch
import dispatch_vocabulary
from dispatch_evidence import (
    _capture_source,
    _scan_enclosing,
)

from dispatch_launch import (
    DEFAULT_ALLOWED_CWDS,
    DEFAULT_HEADROOM,
    DEFAULT_LOG,
    DEFAULT_RUNS,
    HELDOUT_ISOLATION_CHECKER,
    cursor_native,
    wsl_bridge,
)

from dispatch_preflight import (
    _ProofObserver,
)

from dispatch_vocabulary import (
    CURSOR_WSL_BINARY,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_TURNS,
    DEFAULT_TIMEOUT_S,
    GIT_ENV,
    _ordered_unique,
    _run_probe,
    _scan_state,
    _version_from,
    positive_int,
    which_binary,
)

__all__ = [
    "CURSOR_WSL_BINARY",
    "DEFAULT_ALLOWED_CWDS",
    "DEFAULT_HEADROOM",
    "DEFAULT_LOG",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_TURNS",
    "DEFAULT_RUNS",
    "DEFAULT_TIMEOUT_S",
    "GIT_ENV",
    "HELDOUT_ISOLATION_CHECKER",
    "_ProofObserver",
    "_capture_source",
    "_ordered_unique",
    "_run_probe",
    "_scan_enclosing",
    "_scan_state",
    "_version_from",
    "build_parser",
    "cursor_native",
    "heldout_contract_audit",
    "load_allowed_roots",
    "positive_int",
    "run_isolated_recovery_proof",
    "which_binary",
    "wsl_bridge",
]


def heldout_contract_audit(
    contract: str, *, run_dir: Path, run_id: str, cwd: Path, stdout: str, stderr: str
) -> str | None:
    """Return an audit refusal after writing the checker’s explicit local inputs."""
    try:
        audit_stdout = run_dir / f"{run_id}.out"
        audit_stderr = run_dir / f"{run_id}.err"
        audit_diff = run_dir / f"{run_id}.diff"
        audit_stdout.write_text(stdout, encoding="utf-8", newline="\n")
        audit_stderr.write_text(stderr, encoding="utf-8", newline="\n")
        git = which_binary("git")
        if git is None:
            return "held-out audit input is invalid; measurement VOID"
        completed = subprocess.run(
            [git, "-C", str(cwd), "diff", "--no-ext-diff"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=dispatch_vocabulary.GIT_ENV,
            check=False,
        )
        if completed.returncode != 0:
            return "held-out audit input is invalid; measurement VOID"
        audit_diff.write_text(completed.stdout, encoding="utf-8", newline="\n")
        spec = importlib.util.spec_from_file_location(
            "check_heldout_isolation", HELDOUT_ISOLATION_CHECKER
        )
        if spec is None or spec.loader is None:
            return "held-out audit input is invalid; measurement VOID"
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        audit_reason = cast(Callable[..., str | None], checker.audit_reason)
        return audit_reason(
            contract, runs_dir=str(run_dir), uid=run_id, diff=str(audit_diff)
        )
    except (OSError, subprocess.SubprocessError):
        return "held-out audit input is invalid; measurement VOID"


def _cursor_help_and_about() -> tuple[bool, str | None, str]:
    native = dispatch_launch.cursor_native()
    if native is not None:
        code, out, err = _run_probe([native, "--version"])
        version = _version_from(out) or _version_from(err)
        if code == 0 and (out or version):
            return True, version or out.splitlines()[0], native
        code, out, err = _run_probe([native, "about", "--format", "json"])
        if code == 0 and out:
            try:
                payload = json.loads(out)
            except json.JSONDecodeError:
                payload = {}
            version = payload.get("cliVersion") if isinstance(payload, dict) else None
            if isinstance(version, str) and version.strip():
                return True, version, native
        return False, None, err or out or native

    bridge = dispatch_launch.wsl_bridge()
    if bridge is None or os.name != "nt":
        return (
            False,
            None,
            (
                f"cursor-agent is WSL-only; looked for {CURSOR_WSL_BINARY} and no wsl bridge"
            ),
        )
    inner = "cursor-agent --version || cursor-agent about --format json"
    code, out, err = _run_probe([bridge, "-e", "bash", "-lc", inner])
    version = _version_from(out)
    if version is None and out:
        try:
            payload = json.loads(out)
            if isinstance(payload, dict) and isinstance(payload.get("cliVersion"), str):
                version = payload["cliVersion"]
        except json.JSONDecodeError:
            version = None
    if code == 0 and (version or out):
        return True, version or "installed", f"{bridge} + cursor-agent"
    return False, None, err or out or "wsl cursor-agent probe failed"


def load_allowed_roots(path: Path | None = None) -> tuple[Path, ...]:
    """Instance cwd allowlist. Missing file means no extra roots. Malformed file fails closed.

    This does not pass Gate B. The principal names supervised roots; the product default is
    still refuse-everything-else. A filesystem root in the list is refused so a typo cannot
    authorise the machine.
    """
    source = path if path is not None else DEFAULT_ALLOWED_CWDS
    if not source.is_file():
        return ()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"allowed-cwds file {source} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError(
            f"allowed-cwds file {source} must be a JSON object with a roots list"
        )
    listed = raw.get("roots", [])
    if not isinstance(listed, list):
        raise ValueError(
            f"allowed-cwds file {source} field 'roots' must be a list of paths"
        )
    roots: list[Path] = []
    for item in listed:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"allowed-cwds file {source} roots must be non-empty strings"
            )
        try:
            candidate = Path(item).expanduser().resolve()
        except OSError as exc:
            raise ValueError(
                f"allowed-cwds file {source} has an unresolvable root {item!r}: {exc}"
            ) from exc
        if candidate.parent == candidate:
            raise ValueError(
                f"refusing filesystem root {candidate} in allowed-cwds: name a repository, "
                "not a volume"
            )
        if candidate.is_dir():
            roots.append(candidate)
    return tuple(dict.fromkeys(roots))


def _listed_artefact_bindings(
    manifest_path: Path, workspace: Path
) -> list[dict[str, object]]:
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return [{"status": "refused", "reason": "artefact manifest is not valid JSON"}]
    if not isinstance(raw, dict):
        return [{"status": "refused", "reason": "artefact manifest must be an object"}]
    rows = raw.get("artefacts")
    if rows is None:
        return []
    if not isinstance(rows, list):
        return [{"status": "refused", "reason": "artefacts must be a list"}]
    bindings: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            bindings.append(
                {"status": "refused", "reason": f"artefacts[{index}] must be an object"}
            )
            continue
        path_value = row.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            bindings.append(
                {"status": "refused", "reason": f"artefacts[{index}] has no path"}
            )
            continue
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = workspace / path_value
        bindings.append(
            _capture_source(
                candidate, workspace=workspace, media_type="application/octet-stream"
            )
        )
    return bindings


def run_isolated_recovery_proof(
    scratch_root: Path,
    verifier_log: Path,
    *,
    identities: Mapping[str, str],
    manifest: EffectManifest,
    start_files: Mapping[str, str],
    adapter: Mapping[str, object],
    sandbox_policy_digest: str,
    verifier_policy_digest: str,
) -> RecoveryProof:
    """Run one scratch-only recovery proof and return the pure verdict.

    The runner is handed a new scratch root and a verifier log and nothing else:
    no live target, network, credential, provider or spend handle is reachable
    from this signature, which is what makes the proof isolated rather than a
    rehearsal against the thing it is meant to protect.
    """

    scratch = Path(scratch_root).resolve()
    enclosing = scratch.parent
    scratch.mkdir(parents=True, exist_ok=True)
    for relative, content in start_files.items():
        seeded = scratch / relative
        seeded.parent.mkdir(parents=True, exist_ok=True)
        seeded.write_text(content, encoding="utf-8")

    start_digest = canonical_state_digest(_scan_state(scratch))
    enclosing_before = canonical_state_digest(_scan_enclosing(enclosing, scratch))

    observer = _ProofObserver(scratch, enclosing, verifier_policy_digest)
    forward_status = observer.run(adapter.get("forward", ()))
    forward_digest = canonical_state_digest(_scan_state(scratch))
    inverse_status = observer.run(adapter.get("inverse", ()))
    end_digest = canonical_state_digest(_scan_state(scratch))
    enclosing_after = canonical_state_digest(_scan_enclosing(enclosing, scratch))

    log_path = Path(verifier_log)
    lines = [
        json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in observer.log
    ]
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(line + "\n" for line in lines))
    observer_log_digest = hashlib.sha256(log_path.read_bytes()).hexdigest()

    declared_expected = manifest.expected_state
    expected_digest = (
        str(declared_expected.get("commitment", ""))
        if isinstance(declared_expected, Mapping)
        else ""
    )
    # An expected state the manifest never committed to is unmatchable, and
    # `evaluate_recovery_proof` reports it as a capability gap before comparing.
    if len(expected_digest) != 64:
        expected_digest = "0" * 64

    return evaluate_recovery_proof(
        manifest=manifest,
        observation=ProofObservation(
            start_state_digest=start_digest,
            forward_state_digest=forward_digest,
            end_state_digest=end_digest,
            enclosing_before_digest=enclosing_before,
            enclosing_after_digest=enclosing_after,
            expected_state_digest=expected_digest,
            forward_status=forward_status,
            inverse_status=inverse_status,
            sandbox_policy_digest=sandbox_policy_digest,
            verifier_policy_digest=verifier_policy_digest,
            observed_verifier_policy_digest=observer.observed_verifier_policy,
            observer_log_digest=observer_log_digest,
            escaped_attempts=_ordered_unique(observer.escaped),
            observed_residuals=_ordered_unique(observer.residuals),
        ),
        **identities,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatch a task to a subscription harness. Not a consil subcommand."
    )
    parser.add_argument("task", nargs="?", help="the task to run")
    parser.add_argument(
        "--task-file", help="read the task from this file (preferred for long briefs)"
    )
    parser.add_argument(
        "--capability-inventory",
        help="JSON allowlist of available tools, MCPs, skills, plugins and connections",
    )
    parser.add_argument(
        "--capability-request",
        help="JSON capabilities requested for this task; requires --capability-inventory",
    )
    parser.add_argument(
        "--cwd",
        help="working directory; this repository, a worktree of it, or an instance-allowlisted root",
    )
    parser.add_argument(
        "--harness",
        help="run this harness; still refuses an exhausted pool without --allow-exhausted",
    )
    parser.add_argument(
        "--fan-out",
        action="store_true",
        help="run the same task on two harnesses from different model families",
    )
    parser.add_argument(
        "--allow-exhausted",
        action="store_true",
        help="spend an exhausted pool; default is to refuse",
    )
    parser.add_argument(
        "--model", help="model id (cursor-composer defaults to composer-2.5)"
    )
    parser.add_argument(
        "--family",
        help="model family to pick from (e.g. grok, kimi, composer); automatic selection "
        "prefers the idlest registered pool within the family",
    )
    parser.add_argument(
        "--claim",
        action="append",
        default=None,
        metavar="PATH",
        help="declare a path this dispatch intends to touch; repeatable. A second live "
        "dispatch claiming an overlapping path is refused. Claims are trajectory events "
        "with an expiry (timeout + grace), so a crashed dispatcher cannot hold one.",
    )
    parser.add_argument(
        "--heldout-contract",
        help="held-out contract path; refused when reachable from brief, worktree or claims",
    )
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-turns", type=positive_int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--max-tokens", type=positive_int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--headroom", default=str(dispatch_launch.DEFAULT_HEADROOM))
    parser.add_argument("--runs", default=str(DEFAULT_RUNS))
    parser.add_argument(
        "--probe", action="store_true", help="probe installed harnesses and exit"
    )
    parser.add_argument(
        "--supervise",
        action="store_true",
        help="report open dispatches that produced no artefact within the start "
        "window, and exit non-zero if there are any. Reads files only; kills nothing.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="select (and print argv) without running"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--permissions",
        choices=("bypass", "prompt"),
        default=None,
        help="bypass (default) runs children without per-tool prompts; prompt leaves their ask-loop on. "
        "Overrides .harness/permissions.json.",
    )
    return parser
