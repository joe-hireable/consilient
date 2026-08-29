"""V0-30: what a provider counter may claim. The rule is enforced at `append()` rather
than at the renderer, because a renderer is one of several things that could display the
number and the writer is the only thing all of them go through — working principle 3. A
provider that could not be read may not carry a figure, since a dashboard showing "0%"
for a provider nobody could read reports headroom that was never observed; the mirror
image is refused too, because an `ok` carrying nothing is a success claim about no
evidence. Every figure names one of the project's evidence tags, windows stay provider-
native with their reset times intact — the reset is the half a human acts on — and spend
that cannot be compared with a ceiling is not spend. Measured 20 August 2026: `cursor-
agent about --format json` returns a subscription tier with no quota, no consumed figure
and no reset window, and `grok inspect --json` exposes no remaining-quota percentage or
reset timestamp, so both report `unavailable` with a reason, because an unavailable with
no reason is exactly as unfalsifiable as an invented number. Codex's window is
`[measured]` from the response EXP-07 committed; Claude's are `[cited]` because EXP-27
recorded that surface as the string "status_line_json" and this repository has never
parsed one; the dashboard's fake snapshot is `asserted` throughout, so a fabricated
figure that leaks into a screenshot reads as fabricated. OpenRouter's counter read $0
and then $0.045138255 later — a true counter value and a false statement about spend —
which is why that collector reads recorded observations instead."""

import json
import sys
from datetime import datetime, timezone
import pytest
from consilient import events as events_mod
from consilient import projection
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    validate,
)
from v0_invariants_helpers import (
    _spend_scripts,
    now_ts,
    write_budget_state,
)

if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


# ------------------------------------------------ V0-30 / V0-31, usage, limits and spend
# PRODUCT, not instance. Nothing below names an account, a credential or a real balance.
from decimal import Decimal
from consilient import usage as usage_mod


def usage_event(**over):
    data = {
        "provider": "codex",
        "kind": "subscription",
        "status": "ok",
        "detail": "account/rateLimits/read",
        "observed_at": None,
        "quotas": [
            {
                "window": "10080m",
                "used_fraction": "0.05",
                "resets_at": now_ts(3600),
                "provenance": "measured",
            }
        ],
        "spend": [],
    }
    data.update(over)
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "usage.observed",
        "actor": "consilient.usage",
        "data": data,
    }


def as_event(result):
    """A collector's answer, in the form the one writer would have to accept."""
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "usage.observed",
        "actor": "consilient.usage",
        "data": usage_mod.as_payload(result),
    }


def test_a_provider_that_could_not_be_read_may_not_carry_a_figure():
    """V0-30. The invented number is how this feature goes wrong, so it is unwritable.

    A dashboard showing "0%" for a provider nobody could read is worse than one showing
    nothing: it reports headroom that was never observed, and the reader cannot tell the
    two apart. The rule is enforced at `append()` rather than at the renderer, because a
    renderer is one of several things that could display the number and the writer is the
    only thing all of them go through -- working principle 3.
    """
    for status in ("unavailable", "not_configured"):
        with pytest.raises(EventError, match="carries a figure"):
            validate(usage_event(status=status))
        with pytest.raises(EventError, match="carries a figure"):
            validate(
                usage_event(
                    status=status,
                    quotas=[],
                    spend=[
                        {
                            "amount": "0",
                            "currency": "USD",
                            "period": "monthly",
                            "provenance": "measured",
                        }
                    ],
                )
            )
    # And the mirror image: "ok" carrying nothing is a success claim about no evidence.
    with pytest.raises(EventError, match="no figure"):
        validate(usage_event(quotas=[], spend=[]))


def test_a_usage_figure_must_name_one_of_the_projects_evidence_tags():
    """V0-30. `[measured]`, `[cited]` or `[asserted]`. An untagged number reads as fact."""
    for bad in (None, "", "probably", "MEASURED", 1):
        quota = dict(usage_event()["data"]["quotas"][0])
        quota["provenance"] = bad
        with pytest.raises(EventError, match="provenance"):
            validate(usage_event(quotas=[quota]))

    for tag in sorted(events_mod.PROVENANCE):
        quota = dict(usage_event()["data"]["quotas"][0])
        quota["provenance"] = tag
        validate(usage_event(quotas=[quota]))


def test_a_quota_keeps_its_window_and_reset_and_spend_keeps_its_currency():
    """V0-30. A subscription window and a metered charge are different measurements.

    `backends.md`: "Resource windows remain provider-native and separately keyed; a
    five-hour, seven-day or monthly bucket is not flattened into one generic reset." The
    reset time is the part a human acts on, so collapsing a window into one percentage
    would delete the only half of the answer that says when it stops being a problem.
    """
    quota = dict(usage_event()["data"]["quotas"][0])
    del quota["window"]
    with pytest.raises(EventError, match="provider-native window"):
        validate(usage_event(quotas=[quota]))

    quota = dict(usage_event()["data"]["quotas"][0])
    quota["resets_at"] = "2026-08-28 09:00:00"  # no offset: unreadable across machines
    with pytest.raises(EventError, match="resets_at"):
        validate(usage_event(quotas=[quota]))

    # Spend that cannot be compared with a ceiling is not spend.
    with pytest.raises(EventError, match="currency"):
        validate(
            usage_event(
                kind="metered",
                quotas=[],
                spend=[
                    {"amount": "1.00", "period": "weekly", "provenance": "measured"}
                ],
            )
        )


