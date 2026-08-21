"""Block edits to secrets and lockfiles. Agent PreToolUse hook.

Reads the Claude/Grok/Cursor JSON hook payload from stdin. Exit 2 blocks the
tool. Missing or unreadable input is a no-op: a hook that crashes on empty
stdin is worse than none, because it trains people to disable it.

Windows: invoked as `python .githooks/protect-files.py`. The bash copies under
`~/.claude/hooks/` fail here — Git Bash eats backslashes in the path. [measured]
"""

from __future__ import annotations

import json
import re
import sys

SENSITIVE = re.compile(
    r"(\.env$|\.env\.|credentials\.json|firebase-adminsdk|service-account)",
    re.I,
)
ENV_TEMPLATE = re.compile(r"\.env\.(example|sample|template)$", re.I)
LOCKFILE = re.compile(
    r"(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|poetry\.lock)$"
)


def file_path(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        path = tool_input.get("file_path") or tool_input.get("path") or ""
        return str(path)
    return str(payload.get("file_path") or payload.get("path") or "")


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    path = file_path(payload)
    if not path:
        return 0
    if ENV_TEMPLATE.search(path):
        return 0
    if SENSITIVE.search(path):
        print(f"BLOCKED: cannot edit sensitive file: {path}", file=sys.stderr)
        return 2
    if LOCKFILE.search(path):
        print(
            f"BLOCKED: cannot edit lock file {path} — use the package manager",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
