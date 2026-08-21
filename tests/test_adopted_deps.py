"""R36(b): adoption is recorded, or it does not happen.

ADR-0065 permits tier-2 modules to import an adopted library, but until now no
check recorded an adoption — the enforced position was "adopt nothing", the
opposite of the instruction. These tests pin the registry schema, the tier-1
absoluteness, the staleness direction, and the checker against the real tree.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / ".github" / "scripts" / "check_adopted_deps.py"
REGISTRY = ROOT / "docs" / "decisions" / "adopted-deps.json"

spec = importlib.util.spec_from_file_location("check_adopted_deps", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_tier1_list_agrees_with_the_scoped_ban() -> None:
    """The checker and tests/test_tier1_imports.py pin the same eight modules."""
    tier1_test = ROOT / "tests" / "test_tier1_imports.py"
    if not tier1_test.is_file():
        pytest.skip("tier-1 test not present in this checkout")
    spec2 = importlib.util.spec_from_file_location("test_tier1_imports", tier1_test)
    module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(module)
    assert tuple(module.TIER1_MODULES) == checker.TIER1_MODULES


def test_registry_is_valid_and_every_adr_resolves() -> None:
    entries, problems = checker.load_registry(REGISTRY)
    assert problems == []
    for package, entry in entries.items():
        adr = entry["adr"]
        assert isinstance(adr, str)
        assert list((ROOT / "docs" / "decisions").glob(f"{adr}-*.md")), (
            f"{package}: ADR-{adr} does not exist"
        )


def test_schema_violations_are_named() -> None:
    bad = {
        "adopted": {
            "evil": {
                "upstream": "http://insecure.example",
                "licence": "GPL-3.0-only",
                "adr": "9999",
                "modules": [],
                "rationale": "short",
            }
        }
    }
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "adopted-deps.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        _, problems = checker.load_registry(path)
    text = "\n".join(problems)
    assert "https" in text
    assert "GPL-3.0-only" in text
    assert "ADR-9999 does not exist" in text
    assert "modules" in text
    assert "rationale" in text


def test_the_ban_can_fail() -> None:
    """Mutation: an unregistered import and a stale entry must each be caught."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        package = root / "src" / "consilient"
        package.mkdir(parents=True)
        (package / "events.py").write_text("import requests\n", encoding="utf-8")
        problems = checker.check_tree(["src/consilient/events.py"], {}, root)
        assert any("tier-1" in p for p in problems)

        (package / "dashboard.py").write_text("import requests\n", encoding="utf-8")
        problems = checker.check_tree(["src/consilient/dashboard.py"], {}, root)
        assert any("unregistered" in p for p in problems)

        entries = {"requests": {"modules": ["dashboard"], "licence": "MIT", "adr": "0065"}}
        (package / "dashboard.py").write_text("import json\n", encoding="utf-8")
        problems = checker.check_tree(["src/consilient/dashboard.py"], entries, root)
        assert any("stale" in p for p in problems)


def test_self_test_passes() -> None:
    assert checker._self_test() == 0


def test_real_tree_is_clean() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECKER)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
