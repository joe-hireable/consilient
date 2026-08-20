"""EXP-27 longitudinal collector — day N of the fixed 30-day window.

Authorised by Joe on 20 August 2026 ("YES PROCEED"), after the register recorded that every
day of delay costs a day off a 30-day clock that cannot be made up.

What this is allowed to do, from the registration:

  * poll the **fixed six** first-party endpoints in `probe_sources.SOURCES`, conditionally
  * freeze every source event by upstream id or content hash
  * append one observation per source per run to a JSONL log

What it must never do, and cannot:

  * no model inference, no metered provider, no authenticated call
  * **no resource-ledger mutation.** Every emitted record passes `validate_change_record`,
    which rejects any record claiming to increase headroom, decrease usage, move a reset
    window or mark unknown headroom usable. A change feed is an *invalidation* signal; only
    an authenticated account read may ever credit resource state. That is ADR-0029's whole
    point and it is enforced here rather than promised.

Run once per day:

    python docs/10-research/experiments/exp27/collector.py

Idempotent within a day: a second run on the same date records a fresh observation but
adds no duplicate events, because events are keyed by content hash.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from change_record import validate_change_record  # noqa: E402
from probe_sources import SOURCES  # noqa: E402

LOG = HERE / "collector-log.jsonl"
STATE = HERE / "collector-state.json"
TIMEOUT_S = 30
UA = "consilience-exp27-collector/1 (read-only change-intelligence probe)"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fetch(source: dict, state: dict) -> dict:
    """One conditional GET. Never raises: a failure is an observation, not a crash."""
    url = source["url"]
    prior = state.get(url, {})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if prior.get("etag"):
        req.add_header("If-None-Match", prior["etag"])
    if prior.get("last_modified"):
        req.add_header("If-Modified-Since", prior["last_modified"])

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = resp.read()
            return {
                "status": resp.status,
                "etag": resp.headers.get("ETag"),
                "last_modified": resp.headers.get("Last-Modified"),
                "content_type": resp.headers.get("Content-Type"),
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        # 304 is the good case: the source is unchanged since our last conditional read.
        return {
            "status": exc.code,
            "etag": prior.get("etag"),
            "last_modified": prior.get("last_modified"),
            "bytes": 0,
            "sha256": prior.get("sha256"),
            "body": b"",
        }
    except Exception as exc:  # network, DNS, TLS, timeout
        return {"status": None, "error": f"{type(exc).__name__}: {exc}", "body": b""}


ENTRY_PATTERNS = (
    re.compile(rb"<entry\b.*?</entry>", re.S | re.I),  # atom
    re.compile(rb"<item\b.*?</item>", re.S | re.I),  # rss
)
ID_PATTERN = re.compile(rb"<(?:id|guid)[^>]*>(.*?)</(?:id|guid)>", re.S | re.I)
TITLE_PATTERN = re.compile(rb"<title[^>]*>(.*?)</title>", re.S | re.I)


def extract_events(source: dict, body: bytes) -> list[dict]:
    """Freeze each source event by upstream id where one exists, else by content hash.

    Deliberately shallow. This is a *detection* instrument: its job is to notice that
    something changed and to identify it stably enough not to double-count. Interpreting
    what a release means is a human's job, and pretending otherwise is how a change feed
    starts claiming authority over resource state.
    """
    if not body:
        return []
    kind = source["kind"]
    if kind == "status":
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except ValueError:
            return []
        events = []
        for inc in (data.get("incidents") or []) + (
            data.get("scheduled_maintenances") or []
        ):
            events.append(
                {
                    "upstream_id": inc.get("id"),
                    "title": (inc.get("name") or "")[:200],
                    "status": inc.get("status"),
                    "updated_at": inc.get("updated_at"),
                }
            )
        return events

    chunks: list[bytes] = []
    for pat in ENTRY_PATTERNS:
        chunks = pat.findall(body)
        if chunks:
            break
    if not chunks:
        # Cursor's HTML changelog has no feed; hash the whole document so a change is
        # detectable even though individual entries are not separable.
        return [
            {
                "upstream_id": None,
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "title": "(unparsed document; whole-page hash)",
            }
        ]

    events = []
    for chunk in chunks[:50]:
        ident = ID_PATTERN.search(chunk)
        title = TITLE_PATTERN.search(chunk)
        events.append(
            {
                "upstream_id": ident.group(1).decode("utf-8", "replace").strip()
                if ident
                else None,
                "content_sha256": hashlib.sha256(chunk).hexdigest(),
                "title": (
                    title.group(1).decode("utf-8", "replace").strip()[:200]
                    if title
                    else None
                ),
            }
        )
    return events


def event_key(source: dict, event: dict) -> str:
    return "|".join(
        [
            source["harness"],
            source["kind"],
            event.get("upstream_id") or event.get("content_sha256") or "",
        ]
    )


def collect() -> int:
    state = _load_state()
    seen: set[str] = set(state.get("_seen_event_keys", []))
    stamp = _now()
    new_events = 0
    observations = []

    for source in SOURCES:
        result = fetch(source, state)
        body = result.pop("body", b"")
        events = extract_events(source, body) if result.get("status") == 200 else []
        fresh = [e for e in events if event_key(source, e) not in seen]
        for e in fresh:
            seen.add(event_key(source, e))
        new_events += len(fresh)

        record = {
            "v": 1,
            "ts": stamp,
            "harness": source["harness"],
            "kind": source["kind"],
            "url": source["url"],
            "http_status": result.get("status"),
            "unchanged_304": result.get("status") == 304,
            "error": result.get("error"),
            "bytes": result.get("bytes"),
            "sha256": result.get("sha256"),
            "events_seen": len(events),
            "events_new": len(fresh),
            "new_events": fresh,
            # ADR-0029's invariant, asserted on every record rather than assumed.
            "effect": {
                "actions": ["invalidate_cached_capability"],
                "headroom_mutation_permitted": False,
            },
        }
        validate_change_record(record)
        observations.append(record)

        if result.get("status") == 200:
            state[source["url"]] = {
                "etag": result.get("etag"),
                "last_modified": result.get("last_modified"),
                "sha256": result.get("sha256"),
            }

    with LOG.open("a", encoding="utf-8", newline="\n") as fh:
        for record in observations:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    state["_seen_event_keys"] = sorted(seen)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")

    days = len(
        {
            json.loads(line)["ts"][:10]
            for line in LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    )
    ok = sum(1 for o in observations if o["http_status"] in (200, 304))
    print(f"[exp27] {stamp}")
    print(f"  sources reachable      {ok}/{len(SOURCES)}")
    print(f"  new events this run    {new_events}")
    print(f"  distinct days recorded {days} of 30")
    for o in observations:
        flag = o["error"] or (
            "304 unchanged" if o["unchanged_304"] else o["http_status"]
        )
        print(
            f"    {o['harness']:<12} {o['kind']:<12} {str(flag):<24} new={o['events_new']}"
        )
    return 0 if ok == len(SOURCES) else 1


if __name__ == "__main__":
    raise SystemExit(collect())
