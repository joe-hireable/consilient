"""One provider's consumption against one ceiling, over one resetting window.

A distinct subject from the rest of the payload: usage is not derived from the
trajectory's structure but projected from the latest `budget.state` event, and the note
`read_usage` returns says so in the page — the reader is told what the figure was
projected from and when it was observed, rather than being shown a bare number.

Small on purpose. It is separate because it has a different source, not because it was
too large to keep."""

from dataclasses import dataclass
from .events import Event
from .dashboard_types import (
    Payload,
)

from .dashboard_css import (
    CSS,
)


__all__ = [
    "CSS",
    "Payload",
    "UsageWindow",
    "read_usage",
]


@dataclass(frozen=True)
class UsageWindow:
    """One provider's consumption against one ceiling, over one resetting window.

    **This is the consumer side of an interface another agent owns.** The usage and limits
    data layer was being built concurrently on 21 Aug 2026 and had committed nothing to
    `wt/usage` when this was written [measured: `git diff wt/observability wt/usage` was
    empty]. Rather than build a second set of collectors — which would guarantee two
    disagreeing numbers — this declares the shape the dashboard consumes and reads the only
    source already in the record.

    To supply real data, provide windows with these fields. Nothing here opens a socket,
    reads a credential or shells out; if a provider needs a credential it is that provider's
    problem to solve locally, and an unsupplied window renders as "not connected" rather
    than as zero. `used` and `ceiling` are strings because they are money and because
    `events.py` already carries money as Decimal strings.
    """

    provider: str
    plan: str
    window: str
    used: str
    ceiling: str | None
    unit: str
    resets_at: str | None
    observed_at: str
    source: str

    def as_dict(self) -> Payload:
        d: Payload = {
            "provider": self.provider,
            "plan": self.plan,
            "window": self.window,
            "used": self.used,
            "ceiling": self.ceiling,
            "unit": self.unit,
            "resets_at": self.resets_at,
            "observed_at": self.observed_at,
            "source": self.source,
            "fraction": None,
        }
        if self.ceiling is not None:
            try:
                limit = float(self.ceiling)
                if limit > 0:
                    d["fraction"] = min(1.0, max(0.0, float(self.used) / limit))
            except (TypeError, ValueError):
                d["fraction"] = None
        return d


def read_usage(events: list[Event]) -> tuple[list[UsageWindow], str]:
    """Usage windows from the record alone. No network, no credential, no collector.

    `budget.state` events already carry `weekly_spent`, `monthly_spent`, `observed_at` and a
    validated provider and currency (`events._check_budget_contract`), so where they exist
    this is a projection in exactly the sense the SQLite database is. Where they do not, the
    honest answer is an empty list and a reason — not a zero, which would read as "nothing
    spent" when it means "nothing observed".
    """
    latest: Event | None = None
    for event in events:
        if event.kind == "budget.state":
            latest = event
    if latest is None:
        return [], (
            "No budget.state events in the trajectory, so no metered spend has been "
            "observed. This is an absence of observation, not an observation of zero."
        )
    data = latest.data
    provider = str(data.get("provider", "unknown"))
    observed = str(data.get("observed_at", latest.raw["ts"]))
    windows = [
        UsageWindow(
            provider=provider,
            plan="metered",
            window=name,
            used=str(data.get(field, "0")),
            ceiling=(str(data[cap]) if cap in data else None),
            unit=str(data.get("currency", "USD")),
            resets_at=(str(data[reset]) if reset in data else None),
            observed_at=observed,
            source=f"{latest.path}:{latest.line}",
        )
        for name, field, cap, reset in (
            ("weekly", "weekly_spent", "weekly_cap", "weekly_resets_at"),
            ("monthly", "monthly_spent", "monthly_cap", "monthly_resets_at"),
        )
        if field in data
    ]
    return (
        windows,
        f"Projected from the latest budget.state event, observed {observed}.",
    )
