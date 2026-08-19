"""EXP-27 phase-A probe of fixed first-party change/status sources."""

import json
import urllib.request
from datetime import datetime, timezone


SOURCES = [
    {
        "harness": "claude-code",
        "kind": "release",
        "url": "https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/feed.xml",
    },
    {
        "harness": "claude-code",
        "kind": "status",
        "url": "https://status.claude.com/api/v2/summary.json",
    },
    {
        "harness": "codex",
        "kind": "release",
        "url": "https://github.com/openai/codex/releases.atom",
    },
    {
        "harness": "codex",
        "kind": "status",
        "url": "https://status.openai.com/api/v2/summary.json",
    },
    {
        "harness": "cursor",
        "kind": "release-html",
        "url": "https://cursor.com/changelog",
    },
    {
        "harness": "cursor",
        "kind": "status",
        "url": "https://status.cursor.com/api/v2/summary.json",
    },
]


def probe(source):
    request = urllib.request.Request(
        source["url"], headers={"User-Agent": "consilience-exp27/0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        sample = response.read(4096)
        return {
            **source,
            "status": response.status,
            "content_type": response.headers.get_content_type(),
            "sample_bytes": len(sample),
        }


if __name__ == "__main__":
    result = {
        "experiment": "EXP-27-phase-A",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sources": [probe(source) for source in SOURCES],
    }
    print(json.dumps(result, indent=2))
