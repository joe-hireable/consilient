from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_skills.py"


def load_sync_skills() -> ModuleType:
    assert SCRIPT.is_file(), "skills mirror script is missing"
    spec = importlib.util.spec_from_file_location("sync_skills", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skill_tree(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / ".agents" / "skills"
    mirror = tmp_path / ".claude" / "skills"
    (source / "example").mkdir(parents=True)
    (source / "README.md").write_text("source\n", encoding="utf-8")
    (source / "example" / "SKILL.md").write_bytes(b"skill\x00bytes\n")
    mirror.parent.mkdir(parents=True)
    return source, mirror


def test_exact_copied_tree_is_accepted(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)

    assert load_sync_skills().find_drift(source, mirror) == []


def test_missing_copied_file_is_rejected(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)
    (mirror / "README.md").unlink()

    assert "missing: README.md" in load_sync_skills().find_drift(source, mirror)


def test_extra_copied_file_is_rejected(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)
    (mirror / "extra.txt").write_text("extra\n", encoding="utf-8")

    assert "extra: extra.txt" in load_sync_skills().find_drift(source, mirror)


def test_changed_copied_bytes_are_rejected(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)
    (mirror / "example" / "SKILL.md").write_bytes(b"changed\n")

    assert "content differs: example/SKILL.md" in load_sync_skills().find_drift(
        source, mirror
    )


def test_copied_entry_type_drift_is_rejected(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)
    (mirror / "README.md").unlink()
    (mirror / "README.md").mkdir()

    assert "type differs: README.md" in load_sync_skills().find_drift(source, mirror)


def test_correct_symlink_is_accepted(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    target = os.path.relpath(source, mirror.parent).replace(os.sep, "/")
    try:
        os.symlink(target, mirror, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")

    assert load_sync_skills().find_drift(source, mirror) == []


def test_wrong_symlink_target_is_rejected(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    wrong = tmp_path / "wrong"
    wrong.mkdir()
    try:
        os.symlink(wrong, mirror, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")

    assert "symlink target differs" in load_sync_skills().find_drift(source, mirror)[0]


def test_repair_prefers_a_symlink_when_supported(tmp_path: Path) -> None:
    source, mirror = skill_tree(tmp_path)
    probe = tmp_path / "symlink-probe"
    try:
        os.symlink(source, probe, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")
    probe.unlink()

    mode = load_sync_skills().repair(source, mirror)

    assert mode == "symlink"
    assert mirror.is_symlink()


def test_repair_falls_back_to_an_exact_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, mirror = skill_tree(tmp_path)
    mirror.write_text("../.agents/skills", encoding="utf-8")
    module = load_sync_skills()

    def deny_symlink(*_args: object, **_kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(module.os, "symlink", deny_symlink)

    assert module.repair(source, mirror) == "copy"
    assert mirror.is_dir()
    assert module.find_drift(source, mirror) == []


def test_repair_does_not_remove_mirror_when_source_is_missing(tmp_path: Path) -> None:
    source = tmp_path / "missing"
    mirror = tmp_path / "skills"
    mirror.write_text("keep me\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        load_sync_skills().repair(source, mirror)

    assert mirror.read_text(encoding="utf-8") == "keep me\n"


def test_repair_does_not_remove_mirror_when_replacement_cannot_be_built(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, mirror = skill_tree(tmp_path)
    mirror.write_text("keep me\n", encoding="utf-8")
    module = load_sync_skills()

    def deny(*_args: object, **_kwargs: object) -> None:
        raise OSError("denied")

    monkeypatch.setattr(module.os, "symlink", deny)
    monkeypatch.setattr(module.shutil, "copytree", deny)

    with pytest.raises(OSError, match="denied"):
        module.repair(source, mirror)

    assert mirror.read_text(encoding="utf-8") == "keep me\n"


def test_check_mode_returns_nonzero_on_real_byte_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source, mirror = skill_tree(tmp_path)
    shutil.copytree(source, mirror)
    module = load_sync_skills()
    assert module.main(["--check"], source=source, mirror=mirror) == 0
    assert "copy mirror is current" in capsys.readouterr().out

    original = (mirror / "README.md").read_bytes()
    (mirror / "README.md").write_text("mutated\n", encoding="utf-8")

    assert module.main(["--check"], source=source, mirror=mirror) == 1
    assert "content differs: README.md" in capsys.readouterr().out

    (mirror / "README.md").write_bytes(original)

    assert module.main(["--check"], source=source, mirror=mirror) == 0
    assert "copy mirror is current" in capsys.readouterr().out


def test_ci_runs_the_portable_check_and_keeps_the_agent_mirror_check() -> None:
    workflow = (ROOT / ".github" / "workflows" / "skills-mirror.yml").read_text(
        encoding="utf-8"
    )

    assert "python scripts/sync_skills.py --check" in workflow
    assert "test -L .claude/agents" in workflow
    assert 'readlink .claude/agents)" = "../.agents/agents"' in workflow
