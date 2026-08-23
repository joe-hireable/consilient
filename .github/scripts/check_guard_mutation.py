"""Refuse a guard whose deletion leaves its own tests green.

The cross-family review of 23 August 2026 found that 14 of 19 units carried at least
one guard that could be deleted with the unit's own suite still passing
(`docs/00-context/verification-of-the-twenty-2026-08-23.md`). A test that cannot fail
is worse than no test, because it is counted as evidence.

The incumbent for this job is program mutation testing -- `mutmut` (BSD-3-Clause) and
`cosmic-ray` (MIT), named in the experiment register at EXP-47. This repository has
already measured that incumbent against exactly this question and it lost: EXP-48
recovered 5 of 25 catalogued defective guards (recall 20.0%) at cluster precision
24.6%, and 68% of the catalogued guards live outside Python source entirely, where a
first-order syntactic census cannot reach [measured, docs/10-research/experiments/exp48].
A CI gate on "no surviving mutant" would open red on 586 survivors and still miss two
thirds of the real defects.

So this is not a census. It is a declared-guard deletion check: a guard names itself
and names the tests that claim to protect it, the guard's teeth are removed, and those
tests are required to go red. Precision by construction, no census to triage, and no
dependency -- `ast`, `subprocess` and `pytest`, which CI already installs.

The operator is deletion of effect: every `raise` inside the named function becomes
`pass`. A guard is code that refuses; a guard with no refusal left is a guard deleted.
A named function containing no `raise` is a registry error, not a pass.

Two controls keep this check from becoming the thing it polices. Per guard, the
declared tests must be green against an unmutated copy first -- a permanently red test
would otherwise "kill" every mutant it never ran. And `--self-test` builds a synthetic
guard both ways: one whose test exercises it (the mutant must die) and one whose test
does not (the checker must report survival).
"""

from __future__ import annotations

import argparse
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GIT_ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}

# git exports GIT_DIR and GIT_INDEX_FILE into every hook it runs, and GIT_DIR overrides cwd — so a
# subprocess inheriting them works against a different repository than the one it was pointed at,
# silently. Every gate script here scrubs them, and `test_gate_scripts_scrub_the_git_environment`
# refuses one that does not. The rule is deliberately blunt: it applies to any spawn, not only to
# git calls, because a per-script exemption is how an invariant erodes.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

# Windows and the CI runner both need an explicit timeout; a hung mutant must be a
# failure, never a silent pass. A subprocess timeout does not kill grandchildren, so
# the test selections below are deliberately narrow.
TEST_TIMEOUT_S = 900


@dataclass(frozen=True)
class Guard:
    """A named refusal, and the tests that claim deleting it would be noticed."""

    guard_id: str
    module: str
    function: str
    tests: tuple[str, ...]


# Every entry here was confirmed by running this checker: the declared tests are green
# unmutated and red against the mutant. An entry is a claim that these tests protect
# this refusal, and this check is what makes the claim falsifiable.
_V0 = "tests/test_v0_invariants.py"

GUARDS: tuple[Guard, ...] = (
    Guard(
        # CONSILIENCE.md clause 2 in code: a multi-contributor event must name a
        # different class of facts per contributor, or it is echo. Deleting this is
        # not noticed by tests/test_work_items.py, which exercises contributors
        # heavily -- the selection below is the one that dies [measured 23 Aug 2026].
        guard_id="V0-26-evidence-class",
        module="src/consilient/events.py",
        function="_check_evidence_class",
        tests=(
            f"{_V0}::test_multi_contributor_event_with_duplicate_evidence_class_is_refused",
            f"{_V0}::test_multi_contributor_event_with_case_variant_duplicate_is_refused",
            f"{_V0}::test_multi_contributor_event_with_missing_evidence_class_is_refused",
            f"{_V0}::test_multi_contributor_event_with_non_dict_contributor_is_refused",
            f"{_V0}::test_multi_contributor_event_with_non_list_contributors_is_refused",
            f"{_V0}::test_many_contributors_with_partial_duplicate_is_refused",
        ),
    ),
    Guard(
        # V0-18/V0-28: the principal's authority cannot be delegated. Three decisions
        # were filed under his name that he never made; this refusal is what makes
        # that structurally impossible rather than merely discouraged.
        guard_id="V0-28-human-authority",
        module="src/consilient/events.py",
        function="_check_human_authority",
        tests=(
            f"{_V0}::test_agent_cannot_author_a_human_decision",
            f"{_V0}::test_principal_alone_is_not_an_authority_grant",
            f"{_V0}::test_human_decision_must_record_its_channel",
            f"{_V0}::test_an_agent_cannot_author_consent_by_omitting_human_decision",
            f"{_V0}::test_untrusted_transport_cannot_deliver_an_implicit_human_verdict",
            f"{_V0}::test_a_human_decision_channel_must_be_a_non_empty_string",
        ),
    ),
    Guard(
        # Record locators and consent/retention metadata; the whole file dies on
        # deletion, so the selection stays at file granularity.
        guard_id="record-contract",
        module="src/consilient/events.py",
        function="_check_record_contract",
        tests=("tests/test_records.py",),
    ),
)


