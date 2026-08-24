from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sign_verdict.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sign_verdict", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> None:
    subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_verify_derives_allowed_signer_principal_and_rejects_tampering(tmp_path: Path) -> None:
    """A claimed principal or changed byte must not survive the SSH signature check."""
    private_key = tmp_path / "verdict-key"
    _run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_key))
    allowed_signers = tmp_path / "allowed_signers"
    allowed_signers.write_text(
        f"reviewer {private_key.with_suffix('.pub').read_text(encoding='utf-8')}",
        encoding="utf-8",
    )

    signed = _load().sign(
        {"human_verdict": "reject", "principal": "forged-principal"}, private_key
    )

    assert _load().verify(signed, allowed_signers) == (True, "reviewer")

    tampered = {**signed, "human_verdict": "oeject"}
    assert _load().verify(tampered, allowed_signers) == (False, None)

    malformed_signature = {**signed, "signature": "\ud800"}
    assert _load().verify(malformed_signature, allowed_signers) == (False, None)
