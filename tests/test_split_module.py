"""The splitter's rules, pinned to failures that actually happened.

`scripts/split_module.py` documents thirteen hazards in prose and, until this file, enforced them
with nothing. Every one of them was found the same way -- ruff green, the suite red, or worse, both
green and the behaviour quietly changed -- so the prose is a record of what went wrong rather than
a guarantee it will not recur.

These are not tests for every hazard. They are tests for the four that bit on 28 August 2026 while
splitting twenty-eight files, because a defect that has recurred once will recur again:

  * a `__future__` import was dropped from every destination, silently, for a whole day;
  * a bare registration call was copied into every destination instead of the entry alone;
  * a facade imported from a destination ABOVE it and took 76 test modules down at collection;
  * a plan was refused because a symbol name appeared inside a SQL string.

Each runs the real script against a synthetic module under SPLIT_ROOT, so nothing here touches the
repository.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "split_module.py"


def _run(root: Path, spec: dict[str, object]) -> subprocess.CompletedProcess[str]:
    path = root / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**dict(__import__("os").environ), "SPLIT_ROOT": str(root)},
        check=False,
    )


def _module(root: Path, name: str, body: str) -> None:
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8", newline="\n")


def test_future_import_reaches_every_destination(tmp_path: Path) -> None:
    """It binds a name nothing reads, so the usage filter dropped it from all twenty-eight files.

    This is not a tidy-imports question. `from __future__ import annotations` changes how the
    module is compiled; without it every annotation is evaluated eagerly, and a class that
    annotates its own return type raises NameError at import. That is exactly how it surfaced --
    `def from_mapping(cls, ...) -> ImpactContract` inside `class ImpactContract`.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        "from __future__ import annotations\n\n\nLOW = 1\n\n\ndef high() -> int:\n    return LOW\n",
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_low.py",
                "doc": "Low.",
                "symbols": ["LOW"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["high"]}
            ],
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    sibling = (tmp_path / "src/pkg/thing_low.py").read_text(encoding="utf-8")
    assert "from __future__ import annotations" in sibling


def test_a_registration_call_goes_to_the_entry_point_alone(tmp_path: Path) -> None:
    """A bare call that reaches a family symbol runs its side effect once per file that has it.

    work_items.py ends with `_register_transition_validator()`. Copied into five destinations it
    would have registered the validator five times; in a sibling below the definition it could not
    resolve the name at all, which is how it was caught.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        "REGISTRY: list[int] = []\n\n\ndef register() -> None:\n"
        "    REGISTRY.append(1)\n\n\nregister()\n",
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_store.py",
                "doc": "The store.",
                "symbols": ["REGISTRY"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["register"]}
            ],
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "register()" not in (tmp_path / "src/pkg/thing_store.py").read_text(
        encoding="utf-8"
    )
    assert "register()" in (tmp_path / "src/pkg/thing.py").read_text(encoding="utf-8")


def test_a_sibling_never_imports_from_a_destination_above_it(tmp_path: Path) -> None:
    """The facade counts a name spelled in a string, which is right for imports, wrong for direction.

    `promote_checks.py` was handed an import from a destination above it and 76 test modules died
    at collection with "cannot import name 'Candidate' from partially initialized module". A string
    mention needs no import at all, so the edge is dropped rather than emitted upward.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        'LOW = "mentions Candidate in prose"\n\n\nclass Candidate:\n    pass\n',
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_low.py",
                "doc": "Low.",
                "symbols": ["LOW"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["Candidate"]}
            ],
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    low = (tmp_path / "src/pkg/thing_low.py").read_text(encoding="utf-8")
    assert "import" not in low.replace("from __future__ import annotations", "")


