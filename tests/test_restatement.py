"""Restatement lint for generated project facts."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_restatement.py"


def _install_checker(root: Path) -> Path:
    assert CHECKER.is_file(), "the restatement checker must exist"
    destination = root / ".github" / "scripts" / CHECKER.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CHECKER, destination)
    return destination


def _write_facts(root: Path) -> None:
    facts = root / "docs" / "project-facts.md"
    facts.parent.mkdir(parents=True, exist_ok=True)
    facts.write_text(
        "# Project facts\n\n"
        "## adr_count\n\n102\n\n"
        "## experiment_count\n\n113\n\n"
        "## spec_count\n\n21\n\n"
        "## version\n\n0.1.0\n",
        encoding="utf-8",
        newline="\n",
    )


def _run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    checker = _install_checker(root)
    return subprocess.run(
        [sys.executable, str(checker), "--check"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_a_handwritten_stale_count_fails_and_a_pointer_passes(tmp_path: Path) -> None:
    _write_facts(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Fixture\n\nThe repository contains 34 ADRs.\n",
        encoding="utf-8",
        newline="\n",
    )

    failed = _run_checker(tmp_path)

    assert failed.returncode == 1
    assert 'README.md:3 restates a generated fact "34 ADRs"' in failed.stdout

    readme.write_text(
        "# Fixture\n\nSee [project facts](docs/project-facts.md#adr_count).\n",
        encoding="utf-8",
        newline="\n",
    )

    passed = _run_checker(tmp_path)

    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "checked=1 adverse=0" in passed.stdout


def test_every_declared_fact_kind_is_refused_without_matching_identifiers(
    tmp_path: Path,
) -> None:
    _write_facts(tmp_path)
    (tmp_path / "README.md").write_text(
        "# Fixture\n\n"
        "There are 7 registered experiments and 8 specifications.\n"
        "Consilient version 9.8.7 is installed.\n"
        "ADR-0034 and EXP-21 are identifiers, not counts.\n",
        encoding="utf-8",
        newline="\n",
    )

    run = _run_checker(tmp_path)

    assert run.returncode == 1
    assert '"7 registered experiments"' in run.stdout
    assert '"8 specifications"' in run.stdout
    assert '"Consilient version 9.8.7"' in run.stdout
    assert "ADR-0034" not in run.stdout
    assert "EXP-21" not in run.stdout
    assert "adverse=3" in run.stdout


def test_registered_generated_regions_are_ignored_but_unclosed_regions_fail(
    tmp_path: Path,
) -> None:
    _write_facts(tmp_path)
    document = tmp_path / "docs" / "guide.md"
    document.write_text(
        "# Guide\n\n"
        "- **Document class:** W/g\n\n"
        "See [project facts](project-facts.md).\n\n"
        "<!-- BEGIN GENERATED: docs/project-facts.md -->\n"
        "The generated inventory contains 102 ADRs.\n"
        "<!-- END GENERATED: docs/project-facts.md -->\n",
        encoding="utf-8",
        newline="\n",
    )

    passed = _run_checker(tmp_path)

    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "checked=1 adverse=0" in passed.stdout

    document.write_text(
        document.read_text(encoding="utf-8").replace(
            "<!-- END GENERATED: docs/project-facts.md -->\n", ""
        ),
        encoding="utf-8",
        newline="\n",
    )

    failed = _run_checker(tmp_path)

    assert failed.returncode == 1
    assert "guide.md: unclosed generated region" in failed.stdout

    document.write_text(
        "# Guide\n\n"
        "- **Document class:** W/g\n\n"
        "<!-- BEGIN GENERATED: docs/not-project-facts.md -->\n"
        "The generated inventory contains 102 ADRs.\n"
        "<!-- END GENERATED: docs/not-project-facts.md -->\n",
        encoding="utf-8",
        newline="\n",
    )

    unregistered = _run_checker(tmp_path)

    assert unregistered.returncode == 1
    assert '"102 ADRs"' in unregistered.stdout


def test_missing_or_incomplete_fact_spine_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Fixture\n\nSee the generated project facts.\n",
        encoding="utf-8",
        newline="\n",
    )

    missing = _run_checker(tmp_path)

    assert missing.returncode == 1
    assert "FAIL docs/project-facts.md is missing" in missing.stderr
    assert "Traceback" not in missing.stderr

    facts = tmp_path / "docs" / "project-facts.md"
    facts.parent.mkdir(parents=True, exist_ok=True)
    facts.write_text("# Project facts\n\n## adr_count\n\n102\n", encoding="utf-8")

    incomplete = _run_checker(tmp_path)

    assert incomplete.returncode == 1
    assert "FAIL docs/project-facts.md is missing facts:" in incomplete.stderr
