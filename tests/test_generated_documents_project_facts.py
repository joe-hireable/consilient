"""`scripts/build_project_facts.py`, the producer that turns counts on disk into prose.

Its subject differs from the checker's. The checker asks whether a generated document
still matches its producer; these tests ask whether the producer is worth trusting in
the first place, because a drift check over an unreliable producer means nothing. So
they pin the properties it must have: the L01 header, carrying the producer, all four
source patterns, their SHA-256 and the do-not-hand-edit line; `--check` reporting
staleness without writing over the stale file; a second build coming out byte-identical
to the first; an unknown argument exiting 2; and an added ADR moving `adr_count` from 2
to 3, tripping `--check` until the producer is re-run. The last test closes the loop by
putting the project-facts entry through the manifest checker and requiring `checked=1
adverse=0`.

The project-facts digest is taken over newline-normalised bytes, which is why this
module carries its own `_normalized_source_digest` rather than the plain
`_source_digest` the requirements header test uses."""

import hashlib
import subprocess
import sys
from pathlib import Path
from generated_documents_helpers import (
    ROOT,
    _fact_value,
    _install_script,
    _run_checker,
    _write_manifest,
)

BUILD_PROJECT_FACTS = ROOT / "scripts" / "build_project_facts.py"

PROJECT_FACTS_SOURCES = [
    "docs/decisions/[0-9][0-9][0-9][0-9]-*.md",
    "docs/10-research/experiment-register.md",
    "docs/superpowers/specs/*.md",
    "pyproject.toml",
]

PROJECT_FACTS_SOURCE_HEADER = ", ".join(PROJECT_FACTS_SOURCES)


def _normalized_source_digest(root: Path, sources: list[str]) -> str:
    digest = hashlib.sha256()
    for pattern in sources:
        if any(char in pattern for char in "[]*?"):
            parent = root / Path(pattern).parent
            paths = sorted(parent.glob(Path(pattern).name))
        else:
            paths = [root / pattern]
        for path in paths:
            relative = path.relative_to(root).as_posix()
            file_digest = hashlib.sha256(
                path.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_digest.encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


def _write_facts_sources(
    root: Path,
    *,
    adrs: int = 2,
    experiments: int = 3,
    specs: int = 2,
    version: str = "0.1.0",
) -> None:
    decisions = root / "docs" / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    for index in range(1, adrs + 1):
        (decisions / f"{index:04d}-item.md").write_text(
            f"# {index:04d}. Item\n\n- **Status:** ACCEPTED\n",
            encoding="utf-8",
            newline="\n",
        )
    register = root / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True, exist_ok=True)
    headings = "\n\n".join(
        f"### EXP-{index:02d} · Thing `READY`" for index in range(1, experiments + 1)
    )
    register.write_text(
        "# Experiment register\n\n" + headings + "\n",
        encoding="utf-8",
        newline="\n",
    )
    spec_dir = root / "docs" / "superpowers" / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, specs + 1):
        (spec_dir / f"2026-08-22-spec-{index:02d}.md").write_text(
            f"# Spec {index}\n",
            encoding="utf-8",
            newline="\n",
        )
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "consilient"\nversion = "{version}"\n',
        encoding="utf-8",
        newline="\n",
    )


def _run_project_facts(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    script = _install_script(root, BUILD_PROJECT_FACTS)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_project_facts_header_matches_l01_contract_and_counts_match_disk(
    tmp_path: Path,
) -> None:
    _write_facts_sources(tmp_path, adrs=2, experiments=3, specs=2, version="0.1.0")

    run = _run_project_facts(tmp_path)

    assert run.returncode == 0, run.stderr
    rendered = (tmp_path / "docs" / "project-facts.md").read_text(encoding="utf-8")
    digest = _normalized_source_digest(tmp_path, PROJECT_FACTS_SOURCES)
    assert "> **Producer:** `scripts/build_project_facts.py`" in rendered
    assert f"> **Source:** `{PROJECT_FACTS_SOURCE_HEADER}`" in rendered
    assert f"> **Source SHA-256:** `{digest}`" in rendered
    assert (
        "> **Do not hand-edit:** regenerate with `python scripts/build_project_facts.py`."
        in rendered
    )
    assert _fact_value(rendered, "adr_count") == "2"
    assert _fact_value(rendered, "experiment_count") == "3"
    assert _fact_value(rendered, "spec_count") == "2"
    assert _fact_value(rendered, "version") == "0.1.0"


def test_project_facts_check_detects_stale_output_without_writing(
    tmp_path: Path,
) -> None:
    _write_facts_sources(tmp_path)
    assert _run_project_facts(tmp_path).returncode == 0
    target = tmp_path / "docs" / "project-facts.md"
    stale = b"stale generated facts\n"
    target.write_bytes(stale)

    run = _run_project_facts(tmp_path, "--check")

    assert run.returncode == 1
    assert target.read_bytes() == stale


def test_project_facts_second_build_is_byte_identical(tmp_path: Path) -> None:
    _write_facts_sources(tmp_path)
    first = _run_project_facts(tmp_path)
    first_bytes = (tmp_path / "docs" / "project-facts.md").read_bytes()
    checked = _run_project_facts(tmp_path, "--check")
    second = _run_project_facts(tmp_path)

    assert first.returncode == 0, first.stderr
    assert checked.returncode == 0, checked.stderr
    assert second.returncode == 0, second.stderr
    assert (tmp_path / "docs" / "project-facts.md").read_bytes() == first_bytes


def test_project_facts_unknown_argument_is_cli_misuse(tmp_path: Path) -> None:
    _write_facts_sources(tmp_path)

    run = _run_project_facts(tmp_path, "--unknown")

    assert run.returncode == 2


def test_project_facts_count_change_trips_check(tmp_path: Path) -> None:
    _write_facts_sources(tmp_path, adrs=2, experiments=3, specs=2)
    assert _run_project_facts(tmp_path).returncode == 0
    (tmp_path / "docs" / "decisions" / "0003-item.md").write_text(
        "# 0003. Item\n\n- **Status:** ACCEPTED\n",
        encoding="utf-8",
        newline="\n",
    )

    stale = _run_project_facts(tmp_path, "--check")
    rebuilt = _run_project_facts(tmp_path)

    assert stale.returncode == 1
    assert rebuilt.returncode == 0, rebuilt.stderr
    rendered = (tmp_path / "docs" / "project-facts.md").read_text(encoding="utf-8")
    assert _fact_value(rendered, "adr_count") == "3"


def test_checker_verifies_project_facts_entry(tmp_path: Path) -> None:
    _write_facts_sources(tmp_path)
    assert _run_project_facts(tmp_path).returncode == 0
    _write_manifest(
        tmp_path,
        [
            {
                "output": "docs/project-facts.md",
                "producer": "scripts/build_project_facts.py",
                "check_args": ["--check"],
                "sources": PROJECT_FACTS_SOURCES,
                "header": {
                    "producer": "scripts/build_project_facts.py",
                    "source": PROJECT_FACTS_SOURCE_HEADER,
                },
            }
        ],
    )

    run = _run_checker(tmp_path, "--check")

    assert run.returncode == 0, run.stdout + run.stderr
    assert "docs/project-facts.md" in run.stdout
    assert "checked=1" in run.stdout
    assert "adverse=0" in run.stdout
