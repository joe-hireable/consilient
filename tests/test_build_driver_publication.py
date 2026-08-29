"""Everything that must be true before a commit leaves this machine.

Three conditions guard publication and each was found broken in the same week. The STOP-
PUBLISH marker must be honoured before git is called at all.

The suite must be green, and `suite_green` judged that with substring tests — `"passed"
in last and "failed" not in last` — while pytest's summary for a green run of this
repository reads `1761 passed, 3 skipped, 1 xfailed in 250.69s`, and "xfailed" contains
"failed". So a suite with a single expected failure was reported red for ever, and the
gate printed "publish held: 123 commit(s) ready, suite not green" tick after tick while
public sat 123 commits behind [measured, 25 August 2026]. An xfail is a passing outcome.
An absent summary is not: it means the run did not complete, which is not the same as
passing, and neither is a run that never finishes — a tick sat thirty-five minutes on
the suite having burned 29 seconds of CPU, starved rather than computing, because `sh()`
passed no timeout. The parametrised cases here are the real summary lines this
repository produced on 24 and 25 August 2026.

The push itself is the third. `git push public HEAD:main` would have sent 294 commits of
which 275 carried a `Signed-off-by` naming `fixture@example.invalid` — an RFC 2606
address reserved so it can never resolve to anyone — and 240 had no sign-off matching
their author at all, because this worktree's local git config had been written by a test
fixture [measured, 27 August 2026]. Rewriting the commits was measured and rejected: 283
of 635 refs are based inside the unpublished range, with 455 worktrees checked out
against them. So the tree is published as one squashed commit whose author, committer
and sign-off are the same real identity, parented on `public/main` so the push fast-
forwards; and a repository whose config has been poisoned refuses to publish at all. A
sign-off is a certification of origin, and publishing is one-way."""

import re
import subprocess
from pathlib import Path
import pytest
from build_driver_helpers import (
    _load_driver,
)


def test_stop_marker_blocks_publication_before_git_is_called(
    tmp_path: Path, monkeypatch
) -> None:
    driver = _load_driver()
    stop = tmp_path / "STOP-PUBLISH"
    stop.write_text("hold", encoding="utf-8")
    monkeypatch.setattr(driver, "PUBLISH_STOP", stop)

    def unexpected_git(_args):
        raise AssertionError("publication guard called git")

    monkeypatch.setattr(driver, "sh", unexpected_git)
    assert driver.publish_if_ready({}, True) == "publish held: STOP-PUBLISH is present"


# --------------------------------------------------------- suite_green, 25 August 2026
#
# `suite_green` decides whether anything may retire, merge or publish, and it judged the
# summary line with substring tests: `"passed" in last and "failed" not in last`. pytest's
# summary for a GREEN run of this repository reads
#
#     1761 passed, 3 skipped, 1 xfailed in 250.69s
#
# and "xfailed" contains "failed". So a suite with a single expected failure was reported red
# for ever, and the publication gate printed "publish held: 123 commit(s) ready, suite not
# green" tick after tick while public sat 123 commits behind. An xfail is a PASSING outcome.
#
# These cases are the real summary lines this repository produced on 24 and 25 August.
SUMMARY_CASES = [
    ("1761 passed, 3 skipped, 1 xfailed in 250.69s (0:04:10)", True),
    ("1739 passed, 3 skipped, 1 xfailed in 233.70s", True),
    ("1761 passed in 210.41s", True),
    ("5 xfailed, 10 passed in 1.0s", True),
    ("3 failed, 1758 passed, 3 skipped, 1 xfailed in 210.41s", False),
    ("18 failed, 1721 passed, 3 skipped, 1 xfailed in 179.74s", False),
    ("1 failed, 1760 passed in 201.34s", False),
    ("2 errors in 3.10s", False),
    ("1 error, 5 passed in 1.2s", False),
    ("no tests ran in 0.01s", False),
]


@pytest.mark.parametrize("summary, expected_green", SUMMARY_CASES)
def test_suite_green_counts_outcomes_rather_than_sniffing_substrings(
    summary: str, expected_green: bool, monkeypatch
) -> None:
    driver = _load_driver()

    class _Result:
        stdout = summary
        stderr = ""

    monkeypatch.setattr(driver, "sh", lambda _args, **_kw: _Result())
    assert driver.suite_green() is expected_green, summary


def test_an_xfail_alone_does_not_make_the_suite_red() -> None:
    r"""The specific regression: `\b\d+ failed` must not match inside "xfailed"."""
    green = "1761 passed, 3 skipped, 1 xfailed in 250.69s"
    assert re.search(r"\b\d+ (failed|error|errors)\b", green) is None
    assert re.search(r"\b\d+ passed\b", green) is not None
    # And the implementation this replaced got it wrong, which is why the check exists.
    assert not ("passed" in green and "failed" not in green)


def test_suite_green_fails_closed_when_pytest_printed_no_summary(monkeypatch) -> None:
    """An absent summary means the run did not complete. That is not the same as passing."""
    driver = _load_driver()

    class _Result:
        stdout = "ERROR: usage: pytest [options]\nunrecognised argument: --timeout=600"
        stderr = ""

    monkeypatch.setattr(driver, "sh", lambda _args, **_kw: _Result())
    assert driver.suite_green() is False


