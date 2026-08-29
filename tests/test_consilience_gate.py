"""G01 -- what mints an acquisition anchor, and when two anchors are a different class
(ADR-0081).

Whewell's second clause is the whole subject here: a decision converges only when its
evidence is drawn from another *different* class, so a shared channel, a shared
observation anchor or an overlapping derivation root is echo and earns nothing. The
three validation cases lead the file because an acquisition object that cannot survive
`events.validate` never reaches the projection to be judged, and a padded or case-varied
channel must not mint an anchor merely by looking like one. Two models reading the same
source is the case worth keeping in view: different weights are not a different class of
facts, and this file pins that.

Mutation-tested here: dropping channel/anchor/root validation makes the padded-channel
and unknown-roots cases fail; inferring independence from a missing acquisition object
fails the unmeasured-status test.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    Mutation-tested in this file:
      - dropping channel/anchor/root validation makes the padded-channel and
        unknown-roots cases fail
      - treating duplicate verification identities as two slots fails the
        duplicate-key test
      - inferring independence from a missing acquisition object fails the
        unmeasured-status test
"""

from pathlib import Path
import pytest
from consilient import events, projection
from consilience_gate_helpers import (
    _browser_acquisition,
    _corpus_acquisition,
    _execution_acquisition,
    _project,
    _ref,
    _source_acquisition,
    decision_event,
    knowledge_event,
    verification_event,
)


@pytest.mark.parametrize(
    "record",
    (
        verification_event(acquisition=_execution_acquisition()),
        verification_event(acquisition=_browser_acquisition()),
        knowledge_event(acquisition=_source_acquisition()),
        knowledge_event(acquisition=_corpus_acquisition()),
    ),
)
def test_each_channel_anchor_validates(record: dict[str, object]) -> None:
    events.validate(record)


def test_padded_or_cased_channel_cannot_mint_an_anchor() -> None:
    for channel in ("Artefact_execution", " artefact_execution", "artefact_execution "):
        payload = _execution_acquisition()
        payload["channel"] = channel
        with pytest.raises(events.EventError, match="channel"):
            events.validate(verification_event(acquisition=payload))


def test_empty_derivation_roots_cannot_mint_an_anchor() -> None:
    payload = _execution_acquisition(derivation_roots=[])
    with pytest.raises(events.EventError, match="derivation"):
        events.validate(verification_event(acquisition=payload))


def test_legacy_source_without_anchor_metadata_is_unmeasured_status(
    tmp_path: Path,
) -> None:
    source = verification_event()
    conn, written = _project(tmp_path, [source])
    decision = decision_event([_ref(written[0])])
    events.append(tmp_path / "log" / "2026-08-24.jsonl", decision)
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "unmeasured"
    assert report["qualifying_refs"] == []
    assert report["non_qualifying_refs"]
    assert any("unmeasured" in reason for reason in report["reasons"])


def test_different_channel_anchors_report_converged_status(tmp_path: Path) -> None:
    execution = verification_event(acquisition=_execution_acquisition())
    source = knowledge_event(acquisition=_source_acquisition(), offset=1)
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "converged"
    assert len(report["qualifying_refs"]) == 2
    assert {item["event_kind"] for item in report["qualifying_refs"]} == {
        events.VERIFICATION_OUTCOME_KIND,
        events.KNOWLEDGE_RETRIEVED_KIND,
    }


def test_same_channel_different_anchors_cannot_converge(tmp_path: Path) -> None:
    first = verification_event(
        acquisition=_execution_acquisition(observation_anchor="exec:one"),
        verification_id="ver-one",
    )
    second = verification_event(
        acquisition=_execution_acquisition(
            observation_anchor="exec:two",
            derivation_roots=("fixture:other.py",),
        ),
        verification_id="ver-two",
        attempt_id="att-2",
        offset=1,
    )
    conn, written = _project(tmp_path, [first, second])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("channel" in reason for reason in report["reasons"])


def test_same_observation_anchor_cannot_converge(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(observation_anchor="shared-anchor")
    )
    source = knowledge_event(
        acquisition=_source_acquisition(observation_anchor="shared-anchor"),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("observation_anchor" in reason for reason in report["reasons"])


def test_shared_derivation_roots_are_echo_not_an_anchor_pair(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(
            derivation_roots=("root:shared", "root:tests")
        )
    )
    source = knowledge_event(
        acquisition=_source_acquisition(derivation_roots=("root:shared", "root:arxiv")),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert any("derivation" in reason for reason in report["reasons"])


def test_unknown_derivation_roots_report_unmeasured_status(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(derivation_roots="unknown")
    )
    source = knowledge_event(acquisition=_source_acquisition(), offset=1)
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "unmeasured"
    assert report["qualifying_refs"] == []
    assert any("unknown" in reason for reason in report["reasons"])


def test_opposing_stances_report_disagreed_status(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(),
        verifier_accept=True,
    )
    source = knowledge_event(
        acquisition=_source_acquisition(stance="opposes"),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "disagreed"
    assert len(report["qualifying_refs"]) == 2


def test_different_model_same_source_anchor_is_echo(tmp_path: Path) -> None:
    first = knowledge_event(
        acquisition=_source_acquisition(observation_anchor="arxiv:2603.26993"),
        extra_data={"model_family": "claude"},
    )
    second = knowledge_event(
        acquisition=_corpus_acquisition(observation_anchor="arxiv:2603.26993"),
        uri="https://example.com/corpus",
        offset=1,
        extra_data={"model_family": "gpt"},
    )
    conn, written = _project(tmp_path, [first, second])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("observation_anchor" in reason for reason in report["reasons"])
