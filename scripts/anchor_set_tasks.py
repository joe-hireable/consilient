"""The task row both halves read: what a bank entry must contain, and the digest that
stands for its body.

The builder canonicalises rows before ranking them and the drift comparison
canonicalises the same rows before indexing outcomes, so the format sits in neither and
is shared by both. A row carries a family, an id, an optional cluster, and either a
content body or a declared ``content_sha256``.

The body is hashed and then discarded — it is never carried into the written set, which
is what makes a leaked file composition plus a digest rather than the prompts. Where a
body and a declared digest are both supplied they must agree, and a row that supplies
neither takes the digest of the empty string."""

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

EMPTY_CONTENT_SHA256 = hashlib.sha256(b"").hexdigest()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class AnchorSetError(ValueError):
    """The set cannot be built, written or compared."""


def canonical_dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text_field(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AnchorSetError(f"task {key} must be a non-empty string")
    return value.strip()


def _optional_text(row: Mapping[str, Any], key: str) -> str | None:
    if key not in row or row[key] is None:
        return None
    value = row[key]
    if not isinstance(value, str):
        raise AnchorSetError(f"task {key} must be a string")
    return value


def _hex64(value: str, *, label: str) -> str:
    text = value.strip().lower()
    if len(text) != 64:
        raise AnchorSetError(f"{label} must be 64 lowercase hex characters")
    int(text, 16)
    return text


def _content_sha256(row: Mapping[str, Any]) -> str:
    content = _optional_text(row, "content")
    declared = _optional_text(row, "content_sha256")
    digest = (
        hashlib.sha256(content.encode("utf-8")).hexdigest()
        if content is not None
        else None
    )
    if digest is not None and declared is not None:
        declared = _hex64(declared, label="content_sha256")
        if digest != declared:
            raise AnchorSetError("content_sha256 does not match the supplied content")
        return digest
    if digest is not None:
        return digest
    if declared is not None:
        return _hex64(declared, label="content_sha256")
    return EMPTY_CONTENT_SHA256


def _canonical_task(row: Mapping[str, Any]) -> dict[str, str]:
    family = _text_field(row, "family")
    task_id = _text_field(row, "id")
    cluster = _optional_text(row, "cluster")
    return {
        "cluster": cluster.strip() if cluster else task_id,
        "content_sha256": _content_sha256(row),
        "family": family,
        "id": task_id,
    }
