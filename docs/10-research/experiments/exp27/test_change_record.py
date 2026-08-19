"""Executable invariant checks for ADR-0029."""

from change_record import validate_change_record


def must_reject(record):
    try:
        validate_change_record(record)
    except ValueError:
        return
    raise AssertionError(f"record should have been rejected: {record}")


if __name__ == "__main__":
    assert validate_change_record(
        {
            "effect": {
                "actions": ["invalidate_capability", "require_probe"],
                "headroom_mutation_permitted": False,
            }
        }
    )
    for action in (
        "increase_headroom",
        "decrease_used",
        "move_reset",
        "mark_headroom_usable",
    ):
        must_reject(
            {
                "effect": {
                    "actions": [action],
                    "headroom_mutation_permitted": False,
                }
            }
        )
    must_reject({"effect": {"actions": ["invalidate_capability"]}})
    print("EXP-27 change-record invariant checks pass")