def test_a_name_spelled_only_in_a_string_does_not_refuse_a_plan(tmp_path: Path) -> None:
    """`SCHEMA` holds `CREATE TABLE rejections (...)`, and `rejections` is also a function.

    Four correct plans were refused this way in one afternoon. A refusal that fires on prose is a
    refusal that gets worked around, so the check asks about code unless the module actually
    resolves names dynamically.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        'SCHEMA = "CREATE TABLE rejections (id TEXT)"\n\n\ndef rejections() -> int:\n    return 1\n',
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_schema.py",
                "doc": "The schema.",
                "symbols": ["SCHEMA"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["rejections"]}
            ],
        },
    )
    assert result.returncode == 0, (
        "a name appearing only inside a string refused the plan:\n" + result.stdout
    )


def test_the_guard_would_catch_a_genuine_upward_code_reference(tmp_path: Path) -> None:
    """The rule above must still refuse the thing it exists for, or it is only a way to say yes."""
    _module(
        tmp_path,
        "src/pkg/thing.py",
        "def low() -> int:\n    return high()\n\n\ndef high() -> int:\n    return 2\n",
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_low.py",
                "doc": "Low.",
                "symbols": ["low"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["high"]}
            ],
        },
    )
    assert result.returncode == 1, "an upward reference was accepted"
    assert "REFUSING" in result.stdout
    assert not (tmp_path / "src/pkg/thing_low.py").exists(), (
        "a refused split still wrote a file; writes must be staged until every "
        "destination renders"
    )


@pytest.mark.parametrize("name", ["split_module.py", "verify_split.py"])
def test_the_refactoring_tools_are_self_testable(name: str) -> None:
    """Both tools carry their own checks; verify_split's runs on demand and is exercised here."""
    script = ROOT / "scripts" / name
    assert script.is_file(), f"{name} is referenced by this suite but absent"
    if name == "verify_split.py":
        result = subprocess.run(
            [sys.executable, str(script), "--self-test", "x", "y", "z"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_a_conditional_definition_is_not_copied_into_every_destination(
    tmp_path: Path,
) -> None:
    """A platform-guarded constant is a definition, and belongs in exactly one file.

    MEASURED 29 August 2026 by an outside review. `if sys.platform == "win32": FLAGS = ...`
    binds no name at TOP level, so `header_nodes` classified it as a header and the splitter
    copied it into every destination. The durability contract for the append path ended up in
    sixteen files of the events family, fourteen of which never open a descriptor; in one of
    them the only uses of `os` and `sys` were that dead block. Change the flags and you edit
    sixteen files and miss one.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        "import sys\n"
        "\n"
        'if sys.platform == "win32":\n'
        "    FLAGS = 1\n"
        "else:\n"
        "    FLAGS = 2\n"
        "\n"
        "\n"
        "def uses_flags() -> int:\n"
        "    return FLAGS\n"
        "\n"
        "\n"
        "def unrelated() -> int:\n"
        "    return 7\n",
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {
                "path": "src/pkg/thing_flags.py",
                "doc": "The flags.",
                "symbols": ["FLAGS", "uses_flags"],
            },
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["unrelated"]}
            ],
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    entry = (tmp_path / "src/pkg/thing.py").read_text(encoding="utf-8")
    sibling = (tmp_path / "src/pkg/thing_flags.py").read_text(encoding="utf-8")
    assert "FLAGS = 1" in sibling, "the definition must land in its assigned destination"
    assert "FLAGS = 1" not in entry, (
        "the platform block was copied into a file that does not define it; that is the "
        "sixteen-file duplication this test exists to stop"
    )


def test_a_type_checking_import_block_is_still_a_header(tmp_path: Path) -> None:
    """The exclusion that makes the rule above safe.

    `if TYPE_CHECKING: from x import Y` binds a name every destination needs for its
    annotations. Treating it as a definition would move it to one file and break the others,
    so a conditional block that only imports stays a header and is copied everywhere.
    """
    _module(
        tmp_path,
        "src/pkg/thing.py",
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from decimal import Decimal\n"
        "\n"
        "\n"
        "def low() -> 'Decimal | None':\n"
        "    return None\n"
        "\n"
        "\n"
        "def high() -> 'Decimal | None':\n"
        "    return low()\n",
    )
    _module(tmp_path, "src/pkg/__init__.py", "")
    result = _run(
        tmp_path,
        {
            "source": "src/pkg/thing.py",
            "shared": {"path": "src/pkg/thing_low.py", "doc": "Low.", "symbols": ["low"]},
            "targets": [
                {"path": "src/pkg/thing.py", "doc": "Entry.", "symbols": ["high"]}
            ],
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for name in ("thing.py", "thing_low.py"):
        text = (tmp_path / "src/pkg" / name).read_text(encoding="utf-8")
        assert "from decimal import Decimal" in text, (
            f"{name} lost the TYPE_CHECKING import its annotations need"
        )
