"""One-shot classifier for inherited *-verify.out files. Not product code."""

from __future__ import annotations

import json
from pathlib import Path

BRIEFS = Path(__file__).resolve().parent / "dispatch" / "briefs-driver"


def classify(path: Path) -> str:
    size = path.stat().st_size
    err = path.with_suffix(".err")
    err_text = ""
    if err.exists():
        try:
            err_text = err.read_text(encoding="utf-8", errors="replace")[-800:]
        except OSError:
            pass
    if size == 0:
        if "held by another process" in err_text or "status: refused" in err_text:
            return "dispatch_refused"
        return "no_dispatch"
    text = path.read_text(encoding="utf-8", errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("status: refused"):
        return "dispatch_refused"
    if stripped.startswith("status:"):
        status = stripped.split(":", 1)[1].strip().split()[0]
    else:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return "dispatch_failed"
        if not isinstance(obj, dict):
            return "dispatch_failed"
        status = obj.get("status") if isinstance(obj.get("status"), str) else "failed"
    if status == "refused":
        return "dispatch_refused"
    if status != "ok":
        return "dispatch_failed"
    verdict = path.with_name(path.name.replace("-verify.out", "-verdict.json"))
    if not verdict.exists() or verdict.stat().st_size == 0:
        return "no_receipt_file"
    return "has_receipt_file"


def main() -> None:
    files = sorted(BRIEFS.glob("*-verify.out"))
    counts: dict[str, int] = {}
    for path in files:
        kind = classify(path)
        counts[kind] = counts.get(kind, 0) + 1
    print(f"n={len(files)}")
    for kind, n in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{kind}: {n}")


if __name__ == "__main__":
    main()
