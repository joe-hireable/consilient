"""Inspect a scratch repository recorded by backend-comparison.json."""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def main(agent):
    rows = json.loads((HERE / "backend-comparison.json").read_text(encoding="utf-8"))
    row = next(item for item in rows if item["agent"] == agent)
    repo = Path(row["repo"])
    print(f"agent: {agent}\nrepo: {repo}\nexists: {repo.exists()}")
    if not repo.exists():
        return 1

    for name in ("util.py", "test_util.py"):
        path = repo / name
        print(f"\n--- {name} ---")
        print(path.read_text(encoding="utf-8") if path.exists() else "(missing)")

    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    print("\n--- git diff ---")
    print(diff.stdout or "(empty)")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else "codex+ollama:qwen3:8b")
    )
