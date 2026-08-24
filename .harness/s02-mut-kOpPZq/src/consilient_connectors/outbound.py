"""Outbound email and SMS as local-CLI artefacts (ADR-0041, ADR-0042).

Credentials come from the process environment only. Nothing here reads a file
in the repository. SMS is spend and requires an explicit authorise-spend note
that names Twilio and an amount. Both channels require authorise-egress.
A verdict-shaped body is refused: untrusted transports still cannot deliver
human decisions, and the CLI will not launder one through an SMS.
"""

from __future__ import annotations

import json
import os
import re
import smtplib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Callable, Mapping
from uuid import uuid4

from consilient.events import SCHEMA_VERSION, EventPayload
from consilient.transport import looks_like_verdict

OUTBOUND_KIND = "transport.outbound"
OUTBOUND_ACTOR = "consilient.outbound"

EMAIL_HOST = "CONSILIENT_SMTP_HOST"
EMAIL_PORT = "CONSILIENT_SMTP_PORT"
EMAIL_USER = "CONSILIENT_SMTP_USER"
EMAIL_PASSWORD = "CONSILIENT_SMTP_PASSWORD"
EMAIL_FROM = "CONSILIENT_SMTP_FROM"
TWILIO_SID = "CONSILIENT_TWILIO_ACCOUNT_SID"
TWILIO_TOKEN = "CONSILIENT_TWILIO_AUTH_TOKEN"
TWILIO_FROM = "CONSILIENT_TWILIO_FROM"

EmailSender = Callable[..., str]
SmsSender = Callable[..., str]


class OutboundError(ValueError):
    """Egress refused, or the artefact could not be produced."""


def _env(name: str, environ: Mapping[str, str]) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise OutboundError(
            f"{name} is unset: outbound credentials live in the process environment, "
            "never in the repository (ADR-0042)"
        )
    return value


