"""Z10: unconditioned beta rows from third-party upstream PRs we did not write.

The sample is not filtered on our verifier's outcome. Both cells of the table
must be representable, and a verdict computed after the maintainer decided is
not a prediction.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from consilient import beta as beta_mod

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upstream_verdicts.py"

_spec = importlib.util.spec_from_file_location("upstream_verdicts", SCRIPT)
assert _spec is not None and _spec.loader is not None
upstream = importlib.util.module_from_spec(_spec)
sys.modules["upstream_verdicts"] = upstream
_spec.loader.exec_module(upstream)

UpstreamVerdictError = upstream.UpstreamVerdictError
record_row = upstream.record_row
schema_cells = upstream.schema_cells


def _row(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "repository": "pallets/itsdangerous",
        "pr_id": "42",
        "judged_commit": "a" * 40,
        "verifier_accept": True,
        "verifier_ts": "2026-08-25T10:00:00+00:00",
        "human_verdict": "reject",
        "human_decision_ts": "2026-08-25T12:00:00+00:00",
        "decision_kind": "correctness",
        "task_family": "third_party_upstream_prs:pallets/itsdangerous",
        "interaction": "none",
        "authored_by_us": False,
    }
    record.update(overrides)
    return record


def test_schema_accepts_checks_accepted_human_rejected_and_checks_rejected_human_accepted():
    """A schema that can only express one cell recreates verifier-conditioning in the data model."""
    accepted_rejected = record_row(_row())
    rejected_accepted = record_row(
        _row(
            pr_id="43",
            judged_commit="b" * 40,
            verifier_accept=False,
            human_verdict="accept",
        )
    )
    cells = schema_cells([accepted_rejected, rejected_accepted])
    assert (True, "reject") in cells
    assert (False, "accept") in cells


def test_verdict_timestamped_after_maintainer_decision_is_refused():
    """If our verdict is computed after the merge is visible it is not a prediction."""
    with pytest.raises(UpstreamVerdictError, match="postdates"):
        record_row(
            _row(
                verifier_ts="2026-08-25T13:00:00+00:00",
                human_decision_ts="2026-08-25T12:00:00+00:00",
            )
        )


def test_scope_stale_or_inactive_closure_is_not_a_verdict():
    for kind in ("scope", "stale", "inactive"):
        with pytest.raises(UpstreamVerdictError, match="correctness"):
            record_row(_row(decision_kind=kind))


def test_any_interaction_with_the_upstream_pr_is_refused():
    for action in ("comment", "review", "approve"):
        with pytest.raises(UpstreamVerdictError, match="interact"):
            record_row(_row(interaction=action))


def test_collector_does_not_set_lower_bound_or_lower_min_rejections():
    recorded = record_row(_row())
    assert recorded.get("lower_bound_on_joint_error") is not True
    assert beta_mod.MIN_REJECTIONS == 30


def test_register_names_the_family_the_frame_and_the_stopping_rule():
    text = (ROOT / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8"
    )
    heading = "### EXP-145 · Unconditioned human-verdict β on third-party PRs"
    start = text.index(heading)
    body = text[start:]
    assert "third_party_upstream_prs:" in body
    assert "pallets/itsdangerous" in body
    assert "MIN_REJECTIONS" in body
    assert "not conditioned on the verifier" in body
