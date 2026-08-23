"""Regression tests for the generated ADR index."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_decision_index.py"


def _write_adr(root: Path, name: str, title: str | None, metadata: str) -> None:
    path = root / "docs" / "decisions" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    heading = f"# {name[:4]}. {title}\n\n" if title is not None else ""
    path.write_text(heading + metadata + "\n", encoding="utf-8", newline="\n")


def _install_script(root: Path) -> Path:
    destination = root / "scripts" / SCRIPT.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, destination)
    return destination


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    script = _install_script(root)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")):
        relative = path.relative_to(root).as_posix()
        file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _load(root: Path):
    script = _install_script(root)
    spec = importlib.util.spec_from_file_location("build_decision_index", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generates_ordered_escaped_source_derived_rows(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0002-beta.md",
        r"Beta | *special* \\ title",
        "- **Status:** PROVISIONAL | trial *maybe*",
    )
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", "- **Status:** ACCEPTED")

    run = _run(tmp_path)

    assert run.returncode == 0, run.stderr
    rendered = (tmp_path / "docs" / "decisions" / "index.md").read_text(encoding="utf-8")
    assert "**Producer:** `scripts/build_decision_index.py`" in rendered
    assert "**Source:** `docs/decisions/[0-9][0-9][0-9][0-9]-*.md`" in rendered
    assert f"**Source SHA-256:** `{_source_digest(tmp_path)}`" in rendered
    assert "**Do not hand-edit:** regenerate with `python scripts/build_decision_index.py`." in rendered
    assert rendered.index("[0001](0001-alpha.md)") < rendered.index("[0002](0002-beta.md)")
    assert r"Beta \| \*special\* \\\\ title" in rendered
    row = next(line for line in rendered.splitlines() if "[0002](0002-beta.md)" in line)
    assert row.endswith("| PROVISIONAL | — |")


def test_check_detects_stale_index_without_writing(tmp_path: Path) -> None:
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", "- **Status:** ACCEPTED")
    assert _run(tmp_path).returncode == 0
    index = tmp_path / "docs" / "decisions" / "index.md"
    index.write_bytes(b"stale generated index\n")

    run = _run(tmp_path, "--check")

    assert run.returncode == 1
    assert index.read_bytes() == b"stale generated index\n"


def test_duplicate_number_refuses_before_replacing_index(tmp_path: Path) -> None:
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", "- **Status:** ACCEPTED")
    _write_adr(tmp_path, "0001-second.md", "Second", "- **Status:** ACCEPTED")
    index = tmp_path / "docs" / "decisions" / "index.md"
    index.write_bytes(b"existing\n")

    run = _run(tmp_path)

    assert run.returncode == 1
    assert "duplicate ADR number 0001" in run.stderr
    assert index.read_bytes() == b"existing\n"


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ("", "missing Status metadata"),
        ("- **Status:** UNKNOWN", "unrecognised status"),
        ("- **Status:** ACCEPTEDLY", "unrecognised status"),
        ("- **Status:** ACCEPTED-ISH", "unrecognised status"),
        ("- **Status:** ACCEPTED/REJECTED", "unrecognised status"),
        ("- **Status:** PRO_POSED", "unrecognised status"),
    ],
)
def test_refuses_missing_or_invalid_status(tmp_path: Path, metadata: str, expected: str) -> None:
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", metadata)

    run = _run(tmp_path)

    assert run.returncode == 1
    assert expected in run.stderr


def test_refuses_noncomposite_cut_retained_status(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0020-meetings.md",
        "Meetings",
        "- **Status:** CUT anything RETAINED",
    )

    run = _run(tmp_path)

    assert run.returncode == 1
    assert "unrecognised status" in run.stderr


def test_refuses_whitespace_only_title(tmp_path: Path) -> None:
    _write_adr(tmp_path, "0001-alpha.md", " ", "- **Status:** ACCEPTED")

    run = _run(tmp_path)

    assert run.returncode == 1
    assert "missing title metadata" in run.stderr


def test_refuses_body_status_and_nonleading_title(tmp_path: Path) -> None:
    path = tmp_path / "docs" / "decisions" / "0001-alpha.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "Preamble\n\n# 0001. Alpha\n\n## Context\n\n- **Status:** ACCEPTED\n",
        encoding="utf-8",
        newline="\n",
    )

    run = _run(tmp_path)

    assert run.returncode == 1
    assert "missing title metadata" in run.stderr


def test_renders_canonical_status_and_explicit_relations_only(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0002-replacement.md",
        "Replacement",
        "\n".join(
            [
                "- **Status:** **SUPERSEDED IN PART by ADR-0003** on 2026",
                "- **Supersedes in part:** the boundary in [0001](0001-old.md), not [0004](0004-context.md)",
                "- **Date:** 2026-08-23",
                "\n## Context\n\n- **Status:** ACCEPTED",
            ]
        ),
    )

    run = _run(tmp_path)

    assert run.returncode == 0, run.stderr
    rendered = (tmp_path / "docs" / "decisions" / "index.md").read_text(encoding="utf-8")
    assert "| [0002](0002-replacement.md) | Replacement | SUPERSEDED | superseded by 0003; supersedes 0001 |" in rendered
    assert "0004" not in rendered


def test_preserves_bare_supersedes_target_without_link_inference(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0002-replacement.md",
        "Replacement",
        "\n".join(
            [
                "- **Status:** ACCEPTED — see [0008](0008-context.md)",
                "- **Supersedes:** ADR-0005; [0006](0006-context.md) is background",
            ]
        ),
    )

    run = _run(tmp_path)

    assert run.returncode == 0, run.stderr
    rendered = (tmp_path / "docs" / "decisions" / "index.md").read_text(encoding="utf-8")
    assert "| [0002](0002-replacement.md) | Replacement | ACCEPTED | supersedes 0005 |" in rendered
    assert "0006" not in rendered


def test_failed_replace_preserves_existing_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", "- **Status:** ACCEPTED")
    index = tmp_path / "docs" / "decisions" / "index.md"
    index.write_bytes(b"old index\n")
    module = _load(tmp_path)

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        module.write_atomic(index, b"new index\n")
    assert index.read_bytes() == b"old index\n"


def test_current_adr_set_renders_and_second_build_is_identical(tmp_path: Path) -> None:
    decisions = tmp_path / "docs" / "decisions"
    decisions.mkdir(parents=True)
    for source in sorted((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")):
        shutil.copy2(source, decisions / source.name)

    first = _run(tmp_path)
    first_bytes = (decisions / "index.md").read_bytes()
    checked = _run(tmp_path, "--check")
    second = _run(tmp_path)

    assert first.returncode == 0, first.stderr
    assert checked.returncode == 0, checked.stderr
    assert (decisions / "index.md").read_bytes() == first_bytes
    assert second.returncode == 0, second.stderr
    assert (decisions / "index.md").read_bytes() == first_bytes
    rendered = first_bytes.decode("utf-8")
    assert "| [0026](0026-admit-only-budget-and-hardware-feasible-backends.md) | Admit only budget- and hardware-feasible backends to routing | PROVISIONAL | superseded by 0028; supersedes 0005 |" in rendered
    assert "| [0061](0061-the-descriptor-is-agent-command-post.md) | The descriptor is Agent Command Post | ACCEPTED | supersedes 0062 |" in rendered
    assert "| [0064](0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md) | Add training and inference providers; OpenRouter is no longer the sole metered vendor | ACCEPTED | supersedes 0044 |" in rendered


def test_unknown_argument_is_cli_misuse(tmp_path: Path) -> None:
    _write_adr(tmp_path, "0001-alpha.md", "Alpha", "- **Status:** ACCEPTED")

    run = _run(tmp_path, "--unknown")

    assert run.returncode == 2
