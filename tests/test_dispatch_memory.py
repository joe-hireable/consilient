"""M05 — reconstructable dispatch envelope.

A launcher exit code is not acceptance. Reconstruction compares object digests
from the trajectory and the private object store in a fresh process.
"""

from __future__ import annotations

from family_source import seam

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from consilient.events import read_all
from consilient.harness import Decision, harness_by_id
from consilient.instructions import assemble, bind_recall_receipt, record_assembly
from consilient.recall import RECEIPT_BEGIN, RECEIPT_END


ROOT = Path(__file__).resolve().parents[1]
DISPATCH_PATH = ROOT / "scripts" / "dispatch.py"
SRC = ROOT / "src"
SECRET_TOKEN = "sk" + "-or-v1-" + ("a" * 40)
VERSION_A = "a" * 64


def _load_script():
    name = "consilient_dispatch_memory_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _skills(root: Path) -> Path:
    skills = root / "skills"
    alpha = skills / "alpha-skill"
    alpha.mkdir(parents=True)
    (alpha / "SKILL.md").write_text(
        "---\n"
        "name: alpha-skill\n"
        "description: Use when measuring beta and verifier outcomes.\n"
        "---\n\n"
        "Alpha body.\n",
        encoding="utf-8",
    )
    return skills


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / ".harness" / "log").mkdir(parents=True)
    (workspace / ".harness" / "objects").mkdir(parents=True)
    (workspace / ".harness" / "dispatch").mkdir(parents=True)
    return workspace


def _selection() -> dict[str, object]:
    return {
        "schema_version": 1,
        "capabilities": [
            {
                "kind": "tool",
                "name": "pytest",
                "provenance": ["probe:pytest"],
                "reason": "verify task",
            }
        ],
        "inventory_status": "unmeasured",
        "omissions": [],
        "refusals": [],
        "selected_manifests": [
            {
                "identity": "tool:pytest",
                "version_digest": VERSION_A,
                "status": "active",
                "execution_contract_key": "b" * 64,
                "destination_class": "local-harness",
            }
        ],
    }


def _valid_receipt_pack() -> str:
    receipt = {
        "bytes_used": 0,
        "candidate_ids": [],
        "context_complete": True,
        "continuation_cursor": None,
        "omitted": [],
        "prefix_digest": "c" * 64,
        "query_digest": "d" * 64,
        "scan_complete": True,
        "scanned_universe_count": 0,
        "selected_ids": [],
        "semantic_status": "unknown",
    }
    body = json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "recall body\n" + RECEIPT_BEGIN + body + RECEIPT_END + "\n"


def _objects(workspace: Path) -> list[Path]:
    root = workspace / ".harness" / "objects"
    if not root.exists():
        return []
    return [path for path in root.rglob("*") if path.is_file() and ".capture-" not in path.name]


def _object_bytes(workspace: Path) -> set[bytes]:
    payloads: set[bytes] = set()
    for path in _objects(workspace):
        payloads.add(path.read_bytes())
    return payloads


