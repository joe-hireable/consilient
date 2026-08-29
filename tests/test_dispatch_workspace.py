"""Where dispatch is allowed to work, and the workspace it provisions once it is there.

Gate B has a check now. AGENTS.md forbade pointing the harness at another repository and
nothing enforced it — `Path(value).resolve()` accepted every path on the machine, which
is a documented invariant with no enforcement rule, the failure this repository has
already paid for once. The outside path in these tests is constructed under `tmp_path`
deliberately: proving the boundary must not require reading, resolving or naming a
private corpus.

The instance allowlist (ADR-0063) narrows rather than opens: a missing file is empty, a
filesystem root is refused, malformed JSON fails closed, missing directories are
dropped, and an unlisted foreign root is still refused while an allowlist exists. The
listing lives in gitignored instance state and only the empty example ships. A refused
dry run prints its reason and no command, so a path that was rejected never leaks the
invocation that would have run there.

The surface pin belongs here for the same reason: dispatch is a script, not a `consil`
subcommand (ADR-0058), and the subcommand set is asserted exactly. Workspace
provisioning closes the set — every admitted form gets its own git index, so two arms
cannot stage over each other, and a failed probe or an unready native item is refused
before `run_process` is reached rather than after a process has already started writing."""

from family_source import seam

import argparse
import json
import os
import subprocess
from pathlib import Path
import pytest
from consilient.cli import build_parser
from consilient.events import read_all
from consilient.harness import (
    DEFAULT_POOLS,
    select,
)
from dispatch_helpers import (
    DISPATCH_PATH,
    INSTALLED,
    _git,
    _load_script,
)


def test_dispatch_is_a_script_not_a_consil_subcommand():
    parser = build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert set(subparsers.choices) == {
        "record",
        "replay",
        "beta",
        "doctor",
        "dashboard",
        "usage",
    }
    assert DISPATCH_PATH.is_file()
    source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "silently" in source.lower() or "NOT retried" in source


def test_resolve_cwd_allows_this_repository_root():
    script = _load_script()
    assert script.resolve_cwd(str(script.ROOT)) == script.ROOT


def test_resolve_cwd_allows_a_directory_inside_this_repository():
    script = _load_script()
    inside = script.ROOT / "scripts"
    assert inside.is_dir()
    assert script.resolve_cwd(str(inside)) == inside.resolve()


def test_resolve_cwd_refuses_a_path_outside_this_repository(tmp_path):
    """Gate B has a check now. AGENTS.md forbade pointing this at another repository and
    nothing enforced it; `Path(value).resolve()` accepted every path on the machine.

    The outside path is constructed under tmp_path deliberately: proving the boundary must
    not require reading, resolving or naming a private corpus.
    """
    script = _load_script()
    outside = tmp_path / "some-other-repo"
    outside.mkdir()
    with pytest.raises(ValueError, match="only inside its own repository"):
        script.resolve_cwd(str(outside))


def test_resolve_cwd_has_no_override_flag():
    """A second path to the same state is the same hole. There is no --gate-b-approved."""
    source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "gate-b-approved" not in source
    assert "--allow-foreign" not in source


def test_load_allowed_roots_missing_file_is_empty(tmp_path):
    script = _load_script()
    assert script.load_allowed_roots(tmp_path / "no-such.json") == ()


def test_load_allowed_roots_skips_missing_directories(tmp_path):
    script = _load_script()
    present = tmp_path / "present"
    present.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(
        json.dumps({"roots": [str(present), str(tmp_path / "gone")]}) + "\n",
        encoding="utf-8",
    )
    assert script.load_allowed_roots(allow) == (present.resolve(),)


def test_load_allowed_roots_refuses_a_filesystem_root(tmp_path):
    script = _load_script()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(
        json.dumps({"roots": [str(tmp_path.anchor)]}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="filesystem root"):
        script.load_allowed_roots(allow)


def test_load_allowed_roots_malformed_json_fails_closed(tmp_path):
    script = _load_script()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        script.load_allowed_roots(allow)


def test_resolve_cwd_allows_an_instance_listed_root(tmp_path):
    script = _load_script()
    foreign = tmp_path / "authorised-repo"
    foreign.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(foreign)]}) + "\n", encoding="utf-8")
    assert script.resolve_cwd(str(foreign), allowed_file=allow) == foreign.resolve()


