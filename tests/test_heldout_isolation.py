"""A build that can reach the held-out contract is refused before the child is launched.

ADR-0103's enforcement is a boundary crossed once, and these tests hold both sides of
it: the arguments as parsed -- brief, worktree and `--claim` -- and the brief as finally
assembled and written to disk, which is the last surface the child sees. Refusal must
come before any other preflight, so `refresh_default_headroom` is patched to fail the
test outright; anything that reaches it has proved the ordering wrong rather than merely
slow. The refusal itself must never repeat what it is protecting: no contract path, no
fingerprinted line, in the message or on stdout.

An unreachable contract proceeds to preflight, `--probe` still needs no task, and a
claim only refuses when canonical path boundaries actually contain the contract -- so
what is being refused is reachability, not the presence of the flag."""

from family_source import seam

import os
from pathlib import Path
import pytest
from heldout_helpers import (
    DISTINCTIVE_LINE,
    _isolated_pair,
    _load_checker,
    _load_dispatch,
)


@pytest.mark.parametrize("mode", ((), ("--dry-run",), ("--fan-out",)))
def test_heldout_contract_refuses_before_dispatch_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mode: tuple[str, ...],
) -> None:
    """A contract inside the worktree is still refused before further preflight."""
    dispatch = _load_dispatch()
    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: tmp_path)
    monkeypatch.setattr(
        seam("dispatch_progress"),
        "refresh_default_headroom",
        lambda _path: pytest.fail(
            "held-out refusal must precede further dispatch preflight"
        ),
    )

    code = dispatch.main(
        [
            "build the artefact",
            "--heldout-contract",
            str(tmp_path / "contract.py"),
            *mode,
        ]
    )

    assert code == 2
    output = capsys.readouterr().out
    assert "refusing before child launch" in output
    assert "worktree" in output.lower()
    assert "same-OS-user unsandboxed dispatch" not in output


def test_external_contract_alias_that_resolves_inside_worktree_refuses(
    tmp_path: Path,
) -> None:
    """A lexical path outside the worktree must not hide its target within it."""
    checker = _load_checker()
    worktree = tmp_path / "work"
    contract = worktree / "heldout" / "secret-contract.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(DISTINCTIVE_LINE, encoding="utf-8")
    alias = tmp_path / "external-contract-alias"
    try:
        alias.symlink_to(contract)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this Windows test environment: {exc}")

    reason = checker.refusal_reason(
        str(alias), brief="build", worktree=str(worktree), claims=()
    )

    assert reason is not None
    assert "worktree" in reason.lower()


@pytest.mark.parametrize("target_kind", ("contract", "containing directory"))
def test_claim_alias_to_heldout_path_refuses(
    tmp_path: Path, target_kind: str
) -> None:
    """A claim symlink must not hide the contract or its containing directory."""
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    target = contract if target_kind == "contract" else contract.parent
    alias = worktree / "claimed-alias"
    try:
        alias.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this Windows test environment: {exc}")

    reason = checker.refusal_reason(
        str(contract), brief="build", worktree=str(worktree), claims=(alias.name,)
    )

    assert reason is not None
    assert "claim" in reason.lower()


def test_hard_linked_contract_refuses(
    tmp_path: Path,
) -> None:
    """An additional hard link makes the contract's location unsafe to establish."""
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    try:
        os.link(contract, worktree / "contract-hard-link")
    except OSError as exc:
        pytest.skip(f"hard links unavailable in this test environment: {exc}")

    reason = checker.refusal_reason(
        str(contract), brief="build", worktree=str(worktree), claims=()
    )

    assert reason is not None
    assert "refusing before child launch" in reason


@pytest.mark.parametrize("with_worktree", (False, True))
def test_embedded_nul_refuses_in_resolution_and_contract_validation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_worktree: bool
) -> None:
    """An embedded NUL is invalid whether resolution or contract reading sees it first."""
    checker = _load_checker()
    if with_worktree:
        original_resolve = Path.resolve

        def reject_nul(path: Path, strict: bool = False) -> Path:
            if "\0" in str(path):
                raise ValueError("embedded null character")
            return original_resolve(path, strict=strict)

        monkeypatch.setattr(Path, "resolve", reject_nul)

    reason = checker.refusal_reason(
        "\0",
        brief="build",
        worktree=str(tmp_path) if with_worktree else "",
        claims=(),
    )

    assert reason is not None
    assert "input is invalid" in reason


@pytest.mark.skipif(os.name == "nt", reason="native Windows paths are case-insensitive")
def test_distinct_case_native_posix_paths_do_not_overlap(tmp_path: Path) -> None:
    """Native POSIX containment comparisons preserve case before checking overlap."""
    checker = _load_checker()
    worktree = tmp_path / "worktree"
    contract = tmp_path / "Worktree" / "secret-contract.md"
    worktree.mkdir()
    contract.parent.mkdir()
    contract.write_text(DISTINCTIVE_LINE, encoding="utf-8")

    reason = checker.refusal_reason(
        str(contract), brief="build", worktree=str(worktree), claims=()
    )

    assert reason is None


