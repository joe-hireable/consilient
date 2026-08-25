"""The build driver retires units only from consumed review evidence."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"
ARTEFACT = "a" * 64
UNIT = {
    "claims": [".harness/build_driver.py"],
    "title": "review gate",
    "plan": "review-plan.md",
    "commit": "fix(driver): make the reviewer receipt arrive and count what is lost",
}

LOSS_REASONS = (
    "no_dispatch",
    "dispatch_refused",
    "dispatch_failed",
    "no_receipt_file",
    "receipt_unparseable",
    "receipt_mismatched",
)


def _load_driver():
    spec = importlib.util.spec_from_file_location("review_verdict_driver", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _state() -> dict:
    return {
        "built": ["AV"],
        "done": [],
        "verified": [],
        "review_dispatched": ["AV"],
        "review_attempts": {"AV": 1},
        "review_expected": {"AV": {"artefact": ARTEFACT, "attempt": 1}},
    }


def _write_dispatch(tmp_path: Path, payload: object | str) -> None:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (tmp_path / "AV-verify.out").write_text(text, encoding="utf-8")


def _write_receipt(tmp_path: Path, payload: object | str) -> None:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (tmp_path / "AV-verdict.json").write_text(text, encoding="utf-8")


def _ok_envelope() -> dict:
    return {"status": "ok", "stdout_tail": "A01 stays **SOUND**"}


def _verdict(verdict: str, **extra: object) -> dict:
    return {
        "v": 1,
        "unit": "AV",
        "artefact": ARTEFACT,
        "attempt": 1,
        "verdict": verdict,
        "findings": [],
        **extra,
    }


def _prepare(tmp_path: Path, monkeypatch):
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: ARTEFACT)
    recorded: list[dict] = []
    monkeypatch.setattr(driver, "append_review_outcome", recorded.append)
    return driver, recorded


def test_identity_matched_sound_retires_once_and_records_trajectory(
    tmp_path: Path, monkeypatch
) -> None:
    """Removing verdict consumption must leave a built unit unretired."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, _ok_envelope())
    _write_receipt(tmp_path, _verdict("SOUND"))

    assert driver.consume_review_verdict(state, "AV", UNIT) == "SOUND"
    assert state["done"] == ["AV"]
    assert state["verified"] == ["AV"]
    assert recorded == [
        {
            "unit": "AV",
            "artefact": ARTEFACT,
            "attempt": 1,
            "outcome": "SOUND",
            "findings": [],
        }
    ]

    assert driver.consume_review_verdict(state, "AV", UNIT) == "consumed"
    assert recorded[0]["outcome"] == "SOUND"
    assert len(recorded) == 1


def test_defective_review_requeues_repair_with_findings(tmp_path: Path, monkeypatch) -> None:
    """Changing DEFECTIVE into pass must retire a known-bad artefact."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, _ok_envelope())
    _write_receipt(
        tmp_path,
        _verdict("DEFECTIVE", findings=["missing refusal at the trust boundary"]),
    )

    assert driver.consume_review_verdict(state, "AV", UNIT) == "DEFECTIVE"
    assert "AV" not in state["done"]
    assert "AV" not in state["verified"]
    assert "AV" not in state["built"]
    assert state["repair_findings"]["AV"] == ["missing refusal at the trust boundary"]
    assert recorded[0]["outcome"] == "DEFECTIVE"
    assert "missing refusal at the trust boundary" in driver.write_brief(
        "AV", UNIT, state["repair_findings"]["AV"]
    ).read_text(encoding="utf-8")


def test_stdout_json_without_receipt_file_is_not_sound(
    tmp_path: Path, monkeypatch
) -> None:
    """The driver must not consume a receipt from stdout_tail."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(
        tmp_path,
        {"status": "ok", "stdout_tail": json.dumps(_verdict("SOUND"))},
    )

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "no_receipt_file"
    assert outcome != "SOUND"
    assert state["done"] == []
    assert recorded[0]["outcome"] == "no_receipt_file"


def test_prose_receipt_file_is_unparseable_and_not_sound(
    tmp_path: Path, monkeypatch
) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, _ok_envelope())
    _write_receipt(tmp_path, "A01 stays **SOUND**")

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "receipt_unparseable"
    assert recorded[0]["outcome"] == "receipt_unparseable"
    assert state["done"] == []


def test_absent_receipt_file_is_no_receipt_file(tmp_path: Path, monkeypatch) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, _ok_envelope())

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "no_receipt_file"
    assert recorded[0]["outcome"] == "no_receipt_file"
    assert state["done"] == []


def test_empty_out_is_no_dispatch(tmp_path: Path, monkeypatch) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    (tmp_path / "AV-verify.out").write_text("", encoding="utf-8")

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "no_dispatch"
    assert recorded[0]["outcome"] == "no_dispatch"
    assert state["done"] == []


def test_missing_out_is_no_dispatch(tmp_path: Path, monkeypatch) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "no_dispatch"
    assert recorded[0]["outcome"] == "no_dispatch"


def test_refused_dispatch_is_dispatch_refused(tmp_path: Path, monkeypatch) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, "status: refused\nreason: trajectory lock held\n")

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "dispatch_refused"
    assert recorded[0]["outcome"] == "dispatch_refused"
    assert state["done"] == []


def test_json_refused_dispatch_is_dispatch_refused(
    tmp_path: Path, monkeypatch
) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, {"status": "refused", "reason": "claim collision"})
    _write_receipt(tmp_path, _verdict("SOUND"))

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "dispatch_refused"
    assert recorded[0]["outcome"] == "dispatch_refused"