def test_resolve_cwd_allows_a_subdirectory_of_an_instance_listed_root(tmp_path):
    script = _load_script()
    foreign = tmp_path / "authorised-repo"
    inside = foreign / "frontend"
    inside.mkdir(parents=True)
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(foreign)]}) + "\n", encoding="utf-8")
    assert script.resolve_cwd(str(inside), allowed_file=allow) == inside.resolve()


def test_resolve_cwd_still_refuses_an_unlisted_foreign_root_when_allowlist_exists(
    tmp_path,
):
    script = _load_script()
    listed = tmp_path / "authorised-repo"
    listed.mkdir()
    other = tmp_path / "some-other-repo"
    other.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(listed)]}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="only inside its own repository"):
        script.resolve_cwd(str(other), allowed_file=allow)


def test_allowed_cwds_instance_file_is_gitignored_and_the_example_ships():
    """PRODUCT ships the shape; INSTANCE keeps the machine paths."""
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/allowed-cwds.json" in ignored
    example = json.loads(
        Path(".harness/allowed-cwds.example.json").read_text(encoding="utf-8")
    )
    assert example["roots"] == []
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            ".harness/allowed-cwds.json",
            ".harness/allowed-cwds.example.json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    ).stdout.split()
    assert ".harness/allowed-cwds.example.json" in tracked
    assert ".harness/allowed-cwds.json" not in tracked


def test_dry_run_outside_this_repository_is_refused_and_prints_no_command(
    tmp_path, capsys
):
    script = _load_script()
    outside = tmp_path / "some-other-repo"
    outside.mkdir()
    code = script.main(["--dry-run", "--json", "--cwd", str(outside), "noop"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "refused"
    assert "repository" in payload["reason"]
    assert str(outside.resolve()) in payload["reason"]
    assert "command" not in payload


def test_every_write_admitted_form_proves_read_write_stage_commit_and_index_isolation(
    tmp_path,
):
    script = _load_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tracked.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "seed")
    indexes: list[Path] = []
    for form in script.WORKSPACE_FORMS:
        dest = tmp_path / form
        workspace = script.probe_workspace_form(
            form, repo, dest, runtime_id="grok", runtime_version="1.0"
        )
        assert workspace.form == form
        assert workspace.index_path.exists()
        indexes.append(workspace.index_path)
    assert len(set(indexes)) == len(indexes)


def test_failed_workspace_probe_does_not_reach_run_process(tmp_path, monkeypatch):
    script = _load_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tracked.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "seed")

    def boom(*_args, **_kwargs):
        raise AssertionError("run_process must not run after a failed workspace probe")

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", boom)
    monkeypatch.setattr(
        seam("dispatch_workspace"),
        "provision_isolated_workspace",
        lambda *_args, **_kwargs: "linked_worktree failed: probe refused",
    )
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="grok"),
        task="pong",
        cwd=repo,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=("src",),
    )
    assert payload["status"] == "failed"
    assert code == 1
    assert "probe refused" in payload["reason"]
    events, _rejected = read_all(tmp_path / "log")
    kinds = [event.kind for event in events]
    assert "dispatch.outcome" in kinds
    assert "work_item.opened" in kinds
    assert "work_item.completed" in kinds


def test_unready_native_item_does_not_reach_run_process(tmp_path, monkeypatch):
    from consilient import work_items

    script = _load_script()

    def boom(*_args, **_kwargs):
        raise AssertionError("run_process must not run for an unready native item")

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", boom)
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="grok"),
        task="pong",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        native_claim={
            "ticket": "native:missing",
            "revision": 1,
            "task_family": "code",
            "protocol_id": "pytest",
            "protocol_version": "v1",
        },
    )
    assert payload["status"] == "refused"
    assert code == 2
    assert "unready" in payload["reason"]
    events, _rejected = read_all(tmp_path / "log")
    assert work_items.OPENED not in [
        event.kind for event in events if event.data.get("run_id")
    ]
    del work_items
