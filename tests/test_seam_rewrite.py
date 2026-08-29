"""The seam rewrite's claim is about RUNTIME, so it is checked by running it.

`scripts/seam_rewrite.py` exists to make one `monkeypatch.setattr` reach callers that a split has
moved into other files. That is not a claim about the text it produces; it is a claim about what
happens when the patched module object is mutated. Asserting on the diff would pass while the
mechanism silently failed, which is the failure the tool was written to remove.

So the tests below build a two-module family in a temporary directory, import it, patch the module
that DEFINES the name, and check what the caller in the OTHER module actually sees. Before the
rewrite the caller ignores the patch; afterwards both the cross-module caller and the same-module
caller observe it. That difference is the whole justification for a rewrite that touched 73 call
sites in scripts/dispatch.py on 28 August 2026.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "seam_rewrite.py"


def _family(directory: Path) -> None:
    """A definer, and an entry point that calls it by bare name through a facade import."""
    (directory / "thing_seams.py").write_text(
        "def run_process(cmd: str) -> str:\n"
        '    return "real"\n'
        "\n"
        "\n"
        "def helper() -> str:\n"
        '    return run_process("x")\n',
        encoding="utf-8",
        newline="\n",
    )
    (directory / "thing.py").write_text(
        "from thing_seams import (\n    helper,\n    run_process,\n)\n"
        "\n"
        '__all__ = [\n    "helper",\n    "run_process",\n]\n'
        "\n"
        "\n"
        "def go() -> str:\n"
        '    return run_process("y")\n',
        encoding="utf-8",
        newline="\n",
    )


def _run(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "thing",
            "--dir",
            str(directory),
            "--patched",
            "run_process",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _import(directory: Path) -> tuple[object, object]:
    for name in ("thing", "thing_seams"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(directory))
    try:
        seams = importlib.import_module("thing_seams")
        entry = importlib.import_module("thing")
    finally:
        sys.path.remove(str(directory))
    return entry, seams


def test_without_the_rewrite_a_patch_does_not_reach_a_caller_in_another_file(
    tmp_path: Path,
) -> None:
    """The defect, demonstrated. Nothing raises; the caller simply runs the real function."""
    _family(tmp_path)
    entry, seams = _import(tmp_path)
    seams.run_process = lambda cmd: "PATCHED"  # type: ignore[attr-defined]
    assert entry.go() == "real", (  # type: ignore[attr-defined]
        "this test asserts the BROKEN behaviour; if the bare-name caller now sees the patch, "
        "the premise of seam_rewrite.py has changed and the tool may be unnecessary"
    )


def test_after_the_rewrite_one_patch_reaches_every_caller(tmp_path: Path) -> None:
    """The claim: an attribute resolved at call time is resolved against the patched object."""
    _family(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr

    entry, seams = _import(tmp_path)
    assert entry.go() == "real"  # type: ignore[attr-defined]
    seams.run_process = lambda cmd: "PATCHED"  # type: ignore[attr-defined]
    assert entry.go() == "PATCHED", (  # type: ignore[attr-defined]
        "the cross-module caller still resolves the name in its own globals"
    )
    assert seams.helper() == "PATCHED", (  # type: ignore[attr-defined]
        "a caller in the DEFINING module must keep working on a bare name; prefixing those "
        "would be noise, since a bare name there already resolves in the patched namespace"
    )


def test_the_facade_survives_so_existing_importers_do_not_break(tmp_path: Path) -> None:
    """The name import stays. Removing it unbound 53 names that __all__ still listed."""
    _family(tmp_path)
    assert _run(tmp_path).returncode == 0
    text = (tmp_path / "thing.py").read_text(encoding="utf-8")
    assert "import thing_seams" in text
    assert "from thing_seams import" in text, "the facade import was removed"
    assert '"run_process"' in text, "__all__ lost a name it still re-exports"
    entry, _seams = _import(tmp_path)
    assert hasattr(entry, "run_process"), "thing.run_process stopped resolving"


def _split_entry_points() -> list[Path]:
    """Every script that has split siblings beside it."""
    out: list[Path] = []
    for directory in (ROOT / "scripts", ROOT / ".harness"):
        for path in sorted(directory.glob("*.py")):
            if "_" in path.stem and (directory / (path.stem.split("_")[0] + ".py")).is_file():
                continue
            if any(directory.glob(f"{path.stem}_*.py")):
                out.append(path)
    return out


@pytest.mark.parametrize("script", _split_entry_points(), ids=lambda p: p.stem)
def test_a_split_script_still_runs_standalone(script: Path) -> None:
    """Running it is the operator surface, and the suite never runs it.

    Every test loads these through importlib with the scripts directory already on sys.path, so
    2,179 tests passed on 28 August 2026 while `python scripts/dispatch.py --help` raised
    NameError: a sibling imported `consilient` before the split had put src on sys.path, and it
    resolved to a stale copy in site-packages instead. Orchestration is typed as
    `python scripts/dispatch.py`, so a family that only imports under pytest is broken.

    Executed with run_name set to something other than "__main__", so the module and every
    sibling it pulls in are imported while `main()` is not called. The exit code is then the
    whole answer, and no argument parsing is involved -- which matters because these scripts
    disagree about arguments, and because an earlier version of this test looked for four
    exception NAMES in the output and passed a file broken with a SyntaxError.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy, sys; runpy.run_path(sys.argv[1], run_name='imported')",
            str(script),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        check=False,
    )
    assert result.returncode == 0, (
        f"{script.name} does not import when run as a script:" + chr(10)
        + (result.stdout + result.stderr)[-900:]
    )
