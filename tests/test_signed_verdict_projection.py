"""AT — a signed ssh_sig verdict projects as authenticated.

`events.validate` still refuses every via other than cli (V0-28), so these tests
drive `_verdict_auth_status` and `_apply_verdict` directly. A JSONL line with
`via=ssh_sig` cannot survive `read_all` until the writer accepts that channel.
Declared-principal cli rows must stay refused: an agent can write one.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

from consilient import beta as beta_mod
from consilient import events as events_mod
from consilient import projection
from consilient.events import SCHEMA_VERSION, Event, canonical


HUMAN = "joe-brown"
ROOT = Path(__file__).resolve().parents[1]
SIGN_SCRIPT = ROOT / "scripts" / "sign_verdict.py"


def _now_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _ev(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _outcome(attempt_id: str, task: str, accept: bool) -> dict[str, object]:
    return _ev(
        event=events_mod.OUTCOME_KIND,
        data={
            "attempt_id": attempt_id,
            "task": task,
            "verifier_accept": accept,
            "task_family": "repair",
            "verifier_version": "v1",
        },
    )


def _write_log(path: Path, *lines: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(canonical(line) for line in lines) + "\n",
        encoding="utf-8",
    )


def _verdict_event(
    attempt_id: str,
    human_verdict: str,
    *,
    via: str,
    principal: str | None = None,
    extra: dict[str, object] | None = None,
) -> Event:
    data: dict[str, object] = {
        "attempt_id": attempt_id,
        "human_verdict": human_verdict,
        "via": via,
    }
    if principal is not None:
        data["principal"] = principal
    if extra:
        data.update(extra)
    return Event(
        _ev(
            actor=principal or "reviewer",
            event=events_mod.VERDICT_KIND,
            data=data,
        )
    )


def _load_sign_verdict() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sign_verdict", SIGN_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_ssh_sig_is_authenticated_even_when_the_principal_field_is_forged() -> None:
    """Auth status comes from the signed channel, never from a caller-supplied name."""
    forged = {
        "via": "ssh_sig",
        "principal": "forged-principal",
        "human_verdict": "reject",
    }
    assert projection._verdict_auth_status(forged) == "authenticated"
    padded = {"via": " SSH_SIG ", "human_verdict": "reject"}
    assert projection._verdict_auth_status(padded) == "authenticated"


def test_declared_principal_cli_stays_unauthenticated_for_beta() -> None:
    """A local agent can write a syntactically valid cli verdict; that must not count."""
    declared = {
        "via": "cli",
        "principal": HUMAN,
        "human_verdict": "reject",
    }
    assert projection._verdict_auth_status(declared) == "declared_principal"
    assert not beta_mod.admits_human_beta_row(
        {
            "estimand_kind": beta_mod.HUMAN_VERDICT_BETA,
            "auth_status": "declared_principal",
        }
    )


def test_phone_webauthn_is_no_longer_an_authenticated_via() -> None:
    """The unreachable WebAuthn branch is deleted rather than implemented."""
    assert (
        projection._verdict_auth_status({"via": "phone_webauthn", "principal": HUMAN})
        == "unauthenticated"
    )


def test_signed_verdict_reaches_outcomes_and_admits_human_beta(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(path, _outcome("attempt-signed", "signed-task", True))

    conn = projection.build(log_dir, db)
    projection._apply_verdict(
        conn,
        1,
        _verdict_event(
            "attempt-signed",
            "reject",
            via="ssh_sig",
            principal="forged-principal",
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT human_verdict, estimand_kind, auth_status FROM outcomes "
        "WHERE attempt_id = ?",
        ("attempt-signed",),
    ).fetchone()
    assert row == ("reject", beta_mod.HUMAN_VERDICT_BETA, "authenticated")
    assert beta_mod.admits_human_beta_row(
        {"estimand_kind": row[1], "auth_status": row[2]}
    )
    conn.close()


def test_cli_verdict_still_projects_but_is_not_admitted(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-cli", "cli-task", True),
        _ev(
            actor=HUMAN,
            event=events_mod.VERDICT_KIND,
            data={
                "attempt_id": "attempt-cli",
                "human_verdict": "reject",
                "principal": HUMAN,
                "via": "cli",
            },
        ),
    )

    conn = projection.build(log_dir, db)
    row = conn.execute(
        "SELECT human_verdict, auth_status FROM outcomes WHERE attempt_id = ?",
        ("attempt-cli",),
    ).fetchone()
    assert row == ("reject", "declared_principal")
    assert not beta_mod.admits_human_beta_row(
        {
            "estimand_kind": beta_mod.HUMAN_VERDICT_BETA,
            "auth_status": row[1],
        }
    )
    assert beta_mod.from_connection(conn).n_rejected == 0
    conn.close()


def test_verdict_produced_by_sign_verdict_reaches_outcomes(tmp_path: Path) -> None:
    """U4 done criterion: a payload from the shipped signer reaches outcomes.human_verdict."""
    private_key = tmp_path / "verdict-key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    signed = _load_sign_verdict().sign(
        {
            "attempt_id": "attempt-tool",
            "human_verdict": "reject",
            "principal": "forged-principal",
        },
        private_key,
    )
    assert "signature" in signed

    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(path, _outcome("attempt-tool", "tool-task", True))
    conn = projection.build(log_dir, db)
    projection._apply_verdict(
        conn,
        1,
        _verdict_event(
            "attempt-tool",
            "reject",
            via="ssh_sig",
            principal="forged-principal",
            extra={"signature": signed["signature"]},
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT human_verdict, auth_status FROM outcomes WHERE attempt_id = ?",
        ("attempt-tool",),
    ).fetchone()
    assert row == ("reject", "authenticated")
    conn.close()
