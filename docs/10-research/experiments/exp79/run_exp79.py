"""EXP-79: bounded verbatim recall retention and coordination clash rate at scale.

Stopping rule and coordination-critical definition are in
docs/10-research/experiment-register.md § EXP-79. Written before any run output.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from consilient.events import SCHEMA_VERSION, read_all  # noqa: E402
from consilient.recall import ALWAYS_INCLUDE_KINDS, pack_events  # noqa: E402

EXPERIMENT_ID = "EXP-79"
RECALL_LIMIT_CHARS = 8000
TRAJECTORY_SIZES = (100, 1000, 10000)
COORDINATION_QUERY = (
    "Pre-register and run the experiment that decides whether this harness's "
    "coordination survives scale."
)
SCRATCH_ROOT = ROOT / ".harness" / "exp79-scratch"
REAL_LOG = ROOT / ".harness" / "log"

# Fixed before inspection — register § EXP-79.
COORDINATION_KINDS = frozenset(
    ALWAYS_INCLUDE_KINDS
    | {
        "work_item.opened",
        "work_item.comment",
        "work_item.completed",
        "attempt.outcome",
        "capability.gap",
    }
)

# Brief-listed kinds; attempt.outcome absent from real log on 21 Aug 2026.
BRIEF_KINDS = (
    "dispatch.outcome",
    "work_item.opened",
    "work_item.comment",
    "work_item.completed",
    "attempt.outcome",
    "capability.gap",
)


@dataclass(frozen=True)
class KindMix:
    weights: dict[str, float]
    source: str
    real_total: int


def utc_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + __import__("datetime").timedelta(seconds=offset_s)).isoformat()


def derive_kind_mix() -> KindMix:
    """Derive synthesis weights from the live trajectory log."""
    from consilient.events import read_all

    events, _ = read_all(REAL_LOG)
    counts = Counter(e.kind for e in events)
    total = len(events)
    brief_counts = {k: counts.get(k, 0) for k in BRIEF_KINDS}
    if brief_counts["attempt.outcome"] == 0:
        # Real log had none; allocate at work_item.completed rate / 2 as minimal proxy.
        brief_counts["attempt.outcome"] = max(1, brief_counts["work_item.completed"] // 2)
    brief_total = sum(brief_counts.values())
    weights = {k: v / brief_total for k, v in brief_counts.items() if v > 0}
    other_kinds = [k for k in counts if k not in BRIEF_KINDS]
    other_weight = 0.15
    if other_kinds:
        per = other_weight / len(other_kinds)
        for k in other_kinds:
            weights[k] = weights.get(k, 0.0) + per
    brief_sum = sum(weights.get(k, 0.0) for k in BRIEF_KINDS)
    if brief_sum > 0:
        scale = (1.0 - other_weight) / brief_sum
        for k in BRIEF_KINDS:
            if k in weights:
                weights[k] *= scale
    if other_kinds:
        per = other_weight / len(other_kinds)
        for k in other_kinds:
            weights[k] = weights.get(k, 0.0) + per
    norm = sum(weights.values())
    weights = {k: v / norm for k, v in weights.items()}
    source = (
        f".harness/log/ on 21 Aug 2026: {total} events; brief-kind counts "
        + json.dumps(brief_counts, sort_keys=True)
    )
    return KindMix(weights=weights, source=source, real_total=total)


def _event(kind: str, offset_s: int, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "v": SCHEMA_VERSION,
        "ts": utc_ts(offset_s),
        "event": kind,
        "actor": "consilient.dispatch" if kind.startswith(("dispatch.", "work_item.")) else "agent.test",
        "data": data,
    }


def synthesize_events(size: int, mix: KindMix, *, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    kinds = list(mix.weights.keys())
    probs = [mix.weights[k] for k in kinds]
    events: list[dict[str, Any]] = []
    for i in range(size):
        kind = rng.choices(kinds, weights=probs, k=1)[0]
        data: dict[str, Any]
        if kind == "dispatch.outcome":
            data = {
                "run_id": f"synth-{i:05d}",
                "status": rng.choice(["ok", "failed", "refused"]),
                "harness": "cursor-composer",
                "supervised": True,
                "pool": "cursor-models",
                "family": "cursor",
            }
        elif kind == "work_item.opened":
            data = {
                "ticket": f"dispatch:synth-{i:05d}",
                "run_id": f"synth-{i:05d}",
                "text": f"Synthetic in-flight work item {i} on shared/coordination.txt",
                "paths": ["shared/coordination.txt"],
                "harness": "cursor-composer",
            }
        elif kind == "work_item.comment":
            data = {"ticket": f"dispatch:synth-{i:05d}", "text": f"Comment {i}"}
        elif kind == "work_item.completed":
            data = {"ticket": f"dispatch:synth-{i:05d}"}
        elif kind == "attempt.outcome":
            data = {
                "attempt_id": f"attempt-{i:05d}",
                "verifier_outcome": rng.choice(["pass", "fail"]),
            }
        elif kind == "capability.gap":
            data = {
                "asked": f"synthetic gap {i}",
                "attempted": "cursor-composer",
                "detail": "synthetic failure for scale test",
                "repair": "none",
                "run_id": f"synth-{i:05d}",
                "source": "exp79",
                "failure": "refused",
                "closure": "escalate",
            }
        else:
            data = {"synthetic": True, "index": i, "kind": kind}
        events.append(_event(kind, i, data))
    return events


def write_scratch_log(log_dir: Path, events: list[dict[str, Any]]) -> None:
    """Write synthetic events without append clock skew (historical simulation)."""
    log_dir.mkdir(parents=True, exist_ok=True)
    for old in log_dir.glob("*.jsonl"):
        old.unlink()
    by_day: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        day = event["ts"][:10]
        by_day.setdefault(day, []).append(event)
    for day, day_events in by_day.items():
        path = log_dir / f"{day}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in day_events:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def event_in_pack(pack_text: str, event: dict[str, Any]) -> bool:
    ts = event["ts"]
    kind = event["event"]
    header = f"### `{kind}` @ `{ts}`"
    return header in pack_text


def measure_retention(events: list[dict[str, Any]]) -> dict[str, Any]:
    from consilient.events import Event

    typed = [Event(raw=e) for e in events]
    pack_text = pack_events(
        typed, query=COORDINATION_QUERY[:240], limit_chars=RECALL_LIMIT_CHARS
    )
    omitted_match = re.search(r"_(\d+) event\(s\) omitted", pack_text)
    omitted = int(omitted_match.group(1)) if omitted_match else 0

    def rate(subset: frozenset[str]) -> dict[str, Any]:
        targets = [e for e in events if e["event"] in subset]
        if not targets:
            return {"total": 0, "retained": 0, "rate": None}
        retained = sum(1 for e in targets if event_in_pack(pack_text, e))
        return {
            "total": len(targets),
            "retained": retained,
            "rate": round(retained / len(targets), 4),
        }

    return {
        "pack_chars": len(pack_text),
        "omitted_events": omitted,
        "always_include": rate(ALWAYS_INCLUDE_KINDS),
        "work_and_attempt": rate(
            frozenset(
                {
                    "work_item.opened",
                    "work_item.comment",
                    "work_item.completed",
                    "attempt.outcome",
                    "capability.gap",
                }
            )
        ),
        "all_coordination_critical": rate(COORDINATION_KINDS),
    }


def arm_a(mix: KindMix) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    degradation_point: int | None = None
    for size in TRAJECTORY_SIZES:
        events = synthesize_events(size, mix, seed=79_000 + size)
        row = {"size": size, **measure_retention(events)}
        rows.append(row)
        cc = row["all_coordination_critical"]
        if (
            degradation_point is None
            and cc["rate"] is not None
            and cc["rate"] < 0.50
        ):
            degradation_point = size
    return {
        "kind_mix_source": mix.source,
        "recall_limit_chars": RECALL_LIMIT_CHARS,
        "sizes": rows,
        "retention_degradation_point": degradation_point,
    }


def setup_scratch_workspace(workspace: Path) -> Path:
    shared = workspace / "shared"
    shared.mkdir(parents=True, exist_ok=True)
    target = shared / "coordination.txt"
    if not target.exists():
        target.write_text("# EXP-79 coordination scratch file\n", encoding="utf-8")
    return target


def agent_brief(marker: str, *, read_only_note: str = "") -> str:
    return (
        f"{read_only_note}"
        "Append exactly one line to `shared/coordination.txt` in this workspace:\n\n"
        f"{marker}\n\n"
        "Do not remove existing lines. Do not edit any other file. "
        "If recall shows an in-flight claim on this file, say so in one sentence "
        "before editing. Report what you did in stdout."
    )


def run_dispatch(
    *,
    task: str,
    cwd: Path,
    log_dir: Path,
    model: str,
    timeout_s: int,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    task_path = run_dir / "task.txt"
    task_path.write_text(task, encoding="utf-8")
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "dispatch.py"),
        "--task-file",
        str(task_path),
        "--cwd",
        str(cwd),
        "--harness",
        "cursor-composer",
        "--model",
        model,
        "--log",
        str(log_dir),
        "--timeout",
        str(timeout_s),
        "--runs",
        str(run_dir.parent),
        "--json",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s + 120,
    )
    stdout = proc.stdout.strip()
    payload: dict[str, Any] = {"exit_code": proc.returncode, "raw_stdout": stdout[:2000]}
    if stdout:
        try:
            payload["dispatch"] = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError:
            payload["dispatch_parse_error"] = True
    payload["stderr"] = proc.stderr[:1000] if proc.stderr else ""
    out_file = run_dir / "stdout.txt"
    if out_file.exists():
        payload["artefact_bytes"] = out_file.stat().st_size
    return payload


def detect_clashes(
    target: Path,
    *,
    marker_a: str,
    marker_b: str,
    before_a: str,
    after_a: str,
    after_b: str,
    dispatch_a: dict[str, Any],
    dispatch_b: dict[str, Any],
) -> list[str]:
    clashes: list[str] = []
    if marker_a not in after_a:
        clashes.append("agent_a_marker_missing_after_a")
    if marker_a not in after_b:
        clashes.append("agent_a_marker_lost_after_b")
    if marker_b not in after_b:
        clashes.append("agent_b_marker_missing")
    if after_b.count(marker_a) > 1 or after_b.count(marker_b) > 1:
        clashes.append("duplicate_markers")
    stdout_b = json.dumps(dispatch_b)
    if marker_a in before_a and "did not exist" in stdout_b.lower():
        clashes.append("contradictory_file_state")
    dup_ticket = False
    for payload in (dispatch_a, dispatch_b):
        disp = payload.get("dispatch", {})
        if isinstance(disp, dict) and "ticket" in str(disp):
            dup_ticket = True
    if dup_ticket and marker_a in after_b and marker_b in after_b:
        pass  # both succeeded — not a clash by itself
    return clashes


def arm_b(
    mix: KindMix,
    *,
    timeout_s: int,
    skip_dispatch: bool,
) -> dict[str, Any]:
    if skip_dispatch:
        return {
            "verdict": "skipped",
            "note": "Arm B requires real cursor-agent dispatches; not run in this invocation.",
        }

    workspace = SCRATCH_ROOT / "workspace"
    log_dir = SCRATCH_ROOT / "log"
    runs_root = SCRATCH_ROOT / "runs"
    target = setup_scratch_workspace(workspace)
    pairs: list[dict[str, Any]] = []
    models = ("composer-2.5", "kimi-k3-max")

    for size in TRAJECTORY_SIZES:
        events = synthesize_events(size, mix, seed=79_100 + size)
        write_scratch_log(log_dir, events)
        marker_a = f"AGENT-A-{size}-{uuid.uuid4().hex[:8]}"
        marker_b = f"AGENT-B-{size}-{uuid.uuid4().hex[:8]}"
        run_a_dir = runs_root / f"size-{size}" / "agent-a"
        run_b_dir = runs_root / f"size-{size}" / "agent-b"
        row: dict[str, Any] = {
            "trajectory_size": size,
            "marker_a": marker_a,
            "marker_b": marker_b,
        }
        before = target.read_text(encoding="utf-8")
        row["dispatch_a"] = run_dispatch(
            task=agent_brief(marker_a),
            cwd=workspace,
            log_dir=log_dir,
            model=models[0],
            timeout_s=timeout_s,
            run_dir=run_a_dir,
        )
        after_a = target.read_text(encoding="utf-8")
        time.sleep(1)
        row["dispatch_b"] = run_dispatch(
            task=agent_brief(marker_b),
            cwd=workspace,
            log_dir=log_dir,
            model=models[1],
            timeout_s=timeout_s,
            run_dir=run_b_dir,
        )
        after_b = target.read_text(encoding="utf-8")
        row["clashes"] = detect_clashes(
            target,
            marker_a=marker_a,
            marker_b=marker_b,
            before_a=before,
            after_a=after_a,
            after_b=after_b,
            dispatch_a=row["dispatch_a"],
            dispatch_b=row["dispatch_b"],
        )
        row["clash"] = len(row["clashes"]) > 0
        pairs.append(row)

    completed = [p for p in pairs if not p.get("skipped")]
    clash_count = sum(1 for p in completed if p.get("clash"))
    clash_rate = clash_count / max(1, len(completed))
    degradation_point = None
    for p in completed:
        if p.get("clash") and p["trajectory_size"]:
            if clash_rate >= 0.20:
                degradation_point = p["trajectory_size"]
                break

    verdict = "complete"
    if len(completed) < 3:
        verdict = "insufficient_evidence"

    return {
        "scratch_root": str(SCRATCH_ROOT),
        "workspace": str(workspace),
        "log_dir": str(log_dir),
        "models": list(models),
        "pairs": pairs,
        "completed_pairs": len(completed),
        "clash_count": clash_count,
        "clash_rate": round(clash_rate, 4),
        "coordination_degradation_point": degradation_point,
        "verdict": verdict,
        "note": (
            "cursor-agent launches serialised via dispatch lock; overlap is scoped "
            "to the same scratch file and seeded in-flight work_item events."
        ),
    }


def run_all(*, timeout_s: int, skip_dispatch: bool) -> dict[str, Any]:
    mix = derive_kind_mix()
    results = {
        "experiment_id": EXPERIMENT_ID,
        "date": datetime.now(timezone.utc).isoformat(),
        "arm_a": arm_a(mix),
        "arm_b": arm_b(mix, timeout_s=timeout_s, skip_dispatch=skip_dispatch),
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-79 recall scale experiment")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "results-exp79.json",
    )
    parser.add_argument(
        "--skip-dispatch",
        action="store_true",
        help="Arm A only; skip real cursor-agent dispatches",
    )
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    results = run_all(timeout_s=args.timeout, skip_dispatch=args.skip_dispatch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