def _trajectory_text(workspace: Path) -> str:
    log = workspace / ".harness" / "log"
    chunks: list[str] = []
    for path in sorted(log.glob("*.jsonl")):
        chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "".join(chunks)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _reconstruct_in_new_process(workspace: Path, run_id: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from consilient.instructions import reconstruct_envelope\n"
        "result = reconstruct_envelope(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])\n"
        "print(json.dumps({"
        "'ok': result.ok, "
        "'parts': [{'name': part.name, 'ok': part.ok, 'digest': part.digest, "
        "'detail': part.detail} for part in result.parts]"
        "}))\n"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(workspace / ".harness" / "log"),
            str(workspace),
            run_id,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(ROOT),
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return payload


def test_bind_recall_receipt_digests_a_canonical_block() -> None:
    pack = _valid_receipt_pack()
    binding = bind_recall_receipt(pack)
    assert binding["status"] == "ok"
    digest = binding["digest"]
    assert isinstance(digest, str) and len(digest) == 64
    repeated = bind_recall_receipt(pack)
    assert repeated == binding


def test_truncated_recall_receipt_is_an_explicit_refusal() -> None:
    pack = _valid_receipt_pack()[:-12]
    binding = bind_recall_receipt(pack)
    assert binding["status"] == "refused"
    assert "receipt" in str(binding["reason"]).casefold() or "terminated" in str(
        binding["reason"]
    ).casefold() or "missing" in str(binding["reason"]).casefold()


def test_assemble_binds_m04_manifests_and_does_not_invent_them(tmp_path: Path) -> None:
    skills = _skills(tmp_path)
    log = tmp_path / "log"
    log.mkdir()
    bare = assemble(skills, log, task="measure the beta verifier outcome")
    assert bare.capability_manifests == ()
    assert bare.recall_receipt["status"] in {"ok", "refused"}

    selected = assemble(
        skills,
        log,
        task="measure the beta verifier outcome",
        capability_selection=_selection(),
    )
    assert selected.capability_manifests == (
        {"identity": "tool:pytest", "version_digest": VERSION_A},
    )
    event = record_assembly(
        log,
        selected,
        task="measure the beta verifier outcome",
        pre_run_records={"task": {"status": "absent", "reason": "fixture"}},
    )
    data = event["data"]
    assert data["capability_manifests"] == [
        {"identity": "tool:pytest", "version_digest": VERSION_A}
    ]
    assert data["recall_receipt"]["status"] in {"ok", "refused"}
    assert data["pre_run_records"]["task"]["status"] == "absent"


def _dispatch_with_fake(
    monkeypatch,
    workspace: Path,
    *,
    task: str = "measure the beta verifier outcome",
    write_stdout: str | None = "ok-output\n",
    write_stderr: str | None = "ok-stderr\n",
    manifest: dict[str, object] | None = None,
    verifier: dict[str, object] | None = None,
    extra_artefact: Path | None = None,
    capability_selection: dict[str, object] | None = None,
    exit_code: int = 0,
) -> tuple[Any, dict[str, object], int]:
    script = _load_script()
    skills = _skills(workspace)
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_SKILLS", skills)
    monkeypatch.setattr(seam("dispatch_evidence"), "git_diff_bytes", lambda _cwd: 0)
    monkeypatch.setattr(
        seam("dispatch_invocation"),
        "build_command",
        lambda _harness, **kwargs: ["agent", str(kwargs["brief"])],
    )

    def fake_run_process(_argv, *, stdout_path, stderr_path, **_kwargs):
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        if write_stdout is not None:
            stdout_path.write_bytes(write_stdout.encode("utf-8"))
        if write_stderr is not None:
            stderr_path.write_bytes(write_stderr.encode("utf-8"))
        if manifest is not None:
            (stdout_path.parent / "artefact-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8", newline="\n"
            )
        if verifier is not None:
            (stdout_path.parent / "verifier-outcome.json").write_text(
                json.dumps(verifier), encoding="utf-8", newline="\n"
            )
        if extra_artefact is not None:
            extra_artefact.parent.mkdir(parents=True, exist_ok=True)
            if not extra_artefact.exists():
                extra_artefact.write_text("outside-bytes\n", encoding="utf-8")
        return exit_code, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
    grok = harness_by_id("grok")
    assert grok is not None
    payload, code = script.dispatch_one(
        decision=Decision("run", grok, "selected grok", ("codex",)),
        task=task,
        cwd=workspace,
        log_dir=workspace / ".harness" / "log",
        runs_dir=workspace / ".harness" / "dispatch",
        timeout_s=5,
        model=None,
        dry_run=False,
        capability_selection=capability_selection,
    )
    return script, payload, code


def test_happy_path_envelope_reconstructs_byte_for_byte_in_a_fresh_process(
    monkeypatch, tmp_path: Path
) -> None:
    workspace = _workspace(tmp_path)
    stdout = "ok-output\n"
    stderr = "ok-stderr\n"
    manifest = {"artefacts": [{"path": "outputs/result.txt"}]}
    verifier = {"status": "pass", "check": "pytest"}
    (workspace / "outputs").mkdir()
    (workspace / "outputs" / "result.txt").write_text("result-bytes\n", encoding="utf-8")

    _script, payload, code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        write_stdout=stdout,
        write_stderr=stderr,
        manifest=manifest,
        verifier=verifier,
        capability_selection=_selection(),
    )
    assert payload["status"] == "ok"
    # Exit code is recorded, never treated as the envelope verdict.
    assert payload["exit_code"] == 0
    run_id = str(payload["run_id"])

    reconstructed = _reconstruct_in_new_process(workspace, run_id)
    assert reconstructed["ok"] is True
    names = {part["name"]: part for part in reconstructed["parts"]}
    for required in (
        "task",
        "instructions",
        "stdout",
        "stderr",
        "artefact_manifest",
        "verifier_outcome",
        "recall_receipt",
        "capability_manifests",
    ):
        assert names[required]["ok"] is True, required
    assert names["stdout"]["digest"] == _digest(stdout.encode("utf-8"))
    assert names["stderr"]["digest"] == _digest(stderr.encode("utf-8"))
    assert names["capability_manifests"]["digest"] == VERSION_A

    events, rejected = read_all(workspace / ".harness" / "log")
    assert rejected == []
    assembled = [event for event in events if event.kind == "instructions.assembled"]
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert len(assembled) == 1
    assert len(outcomes) == 1
    assert assembled[0].data["capability_manifests"][0]["identity"] == "tool:pytest"
    assert outcomes[0].data["output_records"]["stdout"]["status"] == "ok"
    assert outcomes[0].data["assembly_id"] == assembled[0].data["assembly_id"]


