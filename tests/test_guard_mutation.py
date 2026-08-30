"""The guard-mutation check must itself be able to fail.

This unit exists because 14 of 19 reviewed units carried a guard that could be deleted
with the unit's own suite still green. A checker for that failure which cannot itself
fail would be the same defect wearing a new job title, so the controls below are the
point of the file: the operator is proved to have teeth, survival is proved to be
reported rather than swallowed, and every registry entry is proved to name a real
refusal and a real test.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

from build_driver_helpers import _load_driver

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_guard_mutation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "invariants.yml"
PYPROJECT = ROOT / "pyproject.toml"
MYPY_INI = ROOT / "mypy.ini"
TESTS = ROOT / "tests"

DATE_DERIVED_LOG_PATH = re.compile(r"""\bTS\s*\[\s*:?\s*10\s*\].*\.jsonl""")


def _named_workflow_steps(workflow: str) -> list[tuple[str, str]]:
    job = workflow.partition("jobs:")[2]
    steps: list[tuple[str, str]] = []
    for chunk in job.split("- name:")[1:]:
        name, _, body = chunk.partition("\n")
        steps.append((name.strip(), body))
    return steps


def _docstring_line_ranges(source: str) -> set[int]:
    tree = ast.parse(source)
    ranges: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            continue
        if not hasattr(node, "body") or not node.body:
            continue
        doc_node = node.body[0]
        if isinstance(doc_node, ast.Expr) and isinstance(doc_node.value, ast.Constant):
            start = doc_node.lineno
            end = doc_node.end_lineno or start
            ranges.update(range(start, end + 1))
    return ranges


def _date_literal_log_path_violations(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    doc_lines = _docstring_line_ranges(source)
    violations: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if lineno in doc_lines or line.lstrip().startswith("#"):
            continue
        if not DATE_DERIVED_LOG_PATH.search(line):
            continue
        window = lines[max(0, lineno - 2) : min(len(lines), lineno + 2)]
        if any(".write_text(" in nearby for nearby in window):
            continue
        violations.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    return violations


def _load():
    spec = importlib.util.spec_from_file_location("check_guard_mutation", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # The module defines a dataclass; `dataclasses` looks its owning module up in
    # `sys.modules` while processing the class, so registration precedes execution.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load()


GUARDED = "\n".join(
    (
        "class Holder:",
        "    def refuse(self, value):",
        "        if value < 0:",
        '            raise ValueError("negative")',
        "        for item in ():",
        "            raise RuntimeError(item)",
        "        return value",
        "",
        "def untouched(value):",
        '    raise KeyError("this raise is outside the target")',
        "",
    )
)


def test_deletion_removes_every_refusal_in_the_target_and_nothing_else():
    mutated, deleted = checker.delete_guard(GUARDED, "Holder.refuse")
    assert deleted == 2
    namespace: dict[str, object] = {}
    exec(compile(mutated, "<mutant>", "exec"), namespace)
    holder = namespace["Holder"]()  # type: ignore[operator]
    assert holder.refuse(-1) == -1, "the guard still refuses after deletion"
    assert holder.refuse(1) == 1, "deletion changed the accepted path"
    with pytest.raises(KeyError):
        namespace["untouched"](0)  # type: ignore[operator]


def test_a_function_that_refuses_nothing_is_a_registry_error_not_a_pass():
    source = "def nothing(value):\n    return value\n"
    with pytest.raises(checker.GuardMutationError):
        checker.delete_guard(source, "nothing")


def test_an_unresolvable_target_is_a_registry_error():
    with pytest.raises(checker.GuardMutationError):
        checker.delete_guard(GUARDED, "Holder.absent")
    with pytest.raises(checker.GuardMutationError):
        checker.delete_guard(GUARDED, "absent")


def test_the_operator_has_teeth_when_a_test_watches_the_guard(tmp_path):
    survived = checker._control(tmp_path / "exercised", checker._CONTROL_TEST_EXERCISED)
    assert not survived, (
        "a test that exercises the guard did not notice its deletion; the mutation "
        "operator is inert and every kill this checker reports would be meaningless"
    )


def test_survival_is_reported_when_no_test_watches_the_guard(tmp_path):
    survived = checker._control(tmp_path / "blind", checker._CONTROL_TEST_BLIND)
    assert survived, (
        "a test that never exercises the guard was reported as killing the mutant; "
        "the checker cannot fail and is the defect it exists to find"
    )


def test_the_registry_is_not_empty():
    assert checker.GUARDS, "an empty registry would pass the check vacuously"
    assert checker.check_registry(()) == 1


def test_every_registry_entry_names_a_real_refusal_and_real_tests():
    for guard in checker.GUARDS:
        module = ROOT / guard.module
        assert module.is_file(), f"{guard.guard_id}: {guard.module} does not exist"
        # Follow the split the same way the checker does, or this asserts against a filename
        # while the checker asserts against the code, and the two answer different questions.
        module = checker._resolve_within_family(module, guard.function)
        # Raises GuardMutationError if the function is absent or refuses nothing.
        _, deleted = checker.delete_guard(
            module.read_text(encoding="utf-8"), guard.function
        )
        assert deleted > 0
        assert guard.tests, f"{guard.guard_id}: declares no protecting test"
        for selection in guard.tests:
            path = ROOT / selection.partition("::")[0]
            assert path.exists(), f"{guard.guard_id}: {selection} does not exist"


def test_the_check_is_wired_into_ci():
    # Working principle 3: a chokepoint with no enforcement rule is not a chokepoint.
    # `check_generated_documents.py` existed, worked and was called by no workflow.
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "check_guard_mutation.py --self-test" in workflow, (
        "the guard-mutation check is not invoked by the invariants workflow"
    )


def test_every_named_invariant_step_carries_if_not_cancelled():
    """GitHub Actions skips later steps after the first failure unless they opt out."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    missing = [
        name
        for name, body in _named_workflow_steps(workflow)
        if "!cancelled()" not in body
    ]
    assert not missing, (
        "named invariant steps must carry `if: ${{ !cancelled() }}` so one red gate "
        f"does not mask the rest: {missing}"
    )


