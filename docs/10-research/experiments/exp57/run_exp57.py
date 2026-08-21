"""EXP-57: does more context buy accuracy, or only cost?

Four arms over the same items, same model, context volume the only variable:

    minimal   the diff alone
    relevant  the diff plus the tests that cover it
    full      the diff plus the whole source tree (post-change state)
    padded    full, plus a fixed body of confidently irrelevant material

Items come from EXP-47's committed corpus of 586 non-equivalent surviving mutants
(``docs/10-research/experiments/exp47/results-exp47.json``). The 60 mutants EXP-47
classified as semantically equivalent are *already excluded* from that list —
``true_defects_survived = composite_survived - equivalent_mutants`` — so the
exclusion the brief requires is satisfied by construction and re-asserted by
``verify_corpus_excludes_equivalents``.

Ground truth is mechanical and symmetric:

    defect item   before = pristine file, after = mutated file    -> REJECT is correct
    fix item      before = mutated file, after = pristine file    -> ACCEPT is correct

Both classes are the same two lines of code in opposite directions, so the surface
form of a good item and a bad item is matched. The extra context an arm supplies is
always rendered in the **after** state, so the tree never silently reveals which
direction the change runs in.

Run:

    python docs/10-research/experiments/exp57/run_exp57.py
    python docs/10-research/experiments/exp57/run_exp57.py --control

Both write append-only JSONL checkpoints alongside the results document; a run that
dies mid-arm resumes from the checkpoint and re-does only the calls it never made.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import sysconfig
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CORPUS = ROOT / "docs/10-research/experiments/exp47/results-exp47.json"

# The commit EXP-47's corpus was generated from. The working tree has moved on and
# the corpus line numbers no longer address it, so every item is materialised from
# this revision by `git show`. Reversal: change CORPUS_REV, delete the results, re-run.
# Falsifier: `verify_corpus_alignment` fails if the snippets stop locating uniquely here.
CORPUS_REV = "d579bee"

SOURCE_FILES = (
    "src/consilient/__init__.py",
    "src/consilient/beta.py",
    "src/consilient/cli.py",
    "src/consilient/events.py",
    "src/consilient/projection.py",
)
TEST_FILES = ("tests/test_v0_invariants.py",)

ARMS = ("minimal", "relevant", "full", "padded")

# --- fixed before the run -------------------------------------------------------
# The pre-registration fixes the arms and the stopping rules but fixes no sample
# size, and does not operationalise "materially beats" or "~". Both are settled here,
# in code, before the first model call; see findings-exp57.md §"What the
# pre-registration does not fix".
SEED = 57
N_DEFECT = 64
N_FIX = 64
CONTROL_ITEMS = 32  # determinism control: re-run this many items in every arm
MATERIAL_DELTA = 0.10  # a difference smaller than this is not "material"
DIFF_CONTEXT = 3  # unified-diff context lines
MAX_COVERING_TESTS = 12  # cap on test functions quoted in the `relevant` arm
# --------------------------------------------------------------------------------

MODEL = "sonnet"
CALL_TIMEOUT_S = 600
MAX_WORKERS = 3

SYSTEM_PROMPT = (
    "You are a code reviewer. You are shown a proposed change to a Python codebase, "
    "and sometimes additional context. Decide whether the change should be accepted "
    "into the codebase or rejected. Answer with exactly one word: ACCEPT or REJECT. "
    "No explanation, no punctuation, no other text."
)

# Padding: irrelevant-but-plausible. Real Python standard-library modules, taken in a
# fixed order until they exceed the byte size of the source tree, so `padded` is
# roughly twice `full`. None of them is imported by, tested with, or conceptually
# near `src/consilient`. This tests whether plausible-but-wrong retrieved code
# degrades the answer. Irrelevant-and-obvious padding (lorem ipsum) tests something
# else — whether volume alone distracts — and is a separate experiment.
PADDING_MODULES = ("textwrap.py", "shlex.py", "csv.py", "colorsys.py", "cmd.py")

VERDICT_RE = re.compile(r"\b(ACCEPT|REJECT)\b")


# --------------------------------------------------------------------------- stats


def wilson_interval(
    successes: int, trials: int, z: float = 1.96
) -> tuple[float, float]:
    """Wilson score interval. Returns (0.0, 0.0) for an empty denominator."""
    if trials <= 0:
        return (0.0, 0.0)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def newcombe_interval(
    k1: int, n1: int, k2: int, n2: int, z: float = 1.96
) -> tuple[float, float]:
    """Newcombe hybrid-score interval on p1 - p2 for two independent proportions.

    Newcombe (1998) method 10. No closed-form normal approximation, because at the
    rates this experiment can produce the normal approximation puts mass outside
    [-1, 1] and would manufacture a difference that is not there.
    """
    if n1 <= 0 or n2 <= 0:
        return (-1.0, 1.0)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson_interval(k1, n1, z)
    l2, u2 = wilson_interval(k2, n2, z)
    lower = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (max(-1.0, lower), min(1.0, upper))


def parse_verdict(text: str) -> str | None:
    """Strictly extract ACCEPT or REJECT. Ambiguous or absent -> None.

    A reply naming both words is not a verdict, and scoring it as one would invent
    data. Unparsable replies are counted and excluded from beta and alpha.
    """
    found = set(VERDICT_RE.findall(text.upper()))
    if len(found) != 1:
        return None
    return found.pop().lower()


# --------------------------------------------------------------------------- corpus


def git_show(rev: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git show {rev}:{path} failed: {result.stderr.strip()}")
    return result.stdout


def verify_corpus_excludes_equivalents(document: dict[str, Any]) -> dict[str, int]:
    """Re-derive EXP-47's equivalent-mutant exclusion instead of trusting the brief."""
    counts = document["raw_counts"]
    expected = counts["composite_survived"] - counts["equivalent_mutants"]
    if counts["true_defects_survived"] != expected:
        raise RuntimeError("EXP-47 counts do not reconcile; corpus provenance broken")
    if len(document["weakest_guards"]) != expected:
        raise RuntimeError(
            "weakest_guards is not the equivalence-corrected survivor set"
        )
    return {
        "equivalent_mutants_excluded_by_exp47": counts["equivalent_mutants"],
        "non_equivalent_survivors": expected,
    }


