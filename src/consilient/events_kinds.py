"""The names of the event kinds, and the actors permitted to author them.

An event is identified by a string, and these are all of the strings — attempt outcomes
and their verdicts and corrections, autonomous decisions and action proposals, budget
state, reservations and observed usage, knowledge retrievals, capability gaps and
versioned capabilities, escalations, consent granted and withdrawn, the three durable
feedback kinds, scheduler intent and starvation, delivery estimates, model changes,
visibility changes and captured records. Spelling one of these wrong by hand is the
mistake a named constant makes impossible, and a declared writer beside each kind is how
an event authored by the wrong actor is caught rather than believed.

Here too are the schema's fixed points: the version stamp, the five required top-level
keys, the timestamp pattern that insists on an explicit offset or Z so that a replay
across machines does not depend on the reader's timezone, the digest pattern, and the
thresholds the loop is judged against — the escalation budget, window and precision
floor, the starvation floors, the tolerated clock skew. `EventError` is defined here and
raised by everything above it: an event was rejected before it reached the log.

The review queue opened contract needs only these names and is checked here. The
verification outcome's own body was checked here too until 28 August 2026, when it moved
to `events_evidence.py` to bring this file under the file-length ceiling; it reads nothing
from above, so the move was a relocation and not a change of layer."""

from __future__ import annotations
import json
import re
from contextvars import ContextVar
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

# Event shapes vary by kind at this JSON boundary, so values cannot be narrowed further
# without changing the runtime validation contract. Every consumed value is checked below.
EventPayload = dict[str, Any]

SCHEMA_VERSION = 1

REQUIRED = ("v", "ts", "event", "actor", "data")

OUTCOME_KIND = "attempt.outcome"

VERIFICATION_OUTCOME_KIND = "verification.outcome"

REVIEW_QUEUE_OPENED_KIND = "review.queue.opened"

CANDIDATE_EXPOSED_KIND = "candidate.exposed"

ATTEMPT_REVIEWED_KIND = "attempt.reviewed"

REVIEW_PRESENTATION_FROZEN_KIND = "review.presentation.frozen"

VERDICT_KIND = "attempt.verdict"

VERDICT_CORRECTION_KIND = "attempt.verdict.correction"

DECISION_KIND = "decision.autonomous"

ACTION_PROPOSAL_KIND = "action.proposal"

REVERSAL_KINDS = frozenset({"revert", "command", "inverse"})

_PROTECTED_ADMISSION_CLASSES = frozenset({"protected_covered", "protected_uncovered"})

BUDGET_STATE_KIND = "budget.state"

USAGE_KIND = "usage.observed"

SPEND_RESERVED_KIND = "spend.reserved"

METERED_PROVIDER = "openrouter"

METERED_CURRENCY = "USD"

BUDGET_STATE_ACTOR = "openrouter-probe"

BUDGET_RESERVATION_ACTOR = "consilient.budget"

USAGE_ACTOR = "consilient.usage"

KNOWLEDGE_RETRIEVED_KIND = "knowledge.retrieved"

KNOWLEDGE_ACTOR = "consilient.knowledge"

KNOWLEDGE_STATUSES = frozenset({"ok", "unavailable", "not_configured"})

VERIFICATION_STATUSES = frozenset(
    {"completed", "error", "timeout", "refused", "not_run"}
)

_VERIFICATION_ACQUISITION_CHANNELS = frozenset(
    {"artefact_execution", "browser_observation"}
)

_KNOWLEDGE_ACQUISITION_CHANNELS = frozenset(
    {"primary_source_retrieval", "novel_corpus_observation"}
)

ACQUISITION_STANCES = frozenset({"supports", "opposes"})

ACQUISITION_SOURCE_STATUSES = frozenset({"FULL", "ABS"})

RECORD_CAPTURED_KIND = "record.captured"

RECORD_KIND_ALIASES = frozenset(
    {"record.capture", "record_captured", "records.captured"}
)

CAPABILITY_VERSIONED_KIND = "capability.versioned"

MODEL_CHANGE_KIND = "model.change"

MODEL_CHANGE_STATUSES = frozenset({"started", "succeeded", "failed", "refused"})

_DATA_DRIVEN_PROCEDURES = frozenset({"closed_form", "embedding_fit", "optimiser"})

_NON_DATA_DRIVEN_PROCEDURES = frozenset({"direct_edit"})

_RETRIEVAL_PROCEDURES = frozenset({"embedding_inference", "frozen_embedding"})

_UNKNOWN_DISPOSITIONS = frozenset({"n/a", "none", "unknown", "unspecified"})

CAPABILITY_MANIFEST_KINDS = frozenset({"tool", "mcp", "skill", "plugin", "connection"})

_HEX = frozenset("0123456789abcdef")

CAPABILITY_GAP_KIND = "capability.gap"

GAP_FAILURES = frozenset({"failed", "silent", "refused", "not_implemented"})

GAP_CLOSURES = frozenset({"retry", "escalate"})

INTENT_RECORDED_KIND = "intent.recorded"

