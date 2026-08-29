"""Fixture builders shared by the generated-document test modules.

Each helper installs the checker or a producer into a throwaway root, writes a manifest
there, or reads a generated fact back out of rendered prose. They sit in a module pytest
does not collect because they are used from more than one of the three test modules:
`_run_checker` and `_write_manifest` by both the checker tests and the project-facts
tests, and `_fact_value` by the project-facts fixtures and by the live-tree test that
reads the committed `docs/project-facts.md`. `ROOT`, `CHECKER` and `MANIFEST` name the
real repository, so a fixture root can be seeded from it and the live-tree tests can
point at it directly."""

import re
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER = ROOT / ".github" / "scripts" / "check_generated_documents.py"

MANIFEST = ROOT / "docs" / "generated-manifest.json"


def _install_checker(root: Path) -> Path:
    destination = root / ".github" / "scripts" / CHECKER.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CHECKER, destination)
    return destination


def _install_script(root: Path, source: Path) -> Path:
    destination = root / "scripts" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _run_checker(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    checker = _install_checker(root)
    manifest = root / "docs" / "generated-manifest.json"
    if not manifest.exists() and MANIFEST.exists():
        manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MANIFEST, manifest)
    return subprocess.run(
        [sys.executable, str(checker), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _write_manifest(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "docs" / "generated-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "entries": entries}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _fact_value(text: str, key: str) -> str:
    match = re.search(rf"^## {re.escape(key)}\n+(.+)$", text, re.MULTILINE)
    assert match is not None, f"missing generated fact {key}"
    return match.group(1).strip()