def locate(snippet: str, lines: list[str]) -> int | None:
    """Index of the unique line equal to `snippet` after stripping, else None."""
    hits = [i for i, line in enumerate(lines) if line.strip() == snippet.strip()]
    return hits[0] if len(hits) == 1 else None


def build_pool(
    document: dict[str, Any], sources: dict[str, str]
) -> list[dict[str, Any]]:
    """Corpus entries that address exactly one line of the pinned tree.

    EXP-47 recorded a mutmut-internal line number and truncated snippets at 120
    characters, so entries are located by content and the ones that cannot be
    located uniquely, span lines, or were truncated are dropped. The count dropped
    is recorded; it is not silently absorbed.
    """
    pool = []
    for entry in document["weakest_guards"]:
        orig, mut = entry["orig_snippet"], entry["mut_snippet"]
        if "\n" in orig or "\n" in mut:
            continue
        if len(orig) >= 120 or len(mut) >= 120:
            continue
        if orig.strip() == mut.strip():
            continue
        lines = sources[entry["file"]].splitlines()
        index = locate(orig, lines)
        if index is None:
            continue
        pool.append({**entry, "index": index})
    return pool


def select_items(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministically draw disjoint defect and fix items from the pool.

    Disjoint, not the same mutant in both directions: reusing a mutant twice would
    correlate a defect item with a fix item and narrow every interval by fiat.
    """
    rng = random.Random(SEED)
    ordered = sorted(pool, key=lambda e: (e["file"], e["id"]))
    drawn = rng.sample(ordered, N_DEFECT + N_FIX)
    items = []
    for position, entry in enumerate(drawn):
        direction = "defect" if position < N_DEFECT else "fix"
        items.append(
            {
                "item_id": f"{direction}:{entry['id']:04d}",
                "mutant_id": entry["id"],
                "file": entry["file"],
                "index": entry["index"],
                "operator": entry["operator"],
                "direction": direction,
                "orig_snippet": entry["orig_snippet"],
                "mut_snippet": entry["mut_snippet"],
                "truth": "reject" if direction == "defect" else "accept",
            }
        )
    items.sort(key=lambda item: item["item_id"])
    return items


# -------------------------------------------------------------------------- prompts


def mutate(text: str, index: int, replacement: str) -> str:
    lines = text.splitlines(keepends=True)
    original = lines[index]
    stripped = original.rstrip("\r\n")
    ending = original[len(stripped) :]
    indent = stripped[: len(stripped) - len(stripped.lstrip())]
    lines[index] = f"{indent}{replacement.strip()}{ending or os.linesep}"
    return "".join(lines)


def before_after(item: dict[str, Any], sources: dict[str, str]) -> tuple[str, str]:
    pristine = sources[item["file"]]
    mutated = mutate(pristine, item["index"], item["mut_snippet"])
    if item["direction"] == "defect":
        return pristine, mutated
    return mutated, pristine


def diff_text(item: dict[str, Any], before: str, after: str) -> str:
    return "".join(
        unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{item['file']}",
            tofile=f"b/{item['file']}",
            n=DIFF_CONTEXT,
        )
    )


def enclosing_symbols(source: str, index: int) -> list[str]:
    """Names of every def/class whose body spans the changed line, outermost first."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    line = index + 1
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", None) or node.lineno
            if node.lineno <= line <= end:
                names.append((node.lineno, node.name))
    return [name for _, name in sorted(names)]


def covering_tests(symbols: list[str], tests: dict[str, str]) -> list[tuple[str, str]]:
    """Test functions naming any enclosing symbol of the changed line.

    ponytail: a name-mention heuristic, capped at MAX_COVERING_TESTS. A real
    coverage trace (`coverage.py --contexts`) would be exact; it would also be a
    different experiment's cost. The cap and the hit count are both recorded, so an
    arm that was truncated is visible rather than inferred.
    """
    if not symbols:
        return []
    wanted = re.compile(r"\b(" + "|".join(re.escape(s) for s in symbols) + r")\b")
    found: list[tuple[str, str]] = []
    for path, source in sorted(tests.items()):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            segment = ast.get_source_segment(source, node) or ""
            if wanted.search(segment):
                found.append((f"{path}::{node.name}", segment))
    return found[:MAX_COVERING_TESTS]


def load_padding() -> dict[str, Any]:
    stdlib = Path(sysconfig.get_paths()["stdlib"])
    target = sum(
        len(git_show(CORPUS_REV, path).encode("utf-8")) for path in SOURCE_FILES
    )
    blocks, used, total = [], [], 0
    for name in PADDING_MODULES:
        if total >= target:
            break
        text = (stdlib / name).read_text(encoding="utf-8")
        blocks.append(f"# ---- {name} ----\n{text}")
        used.append(name)
        total += len(text.encode("utf-8"))
    body = "\n".join(blocks)
    return {
        "kind": "irrelevant-but-plausible: Python standard-library source",
        "modules": used,
        "bytes": len(body.encode("utf-8")),
        "target_bytes": target,
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "python_version": sys.version.split()[0],
        "body": body,
    }


def build_prompt(
    arm: str,
    item: dict[str, Any],
    sources: dict[str, str],
    tests: dict[str, str],
    padding: str,
) -> tuple[str, dict[str, Any]]:
    before, after = before_after(item, sources)
    parts = [
        "# Proposed change",
        "",
        "```diff",
        diff_text(item, before, after).rstrip("\n"),
        "```",
    ]
    meta: dict[str, Any] = {"covering_tests": 0}

    if arm == "relevant":
        symbols = enclosing_symbols(before, item["index"])
        hits = covering_tests(symbols, tests)
        meta["covering_tests"] = len(hits)
        meta["symbols"] = symbols
        parts += ["", "# Tests that cover the changed code", ""]
        if hits:
            for name, segment in hits:
                parts += [f"## {name}", "", "```python", segment, "```", ""]
        else:
            parts += ["No test in the suite names the changed code.", ""]

    if arm in ("full", "padded"):
        parts += ["", "# The source tree, as it would be after this change", ""]
        for path in SOURCE_FILES:
            text = after if path == item["file"] else sources[path]
            parts += [f"## {path}", "", "```python", text.rstrip("\n"), "```", ""]

    if arm == "padded":
        parts += ["", "# Additional material", "", "```python", padding, "```", ""]

    parts += [
        "",
        "Should this change be accepted into the codebase? "
        "Reply with exactly one word: ACCEPT or REJECT.",
    ]
    prompt = "\n".join(parts)
    meta["prompt_chars"] = len(prompt)
    meta["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return prompt, meta


# ------------------------------------------------------------------------- the call


class _WindowsJob:
    """Job object so a timed-out `claude` takes its descendants with it.

    Duplicated from EXP-49 rather than imported: importing it would make this
    instrument's provenance depend on another experiment's module and on `mutmut`
    being installed. Defect B2 in P2-guards.md is exactly the failure this prevents.
    """

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
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ) or not kernel32.AssignProcessToJobObject(
            handle, wintypes.HANDLE(process._handle)
        ):
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ctypes.WinError(error)
        self._kernel32 = kernel32
        self._handle: Any = handle

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _kill_process_tree(process: subprocess.Popen[str], job: _WindowsJob | None) -> None:
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
    if process.poll() is None:
        process.kill()


def claude_argv() -> list[str]:
    """The invocation, stripped of everything that is not the experiment.

    `--tools ""`, `--safe-mode`, `--strict-mcp-config` and an explicit
    `--system-prompt` remove the harness's tool schemas, CLAUDE.md, skills, plugins
    and MCP servers from the context window. Measured on this machine: the default
    invocation carries 75,285 input tokens before the prompt begins, which would
    swamp the variable under test. Stripped, the fixed overhead is ~600 tokens.
    Reversal: delete the flags and re-run. Falsifier: if a stripped call and a
    default call disagree on verdicts, the stripping changed the measurement.
    """
    return [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--model",
        MODEL,
        "--tools",
        "",
        "--safe-mode",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--system-prompt",
        SYSTEM_PROMPT,
    ]


def call_model(prompt: str, cwd: Path) -> dict[str, Any]:
    """One `claude -p` call. Never raises; a failure is recorded as a failure."""
    started = time.perf_counter()
    job: _WindowsJob | None = None
    kwargs: dict[str, Any] = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    try:
        process = subprocess.Popen(
            claude_argv(),
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )
    except OSError as exc:
        return {"ok": False, "error": f"spawn: {exc}", "seconds": 0.0}
    if os.name == "nt":
        try:
            job = _WindowsJob(process)
        except OSError:
            job = None
    try:
        stdout, stderr = process.communicate(prompt, timeout=CALL_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        _kill_process_tree(process, job)
        process.communicate()
        return {
            "ok": False,
            "error": "timeout",
            "seconds": time.perf_counter() - started,
        }
    finally:
        if job is not None:
            job.close()
    seconds = time.perf_counter() - started
    try:
        document = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": f"unparsable cli output: {stderr[:200]}",
            "seconds": seconds,
        }
    if document.get("is_error"):
        return {
            "ok": False,
            "error": str(document.get("result"))[:200],
            "seconds": seconds,
        }
    usage = document.get("usage") or {}
    model_usage = document.get("modelUsage") or {}
    return {
        "ok": True,
        "seconds": seconds,
        "text": str(document.get("result", "")),
        "input_tokens": context_tokens(usage),
        "output_tokens": int(usage.get("output_tokens", 0)),
        # Under sustained load the CLI returns a result with no usage block at all.
        # A zero recorded as a measurement would drag every arm mean towards zero, so
        # the absence is recorded and the call is re-run by `--retry`.
        "usage_reported": bool(usage),
        # The CLI bills a second, auxiliary model on the same prompt. It is not part
        # of the answer but it is part of the cost, so it is recorded separately
        # rather than folded into the arm's input-token figure.
        "model_input_tokens": {
            name: int(m.get("inputTokens", 0))
            + int(m.get("cacheCreationInputTokens", 0))
            + int(m.get("cacheReadInputTokens", 0))
            for name, m in model_usage.items()
        },
    }


def context_tokens(usage: dict[str, Any]) -> int:
    """Total context the model was charged for, whatever cache bucket it landed in."""
    return (
        int(usage.get("input_tokens", 0))
        + int(usage.get("cache_creation_input_tokens", 0))
        + int(usage.get("cache_read_input_tokens", 0))
    )


# ----------------------------------------------------------------------- the census


def usable(record: dict[str, Any]) -> bool:
    """A call is done when it succeeded, adjudicated, and reported its token usage."""
    return bool(
        record["ok"]
        and record["verdict"]
        and record.get("usage_reported", record["input_tokens"] > 0)
    )


def load_checkpoint(path: Path, retry: bool = False) -> dict[tuple[str, str], dict[str, Any]]:
    """Replay the append-only checkpoint. Later lines win, so a retried call resumes."""
    done: dict[tuple[str, str], dict[str, Any]] = {}
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        done[(record["arm"], record["item_id"])] = record
    if retry:
        done = {key: record for key, record in done.items() if usable(record)}
    return done


def run_arm(
    arm: str,
    items: list[dict[str, Any]],
    prompts: dict[tuple[str, str], tuple[str, dict[str, Any]]],
    checkpoint: Path,
    done: dict[tuple[str, str], dict[str, Any]],
    cwd: Path,
) -> list[dict[str, Any]]:
    pending = [item for item in items if (arm, item["item_id"]) not in done]
    print(f"arm {arm}: {len(items)} items, {len(pending)} to call", flush=True)

    def one(item: dict[str, Any]) -> dict[str, Any]:
        prompt, meta = prompts[(arm, item["item_id"])]
        outcome = call_model(prompt, cwd)
        verdict = parse_verdict(outcome["text"]) if outcome["ok"] else None
        return {
            "arm": arm,
            "item_id": item["item_id"],
            "mutant_id": item["mutant_id"],
            "file": item["file"],
            "operator": item["operator"],
            "direction": item["direction"],
            "truth": item["truth"],
            "verdict": verdict,
            "ok": outcome["ok"],
            "error": outcome.get("error"),
            "reply": (outcome.get("text") or "")[:200],
            "input_tokens": outcome.get("input_tokens", 0),
            "output_tokens": outcome.get("output_tokens", 0),
            "usage_reported": outcome.get("usage_reported", False),
            "model_input_tokens": outcome.get("model_input_tokens", {}),
            "seconds": round(outcome["seconds"], 3),
            **meta,
        }

    with (
        ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool,
        checkpoint.open("a", encoding="utf-8") as sink,
    ):
        for record in pool.map(one, pending):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
            done[(arm, record["item_id"])] = record
    return [done[(arm, item["item_id"])] for item in items]


# ------------------------------------------------------------------------- analysis


def rate(records: list[dict[str, Any]], direction: str, wrong: str) -> dict[str, Any]:
    scored = [r for r in records if r["direction"] == direction and r["verdict"]]
    errors = sum(1 for r in scored if r["verdict"] == wrong)
    low, high = wilson_interval(errors, len(scored))
    return {
        "point": errors / len(scored) if scored else None,
        "interval_95": [low, high],
        "errors": errors,
        "adjudicated": len(scored),
        "unparsable": sum(
            1 for r in records if r["direction"] == direction and not r["verdict"]
        ),
    }


def summarise_arm(records: list[dict[str, Any]]) -> dict[str, Any]:
    beta = rate(records, "defect", "accept")
    alpha = rate(records, "fix", "reject")
    adjudicated = beta["adjudicated"] + alpha["adjudicated"]
    errors = beta["errors"] + alpha["errors"]
    measured = [r for r in records if usable(r)]
    tokens = [r["input_tokens"] for r in measured]
    auxiliary = [
        sum(v for k, v in r.get("model_input_tokens", {}).items() if "sonnet" not in k)
        for r in measured
    ]
    accepts = sum(1 for r in records if r["verdict"] == "accept")
    return {
        "beta": beta,
        "alpha": alpha,
        "error_rate": {
            "point": errors / adjudicated if adjudicated else None,
            "interval_95": list(wilson_interval(errors, adjudicated)),
            "errors": errors,
            "adjudicated": adjudicated,
        },
        "accept_rate": accepts / adjudicated if adjudicated else None,
        "input_tokens": {
            "total": sum(tokens),
            "mean": sum(tokens) / len(tokens) if tokens else None,
            "min": min(tokens) if tokens else None,
            "max": max(tokens) if tokens else None,
            "measured_calls": len(tokens),
            "usage_not_reported": sum(1 for r in records if r["ok"] and not usable(r)),
        },
        "auxiliary_model_input_tokens": {
            "total": sum(auxiliary),
            "mean": sum(auxiliary) / len(auxiliary) if auxiliary else None,
        },
        "wall_clock_seconds": sum(r["seconds"] for r in records),
        "failed_calls": sum(1 for r in records if not r["ok"]),
    }


def pairwise(arms: dict[str, dict[str, Any]], metric: str) -> list[dict[str, Any]]:
    out = []
    names = [name for name in ARMS if name in arms]
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            ma, mb = arms[a][metric], arms[b][metric]
            low, high = newcombe_interval(
                ma["errors"], ma["adjudicated"], mb["errors"], mb["adjudicated"]
            )
            point = (
                ma["point"] - mb["point"]
                if ma["point"] is not None and mb["point"] is not None
                else None
            )
            out.append(
                {
                    "metric": metric,
                    "a": a,
                    "b": b,
                    "difference": point,
                    "interval_95": [low, high],
                    "spans_zero": low <= 0.0 <= high,
                }
            )
    return out


def discordance(by_arm: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Item-level disagreement between arms, which the unpaired interval cannot see.

    Every arm answers the *same* items, so the Newcombe interval on the difference —
    which assumes two independent samples — is conservative here. The sharper read is
    how often two arms disagree item-for-item: two arms with equal error rates that
    disagree on nothing are a much stronger result than two arms with equal error
    rates that disagree on half the corpus and cancel out.

    ponytail: exact conditional McNemar, no interval on the paired difference.
    Tango's or Newcombe's phi-corrected paired interval would give one; the
    discordant counts already answer the question this experiment asks.
    """
    out = []
    names = [name for name in ARMS if name in by_arm]
    for i, a in enumerate(names):
        left = {r["item_id"]: r for r in by_arm[a] if r["verdict"]}
        for b in names[i + 1:]:
            right = {r["item_id"]: r for r in by_arm[b] if r["verdict"]}
            common = sorted(set(left) & set(right))
            wrong_a = [k for k in common if left[k]["verdict"] != left[k]["truth"]]
            wrong_b = [k for k in common if right[k]["verdict"] != right[k]["truth"]]
            only_a = len(set(wrong_a) - set(wrong_b))
            only_b = len(set(wrong_b) - set(wrong_a))
            out.append(
                {
                    "a": a,
                    "b": b,
                    "items_in_common": len(common),
                    "verdicts_that_differ": sum(
                        1 for k in common if left[k]["verdict"] != right[k]["verdict"]
                    ),
                    "wrong_in_a_only": only_a,
                    "wrong_in_b_only": only_b,
                    "mcnemar_exact_two_sided_p": mcnemar_exact(only_a, only_b),
                }
            )
    return out


def mcnemar_exact(b: int, c: int) -> float:
    """Exact conditional two-sided McNemar p-value. 1.0 when nothing is discordant."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / (2**n)
    return min(1.0, 2 * tail)


def decide(
    arms: dict[str, dict[str, Any]], diffs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Apply the pre-registered stopping rules in a fixed order.

    "materially beats" and "~" are not defined in the register. Operationalised
    here, before the run: two arms differ when the Newcombe interval on the
    difference excludes zero; one materially beats the other when it differs *and*
    the point difference is at least MATERIAL_DELTA.
    """
    beta = {(d["a"], d["b"]): d for d in diffs if d["metric"] == "beta"}

    def get(a: str, b: str) -> dict[str, Any] | None:
        return beta.get((a, b)) or beta.get((b, a))

    def signed(a: str, b: str) -> float | None:
        """beta[a] - beta[b]."""
        d = get(a, b)
        if d is None or d["difference"] is None:
            return None
        return d["difference"] if d["a"] == a else -d["difference"]

    fired: list[str] = []
    all_overlap = all(d["spans_zero"] for d in beta.values())
    delta = signed("minimal", "full")  # positive => full has the lower beta
    mf_differs = not (get("minimal", "full") or {}).get("spans_zero", True)

    if all_overlap:
        fired.append(
            "insufficient power: every pairwise beta difference interval spans zero"
        )
    elif not mf_differs:
        fired.append(
            "minimal ~ full: context volume is cost without benefit on this task"
        )
    elif delta is not None and delta >= MATERIAL_DELTA:
        fired.append(
            "full materially beats minimal: THE PREMISE IS WRONG - send everything, "
            "build nothing"
        )
    elif delta is not None and -delta >= MATERIAL_DELTA:
        fired.append(
            "minimal materially beats full: extra context degrades the answer on this task"
        )
    else:
        fired.append(
            "minimal and full differ, but by less than the material threshold: "
            "no arm is preferred on accuracy"
        )

    padded_full = signed("padded", "full")
    padded_differs = not (get("padded", "full") or {}).get("spans_zero", True)
    if padded_differs and padded_full is not None and padded_full >= MATERIAL_DELTA:
        fired.append(
            "padded is worse than full: irrelevant context actively degrades the answer"
        )
    else:
        fired.append(
            "padded is not worse than full: no measured context poisoning at this n"
        )

    return {
        "rules_fired": fired,
        "all_beta_intervals_overlap": all_overlap,
        "material_delta": MATERIAL_DELTA,
    }


# ----------------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--control",
        action="store_true",
        help="determinism control: re-run the first CONTROL_ITEMS items in every arm",
    )
    parser.add_argument("--arms", nargs="*", default=list(ARMS))
    parser.add_argument(
        "--retry",
        action="store_true",
        help="re-run calls that failed, went unadjudicated, or reported no token usage",
    )
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    document = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus_counts = verify_corpus_excludes_equivalents(document)
    sources = {path: git_show(CORPUS_REV, path) for path in SOURCE_FILES}
    tests = {path: git_show(CORPUS_REV, path) for path in TEST_FILES}

    pool = build_pool(document, sources)
    if len(pool) < N_DEFECT + N_FIX:
        raise RuntimeError(
            f"pool of {len(pool)} cannot supply {N_DEFECT + N_FIX} items"
        )
    items = select_items(pool)
    if args.control:
        # A stride, not a prefix. `item_id` sorts every defect item before every fix
        # item, so a prefix would re-run only defect items and leave alpha's
        # reproducibility untested — which is half the measurement.
        items = items[:: len(items) // CONTROL_ITEMS]

    padding = load_padding()
    prompts = {
        (arm, item["item_id"]): build_prompt(arm, item, sources, tests, padding["body"])
        for arm in args.arms
        for item in items
    }

    suffix = "-rerun-control" if args.control else ""
    checkpoint = HERE / f"checkpoint-exp57{suffix}.jsonl"
    out = HERE / f"results-exp57{suffix}.json"
    done = load_checkpoint(checkpoint, retry=args.retry)

    # `claude` is run from a scratch directory so no CLAUDE.md is discovered even if
    # --safe-mode ever stops suppressing it.
    cwd = HERE / ".scratch"
    cwd.mkdir(exist_ok=True)

    started = time.perf_counter()
    by_arm: dict[str, list[dict[str, Any]]] = {}
    for arm in args.arms:
        by_arm[arm] = run_arm(arm, items, prompts, checkpoint, done, cwd)
        write_results(
            out, by_arm, items, padding, corpus_counts, len(pool), started, args
        )
        summary = summarise_arm(by_arm[arm])
        print(
            f"checkpoint/{arm}: beta={summary['beta']['point']} "
            f"alpha={summary['alpha']['point']} "
            f"mean_input_tokens={summary['input_tokens']['mean']}",
            flush=True,
        )

    write_results(out, by_arm, items, padding, corpus_counts, len(pool), started, args)
    print(f"wrote {out}", flush=True)
    return 0


def write_results(
    out: Path,
    by_arm: dict[str, list[dict[str, Any]]],
    items: list[dict[str, Any]],
    padding: dict[str, Any],
    corpus_counts: dict[str, int],
    pool_size: int,
    started: float,
    args: argparse.Namespace,
) -> None:
    arms = {arm: summarise_arm(records) for arm, records in by_arm.items()}
    diffs = (
        pairwise(arms, "beta") + pairwise(arms, "alpha") + pairwise(arms, "error_rate")
    )
    document = {
        "experiment_id": "EXP-57",
        "mode": "rerun-control" if args.control else "main",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus": {
            "source": "docs/10-research/experiments/exp47/results-exp47.json",
            "revision": CORPUS_REV,
            **corpus_counts,
            "locatable_pool": pool_size,
            "items_used": len(items),
        },
        "design": {
            "seed": SEED,
            "n_defect": sum(1 for i in items if i["direction"] == "defect"),
            "n_fix": sum(1 for i in items if i["direction"] == "fix"),
            "material_delta": MATERIAL_DELTA,
            "diff_context_lines": DIFF_CONTEXT,
            "max_covering_tests": MAX_COVERING_TESTS,
            "arms": list(by_arm),
        },
        "harness": {
            "model": MODEL,
            "argv": claude_argv()[:-1] + ["<system prompt>"],
            "system_prompt_sha256": hashlib.sha256(
                SYSTEM_PROMPT.encode("utf-8")
            ).hexdigest(),
        },
        "padding": {k: v for k, v in padding.items() if k != "body"},
        "arms": arms,
        "pairwise_differences": diffs,
        "pairwise_discordance": discordance(by_arm),
        "stopping_rules": decide(arms, diffs),
        # Summed per-call, not process elapsed: re-deriving the analysis from the
        # checkpoint makes no calls and would otherwise report a census as instant.
        "total_call_seconds": sum(a["wall_clock_seconds"] for a in arms.values()),
        "this_process_seconds": time.perf_counter() - started,
        "records": [r for records in by_arm.values() for r in records],
    }
    out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
