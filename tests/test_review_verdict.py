"""The build driver retires units only from consumed review evidence."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"
ARTEFACT = "a" * 64
UNIT = {
    "claims": [".harness/build_driver.py"],
    "title": "review gate",
    "plan": "review-plan.md",
}


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


def _write_review(tmp_path: Path, payload: object) -> None:
    (tmp_path / "AV-verify.out").write_text(json.dumps(payload), encoding="utf-8")


def _outer(verdict: object, status: str = "ok") -> dict:
    return {"status": status, "stdout_tail": json.dumps(verdict)}


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
    _write_review(tmp_path, _outer(_verdict("SOUND")))

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
    _write_review(
        tmp_path,
        _outer(_verdict("DEFECTIVE", findings=["missing refusal at the trust boundary"])),
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


@pytest.mark.parametrize(
    ("payload", "artefact"),
    [
        (None, ARTEFACT),
        ("SOUND", ARTEFACT),
        (_outer("prose only"), ARTEFACT),
        (_outer(_verdict("SOUND"), status="failed"), ARTEFACT),
        (_outer(_verdict("SOUND", v=2)), ARTEFACT),
        (_outer(_verdict("UNKNOWN")), ARTEFACT),
        (_outer(_verdict("SOUND", unit="OTHER")), ARTEFACT),
        (_outer(_verdict("SOUND", artefact="b" * 64)), ARTEFACT),
        (_outer(_verdict("SOUND", extra="not allowed")), ARTEFACT),
    ],
)
def test_unusable_review_output_fails_closed(
    tmp_path: Path, monkeypatch, payload: object, artefact: str
) -> None:
    """Malformed, failed, and identity-mismatched reviews are infrastructure errors."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: artefact)
    if payload is not None:
        _write_review(tmp_path, payload)

    assert driver.consume_review_verdict(state, "AV", UNIT) == "check_error"
    assert state["done"] == []
    assert state["verified"] == []
    assert recorded[0]["outcome"] == "check_error"


def test_legacy_flags_and_a_rejected_artefact_cannot_retire(tmp_path: Path, monkeypatch) -> None:
    """Deleting the current receipt must make legacy completion state insufficient."""
    driver, _recorded = _prepare(tmp_path, monkeypatch)
    state = {
        "done": ["AV"],
        "verified": ["AV"],
        "force_done": ["AV"],
        "review_results": {"AV": {"outcome": "DEFECTIVE", "artefact": ARTEFACT}},
    }

    assert driver.retired_units(state, {"AV": UNIT}) == set()


def test_malformed_and_stale_sound_outputs_fail_closed(tmp_path: Path, monkeypatch) -> None:
    """A truncated receipt or a changed artefact cannot reuse a prior SOUND."""
    driver, recorded = _prepare(tmp_path, monkeypatch)
    state = _state()
    (tmp_path / "AV-verify.out").write_text("{", encoding="utf-8")
    assert driver.consume_review_verdict(state, "AV", UNIT) == "check_error"
    assert recorded[0]["outcome"] == "check_error"

    state = _state()
    _write_review(tmp_path, _outer(_verdict("SOUND")))
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "b" * 64)
    assert driver.consume_review_verdict(state, "AV", UNIT) == "check_error"
