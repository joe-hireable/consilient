"""Sign and verify verdict payloads with OpenSSH SSHSIG."""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


NAMESPACE = "consilient.verdict.v1"
SIGNATURE_FIELD = "signature"


def _canonical(payload: Mapping[str, Any]) -> bytes:
    """Return the signed representation, excluding any attached signature."""
    unsigned = {key: value for key, value in payload.items() if key != SIGNATURE_FIELD}
    return json.dumps(unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )


def _run(*args: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        input=input,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def sign(payload: Mapping[str, Any], private_key: Path) -> dict[str, Any]:
    """Return *payload* with an SSHSIG signature; no principal is accepted here."""
    signed_bytes = _canonical(payload)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "verdict"
        source.write_bytes(signed_bytes)
        result = _run("ssh-keygen", "-Y", "sign", "-f", str(private_key), "-n", NAMESPACE, str(source))
        signature = Path(f"{source}.sig")
        if result.returncode or not signature.is_file():
            raise RuntimeError("ssh-keygen could not sign the verdict")
        signature_text = signature.read_text(encoding="utf-8", errors="replace")
    return {key: value for key, value in payload.items() if key != SIGNATURE_FIELD} | {
        SIGNATURE_FIELD: signature_text
    }


def verify(payload: Mapping[str, Any], allowed_signers: Path) -> tuple[bool, str | None]:
    """Verify *payload* and derive its sole principal from *allowed_signers*."""
    signature_text = payload.get(SIGNATURE_FIELD)
    if not isinstance(signature_text, str):
        return False, None
    try:
        signed_bytes = _canonical(payload)
    except (TypeError, ValueError):
        return False, None

    with tempfile.TemporaryDirectory() as directory:
        signature = Path(directory) / "verdict.sig"
        try:
            signature.write_text(signature_text, encoding="utf-8")
        except (OSError, UnicodeError):
            return False, None
        principals = _run(
            "ssh-keygen",
            "-Y",
            "find-principals",
            "-f",
            str(allowed_signers),
            "-s",
            str(signature),
            "-n",
            NAMESPACE,
        )
        matches = {line.strip() for line in principals.stdout.splitlines() if line.strip()}
        if principals.returncode or len(matches) != 1:
            return False, None
        principal = matches.pop()
        checked = _run(
            "ssh-keygen",
            "-Y",
            "verify",
            "-f",
            str(allowed_signers),
            "-I",
            principal,
            "-n",
            NAMESPACE,
            "-s",
            str(signature),
            input=signed_bytes.decode("utf-8"),
        )
    return (checked.returncode == 0, principal if checked.returncode == 0 else None)
