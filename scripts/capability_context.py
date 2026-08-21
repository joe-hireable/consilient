#!/usr/bin/env python
"""Emit a vendor-neutral capability context from an allowlist and task request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import CapabilityError, select_capabilities  # noqa: E402


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="JSON capability allowlist")
    parser.add_argument("task_request", type=Path, help="JSON task capability request")
    args = parser.parse_args(argv)
    try:
        context = select_capabilities(_load(args.inventory), _load(args.task_request))
    except (CapabilityError, json.JSONDecodeError, OSError, UnicodeError) as exc:
        print(f"capability context refused: {exc}", file=sys.stderr)
        return 2
    json.dump(
        context,
        sys.stdout,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
