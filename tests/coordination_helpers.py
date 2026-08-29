"""Fixtures shared by the coordination family after the split of
`tests/test_coordination.py`.

Four things are needed in more than one of the resulting modules and nothing else is.
`ROOT` and `DISPATCH_PATH` locate the repository and the dispatch script, because two of
the modules read source at the file level rather than importing it — the routing-wiring
pin and the lane order derived from the build plan both assert against text on disk.
`T0` is the frozen clock; every claim test states an instant rather than reading one, so
a lease boundary is arithmetic and not a race. `_live` reads the trajectory back and
projects it — the point being that a claim is a projection over events, never a lock
file, so every question about who holds a path is answered by replaying the log at a
named instant."""

from datetime import datetime, timezone
from pathlib import Path
from consilient import coordination
from consilient.events import read_all

ROOT = Path(__file__).resolve().parent.parent

DISPATCH_PATH = ROOT / "scripts" / "dispatch.py"

T0 = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


def _live(log: Path, *, now: datetime) -> tuple[coordination.Claim, ...]:
    events, rejected = read_all(log)
    assert not rejected
    return coordination.live_claims(events, now=now)
