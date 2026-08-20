"""Fail closed when a tracked revision contains a credential-shaped value.

This deliberately reports only revision and file name, never the matching line or value.
It is a small repository invariant check, not a general secret-management product.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATTERNS = (
    "sk" + r"-or-v1-[A-Za-z0-9_-]{20,}",
    "sk" + r"-ant-[A-Za-z0-9_-]{20,}",
    "sk" + r"-(proj-)?[A-Za-z0-9]{32,}",
    "AI" + r"za[0-9A-Za-z_-]{35}",
    "gh" + r"[pousr]_[A-Za-z0-9]{20,}",
    "xox" + r"[baprs]-[0-9A-Za-z-]{10,}",
    "pypi-" + r"AgEIcH[A-Za-z0-9_-]{20,}",
    "AK" + r"IA[0-9A-Z]{16}",
)
COMBINED = "(" + ")|(".join(PATTERNS) + ")"
SECRET_RE = re.compile(COMBINED)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def matching_files(revision: str | None) -> list[str]:
    command = ["grep", "-I", "-l", "-E", COMBINED]
    if revision is not None:
        command.append(revision)
    completed = git(*command)
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "git grep failed")
    return [line for line in completed.stdout.splitlines() if line]


def tracked_paths(revision: str | None) -> list[str]:
    command = ["ls-files"] if revision is None else ["ls-tree", "-r", "--name-only", revision]
    completed = git(*command)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate tracked files")
    return [line for line in completed.stdout.splitlines() if line]


def is_private_env_file(path: str) -> bool:
    name = Path(path).name.lower()
    if name == ".env":
        return True
    if not name.startswith(".env."):
        return False
    return not name.endswith((".example", ".sample", ".template"))


def self_test() -> None:
    samples = (
        "sk" + "-or-v1-" + "a" * 40,
        "sk" + "-ant-" + "b" * 40,
        "AI" + "za" + "C" * 35,
        "gh" + "p_" + "D" * 36,
        "AK" + "IA" + "E" * 16,
    )
    assert all(SECRET_RE.search(sample) for sample in samples)
    assert not SECRET_RE.search("OPENROUTER_API_KEY")
    assert not SECRET_RE.search("sk-or-v1-REDACTED")
    assert is_private_env_file("service/.env.local")
    assert not is_private_env_file("service/.env.example")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    findings = [("working-tree", path) for path in matching_files(None)]
    findings.extend(
        ("working-tree", path) for path in tracked_paths(None) if is_private_env_file(path)
    )
    if args.history:
        revisions = git("rev-list", "--all")
        if revisions.returncode != 0:
            raise RuntimeError(revisions.stderr.strip() or "git rev-list failed")
        for revision in revisions.stdout.splitlines():
            findings.extend((revision, path) for path in matching_files(revision))
            findings.extend(
                (revision, path)
                for path in tracked_paths(revision)
                if is_private_env_file(path)
            )

    unique_findings = sorted(set(findings))
    if unique_findings:
        print("Credential-shaped material found; values are intentionally redacted:")
        for revision, path in unique_findings:
            print(f"- {revision}: {path}")
        return 1

    print("secret-history invariant passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
