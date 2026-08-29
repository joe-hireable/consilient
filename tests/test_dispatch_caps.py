"""No arm runs unbounded — and the honest account of how weak the strongest available
bound actually is.

Until the evening of 21 August 2026 this suite pinned the strict reading: refuse the
launch unless the CLI exposed both `--max-turns` and `--max-tokens` natively. Measured
against the installed CLIs, grok exposes `--max-turns` only and codex exposes neither,
so the condition could never pass for two of the three subscription harnesses — a wall,
not a gate. R11's attribution was withdrawn on the same date; the bounded-arm obligation
stands on engineering merit.

What is enforced now: where a native cap exists it is applied, and a cap the CLI does
not expose is never passed; where none exists the arm is bounded by a finite wall-clock
and a process-tree kill, `taskkill /T /F` on Windows and `os.killpg(SIGKILL)` on POSIX,
which the `run_process` tests exercise against a real sleeping child. The limits are
finite by default and the CLI rejects zero, negative and malformed values rather than
reading them as "no limit". Fan-out is here because a cap that reaches one arm and not
the other bounds nothing — both children receive the overrides.

Stated rather than implied: no installed CLI exposes a real per-run token cap, so token
bounding lives in the pool ceiling rather than per arm, and a wall-clock bound is
strictly weaker than a turn cap because an arm can burn many turns quickly inside it."""

from family_source import seam

import sys
from pathlib import Path
import pytest
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    Harness,
    harness_by_id,
    select_fanout,
)
from dispatch_helpers import (
    CAP_HELP,
    INSTALLED,
    _load_script,
)


def _stub_harness_commands(monkeypatch, script) -> None:
    monkeypatch.setattr(seam("dispatch_launch"), "find_claude", lambda: "claude")
    monkeypatch.setattr(seam("dispatch_evidence"), "find_grok", lambda: "grok")
    monkeypatch.setattr(seam("dispatch_launch"), "find_codex", lambda: "codex")
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_evidence"), "metered_grok_reason", lambda: None)
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)


def test_run_process_writes_an_artefact_file(tmp_path):
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, _duration, _timing = script.run_process(
        [sys.executable, "-c", "print('pong')"],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=20,
    )
    assert timed_out is False
    assert code == 0
    assert "pong" in stdout_path.read_text(encoding="utf-8")


def test_run_process_kills_a_sleeping_child(tmp_path):
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, duration, _timing = script.run_process(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=2,
    )
    assert timed_out is True
    assert duration < 15
    assert code != 0 or timed_out


def test_cap_defaults_are_finite_and_cli_overrides_are_honoured():
    script = _load_script()
    parser = script.build_parser()

    defaults = parser.parse_args(["noop"])
    assert defaults.max_turns == script.DEFAULT_MAX_TURNS > 0
    assert defaults.max_tokens == script.DEFAULT_MAX_TOKENS > 0
    assert defaults.timeout == script.DEFAULT_TIMEOUT_S > 0

    overridden = parser.parse_args(
        ["noop", "--max-turns", "7", "--max-tokens", "1234", "--timeout", "9"]
    )
    assert (overridden.max_turns, overridden.max_tokens, overridden.timeout) == (
        7,
        1234,
        9,
    )


@pytest.mark.parametrize("flag", ("--max-turns", "--max-tokens", "--timeout"))
@pytest.mark.parametrize("value", ("0", "-1", "malformed"))
def test_finite_limit_cli_rejects_non_positive_or_malformed_values(flag, value):
    script = _load_script()
    with pytest.raises(SystemExit):
        script.build_parser().parse_args(["noop", flag, value])


@pytest.mark.parametrize("harness_id", tuple(item.id for item in HARNESSES))
def test_every_harness_command_carries_both_native_caps(
    monkeypatch, tmp_path, harness_id
):
    """Mutation target: deleting either cap from any harness command fails this test."""
    script = _load_script()
    _stub_harness_commands(monkeypatch, script)
    harness = harness_by_id(harness_id)
    assert harness is not None

    built = script.build_command(
        harness,
        task="noop",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="composer-2.5" if harness_id == "cursor-composer" else None,
        max_turns=7,
        max_tokens=1234,
    )

    assert isinstance(built, list)
    command = " ".join(str(part) for part in built)
    assert "--max-turns 7" in command
    assert "--max-tokens 1234" in command


