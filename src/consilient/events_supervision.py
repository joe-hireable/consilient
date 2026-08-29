"""The records that make an unattended loop supervisable afterwards.

A loop that runs without anyone watching is only acceptable if it leaves behind enough
for someone to check it later, and these are the four records that carry that burden.
The scheduler writes each tick: what was ready, what it selected, and — for everything
it did not — which of the named non-selection reasons applied, and no fifth reason,
because a bench recorded under an unnamed reason is the failure the record exists to
make visible. An escalation is one exact, closed record of interrupting the principal
(ADR-0075). A promotion registers its immutable impact contract and its typed promoter-β
receipt (ADR-0076). Consent is purpose-specific: an existing grant never becomes
authority for another purpose, and a grant with no stated retention is the gap ADR-0057
forbids shipping.

`bypassed` is the companion to all of them. It reports the lines in a log that never
came through the single writer at all — because a single writer is only a single writer
if something goes looking for the writes that went around it, and lines written straight
to the file by something else are how events V0-18 forbids got in before anything was
checking."""

from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path
from .events_vocabulary import (
    CONSENT_PURPOSES,
    ESCALATION_ATTEMPT_FIELDS,
    ESCALATION_REFUSAL_REASONS,
)

from .events_durability import (
    _check_intent_reason,
)

from .events_evidence import (
    _retry_sleep,
)

from .events_fields import (
    CONSENT_KINDS,
    ESCALATION_CLASSES,
    PROMOTE_CONTRACT_KINDS,
    _canonical_token,
    _intent_timestamp,
    canonical,
)

from .events_kinds import (
    CANONICAL_ON_OTHER,
    CONSENT_GRANTED,
    DIGEST_RE,
    ESCALATION_ATTEMPTED_KIND,
    EventError,
    EventPayload,
    IMPACT_CONTRACT_KIND,
    INTENT_RECORDED_FIELDS,
    INTENT_RECORDED_KIND,
    INTENT_STARVED_FIELDS,
    INTENT_STARVED_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    PROMOTE_ACTOR,
    STARVATION_TICKS,
    _READ_RETRIES,
)


__all__ = [
    "CANONICAL_ON_OTHER",
    "CONSENT_GRANTED",
    "CONSENT_KINDS",
    "CONSENT_PURPOSES",
    "DIGEST_RE",
    "ESCALATION_ATTEMPTED_KIND",
    "ESCALATION_ATTEMPT_FIELDS",
    "ESCALATION_CLASSES",
    "ESCALATION_REFUSAL_REASONS",
    "EventError",
    "EventPayload",
    "IMPACT_CONTRACT_KIND",
    "INTENT_RECORDED_FIELDS",
    "INTENT_RECORDED_KIND",
    "INTENT_STARVED_FIELDS",
    "INTENT_STARVED_KIND",
    "PROMOTER_BETA_RECEIPT_KIND",
    "PROMOTE_ACTOR",
    "PROMOTE_CONTRACT_KINDS",
    "STARVATION_TICKS",
    "_READ_RETRIES",
    "_canonical_token",
    "_check_intent_reason",
    "_intent_timestamp",
    "_retry_sleep",
    "bypassed",
    "canonical",
]


