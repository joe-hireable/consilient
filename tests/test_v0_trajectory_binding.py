"""Which code read which directory, and whether there was anything there to read.
Measured 21 August 2026 on the machine this was written on: a single interpreter-global
editable install put one worktree's `src` on `sys.path` for every process and no tree's
own `src` was on it, so standing in this checkout `python -m consilient.cli doctor` read
this checkout's log with the other checkout's code and reported Gate A1 PASS, exit 0,
while the code in this tree reported A1 FAIL, exit 1, on the same log in the same
directory. Two agents were misled by it in one night. Code identity is settled by
`sys.path` before any of this runs and data identity by the working directory, so the
refusal can only fire once both are known — and because an ordinary repository has no
`src/consilient/cli.py` and the wrong-tree case there is undetectable, `doctor` states
its provenance unprompted; until 21 August 2026 its JSON keys were exactly `gates` and
`routing_orchestration_enabled`, so a transcript could not be audited for which tree
produced it. The second half is the defect the principal hit the same day: run from a
directory with no checkout, `replay`, `dashboard` and `beta` all reported confident
zeros. A missing trajectory is now refused with its resolved path and `--log` named, an
existing but empty one still reports zero and says so, and the guard is mutation-tested
so that breaking it visibly fails the refusal test."""

import json
import sys
from pathlib import Path
from consilient.cli import main
from v0_invariants_helpers import (
    _spend_scripts,
    doctor_payload,
    write_capture_days,
)

if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

# ------------------------------- which tree measured which tree, 21 August 2026


def test_consil_refuses_to_measure_a_checkout_other_than_its_own(
    tmp_path, monkeypatch, capsys
):
    """The instrument may not report one worktree's answers about another's data.

    Measured 21 August 2026 on the machine this was written on: a single interpreter-global
    editable install put one worktree's `src` on `sys.path` for every process, and no
    tree's own `src` was on it, because a src layout means the working directory never
    contains `consilient/`. Standing in this checkout, `python -m consilient.cli doctor`
    read this checkout's log with the other checkout's code and reported Gate A1 `PASS`,
    exit 0; the code in this tree reported A1 `FAIL`, exit 1, on the same log in the same
    directory. Two agents were misled by it in one night, one reporting the wrong gate
    state and one reading the wrong exit code.

    Code identity is settled by `sys.path` before any of this runs and data identity by the
    working directory, so this cannot be made impossible from inside the package -- only
    refused once both are known.
    """
    from consilient import cli as cli_mod

    foreign = tmp_path / "consilient-w-other"
    (foreign / "src" / "consilient").mkdir(parents=True)
    (foreign / "src" / "consilient" / "cli.py").write_text("", encoding="utf-8")
    monkeypatch.chdir(foreign)

    code = main(["--json", "doctor"])

    out, err = capsys.readouterr()
    assert code == 2, "a foreign checkout was measured and the caller was not told"
    assert out == "", "a refused run printed a gate report anyway"
    message = json.loads(err)["error"]
    assert str(foreign.resolve()) in message, message
    assert str(cli_mod.CODE_TREE) in message, message

    # The two cases that must NOT be refused. Without these the guard could be an
    # unconditional refusal, which would be refusing the tool's own purpose.
    ordinary = tmp_path / "someones-repository"
    ordinary.mkdir()
    monkeypatch.chdir(ordinary)
    assert cli_mod._foreign_tree() is None, (
        "measuring somebody else's repository is what this tool is for"
    )
    monkeypatch.chdir(cli_mod.CODE_TREE)
    assert cli_mod._foreign_tree() is None, (
        "the code's own checkout must measure itself"
    )