def test_missing_output_is_visible_as_an_absent_reference(
    monkeypatch, tmp_path: Path
) -> None:
    workspace = _workspace(tmp_path)
    _script, payload, _code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        write_stdout=None,
        write_stderr="err\n",
        manifest=None,
        verifier=None,
    )
    run_id = str(payload["run_id"])
    events, _rejected = read_all(workspace / ".harness" / "log")
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert outcomes
    stdout_ref = outcomes[-1].data["output_records"]["stdout"]
    assert stdout_ref["status"] in {"absent", "refused"}
    assert "reason" in stdout_ref
    reconstructed = _reconstruct_in_new_process(workspace, run_id)
    names = {part["name"]: part for part in reconstructed["parts"]}
    assert names["stdout"]["ok"] is False
    assert names["stdout"]["detail"]


def test_secret_bearing_output_enters_neither_object_store_nor_trajectory(
    monkeypatch, tmp_path: Path
) -> None:
    workspace = _workspace(tmp_path)
    secret_stdout = f"token={SECRET_TOKEN}\n"
    _script, payload, _code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        write_stdout=secret_stdout,
        write_stderr="ok-stderr\n",
    )
    events, _rejected = read_all(workspace / ".harness" / "log")
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert outcomes
    stdout_ref = outcomes[-1].data["output_records"]["stdout"]
    assert stdout_ref["status"] == "refused"
    assert SECRET_TOKEN not in json.dumps(stdout_ref)
    assert SECRET_TOKEN not in _trajectory_text(workspace)
    assert secret_stdout.encode("utf-8") not in _object_bytes(workspace)
    reconstructed = _reconstruct_in_new_process(workspace, str(payload["run_id"]))
    names = {part["name"]: part for part in reconstructed["parts"]}
    assert names["stdout"]["ok"] is False


def test_outside_root_artefact_is_refused_and_not_stored(
    monkeypatch, tmp_path: Path
) -> None:
    workspace = _workspace(tmp_path)
    outside = tmp_path / "outside" / "leak.bin"
    outside.parent.mkdir()
    outside.write_bytes(b"outside-payload\n")
    _script, payload, _code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        write_stdout="ok-output\n",
        manifest={"artefacts": [{"path": str(outside)}]},
        extra_artefact=outside,
    )
    events, _rejected = read_all(workspace / ".harness" / "log")
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    listed = outcomes[-1].data["output_records"]["listed_artefacts"]
    assert listed
    assert listed[0]["status"] == "refused"
    assert b"outside-payload\n" not in _object_bytes(workspace)
    reconstructed = _reconstruct_in_new_process(workspace, str(payload["run_id"]))
    names = {part["name"]: part for part in reconstructed["parts"]}
    assert names["listed_artefacts"]["ok"] is False


def test_exit_code_zero_is_not_envelope_acceptance(
    monkeypatch, tmp_path: Path
) -> None:
    workspace = _workspace(tmp_path)
    _script, payload, _code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        write_stdout="",
        write_stderr="",
        exit_code=0,
    )
    assert payload["status"] == "silent"
    assert payload["exit_code"] == 0
    run_id = str(payload["run_id"])
    reconstructed = _reconstruct_in_new_process(workspace, run_id)
    assert "ok" in reconstructed
    events, _rejected = read_all(workspace / ".harness" / "log")
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert outcomes[-1].data["status"] == "silent"


def test_capability_inventory_entry_point_stays_source_compatible(tmp_path: Path) -> None:
    script = _load_script()
    inventory = tmp_path / "inventory.json"
    request = tmp_path / "request.json"
    inventory.write_text(
        json.dumps(
            {
                "allowlist": [
                    {
                        "kind": "tool",
                        "name": "pytest",
                        "available": True,
                        "provenance": ["probe:pytest"],
                        "gate": {
                            "state": "admitted",
                            "reason": "exact_grant",
                            "grant_kind": "principal_authority",
                            "authority_event": {
                                "event_id": "evt-authority-1",
                                "event_kind": "human.approval",
                                "event_sha256": "b" * 64,
                            },
                            "decision_id": None,
                            "recovery_proof_ref": None,
                            "scope": [],
                            "operations": [],
                            "effect_classes": [],
                            "expires_at": "2099-01-01T00:00:00+00:00",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    request.write_text(
        json.dumps(
            {"capabilities": [{"kind": "tool", "name": "pytest", "reason": "verify task"}]}
        ),
        encoding="utf-8",
    )
    selection = script.load_capability_selection(str(inventory), str(request))
    assert selection is not None
    assert selection["capabilities"][0]["name"] == "pytest"
    injected = script.task_with_capabilities("pong", str(inventory), str(request))
    assert "Selected capability context" in injected
    assert script.load_capability_selection(None, None) is None


def test_no_capability_request_does_not_auto_select(monkeypatch, tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    _script, payload, _code = _dispatch_with_fake(
        monkeypatch,
        workspace,
        capability_selection=None,
    )
    events, _rejected = read_all(workspace / ".harness" / "log")
    assembled = [event for event in events if event.kind == "instructions.assembled"]
    assert assembled
    assert assembled[-1].data["capability_manifests"] == []
    reconstructed = _reconstruct_in_new_process(workspace, str(payload["run_id"]))
    names = {part["name"]: part for part in reconstructed["parts"]}
    assert names["capability_manifests"]["ok"] is True
    assert names["capability_manifests"]["digest"] is None
