"""Regression checks for the local build driver."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("build_driver_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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

    monkeypatch.setattr(driver, "sh", lambda _args: _Result())
    assert driver.suite_green() is expected_green, summary


def test_an_xfail_alone_does_not_make_the_suite_red() -> None:
    """The specific regression: `\b\d+ failed` must not match inside "xfailed"."""
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

    monkeypatch.setattr(driver, "sh", lambda _args: _Result())
    assert driver.suite_green() is False
