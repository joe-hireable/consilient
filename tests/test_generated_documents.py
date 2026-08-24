"""Regression tests for the generated-document manifest runner."""

from __future__ import annotations

import pathlib

import re

import os

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_generated_documents.py"
MANIFEST = ROOT / "docs" / "generated-manifest.json"
BUILD_REQUIREMENTS = ROOT / "scripts" / "build_requirements.py"
BUILD_DECISION_INDEX = ROOT / "scripts" / "build_decision_index.py"
BUILD_PROJECT_FACTS = ROOT / "scripts" / "build_project_facts.py"
PROJECT_FACTS_SOURCES = [
    "docs/decisions/[0-9][0-9][0-9][0-9]-*.md",
    "docs/10-research/experiment-register.md",
    "docs/superpowers/specs/*.md",
    "pyproject.toml",
]
PROJECT_FACTS_SOURCE_HEADER = ", ".join(PROJECT_FACTS_SOURCES)
EXP_HEADING = re.compile(r"^#{2,4}\s*EXP-\d+", re.MULTILINE)


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


def _load_checker(root: Path):
    checker = _install_checker(root)
    spec = importlib.util.spec_from_file_location("check_generated_documents", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source_digest(root: Path, sources: list[str]) -> str:
    digest = hashlib.sha256()
    for pattern in sources:
        if any(char in pattern for char in "[]*?"):
            parent = root / Path(pattern).parent
            glob = Path(pattern).name
            paths = sorted(parent.glob(glob))
        else:
            paths = [root / pattern]
        for path in paths:
            relative = path.relative_to(root).as_posix()
            file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_digest.encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


def _write_manifest(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "docs" / "generated-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "entries": entries}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_requirements_fixture(root: Path) -> None:
    source = root / "docs" / "40-spec" / "requirements-source.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        json.dumps(
            [
                {
                    "id": "R1",
                    "area": "governance",
                    "quote": "Ship the check with the claim.",
                    "requirement": "Every invariant has a test.",
                    "status": "partial",
                    "gap": "not everywhere yet",
                    "effort": "small",
                    "blocks": False,
                    "repeated": False,
                    "evidence": "",
                }
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    _install_script(root, BUILD_REQUIREMENTS)
    subprocess.run(
        [sys.executable, str(root / "scripts" / BUILD_REQUIREMENTS.name)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


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


def _fact_value(text: str, key: str) -> str:
    match = re.search(rf"^## {re.escape(key)}\n+(.+)$", text, re.MULTILINE)
    assert match is not None, f"missing generated fact {key}"
    return match.group(1).strip()


def _write_adr_fixture(root: Path) -> None:
    decisions = root / "docs" / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    (decisions / "0001-alpha.md").write_text(
        "# 0001. Alpha\n\n- **Status:** ACCEPTED\n",
        encoding="utf-8",
        newline="\n",
    )
    _install_script(root, BUILD_DECISION_INDEX)
    subprocess.run(
        [sys.executable, str(root / "scripts" / BUILD_DECISION_INDEX.name)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_manifest_schema_requires_ordered_entry_fields(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    for name in ("a.py", "b.py"):
        script = tmp_path / "scripts" / name
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        module.validate_manifest({"entries": []}, root=tmp_path)
    with pytest.raises(ValueError, match="duplicate output"):
        module.validate_manifest(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "output": "docs/a.md",
                        "producer": "scripts/a.py",
                        "check_args": ["--check"],
                        "sources": ["docs/a-source.json"],
                        "header": {"producer": "scripts/a.py", "source": "docs/a-source.json"},
                    },
                    {
                        "output": "docs/a.md",
                        "producer": "scripts/b.py",
                        "check_args": ["--check"],
                        "sources": ["docs/b-source.json"],
                        "header": {"producer": "scripts/b.py", "source": "docs/b-source.json"},
                    },
                ],
            },
            root=tmp_path,
        )


def test_manifest_rejects_traversal_metacharacters_and_outside_producer(tmp_path: Path) -> None:
    module = _load_checker(tmp_path)
    producer = tmp_path / "scripts" / "good.py"
    producer.parent.mkdir(parents=True)
    producer.write_text("print('ok')\n", encoding="utf-8")
    with pytest.raises(ValueError, match="traversal"):
        module.validate_manifest(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "output": "../outside.md",
                        "producer": "scripts/good.py",
                        "check_args": ["--check"],
                        "sources": ["docs/source.json"],
                        "header": {"producer": "scripts/good.py", "source": "docs/source.json"},
                    }
                ],
            },
            root=tmp_path,
        )
    with pytest.raises(ValueError, match="metacharacter"):
        module.validate_manifest(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "output": "docs/a.md",
                        "producer": "scripts/good.py",
                        "check_args": ["--check", ";rm"],
                        "sources": ["docs/source.json"],
                        "header": {"producer": "scripts/good.py", "source": "docs/source.json"},
                    }
                ],
            },
            root=tmp_path,
        )
    with pytest.raises(ValueError, match="repository-relative|outside repository"):
        module.validate_manifest(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "output": "docs/a.md",
                        "producer": "/bin/evil.py",
                        "check_args": ["--check"],
                        "sources": ["docs/source.json"],
                        "header": {"producer": "/bin/evil.py", "source": "docs/source.json"},
                    }
                ],
            },
            root=tmp_path,
        )


