from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "run: python .github/scripts/check_generated_documents.py --check"


def test_generated_document_drift_check_is_wired_into_ci():
    workflow = (ROOT / ".github" / "workflows" / "invariants.yml").read_text(
        encoding="utf-8"
    )
    step = workflow.partition("- name: Generated document drift check")[2].partition(
        "- name:"
    )[0]
    commands = [
        line.strip()
        for line in step.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert EXPECTED in commands, (
        "FAIL: documentation gates are not wired.\n"
        f"  Missing: {EXPECTED.removeprefix('run: ')}\n"
        "  A check that is not invoked is not a check. On 23 Aug 2026 that checker\n"
        "  reported adverse=2 against this tree while CI was green. Do not delete this test."
    )
