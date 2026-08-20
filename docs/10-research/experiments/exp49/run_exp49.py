"""EXP-49: mutation-test the experiment runners against their paired tests."""

from __future__ import annotations

import argparse
import ast
import atexit
import difflib
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import mutmut.mutation.file_mutation as fm


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).with_name("results-exp49.json")
REGISTRATION_COMMIT = "7b6ada053f0a93e58537761bb7a2742b17998028"
TEST_TIMEOUT_S = 60
MAX_WORKERS = 24
WORKER_DIR: Path | None = None
WORKER_MANIFEST: dict[str, str] = {}

TARGETS = (
    {
        "name": "exp07",
        "source": "docs/10-research/experiments/exp07/run_exp07.py",
        "test": "docs/10-research/experiments/exp07/test_run_exp07.py",
        "tests": 20,
    },
    {
        "name": "exp31",
        "source": "docs/10-research/experiments/exp31/run_exp31.py",
        "test": "docs/10-research/experiments/exp31/test_run_exp31.py",
        "tests": 9,
    },
    {
        "name": "exp43",
        "source": "docs/10-research/experiments/exp43/run_exp43.py",
        "test": "docs/10-research/experiments/exp43/test_exp43.py",
        "tests": 13,
    },
    {
        "name": "exp45",
        "source": "docs/10-research/experiments/exp45/run_exp45.py",
        "test": "docs/10-research/experiments/exp45/test_exp45.py",
        "tests": 6,
    },
    {
        "name": "exp27_collector",
        "source": "docs/10-research/experiments/exp27/collector.py",
        "test": "docs/10-research/experiments/exp27/test_collector.py",
        "tests": 11,
    },
    {
        "name": "exp27_handshake",
        "source": "docs/10-research/experiments/exp27/handshake.py",
        "test": "docs/10-research/experiments/exp27/test_handshake.py",
        "tests": 16,
    },
)

LOCK_FUNCTIONS = {"acquire_lock", "release_lock"}
TIMEOUT_FUNCTIONS = {"kill_tree", "attempt_timeout", "_run_cmd"}
TIMEOUT_CONTEXT_FUNCTIONS = {"verify", "run_attempt", "run_commit_test", "fetch"}
TIMEOUT_WORDS = ("timeout", "deadline", "remaining", "kill", "communicate", "taskkill")
RESULTS_WRITE_RANGES = {
    "exp07": ((23, 23), (590, 603), (621, 624), (710, 710)),
    "exp31": ((38, 38), (460, 470), (499, 515), (538, 545)),
    "exp43": ((25, 25), (467, 476), (487, 494)),
    "exp45": ((681, 684),),
    "exp27_collector": ((46, 47), (229, 234)),
    "exp27_handshake": (),
}

