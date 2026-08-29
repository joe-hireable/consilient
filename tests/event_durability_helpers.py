"""The event builder shared by the durable-append checks.

Not named test_*, so pytest does not collect it. It is on sys.path because pytest
prepends the directory of every collected test module, and tests/ holds no __init__.py —
and because the `spawn` start method hands the parent's sys.path to the child, the
worker processes that re-import the test module can import it too.

`ev` is a constructor, not a fixture: it returns a schema-valid event and takes keyword
overrides, so each test spells out only the field it is varying. It sits here rather
than being copied because a durability suite that builds its own events three different
ways can drift into checking its own builder instead of `events.append`."""

from datetime import datetime, timezone
from consilient.events import SCHEMA_VERSION


def ev(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "test.durability",
        "actor": "durability-test",
        "data": {},
    }
    base.update(over)
    return base
