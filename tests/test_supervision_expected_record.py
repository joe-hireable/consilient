"""BU-1 / N01: a dispatch that names no progress artefact is refused before spawn.

N00 can only read a channel that was declared, and declared before the child exists. A
dispatch that names nothing is unsupervised in exactly the way F-13 was, so the refusal
happens at configuration time and nothing is written — an expected record carrying no
artefact is the silent channel this unit exists to make impossible. The Temporal trap
ADR-0034 §4 records is that shape: a configured-but-unfed progress channel must fail
when it is configured, not quietly at runtime. Whitespace is not a declaration.

Declaring `brief.md` or `recall.md` is the same as declaring none. N00 measured why:
they are the dispatcher's own output, large and on disk before the child is spawned, so
if they count as the declared progress artefact every dead dispatch reads healthy — the
23 August failure exactly.

The ordering is the other half and it is checked from inside the spawn. The wrapper
writes `expected` before Popen, never after and never by goodwill; if the record only
appears once `run_process` has returned, the spawn happened unsupervised, which is F-13
with a file name on it. The refusal path is checked the same way: it raises and the
child is never started."""

from family_source import seam

import json
import pytest
from consilient import coordination
from consilient.harness import harness_by_id
from supervision_helpers import (
    _dirs,
    _script,
)


def test_dispatch_with_no_expected_artefact_raises(tmp_path, monkeypatch):
    """BU-1 / N01. A dispatch that names no progress artefact is refused before spawn.

    The Temporal trap ADR-0034 §4 records: a configured-but-unfed progress channel
    must fail at configuration time, not quietly at runtime. Whitespace is not a
    declaration. Nothing is written, because an expected record with no artefact
    is the silent channel this unit exists to make impossible.
    """
    script = _script()
    _log, runs = _dirs(tmp_path)
    spawned: list[object] = []

    def fake_run_process(*_a, **_k):
        spawned.append(True)
        return 0, False, 0.1, None

    # Direct construction: the named parameter is empty or absent.
    for artefact in ("", None, "   "):
        with pytest.raises(script.ExpectedArtefactError):
            script.write_expected(
                runs,
                run_id="n01-empty",
                arm="codex",
                unit="N01",
                expected_artefact=artefact,
                progress_deadline_s=600,
            )
    assert not (runs / "n01-empty.json").exists()

    # The spawn path raises the same way and does not start the child.
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    with pytest.raises(script.ExpectedArtefactError):
        script.run_harness(
            harness,
            task="pong",
            cwd=tmp_path,
            run_dir=runs / "n01-empty",
            timeout_s=5,
            model=None,
            run_id="n01-empty",
            expected_artefact="",
        )
    assert spawned == []


def test_expected_record_is_written_before_spawn(tmp_path, monkeypatch):
    """The wrapper writes `expected` before Popen, never after, never by goodwill.

    If this fails because the record appears after `run_process` returns, spawn
    happened unsupervised — F-13 with a file name on it.
    """
    script = _script()
    seen: dict[str, object] = {}
    run_id = "n01-before"
    record_path = tmp_path / f"{run_id}.json"

    def fake_run_process(*_a, **_k):
        seen["exists"] = record_path.exists()
        if record_path.exists():
            seen["record"] = json.loads(record_path.read_text(encoding="utf-8"))
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=tmp_path / run_id,
        timeout_s=90,
        model=None,
        run_id=run_id,
        expected_artefact="stdout.txt",
        unit="N01",
    )

    assert seen.get("exists") is True
    expected = seen["record"]["expected"]  # type: ignore[index]
    assert expected["run_id"] == run_id
    assert expected["arm"] == "codex"
    assert expected["unit"] == "N01"
    assert expected["artefact"] == "stdout.txt"
    assert expected["start_window_s"] == script.START_WINDOW_S
    assert expected["progress_deadline_s"] == 90
    assert expected["grace_s"] == coordination.CLAIM_GRACE_S


def test_dispatcher_written_files_are_not_a_progress_artefact(tmp_path):
    """N00 measured this: brief.md and recall.md are the dispatcher's own output.

    If they count as the declared progress artefact, every dead dispatch reads
    healthy — the 23 August failure exactly. Declaring one is the same as
    declaring none.
    """
    script = _script()
    _log, runs = _dirs(tmp_path)
    for name in ("brief.md", "recall.md", "nested/brief.md", "BRIEF.MD"):
        with pytest.raises(script.ExpectedArtefactError):
            script.write_expected(
                runs,
                run_id="n01-self",
                arm="codex",
                unit="N01",
                expected_artefact=name,
                progress_deadline_s=600,
            )
    assert not (runs / "n01-self.json").exists()
