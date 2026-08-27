"""Outbound email/SMS: local creds, spend flag, no verdicts, artefact recorded."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from consilient.events import read
from consilient_connectors.outbound import (
    EMAIL_FROM,
    EMAIL_HOST,
    TWILIO_FROM,
    TWILIO_SID,
    TWILIO_TOKEN,
    OutboundError,
    send_email,
    send_sms,
)


def _email_env() -> dict[str, str]:
    return {
        EMAIL_HOST: "smtp.example.test",
        EMAIL_FROM: "consilient@example.test",
    }


def _sms_env() -> dict[str, str]:
    return {
        TWILIO_SID: "ACtest",
        TWILIO_TOKEN: "token-test",
        TWILIO_FROM: "+447000000000",
    }


def test_email_without_egress_authorisation_does_not_send() -> None:
    calls: list[int] = []

    def sender(**_kwargs: object) -> str:
        calls.append(1)
        return "<id@x>"

    with pytest.raises(OutboundError, match="authorise-egress"):
        send_email(
            to="a@b.c",
            subject="s",
            text="hello",
            authorise_egress="",
            disclosure="told the recipient in advance",
            environ=_email_env(),
            sender=sender,
        )
    assert calls == []


def test_email_without_disclosure_does_not_send() -> None:
    """B1: disclosure is required for every outbound message.send effect."""
    calls: list[int] = []

    def sender(**_kwargs: object) -> str:
        calls.append(1)
        return "<id@x>"

    with pytest.raises(OutboundError, match="disclosure"):
        send_email(
            to="a@b.c",
            subject="s",
            text="hello",
            authorise_egress="notify",
            disclosure="",
            environ=_email_env(),
            sender=sender,
        )
    assert calls == []


def test_sms_without_disclosure_does_not_send() -> None:
    """B1: disclosure is required for every outbound message.send effect."""
    calls: list[int] = []

    def sender(**_kwargs: object) -> str:
        calls.append(1)
        return "SMxxx"

    with pytest.raises(OutboundError, match="disclosure"):
        send_sms(
            to="+447000000001",
            text="hello",
            authorise_egress="wake Joe",
            authorise_spend="Twilio SMS 0.04 GBP",
            disclosure="",
            environ=_sms_env(),
            sender=sender,
        )
    assert calls == []


def test_sms_without_spend_authorisation_does_not_send() -> None:
    calls: list[int] = []

    def sender(**_kwargs: object) -> str:
        calls.append(1)
        return "SMxxx"

    with pytest.raises(OutboundError, match="SMS is spend"):
        send_sms(
            to="+447000000001",
            text="hello",
            authorise_egress="wake Joe",
            authorise_spend=None,
            disclosure="told the recipient in advance",
            environ=_sms_env(),
            sender=sender,
        )
    assert calls == []


def test_sms_spend_note_must_name_twilio_and_an_amount() -> None:
    with pytest.raises(OutboundError, match="Twilio"):
        send_sms(
            to="+447000000001",
            text="hello",
            authorise_egress="wake Joe",
            authorise_spend="just send it",
            disclosure="told the recipient in advance",
            environ=_sms_env(),
            sender=lambda **_k: "SMxxx",
        )


def test_missing_credentials_fail_closed() -> None:
    with pytest.raises(OutboundError, match="CONSILIENT_SMTP_HOST"):
        send_email(
            to="a@b.c",
            subject="s",
            text="hello",
            authorise_egress="notify",
            disclosure="told the recipient in advance",
            environ={},
            sender=lambda **_k: "<id@x>",
        )
    with pytest.raises(OutboundError, match="CONSILIENT_TWILIO_ACCOUNT_SID"):
        send_sms(
            to="+447000000001",
            text="hello",
            authorise_egress="wake Joe",
            authorise_spend="Twilio SMS 0.04 GBP",
            disclosure="told the recipient in advance",
            environ={},
            sender=lambda **_k: "SMxxx",
        )


def test_verdict_shaped_body_is_refused() -> None:
    with pytest.raises(OutboundError, match="verdict-shaped"):
        send_email(
            to="a@b.c",
            subject="s",
            text=json.dumps({"human_decision": "verdict", "human_verdict": "accept"}),
            authorise_egress="notify",
            disclosure="told the recipient in advance",
            environ=_email_env(),
            sender=lambda **_k: "<id@x>",
        )
    with pytest.raises(OutboundError, match="verdict-shaped"):
        send_sms(
            to="+447000000001",
            text=json.dumps({"event": "approval"}),
            authorise_egress="wake Joe",
            authorise_spend="Twilio SMS 0.04 GBP",
            disclosure="told the recipient in advance",
            environ=_sms_env(),
            sender=lambda **_k: "SMxxx",
        )


def test_dry_run_does_not_call_the_sender() -> None:
    calls: list[int] = []

    def sender(**_kwargs: object) -> str:
        calls.append(1)
        return "SHOULD-NOT"

    event = send_sms(
        to="+447000000001",
        text="hello",
        authorise_egress="wake Joe",
        authorise_spend="Twilio SMS 0.04 GBP",
        disclosure="told the recipient in advance",
        environ=_sms_env(),
        sender=sender,
        dry_run=True,
    )
    assert calls == []
    assert event["data"]["artefact"] == "dry-run"
    assert event["data"]["dry_run"] is True
    assert event["data"]["via"] == "cli"


def test_email_records_message_id_artefact() -> None:
    event = send_email(
        to="a@b.c",
        subject="harvest ran",
        text="32 examples written",
        authorise_egress="notify Joe the harvest ran",
        disclosure="told the recipient in advance",
        environ=_email_env(),
        sender=lambda **_k: "<abc@consilient.local>",
    )
    assert event["event"] == "transport.outbound"
    assert event["data"]["artefact"] == "<abc@consilient.local>"
    assert event["data"]["transport_name"] == "email"
    assert event["data"]["disclosure"] == "told the recipient in advance"
    assert "human_decision" not in event["data"]
    assert "human_verdict" not in event["data"]


def test_sms_records_sid_artefact() -> None:
    event = send_sms(
        to="+447000000001",
        text="harvest ran",
        authorise_egress="wake Joe",
        authorise_spend="Twilio SMS notification 0.04 GBP",
        disclosure="told the recipient in advance",
        environ=_sms_env(),
        sender=lambda **_k: "SMrealartefact",
    )
    assert event["data"]["artefact"] == "SMrealartefact"
    assert event["data"]["authorise_spend"].startswith("Twilio")
    assert event["data"]["disclosure"] == "told the recipient in advance"


def test_cli_appends_only_when_not_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from consilient_connectors import outbound as ob

    captured: dict[str, object] = {}

    def fake_send_email(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return send_email(
            to=str(kwargs["to"]),
            subject=str(kwargs["subject"]),
            text=str(kwargs["text"]),
            authorise_egress=str(kwargs["authorise_egress"]),
            disclosure=str(kwargs["disclosure"]),
            environ=_email_env(),
            sender=lambda **_k: "<cli@consilient.local>",
            dry_run=bool(kwargs["dry_run"]),
        )

    monkeypatch.setattr(ob, "send_email", fake_send_email)
    code = ob.main(
        [
            "email",
            "--to",
            "a@b.c",
            "--subject",
            "s",
            "--body",
            "hello",
            "--authorise-egress",
            "notify",
            "--disclosure",
            "told the recipient in advance",
            "--log",
            str(tmp_path),
            "--dry-run",
        ]
    )
    assert code == 0
    assert list(tmp_path.glob("*.jsonl")) == []

    code = ob.main(
        [
            "email",
            "--to",
            "a@b.c",
            "--subject",
            "s",
            "--body",
            "hello",
            "--authorise-egress",
            "notify",
            "--disclosure",
            "told the recipient in advance",
            "--log",
            str(tmp_path),
        ]
    )
    assert code == 0
    logs = list(tmp_path.glob("*.jsonl"))
    assert logs
    events, rejected = read(logs[0])
    assert not rejected
    assert events[0].raw["event"] == "transport.outbound"
    assert events[0].raw["data"]["artefact"] == "<cli@consilient.local>"
    assert captured.get("dry_run") is False
