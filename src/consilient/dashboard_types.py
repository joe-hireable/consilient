"""The names the payload and the renderer must agree on, and nothing else.

This module exists because two halves of the surface have to use the same words.
`build_payload` searches the trajectory for these field names; `_build_raci` searches
for the RACI four; the tests reach for `RACI_FIELDS` and `WORK_ITEM_FIELDS` to check
that neither half has drifted. Holding them in one leaf module is what lets every other
file in the family import downwards and never sideways.

The field tuples are the record's known blind spots, written down. Each is checked
against the real trajectory rather than assumed absent — `build_payload` counts
occurrences, so a gap closes itself the moment events start carrying the field.

`Payload` is the shape at the render boundary: every panel's payload is a
differently-shaped JSON object, exactly as `cli.CommandResult` is, and values are
escaped at emit rather than trusted here.
"""

from typing import Any

# Every panel's payload is a differently-shaped JSON object at the render boundary, exactly
# as `cli.CommandResult` is. Values are escaped at emit, never trusted here.
Payload = dict[str, Any]

# Fields the record would need before the corresponding question could be answered from it.
# Each is checked against the real trajectory rather than assumed absent: `build_payload`
# counts occurrences, so a gap closes itself the moment events start carrying the field.
SPAWN_FIELDS = ("parent", "parent_id", "spawned_by", "session_id")

LIFECYCLE_FIELDS = ("started_at", "finished_at", "heartbeat_at", "state")

READ_FIELDS = ("reads", "inputs", "depends_on")

RACI_FIELDS = ("accountable", "consulted", "informed", "responsible")

WORK_ITEM_FIELDS = ("work_item", "ticket", "decision_id")