INTENT_STARVED_KIND = "intent.starved"

SCHEDULER_ACTOR = "consilient.scheduler"

INTENT_RECORDED_FIELDS = frozenset({"tick", "selected", "not_selected"})

INTENT_STARVED_FIELDS = frozenset({"unit", "reason", "ticks", "since"})

ESCALATION_ATTEMPTED_KIND = "escalation.attempted"

ESCALATION_ACTOR = "consilient.escalation"

ESCALATION_BUDGET = 3

ESCALATION_WINDOW = timedelta(hours=24)

ESCALATION_PRECISION_WINDOW = 20

ESCALATION_PRECISION_FLOOR = 0.7

# The four non-selection reasons of the supervision specification, section 2.1, and no
# fifth. A bench recorded under an unnamed reason is the failure the record exists to
# make visible.
INTENT_REASON_PREFIXES = ("blocked_on:", "quota_exhausted:", "breaker_open:")

INTENT_REASONS = frozenset({"no_capacity"})

# "6 ticks or 60 minutes, whichever is longer" - both floors, not either
# [asserted, preferential; supervision specification section 2.1].
STARVATION_TICKS = 6

STARVATION_WINDOW = timedelta(minutes=60)

# The project's evidence tags (AGENTS.md working principle 1). A usage figure that
# cannot name which of these it is has no business being displayed as a number.
PROVENANCE = frozenset({"measured", "cited", "asserted"})

USAGE_STATUSES = frozenset({"ok", "unavailable", "not_configured"})

BUDGET_LOCK = ".budget.lock"

_BUDGET_LOCK_HELD: ContextVar[Path | None] = ContextVar(
    "consilient_budget_lock", default=None
)

# RFC3339 with an explicit offset or Z. A naive timestamp is rejected: replay across machines
# must not depend on the reader's timezone.
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

# ADR-0057: sharing is opt-in and purpose-specific. An existing grant never becomes
# authority for another purpose; commercial training is authorised one use at a time.
CONSENT_GRANTED = "consent.granted"

CONSENT_WITHDRAWN = "consent.withdrawn"

# feedback-signals.md: the unit of feedback is the task, and the close surface is
# asked of the user, never the agent. Three durable kinds make a skip never re-asked:
# the ask and the decline are recorded, so "have we already asked about this task" is
# a query over the log, not a guess. The asked event carries the goal text verbatim
# from the pre-committed goal record — the surface renders the goal, nothing the
# agent wrote (anti-gaming rule 3).
FEEDBACK_ASKED_KIND = "feedback.asked"

FEEDBACK_DECLINED_KIND = "feedback.declined"

FEEDBACK_ANSWERED_KIND = "feedback.answered"

GOAL_ACHIEVED = frozenset({"fully", "partially", "no"})

# ADR-0076: immutable impact contracts and typed promoter-beta receipts (S01).
IMPACT_CONTRACT_KIND = "promote.impact_contract.registered"

PROMOTER_BETA_RECEIPT_KIND = "promote.promoter_beta.receipt"

ACTIVATION_REFUSED_KIND = "promote.activation.refused"

CANONICAL_ON_OTHER = "no activation"

PROMOTE_ACTOR = "consilient.promote"

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# ADR-0035: four levels, milestones by default; the dial changes what is displayed,
# never what is recorded. The change event exists so β can be stratified by the
# conditions the verdict was produced under — which is the only measurement that
# justifies the dial. The floor and its config-load validation are the CLI's half.
VISIBILITY_LEVELS = ("silent", "milestones", "decisions", "firehose")

VISIBILITY_DEFAULT = "milestones"

VISIBILITY_CHANGE_KIND = "visibility.change"

DELIVERY_ESTIMATE_KIND = "delivery.estimate"

MEASUREMENT_REGISTERED_KIND = "measurement.registered"

MEASUREMENT_RESULT_KIND = "measurement.result"

MEASUREMENT_ACTOR = "consilient.measurement"

DELIVERY_ACTOR = "consilient.delivery"