def test_checker_runs_both_producers_in_manifest_order(tmp_path: Path) -> None:
    _write_requirements_fixture(tmp_path)
    _write_adr_fixture(tmp_path)
    _write_manifest(
        tmp_path,
        [
            {
                "output": "docs/40-spec/requirements.md",
                "producer": "scripts/build_requirements.py",
                "check_args": ["--check"],
                "sources": ["docs/40-spec/requirements-source.json"],
                "header": {
                    "producer": "scripts/build_requirements.py",
                    "source": "docs/40-spec/requirements-source.json",
                },
            },
            {
                "output": "docs/decisions/index.md",
                "producer": "scripts/build_decision_index.py",
                "check_args": ["--check"],
                "sources": ["docs/decisions/[0-9][0-9][0-9][0-9]-*.md"],
                "header": {
                    "producer": "scripts/build_decision_index.py",
                    "source": "docs/decisions/[0-9][0-9][0-9][0-9]-*.md",
                },
            },
        ],
    )

    run = _run_checker(tmp_path, "--check")

    assert run.returncode == 0, run.stdout + run.stderr
    assert "checked=2" in run.stdout
    assert run.stdout.index("requirements.md") < run.stdout.index("index.md")


def test_checker_reports_every_failure_and_adverse_count(tmp_path: Path) -> None:
    _write_requirements_fixture(tmp_path)
    _write_adr_fixture(tmp_path)
    requirements = tmp_path / "docs" / "40-spec" / "requirements.md"
    requirements.write_text(requirements.read_text(encoding="utf-8") + "\nstale\n", encoding="utf-8")
    _write_manifest(
        tmp_path,
        [
            {
                "output": "docs/40-spec/requirements.md",
                "producer": "scripts/build_requirements.py",
                "check_args": ["--check"],
                "sources": ["docs/40-spec/requirements-source.json"],
                "header": {
                    "producer": "scripts/build_requirements.py",
                    "source": "docs/40-spec/requirements-source.json",
                },
            },
            {
                "output": "docs/decisions/index.md",
                "producer": "scripts/build_decision_index.py",
                "check_args": ["--check"],
                "sources": ["docs/decisions/[0-9][0-9][0-9][0-9]-*.md"],
                "header": {
                    "producer": "scripts/build_decision_index.py",
                    "source": "docs/decisions/[0-9][0-9][0-9][0-9]-*.md",
                },
            },
        ],
    )

    run = _run_checker(tmp_path, "--check")

    assert run.returncode == 1
    assert "adverse=1" in run.stdout or "adverse=2" in run.stdout
    assert "requirements.md" in run.stdout


def test_empty_or_malformed_manifest_fails(tmp_path: Path) -> None:
    manifest = tmp_path / "docs" / "generated-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}\n", encoding="utf-8")
    _install_checker(tmp_path)

    run = _run_checker(tmp_path, "--check")

    assert run.returncode == 1
    assert "adverse=" in run.stdout