def _check_intent_contract(event: EventPayload) -> None:
    """The scheduler's own record: what was ready, what ran, and why the rest did not.

    Every other supervision mechanism counts failures. F-08 produced no dispatch, no
    lease and no call, so it was invisible to all of them for two days [measured,
    `docs/00-context/orchestration-failure-modes-2026-08-23.md`]. Non-selection is only
    countable if the reason is written down at the tick, under a fixed vocabulary.
    """
    kind = event["event"]
    if kind not in (INTENT_RECORDED_KIND, INTENT_STARVED_KIND):
        return
    data = event["data"]
    expected = (
        INTENT_RECORDED_FIELDS
        if kind == INTENT_RECORDED_KIND
        else INTENT_STARVED_FIELDS
    )
    unexpected = sorted(set(data) - expected)
    if unexpected:
        raise EventError(f"{kind} carries unexpected field(s) {unexpected}")
    missing = sorted(expected - set(data))
    if missing:
        raise EventError(f"{kind} must carry {missing}")

    if kind == INTENT_STARVED_KIND:
        for field in ("unit", "since"):
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                raise EventError(f"{kind} must carry a non-empty string {field}")
        _intent_timestamp(data["since"], f"{kind} since")
        _check_intent_reason(data["reason"], kind)
        ticks = data["ticks"]
        if not isinstance(ticks, int) or isinstance(ticks, bool):
            raise EventError(f"{kind} ticks must be an integer")
        if ticks < STARVATION_TICKS:
            raise EventError(
                f"{kind} claims a threshold that was not crossed: ticks {ticks} "
                f"is below {STARVATION_TICKS}"
            )
        return

    tick = data["tick"]
    if not isinstance(tick, int) or isinstance(tick, bool) or tick < 0:
        raise EventError(f"{kind} tick must be a non-negative integer")
    selected = data["selected"]
    if not isinstance(selected, list) or any(
        not isinstance(unit, str) or not unit.strip() for unit in selected
    ):
        raise EventError(f"{kind} selected must be a list of unit names")
    not_selected = data["not_selected"]
    if not isinstance(not_selected, dict):
        raise EventError(f"{kind} not_selected must be an object of unit to reason")
    for unit, reason in not_selected.items():
        if not isinstance(unit, str) or not unit.strip():
            raise EventError(f"{kind} not_selected must be keyed by unit name")
        _check_intent_reason(reason, f"{kind} {unit}")
    both = sorted(set(selected) & set(not_selected))
    if both:
        raise EventError(
            f"{kind} unit(s) {both} cannot be both selected and not selected"
        )


def _check_escalation_contract(event: EventPayload) -> None:
    """ADR-0075: one exact, closed principal-interruption record."""
    if event["event"] != ESCALATION_ATTEMPTED_KIND:
        return
    data = event["data"]
    actual = set(data)
    if actual != ESCALATION_ATTEMPT_FIELDS:
        missing = sorted(ESCALATION_ATTEMPT_FIELDS - actual)
        unexpected = sorted(actual - ESCALATION_ATTEMPT_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{ESCALATION_ATTEMPTED_KIND} body fields are fixed: {'; '.join(detail)}"
        )
    for field in (
        "root_cause",
        "escalation_class",
        "what_stopped",
        "what_it_is_holding",
        "what_i_need",
        "evidence",
    ):
        _canonical_token(data[field], f"{ESCALATION_ATTEMPTED_KIND} {field}")
    default = data["default_if_no_reply"]
    if not isinstance(default, dict) or set(default) != {"default", "fires_at"}:
        raise EventError(
            f"{ESCALATION_ATTEMPTED_KIND} default_if_no_reply must contain default and fires_at"
        )
    _canonical_token(
        default["default"], f"{ESCALATION_ATTEMPTED_KIND} default_if_no_reply.default"
    )
    _intent_timestamp(
        default["fires_at"], f"{ESCALATION_ATTEMPTED_KIND} default_if_no_reply.fires_at"
    )

    disposition = data["disposition"]
    if disposition not in {"delivered", "refused"}:
        raise EventError(
            f"{ESCALATION_ATTEMPTED_KIND} disposition must be delivered or refused"
        )
    decision_changed = data["decision_changed"]
    if decision_changed is not None and not isinstance(decision_changed, bool):
        raise EventError(
            f"{ESCALATION_ATTEMPTED_KIND} decision_changed must be boolean or null"
        )
    refusal_reason = data["refusal_reason"]
    escalation_class = data["escalation_class"]
    if escalation_class not in ESCALATION_CLASSES:
        if disposition == "delivered" and refusal_reason is None:
            # The locked writer below converts raw candidates to refusal.
            return
        if disposition != "refused" or refusal_reason != "out_of_set_class":
            raise EventError(
                f"{ESCALATION_ATTEMPTED_KIND} out-of-set classes must be refused"
            )
        return
    if disposition == "delivered":
        if refusal_reason is not None:
            raise EventError(
                f"{ESCALATION_ATTEMPTED_KIND} delivered attempts carry no refusal_reason"
            )
        return
    if refusal_reason not in ESCALATION_REFUSAL_REASONS - {"out_of_set_class"}:
        raise EventError(
            f"{ESCALATION_ATTEMPTED_KIND} refused attempts require a machine-readable reason"
        )


