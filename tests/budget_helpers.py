"""Builders for the `budget.state` snapshot and for the daily trajectory file it is
written to.

The ceiling decision, the state-trust refusals and the append-chokepoint contract all
need a well-formed snapshot to start from, so the two builders live here rather than in
whichever file happens to use them most. `write_state` recomputes the quarantine
fingerprint from the log's own rejections before appending, which is what lets a fresh
snapshot supersede an old quarantine; a test that hand-rolls the dictionary instead
loses that behaviour and the refusal it earns."""

from consilient.events import (
    SCHEMA_VERSION,
    append,
    read_all,
    rejection_digest,
)


def budget_state(
    now,
    *,
    weekly="0",
    monthly="0",
    currency="USD",
    observed_at=None,
    rejection_fingerprint=None,
):
    return {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "budget.state",
        "actor": "openrouter-probe",
        "data": {
            "provider": "openrouter",
            "currency": currency,
            "weekly_spent": weekly,
            "monthly_spent": monthly,
            "observed_at": (observed_at or now).isoformat(),
            "rejection_digest": rejection_fingerprint or rejection_digest([]),
        },
    }


def write_state(log_dir, now, **over):
    path = log_dir / f"{now.date().isoformat()}.jsonl"
    over.setdefault("rejection_fingerprint", rejection_digest(read_all(log_dir)[1]))
    append(path, budget_state(now, **over))
    return path
