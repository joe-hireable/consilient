"""Generate `docs/project-facts.md` from inventory sources on disk.

The document is generated, never hand-edited, so restatable counts have one home.
Hand-copied ADR and experiment tallies in this repository have already drifted
by a factor of three (README 34 / CLAUDE.md 45 / disk 102, measured 23 August
2026). Generation owns freshness; `consil doctor` and `consil beta` remain the
authorities for gate state and β, which are not inventory counts.

    python scripts/build_project_facts.py            # rewrite the document
    python scripts/build_project_facts.py --check     # fail if it has drifted
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "docs" / "project-facts.md"
SOURCES = (
    "docs/decisions/[0-9][0-9][0-9][0-9]-*.md",
    "docs/10-research/experiment-register.md",
    "docs/superpowers/specs/*.md",
    "pyproject.toml",
)
SOURCE_HEADER = ", ".join(SOURCES)
ADR_GLOB = "[0-9][0-9][0-9][0-9]-*.md"
EXP_HEADING = re.compile(r"^#{2,4}\s*EXP-\d+", re.MULTILINE)
FACT_KEYS = ("adr_count", "experiment_count", "spec_count", "version")


def source_digest() -> str:
    digest = hashlib.sha256()
    for pattern in SOURCES:
        path = Path(pattern)
        if any(char in pattern for char in "[]*?"):
            parent = ROOT / path.parent
            paths = sorted(parent.glob(path.name))
        else:
            paths = [ROOT / pattern]
        if not paths:
            raise ValueError(f"source pattern matched no files: {pattern}")
        for resolved in paths:
            if not resolved.is_file():
                raise FileNotFoundError(resolved)
            relative = resolved.relative_to(ROOT).as_posix()
            file_digest = hashlib.sha256(
                resolved.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_digest.encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


def collect_facts() -> dict[str, str]:
    adrs = sorted((ROOT / "docs" / "decisions").glob(ADR_GLOB))
    register = ROOT / "docs" / "10-research" / "experiment-register.md"
    experiments = EXP_HEADING.findall(
        register.read_text(encoding="utf-8").replace("\r\n", "\n")
    )
    specs = sorted((ROOT / "docs" / "superpowers" / "specs").glob("*.md"))
    with (ROOT / "pyproject.toml").open("rb") as handle:
        payload = tomllib.load(handle)
    project = payload.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml is missing [project]")
    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml is missing project.version")
    return {
        "adr_count": str(len(adrs)),
        "experiment_count": str(len(experiments)),
        "spec_count": str(len(specs)),
        "version": version.strip(),
    }


def render(facts: dict[str, str], digest: str) -> bytes:
    lines = [
        "# Project facts",
        "",
        "> **Producer:** `scripts/build_project_facts.py`",
        f"> **Source:** `{SOURCE_HEADER}`",
        f"> **Source SHA-256:** `{digest}`",
        "> **Do not hand-edit:** regenerate with `python scripts/build_project_facts.py`.",
        "",
    ]
    for key in FACT_KEYS:
        lines.extend([f"## {key}", "", facts[key], ""])
    return "\n".join(lines).encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the document has drifted"
    )
    args = parser.parse_args(argv)
    try:
        rendered = render(collect_facts(), source_digest())
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if args.check:
        current = TARGET.read_bytes() if TARGET.exists() else b""
        if current != rendered:
            print(
                "FAIL docs/project-facts.md has drifted; "
                "run python scripts/build_project_facts.py"
            )
            return 1
        print("docs/project-facts.md is current")
        return 0
    write_atomic(TARGET, rendered)
    print(f"wrote docs/project-facts.md ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
