"""Knowledge access layer for dispatched harnesses.

Declares free/public knowledge connectors, materialises them into each harness's MCP
config format, verifies servers by listing tools, and records retrieval provenance
through the single append() writer.

    python scripts/knowledge.py materialise --harness cursor
    python scripts/knowledge.py verify
    python scripts/knowledge.py record --source scholar --status unavailable --reason "offline"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from consilient.events import (  # noqa: E402
    KNOWLEDGE_ACTOR,
    KNOWLEDGE_RETRIEVED_KIND,
    SCHEMA_VERSION,
    append,
)  # noqa: E402
from knowledge_policy import (  # noqa: E402
    DEFAULT_SOURCES,
    KnowledgeSource,
    build_retrieval_event,
    load_sources,
    merge_cursor,
    render_codex_toml,
    render_grok_toml,
    utc_now,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_LOG = ROOT / ".harness" / "log"
CURSOR_CONFIGS = (
    Path.home() / ".cursor" / "mcp.json",
    Path("/mnt/c/Users/jpbpr/.cursor/mcp.json"),
    Path("C:/Users/jpbpr/.cursor/mcp.json"),
)
GROK_CONFIGS = (
    Path("/mnt/c/Users/jpbpr/.grok/config.toml"),
    Path("C:/Users/jpbpr/.grok/config.toml"),
)
CODEX_CONFIGS = (
    Path("/mnt/c/Users/jpbpr/.codex/config.toml"),
    Path("C:/Users/jpbpr/.codex/config.toml"),
)
MCP_PROTOCOL = "2024-11-05"
PROBE_TIMEOUT_S = 45


@dataclass(frozen=True)
class VerifyResult:
    source: KnowledgeSource
    status: str
    tools: tuple[str, ...]
    reason: str


def _which(name: str) -> str | None:
    return shutil.which(name)


def _probe_command(source: KnowledgeSource) -> tuple[list[str], dict[str, str], bool] | None:
    env = os.environ.copy()
    if source.connector.env:
        for key, value in source.connector.env.items():
            if value.startswith("${env:") and value.endswith("}"):
                env_name = value[6:-1]
                env[key] = os.environ.get(env_name, "")
            else:
                env[key] = value
    command = source.connector.command
    if not command:
        return None
    resolved = _which(command)
    if resolved:
        if os.name == "nt" and resolved.lower().endswith((".cmd", ".bat")):
            return ["cmd", "/c", command, *source.connector.args], env, False
        return [resolved, *source.connector.args], env, False
    wsl = _which("wsl")
    if wsl and command in {"npx", "uvx", "docker"}:
        return [wsl, command, *source.connector.args], env, False
    return None


def _json_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def _read_json_line(stream, timeout_s: float) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        line = stream.readline()
        if not line:
            time.sleep(0.05)
            continue
        if not line.strip():
            continue
        parsed = json.loads(line.decode("utf-8", errors="replace"))
        if isinstance(parsed, dict):
            return parsed
    return None


def probe_stdio_tools(source: KnowledgeSource, timeout_s: int = PROBE_TIMEOUT_S) -> VerifyResult:
    if source.connector.transport != "stdio":
        return VerifyResult(source, "skipped", (), "http transport is not probed here")
    if source.credential_status(os.environ) == "not_configured":
        return VerifyResult(
            source,
            "not_configured",
            (),
            f"missing credential env: {', '.join(source.credential_env)}",
        )
    resolved = _probe_command(source)
    if resolved is None:
        return VerifyResult(source, "unavailable", (), "spawn failed: command not on PATH")
    argv, env, _use_shell = resolved
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=False,
        )
    except OSError as exc:
        return VerifyResult(source, "unavailable", (), f"spawn failed: {exc}")
    assert process.stdin is not None and process.stdout is not None
    try:
        process.stdin.write(
            _json_line(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL,
                        "capabilities": {},
                        "clientInfo": {"name": "consilient-knowledge", "version": "0.1.0"},
                    },
                }
            )
        )
        process.stdin.flush()
        init_response = _read_json_line(process.stdout, timeout_s / 2)
        if not init_response or "error" in init_response:
            reason = "initialize failed"
            if init_response and "error" in init_response:
                reason = str(init_response["error"])
            return VerifyResult(source, "unavailable", (), reason)
        process.stdin.write(
            _json_line({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        )
        process.stdin.flush()
        process.stdin.write(_json_line({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        process.stdin.flush()
        tools_response = _read_json_line(process.stdout, timeout_s / 2)
        if not tools_response or "error" in tools_response:
            reason = "tools/list failed"
            if tools_response and "error" in tools_response:
                reason = str(tools_response["error"])
            return VerifyResult(source, "unavailable", (), reason)
        result = tools_response.get("result")
        if not isinstance(result, dict):
            return VerifyResult(source, "unavailable", (), "tools/list returned no result object")
        tools_raw = result.get("tools")
        if not isinstance(tools_raw, list) or not tools_raw:
            return VerifyResult(source, "unavailable", (), "server returned zero tools")
        names = tuple(
            str(item["name"])
            for item in tools_raw
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        )
        if not names:
            return VerifyResult(source, "unavailable", (), "tool names were not readable")
        return VerifyResult(source, "ok", names, "")
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def materialise_cursor(sources: tuple[KnowledgeSource, ...], dry_run: bool) -> list[Path]:
    written: list[Path] = []
    for path in CURSOR_CONFIGS:
        existing: dict[str, Any] = {}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8-sig"))
        merged = merge_cursor(existing, sources)
        if dry_run:
            print(json.dumps({str(path): merged["mcpServers"]}, indent=2))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def materialise_grok(sources: tuple[KnowledgeSource, ...], dry_run: bool) -> list[Path]:
    written: list[Path] = []
    for path in GROK_CONFIGS:
        if not path.parent.exists():
            continue
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        rendered = render_grok_toml(existing, sources)
        if dry_run:
            print(rendered)
            written.append(path)
            continue
        path.write_text(rendered, encoding="utf-8")
        written.append(path)
    return written


def materialise_codex(sources: tuple[KnowledgeSource, ...], dry_run: bool) -> list[Path]:
    written: list[Path] = []
    for path in CODEX_CONFIGS:
        if not path.parent.exists():
            continue
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        rendered = render_codex_toml(existing, sources)
        if dry_run:
            print(rendered)
            written.append(path)
            continue
        path.write_text(rendered, encoding="utf-8")
        written.append(path)
    return written


def record_retrieval(
    *,
    log: Path,
    source: KnowledgeSource,
    status: str,
    reason: str = "",
    uri: str = "",
    query: str = "",
    content: bytes = b"",
) -> dict[str, Any]:
    retrieved_at = utc_now()
    digest = hashlib.sha256(content).hexdigest() if content else ""
    data = build_retrieval_event(
        source=source,
        status=status,
        retrieved_at=retrieved_at,
        uri=uri,
        reason=reason,
        content_digest=digest,
        query=query,
    )
    event = {
        "v": SCHEMA_VERSION,
        "ts": retrieved_at,
        "event": KNOWLEDGE_RETRIEVED_KIND,
        "actor": KNOWLEDGE_ACTOR,
        "data": data,
    }
    path = log / f"{retrieved_at[:10]}.jsonl"
    append(path, event)
    return event


def _find_source(sources: tuple[KnowledgeSource, ...], source_id: str) -> KnowledgeSource:
    for source in sources:
        if source.id == source_id:
            return source
    raise SystemExit(f"unknown source id {source_id!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES), help="sources declaration")
    sub = parser.add_subparsers(dest="command", required=True)

    materialise = sub.add_parser("materialise", help="write harness MCP configs")
    materialise.add_argument(
        "--harness",
        choices=("cursor", "grok", "codex", "all"),
        default="all",
    )
    materialise.add_argument("--dry-run", action="store_true")

    verify = sub.add_parser("verify", help="probe stdio MCP servers and list tools")
    verify.add_argument("--timeout", type=int, default=PROBE_TIMEOUT_S)
    verify.add_argument("--source", action="append", dest="sources_filter")

    record = sub.add_parser("record", help="append a knowledge.retrieved event")
    record.add_argument("--log", default=str(DEFAULT_LOG))
    record.add_argument("--source", required=True)
    record.add_argument(
        "--status",
        choices=("ok", "unavailable", "not_configured"),
        required=True,
    )
    record.add_argument("--reason", default="")
    record.add_argument("--uri", default="")
    record.add_argument("--query", default="")
    record.add_argument("--content-file", default="")

    args = parser.parse_args(argv)
    _, sources = load_sources(Path(args.sources))

    if args.command == "materialise":
        if args.harness in ("cursor", "all"):
            paths = materialise_cursor(sources, args.dry_run)
            for path in paths:
                print(f"cursor: {path}")
        if args.harness in ("grok", "all"):
            for path in materialise_grok(sources, args.dry_run):
                print(f"grok: {path}")
        if args.harness in ("codex", "all"):
            for path in materialise_codex(sources, args.dry_run):
                print(f"codex: {path}")
        return 0

    if args.command == "verify":
        selected = sources
        if args.sources_filter:
            wanted = set(args.sources_filter)
            selected = tuple(source for source in sources if source.id in wanted)
        results = [probe_stdio_tools(source, timeout_s=args.timeout) for source in selected]
        for result in results:
            if result.status == "ok":
                print(
                    f"{result.source.id}: ok ({len(result.tools)} tools) "
                    f"{', '.join(result.tools[:8])}"
                )
            else:
                detail = result.reason or result.status
                print(f"{result.source.id}: {result.status} — {detail}")
        return 0

    source = _find_source(sources, args.source)
    content = b""
    if args.content_file:
        content = Path(args.content_file).read_bytes()
    if args.status == "ok" and not args.uri:
        raise SystemExit("--uri is required when status is ok")
    if args.status != "ok" and not args.reason:
        raise SystemExit("--reason is required when status is not ok")
    event = record_retrieval(
        log=Path(args.log),
        source=source,
        status=args.status,
        reason=args.reason,
        uri=args.uri,
        query=args.query,
        content=content,
    )
    print(f"{event['event']} {args.source} -> {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
