"""Research-time invariant for ADR-0029 change-intelligence records."""


FORBIDDEN_RESOURCE_EFFECTS = {
    "increase_headroom",
    "decrease_used",
    "move_reset",
    "mark_headroom_usable",
}


def validate_change_record(record):
    """Reject change intelligence that claims resource-ledger authority."""
    effect = record.get("effect") or {}
    actions = set(effect.get("actions") or [])
    forbidden = actions & FORBIDDEN_RESOURCE_EFFECTS
    if forbidden:
        raise ValueError(
            "change intelligence cannot mutate resource state: "
            + ", ".join(sorted(forbidden))
        )
    if effect.get("headroom_mutation_permitted") is not False:
        raise ValueError("headroom_mutation_permitted must be explicitly false")
    return True