# Add only audited exceptions here after the census. Unknown survivors remain in the
# conservative corrected numerator, as fixed in the pre-registration.
EQUIVALENT_OVERRIDES: dict[str, str] = {
    **dict.fromkeys(
        (
            "exp07:0081",
            "exp07:0150",
            "exp07:0157",
            "exp07:0361",
            "exp07:0372",
            "exp07:0383",
            "exp07:0427",
            "exp07:0449",
            "exp07:0473",
            "exp07:0498",
            "exp07:0640",
            "exp07:1077",
            "exp31:0090",
            "exp31:0123",
            "exp31:0167",
            "exp31:0277",
            "exp31:0288",
            "exp31:0364",
            "exp31:0371",
            "exp31:0423",
            "exp31:0876",
            "exp31:0966",
            "exp31:1054",
            "exp43:0067",
            "exp43:0139",
            "exp43:0146",
            "exp43:0194",
            "exp43:0256",
            "exp43:0302",
            "exp43:0360",
            "exp43:0435",
            "exp43:0497",
            "exp43:1012",
            "exp43:1057",
            "exp45:0515",
            "exp45:1334",
            "exp27_collector:0028",
            "exp27_collector:0177",
            "exp27_collector:0244",
            "exp27_collector:0259",
            "exp27_collector:0421",
            "exp27_collector:0451",
            "exp27_handshake:0098",
        ),
        "UTF-8 codec-name capitalisation resolves to the same Python codec",
    ),
    **dict.fromkeys(
        (
            "exp43:0048",
            "exp43:0050",
            "exp43:0052",
            "exp43:0054",
        ),
        "Windows-only taskkill executable and switch lookup is case-insensitive",
    ),
    **dict.fromkeys(
        (
            "exp27_collector:0043",
            "exp27_collector:0044",
            "exp27_collector:0053",
            "exp27_collector:0054",
            "exp27_collector:0065",
            "exp27_collector:0066",
        ),
        "HTTP request header names are case-insensitive",
    ),
    **dict.fromkeys(
        (
            "exp27_collector:0080",
            "exp27_collector:0081",
            "exp27_collector:0086",
            "exp27_collector:0087",
            "exp27_collector:0092",
            "exp27_collector:0093",
        ),
        "HTTP response header lookup is case-insensitive",
    ),
    **dict.fromkeys(
        (
            "exp27_collector:0138",
            "exp27_collector:0145",
            "exp27_collector:0153",
            "exp27_collector:0161",
        ),
        "case-only regular-expression change is neutral under re.IGNORECASE",
    ),
    "exp27_collector:0426": "ensure_ascii=False and None take the same false branch",
    **dict.fromkeys(
        ("exp27_handshake:0056", "exp27_handshake:0058"),
        "missing usable=False and None are only truth-tested and are both false",
    ),
    **dict.fromkeys(
        ("exp27_handshake:0085", "exp27_handshake:0091"),
        "an explicit encoding still enables subprocess text mode when text is None",
    ),
    "exp43:0701": "wilson_score_interval never reads its confidence parameter",
}
NON_EQUIVALENT_OVERRIDES: dict[str, str] = {
    **dict.fromkeys(
        (
            "exp07:0027",
            "exp07:0652",
            "exp31:0903",
            "exp43:0019",
            "exp43:0020",
            "exp43:0043",
            "exp43:0282",
            "exp43:0341",
            "exp43:0447",
            "exp43:0450",
            "exp43:0574",
            "exp43:0585",
            "exp43:0975",
            "exp27_collector:0016",
            "exp27_collector:0017",
            "exp27_collector:0069",
            "exp27_collector:0070",
            "exp27_collector:0071",
            "exp27_collector:0072",
            "exp27_handshake:0081",
            "exp27_handshake:0088",
            "exp27_handshake:0094",
        ),
        "audited behavioural change to a timeout bound or process control",
    ),
    **dict.fromkeys(
        (
            "exp07:0092",
            "exp07:0095",
            "exp07:0115",
            "exp07:0116",
            "exp43:0072",
            "exp43:0077",
            "exp43:0078",
            "exp43:0079",
            "exp43:0080",
            "exp43:0081",
            "exp43:0104",
            "exp43:0105",
            "exp43:0129",
            "exp43:0151",
            "exp43:0152",
        ),
        "audited behavioural change to lock acquisition, validation or release",
    ),
    **dict.fromkeys(
        (
            "exp07:1119",
            "exp07:1139",
            "exp31:0863",
            "exp31:1041",
            "exp43:0090",
            "exp43:0091",
            "exp43:0901",
            "exp43:0903",
            "exp43:0993",
            "exp43:0994",
        ),
        "audited behavioural change to run_id generation or persistence",
    ),
    **dict.fromkeys(
        (
            "exp07:1089",
            "exp07:1134",
            "exp31:0943",
            "exp31:1044",
            "exp43:0002",
            "exp43:0004",
            "exp43:0005",
            "exp43:0992",
            "exp43:1006",
            "exp43:1028",
            "exp43:1041",
            "exp43:1045",
            "exp45:1319",
            "exp45:1321",
            "exp45:1323",
            "exp45:1327",
            "exp45:1330",
            "exp45:1335",
            "exp45:1337",
            "exp45:1340",
            "exp45:1341",
            "exp27_collector:0412",
            "exp27_collector:0420",
            "exp27_collector:0422",
            "exp27_collector:0425",
            "exp27_collector:0427",
            "exp27_collector:0447",
            "exp27_collector:0449",
            "exp27_collector:0450",
        ),
        "audited behavioural change to persisted result or state output",
    ),
}


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 0.0
    p = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denominator
    spread = z * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def changed_line(original: str, mutated: str) -> int:
    line_number = 1
    for line in difflib.ndiff(original.splitlines(), mutated.splitlines()):
        if line.startswith("  "):
            line_number += 1
        elif line.startswith("- "):
            return line_number
        elif line.startswith("+ "):
            return line_number
    return 1


