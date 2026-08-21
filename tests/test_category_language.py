"""Operator-facing prose uses Agent Command Post for Consilient, harness for children.

ADR-0061. Historical ADRs may still say meta-harness; README and AGENTS.md may not.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_agents_md_does_not_call_consilient_a_meta_harness():
    text = _read("AGENTS.md")
    assert "meta-harness" not in text.casefold()
    assert "agent command post" in text.casefold()


def test_readme_does_not_call_consilient_a_meta_harness():
    text = _read("README.md")
    opening = text.partition("## Install")[0]
    assert "agent command post" in opening.casefold()
    assert "open-source **meta-harness**" not in opening
    assert "open-source meta-harness" not in opening.casefold()
    # Stanford/MIT Meta-Harness may still be named as prior art later in the file.
