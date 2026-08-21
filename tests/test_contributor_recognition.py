"""R21: contributor recognition exists and stays social-only.

Two limbs, both pinned. Positive: a CONTRIBUTORS file exists with an opt-in listing
mechanism and the social-only rule stated in it. Negative: no code path keys capability
on contributor status — ADR-0024 forbids capability as reward, and until this test the
prohibition lived only in prose (docs/00-context/ways-to-contribute.md:56-58,
docs/20-design/feedback-signals.md:150-153), the exact pattern this repository catalogues
as guards that could not fail.

What the guard can and cannot see [asserted]: it scans Python source for identifiers that
join contributor status to a reward mechanic (``contributor_tier``, ``unlock_for_
contributors`` and their kin). Prose uses of "tier" (the critic tier, plan tiers, ADR-0065
import tiers) are legitimate and must not trip it — they are why the pattern keys on the
join, not the words. A reward hidden in prose alone is the doctrine files' problem, and
their wording is pinned below instead.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTORS = ROOT / "CONTRIBUTORS.md"

# The join is the defect: contributor status on one side, a reward mechanic on the other.
# Either order, with up to two identifier words between. Prose senses of "tier" never
# carry "contributor" next to them in this tree [measured: grep, 21 Aug 2026].
REWARD_JOIN = re.compile(
    r"contribut\w*[_\s]{0,3}(?:\w+[_\s]{0,3}){0,2}(perk|premium|unlock|tier|badge|reward)"
    r"|(perk|premium|unlock|tier|badge|reward)[_\s]{0,3}(?:\w+[_\s]{0,3}){0,2}contribut\w*",
    re.IGNORECASE,
)

SCANNED_SUFFIXES = {".py"}


def _python_files():
    for base in ("src", "scripts"):
        yield from (ROOT / base).rglob("*.py")


def test_contributors_file_states_the_social_only_rule() -> None:
    assert CONTRIBUTORS.is_file(), "CONTRIBUTORS.md is missing — recognition does not exist"
    text = CONTRIBUTORS.read_text(encoding="utf-8")
    for phrase in (
        "social only",
        "no perks",
        "opt-in",
        "release notes",
    ):
        assert phrase in text.lower(), f"CONTRIBUTORS.md must state: {phrase!r}"
    assert "ADR-0024" in text, "the social-only rule cites ADR-0024"


def test_no_code_keys_capability_on_contributor_status() -> None:
    offenders = []
    for path in _python_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if REWARD_JOIN.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "contributor-keyed reward mechanics found (ADR-0024 forbids capability as "
        "reward):\n" + "\n".join(offenders)
    )


def test_the_guard_can_fail() -> None:
    """Mutation check: a contributor-keyed reward line must trip the pattern."""
    assert REWARD_JOIN.search("contributor_tier = 'gold'")
    assert REWARD_JOIN.search("def unlock_for_contributors(user):")
    assert REWARD_JOIN.search("premium_contributor_console")
    assert not REWARD_JOIN.search("the critic tier's own beta is measured")
    assert not REWARD_JOIN.search("plan tier is observed but is not headroom")
