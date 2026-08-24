"""Prove CI refuses a measurement result without prior registration."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from consilient import projection  # noqa: E402
from consilient.events import (  # noqa: E402
    MEASUREMENT_ACTOR,
    MEASUREMENT_REGISTERED_KIND,
    MEASUREMENT_RESULT_KIND,
    SCHEMA_VERSION,
    canonical,
)


RUN_ID = "self-test-measurement"


def _event(kind: str) -> dict[str, object]:
    data: dict[str, object] = {"run_id": RUN_ID}
    if kind == MEASUREMENT_REGISTERED_KIND:
        data.update({"config_hash": "a" * 64, "hardware_id": "self-test"})
    else:
        data["fixture"] = "self-test"
    return {
        "v": SCHEMA_VERSION,
        "ts": "2026-08-24T00:00:00+00:00",
        "event": kind,
        "actor": MEASUREMENT_ACTOR,
        "data": data,
    }


def _write_log(path: Path, *events: dict[str, object]) -> None:
    path.mkdir(parents=True)
    (path / "2026-08-24.jsonl").write_text(
        "\n".join(canonical(event) for event in events) + "\n",
        encoding="utf-8",
    )


def measurement_failures(log_dir: Path, db: Path) -> list[str]:
    """Return missing-registration failures from replay."""
    conn = projection.build(log_dir, db)
    try:
        return [
            str(row["reason"])
            for row in projection.relational_quarantines(conn)
            if "measurement.registered" in str(row["reason"])
            and "measurement.result" in str(row["reason"])
        ]
    finally:
        conn.close()


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="measurement-recorded-") as scratch:
        root = Path(scratch)
        orphan = root / "orphan"
        _write_log(orphan, _event(MEASUREMENT_RESULT_KIND))
        assert measurement_failures(orphan, root / "orphan.db"), (
            "an unregistered measurement result was not detected"
        )

        registered = root / "registered"
        _write_log(
            registered,
            _event(MEASUREMENT_REGISTERED_KIND),
            _event(MEASUREMENT_RESULT_KIND),
        )
        assert not measurement_failures(registered, root / "registered.db"), (
            "a registered measurement result was refused"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("choose --self-test")
    self_test()
    print("measurement-recorded self-test passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
