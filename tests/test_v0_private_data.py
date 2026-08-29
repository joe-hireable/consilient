"""What must never be committed, and who must never be recorded as the committer. A
user's trajectory is their data: two days of it were tracked and reached the public
repository before this check existed [measured], only `state.db` and `dispatch/` had
ever been ignored, and publishing is one-way, so those two are not retractable — this
stops the third. The share directory is gitignored before any exporter exists, so the
same failure cannot recur on the second artefact. Adding a runtime must force adding its
credential shape: Grok Build was installed and authenticated on 20 August 2026 while the
secret checker had no xAI pattern at all for the first hours of that runtime's life, and
nothing failed because nothing was checking that the pattern list kept pace with the
runtimes — a vendor that issues no user-visible key declares that explicitly, so the
absence is a statement rather than an oversight. Dispatch transcripts and briefs are
multi-megabyte verbatim records of whatever an agent read or was told, and `git add -A`
swept four brief files into a commit on 20 August 2026, so that is not hypothetical. The
two authorship ratchets are the same concern turned on the commits themselves: a shared
`.git/config` stamped fifty-one of this branch's commits with EXP-07's fixture identity,
and on 27 August 2026 a local config left behind by `tests/test_supervision.py` meant
280 of the 289 commits awaiting publication were committed by a fixture and 63 authored
by one. Commit identity is part of the commit object, so a wrong committer travels by
construction and cannot be corrected after a push."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
from v0_invariants_helpers import (
    _spend_scripts,
)


def test_no_new_commit_may_be_authored_by_a_fixture_identity():
    """A ratchet on git authorship, found on 20 Aug 2026 and not by any check here.

    EXP-07 builds throwaway repositories and stamps them `EXP-07 <exp07@local>` so its
    synthetic commits are distinguishable. That identity — along with a WSL-absolute
    `core.worktree` — was also present in the *primary* repository's `.git/config`, which
    every worktree shares. Fifty-one of this branch's commits, including two written the
    day this test was added, are therefore authored and committed by a test fixture rather
    than by the person accountable for them.

    This is V0-18's concern inverted. V0-18 stops an agent claiming a human's decision; the
    same record silently attributed a human's work to a fixture, and nothing looked. The
    repair for the config is done; this is the ratchet that stops it recurring.

    The published history is NOT rewritten here — that is a force-push and belongs to the
    principal. The constant below is the measured legacy baseline and may only go DOWN.
    """
    git = shutil.which("git")
    if git is None or not Path(".git").exists():  # pragma: no cover - repository-only
        pytest.skip("no git checkout")
    result = subprocess.run(
        [git, "log", "--format=%ae%n%ce", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    fixture_stamped = [
        line for line in result.stdout.splitlines() if line.endswith("@local")
    ]
    # Raised 102 → 108 on 22 Aug 2026: merging fleet-condensation made three historical
    # commits reachable (762c3b6, 321d644, b3d3c71; EXP-45 pre-registration, run and
    # findings, 20 Aug 2026 13:17–13:26), each counted twice (author and committer).
    # They were stamped by the shared-config defect this test documents, predate its
    # repair, and are not new fixture authorship; the alternative — rewriting their
    # authorship — would falsify the record this ratchet exists to keep honest. The
    # guard against NEW fixture-stamped commits is unchanged.
    # Raised 108 → 112 on 22 Aug 2026: merging fleet-guards made two more historical
    # commits reachable (fb0309f, 87e48b6; EXP-48 pre-registration and findings,
    # 20 Aug 2026 15:17–15:23), same defect, same reasoning as the 102 → 108 raise.
    # Raised 112 → 116 on 22 Aug 2026: merging fleet-mutation made two more reachable
    # (5d278c7, 32c1a7b; EXP-47 pre-registration and results, 20 Aug 2026 14:15–14:43),
    # same defect, same reasoning.
    # Raised 116 → 118 on 22 Aug 2026: merging fleet-retroverifier made one more
    # reachable (cda454f; EXP-43 primary at n=50, 20 Aug 2026 12:47), same defect,
    # same reasoning.
    # Raised 118 → 120 on 22 Aug 2026: merging fleet-transport made one more reachable
    # (6275650; ADR-0041/0042 authorship, 20 Aug 2026 15:15), same defect, same
    # reasoning. This is the last fixture-stamped branch: no further unmerged branch
    # carries an @local identity, so 120 is the final re-baseline of this raise.
    assert len(fixture_stamped) <= 120, (
        "a commit was authored by a fixture identity; check `git config user.email` — "
        "worktrees share the primary repository's config"
    )


# --------------------------------------------- credentials, after Joe's 20 Aug 2026 request
def _secret_checker_source() -> str:
    return Path(".github/scripts/check_secrets.py").read_text(encoding="utf-8")


def test_every_adapter_has_a_declared_credential_shape():
    """Adding a runtime must force adding its credential pattern, or the gap recurs.

    Grok Build was installed and authenticated on 20 Aug 2026 and the secret checker had **no
    xAI pattern at all** for the first hours of that runtime's life. Nothing failed, because
    nothing was checking that the pattern list kept pace with the runtimes.

    The fix goes in code rather than in a memory (working principle 4). Each adapter declares
    the credential shape its vendor issues; a vendor that issues none — subscription-only
    sign-in with a token the CLI keeps outside the repository — declares that explicitly, so
    the absence is a statement rather than an oversight.
    """
    # adapter stem -> the token prefix its vendor issues, or None for subscription-only.
    DECLARED = {
        "claude_code": "sk-ant-",
        "codex": "sk-",
        "cursor": None,  # editor sign-in; no user-visible key format
        "cursor_acp": None,  # same credential as cursor
        "antigravity": None,  # editor sign-in
        "opencode": None,  # brings its own provider key, covered by that provider
        "model_backed": None,  # local weights, no credential
        "grok": "xai-",
    }
    present = {
        path.stem.replace("adapter_", "")
        for path in Path("docs/10-research/experiments/exp05").glob("adapter_*.py")
    }
    undeclared = present - set(DECLARED)
    assert not undeclared, (
        f"adapter(s) {sorted(undeclared)} have no declared credential shape. Add the vendor's "
        "token prefix here and to .github/scripts/check_secrets.py, or declare None and say "
        "why in the commit."
    )

    source = _secret_checker_source()
    for stem, prefix in sorted(DECLARED.items()):
        if prefix is None or stem not in present:
            continue
        # The checker splits its literals so it does not match itself; match the same way.
        head, tail = prefix[:2], prefix[2:]
        assert f'"{head}" + r"{tail}' in source or f'"{head}" + r"-{tail}' in source, (
            f"{stem}'s vendor issues {prefix!r}-shaped tokens and check_secrets.py has no "
            f"pattern for it. This is the exact gap xAI sat in on 20 August 2026."
        )


def test_ci_secret_scan_also_reads_untracked_files():
    """`git grep` sees only tracked content, and agents leave files in the tree.

    A dispatched agent's transcript sitting untracked in the working directory was invisible to
    this check until someone staged it — the moment it is already too late. `--untracked` is
    what closes that, and it must not quietly disappear from the workflow.
    """
    workflow = Path(".github/workflows/secret-scan.yml").read_text(encoding="utf-8")
    assert "--untracked" in workflow, (
        "the CI secret scan stopped reading untracked files"
    )
    assert "--history" in workflow, "the CI secret scan stopped reading history"
    assert "--self-test" in workflow, (
        "the CI secret scan stopped proving it can still detect"
    )


def test_agent_transcripts_and_briefs_cannot_be_committed():
    """Dispatch transcripts are multi-megabyte verbatim records and belong nowhere near a commit.

    They carry whatever an agent read, printed, or was told. `git add -A` swept four brief files
    into a commit on 20 August 2026, so this is not hypothetical.
    """
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/dispatch/" in ignored, "agent transcripts became committable again"
    assert "brief-*.md" in ignored, "dispatch briefs became committable again"


# ------------------------------------------------ V0-33, privacy of the trajectory, 21 Aug 2026
def test_no_user_trajectory_is_tracked():
    """A user's trajectory is their data and is never tracked, so it cannot be published.

    Joe Brown, 21 August 2026: "Obviously we shouldn't be shipping anyones personal logs to
    the public repo ... my usage of consilient should remain private just like anyone elses
    unless they agree to share data in which case that is private and used to improve
    consilient only."

    Two days of trajectory -- `.harness/log/2026-08-19.jsonl` and `2026-08-20.jsonl` -- were
    tracked and reached the public repository before this check existed. Only `state.db` and
    `dispatch/` had ever been ignored. [measured] Publishing is one-way, so those two are not
    retractable; this stops the third.

    The project's own provenance -- which ADRs were accepted, what the gates measured -- is a
    DIFFERENT artefact and may be published deliberately. What must never happen is a user's
    log being published as a side effect of living in a tracked path. Today they are the same
    file only because this project is its own only user; that stops being true the moment
    anyone else runs it, and the fix belongs here rather than after it has a victim.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "ls-files", ".harness/log/"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    ).stdout.split()
    assert tracked == [], (
        "a user trajectory file is tracked and would be published on the next release: "
        f"{tracked}. The trajectory is private by default; publish a curated provenance "
        "record instead."
    )


