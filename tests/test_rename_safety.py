"""Tests for the Consilience -> Consilient rename safety classifier and sweep.

Enforces ADR-0038 rename invariants and prevents regression of past rename bugs:
  1. Quoted text and blockquotes are protected.
  2. Whewell's concept noun and lowercase 'consilience' are protected.
  3. Literal 'CONSILIENCE.md' filename and markdown links to it are protected.
  4. ACCEPTED and SUPERSEDED ADR bodies are protected (ADRs are superseded, not edited).
  5. Dated historical documents and transcripts are protected.
  6. The sweep is strictly idempotent (running it twice produces zero changes).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add .github/scripts to sys.path so we can import the classifier module
scripts_dir = str(Path(__file__).resolve().parent.parent / ".github" / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import check_rename_safety as crs  # noqa: E402


# ---------------------------------------------------------------- Fixture cases from the brief
def test_p3_echo_quoted_novelty_assessment_is_protected() -> None:
    """`docs/50-publications/P3-echo.md:748` exact string inside double quotes."""
    line = 'mutation testing at scale). Our own novelty assessment already says this — "Consilience is an orchestration front-end for mutation testing"'
    m = next(re.finditer(r"\bConsilience\b", line))
    cat, reason = crs.classify_token(
        "docs/50-publications/P3-echo.md",
        748,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "protected"
    assert "quote" in reason or "dated_or_historical" in reason or "published" in reason


def test_partially_renamed_line_classifies_first_token_renameable_and_is_idempotent(
    tmp_path: Path,
) -> None:
    """'Consilience does not become the only way to work on Consilient'."""
    line = "Consilience does not become the only way to work on Consilient\n"
    doc = tmp_path / "spec.md"
    doc.write_text(line, encoding="utf-8")

    # In a living document:
    m = next(re.finditer(r"\bConsilience\b", line))
    cat, reason = crs.classify_token(
        "docs/40-spec/v0-draft.md",
        1,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "renameable"

    # Create Occurrence object and apply sweep
    occ = crs.Occurrence(
        file="spec.md",
        line_number=1,
        start=m.start(),
        end=m.end(),
        word=m.group(0),
        classification="renameable",
        reason=reason,
        line_content=line,
    )
    first_renamed = crs.apply_rename_sweep(tmp_path, [occ])
    assert first_renamed == 1
    new_content = doc.read_text(encoding="utf-8")
    assert new_content == "Consilient does not become the only way to work on Consilient\n"

    # Scanning again should find 0 renameable occurrences (only already-renamed Consilient)
    second_occs = [
        o for o in crs.scan_repository(tmp_path) if o.classification == "renameable"
    ]
    assert len(second_occs) == 0
    second_renamed = crs.apply_rename_sweep(tmp_path, second_occs)
    assert second_renamed == 0
    assert doc.read_text(encoding="utf-8") == new_content


def test_accepted_adr_body_is_protected() -> None:
    """ACCEPTED ADR bodies must never be edited."""
    adr_content = """# 0015. Dogfooding gate
- **Status:** ACCEPTED
- **Date:** 2026-08-20

## Context
Consilience runs alongside, collecting trajectory data.
"""
    m = next(re.finditer(r"\bConsilience\b", adr_content))
    cat, reason = crs.classify_token(
        "docs/decisions/0015-dogfooding-gate.md",
        7,
        m.group(0),
        m.start(),
        m.end(),
        "Consilience runs alongside, collecting trajectory data.",
        adr_content,
    )
    assert cat == "protected"
    assert reason == "accepted_or_superseded_adr"


def test_superseded_adr_body_is_protected() -> None:
    """SUPERSEDED ADR bodies must never be edited."""
    adr_content = """# 0008. Name the project Consilience
- **Status:** SUPERSEDED by [0038](0038-rename-the-project-consilient.md)
- **Date:** 2026-08-19

## Context
Name the project Consilience.
"""
    m = next(re.finditer(r"\bConsilience\b", adr_content))
    cat, reason = crs.classify_token(
        "docs/decisions/0008-name-the-project-consilience.md",
        7,
        m.group(0),
        m.start(),
        m.end(),
        "Name the project Consilience.",
        adr_content,
    )
    assert cat == "protected"
    assert reason == "accepted_or_superseded_adr"


def test_consilience_md_filename_and_links_are_protected() -> None:
    """CONSILIENCE.md file and markdown links to it are protected."""
    line = "**Consilient** — read [`CONSILIENCE.md`](CONSILIENCE.md) first."
    m = next(re.finditer(r"\bCONSILIENCE\b", line))
    cat, reason = crs.classify_token(
        "AGENTS.md",
        7,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "protected"
    assert "consilience_md" in reason


def test_lowercase_consilience_is_protected() -> None:
    """Lowercase consilience as common noun/concept is protected."""
    line = "Two agents agreeing about the same evidence is not consilience. It is echo."
    m = next(re.finditer(r"\bconsilience\b", line))
    cat, reason = crs.classify_token(
        "CONSILIENCE.md",
        47,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "protected"
    assert reason == "lowercase_common_noun_concept"


def test_whewell_concept_phrases_in_prose_are_protected() -> None:
    """Semantic Whewell concept phrases in living prose are protected."""
    line = "## 7. Consilience check on each technique"
    m = next(re.finditer(r"\bConsilience\b", line))
    cat, reason = crs.classify_token(
        "docs/10-research/manufacturing-oracles.md",
        259,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "protected"
    assert reason == "whewell_epistemic_concept"


def test_dated_document_is_protected() -> None:
    """Historical dated documents (e.g. *-2026-08-20.md) are protected."""
    line = "Consilience has not yet established an unbiased sampling frame."
    m = next(re.finditer(r"\bConsilience\b", line))
    cat, reason = crs.classify_token(
        "docs/20-design/design-capability-assessment-2026-08-20.md",
        45,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "protected"
    assert reason == "dated_or_historical_document"


def test_provisional_adr_is_ambiguous() -> None:
    """PROVISIONAL ADRs are classified as ambiguous for human review."""
    adr_content = """# 0027. Compose domain harness provider and model
- **Status:** PROVISIONAL
- **Date:** 2026-08-20

## Context
Consilience is intended to be domain-blind.
"""
    m = next(re.finditer(r"\bConsilience\b", adr_content))
    cat, reason = crs.classify_token(
        "docs/decisions/0027-compose-domain-harness-provider-and-model.md",
        7,
        m.group(0),
        m.start(),
        m.end(),
        "Consilience is intended to be domain-blind.",
        adr_content,
    )
    assert cat == "ambiguous"
    assert reason == "provisional_or_proposed_adr_body"


def test_living_document_project_reference_is_renameable() -> None:
    """Living documentation referencing the project name is renameable."""
    line = "# Consilience — agent rules"
    m = next(re.finditer(r"\bConsilience\b", line))
    cat, reason = crs.classify_token(
        "AGENTS.md",
        1,
        m.group(0),
        m.start(),
        m.end(),
        line,
        line,
    )
    assert cat == "renameable"
    assert reason == "project_name_in_living_doc"