def test_suite_green_fails_closed_when_the_run_does_not_finish(monkeypatch) -> None:
    """MEASURED 25 August 2026, 21:36: a tick sat THIRTY-FIVE MINUTES on the suite having burned
    29 seconds of CPU -- starved, not computing -- because `sh()` passes no timeout. The only
    bound was the loop abandoning the whole tick at 3000s, which also leaks grandchildren.

    The starvation is self-inflicted: the same tick dispatches its agents and then runs the full
    suite against the load it just created. Since the suite is the last gate before publication,
    a tick that never finishes it never publishes -- thirty commits sat behind exactly this.

    An unfinished run is "not evaluated", which is not "passing".
    """
    driver = _load_driver()

    def _timeout(*_args, **kwargs):
        assert "timeout" in kwargs, "the suite call must carry a timeout"
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=kwargs["timeout"])

    monkeypatch.setattr(driver, "sh", _timeout)
    assert driver.suite_green() is False


def test_the_suite_bound_is_well_inside_the_tick_abandonment(monkeypatch) -> None:
    """The bound only helps if it fires before the loop gives up on the whole tick. The loop
    abandons at 3000s; a clean run of this suite is about seven minutes."""
    driver = _load_driver()
    assert driver.SUITE_TIMEOUT_S >= 600, (
        "shorter than a clean run would fail closed constantly"
    )
    assert driver.SUITE_TIMEOUT_S <= 1800, (
        "must fire well before the 3000s tick abandonment"
    )


class _Res:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _publish_harness(driver, monkeypatch, tmp_path, ident: str):
    """Drive `publish_if_ready` over a fake git, recording every command."""
    calls: list[list[str]] = []
    squash_sha = "a" * 40

    def fake_sh(args, **_kw):
        calls.append(list(args))
        if args[:3] == ["git", "rev-list", "--count"]:
            return _Res("7\n")
        if args[:3] == ["git", "var", "GIT_AUTHOR_IDENT"]:
            return _Res(f"{ident} 1787841088 +0100\n")
        if args[:2] == ["git", "commit-tree"]:
            return _Res(squash_sha + "\n")
        return _Res("")

    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "PUBLISH_STOP", tmp_path / "absent")
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    for script, _args in [
        (".github/scripts/check_foreign_identifiers.py", []),
        (".github/scripts/check_secrets.py", []),
        (".github/scripts/check_private_corpus.py", []),
        (".github/scripts/check_private_repo_names.py", []),
        (".github/scripts/check_generated_documents.py", ["--check"]),
    ]:
        path = tmp_path / script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return calls, squash_sha


def test_publication_never_pushes_the_branch_itself(tmp_path, monkeypatch) -> None:
    """MEASURED 27 August 2026, on a push that was about to happen.

    This path read `git push public HEAD:main`. What that would have sent was 294 commits of
    which 275 carried a `Signed-off-by` naming `fixture@example.invalid` -- an RFC 2606 address
    reserved so it can never resolve to anyone -- and 240 had no sign-off matching their author
    at all, because this worktree's local git config had been written by a test fixture.

    CONTRIBUTING.md requires a real name and email; the DCO workflow requires a sign-off
    matching the author. A sign-off is a certification of ORIGIN, so pushing the branch would
    have filed 240 false certifications in a public repository whose declared subject is
    provenance -- and publishing is one-way.

    Rewriting the commits was measured and rejected: 283 of 635 refs are based inside the
    unpublished range, with 455 worktrees checked out against them. So the tree is published
    under one commit whose author, committer and sign-off are the same real identity.
    """
    driver = _load_driver()
    # NOT an example.com address, which is the joke this test used to be at the expense of: the
    # fixture identity was `joe@example.com`, itself an RFC 2606 reserved domain, in a test whose
    # own docstring explains that reserved domains cannot certify origin. It passed only because
    # the guard checked for the two literal spellings "fixture" and ".invalid". When the guard
    # was widened to the actual property on 29 August 2026, this test was the first thing it
    # caught. A fixture must be a plausible REAL identity or it cannot exercise the accept path.
    calls, squash_sha = _publish_harness(
        driver,
        monkeypatch,
        tmp_path,
        "Joe Brown <joe@publisher.example-not-reserved.co.uk>",
    )

    result = driver.publish_if_ready({}, True)

    pushes = [c for c in calls if c[:3] == ["git", "push", "public"]]
    assert pushes, f"nothing was pushed: {result}"
    assert ["git", "push", "public", "HEAD:main"] not in calls, (
        "the branch itself was pushed; every fixture-signed commit in it travels"
    )
    assert pushes[0][3] == f"{squash_sha}:main", pushes[0]

    tree = [c for c in calls if c[:2] == ["git", "commit-tree"]]
    assert tree and "public/main" in tree[0], (
        "the squash must be parented on public/main so the push fast-forwards"
    )
    assert (
        "Signed-off-by: Joe Brown <joe@publisher.example-not-reserved.co.uk>"
        in tree[0][-1]
    ), "the published commit must carry a sign-off naming its own author"
    assert any(c[:4] == ["git", "merge", "-s", "ours"] for c in calls), (
        "public/main must be recorded as an ancestor, or every later tick re-publishes"
    )


def test_publication_refuses_to_certify_origin_as_a_fixture(
    tmp_path, monkeypatch
) -> None:
    """The identity that signs is the identity that is configured, so the check belongs here
    too -- a repository whose config has been poisoned must not publish at all, rather than
    publish one commit that certifies origin as somebody who does not exist."""
    driver = _load_driver()
    calls, _ = _publish_harness(
        driver, monkeypatch, tmp_path, "Fixture <fixture@example.invalid>"
    )

    result = driver.publish_if_ready({}, True)

    assert "REFUSED" in result, result
    assert not [c for c in calls if c[:3] == ["git", "push", "public"]], (
        "it published anyway under an identity that cannot certify anything"
    )
