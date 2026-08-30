"""The previous attempt's receipts must survive the next attempt starting.

Attempt 2 opens the live receipt with mode `w`, which truncates it, so attempt 1's
evidence has to be moved aside first or a check_error can never be diagnosed afterwards.
This is unit AI's deliverable and Rank 6 of the failure-classes register.

MEASURED 27 August 2026: `preserve_review_artefacts` moved the receipts with a bare
`src.replace(dst)`. A reviewer subprocess that had not yet closed its stdout still held
`N02-verify.out` open, Windows refused the rename with WinError 32, and the
PermissionError travelled all the way to `raise SystemExit(main())` — killing a tick
that had already dispatched work and merged nothing. The rename is history-keeping: it
is allowed to fail, and one failure must not abandon the receipts it could still have
moved. The tick is not allowed to fail.

MEASURED 28 August 2026: the guard added for that stopped the crash and not the loss. A
rename needs exclusive access, so whenever a previous dispatch still held the file the
archive silently did nothing, and AI's reviewers measured exactly this and returned
DEFECTIVE three times. A copy reads the source, which Windows permits while another
handle holds it. The held-open handle is the whole point of the fixture — without it a
rename passes and the test proves nothing.

The last check is on the production call site rather than on the helper, and it is
structural because the property is structural — an ordering between two calls. AI's
second finding, measured by its reviewers: deleting `preserve_review_artefacts(uid,
attempt)` immediately before the verify `spawn_logged` left the whole suite green, 89
passed, and the self-test still printed PASS, because `_self_test` calls the helpers
directly and never the dispatch site. Positive controls on the same command showed the
suite is not blind in general; it was blind exactly there."""

import ast
import sys
import subprocess
from pathlib import Path
from build_driver_helpers import (
    DRIVER,
    ROOT,
    _load_driver,
)


def test_an_open_receipt_does_not_kill_the_tick(tmp_path: Path) -> None:
    """A receipt another process still holds open must not reach __main__.

    MEASURED 27 August 2026. `preserve_review_artefacts` renamed the previous attempt's
    receipts aside with a bare `src.replace(dst)`. A reviewer subprocess that had not yet
    closed its stdout still held `N02-verify.out`, Windows refused the rename with WinError
    32, and the PermissionError travelled to `raise SystemExit(main())` -- killing a tick
    that had already dispatched work and merged nothing.

    The rename is history-keeping. It is allowed to fail; the tick is not.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs-driver"
    briefs.mkdir()
    driver.BRIEFS = briefs

    held = briefs / "N02-verify.out"
    held.write_text("first attempt receipt", encoding="utf-8")
    (briefs / "N02-verdict.json").write_text("{}", encoding="utf-8")

    handle = open(held, "a", encoding="utf-8")
    try:
        driver.preserve_review_artefacts("N02", 2)  # must not raise
    finally:
        handle.close()

    # The receipt that COULD be renamed still was: one failure must not abandon the rest.
    assert (briefs / "N02-verdict-1.json").exists()


def test_the_previous_attempts_receipt_survives_a_held_open_file(
    tmp_path: Path,
) -> None:
    """Attempt 1's receipt must still be readable after attempt 2 starts.

    This is unit AI's deliverable and it is Rank 6 of the failure-classes register: opening
    the live receipt with mode 'w' destroyed the previous attempt, so a check_error could
    not be diagnosed afterwards.

    MEASURED 28 August 2026. The archive was a RENAME, and a rename needs exclusive access:
    when a previous dispatch still held the file open it raised WinError 32. The guard
    added on 27 August caught that and carried on -- so the crash stopped and the loss did
    not. AI's reviewers measured exactly this and returned DEFECTIVE three times.

    A copy reads the source, which Windows permits while another handle holds it.

    The held-open handle is the whole point of the fixture: without it a rename passes and
    the test proves nothing.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs-driver"
    briefs.mkdir()
    driver.BRIEFS = briefs

    live = briefs / "U01-verify.out"
    live.write_text("attempt-1 receipt", encoding="utf-8")
    (briefs / "U01-verdict.json").write_text("{}", encoding="utf-8")

    holder = open(live, "a", encoding="utf-8")
    try:
        driver.preserve_review_artefacts("U01", 2)
    finally:
        holder.close()

    # the next dispatch opens the live path with mode 'w'
    with live.open("w", encoding="utf-8") as handle:
        handle.write("attempt-2 live")

    archived = briefs / "U01-verify-1.out"
    assert archived.is_file(), (
        "attempt 1 was not archived: a held-open receipt defeated the archive"
    )
    assert archived.read_text(encoding="utf-8") == "attempt-1 receipt"
    assert live.read_text(encoding="utf-8") == "attempt-2 live"


def test_the_review_dispatch_archives_before_it_truncates() -> None:
    """The production CALL SITE is enforced, not merely the helper.

    AI's second finding, measured by its reviewers: deleting
    `preserve_review_artefacts(uid, attempt)` immediately before the verify `spawn_logged`
    left the whole suite green -- 89 passed -- and the self-test still printed PASS,
    because `_self_test` calls the helpers directly and never the dispatch site. They ran
    positive controls on the same command to show the suite is not blind in general; it was
    blind exactly there.

    So this asserts the ORDER at the site: within the review dispatch, the archive must
    happen before the spawn that truncates. It is a structural test because the property is
    structural -- an ordering between two calls -- and a behavioural test of the helper
    alone cannot see the site at all, which is precisely how this was missed.
    """
    source = DRIVER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    spawn_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "spawn_logged"
        and "verify" in ast.unparse(node)
    ]
    assert spawn_lines, "no verify dispatch found -- has the site moved?"

    preserve_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "preserve_review_artefacts"
    ]
    for spawn_at in spawn_lines:
        assert any(0 < spawn_at - at <= 6 for at in preserve_lines), (
            f"the verify dispatch at line {spawn_at} is not preceded by "
            "preserve_review_artefacts; attempt 1 will be truncated"
        )


def test_the_driver_self_test_is_actually_run() -> None:
    """`build_driver.py --self-test` must pass, and something must invoke it. This is that thing.

    MEASURED 30 August 2026. Every other `--self-test` in this repository has an invoker --
    check_adr_trail, check_merge_acceptance, check_source_depth, check_foreign_identifiers and
    split_module are each run by a test. build_driver's had none: no test, no CI step, nothing.

    So it rotted silently. `_self_test` asserted that preserve_review_artefacts REMOVES the live
    file, which was true until 28 August when the helper moved to shutil.copy2 because a rename
    fails with WinError 32 while another handle holds the file. From that day the driver's own
    self-test exited 1 on every invocation nobody made, for two days, while the pytest suite
    beside it stayed green -- the suite tested the helper, and only the self-test tested the
    self-test.

    Unit AI's review found it, was refused three times, and was right each time. A self-test that
    nothing runs is not a check; it is a comment that happens to be executable, and working
    principle 3 says a chokepoint without an enforcement rule is no chokepoint. This is the rule.
    """
    result = subprocess.run(
        [sys.executable, str(DRIVER), "--self-test"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, (
        "build_driver.py --self-test failed:\n" + (result.stdout + result.stderr)[-1500:]
    )