def test_share_payloads_are_not_tracked():
    """A redacted share bundle is still user data and must not live on a tracked path.

    ADR-0057: data a user chooses to share is held privately, not published. The
    trajectory log was published by occupying a tracked path; the share directory
    is gitignored before any exporter exists so that failure cannot recur on the
    second artefact. docs/20-design/trajectory-sharing-consent-2026-08-21.md.
    """
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/share/" in gitignore, (
        ".harness/share/ is not in .gitignore; a share bundle would be committable "
        "the moment an exporter writes one"
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "ls-files", ".harness/share/"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    ).stdout.split()
    assert tracked == [], (
        "a share payload is tracked and would be published on the next release: "
        f"{tracked}"
    )


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


def test_no_instance_limits_or_captured_payload_is_committed():
    """PRODUCT ships the shape; INSTANCE keeps the numbers. Only the example is tracked.

    A limits file names what the principal is willing to spend and a captured payload is
    an observation of his account. Neither is a credential, and neither belongs in a public
    repository.
    """
    tracked = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    ).stdout.splitlines()
    assert ".harness/limits.example.json" in tracked, "the shape must ship"
    assert ".harness/limits.json" not in tracked, (
        "an instance limits file was committed"
    )
    assert not [name for name in tracked if name.startswith(".harness/usage/")], (
        "a captured provider payload was committed; those are instance observations"
    )
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/limits.json" in ignored and ".harness/usage/" in ignored


