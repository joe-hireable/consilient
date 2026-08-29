"""The operator surface: what `consil` exposes, what it prints, and what it hands back
to `$?`. The scope test asserts the command set exactly, so that surface growth is a
decision someone had to make here, and it inspects the parser rather than the help
prose, because the description legitimately contains "route" while saying the tool does
not do it; the loop runtime is checked against the same set, since Stage 3 permits
building it but does not put it behind `consil`. The doctor exit-code tests exist
because `consil doctor` printed `Gate A: FAIL` and exited 0 until 21 August 2026:
`main()` returned `0 if result.get("identical", True) else 1` and `cmd_doctor`'s result
carries no `identical` key, so every invocation returned 0 whatever the gates said —
ADR-0015 calls this command "not advisory", and a command whose failure a caller cannot
read from `$?` is advisory. The exit code is tested in both directions so that it is a
report rather than a constant, and a locked state database must surface as one line on
stderr with a non-zero code rather than a stack trace. The packaging tests pin a second
install-time defect from the same day: `pip install .` failed on a clean machine because
neither `pyproject.toml` nor `setup.py` existed, so the `consil` entry point that
thirty-odd documents refer to could not be installed by anyone, and the declared Python
floor must not drift from the one mypy type-checks against."""

import argparse
import json
import sys
from pathlib import Path
import pytest
from consilient import projection
from consilient import cli_replay
from consilient.cli import build_parser, main
from v0_invariants_helpers import (
    _spend_scripts,
    append_judged,
    write_capture_days,
)


