"""Class-W living-document contract — ADR-0073 / L04."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_living_documents.py"
MANIFEST = ROOT / "docs" / "generated-manifest.json"

FIRST_TRANCHE = (
    "docs/superpowers/specs/2026-08-22-action-surface.md",
    "docs/superpowers/specs/2026-08-22-autonomy-and-friction.md",
    "docs/superpowers/specs/2026-08-22-chat-conversation.md",
    "docs/superpowers/specs/2026-08-22-chat-delivery.md",
    "docs/superpowers/specs/2026-08-22-consilience-gate.md",
    "docs/superpowers/specs/2026-08-22-decision-protocol.md",
    "docs/superpowers/specs/2026-08-22-evidence-fusion.md",
    "docs/superpowers/specs/2026-08-22-expertise-acquisition.md",
)

GENERATED_SENTENCE = (
    "The generated tally states thirty six requirements are currently unmet "
    "across every recorded status bucket."
)


def _install_checker(root: Path) -> Path:
    destination = root / ".github" / "scripts" / CHECKER.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CHECKER, destination)
    return destination


def _load_checker(root: Path):
    checker = _install_checker(root)
    spec = importlib.util.spec_from_file_location("check_living_documents", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_manifest(root: Path, *, output: str = "docs/40-spec/requirements.md") -> None:
    manifest = root / "docs" / "generated-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    generated = root / output
    generated.parent.mkdir(parents=True, exist_ok=True)
    if not generated.exists():
        generated.write_text(
            f"# Requirements\n\n{GENERATED_SENTENCE} [measured]\n",
            encoding="utf-8",
            newline="\n",
        )
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "output": output,
                        "producer": "scripts/build_requirements.py",
                        "check_args": ["--check"],
                        "sources": ["docs/40-spec/requirements-source.json"],
                        "header": {
                            "producer": "scripts/build_requirements.py",
                            "source": "docs/40-spec/requirements-source.json",
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _valid_body(*, extra: str = "") -> str:
    return (
        "# Fixture specification\n\n"
        "- **Document class:** W\n"
        "- **Review by:** 2026-09-22\n"
        "- **Falsifier:** EXP-99 kills this if generated documents drift undetected.\n\n"
        "**Class-W contract adopted 22 August 2026.** Mechanical admission only. "
        "[asserted]\n\n"
        "One Owner remains the default for reversible local work. [asserted]\n"
        f"{extra}"
    )


def _write_spec(root: Path, rel: str, body: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def _run_checker(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    checker = _install_checker(root)
    return subprocess.run(
        [sys.executable, str(checker), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_class_w_parser_requires_exactly_one_class_review_date_and_falsifier(
    tmp_path: Path,
) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"

    missing_class = _valid_body().replace("- **Document class:** W\n", "")
    _write_spec(tmp_path, rel, missing_class)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("Document class" in item.detail for item in result.findings)

    _write_spec(tmp_path, rel, _valid_body() + "\n- **Document class:** W\n")
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert any("exactly one" in item.detail.lower() for item in result.findings)

    missing_review = _valid_body().replace("- **Review by:** 2026-09-22\n", "")
    _write_spec(tmp_path, rel, missing_review)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert any("Review by" in item.detail for item in result.findings)

    empty_falsifier = _valid_body().replace(
        "- **Falsifier:** EXP-99 kills this if generated documents drift undetected.\n",
        "- **Falsifier:**   \n",
    )
    _write_spec(tmp_path, rel, empty_falsifier)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert any("falsifier" in item.detail.lower() for item in result.findings)

    heading_only = (
        "# Fixture\n\n"
        "- **Document class:** W\n"
        "- **Review by:** 2026-09-22\n\n"
        "## What would falsify this\n\n"
        "EXP-99 kills the generalisation if generated classes are no better. [asserted]\n\n"
        "One Owner remains the default for reversible local work. [asserted]\n"
    )
    _write_spec(tmp_path, rel, heading_only)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken == 0, [item.detail for item in result.findings]


def test_expired_and_impossible_review_dates_fail(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"

    _write_spec(tmp_path, rel, _valid_body().replace("2026-09-22", "2020-01-01"))
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.stale >= 1
    assert any("stale" in item.detail.lower() or "expired" in item.detail.lower() for item in result.findings)

    _write_spec(tmp_path, rel, _valid_body().replace("2026-09-22", "2026-02-31"))
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("impossible" in item.detail.lower() or "invalid" in item.detail.lower() for item in result.findings)


def test_untagged_claim_paragraph_fails(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"
    body = _valid_body(
        extra=(
            "\nThe composite verifier currently admits three candidates at every "
            "exposure ceiling below one half.\n"
        )
    )
    _write_spec(tmp_path, rel, body)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("untagged" in item.detail.lower() for item in result.findings)


def test_principal_quote_requires_adjacent_source_locator(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    source = tmp_path / "docs" / "00-context" / "the-machine-2026-08-22.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("line1\n" * 20, encoding="utf-8", newline="\n")
    rel = "docs/superpowers/specs/fixture.md"

    quoted = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "That quote is an architectural requirement. [asserted]\n"
        )
    )
    _write_spec(tmp_path, rel, quoted)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("locator" in item.detail.lower() or "source" in item.detail.lower() for item in result.findings)

    located = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "Source: docs/00-context/the-machine-2026-08-22.md:12\n\n"
            "That quote is an architectural requirement. [asserted]\n"
        )
    )
    _write_spec(tmp_path, rel, located)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken == 0, [item.detail for item in result.findings]


def test_bare_date_and_author_inference_are_not_provenance(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"

    dated = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "Source: 22 August 2026\n"
        )
    )
    _write_spec(tmp_path, rel, dated)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert any("date" in item.detail.lower() or "provenance" in item.detail.lower() for item in result.findings)

    inferred = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "Source: inferred from the author's intent on that date\n"
        )
    )
    _write_spec(tmp_path, rel, inferred)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert any("infer" in item.detail.lower() for item in result.findings)


def test_dead_local_locator_fails(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"
    body = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "Source: docs/00-context/does-not-exist.md:4\n"
        )
    )
    _write_spec(tmp_path, rel, body)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("dead" in item.detail.lower() or "missing" in item.detail.lower() for item in result.findings)


def test_literal_restatement_of_generated_surface_fails(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"
    body = _valid_body(extra=f"\n{GENERATED_SENTENCE} [asserted]\n")
    _write_spec(tmp_path, rel, body)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken >= 1
    assert any("restatement" in item.detail.lower() for item in result.findings)


def test_restatement_ok_directive_suppresses_matching_sentence(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"
    body = _valid_body(
        extra=(
            "\n<!-- living-doc: restatement-ok docs/40-spec/requirements.md#tally : "
            "quoting the generated tally as a pointer, not a second source -->\n"
            f"{GENERATED_SENTENCE} [asserted]\n"
        )
    )
    _write_spec(tmp_path, rel, body)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken == 0, [item.detail for item in result.findings]
    assert result.suppressed >= 1


def test_public_url_locator_is_unknown_not_broken(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    _write_manifest(tmp_path)
    rel = "docs/superpowers/specs/fixture.md"
    body = _valid_body(
        extra=(
            "\nThe principal, 22 August 2026, verbatim:\n\n"
            '> "Bake this into the specs."\n\n'
            "Source: https://example.com/transcript#L12\n\n"
            "That quote is an architectural requirement. [asserted]\n"
        )
    )
    _write_spec(tmp_path, rel, body)
    result = module.check_paths([tmp_path / rel], root=tmp_path)
    assert result.broken == 0, [item.detail for item in result.findings]
    assert result.unknown >= 1


def test_counts_include_zeros_and_check_flag_is_required(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_spec(tmp_path, "docs/superpowers/specs/fixture.md", _valid_body())
    run = _run_checker(tmp_path, "--check", "docs/superpowers/specs/fixture.md")
    assert run.returncode == 0, run.stdout + run.stderr
    for key in ("checked=", "stale=", "suppressed=", "broken=", "unknown="):
        assert key in run.stdout
    assert "checked=1" in run.stdout
    assert "stale=0" in run.stdout
    assert "broken=0" in run.stdout

    missing = _run_checker(tmp_path)
    assert missing.returncode == 2


def test_first_tranche_passes_and_outside_specs_are_not_admitted() -> None:
    assert CHECKER.is_file()
    run = subprocess.run(
        [sys.executable, str(CHECKER), "--check", *FIRST_TRANCHE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "checked=8" in run.stdout
    assert "stale=0" in run.stdout
    assert "broken=0" in run.stdout
    stdout = run.stdout.lower()
    for name in (
        "answer-quality",
        "living-documentation",
        "task-management",
        "triggered-recall",
    ):
        assert name not in stdout

    for rel in FIRST_TRANCHE:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert text.count("Document class: W") == 1
        assert "Review by:" in text
        assert "2026-09-22" in text
        assert "22 August 2026" in text
        assert "Falsifier:" in text or "falsif" in text.lower()

    specs_root = ROOT / "docs" / "superpowers" / "specs"
    outside = sorted(
        path.relative_to(ROOT).as_posix()
        for path in specs_root.glob("2026-08-22-*.md")
        if path.relative_to(ROOT).as_posix() not in FIRST_TRANCHE
    )
    assert outside, "L05's remaining files must exist and stay unadmitted"
    sample = ROOT / outside[0]
    text = sample.read_text(encoding="utf-8")
    assert "Document class: W" not in text
