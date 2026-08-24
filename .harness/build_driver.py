"""Dispatch plan units one at a time, in the build plan's recommended order.

Operational tooling, deliberately untracked: it drives `scripts/dispatch.py`, it is not
product code and carries no ADR. Run it under `scripts/run_loop.py`, which already solves
the process-tree kill and the pipe-blocking problems measured on this machine.

Each tick:
  * if a dispatcher is already live, do nothing — the lanes are serial by design
  * otherwise take the next unit not yet recorded done, write it a brief that points at
    its plan unit rather than restating it, and dispatch it with the claims the plan
    itself declares
  * a unit counts as done only when the suite is green AND a commit mentions its id;
    verify by artefact, never by exit code

State lives in .harness/driver-state.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNITS = ROOT / ".harness/plan-units.json"
STATE = ROOT / ".harness/driver-state.json"
BRIEFS = ROOT / ".harness/dispatch/briefs-driver"
TAIL = ROOT / ".harness/dispatch/briefs-2026-08-22/_tail.md"
LOG = ROOT / ".harness" / "log"
RUNS = ROOT / ".harness" / "dispatch"
PUBLISH_STOP = ROOT / ".harness" / "STOP-PUBLISH"

# The build plan's recommended order. Foundation first, then the task spine, then recall
# and delivery; ingress and self-improvement last because they unlock nothing upstream.
ORDER = [
    "F01",
    "F02",
    "F03",
    "L01",
    "C01",
    "O01",
    "T01",
    "T02",
    "T03",
    "T04",
    "C03",
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "D01",
    "D02",
    "D03",
    "D04",
    "C02",
    "C04",
    "L02",
    "L03",
    "L04",
    "L05",
    "L06",
    "S01",
    "S02",
    "S03",
    "S04",
    "S05",
    "S06",
    "H01",
    "H02",
    "H03",
]

# Arms carry their own wall-clock leash, because a failure costs whatever the leash allows.
#
# CURSOR MODELS ONLY on the Cursor arm. The principal's billing page, 23 Aug 2026 00:53:
# "Cursor Models — Includes Cursor Grok and Composer — 1% used"; "Other Models — 81% used";
# "Additional usage beyond limits consumes Other Models quota or on-demand spend."
# On-demand spending is Disabled and must stay disabled.
#
# `harness.py` maps kimi-k3-* and glm-5.2-* to the `cursor-models` pool, but Cursor's own UI
# names only Grok and Composer as included. Other Models rose from 58% to 81% across a day of
# heavy kimi-k3-max use, which is consistent with kimi billing to Other Models and the
# repository's mapping being wrong. Until that is settled, route ONLY to composer and
# cursor-grok: they are named on the billing page itself, so they are the verified-free ones.
#
# Codex: reset by the principal on 22 Aug; a live probe read 0.0% used, resetting 29 Aug.
# Grok: RESTORED to a full share on 23 Aug 2026 after F05 repaired the arm and a live smoke
# through the real dispatch path returned an artefact. The 19-in-29 timeout rate was never the
# model failing: xAI documents that Grok auto-imports Claude Code's marketplaces, plugins,
# skills, MCPs, agents and hooks, so every run spent two minutes launching that fleet before
# reading the brief. F05 uses native --prompt-file, a clean GROK_HOME per run, GROK_AUTH_PATH
# pointing back at the existing subscription credential, and disables Claude MCP compatibility.
# An earlier hand attempt failed because it isolated GROK_HOME *and* the auth together.
# SuperGrok Heavy was 17% used with 83% idle and a banked reset — the most wasted capacity here.
# Weighted to MEASURED headroom, read off the providers' own dashboards on 23 August 2026:
# Cursor Models (Composer and Cursor Grok) 2% used with 28 days to reset -- almost untouched;
# Grok Bot 4% weekly; SuperGrok Heavy 17%. Meanwhile Cursor's "Other Models" pool sat at 82%,
# and past that limit it spends on demand, which the principal has forbidden outright -- so
# every cursor arm here names a model that `cursor_pool_for_model` puts in `cursor-models`,
# and none may fall back to a default.
#
# The reason those pools stayed idle was NOT this table. Dispatches were crashing before they
# reached a harness (PermissionError on the trajectory, now repaired in `events.read`), so the
# rotation was correct and the work never started. Rebalancing without that fix would have
# changed nothing, which is why the fix came first.
# Claude was a registered harness the whole time -- `Harness(id="claude", family="anthropic",
# pool="claude-weekly")` -- and appeared nowhere in this table, so an entire subscription went
# unused while three pools carried every unit. It is added here for builds, and it matters more
# for REVIEWS: reviewer selection picks a different family from the builder, and with only
# openai/cursor/xai present the anthropic family could never be chosen at all. [measured 23 Aug 2026]
# CLAUDE IS WITHDRAWN FROM BUILDS, 23 August 2026. The principal: "We need to go easy on Claude work
# now we are nearing our 5 hour usage limit that resets in a couple of hours... Claude must be
# temporarily orchestration only." Its two slots are returned to codex and grok, which have the most
# measured headroom. Restore the two ("claude", None, 3600) entries after the reset — reviewer
# selection needs the anthropic family to exist, or a cross-family review of cursor or codex work
# has one fewer family to draw from.
ARMS = [
    # The principal's routing, 24 August 2026: Cursor Grok 4.6 High Fast, Composer 2.5,
    # Codex and SuperGrok Heavy, all of which have quota to spare. Claude is deliberately
    # absent -- it is orchestrating, not building.
    ("cursor-composer", "cursor-grok-4.6-high-fast", 3600),
    ("codex", None, 3600),
    ("cursor-composer", "composer-2.5-fast", 3600),
    ("grok", None, 3600),
    ("cursor-composer", "cursor-grok-4.6-high-fast", 3600),
    ("codex", None, 3600),
    ("cursor-composer", "composer-2.5", 3600),
    ("grok", None, 3600),
    ("cursor-composer", "cursor-grok-4.6-medium-fast", 3600),
    ("codex", None, 3600),
    ("cursor-composer", "cursor-grok-4.6-high-fast", 3600),
    ("codex", None, 3600),
]


# cursor-agent serialises on an exclusive file lock in scripts/dispatch.py, so more than one
# concurrent cursor dispatch does not run in parallel — it waits out the leash and fails.
# MEASURED 24 Aug 2026. scripts/dispatch.py defaults to --max-turns 20 and the driver never
# overrode it, so every grok dispatch died mid-orientation with "Error: max turns reached"
# and exit 1 -- seven for seven, artefacts of 509B-2.3KB, nothing written. T01 alone gates 22
# units and burned three attempts that way. Reproduced directly: the same prompt exits 0 under
# a sufficient cap and 1 under a short one. Only grok and claude expose the flag; codex and
# cursor ignore it, which is why the failure looked provider-specific. The LEASH bounds cost
# here, not the turn count, so the cap should be generous enough never to be the binding limit.
DEFAULT_TURNS = 150

CURSOR_CONCURRENCY = (
    6  # startup-scoped lock since 24 Aug; runs overlap after ~20s settle
)


def pick_arm(index: int, state: dict) -> tuple:
    """Choose an arm, refusing to oversubscribe one that serialises.

    `scripts/dispatch.py` takes an EXCLUSIVE FILE LOCK around every cursor-composer run
    (`DEFAULT_CURSOR_LOCK`), so exactly one can execute at a time. Dispatching several
    simultaneously does not parallelise them — the extras block on the lock for the whole leash and
    then fail with "cursor-agent lock held: could not acquire ... within 3600.0s". Measured on
    24 August 2026: B04, L03 and Q02 each burned a full hour that way while one cursor run worked,
    which is most of the Cursor capacity spent on waiting. [measured]

    So a second concurrent cursor slot is skipped rather than queued, and the rotation moves on to a
    harness that can actually start. This is the F-08 lesson in a new place: capacity that cannot be
    used is not capacity, and a scheduler that treats a serialised arm as parallel reports itself
    busy while nothing happens.
    """
    inflight = state.get("in_flight", {})
    arms_by_unit = state.get("last_arm", {})
    # Every cursor dispatch contends for the same startup lock, not just the builds. Reviews go
    # out through their own path and resolvers through this one, and neither appears in
    # `in_flight` -- so counting only in-flight builds let cursor be oversubscribed by however
    # many reviews and resolvers happened to be live, and the extras then queued on the lock.
    # Found 24 August 2026 by a test from an orphaned worktree (AI2) whose implementation was
    # seven hours stale but whose invariant was right.
    cursor_units = (
        set(inflight)
        | set(state.get("review_dispatched") or [])
        | set(state.get("resolve_dispatched") or [])
    )
    cursor_live = sum(
        1 for uid in cursor_units if arms_by_unit.get(uid) == "cursor-composer"
    )
    for offset in range(len(ARMS)):
        harness, model, leash = ARMS[(index + offset) % len(ARMS)]
        if harness == "cursor-composer" and cursor_live >= CURSOR_CONCURRENCY:
            continue
        return harness, model, leash
    # Every arm is a saturated cursor slot. Return the nominal one and let dispatch refuse loudly
    # rather than inventing a harness that was not configured.
    return ARMS[index % len(ARMS)]


def sh(args, **kw):
    return subprocess.run(
        args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kw,
    )


def save_state(state: dict) -> None:
    """Write driver state atomically. Never truncate the only record of what is in flight.

    MEASURED 24 August 2026. This was three bare `STATE.write_text(json.dumps(...))` calls --
    truncate, then write, with no temp file, no fsync and no lock -- while `load()` swallowed
    every exception and returned `{"done": [], "attempts": {}}`. A power cut or a kill during
    that window therefore leaves a torn file that reads as NOTHING DONE AND NOTHING IN FLIGHT,
    and the next tick re-dispatches every unit at attempt zero against live claims held by
    still-running agents. The file is the only record of what is running; it was the least
    durable thing in the repository.

    Temp-and-rename makes the swap atomic: a reader sees the old file or the new one, never a
    half. fsync before rename means the content is on disk before the name points at it.
    """
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".json.tmp")
    payload = json.dumps(state, indent=1)
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, STATE)


def load(path, default):
    """Read JSON state. A CORRUPT file is fatal; a missing one is the default.

    Returning the default on a parse error is what made a torn write catastrophic rather than
    merely annoying: an unreadable driver-state read as "nothing done, nothing in flight" and
    the next tick re-dispatched everything. Absence and corruption are different facts and only
    one of them is safe to paper over.
    """
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"driver: {path} is unreadable ({exc}). Refusing to continue: treating this as an "
            f"empty state would re-dispatch every unit against live claims. Inspect it, or move "
            f"it aside deliberately if you accept losing the record of what is running."
        ) from exc


def live_dispatchers() -> int:
    r = sh(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -match 'dispatch.py' }).Count",
        ]
    )
    try:
        return int(r.stdout.strip() or 0)
    except ValueError:
        return 0


def suite_green() -> bool:
    """True only when pytest printed a summary and that summary shows no failures.

    This previously passed `--timeout=600`, which pytest-timeout is not installed to
    support. pytest exited with a usage error, stdout carried no summary line, and the
    function returned False for every unit — so NOTHING could ever be recorded done. The
    build loop ran 66 ticks retiring nothing while F02 and F05 sat committed in the log.
    [measured 23 Aug 2026]

    Judge on the summary line pytest actually prints, and fail closed when there is none:
    an absent summary means the run did not complete, which is not the same as passing.
    """
    r = sh([sys.executable, "-m", "pytest", "tests/", "-q"])
    text = (r.stdout or "") + (r.stderr or "")
    summary = [
        ln
        for ln in text.splitlines()
        if " passed" in ln or " failed" in ln or " error" in ln
    ]
    if not summary:
        return False
    last = summary[-1]
    return "passed" in last and "failed" not in last and "error" not in last


def committed(uid: str, unit: dict) -> bool:
    """Has this unit landed?

    Match the commit message the PLAN specifies, not the unit id. The ids do not appear in
    commit subjects — F01's is `feat(events): make ordinary append durable and
    process-serialised` — so an id search reports a finished unit as unfinished. That defect
    dispatched F01 three times on 22 Aug 2026 and then recorded it skipped while its commit
    was already in the log. Verify by the artefact the plan actually asks for.
    """
    want = (unit.get("commit") or "").strip().lower()
    if not want:
        return False
    # Prefix, not equality. A subject legitimately carries context the plan did not specify —
    # S01 landed as "...safety floors (S01, merged by hand)" and an exact match reported the
    # unit unbuilt while its code was in the tree. Still tight: these subjects are long and
    # specific, which is why matching the unit id was too loose and this is not.
    r = sh(["git", "log", "--oneline", "-200", "--format=%s"])
    return any(
        line.strip().lower().startswith(want) for line in (r.stdout or "").splitlines()
    )


def artefact_identity(unit: dict[str, Any]) -> str | None:
    """Hash the current committed blobs the review is permitted to judge."""
    claims = unit.get("claims")
    if not isinstance(claims, list) or not all(
        isinstance(path, str) for path in claims
    ):
        return None
    blobs = []
    for path in sorted(claims):
        result = sh(["git", "rev-parse", "HEAD:" + path])
        blob = result.stdout.strip()
        if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", blob):
            return None
        blobs.append((path, blob))
    return hashlib.sha256(
        json.dumps(blobs, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def append_review_outcome(outcome: dict[str, Any]) -> None:
    """Record consumed critic evidence through the one trajectory writer."""
    sys.path.insert(0, str(ROOT / "src"))
    from datetime import datetime, timezone

    from consilient import events  # type: ignore[import-untyped]

    now = datetime.now(timezone.utc)
    events.append(
        LOG / (now.date().isoformat() + ".jsonl"),
        {
            "v": 1,
            "ts": now.isoformat(),
            "event": "review.outcome",
            "actor": "build_driver",
            "data": outcome,
        },
    )


def retired_units(state: dict[str, Any], units: dict[str, dict[str, Any]]) -> set[str]:
    """Only a current, consumed SOUND review may retire a unit."""
    retired: set[str] = set()
    results = state.get("review_results", {})
    if not isinstance(results, dict):
        return retired
    for uid, result in results.items():
        if uid not in units or not isinstance(result, dict):
            continue
        if result.get("outcome") != "SOUND":
            continue
        artefact = artefact_identity(units[uid])
        if artefact is not None and result.get("artefact") == artefact:
            retired.add(uid)
    return retired


def _verdict_candidates(outer: dict[str, Any]) -> list[str]:
    """Every JSON object in the reviewer's output that might be the verdict, newest last.

    MEASURED 24 August 2026. The parser required `stdout_tail` to BE the verdict JSON. It is
    not: it is the LAST 2000 CHARACTERS of the reviewer's stdout, and a reviewer writes prose
    around its verdict. All 44 verdicts consumed that day came back `check_error`, so nothing
    could retire -- reviews dispatched, billed, and discarded at a later stage than before.

    The envelope carries `stdout_path`, the whole output on disk, so the verdict is looked for
    across all of it rather than in whatever happened to fall inside a 2000-character window.
    This changes only where the candidate is FOUND. Every field is still validated afterwards
    exactly as before -- v, unit, artefact, attempt, verdict, findings -- so a wrong verdict
    cannot be admitted by looking in more places for it.
    """
    seen: list[str] = []
    blobs: list[str] = []
    path = outer.get("stdout_path")
    if isinstance(path, str) and path:
        try:
            blobs.append(
                pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
            )
        except OSError:
            pass
    tail = outer.get("stdout_tail")
    if isinstance(tail, str) and tail:
        blobs.append(tail)
    for blob in blobs:
        # Objects that name a verdict at all. Non-greedy and brace-balanced only to one level,
        # which is enough: the receipt is flat by specification.
        for match in re.finditer(r"\{[^{}]*\"verdict\"[^{}]*\}", blob, re.S):
            text = match.group(0)
            if text not in seen:
                seen.append(text)
    return seen


def consume_review_verdict(
    state: dict[str, Any], uid: str, unit: dict[str, Any]
) -> str:
    """Consume one strict reviewer receipt; anything else is a retryable check error."""
    expected = state.setdefault("review_expected", {}).get(uid)
    if not isinstance(expected, dict):
        expected = {}
    attempt = expected.get("attempt")
    artefact = expected.get("artefact")
    consumed = state.setdefault("review_consumed", {}).get(uid)
    if consumed == expected and expected:
        return "consumed"

    outcome = "check_error"
    findings: list[str] = []
    try:
        outer = json.loads((BRIEFS / f"{uid}-verify.out").read_text(encoding="utf-8"))
        if not isinstance(outer, dict) or outer.get("status") != "ok":
            raise ValueError("outer dispatch did not succeed")
        inner = None
        for candidate in _verdict_candidates(outer):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and parsed.get("unit") == uid:
                inner = parsed
        if inner is None:
            raise ValueError("no verdict object found in the reviewer's output")
        if (
            not isinstance(inner, dict)
            or set(inner) != {"v", "unit", "artefact", "attempt", "verdict", "findings"}
            or inner.get("v") != 1
            or inner.get("unit") != uid
            or inner.get("artefact") != artefact
            or inner.get("attempt") != attempt
            or artefact_identity(unit) != artefact
            or inner.get("verdict") not in {"SOUND", "DEFECTIVE"}
            or not isinstance(inner.get("findings"), list)
            or not all(
                isinstance(finding, str) and finding.strip()
                for finding in inner["findings"]
            )
            or (inner["verdict"] == "SOUND" and inner["findings"])
            or (inner["verdict"] == "DEFECTIVE" and not inner["findings"])
            or not isinstance(attempt, int)
        ):
            raise ValueError("invalid review verdict")
        outcome = inner["verdict"]
        findings = inner["findings"]
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        pass

    record = {
        "unit": uid,
        "artefact": artefact,
        "attempt": attempt,
        "outcome": outcome,
        "findings": findings,
    }
    append_review_outcome(record)
    state["review_consumed"][uid] = expected
    state.setdefault("review_results", {})[uid] = record
    dispatched = state.setdefault("review_dispatched", [])
    if uid in dispatched:
        dispatched.remove(uid)
    if outcome == "SOUND":
        state.setdefault("done", [])
        if uid not in state["done"]:
            state["done"].append(uid)
        state.setdefault("verified", [])
        if uid not in state["verified"]:
            state["verified"].append(uid)
        if uid in state.setdefault("built", []):
            state["built"].remove(uid)
        state.setdefault("repair_findings", {}).pop(uid, None)
        state.setdefault("rejected_artefacts", {}).pop(uid, None)
    elif outcome == "DEFECTIVE":
        for key in ("done", "verified", "built"):
            if uid in state.setdefault(key, []):
                state[key].remove(uid)
        state.setdefault("repair_findings", {})[uid] = findings
        state.setdefault("rejected_artefacts", {})[uid] = artefact
    return outcome


FAMILY = {
    "codex": "openai",
    "cursor-composer": "cursor",
    "grok": "xai",
    "claude": "anthropic",
}


WORKTREES = ROOT / ".harness/unit-worktrees"


def unit_worktree(uid: str) -> pathlib.Path | None:
    """Give a unit its own tree, so parallel units cannot collide on one index.

    The shared index is what forced units to be serialised on claim overlap: `git add` is
    global, so two agents staging at once capture each other's files. A worktree per unit
    removes the shared state rather than coordinating around it — the cheapest fix to a
    coordination problem is usually to delete the sharing.
    """
    WORKTREES.mkdir(parents=True, exist_ok=True)
    path = WORKTREES / uid
    if path.exists():
        return path
    r = sh(["git", "worktree", "add", "--detach", str(path), "HEAD"])
    return path if r.returncode == 0 else None


def rebase_worktree(uid: str, path: pathlib.Path) -> bool:
    """Replay a finished unit's commits onto current HEAD, inside its OWN worktree.

    Worktree isolation removes contention over the git *index*; it does nothing about two
    units editing the same file. The collision simply moves to merge time, where it is more
    expensive because both units have already done their work. 667 unit pairs share a claimed
    file with no ordering between them — 442 of them on `events.py` — so this is the common
    case, not the exception. [measured 23 Aug 2026]

    Rebasing in the unit's own tree puts the conflict where the code that caused it lives, and
    leaves the unit's commits replayed on the tree they will actually land on. Only ever call
    this on a unit whose dispatcher has exited: rebasing under a live worker rewrites the
    branch beneath it.
    """
    head = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    if not head:
        return False
    if sh(["git", "-C", str(path), "rebase", head]).returncode == 0:
        return True
    sh(["git", "-C", str(path), "rebase", "--abort"])
    return False


# How long a dispatch may write nothing before its slot is treated as unused. Generous, because a
# unit legitimately spends time reading before it writes; the measured idle cases sat at 43 minutes
# with zero bytes produced.
PROGRESS_SILENCE_S = 1800
CRLF = bytes((13, 10))
NL = bytes((10,))


def run_dir_progress(uid: str, started: float) -> float:
    """Newest streaming artefact for `uid`'s live run, as an mtime. 0.0 if none found.

    MEASURED 24 August 2026, and it cost the most expensive unit in the plan. Reclamation
    judged silence from `briefs-driver/<UID>.out`, but `scripts/dispatch.py` writes that file
    ONCE, AT COMPLETION -- so a healthy run and a dead one are byte-identical for the whole of
    a run's life, and any unit taking longer than PROGRESS_SILENCE_S was declared silent while
    working. The slot was freed, the unit re-dispatched, and the new dispatch then refused
    against the claim still held by its own earlier run. T01 -- which gates 22 units -- was
    reclaimed and cannibalised exactly that way, and the run it collided with went on to write
    over a megabyte of output afterwards.

    The streaming artefacts are `stdout.txt` and `stderr.txt` inside the run directory; some
    harnesses write progress only to stderr, so both count. Runs are matched to units by exact
    brief content, because the driver does not learn the run id until the run ends -- which is
    the same reason the old check reached for the wrong file.
    """
    try:
        # Newlines are normalised before comparing: the driver writes its briefs CRLF on this
        # machine and dispatch.py composes the run brief LF, so a raw comparison never matches.
        # That is the same CRLF trap that made the generated-documents gate pass locally and
        # fail on a clean checkout.
        want = (BRIEFS / (uid + ".md")).read_bytes().replace(CRLF, NL)[:400]
    except OSError:
        return 0.0
    if not want:
        return 0.0
    newest = 0.0
    try:
        candidates = list(RUNS.iterdir())
    except OSError:
        return 0.0
    for d in candidates:
        if not d.is_dir() or d.name == "briefs-driver":
            continue
        try:
            brief = d / "brief.md"
            if brief.stat().st_mtime < started - 120:
                continue
            if want not in brief.read_bytes().replace(CRLF, NL):
                continue
        except OSError:
            continue
        for name in ("stdout.txt", "stderr.txt"):
            try:
                f = d / name
                if f.exists():
                    newest = max(newest, f.stat().st_mtime)
            except OSError:
                pass
    return newest


def downstream_count(uid: str, units: dict) -> int:
    """How many units are transitively waiting on `uid`.

    MEASURED 24 August 2026. Startable units were ordered by phase letter and then
    ALPHABETICALLY, so with a bounded number of slots the driver spent them on whatever sorted
    first rather than on whatever released the most work. P02 gates 13 units and A04 another 12
    behind it; both sort after a dozen leaf units whose completion frees nothing. T01 sat unbuilt
    for a day while holding 22 units, for the same reason among others.

    Ordering by transitive dependents is the standard critical-path heuristic and it costs one
    graph walk per tick. It is a heuristic, not an optimum -- unit durations are unknown, so this
    cannot be a true critical path -- but "release the most work first" beats "release whatever
    is alphabetically first" without needing to estimate anything.
    """
    children: dict[str, set[str]] = {}
    for node, spec in units.items():
        for dep in spec.get("deps", []):
            children.setdefault(dep, set()).add(node)
    seen: set[str] = set()
    stack = list(children.get(uid, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(children.get(node, ()))
    return len(seen)


def _content_landed(sha: str) -> bool:
    """Are this commit's added lines already present in HEAD, line for line?

    Identity of WORK, not of commit message. A subject is not identity: 14 subjects recur in
    this repository's history and one recurs 24 times [measured 24 August 2026]. A patch-id is
    not identity either -- `git patch-id` normalises whitespace, and in Python whitespace is the
    language, so moving a statement into a loop preserves the patch-id while changing the
    meaning.

    Deliberately asymmetric: it asks only whether what the commit ADDS is present, not whether
    HEAD matches the commit. A unit whose work landed and was then built upon should still
    retire. The thresholds are the discriminator -- below twenty added lines a diff is too small
    to tell "landed" from "coincidentally similar", so it stays escalated rather than guessing.
    """
    show = sh(["git", "show", "--format=", "-U0", sha])
    if show.returncode != 0:
        return False
    added: dict[str, list[str]] = {}
    path = None
    for line in show.stdout.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:].strip()
        elif line.startswith("+") and not line.startswith("+++") and path:
            body = line[1:].strip()
            if body:
                added.setdefault(path, []).append(body)
    total = sum(len(v) for v in added.values())
    if total < 20:
        return False
    absent = 0
    for file_path, lines in added.items():
        head = sh(["git", "show", f"HEAD:{file_path}"])
        blob = head.stdout if head.returncode == 0 else ""
        present = {ln.strip() for ln in blob.splitlines()}
        absent += sum(1 for ln in lines if ln not in present)
    return (total - absent) / total >= 0.99


def reclaim_expired_slots(state: dict) -> list[str]:
    """Free slots whose leash has run out, before anything can return early.

    The scheduler held twelve units in flight while three dispatcher processes were alive; nine
    leashes had been expired for forty minutes. Reclamation existed, and it sat behind two early
    returns, so on any tick that took one of those paths the ghosts survived and the queue starved
    against capacity that was not being used. [measured 23 Aug 2026]

    This is the idle case rather than the crash case (F-13): nothing failed, nothing raised, and
    the only artefact was an absence. **An expired leash is not evidence about the work**, so the
    attempt is refunded — F-05 — and the unit becomes a candidate again rather than burning toward
    its retry cap for having been forgotten.
    """
    import time as _t

    inflight = state.setdefault("in_flight", {})
    now = _t.time()
    freed = []
    for uid in list(inflight):
        started, leash = inflight[uid]

        # Two ways a slot stops being work. The leash running out is the obvious one.
        expired = now - started > leash

        # The other is silence. A dispatch that has written nothing for half an hour has either
        # exited without saying so or is hung, and in both cases the slot is capacity the queue
        # cannot use. Measured 23 August 2026: nineteen units held slots while seven processes were
        # alive, and eight of them had produced no output for forty-three minutes — every one still
        # inside its leash and therefore invisible to the check above.
        #
        # Progress is read from the artefact, never from a process table, because a process check
        # has reported healthy over dead work three times in this repository. Freeing the slot does
        # not kill anything: a unit whose worktree already holds commits is excluded from dispatch
        # by the built-unmerged check, so a slow-but-working unit is not restarted, only unblocked.
        stale = False
        newest = 0.0
        for stem in (uid, uid + "-resolve", uid + "-verify"):
            out = BRIEFS / (stem + ".out")
            try:
                if out.exists():
                    newest = max(newest, out.stat().st_mtime)
            except OSError:
                pass
        # The completion artefact above tells us nothing while a run is in progress, so the
        # streaming ones decide. Without this the driver reclaims its own healthy work.
        newest = max(newest, run_dir_progress(uid, started))
        if newest and now - newest > PROGRESS_SILENCE_S:
            stale = True

        if expired or stale:
            inflight.pop(uid, None)
            attempts = state.setdefault("attempts", {})
            attempts[uid] = max(0, attempts.get(uid, 1) - 1)
            freed.append(uid + ("" if expired else " (silent)"))
    return sorted(freed)


def publish_if_ready(state: dict, green: bool | None) -> str:
    """Push to the public remote when the tree is green and every publication gate passes.

    The principal, 23 August 2026: "we need to publish ready work and do this continuously via the
    agent that adversarially verifies and signs off." Public had sat 20 hours and 75 commits behind
    because publishing was something a person had to remember, and a release that depends on
    somebody remembering is not a release process.

    Three conditions, every one an artefact rather than a judgement: the suite is green, every
    publication gate exits zero, and there is something to push. The pre-push hook runs the leak
    gates again independently — this pre-flight does not replace it and must not, because a
    publishing path that trusts its own checks is one bug away from an irreversible disclosure.
    Publishing is the only thing this driver does that cannot be undone, so it is the one place
    two independent checks are worth the duplication.
    """
    if PUBLISH_STOP.exists():
        return "publish held: STOP-PUBLISH is present"

    ahead = sh(["git", "rev-list", "--count", "public/main..HEAD"]).stdout.strip()
    if not ahead or ahead == "0":
        return ""
    # Reuse the tick's existing suite result. Running it again here doubled the tick to past ten
    # minutes and starved the scheduler of the thing it exists to do. `green` is None when the tick
    # never needed to compute it, in which case there is nothing newly retired and nothing new to
    # publish either, so holding is correct rather than merely cheap.
    if green is None:
        return f"publish held: {ahead} commit(s) ready, suite not evaluated this tick"
    if not green:
        return f"publish held: {ahead} commit(s) ready, suite not green"
    gates = [
        (".github/scripts/check_foreign_identifiers.py", []),
        (".github/scripts/check_secrets.py", []),
        (".github/scripts/check_private_corpus.py", []),
        (".github/scripts/check_generated_documents.py", ["--check"]),
    ]
    for script, args in gates:
        path = ROOT / script
        if not path.is_file():
            return f"publish held: {script} is missing"
        if sh([sys.executable, str(path), *args]).returncode != 0:
            return f"publish REFUSED: {pathlib.Path(script).name} failed"
    result = sh(["git", "push", "public", "HEAD:main"])
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip().splitlines()
        return f"publish FAILED: {tail[-1] if tail else 'unknown'}"
    state["last_published_count"] = ahead
    return f"published {ahead} commit(s) to public"


def start_failed_dispatches() -> list[dict[str, object]]:
    """BU-0 / N00: open claims with no child artefact inside the start window.

    Reads the trajectory and run directories only — never a process table. stderr
    tracebacks catch crashes that raised; this catches dispatches that died quiet,
    which is the failure measured on 23 August 2026 when six of six failed at startup
    and the loop kept reporting itself busy. [measured, F-13]
    """
    completed = sh(
        [
            sys.executable,
            "scripts/dispatch.py",
            "--supervise",
            "--log",
            str(LOG),
            "--runs",
            str(RUNS),
            "--json",
        ]
    )
    if completed.returncode == 0:
        return []
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return []
    rows = payload.get("start_failed")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def crashed_dispatches(state: dict) -> list[tuple[str, str, bool]]:
    """Dispatches that died, found by ARTEFACT rather than by asking whether a process exists.

    Every silent failure this driver has produced was a process that started, died, and left the
    scheduler reporting success. On 23 August 2026 six of six failed dispatches ended in an
    unhandled exception seconds after "dispatched" was printed, and one of them was the only run
    ever sent to a whole provider -- so that provider sat at 17% usage for two days while this loop
    called it busy. The principal found it, three times, by looking at a usage graph. [measured]

    The artefact is the dispatcher's own stderr. A non-empty stderr carrying a traceback means the
    run is dead, whatever any process table says. Returns (unit, last line, refused?) where a
    refusal is a claim collision rather than a crash and must not consume a retry either.
    """
    dead: list[tuple[str, str, bool]] = []
    # Reviews are tracked separately from in_flight and crash just as readily: A02, C01 and F05
    # all died the same way and nothing noticed, because a review that never happens leaves no
    # gap anyone can see. A unit sits "awaiting review" forever and reads as progress.
    watched = set(state.get("in_flight", {}))
    watched.update(state.get("review_dispatched", []))
    for uid in sorted(watched):
        for stem in (uid, uid + "-resolve", uid + "-verify"):
            err = BRIEFS / (stem + ".err")
            out = BRIEFS / (stem + ".out")
            try:
                if not err.exists() or err.stat().st_size == 0:
                    continue
                text = err.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "Traceback" not in text and "Error" not in text:
                continue
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            refused = False
            try:
                if out.exists() and out.stat().st_size:
                    refused = out.read_text(
                        encoding="utf-8", errors="replace"
                    ).startswith("status: refused")
            except OSError:
                pass
            dead.append((uid, lines[-1] if lines else "unknown failure", refused))
            break
    return dead


def release_dead_claims(uids: set[str]) -> int:
    """Close the trajectory claims held by runs that are gone.

    A crashed dispatch never closes its claim, so the unit it held stays unclaimable for the whole
    lease -- an hour, with nothing running. Measured on 23 August 2026: two units were blocked this
    way and every re-dispatch was refused against a process that no longer existed.
    """
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from datetime import datetime, timezone

        from consilient import coordination, events as events_mod
    except Exception:
        return 0
    log = ROOT / ".harness" / "log"
    try:
        evs, _ = events_mod.read_all(log)
        live = coordination.live_claims(evs, now=datetime.now(timezone.utc))
    except Exception:
        return 0
    closed = 0
    for claim in live:
        paths = getattr(claim, "paths", None) or getattr(claim, "claims", ())
        blob = " ".join(str(x).lower() for x in paths)
        if any(("unit-worktrees/" + u.lower()) in blob for u in uids):
            try:
                coordination.close_claim(log, run_id=claim.run_id)
                closed += 1
            except Exception:
                pass
    return closed


def merge_unit_worktree(uid: str, quiescent: bool = False) -> str:
    """Take only the commits the unit itself made, never its whole tree state.

    `git merge <worktree-head>` was wrong: a worktree branched from an older HEAD carries the
    ABSENCE of every commit landed since, so merging its state reverts other units' work and
    conflicts on files the unit never touched. L01 and L03 both conflicted on `events.py` and
    `effects.py` this way, having edited neither. [measured 23 Aug 2026]

    Cherry-pick the unit's own commits — those reachable from its head but not from ours.
    """
    path = WORKTREES / uid
    if not path.exists():
        return "no worktree"
    head = sh(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
    if not head:
        return "no commits"
    own = [
        ln.strip()
        for ln in sh(
            ["git", "rev-list", "--reverse", f"HEAD..{head}"]
        ).stdout.splitlines()
        if ln.strip()
    ]
    if not own:
        return "no commits"
    # Defer if any path this unit touches is dirty in the main tree. Research streams still
    # write here directly — only build units are isolated — so a cherry-pick can collide with
    # an agent mid-write. Deferring costs one tick; forcing would discard live work. The
    # unit's commits are safe in its own worktree until the path is quiet.
    touched = set()
    for sha in own:
        for ln in sh(
            ["git", "show", "--name-only", "--format=", sha]
        ).stdout.splitlines():
            if ln.strip():
                touched.add(ln.strip())
    # Content, not `git status`. On Windows a checked-out file whose line endings differ from the
    # index reports as modified while carrying NO content change, and a merge deferred on that
    # never becomes undeferred — the file will read dirty forever. `projection.py` was
    # byte-identical to HEAD ignoring line endings, untouched for 42 minutes, and had blocked two
    # finished units (V01, D01) from merging indefinitely. That is F-02 again with a new cause, so
    # the check now asks git for paths with real content deltas. [measured 23 Aug 2026]
    dirty = {
        ln.split("	")[-1].strip()
        for ln in sh(["git", "diff", "--numstat", "HEAD"]).stdout.splitlines()
        if ln.strip()
    }
    clash = touched & dirty
    if clash:
        return f"deferred {uid}: {len(clash)} path(s) dirty in the main tree ({sorted(clash)[0]})"

    applied = 0
    already = 0
    for sha in own:
        r = sh(["git", "cherry-pick", "--allow-empty", "-x", sha])
        if r.returncode != 0:
            # ALREADY APPLIED is not a conflict. A unit's work often lands under a different sha —
            # cherry-picked with -x, rebased, or resolved by hand — and `HEAD..worktree_head` still
            # lists the original. Git says so plainly ("The previous cherry-pick is now empty"), and
            # treating that as a conflict parks finished work behind a resolver that has nothing to
            # resolve. X04 sat blocked this way while its files were already in HEAD as 6110f4b.
            # [measured 23 Aug 2026]
            # Match git's own sentence, not a keyword. Its already-applied message reads "The
            # previous cherry-pick is now empty, possibly due to conflict resolution" -- so a naive
            # test for "conflict" absent from the text marks the success case as a failure, which is
            # what the first version of this check did.
            blurb = ((r.stdout or "") + (r.stderr or "")).lower()
            if "is now empty" in blurb or "nothing to commit" in blurb:
                sh(["git", "cherry-pick", "--skip"])
                already += 1
                continue
            sh(["git", "cherry-pick", "--abort"])
            # Silently returning a string here is how S01 sat unmerged: the driver printed
            # the line and forgot it, and the queue behind it read as "idle" (F-01/F-02).
            # A conflict is now either repaired in the unit's own tree or escalated by name.
            if quiescent and rebase_worktree(uid, path):
                return merge_unit_worktree(uid, quiescent=False)
            return f"CONFLICT cherry-picking {sha[:9]} for {uid} ({applied} applied); needs resolution"
        applied += 1
    # Distinguish landed from already-there. "applied 1" over a commit that was merely
    # already present reads as progress that did not happen, which is the ambiguity this
    # repository exists to refuse.
    if applied and already:
        return f"applied {applied} and skipped {already} already-present commit(s) from {uid}"
    if already:
        return f"{uid} was already in the tree ({already} commit(s) already present)"
    return f"applied {applied} commit(s) from {uid}"


def write_verify_brief(
    uid: str, unit: dict, artefact: str, attempt: int
) -> pathlib.Path:
    """Adversarial review of a landed unit, by a different model family than built it.

    A unit whose own tests pass has marked its own homework. `CONSILIENCE.md`: agreement
    between agents that share evidence is echo, not consilience. The reviewer's different
    class is that it runs the artefact and checks it against the plan and the incumbent,
    rather than re-reading the diff that produced it.
    """
    BRIEFS.mkdir(parents=True, exist_ok=True)
    path = BRIEFS / f"{uid}-verify.md"
    claims = "\n".join(f"- `{c}`" for c in unit["claims"])
    # A unit's specification does not always live in docs/superpowers/plans/. The design work
    # of 23 August 2026 specified units inside docs/20-design/ documents, and a brief
    # pointing at a path that does not exist sends the agent hunting instead of building.
    # A plan value containing a slash is taken as a path from the repository root.
    plan_ref = (
        unit["plan"]
        if "/" in unit["plan"]
        else "docs/superpowers/plans/" + unit["plan"]
    )
    path.write_text(
        f"""# Adversarially verify {uid}. Find where it fails the plan or the bar.

## What landed

`{plan_ref}`, unit **{uid} — {unit["title"]}**, committed as
`{unit["commit"]}`. **Read the plan unit first, then the commit.**

**You did not build this and you are not from the family that did.** Your job is to find where it is
wrong, not to confirm it. A reviewer who reads the same diff the author read adds nothing — **your
different class of evidence is that you RUN it.**

## Check these, in order of what would hurt most

1. **Does it do what the unit's Deliverable says** — not approximately, exactly? Quote the Deliverable
   line and say whether it holds.
2. **Does its Done criterion actually hold?** Run the unit's own given test command and report the
   literal output. **If the criterion is untestable as written, that is a finding.**
3. **Are the tests real?** A test that cannot fail is worse than no test. **Break the implementation
   deliberately and confirm the test catches it.** Report what you broke and what happened. If a test
   passes with the implementation gutted, say so — that is the most valuable finding available here.
4. **Working principle 9:** did it name the incumbent and beat it, or quietly build the obvious thing?
   If it did not name a bar, name one yourself and say how this compares.
5. **Did it check prior art?** Search `docs/20-design/`, `docs/40-spec/v0-draft.md` and the findings
   for a document bearing on this unit. **If one exists and the unit ignored or contradicted it,
   that is a high-severity finding** — this repository has already paid twice for the same answer
   more than once.
6. **Did it stay in scope?** Claimed paths were: 
{claims}
   Anything touched outside that list is a finding.
7. **Did it weaken anything to pass?** A relaxed assertion, a widened allowlist, a lowered ratchet, a
   deleted case. **This is the one to hunt hardest.**

## Rules

- **Report only. Change nothing** except by appending to your own report file.
- **A finding is a failing check or a reproduction, never an opinion.** If you cannot express a concern
  as something that fails, say so and do not file it as a defect.
- **If the unit is good, say so plainly and stop.** A review that manufactures findings to look
  thorough is worse than one that finds nothing, and this project has recorded the cost of both.
- Baseline **914 passed, 1 skipped**. Report the exact line.

## Report

For each of the six checks: pass, or the finding with its reproduction. **What you broke to test the
tests, and whether they caught it.** The incumbent and how this compares.

## Required machine receipt

Your final output must be this exact JSON object and nothing else. `findings` is empty for SOUND and
contains one or more non-empty strings for DEFECTIVE. The immutable artefact identity and attempt
number are fixed below; a mismatch is refused and retried.

```json
{{"v":1,"unit":"{uid}","artefact":"{artefact}","attempt":{attempt},"verdict":"SOUND|DEFECTIVE","findings":[]}}
```
""",
        encoding="utf-8",
    )
    return path


def write_resolve_brief(uid: str, unit: dict, why: str) -> pathlib.Path:
    """Ask the unit's own worktree to rebase itself onto current head and resolve.

    A conflict is not a build failure and must not be re-dispatched as one: the code is written
    and tested, it simply no longer applies to a tree that moved underneath it. Resolution belongs
    with the agent that holds the context, in the tree that holds the code -- not with whoever
    happens to read the tick output. S01 needed a hand-merge that silently dropped a dataclass
    decorator; V01's conflict changed a function signature on both sides, which is worse.
    [measured 23 Aug 2026, F-11]
    """
    BRIEFS.mkdir(parents=True, exist_ok=True)
    path = BRIEFS / f"{uid}-resolve.md"
    claims = chr(10).join(f"- `{c}`" for c in unit["claims"])
    path.write_text(
        f"""# Rebase {uid} onto current main and resolve the conflict. Do not rebuild it.

**Your work is already written and it already passed.** It no longer applies cleanly because main
moved while you were working. {why}

You are in **your own worktree**, on your own branch. Main's head is in the same repository.

## Do this

1. `git -C . fetch` is not needed -- main is local. Find its head: `git rev-parse main` (or
   `git rev-parse HEAD` in the parent checkout if `main` does not resolve).
2. **Rebase your branch onto that head.** Your commits replay one at a time onto the current tree.
3. Resolve each conflict **as a semantic merge, never a textual one**. Both sides usually added
   something real and both usually need to survive. Two specific traps, both measured here today:
   - **A shared decorator.** If your class and main's class sat under one `@dataclass(frozen=True)`
     line, concatenating them leaves the second class undecorated. It still parses. It is broken.
   - **A changed signature.** If both sides altered the same function's parameters, the merged
     function must accept BOTH sets and every caller must be updated. Do not pick a side.
4. **Run `mypy --strict` on every file you touched.** This is not optional -- it caught the
   decorator bug in under a second when a full AST parse said the merge was fine.
5. Run the unit's own tests, then the full suite: `python -m pytest tests/ -q`.
6. Commit on your branch with the message the plan specifies: `{unit["commit"]}`

## What you claim
{claims}

## The bar
The merge is correct when the suite is green **and** `mypy --strict` reports no NEW errors against
the merged tree -- compare against main before your change, because some errors pre-date you.

**If a conflict is genuinely ambiguous, stop and say so in your final message rather than guessing.**
A wrong merge that passes the tests is the worst outcome available here: this repository exists to
measure the rate at which checks accept bad artefacts, and a green suite over a bad merge is
exactly that number going up. Say which hunk defeated you and what the two readings were.
""",
        encoding="utf-8",
    )
    return path


def write_brief(
    uid: str, unit: dict, repair_findings: list[str] | None = None
) -> pathlib.Path:
    BRIEFS.mkdir(parents=True, exist_ok=True)
    path = BRIEFS / f"{uid}.md"
    claims = "\n".join(f"- `{c}`" for c in unit["claims"])
    # A unit's specification does not always live in docs/superpowers/plans/. The design work
    # of 23 August 2026 specified units inside docs/20-design/ documents, and a brief
    # pointing at a path that does not exist sends the agent hunting instead of building.
    # A plan value containing a slash is taken as a path from the repository root.
    plan_ref = (
        unit["plan"]
        if "/" in unit["plan"]
        else "docs/superpowers/plans/" + unit["plan"]
    )
    # A per-unit note carries what the plan cannot: why an earlier attempt refused, what has
    # since changed, and which of its objections were right. Without it the same refusal
    # simply repeats -- T01 refused three times for reasons two-thirds already resolved.
    note = unit.get("note", "")
    if note:
        note = (
            chr(10)
            + "## Read this before you start"
            + chr(10)
            + chr(10)
            + note
            + chr(10)
        )
    if repair_findings:
        note += (
            "\n## Repair required\n\nThe prior adversarial review found:\n"
            + "\n".join("- " + finding for finding in repair_findings)
            + "\nRepair these findings; the unit cannot retire until a changed artefact receives a SOUND review.\n"
        )
    body = f"""# Build {uid} exactly as the plan specifies. Test-first, one commit.

## Your assignment

`{plan_ref}`, unit **{uid} — {unit["title"]}**.

**The plan is the specification.** Read that unit in full and follow it exactly: deliverable,
depends-on, claims, steps, done criteria, its given test command and its given commit message.
**Build {uid} only.** Do not build the next unit, do not widen scope, and do not refactor
adjacent code.

Read first: `docs/superpowers/plans/2026-08-22-build-plan.md` for the global constraints and the
serial lane order, then `AGENTS.md`, then the ADRs your unit cites.

## Check prior art BEFORE you build — this is not optional

**This repository keeps paying twice for the same answer.** On 23 August 2026 the orchestrator spent a
day routing dispatches through the wrong billing pool and then rediscovered the cause from a
screenshot — while `docs/20-design/quota-pools-and-routes-2026-08-21.md` had already established it
two days earlier, with measurements. [measured] A competitor teardown was commissioned for `ruflo`
when `docs/20-design/ruflo-adoption-and-upstream-plan-2026-08-20.md` already existed.

**Before writing code, search `docs/` for whether your unit's problem is already decided or already
measured.** The corpus is 90 ADRs, 29 design documents and 56 research documents — far more than the
handful your plan unit names.

- **`docs/40-spec/v0-draft.md` is the approved implementation boundary.** Read it. If your unit would
  exceed it, stop and say so rather than exceeding it.
- **`docs/20-design/`** almost certainly holds a document about your subject. Find it.
- **`docs/10-research/findings.md` and the experiment register.** **If an experiment already measured
  what your unit assumes, use the measurement — and if it contradicts your unit, that is a finding
  worth more than the unit.**
- **`docs/decisions/index.md`** maps all 90 ADRs. Your unit cites a few; check whether others bind it.

**Name in your report every existing document you found that bears on this unit, and what it changed.**
"Nothing existed" is a claim requiring evidence — say what you searched.

## Claim exactly these and nothing else

{claims}
{note}

**If a path you need is not in that list, stop and say so in your report** rather than claiming it.
An under-declared claim races silently; that is a defect this project has already measured.

## Method

**Test-first**, as the unit's own steps require: write the failing checks, then the smallest
implementation that passes. **Working principle 4 — the fix goes in code, so it cannot regress.**
Ship the check that fails if your work is undone.

## Better than best — working principle 9, and it binds this unit

**Building the plan exactly is conformance. It is not the standard here.** The principal, 21 August
2026: *"In everything we do, and the harness does, we should always enforce aiming for better than the
best that already exists. That is the bar."*

**Read `.agents/skills/better-than-best/SKILL.md` and apply its own three-condition threshold**, which
exists precisely so this does not become ceremony: run the full protocol only when a decision turns on
the answer, the question is open, and being wrong costs more than the protocol costs. **On a mechanical
edit inside an already-decided approach, answer directly, tag the claim, and move on** — a five-stage
synthesis on a typo teaches people to skip the protocol when it matters.

Where it does apply to this unit:

1. **Name the incumbent.** What is the best existing implementation of the thing you are building — a
   standard-library primitive, a published algorithm, a well-known library, another project's approach?
   **State it and cite it.** "Nothing exists" is a claim requiring evidence, and it is the claim this
   project has already got wrong in its own README.
2. **Say how yours is better, and what measurement would show it.** If yours is merely equal, say that
   plainly — **a correct standard answer beats a novel wrong one**, and the skill says so.
3. **If the plan's approach is worse than the incumbent, say so in your report and build the better
   one.** The plan is a specification, not scripture. Correcting it is worth more than following it
   silently, and the plan itself asks you to.

**Record the bar so it can be re-checked.** A bar found once and never re-measured is a bar you have
stopped clearing.

## Hard limits

- **Baseline is 898 passed, 1 skipped.** None may fall. Report the exact suite line before and after.
- `src/consilient/` is AST-locked: no `subprocess`, network, credentials, third-party imports or
  `getattr`. Subprocess work belongs in `scripts/`.
- **No new CLI subcommand** — the set is pinned at six. **Change no gate condition**; `consil doctor`
  must report exactly what it reports now. `events.py` remains the single writer.
- `CONSILIENT_RUN_ID` required; stage only your claimed paths; never `--no-verify`; do not push.
- No secret; no metered call; **nothing from `../hireable-3.0` or `../jobboard-v2`** — not their code,
  contents, paths or commit identifiers. One stream leaked a line from them on 22 Aug 2026.

## Report

What you built, the check that proves it, and the commit hash. **The exact suite line before and
after.** Anything in the plan unit you found wrong — **correcting it is worth more than following it
silently.** And any path you needed that your claim list did not cover.
"""
    text = body + (TAIL.read_text(encoding="utf-8") if TAIL.exists() else "")
    path.write_text(text, encoding="utf-8")
    return path


# The real constraint is the 24-level dependency critical path, not this number. Levels are
# up to 5 units wide, and reviews run beside builds rather than after them, so the cap must
# cover a full level of builds PLUS its predecessors' reviews or it becomes the bottleneck
# itself. Claim disjointness and dispatch.py's claim refusal are the actual safety guard;
# this is only a load cap on the machine.
# Parallel by DEFAULT. The principal, 23 Aug 2026: "It should always maximise paralellism by
# default unless deliberately constrained by the user and I will never want it constrained."
#
# Adopted from his own plans, which group work into WAVES rather than levels: everything in a
# wave runs together and the justification is a fact about files — "no shared files" — while
# serialisation carries a named reason, e.g. "destructive cutover wants the deploy-signing
# substrate live". Units that police others go LAST, not first.
#
# His repository layout is the other half of the method: jb-ws1..jb-ws13, jb-fix2-*,
# consilient-w-a1..w-p5 — one tree per workstream, so a shared git index never arises. This
# driver now does the same: every unit builds in its own worktree, so two units editing
# different files cannot collide at all, and only the merge-back is serial.
MAX_BUILDS = 24
MAX_REVIEWS = 12
MAX_CONCURRENT = MAX_BUILDS + MAX_REVIEWS

# Phase order from the build plan's recommended sequence. Foundation and the record first;
# ingress and self-improvement last because they unlock nothing upstream. Within a phase,
# dependency edges and claim disjointness decide what may actually start.
PHASE = {
    "F": 0,
    "R": 1,
    "E": 1,
    "O": 2,
    "C": 2,
    "T": 2,
    "M": 3,
    "D": 4,
    "L": 5,
    "V": 6,
    "P": 6,
    "Q": 6,
    "G": 6,
    "A": 7,
    "S": 8,
    "H": 8,
}


def ready(uid, unit, done, units):
    """A unit may start when every dependency it declares has landed.

    Dependencies come from the plans' own `Depends on:` lines. A dependency naming a unit
    that does not exist in any plan is treated as unsatisfiable and reported, never assumed
    satisfied — silently ignoring an unknown edge is how a unit gets built on nothing.
    """
    for d in unit.get("deps", []):
        if d not in units:
            return False
        if d not in done:
            return False
    return True


TICK_LOCK = ROOT / ".harness" / "driver-tick.lock"


def hold_tick_lock():
    """One tick at a time, or the suite runs against itself.

    MEASURED 24 August 2026: two build_driver processes were ticking concurrently -- the
    saturation agent's loop and an orchestrator's -- and nine pytest processes were live at
    once. The suite went from 432s to 961s purely on contention, and since a unit only retires
    on a green suite, both ticks were paying double to do the same work more slowly. Nothing
    guarded against it; the driver had no notion that another copy of itself might exist.

    Returns the held handle, or None when another tick owns it. Never blocks: a queued tick is
    a tick doing nothing useful, and the caller should simply exit and let the holder finish.
    """
    handle = TICK_LOCK.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def main() -> int:
    units = load(UNITS, {})
    state = load(STATE, {"done": [], "attempts": {}})
    # `done` means retired. Old `done`, `verified`, and `force_done` values predate structured,
    # identity-bound review receipts, so none can substitute for current evidence.
    done = retired_units(state, units)
    built = set(state.setdefault("built", []))
    # Register EVERY unit whose plan commit is in the tree, not only those a previous `done`
    # list happened to name. `committed()` prefix-matches the subject the plan specifies and
    # already tolerates a hand-merge suffix, so it recognises work however it arrived -- merged
    # by the driver, cherry-picked by hand, or landed under a second sha after a unit was built
    # twice.
    #
    # MEASURED 24 August 2026: SEVENTEEN units had their plan commit in HEAD while the driver
    # recorded them as neither built nor retired. Each one blocked its dependents and was
    # eligible to be dispatched again, so the queue was paying twice for work already in the
    # tree. The check existed and was simply pointed at the wrong set.
    for uid, unit in units.items():
        if uid not in done and uid not in built and committed(uid, unit):
            built.add(uid)
            state.get("conflicts", {}).pop(uid, None)
    state["done"] = sorted(done)
    state["built"] = sorted(built)

    # Retire anything that landed since the last tick, whether we dispatched it or not.
    # Bring back anything that finished in its own tree, then judge it.
    # Slots first, before anything below can return early. A held slot is capacity the queue cannot
    # use, and an idle unit produces no artefact to notice it by.
    # A unit vanishing from the plan is silent, and it happened: the surfaces unit queued on
    # 24 August 2026 was simply absent an hour later. Nothing in this repository WRITES
    # plan-units.json -- it is read-only to every script -- so the loss came from a git
    # operation restoring an older copy over a hand edit, during one of the cherry-picks and
    # checkouts used to resolve merges. Queued work disappearing without a sound is worse than
    # a merge conflict, because a conflict announces itself.
    #
    # This cannot prevent the loss; it makes it loud. The count is recorded each tick and a DROP
    # is reported. It never blocks -- a unit legitimately removed by the principal is not an
    # error -- but it will never again happen without a line in the log naming it.
    seen_units = int(state.get("unit_count") or 0)
    if seen_units and len(units) < seen_units:
        missing = seen_units - len(units)
        print(
            f"driver: WARNING -- the plan lost {missing} unit(s) since the last tick "
            f"({seen_units} -> {len(units)}). Nothing here writes plan-units.json, so this is a "
            "git operation restoring an older copy over an edit. Check the last merge or "
            "checkout before dispatching anything."
        )
    state["unit_count"] = len(units)

    reclaimed = reclaim_expired_slots(state)
    if reclaimed:
        print(
            f"driver: reclaimed {len(reclaimed)} expired slot(s), attempts refunded: "
            + " ".join(reclaimed)
        )

    # BU-0: the cheap supervision floor. One pass over open claims and their artefacts;
    # non-zero means something died quiet and the tick should not pretend the queue is fine.
    stalled = start_failed_dispatches()
    for row in stalled:
        run_id = row.get("run_id", "?")
        signal = row.get("signal", "no artefact within the start window")
        observed = row.get("observed_bytes", 0)
        print(
            f"driver: START_FAILED {run_id} -- {signal} "
            f"({observed} bytes after {row.get('observed_s')}s)"
        )

    # A crash is reported the tick it happens, not at the next check-in. The principal asked for
    # this after finding three of them himself: "this needs to be reported and auto-fixed to
    # orchestrators in real time not discovered during a check in."
    dead = crashed_dispatches(state)
    if dead:
        crash_log = state.setdefault("crash_history", {})
        for uid, why, refused in dead:
            kind = "REFUSED" if refused else "CRASHED"
            print("driver: " + kind + " " + uid + " -- " + why[:160])
            seen = crash_log.setdefault(uid, [])
            seen.append(why[:200])
            # An infrastructure death is not evidence about the work, so it must not spend a
            # retry -- F-05. But a repeated identical death IS evidence, and auto-repair that
            # silently retries a systematic defect is how a system ships with its own bugs built
            # in. Three of the same failure stops being repaired and starts being escalated.
            # Releasing what a dead run held is hygiene, not repair, so it happens for every
            # death INCLUDING an escalated one. The escalation used to `continue` straight past
            # this block, so an escalated unit kept its slot for ever: Y02 died the same way 77
            # times while still counted as in flight. Stopping the retries is right; leaking the
            # capacity is not. [measured 24 Aug 2026]
            state["in_flight"].pop(uid, None)
            for bucket_name in ("resolve_dispatched", "review_dispatched"):
                bucket = state.get(bucket_name, [])
                if uid in bucket:
                    bucket.remove(uid)
            if len(seen) >= 3 and len(set(seen[-3:])) == 1:
                print(
                    "driver: ESCALATION -- "
                    + uid
                    + " has died the same way "
                    + str(len(seen))
                    + " times. This is a defect, not bad luck. Auto-repair "
                    "stopped; it needs a person."
                )
                continue
            state.setdefault("attempts", {})[uid] = max(
                0, state.get("attempts", {}).get(uid, 1) - 1
            )
            # A crashed review is the quietest failure of the lot: the unit stays "done", the
            # review never happens, and nothing anywhere records that the artefact was never
            # checked by a different model family. Three units reached done this way today.
            state.setdefault("verified", [])
        freed = release_dead_claims({u for u, _, _ in dead})
        if freed:
            print(
                "driver: released "
                + str(freed)
                + " claim(s) held by runs that are gone"
            )

    # A review process owns the output until it exits. Once none is live, consume every receipt;
    # malformed, stale and failed output are explicit check errors and will be retried.
    # Consume a receipt when THAT REVIEW has finished, not when the whole system is idle.
    #
    # MEASURED 24 August 2026, and this is why nothing was ever verified. The condition was
    # `live_dispatchers() == 0`, which is true only when NOTHING at all is running. This driver
    # exists to saturate -- 24 units in flight is normal -- so that state effectively never
    # arrives, and valid verdicts queued indefinitely. B01 returned a well-formed SOUND receipt
    # whose artefact identity bound correctly against both the expectation and the unit's current
    # artefact, and it still could not retire, because something unrelated was running.
    #
    # `scripts/dispatch.py` writes `<uid>-verify.out` ONCE, AT COMPLETION -- the same property
    # that made the tail-only parser fail is what makes this safe. A non-empty artefact means
    # that review's process has written its final report and let go of the file. A torn read
    # fails json.loads, becomes a check_error, and is retried, so the race fails closed.
    for uid in sorted(list(state.setdefault("review_dispatched", []))):
        receipt = BRIEFS / f"{uid}-verify.out"
        try:
            finished = receipt.stat().st_size > 0
        except OSError:
            finished = False
        if not finished:
            continue
        outcome = consume_review_verdict(state, uid, units[uid])
        print(f"driver: review of {uid} consumed as {outcome}")
    done = retired_units(state, units)
    built = set(state.setdefault("built", []))
    state["done"] = sorted(done)
    state["built"] = sorted(built)

    import time as _time_m

    conflicts = state.setdefault("conflicts", {})
    # MEASURED 24 August 2026. A conflict was recorded once and never re-tested, but HEAD moves
    # every tick, so a cherry-pick that collided an hour ago usually applies cleanly later. Of 23
    # units reported as unmergeable, SIXTEEN were stale rather than genuine -- they had been
    # waiting on a collision that no longer existed, and each was holding a resolver slot for it.
    # Re-testing is cheap (`git merge-tree` writes nothing) and it is the difference between a
    # queue that drains and one that only grows.
    for _uid, _why in sorted(list(conflicts.items())):
        _m = re.search(r"cherry-picking ([0-9a-f]{7,40})", _why or "")
        if not _m:
            continue
        _sha = _m.group(1)
        if sh(["git", "merge-base", "--is-ancestor", _sha, "HEAD"]).returncode == 0:
            conflicts.pop(_uid, None)
            print(f"driver: {_uid} conflict cleared -- already in the tree")
            continue
        # A unit dispatched twice -- a retry after its slot was reclaimed -- builds twice. One
        # attempt merges and the driver goes on retrying the OTHER sha for ever, because work is
        # identified here by commit id rather than by what the commit says. MEASURED 24 August
        # 2026: NINE of twelve units reported as unmergeable had already landed under a different
        # sha with an identical subject, including T01, which gates 22 units and had been
        # "blocked" for hours on a merge that had already happened.
        # Retire on CONTENT, never on a commit subject. MEASURED 24 August 2026: across 646
        # commits there are 590 distinct subjects and 14 reused ones -- a single subject appears
        # 24 TIMES and another 18, carrying different patch content. Grepping the subject and
        # retiring on any hit is therefore a false-accept path in the driver's own classifier: a
        # check accepting "this work has landed" when it has not. It demonstrably did so --
        # src/consilient/harness.py carries a duplicated block, `_validate_instance` bound at
        # both 292 and 605 and `grammar_accepts` at 344 and 657, giving 17 mypy no-redef errors
        # in the product tree.
        #
        # Content coverage instead: take the unit's own added lines and ask whether they are
        # actually present in HEAD's copy of the same file. Retire only at >= 99% coverage AND
        # at least 20 added lines -- below either bar it falls through and stays escalated,
        # because a small diff cannot distinguish "landed" from "coincidentally similar".
        _covered = _content_landed(_sha)
        if _covered:
            # Record it as BUILT, not force_done. MEASURED 24 August 2026: force_done is written
            # here and read nowhere -- `done` is derived from consumed review receipts alone --
            # so the conflict was popped and then RE-ADDED by the merge loop later in the same
            # tick, which still had the unit in `mergeable`. Eight units cycled that way
            # indefinitely. `built` is the set the merge loop actually skips, and it is the
            # honest description: the work IS in the tree, it simply has not been verified.
            #
            # This also reconciles two detectors that disagreed by construction. `committed()`
            # prefix-matches the subject the PLAN specifies; this loop matches the subject the
            # cherry-picked COMMIT carries. Six of eight units had landed under a subject the
            # agent chose rather than the one the plan named -- AT's plan says "admit ssh-signed
            # verdicts", it landed as "recognise signed ssh_sig verdicts as authenticated" -- so
            # committed() said no while this loop said yes. Only this loop was right.
            conflicts.pop(_uid, None)
            state.setdefault("built", [])
            if _uid not in state["built"]:
                state["built"].append(_uid)
            if _uid in state.setdefault("resolve_dispatched", []):
                state["resolve_dispatched"].remove(_uid)
            print(
                f"driver: {_uid} already landed -- its added lines are present in HEAD; retiring"
            )
            continue
        if (
            sh(
                ["git", "merge-tree", "--write-tree", "--name-only", "HEAD", _sha]
            ).stdout.count("CONFLICT")
            == 0
        ):
            conflicts.pop(_uid, None)
            if _uid in state.setdefault("resolve_dispatched", []):
                state["resolve_dispatched"].remove(_uid)
            print(
                f"driver: {_uid} conflict was stale -- it merges cleanly against current HEAD"
            )
    _now_m = _time_m.time()
    _dispatchers_alive = live_dispatchers()
    # Every unmerged worktree, not just the in-flight ones. A unit that finished, dropped out of
    # in_flight when its leash expired, and still held unmerged commits was never revisited: the
    # merge loop only ever looked at in_flight, so its output was stranded exactly as F-02
    # describes. V01 sat built-and-unmergeable this way while the tick reported it every time and
    # did nothing about it. [measured 23 Aug 2026]
    mergeable = [
        uid
        for uid in units
        if uid not in done and uid not in built and (WORKTREES / uid).exists()
    ]
    for uid in mergeable:
        if True:
            started, leash = state.get("in_flight", {}).get(uid, (0.0, 0.0))
            # Quiescent means the leash has run out, so no dispatcher should still be writing
            # in that tree. Only then may its branch be rebased under it.
            msg = merge_unit_worktree(
                uid, quiescent=(_now_m - started > leash or _dispatchers_alive == 0)
            )
            if msg not in ("no commits", "no worktree"):
                print(f"driver: {msg}")
            if msg.startswith("CONFLICT"):
                conflicts[uid] = msg
            else:
                conflicts.pop(uid, None)
    if conflicts:
        print(
            f"driver: ESCALATION — {len(conflicts)} unit(s) cannot merge without help: "
            f"{' '.join(sorted(conflicts))}"
        )

    green = None
    rejected = state.setdefault("rejected_artefacts", {})
    for uid, unit in units.items():
        artefact = artefact_identity(unit)
        if (
            uid not in done
            and uid not in built
            and artefact is not None
            and rejected.get(uid) != artefact
            and committed(uid, unit)
        ):
            if green is None:
                green = suite_green()
            if green:
                built_by = state.setdefault("built_by", {})
                built_by.setdefault(uid, state.get("last_arm", {}).get(uid, "codex"))
                state.setdefault("built", []).append(uid)
                built.add(uid)
                print(
                    f"driver: {uid} built (plan commit present, suite green) — awaiting review"
                )
    state["done"] = sorted(done)

    # Built but unreviewed units get an adversarial reviewer from a different family before
    # they count as complete. Verifying by the unit's own tests alone is echo.
    pending_review = [
        u
        for u in sorted(state.setdefault("built", []))
        if u not in state.setdefault("review_dispatched", [])
    ]

    live = live_dispatchers()
    # Reviews ALREADY outstanding count against MAX_REVIEWS. This started at 0 each tick, so it
    # counted only what this tick launched and never what was still running: every tick added up
    # to twelve more on top of the backlog. MEASURED 24 Aug 2026 -- 64 reviews in flight against
    # a cap of 12, one unit on its 27th review attempt, and 68 check_error against 3 SOUND.
    #
    # Each review full-clones a 136 MB workspace, so sixty-four of them thrash the machine badly
    # enough that none of them finish, which is why the verification tier produced almost nothing
    # while looking maximally busy. MAX_REVIEWS was always meant to be a concurrency cap -- the
    # name says so -- and this makes it one instead of a per-tick rate.
    reviews_out = len(state.setdefault("review_dispatched", []))
    for uid in pending_review:
        if reviews_out >= MAX_REVIEWS or live >= MAX_CONCURRENT:
            break
        builder = state.get("built_by", {}).get(uid, "codex")
        reviewers = [a for a in ARMS if FAMILY.get(a[0]) != FAMILY.get(builder)]
        if not reviewers:
            continue
        artefact = artefact_identity(units[uid])
        if artefact is None:
            continue
        rh, rm, rl = reviewers[0]
        attempt = state.setdefault("review_attempts", {}).get(uid, 0) + 1
        state["review_attempts"][uid] = attempt
        state.setdefault("review_expected", {})[uid] = {
            "artefact": artefact,
            "attempt": attempt,
        }
        vb = write_verify_brief(uid, units[uid], artefact, attempt)
        vargs = [
            sys.executable,
            "scripts/dispatch.py",
            "--task-file",
            str(vb),
            "--harness",
            rh,
            "--allow-exhausted",
            "--timeout",
            str(rl),
            "--permissions",
            "bypass",
            "--max-turns",
            str(DEFAULT_TURNS),
            "--json",
        ]
        if rm:
            vargs += ["--model", rm]
        vo = (BRIEFS / f"{uid}-verify.out").open("w", encoding="utf-8")
        ve = (BRIEFS / f"{uid}-verify.err").open("w", encoding="utf-8")
        subprocess.Popen(vargs, cwd=str(ROOT), stdout=vo, stderr=ve)
        state["review_dispatched"].append(uid)
        live += 1
        reviews_out += 1
        print(f"driver: review of {uid} dispatched to {rh} (built by {builder})")

    if live >= MAX_CONCURRENT:
        print(f"driver: {live} dispatchers live at the cap; holding")
        save_state(state)
        return 0

    attempts = state.setdefault("attempts", {})

    # A unit already dispatched and still within its leash is NOT a candidate. The driver
    # previously had no memory of what it had started, so each tick re-dispatched everything
    # in flight until the retry cap fired on units that were working fine.
    import time as _time

    inflight = state.setdefault("in_flight", {})
    now = _time.time()
    # Reclamation also runs unconditionally at the top of the tick (see reclaim_expired_slots),
    # because sitting here it was behind two early returns and nine slots stayed held for forty
    # minutes past their leash while three processes were alive. [measured 23 Aug 2026, F-14]
    for uid in list(inflight):
        started, leash = inflight[uid]
        if uid in done or now - started > leash + 300:
            inflight.pop(uid, None)

    # A unit whose worktree already holds its own commits is BUILT — it is waiting to merge,
    # not waiting to be built. Re-dispatching it burns a retry on a merge-back problem and
    # discards finished work. F03 was re-dispatched this way while its commit sat complete in
    # its worktree. [measured 23 Aug 2026]
    built_unmerged = set()
    for uid in list(units):
        wt = WORKTREES / uid
        if uid not in done and wt.exists():
            head = sh(["git", "-C", str(wt), "rev-parse", "HEAD"]).stdout.strip()
            if head and sh(
                ["git", "rev-list", "--count", f"HEAD..{head}"]
            ).stdout.strip() not in ("", "0"):
                built_unmerged.add(uid)
    if built_unmerged:
        print(f"driver: built and awaiting merge: {' '.join(sorted(built_unmerged))}")

    candidates = [
        u
        for u in units
        if u not in done
        and u not in state.setdefault("built", [])
        and u not in inflight
        and u not in built_unmerged
        and attempts.get(u, 0) < 3
    ]
    candidates.sort(key=lambda u: (PHASE.get(u[0], 9), u))

    # A dependency is satisfied when its code is IN THE TREE, not when it has been verified.
    # AV correctly made RETIREMENT require a consumed SOUND verdict, but the same set was also
    # gating what may START, and those are different questions: a dependent needs the code to
    # exist so it can build against it, whereas verification decides whether the work is sound
    # enough to ship. MEASURED 24 August 2026, immediately after AV landed: 45 units merged, 0
    # retired, and TWENTY units whose dependencies were all present could not start -- including
    # P02, T02 and T03, which is the entire critical path. The build had stopped behind review
    # throughput.
    #
    # This is a relaxation and it is named as one. The risk it accepts: a unit may build on a
    # dependency later judged DEFECTIVE. That risk is bounded because the dependent is itself
    # reviewed, and because review runs in parallel rather than after. What is NOT relaxed is
    # retirement or publication -- both still require the identity-bound SOUND verdict, which is
    # where the beta discipline actually bites.
    landed = done | set(state.setdefault("built", []))
    blocked = [u for u in candidates if not ready(u, units[u], landed, units)]
    startable = [u for u in candidates if ready(u, units[u], landed, units)]
    # Spend slots on whatever releases the most work, not on whatever sorts first.
    # Downstream count is the right default and a bad rule for one case: a unit that unblocks
    # nothing but improves the QUALITY of everything -- the cross-family verdict parser is the
    # example -- sorts last under it, which is exactly backwards. An explicit `priority` on the
    # unit is added to its effective rank. It is deliberately a separate, visible field rather
    # than a fudged dependency, because inflating a dependency count to win a scheduling argument
    # is how a plan stops describing the work.
    startable.sort(
        key=lambda u: (
            -(downstream_count(u, units) + int(units[u].get("priority", 0))),
            PHASE.get(u[0], 9),
            u,
        )
    )

    if not candidates:
        print(f"driver: every unit is done or exhausted ({len(done)}/{len(units)})")
        save_state(state)
        return 0

    launched = 0
    for uid in startable:
        if launched >= MAX_BUILDS or live + launched >= MAX_CONCURRENT:
            break
        unit = units[uid]
        n = attempts.get(uid, 0)
        brief = write_brief(uid, unit, state.setdefault("repair_findings", {}).get(uid))
        rot = state.get("arm_rotation", 0)
        harness, model, leash = pick_arm(rot + n, state)
        state["arm_rotation"] = rot + 1
        args = [
            sys.executable,
            "scripts/dispatch.py",
            "--task-file",
            str(brief),
            "--harness",
            harness,
            "--allow-exhausted",
            "--timeout",
            str(leash),
            "--permissions",
            "bypass",
            "--max-turns",
            str(unit.get("turns", DEFAULT_TURNS)),
        ]
        if model:
            args += ["--model", model]
        for c in unit["claims"]:
            args += ["--claim", c]
        wt = unit_worktree(uid)
        if wt is not None:
            args += ["--cwd", str(wt)]
        out = (BRIEFS / f"{uid}.out").open("w", encoding="utf-8")
        err = (BRIEFS / f"{uid}.err").open("w", encoding="utf-8")
        subprocess.Popen(args, cwd=str(ROOT), stdout=out, stderr=err)
        attempts[uid] = n + 1
        inflight[uid] = (now, leash)
        # Record which arm actually took the work. This was read at retirement and never
        # written, so `built_by` recorded "codex" for all 17 finished units regardless of who
        # built them -- and reviewer selection, which picks a DIFFERENT model family from the
        # builder, was choosing against fabricated data. A cross-family reviewer selected from a
        # wrong builder is not a different class of evidence; it is echo with paperwork.
        state.setdefault("last_arm", {})[uid] = harness
        launched += 1
        print(
            f"driver: dispatched {uid} ({unit['title']}) to {harness}/{model or 'default'} "
            f"[{leash}s], attempt {n + 1}"
        )

    # A conflicted unit is startable work of a different kind, and it cannot clear itself: V01
    # reached the retry cap while its code sat finished in its worktree, because a merge conflict
    # consumed attempts that were meant to count genuine build failures (F-05). Resolution gets
    # its own dispatch, its own brief, and does not touch the build retry counter.
    resolving = state.setdefault("resolve_dispatched", [])
    for uid, why in sorted(conflicts.items()):
        if launched >= MAX_BUILDS or live + launched >= MAX_CONCURRENT:
            break
        if uid in resolving or uid in done or (WORKTREES / uid).exists() is False:
            continue
        unit = units.get(uid)
        if not unit:
            continue
        rbrief = write_resolve_brief(uid, unit, why)
        rot = state.get("arm_rotation", 0)
        harness, model, leash = pick_arm(rot, state)
        state["arm_rotation"] = rot + 1
        rargs = [
            sys.executable,
            "scripts/dispatch.py",
            "--task-file",
            str(rbrief),
            "--harness",
            harness,
            "--allow-exhausted",
            "--timeout",
            str(leash),
            "--permissions",
            "bypass",
            "--max-turns",
            str(DEFAULT_TURNS),
        ]
        if model:
            rargs += ["--model", model]
        for c in unit["claims"]:
            rargs += ["--claim", c]
        wt = unit_worktree(uid)
        if wt is not None:
            rargs += ["--cwd", str(wt)]
        ro = (BRIEFS / f"{uid}-resolve.out").open("w", encoding="utf-8")
        re_ = (BRIEFS / f"{uid}-resolve.err").open("w", encoding="utf-8")
        subprocess.Popen(rargs, cwd=str(ROOT), stdout=ro, stderr=re_)
        resolving.append(uid)
        inflight[uid] = (now, leash)
        launched += 1
        print(
            f"driver: RESOLVE dispatched for {uid} to {harness}/{model or 'default'} [{leash}s]"
        )

    if not launched:
        print(
            f"driver: nothing startable — {len(blocked)} unit(s) waiting on dependencies"
        )
    print(
        f"driver: {len(done)}/{len(units)} done, {len(startable)} ready, {len(blocked)} blocked"
    )

    # Last, so a publish only ever carries work that survived everything above it this tick.
    published = publish_if_ready(state, green)
    if published:
        print(f"driver: {published}")

    save_state(state)
    return 0


if __name__ == "__main__":
    _lock = hold_tick_lock()
    if _lock is None:
        print(
            "driver: another tick holds the lock; exiting rather than competing for the suite"
        )
        raise SystemExit(0)
    try:
        raise SystemExit(main())
    finally:
        _lock.close()
