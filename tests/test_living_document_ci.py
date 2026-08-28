import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "invariants.yml"
SPECS = ROOT / "docs" / "superpowers" / "specs"
DOCUMENTATION_STEP = "- name: Generated document drift check"
NEXT_STEP = "- name: Relative link invariant check"
EXPECTED_COMMANDS = (
    "python scripts/build_requirements.py --check",
    "python .github/scripts/check_generated_documents.py --check",
    "python .github/scripts/check_adr_trail.py",
    "python .github/scripts/check_living_documents.py --check "
    "docs/superpowers/specs/2026-08-22-*.md",
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