@pytest.mark.parametrize("harness_id", tuple(item.id for item in HARNESSES))
def test_every_harness_applies_the_native_caps_its_cli_actually_exposes(
    monkeypatch, tmp_path, harness_id
):
    """R11 obliges that no arm runs UNBOUNDED. It does not oblige a flag spelling.

    R11's attribution was withdrawn on 21 August 2026; the bounded-arm obligation remains
    on engineering merit.

    Until that evening this suite pinned the stricter reading -- refuse the launch unless the
    CLI exposed BOTH `--max-turns` and `--max-tokens` natively. Measured against the installed
    CLIs: grok exposes `--max-turns` only, codex exposes neither. So the condition could never
    pass for two of the three subscription harnesses, and the harness had locked itself out of
    two of the plans it exists to spend -- a wall, not a gate, and in direct conflict with the
    principal's standing instruction to use every subscription.

    The obligation is still enforced. Where a native cap exists it is applied, asserted here.
    Where it does not, the arm is bounded by the wall-clock timeout and the process-tree kill
    in `run_process`, asserted by `test_an_arm_without_a_native_cap_is_still_bounded`.

    Not achieved, and stated rather than implied: no installed CLI exposes a real per-run token
    cap, so token bounding lives in the pool ceiling rather than per arm; and a wall-clock bound
    is strictly weaker than a turn cap, since an arm can burn many turns quickly inside it.
    """
    script = _load_script()
    _stub_harness_commands(monkeypatch, script)
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: "--max-turns <N>")
    harness = harness_by_id(harness_id)
    assert harness is not None

    built = script.build_command(
        harness,
        task="noop",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="composer-2.5" if harness_id == "cursor-composer" else None,
    )

    assert not isinstance(built, str), (
        f"{harness_id} refused a launch it can bound: {built}"
    )
    command = " ".join(built)
    assert "--max-turns" in command, "the native cap on offer was not applied"
    assert "--max-tokens" not in command, (
        "a cap the CLI does not expose must not be passed"
    )


def test_an_arm_without_a_native_cap_is_still_bounded(monkeypatch, tmp_path):
    """The fallback bound is what makes the change above honest rather than a loosening.

    A CLI exposing no cap flag at all must still be launched under a finite wall-clock, and
    `run_process` must kill the process tree when it expires -- `taskkill /T /F` on Windows,
    `os.killpg(SIGKILL)` on POSIX. Without this, dropping the native-flag requirement would
    genuinely leave arms unbounded and R11 would be unmet.
    """
    script = _load_script()
    _stub_harness_commands(monkeypatch, script)
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: "no cap flags here")
    harness = harness_by_id("codex")
    assert harness is not None

    built = script.build_command(
        harness, task="noop", cwd=tmp_path, brief=tmp_path / "brief.md", model=None
    )
    assert not isinstance(built, str), f"a bounded launch was refused: {built}"
    command = " ".join(built)
    assert "--max-turns" not in command and "--max-tokens" not in command

    # The whole family: `run_process` and its wall-clock bound moved to dispatch_launch.py in
    # the 28 August 2026 split, so reading the entry point alone found neither.
    source = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(Path(script.__file__).parent.glob("dispatch*.py"))
    )
    assert "subprocess.TimeoutExpired" in source, "no wall-clock bound in run_process"
    assert "taskkill" in source, "no Windows process-tree kill"
    assert "killpg" in source, "no POSIX process-group kill"


def test_fanout_plumbs_cap_overrides_to_both_children(tmp_path, monkeypatch):
    script = _load_script()
    seen: list[tuple[int, int]] = []

    def fake_run(harness: Harness, **kwargs):
        seen.append((kwargs["max_turns"], kwargs["max_tokens"]))
        return script.RunResult(
            harness=harness,
            status="ok",
            reason="produced an artefact",
            exit_code=0,
            stdout="pong\n",
            stderr="",
            artefact_bytes=5,
            diff_bytes=0,
            timed_out=False,
            duration_s=0.1,
            command=("agent", "--max-turns", "7", "--max-tokens", "1234"),
            run_id=kwargs["run_id"],
            stdout_path=str(tmp_path / "stdout.txt"),
            stderr_path=str(tmp_path / "stderr.txt"),
        )

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", fake_run)
    payload, code = script.dispatch_fanout(
        decision=select_fanout(probes=INSTALLED, pools=DEFAULT_POOLS),
        task="pong",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        max_turns=7,
        max_tokens=1234,
    )

    assert code == 0
    assert payload["status"] == "agree"
    assert seen == [(7, 1234), (7, 1234)]
