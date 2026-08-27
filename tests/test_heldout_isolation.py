"""Held-out contracts are refused when a dispatch can reach them, and leaks void the measurement.

ADR-0103's enforcement is the boundary: a build whose brief, worktree or claims can
reach the contract is refused before child launch. A post-build audit voids a
measurement that leaked the path, digest or a fingerprinted line. The residual is
recorded on the checker: a child that reads the contract and neither echoes its path
nor reproduces its assertions is not detected. [asserted]
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

DISTINCTIVE_LINE = (
    "Held-out isolation fingerprints a deliberately unusual sequence of operational "
    "constraints so a copied assertion cannot resemble ordinary project boilerplate "
    "by accident."
)
SHORT_LINE = "short assertion"
CONTRACT_BODY = f"{SHORT_LINE}\n{DISTINCTIVE_LINE}\n"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_dispatch() -> ModuleType:
    return _load_module("heldout_dispatch", Path("scripts/dispatch.py").resolve())


def _load_checker() -> ModuleType:
    return _load_module(
        "heldout_isolation_checker",
        Path(".github/scripts/check_heldout_isolation.py").resolve(),
    )


def _load_corpus() -> ModuleType:
    return _load_module(
        "heldout_private_corpus",
        Path(".github/scripts/check_private_corpus.py").resolve(),
    )


def _write_contract(path: Path, body: str = CONTRACT_BODY) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _isolated_pair(tmp_path: Path) -> tuple[Path, Path]:
    worktree = tmp_path / "work"
    worktree.mkdir()
    contract = _write_contract(tmp_path / "heldout" / "secret-contract.md")
    return worktree, contract


@pytest.mark.parametrize("mode", ((), ("--dry-run",), ("--fan-out",)))
def test_heldout_contract_refuses_before_dispatch_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mode: tuple[str, ...],
) -> None:
    """A contract inside the worktree is still refused before further preflight."""
    dispatch = _load_dispatch()
    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: tmp_path)
    monkeypatch.setattr(
        dispatch,
        "refresh_default_headroom",
        lambda _path: pytest.fail("held-out refusal must precede further dispatch preflight"),
    )

    code = dispatch.main(
        ["build the artefact", "--heldout-contract", str(tmp_path / "contract.py"), *mode]
    )

    assert code == 2
    output = capsys.readouterr().out
    assert "refusing before child launch" in output
    assert "worktree" in output.lower()
    assert "same-OS-user unsandboxed dispatch" not in output


def test_heldout_contract_named_in_brief_refuses_before_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(
        dispatch,
        "refresh_default_headroom",
        lambda _path: pytest.fail("held-out refusal must precede further dispatch preflight"),
    )

    code = dispatch.main(
        [
            f"implement the unit against {contract}",
            "--heldout-contract",
            str(contract),
        ]
    )

    assert code == 2
    output = capsys.readouterr().out
    assert "brief" in output.lower()
    assert "refusing before child launch" in output
    assert DISTINCTIVE_LINE not in output


def test_heldout_contract_quoted_in_brief_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    reason = checker.refusal_reason(
        str(contract),
        brief=f'The builder must not copy "{DISTINCTIVE_LINE}"',
        worktree=str(worktree),
        claims=(),
    )
    assert reason is not None
    assert "brief" in reason.lower()
    assert "refusing before child launch" in reason
    assert DISTINCTIVE_LINE not in reason
    assert DISTINCTIVE_LINE not in capsys.readouterr().out


def test_heldout_contract_covered_by_claim_refuses_before_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(
        dispatch,
        "refresh_default_headroom",
        lambda _path: pytest.fail("held-out refusal must precede further dispatch preflight"),
    )

    code = dispatch.main(
        [
            "build the artefact",
            "--heldout-contract",
            str(contract),
            "--claim",
            str(contract.parent),
        ]
    )

    assert code == 2
    output = capsys.readouterr().out.lower()
    assert "claim" in output
    assert "refusing before child launch" in output


def test_heldout_contract_unreachable_proceeds_to_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    seen = {"refresh": False}

    def _refresh(_path: Path) -> str:
        seen["refresh"] = True
        return "stop-after-isolation"

    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(dispatch, "refresh_default_headroom", _refresh)

    code = dispatch.main(
        ["build the artefact", "--heldout-contract", str(contract)]
    )

    assert seen["refresh"] is True
    assert code == 2
    output = capsys.readouterr().out
    assert "stop-after-isolation" in output


def test_dispatch_passes_brief_worktree_and_claims_to_the_checker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    captured: dict[str, object] = {}

    def _spy(
        path: str,
        *,
        brief: str = "",
        worktree: str = "",
        claims: tuple[str, ...] = (),
    ) -> str | None:
        captured["contract"] = path
        captured["brief"] = brief
        captured["worktree"] = worktree
        captured["claims"] = claims
        return "stop-after-capture"

    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(dispatch, "heldout_contract_refusal", _spy)
    monkeypatch.setattr(
        dispatch,
        "refresh_default_headroom",
        lambda _path: pytest.fail("a captured refusal must precede further preflight"),
    )

    code = dispatch.main(
        [
            "build the artefact",
            "--heldout-contract",
            str(contract),
            "--claim",
            "src/consilient/beta.py",
        ]
    )

    assert code == 2
    assert captured["contract"] == str(contract)
    assert captured["brief"] == "build the artefact"
    assert captured["worktree"] == str(worktree)
    assert captured["claims"] == ("src/consilient/beta.py",)


def test_checker_permits_an_unreachable_contract_and_cli_prints_what_it_checked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    reason = checker.refusal_reason(
        str(contract),
        brief="build the artefact",
        worktree=str(worktree),
        claims=("src/consilient/beta.py",),
    )
    assert reason is None
    assert capsys.readouterr().out == ""
    code = checker.main(
        [
            "--heldout-contract",
            str(contract),
            "--brief",
            "build the artefact",
            "--worktree",
            str(worktree),
            "--claim",
            "src/consilient/beta.py",
        ]
    )
    output = capsys.readouterr().out.lower()
    assert code == 0
    assert "worktree" in output
    assert "brief" in output
    assert "claim" in output
    assert DISTINCTIVE_LINE not in output


def test_residual_is_recorded_in_the_module_docstring() -> None:
    checker = _load_checker()
    doc = checker.__doc__ or ""
    assert (
        "a child that reads the contract and neither echoes its path nor "
        "reproduces its assertions is not detected" in doc.casefold()
    )
    assert "[asserted]" in doc


def test_audit_reuses_private_corpus_content_digest() -> None:
    checker = _load_checker()
    source = Path(".github/scripts/check_heldout_isolation.py").read_text(encoding="utf-8")
    assert "check_private_corpus" in source
    assert checker.content_digest(DISTINCTIVE_LINE) == _load_corpus().content_digest(DISTINCTIVE_LINE)
    assert checker.content_digest(SHORT_LINE) is None


def _run_audit(
    checker: ModuleType,
    *,
    contract: Path,
    runs: Path,
    uid: str,
    transcript: str,
    err: str = "",
    diff: str = "",
    filename: str | None = None,
) -> tuple[int, str]:
    stem = filename or uid
    (runs / f"{stem}.out").write_text(transcript, encoding="utf-8")
    (runs / f"{stem}.err").write_text(err, encoding="utf-8")
    diff_path = runs / f"{stem}.diff"
    diff_path.write_text(diff, encoding="utf-8")
    argv = [
        "--audit",
        "--heldout-contract",
        str(contract),
        "--uid",
        uid,
        "--runs-dir",
        str(runs),
    ]
    argv.extend(["--diff", str(diff_path)])
    code = checker.main(argv)
    return code, ""


def test_audit_returns_leaked_and_void_on_contract_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker,
        contract=contract,
        runs=runs,
        uid="AR",
        transcript=f"opened {contract} and continued\n",
    )
    output = capsys.readouterr().out
    assert code != 0
    assert "LEAKED" in output
    assert "VOID" in output
    assert DISTINCTIVE_LINE not in output
    assert str(contract) not in output


def test_audit_returns_leaked_on_contract_digest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    digest = hashlib.sha256(contract.read_bytes()).hexdigest()
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker,
        contract=contract,
        runs=runs,
        uid="AR",
        transcript=f"sha256 {digest}\n",
    )
    output = capsys.readouterr().out
    assert code != 0
    assert "LEAKED" in output
    assert "VOID" in output
    assert DISTINCTIVE_LINE not in output


def test_audit_returns_leaked_on_fingerprinted_line(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker,
        contract=contract,
        runs=runs,
        uid="AR",
        transcript=f"{DISTINCTIVE_LINE}\n",
    )
    output = capsys.readouterr().out
    assert code != 0
    assert "LEAKED" in output
    assert "VOID" in output
    assert DISTINCTIVE_LINE not in output


@pytest.mark.parametrize("surface", ("transcript", "err", "diff"))
def test_audit_scans_each_surface(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], surface: str
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker,
        contract=contract,
        runs=runs,
        uid="AR",
        transcript=f"{DISTINCTIVE_LINE}\n" if surface == "transcript" else "clean stdout\n",
        err=DISTINCTIVE_LINE if surface == "err" else "clean stderr\n",
        diff=DISTINCTIVE_LINE if surface == "diff" else "clean diff\n",
    )
    output = capsys.readouterr().out
    assert code != 0
    assert "LEAKED" in output
    assert "VOID" in output
    assert DISTINCTIVE_LINE not in output


def test_audit_returns_clean_otherwise(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker,
        contract=contract,
        runs=runs,
        uid="AR",
        transcript="the child produced a passing suite and wrote three files.\n",
        err="no diagnostics\n",
        diff="diff --git a/src/consilient/beta.py b/src/consilient/beta.py\n",
    )
    output = capsys.readouterr().out
    assert code == 0
    assert "CLEAN" in output
    assert "LEAKED" not in output
    assert "VOID" not in output
    assert DISTINCTIVE_LINE not in output
    assert SHORT_LINE not in output


@pytest.mark.parametrize(
    ("transcript", "expected"),
    (
        (f"  {DISTINCTIVE_LINE.upper()}  \n", "LEAKED"),
        (f"{SHORT_LINE}\n", "CLEAN"),
    ),
)
def test_audit_normalises_distinctive_lines_but_ignores_short_ones(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    transcript: str,
    expected: str,
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code, _ = _run_audit(
        checker, contract=contract, runs=runs, uid="AR", transcript=transcript
    )

    assert (code == 0) is (expected == "CLEAN")
    assert expected in capsys.readouterr().out


@pytest.mark.parametrize(
    ("claim", "refused"),
    (
        ("", True),
        ("../heldout/secret-contract.md", True),
        ("../heldout", True),
        ("../heldout-x/secret-contract.md", False),
    ),
)
def test_claim_reachability_uses_canonical_path_boundaries(
    tmp_path: Path, claim: str, refused: bool
) -> None:
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    claims = (str(contract),) if not claim else (claim,)
    reason = checker.refusal_reason(
        str(contract), brief="build", worktree=str(worktree), claims=claims
    )
    assert (reason is not None) is refused


def test_final_assembled_brief_is_checked_before_child_launch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    harness = dispatch.harness_by_id("codex")
    assert harness is not None
    original_write_brief = dispatch.write_brief

    def write_leaking_brief(*args: object, **kwargs: object) -> Path:
        written = original_write_brief(*args, **kwargs)
        if not isinstance(written, Path):
            raise TypeError("write_brief must return Path")
        written.write_text(
            written.read_text(encoding="utf-8") + contract.name, encoding="utf-8"
        )
        return written

    monkeypatch.setattr(dispatch, "write_brief", write_leaking_brief)
    monkeypatch.setattr(dispatch, "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        dispatch, "run_process", lambda *_args, **_kwargs: pytest.fail("must not launch")
    )

    result = dispatch.run_harness(
        harness,
        task="build",
        cwd=worktree,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="AR",
        heldout_contract=str(contract),
    )

    assert result.status == "refused"
    assert "brief" in result.reason.lower()


def test_unreadable_final_brief_refuses_before_child_launch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    harness = dispatch.harness_by_id("codex")
    assert harness is not None
    original_read = Path.read_text

    def unreadable_brief(
        path: Path,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> str:
        if path.name == "brief.md":
            raise OSError("brief unavailable")
        return original_read(
            path, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "read_text", unreadable_brief)
    monkeypatch.setattr(dispatch, "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        dispatch, "run_process", lambda *_args, **_kwargs: pytest.fail("must not launch")
    )

    result = dispatch.run_harness(
        harness,
        task="build",
        cwd=worktree,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="AR",
        heldout_contract=str(contract),
    )

    assert result.status == "refused"
    assert "final brief" in result.reason


def test_dry_run_refuses_a_generated_contract_bearing_brief(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    harness = dispatch.harness_by_id("codex")
    assert harness is not None
    original_write_brief = dispatch.write_brief

    def write_leaking_brief(*args: object, **kwargs: object) -> Path:
        written = original_write_brief(*args, **kwargs)
        if not isinstance(written, Path):
            raise TypeError("write_brief must return Path")
        written.write_text(
            written.read_text(encoding="utf-8") + contract.name, encoding="utf-8"
        )
        return written

    monkeypatch.setattr(dispatch, "write_brief", write_leaking_brief)
    payload, code = dispatch.dispatch_one(
        decision=dispatch.Decision("run", harness, "test harness", ()),
        task="build",
        cwd=worktree,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=True,
        heldout_contract=str(contract),
    )

    assert code == 2
    assert payload["status"] == "refused"
    assert "brief" in str(payload["reason"]).lower()


def test_audit_finding_voids_the_child_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    harness = dispatch.harness_by_id("codex")
    assert harness is not None
    monkeypatch.setattr(dispatch, "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        dispatch,
        "run_process",
        lambda _argv, **kwargs: (
            Path(kwargs["stdout_path"]).write_text(
                f"{contract}\n{DISTINCTIVE_LINE}\n", encoding="utf-8"
            ),
            Path(kwargs["stderr_path"]).write_text(str(contract), encoding="utf-8"),
            (0, False, 0.1, None),
        )[-1],
    )
    monkeypatch.setattr(
        dispatch,
        "heldout_contract_audit",
        lambda *_args, **_kwargs: "held-out contract LEAKED; measurement VOID",
    )

    result = dispatch.run_harness(
        harness,
        task="build",
        cwd=worktree,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="AR",
        heldout_contract=str(contract),
    )

    assert result.status == "refused"
    assert result.reason == "held-out contract LEAKED; measurement VOID"
    payload = dispatch._result_payload(result)
    assert result.stdout == ""
    assert result.stderr == ""
    assert str(contract) not in str(payload)
    assert DISTINCTIVE_LINE not in str(payload)


def test_dispatch_loads_task_file_before_heldout_preflight_with_relative_claims(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    task_file = tmp_path / "task.md"
    task_file.write_text("build from a task file", encoding="utf-8")
    captured: dict[str, object] = {}

    def capture(path: str, **kwargs: object) -> str:
        captured["path"] = path
        captured.update(kwargs)
        return "stop after held-out preflight"

    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(dispatch, "heldout_contract_refusal", capture)
    monkeypatch.setattr(
        dispatch, "refresh_default_headroom", lambda _path: pytest.fail("too late")
    )
    code = dispatch.main(
        [
            "--task-file",
            str(task_file),
            "--cwd",
            str(worktree),
            "--heldout-contract",
            str(contract),
            "--claim",
            "../heldout/secret-contract.md",
        ]
    )

    assert code == 2
    assert captured["brief"] == "build from a task file"
    assert captured["claims"] == ("../heldout/secret-contract.md",)


def test_probe_keeps_task_optional_with_a_heldout_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(dispatch, "load_task", lambda *_args: pytest.fail("probe needs no task"))
    monkeypatch.setattr(dispatch, "refresh_default_headroom", lambda _path: None)
    monkeypatch.setattr(dispatch, "ensure_default_headroom", lambda _path: None)
    monkeypatch.setattr(dispatch, "load_pools", lambda _path: ())
    monkeypatch.setattr(dispatch, "headroom_freshness_refusal", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dispatch, "probe_all", lambda: ())

    assert dispatch.main(["--probe", "--heldout-contract", str(contract)]) == 0


def test_audit_refuses_invalid_inputs_without_reporting_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checker = _load_checker()
    _worktree, contract = _isolated_pair(tmp_path)
    runs = tmp_path / "dispatch"
    runs.mkdir()
    code = checker.main(
        [
            "--audit",
            "--heldout-contract",
            str(contract),
            "--uid",
            "../escape",
            "--runs-dir",
            str(runs),
            "--diff",
            str(runs / "missing.diff"),
        ]
    )

    output = capsys.readouterr().out
    assert code != 0
    assert "CLEAN" not in output
    assert "VOID" in output
