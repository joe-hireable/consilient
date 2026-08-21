"""R23's documentation limb: the separation rule is pinned where it is stated.

The schema refuses composite fields on feedback events (commit 02d8838), but the
*doctrine* lives in docs/20-design/feedback-signals.md, and nothing failed if that
section was quietly reworded — the catalogued failure shape of a rule held in prose
alone. This test pins the load-bearing sentences so softening them is a diff a test
can see. Mutation: delete or reword any pinned line and this fails.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "20-design" / "feedback-signals.md"

PINNED = (
    "Efficiency and achievement are recorded separately",
    "separate records",
    "No default composite score exists anywhere in the product",
    "Any composite requires the user to set the weighting explicitly",
    "skippable with no consequence",
    "no re-ask for that task",
)


def _normalised(text: str) -> str:
    # Whitespace-insensitive: rewrapping a paragraph is not a rewording.
    return " ".join(text.split())


def test_feedback_signals_doc_keeps_the_separation_rule() -> None:
    text = _normalised(DOC.read_text(encoding="utf-8"))
    missing = [line for line in PINNED if _normalised(line) not in text]
    assert not missing, (
        "feedback-signals.md no longer states the separation rule verbatim; "
        "softening it is a decision, not an edit — missing:\n" + "\n".join(missing)
    )