def test_this_repository_does_not_commit_under_a_test_fixture_identity() -> None:
    """MEASURED 27 August 2026 by a pre-publication audit, and it had been true for days.

    The live worktree's LOCAL git config read `Fixture <fixture@example.invalid>` while the
    global config was correct. `tests/test_supervision.py` sets that identity on a repository it
    builds, and it reached the real one. Consequence: 280 of the 289 commits awaiting
    publication were committed by a test fixture, and 63 were authored by one -- against roughly
    10% of the already-published history, so the defect was recent and accelerating.

    Publishing is one-way. Commit identity is part of the commit object, so a wrong committer
    travels by construction and cannot be corrected afterwards without rewriting every sha. The
    only cheap moment to catch this is before the push, which is exactly where nothing was
    looking.

    A `.invalid` address is the tell: RFC 2606 reserves that TLD precisely so it can never be a
    real address, which makes it perfect for a fixture and disqualifying for a commit anyone is
    meant to be able to trace.
    """
    import subprocess

    ident = subprocess.run(
        ["git", "var", "GIT_COMMITTER_IDENT"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip()
    if not ident:  # pragma: no cover - not a git checkout
        pytest.skip("git identity unavailable")

    lowered = ident.lower()
    assert ".invalid" not in lowered and "fixture" not in lowered, (
        "this repository is configured to commit under a test-fixture identity "
        f"({ident!r}). A test wrote it into the real config. Clear it with "
        "`git config --local --unset user.name` and `--unset user.email` so the "
        "global identity applies; every commit made meanwhile carries the wrong committer "
        "and cannot be corrected after a push."
    )
