import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "invariants.yml"
SPECS = ROOT / "docs" / "superpowers" / "specs"
DOCUMENTATION_STEP = "- name: Generated document drift check"
NEXT_STEP = "- name: Relative link invariant check"
# C4 of the surfaces plan. It is a separate step so a red C1 block still
# reports broken links (`if: ${{ !cancelled() }}`). C0 must pin it anyway:
# using NEXT_STEP only as a delimiter left C4 deletable with this file green.
C4 = "python .github/scripts/check_links.py --self-test"
EXPECTED_COMMANDS = (
    "python scripts/build_requirements.py --check",
    "python .github/scripts/check_generated_documents.py --check",
    "python .github/scripts/check_adr_trail.py",
    "python .github/scripts/check_living_documents.py --check "
    "docs/superpowers/specs/2026-08-22-*.md",
    # The file-length ratchet. Listed here so the gate cannot be silently unwired --
    # which is exactly the finding unit W07 raised about check_links.
    "python .github/scripts/check_file_length.py",
    # The per-FUNCTION ratchet (ADR-0111), and its self-test, which runs first so a broken
    # checker is caught before its verdict is trusted. This half is the one worth protecting
    # from a silent unwiring: a size rule enforced on files alone is satisfied by a facade
    # split that leaves every function exactly as long as it was.
    "python .github/scripts/check_function_size.py --self-test",
    "python .github/scripts/check_function_size.py",
)
WEEKLY_CRON = re.compile(
    r"(?m)^  schedule:\n    - cron: ['\"]\d+ \d+ \* \* [0-6]['\"]$"
)
UNWIRED_GATE = (
    "FAIL: documentation gates are not wired.\n"
    "  Missing: {missing}\n"
    "  A check that is not invoked is not a check. On 23 Aug 2026 that checker\n"
    "  reported adverse=2 against this tree while CI was green. Do not delete this test."
)


def _active_python_commands(workflow: str) -> list[str]:
    """``run:`` bodies and ``run: |`` lines, skipping comments.

    A commented-out invocation is not an invocation. Scanning the raw file
    would treat ``# run: python ...`` as wired, which is how a gate is
    deleted while the suite stays green.
    """
    commands: list[str] = []
    for raw in workflow.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        body = stripped.removeprefix("run: ").strip()
        if body.startswith("python "):
            commands.append(body)
    return commands


def _contract_errors(workflow: str, specs: list[Path]) -> list[str]:
    errors: list[str] = []
    documentation = workflow.partition(DOCUMENTATION_STEP)[2].partition(NEXT_STEP)[0]
    gate = documentation.partition("- name:")[0]
    commands = tuple(
        line.strip().removeprefix("run: ")
        for line in gate.splitlines()
        if line.strip().removeprefix("run: ").startswith("python ")
    )
    triggers = workflow.partition("\njobs:")[0]
    if "pull_request:" not in triggers or "push:" not in triggers:
        errors.append("existing pull_request/push triggers were removed")
    if WEEKLY_CRON.search(triggers) is None:
        errors.append("missing weekly schedule")
    if commands != EXPECTED_COMMANDS:
        missing = [command for command in EXPECTED_COMMANDS if command not in commands]
        if missing:
            errors.append(UNWIRED_GATE.format(missing=missing[0]))
        else:
            errors.append("documentation invocations are missing or reordered")
    if "run: |" not in gate or "shell:" in gate or "continue-on-error:" in gate:
        errors.append("documentation checks are not one fail-fast shell step")
    if len(specs) != 21:
        errors.append(f"expected 21 admitted specifications, found {len(specs)}")
    # C4 is a sibling step, not a line in the fail-fast block. Pin it on the
    # whole workflow so deleting that step fails this file — the surfaces-plan
    # C0 contract, and the hole W07 measured.
    active = _active_python_commands(workflow)
    c1 = EXPECTED_COMMANDS[1]
    if C4 not in active:
        errors.append(UNWIRED_GATE.format(missing=C4))
    elif c1 in active and active.index(C4) < active.index(c1):
        errors.append(
            "FAIL: documentation gates are reordered.\n"
            "  Required order: "
            + c1
            + ", "
            + C4
            + "\n"
            "  A check that is not invoked is not a check. On 23 Aug 2026 that checker\n"
            "  reported adverse=2 against this tree while CI was green. Do not delete this test."
        )
    return errors


