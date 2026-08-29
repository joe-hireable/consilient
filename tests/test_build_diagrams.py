"""Regression tests for diagrams generated from code rather than drawn."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_diagrams.py"
DIAGRAMS = (
    "permission-model.mmd",
    "event-flow.mmd",
    "data-model.mmd",
    "module-dependency.mmd",
)


def _install_script(root: Path) -> Path:
    """Copy the generator AND its siblings.

    build_diagrams.py was split on 28 August 2026, and scripts/ is not a package: a sibling is
    importable only because the entry point puts its own directory on sys.path. Copying one file
    into a scratch tree therefore produced a ModuleNotFoundError rather than a diagram.
    """
    destination = root / "scripts" / SCRIPT.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    for path in [SCRIPT, *sorted(SCRIPT.parent.glob(f"{SCRIPT.stem}_*.py"))]:
        shutil.copy2(path, destination.parent / path.name)
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _digest(root: Path, relative: str) -> str:
    path = root / relative
    digest = hashlib.sha256()
    file_digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    digest.update(relative.encode("utf-8"))
    digest.update(b"\0")
    digest.update(file_digest.encode("ascii"))
    digest.update(b"\n")
    return digest.hexdigest()


def _fixture_tree(root: Path) -> None:
    _write(
        root / "src" / "consilient" / "effects.py",
        '''
ADMISSION_CLASSES = frozenset({"material_choice", "capability_gap", "protected_uncovered"})


class AdmissionResult:
    def __init__(self, admission, disposition, reason):
        self.admission = admission
        self.disposition = disposition
        self.reason = reason


def derive_admission(manifest, capability, facts):
    if not capability.available:
        return AdmissionResult("capability_gap", "refuse", "capability_unavailable")
    if capability.gate.state != "admitted":
        return AdmissionResult("capability_gap", "refuse", capability.gate.reason)
    admission = _classify_admission(manifest, facts)
    disposition, reason = _disposition_for(admission, "exact_grant", facts)
    return AdmissionResult(admission, disposition, reason)


def _classify_admission(manifest, facts):
    if facts.is_material_choice:
        return "material_choice"
    if facts.is_protected:
        return "protected_uncovered"
    return "capability_gap"


def _disposition_for(admission, gate_reason, facts):
    if admission == "capability_gap":
        return "refuse", gate_reason
    if admission == "protected_uncovered":
        return "escalate", "protected_class_without_standing_authority"
    if admission in {"material_choice"}:
        return "execute", gate_reason
    return "refuse", "unhandled_admission_class"
'''.lstrip(),
    )
    _write(
        root / "src" / "consilient" / "events.py",
        '''
from . import effects

OUTCOME_KIND = "attempt.outcome"
RECORD_CAPTURED_KIND = "record.captured"


def validate(event):
    return event


def append(event):
    validate(event)
    return event


def register_transition_validator(kinds, validator):
    return None
'''.lstrip(),
    )
    _write(
        root / "src" / "consilient" / "projection.py",
        '''
from . import events

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    position   INTEGER PRIMARY KEY,
    ts         TEXT NOT NULL,
    kind       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    attempt_id      TEXT NOT NULL UNIQUE,
    verifier_accept INTEGER NOT NULL,
    human_verdict   TEXT
);
"""
'''.lstrip(),
    )
    _write(
        root / "src" / "consilient" / "cli.py",
        "from . import events\nfrom . import projection\n",
    )


def _diagram(root: Path, name: str) -> str:
    return (root / "docs" / "diagrams" / name).read_text(encoding="utf-8")


def _body(rendered: str) -> str:
    lines = [line for line in rendered.splitlines() if not line.startswith("%%")]
    return "\n".join(lines).lstrip()


def test_writes_four_named_mermaid_diagrams(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    run = _run(tmp_path)

    assert run.returncode == 0, run.stderr
    names = sorted(path.name for path in (tmp_path / "docs" / "diagrams").glob("*.mmd"))
    assert names == sorted(DIAGRAMS)


def test_permission_model_is_derived_from_effects_control_flow(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    rendered = _diagram(tmp_path, "permission-model.mmd")

    assert _body(rendered).startswith("flowchart")
    assert "material_choice" in rendered
    assert "protected_uncovered" in rendered
    assert "execute" in rendered
    assert "escalate" in rendered
    assert "refuse" in rendered
    assert "is_material_choice" in rendered


def test_material_choice_executes_because_that_is_what_the_code_does(
    tmp_path: Path,
) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    rendered = _diagram(tmp_path, "permission-model.mmd")
    execute_line = next(
        line for line in rendered.splitlines() if "material_choice" in line and "execute" in line
    )
    assert "-->" in execute_line or "execute" in execute_line


def test_event_flow_lists_kind_constants_and_the_append_boundary(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    rendered = _diagram(tmp_path, "event-flow.mmd")

    assert "attempt.outcome" in rendered
    assert "record.captured" in rendered
    assert "append" in rendered
    assert "register_transition_validator" in rendered


def test_data_model_lists_schema_tables_and_columns(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    rendered = _diagram(tmp_path, "data-model.mmd")

    assert _body(rendered).startswith("erDiagram")
    assert "events" in rendered
    assert "outcomes" in rendered
    assert "verifier_accept" in rendered
    assert "human_verdict" in rendered


def test_module_dependency_lists_import_edges_from_src(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    rendered = _diagram(tmp_path, "module-dependency.mmd")

    assert "consilient_events --> consilient_effects" in rendered
    assert "consilient_projection --> consilient_events" in rendered
    assert "consilient_cli --> consilient_events" in rendered
    assert "consilient_cli --> consilient_projection" in rendered


def test_headers_name_producer_source_and_digest(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)

    assert _run(tmp_path).returncode == 0
    permission = _diagram(tmp_path, "permission-model.mmd")
    assert "**Producer:** `scripts/build_diagrams.py`" in permission
    assert "**Source:** `src/consilient/effects.py`" in permission
    assert f"**Source SHA-256:** `{_digest(tmp_path, 'src/consilient/effects.py')}`" in permission
    assert "**Do not hand-edit:** regenerate with `python scripts/build_diagrams.py`." in permission


def test_check_passes_when_diagrams_match_a_fresh_render(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)
    assert _run(tmp_path).returncode == 0

    run = _run(tmp_path, "--check")

    assert run.returncode == 0, run.stderr
    assert "current" in run.stdout


def test_check_detects_stale_permission_model_without_writing(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)
    assert _run(tmp_path).returncode == 0
    target = tmp_path / "docs" / "diagrams" / "permission-model.mmd"
    stale = b"stale drawn diagram\n"
    target.write_bytes(stale)

    run = _run(tmp_path, "--check")

    assert run.returncode == 1
    assert "permission-model.mmd" in run.stderr
    assert target.read_bytes() == stale


def test_editing_effects_without_regenerating_fails_check(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)
    assert _run(tmp_path).returncode == 0
    effects = tmp_path / "src" / "consilient" / "effects.py"
    effects.write_text(
        effects.read_text(encoding="utf-8").replace(
            'return "capability_gap"',
            'return "brand_new_class"',
            1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    before = {
        name: (tmp_path / "docs" / "diagrams" / name).read_bytes() for name in DIAGRAMS
    }

    run = _run(tmp_path, "--check")

    assert run.returncode == 1
    assert "permission-model.mmd" in run.stderr
    after = {
        name: (tmp_path / "docs" / "diagrams" / name).read_bytes() for name in DIAGRAMS
    }
    assert after == before


def test_second_generation_is_byte_identical(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)
    assert _run(tmp_path).returncode == 0
    first = {
        name: (tmp_path / "docs" / "diagrams" / name).read_bytes() for name in DIAGRAMS
    }

    run = _run(tmp_path)
    assert run.returncode == 0, run.stderr
    second = {
        name: (tmp_path / "docs" / "diagrams" / name).read_bytes() for name in DIAGRAMS
    }
    assert second == first
    for content in second.values():
        assert b"\r" not in content
        lowered = content.lower()
        assert b"datetime" not in lowered
        assert b"timestamp" not in lowered


def test_missing_source_refuses_without_writing(tmp_path: Path) -> None:
    _fixture_tree(tmp_path)
    (tmp_path / "src" / "consilient" / "effects.py").unlink()

    run = _run(tmp_path)

    assert run.returncode == 1
    assert "effects.py" in run.stderr
    assert not (tmp_path / "docs" / "diagrams").exists()


def test_live_effects_py_still_routes_material_choice_to_execute(tmp_path: Path) -> None:
    for path in (ROOT / "src").rglob("*.py"):
        destination = tmp_path / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    run = _run(tmp_path)
    assert run.returncode == 0, run.stderr
    rendered = _diagram(tmp_path, "permission-model.mmd")
    assert "material_choice" in rendered
    assert "execute" in rendered
    assert any(
        "material_choice" in line and "execute" in line for line in rendered.splitlines()
    )


def test_failed_replace_preserves_existing_diagram(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fixture_tree(tmp_path)
    target = tmp_path / "docs" / "diagrams" / "permission-model.mmd"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"old diagram\n")
    spec = importlib.util.spec_from_file_location(
        "build_diagrams", _install_script(tmp_path)
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("replace failed")

    # `write_atomic` and its `os` import moved into build_diagrams_sources.py on 28 August
    # 2026. The entry point no longer imports os at all, so patching it there raised rather
    # than silently missing -- the loud version of the facade hazard, for once.
    sources = sys.modules["build_diagrams_sources"]
    monkeypatch.setattr(sources.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        module.write_atomic(target, b"new diagram\n")
    assert target.read_bytes() == b"old diagram\n"


def test_committed_diagrams_match_a_fresh_render() -> None:
    """The files say "do not hand-edit, regenerate" -- so something must check they were.

    Nothing did. `build_diagrams.py` appears in no workflow and no test compared its output to
    what is committed, and MEASURED on 28 August 2026 the committed data model was three tables
    short: capability_versions, capability_heads and capability_conflicts had been added to
    `SCHEMA` and the diagram was never regenerated. The instruction in the header was the whole
    of the enforcement, which is to say there was none.

    This is cheap because the renderers are pure functions of the source tree, so the check is
    simply to run them and compare bytes. It fails loudly on the next drift instead of leaving a
    stale document that still looks authoritative.
    """
    spec = importlib.util.spec_from_file_location("build_diagrams_live", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    stale = [
        name
        for name, content in module.render_all(ROOT)
        if (ROOT / "docs" / "diagrams" / name).read_bytes() != content
    ]
    assert not stale, (
        "these committed diagrams no longer match their source: "
        + ", ".join(stale)
        + ". Run `python scripts/build_diagrams.py` and commit the result."
    )
