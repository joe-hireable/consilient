"""What the harness is actually handed — the brief, and everything assembled into it.

The task reaches the child by reference, never inline: the command line carries the path
to `brief.md` and no sentinel from the task text, which is what keeps `$(touch escaped)`
and backticks from being interpreted by a shell along the way. What the file contains is
pinned layer by layer — invariant core, selected skills, recall pack and adapted layer —
and the recorded `instructions.assembled` event carries an `assembly_id` that is the
sha256 of the delivered text, so a brief that was changed after recording cannot pass as
the one that was recorded. Cutting any of the live caller, the delivery or the recording
breaks that test, which is why single dispatch and fan-out are both driven through it.

The recall pack is read from the trajectory, so a brief written with no log is the task
alone and one written beside a log carries the prior outcome. Capability context is
fail-closed in the same file because it is another thing injected into the task:
inventory and request must be passed together, an unknown capability is refused, and an
inventory entry with no gate defaults to gated and is refused too. That default was made
real by Unit AF; the fixture here predates it and had been relying on absence meaning
permission — declaring the grant is the honest repair, since relaxing the check to admit
an ungated entry would delete the guarantee instead."""

from family_source import seam

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient.harness import (
    DEFAULT_POOLS,
    Decision,
    FanoutDecision,
    harness_by_id,
)
from dispatch_helpers import (
    CAP_HELP,
    INSTALLED,
    _load_script,
)


@pytest.mark.parametrize("harness_id", ("claude", "grok", "codex"))
def test_brief_is_delivered_by_reference(monkeypatch, tmp_path, harness_id):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "find_claude", lambda: "claude")
    monkeypatch.setattr(seam("dispatch_evidence"), "find_grok", lambda: "grok")
    monkeypatch.setattr(seam("dispatch_launch"), "find_codex", lambda: "codex")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
    monkeypatch.setattr(seam("dispatch_evidence"), "metered_grok_reason", lambda: None)
    harness = harness_by_id(harness_id)
    assert harness is not None
    brief = (tmp_path / "brief.md").resolve()
    task = "INLINE_TASK_SENTINEL $(touch escaped) `also escaped`"

    built = script.build_command(
        harness,
        task=task,
        cwd=tmp_path,
        brief=brief,
        model=None,
    )

    assert isinstance(built, list)
    command = " ".join(str(part) for part in built)
    assert "INLINE_TASK_SENTINEL" not in command
    assert brief.as_posix() in command