@pytest.mark.parametrize("failure", (OSError("unavailable"), RuntimeError("cycle")))
def test_unresolvable_path_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: Exception
) -> None:
    """Resolution failures are unsafe rather than treated as an unreachable contract."""
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    original_resolve = Path.resolve

    def unresolved(path: Path, strict: bool = False) -> Path:
        if path == contract:
            raise failure
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", unresolved)

    reason = checker.refusal_reason(
        str(contract), brief="build", worktree=str(worktree), claims=()
    )

    assert reason is not None
    assert "input is invalid" in reason


def test_wsl_path_spelling_resolves_before_canonical_comparison(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A WSL path must resolve before its Windows canonical spelling is compared."""
    checker = _load_checker()
    worktree = tmp_path / "work"
    contract = worktree / "heldout" / "secret-contract.md"
    contract.parent.mkdir(parents=True)
    contract.write_text(DISTINCTIVE_LINE, encoding="utf-8")
    alias = Path("/mnt/c/External-Contract-Alias")
    wsl_worktree = Path("/mnt/c/Work")
    local_alias = Path("c:/External-Contract-Alias") if os.name == "nt" else alias
    local_worktree = Path("c:/Work") if os.name == "nt" else wsl_worktree
    original_resolve = Path.resolve
    seen: list[str] = []

    def resolve(path: Path, strict: bool = False) -> Path:
        seen.append(str(path))
        if str(path) == str(local_alias):
            return contract
        if str(path) == str(local_worktree):
            return worktree
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)

    reason = checker.refusal_reason(
        str(alias), brief="build", worktree=str(wsl_worktree), claims=()
    )

    assert reason is not None
    assert "worktree" in reason.lower()
    assert seen == [str(local_alias), str(local_worktree)]


def test_heldout_contract_named_in_brief_refuses_before_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(
        seam("dispatch_progress"),
        "refresh_default_headroom",
        lambda _path: pytest.fail(
            "held-out refusal must precede further dispatch preflight"
        ),
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


@pytest.mark.parametrize(
    "quoted",
    (DISTINCTIVE_LINE, DISTINCTIVE_LINE.upper(), DISTINCTIVE_LINE.lower()),
)
def test_heldout_contract_quoted_in_brief_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    quoted: str,
) -> None:
    checker = _load_checker()
    worktree, contract = _isolated_pair(tmp_path)
    reason = checker.refusal_reason(
        str(contract),
        brief=f'The builder must not copy "{quoted}"',
        worktree=str(worktree),
        claims=(),
    )
    assert reason is not None
    assert "brief" in reason.lower()
    assert "refusing before child launch" in reason
    assert DISTINCTIVE_LINE not in reason
    assert quoted not in reason
    output = capsys.readouterr().out
    assert DISTINCTIVE_LINE not in output
    assert quoted not in output


def test_heldout_contract_covered_by_claim_refuses_before_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dispatch = _load_dispatch()
    worktree, contract = _isolated_pair(tmp_path)
    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(
        seam("dispatch_progress"),
        "refresh_default_headroom",
        lambda _path: pytest.fail(
            "held-out refusal must precede further dispatch preflight"
        ),
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

    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(seam("dispatch_progress"), "refresh_default_headroom", _refresh)

    code = dispatch.main(["build the artefact", "--heldout-contract", str(contract)])

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

    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(seam("dispatch_invocation"), "heldout_contract_refusal", _spy)
    monkeypatch.setattr(
        seam("dispatch_progress"),
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

    monkeypatch.setattr(seam("dispatch_preflight"), "write_brief", write_leaking_brief)
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "run_process",
        lambda *_args, **_kwargs: pytest.fail("must not launch"),
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
        return original_read(path, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "read_text", unreadable_brief)
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_args, **_kwargs: ["fake"])
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "run_process",
        lambda *_args, **_kwargs: pytest.fail("must not launch"),
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

    monkeypatch.setattr(seam("dispatch_preflight"), "write_brief", write_leaking_brief)
    payload, code = dispatch.dispatch_one(
        # `Decision` is a consilient.harness type. The dispatch entry point imported it before
        # the 28 August 2026 split and no longer does, because nothing in the entry uses it.
        decision=seam("dispatch_single").Decision("run", harness, "test harness", ()),
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

    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(seam("dispatch_invocation"), "heldout_contract_refusal", capture)
    monkeypatch.setattr(
        seam("dispatch_progress"), "refresh_default_headroom", lambda _path: pytest.fail("too late")
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
    monkeypatch.setattr(seam("dispatch_progress"), "resolve_cwd", lambda _value: worktree)
    monkeypatch.setattr(
        seam("dispatch_vocabulary"), "load_task", lambda *_args: pytest.fail("probe needs no task")
    )
    monkeypatch.setattr(seam("dispatch_progress"), "refresh_default_headroom", lambda _path: None)
    monkeypatch.setattr(seam("dispatch_vocabulary"), "ensure_default_headroom", lambda _path: None)
    monkeypatch.setattr(dispatch, "load_pools", lambda _path: ())
    monkeypatch.setattr(
        dispatch, "headroom_freshness_refusal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(seam("dispatch_workspace"), "probe_all", lambda: ())

    assert dispatch.main(["--probe", "--heldout-contract", str(contract)]) == 0