def _refuse_verdict(channel: str, text: str, extra: Mapping[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"transport_name": channel, "text": text}
    if extra:
        payload.update(dict(extra))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            payload.update(parsed)
    found = looks_like_verdict(payload)
    if found is not None:
        raise OutboundError(
            f"refusing verdict-shaped outbound {channel} ({found!r}): "
            "untrusted transports cannot deliver human decisions (ADR-0041)"
        )


def _require_egress(note: str) -> str:
    if not note.strip():
        raise OutboundError(
            "outbound egress is blocked unless --authorise-egress names the purpose "
            "(ADR-0042)"
        )
    return note.strip()


def _require_sms_spend(note: str | None) -> str:
    if note is None or not note.strip():
        raise OutboundError(
            "SMS is spend: pass --authorise-spend naming Twilio and an amount "
            "(ADR-0019/0042). Standing authorisation is not accepted."
        )
    text = note.strip()
    if "twilio" not in text.casefold() or re.search(r"\d", text) is None:
        raise OutboundError(
            "authorise-spend must name Twilio and include an amount, e.g. "
            "'Twilio SMS notification 0.04 GBP'"
        )
    return text


def smtp_send(
    *,
    host: str,
    port: int,
    user: str | None,
    password: str | None,
    mail_from: str,
    to: str,
    subject: str,
    body: str,
) -> str:
    message_id = f"<{uuid4()}@consilient.local>"
    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        if port != 25:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
    return message_id


def twilio_send(
    *,
    account_sid: str,
    auth_token: str,
    from_number: str,
    to: str,
    body: str,
) -> str:
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(account_sid)}"
        "/Messages.json"
    )
    data = urllib.parse.urlencode(
        {"From": from_number, "To": to, "Body": body}
    ).encode("utf-8")
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, account_sid, auth_token)
    opener = urllib.request.build_opener(
        urllib.request.HTTPBasicAuthHandler(password_mgr)
    )
    request = urllib.request.Request(url, data=data, method="POST")
    try:
        with opener.open(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OutboundError(f"Twilio refused the send ({exc.code}): {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise OutboundError(f"Twilio was unreachable: {exc}") from exc
    sid = payload.get("sid")
    if not isinstance(sid, str) or not sid.strip():
        raise OutboundError("Twilio returned no Message SID; nothing to record as artefact")
    return sid.strip()


def send_email(
    *,
    to: str,
    subject: str,
    text: str,
    authorise_egress: str,
    environ: Mapping[str, str] | None = None,
    sender: EmailSender | None = None,
    dry_run: bool = False,
) -> EventPayload:
    env = environ if environ is not None else os.environ
    _refuse_verdict("email", text, {"subject": subject})
    purpose = _require_egress(authorise_egress)
    if not to.strip() or not subject.strip() or not text.strip():
        raise OutboundError("email requires --to, --subject and a non-empty body")
    host = _env(EMAIL_HOST, env)
    mail_from = _env(EMAIL_FROM, env)
    port_raw = env.get(EMAIL_PORT, "587").strip() or "587"
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise OutboundError(f"{EMAIL_PORT} must be an integer") from exc
    user = env.get(EMAIL_USER, "").strip() or None
    password = env.get(EMAIL_PASSWORD, "").strip() or None
    if dry_run:
        artefact = "dry-run"
    else:
        send = sender or smtp_send
        artefact = send(
            host=host,
            port=port,
            user=user,
            password=password,
            mail_from=mail_from,
            to=to.strip(),
            subject=subject.strip(),
            body=text,
        )
        if not artefact.strip():
            raise OutboundError("email send produced no Message-ID artefact")
    return _event(
        transport_name="email",
        to=to.strip(),
        text=text,
        artefact=artefact,
        dry_run=dry_run,
        authorise_egress=purpose,
        extra={"subject": subject.strip(), "from": mail_from},
    )


def send_sms(
    *,
    to: str,
    text: str,
    authorise_egress: str,
    authorise_spend: str | None,
    environ: Mapping[str, str] | None = None,
    sender: SmsSender | None = None,
    dry_run: bool = False,
) -> EventPayload:
    env = environ if environ is not None else os.environ
    _refuse_verdict("sms", text)
    purpose = _require_egress(authorise_egress)
    spend = _require_sms_spend(authorise_spend)
    if not to.strip() or not text.strip():
        raise OutboundError("sms requires --to and a non-empty body")
    sid = _env(TWILIO_SID, env)
    token = _env(TWILIO_TOKEN, env)
    from_number = _env(TWILIO_FROM, env)
    if dry_run:
        artefact = "dry-run"
    else:
        send = sender or twilio_send
        artefact = send(
            account_sid=sid,
            auth_token=token,
            from_number=from_number,
            to=to.strip(),
            body=text,
        )
        if not artefact.strip():
            raise OutboundError("SMS send produced no Message SID artefact")
    return _event(
        transport_name="sms",
        to=to.strip(),
        text=text,
        artefact=artefact,
        dry_run=dry_run,
        authorise_egress=purpose,
        extra={"from": from_number, "authorise_spend": spend},
    )


def _event(
    *,
    transport_name: str,
    to: str,
    text: str,
    artefact: str,
    dry_run: bool,
    authorise_egress: str,
    extra: Mapping[str, str],
) -> EventPayload:
    now = datetime.now(timezone.utc).isoformat()
    data: dict[str, Any] = {
        "transport_name": transport_name,
        "to": to,
        "text": text,
        "artefact": artefact,
        "via": "cli",
        "dry_run": dry_run,
        "authorise_egress": authorise_egress,
    }
    data.update(dict(extra))
    return {
        "v": SCHEMA_VERSION,
        "ts": now,
        "event": OUTBOUND_KIND,
        "actor": OUTBOUND_ACTOR,
        "data": data,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys
    from datetime import datetime, timezone
    from pathlib import Path

    from consilient.events import EventError, append

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", choices=("email", "sms"))
    parser.add_argument("--to", required=True)
    parser.add_argument("--body", required=True, help="message text")
    parser.add_argument("--subject", default="", help="email subject")
    parser.add_argument(
        "--authorise-egress",
        default="",
        help="required: why this message may leave the machine",
    )
    parser.add_argument(
        "--authorise-spend",
        default="",
        help="required for SMS: must name Twilio and an amount",
    )
    parser.add_argument("--log", default=".harness/log")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.channel == "email":
            event = send_email(
                to=args.to,
                subject=args.subject,
                text=args.body,
                authorise_egress=args.authorise_egress,
                dry_run=args.dry_run,
            )
        else:
            event = send_sms(
                to=args.to,
                text=args.body,
                authorise_egress=args.authorise_egress,
                authorise_spend=args.authorise_spend or None,
                dry_run=args.dry_run,
            )
    except OutboundError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        if args.json:
            print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"dry-run: {event['data']['transport_name']} to {event['data']['to']}")
        return 0
    log = Path(args.log)
    log.mkdir(parents=True, exist_ok=True)
    day = event["ts"][:10]
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        day = datetime.now(timezone.utc).date().isoformat()
    try:
        recorded = append(log / f"{day}.jsonl", event)
    except EventError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    artefact = recorded["data"].get("artefact")
    if args.json:
        print(json.dumps(recorded, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{recorded['event']} {artefact} -> {log / f'{day}.jsonl'}")
    return 0