class EventError(ValueError):
    """An event was rejected before it reached the log."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _check_review_queue_contract(event: EventPayload) -> None:
    kind = event["event"]
    if kind == REVIEW_QUEUE_OPENED_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "stream_cap",
            "exp105_prefix_n",
            "rejection_target",
            "population",
            "task_family",
            "protocol_id",
            "verifier_version",
            "verifier_contract_digest",
            "start_position",
            "eligible_universe_digest",
            "selector",
            "order_rule",
        }
        actual = set(data)
        if actual != required:
            missing = sorted(required - actual)
            unexpected = sorted(actual - required)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if unexpected:
                detail.append(f"unexpected {unexpected}")
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} body fields are fixed: {'; '.join(detail)}"
            )
        if int(data["stream_cap"]) != 90:
            raise EventError(f"{REVIEW_QUEUE_OPENED_KIND} stream_cap is fixed at 90")
        if int(data["exp105_prefix_n"]) != 30:
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} exp105_prefix_n is fixed at 30"
            )
        if data["selector"] != "first_matching_trajectory_order":
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} selector must be "
                "'first_matching_trajectory_order'"
            )
        for field in ("verifier_contract_digest", "eligible_universe_digest"):
            digest = data[field]
            if (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise EventError(
                    f"{REVIEW_QUEUE_OPENED_KIND} {field} must be 64 lowercase hex characters"
                )
        for field in ("rejection_target", "start_position"):
            value = data[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise EventError(
                    f"{REVIEW_QUEUE_OPENED_KIND} {field} must be a non-negative integer"
                )
        from . import verification as verification_mod

        recomputed = verification_mod.eligible_universe_digest(
            task_family=cast(str, data["task_family"]),
            population=cast(str, data["population"]),
            protocol_id=cast(str, data["protocol_id"]),
            verifier_version=cast(str, data["verifier_version"]),
            verifier_contract_digest=cast(str, data["verifier_contract_digest"]),
            order_rule=cast(str, data["order_rule"]),
        )
        if data["eligible_universe_digest"] != recomputed:
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} eligible_universe_digest does not match the "
                "frozen manifest"
            )
        return

    if kind == CANDIDATE_EXPOSED_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "exposure_id",
            "attempt_id",
            "exposure_ordinal",
            "start_token",
            "artefact_sha256",
            "task_family",
            "protocol_id",
            "verifier_version",
            "verifier_contract_digest",
        }
        actual = set(data)
        if actual != required:
            missing = sorted(required - actual)
            unexpected = sorted(actual - required)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if unexpected:
                detail.append(f"unexpected {unexpected}")
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} body fields are fixed: {'; '.join(detail)}"
            )
        ordinal = data["exposure_ordinal"]
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal <= 0:
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} exposure_ordinal must be a positive integer"
            )
        for field in ("start_token", "artefact_sha256", "verifier_contract_digest"):
            digest = data[field]
            if (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise EventError(
                    f"{CANDIDATE_EXPOSED_KIND} {field} must be 64 lowercase hex characters"
                )
        return

    if kind == ATTEMPT_REVIEWED_KIND:
        data = event["data"]
        required = {"queue_id", "exposure_id", "attempt_id", "disposition"}
        if set(data) != required:
            raise EventError(f"{ATTEMPT_REVIEWED_KIND} body fields are fixed")
        if data["disposition"] not in ("unclear",):
            raise EventError(
                f"{ATTEMPT_REVIEWED_KIND} disposition must be 'unclear' until Q02 ingress"
            )
        return

    if kind == REVIEW_PRESENTATION_FROZEN_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "exposure_id",
            "attempt_id",
            "contract_digest",
            "artefact_digest",
            "component_rollup_digest",
            "presentation_digest",
        }
        if set(data) != required:
            raise EventError(f"{REVIEW_PRESENTATION_FROZEN_KIND} body fields are fixed")
        for field in (
            "contract_digest",
            "artefact_digest",
            "component_rollup_digest",
            "presentation_digest",
        ):
            digest = data[field]
            if (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise EventError(
                    f"{REVIEW_PRESENTATION_FROZEN_KIND} {field} must be 64 lowercase hex "
                    "characters"
                )


MAX_CLOCK_SKEW_S = 15 * 60

# The transaction lock lives past every byte a reader will ever touch.
#
# MEASURED 25 August 2026: of 4,930 recorded dispatch deaths, 3,895 -- SEVENTY-NINE PERCENT --
# were readers refused on this file, across 106 units. It was the single largest cause of
# failure in the whole system, larger than every other cause combined.
#
# The mechanism was the lock offset. A Windows byte-range lock denies a reader that overlaps
# the locked region, and this lock was taken on BYTE 0 -- which is inside the region every
# reader reads. So for the entire duration of a transaction, including the full parse of the
# prefix that a transaction performs before it writes anything, every concurrent reader was
# denied. `read()` retries six times over ~2.5 s and then fails closed, correctly, but
# globally: a refused read fails the suite, and a failed suite blocks retirement, merging and
# publication together. As the log grew the hold grew with it, so the system got worse at
# exactly the rate it did work.
#
# Byte-range locks are per-REGION. Moving the lock to a byte beyond any plausible end of file
# keeps writers excluding each other -- they contend for the same sentinel -- while readers
# never overlap it at all. MEASURED with a two-process probe before this change
# (scratchpad/lock_region_experiment.py):
#
#   lock byte 0        reader DENIED (PermissionError)      writer refused (exclusion holds)
#   lock byte 2^40     reader read 2,000 lines in 0 ms      writer refused (exclusion holds)
#
# One terabyte. A JSONL trajectory reaching that offset has problems this lock cannot help
# with, and locking past EOF neither extends the file nor writes to it.
_TRANSACTION_LOCK_BYTE = 1 << 40

# Six attempts with doubling backoff from 40ms spans roughly 2.5s, which is far longer than a
# file replace holds the path, and short enough that a genuinely stuck file fails the dispatch
# rather than hanging it.
_READ_RETRIES = 6

_READ_ALL_CACHE_MAX = 4