def test_a_used_fraction_outside_zero_to_one_is_refused():
    """V0-30. A percentage written into a fraction field is a factor-of-100 error."""
    quota = dict(usage_event()["data"]["quotas"][0])
    quota["used_fraction"] = "5"
    with pytest.raises(EventError, match="0, 1"):
        validate(usage_event(quotas=[quota]))


def test_providers_with_no_counter_say_unavailable_and_give_the_reason(tmp_path):
    """V0-30, at the collector rather than at the writer.

    Measured 20 August 2026: `cursor-agent about --format json` returns `subscriptionTier`
    with no quota, no consumed figure and no reset window; `grok inspect --json` exposes no
    individual remaining-quota percentage, allowance counter or reset timestamp. These are
    the two providers most likely to acquire a fabricated zero, because a dashboard row
    that says nothing looks like a bug to whoever is asked to fix it.

    The reason string is asserted too. An "unavailable" with no reason is exactly as
    unfalsifiable as an invented number: nobody can tell whether it is a fact about the
    vendor or a collector somebody never finished.
    """
    (tmp_path / "cursor.json").write_text(
        '{"subscriptionTier": "ultra"}', encoding="utf-8"
    )
    (tmp_path / "grok.json").write_text('{"model": "grok-4.6"}', encoding="utf-8")
    sources = usage_mod.Sources(payloads=tmp_path, log=tmp_path / "log")

    for provider in ("cursor", "grok"):
        result = usage_mod.COLLECTORS[provider](sources)
        assert result.status == "unavailable", provider
        assert result.quotas == () and result.spend == (), provider
        assert len(result.detail) > 40, f"{provider} gave no reason for unavailable"
        validate(as_event(result))


def test_an_absent_provider_degrades_to_not_configured_rather_than_failing(tmp_path):
    """A collector must never raise. An empty directory is an installation, not an error."""
    sources = usage_mod.Sources(payloads=tmp_path / "nothing", log=tmp_path / "nolog")
    for name, collector in sorted(usage_mod.COLLECTORS.items()):
        result = collector(sources)
        assert result.status in ("not_configured", "unavailable"), name
        assert result.quotas == () and result.spend == (), name
        validate(as_event(result))

    snapshot = usage_mod.snapshot(sources)
    assert [p["provider"] for p in snapshot["providers"]] == sorted(
        usage_mod.COLLECTORS
    )
    assert all(p["status"] != "ok" for p in snapshot["providers"])


