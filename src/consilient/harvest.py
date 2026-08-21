"""Project Consilient usage into a private local corpus (ADR-0057).

The expensive interaction is already on disk: trajectory events and dispatch
run directories. This module copies them into append-only JSONL that is never
tracked. The only permitted in-repository dest is ``.harness/training``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import read_all

HARVEST_KIND = "harvest.example"
DEFAULT_RELATIVE = Path(".harness") / "training"
HARVEST_FILE = "harvest.jsonl"


class HarvestError(ValueError):
    """A dest that would publish, or a payload that cannot be harvested."""


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def assert_unpublishable(dest: Path, *, root: Path) -> Path:
    """Refuse a dest git would ship. Outside the repo is operator-owned storage."""
    dest = dest.resolve()
    root = root.resolve()
    if not is_inside(dest, root):
        return dest
    default = root / DEFAULT_RELATIVE
    if default.resolve() == default and is_inside(dest, default):
        return dest
    raise HarvestError(
        f"refusing harvest dest {dest}: ADR-0057 permits only "
        ".harness/training/ inside this repository, or a path outside it"
    )


def _load_seen(path: Path) -> set[str]:
    seen: set[str] = set()
    if not path.is_file():
        return seen
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        run_id = row.get("run_id")
        if isinstance(run_id, str) and run_id.strip():
            seen.add(run_id.strip())
    return seen


def _read_run_file(run_dir: Path, name: str) -> str:
    path = run_dir / name
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _verdicts_by_run(log_dir: Path) -> dict[str, str]:
    events, _ = read_all(log_dir)
    out: dict[str, str] = {}
    for event in events:
        if event.raw.get("event") != "attempt.verdict":
            continue
        data = event.raw.get("data")
        if not isinstance(data, dict):
            continue
        run_id = data.get("run_id")
        verdict = data.get("human_verdict")
        if isinstance(run_id, str) and isinstance(verdict, str):
            out[run_id] = verdict
    return out


def project_run(
    *,
    run_id: str,
    data: dict[str, Any],
    run_dir: Path | None,
    verdict: str | None,
) -> dict[str, Any]:
    brief = _read_run_file(run_dir, "brief.md") if run_dir is not None else ""
    stdout = _read_run_file(run_dir, "stdout.txt") if run_dir is not None else ""
    stderr = _read_run_file(run_dir, "stderr.txt") if run_dir is not None else ""
    return {
        "v": 1,
        "kind": HARVEST_KIND,
        "run_id": run_id,
        "ts": data.get("ts") or "",
        "harness": data.get("harness"),
        "family": data.get("family"),
        "pool": data.get("pool"),
        "status": data.get("status"),
        "reason": data.get("reason"),
        "task": data.get("task"),
        "artefact_bytes": data.get("artefact_bytes"),
        "diff_bytes": data.get("diff_bytes"),
        "verdict": verdict,
        "brief": brief,
        "stdout": stdout,
        "stderr": stderr,
        "source": "consilient.dispatch",
    }


def harvest(
    *,
    log_dir: Path,
    runs_dir: Path,
    dest: Path,
    root: Path,
) -> dict[str, int]:
    """Append new dispatch outcomes to dest/harvest.jsonl. Returns counts."""
    dest = assert_unpublishable(dest, root=root)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / HARVEST_FILE
    seen = _load_seen(out)
    verdicts = _verdicts_by_run(log_dir)
    events, _ = read_all(log_dir)
    written = 0
    skipped = 0
    with out.open("a", encoding="utf-8", newline="\n") as handle:
        for event in events:
            kind = event.raw.get("event")
            if kind == "dispatch.outcome":
                data = dict(event.raw.get("data") or {})
                data["ts"] = event.raw.get("ts", "")
                run_id = data.get("run_id")
                if not isinstance(run_id, str) or not run_id.strip():
                    continue
                run_id = run_id.strip()
                if run_id in seen:
                    skipped += 1
                    continue
                run_dir = runs_dir / run_id
                row = project_run(
                    run_id=run_id,
                    data=data,
                    run_dir=run_dir if run_dir.is_dir() else None,
                    verdict=verdicts.get(run_id),
                )
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                seen.add(run_id)
                written += 1
            elif kind in {"computer.use", "transport.outbound"}:
                data = dict(event.raw.get("data") or {})
                data["ts"] = event.raw.get("ts", "")
                run_id = data.get("run_id") or data.get("artefact")
                if not isinstance(run_id, str) or not run_id.strip():
                    continue
                run_id = run_id.strip()
                if run_id in seen:
                    skipped += 1
                    continue
                row = {
                    "v": 1,
                    "kind": HARVEST_KIND,
                    "run_id": run_id,
                    "ts": data.get("ts") or "",
                    "harness": event.raw.get("event"),
                    "status": "ok",
                    "task": data.get("task") or data.get("text") or "",
                    "artefact_bytes": data.get("bytes"),
                    "verdict": verdicts.get(run_id),
                    "brief": data.get("task") or data.get("text") or "",
                    "stdout": data.get("artefact") or "",
                    "stderr": "",
                    "source": str(event.raw.get("event")),
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                seen.add(run_id)
                written += 1
    return {"written": written, "skipped": skipped, "total": written + skipped}


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    root = here.parents[2] if here.parents[1].name == "src" else Path.cwd()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default=str(root / ".harness" / "log"))
    parser.add_argument("--runs", default=str(root / ".harness" / "dispatch"))
    parser.add_argument("--out", default=str(root / DEFAULT_RELATIVE))
    args = parser.parse_args(argv)
    try:
        counts = harvest(
            log_dir=Path(args.log),
            runs_dir=Path(args.runs),
            dest=Path(args.out),
            root=root,
        )
    except HarvestError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(counts, sort_keys=True))
    return 0
