"""Collect unconditioned beta rows from third-party upstream PRs we did not write.

This is the Z10 collector. We run our composite verifier over a PR someone else
submitted, stamp that verdict with the commit it judged and the time, then later
record what the maintainer decided. The maintainer has never seen our checks.

Must not comment, review or approve the upstream PR: influencing the decision
reintroduces the dependence this design exists to remove.

This measures the family ``third_party_upstream_prs:<repository>``. That is not
the family our harness produces. The figure may not be quoted as the harness's
own beta. See EXP-145.

    python scripts/upstream_verdicts.py record --in row.json --out rows.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

TASK_FAMILY_PREFIX = "third_party_upstream_prs:"
REPOSITORIES = (
    "pallets/itsdangerous",
    "joe-hireable/consilient",
)
CORRECTNESS = "correctness"
NON_VERDICT_KINDS = frozenset({"scope", "stale", "inactive", "fit", "style", "roadmap"})
FORBIDDEN_INTERACTIONS = frozenset({"comment", "review", "approve", "request_changes"})
REQUIRED = (
    "repository",
    "pr_id",
    "judged_commit",
    "verifier_accept",
    "verifier_ts",
    "human_verdict",
    "human_decision_ts",
    "decision_kind",
    "task_family",
    "interaction",
    "authored_by_us",
)


class UpstreamVerdictError(ValueError):
    """A row that would silently condition or backdate the sample."""


def _parse_ts(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise UpstreamVerdictError(f"{field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise UpstreamVerdictError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise UpstreamVerdictError(f"{field} must be an RFC3339 timestamp")
    return parsed


def record_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a complete prediction-then-outcome row.

    Refuses a verdict timestamped later than the maintainer's decision, a
    non-correctness closure, any interaction with the PR, and a row we authored.
    Does not set ``lower_bound_on_joint_error``.
    """
    missing = [name for name in REQUIRED if name not in row]
    if missing:
        raise UpstreamVerdictError(f"missing required field: {missing[0]}")

    repository = str(row["repository"])
    if repository not in REPOSITORIES:
        raise UpstreamVerdictError(f"repository {repository!r} is outside the sampling frame")

    if row["authored_by_us"] is not False:
        raise UpstreamVerdictError("row must be a PR we did not write")

    family = str(row["task_family"])
    expected = f"{TASK_FAMILY_PREFIX}{repository}"
    if family != expected:
        raise UpstreamVerdictError(
            f"task_family must be {expected!r}; this is not the harness family"
        )

    if row["decision_kind"] != CORRECTNESS:
        raise UpstreamVerdictError(
            "only a correctness decision is a verdict; scope, staleness and "
            "inactivity are not counted"
        )

    interaction = str(row["interaction"])
    if interaction in FORBIDDEN_INTERACTIONS or interaction != "none":
        raise UpstreamVerdictError(
            "must not interact with the upstream PR; comment, review and approve "
            "reintroduce dependence"
        )

    human_verdict = str(row["human_verdict"])
    if human_verdict not in {"accept", "reject"}:
        raise UpstreamVerdictError("human_verdict must be accept or reject")

    verifier_accept = row["verifier_accept"]
    if not isinstance(verifier_accept, bool):
        raise UpstreamVerdictError("verifier_accept must be a bool")

    judged = str(row["judged_commit"])
    if len(judged) < 7:
        raise UpstreamVerdictError("judged_commit is required")

    verifier_ts = _parse_ts(row["verifier_ts"], "verifier_ts")
    decision_ts = _parse_ts(row["human_decision_ts"], "human_decision_ts")
    if verifier_ts > decision_ts:
        raise UpstreamVerdictError(
            "verifier verdict postdates the maintainer's decision; not a prediction"
        )

    recorded = {name: row[name] for name in REQUIRED}
    recorded["pr_id"] = str(row["pr_id"])
    recorded["judged_commit"] = judged
    recorded["verifier_accept"] = verifier_accept
    recorded["human_verdict"] = human_verdict
    recorded["decision_kind"] = CORRECTNESS
    recorded["interaction"] = "none"
    recorded["authored_by_us"] = False
    recorded["task_family"] = expected
    # Explicitly omitted: lower_bound_on_joint_error. The protocol lives in EXP-145;
    # this collector does not assert the bound.
    return recorded


def schema_cells(rows: Iterable[Mapping[str, Any]]) -> set[tuple[bool, str]]:
    """The 2x2 cells present in recorded rows."""
    return {
        (bool(row["verifier_accept"]), str(row["human_verdict"])) for row in rows
    }


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="upstream_verdicts.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=("record",), help="record one validated row")
    parser.add_argument("--in", dest="source", required=True, help="JSON object for one PR")
    parser.add_argument(
        "--out",
        required=True,
        help="JSONL dest (instance data; do not publish)",
    )
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.source).read_text(encoding="utf-8"))
    recorded = record_row(payload)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(recorded, ensure_ascii=False) + "\n")
    print(json.dumps(recorded, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
