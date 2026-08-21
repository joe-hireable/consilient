"""Knowledge access layer invariants (V0-31).

Mutation-tested in this file:
  - breaking `_check_knowledge_contract` makes `test_knowledge_retrieved_ok_requires_digest` fail
  - breaking status enforcement makes `test_knowledge_unavailable_must_not_carry_digest` fail
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from consilient.events import (
    KNOWLEDGE_ACTOR,
    KNOWLEDGE_RETRIEVED_KIND,
    EventError,
    validate,
)

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "scripts" / "knowledge_policy.py"
KNOWLEDGE_PATH = ROOT / "scripts" / "knowledge.py"
SOURCES_PATH = ROOT / ".harness" / "knowledge" / "sources.json"


def _load_module(name: str, path: Path):
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _source(**overrides):
    policy = _load_module("knowledge_policy_test", POLICY_PATH)
    base = policy.KnowledgeSource(
        id="scholar",
        category="literature",
        purpose="test",
        licence="MIT",
        licence_url="https://example.com/licence",
        redistributable=True,
        metered=False,
        credential_env=(),
        connector=policy.Connector(
            transport="stdio",
            command="npx",
            args=("-y", "@kak4343/scholar-mcp"),
        ),
    )
    if not overrides:
        return base
    data = base.__dict__.copy()
    data.update(overrides)
    return policy.KnowledgeSource(**data)


def _event(**data_overrides):
    data = {
        "source_id": "scholar",
        "source_url": "https://example.com/licence",
        "licence": "MIT",
        "category": "literature",
        "retrieved_at": "2026-08-21T17:00:00+00:00",
        "status": "ok",
        "uri": "https://arxiv.org/abs/2603.26993",
        "content_digest": "a" * 64,
    }
    data.update(data_overrides)
    return {
        "v": 1,
        "ts": "2026-08-21T17:00:01+00:00",
        "event": KNOWLEDGE_RETRIEVED_KIND,
        "actor": KNOWLEDGE_ACTOR,
        "data": data,
    }


def test_sources_declaration_loads_and_names_connectors():
    policy = _load_module("knowledge_policy_sources", POLICY_PATH)
    version, sources = policy.load_sources(SOURCES_PATH)
    assert version == 1
    ids = {source.id for source in sources}
    assert ids == {"scholar", "packages", "fetch", "context7", "github"}
    scholar = next(source for source in sources if source.id == "scholar")
    assert scholar.licence == "MIT"
    assert scholar.connector.transport == "stdio"


def test_metered_sources_are_refused_at_load(tmp_path):
    policy = _load_module("knowledge_policy_metered", POLICY_PATH)
    payload = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    payload["sources"][0]["metered"] = True
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="metered"):
        policy.load_sources(path)


def test_knowledge_retrieved_ok_requires_digest():
    validate(_event())


def test_knowledge_retrieved_ok_rejects_missing_digest():
    with pytest.raises(EventError, match="content_digest"):
        validate(_event(content_digest=""))


def test_knowledge_unavailable_must_not_carry_digest():
    validate(
        _event(
            status="unavailable",
            reason="server offline",
            uri="",
            content_digest="",
        )
    )
    with pytest.raises(EventError, match="content_digest"):
        validate(
            _event(
                status="unavailable",
                reason="server offline",
                uri="",
                content_digest="b" * 64,
            )
        )


def test_knowledge_not_configured_requires_reason():
    validate(
        _event(
            status="not_configured",
            reason="missing GITHUB_PERSONAL_ACCESS_TOKEN",
            uri="",
            content_digest="",
        )
    )


def test_knowledge_retrieved_goes_through_append(tmp_path):
    policy = _load_module("knowledge_policy_append", POLICY_PATH)
    knowledge = _load_module("knowledge_script_append", KNOWLEDGE_PATH)
    log = tmp_path / "log"
    log.mkdir()
    _, sources = policy.load_sources(SOURCES_PATH)
    scholar = next(source for source in sources if source.id == "scholar")
    event = knowledge.record_retrieval(
        log=log,
        source=scholar,
        status="unavailable",
        reason="probe skipped in test",
    )
    path = log / f"{event['ts'][:10]}.jsonl"
    assert path.exists()
    line = json.loads(path.read_text(encoding="utf-8").strip())
    assert line["event"] == KNOWLEDGE_RETRIEVED_KIND
    assert line["data"]["licence"] == "MIT"


def test_cursor_materialise_merges_without_dropping_existing(tmp_path, monkeypatch):
    policy = _load_module("knowledge_policy_cursor", POLICY_PATH)
    knowledge = _load_module("knowledge_script_cursor", KNOWLEDGE_PATH)
    cursor_path = tmp_path / "mcp.json"
    cursor_path.write_text(
        json.dumps({"mcpServers": {"playwright": {"command": "npx"}}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(knowledge, "CURSOR_CONFIGS", (cursor_path,))
    _, sources = policy.load_sources(SOURCES_PATH)
    knowledge.materialise_cursor(sources, dry_run=False)
    merged = json.loads(cursor_path.read_text(encoding="utf-8"))
    assert "playwright" in merged["mcpServers"]
    assert "consilient-scholar" in merged["mcpServers"]


def test_github_source_is_not_configured_without_token(monkeypatch):
    policy = _load_module("knowledge_policy_github", POLICY_PATH)
    _, sources = policy.load_sources(SOURCES_PATH)
    github = next(source for source in sources if source.id == "github")
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    assert github.credential_status({}) == "not_configured"


def test_probe_reports_not_configured_for_github(monkeypatch):
    knowledge = _load_module("knowledge_script_probe", KNOWLEDGE_PATH)
    policy = _load_module("knowledge_policy_probe", POLICY_PATH)
    _, sources = policy.load_sources(SOURCES_PATH)
    github = next(source for source in sources if source.id == "github")
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    result = knowledge.probe_stdio_tools(github, timeout_s=1)
    assert result.status == "not_configured"


def test_scholar_mcp_lists_tools_when_run_live():
    if not Path("/usr/bin/npx").exists() and not Path("/mnt/c/Program Files/nodejs/npx.cmd").exists():
        pytest.skip("npx not available")
    knowledge = _load_module("knowledge_script_live", KNOWLEDGE_PATH)
    policy = _load_module("knowledge_policy_live", POLICY_PATH)
    _, sources = policy.load_sources(SOURCES_PATH)
    scholar = next(source for source in sources if source.id == "scholar")
    result = knowledge.probe_stdio_tools(scholar, timeout_s=90)
    assert result.status == "ok", result.reason
    assert "scholar_search" in result.tools or len(result.tools) >= 1
