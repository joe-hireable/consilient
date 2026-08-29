"""The artefacts A1, B1, B2 and B3 read: the experiment register and the dated fallback
result. B2 and B3 were given success criteria by ADR-0045 and ADR-0046 on the day the
unpassable-condition audit was written, and the shape of both amendments is that
malformed or missing evidence FAILS rather than reporting `unknown` — `unknown` is the
status that made them walls in the first place, a placeholder that reads like
outstanding work, and a result nobody can parse is not an open question. A green result
from a month ago is evidence about a month ago, so a fallback fifteen days old fails:
two missed weekly cycles, and the failure mode guarded against is a workflow that
silently stopped running while its last result stayed green. Under Joe's no-secrets rule
the exercise can never run in this repository's CI, so the gate stopped having an
opinion about GitHub Actions and reads the dated result instead, refusing a forged
command or runner and a timestamp with no offset. B2 no longer reads the repository's
own β at all: thirty repository-wide human rejections are not critic-recall evidence,
and requiring an explicit `critic-beta-measured:` marker makes that substitution
structurally impossible rather than merely refused, while a point outside its own
interval — a transcription error in the register — must not become a passing gate. A1
fails on a fired stopping rule even when the entry says DONE, and on an interval half-
width above 0.05. The two runner tests hold producer and consumer together, because
`scripts/run_fallback.py` and `_fallback_condition` live in different files and run in
different places, sharing only a JSON shape, so a renamed key would fail B3 permanently
and the cause would be a keystroke."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from v0_invariants_helpers import (
    _gate_b,
    _spend_scripts,
    append_judged,
    doctor_payload,
    write_capture_days,
)


def test_doctor_fails_the_unbuilt_weekly_fallback(tmp_path, capsys, monkeypatch):
    """Amended by ADR-0046. The evidence path changed; the assertion did not weaken.

    This used to assert the condition cites `.github/workflows`. Under Joe's no-secrets rule
    the exercise can never run in this repository's CI, so the gate stopped having an opinion
    about GitHub Actions and reads the dated result instead. An absent result still FAILS —
    never `unknown`, which is the status that made B3 a wall in the first place.
    """
    # Isolate from the repository's own result file. Since 20 Aug 2026 a real passing result
    # exists at the repository root, so without this the test reads it and B3 passes — the
    # test was only ever green because the artefact did not exist yet.
    monkeypatch.chdir(tmp_path)
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][2]

    assert condition["id"] == "B3" and condition["status"] == "fail"
    assert ".harness/fallback-result.json" in condition["evidence"]
    assert "never recorded one" in condition["reason"]


def test_doctor_reads_the_wrapped_exp05_result_as_pass(tmp_path, capsys):
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][0]

    assert condition["id"] == "B1" and condition["status"] == "pass"


def test_doctor_does_not_substitute_repository_beta_for_exp08(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text("### EXP-08 · Critic recall `DONE`\n", encoding="utf-8")
    log = tmp_path / "log" / "2026-08-20.jsonl"
    for index in range(30):
        append_judged(log, f"critic-{index}", f"t{index}", False, "reject")

    payload = doctor_payload(tmp_path, capsys)
    condition = payload["gates"]["B"]["conditions"][1]

    # Amended by ADR-0045. The intent is unchanged and now stronger: thirty repository-wide
    # human rejections are not critic-recall evidence and must not satisfy B2. Previously the
    # condition read the repository beta and reported `unknown`; it no longer reads it at all
    # and requires an explicit `critic-beta-measured:` marker, so the substitution the test
    # guards against is now structurally impossible rather than merely refused.
    assert condition["id"] == "B2" and condition["status"] == "fail"
    assert "records no `critic-beta-measured" in condition["reason"]
    assert payload["routing_orchestration_enabled"] is False


def _b3_world(tmp_path, result):
    """A workspace carrying a given fallback result.

    ADR-0046 removed the schedule-trigger half. The exercise cannot run in this repository's
    CI at all — that would need a secret in a public repository — and a schedule trigger was
    only ever a proxy for "this runs regularly". A result dated inside the window cannot be
    produced without something having run, so the dated result is the whole of the evidence.
    """
    if result is not None:
        harness = tmp_path / ".harness"
        harness.mkdir(parents=True, exist_ok=True)
        (harness / "fallback-result.json").write_text(
            result if isinstance(result, str) else json.dumps(result), encoding="utf-8"
        )
    write_capture_days(tmp_path / "log", "2026-08-20")


def _fallback(days_old, outcome="pass"):
    stamped = datetime.now(timezone.utc) - timedelta(days=days_old)
    from consilient.cli import EXPECTED_FALLBACK_COMMAND, FALLBACK_RUNNER_IDENTITY

    return {
        "ts": stamped.isoformat(),
        "command": EXPECTED_FALLBACK_COMMAND,
        "outcome": outcome,
        "runner": FALLBACK_RUNNER_IDENTITY,
        "run": "https://example.invalid/run/1",
    }


def test_b3_passes_on_a_recent_passing_fallback(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(2))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "pass", condition["reason"]
    assert "2 day(s) ago and passed" in condition["reason"]


def test_b3_fails_on_a_stale_fallback(tmp_path, capsys, monkeypatch):
    """Fifteen days is two missed weekly cycles. ADR-0045 names this case explicitly.

    A green result from a month ago is evidence about a month ago. The failure mode this
    guards is a workflow that silently stopped running while its last result stayed green.
    """
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(15))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "15 days old" in condition["reason"]


def test_b3_fails_when_the_fallback_itself_failed(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(1, outcome="fail"))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "'fail'" in condition["reason"]


def test_b3_fails_on_an_unreadable_or_undated_fallback(tmp_path, capsys, monkeypatch):
    """Malformed evidence FAILS rather than reporting unknown.

    `unknown` was the status that made B2 and B3 unpassable in the first place: a placeholder
    that reads like outstanding work. A result nobody can parse is not an open question.
    """
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, "{not json}")
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "unreadable" in condition["reason"]


def test_b3_fails_when_the_result_timestamp_has_no_offset(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    payload = _fallback(1)
    payload["ts"] = "2026-08-20T06:00:00"
    _b3_world(tmp_path, payload)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "offset" in condition["reason"]


def test_b2_passes_on_a_recorded_critic_beta(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `DONE 21 Aug 2026`\n"
        "critic-beta-measured: 0.31 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert condition["status"] == "pass", condition["reason"]
    assert "0.31" in condition["reason"]


def test_b2_fails_when_the_recorded_point_is_outside_its_own_interval(
    tmp_path, capsys, monkeypatch
):
    """A transcription error in the register must not become a passing gate."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `DONE 21 Aug 2026`\n"
        "critic-beta-measured: 0.91 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert (
        condition["status"] == "fail"
        and "outside its own interval" in condition["reason"]
    )


