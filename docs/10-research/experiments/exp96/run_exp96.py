"""EXP-96: two-corpus mutation-proxy measurement of verifier beta.

This does not compute human-verdict beta. It measures survival of seeded first-order
mutants under each repository's pytest + mypy + Ruff composite.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from consilient.beta import wilson  # noqa: E402

try:
    import mutmut.mutation.file_mutation as fm
except ImportError:
    fm = None  # type: ignore[assignment]

EXPERIMENT_ID = "EXP-96"
CONSILIENT_REVISION = "e7a9940"
ITSDANGEROUS_REVISION = "096c8d42545d3b68ea21a4f890fb2b2d8979c0bd"
ITSDANGEROUS_REMOTE = "https://github.com/pallets/itsdangerous.git"
MUTMUT_VERSION = "3.7.0"
LIBCST_VERSION = "1.9.0"
CHECK_TIMEOUT_S = 60
MIN_CLASSIFIABLE = 50
MAX_HALF_WIDTH = 0.05
MAX_UNCLASSIFIABLE_RATE = 0.10
MAX_IDENTIFICATION_WIDTH = 0.10
FROZEN_EQUIVALENT_CLASSES = frozenset(
    {
        "docstring_mutation",
        "sql_case_insensitive_mutation",
        "cli_help_metadata_string",
        "dataclass_default_caveat_string",
    }
)
OPERATOR_FAMILIES = frozenset(
    {
        "comparison",
        "boolean_logical",
        "binary_arithmetic",
        "unary",
        "constant_literal",
        "statement",
    }
)
STRING_NODE_TYPES = frozenset(
    {"SimpleString", "FormattedString", "FormattedStringText"}
)

WORKER_BASE: Path | None = None
WORKER_PARENT: Path | None = None
WORKER_SPEC: dict[str, Any] | None = None

EXPECTED_CONSILIENT_TOOLS = {
    "pytest": "9.0.3",
    "mypy": "2.3.1",
    "ruff": "0.15.10",
}
EXPECTED_ITSDANGEROUS_TOOLS = {
    "freezegun": "1.4.0",
    "iniconfig": "2.0.0",
    "itsdangerous": "2.2.0",
    "mypy": "1.9.0",
    "packaging": "24.0",
    "pluggy": "1.4.0",
    "pytest": "8.1.1",
    "python-dateutil": "2.9.0.post0",
    "ruff": "0.3.7",
    "six": "1.16.0",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def acquire_output_lock(output: Path) -> tuple[Path, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = output.with_suffix(output.suffix + ".lock")
    token = f"{os.getpid()}-{time.time_ns()}"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"EXP-96 output is locked: {lock}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps({"pid": os.getpid(), "token": token}))
    return lock, token


def release_output_lock(lock: Path, token: str) -> None:
    try:
        owner = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if owner.get("pid") == os.getpid() and owner.get("token") == token:
        lock.unlink(missing_ok=True)


def scrubbed_environment(pythonpath: Path | None = None) -> dict[str, str]:
    blocked_prefixes = ("GIT_", "MYPY_", "PYTEST_", "RUFF_")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(blocked_prefixes)
        and key.upper() not in {"PYTHONHOME", "VIRTUAL_ENV"}
    }
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath.resolve())
    return env


def git_text(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo.resolve()), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=scrubbed_environment(),
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def normalise_remote(value: str) -> str:
    return value.rstrip("/").removesuffix(".git").casefold()


def verify_external_repo(repo: Path) -> dict[str, str]:
    revision = git_text(repo, "rev-parse", "HEAD")
    remote = git_text(repo, "remote", "get-url", "origin")
    dirty = git_text(repo, "status", "--porcelain", "--untracked-files=no")
    if revision != ITSDANGEROUS_REVISION:
        raise RuntimeError(
            f"itsdangerous revision mismatch: expected {ITSDANGEROUS_REVISION}, got {revision}"
        )
    if normalise_remote(remote) != normalise_remote(ITSDANGEROUS_REMOTE):
        raise RuntimeError(f"itsdangerous remote mismatch: {remote}")
    if dirty:
        raise RuntimeError("itsdangerous has tracked changes")
    return {"revision": revision, "remote": ITSDANGEROUS_REMOTE}


def clone_revision(repo: Path, revision: str, destination: Path) -> None:
    result = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-checkout",
            "--local",
            str(repo.resolve()),
            str(destination.resolve()),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=scrubbed_environment(),
        timeout=120,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "local git clone failed")
    git_text(destination, "checkout", "--quiet", "--detach", revision)


def archive_revision(repo: Path, revision: str, destination: Path) -> None:
    archive = destination.with_suffix(".tar")
    destination.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo.resolve()),
            "archive",
            "--format=tar",
            f"--output={archive.resolve()}",
            revision,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=scrubbed_environment(),
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git archive failed")
    with tarfile.open(archive) as tar:
        tar.extractall(destination, filter="data")
    archive.unlink()


def input_manifest(root: Path) -> dict[str, str]:
    ignored = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not any(part in ignored for part in path.relative_to(root).parts)
        and path.suffix != ".pyc"
    }


class _WindowsJob:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000
        if not kernel32.SetInformationJobObject(
            handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ) or not kernel32.AssignProcessToJobObject(
            handle, wintypes.HANDLE(process._handle)
        ):
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ctypes.WinError(error)
        self._kernel32 = kernel32
        self._handle = handle

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _kill_process_tree(
    process: subprocess.Popen[bytes], job: _WindowsJob | None = None
) -> None:
    if job is not None:
        job.close()
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass


def run_command(
    argv: list[str], cwd: Path, env: dict[str, str], timeout_s: int, receipt_dir: Path
) -> dict[str, Any]:
    stdout_path = receipt_dir / "stdout.txt"
    stderr_path = receipt_dir / "stderr.txt"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    started = time.perf_counter()
    job: _WindowsJob | None = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                **kwargs,
            )
        except OSError as exc:
            return {
                "outcome": "execution_error",
                "returncode": None,
                "duration_s": time.perf_counter() - started,
                "error": type(exc).__name__,
            }
        if os.name == "nt":
            try:
                job = _WindowsJob(process)
            except OSError as exc:
                _kill_process_tree(process)
                return {
                    "outcome": "execution_error",
                    "returncode": None,
                    "duration_s": time.perf_counter() - started,
                    "error": type(exc).__name__,
                }
        timed_out = False
        try:
            process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_process_tree(process, job)
            job = None
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        finally:
            if job is not None:
                job.close()
    stdout_bytes = stdout_path.read_bytes()
    stderr_bytes = stderr_path.read_bytes()
    return {
        "outcome": "timeout"
        if timed_out
        else "accepted"
        if process.returncode == 0
        else "rejected"
        if process.returncode == 1
        else "execution_error",
        "returncode": process.returncode,
        "duration_s": time.perf_counter() - started,
        "stdout_sha256": sha256_bytes(stdout_bytes),
        "stderr_sha256": sha256_bytes(stderr_bytes),
        "stdout_tail": stdout_bytes.decode("utf-8", errors="replace")[-2000:],
        "stderr_tail": stderr_bytes.decode("utf-8", errors="replace")[-2000:],
        "error": (
            "unexpected_returncode"
            if not timed_out and process.returncode not in {0, 1}
            else None
        ),
    }


def changed_line(original: str, mutated: str) -> int:
    import difflib

    line_number = 1
    for line in difflib.ndiff(original.splitlines(), mutated.splitlines()):
        if line.startswith("  "):
            line_number += 1
        elif line.startswith(("- ", "+ ")):
            return line_number
    return 1


def docstring_lines(source: str) -> set[int]:
    lines: set[int] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                lines.update(
                    range(first.lineno, (first.end_lineno or first.lineno) + 1)
                )
    return lines


def operator_family(original_node: Any, original: str) -> str:
    name = type(original_node).__name__
    if name in {"Comparison", "ComparisonTarget"}:
        family = "comparison"
    elif name == "BooleanOperation" or original.strip() in {"True", "False"}:
        family = "boolean_logical"
    elif name in {"BinaryOperation", "AugAssign"}:
        family = "binary_arithmetic"
    elif name == "UnaryOperation":
        family = "unary"
    elif name in {"Integer", "Float", "Imaginary", "SimpleString", "FormattedString"}:
        family = "constant_literal"
    else:
        family = "statement"
    assert family in OPERATOR_FAMILIES
    return family


def is_sql_case_equivalent(original: str, mutated: str) -> bool:
    original_folded = original.strip("'\"").casefold()
    mutated_folded = mutated.strip("'\"").casefold()
    keywords = (
        "select",
        "insert",
        "update",
        "delete",
        "create",
        "table",
        "values",
        "from",
        "where",
        "count",
        "primary key",
        "unique",
    )
    return original_folded == mutated_folded and any(
        keyword in original_folded for keyword in keywords
    )


def frozen_equivalent_reason(record: dict[str, Any]) -> str | None:
    original = record["original_node"]
    mutated = record["mutated_node"]
    file = record["file"]
    original_line = record["original_line"]
    if record["docstring_only"]:
        return "docstring_mutation"
    if is_sql_case_equivalent(original, mutated):
        return "sql_case_insensitive_mutation"
    cli_metadata_value_changed = (
        file == "src/consilient/cli.py"
        and record["original_node_type"] in STRING_NODE_TYPES
        and record["mutated_node_type"] in STRING_NODE_TYPES
        and any(
            re.search(rf"\b{marker}\s*=\s*{re.escape(original)}", original_line)
            for marker in ("help", "description", "epilog", "metavar")
        )
    )
    if cli_metadata_value_changed:
        return "cli_help_metadata_string"
    if (
        file == "src/consilient/beta.py"
        and record["original_node_type"] in STRING_NODE_TYPES
        and record["mutated_node_type"] in STRING_NODE_TYPES
        and (
            "caveat: str = field" in original_line
            or 'default="beta is conditional' in original_line
        )
    ):
        return "dataclass_default_caveat_string"
    return None


def ambiguous_presentation(record: dict[str, Any]) -> bool:
    node_types = {record["original_node_type"], record["mutated_node_type"]}
    if node_types & STRING_NODE_TYPES:
        return True
    text = (
        f"{record['original_node']}\n{record['mutated_node']}\n"
        f"{record['original_line']}\n{record['mutated_line']}"
    )
    return record["original_node_type"] in {"AnnAssign", "Param"} and (
        "field(" in text or "default" in text or "Literal[" in text
    )


def classify_mutant(record: dict[str, Any]) -> tuple[str, str]:
    equivalent = frozen_equivalent_reason(record)
    if equivalent is not None:
        assert equivalent in FROZEN_EQUIVALENT_CLASSES
        return "equivalent", equivalent
    if ambiguous_presentation(record):
        return "unclassifiable", "presentation_or_metadata_without_contract_oracle"
    return "true_defect", "seeded_non_presentation_operator"


def generate_tasks(spec: dict[str, Any]) -> list[tuple[dict[str, Any], str]]:
    if fm is None:
        raise RuntimeError("EXP-96 requires mutmut 3.7.0")
    tasks: list[tuple[dict[str, Any], str]] = []
    next_id = 0
    root = Path(spec["root"])
    source_root = root / spec["source_dir"]
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        module, mutations, _, _ = fm.create_mutations(relative, source)
        documentation = docstring_lines(source)
        for mutation in mutations:
            mutated_tree = fm.deep_replace(
                module, mutation.original_node, mutation.mutated_node
            )
            mutated_code = mutated_tree.code
            line = changed_line(source, mutated_code)
            mutated_lines = mutated_code.splitlines()
            original_node = module.code_for_node(mutation.original_node)
            mutated_node = module.code_for_node(mutation.mutated_node)
            record = {
                "id": f"{spec['name']}:{next_id:05d}",
                "corpus": spec["name"],
                "file": relative,
                "line": line,
                "operator_family": operator_family(
                    mutation.original_node, original_node
                ),
                "original_node_type": type(mutation.original_node).__name__,
                "mutated_node_type": type(mutation.mutated_node).__name__,
                "original_node": original_node[:240],
                "mutated_node": mutated_node[:240],
                "original_line": (
                    source_lines[line - 1][:240]
                    if 0 < line <= len(source_lines)
                    else ""
                ),
                "mutated_line": (
                    mutated_lines[line - 1][:240]
                    if 0 < line <= len(mutated_lines)
                    else ""
                ),
                "docstring_only": line in documentation,
                "mutated_file_sha256": sha256_bytes(mutated_code.encode("utf-8")),
            }
            tasks.append((record, mutated_code))
            next_id += 1
    return tasks


def init_worker(base_root: str, worker_parent: str, spec: dict[str, Any]) -> None:
    global WORKER_BASE, WORKER_PARENT, WORKER_SPEC
    WORKER_BASE = Path(base_root)
    WORKER_PARENT = Path(worker_parent)
    WORKER_SPEC = spec


def copy_corpus(base: Path, destination: Path) -> None:
    git_dir = base / ".git"
    shutil.copytree(
        base,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"
        ),
    )
    if git_dir.is_dir():
        (destination / ".git").write_text(
            f"gitdir: {git_dir.resolve().as_posix()}\n",
            encoding="utf-8",
            newline="\n",
        )


def run_mutant(task: tuple[dict[str, Any], str]) -> dict[str, Any]:
    assert (
        WORKER_BASE is not None
        and WORKER_PARENT is not None
        and WORKER_SPEC is not None
    )
    record, mutated_code = task
    semantic_class, classification_reason = classify_mutant(record)
    record["semantic_class"] = semantic_class
    record["classification_reason"] = classification_reason
    checks: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(
        prefix=f"mutant-{record['id'].replace(':', '-')}-", dir=WORKER_PARENT
    ) as temporary:
        worker_dir = Path(temporary) / "repo"
        copy_corpus(WORKER_BASE, worker_dir)
        target = worker_dir / record["file"]
        target.write_text(mutated_code, encoding="utf-8", newline="\n")
        if sha256_file(target) != record["mutated_file_sha256"]:
            raise RuntimeError("mutant bytes differ from the generated receipt")
        expected_input = input_manifest(worker_dir)
        env = scrubbed_environment(worker_dir / "src")
        receipt_root = Path(temporary) / "receipts"
        for check in WORKER_SPEC["checks"]:
            name = check["name"]
            result = run_command(
                check["argv"],
                worker_dir,
                env,
                CHECK_TIMEOUT_S,
                receipt_root / name,
            )
            if input_manifest(worker_dir) != expected_input:
                result["outcome"] = "execution_error"
                result["error"] = "input_rewritten_by_check"
            result.pop("stdout_tail", None)
            result.pop("stderr_tail", None)
            checks[name] = result
            if result["outcome"] in {"execution_error", "timeout"}:
                break
    outcomes = [result["outcome"] for result in checks.values()]
    if len(checks) != len(WORKER_SPEC["checks"]) or any(
        outcome in {"execution_error", "timeout"} for outcome in outcomes
    ):
        record["composite_outcome"] = "execution_error"
    elif all(outcome == "accepted" for outcome in outcomes):
        record["composite_outcome"] = "accepted"
        record["survivor_class"] = semantic_class
    else:
        record["composite_outcome"] = "rejected"
    record["checks"] = checks
    return record


def run_baseline(spec: dict[str, Any]) -> dict[str, Any]:
    root = Path(spec["root"])
    before = input_manifest(root)
    env = scrubbed_environment(root / "src")
    results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(
        prefix=f"exp96-baseline-{spec['name']}-"
    ) as receipts:
        for check in spec["checks"]:
            result = run_command(
                check["argv"],
                root,
                env,
                CHECK_TIMEOUT_S,
                Path(receipts) / check["name"],
            )
            results[check["name"]] = result
            if result["outcome"] != "accepted":
                break
    unchanged = before == input_manifest(root)
    return {
        "checks": results,
        "accepted": len(results) == len(spec["checks"])
        and all(result["outcome"] == "accepted" for result in results.values())
        and unchanged,
        "inputs_unchanged": unchanged,
    }


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarise_corpus(
    rows: list[dict[str, Any]],
    generated: int,
    baseline_ok: bool,
    inputs_unchanged: bool,
) -> dict[str, Any]:
    errors = sum(row.get("composite_outcome") == "execution_error" for row in rows)
    killed = sum(
        row.get("composite_outcome") == "rejected"
        and row.get("semantic_class") == "true_defect"
        for row in rows
    )
    true_defects = sum(
        row.get("composite_outcome") == "accepted"
        and row.get("semantic_class") == "true_defect"
        for row in rows
    )
    equivalent = sum(
        row.get("composite_outcome") != "execution_error"
        and row.get("semantic_class") == "equivalent"
        for row in rows
    )
    equivalent_accepted = sum(
        row.get("composite_outcome") == "accepted"
        and row.get("semantic_class") == "equivalent"
        for row in rows
    )
    unclassifiable = sum(
        row.get("composite_outcome") != "execution_error"
        and row.get("semantic_class") == "unclassifiable"
        for row in rows
    )
    unclassifiable_accepted = sum(
        row.get("composite_outcome") == "accepted"
        and row.get("semantic_class") == "unclassifiable"
        for row in rows
    )
    unclassifiable_rejected = sum(
        row.get("composite_outcome") == "rejected"
        and row.get("semantic_class") == "unclassifiable"
        for row in rows
    )
    accounted = killed + true_defects + equivalent + unclassifiable + errors
    row_accounting_holds = generated == accounted == len(rows)
    identity_holds = errors == 0 and generated == accounted == len(rows)
    classifiable = killed + true_defects
    interval = wilson(true_defects, classifiable) if classifiable else None
    half_width = (interval[1] - interval[0]) / 2 if interval else None
    lower = rate(true_defects, killed + true_defects + unclassifiable_rejected)
    upper = rate(
        true_defects + unclassifiable_accepted,
        killed + true_defects + unclassifiable_accepted,
    )
    identification_width = (
        upper - lower if lower is not None and upper is not None else None
    )
    survivors = true_defects + equivalent_accepted + unclassifiable_accepted
    stopping_failures: list[str] = []
    if not baseline_ok:
        stopping_failures.append("baseline_failed")
    if not inputs_unchanged:
        stopping_failures.append("input_drift")
    if not identity_holds:
        stopping_failures.append("incomplete_census")
    if errors:
        stopping_failures.append("execution_error_or_timeout")
    if classifiable < MIN_CLASSIFIABLE:
        stopping_failures.append("fewer_than_50_classifiable_mutants")
    if half_width is None:
        stopping_failures.append("wilson_interval_unavailable")
    elif half_width > MAX_HALF_WIDTH:
        stopping_failures.append("wilson_half_width_above_0.05")
    contamination_reasons: list[str] = []
    if generated and unclassifiable / generated > MAX_UNCLASSIFIABLE_RATE:
        contamination_reasons.append("unclassifiable_rate_above_0.10")
    if (
        identification_width is not None
        and identification_width > MAX_IDENTIFICATION_WIDTH
    ):
        contamination_reasons.append("identification_width_above_0.10")
    measurement_complete = not stopping_failures
    contamination_rule_fired = bool(contamination_reasons)
    check_accepts = {
        name: sum(
            row.get("checks", {}).get(name, {}).get("outcome") == "accepted"
            for row in rows
        )
        for name in ("pytest", "mypy", "ruff")
    }
    return {
        "generated": generated,
        "rows": len(rows),
        "row_accounting_holds": row_accounting_holds,
        "census_identity_holds": identity_holds,
        "counts": {
            "K_true_defect_rejected": killed,
            "D_true_defect_survivors": true_defects,
            "E_equivalent_total": equivalent,
            "E_equivalent_survivors": equivalent_accepted,
            "U_unclassifiable_total": unclassifiable,
            "U_A_unclassifiable_survivors": unclassifiable_accepted,
            "U_R_unclassifiable_rejected": unclassifiable_rejected,
            "execution_errors": errors,
        },
        "check_accepts": check_accepts,
        "classifiable_mutation_beta": rate(true_defects, classifiable),
        "classifiable_n": classifiable,
        "wilson_interval_95": list(interval) if interval else None,
        "wilson_half_width": half_width,
        "partial_identification": [lower, upper],
        "partial_identification_width": identification_width,
        "contamination": {
            "known_equivalent_E_over_N": rate(equivalent, generated),
            "unresolved_U_over_N": rate(unclassifiable, generated),
            "possible_inertness_E_to_E_plus_U_over_N": [
                rate(equivalent, generated),
                rate(equivalent + unclassifiable, generated),
            ],
            "known_equivalent_survivor_share": rate(equivalent_accepted, survivors),
            "possible_inert_survivor_share": [
                rate(equivalent_accepted, survivors),
                rate(equivalent_accepted + unclassifiable_accepted, survivors),
            ],
        },
        "measurement_complete": measurement_complete,
        "stopping_failures": stopping_failures,
        "contamination_rule_fired": contamination_rule_fired,
        "contamination_reasons": contamination_reasons,
        "verdict": (
            "insufficient_evidence"
            if not measurement_complete
            else "complete_contamination_rule_fired"
            if contamination_rule_fired
            else "complete_decision_grade"
        ),
    }


def external_tool_versions(python: Path) -> dict[str, str]:
    code = (
        "import importlib.metadata as m, json, sys; "
        f"names={tuple(EXPECTED_ITSDANGEROUS_TOOLS)!r}; "
        "print(json.dumps({'isolated':sys.prefix != sys.base_prefix, "
        "'versions':{n:m.version(n) for n in names}}))"
    )
    result = subprocess.run(
        [str(python.resolve()), "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=scrubbed_environment(),
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip() or "cannot read itsdangerous tool versions"
        )
    identity = json.loads(result.stdout)
    versions = identity.get("versions")
    if identity.get("isolated") is not True or versions != EXPECTED_ITSDANGEROUS_TOOLS:
        raise RuntimeError(
            "itsdangerous interpreter is not the fixed isolated environment: "
            f"expected {EXPECTED_ITSDANGEROUS_TOOLS}, got {identity}"
        )
    return versions


def corpus_specs(
    consilient_root: Path, itsdangerous_root: Path, itsdangerous_python: Path
) -> list[dict[str, Any]]:
    host_python = str(Path(sys.executable).resolve())
    external_python = str(itsdangerous_python.resolve())
    return [
        {
            "name": "consilient",
            "root": str(consilient_root),
            "source_dir": "src/consilient",
            "checks": [
                {
                    "name": "pytest",
                    "argv": [
                        host_python,
                        "-B",
                        "-m",
                        "pytest",
                        "tests",
                        "-q",
                        "-p",
                        "no:cacheprovider",
                    ],
                },
                {
                    "name": "mypy",
                    "argv": [
                        host_python,
                        "-m",
                        "mypy",
                        "--strict",
                        "--no-incremental",
                        "src/consilient",
                    ],
                },
                {
                    "name": "ruff",
                    "argv": [host_python, "-m", "ruff", "check", "--no-cache", "."],
                },
            ],
        },
        {
            "name": "itsdangerous",
            "root": str(itsdangerous_root),
            "source_dir": "src/itsdangerous",
            "checks": [
                {
                    "name": "pytest",
                    "argv": [
                        external_python,
                        "-B",
                        "-m",
                        "pytest",
                        "tests",
                        "-q",
                        "-p",
                        "no:cacheprovider",
                    ],
                },
                {
                    "name": "mypy",
                    "argv": [external_python, "-m", "mypy", "--no-incremental"],
                },
                {
                    "name": "ruff",
                    "argv": [
                        external_python,
                        "-m",
                        "ruff",
                        "check",
                        "--no-fix",
                        "--no-cache",
                        ".",
                    ],
                },
            ],
        },
    ]


def _run_experiment(
    itsdangerous_repo: Path, itsdangerous_python: Path, output: Path, workers: int
) -> dict[str, Any]:
    started = time.perf_counter()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if fm is None:
        raise RuntimeError("EXP-96 requires mutmut 3.7.0")
    engine = {
        "mutmut": importlib.metadata.version("mutmut"),
        "libcst": importlib.metadata.version("libcst"),
    }
    if engine != {"mutmut": MUTMUT_VERSION, "libcst": LIBCST_VERSION}:
        raise RuntimeError(f"mutation engine mismatch: {engine}")
    host_tools = {
        name: importlib.metadata.version(name) for name in EXPECTED_CONSILIENT_TOOLS
    }
    if host_tools != EXPECTED_CONSILIENT_TOOLS:
        raise RuntimeError(
            f"Consilient tool mismatch: expected {EXPECTED_CONSILIENT_TOOLS}, got {host_tools}"
        )
    external_identity = verify_external_repo(itsdangerous_repo)
    external_tools = external_tool_versions(itsdangerous_python)
    harness_hash = sha256_file(Path(__file__))
    harness_commit = git_text(ROOT, "rev-parse", "HEAD")
    with tempfile.TemporaryDirectory(prefix="exp96-corpora-") as temporary:
        temporary_root = Path(temporary)
        consilient_base = temporary_root / "consilient"
        itsdangerous_base = temporary_root / "itsdangerous"
        clone_revision(ROOT, CONSILIENT_REVISION, consilient_base)
        archive_revision(itsdangerous_repo, ITSDANGEROUS_REVISION, itsdangerous_base)
        specs = corpus_specs(consilient_base, itsdangerous_base, itsdangerous_python)
        manifests = {spec["name"]: input_manifest(Path(spec["root"])) for spec in specs}
        baselines = {spec["name"]: run_baseline(spec) for spec in specs}
        generated: dict[str, int] = {}
        rows: dict[str, list[dict[str, Any]]] = {spec["name"]: [] for spec in specs}
        run_errors: dict[str, str] = {}

        if all(baseline["accepted"] for baseline in baselines.values()):
            for spec in specs:
                try:
                    tasks = generate_tasks(spec)
                    generated[spec["name"]] = len(tasks)
                    with tempfile.TemporaryDirectory(
                        prefix="exp96-workers-"
                    ) as worker_parent:
                        with ProcessPoolExecutor(
                            max_workers=workers,
                            initializer=init_worker,
                            initargs=(spec["root"], worker_parent, spec),
                        ) as executor:
                            futures = [
                                executor.submit(run_mutant, task) for task in tasks
                            ]
                            for completed, future in enumerate(
                                as_completed(futures), start=1
                            ):
                                rows[spec["name"]].append(future.result())
                                if completed % 100 == 0 or completed == len(tasks):
                                    print(
                                        f"{spec['name']}: {completed}/{len(tasks)} mutants",
                                        flush=True,
                                    )
                    rows[spec["name"]].sort(key=lambda row: row["id"])
                except Exception as exc:  # incomplete census is a result, not a crash
                    message = (
                        str(exc)
                        .replace(str(ROOT), "<repo>")
                        .replace(str(itsdangerous_repo), "<external>")
                        .replace(str(temporary_root), "<temp>")
                    )
                    run_errors[spec["name"]] = f"{type(exc).__name__}: {message[:300]}"
        inputs_unchanged = {
            spec["name"]: manifests[spec["name"]] == input_manifest(Path(spec["root"]))
            for spec in specs
        }
        summaries = {
            spec["name"]: summarise_corpus(
                rows[spec["name"]],
                generated.get(spec["name"], 0),
                baselines[spec["name"]]["accepted"],
                inputs_unchanged[spec["name"]],
            )
            for spec in specs
        }
        all_complete = all(
            summary["measurement_complete"] for summary in summaries.values()
        )
        fired_stopping_rules = [
            f"{name}:{reason}"
            for name, summary in summaries.items()
            for reason in (
                summary["stopping_failures"] + summary["contamination_reasons"]
            )
        ]
        completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        document = {
            "experiment_id": EXPERIMENT_ID,
            "estimand": "mutation-proxy beta; not human-verdict beta and not a Gate A1 input",
            "evidence": "[measured] outcomes; [asserted] synthetic-fault validity",
            "registration_commit": "d5c9dca",
            "pre_run_protocol_and_harness_commit": harness_commit,
            "harness_sha256": harness_hash,
            "engine": engine,
            "operator_families": sorted(OPERATOR_FAMILIES),
            "frozen_equivalent_classes": sorted(FROZEN_EQUIVALENT_CLASSES),
            "corpora": {
                "consilient": {"revision": CONSILIENT_REVISION},
                "itsdangerous": external_identity,
            },
            "tool_versions": {
                "consilient": host_tools,
                "itsdangerous": external_tools,
            },
            "verifier_contracts": {
                spec["name"]: [
                    {"name": check["name"], "argv": ["<python>", *check["argv"][1:]]}
                    for check in spec["checks"]
                ]
                for spec in specs
            },
            "sampling": "complete first-order mutant census per corpus; no pooled beta",
            "thresholds": {
                "min_classifiable": MIN_CLASSIFIABLE,
                "max_wilson_half_width": MAX_HALF_WIDTH,
                "max_unclassifiable_rate": MAX_UNCLASSIFIABLE_RATE,
                "max_identification_width": MAX_IDENTIFICATION_WIDTH,
            },
            "input_sha256": manifests,
            "baselines": baselines,
            "generated_counts": generated,
            "run_errors": run_errors,
            "mutants": rows,
            "summary": {"per_corpus": summaries},
            "inputs_verified_unchanged": inputs_unchanged,
            "fired_stopping_rules": fired_stopping_rules,
            "wall_clock_s": time.perf_counter() - started,
            "run_window_utc": {"started": started_at, "completed": completed_at},
            "generated_at": completed_at,
            "complete": all_complete,
            "verdict": (
                "insufficient_evidence"
                if not all_complete
                else "complete_contamination_rule_fired"
                if any(
                    summary["contamination_rule_fired"]
                    for summary in summaries.values()
                )
                else "complete_decision_grade"
            ),
        }
        write_json_atomic(output, document)
        return document


def run_experiment(
    itsdangerous_repo: Path, itsdangerous_python: Path, output: Path, workers: int
) -> dict[str, Any]:
    lock, token = acquire_output_lock(output)
    try:
        return _run_experiment(itsdangerous_repo, itsdangerous_python, output, workers)
    finally:
        release_output_lock(lock, token)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--itsdangerous-repo", type=Path, required=True)
    parser.add_argument("--itsdangerous-python", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/10-research/experiments/exp96/results-exp96.json",
    )
    parser.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 1))
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    result = run_experiment(
        args.itsdangerous_repo.resolve(),
        args.itsdangerous_python.resolve(),
        args.output.resolve(),
        args.workers,
    )
    print(json.dumps({"verdict": result["verdict"], "complete": result["complete"]}))


if __name__ == "__main__":
    main()
