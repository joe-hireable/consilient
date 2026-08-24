"""Z05 — every retry backoff carries full jitter, and no site sleeps in lockstep.

A chokepoint without an enforcement rule is not a chokepoint (AGENTS.md principle 3), so the
jitter ships with the check that keeps it. The defect this guards was measured on 24 August
2026: `could not be read after 6 attempts: observed access denial` was the commonest crash
signature in driver state, with single units dying that way 77 and 78 times, because roughly
twenty concurrent agents share one append-only trajectory and all retried on the same schedule.

Cited: Marc Brooker, "Exponential Backoff And Jitter", AWS Architecture Blog, 4 March 2015.
"""

from __future__ import annotations

import ast
import pathlib
import re
import statistics

import pytest

from consilient import events

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "consilient"


def _sleep_arguments(path: pathlib.Path) -> list[tuple[int, str]]:
    """Every `time.sleep(...)` argument in a module, with its line number."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Attribute):
            name = func.attr
            if isinstance(func.value, ast.Name):
                name = f"{func.value.id}.{func.attr}"
        elif isinstance(func, ast.Name):
            name = func.id
        if name in {"time.sleep", "sleep"} and node.args:
            found.append((node.lineno, ast.unparse(node.args[0])))
    return found


@pytest.mark.parametrize("module", ["events.py", "cli.py"])
def test_no_retry_sleeps_in_lockstep(module: str) -> None:
    """A doubling backoff with no jitter is the herd. Fail on the bare `2**` pattern."""
    path = SRC / module
    offenders = [
        (line, arg)
        for line, arg in _sleep_arguments(path)
        if "2**" in arg.replace(" ", "")
    ]
    assert not offenders, (
        f"{module} sleeps on an exponential schedule directly at "
        + ", ".join(f"line {line}: {arg}" for line, arg in offenders)
        + " -- a doubling backoff with no jitter puts every waiter on the same instant. "
        "Route it through events.jittered_sleep. Do NOT fix this by raising the retry count "
        "or the budget; that widens the window without decorrelating anything."
    )


def test_retry_sleep_is_bounded_by_the_unjittered_schedule() -> None:
    """Full jitter keeps the same ceiling; it only spreads waiters underneath it."""
    slept: list[float] = []
    original = events.time.sleep
    events.time.sleep = slept.append  # type: ignore[assignment]
    try:
        for attempt in range(events._READ_RETRIES):
            events._retry_sleep(attempt)
    finally:
        events.time.sleep = original  # type: ignore[assignment]

    assert len(slept) == events._READ_RETRIES
    for attempt, delay in enumerate(slept):
        ceiling = events._READ_BACKOFF * (2**attempt)
        assert 0.0 <= delay <= ceiling, (
            f"attempt {attempt} slept {delay}, ceiling {ceiling}"
        )


def test_retry_sleep_decorrelates_across_processes() -> None:
    """Twenty processes evicted together must not retry together.

    This is the property that matters and it is a CROSS-process one: the herd is twenty
    separate dispatchers, each with one waiter, all evicted by the same writer. Within a
    single process there is only ever one waiter, and its successive attempts are already
    separated by the doubling ceiling.

    So vary the process id, which is exactly what differs in the real herd, and require the
    draws to spread rather than land together.
    """
    attempt = 3
    ceiling = events._READ_BACKOFF * (2**attempt)
    delays = [_draw_as_pid(attempt, pid) for pid in range(4100, 4120)]

    assert len(set(delays)) > 1, "every process drew the same delay -- that is lockstep"
    assert statistics.pstdev(delays) > 0.0
    assert all(0.0 <= d <= ceiling for d in delays)
    # Neighbouring pids arrive in blocks when a driver launches its dispatchers, so
    # consecutive ids must not produce consecutive delays.
    assert max(delays) - min(delays) > ceiling / 4, (
        f"twenty processes spread over only {max(delays) - min(delays):.6f}s of a "
        f"{ceiling:.6f}s ceiling -- not enough decorrelation to break a herd"
    )


def test_the_unjittered_schedule_would_have_failed_that() -> None:
    """Negative control: the code this replaced puts every waiter on the same instant."""
    attempt = 3
    lockstep = [events._READ_BACKOFF * (2**attempt) for _ in range(20)]
    assert len(set(lockstep)) == 1
    assert statistics.pstdev(lockstep) == 0.0


def _draw_as_pid(attempt: int, pid: int) -> float:
    """One jitter draw as if this were process `pid`, without sleeping."""
    captured: list[float] = []
    real_sleep, real_getpid = events.time.sleep, events.os.getpid
    events.time.sleep = captured.append  # type: ignore[assignment]
    events.os.getpid = lambda: pid  # type: ignore[assignment]
    try:
        events._retry_sleep(attempt)
    finally:
        events.time.sleep = real_sleep  # type: ignore[assignment]
        events.os.getpid = real_getpid  # type: ignore[assignment]
    return captured[0]


def test_the_retry_budget_was_not_widened_to_make_this_pass() -> None:
    """The remedy is decorrelation, never a longer window. Pin both constants."""
    assert events._READ_RETRIES == 6, (
        "the read retry count changed; full jitter is the fix for contention, and raising the "
        "count widens the window a bad read can hide in without decorrelating anything"
    )
    assert events._READ_BACKOFF == pytest.approx(0.04)


def test_the_refusal_still_fails_closed() -> None:
    """Jitter must not have turned a refused read into a silent empty trajectory."""
    source = (SRC / "events.py").read_text(encoding="utf-8")
    assert re.search(r"could not be read after .* attempts", source), (
        "the read refusal message is gone; a reader that silently returns an incomplete "
        "trajectory is far worse than one that stops"
    )
