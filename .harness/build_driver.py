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
import shutil
import subprocess
import sys
import time
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNITS = ROOT / ".harness/plan-units.json"
STATE = ROOT / ".harness/driver-state.json"
BRIEFS = ROOT / ".harness/dispatch/briefs-driver"
TAIL = ROOT / ".harness/dispatch/briefs-2026-08-22/_tail.md"
LOG = ROOT / ".harness" / "log"
RUNS = ROOT / ".harness" / "dispatch"
PUBLISH_STOP = ROOT / ".harness" / "STOP-PUBLISH"

# Dispatch order is `.harness/plan-units.json` plus each unit's `deps`.
# A hardcoded ORDER list lived here and was never read; unit AI deleted it.

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
ARMS: list[tuple[str, str | None, int]] = [
    # CURSOR RESTORED, 27 August 2026, after the principal reauthenticated it from a near-spent
    # account to one with headroom. The account itself is not named here: a pre-publication audit
    # the same day found this comment carrying an operational account's address on the private
    # commercial product's own domain, together with the minute it was created -- an identity and
    # a timeline that a source comment does not need and a public repository should not carry.
    # `cursor-agent status` is where the current identity is read from, and it is not tracked.
    # Restored on the artefact, not on the account page: four live dispatches through the
    # real path returned `produced an artefact` with the expected string in stdout, one per
    # model id below plus the two grok-backed ids, in 20-34s each. That is the same bar the
    # 23 August grok restoration had to clear, and it is the bar because a harness that starts
    # and dies looks identical to one that found nothing. [measured]
    #
    # ALL FOUR CURSOR ARMS NAME A COMPOSER MODEL, AND THAT IS THE POINT. Reviewer selection is
    # `FAMILY.get(a[0]) != FAMILY.get(builder)`, keyed on the HARNESS ID alone -- so
    # `("cursor-composer", "cursor-grok-4.6-high-fast", ...)` is offered as a cross-family
    # check on grok-built work while running xAI's Grok 4.6. The map says "cursor"; the model
    # is the builder's own. Four of the six cursor arms withdrawn on 26 August were exactly
    # that, so for as long as they ran, a share of cross-family review was agreement between
    # two instances of the same model. AGENTS.md principle 6: agreement between agents that
    # share evidence is not consilience, it is echo -- and Whewell's test needs "another
    # DIFFERENT class". A nominal family is not a different class. Composer is Cursor's own
    # model, so a composer arm makes the cursor family real rather than declared.
    # `test_cursor_arms_do_not_borrow_another_familys_model` enforces this, because a rule
    # this file states and nothing checks is how the last four of these got there.
    #
    # Even 4/4/4, not the 6/4/2 of 26 August. That weighting was tuned to headroom measured on
    # 23 August -- cursor 2%, grok 17% -- and every one of those accounts has since been
    # replaced. A weighting whose evidence no longer exists is a guess with a history, so the
    # split is even until there is something to measure. Codex is the only pool exposing a
    # verified counter (2.0% used, resets 3 September); cursor and grok report `unknown`.
    ("codex", None, 3600),
    ("grok", None, 3600),
    ("cursor-composer", "composer-2.5", 3600),
    ("codex", None, 3600),
    ("grok", None, 3600),
    ("cursor-composer", "composer-2.5-fast", 3600),
    ("codex", None, 3600),
    ("grok", None, 3600),
    ("cursor-composer", "composer-2.5", 3600),
    ("codex", None, 3600),
    ("grok", None, 3600),
    ("cursor-composer", "composer-2.5-fast", 3600),
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

# MEASURED 27 August 2026: both remaining arms (codex, grok) were simultaneously out of
# usage -- Codex's own app-server reported `rateLimitReachedType` set, and a live Grok call
# inside a dispatch's own test run returned "API error (status 402 Payment Required): Grok
# Build usage balance exhausted" -- while `pick_arm` kept rotating into both anyway, spending
# slots on dispatches with no usable model behind them. Reactive rather than a live probe per
# arm: there is no lightweight balance check for every provider (headroom.py's own probe
# explicitly excludes grok), but every dispatch that hits an exhausted provider says so in its
# own stdout/stderr, so recognising a small set of narrow, unambiguous phrases there covers any
# arm uniformly without a bespoke integration per provider. Bare status codes ("429", "402") are
# deliberately excluded -- they were false positives (line numbers, commit-ish fragments) in a
# real transcript scan.
ARM_EXHAUSTION_PHRASES = (
    "usage balance exhausted",
    "rate limit reached",
    "ratelimitreached",
    "spend-control",
    "spend control reached",
    "quota exhausted",
    "quota exceeded",
    "payment required",
)
# Conservative guess, not a measured reset cadence -- there is no live per-arm balance check to
# confirm recovery, so this only bounds how long a stale cooldown can block a recovered arm.
ARM_COOLDOWN_S = 1800

# What to assume for a resolve entry recorded before start times were kept. Every arm in `ARMS`
# leases 3600s and every resolve dispatch uses that leash, so this is the value they were
# actually given -- not a guess, just the one that was never written down.
RESOLVE_ADOPTED_LEASH_S = 3600


def _tail_text(path: pathlib.Path, max_bytes: int = 8192) -> str:
    """Up to the last `max_bytes` of a file, read as text. Empty string if unreadable."""
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > max_bytes:
                fh.seek(-max_bytes, os.SEEK_END)
            return fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def detect_exhausted_arms(state: dict) -> None:
    """Cool down an arm whose most recent dispatch reports it is out of usage.

    Scans the same watched set `crashed_dispatches` does (in-flight, review, resolve), but
    independently: an exhaustion signal can appear inside a dispatch that otherwise COMPLETED
    (exit 0) -- N03's build finished normally on 27 August 2026 while its own internal test run
    hit Grok's 402, so this cannot be folded into crash detection without missing exactly the
    case that motivated it. [measured]

    AN EXHAUSTION SIGNAL IS EVIDENCE ONCE, NOT ONCE PER TICK. `<stem>.out`/`.err` persist
    until the NEXT dispatch for that unit overwrites them, so re-reading a historical 402
    every tick and re-stamping `cooldown[harness] = now` pins the arm in a cooldown that can
    never expire -- the arm is dead forever on the strength of one old line. That is exactly
    the defect `crashed_dispatches` already carries a fingerprint to prevent (it counted 4,531
    "crashes" that were tick counts), and it bites harder here: on 27 August 2026 Joe moved
    every harness onto a fresh second account, and a stale 402 from the RETIRED grok account
    re-cooled the NEW one 11 minutes after it authenticated. Identity is (stem, mtime, size),
    same shape as `crash_counted`: a genuinely new report rewrites the file and is counted, an
    unchanged file is the report already counted. [measured]
    """
    watched = (
        set(state.get("in_flight", {}))
        | set(state.get("review_dispatched") or [])
        | set(state.get("resolve_dispatched") or [])
    )
    arms_by_unit = state.get("last_arm", {})
    cooldown = state.setdefault("arm_cooldown", {})
    counted = state.setdefault("arm_exhaustion_counted", {})
    now = time.time()
    for uid in sorted(watched):
        harness = arms_by_unit.get(uid)
        if not harness:
            continue
        for stem in (uid, uid + "-resolve", uid + "-verify"):
            fingerprint = []
            newest = 0.0
            for ext in (".err", ".out"):
                try:
                    st = (BRIEFS / f"{stem}{ext}").stat()
                    fingerprint.append(f"{ext}:{int(st.st_mtime)}:{st.st_size}")
                    newest = max(newest, st.st_mtime)
                except OSError:
                    continue
            # AN EXHAUSTION REPORT OLDER THAN THE COOLDOWN HAS ALREADY EXPIRED AS EVIDENCE.
            # The fingerprint above stops the same report being counted twice while its unit
            # stays watched, but `arm_exhaustion_counted` is pruned for any stem that leaves
            # the watched set -- and the `<stem>.out` file is not, because nothing overwrites
            # it until that unit dispatches again. So a unit that leaves and re-enters arrives
            # with its memory erased and its evidence intact, and the old line counts afresh.
            # MEASURED 27 August 2026: `AP-verify.out` carried a "Payment Required" written at
            # 23:34 the previous night, from the grok account since retired. It cooled grok at
            # 12:57 the next day, 13.5 hours later. Worse, `last_arm["AP"]` had by then moved to
            # codex, so the next re-entry would have cooled CODEX -- the one arm still working,
            # measured at 0.0% of its weekly pool -- on the strength of a different account's
            # bill from the day before.
            # Age is the check that does not depend on bookkeeping surviving. A report older
            # than ARM_COOLDOWN_S describes a cooldown that would already have elapsed, so
            # acting on it can only re-impose a window the arm has served.
            if newest and now - newest > ARM_COOLDOWN_S:
                continue
            text = (
                _tail_text(BRIEFS / f"{stem}.err") + _tail_text(BRIEFS / f"{stem}.out")
            ).lower()
            if not text:
                continue
            hit = next((p for p in ARM_EXHAUSTION_PHRASES if p in text), None)
            if hit is None:
                continue
            mark = "|".join(fingerprint)
            if mark and counted.get(stem) == mark:
                break
            if mark:
                counted[stem] = mark
            print(
                f"driver: ARM COOLDOWN -- {harness} reported {hit!r} via {uid}; "
                f"skipping for {ARM_COOLDOWN_S}s"
            )
            cooldown[harness] = now
            break
    # Bounded, like `crash_counted`: a stem no longer watched is forgotten, so this cannot
    # grow without limit and a unit that reports exhaustion again later is counted again.
    for stem in list(counted):
        if stem.split("-")[0] not in watched:
            counted.pop(stem, None)


def pick_arm(index: int, state: dict) -> tuple | None:
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
    cooldown = state.get("arm_cooldown", {})
    now = time.time()
    for offset in range(len(ARMS)):
        harness, model, leash = ARMS[(index + offset) % len(ARMS)]
        if harness == "cursor-composer" and cursor_live >= CURSOR_CONCURRENCY:
            continue
        cooled_at = cooldown.get(harness)
        if cooled_at is not None and now - cooled_at < ARM_COOLDOWN_S:
            continue
        return harness, model, leash
    # Every arm is either a saturated cursor slot or in an exhaustion cooldown -- a saturated
    # cursor slot alone would not empty this loop, since the other arms are what it fell through
    # to. Refuse to invent a harness that cannot do the work rather than spend a slot proving
    # that again; the caller reports this once and skips the dispatch for this tick.
    return None


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


def spawn_logged(
    args: list[str], stdout_path: pathlib.Path, stderr_path: pathlib.Path
) -> None:
    """Start a child, then close the parent's copies of the log handles.

    `Popen` duplicates the fds into the child; the parent must drop its copies
    or the file stays locked on Windows and a later attempt cannot rewrite the
    same path. The 24 August audit named this leak. [cited: subprocess.Popen]
    """
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        stdout_path.open("w", encoding="utf-8") as out,
        stderr_path.open("w", encoding="utf-8") as err,
    ):
        subprocess.Popen(args, cwd=str(ROOT), stdout=out, stderr=err)


