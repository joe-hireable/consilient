"""Fail closed when a tracked revision contains a credential-shaped value.

This deliberately reports only revision and file name, never the matching line or value.
It is a small repository invariant check, not a general secret-management product.
"""

from __future__ import annotations

import argparse
import os
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
    # Fine-grained PATs are `github_pat_...`, which the class above cannot match: after "gh"
    # comes "i", not one of pousr. MEASURED 29 August 2026 -- the scanner detected a classic
    # ghp_ token and missed the format GitHub has issued by default since 2022.
    "github" + r"_pat_[A-Za-z0-9_]{20,}",
    "xox" + r"[baprs]-[0-9A-Za-z-]{10,}",
    "pypi-" + r"AgEIcH[A-Za-z0-9_-]{20,}",
    "AK" + r"IA[0-9A-Z]{16}",
    # xAI / Grok, added 20 Aug 2026 when SuperGrok Heavy became the fourth runtime. The
    # absence of this pattern for the first hours of that runtime's life is the reason this
    # list is now checked against the installed runtimes rather than maintained by memory.
    "xa" + r"i-[A-Za-z0-9]{20,}",
    # Bearer tokens and signed blobs, which carry credentials without matching a vendor prefix.
    # ENCRYPTED included: a passphrase-protected key is still a key, and the passphrase is
    # not in the repository to protect it. Measured missing on the same day.
    r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----",
    r"ey" + r"J[A-Za-z0-9_-]{10,}\.ey" + r"J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
)
COMBINED = "(" + ")|(".join(PATTERNS) + ")"
SECRET_RE = re.compile(COMBINED)


# Git exports GIT_DIR, GIT_INDEX_FILE and GIT_WORK_TREE into every hook it runs, and GIT_DIR
# overrides cwd. Measured 21 August 2026: an unscrubbed `git ls-files` in
# check_private_corpus.py read the hook's repository instead of the private corpus it was
# pointed at, and the gate reported on a tree it had never opened. Every git subprocess in
# .github/scripts now runs with these removed.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=GIT_ENV,
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


def _scan_paths(paths: list[str]) -> list[str]:
    """Read each path and report the ones matching, never the matched text."""
    hits = []
    for relative in paths:
        path = Path(relative)
        try:
            if not path.is_file() or path.stat().st_size > 40_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if SECRET_RE.search(text) or is_private_env_file(relative):
            hits.append(relative)
    return hits


def scan_untracked() -> list[str]:
    completed = git("ls-files", "--others", "--exclude-standard")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate untracked files")
    return _scan_paths([line for line in completed.stdout.splitlines() if line])


def scan_staged() -> list[str]:
    completed = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate staged files")
    return _scan_paths([line for line in completed.stdout.splitlines() if line])


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
        "xa" + "i-" + "F" * 40,
        "ey" + "J" + "a" * 20 + ".ey" + "J" + "b" * 20 + "." + "c" * 30,
        # Split so this file does not match its own checker. Every sample above follows the
        # same convention for the same reason.
        "-----BEGIN " + "PRIVATE" + " KEY-----",
        # Both added 29 August 2026 after an outside review found them missing. The
        # fine-grained PAT is the format GitHub issues by default and the class above
        # cannot match it; a passphrase-protected key is still a key.
        "github" + "_pat_" + "1" * 30,
        "-----BEGIN " + "ENCRYPTED PRIVATE" + " KEY-----",
    )
    assert all(SECRET_RE.search(sample) for sample in samples)
    assert not SECRET_RE.search("OPENROUTER_API_KEY")
    assert not SECRET_RE.search("sk-or-v1-REDACTED")
    assert not SECRET_RE.search("XAI_API_KEY"), "the env var NAME is not a secret"
    assert not SECRET_RE.search("@xai-official/grok"), "the npm package name is not a secret"
    assert not SECRET_RE.search("xai-org/grok-build"), "the GitHub org is not a secret"
    assert not SECRET_RE.search("github" + "_patterns_are_documented"), (
        "a word beginning github_pat is not a token"
    )
    assert is_private_env_file("service/.env.local")
    assert not is_private_env_file("service/.env.example")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--untracked",
        action="store_true",
        help=(
            "also scan untracked-but-not-ignored files. `git grep` sees only tracked content, "
            "so a transcript an agent left in the tree is invisible to this check until "
            "someone stages it -- which is the moment it is already too late."
        ),
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan what is staged right now. This is the pre-commit mode: it refuses before a "
        "commit exists, where CI can only report after one has been pushed.",
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()

    findings = [("working-tree", path) for path in matching_files(None)]
    if args.untracked:
        findings.extend(("untracked", path) for path in scan_untracked())
    if args.staged:
        findings.extend(("staged", path) for path in scan_staged())
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
