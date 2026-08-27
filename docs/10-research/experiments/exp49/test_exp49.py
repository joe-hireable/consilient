import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from run_exp49 import (
    _WindowsJob,
    _kill_process_tree,
    ROOT,
    TARGETS,
    changed_line,
    critical_paths,
    docstring_lines,
    function_at_line,
    generate_tasks,
    init_worker,
    input_manifest,
    required_experiments,
    run_mutant,
    run_pytest,
    select_manifest,
    source_hash,
    summarise,
    wilson_interval,
)


def test_statistics_and_classification_contract():
    low, high = wilson_interval(0, 10)
    assert low == 0.0 and 0.0 < high < 1.0
    assert wilson_interval(0, 0) == (0.0, 0.0)
    assert changed_line("a = 1\nb = 2\n", "a = 1\nb = 3\n") == 2
    assert docstring_lines('"""module"""\n\ndef f():\n    """function"""\n    return 1\n') == {1, 4}
    nested = "def outer():\n    def checkpoint():\n        return 1\n    return checkpoint()\n"
    assert function_at_line(nested, 3) == "checkpoint"
    assert critical_paths(
        "exp07", "acquire_lock", 78, 'payload = {"run_id": run_id}'
    ) == [
        "lock",
        "run_id",
    ]
    assert critical_paths(
        "exp45", "run_exp45_analysis", 683, 'with open(output_json_path, "w")'
    ) == ["results_write"]
    assert critical_paths(
        "exp07", "make_repo", 281, '(repo / ".gitignore").write_text(...)'
    ) == []

    mutants = [
        {
            "id": "exp07:0000",
            "target": "exp07",
            "function": "f",
            "critical_paths": [],
            "outcome": "survived",
            "docstring_only": True,
        },
        {
            "id": "exp07:0001",
            "target": "exp07",
            "function": "f",
            "critical_paths": [],
            "outcome": "survived",
            "docstring_only": False,
        },
        {
            "id": "exp07:0002",
            "target": "exp07",
            "function": "f",
            "critical_paths": [],
            "outcome": "killed",
            "docstring_only": False,
        },
    ]
    summary = summarise(mutants, {"exp07": {"outcome": "survived"}})
    rate = summary["per_target"]["exp07"]
    assert rate["equivalent"] == 1
    assert rate["unclassifiable_survivors"] == 1
    assert rate["corrected_survivors"] == 1
    assert rate["corrected_denominator"] == 2


def test_pytest_executor_can_reject(tmp_path: Path):
    test_file = tmp_path / "test_deliberate_failure.py"
    test_file.write_text("def test_bad():\n    assert 2 == 1\n", encoding="utf-8")
    result = run_pytest(tmp_path, test_file, timeout_s=10)
    assert result["outcome"] == "killed"
    assert result["returncode"] != 0


def test_real_mutant_runs_in_verified_fresh_copy():
    spec = next(target for target in TARGETS if target["name"] == "exp27_collector")
    required = required_experiments(spec["source"])
    manifest = select_manifest(input_manifest(ROOT), required)
    with ProcessPoolExecutor(
        max_workers=1,
        initializer=init_worker,
        initargs=(manifest, source_hash(Path(__file__).with_name("run_exp49.py"))),
    ) as executor:
        result = executor.submit(run_mutant, generate_tasks(spec)[0]).result(timeout=60)
    assert result["outcome"] in {"survived", "killed", "timeout"}


@pytest.mark.skipif(os.name != "nt", reason="Windows job-object regression")
def test_job_kills_descendant_after_direct_parent_exits():
    parent = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import subprocess,sys;"
                "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
                "print(child.pid,flush=True)"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    job = _WindowsJob(parent)
    assert parent.stdout is not None
    pid = int(parent.stdout.readline())
    parent.wait(timeout=5)
    assert parent.poll() == 0
    _kill_process_tree(parent, job)
    parent.communicate(timeout=5)
    probe = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    assert f'"{pid}"' not in probe.stdout
