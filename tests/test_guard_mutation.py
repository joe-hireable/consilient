"""The guard-mutation check must itself be able to fail.

This unit exists because 14 of 19 reviewed units carried a guard that could be deleted
with the unit's own suite still green. A checker for that failure which cannot itself
fail would be the same defect wearing a new job title, so the controls below are the
point of the file: the operator is proved to have teeth, survival is proved to be
reported rather than swallowed, and every registry entry is proved to name a real
refusal and a real test.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_guard_mutation.py"
WORKFLOW = ROOT / ".github" / "workflows" / "invariants.yml"


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