def test_no_test_builds_a_daily_log_path_from_a_frozen_timestamp_slice():
    """The midnight suite failure: API writes today's file, tests read a frozen TS date."""
    violations: list[str] = []
    for path in sorted(TESTS.rglob("*.py")):
        if path.name == "test_guard_mutation.py":
            continue
        violations.extend(_date_literal_log_path_violations(path))
    assert not violations, (
        "tests must not name daily log files from a frozen TS timestamp slice; "
        "read the directory instead:\n" + "\n".join(violations)
    )


def test_ruff_excludes_harness_instance_data():
    import tomllib

    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    exclude = config["tool"]["ruff"]["exclude"]
    assert ".harness" in exclude, (
        "instance trajectory data under .harness/ must not be linted as product code"
    )


def test_ruff_lint_selects_ruf100():
    import tomllib

    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    selected = config["tool"]["ruff"]["lint"]["extend-select"]
    assert "RUF100" in selected, (
        "unused `# noqa` comments must fail lint, not silently rot"
    )


def test_mypy_ini_targets_strict_mode():
    assert "strict = True" in MYPY_INI.read_text(encoding="utf-8"), (
        "mypy.ini must declare strict mode alongside pyproject's tested floor"
    )


def test_a_loaded_driver_holds_no_live_instance_path() -> None:
    """The pollution of 30 August 2026 was read out of the live tree, not written by it."""
    driver = _load_driver()
    live = (driver.ROOT / ".harness").resolve()
    stray = sorted(
        name
        for name, value in vars(driver).items()
        if isinstance(value, Path)
        and name != "UNITS"
        and live in value.resolve().parents
    )
    assert not stray, (
        "a driver loaded for a check points at live instance state: "
        + ", ".join(stray)
        + ". Four zero-byte U01 files in the live briefs directory failed three checks "
        "for ten hours, 30 minutes after they were written. Route the load through "
        "_sandbox_instance_paths, or exempt the global there with the reason it must "
        "stay live."
    )


def test_every_driver_loader_sandboxes_the_module_it_loads() -> None:
    """Four loaders of the driver already exist; the fifth is where this regresses.

    A CALL is required, not a mention. Measured while proving this guard could be made
    red: deleting `_sandbox_instance_paths(module)` from a loader left a substring check
    green, because the import line above it still carried the name. The import is not the
    isolation; the call is.
    """
    bypass = []
    # This file states the rule, so it names the driver and calls spec_from_file_location
    # (for the guard-mutation checker) without being a loader. Excluded by name because
    # every sharper filter tried -- string constants, exec_module, path shape -- matched
    # it too; a filter tuned until it missed this file is this exclusion, hidden.
    self_name = Path(__file__).name
    for source_path in sorted(TESTS.glob("*.py")):
        if source_path.name == self_name:
            continue
        source = source_path.read_text(encoding="utf-8")
        if "spec_from_file_location" not in source or "build_driver.py" not in source:
            continue
        called = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_sandbox_instance_paths"
            for node in ast.walk(ast.parse(source))
        )
        if not called:
            bypass.append(source_path.name)
    assert not bypass, (
        "these load the build driver without sandboxing its instance paths, so a "
        "fixture id they write survives in the live tree and decides a later check: "
        + ", ".join(bypass)
    )
