"""Capture the build state the board renders. Run this, then build_board.py, then republish."""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFS = ROOT / ".harness" / "dispatch" / "briefs-driver"
OUT = ROOT / ".harness" / "board-snapshot.json"


def artefact(uid: str, now: float) -> dict[str, object]:
    path = BRIEFS / f"{uid}.out"
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    head: dict[str, str] = {}
    for line in text.splitlines()[:6]:
        if ":" in line:
            key, value = line.split(":", 1)
            head[key.strip()] = value.strip()
    return {
        "bytes": path.stat().st_size,
        "age": int((now - path.stat().st_mtime) / 60),
        "status": head.get("status"),
        "reason": (head.get("reason") or "")[:140],
        "harness": (head.get("harness") or "").split(" ")[0],
    }


def main() -> int:
    units_spec = json.loads(
        (ROOT / ".harness/plan-units.json").read_text(encoding="utf-8")
    )
    state = json.loads(
        (ROOT / ".harness/driver-state.json").read_text(encoding="utf-8")
    )
    done = set(state["done"])
    in_flight = state.get("in_flight", {})
    conflicts = state.get("conflicts", {})
    verified = set(state.get("verified", []))
    arms = state.get("last_arm", {})
    built = state.get("built_by", {})
    now = time.time()

    children: dict[str, set[str]] = {}
    for uid, spec in units_spec.items():
        for dep in spec.get("deps", []):
            children.setdefault(dep, set()).add(uid)

    def closure(node: str, seen: set[str] | None = None) -> set[str]:
        seen = seen if seen is not None else set()
        for child in children.get(node, ()):
            if child not in seen:
                seen.add(child)
                closure(child, seen)
        return seen

    units = []
    for uid, spec in sorted(units_spec.items()):
        deps = spec.get("deps", [])
        undone = [d for d in deps if d not in done]
        if uid in done:
            state_name = "done"
        elif uid in conflicts:
            state_name = "conflict"
        elif uid in in_flight:
            state_name = "running"
        elif undone:
            state_name = "blocked"
        else:
            state_name = "ready"
        art = artefact(uid, now)
        units.append(
            {
                "id": uid,
                "title": spec.get("title", ""),
                "state": state_name,
                "verified": uid in verified,
                "deps": deps,
                "undone": undone,
                "gates": len(closure(uid)),
                "arm": arms.get(uid) or art.get("harness") or "",
                "built_by": built.get(uid, ""),
                "claims": spec.get("claims", [])[:4],
                "elapsed": int((now - in_flight[uid][0]) / 60)
                if uid in in_flight
                else None,
                "leash": int(in_flight[uid][1] / 60) if uid in in_flight else None,
                "out_bytes": art.get("bytes", 0),
                "out_age": art.get("age"),
                "out_status": art.get("status"),
                "reason": art.get("reason", ""),
            }
        )

    try:
        doctor = subprocess.run(
            ["python", "-m", "consilient.cli", "doctor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            cwd=str(ROOT),
        ).stdout
    except Exception:
        doctor = ""
    gates = [
        {"id": m.group(1), "status": m.group(2), "text": m.group(3).strip()[:200]}
        for m in re.finditer(
            r"^\s*([AB]\d)\s+(PASS|FAIL|UNKNOWN):\s*(.+)$", doctor, re.M
        )
    ]
    overall = dict(re.findall(r"^(Gate [AB]):\s*(\w+)$", doctor, re.M))

    log_path = ROOT / ".harness" / "build-loop.log"
    log: list[str] = []
    if log_path.exists():
        log = [
            line.rstrip()
            for line in log_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
            if line.strip()
        ][-60:]

    snap = {
        "taken": int(now),
        "taken_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        "units": units,
        "gates": gates,
        "overall": overall,
        "counts": {
            s: sum(1 for u in units if u["state"] == s)
            for s in ("done", "running", "ready", "blocked", "conflict")
        },
        "verified": len(verified),
        "total": len(units_spec),
        "log": log,
    }
    OUT.write_text(json.dumps(snap), encoding="utf-8")
    print(f"snapshot: {snap['counts']} verified={len(verified)} of {len(units_spec)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