class GuardMutationError(Exception):
    """The registry, not the code under test, is wrong."""


def _find_function(
    tree: ast.Module, qualified: str
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    body: list[ast.stmt] = list(tree.body)
    node: ast.stmt | None = None
    names = qualified.split(".")
    for index, name in enumerate(names):
        node = next(
            (
                item
                for item in body
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                and item.name == name
            ),
            None,
        )
        if node is None:
            raise GuardMutationError(f"no definition named {qualified!r}")
        if index < len(names) - 1:
            if not isinstance(node, ast.ClassDef):
                raise GuardMutationError(f"{name!r} in {qualified!r} is not a class")
            body = list(node.body)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise GuardMutationError(f"{qualified!r} is not a function")
    return node


class _DeleteRaises(ast.NodeTransformer):
    def __init__(self) -> None:
        self.deleted = 0

    def visit_Raise(self, node: ast.Raise) -> ast.stmt:
        self.deleted += 1
        return ast.copy_location(ast.Pass(), node)


def delete_guard(source: str, qualified: str) -> tuple[str, int]:
    """Return the source with every `raise` in `qualified` neutralised, and the count."""
    tree = ast.parse(source)
    target = _find_function(tree, qualified)
    remover = _DeleteRaises()
    target.body = [remover.visit(statement) for statement in target.body]
    if remover.deleted == 0:
        raise GuardMutationError(
            f"{qualified!r} raises nothing; it is not a refusal, so this registry "
            "entry cannot be tested by deletion"
        )
    ast.fix_missing_locations(tree)
    return ast.unparse(tree), remover.deleted


def _pytest(
    src: Path, tests: tuple[str, ...], cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *tests,
            "-q",
            "-x",
            "-p",
            "no:cacheprovider",
            # `-o` overrides `pytest.ini`'s `pythonpath = src`, which would otherwise
            # shadow the mutant with the real tree. Measured on Windows 11 / pytest
            # 9.0.3: a backslash path here is silently not applied and every module
            # fails to import, so the value must be posix-form. If the override ever
            # stops applying, the mutant has no effect and the guard is reported as
            # SURVIVED -- this fails closed, it does not pass silently.
            "-o",
            f"pythonpath={src.as_posix()}",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        # Every gate script in .github/scripts/ scrubs GIT_* before spawning, because git exports
        # GIT_DIR and GIT_INDEX_FILE into any hook it runs and GIT_DIR overrides cwd — so a run
        # inheriting them inspects a different repository than the one it was pointed at, silently.
        # `test_gate_scripts_scrub_the_git_environment` refuses a script without it, and refused
        # this one. The subprocess here runs pytest rather than git, but the invariant is
        # deliberately blunt: a per-script exemption is how the rule erodes.
        env=GIT_ENV,
        timeout=TEST_TIMEOUT_S,
        check=False,
    )


def roundtrip(source: str) -> str:
    """Unparse the module without changing it.

    The mutant is produced by `ast.unparse`, which drops comments and normalises
    formatting. Comparing it against the tracked file would confound "the guard was
    deleted" with "unparsing broke something else", and a mutant red for the second
    reason would be scored as a kill -- a check that cannot fail. The control is
    therefore the same unparse with no raise removed, so the only delta is the guard.
    """
    return ast.unparse(ast.parse(source))


def check_registry(guards: tuple[Guard, ...] = GUARDS) -> int:
    if not guards:
        print("guard mutation check FAILED: the registry is empty")
        return 1
    failures = 0
    with tempfile.TemporaryDirectory(prefix="guard-mutation-") as scratch:
        src = Path(scratch) / "src"
        shutil.copytree(ROOT / "src", src)
        baselines: dict[tuple[str, tuple[str, ...]], bool] = {}
        for guard in guards:
            module = src / Path(guard.module).relative_to("src")
            original = module.read_text(encoding="utf-8")
            try:
                mutated, deleted = delete_guard(original, guard.function)
            except (GuardMutationError, SyntaxError) as exc:
                print(f"{guard.guard_id}: registry error: {exc}")
                failures += 1
                continue
            key = (guard.module, guard.tests)
            if key not in baselines:
                module.write_text(roundtrip(original), encoding="utf-8")
                try:
                    control = _pytest(src, guard.tests, ROOT)
                finally:
                    module.write_text(original, encoding="utf-8")
                baselines[key] = control.returncode == 0
                if control.returncode != 0:
                    print(
                        f"{guard.guard_id}: control FAILED -- {' '.join(guard.tests)} "
                        "is already red with the guard intact, so it would kill any "
                        "mutant vacuously"
                    )
            if not baselines[key]:
                failures += 1
                continue
            module.write_text(mutated, encoding="utf-8")
            try:
                result = _pytest(src, guard.tests, ROOT)
            finally:
                module.write_text(original, encoding="utf-8")
            if result.returncode == 0:
                print(
                    f"{guard.guard_id}: SURVIVED -- {guard.module}::{guard.function} "
                    f"lost {deleted} refusal(s) and {' '.join(guard.tests)} stayed green"
                )
                failures += 1
            else:
                print(
                    f"{guard.guard_id}: killed ({deleted} refusal(s) deleted, "
                    f"{len(guard.tests)} selection(s) went red)"
                )
    if failures:
        print(f"guard mutation check FAILED: {failures} of {len(guards)} guard(s)")
        return 1
    print(f"guard mutation check passes: {len(guards)} guard(s) died on deletion")
    return 0


_CONTROL_MODULE = "\n".join(
    (
        "def refuse(value):",
        "    if value < 0:",
        '        raise ValueError("negative")',
        "    return value",
        "",
    )
)

_CONTROL_TEST_EXERCISED = "\n".join(
    (
        "import pytest",
        "from control import refuse",
        "",
        "",
        "def test_refuses():",
        "    with pytest.raises(ValueError):",
        "        refuse(-1)",
        "",
    )
)

_CONTROL_TEST_BLIND = "\n".join(
    (
        "from control import refuse",
        "",
        "",
        "def test_happy_path_only():",
        "    assert refuse(1) == 1",
        "",
    )
)


def _control(scratch: Path, test_source: str) -> bool:
    """Build a one-guard project, delete the guard, and report whether it survived."""
    src = scratch / "src"
    src.mkdir(parents=True)
    module = src / "control.py"
    tests = scratch / "tests"
    tests.mkdir()
    (tests / "test_control.py").write_text(test_source, encoding="utf-8")
    mutated, deleted = delete_guard(_CONTROL_MODULE, "refuse")
    if deleted != 1:
        raise GuardMutationError(f"control mutant deleted {deleted} refusals, not 1")
    module.write_text(mutated, encoding="utf-8")
    return _pytest(src, ("tests",), scratch).returncode == 0


def self_test() -> int:
    """Prove the operator has teeth and that survival is reported, then scan."""
    with tempfile.TemporaryDirectory(prefix="guard-mutation-control-") as scratch:
        killed = not _control(Path(scratch) / "exercised", _CONTROL_TEST_EXERCISED)
        survived = _control(Path(scratch) / "blind", _CONTROL_TEST_BLIND)
    if not killed:
        print(
            "self-test FAILED: a test that exercises the guard did not notice deletion"
        )
        return 1
    if not survived:
        print("self-test FAILED: a test that never exercises the guard reported a kill")
        return 1
    print("self-test passes: deletion is detected when watched and reported when not")
    return check_registry()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="run the guard registry")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove the detector detects, then run the guard registry",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.check:
        return check_registry()
    parser.error("choose --check or --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
