"""S02 — the child process that runs a candidate: isolation, timeout and the kill path.

These pin `scripts/promote_loop.py`'s runner rather than the sealed instrument above it,
which is why they stand apart: the subject is process mechanics, and the failures are
the runner handing back a result it had no right to. A candidate that walks its parent's
stack frames must not find the expected answers there — it scores zero, because the
answers are not in the process it runs in. A candidate that spawns a grandchild and then
sleeps must be killed with its whole tree, and the marker file is the proof: a
`subprocess` timeout does not kill grandchildren, so the parent returning promptly would
look identical to success while the descendant carried on writing.

The Windows fallback is here for the same reason. When `taskkill` itself hangs, the
runner must still kill the direct child rather than wait on a tree-kill that will never
return. And a child that emits malformed output and exits must produce a clean
`ran=False`, not an exception in the parent that ends the run."""

import os
import subprocess
import time
from pathlib import Path
import pytest
from promote_instrument_helpers import (
    _loop_module,
)


def _loop_execute():
    return _loop_module().execute


def test_candidate_runs_in_another_process_without_parent_expected_answers():
    source = """
def solve(prompt):
    if prompt == "pid":
        return str(__import__("os").getpid())
    frame = __import__("sys")._getframe()
    while frame is not None:
        for value in frame.f_locals.values():
            if isinstance(value, (list, tuple)):
                for item in value:
                    if (
                        isinstance(item, (list, tuple))
                        and len(item) == 2
                        and item[0] == prompt
                    ):
                        return str(item[1])
        frame = frame.f_back
    return "expected-answer-not-found"
"""
    ran, score = _loop_execute()(
        source,
        [("pid", str(os.getpid())), ("sealed prompt", "sealed expected answer")],
    )
    assert ran is True
    assert score == 0.0


def test_candidate_timeout_kills_descendant_process_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = _loop_module()
    monkeypatch.setattr(module, "EXECUTION_TIMEOUT_SECONDS", 0.2)
    marker = tmp_path / "survived.txt"
    grandchild = (
        "import pathlib,time; time.sleep(0.8); "
        f"pathlib.Path({str(marker)!r}).write_text('survived', encoding='utf-8')"
    )
    source = f"""
def solve(prompt):
    subprocess = __import__("subprocess")
    sys = __import__("sys")
    subprocess.Popen([sys.executable, "-c", {grandchild!r}])
    __import__("time").sleep(60)
"""
    started = time.monotonic()
    ran, score = module.execute(source, [("prompt", "answer")])
    assert ran is False
    assert score == 0.0
    assert time.monotonic() - started < 5
    time.sleep(1)
    assert not marker.exists()


def test_hung_windows_taskkill_falls_back_to_direct_child_kill(monkeypatch):
    module = _loop_module()

    class Windows:
        name = "nt"

    class Process:
        pid = 123
        killed = False

        def poll(self):
            return None

        def kill(self):
            self.killed = True

    def hung_taskkill(argv, *, timeout, **kwargs):
        raise subprocess.TimeoutExpired(argv, timeout)

    process = Process()
    monkeypatch.setattr(module, "os", Windows())
    monkeypatch.setattr(module.subprocess, "run", hung_taskkill)
    module._kill_process_tree(process)
    assert process.killed is True


def test_candidate_cannot_crash_parent_with_malformed_child_output():
    source = """
__import__("sys").stdout.write("[]")
__import__("sys").stdout.flush()
__import__("os")._exit(0)
"""
    ran, score = _loop_execute()(source, [("prompt", "answer")])
    assert ran is False
    assert score == 0.0
