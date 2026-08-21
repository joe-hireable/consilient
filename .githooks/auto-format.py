"""Format a just-edited file. Agent PostToolUse hook.

Never fails the tool: a formatter that is missing, or a file that ruff cannot
parse, is not a reason to throw away the edit. Exit 0 always.

Windows: invoked as `python .githooks/auto-format.py`. [measured]
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def file_path(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        path = tool_input.get("file_path") or tool_input.get("path") or ""
        return str(path)
    return str(payload.get("file_path") or payload.get("path") or "")


def run(argv: list[str]) -> None:
    try:
        subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    path = file_path(payload)
    if not path or not Path(path).is_file():
        return 0
    if path.endswith(".py") and shutil.which("ruff"):
        run(["ruff", "format", path])
        run(["ruff", "check", "--fix", path])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
