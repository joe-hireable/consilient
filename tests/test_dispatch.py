from __future__ import annotations

import importlib.util
import json
import sys
import time
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path

import pytest

import consilient.dispatch as dispatch_policy
from consilient.dispatch import DispatchRefused, Harness, REGISTRY, select_harnesses
from consilient.events import EventError, read_all, validate


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"
SPEC = importlib.util.spec_from_file_location("consilient_dispatch_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SCRIPT_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCRIPT_MODULE
SPEC.loader.exec_module(SCRIPT_MODULE)


def installed(*names: str) -> dict[str, bool]:
    return {harness.name: harness.name in names for harness in REGISTRY}


@pytest.mark.parametrize("suffix", [".cmd", ".bat"])
def test_windows_batch_wrappers_are_not_dispatch_executables(suffix: str) -> None:
    if sys.platform != "win32":
        pytest.skip("Windows command-wrapper boundary")

    assert SCRIPT_MODULE.is_direct_executable(Path(f"C:/bin/harness{suffix}")) is False
    assert SCRIPT_MODULE.is_direct_executable(Path("C:/bin/harness.exe")) is True


def test_dispatch_prefers_the_pool_with_most_known_headroom() -> None:
    selected = select_harnesses(
        installed("claude", "cursor-composer", "grok", "codex")
    )

    assert [harness.name for harness in selected] == ["cursor-composer"]
    assert selected[0].headroom_percent == 99
    assert selected[0].headroom_source == "principal measurement, 2026-08-21"


def test_dispatch_never_falls_back_to_exhausted_or_unknown_headroom() -> None:
    with pytest.raises(DispatchRefused, match="no installed harness has known headroom"):
        select_harnesses(installed("claude", "codex"))


def test_explicit_exhausted_harness_is_refused_with_its_reason() -> None:
    with pytest.raises(DispatchRefused, match="nearly exhausted"):
        select_harnesses(installed("claude"), requested="claude")


def test_zero_numeric_headroom_is_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exhausted = Harness(
        "fixture",
        "fixture-family",
        "fixture-pool",
        ("fixture", "{task}"),
        100,
        "known",
        "fixture measurement",
    )
    monkeypatch.setattr(dispatch_policy, "REGISTRY", (exhausted,))

    with pytest.raises(DispatchRefused, match="no installed harness has known headroom"):
        dispatch_policy.select_harnesses({"fixture": True})


def test_fan_out_selects_two_different_model_families() -> None:
    selected = select_harnesses(
        installed("claude", "cursor-composer", "grok", "codex"), count=2
    )

    assert [harness.name for harness in selected] == ["cursor-composer", "grok"]
    assert len({harness.family for harness in selected}) == 2


def test_fan_out_runs_and_returns_both_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output_root = tmp_path / "output"
    probes = tuple(
        SCRIPT_MODULE.Probe(harness, True, harness.name, "fixture")
        for harness in REGISTRY
    )
    ran: list[str] = []

    def fake_run(
        harness: Harness, command: list[str], **kwargs: object
    ) -> dict[str, object]:
        del command, kwargs
        ran.append(harness.name)
        return {"harness": harness.name, "status": "produced"}

    monkeypatch.setattr(SCRIPT_MODULE, "OUTPUT_ROOT", output_root)
    monkeypatch.setattr(SCRIPT_MODULE, "probe_registry", lambda: probes)
    monkeypatch.setattr(SCRIPT_MODULE, "run_harness", fake_run)
    monkeypatch.setattr(
        SCRIPT_MODULE, "refuse_metered_environment", lambda *args: None
    )

    code = SCRIPT_MODULE.main(
        ["--supervised", "--fan-out", "--json", "--cwd", str(tmp_path), "task"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert ran == ["cursor-composer", "grok"]
    assert [result["harness"] for result in payload["results"]] == ran
    assert next(output_root.glob("*/brief.txt")).read_text(encoding="utf-8") == "task"


def test_cursor_shell_receives_workspace_and_task_as_arguments() -> None:
    cursor = next(harness for harness in REGISTRY if harness.name == "cursor-composer")

    assert "{cwd}" not in cursor.invocation[4]
    assert "{task}" not in cursor.invocation[4]
    assert "--trust" in cursor.invocation[4]
    assert "--help" in cursor.invocation[4]
    assert "trust=(--trust)" in cursor.invocation[4]
    assert "clean=(env -i" in cursor.invocation[4]
    assert 'exec "${clean[@]}"' in cursor.invocation[4]
    assert "CURSOR_API_KEY" not in cursor.invocation[4]
    assert "CURSOR_API_ENDPOINT" not in cursor.invocation[4]
    assert cursor.invocation[-2:] == ("{cwd}", "{brief}")


@pytest.mark.parametrize("supervised", [None, "yes"])
def test_dispatch_events_require_an_explicit_supervision_measurement(
    supervised: str | None,
) -> None:
    data = {"run_id": "run-1"}
    if supervised is not None:
        data["supervised"] = supervised
    event = {
        "v": 1,
        "ts": "2026-08-21T12:00:00+00:00",
        "event": "dispatch.started",
        "actor": "consilient.dispatch",
        "data": data,
    }

    with pytest.raises(EventError, match="supervised"):
        validate(event)


def test_dispatch_event_schema_can_record_unsupervised_after_gate_b() -> None:
    event = {
        "v": 1,
        "ts": "2026-08-21T12:00:00+00:00",
        "event": "dispatch.started",
        "actor": "consilient.dispatch",
        "data": {"run_id": "run-1", "supervised": False},
    }

    assert validate(event) == event


def test_unsupervised_dispatch_refuses_before_any_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_probe() -> None:
        raise AssertionError("unsupervised dispatch reached the execution boundary")

    monkeypatch.setattr(SCRIPT_MODULE, "probe_registry", unexpected_probe)

    with pytest.raises(SystemExit) as refused:
        SCRIPT_MODULE.main(["--cwd", str(tmp_path), "task"])

    assert refused.value.code == 2


@pytest.mark.parametrize("timeout", ["nan", "inf", "-inf", "0"])
def test_non_finite_or_non_positive_timeout_refuses_before_probe(
    timeout: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_probe() -> None:
        raise AssertionError("invalid timeout reached the execution boundary")

    monkeypatch.setattr(SCRIPT_MODULE, "probe_registry", unexpected_probe)

    with pytest.raises(SystemExit) as refused:
        SCRIPT_MODULE.main(
            ["--supervised", "--timeout", timeout, "--cwd", str(tmp_path), "task"]
        )

    assert refused.value.code == 2


def test_cursor_command_passes_an_absolute_brief_outside_shell_text() -> None:
    cursor = next(harness for harness in REGISTRY if harness.name == "cursor-composer")
    probe = SCRIPT_MODULE.Probe(cursor, True, "wsl.exe", "reachable through WSL")
    brief = Path("C:/dispatch/brief with spaces.txt")

    command = SCRIPT_MODULE.build_command(
        probe, brief, Path("C:/work tree/repository")
    )

    assert str(brief) not in command[4]
    assert command[-2:] == [
        "/mnt/c/work tree/repository",
        "Read and follow the task in /mnt/c/dispatch/brief with spaces.txt",
    ]


def test_run_captures_a_real_artefact_and_appends_trajectory(tmp_path: Path) -> None:
    grok = next(harness for harness in REGISTRY if harness.name == "grok")
    log = tmp_path / "log"
    output = tmp_path / "output"

    result = SCRIPT_MODULE.run_harness(
        grok,
        [sys.executable, "-c", "print('real artefact')"],
        task="produce an artefact",
        cwd=tmp_path,
        log_dir=log,
        output_root=output,
        timeout_s=5,
        run_id="run-success",
    )

    assert result["status"] == "produced"
    assert result["artefact_present"] is True
    assert result["verified"] is False
    assert Path(result["stdout_path"]).read_text(encoding="utf-8") == "real artefact\n"
    events, rejected = read_all(log)
    assert rejected == []
    assert [event.kind for event in events] == [
        "dispatch.started",
        "dispatch.completed",
    ]
    assert all(event.data["supervised"] is True for event in events)
    assert events[-1].data["status"] == "produced"
    assert events[-1].data["artefact_present"] is True
    assert events[-1].data["verified"] is False


def test_child_output_is_captured_as_bytes_then_decoded_safely(tmp_path: Path) -> None:
    grok = next(harness for harness in REGISTRY if harness.name == "grok")

    result = SCRIPT_MODULE.run_harness(
        grok,
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'valid\\xff')",
        ],
        task="emit non-UTF-8 output",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-bytes",
    )

    assert result["status"] == "produced"
    assert result["output"] == "valid\ufffd"
    assert Path(result["stdout_path"]).read_bytes() == "valid\ufffd".encode()


def test_workspace_trust_exit_zero_is_recorded_as_silent(tmp_path: Path) -> None:
    cursor = next(harness for harness in REGISTRY if harness.name == "cursor-composer")
    log = tmp_path / "log"

    result = SCRIPT_MODULE.run_harness(
        cursor,
        [sys.executable, "-c", "print('Workspace Trust Required')"],
        task="produce an artefact",
        cwd=tmp_path,
        log_dir=log,
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-silent",
    )

    assert result["exit_code"] == 0
    assert result["status"] == "silent"
    events, _ = read_all(log)
    assert events[-1].data["status"] == "silent"


def test_workspace_trust_nonzero_is_still_recorded_as_silent(tmp_path: Path) -> None:
    cursor = next(harness for harness in REGISTRY if harness.name == "cursor-composer")
    command = [
        sys.executable,
        "-c",
        (
            "import sys; print('Workspace Trust Required', file=sys.stderr); "
            "raise SystemExit(1)"
        ),
    ]

    result = SCRIPT_MODULE.run_harness(
        cursor,
        command,
        task="produce an artefact",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-silent-nonzero",
    )

    assert result["exit_code"] == 1
    assert result["status"] == "silent"


@pytest.mark.parametrize(
    ("harness_name", "key"),
    [("grok", "XAI_API_KEY"), ("cursor-composer", "CURSOR_API_KEY")],
)
def test_metered_vendor_key_is_refused_without_exposing_its_value(
    harness_name: str, key: str
) -> None:
    harness = next(harness for harness in REGISTRY if harness.name == harness_name)
    secret = "do-not-print-this-value"

    with pytest.raises(DispatchRefused) as refused:
        SCRIPT_MODULE.refuse_metered_environment(harness, {key: secret})

    assert secret not in str(refused.value)


def test_child_environment_drops_secrets_without_reading_them() -> None:
    class GuardedEnvironment(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            if key != "PATH":
                raise AssertionError("secret value was read")
            return "safe-path"

        def __iter__(self) -> Iterator[str]:
            return iter(
                (
                    "PATH",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "DATABASE_URL",
                    "REDIS_URL",
                    "SENTRY_DSN",
                    "HTTPS_PROXY",
                )
            )

        def __len__(self) -> int:
            return 6

    assert SCRIPT_MODULE.sanitise_environment(GuardedEnvironment()) == {
        "PATH": "safe-path"
    }


def test_console_streams_are_configured_as_utf8(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    class FakeStream:
        def reconfigure(self, *, encoding: str, errors: str) -> None:
            calls.append((encoding, errors))

    monkeypatch.setattr(SCRIPT_MODULE.sys, "stdout", FakeStream())
    monkeypatch.setattr(SCRIPT_MODULE.sys, "stderr", FakeStream())

    SCRIPT_MODULE.configure_console()

    assert calls == [("utf-8", "replace"), ("utf-8", "replace")]


def test_windows_process_is_job_owned_before_it_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":
        pytest.skip("Windows process containment invariant")
    grok = next(harness for harness in REGISTRY if harness.name == "grok")
    order: list[str] = []

    class FakeProcess:
        returncode = 0
        pid = 123
        _handle = 456

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            order.append("wait")
            return 0

        def poll(self) -> int:
            return 0

        def kill(self) -> None:
            raise AssertionError("completed fixture must not be killed")

    def fake_popen(*args: object, **kwargs: object) -> FakeProcess:
        del args
        flags = kwargs["creationflags"]
        assert isinstance(flags, int)
        assert flags & SCRIPT_MODULE.WINDOWS_CREATE_SUSPENDED
        order.append("popen-suspended")
        return FakeProcess()

    class FakeJob:
        def __init__(self, process: FakeProcess) -> None:
            del process
            order.append("job-assigned")

        def resume(self) -> None:
            order.append("resumed")

        def close(self) -> None:
            order.append("closed")

    monkeypatch.setattr(SCRIPT_MODULE.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(SCRIPT_MODULE, "_WindowsJob", FakeJob)

    SCRIPT_MODULE.run_harness(
        grok,
        ["fixture"],
        task="contain fixture",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-contained",
    )

    assert order[:4] == ["popen-suspended", "job-assigned", "resumed", "wait"]


def test_windows_tree_kill_does_not_search_for_an_external_utility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if sys.platform != "win32":
        pytest.skip("Windows process containment invariant")

    class FakeProcess:
        pid = 123
        killed = False

        def poll(self) -> int | None:
            return 1 if self.killed else None

        def kill(self) -> None:
            self.killed = True

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return 1

    def unexpected_run(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("process cleanup searched for an external utility")

    process = FakeProcess()
    monkeypatch.setattr(SCRIPT_MODULE.subprocess, "run", unexpected_run)

    SCRIPT_MODULE._kill_process_tree(process)

    assert process.killed is True


def test_windows_resume_failure_closes_the_assigned_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":
        pytest.skip("Windows process containment invariant")
    grok = next(harness for harness in REGISTRY if harness.name == "grok")
    closed: list[bool] = []

    class FakeProcess:
        returncode: int | None = None
        pid = 123
        _handle = 456

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            self.returncode = 1
            return 1

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            self.returncode = 1

    class FakeJob:
        def __init__(self, process: FakeProcess) -> None:
            del process

        def resume(self) -> None:
            raise OSError("resume failed")

        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(
        SCRIPT_MODULE.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )
    monkeypatch.setattr(SCRIPT_MODULE, "_WindowsJob", FakeJob)

    result = SCRIPT_MODULE.run_harness(
        grok,
        ["fixture"],
        task="resume fixture",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-resume-failure",
    )

    assert closed == [True]
    assert result["status"] == "unavailable"


def test_dispatch_recording_cannot_bypass_append_validation(tmp_path: Path) -> None:
    event = {
        "v": 99,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "dispatch.started",
        "actor": "consilient.dispatch",
        "data": {"supervised": True},
    }

    with pytest.raises(EventError, match="unsupported schema"):
        SCRIPT_MODULE.record_event(tmp_path, event)

    assert list(tmp_path.glob("*.jsonl")) == []


def test_timeout_kills_descendants_before_they_can_write(tmp_path: Path) -> None:
    grok = next(harness for harness in REGISTRY if harness.name == "grok")
    survived = tmp_path / "child-survived.txt"
    child = (
        "import time; from pathlib import Path; time.sleep(2); "
        f"Path({str(survived)!r}).write_text('survived', encoding='utf-8')"
    )
    parent = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(60)"
    )

    result = SCRIPT_MODULE.run_harness(
        grok,
        [sys.executable, "-c", parent],
        task="timeout fixture",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=0.5,
        run_id="run-timeout",
    )
    time.sleep(2.5)

    assert result["status"] == "timeout"
    assert not survived.exists()


def test_exited_parent_cannot_leave_a_descendant_running(tmp_path: Path) -> None:
    grok = next(harness for harness in REGISTRY if harness.name == "grok")
    survived = tmp_path / "orphan-survived.txt"
    child = (
        "import time; from pathlib import Path; time.sleep(2); "
        f"Path({str(survived)!r}).write_text('survived', encoding='utf-8')"
    )
    parent = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(0.1)"
    )

    result = SCRIPT_MODULE.run_harness(
        grok,
        [sys.executable, "-c", parent],
        task="orphan fixture",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        output_root=tmp_path / "output",
        timeout_s=5,
        run_id="run-orphan",
    )
    time.sleep(2.5)

    assert result["status"] == "silent"
    assert not survived.exists()
