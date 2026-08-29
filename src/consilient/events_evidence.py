"""What an event must say about the evidence it carries.

A trajectory is only worth replaying if every line declares where its content came from,
and these are the contracts that force it to. A multi-contributor event must declare a
distinct evidence_class per contributor (V0-26), because agreement between agents
drawing on the same evidence is echo rather than consilience — Whewell's test needs
another, different class, and an event that cannot name one is not offering a test. A
knowledge retrieval names its source, its licence and its retrieval date, and a source
that could not be reached says so and carries no invented content (V0-31). A measurement
names what was registered and what came back. An attempt's outcome and a human's later
judgement of it stay on distinct event paths, so neither can be filed as the other.

The verification outcome's own body is checked here as well. That contract sat in
`events_kinds.py` until 28 August 2026 and moved to bring that file under the
file-length ceiling; it reads only names defined below it, so the layering did not
change -- only which file holds it.

The append lock lives here too, because it is the smallest thing that needed a home
below the writers: byte zero is held across the append itself and across nothing more,
and the full-jitter backoff every retrying reader sleeps by is beside it. Holding a lock
for longer than the write it protects is how a log stops being appendable under
contention."""

from __future__ import annotations
import os
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from .events_vocabulary import (
    jittered_sleep,
)

from .events_kinds import (
    VERIFICATION_STATUSES,
    VERIFICATION_OUTCOME_KIND,
    DECISION_KIND,
    DIGEST_RE,
    EventError,
    EventPayload,
    KNOWLEDGE_ACTOR,
    KNOWLEDGE_RETRIEVED_KIND,
    KNOWLEDGE_STATUSES,
    MEASUREMENT_ACTOR,
    MEASUREMENT_REGISTERED_KIND,
    MEASUREMENT_RESULT_KIND,
    OUTCOME_KIND,
    REVERSAL_KINDS,
    TS,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    _TRANSACTION_LOCK_BYTE,
)


__all__ = [
    "_check_verification_outcome_contract",
    "DECISION_KIND",
    "DIGEST_RE",
    "EventError",
    "EventPayload",
    "KNOWLEDGE_ACTOR",
    "KNOWLEDGE_RETRIEVED_KIND",
    "KNOWLEDGE_STATUSES",
    "MEASUREMENT_ACTOR",
    "MEASUREMENT_REGISTERED_KIND",
    "MEASUREMENT_RESULT_KIND",
    "OUTCOME_KIND",
    "REVERSAL_KINDS",
    "TS",
    "VERDICT_CORRECTION_KIND",
    "VERDICT_KIND",
    "_TRANSACTION_LOCK_BYTE",
    "jittered_sleep",
]


def _check_knowledge_contract(event: EventPayload) -> None:
    """V0-31: every retrieval carries source, licence and date; failures stay empty."""
    if event["event"] != KNOWLEDGE_RETRIEVED_KIND:
        return
    if event["actor"] != KNOWLEDGE_ACTOR:
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} must be attributed to {KNOWLEDGE_ACTOR!r}"
        )
    data = event["data"]
    for field in (
        "source_id",
        "source_url",
        "licence",
        "category",
        "retrieved_at",
        "status",
    ):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} must carry a non-empty string {field}"
            )
    status = data["status"]
    if status not in KNOWLEDGE_STATUSES:
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} status must be one of {sorted(KNOWLEDGE_STATUSES)}, "
            f"got {status!r}"
        )
    retrieved_at = data["retrieved_at"]
    if not TS.match(retrieved_at):
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} retrieved_at must be RFC3339 with an explicit offset"
        )
    if status == "ok":
        if not isinstance(data.get("uri"), str) or not data["uri"].strip():
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must carry uri"
            )
        digest = data.get("content_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must carry a 64-char "
                "content_digest"
            )
        if data.get("reason"):
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must not carry a failure reason"
            )
        return
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} with status {status!r} must carry a non-empty reason"
        )
    if data.get("content_digest"):
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} with status {status!r} must not carry content_digest"
        )


def _check_evidence_class(event: EventPayload) -> None:
    """V0-26: multi-contributor events must declare a distinct evidence_class per contributor.

    ADR-0010 and CONSILIENCE.md clause 2: agreement between agents that share evidence
    is echo, not consilience. A multi-contributor event must name a different class of
    facts per contributor (Ao, Gao & Simchi-Levi 2026, arXiv:2603.26993).
    """
    data = event.get("data")
    if not isinstance(data, dict):
        return
    contributors = data.get("contributors")
    if contributors is None and "contributors" in event:
        contributors = event.get("contributors")
    if contributors is None:
        return

    if not isinstance(contributors, list):
        raise EventError("contributors must be a list")

    if len(contributors) <= 1:
        return

    seen_classes: set[str] = set()
    for contributor in contributors:
        if not isinstance(contributor, dict):
            raise EventError("contributor must be an object")
        ec = contributor.get("evidence_class")
        if not isinstance(ec, str) or not ec.strip():
            identity = (
                contributor.get("logical_identity")
                or contributor.get("runtime_identity")
                or "contributor"
            )
            raise EventError(
                f"multi-contributor event requires a non-empty evidence_class for {identity!r} (V0-26)"
            )
        normalized = ec.strip().casefold()
        if normalized in seen_classes:
            raise EventError(
                f"multi-contributor event must name distinct evidence classes; duplicate "
                f"evidence_class {ec.strip()!r} (V0-26)"
            )
        seen_classes.add(normalized)


