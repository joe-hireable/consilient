"""Tier-1 policy helpers for the harness knowledge access layer.

Source connectors are tier 2 (ADR-0065). This module validates declarations,
formats harness-specific config, and builds provenance records — it never performs
retrieval itself and never reads credentials from the repository tree.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Transport = Literal["stdio", "http"]

PERMISSIVE_LICENCES = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "0BSD",
        "Unlicense",
    }
)
NON_REDISTUTABLE_LICENCE_TAGS = frozenset({"proprietary-service"})

DEFAULT_SOURCES = Path(".harness/knowledge/sources.json")
SERVER_PREFIX = "consilient"


@dataclass(frozen=True)
class Connector:
    transport: Transport
    command: str | None = None
    args: tuple[str, ...] = ()
    env: dict[str, str] | None = None
    url: str | None = None


@dataclass(frozen=True)
class KnowledgeSource:
    id: str
    category: str
    purpose: str
    licence: str
    licence_url: str
    redistributable: bool
    metered: bool
    credential_env: tuple[str, ...]
    connector: Connector

    @property
    def server_name(self) -> str:
        return f"{SERVER_PREFIX}-{self.id}"

    def credential_status(self, environ: dict[str, str]) -> str:
        if self.metered:
            return "metered_refused"
        missing = [name for name in self.credential_env if not environ.get(name, "").strip()]
        if missing:
            return "not_configured"
        return "ready"


def _require_mapping(value: object, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be an object")
    return value


def load_sources(path: Path = DEFAULT_SOURCES) -> tuple[int, tuple[KnowledgeSource, ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    doc = _require_mapping(raw, "sources document")
    version = doc.get("version")
    if version != 1:
        raise ValueError(f"unsupported sources version {version!r}; expected 1")
    entries = doc.get("sources")
    if not isinstance(entries, list) or not entries:
        raise ValueError("sources must be a non-empty list")
    parsed: list[KnowledgeSource] = []
    seen: set[str] = set()
    for index, item in enumerate(entries):
        source = _parse_source(_require_mapping(item, f"sources[{index}]"))
        if source.id in seen:
            raise ValueError(f"duplicate source id {source.id!r}")
        seen.add(source.id)
        parsed.append(source)
    return version, tuple(parsed)


def _parse_source(raw: dict[str, Any]) -> KnowledgeSource:
    source_id = raw.get("id")
    if not isinstance(source_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", source_id):
        raise ValueError(f"source id must be a lowercase slug, got {source_id!r}")
    connector_raw = _require_mapping(raw.get("connector"), f"{source_id}.connector")
    transport = connector_raw.get("transport")
    if transport not in ("stdio", "http"):
        raise ValueError(f"{source_id}.connector.transport must be 'stdio' or 'http'")
    command = connector_raw.get("command")
    args_raw = connector_raw.get("args", [])
    env_raw = connector_raw.get("env")
    url = connector_raw.get("url")
    if transport == "stdio":
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"{source_id}.connector.command is required for stdio transport")
        if not isinstance(args_raw, list) or not all(isinstance(x, str) for x in args_raw):
            raise ValueError(f"{source_id}.connector.args must be a list of strings")
    else:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError(f"{source_id}.connector.url must be an http(s) URL")
    env: dict[str, str] | None = None
    if env_raw is not None:
        if not isinstance(env_raw, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in env_raw.items()
        ):
            raise ValueError(f"{source_id}.connector.env must be a string map")
        env = dict(env_raw)
    credential_env_raw = raw.get("credential_env", [])
    if not isinstance(credential_env_raw, list) or not all(
        isinstance(x, str) and x for x in credential_env_raw
    ):
        raise ValueError(f"{source_id}.credential_env must be a list of env var names")
    licence = raw.get("licence")
    if not isinstance(licence, str) or not licence.strip():
        raise ValueError(f"{source_id}.licence must be a non-empty string")
    redistributable = raw.get("redistributable")
    if not isinstance(redistributable, bool):
        raise ValueError(f"{source_id}.redistributable must be a boolean")
    metered = raw.get("metered")
    if not isinstance(metered, bool):
        raise ValueError(f"{source_id}.metered must be a boolean")
    if metered:
        raise ValueError(f"{source_id} is metered and refused by policy")
    for field in ("category", "purpose", "licence_url"):
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{source_id}.{field} must be a non-empty string")
    return KnowledgeSource(
        id=source_id,
        category=str(raw["category"]),
        purpose=str(raw["purpose"]),
        licence=licence,
        licence_url=str(raw["licence_url"]),
        redistributable=redistributable,
        metered=metered,
        credential_env=tuple(credential_env_raw),
        connector=Connector(
            transport=transport,
            command=str(command) if isinstance(command, str) else None,
            args=tuple(args_raw) if isinstance(args_raw, list) else (),
            env=env,
            url=str(url) if isinstance(url, str) else None,
        ),
    )


def cursor_entry(source: KnowledgeSource) -> dict[str, Any]:
    if source.connector.transport == "http":
        entry: dict[str, Any] = {"url": source.connector.url}
        return entry
    entry = {
        "command": source.connector.command,
        "args": list(source.connector.args),
    }
    if source.connector.env:
        entry["env"] = dict(source.connector.env)
    return entry


def grok_entry(source: KnowledgeSource) -> dict[str, Any]:
    if source.connector.transport == "http":
        return {"url": source.connector.url, "enabled": True}
    payload: dict[str, Any] = {
        "command": source.connector.command,
        "args": list(source.connector.args),
        "enabled": True,
        "startup_timeout_sec": 120,
    }
    if source.connector.env:
        payload["env"] = dict(source.connector.env)
    return payload


def codex_entry(source: KnowledgeSource) -> dict[str, Any]:
    if source.connector.transport == "http":
        return {"url": source.connector.url}
    payload: dict[str, Any] = {
        "command": source.connector.command,
        "args": list(source.connector.args),
        "startup_timeout_sec": 120,
    }
    if source.connector.env:
        payload["env"] = dict(source.connector.env)
    return payload


def merge_cursor(existing: dict[str, Any], sources: tuple[KnowledgeSource, ...]) -> dict[str, Any]:
    merged = dict(existing)
    servers = dict(merged.get("mcpServers", {}))
    for source in sources:
        servers[source.server_name] = cursor_entry(source)
    merged["mcpServers"] = servers
    return merged


def render_grok_toml(existing_text: str, sources: tuple[KnowledgeSource, ...]) -> str:
    lines = [existing_text.rstrip(), ""]
    for source in sources:
        lines.append(f"[mcp_servers.{source.server_name}]")
        entry = grok_entry(source)
        if "url" in entry:
            lines.append(f'url = "{entry["url"]}"')
            lines.append("enabled = true")
            continue
        lines.append(f'command = "{entry["command"]}"')
        lines.append("args = [")
        for arg in entry["args"]:
            lines.append(f'    "{arg}",')
        lines.append("]")
        lines.append("startup_timeout_sec = 120")
        lines.append("enabled = true")
        if source.connector.env:
            lines.append("env = {")
            for key, value in source.connector.env.items():
                lines.append(f'    {key} = "{value}"')
            lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_codex_toml(existing_text: str, sources: tuple[KnowledgeSource, ...]) -> str:
    lines = [existing_text.rstrip(), ""]
    for source in sources:
        lines.append(f"[mcp_servers.{source.server_name}]")
        entry = codex_entry(source)
        if "url" in entry:
            lines.append(f'url = "{entry["url"]}"')
            lines.append("")
            continue
        lines.append(f'command = "{entry["command"]}"')
        if entry["args"]:
            lines.append("args = [")
            for arg in entry["args"]:
                lines.append(f'    "{arg}",')
            lines.append("]")
        else:
            lines.append("args = []")
        lines.append("startup_timeout_sec = 120")
        if source.connector.env:
            lines.append("[mcp_servers." + source.server_name + ".env]")
            for key, value in source.connector.env.items():
                lines.append(f'{key} = "{value}"')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_retrieval_event(
    *,
    source: KnowledgeSource,
    status: str,
    retrieved_at: str,
    uri: str = "",
    reason: str = "",
    content_digest: str = "",
    query: str = "",
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source_id": source.id,
        "source_url": source.licence_url,
        "licence": source.licence,
        "category": source.category,
        "retrieved_at": retrieved_at,
        "status": status,
    }
    if query:
        data["query"] = query
    if uri:
        data["uri"] = uri
    if reason:
        data["reason"] = reason
    if content_digest:
        data["content_digest"] = content_digest
    return data