def test_doctor_states_which_code_measured_which_directory(tmp_path, capsys):
    """The refusal cannot fire in an ordinary repository, so doctor says it unprompted.

    An ordinary repository has no `src/consilient/cli.py`, so the wrong-tree case there is
    undetectable from inside the package and the only defence is that the report names the
    code it came from. `consil doctor --json` carried no provenance at all until 21 August
    2026 [measured]: its keys were exactly `gates` and `routing_orchestration_enabled`, so
    a transcript of a run could not be audited for which tree produced it.
    """
    from consilient import cli as cli_mod

    write_capture_days(tmp_path / "log", "2026-08-20")

    payload = doctor_payload(tmp_path, capsys)

    assert payload["provenance"] == {
        "code": str(cli_mod.CODE_TREE),
        "data": str(Path.cwd().resolve()),
        "log": str((tmp_path / "log").resolve()),
    }
    rendered = cli_mod.render("doctor", payload).splitlines()
    assert rendered[0] == f"code: {cli_mod.CODE_TREE}", (
        "the human rendering lost the provenance line; that is the form an agent pastes "
        "into a transcript, and the only place the wrong tree stays visible afterwards"
    )
    assert str((tmp_path / "log").resolve()) in rendered[1], rendered[1]


# --------------------------- missing trajectory is not an empty trajectory, 21 Aug 2026
def test_cli_read_commands_refuse_a_missing_trajectory_directory(
    tmp_path, monkeypatch, capsys
):
    """The defect the principal hit: defaults to `.harness/log` under cwd and reports zero.

    Measured 21 August 2026 from `C:\\Users\\jpbpr` with no checkout: `consil replay`,
    `dashboard` and `beta` all reported confident zeros. Each command here is run from a
    directory with no trajectory directory at all.
    """
    monkeypatch.chdir(tmp_path)
    log = tmp_path / ".harness" / "log"
    db = tmp_path / ".harness" / "state.db"
    out_path = tmp_path / ".harness" / "dashboard.html"
    assert not log.is_dir()

    cases = [
        (["replay"], {}),
        (["beta"], {}),
        (["usage"], {}),
        (["doctor"], {}),
        (["dashboard", "--out", str(out_path)], {"out_path": out_path}),
    ]
    for argv, extra in cases:
        capsys.readouterr()
        code = main(["--log", str(log), "--db", str(db), *argv])
        captured = capsys.readouterr()
        assert code == 2, argv
        assert captured.out == "", f"{argv} printed a report despite a missing log"
        message = captured.err
        assert "trajectory not configured" in message, message
        assert str(log.resolve()) in message, message
        assert "--log" in message, message
        assert "0 events" not in message
        assert "0 human rejections" not in message
        if out := extra.get("out_path"):
            assert not out.exists(), f"{argv} wrote {out} without a trajectory"


def test_cli_read_commands_report_zero_on_an_empty_trajectory(tmp_path, capsys):
    """An existing but empty directory is zero — and must say so, with its path visible."""
    log = tmp_path / "log"
    log.mkdir(parents=True)
    db = tmp_path / "state.db"

    capsys.readouterr()
    replay_code = main(["--log", str(log), "--db", str(db), "replay"])
    replay_out = capsys.readouterr().out
    assert replay_code != 2, "an empty trajectory must not be refused"
    assert "replayed 0 events" in replay_out
    assert "trajectory not configured" not in replay_out
    assert str(log.resolve()) in replay_out
    assert "empty" in replay_out

    capsys.readouterr()
    assert main(["--log", str(log), "--db", str(db), "beta"]) == 0
    beta_out = capsys.readouterr().out
    assert "0 human rejections" in beta_out
    assert "trajectory not configured" not in beta_out
    assert str(log.resolve()) in beta_out
    assert "empty" in beta_out


def test_missing_trajectory_guard_is_mutation_tested(tmp_path, monkeypatch, capsys):
    """Break the guard, confirm this file's refusal test fails, restore, confirm it passes."""
    from consilient import cli as cli_mod

    monkeypatch.chdir(tmp_path)
    log = tmp_path / "log"
    db = tmp_path / "state.db"

    real = cli_mod.require_trajectory
    monkeypatch.setattr(cli_mod, "require_trajectory", lambda _log: "empty")
    capsys.readouterr()
    broken_code = main(["--log", str(log), "--db", str(db), "replay"])
    broken = capsys.readouterr()
    assert broken_code != 2, "mutation did not restore the false-zero path"
    assert "replayed 0 events" in broken.out
    assert "trajectory not configured" not in broken.err

    monkeypatch.setattr(cli_mod, "require_trajectory", real)
    capsys.readouterr()
    fixed_code = main(["--log", str(log), "--db", str(db), "replay"])
    fixed_err = capsys.readouterr().err
    assert fixed_code == 2
    assert "trajectory not configured" in fixed_err