def docstring_lines(source: str) -> set[int]:
    lines: set[int] = set()
    tree = ast.parse(source)
    nodes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, nodes) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def function_at_line(source: str, line: int) -> str:
    candidates = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.lineno <= line <= (node.end_lineno or node.lineno)
    ]
    if not candidates:
        return "<module>"
    return min(candidates, key=lambda node: (node.end_lineno or node.lineno) - node.lineno).name


def operator_category(original_node: Any) -> str:
    name = type(original_node).__name__
    if name in {"Integer", "Float", "Imaginary", "SimpleString", "FormattedString"}:
        return "literal"
    if name in {"Comparison", "ComparisonTarget"}:
        return "comparison"
    if name in {"BooleanOperation", "Name", "UnaryOperation"}:
        return "boolean_or_unary"
    if name in {"BinaryOperation", "AugAssign"}:
        return "arithmetic_or_binary"
    if name in {"Call", "Arg"}:
        return "call_or_argument"
    if name in {"If", "IfExp", "Else", "Raise", "Return", "Break", "Continue"}:
        return "control_flow"
    return "expression"


def critical_paths(target: str, function: str, line: int, source_line: str) -> list[str]:
    text = source_line.casefold()
    paths: list[str] = []
    if function in LOCK_FUNCTIONS or "lock_path" in text or "lock_file" in text:
        paths.append("lock")
    if (
        function in TIMEOUT_FUNCTIONS
        or (function in TIMEOUT_CONTEXT_FUNCTIONS and any(word in text for word in TIMEOUT_WORDS))
        or "timeout_s" in text
    ):
        paths.append("timeout")
    if "run_id" in text:
        paths.append("run_id")
    if any(start <= line <= end for start, end in RESULTS_WRITE_RANGES[target]):
        paths.append("results_write")
    return paths


def _safe_remove_worker_dir() -> None:
    global WORKER_DIR
    if WORKER_DIR is None:
        return
    resolved = WORKER_DIR.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved.parent == temp_root and resolved.name.startswith("exp49_worker_"):
        shutil.rmtree(resolved, ignore_errors=True)
    WORKER_DIR = None


def _remove_case_dir(case_dir: Path) -> None:
    assert WORKER_DIR is not None
    resolved = case_dir.resolve()
    if resolved.parent != WORKER_DIR.resolve() or resolved.name != "case":
        raise RuntimeError(f"refusing to remove unexpected case directory: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)


def init_worker(manifest: dict[str, str], harness_digest: str) -> None:
    global WORKER_DIR, WORKER_MANIFEST
    if source_hash(Path(__file__)) != harness_digest:
        raise RuntimeError("worker harness does not match fixed EXP-49 harness")
    WORKER_DIR = Path(tempfile.mkdtemp(prefix=f"exp49_worker_{os.getpid()}_"))
    WORKER_MANIFEST = manifest
    atexit.register(_safe_remove_worker_dir)


class _WindowsJob:
    def __init__(self, process: subprocess.Popen[str]) -> None:
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
        ) or not kernel32.AssignProcessToJobObject(handle, wintypes.HANDLE(process._handle)):
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
    process: subprocess.Popen[str], job: _WindowsJob | None = None
) -> None:
    if job is not None:
        job.close()
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except subprocess.SubprocessError:
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    if process.poll() is None:
        process.kill()


def run_pytest(cwd: Path, test_path: Path, timeout_s: int = TEST_TIMEOUT_S) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    kwargs: dict[str, Any]
    if os.name == "nt":
        kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        kwargs = {"start_new_session": True}
    started = time.perf_counter()
    job: _WindowsJob | None = None
    try:
        process = subprocess.Popen(
            ["python", "-B", "-m", "pytest", str(test_path), "-q"],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )
        if os.name == "nt":
            try:
                job = _WindowsJob(process)
            except OSError:
                _kill_process_tree(process)
                raise
        try:
            stdout, stderr = process.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _kill_process_tree(process, job)
            stdout, stderr = process.communicate(timeout=10)
            return {
                "outcome": "timeout",
                "returncode": process.returncode,
                "duration_s": time.perf_counter() - started,
                "stdout": stdout,
                "stderr": stderr,
            }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "outcome": "execution_error",
            "returncode": None,
            "duration_s": time.perf_counter() - started,
            "stdout": "",
            "stderr": type(exc).__name__,
        }
    finally:
        if job is not None:
            job.close()
    return {
        "outcome": "survived" if process.returncode == 0 else "killed",
        "returncode": process.returncode,
        "duration_s": time.perf_counter() - started,
        "stdout": stdout,
        "stderr": stderr,
    }