def test_the_measured_codex_payload_parses_to_a_quota_that_keeps_its_reset(tmp_path):
    """The one subscription whose headroom schema this repository actually measured.

    EXP-07 queried `codex app-server --stdio` with `account/rateLimits/read` and committed
    the response. These are its field names and its values, so this fails if the parser
    drifts from the shape that was really observed. [measured]
    """
    (tmp_path / "codex.json").write_text(
        json.dumps(
            {
                "result": {
                    "rateLimits": {
                        "planType": "pro",
                        "primary": {
                            "usedPercent": 5,
                            "resetsAt": 1787767120,
                            "windowDurationMins": 10080,
                        },
                        "rateLimitReachedType": None,
                        "spendControlReached": False,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    result = usage_mod.COLLECTORS["codex"](
        usage_mod.Sources(payloads=tmp_path, log=tmp_path)
    )

    assert result.status == "ok"
    assert result.spend == (), "a flat-fee subscription window is not money"
    (quota,) = result.quotas
    assert quota.used_fraction == Decimal("0.05")
    assert quota.window == "10080m", "the seven-day window must stay provider-native"
    assert quota.resets_at == datetime.fromtimestamp(1787767120, timezone.utc)
    assert quota.provenance == "measured"
    validate(as_event(result))


def test_a_payload_present_but_carrying_no_counter_is_unavailable_not_zero(tmp_path):
    """The exact failure this layer exists to prevent, at the parser."""
    (tmp_path / "codex.json").write_text(
        '{"result": {"rateLimits": {}}}', encoding="utf-8"
    )
    (tmp_path / "claude.json").write_text('{"windows": []}', encoding="utf-8")
    sources = usage_mod.Sources(payloads=tmp_path, log=tmp_path)

    for provider in ("codex", "claude"):
        result = usage_mod.COLLECTORS[provider](sources)
        assert result.status == "unavailable", provider
        assert result.quotas == (), provider


def test_claude_figures_are_cited_because_the_schema_was_never_verified_here(tmp_path):
    """V0-30. `[cited]` is not pedantry; it is the difference from `[measured]`.

    Anthropic documents five-hour and seven-day utilisation and reset fields. EXP-27
    recorded Claude's quota surface as the *string* "status_line_json", inferred from the
    CLI being installed -- this repository has never parsed one. Tagging these figures
    `measured` would upgrade an evidence class without new evidence, which working
    principle 1 forbids in as many words.
    """
    (tmp_path / "claude.json").write_text(
        json.dumps(
            {
                "windows": [
                    {"window": "5h", "used_percentage": 42, "resets_at": now_ts(3600)},
                    {"window": "7d", "used_percentage": 8, "resets_at": now_ts(86400)},
                ]
            }
        ),
        encoding="utf-8",
    )
    result = usage_mod.COLLECTORS["claude"](
        usage_mod.Sources(payloads=tmp_path, log=tmp_path)
    )

    assert result.status == "ok"
    assert [q.window for q in result.quotas] == ["5h", "7d"]
    assert {q.provenance for q in result.quotas} == {"cited"}
    assert all(q.resets_at is not None for q in result.quotas)


def test_openrouter_spend_is_unknown_rather_than_zero_without_an_observation(tmp_path):
    """Measured 20 Aug 2026: the key-status counter read $0, then $0.045138255 later.

    The zero was a true counter value and a false statement about spend. Reporting "no
    observation" is the only reading of an empty trajectory that is not a claim about
    money, which is why this collector reads recorded observations rather than a counter.
    """
    log = tmp_path / "log"
    log.mkdir()
    result = usage_mod.COLLECTORS["openrouter"](
        usage_mod.Sources(payloads=tmp_path, log=log)
    )
    assert result.status == "unavailable"
    assert "not zero" in result.detail
    assert result.spend == ()

    write_budget_state(log, "1.50", "4.25")
    result = usage_mod.COLLECTORS["openrouter"](
        usage_mod.Sources(payloads=tmp_path, log=log)
    )
    assert result.status == "ok"
    assert result.quotas == (), "metered spend is not a subscription window"
    assert {(s.period, str(s.amount), s.currency) for s in result.spend} == {
        ("weekly", "1.50", "USD"),
        ("monthly", "4.25", "USD"),
    }
    assert {s.provenance for s in result.spend} == {"measured"}
    validate(as_event(result))


def test_the_fake_snapshot_obeys_the_same_contract_as_a_real_one():
    """The dashboard's fixture must not be able to drift from what the writer accepts.

    A fake a renderer can display but `append()` would refuse is a fake that teaches the
    renderer to handle shapes the real system never produces.
    """
    snapshot = usage_mod.fake_snapshot()
    statuses = {p["status"] for p in snapshot["providers"]}
    assert statuses == {"ok", "unavailable", "not_configured"}, (
        "the fixture must exercise every case a renderer has to handle"
    )
    for provider in snapshot["providers"]:
        validate(
            {
                "v": SCHEMA_VERSION,
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "usage.observed",
                "actor": "consilient.usage",
                "data": provider,
            }
        )
    figures = [
        figure
        for provider in snapshot["providers"]
        for figure in list(provider["quotas"]) + list(provider["spend"])
    ]
    assert figures and all(f["provenance"] == "asserted" for f in figures), (
        "a fabricated figure that leaks into a screenshot must read as fabricated"
    )


def test_usage_observations_reach_the_trajectory_and_project_including_silent_ones(
    tmp_path,
):
    """V0-02 and V0-30 together: the projection is rebuilt from the log, and shows absence.

    A provider that could not be read still gets a row. Projecting only the readable ones
    would make "unobserved" indistinguishable from "never asked", which is the silent skip
    the rejections table already exists to prevent.
    """
    log, db = tmp_path / "log", tmp_path / "state.db"
    log.mkdir()
    assert usage_mod.record(log, usage_mod.fake_snapshot()) == 4
    assert not events_mod.bypassed(log), "usage must be written through append() only"

    conn = projection.build(log, db)
    rows = conn.execute(
        "SELECT provider, status, measure, window_label, used_fraction, resets_at,"
        " amount, currency, period, provenance FROM usage ORDER BY id"
    ).fetchall()
    by_provider: dict[str, list[tuple[object, ...]]] = {}
    for row in rows:
        by_provider.setdefault(row[0], []).append(row)

    (silent,) = by_provider["fake-no-counter"]
    assert silent[1] == "unavailable" and silent[2] == "none"
    assert silent[9] is None, (
        "a provider that reported nothing must carry no provenance"
    )
    (absent,) = by_provider["fake-absent"]
    assert absent[1] == "not_configured" and absent[2] == "none"
    assert {row[2] for row in by_provider["fake-metered"]} == {"spend"}
    assert {row[7] for row in by_provider["fake-metered"]} == {"USD"}
    assert {row[8] for row in by_provider["fake-metered"]} == {"weekly", "monthly"}
    windows = by_provider["fake-subscription"]
    assert {row[3] for row in windows} == {"10080m", "300m"}, (
        "provider-native windows were flattened into one"
    )
    assert all(row[5] is not None for row in windows), "a reset time was lost"
    assert all(row[6] is None for row in windows), "a quota acquired a money column"

    digest = projection.state_digest(conn)
    conn.close()
    rebuilt = projection.build(log, db)
    assert projection.state_digest(rebuilt) == digest
    rebuilt.close()