def test_failed_dispatch_is_dispatch_failed(tmp_path: Path, monkeypatch) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, {"status": "timeout"})

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "dispatch_failed"
    assert recorded[0]["outcome"] == "dispatch_failed"
    assert state["done"] == []


def test_mismatched_artefact_is_receipt_mismatched(
    tmp_path: Path, monkeypatch
) -> None:
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    _write_dispatch(tmp_path, _ok_envelope())
    _write_receipt(tmp_path, _verdict("SOUND", artefact="b" * 64))

    outcome = driver.consume_review_verdict(state, "AV", UNIT)
    assert outcome == "receipt_mismatched"
    assert recorded[0]["outcome"] == "receipt_mismatched"
    assert state["done"] == []


def test_loss_reasons_are_distinct_and_none_is_sound(
    tmp_path: Path, monkeypatch
) -> None:
    """Prose, absent file, empty .out, refused dispatch and mismatch stay partitioned."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    cases = [
        ("prose", "receipt_unparseable"),
        ("absent", "no_receipt_file"),
        ("empty", "no_dispatch"),
        ("refused", "dispatch_refused"),
        ("mismatch", "receipt_mismatched"),
    ]
    seen: list[str] = []
    for label, expected in cases:
        state = _state()
        if (tmp_path / "AV-verdict.json").exists():
            (tmp_path / "AV-verdict.json").unlink()
        if (tmp_path / "AV-verify.out").exists():
            (tmp_path / "AV-verify.out").unlink()
        if label == "prose":
            _write_dispatch(tmp_path, _ok_envelope())
            _write_receipt(tmp_path, "A01 stays **SOUND**")
        elif label == "absent":
            _write_dispatch(tmp_path, _ok_envelope())
        elif label == "empty":
            (tmp_path / "AV-verify.out").write_text("", encoding="utf-8")
        elif label == "refused":
            _write_dispatch(tmp_path, "status: refused\n")
        else:
            _write_dispatch(tmp_path, _ok_envelope())
            _write_receipt(tmp_path, _verdict("SOUND", artefact="b" * 64))
        outcome = driver.consume_review_verdict(state, "AV", UNIT)
        assert outcome == expected, label
        assert outcome != "SOUND"
        assert state["done"] == []
        seen.append(outcome)
    assert len(set(seen)) == len(seen)
    assert set(seen) <= set(LOSS_REASONS)


def test_legacy_flags_and_a_rejected_artefact_cannot_retire(
    tmp_path: Path, monkeypatch
) -> None:
    """Deleting the current receipt must make legacy completion state insufficient."""
    driver, _recorded = _prepare(tmp_path, monkeypatch)
    state = {
        "done": ["AV"],
        "verified": ["AV"],
        "force_done": ["AV"],
        "review_results": {"AV": {"outcome": "DEFECTIVE", "artefact": ARTEFACT}},
    }

    assert driver.retired_units(state, {"AV": UNIT}) == set()


def test_verify_brief_demands_the_receipt_file(tmp_path: Path, monkeypatch) -> None:
    driver, _recorded = _prepare(tmp_path, monkeypatch)
    path = driver.write_verify_brief("AV", UNIT, ARTEFACT, 1)
    text = path.read_text(encoding="utf-8")
    receipt = tmp_path / "AV-verdict.json"
    assert str(receipt) in text
    assert "stdout" in text.lower()
    assert "not the receipt" in text.lower() or "not stdout" in text.lower()


def test_end_to_end_receipt_file_writes_sound_trajectory_event(
    tmp_path: Path, monkeypatch
) -> None:
    """A real receipt file must produce a review.outcome event, not an exit code."""
    driver = _load_driver()
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "LOG", log_dir)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: ARTEFACT)
    (briefs / "AV-verify.out").write_text(json.dumps(_ok_envelope()), encoding="utf-8")
    (briefs / "AV-verdict.json").write_text(
        json.dumps(_verdict("SOUND")), encoding="utf-8"
    )

    returned = driver.consume_review_verdict(_state(), "AV", UNIT)
    assert returned == "SOUND"

    log_path = log_dir / (date.today().isoformat() + ".jsonl")
    assert log_path.is_file()
    events = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    outcomes = [
        event
        for event in events
        if event.get("event") == "review.outcome"
        and event.get("data", {}).get("unit") == "AV"
    ]
    assert outcomes, "no review.outcome event was appended"
    assert outcomes[-1]["data"]["outcome"] in {"SOUND", "DEFECTIVE"}
    assert outcomes[-1]["data"]["outcome"] == "SOUND"


def test_a_silent_review_does_not_spend_an_attempt(tmp_path: Path, monkeypatch) -> None:
    driver, _recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    state["review_attempts"] = {"AV": 2}

    assert driver.consume_review_verdict(state, "AV", UNIT) == "no_dispatch"
    assert state["review_attempts"]["AV"] == 1, "a silent review consumed a review attempt"


def test_a_reviewer_that_spoke_badly_does_spend_an_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """Deduplication of infrastructure must not become a free pass for a bad reviewer."""
    driver, _recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    state["review_attempts"] = {"AV": 2}
    _write_dispatch(tmp_path, {"status": "ok", "stdout_tail": "it seems fine to me."})

    assert driver.consume_review_verdict(state, "AV", UNIT) == "no_receipt_file"
    assert state["review_attempts"]["AV"] == 2, "a reviewer that ran must still spend its attempt"
