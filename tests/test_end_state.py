"""W05: the end-state page a stranger can read.

docs/20-design/documentation-and-surfaces-plan-2026-08-23.md, build unit 5.
The page is the flagship a newcomer is sent to. Two measured failures it must
not repeat:

- A restated live value becomes a second source of truth. On 23 August 2026 two
  generated documents had drifted while CI was green because the checker was
  unwired. [measured] The distance table therefore names the command that
  answers the question, not a copy of today's answer.
- A uniqueness claim without an incumbent is the README's "Nothing on the
  market measures it" failure, which this repository's own register already
  contradicted. [measured] The page may not say nobody else measures verifier
  error.

The plan asked for the distance column as a C1-checked generated region. A
generated region still holds a copy that is stale between regeneration and
commit — the same failure. A row holding no copy cannot drift. This test
pins that correction rather than the plan's weaker mechanism.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "END-STATE.md"
LIVING = ROOT / ".github" / "scripts" / "check_living_documents.py"

RESTATED_COUNT = (
    re.compile(r"(?<![\w,])\d[\d,]*\s+ADRs?\b", re.IGNORECASE),
    re.compile(r"(?<![\w,])\d[\d,]*\s+registered\s+experiments?\b", re.IGNORECASE),
    re.compile(
        r"(?<![\w,])\d[\d,]*\s+(?:specifications?|specs?)\b", re.IGNORECASE
    ),
)
LIVE_FLAG_VALUE = re.compile(
    r"routing_orchestration_enabled\s*:\s*(true|false)\b", re.IGNORECASE
)
UNIQUENESS = re.compile(
    r"\b(?:nobody else|no one else|nothing on the market|"
    r"the only (?:system|harness|tool|project|product)|"
    r"the first (?:system|harness|tool|project|product))\b",
    re.IGNORECASE,
)
GENERATED_REGION = re.compile(
    r"<!--\s*(?:BEGIN|END) GENERATED:", re.IGNORECASE
)


def _text() -> str:
    assert PAGE.is_file(), "docs/END-STATE.md is the W05 deliverable and must exist"
    return PAGE.read_text(encoding="utf-8")


def test_end_state_page_exists_and_is_admitted_as_class_w() -> None:
    text = _text()
    header = "\n".join(text.splitlines()[:20])
    assert re.search(r"Document class:\s*\**\s*W\b", header, re.IGNORECASE)
    assert re.search(r"Review by:\s*\**\s*`?2026-09-24`?", header, re.IGNORECASE)
    assert re.search(r"Falsifier:", header, re.IGNORECASE)

    run = subprocess.run(
        [sys.executable, str(LIVING), "--check", "docs/END-STATE.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "checked=1" in run.stdout
    assert "broken=0" in run.stdout
    assert "stale=0" in run.stdout


def test_the_page_is_not_a_status_report_and_names_the_distance() -> None:
    text = _text()
    assert "not a status report" in text.lower()
    assert "`consil doctor`" in text
    assert "`consil beta`" in text
    assert "`consil replay`" in text
    assert "Q24" in text
    assert "docs/00-context/the-machine-2026-08-22.md:25" in text


def test_distance_table_names_commands_not_live_values() -> None:
    """A generated copy of today's doctor output would be stale tomorrow.

    The plan's C1 region still holds a copy. Naming the command does not.
    """
    text = _text()
    assert "| What this page describes | Where the code is | Ask it yourself |" in text
    assert LIVE_FLAG_VALUE.search(text) is None, (
        "END-STATE.md restates a live gate flag. Name `consil doctor` and the "
        "field to read; do not print today's value."
    )
    assert GENERATED_REGION.search(text) is None, (
        "a generated region on this page would be a copy of live state with no "
        "producer (project-facts.md and the regions manifest type are later "
        "units). Commands, not copies."
    )


def test_written_prose_does_not_restate_inventory_counts() -> None:
    text = _text()
    offenders: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern in RESTATED_COUNT:
            if match := pattern.search(line):
                offenders.append(f"{line_no}: {match.group(0)}")
    assert not offenders, (
        "END-STATE.md restates a generated inventory count; point at the "
        "command or at docs/project-facts.md when that spine exists:\n  "
        + "\n  ".join(offenders)
    )


def test_uniqueness_claims_are_refused() -> None:
    """Public uniqueness without an incumbent is the README failure, again.

    Reflexion (Shinn et al., arXiv:2303.11366) already consumes test feedback;
    Cobbe et al. 2110.14168 already train verifiers whose failure mode is β.
    The honest claim is measurement on the reader's work, not 'nobody else'.
    """
    text = _text()
    offenders: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if UNIQUENESS.search(line):
            offenders.append(f"{line_no}: {line.strip()[:100]}")
    assert not offenders, (
        "END-STATE.md claims uniqueness without naming an incumbent. Drop the "
        "superlative or cite who was searched:\n  " + "\n  ".join(offenders)
    )


def test_ask_list_follows_adr_0033_not_the_plan_six() -> None:
    text = _text().lower()
    for needle in (
        "money",
        "credential",
        "taste",
        "safety floor",
        "verdict",
        "publishing",
        "lifting a gate",
    ):
        assert needle in text, (
            f"ADR-0033 §2 names seven user-only classes; {needle!r} is missing. "
            "The plan's six dropped the β verdict and the safety floor."
        )


def test_open_core_and_byo_model_are_not_smoothed() -> None:
    text = _text()
    assert "ADR-0024" in text and "PROPOSED" in text
    assert "ADR-0048" in text and "ACCEPTED" in text
    assert "intention, not yet a check" in text.lower() or (
        "not yet a check" in text.lower()
    )


def test_relative_links_on_this_page_resolve() -> None:
    text = _text()
    missing: list[str] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).split("#", 1)[0].strip()
        if not target or "://" in target:
            continue
        dest = (PAGE.parent / target).resolve()
        if not dest.is_file():
            missing.append(target)
    assert not missing, (
        "END-STATE.md points at a path that is not a file:\n  " + "\n  ".join(missing)
    )