def test_live_dispatches_consume_recorded_instruction_assemblies(monkeypatch, tmp_path):
    """Cutting either live caller, delivery, or recording breaks this test."""
    script = _load_script()
    active_log = tmp_path / "single-log"
    observed = []

    def fake_build_command(_harness, **kwargs):
        return ["agent", str(kwargs["brief"])]

    def fake_run_process(argv, *, stdout_path, **_kwargs):
        brief_path = Path(argv[-1])
        brief = brief_path.read_text(encoding="utf-8")
        # `read_all` is imported into the siblings that use it, not into the entry point,
        # since the 28 August 2026 split.
        events, rejected = seam("dispatch_evidence").read_all(active_log)
        assemblies = [
            event for event in events if event.kind == "instructions.assembled"
        ]
        observed.append(
            {
                "brief": brief,
                "recall": brief_path.with_name("recall.md").read_text(encoding="utf-8"),
                "assemblies": assemblies,
                "rejected": rejected,
            }
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("pong\n", encoding="utf-8")
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", fake_build_command)
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
    grok = harness_by_id("grok")
    codex = harness_by_id("codex")
    assert grok is not None and codex is not None

    single, single_code = script.dispatch_one(
        decision=Decision("run", grok, "selected grok", ("codex",)),
        task="pong",
        cwd=tmp_path,
        log_dir=active_log,
        runs_dir=tmp_path / "single-runs",
        timeout_s=5,
        model=None,
        dry_run=False,
    )
    assert single_code == 0 and single["status"] == "ok"

    active_log = tmp_path / "fanout-log"
    fanout, fanout_code = script.dispatch_fanout(
        decision=FanoutDecision("run", grok, codex, "two families", ()),
        task="pong",
        cwd=tmp_path,
        log_dir=active_log,
        runs_dir=tmp_path / "fanout-runs",
        timeout_s=5,
        model=None,
        dry_run=False,
    )
    assert fanout_code == 0 and fanout["status"] == "agree"

    assert [len(item["assemblies"]) for item in observed] == [1, 1, 2]
    for item in observed:
        brief = item["brief"]
        assert brief.startswith("pong\n")
        assert "# Invariant core" in brief
        assert "# Skills selected for this task" in brief
        assert "# Recall pack" in brief
        assert "# Adapted layer" in brief
        assert "`recall.md` beside this brief" in brief
        assert "work_item.opened" in item["recall"]
        assert not item["rejected"]
        assembly = item["assemblies"][-1]
        assert assembly.data["recall"]["query"] == "pong"
        delivered = brief[brief.index("# Invariant core") :]
        assert (
            assembly.data["assembly_id"]
            == hashlib.sha256(delivered.encode("utf-8")).hexdigest()
        )


def test_write_brief_without_a_log_is_the_task_alone(tmp_path):
    script = _load_script()
    brief = script.write_brief(tmp_path / "run", "pong")
    assert brief.read_text(encoding="utf-8") == "pong\n"


def test_main_injects_one_fail_closed_task_capability_context(
    monkeypatch, tmp_path, capsys
):
    script = _load_script()
    now = datetime.now(timezone.utc).isoformat()
    headroom = tmp_path / "headroom.json"
    headroom.write_text(
        json.dumps(
            {
                "observed_at": now,
                "source": "test",
                "pools": {
                    pool.name: {
                        "used_percent": 10,
                        "exhausted": False,
                        "note": "test",
                    }
                    for pool in DEFAULT_POOLS
                },
            }
        ),
        encoding="utf-8",
    )
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            {
                "allowlist": [
                    {
                        "kind": "tool",
                        "name": "pytest",
                        "available": True,
                        "provenance": ["probe:pytest"],
                        # An entry with no gate defaults to "gated" and is refused, which is
                        # what this test's own name asks for. Unit AF made that default real;
                        # this fixture predates it and had been relying on absence meaning
                        # permission. Declaring the grant is the honest repair -- relaxing the
                        # check to admit an ungated entry would delete the guarantee instead.
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
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "capabilities": [
                    {"kind": "tool", "name": "pytest", "reason": "verify task"}
                ]
            }
        ),
        encoding="utf-8",
    )
    captured = {}
    monkeypatch.setattr(seam("dispatch_workspace"), "probe_all", lambda: INSTALLED)

    def fake_dispatch_one(**kwargs):
        captured["task"] = kwargs["task"]
        return {"status": "ok"}, 0

    monkeypatch.setattr(seam("dispatch_single"), "dispatch_one", fake_dispatch_one)

    code = script.main(
        [
            "pong",
            "--cwd",
            str(Path.cwd()),
            "--headroom",
            str(headroom),
            "--harness",
            "grok",
            "--capability-inventory",
            str(inventory),
            "--capability-request",
            str(request),
            "--json",
        ]
    )

    assert code == 0, capsys.readouterr().out
    task = captured["task"]
    assert "Selected capability context" in task
    assert '"name":"pytest"' in task
    assert '"reason":"verify task"' in task


def test_capability_context_refuses_unpaired_or_unknown_inputs(tmp_path):
    script = _load_script()
    with pytest.raises(ValueError, match="must be passed together"):
        script.task_with_capabilities("pong", str(tmp_path / "one.json"), None)

    inventory = tmp_path / "inventory.json"
    request = tmp_path / "request.json"
    inventory.write_text(json.dumps({"allowlist": []}), encoding="utf-8")
    request.write_text(
        json.dumps(
            {"capabilities": [{"kind": "tool", "name": "missing", "reason": "needed"}]}
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown capability"):
        script.task_with_capabilities("pong", str(inventory), str(request))


def test_write_brief_includes_a_recall_pack_from_the_log(tmp_path):
    from datetime import datetime, timezone

    from consilient.events import SCHEMA_VERSION, append

    script = _load_script()
    log = tmp_path / "log"
    log.mkdir()
    ts = datetime.now(timezone.utc).isoformat()
    append(
        log / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": "dispatch.outcome",
            "actor": "consilient.dispatch",
            "data": {
                "status": "ok",
                "harness": "grok",
                "task": "pong",
                "supervised": True,
            },
        },
    )
    brief = script.write_brief(tmp_path / "run", "continue the work", log_dir=log)
    text = brief.read_text(encoding="utf-8")
    assert text.startswith("continue the work")
    assert "Recall pack" in text
    assert "dispatch.outcome" in text
