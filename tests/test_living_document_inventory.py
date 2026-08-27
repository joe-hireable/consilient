"""Exact twenty-one-file Class-W inventory — ADR-0073 / L05."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "docs" / "superpowers" / "specs"
CHECKER = ROOT / ".github" / "scripts" / "check_living_documents.py"

L04 = (
    "docs/superpowers/specs/2026-08-22-action-surface.md",
    "docs/superpowers/specs/2026-08-22-autonomy-and-friction.md",
    "docs/superpowers/specs/2026-08-22-chat-conversation.md",
    "docs/superpowers/specs/2026-08-22-chat-delivery.md",
    "docs/superpowers/specs/2026-08-22-consilience-gate.md",
    "docs/superpowers/specs/2026-08-22-decision-protocol.md",
    "docs/superpowers/specs/2026-08-22-evidence-fusion.md",
    "docs/superpowers/specs/2026-08-22-expertise-acquisition.md",
)

L05 = (
    "docs/superpowers/specs/2026-08-22-answer-quality.md",
    "docs/superpowers/specs/2026-08-22-autonomous-qa.md",
    "docs/superpowers/specs/2026-08-22-dependency-scheduling.md",
    "docs/superpowers/specs/2026-08-22-living-documentation.md",
    "docs/superpowers/specs/2026-08-22-memory-and-capability.md",
    "docs/superpowers/specs/2026-08-22-model-lifecycle.md",
    "docs/superpowers/specs/2026-08-22-observability-and-steering.md",
    "docs/superpowers/specs/2026-08-22-one-surface.md",
    "docs/superpowers/specs/2026-08-22-portable-capability.md",
    "docs/superpowers/specs/2026-08-22-self-improvement.md",
    "docs/superpowers/specs/2026-08-22-squad-roles.md",
    "docs/superpowers/specs/2026-08-22-task-management.md",
    "docs/superpowers/specs/2026-08-22-verdict-supply.md",
)

ADMITTED = tuple(sorted((*L04, *L05)))
REVIEW_BY = re.compile(r"Review by:\s*\**\s*`?(\d{4}-\d{2}-\d{2})`?", re.IGNORECASE)
FALSIFIER_FIELD = re.compile(r"Falsifier:\s*(.+)$", re.IGNORECASE)
FALSIFIER_HEADING = re.compile(r"^#{1,6}\s+.*falsif", re.IGNORECASE)
CONTRACT_REVIEW = date(2026, 9, 22)


def _glob_admitted(specs_root: Path) -> list[str]:
    return sorted(path.name for path in specs_root.glob("2026-08-22-*.md"))


def _expected_names() -> list[str]:
    return [Path(rel).name for rel in ADMITTED]


def _has_falsifier(text: str) -> bool:
    for line in text.splitlines():
        match = FALSIFIER_FIELD.search(line)
        if match and re.sub(r"[*`\s]", "", match.group(1)):
            return True
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not FALSIFIER_HEADING.search(line):
            continue
        remainder = "\n".join(lines[index + 1 :])
        next_heading = re.search(r"^#{1,6}\s+", remainder, re.MULTILINE)
        body = remainder[: next_heading.start()] if next_heading else remainder
        if body.strip():
            return True
    return False


def _name_errors(names: list[str]) -> list[str]:
    errors: list[str] = []
    expected = _expected_names()
    missing = sorted(set(expected) - set(names))
    extra = sorted(set(names) - set(expected))
    if missing:
        errors.append(f"missing admitted specification: {missing}")
    if extra:
        errors.append(f"unlisted specification: {extra}")
    lowered = [name.lower() for name in names]
    if len(lowered) != len(set(lowered)):
        errors.append("duplicate or case-alias specification name")
    if names != expected and not missing and not extra:
        errors.append("inventory order or exact-name mismatch")
    return errors


def _inventory_errors(specs_root: Path) -> list[str]:
    errors = _name_errors(_glob_admitted(specs_root))
    names = _glob_admitted(specs_root)
    expected = _expected_names()
    for name in names:
        if name not in expected:
            continue
        text = (specs_root / name).read_text(encoding="utf-8")
        class_hits = re.findall(r"Document class:\s*\**\s*W\b", text)
        if len(class_hits) != 1:
            errors.append(f"{name}: expected exactly one Document class: W")
        match = REVIEW_BY.search(text)
        if match is None:
            errors.append(f"{name}: missing Review by ISO date")
        else:
            review = date.fromisoformat(match.group(1))
            if review > CONTRACT_REVIEW:
                errors.append(f"{name}: review date {review.isoformat()} extends past {CONTRACT_REVIEW.isoformat()}")
        if not _has_falsifier(text):
            errors.append(f"{name}: missing or empty falsifier")
    return errors


def _copy_specs(tmp_path: Path) -> Path:
    destination = tmp_path / "specs"
    shutil.copytree(SPECS, destination)
    return destination


def test_explicit_inventory_is_exactly_twenty_one_unique_paths() -> None:
    assert len(ADMITTED) == 21
    assert len(set(ADMITTED)) == 21
    lowered = [rel.lower() for rel in ADMITTED]
    assert len(lowered) == len(set(lowered))
    assert set(L04).isdisjoint(L05)
    assert len(L04) == 8
    assert len(L05) == 13


def test_glob_and_explicit_inventory_are_identical() -> None:
    globbed = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(SPECS.glob("2026-08-22-*.md"))
    ]
    assert globbed == list(ADMITTED)


def test_later_dated_specifications_stay_outside_this_inventory() -> None:
    later = sorted(path.name for path in SPECS.glob("2026-08-2[3-9]-*.md"))
    expected = set(_expected_names())
    overlap = sorted(set(later) & expected)
    assert overlap == []
    assert all(not name.startswith("2026-08-22-") for name in later)


def test_working_tree_inventory_is_class_w() -> None:
    errors = _inventory_errors(SPECS)
    assert errors == [], errors


def test_every_claimed_specification_has_the_review_by_contract() -> None:
    for rel in L05:
        text = (ROOT / rel).read_text(encoding="utf-8")
        match = REVIEW_BY.search(text)
        assert match is not None, rel
        review = date.fromisoformat(match.group(1))
        assert review <= CONTRACT_REVIEW, rel
        assert "Class-W contract adopted 22 August 2026" in text


def test_missing_file_fails_on_copied_specs_root(tmp_path: Path) -> None:
    copied = _copy_specs(tmp_path)
    (copied / Path(L05[0]).name).unlink()
    errors = _inventory_errors(copied)
    assert any("missing" in item for item in errors), errors


def test_unlisted_file_fails_on_copied_specs_root(tmp_path: Path) -> None:
    copied = _copy_specs(tmp_path)
    extra = copied / "2026-08-22-unlisted-fixture.md"
    extra.write_text(
        "# Unlisted fixture\n\n- **Document class: W**\n- **Review by:** 2026-09-22\n"
        "- **Falsifier:** temporary inventory fixture.\n",
        encoding="utf-8",
        newline="\n",
    )
    errors = _inventory_errors(copied)
    assert any("unlisted" in item for item in errors), errors
    assert extra.is_file()
    assert not (SPECS / extra.name).exists()


def test_case_alias_or_duplicate_name_fails() -> None:
    # /mnt/c is case-insensitive, so a second casing cannot be written beside
    # the real file. The name-list check still has to reject a case alias or
    # a duplicated basename. [measured]
    alias_errors = _name_errors([*_expected_names(), "2026-08-22-Answer-Quality.md"])
    assert any("unlisted" in item or "case-alias" in item for item in alias_errors), alias_errors
    duplicate_errors = _name_errors([*_expected_names(), Path(L05[0]).name])
    assert any("case-alias" in item or "duplicate" in item for item in duplicate_errors), duplicate_errors


def test_non_w_class_fails_on_copied_specs_root(tmp_path: Path) -> None:
    copied = _copy_specs(tmp_path)
    target = copied / Path(L05[0]).name
    text = target.read_text(encoding="utf-8").replace("Document class: W", "Document class: G", 1)
    target.write_text(text, encoding="utf-8")
    errors = _inventory_errors(copied)
    assert any("Document class: W" in item for item in errors), errors


def test_missing_falsifier_fails_on_copied_specs_root(tmp_path: Path) -> None:
    copied = _copy_specs(tmp_path)
    target = copied / Path(L05[0]).name
    stripped = [
        line
        for line in target.read_text(encoding="utf-8").splitlines()
        if "falsif" not in line.lower()
    ]
    target.write_text("\n".join(stripped) + "\n", encoding="utf-8", newline="\n")
    errors = _inventory_errors(copied)
    assert any("falsifier" in item.lower() for item in errors), errors


def test_l04_checker_admits_all_twenty_one_paths() -> None:
    run = subprocess.run(
        [sys.executable, str(CHECKER), "--check", *ADMITTED],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "checked=21" in run.stdout
    assert "stale=0" in run.stdout
    assert "broken=0" in run.stdout
