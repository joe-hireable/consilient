from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events
from consilient.events import EventError, bypassed, read_all

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "consent.py"
PRINCIPAL = "joe-brown"


def consent_event(kind: str, purpose: str, **extra: object) -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": PRINCIPAL,
        "data": {
            "purpose": purpose,
            "principal": PRINCIPAL,
            "via": "cli",
            **extra,
        },
    }


def run_consent(
    log: Path, *args: str, input_text: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--log", str(log)],
        cwd=ROOT,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )


def grant(log: Path, purpose: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return run_consent(
        log,
        "grant",
        "--purpose",
        purpose,
        "--retention-days",
        "30",
        "--principal",
        PRINCIPAL,
        "--via",
        "cli",
        *extra,
        input_text="yes\n",
    )


def section(render: str, purpose: str) -> str:
    marker = f"[{purpose}]\n"
    assert render.count(marker) == 1
    return render.split(marker, 1)[1].split("\n\n", 1)[0].rstrip()


def test_schema_has_three_separate_consent_purposes() -> None:
    assert events.CONSENT_PURPOSES == {
        "improve-consilient",
        "train-consilient",
        "commercial-training",
    }
    for purpose in ("improve-consilient", "train-consilient"):
        events.validate(
            consent_event(events.CONSENT_GRANTED, purpose, retention_days=30)
        )


@pytest.mark.parametrize("purpose", ("improve-consilient", "train-consilient"))
@pytest.mark.parametrize("retention_days", (None, 0, True, "30"))
def test_ordinary_grants_require_positive_integer_retention(
    purpose: str, retention_days: object
) -> None:
    event = consent_event(
        events.CONSENT_GRANTED, purpose, retention_days=retention_days
    )
    if retention_days is None:
        data = event["data"]
        assert isinstance(data, dict)
        del data["retention_days"]
    with pytest.raises(EventError, match="retention_days"):
        events.validate(event)


def test_commercial_grant_names_one_per_use_authorisation() -> None:
    events.validate(
        consent_event(
            events.CONSENT_GRANTED,
            "commercial-training",
            retention_days=30,
            per_use=True,
            use_ref="customer-evaluation-17",
        )
    )


@pytest.mark.parametrize(
    "extra",
    (
        {"use_ref": "customer-evaluation-17"},
        {"per_use": False, "use_ref": "customer-evaluation-17"},
        {"per_use": 1, "use_ref": "customer-evaluation-17"},
        {"per_use": True},
        {"per_use": True, "use_ref": ""},
        {"per_use": True, "use_ref": 17},
    ),
)
def test_commercial_grant_refuses_missing_or_malformed_per_use_fields(
    extra: dict[str, object],
) -> None:
    with pytest.raises(EventError, match="per.use|single authorised use"):
        events.validate(
            consent_event(
                events.CONSENT_GRANTED,
                "commercial-training",
                retention_days=30,
                **extra,
            )
        )


@pytest.mark.parametrize("field", ({"per_use": True}, {"use_ref": "use-17"}))
def test_withdrawal_refuses_grant_only_per_use_fields(field: dict[str, object]) -> None:
    with pytest.raises(EventError, match="withdrawal|withdrawn"):
        events.validate(
            consent_event(
                events.CONSENT_WITHDRAWN,
                "commercial-training",
                **field,
            )
        )


def test_improvement_and_training_are_separate_prompted_grants(tmp_path: Path) -> None:
    log = tmp_path / "log"

    improvement = grant(log, "improve-consilient")
    training = grant(log, "train-consilient")

    assert improvement.returncode == 0, improvement.stderr
    assert training.returncode == 0, training.stderr
    assert "Grant improve-consilient consent" in improvement.stdout
    assert "Grant train-consilient consent" in training.stdout
    recorded, rejected = read_all(log)
    assert rejected == []
    assert [(event.kind, event.data["purpose"]) for event in recorded] == [
        (events.CONSENT_GRANTED, "improve-consilient"),
        (events.CONSENT_GRANTED, "train-consilient"),
    ]
    assert [event.actor for event in recorded] == [PRINCIPAL, PRINCIPAL]
    assert bypassed(log) == []


def test_bundled_purpose_is_refused_without_writing(tmp_path: Path) -> None:
    log = tmp_path / "log"
    result = grant(log, "both")

    assert result.returncode != 0
    assert "invalid choice" in result.stderr
    assert read_all(log) == ([], [])


def test_commercial_flow_refuses_no_use_ref_then_records_one_use(tmp_path: Path) -> None:
    log = tmp_path / "log"

    refused = grant(log, "commercial-training")
    assert refused.returncode != 0
    assert "--use-ref" in refused.stderr
    assert "single authorised use" in refused.stderr
    assert read_all(log) == ([], [])

    accepted = grant(
        log,
        "commercial-training",
        "--use-ref",
        "customer-evaluation-17",
    )
    assert accepted.returncode == 0, accepted.stderr
    recorded, rejected = read_all(log)
    assert rejected == []
    assert len(recorded) == 1
    assert recorded[0].data["per_use"] is True
    assert recorded[0].data["use_ref"] == "customer-evaluation-17"


def test_declining_a_grant_writes_nothing(tmp_path: Path) -> None:
    log = tmp_path / "log"
    result = run_consent(
        log,
        "grant",
        "--purpose",
        "improve-consilient",
        "--retention-days",
        "30",
        "--principal",
        PRINCIPAL,
        "--via",
        "cli",
        input_text="no\n",
    )

    assert result.returncode != 0
    assert "No consent recorded" in result.stdout
    assert read_all(log) == ([], [])


def test_show_quarantines_a_non_string_purpose(tmp_path: Path) -> None:
    log = tmp_path / "log"
    log.mkdir()
    malformed = consent_event(
        events.CONSENT_GRANTED, "improve-consilient", retention_days=30
    )
    data = malformed["data"]
    assert isinstance(data, dict)
    data["purpose"] = []
    (log / "malformed.jsonl").write_text(
        json.dumps(malformed) + "\n", encoding="utf-8"
    )

    result = run_consent(log, "show")

    assert result.returncode == 0, result.stderr
    assert "1 rejected trajectory line" in result.stderr
    for purpose in events.CONSENT_PURPOSES:
        assert section(result.stdout, purpose) == "status: never-asked"


def test_unrenderable_retention_is_refused_before_writing(tmp_path: Path) -> None:
    log = tmp_path / "log"
    result = run_consent(
        log,
        "grant",
        "--purpose",
        "improve-consilient",
        "--retention-days",
        "1000000000",
        "--principal",
        PRINCIPAL,
        "--via",
        "cli",
        input_text="yes\n",
    )

    assert result.returncode != 0
    assert "retention_days" in result.stderr
    assert read_all(log) == ([], [])


def test_withdrawal_changes_only_its_section(tmp_path: Path) -> None:
    log = tmp_path / "log"
    assert grant(log, "improve-consilient").returncode == 0
    assert grant(log, "train-consilient").returncode == 0

    before = run_consent(log, "show")
    assert before.returncode == 0, before.stderr
    assert section(before.stdout, "improve-consilient").startswith(
        "status: granted-until "
    )
    assert section(before.stdout, "train-consilient").startswith(
        "status: granted-until "
    )
    assert section(before.stdout, "commercial-training") == "status: never-asked"

    withdrawn = run_consent(
        log,
        "withdraw",
        "--purpose",
        "train-consilient",
        "--principal",
        PRINCIPAL,
        "--via",
        "cli",
    )
    assert withdrawn.returncode == 0, withdrawn.stderr

    after = run_consent(log, "show")
    assert after.returncode == 0, after.stderr
    assert section(after.stdout, "improve-consilient") == section(
        before.stdout, "improve-consilient"
    )
    assert section(after.stdout, "train-consilient") == "status: withdrawn"
    assert section(after.stdout, "commercial-training") == "status: never-asked"
