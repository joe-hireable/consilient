"""The generated-document checker's own mechanics, exercised against throwaway roots.

Two halves sit together because they are the same subject seen from either side of the
process boundary. What `validate_manifest` refuses about a manifest: a missing
`schema_version`, a duplicated output, a path that traverses out of the repository, a
shell metacharacter in `check_args`, a producer that is not repository-relative. And
what the checker does when it is actually run over one: execute the producers in
manifest order, report every failure with an adverse count rather than stopping at the
first, fail on an empty or malformed manifest, and exit 2 on CLI misuse rather than
pretending the run happened. The L01 header contract for `build_requirements.py` is
pinned here too — producer, source, source SHA-256, and the do-not-hand-edit line.

Nothing in this module touches the committed tree, and that is deliberate rather than
tidy: every test here can pass while a real generated document is drifted. The tests
that read the repository itself are in `test_generated_documents_live_tree.py`."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import pytest
from generated_documents_helpers import (
    ROOT,
    _install_checker,
    _install_script,
    _run_checker,
    _write_manifest,
)

BUILD_REQUIREMENTS = ROOT / "scripts" / "build_requirements.py"

BUILD_DECISION_INDEX = ROOT / "scripts" / "build_decision_index.py"


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
                        "header": {
                            "producer": "scripts/a.py",
                            "source": "docs/a-source.json",
                        },
                    },
                    {
                        "output": "docs/a.md",
                        "producer": "scripts/b.py",
                        "check_args": ["--check"],
                        "sources": ["docs/b-source.json"],
                        "header": {
                            "producer": "scripts/b.py",
                            "source": "docs/b-source.json",
                        },
                    },
                ],
            },
            root=tmp_path,
        )


def test_manifest_rejects_traversal_metacharacters_and_outside_producer(
    tmp_path: Path,
) -> None:
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
                        "header": {
                            "producer": "scripts/good.py",
                            "source": "docs/source.json",
                        },
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
                        "header": {
                            "producer": "scripts/good.py",
                            "source": "docs/source.json",
                        },
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
                        "header": {
                            "producer": "/bin/evil.py",
                            "source": "docs/source.json",
                        },
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
    requirements.write_text(
        requirements.read_text(encoding="utf-8") + "\nstale\n", encoding="utf-8"
    )
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
    rendered = (tmp_path / "docs" / "40-spec" / "requirements.md").read_text(
        encoding="utf-8"
    )
    digest = _source_digest(tmp_path, ["docs/40-spec/requirements-source.json"])
    assert "> **Producer:** `scripts/build_requirements.py`" in rendered
    assert "> **Source:** `docs/40-spec/requirements-source.json`" in rendered
    assert f"> **Source SHA-256:** `{digest}`" in rendered
    assert (
        "> **Do not hand-edit:** regenerate with `python scripts/build_requirements.py`."
        in rendered
    )


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