def _check_measurement_contract(event: EventPayload) -> None:
    """Per-event fields for measurement.registered / measurement.result.

    Lifecycle join is not done here: a single event cannot see its partner.
    Replay quarantines unmatched results; ``projection.joined_measurement_results``
    raises. That split matches MLPerf Logging's compliance_checker
    (mlcommons/logging, retrieved 2026-08-28): invalid lifecycle fails the
    checker; the log remains readable.
    """
    kind = event["event"]
    if kind not in (MEASUREMENT_REGISTERED_KIND, MEASUREMENT_RESULT_KIND):
        return
    if event["actor"] != MEASUREMENT_ACTOR:
        raise EventError(
            f"{kind} must be attributed to declared writer {MEASUREMENT_ACTOR!r}"
        )
    data = event["data"]
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise EventError(f"{kind} must carry a non-empty string run_id")
    if kind == MEASUREMENT_REGISTERED_KIND:
        config_hash = data.get("config_hash")
        if not isinstance(config_hash, str) or DIGEST_RE.fullmatch(config_hash) is None:
            raise EventError(
                f"{MEASUREMENT_REGISTERED_KIND} config_hash must be 64 lower-case hex characters"
            )
        hardware_id = data.get("hardware_id")
        if not isinstance(hardware_id, str) or not hardware_id.strip():
            raise EventError(
                f"{MEASUREMENT_REGISTERED_KIND} must carry a non-empty string hardware_id"
            )
        return
    fixture = data.get("fixture")
    if not isinstance(fixture, str) or not fixture.strip():
        raise EventError(
            f"{MEASUREMENT_RESULT_KIND} must carry a non-empty string fixture"
        )


def _check_attempt_contract(event: EventPayload) -> None:
    """Keep verifier outcomes and human judgements on distinct event paths."""
    kind = event["event"]
    data = event["data"]
    if kind == OUTCOME_KIND and "human_verdict" in data:
        raise EventError(
            f"{OUTCOME_KIND} cannot carry human_verdict; append a separate "
            f"{VERDICT_KIND} event"
        )
    if "human_verdict" in data and kind not in (
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
    ):
        raise EventError(
            f"human_verdict is valid only on {VERDICT_KIND} or "
            f"{VERDICT_CORRECTION_KIND}"
        )
    if kind in (VERDICT_KIND, VERDICT_CORRECTION_KIND) and "human_verdict" not in data:
        raise EventError(f"{kind} must carry human_verdict")
    if kind != VERDICT_CORRECTION_KIND:
        return

    previous = data.get("previous_verdict")
    if previous not in ("accept", "reject"):
        raise EventError(
            f"{VERDICT_CORRECTION_KIND} must carry previous_verdict 'accept' or "
            f"'reject', got {previous!r}"
        )
    if data["human_verdict"] == previous:
        raise EventError("a verdict correction must change the previous verdict")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(f"{VERDICT_CORRECTION_KIND} must carry a non-empty reason")


def _check_decision_content(data: EventPayload) -> None:
    for field in ("decision", "reasoning", "falsifier"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{DECISION_KIND} must carry {field} as a non-empty string"
            )

    if "reversal" not in data:
        raise EventError(f"{DECISION_KIND} must carry reversal (V0-22)")
    reversal = data["reversal"]
    if not isinstance(reversal, dict):
        raise EventError("reversal must be an object carrying kind and value")
    kind = reversal.get("kind")
    if not isinstance(kind, str) or kind not in REVERSAL_KINDS:
        raise EventError(
            f"reversal kind must be one of {sorted(REVERSAL_KINDS)}, got {kind!r}"
        )
    if "value" not in reversal:
        raise EventError("reversal must carry value")

    value = reversal["value"]
    if kind == "revert":
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{7,40}", value) is None:
            raise EventError(
                "revert reversal value must be a 7-40 character commit sha"
            )
    elif kind == "command":
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(token, str) or not token.strip() for token in value)
        ):
            raise EventError(
                "command reversal value must be a non-empty argv token list"
            )
    elif (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", value)
        is None
    ):
        raise EventError("inverse reversal value must be a dotted importable symbol")