def _check_promote_contract(event: EventPayload) -> None:
    """ADR-0076: registered impact contracts and promoter-beta receipts are typed."""
    kind = event["event"]
    if kind not in PROMOTE_CONTRACT_KINDS:
        return
    if event["actor"] != PROMOTE_ACTOR:
        raise EventError(
            f"{kind} must be attributed to declared writer {PROMOTE_ACTOR!r}"
        )
    data = event["data"]
    if kind == IMPACT_CONTRACT_KIND:
        experiment_id = data.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            raise EventError(f"{kind} must carry a non-empty experiment_id")
        digest_value = data.get("registration_digest")
        if (
            not isinstance(digest_value, str)
            or DIGEST_RE.fullmatch(digest_value) is None
        ):
            raise EventError(
                f"{kind} must carry registration_digest as a lowercase SHA-256 digest"
            )
        contract = data.get("contract")
        if not isinstance(contract, dict):
            raise EventError(f"{kind} must carry contract as an object")
        on_other = contract.get("on_other")
        if (
            not isinstance(on_other, str)
            or on_other.strip().casefold() != CANONICAL_ON_OTHER
        ):
            raise EventError(
                f"{kind} contract.on_other cannot be weakened; must be {CANONICAL_ON_OTHER!r}"
            )
        return
    if kind == PROMOTER_BETA_RECEIPT_KIND:
        if data.get("receipt_kind") != "promoter_beta":
            raise EventError(f"{kind} must carry receipt_kind promoter_beta")
        n_rejected = data.get("n_human_rejected")
        if not isinstance(n_rejected, int) or n_rejected < 30:
            raise EventError(f"{kind} must carry n_human_rejected as an integer >= 30")
        for field in (
            "qualification_rule_digest",
            "decision_surface_digest",
            "instrument_digest",
            "generator_policy_digest",
            "sampling_frame_digest",
            "interval_rule_digest",
        ):
            value = data.get(field)
            if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
                raise EventError(
                    f"{kind} must carry {field} as a lowercase SHA-256 digest"
                )
        interval = data.get("wilson_interval")
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or not all(isinstance(item, (int, float)) for item in interval)
        ):
            raise EventError(f"{kind} must carry wilson_interval as a two-number list")
        return
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(f"{kind} must carry a non-empty refusal reason")


def _check_consent_contract(event: EventPayload) -> None:
    """Consent is purpose-specific; commercial grants authorise one named use.

    ADR-0057 forbids shipping sharing until consent, retention and a checkable use
    limit exist. The exporter is not in this commit. These two fields are the part
    of that bar that can be enforced on the record itself: a grant with no purpose
    or no retention is the gap the ADR named, and omitting `human_decision` must
    not dodge V0-18 the way omitting it once dodged a verdict.
    """
    kind = event["event"]
    if kind not in CONSENT_KINDS:
        return
    data = event["data"]
    purpose = data.get("purpose")
    if not isinstance(purpose, str) or purpose not in CONSENT_PURPOSES:
        raise EventError(
            f"{kind} must declare purpose as one of {sorted(CONSENT_PURPOSES)}; "
            "purposes are not bundled"
        )
    if kind != CONSENT_GRANTED:
        grant_fields = sorted({"per_use", "use_ref"} & set(data))
        if grant_fields:
            raise EventError(
                f"{kind} is a withdrawal and must not carry commercial grant "
                f"field(s) {grant_fields}"
            )
        return
    retention = data.get("retention_days")
    if not isinstance(retention, int) or isinstance(retention, bool) or retention <= 0:
        raise EventError(
            f"{kind} must carry retention_days as a positive integer; "
            "a grant with no stated retention is the gap ADR-0057 forbids shipping"
        )
    try:
        datetime.fromisoformat(event["ts"]) + timedelta(days=retention)
    except OverflowError as exc:
        raise EventError(
            f"{kind} retention_days must produce a representable granted-until "
            "timestamp"
        ) from exc
    if purpose != "commercial-training":
        return
    if data.get("per_use") is not True:
        raise EventError(
            f"{kind} for commercial-training must carry per_use: true; commercial "
            "gain requires fresh consent for each use"
        )
    use_ref = data.get("use_ref")
    if not isinstance(use_ref, str) or not use_ref.strip():
        raise EventError(
            f"{kind} for commercial-training must carry use_ref as a non-empty "
            "string naming the single authorised use"
        )