# ---------------------------------------------------------------- ADR-0046
def test_the_fallback_runner_and_the_gate_agree_on_the_result_shape(
    tmp_path, capsys, monkeypatch
):
    """Producer and consumer must not drift, and nothing else would notice if they did.

    `scripts/run_fallback.py` writes the result and `_fallback_condition` reads it. They live
    in different files, run in different places — one on the principal's machine, one in CI —
    and share only a JSON shape. A renamed key would make B3 fail permanently with a message
    about unreadable evidence, and the cause would be a keystroke.

    This builds the result by executing the runner's own writer code path against a stubbed
    command, then asserts the gate reads it as a pass.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_fallback", Path("scripts/run_fallback.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    monkeypatch.setattr(runner, "run", lambda: ("pass", "stubbed"))
    monkeypatch.setattr(
        runner, "RESULT", tmp_path / ".harness" / "fallback-result.json"
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["run_fallback.py"])
    assert runner.main() == 0
    capsys.readouterr()  # the runner prints; drain it so doctor's JSON stands alone

    write_capture_days(tmp_path / "log", "2026-08-20")
    monkeypatch.chdir(tmp_path)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "pass", condition["reason"]


def test_the_fallback_runner_records_a_failure_rather_than_crashing(
    tmp_path, monkeypatch
):
    """A broken fallback is a measurement. It must not look like a broken script.

    If the runner exited non-zero on a failed exercise, a scheduler would treat the evidence
    as an error and — depending on how it is wired — retry it, alert on it, or drop it. The
    result file is the output; the exit code is not.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_fallback_fail", Path("scripts/run_fallback.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    result_path = tmp_path / ".harness" / "fallback-result.json"
    monkeypatch.setattr(
        runner, "run", lambda: ("fail", "the `claude` executable is not on PATH")
    )
    monkeypatch.setattr(runner, "RESULT", result_path)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["run_fallback.py"])

    assert runner.main() == 0, "a failed fallback must not exit non-zero"
    recorded = json.loads(result_path.read_text(encoding="utf-8"))
    assert recorded["outcome"] == "fail"
    assert "not on PATH" in recorded["detail"]


# ---------------------------------------------------------------- Audit Fixes (ADR-0043, ADR-0045, ADR-0046, ADR-0039)
def test_gate_a1_fails_when_exp01_stopping_rule_fired(tmp_path, capsys, monkeypatch):
    """Gate A1 must fail if EXP-01 stopping rule fired, even if status is DONE."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE: stopping rule FIRED: history mining could not narrow interval`\n"
        "beta-measured: 0.3132 [0.2800, 0.3464]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "fail", condition["reason"]
    assert "stopping rule fired" in condition["reason"].lower()


def test_gate_a1_fails_when_interval_half_width_exceeds_tolerance(
    tmp_path, capsys, monkeypatch
):
    """Gate A1 must fail if EXP-01 beta interval half-width is > 0.05."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE 20 Aug 2026`\n"
        "beta-measured: 0.3132 [0.1500, 0.4500]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "fail", condition["reason"]
    assert "exceeds" in condition["reason"] and "0.05" in condition["reason"]


def test_gate_a1_passes_when_usable_interval_recorded(tmp_path, capsys, monkeypatch):
    """Gate A1 passes when EXP-01 is DONE and carries a usable interval (half-width <= 0.05)."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE 20 Aug 2026`\n"
        "beta-measured: 0.3132 [0.2800, 0.3464]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "pass", condition["reason"]
    assert "0.3132" in condition["reason"]


def test_gate_b2_fails_when_exp08_not_done(tmp_path, capsys, monkeypatch):
    """Gate B2 must fail if EXP-08 is not DONE, even if a measurement tag exists."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `IN PROGRESS`\n"
        "critic-beta-measured: 0.31 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert condition["status"] == "fail", condition["reason"]
    assert "must be DONE" in condition["reason"]


def test_b3_fails_on_unexpected_command_or_runner(tmp_path, capsys, monkeypatch):
    """Gate B3 fails if fallback result JSON has forged command or runner."""
    monkeypatch.chdir(tmp_path)

    # Wrong command
    bad_cmd = _fallback(1)
    bad_cmd["command"] = "claude -p 'do something else'"
    _b3_world(tmp_path, bad_cmd)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "unexpected command" in condition["reason"]

    # Wrong runner
    bad_runner = _fallback(1)
    bad_runner["runner"] = "scripts/forged_runner.py"
    _b3_world(tmp_path, bad_runner)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "unexpected runner" in condition["reason"]


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)
