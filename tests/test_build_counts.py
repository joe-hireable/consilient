"""Counts in README.md and CLAUDE.md are generated, never handwritten.

On 23 August 2026 README.md claimed 34 ADRs and 35 registered experiments while the
tree held 95 and 109, and CLAUDE.md independently claimed 45 ADRs and 47 experiments
against the same disk. [measured] Two hand-kept locations produced two different
wrong answers. Generation from the files on disk is the repair; --check is the
ratchet so it cannot silently drift again.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_counts.py"

INVENTORY_BEGIN = "<!-- BEGIN GENERATED: scripts/build_counts.py#inventory -->"
INVENTORY_END = "<!-- END GENERATED: scripts/build_counts.py#inventory -->"
EXPERIMENTS_BEGIN = "<!-- BEGIN GENERATED: scripts/build_counts.py#experiments -->"
EXPERIMENTS_END = "<!-- END GENERATED: scripts/build_counts.py#experiments -->"


def _install_script(root: Path) -> Path:
    assert SCRIPT.is_file(), "scripts/build_counts.py must exist"
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


def _write_sources(root: Path, *, adrs: int, experiments: int, steps: int) -> None:
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
    headings = "\n".join(f"### EXP-{index:02d}\n" for index in range(1, experiments + 1))
    register.write_text(headings + "\n", encoding="utf-8", newline="\n")
    workflow = root / ".github" / "workflows" / "invariants.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    named = "\n".join(f"      - name: Check {index}\n" for index in range(steps))
    workflow.write_text(
        "jobs:\n  invariants:\n    steps:\n" + named,
        encoding="utf-8",
        newline="\n",
    )


def _write_documents(root: Path, *, inventory: str, experiments: str, claude: str) -> None:
    (root / "README.md").write_text(
        "# Fixture\n\n"
        f"{INVENTORY_BEGIN}\n{inventory}\n{INVENTORY_END}\n\n"
        f"See {EXPERIMENTS_BEGIN}\n{experiments}\n{EXPERIMENTS_END}.\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "CLAUDE.md").write_text(
        "# Fixture\n\n"
        f"The repository holds {INVENTORY_BEGIN}\n{claude}\n{INVENTORY_END}.\n",
        encoding="utf-8",
        newline="\n",
    )


def test_producer_writes_counts_from_disk_and_check_is_byte_identical(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, adrs=3, experiments=5, steps=2)
    _write_documents(
        tmp_path,
        inventory="0 ADRs, 0 registered experiments, 0 invariant checks in CI.",
        experiments="0 experiments with stopping rules",
        claude="0 ADRs and 0 registered experiments",
    )

    written = _run(tmp_path)
    assert written.returncode == 0, written.stderr
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "3 ADRs, 5 registered experiments, 2 invariant checks in CI." in readme
    assert "5 experiments with stopping rules" in readme
    assert "3 ADRs and 5 registered experiments" in claude
    first_readme = (tmp_path / "README.md").read_bytes()
    first_claude = (tmp_path / "CLAUDE.md").read_bytes()

    checked = _run(tmp_path, "--check")
    assert checked.returncode == 0, checked.stdout + checked.stderr
    again = _run(tmp_path)
    assert again.returncode == 0, again.stderr
    assert (tmp_path / "README.md").read_bytes() == first_readme
    assert (tmp_path / "CLAUDE.md").read_bytes() == first_claude


def test_check_fails_on_a_hand_edited_count_and_missing_region(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, adrs=2, experiments=4, steps=1)
    _write_documents(
        tmp_path,
        inventory="2 ADRs, 4 registered experiments, 1 invariant checks in CI.",
        experiments="4 experiments with stopping rules",
        claude="2 ADRs and 4 registered experiments",
    )
    generate = _run(tmp_path)
    assert generate.returncode == 0, generate.stderr

    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "2 ADRs, 4 registered experiments, 1 invariant checks in CI.",
            "99 ADRs, 4 registered experiments, 1 invariant checks in CI.",
        ),
        encoding="utf-8",
        newline="\n",
    )
    drifted = _run(tmp_path, "--check")
    assert drifted.returncode == 1
    assert "README.md" in drifted.stdout + drifted.stderr

    (tmp_path / "CLAUDE.md").write_text("# Fixture\n\nno region\n", encoding="utf-8")
    missing = _run(tmp_path, "--check")
    assert missing.returncode == 1
    assert "CLAUDE.md" in missing.stdout + missing.stderr


def test_unknown_argument_is_cli_misuse(tmp_path: Path) -> None:
    _write_sources(tmp_path, adrs=1, experiments=1, steps=1)
    _write_documents(
        tmp_path,
        inventory="1 ADRs, 1 registered experiments, 1 invariant checks in CI.",
        experiments="1 experiments with stopping rules",
        claude="1 ADRs and 1 registered experiments",
    )
    run = _run(tmp_path, "--unknown")
    assert run.returncode == 2


def test_live_claude_and_readme_counts_are_generated_from_disk() -> None:
    """The public restatements that drifted. CLAUDE.md's '45 ADRs' is the named defect."""
    assert SCRIPT.is_file(), "scripts/build_counts.py must exist"
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "45 ADRs" not in claude
    assert INVENTORY_BEGIN in readme
    assert INVENTORY_BEGIN in claude
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