def test_requirements_header_matches_l01_contract(tmp_path: Path) -> None:
    _write_requirements_fixture(tmp_path)
    rendered = (tmp_path / "docs" / "40-spec" / "requirements.md").read_text(encoding="utf-8")
    digest = _source_digest(tmp_path, ["docs/40-spec/requirements-source.json"])
    assert "> **Producer:** `scripts/build_requirements.py`" in rendered
    assert "> **Source:** `docs/40-spec/requirements-source.json`" in rendered
    assert f"> **Source SHA-256:** `{digest}`" in rendered
    assert "> **Do not hand-edit:** regenerate with `python scripts/build_requirements.py`." in rendered


def test_repository_manifest_matches_committed_generated_documents() -> None:
    if not MANIFEST.is_file():
        pytest.skip("manifest not built yet")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    outputs = [entry["output"] for entry in manifest["entries"]]
    assert outputs == [
        "docs/40-spec/requirements.md",
        "docs/decisions/index.md",
        "docs/project-facts.md",
    ]


def test_unknown_argument_is_cli_misuse(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        [
            {
                "output": "docs/40-spec/requirements.md",
                "producer": "scripts/build_requirements.py",
                "check_args": ["--check"],
                "sources": ["docs/40-spec/requirements-source.json"],
                "header": {
                    "producer": "scripts/build_requirements.py",
                    "source": "docs/40-spec/requirements-source.json",
                },
            }
        ],
    )
    _install_checker(tmp_path)

    run = _run_checker(tmp_path, "--unknown")

    assert run.returncode == 2

def test_the_committed_generated_documents_are_not_currently_drifted():
    """The live tree, not the checker's mechanics.

    Every other test in this file exercises the checker against fixtures, and all eight passed on
    23 August 2026 while BOTH real generated documents were drifted -- `docs/decisions/index.md`
    and `docs/40-spec/requirements.md`. The checker itself said so, exiting 1 with
    `checked=2 adverse=2`, and nothing consumed that exit code: it was wired into no workflow and
    no test. A check whose result nobody reads is a report. [measured]
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    script = root / ".github" / "scripts" / "check_generated_documents.py"
    assert script.is_file(), "the generated-document checker must exist"
    run = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert run.returncode == 0, (
        "a generated document has drifted from its producer. Re-run the producer and commit the "
        f"result; do not edit the generated file by hand. {run.stdout} {run.stderr}"
    )


def test_the_readme_counts_match_what_is_on_disk():
    """Restated numbers drift, and these drifted by a factor of three.

    On 23 August 2026 README.md claimed 34 ADRs and 35 registered experiments while the tree held
    95 and 109. [measured] The counts sit in the public shop window of a project whose subject is
    measurement honesty, which makes a stale count the same class of defect as an uncited
    superlative -- and that one already has a check.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace")
    adrs = len(list((root / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")))
    register = (root / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8", errors="replace"
    )
    exps = len(re.findall(r"^#{2,4}\s*EXP-\d+", register, re.M))
    for claimed, actual, what in (
        (re.search(r"(\d+) ADRs", readme), adrs, "ADRs"),
        (re.search(r"(\d+) registered experiments", readme), exps, "registered experiments"),
    ):
        assert claimed, f"README no longer states a count of {what}; update this check with it"
        assert int(claimed.group(1)) == actual, (
            f"README claims {claimed.group(1)} {what}; the tree holds {actual}. "
            "Correct the README — a number in public prose is a claim like any other."
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


def test_project_facts_check_detects_stale_output_without_writing(tmp_path: Path) -> None:
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


def test_live_project_facts_counts_match_disk() -> None:
    facts = ROOT / "docs" / "project-facts.md"
    assert facts.is_file(), "docs/project-facts.md must be generated"
    text = facts.read_text(encoding="utf-8")
    adrs = len(list((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")))
    register = (ROOT / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8"
    )
    experiments = len(EXP_HEADING.findall(register))
    specs = len(list((ROOT / "docs" / "superpowers" / "specs").glob("*.md")))
    version = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert version is not None
    assert _fact_value(text, "adr_count") == str(adrs)
    assert _fact_value(text, "experiment_count") == str(experiments)
    assert _fact_value(text, "spec_count") == str(specs)
    assert _fact_value(text, "version") == version.group(1)
    run = subprocess.run(
        [sys.executable, str(CHECKER), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "docs/project-facts.md" in run.stdout
    assert "checked=3" in run.stdout
    assert "adverse=0" in run.stdout