def bypassed(directory: Path) -> list[tuple[str, int]]:
    """Lines that did not come through `append()`.

    `append` is documented as the only writer and is the only place `validate` runs. On
    20 August 2026, 92 of the 93 events in the real trajectory — 98.9% — had been written
    straight to the file by something else, which is how three events V0-18 forbids came
    to be in an authoritative record whose sole writer rejects them. [measured]

    That is `AGENTS.md` working principle 3 reproduced inside the artefact the principle
    was written about: a documented single boundary fragments into several access paths
    because no check bans the bypass.

    ponytail: canonical form is a proxy, not a boundary. It catches hand-written JSON,
    which is the failure that actually happened; it would not catch a writer that
    formatted its output correctly. The upgrade path if that ever matters is a per-event
    digest of the previous line, which cannot be applied retroactively to history.
    """
    out: list[tuple[str, int]] = []
    for path in sorted(directory.glob("*.jsonl")):
        # MEASURED 24 August 2026. Windows denies a reader while a writer holds the file, and
        # roughly twenty agents append here continuously, so this raised PermissionError and
        # failed the suite -- which then blocked retirement, merging and publication at once.
        # `read()` above already retries for exactly this reason; this path was written without
        # it. Same bound, same backoff, and the same refusal to report a partial trajectory:
        # after the last attempt it raises rather than returning a short list, because a
        # bypass check that silently sees fewer lines reports fewer bypasses.
        # The retry used to guard a zero-byte PROBE -- `probe.read(0)` -- and then break, after
        # which the real read happened in a second, unguarded `open`. That is check-then-act: a
        # writer can take the file between the probe succeeding and the read starting, and even
        # a perfect probe says nothing about the open that follows it. So the retry was
        # decorative, and the read it was written to protect still raised a raw PermissionError
        # straight through this function. MEASURED 24 August 2026, failing the suite from a live
        # trajectory that twelve consecutive manual reads had just read cleanly.
        #
        # The work now happens INSIDE the retry, and results accumulate into a local list that
        # only joins `out` once the whole file has been read. A retry after a partial read must
        # not report the lines it already saw twice.
        for attempt in range(_READ_RETRIES):
            found: list[tuple[str, int]] = []
            try:
                with path.open(encoding="utf-8") as fh:
                    for number, line in enumerate(fh, start=1):
                        line = line.rstrip("\n")
                        if not line.strip():
                            continue
                        try:
                            if canonical(json.loads(line)) != line:
                                found.append((str(path), number))
                        except json.JSONDecodeError:
                            found.append((str(path), number))
                out.extend(found)
                break
            except PermissionError as exc:
                if attempt == _READ_RETRIES - 1:
                    raise EventError(
                        f"{path} could not be read after {_READ_RETRIES} attempts: observed "
                        f"access denial ({exc}); it may be held by another process. The "
                        "trajectory is never partially reported -- refusing rather than "
                        "continuing against an incomplete history."
                    ) from exc
                _retry_sleep(attempt)
    return out
