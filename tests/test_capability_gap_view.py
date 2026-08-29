"""V0-41, part three: the view, which is where the record closes the loop or fails to.

The dashboard ranks gaps by repetition rather than recency, because a gap hit twice is a
stronger signal than a novel one. The ordering test is written adversarially for that
reason — the repeated gap is recorded first and the novel one last, so that a sort by
recency alone would put the wrong row on top. It is pinned after exactly that mutant,
one dropping the count sort, survived a weaker version of this test which gave every
event the same timestamp; the microsecond offsets exist to keep the mutant dead.

Grouping is by the normalised triple, not the verbatim detail, so "exit 1 on Monday" and
"exit 1 on Tuesday" are one gap seen twice with the latest detail shown. The empty view
must say that an absence of recorded gaps is not proof that none occurred, and the panel
must actually be wired into the page — the tab, its label and its pane — stating the
retry/escalate boundary in words and shipping no script tag."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from consilient.dashboard import build_payload, render_html
from consilient.events import read_all
from capability_gap_helpers import (
    _append_gap,
)


def _payload_over(events_dir: Path):
    events, rejected = read_all(events_dir)
    assert not rejected
    return build_payload(
        events,
        rejected,
        doctor={
            "routing_orchestration_enabled": False,
            "gates": {},
            "generated_at": "now",
        },
        beta_result={
            "verdict": "unmeasured",
            "n_rejected": 0,
            "n_false_accept": 0,
            "caveat": "no data",
            "lower_bound_on_joint_error": False,
        },
        beta_line="beta: no data",
        bypassed=0,
    )


def test_the_gap_view_ranks_repetition_above_novelty(tmp_path):
    # The same gap hit twice, then a DIFFERENT gap hit once LATER. Recency alone would
    # put the novel one on top; the view must rank the repeated one first, because a
    # gap hit twice is the stronger signal. (This ordering is what a mutant dropping
    # the count sort breaks — pinned after exactly that mutant survived a weaker
    # version of this test that gave every event the same timestamp.)
    base = datetime.now(timezone.utc)
    t1 = base.isoformat()
    t2 = (base + timedelta(microseconds=1)).isoformat()
    t3 = (base + timedelta(microseconds=2)).isoformat()
    _append_gap(tmp_path, t1, run_id="run-1", failure="failed", detail="exit 1")
    _append_gap(tmp_path, t2, run_id="run-2", failure="failed", detail="exit 1 again")
    _append_gap(
        tmp_path,
        t3,
        run_id="run-3",
        failure="silent",
        closure="escalate",
        repair="a human inspects",
        attempted="cursor-composer",
        detail="exit 0, nothing written",
    )
    payload = _payload_over(tmp_path)
    gaps = payload["capability_gaps"]
    assert gaps["total"] == 3
    assert gaps["distinct"] == 2
    top = gaps["rows"][0]
    assert top["count"] == 2
    assert top["failure"] == "failed"
    assert top["latest_detail"] == "exit 1 again"
    assert gaps["rows"][1]["count"] == 1
    assert gaps["rows"][1]["last_seen"] == t3
    # The boundary is stated, not implied.
    assert "retry" in gaps["boundary"]
    assert "escalate" in gaps["boundary"]


def test_the_gap_view_groups_by_the_normalised_triple_not_the_verbatim_detail(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    _append_gap(tmp_path, ts, run_id="run-1", detail="exit 1 on Monday")
    _append_gap(tmp_path, ts, run_id="run-2", detail="exit 1 on Tuesday")
    payload = _payload_over(tmp_path)
    assert payload["capability_gaps"]["distinct"] == 1


def test_an_empty_gap_view_says_absence_is_not_proof(tmp_path):
    payload = _payload_over(tmp_path)
    gaps = payload["capability_gaps"]
    assert gaps["total"] == 0
    assert gaps["rows"] == []
    html = render_html(payload)
    assert "absence of" in html
    assert "not proof none occurred" in html


def test_the_gap_panel_is_wired_into_the_page(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    _append_gap(tmp_path, ts)
    html = render_html(_payload_over(tmp_path))
    assert 'id="t-capgaps"' in html
    assert 'for="t-capgaps"' in html
    assert 'id="p-capgaps"' in html
    assert "Capability gaps" in html
    assert "self-healing boundary" in html
    assert "<script" not in html
