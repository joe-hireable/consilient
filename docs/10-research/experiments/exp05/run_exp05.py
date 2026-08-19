"""
EXP-05 smoke runner: one trivial ticket through an adapter, verifier verdict after.

Run:  python run_exp05.py [claude|codex]

Builds a scratch git repo (outside this repository), feeds the adapter one
ticket whose goal is checkable by the repo's own tests, then runs the verifier
(pytest) and reports both the agent outcome and the verifier verdict — the
verifier_verdict / human_verdict pair is the exact record shape the beta-meter
ingests (ADR-0002), so this smoke test doubles as the first trajectory-record
fixture.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GIT = shutil.which("git")

UTIL = "def multiply(a, b):\n    return a * b\n"
TEST = (
    "from util import multiply, add\n\n"
    "def test_multiply():\n    assert multiply(3, 4) == 12\n\n"
    "def test_add():\n    assert add(2, 5) == 7\n    assert add(-1, 1) == 0\n"
)
GOAL = (
    "test_util.py imports a function `add` that does not exist yet. "
    "Add an `add(a, b)` function to util.py so the whole test file passes. "
    "Change nothing else."
)


def make_repo():
    d = Path(tempfile.mkdtemp(prefix="exp05_"))
    (d / "util.py").write_text(UTIL, encoding="utf-8")
    (d / "test_util.py").write_text(TEST, encoding="utf-8")
    for cmd in (
        [GIT, "init", "-q"],
        [GIT, "add", "-A"],
        [
            GIT,
            "-c",
            "user.email=exp05@local",
            "-c",
            "user.name=exp05",
            "commit",
            "-q",
            "-m",
            "fixture",
        ],
    ):
        subprocess.run(cmd, cwd=d, check=True, capture_output=True, text=True)
    return d


def verify(repo):
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {"passed": p.returncode == 0, "tail": (p.stdout or "")[-300:]}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "claude"
    if which == "claude":
        import adapter_claude_code as adapter
    else:
        import adapter_codex as adapter

    repo = make_repo()
    ticket = {
        "id": f"exp05-smoke-{which}",
        "goal": GOAL,
        "repo_dir": str(repo),
        "timeout_s": 300,
    }
    outcome = adapter.run(ticket)
    outcome["verifier"] = verify(repo)
    print(json.dumps({k: v for k, v in outcome.items() if k != "diff"}, indent=2))
    print("--- diff ---")
    print(outcome["diff"] or "(empty)")
