"""M01 — the capture fixtures shared by the records suites.

``_records`` imports ``consilient.records`` lazily and fails the test rather than
erroring at collection, so a missing module reports as M01's own failure instead of
taking the session down. ``_capture`` is the single call site for ``capture_file`` in
the suite: every test that installs an object goes through it, so the workspace root,
object root, log directory, actor, consent purpose and retention class are fixed in one
place and cannot drift apart between the success file and the refusal file. ``_events``
reads the whole log and asserts that nothing was rejected, which is why a test asserting
no event can assert the log is genuinely empty rather than that its own event was merely
dropped on the floor."""

import importlib
from pathlib import Path
from typing import Any
import pytest
from consilient import events

OBJECTS = Path(".harness/objects")

LOG = Path(".harness/log")


def _records() -> Any:
    try:
        return importlib.import_module("consilient.records")
    except ModuleNotFoundError as exc:
        if exc.name != "consilient.records":
            raise
        pytest.fail("M01 requires the missing consilient.records module")


def _capture(
    workspace: Path,
    payload: bytes = b"record bytes\n",
    *,
    relative: str = "inputs/record.bin",
    media_type: str = "application/octet-stream",
) -> tuple[Any, Path]:
    source = workspace / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(payload)
    ref = _records().capture_file(
        source,
        workspace_root=workspace,
        object_root=workspace / OBJECTS,
        log_dir=workspace / LOG,
        actor="records-test",
        media_type=media_type,
        consent_purpose="task-evidence",
        retention_class="project",
    )
    return ref, source


def _events(workspace: Path) -> list[events.Event]:
    accepted, rejected = events.read_all(workspace / LOG)
    assert rejected == []
    return accepted