def preserve_review_artefacts(uid: str, attempt: int) -> None:
    """Keep the previous attempt's receipts under per-attempt names.

    Opening `{uid}-verify.out` with mode ``w`` destroyed the previous attempt, which is
    why a `check_error` could not be diagnosed after the fact. [measured: Rank 6,
    docs/10-research/failure-classes-and-resilience-2026-08-24.md, 24 August 2026]

    The live names stay `{uid}-verify.out` and `{uid}-verdict.json` so the reviewer
    contract and the identity-bound consumer do not move; history is renamed aside
    before the next attempt truncates them.
    """
    previous = attempt - 1
    if previous < 1:
        return
    BRIEFS.mkdir(parents=True, exist_ok=True)
    pairs = (
        (f"{uid}-verify.out", f"{uid}-verify-{previous}.out"),
        (f"{uid}-verify.err", f"{uid}-verify-{previous}.err"),
        (f"{uid}-verdict.json", f"{uid}-verdict-{previous}.json"),
    )
    for src_name, dst_name in pairs:
        src = BRIEFS / src_name
        dst = BRIEFS / dst_name
        if src.exists() and not dst.exists():
            try:
                # COPY, not rename. MEASURED 28 August 2026 on the held-open case:
                #   rename : FAILED (PermissionError)   <- WinError 32
                #   copy   : SUCCEEDED, archived 'attempt-1 receipt'
                # A copy READS the source, and Windows permits that while another handle
                # holds it; a rename needs exclusive access and cannot get it. The guard
                # added on 27 August stopped the crash but let the archive silently fail,
                # so attempt 1 was still lost to the next mode-'w' open -- which is the
                # whole of Rank 6, and exactly what unit AI's reviewers measured and
                # called DEFECTIVE three times running.
                #
                # Leaving the original in place is correct: the next dispatch truncates it,
                # and if that dispatch never starts the live file still holds attempt 1.
                shutil.copy2(src, dst)
            except OSError as exc:
                # MEASURED 27 August 2026: WinError 32 on N02-verify.out took down the whole
                # tick. Windows refuses to rename a file another process still holds open, and a
                # reviewer subprocess that has not yet closed its stdout is exactly that. Losing
                # one previous attempt's receipt costs a diagnosis; letting the exception reach
                # __main__ costs every unit in flight. The rename is history-keeping, so it is
                # the half that yields -- and the loop keeps going.
                print(
                    f"driver: could not preserve {src_name} ({type(exc).__name__}); "
                    f"the next attempt will overwrite it",
                    flush=True,
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

    The temp name is unique. A fixed `STATE.with_suffix(".json.tmp")` lets two writers
    rename each other's partial file into place -- a crash vulnerability with no crash
    required. `records._install_object` already does this with `os.urandom(16).hex()`.
    [measured: Rank 8, same findings file]
    """
    if _LAST_SUITE_SUMMARY:
        state["last_green_summary"] = _LAST_SUITE_SUMMARY
    STATE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, indent=1)
    tmp = STATE.parent / f".driver-state-{os.urandom(16).hex()}.tmp"
    try:
        with tmp.open("x", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, STATE)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


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


RESTART_WINDOW_S = 600
MAX_RESTARTS = 6
MAX_REVIEW_ATTEMPTS = 3


def quarantine_unit(state: dict, uid: str) -> bool:
    """Quarantine once; ordinary recovery must never make it dispatchable again."""
    quarantined = state.setdefault("quarantined", [])
    if uid in quarantined:
        return False
    quarantined.append(uid)
    state.setdefault("quarantine_escalated", []).append(uid)
    return True


def clear_quarantine_after_landed_check(state: dict, uid: str) -> None:
    """A SOUND, identity-bound review is the automatic quarantine recovery path."""
    quarantined = state.setdefault("quarantined", [])
    if uid in quarantined:
        quarantined.remove(uid)


def record_restart(state: dict, uid: str, *, now: float) -> bool:
    """Record every repair attempt, including failures refundable to the unit budget."""
    restarts = state.setdefault("total_restarts", {}).setdefault(uid, [])
    restarts[:] = [
        timestamp for timestamp in restarts if now - timestamp <= RESTART_WINDOW_S
    ]
    restarts.append(now)
    return len(restarts) > MAX_RESTARTS and quarantine_unit(state, uid)


def reset_review_attempts_on_new_artefact(state: dict, uid: str, artefact: str) -> bool:
    """A rebuilt unit gets a fresh review budget for the code it actually carries now.

    Decided by the principal, 25 August 2026, after AL, AO and AP were found escalated while
    each held a DIFFERENT, newer artefact than the one their three attempts had been spent
    against. `review_attempts` was a pure LIFETIME counter with no relationship to which code
    was under review: a unit reviewed three times, rebuilt after a genuine DEFECTIVE finding
    each time, accumulated exactly as fast as one reviewed three times against the SAME
    unchanged code -- and both landed on the identical escalation, "it needs a person," even
    though only the second is actually stuck.

    `review_expected[uid]` already records the artefact the LAST dispatched attempt was against.
    If the artefact computed for a fresh dispatch differs from that, the code has moved --
    through a legitimate rebuild addressing prior findings -- and the counter resets. If it is
    the SAME artefact (an infrastructure-loss retry under F-05, which does not change
    `review_expected`), nothing resets, and three genuine attempts against the SAME code still
    escalates exactly as before. Returns whether anything was actually reset, so the caller can
    report it rather than print on every dispatch.
    """
    last_artefact = state.setdefault("review_expected", {}).get(uid, {}).get("artefact")
    if last_artefact is None or last_artefact == artefact:
        return False
    attempts = state.setdefault("review_attempts", {})
    escalated = state.setdefault("review_escalated", [])
    changed = attempts.get(uid, 0) > 0 or uid in escalated
    attempts[uid] = 0
    if uid in escalated:
        escalated.remove(uid)
    return changed


def clear_escalations_whose_artefact_moved(
    state: dict, units: dict, pending_review: list[str]
) -> list[str]:
    """Un-escalate every unit whose claimed code has moved since its last review attempt.

    BOOKKEEPING IS NOT A RESOURCE, AND THE REVIEW LOOP TREATED IT AS ONE.

    `reset_review_attempts_on_new_artefact` is what releases a unit whose finding has since
    been fixed. It costs no review slot, no 136 MB clone and no dispatch -- only a hash of the
    claimed blobs. But it was called from inside the review DISPATCH loop, after
    `admit_review`'s `break`. So whenever the review lane sat at its ceiling, that loop broke
    on its FIRST iteration and no unit's artefact was ever recomputed: an escalation could not
    clear no matter how completely the defect behind it had been repaired.

    MEASURED 27 August 2026. BK was escalated carrying a DEFECTIVE verdict that named a
    DDL-detection bypass in `check_merge_acceptance.py` -- `sql_shaped` required
    lstrip-startswith("create table") and vetoed any backslash. Commit 6322d3b fixed exactly
    that on 26 August. BK's artefact identity duly moved, 06d792af -> e54878b3, and BK stayed
    escalated anyway: `reviews_out` was 6 against `MAX_REVIEWS` 6, so the loop printed "review
    lane at ceiling" and broke. 76 units were pending review; the number whose artefact was
    examined was zero, including the one sitting first in the list.

    This is the F-08 lesson in a new place -- capacity that cannot be used is not capacity --
    inverted: work that needs no capacity must not be queued behind the thing that has none.

    Restricted to units the reset can actually report on. It returns False unless
    `review_attempts[uid] > 0` or the unit is escalated, so recomputing the rest would spend two
    `git rev-parse` calls each to learn nothing. On the live state that is 11 units, not 76.
    """
    escalated = state.setdefault("review_escalated", [])
    attempts = state.setdefault("review_attempts", {})
    cleared = []
    for uid in pending_review:
        if uid not in escalated and attempts.get(uid, 0) <= 0:
            continue
        unit = units.get(uid)
        if unit is None:
            continue
        artefact = artefact_identity(unit)
        if artefact is None:
            continue
        if reset_review_attempts_on_new_artefact(state, uid, artefact):
            cleared.append(uid)
    return cleared


def review_dispatch_allowed(state: dict, uid: str) -> bool:
    """Refuse a fourth review attempt and emit its escalation only once."""
    attempts = state.setdefault("review_attempts", {}).get(uid, 0)
    if attempts < MAX_REVIEW_ATTEMPTS:
        return True
    escalated = state.setdefault("review_escalated", [])
    if uid not in escalated:
        escalated.append(uid)
    return False


def live_dispatchers(state: dict) -> int:
    """Count only dispatches this driver recorded, never machine-wide process names."""
    return len(state.get("in_flight", {}))


# A clean run of this suite is ~7 minutes. Twice that is generous for contention and still far
# short of the loop's 3000 s tick abandonment, which is the outcome this exists to avoid.
SUITE_TIMEOUT_S = 900
_LAST_SUITE_SUMMARY: str | None = None


def suite_baseline_line() -> str:
    """The last green pytest summary, or an honest unmeasured marker.

    Hardcoded '898 passed' / '914 passed' in the briefs drifted the moment the suite
    moved. Unit AI interpolates from the last stored green summary instead.
    """
    if _LAST_SUITE_SUMMARY:
        return _LAST_SUITE_SUMMARY
    return "unmeasured (no green suite summary stored yet)"


def suite_green() -> bool:
    """True only when pytest printed a summary and that summary shows no failures.

    This previously passed `--timeout=600`, which pytest-timeout is not installed to
    support. pytest exited with a usage error, stdout carried no summary line, and the
    function returned False for every unit — so NOTHING could ever be recorded done. The
    build loop ran 66 ticks retiring nothing while F02 and F05 sat committed in the log.
    [measured 23 Aug 2026]

    Judge on the summary line pytest actually prints, and fail closed when there is none:
    an absent summary means the run did not complete, which is not the same as passing.

    SUBSTRINGS, NOT COUNTS, was the second defect here and it cost far more than the first.
    The test was `"failed" not in last`, and pytest's summary for a green run reads

        1761 passed, 3 skipped, 1 xfailed in 250.69s

    -- in which "xfailed" CONTAINS "failed". So a suite with a single expected failure was
    reported red for ever. MEASURED 25 August 2026: the same tree that pytest summarised as
    "1761 passed, 3 skipped, 1 xfailed" was reported by this function as not green, and the
    publication gate printed "publish held: 123 commit(s) ready, suite not green" tick after
    tick while public sat 123 commits behind. An xfail is a PASSING outcome; a test expected
    to fail and failing is the suite working.

    Count the numbers pytest reports rather than sniffing for words inside other words. The
    word boundary is what does the work: `\\b\\d+ failed` cannot match "1 xfailed", because the
    "x" is a word character. Fails closed still -- no counted pass means not green.
    """
    # BOUNDED, and the bound is the point.
    #
    # MEASURED 25 August 2026, 21:36: a driver tick sat for THIRTY-FIVE MINUTES on this call
    # having burned 29 seconds of CPU -- starved, not computing. `sh()` passes no timeout, so
    # the only bound was the loop abandoning the whole tick at 3000 s, which also leaks the
    # grandchildren (82 processes were cleared from two such abandonments earlier today).
    #
    # The starvation is SELF-INFLICTED and that is what makes the bound necessary rather than
    # merely tidy. The same tick dispatches its agents and THEN runs the full suite, so the
    # suite always runs against the maximum load the driver has just created -- five dispatch
    # agents and their CLIs, in the measured case. A clean run of this suite takes about seven
    # minutes; the same suite under the tick's own dispatches had not finished in thirty-five.
    #
    # Because the suite is the LAST gate before publication, a tick that never finishes it never
    # publishes. Thirty commits sat ready behind a suite this driver was starving itself.
    #
    # A timeout here FAILS CLOSED: an unfinished run is "not evaluated", which is not the same
    # as passing, and `publish_if_ready` already refuses on a false. So the cost of the bound is
    # a tick that declines to publish; the cost of no bound is a tick that never ends.
    try:
        r = sh(
            [sys.executable, "-m", "pytest", "tests/", "-q"], timeout=SUITE_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        print(
            f"driver: suite did not finish within {SUITE_TIMEOUT_S}s -- treating as NOT GREEN "
            "and continuing the tick rather than wedging it"
        )
        return False
    text = (r.stdout or "") + (r.stderr or "")
    summary = [
        ln
        for ln in text.splitlines()
        if re.search(r"\b\d+ (passed|failed|error|errors|xfailed|skipped)\b", ln)
    ]
    if not summary:
        return False
    last = summary[-1]
    if re.search(r"\b\d+ (failed|error|errors)\b", last):
        return False
    green = bool(re.search(r"\b\d+ passed\b", last))
    global _LAST_SUITE_SUMMARY
    if green:
        _LAST_SUITE_SUMMARY = last.strip()
    return green


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


def family_claims(claims: list[str]) -> list[str]:
    """Expand a claimed module to its split family, because that is where its behaviour went.

    MEASURED 29 August 2026, and this is a safety fix rather than tidying. The 28 August refactor
    moved behaviour out of 22 modules into `<stem>_*.py` siblings and `.harness/plan-units.json`
    was never updated: 102 of 147 units -- 76 of them not yet done -- claim a path that is now an
    almost-empty re-export facade. `events.py` is claimed by 41 units and has 15 siblings;
    `projection.py` by 34 with 5; `dispatch.py` by 31 with 12.

    Claim disjointness is this driver's real concurrency guard, and `scripts/dispatch.py` refuses
    a second dispatch whose PATHS overlap a live claim. So a unit claiming `events.py` and needing
    to change something that now lives in `events_projection.py` has two exits and both are bad.
    Stage only what it claimed, and it writes logic back into a re-export manifest. Edit the
    sibling it actually needs, and it edits a path no claim covers -- where two units that look
    disjoint (`events.py` and `projection.py`) collide inside a file neither of them named, with
    nothing to detect it.

    Expanding here rather than in the plan, or in `coordination.paths_overlap`:

      * The plan would go stale again at the next split. This reads the tree, so it is correct
        for whatever the tree currently is.
      * `paths_overlap` is a path primitive whose contract is "equality or containment at a path
        boundary". Teaching it that `a.py` and `a_b.py` are the same module would put Python
        naming conventions inside a general path function, and would widen every claim in the
        product, not just the ones this driver makes.

    Only an ENTRY POINT expands. A unit that claims `events_kinds.py` directly is taken at its
    word; widening that to the whole family would cost concurrency to protect a unit that already
    said precisely what it meant.
    """
    out: list[str] = []
    for claim in claims:
        out.append(claim)
        path = ROOT / claim
        if path.suffix != ".py":
            continue
        stem = path.stem
        # A sibling names an entry point that exists; that file is not itself an entry point.
        if "_" in stem and (path.parent / (stem.split("_")[0] + ".py")).is_file():
            continue
        out.extend(
            str(sibling.relative_to(ROOT)).replace("\\", "/")
            for sibling in sorted(path.parent.glob(stem + "_*.py"))
        )
    seen: set[str] = set()
    return [c for c in out if not (c in seen or seen.add(c))]


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


# WITHDRAWN 27 August 2026, hours after it landed. `resolver_can_change_nothing` skipped the
# resolver for any conflicted unit whose every CLAIMED PATH resolved in HEAD, on the reasoning that
# a conflict over work HEAD already carries needs a verdict rather than a merge.
#
# The predicate was wrong, and the driver already contained the right one. `artefact_identity`
# answers "do these paths exist", not "did this work arrive" -- Z03 is the counterexample:
# `.harness/build_loop.py` is present in HEAD, Z03's changes to it are not, and all six of its
# tests fail against the tree. `_content_landed` is the real question, and `retest_conflicts`
# already asks it EVERY TICK and pops the conflict when it is true.
#
# So by construction, a unit still sitting in `conflicts` after that retest has content that is
# NOT in HEAD and genuinely needs resolving. The skip withheld a resolver from precisely the units
# that needed one: 37 of 39, and zero commits merged in the 47 minutes it was live. [measured]
#
# What was right about the change is kept: resolvers now count against their own lane, and a
# finished dispatch releases its slot. Those fixed a real leak of 34 slots. This part fixed
# nothing and broke merging, and it is recorded here rather than deleted because a wrong turn
# taken for a plausible reason is worth the next reader's five seconds.


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


def _unit_added_line_hashes(uid: str) -> dict[str, list[str]]:
    """The lines this unit's own commits ADD, as short hashes, by path.

    Line hashes rather than the lines themselves for two reasons. Size: a unit adding 500 lines
    costs 8KB of driver state instead of tens of kilobytes of source. And provenance: the state
    file is instance data that gets copied into dispatch workspaces, and storing verbatim source
    there would put the same content in more places than it needs to be.

    Whitespace-insensitive at the ends only. In Python, indentation IS the language, so leading
    whitespace is kept -- `check_merge_acceptance` learned that the expensive way when a
    whitespace-normalising patch-id declared a moved statement identical to itself.
    """
    path = WORKTREES / uid
    if not path.exists():
        return {}
    head = sh(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
    if not head:
        return {}
    own = [
        ln.strip()
        for ln in sh(
            ["git", "rev-list", "--reverse", f"HEAD..{head}"]
        ).stdout.splitlines()
        if ln.strip()
    ]
    added: dict[str, list[str]] = {}
    for sha in own:
        show = sh(["git", "show", "--format=", "-U0", sha])
        if show.returncode != 0:
            continue
        current: str | None = None
        for line in show.stdout.splitlines():
            if line.startswith("+++ b/"):
                current = line[6:].strip()
            elif line.startswith("+") and not line.startswith("+++") and current:
                body = line[1:].rstrip()
                if body.strip():
                    added.setdefault(current, []).append(
                        hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
                    )
    return {p: sorted(set(v)) for p, v in added.items()}


def deliverable_present(deliverable: dict[str, list[str]] | None) -> bool:
    """Are this unit's own added lines still in HEAD?

    The retirement question, asked of the unit's OWN WORK rather than of every byte of every file
    it happens to touch. Another unit editing the same file elsewhere does not move this answer;
    deleting or rewriting THIS unit's lines does.

    The 99% floor and the twenty-line minimum are `_content_landed`'s, deliberately: two ways of
    asking "did this work land" that disagreed about how much drift is drift would be worse than
    either. Below twenty lines a diff cannot be told from a coincidence, so such a unit falls back
    to blob identity rather than being waved through on a weak signal.
    """
    if not deliverable:
        return False
    total = sum(len(v) for v in deliverable.values())
    if total < 20:
        return False
    absent = 0
    for file_path, wanted in deliverable.items():
        head = sh(["git", "show", f"HEAD:{file_path}"])
        blob = head.stdout if head.returncode == 0 else ""
        present = {
            hashlib.sha256(ln.rstrip().encode("utf-8")).hexdigest()[:16]
            for ln in blob.splitlines()
            if ln.strip()
        }
        absent += sum(1 for h in wanted if h not in present)
    return (total - absent) / total >= 0.99


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
        # BIND THE VERDICT TO THE UNIT'S OWN DIFF, NOT TO EVERY BYTE IT TOUCHES. ADR-0109.
        #
        # `artefact_identity` hashes every claimed blob, so a verdict died whenever ANY of those
        # files changed for ANY reason. MEASURED 27 August 2026: `src/consilient/events.py` is
        # claimed by 67 units, `projection.py` by 40, `dispatch.py` by 32. Every unit landing work
        # in events.py killed the standing SOUND verdict of the other 66, whose own work was
        # untouched. Ten verdicts were dead of this at once against six review slots, and the rate
        # rises as more units land -- verdicts were being invalidated faster than they could be
        # earned.
        #
        # A verdict now survives on the question the reviewer actually answered: is this unit's
        # deliverable present and sound. Someone else's unrelated edit to a shared file does not
        # move that. Deleting or rewriting THIS unit's lines does, and still invalidates it.
        deliverable = result.get("deliverable")
        if deliverable and deliverable_present(deliverable):
            retired.add(uid)
            continue
        # No recorded deliverable -- a verdict from before this existed, or a diff too small to
        # tell from coincidence. Fall back to the old binding rather than retiring on nothing.
        artefact = artefact_identity(units[uid])
        if artefact is not None and result.get("artefact") == artefact:
            retired.add(uid)
    return retired


_INFRASTRUCTURE_LOSS = frozenset(
    {
        "no_dispatch",
        "dispatch_refused",
        "dispatch_failed",
        "no_receipt_file",
        "receipt_unparseable",
        "receipt_mismatched",
    }
)
# MEASURED 26 August 2026: this set had only ever grown to two of the six outcomes its own
# neighbouring docstrings already named -- `clear_stale_review_memos` (below) and the comment
# in `consume_review_verdict` both list all six as infrastructure losses, but only
# "no_dispatch"/"dispatch_refused" were ever actually refunded. Two live units (AC, AT) had a
# real, well-formed verdict silently orphaned by this gap: AC's DEFECTIVE receipt arrived 37
# minutes after the driver had already given up and recorded `dispatch_failed`, spending a
# strike for a verdict that existed and was simply late; AT's reviewer reported SOUND but
# never produced a receipt at the WSL-translated path the brief demanded, and `no_receipt_file`
# spent a strike for a dispatch problem, not a code problem. Both escalated to a human on the
# strength of infrastructure noise, which is exactly what F-05 says must not happen.


def _outer_status(text: str) -> str:
    """Classify the dispatch envelope. Never reads a verdict out of stdout."""
    stripped = text.lstrip()
    if stripped.startswith("status:"):
        token = stripped.split(":", 1)[1].strip().split()[0].strip().rstrip(",")
        return token or "failed"
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return "failed"
    if not isinstance(obj, dict):
        return "failed"
    status = obj.get("status")
    if isinstance(status, str) and status:
        return status
    return "failed"


def _err_shows_refusal(uid: str) -> bool:
    err = BRIEFS / f"{uid}-verify.err"
    try:
        text = err.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "held by another process" in text or "status: refused" in text


def _load_verdict_file(
    uid: str, unit: dict[str, Any], expected: dict[str, Any]
) -> tuple[str, list[str]]:
    """Read `<uid>-verdict.json`. Fail closed; never scrape stdout for SOUND."""
    attempt = expected.get("attempt")
    artefact = expected.get("artefact")
    path = BRIEFS / f"{uid}-verdict.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return "no_receipt_file", []
    if not raw.strip():
        return "no_receipt_file", []
    try:
        inner = json.loads(raw)
    except json.JSONDecodeError:
        return "receipt_unparseable", []
    # IDENTITY IS THE ARTEFACT, NOT THE ATTEMPT NUMBER.
    #
    # MEASURED 25 August 2026, 20:18. Verdicts were being produced steadily and discarded almost
    # entirely -- nine of the ten most recent receipts were refused, including a SOUND for A03 and
    # DEFECTIVE verdicts for AL, AO and AJ. Two examples, receipt against expectation:
    #
    #   AL  artefact 3cfd3df7048c == expected 3cfd3df7048c, attempt 2 vs 3 -> receipt_mismatched
    #   AO  artefact b45304e972f0 == expected b45304e972f0, attempt 1 vs 2 -> check_error
    #
    # The artefact matched EXACTLY in both. Only the attempt counter differed, and that is enough
    # to throw the verdict away.
    #
    # The race: a review takes ~20 minutes, the driver's patience is shorter, so it gives up and
    # re-dispatches -- incrementing the attempt -- while the original agent is still alive. That
    # agent then finishes and writes a valid verdict about the CORRECT code, arriving one attempt
    # behind and refused for it. Because the pattern repeats every cycle, receipts are permanently
    # stale and essentially no review could ever be consumed. That is why nothing had been
    # verified for hours while agents worked continuously.
    #
    # The attempt number discriminates WHICH DISPATCH produced a receipt. It says nothing about
    # WHAT WAS JUDGED. `artefact` is the SHA-256 of the committed blobs of the unit's claimed
    # paths -- it is the whole of the binding, and it is checked twice below: the receipt must
    # match the expectation, AND the expectation must still equal the unit's identity re-derived
    # from the tree right now. A verdict that clears both is a verdict about exactly this code.
    #
    # So this is NOT a relaxed gate. The discriminator is unchanged and still checked on both
    # sides; a redundant bookkeeping equality that was destroying valid evidence is removed.
    #
    # The objection, stated rather than buried: an older reviewer's receipt could now be consumed
    # in place of the current reviewer's. What bounds it is that consumption only runs for units
    # whose `<uid>-verify.out` is non-empty, and dispatch writes that once, at completion -- so we
    # read the file only after the current review has finished. If an earlier agent's receipt is
    # what sits there, the current one produced none, and a real verdict about the right artefact
    # is better evidence than a check_error. The receipt's own attempt is recorded in the result
    # so the trail still shows which dispatch spoke.
    identity_ok = (
        isinstance(inner, dict)
        and inner.get("unit") == uid
        and inner.get("artefact") == artefact
        and isinstance(inner.get("attempt"), int)
        and artefact_identity(unit) == artefact
    )
    schema_ok = (
        isinstance(inner, dict)
        and set(inner) == {"v", "unit", "artefact", "attempt", "verdict", "findings"}
        and inner.get("v") == 1
        and inner.get("verdict") in {"SOUND", "DEFECTIVE"}
        and isinstance(inner.get("findings"), list)
        and all(
            isinstance(finding, str) and finding.strip()
            for finding in inner["findings"]
        )
        and not (inner.get("verdict") == "SOUND" and inner["findings"])
        and not (inner.get("verdict") == "DEFECTIVE" and not inner["findings"])
        and isinstance(attempt, int)
    )
    if schema_ok and identity_ok:
        return inner["verdict"], inner["findings"]
    if not schema_ok:
        return "receipt_unparseable", []
    return "receipt_mismatched", []


def _consume_review_receipt(
    uid: str, unit: dict[str, Any], expected: dict[str, Any]
) -> tuple[str, list[str]]:
    # A RECEIPT OUTRANKS THE ENVELOPE ONLY WHEN THE ENVELOPE IS SILENT -- never when the
    # wrapper made a DEFINITE statement about this dispatch.
    #
    # MEASURED 25 August 2026, 22:02, then corrected the same evening by a test that already
    # existed to guard exactly this: `test_json_refused_dispatch_is_dispatch_refused` writes a
    # dispatch envelope reporting `status: refused` (a claim collision -- the wrapper explicitly
    # declined to even launch a reviewer) ALONGSIDE a well-formed, identity-matching SOUND
    # receipt, and asserts the outcome is `dispatch_refused`. The first version of this fix broke
    # that test, because it tried the receipt unconditionally, before ever looking at the
    # envelope's status.
    #
    # The two cases are not the same shape and must not be treated alike. An EMPTY or ABSENT
    # envelope (AE, AA, A01, AB, AC) is genuinely ambiguous -- the wrapper may have died after the
    # reviewer had already finished and written its receipt, or nothing may have run at all, and
    # there is no way to tell from the envelope alone. A receipt IS the stronger evidence there,
    # because there is nothing to weigh it against. An envelope that explicitly reads "refused"
    # or any other non-"ok" status is NOT ambiguous: the wrapper is asserting, definitely, that
    # this dispatch never ran a legitimate review to completion. A receipt claiming otherwise for
    # that exact attempt is not stronger evidence than that assertion -- it is a contradiction of
    # it, and accepting the friendlier of two disagreeing signals is precisely the false accept
    # this project exists to measure. So a definite envelope status wins, unconditionally.
    #
    # Nothing else changes. `_load_verdict_file` still validates the schema and re-derives
    # artefact identity on both sides in every path that reaches it, so a verdict from an earlier
    # attempt about code that has since moved is still refused.
    out_path = BRIEFS / f"{uid}-verify.out"
    try:
        size = out_path.stat().st_size
        exists = True
    except OSError:
        size = 0
        exists = False

    if not exists or size == 0:
        early_outcome, early_findings = _load_verdict_file(uid, unit, expected)
        if early_outcome in ("SOUND", "DEFECTIVE"):
            return early_outcome, early_findings
        if _err_shows_refusal(uid):
            return "dispatch_refused", []
        return "no_dispatch", []

    try:
        text = out_path.read_text(encoding="utf-8")
    except OSError:
        return "no_dispatch", []
    status = _outer_status(text)
    if status == "refused":
        return "dispatch_refused", []
    if status != "ok":
        return "dispatch_failed", []
    return _load_verdict_file(uid, unit, expected)


def review_receipt_is_finished(uid: str, expected: dict[str, Any]) -> bool:
    """Is there real evidence THIS review attempt is done -- envelope, or a bound receipt?

    Two independent signals, either sufficient: `<uid>-verify.out` non-empty (the wrapper
    finished and wrote its report, once, at completion -- see `consume_review_verdict`'s own
    note on why that write is atomic), or `<uid>-verdict.json` present AND bound to the CURRENT
    expectation (this attempt's number and artefact).

    The second half of that AND is not optional. A non-empty verdict.json is not enough by
    itself -- it must be THIS attempt's receipt, or a stale one left by a PRIOR attempt
    satisfies this check the instant a re-dispatch truncates `.out`, before the new review has
    produced anything at all.

    MEASURED 25 August 2026, ~23:00, a REGRESSION introduced by the fix that first admitted
    verdict.json as a completion signal. `open(path, "w")` truncates `.out` to 0 bytes the
    moment `subprocess.Popen(stdout=vo)` opens it for a re-dispatch -- but nothing clears the
    OLD `<uid>-verdict.json` from the attempt before. A01, AB and AC were each re-dispatched at
    a fresh attempt=1 after their artefact changed; at that same tick, their STALE verdict.json
    (from a much earlier attempt, wrong artefact) still had bytes in it, so the old check fired
    immediately. `_load_verdict_file` correctly refused the mismatched identity, fell through to
    the freshly-truncated empty `.out`, and returned "no_dispatch" -- which
    `consume_review_verdict` memoises PERMANENTLY, before the real reviewer had even started.
    The eventual valid verdict, written minutes later, was never looked at again.

    So a verdict.json only counts as evidence THIS review finished if it is bound to the same
    attempt and artefact the driver is currently expecting. A leftover from a different attempt
    is not evidence about this one.
    """
    try:
        if (BRIEFS / f"{uid}-verify.out").stat().st_size > 0:
            return True
    except OSError:
        pass
    try:
        candidate = json.loads(
            (BRIEFS / f"{uid}-verdict.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(candidate, dict)
        and candidate.get("unit") == uid
        and candidate.get("attempt") == expected.get("attempt")
        and candidate.get("artefact") == expected.get("artefact")
    )


# MEASURED 26 August 2026: escalated under the two-outcome `_INFRASTRUCTURE_LOSS` gap fixed
# immediately above -- each reached 3 review attempts, but every one of those attempts was an
# infrastructure loss against an UNCHANGED artefact, not a genuine repeated defect:
#   AC  a well-formed DEFECTIVE receipt arrived 37 minutes after the driver had already given up
#       and recorded `dispatch_failed` for the same attempt.
#   AT  the reviewer's own stdout said "AT is SOUND", but the receipt never reached the
#       WSL-translated path the brief demanded, and the driver recorded `no_receipt_file`.
#   B01 a genuinely dead dispatch (silent envelope, no verdict) -- nothing recoverable, but
#       F-05 says an infrastructure death must not spend a retry regardless of whether
#       anything is recoverable from it.
# One-time, hardcoded migration for these three specific units, found by direct forensic
# reading of their receipt files -- `review_results` only retains the latest outcome per uid,
# so which of a unit's PAST attempts were infrastructure losses cannot be reconstructed from
# state alone. Safe to run every tick: a no-op once none of the three remain escalated.
_UNJUSTLY_ESCALATED = frozenset({"AC", "AT", "B01"})


def clear_unjustly_escalated_reviews(state: dict[str, Any]) -> list[str]:
    """Un-escalate units whose 3-attempt cap was reached entirely by infrastructure losses.

    See `_UNJUSTLY_ESCALATED` for the specific units and the forensic evidence for each.
    """
    cleared: list[str] = []
    escalated = state.setdefault("review_escalated", [])
    attempts = state.setdefault("review_attempts", {})
    for uid in _UNJUSTLY_ESCALATED:
        if uid in escalated:
            escalated.remove(uid)
            attempts[uid] = 0
            cleared.append(uid)
    return cleared


def clear_stale_review_memos(state: dict[str, Any], units: dict[str, Any]) -> list[str]:
    """Undo a memo written before outcome-gating existed. Returns the uids cleared.

    ONE-TIME MIGRATION, but safe to run every tick: a no-op once no stale non-terminal memo
    remains. `consume_review_verdict` used to memoise EVERY outcome, not only SOUND/DEFECTIVE.
    A memo recorded against a non-terminal outcome -- no_dispatch, dispatch_refused,
    dispatch_failed, receipt_unparseable, receipt_mismatched, no_receipt_file -- blocks a
    genuinely later, valid verdict for no reason: F-05 refunds an infrastructure loss's attempt
    counter precisely so it can be retried under the SAME (attempt, artefact) pair, and the old
    memo froze exactly that pair.

    MEASURED 25 August 2026, ~23:15, from the trajectory itself: A01's history reads
    `attempt=1 artefact=6e826... outcome=no_dispatch`, and the SAME pair was never looked at
    again even after a genuinely valid, matching receipt arrived minutes later. AB and AC were
    stuck the identical way.

    Re-adding a uid to `review_dispatched` cannot cause a double dispatch -- `pending_review`
    already excludes anything already in that set -- so this only widens what gets LOOKED AT,
    never what gets admitted to a fresh review.
    """
    cleared: list[str] = []
    consumed = state.setdefault("review_consumed", {})
    results = state.setdefault("review_results", {})
    dispatched = state.setdefault("review_dispatched", [])
    for uid, memo in list(consumed.items()):
        if not memo:
            continue
        if results.get(uid, {}).get("outcome") in ("SOUND", "DEFECTIVE"):
            continue
        consumed.pop(uid, None)
        if uid in units and uid not in dispatched:
            dispatched.append(uid)
        cleared.append(uid)
    return cleared


def consume_review_verdict(
    state: dict[str, Any], uid: str, unit: dict[str, Any]
) -> str:
    """Consume one strict reviewer receipt file; losses are typed, never collapsed."""
    expected = state.setdefault("review_expected", {}).get(uid)
    if not isinstance(expected, dict):
        expected = {}
    attempt = expected.get("attempt")
    artefact = expected.get("artefact")
    consumed = state.setdefault("review_consumed", {}).get(uid)
    if consumed == expected and expected:
        return "consumed"

    outcome, findings = _consume_review_receipt(uid, unit, expected)

    if outcome != "SOUND" and record_restart(state, uid, now=time.time()):
        print(
            "driver: ESCALATION -- "
            + uid
            + " exceeded the restart intensity limit. Auto-repair stopped; "
            "it needs a person."
        )
    if outcome in _INFRASTRUCTURE_LOSS:
        # MEASURED 25 August 2026. Empty and refused dispatches used to spend the review
        # cap, after which the driver refused to review those units ever again. An
        # infrastructure death is not evidence about the work, so it must not spend a retry.
        counter = state.setdefault("review_attempts", {})
        counter[uid] = max(0, counter.get(uid, 1) - 1)

    record = {
        "unit": uid,
        "artefact": artefact,
        "attempt": attempt,
        "outcome": outcome,
        "findings": findings,
    }
    append_review_outcome(record)
    # Memoise ONLY a terminal outcome. A verdict of SOUND or DEFECTIVE is a real, identity-bound
    # answer, and remembering it stops a re-dispatch of the SAME (attempt, artefact) pair from
    # double-applying it -- appending the outcome event twice, or double-adding to `done`.
    #
    # MEASURED 25 August 2026, ~23:15, via the trajectory itself: A01's history reads
    # `attempt=1 artefact=6e826... outcome=no_dispatch`, and the SAME (attempt, artefact) pair
    # was never looked at again, because this line used to fire for EVERY outcome. F-05 refunds
    # an infrastructure loss's attempt counter precisely so it can be retried WITHOUT a new
    # attempt number -- `no_dispatch`, `dispatch_refused` and `dispatch_failed` all take that
    # path -- so the retry re-enters `review_dispatched` under the IDENTICAL expected pair the
    # memo had already frozen. The retry's own genuine verdict, arriving later, was then refused
    # by the short-circuit at the top of this function before it was ever read.
    #
    # `review_dispatched` membership already governs whether a unit is looked at THIS tick, and
    # `review_receipt_is_finished` already governs WHEN a look is warranted; the memo add nothing
    # to safety for a non-terminal outcome, and actively discards a later, real one. So it is
    # written only for the two outcomes that cannot be improved on by waiting: SOUND, DEFECTIVE.
    if outcome in ("SOUND", "DEFECTIVE"):
        state["review_consumed"][uid] = expected
    # Carry the deliverable fingerprint from the dispatch record onto the verdict. `retired_units`
    # reads the RESULT, not the expectation, and the fingerprint cannot be re-derived once the
    # unit has merged -- `HEAD..worktree_head` is empty by then. If it does not travel here it is
    # lost exactly when it is needed. ADR-0109.
    if isinstance(expected, dict) and expected.get("deliverable"):
        record["deliverable"] = expected["deliverable"]
    state.setdefault("review_results", {})[uid] = record
    dispatched = state.setdefault("review_dispatched", [])
    if uid in dispatched:
        dispatched.remove(uid)
    if outcome == "SOUND":
        clear_quarantine_after_landed_check(state, uid)
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
        _refresh_worktree(uid, path)
        return path
    r = sh(["git", "worktree", "add", "--detach", str(path), "HEAD"])
    return path if r.returncode == 0 else None


def _refresh_worktree(uid: str, path: pathlib.Path) -> None:
    """Bring an existing unit worktree up to HEAD before anything is dispatched into it.

    A STALE WORKTREE REINTRODUCES EVERY BUG FIXED SINCE IT WAS CREATED, and the driver then
    reads the resulting crash as evidence about the unit rather than about the tree.

    MEASURED 25 August 2026. Unit worktrees sat at 0d088db for hours while HEAD carried the
    fencing-epoch fix. Dispatch runs with `--cwd <unit worktree>`, so every agent imported the
    OLD src/consilient/coordination.py and died with "fencing epoch 4 is stale; expected 1" --
    the exact defect that had been fixed and committed hours earlier. BM died that way eleven
    times and D02 nine, and both were escalated as "a defect, not bad luck", which was true but
    about the wrong thing. Forty worktrees were stale at once.

    Three refusals, and each of them protects work:

      * a DIRTY worktree is left alone -- an agent may be working in it right now, and its
        uncommitted work is not ours to discard;
      * a worktree holding COMMITS OF ITS OWN is left alone -- that is unmerged work and the
        merge path owns it;
      * anything else is reset to HEAD, which is a no-op when it is already there.

    This is deliberately the narrow version. Unit BN, "keep worktrees current and refuse
    concurrent duplicate-subsystem units", is the full treatment and is queued; that unit was
    itself stranded by the workspace bug, which is why this stopgap exists in the meantime.
    """
    head = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    if not head:
        return
    current = sh(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
    if not current or current == head:
        return
    dirty = [
        line
        for line in sh(
            ["git", "-C", str(path), "status", "--porcelain"]
        ).stdout.splitlines()
        if line.strip() and ".consilient-workspace-probe-" not in line
    ]
    if dirty:
        return
    own = sh(["git", "rev-list", "--count", f"{head}..{current}"]).stdout.strip()
    if own not in ("", "0"):
        return
    if sh(["git", "-C", str(path), "reset", "--hard", head]).returncode == 0:
        print(f"driver: refreshed {uid}'s worktree to {head[:9]} (was {current[:9]})")


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


def rebase_mergeable_worktrees(
    mergeable: list[str], state: dict, now: float, dispatchers_alive: int
) -> None:
    """Replay every unmerged worktree that no live dispatcher can still be writing."""
    for uid in mergeable:
        started, leash = state.get("in_flight", {}).get(uid, (0.0, 0.0))
        if now - started <= leash and dispatchers_alive:
            continue
        path = WORKTREES / uid
        head = sh(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()
        if not head:
            continue
        commits = [
            line
            for line in sh(
                ["git", "rev-list", "--reverse", f"HEAD..{head}"]
            ).stdout.splitlines()
            if line.strip()
        ]
        if not commits:
            continue
        if rebase_worktree(uid, path):
            print(
                f"driver: rebased {uid} onto HEAD ({len(commits)} commit(s) replayed)"
            )
        else:
            print(
                f"driver: rebase of {uid} failed "
                f"(0 of {len(commits)} commit(s) replayed)"
            )


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


def _content_landed(shas: str | list[str]) -> bool:
    """Are these commits' added lines already present in HEAD, line for line?

    Identity of WORK, not of commit message. A subject is not identity: 14 subjects recur in
    this repository's history and one recurs 24 times [measured 24 August 2026]. A patch-id is
    not identity either -- `git patch-id` normalises whitespace, and in Python whitespace is the
    language, so moving a statement into a loop preserves the patch-id while changing the
    meaning.

    Deliberately asymmetric: it asks only whether what the commit ADDS is present, not whether
    HEAD matches the commit. A unit whose work landed and was then built upon should still
    retire. The thresholds are the discriminator -- below twenty added lines a diff is too small
    to tell "landed" from "coincidentally similar", so it stays escalated rather than guessing.

    Indentation-sensitive, not just whitespace-sensitive [measured 26 August 2026]: comparing
    with `.strip()` on both sides discards LEADING whitespace too, so a commit that re-indents
    an existing block (moves it into a loop, a conditional, a different scope) reads as
    "already present" even though the code now means something else. Only trailing
    whitespace/newline is stripped here -- the same class of bug this repository already
    rejected for `git patch-id` in the docstring above.
    """
    if isinstance(shas, str):
        shas = [shas]
    added: dict[str, list[str]] = {}
    for sha in shas:
        show = sh(["git", "show", "--format=", "-U0", sha])
        if show.returncode != 0:
            continue
        path = None
        for line in show.stdout.splitlines():
            if line.startswith("+++ b/"):
                path = line[6:].strip()
            elif line.startswith("+") and not line.startswith("+++") and path:
                body = line[1:].rstrip()
                if body.strip():
                    added.setdefault(path, []).append(body)
    total = sum(len(v) for v in added.values())
    if total < 20:
        return False
    absent = 0
    for file_path, lines in added.items():
        head = sh(["git", "show", f"HEAD:{file_path}"])
        blob = head.stdout if head.returncode == 0 else ""
        present = {ln.rstrip() for ln in blob.splitlines()}
        absent += sum(1 for ln in lines if ln not in present)
    return (total - absent) / total >= 0.99


def _cherry_and_diff_match(worktree_head: str, touched: list[str]) -> bool:
    """Cheap first rung: patch already upstream AND the touched paths match HEAD.

    `git cherry` alone must never retire a unit. patch-id normalises whitespace, and in
    Python whitespace is the language. Both halves are required.
    """
    if not worktree_head or not touched:
        return False
    # A worktree sitting EXACTLY at HEAD has done nothing; it has not "already landed".
    #
    # MEASURED 25 August 2026. Both halves of this check pass trivially when the two trees are
    # the same commit: `git cherry HEAD <head>` prints nothing, so no line starts with "+", and
    # `git diff --quiet <head> HEAD` exits 0 because there is no difference. The function then
    # reports the unit's work as present in HEAD. What it actually observed is the unit having
    # no work at all.
    #
    # That is not a hypothetical window. `_refresh_worktree` resets a unit worktree to HEAD
    # every tick whenever it is clean and carries no commits of its own, so a conflicted unit
    # is routinely sitting at exactly HEAD when `retest_conflicts` runs. BN was reported
    # "already landed -- its added lines are present in HEAD; retiring" while
    # `rebase_mergeable_worktrees` and `SUBSYSTEM_JACCARD_THRESHOLD` were both absent from HEAD,
    # and the unit was dropped from `conflicts` so the driver stopped trying to merge its work.
    #
    # A gate accepting an artefact that is not there is a FALSE ACCEPT -- the quantity this
    # repository exists to measure -- and it was arriving through the cheapest rung of the
    # cheapest check. Emptiness is not evidence of completion.
    head_sha = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    if head_sha and worktree_head.startswith(head_sha[:12]):
        return False
    if head_sha and head_sha.startswith(worktree_head[:12]):
        return False
    cherry = sh(["git", "cherry", "HEAD", worktree_head])
    if cherry.returncode != 0:
        return False
    if any(line.startswith("+") for line in cherry.stdout.splitlines()):
        return False
    diff = sh(["git", "diff", "--quiet", worktree_head, "HEAD", "--", *touched])
    return diff.returncode == 0


def _unit_own_shas(
    uid: str, fallback_sha: str
) -> tuple[str | None, list[str], list[str]]:
    """The unit's own commits, preferring the worktree head over the conflict sha."""
    worktree = WORKTREES / uid
    head = fallback_sha
    if worktree.exists():
        resolved = sh(["git", "-C", str(worktree), "rev-parse", "HEAD"]).stdout.strip()
        if resolved:
            head = resolved
    own = [
        line.strip()
        for line in sh(
            ["git", "rev-list", "--reverse", f"HEAD..{head}"]
        ).stdout.splitlines()
        if line.strip()
    ]
    if not own and fallback_sha:
        own = [fallback_sha]
    touched: list[str] = []
    seen: set[str] = set()
    for sha in own:
        for line in sh(
            ["git", "show", "--name-only", "--format=", sha]
        ).stdout.splitlines():
            path = line.strip()
            if path and path not in seen:
                seen.add(path)
                touched.append(path)
    worktree_head = head if (WORKTREES / uid).exists() else None
    return worktree_head, own, touched


def _dispatch_output_age(stem: str, now: float) -> float | None:
    """Seconds since this dispatch last wrote anything, or None if it never wrote at all.

    The dispatcher streams into `<stem>.out` and `<stem>.err` while it runs, so the newest of
    the two is the last moment the run is known to have existed. That is an artefact, which is
    what this driver is required to judge by -- a process table says only whether something with
    that name is running now, and every silent failure here has been a run that started, died,
    and left the scheduler reporting success.
    """
    newest = None
    for ext in (".out", ".err"):
        try:
            mtime = (BRIEFS / f"{stem}{ext}").stat().st_mtime
        except OSError:
            continue
        newest = mtime if newest is None else max(newest, mtime)
    return None if newest is None else now - newest


def expire_finished_dispatches(
    state: dict,
    bucket_key: str = "resolve_dispatched",
    started_key: str = "resolve_started",
    stem_suffix: str = "-resolve",
    now: float | None = None,
) -> list[str]:
    """Release a dispatch slot whose run is over, however it ended.

    A `resolve_dispatched` entry was only ever removed on two paths: the unit's conflict
    clearing, or `crashed_dispatches` finding the run dead. A resolver that ran, failed to fix
    the conflict, and exited CLEANLY matched neither -- so its entry stayed for ever.

    MEASURED 27 August 2026: 34 entries against roughly nine live dispatch processes in total,
    builds and reviews included. Every one of those 34 units was therefore permanently barred
    from re-dispatch by `uid in resolving`, and once resolvers began counting against their own
    lane the stale entries alone exceeded MAX_BUILDS -- so the loop broke before examining
    anything, and the two units that genuinely needed a resolver could not get one either.

    This is the Y02 lesson in a second bucket, and this file already states it: stopping the
    retries is right, leaking the capacity is not. Builds record `(started, leash)` in
    `in_flight` and expire on it; resolves recorded a name and nothing else, so there was no
    fact to expire against. Now they record the same pair.

    Grace matches `crashed_dispatches`: a dispatch is not late until its leash plus 300s has
    passed, so a slow-but-living dispatch is never reaped out from under itself.

    REVIEWS HAD IT WORSE, and that is why this takes the bucket as a parameter. Measured the
    same day: four entries in `review_dispatched` whose newest output was 36, 36, 45 and 50
    HOURS old, against a lane capped at six. Two thirds of the review lane was held by runs
    that ended two days earlier, while 76 units waited for a verdict -- and the review lane
    is what decides a unit, so this was the single largest brake on the pipeline.

    `crashed_dispatches` could not see them. It defines death as `<stem>.err` carrying a
    traceback, which finds a dispatch that CRASHED and never one that simply stopped
    existing -- killed, cut off with the machine, or exited quietly after doing nothing. An
    empty `.err` reads exactly like a healthy run. Time is the signal that does not depend on
    the dead process having written its own death certificate.
    """
    now = time.time() if now is None else now
    started = state.setdefault(started_key, {})
    resolving = state.setdefault(bucket_key, [])
    expired = []
    for uid in list(resolving):
        when = started.get(uid)
        if when is None:
            # Recorded before this bookkeeping existed, so there is no start time to expire
            # against. ASK THE ARTEFACT rather than guessing either way: the dispatch's own
            # `.out`/`.err` are written as it runs, so an output file older than a full leash is
            # positive evidence the run is over -- not merely an absence of evidence.
            #
            # This matters because the alternative was a blind adoption at `now`, which would
            # have held 38 slots for a further hour on entries whose newest output was already
            # 32 and 50 HOURS old. Where the artefact says nothing at all, adoption is still the
            # safe answer: unknown is not known-dead, and cancelling a live run is worse than
            # waiting one leash for certainty.
            age = _dispatch_output_age(uid + stem_suffix, now)
            if age is not None and age > RESOLVE_ADOPTED_LEASH_S + 300:
                resolving.remove(uid)
                expired.append(uid)
            else:
                started[uid] = [now, RESOLVE_ADOPTED_LEASH_S]
            continue
        try:
            begun, leash = float(when[0]), float(when[1])
        except (TypeError, ValueError, IndexError):
            started[uid] = [now, RESOLVE_ADOPTED_LEASH_S]
            continue
        # A DISPATCH CANNOT HAVE LAST WRITTEN OUTPUT BEFORE IT STARTED. When the artefact is
        # older than the recorded start, that start is not a dispatch time -- it is an adoption
        # this function performed on an entry that had none, and adopting is a guess where the
        # artefact is evidence.
        #
        # MEASURED 27 August 2026: the tick that first ran this reaper stamped 34 resolve entries
        # at `now` before the artefact check existed, so they read as "started 47 minutes ago"
        # while their own output was 32 HOURS old. Without this they would hold their slots for a
        # further full leash on the strength of a timestamp the reaper itself invented.
        age = _dispatch_output_age(uid + stem_suffix, now)
        if age is not None and age > now - begun:
            begun = now - age
        if now - begun > leash + 300:
            resolving.remove(uid)
            started.pop(uid, None)
            expired.append(uid)
    for uid in list(started):
        if uid not in resolving:
            started.pop(uid, None)
    return expired


def clear_retired_conflicts(state: dict) -> None:
    """A conflict entry is re-earned each tick. Retirement clears it.

    K01 sat in force_done and on the escalation banner at once because only the
    re-test loop popped conflicts [measured 24 August 2026].
    """
    retired: set[str] = set()
    for key in ("force_done", "done", "built"):
        value = state.get(key) or []
        if isinstance(value, list):
            retired.update(str(item) for item in value)
    conflicts = state.get("conflicts")
    if not isinstance(conflicts, dict):
        return
    for uid in list(conflicts):
        if uid in retired:
            conflicts.pop(uid, None)


def retest_conflicts(state: dict) -> int:
    """Re-earn every escalation. Return how many retired as already-landed."""
    conflicts = state.setdefault("conflicts", {})
    if not isinstance(conflicts, dict):
        return 0
    retired_without_review = 0
    for uid, why in sorted(list(conflicts.items())):
        match = re.search(r"cherry-picking ([0-9a-f]{7,40})", why or "")
        if match:
            sha = match.group(1)
        else:
            # A GATE-FAILURE conflict records no sha. Its reason reads
            # "gate failed for X after cherry-pick", so the regex above misses it and the
            # unit was skipped by `continue` -- never re-tested, and therefore unable to
            # clear however clean it became.
            #
            # MEASURED 28 August 2026: six units -- A01, AC, AV, BC, W10, Y06 -- had ZERO
            # conflicting commits and merged perfectly. Their cherry-pick had SUCCEEDED and
            # the suite had failed afterwards, mostly on the six knowledge tests that fail
            # in any worktree lacking the gitignored declaration. They sat unreachable
            # while the whole pipeline reported 31/147 done for thirteen ticks.
            #
            # A gate failure is a statement about the SUITE at a moment in time, not about
            # the merge, so it must be re-earned like every other conflict. The unit's own
            # head is the right thing to re-test it against.
            head = sh(
                ["git", "-C", str(WORKTREES / uid), "rev-parse", "HEAD"]
            ).stdout.strip()
            if not head:
                continue
            sha = head
        if sh(["git", "merge-base", "--is-ancestor", sha, "HEAD"]).returncode == 0:
            conflicts.pop(uid, None)
            print(f"driver: {uid} conflict cleared -- already in the tree")
            continue
        worktree_head, own, touched = _unit_own_shas(uid, sha)
        landed = _content_landed(own)
        if not landed and worktree_head is not None:
            landed = _cherry_and_diff_match(worktree_head, touched)
        if landed:
            conflicts.pop(uid, None)
            built = state.setdefault("built", [])
            if uid not in built:
                built.append(uid)
            if uid in state.setdefault("resolve_dispatched", []):
                state["resolve_dispatched"].remove(uid)
            print(
                f"driver: {uid} already landed -- its added lines are present in HEAD; retiring"
            )
            retired_without_review += 1
            continue
        # BOTH the recorded sha AND the worktree's CURRENT head.
        #
        # MEASURED 28 August 2026, and this is why resolution never worked. The check used
        # to test only `sha` -- the commit that conflicted when the conflict was RECORDED.
        # A resolver's whole job is to add commits that make the unit merge, so its work is
        # by definition not in that sha, and the check could never see it. 217 resolve
        # dispatches ran and not one conflict ever cleared.
        #
        # Measured at the moment of the fix: AA, AF and Q02 all merged CLEANLY at their
        # worktree head while the stale sha they were recorded against still showed 29
        # conflicts. Three finished resolutions sat unnoticed while seven resolvers held
        # the build lane and thirteen consecutive ticks reported an identical
        # 31/147 done, 8 ready, 53 blocked.
        #
        # Clearing a conflict does not merge anything -- it lets the merge be ATTEMPTED,
        # and that attempt is still gated on the suite and on mypy. So a resolver that only
        # thinks it succeeded costs one gated attempt, not a bad merge.
        # SCOPE, corrected the same night it was introduced. The first version of this
        # loop tested the worktree head alone -- `--merge-base=head^ HEAD head` -- which is
        # ONE commit, while `merge_unit_worktree` cherry-picks EVERY commit in
        # `HEAD..head`. AA, AF and Q02 passed the one-commit test and then failed the real
        # cherry-pick on ddbf0f556, an earlier commit in their own range that deletes 54
        # files including .harness/build_driver.py and whole test files still present in
        # HEAD. They cleared and re-conflicted on every tick, burning a merge attempt each
        # time. The refusal was right; my check was measuring the wrong thing.
        #
        # So the head only counts as clear when EVERY commit the merge would replay is
        # clear. Conservative in the safe direction: sequential cherry-picks can conflict
        # even when each is individually clean against HEAD, so this can still be
        # optimistic -- but it can no longer wave through a range containing a commit that
        # visibly conflicts on its own.
        candidates = [sha]
        if worktree_head:
            own_range = [
                ln.strip()
                for ln in sh(
                    ["git", "rev-list", "--reverse", f"HEAD..{worktree_head}"]
                ).stdout.splitlines()
                if ln.strip()
            ]
            if own_range and all(
                sh(
                    [
                        "git",
                        "merge-tree",
                        "--write-tree",
                        "--name-only",
                        f"--merge-base={c}^",
                        "HEAD",
                        c,
                    ]
                ).stdout.count("CONFLICT")
                == 0
                for c in own_range
            ):
                candidates.append(worktree_head)
        for candidate in candidates:
            if not candidate:
                continue
            tree = sh(
                [
                    "git",
                    "merge-tree",
                    "--write-tree",
                    "--name-only",
                    f"--merge-base={candidate}^",
                    "HEAD",
                    candidate,
                ]
            )
            if tree.returncode == 0 and tree.stdout.count("CONFLICT") == 0:
                conflicts.pop(uid, None)
                if uid in state.setdefault("resolve_dispatched", []):
                    state["resolve_dispatched"].remove(uid)
                how = (
                    "it merges cleanly against current HEAD"
                    if candidate == sha
                    else "the resolver's own commits merge cleanly against current HEAD"
                )
                print(f"driver: {uid} conflict cleared -- {how}")
                break
    return retired_without_review


def _mypy_error_count(text: str) -> int:
    return text.count(": error:")


def _mypy_gate(python_files: list[str], baseline: str) -> str | None:
    """mypy on `python_files`, refusing only a genuine increase over `baseline`.

    MEASURED 26 August 2026: a bare zero-tolerance mypy check meant ANY commit touching a file
    carrying pre-existing type debt could never pass this gate, regardless of whether the commit
    fixed the debt, worsened it, or never touched the offending lines at all. build_driver.py
    itself carries roughly 87 long-accepted mypy errors (untyped `sh()` calls, bare `dict`
    generics -- an established, tracked pattern all through this build, never a surprise). BO's
    own merge-event-recording fix was refused by this exact gate despite a by-hand check showing
    its error delta was zero (verified: only +3 calls to the same already-accepted untyped `sh()`
    pattern). A gate that can never pass for a file is not a gate -- it is a permanent block, the
    same class of failure this function already names for `.gitignore`-as-Python.

    `baseline` is materialised via a real `git worktree add` rather than loose file copies in a
    scratch directory, so mypy's own import resolution (`mypy_path = src`, cross-module checks)
    sees a genuine checkout and not a directory structure that never existed. Only invoked when
    the plain mypy check already failed, so a clean file pays no extra cost.
    """
    after = sh(
        [sys.executable, "-m", "mypy", "--config-file", "mypy.ini", *python_files]
    )
    if after.returncode == 0:
        return None
    after_text = (after.stdout or "") + (after.stderr or "")
    after_count = _mypy_error_count(after_text)
    scratch = ROOT / ".harness" / f"gate-baseline-{uuid.uuid4().hex[:8]}"
    added = sh(["git", "worktree", "add", "--detach", str(scratch), baseline])
    if added.returncode != 0:
        # Can't establish a baseline -- fail closed on the original zero-tolerance result rather
        # than silently letting anything through.
        return after_text.strip() or " ".join(
            [sys.executable, "-m", "mypy", "--config-file", "mypy.ini", *python_files]
        )
    try:
        before_files = [
            str(scratch / path) for path in python_files if (scratch / path).exists()
        ]
        before_count = 0
        if before_files:
            before_ini = scratch / "mypy.ini"
            config = str(before_ini) if before_ini.exists() else "mypy.ini"
            before = sh(
                [sys.executable, "-m", "mypy", "--config-file", config, *before_files]
            )
            before_count = _mypy_error_count(
                (before.stdout or "") + (before.stderr or "")
            )
        if after_count > before_count:
            return (
                f"mypy regressed on {', '.join(python_files)}: {before_count} error(s) at "
                f"{baseline} -> {after_count} now\n{after_text.strip()}"
            )
        return None
    finally:
        removed = sh(["git", "worktree", "remove", "--force", str(scratch)])
        if removed.returncode != 0:
            shutil.rmtree(scratch, ignore_errors=True)


def gate_merged_tree(touched: list[str], baseline: str) -> str | None:
    """Run the existing merge gate on the files this cherry-pick touched.

    Scoped to `touched` so a pre-existing red file does not block an unrelated merge.
    mypy is invoked with `--config-file mypy.ini`, never bare `--strict`: warn_unreachable
    lives in the ini [measured 24 August 2026, T01 specimen]. `baseline` is the tree this
    cherry-pick started from -- `_mypy_gate` compares against it rather than demanding zero
    errors, so a file's pre-existing debt does not permanently block every future merge to it.
    """
    existing = [path for path in touched if path and (ROOT / path).exists()]
    if not existing:
        return None
    # ruff and mypy are PYTHON tools and must only be handed Python.
    #
    # MEASURED 25 August 2026: a cherry-pick that touched `.gitignore` had it passed straight to
    # `ruff check`, which parsed it as a module and reported `invalid-syntax: Expected an
    # expression` on the glob patterns -- 129 errors, non-zero exit, merge REFUSED. The commit
    # was fine. The gate was reading a gitignore as a syntax error, and the units it blocked
    # hardest were the harness-cleanup ones, because those are the commits that touch
    # `.gitignore`.
    #
    # A gate that refuses correct work is worse than no gate: it is indistinguishable from the
    # work being wrong, and it teaches everyone to route around the gate.
    python_files = [path for path in existing if path.endswith(".py")]
    checks: list[list[str]] = []
    if python_files:
        checks.append(["ruff", "check", *python_files])
    acceptance = ROOT / ".github" / "scripts" / "check_merge_acceptance.py"
    if acceptance.is_file():
        checks.append([sys.executable, str(acceptance), "--files", *existing])
    for command in checks:
        result = sh(command)
        if result.returncode != 0:
            output = ((result.stdout or "") + (result.stderr or "")).strip()
            return output or " ".join(command)
    if python_files:
        mypy_fail = _mypy_gate(python_files, baseline)
        if mypy_fail:
            return mypy_fail
    return None


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
            release_dead_claims({uid})
            if record_restart(state, uid, now=now):
                print(
                    "driver: ESCALATION -- "
                    + uid
                    + " exceeded the restart intensity limit. Auto-repair stopped; "
                    "it needs a person."
                )
            attempts = state.setdefault("attempts", {})
            attempts[uid] = max(0, attempts.get(uid, 1) - 1)
            freed.append(uid + ("" if expired else " (silent)"))
    return sorted(freed)


# Domains reserved by RFC 2606 and RFC 6761 precisely so that they can never belong to anyone.
# An address in one of these cannot certify the origin of anything, because there is nobody to
# certify it.
UNCERTIFIABLE_DOMAINS = (
    "example.com",
    "example.net",
    "example.org",
    "example",
    "invalid",
    "test",
    "localhost",
)


def _identity_cannot_certify(signer: str) -> bool:
    """Whether a sign-off identity is a fixture rather than a person.

    MEASURED 29 August 2026, and this widening is the repair for a near miss. The check here
    was `"fixture" in signer or ".invalid" in signer`, and it was found looking at the identity
    this worktree's LOCAL git config actually held at the time:

        Test <t@example.com>

    which contains neither substring. `tests/test_supervision.py` and its siblings write a
    fixture identity into a local config, the override had leaked into the real worktree, and
    every commit made that day was authored by it. The guard would have passed, `commit-tree`
    would have taken that identity, and a squash certifying the origin of 376 commits would
    have been filed in public over an address that resolves to nobody.

    The two spellings the old check knew were the two that had been seen. Reserved domains are
    the property the check was reaching for, so test the property.
    """
    lowered = signer.lower()
    if "fixture" in lowered:
        return True
    # The DOMAIN is the property, so extract it rather than matching substrings against the
    # whole line. A substring test cuts both ways: ".localhost" misses the bare `a@localhost`,
    # and a bare "example" would refuse a real company such as examples-ltd.co.uk.
    if "@" not in lowered:
        return False
    domain = lowered.rsplit("@", 1)[1].split(">")[0].strip().rstrip(".")
    return domain in UNCERTIFIABLE_DOMAINS or any(
        domain.endswith("." + reserved) for reserved in UNCERTIFIABLE_DOMAINS
    )


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
    # minutes and starved the scheduler of the thing it exists to do.
    #
    # But `green is None` used to RETURN here, on the reasoning that "there is nothing newly
    # retired and nothing new to publish either". That premise is false and the measurement says
    # so: on 24 August 2026 this printed "publish held: 112 commit(s) ready, suite not evaluated
    # this tick" on tick after tick, while `ahead` climbed 109 -> 110 -> 112. Commits reach HEAD
    # by paths that have nothing to do with unit registration -- merges, conflict resolutions and
    # the orchestrator's own fixes -- so a tick can have plenty to publish and still never touch
    # the registration loop that happens to compute `green`.
    #
    # Publication was therefore gated on an unrelated side effect, and public sat hours behind
    # for want of a suite run nobody had asked for. Evaluate it here when, and only when, there
    # is something to push. That is still at most one suite run per tick, because a tick that
    # already computed `green` reuses it.
    if green is None:
        green = suite_green()
    if not green:
        return f"publish held: {ahead} commit(s) ready, suite not green"
    # MEASURED 27 August 2026. This list had four entries and the `pre-push` hook runs FIVE --
    # it also runs `check_private_repo_names`, the ratchet on unpinned private-repository names.
    # So the driver's pre-flight could report every gate passing on a tree the hook would then
    # refuse, which is exactly what happened: a push of 294 commits was declined on a new file
    # in `docs/10-research/` that this list could not see. A pre-flight that is weaker than the
    # thing it is a pre-flight for is not a pre-flight; it is a second opinion that always
    # agrees. Any gate the hook runs belongs here.
    gates = [
        (".github/scripts/check_foreign_identifiers.py", []),
        (".github/scripts/check_secrets.py", []),
        (".github/scripts/check_private_corpus.py", ["--require-corpora"]),
        (".github/scripts/check_private_repo_names.py", []),
        (".github/scripts/check_generated_documents.py", ["--check"]),
    ]
    for script, args in gates:
        path = ROOT / script
        if not path.is_file():
            return f"publish held: {script} is missing"
        if sh([sys.executable, str(path), *args]).returncode != 0:
            return f"publish REFUSED: {pathlib.Path(script).name} failed"
    # PUBLISH A SQUASH, NEVER THE BRANCH.
    #
    # MEASURED 27 August 2026. This read `git push public HEAD:main`, and what that would have
    # sent was 294 commits of which 275 carried a `Signed-off-by` naming
    # `fixture@example.invalid` -- an RFC 2606 address that resolves to nobody -- and 240 had no
    # sign-off matching their author at all. The cause was this worktree's LOCAL git config,
    # which `tests/test_supervision.py` had written a fixture identity into. CONTRIBUTING.md
    # requires a real name and email and the DCO workflow requires the sign-off to match the
    # author, so that push would have filed 240 false certifications of origin in public.
    #
    # Correcting the commits in place was measured and rejected: 283 of this repository's 635
    # refs are based inside the unpublished range and 455 worktrees are checked out against
    # them, so rewriting orphans the build. The `pre-push` hook already records the alternative
    # from the 21 August 2026 audit -- publish a squashed commit rather than the history -- and
    # it costs nothing here, because what is being published is the tree, and the tree is
    # identical either way.
    #
    # `commit-tree` takes the CONFIGURED identity, which is also what the sign-off names, so
    # author, committer and certification agree by construction rather than by discipline. The
    # `-s ours` merge afterwards keeps `public/main` an ancestor, so the next `ahead` count is
    # honest; without it every later tick recomputes against a public/main it does not contain.
    ident = sh(["git", "var", "GIT_AUTHOR_IDENT"]).stdout.strip()
    signer = ident.rsplit(">", 1)[0] + ">" if ">" in ident else ""
    if not signer:
        return "publish held: no git identity configured to sign off with"
    if _identity_cannot_certify(signer):
        return f"publish REFUSED: identity {signer!r} cannot certify origin"
    message = "\n".join(
        [
            f"publish: {ahead} commit(s) of harness work, squashed for an honest sign-off",
            "",
            "Squashed rather than fast-forwarded so that every published commit carries a",
            "sign-off matching its author. The granular history is not lost, it stays in the",
            "work repository; what travels is the tree, and one certification that is true.",
            "",
            f"Signed-off-by: {signer}",
            "",
        ]
    )
    squash = sh(
        ["git", "commit-tree", "HEAD^{tree}", "-p", "public/main", "-m", message]
    ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", squash):
        return "publish FAILED: could not build the squash commit"
    result = sh(["git", "push", "public", f"{squash}:main"])
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip().splitlines()
        return f"publish FAILED: {tail[-1] if tail else 'unknown'}"
    merged = sh(
        [
            "git",
            "merge",
            "-s",
            "ours",
            "--no-ff",
            squash,
            "-m",
            "record the published squash as an ancestor",
        ]
    )
    if merged.returncode != 0:
        # Published, but the ancestry record failed. Say so plainly rather than reporting a
        # clean publish: until that merge lands, every later tick computes `ahead` against a
        # public/main this branch does not contain and tries to publish everything again.
        return (
            f"published {ahead} commit(s) to public as {squash[:9]}, but recording it as an "
            "ancestor FAILED -- the next tick will over-count; merge it by hand"
        )
    return f"published {ahead} commit(s) to public as {squash[:9]}"


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
            # A CRASH IS EVIDENCE ONCE, NOT ONCE PER TICK.
            #
            # This reads `<stem>.err` from disk, and that file persists until the NEXT dispatch
            # for the same unit overwrites it. So every tick re-read the same stale traceback
            # and reported it as a fresh death. MEASURED 25 August 2026: driver state recorded
            # 4,531 "crashes" across 99 units, with AL at 102 and AJ at 95 -- those are TICK
            # COUNTS, not failures. A monitor caught the same run ids being re-reported with
            # nothing but the elapsed seconds changing.
            #
            # It is not merely noisy. The three-identical-deaths rule stops auto-repair and
            # escalates "this is a defect, not bad luck" -- so a single historical crash, re-read
            # three times, permanently escalated a unit and took it out of the retry pool. Units
            # were escalated on evidence that was one event wearing many hats, which is the same
            # false-accept shape this repository exists to detect, in its own supervisor.
            #
            # Identity is (stem, mtime, size): a NEW crash rewrites the file and is counted, an
            # unchanged file is the crash already counted. Recorded in state so it survives the
            # tick, and pruned to the watched set so it cannot grow without bound.
            try:
                stat = err.stat()
                fingerprint = f"{stem}:{int(stat.st_mtime)}:{stat.st_size}"
            except OSError:
                fingerprint = None
            counted = state.setdefault("crash_counted", {})
            if fingerprint is not None:
                if counted.get(stem) == fingerprint:
                    break
                counted[stem] = fingerprint
            dead.append((uid, lines[-1] if lines else "unknown failure", refused))
            break
    counted = state.setdefault("crash_counted", {})
    for stem in list(counted):
        if stem.split("-")[0] not in watched:
            counted.pop(stem, None)
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


def merge_unit_worktree(uid: str) -> str:
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

    pre_sha = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    post_pick_sha = pre_sha
    applied = 0
    already = 0
    for sha in own:
        # DCO requires a `Signed-off-by:` trailer on every commit that reaches `main`, and a
        # dispatched worker's own commit is not guaranteed to carry one -- the workers run
        # arbitrary shells across several harnesses, and asking each one to remember `--signoff`
        # is a prompt-level fix the Engineering Ratchet rejects. This is the one chokepoint every
        # unit's work must pass through before landing, so the sign-off is stamped here instead:
        # `--signoff` adds a trailer for the CURRENTLY CONFIGURED identity (the one performing the
        # merge), which DCO accepts alongside the original author already preserved by cherry-pick.
        # [measured 26 August 2026] -- CI's "v0 invariants"/DCO check failed on every recent push
        # with "no sign-off found" for that exact reason.
        # NO `--allow-empty`. MEASURED 27 August 2026 against real git. The flag does not do
        # what it was assumed to: a commit whose CONTENT is already in HEAD still exits
        # non-zero with "the previous cherry-pick is now empty" either way, and the branch
        # below handles it. What the flag actually permits is replaying a source commit that
        # was empty TO BEGIN WITH as a fresh empty commit, exit 0, counted as `applied`.
        # That case cannot terminate: the replay gets a new sha, so `HEAD..unit_head` still
        # lists the original next tick, and an empty commit leaves no content for git to
        # recognise as already present -- so it lands again, once per tick, forever. Two units
        # did exactly this; 189 of one 200-commit window were two zero-diff messages
        # repeating. Without the flag an empty source commit takes the already-applied path
        # and nothing lands, which is the honest outcome for a commit that changes nothing.
        r = sh(["git", "cherry-pick", "--signoff", "-x", sha])
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
            # The tick rebases every quiescent worktree before reaching this merge. A conflict
            # that survives that pass needs named escalation, not another hidden retry here.
            return f"CONFLICT cherry-picking {sha[:9]} for {uid} ({applied} applied); needs resolution"
        applied += 1
        post_pick_sha = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    if applied:
        gate_fail = gate_merged_tree(sorted(touched), pre_sha)
        if gate_fail:
            # `reset --hard pre_sha` discards EVERYTHING committed since pre_sha was read, not
            # only this unit's cherry-picks. That assumption -- nothing else commits to this
            # worktree during a merge -- is false, and the reflog proves it:
            #
            #   1deb5f1 HEAD@{0}: reset: moving to 1deb5f19d...
            #   1deb5f1 HEAD@{1}: reset: moving to 1deb5f19d...   (x5)
            #   084c174 HEAD@{5}: commit: fix(driver): quarantine blocked review ...
            #
            # MEASURED 25 August 2026: a commit made between `pre_sha` being read and the gate
            # failing was destroyed, repeatedly, by a rollback that had no business touching it.
            # The commit object survived in the reflog, so the loss was silent AND recoverable
            # only by someone who thought to look. Agents commit into this worktree too.
            #
            # So the rollback is now CONDITIONAL on the tree still being where we left it. If
            # HEAD has moved past our last cherry-pick, another writer got there first and their
            # work is not ours to throw away: leave the tree alone and report the gate failure.
            # The unit stays unmerged either way, which is the outcome the gate was asking for;
            # what changes is that it no longer takes bystanders with it.
            head_now = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
            if head_now and head_now != post_pick_sha:
                return (
                    f"CONFLICT gate failed for {uid} after cherry-pick, and HEAD moved to "
                    f"{head_now[:9]} while the gate ran -- refusing to roll back over "
                    "another writer's commit; needs resolution\n" + gate_fail
                )
            sh(["git", "reset", "--hard", pre_sha])
            return (
                f"CONFLICT gate failed for {uid} after cherry-pick; needs resolution\n"
                + gate_fail
            )
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
    claims = "\n".join(f"- `{c}`" for c in family_claims(unit["claims"]))
    # A unit's specification does not always live in docs/superpowers/plans/. The design work
    # of 23 August 2026 specified units inside docs/20-design/ documents, and a brief
    # pointing at a path that does not exist sends the agent hunting instead of building.
    # A plan value containing a slash is taken as a path from the repository root.
    plan_ref = (
        unit["plan"]
        if "/" in unit["plan"]
        else "docs/superpowers/plans/" + unit["plan"]
    )
    receipt_path = BRIEFS / f"{uid}-verdict.json"
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
- Baseline **{suite_baseline_line()}**. Report the exact line.

## Report

For each of the six checks: pass, or the finding with its reproduction. **What you broke to test the
tests, and whether they caught it.** The incumbent and how this compares.

## Required machine receipt

Write this exact JSON object to `{receipt_path}`. That file is the receipt. Stdout is not the receipt:
it is truncated, wrapped differently by different harnesses, and invites prose. Do not wrap the
object in markdown and do not regex the word SOUND into a verdict. `findings` is empty for SOUND and
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
    claims = chr(10).join(f"- `{c}`" for c in family_claims(unit["claims"]))
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
    claims = "\n".join(f"- `{c}`" for c in family_claims(unit["claims"]))
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

- **Baseline is {suite_baseline_line()}.** None may fall. Report the exact suite line before and after.
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
# RESTORED to 24/12 on 25 August 2026. The reduction was a load-shed while ticks could not
# finish, and the reason they could not has been fixed at its root: a /mnt/c line in the
# shared .git/config broke `git worktree add`, so every dispatch fell through to a
# workspace form whose commits are unreachable, and work was being redone rather than
# landed. Redone work is what filled the machine. `self_heal` now runs per tick and the
# line cannot persist.
#
# The principal's standing instruction is to maximise parallelism and never constrain it.
# The shed was measured and temporary; this restores it. Z03 (checkpoint the tick, bound
# every subprocess) and Z06 (separate admission pools) remain the durable fixes and are
# queued -- if saturation recurs, the answer is those, not another quiet reduction.
# The principal's standing instruction is to maximise parallelism and never constrain it, and
# this does not contradict it: at 36 the system was completing NOTHING, so 36 was not
# parallelism, it was saturation past the knee.
#
# MEASURED at the moment of this change: 21 concurrent pytest processes, 27 dispatchers and 77
# node processes at TWENTY PERCENT CPU. Nothing was computing; everything was blocked on the
# shared trajectory's file locks. A driver tick that began at 09:31 was still in its publish
# suite at 10:03, and this repository has already measured the amplification directly -- nine
# concurrent pytest processes took the suite from 432 s to 961 s.
#
# That is the metastable state Huang et al. describe: goodput collapses and does not recover
# when the trigger is removed, because the queue itself sustains the load. Their remedy, and
# the only one that works, is to SHED LOAD. Throughput at 12 is higher than throughput at 36
# when throughput at 36 is zero.
#
# The real fixes are queued and are not this: Z06 gives builds and reviews separate admission
# pools so neither starves the other, and Z03 checkpoints the tick and bounds every subprocess
# so a killed one stops costing its whole tick. Both were blocked behind a dispatch path that
# could not start work; that is now fixed, so they can be built -- and this constant goes back
# to 24/12 when they land.
#
# 25 August 2026, 15:05: saturation recurred at 24/12, exactly as the paragraph above predicted,
# and the note above says the answer is Z03/Z06 rather than "another quiet reduction". It still
# is -- but neither can land while nothing completes, so the shed is what lets its own fix
# through. This one is not quiet: the number is measured, and the exit condition is written down.
#
# MEASURED from the dispatch cohorts of this day, counting a run as started only if it wrote a
# real artefact (scratchpad/cohort.py):
#     11:51  12 runs -> 100% started      11:22  31 runs ->   0% started
#     11:52  13 runs -> 100% started      11:38  31 runs ->   0% started
#     11:58  19 runs -> 100% started      13:21  30 runs ->  90% started
# The knee sits between 19 and 31. Twelve builds plus six reviews is 18 concurrent, inside the
# band that started every time, and it is a ceiling rather than a target.
#
# Corroborating, at the moment of this change: 658 agent processes on 32 cores, and the entire
# 14:21 cohort -- 26 dispatches -- alive for 40 minutes with agent CLIs spawned and ZERO bytes
# written. Not slow: producing nothing. 24/12 is not parallelism at that point, it is queueing.
#
# Z06 landed: the lanes are independent pools and a full lane sheds rather than
# borrowing. The ceilings stay at the measured 12/6. Restoring 24/12 would raise
# MAX_CONCURRENT past the knee this comment just measured (19–31), which is the
# remedy the unit forbids. Z03 still owns tick checkpointing and subprocess bounds.
# 19:30, same day: the SHAPE of the work changed, so the split follows it. The ceiling is
# unchanged at 18 -- the measured safe band is 12-19 concurrent and this stays inside it.
#
# MEASURED at this moment: 81 units BUILT and waiting on review or merge, against roughly 56
# not yet built, and 10 done. The queue is not short of things to build; it is short of things
# JUDGED. Ten more builds would add to a backlog that already dwarfs the review lane's ability
# to drain it, and a built-but-unverified unit retires nothing and unblocks nothing.
#
# The receipt work makes the shift worth making. Reviews used to return a usable verdict 32% of
# the time (24 of 76). Since `<uid>-verdict.json` landed, five dispatched reviews have produced
# six well-formed receipts -- three SOUND, three DEFECTIVE, every one of them usable. Review
# capacity converts to verdicts now, where before it largely converted to `check_error`, so
# capacity spent there is worth more than it was this morning.
#
# REVERT TO 12/6 if the review lane stops being the constraint -- that is, when `built` falls
# to the same order as the not-yet-built count. This is a ratio, not a preference.
# REVERTED to 12/6 at 20:50, same day. Z06's `test_ceilings_are_not_raised_to_paper_over_contention`
# is a TRACKED, landed invariant and it pins both constants exactly. Editing another unit's guard
# so my tuning fits is the gate-erosion move this repository exists to catch, so the tuning goes
# and the guard stays.
#
# The cost is real and worth recording: 81 units are built and waiting to be JUDGED against only
# six review slots, and review is the critical path. The rebalance to 8/10 kept the total at 18 --
# unchanged -- and only moved capacity to the starved lane.
#
# The tension is genuine rather than a mistake on either side. Z06's stated evidence is
# "degradation ~2.2 at n=9", which is about TOTAL concurrency and does not distinguish 12/6 from
# 8/10; it also sits oddly with Z06's own total of 18. Changing that invariant needs a unit or an
# ADR carrying the measurement, not a constant edited underneath it.
MAX_BUILDS = 12
MAX_REVIEWS = 6
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


def not_selected_reasons(units, landed, blocked, startable, selected):
    """Why each waiting unit was not selected this tick.

    Section 2.1's vocabulary is closed in events.py. This function only emits
    reasons it can observe: `blocked_on:<unit>` from an unmet dependency, and
    `no_capacity` for startable work that did not get a slot. `quota_exhausted`
    and `breaker_open` stay unused until a measured pool or breaker reading
    exists — ADR-0056 D3/D4 are inert until EXP-94, and inventing either reason
    from a brand name is the F-08 failure the record exists to catch.
    """
    chosen = set(selected)
    reasons = {}
    for uid in blocked:
        if uid in chosen:
            continue
        unmet = [dep for dep in units.get(uid, {}).get("deps", []) if dep not in landed]
        reasons[uid] = f"blocked_on:{unmet[0]}" if unmet else "no_capacity"
    for uid in startable:
        if uid in chosen:
            continue
        reasons[uid] = "no_capacity"
    return reasons


def shed_lane(outstanding: int, ceiling: int) -> bool:
    """True when this lane is at or over its own ceiling.

    A full lane sheds. It does not borrow the other lane's reserved slots.
    MAX_CONCURRENT is the documented sum of the two ceilings, not an admission
    pool — a safety property held only by that incidental constant is the
    defect this function exists to retire.
    """
    return outstanding >= ceiling


def admit_review(reviews_out: int) -> bool:
    return not shed_lane(reviews_out, MAX_REVIEWS)


RESOLVE_RESERVE = 3


def resolve_slots_reserved(conflicts, resolving) -> int:
    """How many build-lane slots to hold back for conflict resolution.

    MEASURED 28 August 2026. Resolvers were made to count against the build lane earlier the
    same night, which was right -- 34 of them had been running at once on a lane capped at 12,
    because the cap counted builds only. But the BUILD loop still admitted on `len(inflight)`
    alone, so builds filled all twelve slots first and resolvers only ever got what builds left
    over. With 116 units still to build there is always another build, so that remainder was
    zero: `done` sat at 31 for two hours while conflicts climbed 8 -> 16 and exactly one
    resolver ran.

    A conflict cannot clear itself, and every failed merge adds one, so a starved resolve lane
    is a pile that only grows. Reserving a few slots costs a little build throughput and is the
    difference between the pile draining and the pile being permanent.

    Nothing here raises a ceiling: MAX_BUILDS, MAX_REVIEWS and MAX_CONCURRENT are untouched.
    This partitions the existing lane, which is what the two-lane design already does between
    builds and reviews. Nothing is reserved when no conflict is waiting, so an unconflicted
    queue still gets the whole lane.
    """
    waiting = [u for u in (conflicts or {}) if u not in (resolving or [])]
    return min(RESOLVE_RESERVE, len(waiting))


def admit_build(builds_out: int) -> bool:
    return not shed_lane(builds_out, MAX_BUILDS)


def builds_outstanding(state: dict) -> int:
    return len(state.get("in_flight", {}))


def reviews_outstanding(state: dict) -> int:
    return len(state.get("review_dispatched", []))


def choose_selected(startable, live):
    """Who this tick will spawn from the build lane's own remaining slots."""
    slots = max(0, MAX_BUILDS - live)
    return list(startable[:slots])


def record_tick_intent(tick, selected, not_selected, *, window=None):
    """Write this tick's intent through events.py, before any unit spawn.

    A tick that selects nobody still records why. That is the only way a
    benched arm becomes an event rather than a quiet night. events.py remains
    the single writer.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from datetime import datetime, timezone

    from consilient.events import record_intent

    now = datetime.now(timezone.utc)
    extra = {}
    if window is not None:
        extra["window"] = window
    record_intent(
        LOG / (now.date().isoformat() + ".jsonl"),
        ts=now.isoformat(),
        tick=tick,
        selected=selected,
        not_selected=not_selected,
        **extra,
    )


SUBSYSTEM_JACCARD_THRESHOLD = float(
    os.environ.get("CONSILIENT_SUBSYSTEM_JACCARD_THRESHOLD", "0.18")
)
if not 0.0 <= SUBSYSTEM_JACCARD_THRESHOLD <= 1.0:
    raise ValueError("CONSILIENT_SUBSYSTEM_JACCARD_THRESHOLD must be between 0 and 1")

SUBSYSTEM_STOP_WORDS = frozenset(
    "a an the and or of to for in on with by that it its is are be not no "
    "feat fix docs test research ci chore refactor perf build style revert".split()
)


def _subsystem_tokens(unit: dict) -> set[str]:
    text = f"{unit.get('title', '')} {unit.get('commit', '')}".lower()
    return {
        token
        for token in re.findall(r"[a-z]+", text)
        if len(token) > 2 and token not in SUBSYSTEM_STOP_WORDS
    }


def ready(uid, unit, done, units, in_flight=()):
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
    tokens = _subsystem_tokens(unit)
    serialised = False
    for other_uid in in_flight:
        if other_uid == uid or other_uid not in units:
            continue
        other = units[other_uid]
        shared_claims = set(unit.get("claims", [])) & set(other.get("claims", []))
        if not shared_claims:
            continue
        other_tokens = _subsystem_tokens(other)
        union = tokens | other_tokens
        similarity = len(tokens & other_tokens) / len(union) if union else 0.0
        if similarity > SUBSYSTEM_JACCARD_THRESHOLD:
            print(
                f"driver: serialising {uid} behind {other_uid} -- duplicate subsystem "
                f"similarity {similarity:.3f} > {SUBSYSTEM_JACCARD_THRESHOLD:.3f}; "
                f"shared claims: {', '.join(sorted(shared_claims))}"
            )
            serialised = True
    return not serialised


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


def _handle_crashed_dispatches(state: dict) -> None:
    """Report every dead dispatch, release what it held, and refund the RIGHT counter.

    Extracted from what was inline in `main()`, so it can be tested directly -- matching this
    file's own pattern (`review_receipt_is_finished`, `clear_stale_review_memos`).

    A crash during a REVIEW dispatch must refund the REVIEW attempt, not the build one.

    MEASURED 25 August 2026, ~23:30: AL and AO, freshly reset for review under
    `reset_review_attempts_on_new_artefact`, crashed on a `git clone --separate-git-dir` timeout
    inside workspace setup -- before a reviewer ever ran. The refund below used to touch
    `state["attempts"]`, the BUILD counter, UNCONDITIONALLY, for every crash regardless of which
    pool the dead run belonged to. A unit crashing while being REVIEWED never had its review
    attempt refunded at all: F-05 says an infrastructure death must not spend a retry, and this
    path was spending one silently, undoing the fresh budget just granted one commit earlier.
    """
    dead = crashed_dispatches(state)
    if not dead:
        return
    crash_log = state.setdefault("crash_history", {})
    for uid, why, refused in dead:
        kind = "REFUSED" if refused else "CRASHED"
        print("driver: " + kind + " " + uid + " -- " + why[:160])
        seen = crash_log.setdefault(uid, [])
        seen.append(why[:200])
        restart_quarantined = record_restart(state, uid, now=time.time())
        # An infrastructure death is not evidence about the work, so it must not spend a
        # retry -- F-05. But a repeated identical death IS evidence, and auto-repair that
        # silently retries a systematic defect is how a system ships with its own bugs built
        # in. Three of the same failure stops being repaired and starts being escalated.
        # Releasing what a dead run held is hygiene, not repair, so it happens for every
        # death INCLUDING an escalated one. The escalation used to `continue` straight past
        # this block, so an escalated unit kept its slot for ever: Y02 died the same way 77
        # times while still counted as in flight. Stopping the retries is right; leaking the
        # capacity is not. [measured 24 Aug 2026]
        #
        # Captured before cleanup below removes it, so the refund can tell which pool this
        # crash actually belonged to.
        was_review_dispatched = uid in state.get("review_dispatched", [])
        state["in_flight"].pop(uid, None)
        for bucket_name in ("resolve_dispatched", "review_dispatched"):
            bucket = state.get(bucket_name, [])
            if uid in bucket:
                bucket.remove(uid)
        if len(seen) >= 3 and len(set(seen[-3:])) == 1:
            if restart_quarantined:
                print(
                    "driver: ESCALATION -- "
                    + uid
                    + " exceeded the restart intensity limit. Auto-repair stopped; "
                    "it needs a person."
                )
            elif quarantine_unit(state, uid):
                print(
                    "driver: ESCALATION -- "
                    + uid
                    + " has died the same way "
                    + str(len(seen))
                    + " times. This is a defect, not bad luck. Auto-repair "
                    "stopped; it needs a person."
                )
            continue
        elif restart_quarantined:
            print(
                "driver: ESCALATION -- "
                + uid
                + " exceeded the restart intensity limit. Auto-repair stopped; "
                "it needs a person."
            )
        if was_review_dispatched:
            review_attempts = state.setdefault("review_attempts", {})
            review_attempts[uid] = max(0, review_attempts.get(uid, 1) - 1)
        else:
            state.setdefault("attempts", {})[uid] = max(
                0, state.get("attempts", {}).get(uid, 1) - 1
            )
        # A crashed review is the quietest failure of the lot: the unit stays "done", the
        # review never happens, and nothing anywhere records that the artefact was never
        # checked by a different model family. Three units reached done this way today.
        state.setdefault("verified", [])
    freed = release_dead_claims({u for u, _, _ in dead})
    if freed:
        print("driver: released " + str(freed) + " claim(s) held by runs that are gone")


def main() -> int:
    units = load(UNITS, {})
    state = load(STATE, {"done": [], "attempts": {}})
    stored = state.get("last_green_summary")
    if isinstance(stored, str) and stored.strip():
        global _LAST_SUITE_SUMMARY
        _LAST_SUITE_SUMMARY = stored.strip()
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
        # A TICK WITHOUT A PLAN DOES NOT DEGRADE GRACEFULLY, SO IT MUST NOT RUN.
        #
        # MEASURED 27 August 2026, twice within an hour. `plan-units.json` was DELETED -- it is
        # untracked instance data, so git cannot restore it -- and this warning printed, and then
        # the tick carried on into `units[uid]` and died on KeyError. Six separate call sites
        # subscript `units` directly, so guarding one merely moved the crash to the next.
        #
        # Every one of those sites is downstream of a single question: is there a plan? When the
        # answer is no, the honest tick does nothing at all. It cannot retire (no claims to hash),
        # cannot dispatch (no briefs), and cannot merge safely. Continuing produced a driver that
        # crashed every tick for 40 minutes while the loop dutifully restarted it.
        #
        # Half a plan is refused for the same reason: `retired_units` would silently drop every
        # unit it can no longer see, and the driver would write a `done` set that reads as
        # regression rather than as data loss. Losing more than a quarter is not a plan edit, it
        # is a missing file, and the difference matters more than the tick does.
        if not units or missing > seen_units * 0.25:
            print(
                f"driver: REFUSING THIS TICK -- {len(units)} of {seen_units} unit(s) present. "
                "This is data loss, not a plan edit. Restore .harness/plan-units.json (the "
                "newest complete copy is under .harness/plan-backups/) before the driver can "
                "retire, dispatch or merge anything. Nothing has been changed."
            )
            # AND MEAN IT. This called save_state(), which wrote a `done` set computed from the
            # missing plan -- so the tick that refused to act still recorded 0 of 147 retired,
            # over a state file that had said 15. The message said nothing had changed while the
            # code changed the one thing that matters. MEASURED 27 August 2026, twice.
            #
            # A refusal writes nothing. The previous state file is the last one computed from a
            # real plan, and it stands until a real plan is back.
            return 0
    state["unit_count"] = len(units)

    reclaimed = reclaim_expired_slots(state)
    if reclaimed:
        print(
            f"driver: reclaimed {len(reclaimed)} expired slot(s), attempts refunded: "
            + " ".join(reclaimed)
        )

    # BU-0: the cheap supervision floor. One pass over open claims and their artefacts;
    # non-zero means something died quiet and the tick should not pretend the queue is fine.
    # REPORTED ONCE PER RUN, not once per tick. `start_failed_dispatches` re-derives the same
    # stalled runs from the same run directories every tick, so the log filled with the same
    # ids over and over with nothing changing but the elapsed seconds -- one run was reported
    # with 847s, then 1457s, then 3353s. MEASURED 25 August 2026, caught by a monitor.
    #
    # Same defect as the crash re-reporting fixed alongside this: a supervisor that cannot tell
    # a new failure from an old one it has already seen reports an echo as evidence, and the
    # signal that something is wrong NOW is buried under a hundred repetitions of something
    # that was wrong an hour ago.
    stalled = start_failed_dispatches()
    reported = state.setdefault("start_failed_reported", [])
    fresh = [row for row in stalled if row.get("run_id") not in reported]
    for row in fresh:
        run_id = row.get("run_id", "?")
        signal = row.get("signal", "no artefact within the start window")
        observed = row.get("observed_bytes", 0)
        print(
            f"driver: START_FAILED {run_id} -- {signal} "
            f"({observed} bytes after {row.get('observed_s')}s)"
        )
        reported.append(run_id)
    if len(stalled) > len(fresh):
        print(
            f"driver: {len(stalled) - len(fresh)} start-failure(s) already reported; "
            "not repeating them"
        )
    # Bounded: a run id that no longer appears as stalled is forgotten, so this cannot grow
    # without limit and a run that stalls again later is reported again.
    live_ids = {row.get("run_id") for row in stalled}
    state["start_failed_reported"] = [r for r in reported if r in live_ids]

    # A crash is reported the tick it happens, not at the next check-in. The principal asked for
    # this after finding three of them himself: "this needs to be reported and auto-fixed to
    # orchestrators in real time not discovered during a check in."
    _handle_crashed_dispatches(state)
    detect_exhausted_arms(state)

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
    cleared_escalations = clear_unjustly_escalated_reviews(state)
    if cleared_escalations:
        print(
            "driver: un-escalated "
            + " ".join(sorted(cleared_escalations))
            + " -- their 3-attempt cap was reached entirely by infrastructure losses"
        )
    stale_memos = clear_stale_review_memos(state, units)
    if stale_memos:
        print(
            f"driver: cleared {len(stale_memos)} non-terminal review memo(s), re-queued: "
            + " ".join(sorted(stale_memos))
        )

    consumed_any = False
    for uid in sorted(list(state.setdefault("review_dispatched", []))):
        expected_now = state.setdefault("review_expected", {}).get(uid) or {}
        if not review_receipt_is_finished(uid, expected_now):
            continue
        # A UNIT MISSING FROM THE PLAN MUST NOT KILL THE DRIVER.
        #
        # MEASURED 27 August 2026: `.harness/plan-units.json` was deleted -- it is untracked
        # instance data, so git could not restore it -- and `units` became empty while
        # `review_dispatched` still named CB1. `units[uid]` raised KeyError at this line, the
        # driver died on that exception, and it died again on every subsequent tick. The pipeline
        # stalled completely, and the only reason it was noticed is that a watchdog was watching
        # the log for tracebacks.
        #
        # The driver already prints a loud warning when the plan shrinks ("the plan lost 147
        # unit(s)"), then walks straight into an unguarded subscript. Warning about a condition
        # and then crashing on it is not handling it. Skip the orphan, say so once, and keep the
        # other units moving -- a missing plan entry is a data problem, not a reason to stop
        # reviewing everything else.
        unit = units.get(uid)
        if unit is None:
            if uid not in state.setdefault("orphan_reviews_reported", []):
                state["orphan_reviews_reported"].append(uid)
                print(
                    f"driver: {uid} is in review_dispatched but absent from the plan -- "
                    "skipping its verdict. The plan has lost a unit that still has work in "
                    "flight; restore plan-units.json before trusting the counts."
                )
            continue
        outcome = consume_review_verdict(state, uid, unit)
        print(f"driver: review of {uid} consumed as {outcome}")
        consumed_any = True
    # PERSIST A VERDICT THE MOMENT IT IS CONSUMED, not at the end of the tick.
    #
    # MEASURED 25 August 2026, 22:30. The log recorded `review of AA consumed as DEFECTIVE` and
    # `review of AE consumed as SOUND`, and forty minutes later the state file still said
    # `no_dispatch` for both -- because `save_state` runs at the END of `main()`, and the tick had
    # not got there. Consumption happens in the first minutes; merges, dispatches and a full suite
    # follow. A tick that is killed, wedged or abandoned at its deadline loses every verdict it
    # consumed, and this driver's ticks have been killed repeatedly today.
    #
    # So the evidence was being gathered correctly and then thrown away by a save that came too
    # late. That is the quietest way to lose work: nothing errors, the log says the verdict was
    # consumed, and the state simply does not have it.
    #
    # A verdict is the most expensive artefact this system produces -- an adversarial review by a
    # different model family, twenty minutes of it -- and it should not be held in memory across
    # the slowest part of the tick. `save_state` is atomic (temp file plus `os.replace`), so
    # calling it more than once per tick costs a write and risks nothing.
    if consumed_any:
        save_state(state)
    done = retired_units(state, units)
    built = set(state.setdefault("built", []))
    state["done"] = sorted(done)
    state["built"] = sorted(built)
    for _expired in expire_finished_dispatches(state):
        print(f"driver: resolve slot released for {_expired} -- its dispatch is over")
    for _expired in expire_finished_dispatches(
        state, "review_dispatched", "review_started", "-verify"
    ):
        print(f"driver: review slot released for {_expired} -- its dispatch is over")
    clear_retired_conflicts(state)

    import time as _time_m

    conflicts = state.setdefault("conflicts", {})
    # MEASURED 24 August 2026. A conflict was recorded once and never re-tested, but HEAD moves
    # every tick, so a cherry-pick that collided an hour ago usually applies cleanly later. Of 23
    # units reported as unmergeable, SIXTEEN were stale rather than genuine -- they had been
    # waiting on a collision that no longer existed, and each was holding a resolver slot for it.
    # Re-testing is cheap (`git merge-tree` writes nothing) and it is the difference between a
    # queue that drains and one that only grows.
    #
    # Retirement clears the conflict on every path, not only here. K01 was in force_done and
    # still on the banner because only this loop popped the entry.
    clear_retired_conflicts(state)
    retired_without_review = retest_conflicts(state)
    conflicts = state.setdefault("conflicts", {})
    built = set(state.setdefault("built", []))
    state["built"] = sorted(built)
    _now_m = _time_m.time()
    _dispatchers_alive = live_dispatchers(state)
    # Every unmerged worktree, not just the in-flight ones. A unit that finished, dropped out of
    # in_flight when its leash expired, and still held unmerged commits was never revisited: the
    # merge loop only ever looked at in_flight, so its output was stranded exactly as F-02
    # describes. V01 sat built-and-unmergeable this way while the tick reported it every time and
    # did nothing about it. [measured 23 Aug 2026]
    #
    # Not `uid not in built` either. `built` records that the plan commit landed once; it is
    # never cleared by new commits a fork adds to the SAME worktree afterwards (a merge-conflict
    # or review fix landing after the unit was already marked built). Excluding built units here
    # stranded exactly that work forever, with no tick ever looking at the worktree again. AN, AJ
    # and AL each sat this way with a fork's fix committed and never merged. [measured 26 August
    # 2026] `merge_unit_worktree`'s own `HEAD..head` rev-list is the cheap no-op check -- a
    # built unit with nothing new past HEAD costs one rev-parse and one rev-list, not a gate run.
    # `force_done` is a permanent, manually-decided retirement -- not the review pipeline's
    # doing, so `done` (which only reads `review_results`) never covers it. Without this
    # exclusion a force_done unit stayed in `mergeable` forever and could have `conflicts[uid]`
    # rewritten on every tick, resurrecting an escalation for work that is not coming back.
    # [measured 26 August 2026]
    force_done = set(state.get("force_done") or [])
    mergeable = [
        uid
        for uid in units
        if uid not in done and uid not in force_done and (WORKTREES / uid).exists()
    ]
    rebase_mergeable_worktrees(mergeable, state, _now_m, _dispatchers_alive)
    for uid in mergeable:
        msg = merge_unit_worktree(uid)
        if msg not in ("no commits", "no worktree"):
            print(f"driver: {msg}")
        if msg.startswith("CONFLICT"):
            conflicts[uid] = msg
        else:
            conflicts.pop(uid, None)
    if conflicts or retired_without_review:
        print(
            f"driver: ESCALATION -- {len(conflicts)} escalated, "
            f"{retired_without_review} retired without review"
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
                conflicts.pop(uid, None)
                print(
                    f"driver: {uid} built (plan commit present, suite green) — awaiting review"
                )
    state["done"] = sorted(done)

    # Built but unreviewed units get an adversarial reviewer from a different family before
    # they count as complete. Verifying by the unit's own tests alone is echo.
    # Quarantine must NOT block review, and this used to exclude quarantined units here.
    #
    # MEASURED 25 August 2026: that made quarantine a terminal state wearing a recoverable
    # one's clothes. `clear_quarantine_after_landed_check` says so in its own docstring -- "a
    # SOUND, identity-bound review is the automatic quarantine recovery path" -- and the only
    # route to a SOUND review was a list this filter removed the unit from. Quarantine blocked
    # review; only review cleared quarantine. Seven units sat in it with no way out: AJ, AL,
    # F04, N04, BM, D02 and BN.
    #
    # BN is the one that shows the cost. It was quarantined for three identical fencing deaths,
    # and it had ALREADY produced the fix for the build's central convergence problem --
    # serialising units that design the same subsystem. Its work was sound and its tests passed.
    # A deadlock in the recovery path was holding the repair for the thing most in need of it.
    #
    # Quarantine exists to stop a unit burning retries on a dispatch that keeps dying the same
    # way -- "a defect, not bad luck". That is a statement about DISPATCHING more work. It is
    # not a reason to refuse to JUDGE work that already exists and is already committed. The two
    # are different questions and only the first is what quarantine was reasoning about.
    #
    # Dispatch stays blocked (the build and resolve paths still exclude quarantined units), so
    # nothing starts burning retries again. Only the verdict path reopens, which is precisely
    # the door the recovery was written to come through.
    pending_review = [
        u
        for u in sorted(state.setdefault("built", []))
        if u not in state.setdefault("review_dispatched", [])
    ]

    live = live_dispatchers(state)
    # Reviews ALREADY outstanding count against MAX_REVIEWS. This started at 0 each tick, so it
    # counted only what this tick launched and never what was still running: every tick added up
    # to twelve more on top of the backlog. MEASURED 24 Aug 2026 -- 64 reviews in flight against
    # a cap of 12, one unit on its 27th review attempt, and 68 check_error against 3 SOUND.
    #
    # Each review full-clones a 136 MB workspace, so sixty-four of them thrash the machine badly
    # enough that none of them finish, which is why the verification tier produced almost nothing
    # while looking maximally busy. MAX_REVIEWS was always meant to be a concurrency cap -- the
    # name says so -- and this makes it one instead of a per-tick rate.
    # Before the ceiling, not behind it: releasing a unit whose code has moved spends no
    # review slot, and running it inside the loop below meant it never ran at all while the
    # lane was full. See `clear_escalations_whose_artefact_moved`.
    for cleared_uid in clear_escalations_whose_artefact_moved(
        state, units, pending_review
    ):
        print(
            f"driver: {cleared_uid}'s artefact changed since its last review attempt; "
            "review budget reset"
        )

    reviews_out = len(state.setdefault("review_dispatched", []))
    for uid in pending_review:
        if not admit_review(reviews_out):
            print(
                f"driver: review lane at ceiling ({reviews_out}/{MAX_REVIEWS}); shedding"
            )
            break
        builder = state.get("built_by", {}).get(uid, "codex")
        reviewers = [a for a in ARMS if FAMILY.get(a[0]) != FAMILY.get(builder)]
        if not reviewers:
            continue
        artefact = artefact_identity(units[uid])
        if artefact is None:
            # A UNIT THAT CAN NEVER BE REVIEWED MUST NOT BE SKIPPED IN SILENCE.
            #
            # `artefact_identity` returns None when a claimed path is absent from HEAD, so no
            # verdict can bind and this unit can never retire. The loop simply moved on, every
            # tick, for as long as the condition lasted.
            #
            # MEASURED 27 August 2026: five units sat in exactly this state -- D01, O01, Q01, S03
            # and T02, each missing one claimed test file -- and nothing named them. The driver
            # prints an aggregate "N built unit(s) CANNOT retire" line elsewhere, which says the
            # count but not which, and says it in a different part of the tick from the loop that
            # is actually skipping them.
            #
            # This is the same defect as the resolve and review slot leaks repaired earlier the
            # same day: a `continue` where a line of output belonged. Reported once per unit
            # rather than per tick, because a message repeated every ninety seconds stops being
            # read, which is how the aggregate line got ignored in the first place.
            unreviewable = state.setdefault("unreviewable_reported", [])
            if uid not in unreviewable:
                unreviewable.append(uid)
                missing = [
                    p
                    for p in (units[uid].get("claims") or [])
                    if sh(["git", "rev-parse", "HEAD:" + p]).returncode != 0
                ]
                print(
                    f"driver: {uid} CANNOT BE REVIEWED -- claimed path(s) absent from HEAD: "
                    f"{', '.join(missing) or 'unknown'}. No verdict can bind to it, so it can "
                    "never retire. It needs the missing work landed, not another review."
                )
            continue
        review_escalated = uid in state.setdefault("review_escalated", [])
        if not review_dispatch_allowed(state, uid):
            if not review_escalated:
                print(
                    f"driver: ESCALATION -- review of {uid} reached "
                    f"{MAX_REVIEW_ATTEMPTS} attempts; refusing another dispatch"
                )
            continue
        rh, rm, rl = reviewers[0]
        attempt = state.setdefault("review_attempts", {}).get(uid, 0) + 1
        state["review_attempts"][uid] = attempt
        # Captured HERE, not at retirement, and this is the load-bearing detail. A unit's own
        # commits are `HEAD..worktree_head`, which is EMPTY once the unit has merged -- so the
        # fingerprint cannot be re-derived later for exactly the units that reach retirement. It
        # is taken while the answer still exists and carried forward with the verdict.
        state.setdefault("review_expected", {})[uid] = {
            "artefact": artefact,
            "attempt": attempt,
            "deliverable": _unit_added_line_hashes(uid),
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
        preserve_review_artefacts(uid, attempt)
        spawn_logged(vargs, BRIEFS / f"{uid}-verify.out", BRIEFS / f"{uid}-verify.err")
        state["review_dispatched"].append(uid)
        state.setdefault("review_started", {})[uid] = [time.time(), rl]
        reviews_out += 1
        print(f"driver: review of {uid} dispatched to {rh} (built by {builder})")

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

    # A unit whose claimed path is absent from HEAD can NEVER retire, and said so nowhere.
    #
    # `artefact_identity` hashes `git rev-parse HEAD:<path>` for every claimed path and returns
    # None if any one of them fails; `retired_units` requires a non-None identity. So such a unit
    # is structurally incapable of retiring however good its review is -- and the failure is
    # SILENT: it simply never appears in `done`, which is indistinguishable from not having been
    # reviewed yet.
    #
    # MEASURED 25 August 2026: 43 of 147 units claim a path absent from HEAD. For a unit not yet
    # built that is ordinary -- the missing file is the one it exists to create. For a unit
    # already BUILT it is a trap, and seven were in it: A03, AU, D01, O01, Q01, S03, T02. Either
    # the work did not land where the plan says, or the plan names a path the unit never creates.
    # Both need a person; neither is fixed by another review, and a review spent on one is spent
    # for nothing.
    #
    # This reports; it changes no behaviour. The point is that the trap stops being silent.
    unretirable = []
    for uid in sorted(built_unmerged | set(state.setdefault("built", []))):
        unit = units.get(uid)
        if unit is None or artefact_identity(unit) is not None:
            continue
        claims = unit.get("claims") if isinstance(unit.get("claims"), list) else []
        absent = [
            path
            for path in claims
            if isinstance(path, str)
            and sh(["git", "rev-parse", "HEAD:" + path]).returncode != 0
        ]
        unretirable.append((uid, absent))
    if unretirable:
        print(
            f"driver: {len(unretirable)} built unit(s) CANNOT retire -- a claimed path is "
            "absent from HEAD, so no identity can be derived and no verdict can bind:"
        )
        for uid, absent in unretirable:
            shown = ", ".join(absent[:3]) or "(claims unreadable)"
            print(f"driver:   {uid} -- missing {len(absent)}: {shown}")

        # A UNIT THAT NEVER PRODUCED A FILE IT CLAIMS IS NOT BUILT.
        #
        # This block reported the condition and stopped there, so such a unit sat in `built` for
        # ever: it cannot retire, because no identity binds; it cannot be reviewed, for the same
        # reason; and it is not a build candidate, because `built` membership excludes it. Three
        # doors, all shut, and the only sign was a line of log nobody acted on.
        #
        # MEASURED 27 August 2026: D01, O01, Q01, S03 and T02, five units between them missing six
        # claimed test files. Every one of those files was absent from HEAD *and* from the unit's
        # own worktree -- so this is not a merge that failed to land, it is a build that never
        # wrote the file. AU looked identical and was NOT this case: its file existed in its
        # worktree and merely needed landing, which is why the check is on BOTH locations rather
        # than on HEAD alone. Getting that distinction wrong would re-dispatch finished work and
        # throw away the merge repair.
        #
        # Returning it to the queue is the conservative move: it re-runs a build that demonstrably
        # did not finish. It does not touch the attempt counter, so a unit that keeps failing this
        # way still reaches its retry cap and escalates rather than looping for ever.
        for uid, absent in unretirable:
            unit = units.get(uid) or {}
            worktree = WORKTREES / uid
            never_written = [p for p in absent if not (worktree / p).is_file()]
            if not never_written or len(never_written) != len(absent):
                continue
            built_list = state.setdefault("built", [])
            if uid in built_list:
                built_list.remove(uid)
                print(
                    f"driver: {uid} returned to the build queue -- it claims "
                    f"{len(never_written)} path(s) that exist in neither HEAD nor its worktree, "
                    "so the build never wrote them. Reviewing it cannot help; building it can."
                )

    candidates = [
        u
        for u in units
        if u not in done
        and u not in state.setdefault("built", [])
        and u not in inflight
        and u not in built_unmerged
        and attempts.get(u, 0) < 3
        and u not in state.setdefault("quarantined", [])
    ]
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
    # Spend slots on whatever releases the most work, not on whatever sorts first.
    # Downstream count is the right default and a bad rule for one case: a unit that unblocks
    # nothing but improves the QUALITY of everything -- the cross-family verdict parser is the
    # example -- sorts last under it, which is exactly backwards. An explicit `priority` on the
    # unit is added to its effective rank. It is deliberately a separate, visible field rather
    # than a fudged dependency, because inflating a dependency count to win a scheduling argument
    # is how a plan stops describing the work.
    candidates.sort(
        key=lambda u: (
            -(downstream_count(u, units) + int(units[u].get("priority", 0))),
            PHASE.get(u[0], 9),
            u,
        )
    )
    blocked = []
    startable = []
    planned_in_flight = set(inflight)
    for uid in candidates:
        if ready(uid, units[uid], landed, units, planned_in_flight):
            startable.append(uid)
            planned_in_flight.add(uid)
        else:
            blocked.append(uid)

    # Intent first, spawn second. A tick that selects nobody still names why, which is
    # the only record F-08-class silence can leave. Written before the cap return so a
    # full queue is not indistinguishable from a night with nothing to do.
    selected = choose_selected(startable, live)
    tick = int(state.get("intent_tick", 0))
    record_tick_intent(
        tick,
        selected,
        not_selected_reasons(units, landed, blocked, startable, selected),
    )
    state["intent_tick"] = tick + 1

    if not candidates:
        print(f"driver: every unit is done or exhausted ({len(done)}/{len(units)})")
        save_state(state)
        return 0

    launched = 0
    # Builds are dispatched before resolves in this tick, so whatever builds take, resolve
    # never sees. Count the resolvers already out -- they occupy this same lane -- and hold
    # back a few slots for the conflicts waiting behind them.
    resolving_now = state.setdefault("resolve_dispatched", [])
    reserved = resolve_slots_reserved(conflicts, resolving_now)
    for uid in startable:
        if not admit_build(len(inflight) + len(resolving_now) + reserved):
            print(
                f"driver: build lane at ceiling ({len(inflight)} building + "
                f"{len(resolving_now)} resolving + {reserved} reserved for resolve"
                f"/{MAX_BUILDS}); shedding"
            )
            break
        unit = units[uid]
        n = attempts.get(uid, 0)
        brief = write_brief(uid, unit, state.setdefault("repair_findings", {}).get(uid))
        rot = state.get("arm_rotation", 0)
        picked = pick_arm(rot + n, state)
        state["arm_rotation"] = rot + 1
        if picked is None:
            if not state.get("_all_arms_exhausted_reported"):
                print(
                    "driver: ALL ARMS EXHAUSTED -- every configured harness is cooling down "
                    "or saturated; no build dispatched this tick"
                )
                state["_all_arms_exhausted_reported"] = True
            break
        harness, model, leash = picked
        state["_all_arms_exhausted_reported"] = False
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
        for c in family_claims(unit["claims"]):
            args += ["--claim", c]
        wt = unit_worktree(uid)
        if wt is not None:
            args += ["--cwd", str(wt)]
        spawn_logged(args, BRIEFS / f"{uid}.out", BRIEFS / f"{uid}.err")
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
        # RESOLVERS COUNT AGAINST THE LANE THEY ARE GATED ON. This read
        # `admit_build(len(inflight))`, where `inflight` holds BUILDS only -- so a resolver
        # was admitted on the build lane's occupancy while adding nothing to it, and the next
        # was admitted on the same unchanged number. MEASURED 27 August 2026: 34 resolvers
        # live at once, each a full workspace clone and a harness run, on a lane whose cap is
        # MAX_BUILDS. This is the MAX_REVIEWS defect in a second place: a cap that does not
        # count what it is capping is not a cap.
        if not admit_build(len(inflight) + len(resolving)):
            print(
                f"driver: build lane at ceiling "
                f"({len(inflight)} building + {len(resolving)} resolving/{MAX_BUILDS}); shedding"
            )
            break
        if (
            uid in resolving
            or uid in done
            or uid in state.setdefault("quarantined", [])
            or (WORKTREES / uid).exists() is False
        ):
            continue
        unit = units.get(uid)
        if not unit:
            continue
        rbrief = write_resolve_brief(uid, unit, why)
        rot = state.get("arm_rotation", 0)
        picked = pick_arm(rot, state)
        state["arm_rotation"] = rot + 1
        if picked is None:
            if not state.get("_all_arms_exhausted_reported"):
                print(
                    "driver: ALL ARMS EXHAUSTED -- every configured harness is cooling down "
                    "or saturated; no resolve dispatched this tick"
                )
                state["_all_arms_exhausted_reported"] = True
            break
        harness, model, leash = picked
        state["_all_arms_exhausted_reported"] = False
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
        for c in family_claims(unit["claims"]):
            rargs += ["--claim", c]
        wt = unit_worktree(uid)
        if wt is not None:
            rargs += ["--cwd", str(wt)]
        spawn_logged(
            rargs, BRIEFS / f"{uid}-resolve.out", BRIEFS / f"{uid}-resolve.err"
        )
        resolving.append(uid)
        state.setdefault("resolve_started", {})[uid] = [time.time(), leash]
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


def _self_test() -> None:
    """Regression checks for unit AI. Invoked as: python .harness/build_driver.py --self-test."""
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        default: dict[str, object] = {"done": [], "attempts": {}}
        assert load(root / "missing.json", default) == default

        torn = root / "torn.json"
        torn.write_text('{"done": ["F01"], "attempts":', encoding="utf-8")
        try:
            load(torn, default)
        except SystemExit as exc:
            assert "unreadable" in str(exc)
        else:
            raise AssertionError("truncated state was treated as absent")

        target = root / "driver-state.json"
        replacements: list[tuple[pathlib.Path, pathlib.Path]] = []
        real_replace = os.replace

        def wrapped(src: str, dst: str) -> None:
            replacements.append((pathlib.Path(src), pathlib.Path(dst)))
            real_replace(src, dst)

        global STATE
        old_state = STATE
        STATE = target
        os.replace = wrapped  # type: ignore[assignment]
        try:
            save_state({"done": ["A"]})
        finally:
            os.replace = real_replace
            STATE = old_state
        assert replacements, "save_state must go through os.replace"
        src, dst = replacements[-1]
        assert dst == target
        assert src.parent == target.parent
        assert src != dst
        assert src != target.with_suffix(".json.tmp"), (
            "a fixed temp name lets two writers rename each other's partial file"
        )
        assert load(target, {}) == {"done": ["A"]}

        briefs = root / "briefs"
        briefs.mkdir()
        receipt = {
            "v": 1,
            "unit": "U01",
            "artefact": "digest",
            "attempt": 1,
            "verdict": "DEFECTIVE",
            "findings": ["fault"],
        }
        (briefs / "U01-verify.out").write_text(
            json.dumps({"status": "ok", "stdout_tail": "reviewer finished"}),
            encoding="utf-8",
        )
        (briefs / "U01-verdict.json").write_text(json.dumps(receipt), encoding="utf-8")
        old_briefs = BRIEFS
        real_append = append_review_outcome
        real_identity = artefact_identity
        globals()["BRIEFS"] = briefs
        globals()["append_review_outcome"] = lambda _outcome: None
        globals()["artefact_identity"] = lambda _unit: "digest"
        try:
            state = {
                "built": ["U01"],
                "done": ["U01"],
                "verified": ["U01"],
                "review_dispatched": ["U01"],
                "review_expected": {"U01": {"artefact": "digest", "attempt": 1}},
            }
            assert consume_review_verdict(state, "U01", {}) == "DEFECTIVE"
            assert "U01" not in state["verified"]
            assert "U01" not in state["done"]
            assert "U01" not in state["built"]
        finally:
            globals()["BRIEFS"] = old_briefs
            globals()["append_review_outcome"] = real_append
            globals()["artefact_identity"] = real_identity

        (briefs / "U01-verify.out").write_text("attempt-1-out", encoding="utf-8")
        (briefs / "U01-verdict.json").write_text("attempt-1-verdict", encoding="utf-8")
        globals()["BRIEFS"] = briefs
        try:
            preserve_review_artefacts("U01", 2)
            assert not (briefs / "U01-verify.out").exists()
            assert (briefs / "U01-verify-1.out").read_text(encoding="utf-8") == (
                "attempt-1-out"
            )
            assert (briefs / "U01-verdict-1.json").read_text(encoding="utf-8") == (
                "attempt-1-verdict"
            )
        finally:
            globals()["BRIEFS"] = old_briefs

    ignore_lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".harness/driver-state.json" in ignore_lines
    assert not hasattr(sys.modules[__name__], "ORDER")
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert ('state["last_published_' + 'count"]') not in source
    assert ('state["skip' + 'ped"]') not in source
    corpora_flag = "--require" + "-corpora"
    assert f'["{corpora_flag}"]' in source

    released: list[str] = []
    real_release = release_dead_claims
    real_progress = run_dir_progress
    old_briefs = BRIEFS
    briefs = pathlib.Path(tempfile.mkdtemp())
    out = briefs / "S.out"
    out.write_text("started\n", encoding="utf-8")
    aged = time.time() - PROGRESS_SILENCE_S - 30
    os.utime(out, (aged, aged))
    globals()["BRIEFS"] = briefs
    globals()["run_dir_progress"] = lambda _uid, _started: 0.0
    globals()["release_dead_claims"] = lambda uids: (
        released.extend(sorted(uids)) or len(uids)
    )
    try:
        silent_state = {
            "in_flight": {"S": (time.time() - 10, 3600.0)},
            "attempts": {"S": 2},
        }
        assert reclaim_expired_slots(silent_state) == ["S (silent)"]
        assert released == ["S"]
        assert "S" not in silent_state["in_flight"]
    finally:
        globals()["BRIEFS"] = old_briefs
        globals()["run_dir_progress"] = real_progress
        globals()["release_dead_claims"] = real_release

    handles: list[object] = []
    real_popen = subprocess.Popen

    def fake_popen(*_args: object, **kwargs: object) -> object:
        handles.append(kwargs["stdout"])
        handles.append(kwargs["stderr"])
        return object()

    subprocess.Popen = fake_popen  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as directory:
            spawn_logged(
                ["python", "-c", "pass"],
                pathlib.Path(directory) / "unit.out",
                pathlib.Path(directory) / "unit.err",
            )
    finally:
        subprocess.Popen = real_popen
    assert handles and all(getattr(handle, "closed") for handle in handles)

    global _LAST_SUITE_SUMMARY
    old_summary = _LAST_SUITE_SUMMARY
    old_briefs = BRIEFS
    with tempfile.TemporaryDirectory() as directory:
        globals()["BRIEFS"] = pathlib.Path(directory)
        _LAST_SUITE_SUMMARY = "1418 passed, 3 skipped"
        unit = {
            "title": "test",
            "plan": "test.md",
            "claims": ["a.py"],
            "commit": "test",
        }
        try:
            brief = write_brief("T", unit)
            verify = write_verify_brief("T", unit, "d" * 64, 1)
            brief_text = brief.read_text(encoding="utf-8")
            verify_text = verify.read_text(encoding="utf-8")
            assert "1418 passed, 3 skipped" in brief_text
            assert "1418 passed, 3 skipped" in verify_text
            assert "898 passed" not in brief_text
            assert "914 passed" not in verify_text
        finally:
            _LAST_SUITE_SUMMARY = old_summary
            globals()["BRIEFS"] = old_briefs

    print("build_driver self-test: PASS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
        raise SystemExit(0)
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
