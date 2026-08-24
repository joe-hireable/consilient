"""Print a production beta calculation over a bundled synthetic trajectory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.beta import compute  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    print("SYNTHETIC DEMO — not measured user beta; does not affect gates or routing.")
    rows = [
        {
            "task_family": "synthetic-demo",
            "verifier_version": "bundled-v1",
            "verifier_accept": index < 10,
            "human_verdict": "reject",
        }
        for index in range(40)
    ]
    print(
        compute(
            rows,
            task_family="synthetic-demo",
            verifier_version="bundled-v1",
        ).render()
    )


if __name__ == "__main__":
    main()
