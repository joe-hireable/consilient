"""Builders shared by the three halves of V0-41, kept in one place so that a change to
the capability.gap payload breaks the contract, the wiring and the view together rather
than letting them drift apart.

`_gap_data` is the canonical well-formed gap — asked, attempted, failure class, detail,
closure, repair, run_id, source — and every test that needs a malformed one deforms a
copy of it rather than writing its own. `_append_gap` writes that payload to the day's
log file under the same name the reader expects.

`INSTALLED` presents every registered harness as present at version 1.0 so that a
refusal under test is a refusal about pools or claims, never an accident of what happens
to be installed on the machine running the suite."""

from pathlib import Path
from consilient.events import append
from consilient.harness import (
    HARNESSES,
    Probe,
)

INSTALLED = tuple(
    Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
)


def _gap_data(**overrides):
    data = {
        "asked": "deploy the staging environment",
        "attempted": "grok",
        "failure": "failed",
        "detail": "exit 1: terraform not configured",
        "closure": "retry",
        "repair": "re-dispatch the task",
        "run_id": "run-1",
        "source": "dispatch.outcome",
    }
    data.update(overrides)
    return data


def _append_gap(log_dir: Path, ts: str, **overrides):
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": 1,
            "ts": ts,
            "event": "capability.gap",
            "actor": "dispatch",
            "data": _gap_data(**overrides),
        },
    )
