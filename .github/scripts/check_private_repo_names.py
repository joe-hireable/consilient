"""Refuse unpinned private-repository names in tracked content.

    python .github/scripts/check_private_repo_names.py
    python .github/scripts/check_private_repo_names.py --self-test
"""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GIT_ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
PROTECTED_NAMES = ("hireable" + "-3.0", "jobboard" + "-v2")
PROTECTED_BYTES = tuple(name.encode("ascii").lower() for name in PROTECTED_NAMES)
ALLOWED_PATHS = frozenset({"AGENTS.md", ".gitignore", ".github/scripts/check_private_corpus.py"})
EXISTING_BREACHES = frozenset({
    ".agents/skills/README.md",
    ".agents/skills/adversarial-audit/SKILL.md",
    ".agents/skills/writing-adrs/SKILL.md",
    ".github/scripts/check_foreign_identifiers.py",
    ".harness/HANDOFF.md",
    ".harness/build_driver.py",
    "README.md",
    "docs/00-context/CONTINUE-PROMPT.md",
    "docs/00-context/alpha-is-invented-2026-08-20.md",
    "docs/00-context/beta-axis-defect-2026-08-20.md",
    "docs/00-context/cross-family-audit-2026-08-20.md",
    "docs/00-context/decisions-so-far.md",
    "docs/00-context/design-bar-2026-08-23.md",
    "docs/00-context/gate-bypass-log.md",
    "docs/00-context/morning-briefing-2026-08-20.md",
    "docs/00-context/owed-actions-2026-08-20.md",
    "docs/00-context/publication-blocked-2026-08-21.md",
    "docs/00-context/the-machine-2026-08-22.md",
    "docs/10-research/experiment-register.md",
    "docs/10-research/experiments/exp01/alpha_sensitivity.py",
    "docs/10-research/experiments/exp01/findings-alpha-2026-08-20.md",
    "docs/10-research/experiments/exp01/findings-exp01.md",
    "docs/10-research/experiments/exp01/independent_replicate.py",
    "docs/10-research/experiments/exp01/red_cell_adjudication.py",
    "docs/10-research/experiments/exp01/replication-2026-08-20.md",
    "docs/10-research/experiments/exp01/stopping-rule-verdict-2026-08-20.md",
    "docs/10-research/experiments/exp01/stopping_rule.py",
    "docs/10-research/experiments/exp16/grading-key-SEALED.md",
    "docs/10-research/experiments/exp16/transcripts/README.md",
    "docs/10-research/experiments/exp16/transcripts/armA-transcript.jsonl",
    "docs/10-research/experiments/exp16/transcripts/armB-transcript.md",
    "docs/10-research/experiments/exp16/transcripts/armC-transcript.md",
    "docs/10-research/experiments/exp43/findings-exp43.md",
    "docs/10-research/experiments/exp43/run_exp43.py",
    "docs/10-research/local-experimentation.md",
    "docs/10-research/qa-automation-and-the-anchor-problem.md",
    "docs/10-research/two-oracles-disagree-2026-08-20.md",
    "docs/20-design/backends.md",
    "docs/30-source-material/gemini-session-critique.md",
    "docs/30-source-material/prior-repo-assets.md",
    "docs/40-spec/requirements-source.json",
    "docs/40-spec/requirements.md",
    "docs/50-publications/P1-proxy.md",
    "docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md",
    "docs/decisions/0006-ticket-store-sqlite-plus-git-log.md",
    "docs/decisions/0008-name-the-project-consilience.md",
    "docs/decisions/0013-evaluate-on-repo-history-not-benchmarks.md",
    "docs/decisions/0014-portable-skills-agents-md.md",
    "docs/decisions/0015-dogfooding-gate.md",
    "docs/decisions/0017-bootstrap-harness.md",
    "docs/decisions/0023-pr-review-gates.md",
    "docs/decisions/0036-upstream-first-adopt-contribute-never-silently-fork.md",
    "docs/decisions/0042-admit-connectors-by-capability-probing-credential-isolation-and-fail-closed-boundaries.md",
    "docs/decisions/0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md",
    "docs/decisions/0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md",
    "docs/decisions/0055-simulated-users-produce-runs-not-verdicts.md",
    "docs/decisions/0059-package-the-discipline-as-skills-and-separate-instance-from-product.md",
    "docs/decisions/0063-instance-cwd-allowlist-is-supervised-dispatch-not-a-gate-pass.md",
    "docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md",
    "docs/decisions/README.md",
    "docs/publications/README.md",
    "src/consilient/events.py",
    "src/consilient/instructions.py",
    "tests/test_v0_invariants.py",
})
MAX_EXISTING_BREACHES = 64


def tracked_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if completed.returncode != 0:
        raise RuntimeError("cannot enumerate tracked files")
    return [path for path in completed.stdout.split("\0") if path]


def tracked_bytes(relative: str) -> bytes:
    path = ROOT / relative
    try:
        if path.is_symlink():
            return os.fsencode(os.readlink(path))
        return path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"cannot read tracked file: {relative}") from exc


def has_protected_name(content: bytes) -> bool:
    folded = content.lower()
    return any(name in folded for name in PROTECTED_BYTES)


def matching_paths(paths: list[str]) -> set[str]:
    return {relative for relative in paths if has_protected_name(tracked_bytes(relative))}


def classify(matches: set[str]) -> tuple[set[str], set[str]]:
    new = matches - ALLOWED_PATHS - EXISTING_BREACHES
    stale = set(EXISTING_BREACHES - matches)
    return new, stale


def self_test() -> None:
    mixed_case = PROTECTED_NAMES[0].swapcase().encode("ascii")
    assert has_protected_name(mixed_case), "detector must find mixed-case names"
    assert not has_protected_name(b"clean content"), "detector must accept clean content"

    current = set(EXISTING_BREACHES)
    new, stale = classify(current | {"new-match.txt"})
    assert new == {"new-match.txt"} and not stale, "new matches must fail"
    stale_path = "README.md"
    new, stale = classify(current - {stale_path})
    assert not new and stale == {stale_path}, "stale pins must fail"
    assert len(EXISTING_BREACHES) <= MAX_EXISTING_BREACHES, "pin count may not grow"
    print("self-test detected mixed-case, new, and stale cases; accepted clean content")


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="prove detector behaviour")
    args = parser.parse_args()

    if args.self_test:
        self_test()
    if len(EXISTING_BREACHES) > MAX_EXISTING_BREACHES:
        print("private-repository-name invariant failed: pin count exceeds its ceiling")
        return 1
    try:
        matches = matching_paths(tracked_paths())
    except RuntimeError as exc:
        print(f"private-repository-name invariant failed: {exc}")
        return 1
    new, stale = classify(matches)
    if new or stale:
        print("private-repository-name invariant failed:")
        for relative in sorted(new):
            print(f"- new matching path: {relative}")
        for relative in sorted(stale):
            print(f"- stale pin: {relative}; remove the stale pin")
        return 1
    print(
        "private-repository-name invariant passes: "
        f"{len(EXISTING_BREACHES)} pinned breach path(s), 0 new"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