def run_mutant(task: tuple[dict[str, Any], str, str, str]) -> dict[str, Any]:
    assert WORKER_DIR is not None
    record, source_rel, test_rel, mutated_code = task
    case_dir = WORKER_DIR / "case"
    if case_dir.exists():
        _remove_case_dir(case_dir)
    required = required_experiments(source_rel)
    for name in required:
        source_dir = ROOT / "docs/10-research/experiments" / name
        destination = case_dir / "docs/10-research/experiments" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source_dir,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    shutil.copy2(ROOT / "pytest.ini", case_dir / "pytest.ini")
    target = case_dir / source_rel
    try:
        if input_manifest(case_dir, required) != WORKER_MANIFEST:
            raise RuntimeError("worker input manifest does not match fixed verifier inputs")
        target.write_text(mutated_code, encoding="utf-8")
        result = run_pytest(case_dir, case_dir / test_rel)
    finally:
        _remove_case_dir(case_dir)
    return {
        **record,
        "outcome": result["outcome"],
        "returncode": result["returncode"],
        "duration_s": result["duration_s"],
    }


def classify(mutant: dict[str, Any]) -> None:
    if mutant["outcome"] != "survived":
        mutant["classification"] = "not_applicable"
        mutant["classification_reason"] = "verifier_rejected"
    elif mutant["id"] in EQUIVALENT_OVERRIDES:
        mutant["classification"] = "equivalent"
        mutant["classification_reason"] = EQUIVALENT_OVERRIDES[mutant["id"]]
    elif mutant.get("docstring_only"):
        mutant["classification"] = "equivalent"
        mutant["classification_reason"] = "docstring_only"
    elif mutant["id"] in NON_EQUIVALENT_OVERRIDES:
        mutant["classification"] = "non_equivalent"
        mutant["classification_reason"] = NON_EQUIVALENT_OVERRIDES[mutant["id"]]
    else:
        mutant["classification"] = "unclassifiable"
        mutant["classification_reason"] = "semantic_equivalence_not_proven"