def _live_inputs() -> tuple[str, list[Path]]:
    return WORKFLOW.read_text(encoding="utf-8"), sorted(SPECS.glob("2026-08-22-*.md"))


def test_live_workflow_enforces_the_admitted_documentation_surface() -> None:
    workflow, specs = _live_inputs()
    assert _contract_errors(workflow, specs) == []


def test_removing_or_reordering_each_invocation_fails() -> None:
    workflow, specs = _live_inputs()
    for index, command in enumerate(EXPECTED_COMMANDS):
        assert _contract_errors(workflow.replace(command, "", 1), specs)
        if index == len(EXPECTED_COMMANDS) - 1:
            continue
        following = EXPECTED_COMMANDS[index + 1]
        swapped = workflow.replace(command, "__COMMAND__", 1)
        swapped = swapped.replace(following, command, 1)
        swapped = swapped.replace("__COMMAND__", following, 1)
        assert _contract_errors(swapped, specs)


def test_moving_command_to_second_step_fails() -> None:
    workflow, specs = _live_inputs()
    command = EXPECTED_COMMANDS[3]
    moved = workflow.replace(
        f"          {command}\n",
        "      - name: Settled record ratchet\n"
        "        if: ${{ !cancelled() }}\n"
        f"        run: {command}\n",
        1,
    )
    assert moved.count(NEXT_STEP) == 1
    assert _contract_errors(moved, specs)


def test_one_file_short_inventory_fails() -> None:
    workflow, specs = _live_inputs()
    assert len(specs) == 21
    assert _contract_errors(workflow, specs[:-1])


def test_removing_the_weekly_schedule_fails() -> None:
    workflow, specs = _live_inputs()
    schedule = re.search(r"(?m)^  schedule:\n    - cron: [^\n]+\n", workflow)
    assert schedule is not None
    without_schedule = workflow[: schedule.start()] + workflow[schedule.end() :]
    assert _contract_errors(without_schedule, specs)


def test_removing_an_existing_trigger_fails() -> None:
    workflow, specs = _live_inputs()
    without_pull = workflow.replace("  pull_request:\n", "", 1)
    without_push = workflow.replace("  push:\n", "", 1)
    assert _contract_errors(without_pull, specs)
    assert _contract_errors(without_push, specs)


def test_removing_the_link_gate_fails_the_suite() -> None:
    """C0: deleting C4 must fail. W07 measured that it currently does not.

    Plan C0 inspects invariants.yml and fails if any of C1–C4 is absent. C1 is
    already pinned inside the documentation block. C4 lives in the *next* step,
    which this file used only as a delimiter, so deleting the Relative link
    invariant check left `_contract_errors == []`.
    """
    workflow, specs = _live_inputs()
    assert C4 in workflow
    deleted_step = workflow.replace(NEXT_STEP, "- name: Deleted link gate", 1).replace(
        C4, "true", 1
    )
    errors = _contract_errors(deleted_step, specs)
    assert errors, (
        "deleting C4 left the documentation-gate contract green; "
        "a check that is not invoked is not a check"
    )
    assert any(C4 in error for error in errors)
    assert any("Do not delete this test." in error for error in errors)


def test_commenting_out_the_link_gate_fails_the_suite() -> None:
    workflow, specs = _live_inputs()
    commented = workflow.replace(
        f"        run: {C4}",
        f"        # run: {C4}",
        1,
    )
    errors = _contract_errors(commented, specs)
    assert errors
    assert any(C4 in error for error in errors)


def test_reordering_c4_before_c1_fails_the_suite() -> None:
    workflow, specs = _live_inputs()
    c1 = EXPECTED_COMMANDS[1]
    swapped = (
        workflow.replace(c1, "__DOC_GATE_PLACEHOLDER__", 1)
        .replace(C4, c1, 1)
        .replace("__DOC_GATE_PLACEHOLDER__", C4, 1)
    )
    errors = _contract_errors(swapped, specs)
    assert errors
    assert any(
        "reordered" in error or C4 in error or c1 in error for error in errors
    )
