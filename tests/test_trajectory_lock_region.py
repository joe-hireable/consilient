"""The transaction lock must not sit on a byte that readers read.

MEASURED 25 August 2026, from `.harness/build-loop.log`: of 4,930 recorded dispatch deaths,
3,895 -- 79% -- were `could not be read after 6 attempts: observed access denial` on the
shared trajectory, across 106 units. It was the largest single cause of failure in the
system, larger than every other cause put together.

The cause was not the retry budget, which is correct, and not contention in the abstract. It
was the lock OFFSET. `_lock_file` seeks to 0 and locks one byte, and byte 0 is inside the
region every reader reads, so a transaction denied every concurrent reader for as long as it
held the lock -- including the full parse of the prefix it performs before writing anything.

A chokepoint without an enforcement rule is not a chokepoint (AGENTS.md principle 3), so the
offset ships with the checks that keep it there. The first test below fails on the code as it
stood this morning.

Windows-only by nature: POSIX `flock` is whole-file and advisory, so it excludes writers
without ever denying a reader. That is why this failure never appeared on CI.
"""

from __future__ import annotations

import ast
import os
import pathlib
import sys

import pytest

from consilient import events

SRC = (
    pathlib.Path(__file__).resolve().parent.parent / "src" / "consilient" / "events.py"
)

windows_only = pytest.mark.skipif(
    sys.platform != "win32",
    reason="byte-range lock denial is a Windows behaviour; POSIX flock is advisory",
)


def _populate(path: pathlib.Path, lines: int = 200) -> int:
    """A trajectory-shaped file. The lines need not validate: what is under test is
    whether the bytes can be READ while a transaction holds the lock, and a line that
    fails validation is returned as a Rejection rather than raising."""
    path.write_text('{"event": "probe"}\n' * lines, encoding="utf-8")
    return lines


@windows_only
def test_a_reader_is_not_denied_while_a_transaction_holds_the_lock(
    tmp_path: pathlib.Path,
) -> None:
    """The regression test for 3,895 deaths. Fails if the lock returns to byte 0."""
    log = tmp_path / "2026-08-25.jsonl"
    written = _populate(log)

    fd = os.open(log, events._TRANSACTION_OPEN_FLAGS)
    try:
        events._lock_file(fd)
        try:
            accepted, rejected = events.read(log)
        finally:
            events._unlock_file(fd)
    finally:
        os.close(fd)

    # Every line was reached: a partial read would be worse than a refused one.
    assert len(accepted) + len(rejected) == written


@windows_only
def test_a_second_writer_is_still_excluded(tmp_path: pathlib.Path) -> None:
    """Freeing readers must not free writers. Same region, so they still contend."""
    import msvcrt

    log = tmp_path / "2026-08-25.jsonl"
    _populate(log)

    first = os.open(log, events._TRANSACTION_OPEN_FLAGS)
    second = os.open(log, events._TRANSACTION_OPEN_FLAGS)
    try:
        events._lock_file(first)
        os.lseek(second, events._TRANSACTION_LOCK_BYTE, os.SEEK_SET)
        with pytest.raises(OSError):
            msvcrt.locking(second, msvcrt.LK_NBLCK, 1)
        events._unlock_file(first)
        # And released cleanly: the next writer gets it.
        os.lseek(second, events._TRANSACTION_LOCK_BYTE, os.SEEK_SET)
        msvcrt.locking(second, msvcrt.LK_NBLCK, 1)
        os.lseek(second, events._TRANSACTION_LOCK_BYTE, os.SEEK_SET)
        msvcrt.locking(second, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(second)
        os.close(first)


@windows_only
def test_the_append_region_excludes_a_writer_that_has_not_moved_its_lock(
    tmp_path: pathlib.Path,
) -> None:
    """`_appending` holds byte 0, so a writer still locking byte 0 -- an older checkout, a
    process that imported this module before the change, another tool appending to the same
    trajectory -- cannot interleave a write with ours."""
    import msvcrt

    log = tmp_path / "2026-08-25.jsonl"
    _populate(log)

    ours = os.open(log, events._TRANSACTION_OPEN_FLAGS)
    theirs = os.open(log, events._TRANSACTION_OPEN_FLAGS)
    try:
        with events._appending(ours):
            os.lseek(theirs, 0, os.SEEK_SET)
            with pytest.raises(OSError):
                msvcrt.locking(theirs, msvcrt.LK_NBLCK, 1)
        # Released on exit, including by the context manager's finally.
        os.lseek(theirs, 0, os.SEEK_SET)
        msvcrt.locking(theirs, msvcrt.LK_NBLCK, 1)
        os.lseek(theirs, 0, os.SEEK_SET)
        msvcrt.locking(theirs, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(theirs)
        os.close(ours)


def test_the_lock_byte_is_past_any_trajectory_this_project_can_write() -> None:
    """One terabyte. A JSONL trajectory reaching this offset has a different problem."""
    assert events._TRANSACTION_LOCK_BYTE >= 1 << 40


def test_lock_and_unlock_seek_to_the_sentinel_and_never_to_zero() -> None:
    """The source-level ratchet. The defect was a literal `0` in these two functions, and it
    survived months of review because it looks like the obvious thing to write. Reading the
    offset out of the AST means a regression fails here rather than in production, where it
    cost 3,895 deaths before anyone attributed them to a seek."""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name not in {
            "_lock_file",
            "_unlock_file",
        }:
            continue
        checked += 1
        offsets = [
            ast.unparse(call.args[1])
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "lseek"
            and len(call.args) >= 2
        ]
        assert offsets, f"{node.name} performs no seek before locking"
        for offset in offsets:
            assert "_TRANSACTION_LOCK_BYTE" in offset, (
                f"{node.name} seeks to {offset!r} before locking. The transaction lock must "
                "not sit on a byte any reader reads -- that is the 79% defect."
            )
    assert checked == 2, "expected to inspect both _lock_file and _unlock_file"