def _rate(mutants: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(mutants)
    execution_errors = sum(m["outcome"] == "execution_error" for m in mutants)
    valid_total = total - execution_errors
    survived = sum(m["outcome"] == "survived" for m in mutants)
    equivalent = sum(m.get("classification") == "equivalent" for m in mutants)
    unclassifiable = sum(m.get("classification") == "unclassifiable" for m in mutants)
    known_non_equivalent = sum(m.get("classification") == "non_equivalent" for m in mutants)
    denominator = valid_total - equivalent
    corrected_survivors = survived - equivalent
    raw_interval = wilson_interval(survived, valid_total)
    corrected_interval = wilson_interval(corrected_survivors, denominator)
    return {
        "total": total,
        "valid_total": valid_total,
        "killed": sum(m["outcome"] == "killed" for m in mutants),
        "survived": survived,
        "timeouts": sum(m["outcome"] == "timeout" for m in mutants),
        "execution_errors": execution_errors,
        "equivalent": equivalent,
        "known_non_equivalent_survivors": known_non_equivalent,
        "unclassifiable_survivors": unclassifiable,
        "raw_beta": survived / valid_total if valid_total else 0.0,
        "raw_denominator": valid_total,
        "raw_interval_95": list(raw_interval),
        "corrected_survivors": corrected_survivors,
        "corrected_denominator": denominator,
        "corrected_beta": corrected_survivors / denominator if denominator else 0.0,
        "corrected_interval_95": list(corrected_interval),
    }


def summarise(
    mutants: list[dict[str, Any]],
    baselines: dict[str, Any],
    generated_counts: dict[str, int] | None = None,
    inputs_unchanged: bool = True,
) -> dict[str, Any]:
    for mutant in mutants:
        classify(mutant)
    per_target = {
        target["name"]: _rate([m for m in mutants if m["target"] == target["name"]])
        for target in TARGETS
    }
    by_function: dict[str, dict[str, Any]] = {}
    for target in TARGETS:
        target_mutants = [m for m in mutants if m["target"] == target["name"]]
        functions = sorted({m["function"] for m in target_mutants})
        by_function[target["name"]] = {
            function: _rate([m for m in target_mutants if m["function"] == function])
            for function in functions
        }
    critical = {
        path: _rate([m for m in mutants if path in m["critical_paths"]])
        for path in ("timeout", "lock", "run_id", "results_write")
    }
    composite = _rate(mutants)
    baseline_failed = len(baselines) != len(TARGETS) or any(
        b["outcome"] != "survived" for b in baselines.values()
    )
    count_mismatch = generated_counts is not None and any(
        len([m for m in mutants if m["target"] == target["name"]])
        != generated_counts.get(target["name"], -1)
        for target in TARGETS
    )
    incomplete = (
        count_mismatch
        or not inputs_unchanged
        or any(v["execution_errors"] for v in per_target.values())
    )
    underpowered = any(v["corrected_denominator"] < 50 for v in per_target.values())
    sufficient = not baseline_failed and not incomplete and not underpowered
    if not sufficient:
        verdict = "insufficient_evidence"
        comparison = "not_permitted"
    elif composite["corrected_beta"] >= 0.20:
        verdict = "high_runner_false_accept_rate"
        comparison = compare_with_exp47(composite["corrected_interval_95"])
    elif composite["corrected_beta"] < 0.05:
        verdict = "strong_runner_guard_discipline"
        comparison = compare_with_exp47(composite["corrected_interval_95"])
    else:
        verdict = "measured_without_categorical_verdict"
        comparison = compare_with_exp47(composite["corrected_interval_95"])
    return {
        "per_target": per_target,
        "composite": composite,
        "critical_paths": critical,
        "by_function": by_function,
        "verdict": verdict,
        "comparison_with_exp47": comparison,
        "complete": not incomplete,
        "exp47_corrected_beta": 0.3132,
        "exp47_corrected_interval_95": [0.2926, 0.3346],
    }


def compare_with_exp47(interval: list[float]) -> str:
    if interval[0] > 0.3346:
        return "materially_worse"
    if interval[1] < 0.2926:
        return "materially_better"
    return "intervals_overlap_no_material_difference_established"


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_experiments(source_rel: str) -> set[str]:
    name = Path(source_rel).parent.name
    return {name, "exp07"} if name == "exp31" else {name}


def input_manifest(root: Path, experiments: set[str] | None = None) -> dict[str, str]:
    names = experiments or {"exp07", "exp27", "exp31", "exp43", "exp45"}
    paths = [root / "pytest.ini"]
    for name in sorted(names):
        directory = root / "docs/10-research/experiments" / name
        paths.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    return {
        path.relative_to(root).as_posix(): source_hash(path)
        for path in sorted(paths)
    }


def select_manifest(manifest: dict[str, str], experiments: set[str]) -> dict[str, str]:
    prefixes = tuple(f"docs/10-research/experiments/{name}/" for name in experiments)
    return {
        path: digest
        for path, digest in manifest.items()
        if path == "pytest.ini" or path.startswith(prefixes)
    }


def baseline(spec: dict[str, Any]) -> dict[str, Any]:
    result = run_pytest(ROOT, ROOT / spec["test"])
    match = re.search(r"(\d+) passed", result["stdout"])
    tests_passed = int(match.group(1)) if match else None
    outcome = result["outcome"]
    if outcome == "survived" and tests_passed != spec["tests"]:
        outcome = "execution_error"
    return {
        "outcome": outcome,
        "returncode": result["returncode"],
        "tests_passed": tests_passed,
        "tests_expected": spec["tests"],
        "duration_s": result["duration_s"],
    }


def generate_tasks(spec: dict[str, Any]) -> list[tuple[dict[str, Any], str, str, str]]:
    source = (ROOT / spec["source"]).read_text(encoding="utf-8")
    module, mutations, _, _ = fm.create_mutations(spec["source"], source)
    documentation = docstring_lines(source)
    source_lines = source.splitlines()
    tasks = []
    for index, mutation in enumerate(mutations):
        mutated_tree = fm.deep_replace(
            module, mutation.original_node, mutation.mutated_node
        )
        assert hasattr(mutated_tree, "code")
        mutated_code = mutated_tree.code
        line = changed_line(source, mutated_code)
        function = function_at_line(source, line)
        original_line = source_lines[line - 1] if 0 < line <= len(source_lines) else ""
        record = {
            "id": f"{spec['name']}:{index:04d}",
            "target": spec["name"],
            "file": spec["source"],
            "line": line,
            "function": function,
            "operator": operator_category(mutation.original_node),
            "node_change": (
                f"{type(mutation.original_node).__name__}"
                f"->{type(mutation.mutated_node).__name__}"
            ),
            "critical_paths": critical_paths(
                spec["name"], function, line, original_line
            ),
            "docstring_only": line in documentation,
        }
        tasks.append((record, spec["source"], spec["test"], mutated_code))
    return tasks


def print_headline(document: dict[str, Any]) -> None:
    summary = document["summary"]
    print("\n=== EXP-49 DECISION-RELEVANT RESULTS ===", flush=True)
    baseline_failures = [
        name
        for name, result in document["baselines"].items()
        if result["outcome"] != "survived"
    ]
    print(
        f"integrity: complete={summary['complete']} "
        f"inputs_unchanged={document['inputs_verified_unchanged']} "
        f"execution_errors={summary['composite']['execution_errors']} "
        f"baseline_failures={baseline_failures}",
        flush=True,
    )
    for target in TARGETS:
        name = target["name"]
        rate = summary["per_target"][name]
        low, high = rate["corrected_interval_95"]
        print(
            f"{name}: raw_beta={rate['raw_beta']:.4f} "
            f"({rate['survived']}/{rate['raw_denominator']}); "
            f"corrected_beta={rate['corrected_beta']:.4f} "
            f"[{low:.4f}, {high:.4f}] "
            f"({rate['corrected_survivors']}/{rate['corrected_denominator']}); "
            f"equivalent={rate['equivalent']}, unclassifiable={rate['unclassifiable_survivors']}",
            flush=True,
        )
    composite = summary["composite"]
    low, high = composite["corrected_interval_95"]
    print(
        f"composite: raw_beta={composite['raw_beta']:.4f} "
        f"({composite['survived']}/{composite['raw_denominator']}); "
        f"corrected_beta={composite['corrected_beta']:.4f} "
        f"[{low:.4f}, {high:.4f}] "
        f"({composite['corrected_survivors']}/{composite['corrected_denominator']})",
        flush=True,
    )
    print(f"verdict: {summary['verdict']}", flush=True)
    print(f"EXP-47 comparison: {summary['comparison_with_exp47']}", flush=True)
    for path, rate in summary["critical_paths"].items():
        print(
            f"critical/{path}: {rate['corrected_survivors']}/{rate['corrected_denominator']} "
            f"survived, beta={rate['corrected_beta']:.4f}",
            flush=True,
        )
    functions = []
    for target, rates in summary["by_function"].items():
        for function, rate in rates.items():
            if rate["corrected_denominator"]:
                functions.append((rate["corrected_beta"], target, function, rate))
    for _, target, function, rate in sorted(functions, reverse=True)[:10]:
        print(
            f"weakest/{target}/{function}: "
            f"{rate['corrected_survivors']}/{rate['corrected_denominator']} "
            f"survived, beta={rate['corrected_beta']:.4f}",
            flush=True,
        )


def run_census(workers: int) -> dict[str, Any]:
    engine = {
        "mutmut": importlib.metadata.version("mutmut"),
        "libcst": importlib.metadata.version("libcst"),
    }
    if engine["mutmut"] != "3.7.0":
        raise RuntimeError(f"EXP-49 requires mutmut 3.7.0, found {engine['mutmut']}")
    baselines: dict[str, Any] = {}
    fixed_manifest = input_manifest(ROOT)
    harness_digest = source_hash(Path(__file__))
    all_mutants: list[dict[str, Any]] = []
    generated_counts: dict[str, int] = {}
    started = time.perf_counter()

    def checkpoint(inputs_unchanged: bool) -> dict[str, Any]:
        document = {
            "experiment_id": "EXP-49",
            "registration_commit": REGISTRATION_COMMIT,
            "engine": engine,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "workers": workers,
            "test_timeout_s": TEST_TIMEOUT_S,
            "input_sha256": fixed_manifest,
            "harness_sha256": harness_digest,
            "analysis_harness_sha256": source_hash(Path(__file__)),
            "generated_counts": generated_counts,
            "baselines": baselines,
            "mutants": all_mutants,
            "summary": summarise(
                all_mutants, baselines, generated_counts, inputs_unchanged
            ),
            "wall_clock_s": time.perf_counter() - started,
            "inputs_verified_unchanged": inputs_unchanged,
        }
        write_json_atomic(OUT, document)
        return document

    for spec in TARGETS:
        name = spec["name"]
        baselines[name] = baseline(spec)
        base = baselines[name]
        print(
            f"baseline/{name}: outcome={base['outcome']} exit={base['returncode']} "
            f"tests={base['tests_passed']}/{base['tests_expected']} "
            f"duration={base['duration_s']:.2f}s",
            flush=True,
        )
    inputs_unchanged = (
        input_manifest(ROOT) == fixed_manifest
        and source_hash(Path(__file__)) == harness_digest
    )
    if any(base["outcome"] != "survived" for base in baselines.values()) or not inputs_unchanged:
        print("baseline gate failed; verdict=insufficient_evidence; no mutants executed", flush=True)
        return checkpoint(inputs_unchanged)

    for spec in TARGETS:
        name = spec["name"]
        if (
            input_manifest(ROOT) != fixed_manifest
            or source_hash(Path(__file__)) != harness_digest
        ):
            print("input manifest changed; stopping with insufficient evidence", flush=True)
            return checkpoint(False)
        tasks = generate_tasks(spec)
        generated_counts[name] = len(tasks)
        print(f"generated/{name}: {len(tasks)} mutants", flush=True)
        target_results: list[dict[str, Any]] = []
        required = required_experiments(spec["source"])
        worker_manifest = select_manifest(fixed_manifest, required)
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=init_worker,
            initargs=(worker_manifest, harness_digest),
        ) as executor:
            futures = {executor.submit(run_mutant, task): task[0] for task in tasks}
            progress_every = max(1, len(tasks) // 10)
            for completed, future in enumerate(as_completed(futures), start=1):
                record = futures[future]
                try:
                    target_results.append(future.result())
                except Exception as exc:
                    target_results.append(
                        {
                            **record,
                            "outcome": "execution_error",
                            "returncode": None,
                            "duration_s": 0.0,
                            "worker_error": type(exc).__name__,
                        }
                    )
                if completed % progress_every == 0 or completed == len(tasks):
                    print(f"progress/{name}: {completed}/{len(tasks)}", flush=True)
        target_results.sort(key=lambda item: item["id"])
        all_mutants.extend(target_results)
        document = checkpoint(
            input_manifest(ROOT) == fixed_manifest
            and source_hash(Path(__file__)) == harness_digest
        )
        rate = document["summary"]["per_target"][name]
        print(
            f"checkpoint/{name}: survived={rate['survived']} killed={rate['killed']} "
            f"timeouts={rate['timeouts']} errors={rate['execution_errors']}",
            flush=True,
        )
    return checkpoint(
        input_manifest(ROOT) == fixed_manifest
        and source_hash(Path(__file__)) == harness_digest
    )


def analyse_existing() -> dict[str, Any]:
    document = json.loads(OUT.read_text(encoding="utf-8"))
    if document["engine"]["mutmut"] != "3.7.0":
        raise RuntimeError("stored EXP-49 census was not generated by mutmut 3.7.0")
    overlapping = EQUIVALENT_OVERRIDES.keys() & NON_EQUIVALENT_OVERRIDES.keys()
    survivor_ids = {
        mutant["id"] for mutant in document["mutants"] if mutant["outcome"] == "survived"
    }
    unknown = (EQUIVALENT_OVERRIDES.keys() | NON_EQUIVALENT_OVERRIDES.keys()) - survivor_ids
    if overlapping or unknown:
        raise RuntimeError(
            f"invalid survivor overrides: overlapping={sorted(overlapping)}, "
            f"unknown={sorted(unknown)}"
        )
    document["summary"] = summarise(
        document["mutants"],
        document["baselines"],
        document["generated_counts"],
        document["inputs_verified_unchanged"],
    )
    document["analysis_harness_sha256"] = source_hash(Path(__file__))
    write_json_atomic(OUT, document)
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--analyse-existing", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    document = analyse_existing() if args.analyse_existing else run_census(args.workers)
    print_headline(document)


if __name__ == "__main__":
    main()