# ---------------------------------------------------------------- V0-14
def test_human_output_renders_the_same_result_as_json(tmp_path, capsys):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
    argv = ["--log", str(log_dir), "--db", str(db), "beta"]

    assert main(argv + ["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert main(argv) == 0
    human = capsys.readouterr().out.strip()

    assert str(payload["n_rejected"]) in human
    assert payload["verdict"] == "insufficient_data"
    assert "insufficient data" in human


def test_cli_rejects_an_invalid_event_with_a_nonzero_exit(tmp_path, capsys):
    bad = json.dumps(
        {
            "v": 99,
            "ts": "2026-08-20T01:00:00+01:00",
            "event": "x",
            "actor": "a",
            "data": {},
        }
    )
    code = main(["--log", str(tmp_path), "record", "--event", bad, "--json"])
    assert code == 2
    assert "unsupported schema version" in capsys.readouterr().err


# ---------------------------------------------------------------- scope
def test_the_cli_exposes_no_routing_or_blocking_surface():
    """Stage 3 needs Gate B. The CLI exposes no labelled connector control surface.

    This inspects the parser surface rather than the help prose: the description
    legitimately contains "route" while saying the tool does not do it.
    """
    parser = build_parser()
    actions = {a.dest for a in parser._actions}
    subparsers = next(
        (a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None
    )
    assert subparsers is not None
    commands = set(subparsers.choices)
    for sub in subparsers.choices.values():
        actions |= {a.dest for a in sub._actions}

    # `dashboard` added 21 Aug 2026 by ADR-0053. It renders and writes one HTML file;
    # it accepts nothing, routes nothing and blocks nothing, so it passes the
    # forbidden-verb check below on its own merits rather than by exemption. The exact
    # set is asserted so that surface growth is a decision someone had to make here.
    assert commands == {"record", "replay", "beta", "doctor", "dashboard", "usage"}, (
        commands
    )
    for forbidden in (
        "route",
        "dispatch",
        "block",
        "accept",
        "gate",
        "escalate",
        "connector",
        "mcp",
        "admit",
        "admission",
        "invoke",
    ):
        offenders = {x for x in actions | commands if forbidden in x}
        assert not offenders, f"observe-only CLI exposes {offenders}"

    for forbidden_argv in (
        ["connector"],
        ["doctor", "--connector", "x"],
        ["replay", "--admission", "x"],
        ["beta", "--invoke", "x"],
        ["record", "--mcp", "x", "--event", "{}"],
    ):
        with pytest.raises(SystemExit) as refused:
            parser.parse_args(forbidden_argv)
        assert refused.value.code == 2


def test_shared_options_survive_on_either_side_of_the_command(tmp_path, capsys):
    """argparse `parents=` lets a subparser default clobber an already-parsed value.

    Before this was fixed, `--log X replay` silently reverted to the default log
    directory and replayed the wrong trajectory.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
    projection.build(log_dir, db).close()  # give `replay` something to compare against

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 0
    before = json.loads(capsys.readouterr().out)

    assert main(["replay", "--log", str(log_dir), "--db", str(db), "--json"]) == 0
    after = json.loads(capsys.readouterr().out)

    assert before["events"] == after["events"] == 2
    assert before["digest"] == after["digest"]


# ------------------------------------------- packaging and exit codes, 21 August 2026
# `pip install .` failed on a clean machine: neither `pyproject.toml` nor `setup.py`
# existed, so the `consil` entry point that `packages/consil/README.md` and thirty-odd
# documents refer to could not be installed by anyone. These pin the repair.


def _pyproject() -> dict:
    import tomllib

    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_the_consil_entry_point_resolves_to_a_real_callable():
    """A declared console script that does not import is a broken install, not a typo."""
    import importlib

    target = _pyproject()["project"]["scripts"]["consil"]
    module_name, _, attribute = target.partition(":")
    assert module_name and attribute, f"malformed entry point {target!r}"
    resolved = getattr(importlib.import_module(module_name), attribute)
    assert callable(resolved), f"{target} is not callable"


def test_the_declared_python_floor_matches_mypy():
    """Two files state the supported interpreter. They must not drift apart.

    `requires-python` is what pip enforces on a stranger's machine; `python_version` in
    mypy.ini is what the type checker assumes. If the floor is lowered in one and not the
    other, the gate type-checks against a version pip will not install on.
    """
    declared = _pyproject()["project"]["requires-python"]
    assert declared.startswith(">="), f"floor {declared!r} is not a simple lower bound"
    floor = declared.removeprefix(">=").strip()
    mypy_ini = Path("mypy.ini").read_text(encoding="utf-8")
    assert f"python_version = {floor}" in mypy_ini, (
        f"pyproject requires-python is {declared!r} but mypy.ini does not target {floor}"
    )


def test_the_package_declares_no_runtime_dependencies():
    """`consilient` is standard library only. A new dependency is a decision, not a diff.

    AGENTS.md requires a new dependency to be argued. Nothing enforced that, so this does:
    adding one fails here and the commit has to say what it bought.
    """
    assert _pyproject()["project"]["dependencies"] == [], (
        "consilient gained a runtime dependency; say in the commit what it buys and why "
        "the standard library could not"
    )


def test_doctor_exits_nonzero_while_the_gates_are_shut(tmp_path, capsys):
    """`consil doctor` printed `Gate A: FAIL` and exited 0 until 21 August 2026.

    `main()` returned `0 if result.get("identical", True) else 1`, and `cmd_doctor`'s
    result carries no `identical` key, so every doctor invocation returned 0 whatever the
    gates said. ADR-0015's Enforcement clause calls this command "Not advisory"; a command
    whose failure a caller cannot read from `$?` is advisory. B9 in the guard catalogue is
    the same mistake made accidentally with a pipe.
    """
    write_capture_days(tmp_path / "log", "2026-08-20")
    code = main(
        [
            "--log",
            str(tmp_path / "log"),
            "--db",
            str(tmp_path / "state.db"),
            "--json",
            "doctor",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["routing_orchestration_enabled"] is False, (
        "fixture should not open the gates"
    )
    assert code == 1, "doctor reported shut gates and told its caller they were open"


def test_doctor_refuses_when_state_database_is_busy(tmp_path, monkeypatch, capsys):
    """Removing the PermissionError handler must expose the raw lock failure again."""
    log = tmp_path / "log"
    log.mkdir()
    db = tmp_path / "state.db"
    db.touch()

    def locked(_path):
        raise PermissionError("locked by another process")

    # sqlite3 is imported by cli_replay.py, which holds the replay command, since the
    # 28 August 2026 split; the entry point no longer imports it at all.
    monkeypatch.setattr(cli_replay.sqlite3, "connect", locked)

    code = main(["--log", str(log), "--db", str(db), "doctor"])
    captured = capsys.readouterr()

    assert code == 2
    assert captured.out == ""
    assert len(captured.err.splitlines()) == 1
    message = captured.err.lower()
    assert "state.db" in message
    assert "locked" in message or "busy" in message


def test_doctor_exits_zero_when_every_gate_passes(tmp_path, capsys, monkeypatch):
    """The other direction, so the exit code is a report and not a constant.

    Building a world where all seven conditions pass needs evidence this repository does
    not have. The mapping from payload to exit code is what is under test here, so the
    payload is supplied directly.
    """
    from consilient import cli as cli_mod

    monkeypatch.setattr(
        cli_mod,
        "cmd_doctor",
        lambda args: {"gates": {}, "routing_orchestration_enabled": True},
    )
    # Pointed at an empty tmp log rather than the repository's own. `cmd_doctor` is stubbed, so
    # the live trajectory is incidental to what this asserts -- but `main` still opens it, and
    # on 24 August 2026 a write burst from ~36 concurrent dispatchers made that read fail and
    # took this test red for a reason it does not test. The mapping from payload to exit code
    # is the subject; isolate it.
    log = tmp_path / "log"
    log.mkdir()
    assert main(["--json", "--log", str(log), "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["routing_orchestration_enabled"] is True


def test_the_loop_runtime_cannot_be_reached_from_the_observe_only_cli():
    """Stage 3 permits building this; it does not put it behind `consil`.

    The loop is an operator surface with a kill switch, not a reporting command, and the
    scope test that pins the CLI to four commands stays untouched by it.
    """
    parser = build_parser()
    subparsers = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    assert set(subparsers.choices) == {
        "record",
        "replay",
        "beta",
        "doctor",
        "dashboard",
        "usage",
    }


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)
