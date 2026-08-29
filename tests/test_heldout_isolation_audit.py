"""The post-build audit voids a measurement that leaked, and reports it without
repeating the leak.

Every surface a child can write to is scanned -- stdout, stderr and the diff -- for the
contract's path, the digest of its bytes, or a line distinctive enough that reproducing
it cannot be coincidence. Short lines are ignored on purpose: ordinary boilerplate would
otherwise be indistinguishable from a leak, so the fingerprint has a length floor and
`SHORT_LINE` proves it holds. The digest is the one `check_private_corpus` already
computes, reused rather than reimplemented, so a leak is recognised the same way by both
checks and cannot pass one while failing the other.

A finding is LEAKED and VOID; the child's stdout and stderr are dropped from the result
payload so the void verdict does not itself become the leak; and invalid inputs are
refused rather than quietly reported CLEAN, because a check that cannot run must not
look like a check that passed.

The residual is recorded in the checker's own docstring and pinned here: a child that
reads the contract and neither echoes its path nor reproduces its assertions is not
detected. [asserted]"""

from family_source import seam

import hashlib
from pathlib import Path
from types import ModuleType
import pytest
from heldout_helpers import (
    DISTINCTIVE_LINE,
    SHORT_LINE,
    _isolated_pair,
    _load_checker,
    _load_dispatch,
    _load_module,
)


def _load_corpus() -> ModuleType:
    return _load_module(
        "heldout_private_corpus",
        Path(".github/scripts/check_private_corpus.py").resolve(),
    )


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
    source = Path(".github/scripts/check_heldout_isolation.py").read_text(
        encoding="utf-8"
    )
    assert "check_private_corpus" in source
    assert checker.content_digest(DISTINCTIVE_LINE) == _load_corpus().content_digest(
        DISTINCTIVE_LINE
    )
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
        transcript=f"{DISTINCTIVE_LINE}\n"
        if surface == "transcript"
        else "clean stdout\n",
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


def test_audit_finding_voids_the_child_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    harness = dispatch.harness_by_id("codex")
    assert harness is not None
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        seam("dispatch_launch"),
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
        seam("dispatch_boundaries"),
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