@contextmanager
def _appending(fd: int) -> Iterator[None]:
    """Hold byte 0 across the append itself, and only across the append.

    Two reasons, and the second is the one that makes this permanent rather than transitional.

    First, a writer that has not yet adopted `_TRANSACTION_LOCK_BYTE` -- an older checkout, a
    long-lived process that imported this module before the change, another tool appending to
    the same trajectory -- still contends on byte 0. Without this, such a writer and a current
    one would not exclude each other at all, and two concurrent `O_APPEND` writes on Windows
    are a seek-then-write pair rather than one atomic operation, so they can interleave into a
    torn line. A torn line is quarantined by `read()` rather than accepted, so it fails
    closed -- but a trajectory that β is measured from should not be shedding lines at all.

    Second, it keeps the honest invariant that concurrent appenders exclude one another
    through the bytes they actually write, whatever else changes above.

    Readers still overlap this region, so they can still be denied -- for the microseconds of
    a write and an fsync, not for the whole parse. That is precisely the transient the six
    jittered retries in `read()` exist to ride out, and it is why that budget stays unchanged.

    POSIX needs nothing here: `flock` is whole-file and advisory, so it already excludes
    writers without denying readers, which is why this failure was Windows-only.
    """
    if sys.platform != "win32":
        yield
        return
    import msvcrt

    held = False
    try:
        while True:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                held = True
                break
            except OSError:
                jittered_sleep(0.01)
        yield
    finally:
        if held:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass


_READ_BACKOFF = 0.04


def _retry_sleep(attempt: int) -> None:
    """Back off with FULL JITTER, not in lockstep.

    The backoff above was exact -- every waiter slept 40 ms, then 80, then 160, on the same
    schedule. That is fine for one reader and pathological for twenty, which is what this
    repository actually runs: roughly twenty concurrent agents share one append-only trajectory,
    and on Windows a writer denies every reader while it holds the file. Evict twenty readers at
    once and they all retry at the same instants, so they collide again at every step, and the
    ~2.5 s budget then fails CLOSED -- correctly, but globally, because a refused read fails the
    suite, and a failed suite blocks retirement, merging and publication together.

    MEASURED 24 August 2026: `could not be read after 6 attempts: observed access denial` was the
    commonest crash signature in driver state, with single units dying this way 77 and 78 times,
    which stopped the build lane outright.

    Full jitter -- sleep(uniform(0, base * 2**attempt)) -- is the standard remedy and the one
    Brooker measures as best-in-class for reducing both contention and total work: "Exponential
    Backoff And Jitter", AWS Architecture Blog, 4 March 2015. It keeps the same ceiling and
    spreads the waiters across it, so the herd stops arriving together.

    The retry COUNT and the budget are deliberately unchanged. Raising either would widen the
    window a bad read can hide in without decorrelating anything, and the refusal is correct
    fail-closed behaviour -- a reader that silently returned a partial trajectory would be far
    worse than one that stops.

    NO PRNG. The obvious spelling is `random.uniform`, and `random` is not in this package's
    import allowlist (`tests/test_budget.py::PRODUCT_IMPORTS`). That allowlist is a capability
    boundary with a written justification per entry, and widening it so a fix compiles is the
    move it exists to refuse -- so the spread is drawn from primitives already permitted. The
    process id decorrelates ACROSS processes, which is the whole problem here, and the monotonic
    clock decorrelates across attempts within one. Multiplying the pid by a large odd constant
    scatters neighbouring pids, which arrive in blocks when a driver launches its dispatchers.
    """
    jittered_sleep(_READ_BACKOFF * (2**attempt))


def _check_verification_outcome_contract(event: EventPayload) -> None:
    """Keep component outcomes pairable without treating missing work as rejection."""
    if event["event"] != VERIFICATION_OUTCOME_KIND:
        return

    data = event["data"]
    for field in (
        "verification_id",
        "attempt_id",
        "protocol_id",
        "verifier_id",
        "verifier_version",
        "evidence_class",
    ):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} must carry a non-empty string {field}"
            )

    version = data["verifier_version"]
    if version != version.strip() or not version.isprintable():
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} verifier_version must be canonical printable text"
        )

    digest = data.get("artefact_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} artefact_sha256 must be 64 lowercase hex characters"
        )

    status = data.get("status")
    if status not in VERIFICATION_STATUSES:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} status must be one of "
            f"{sorted(VERIFICATION_STATUSES)}, got {status!r}"
        )

    if status == "completed":
        if not isinstance(data.get("verifier_accept"), bool):
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} verifier_accept must be a boolean when completed"
            )
    elif "verifier_accept" in data:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} verifier_accept is valid only when completed"
        )

    if "human_decision" in data:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} cannot carry human_decision; append a separate "
            f"{VERDICT_KIND} event"
        )

    token = data.get("start_token")
    if token is not None:
        if not isinstance(token, str) or re.fullmatch(r"[0-9a-f]{64}", token) is None:
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} start_token must be 64 lowercase hex characters"
            )
