"""Gate A3 and the capture record it reads. A3 was unsatisfiable before ADR-0043,
because refusals are permanent in an append-only log: unbroken capture failed at seven
days, at sixty and at 365, while a run that LOST a day passed — the only way to satisfy
"no data loss" was to lose data. The amendment tolerates a pinned historical baseline
and nothing more. One refusal above it still fails, a misdated line still fails because
a timestamp disagreeing with its own file is a live capture fault rather than a
historical judgement, a tolerated refusal must still be named in the verdict rather than
silently absorbed, and the tolerance itself may only fall — ADR-0105, accepted 26 August
2026, raised it once from three to six to baseline the 22 August torn-append refusals,
and it may not rise again without a further principal event. The digests are checked
against the live trajectory rather than against each other: until 21 August 2026 this
hashed the constant in this file and compared it with the constant in `cli.py`, two
hand-written values agreeing with themselves, and both could have drifted from the log
together while `_capture_condition` quietly widened the tolerance.
`test_no_new_event_may_bypass_append` is the ratchet beneath all of it — on 20 August
2026, 92 of 93 logged lines had been written straight to the file by something other
than `append()`, which is how three events V0-18 forbids reached an authoritative record
whose only writer rejects them — and the two `capture_health` tests keep A3's evidence a
check rather than a heartbeat, since a heartbeat proves a writer ran and says nothing
about the record."""

import sys
from pathlib import Path
import pytest
from consilient import events as events_mod
from consilient.cli import main
from consilient.events import (
    canonical,
)
from v0_invariants_helpers import (
    _against_live_trajectory,
    _read_live_trajectory,
    _spend_scripts,
    doctor_payload,
    ev,
    write_capture_days,
)

PINNED_TRAJECTORY_REJECTIONS: frozenset[tuple[str, int, str]] = frozenset(
    {
        (
            "2026-08-20.jsonl",
            62,
            "0fb234324063389745b5e79be163b8b6e3988a955d2a2fbd19f4036e225a7b90",
        ),
        (
            "2026-08-20.jsonl",
            63,
            "6921e71b2c687dd2f1f816410d20f53e106db1126bbf39fceeec02e33204f260",
        ),
        (
            "2026-08-20.jsonl",
            66,
            "65df9c30eeaf7095072eaada45ce276cbaca877b9540c48c519bcfdc729eb300",
        ),
        (
            "2026-08-22.jsonl",
            27,
            "305cfe4853e3d9576fd186f86cac2f3900805c44a75a41b0642a27e1da5741d3",
        ),
        (
            "2026-08-22.jsonl",
            35,
            "3769e62caa9131bb916fef24b40d46d70b49e19ee59a0686aa106b66eed15387",
        ),
        (
            "2026-08-22.jsonl",
            45,
            "6511adf8d1b5ef4aea3f542d610d261572c6a103d630775ce785ab2395a187ec",
        ),
    }
)

TORN_APPEND_LOCATIONS: frozenset[tuple[str, int]] = frozenset(
    (filename, line)
    for filename, line, _digest in PINNED_TRAJECTORY_REJECTIONS
    if filename == "2026-08-22.jsonl"
)


def test_no_new_event_may_bypass_append(tmp_path):
    """A ratchet on the real trajectory, not a fixture.

    `append` is the documented sole writer and the only place `validate` runs. On
    20 Aug 2026, 92 of 93 logged lines had been written straight to the file by something
    else — which is how three events V0-18 forbids reached an authoritative record whose
    only writer rejects them. That is working principle 3 (`AGENTS.md`) happening inside
    the artefact the principle was written about.

    History cannot be rewritten in an append-only log. Three torn concurrent appends on
    22 Aug did use `append()` but are invalid JSON, so this canonical-form proxy also reports
    them as bypasses. Their exact locations are owned by the rejection ratchet below and are
    removed here before retaining the original 92-line ceiling. A seventh or substituted
    rejection remains red; the historical A3 tolerance is not widened.
    """
    log = Path(".harness/log")
    if not log.exists():  # pragma: no cover - repository-only check
        pytest.skip("no repository trajectory in this checkout")
    bypassed = {
        (Path(path).name, line)
        for path, line in _against_live_trajectory(events_mod.bypassed, log)
    }
    assert TORN_APPEND_LOCATIONS <= bypassed, "the pinned torn-append incident changed"
    assert len(bypassed - TORN_APPEND_LOCATIONS) <= 92, (
        "a new event bypassed append(); write it with `consil record`"
    )


# ---------------------------------------------------------------- ADR-0043
def _a3(tmp_path, capsys):
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    return {c["id"]: c for c in gate_a["conditions"]}["A3"]


def test_a3_passes_seven_clean_days(tmp_path, capsys):
    """The amended condition is satisfiable at all, which the original was not."""
    log = tmp_path / "log"
    write_capture_days(log, *[f"2026-08-{day:02d}" for day in range(10, 17)])
    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]


HISTORICAL_REFUSAL_LINES: list[str] = [
    (
        '{"v": 1, "ts": "2026-08-20T09:41:46+01:00", "exp": "EXP-27", '
        '"event": "longitudinal.clock_started", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "implementer", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"authority": "Joe: \'YES PROCEED DONT WANT MONTHS OF DELAY\' - explicit approval for the '
        'read-only collector, which is new product-adjacent code and was the one gate he had to lift", '
        '"day_1": "09:39, all six fixed first-party sources reachable, 31 events frozen", '
        '"earliest_promotion": "19 September 2026, one day later for each day missed", '
        '"design": "conditional polling with ETag and If-Modified-Since; each event frozen by upstream id '
        'or content hash; one appended observation per source per run", "idempotent": "a second run '
        "within the same day returned 304 on every source and zero new events, so the day count cannot be "
        'inflated by re-running", "invariant_enforced_not_promised": "every emitted record passes '
        "validate_change_record, which raises on any record claiming to increase headroom, decrease usage, "
        "move a reset window or mark unknown headroom usable. Eleven tests, including one per forbidden action, "
        'plus one asserting that silence about headroom is not permission.", "no_inference_no_metered_provider": true, '
        '"owed": "the dispatch-time version/capability handshake (procedure step 4) and the three injected fixtures '
        "(step 5). Neither blocks the clock; both must land before the window closes or the run cannot answer its "
        'own question.", "scheduling_gap": "the collector must run once a day. Today\'s run is manual. A scheduled '
        "task or a daily invocation is needed and is not yet in place - if nobody runs it, the window silently "
        'accumulates missing days, which is exactly the failure the register warns about."}}\n'
    ),
    (
        '{"v": 1, "ts": "2026-08-20T09:42:46+01:00", "exp": "decision-protocol", '
        '"event": "autonomy.scope_widened", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "decision owner", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"quote": "I don\'t have any appetite for granular technical decisions - these need to be made by '
        'agents. Many users will prefer it this way.", "why_it_is_an_ADR_and_not_a_note": "the second sentence '
        "makes it a statement about who the product is for, not one maintainer's preference on one morning\", "
        '"unchanged": "the reserved list - money, credentials, anything published or exposed outside the machine, '
        'irrecoverable deletion, and genuine preference questions no fact settles", "now_explicit": "the converse '
        "the ADR implied and did not say: a technical question with a defensible answer is not a preference "
        'question and must not be escalated as one. Escalating one is a defect, not caution.", "named_classes": '
        '["which of two conditionals a quantity is defined on, where one is already implied by the code and the '
        'algebra", "which of several defensible estimators, thresholds or samples", "whether an experiment is '
        're-run and in what order work is done", "how an instrument is repaired and what its tests must cover", '
        '"any change reversible by one git revert, whatever its blast radius on paper"], "the_failure_it_prevents": '
        '"an ask the user cannot cheaply answer gets approved to keep things moving, and a rubber-stamped approval '
        "launders the agent's decision into a human one - worse than deciding, because it destroys the record of who "
        'actually chose", "obligation_replacing_the_ask": "every such decision carries, in the same commit, the '
        "reasoning including the option not taken, the reversal command rather than an assurance, and the falsifier. "
        "A decision recorded without a falsifier is a preference wearing a technical costume and should have been "
        'escalated.", "product_posture": "the harness decides technical questions and reports; the human decides '
        "irreversible and preferential ones and is asked. A user who wants more say turns the ADR-0035 visibility "
        'dial up rather than the harness asking more.", "overturning_test": "a user who wanted to be asked, was not, '
        "and lost something they cared about - measurable, and EXP-33 is where it would show. The unread-approval "
        "floor is the same signal from the other side: approvals returned faster than they could be read mean the asks "
        'were not wanted either."}}\n'
    ),
    (
        '{"v": 1, "ts": "2026-08-20T09:56:48+01:00", "exp": "EXP-27", '
        '"event": "collection.scheduled", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "implementer", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"authority": "Joe: \'exp 27 schedule what you need to schedule\' - explicit authorisation for a '
        'system-level change, a Windows scheduled task on his machine", "task": "Consilience-EXP27-Collector, '
        'daily 09:00, first fire 21 August 2026", "verified_by_artefact": "task Ready, next run 21/08 09:00, '
        "on-demand run returned Last Result 0, log grew 11 to 22 lines, six of six sources reachable - "
        'checked rather than inferred from the SUCCESS message", "settings_that_matter": {"StartWhenAvailable": '
        '"a laptop asleep at 09:00 runs on wake rather than skipping the day - the single most important setting", '
        '"RunOnlyIfNetworkAvailable": "a run with no network would record six failures and make the day look '
        'collected when it was not", "RestartOnFailure": "3 attempts 30 minutes apart, so a transient outage does '
        'not cost a day", "DisallowStartIfOnBatteries": "false, because the default would skip on battery, which '
        'on a laptop is most of the time", "InteractiveToken": "runs as Joe with no stored credentials. A day he '
        "never logs in is a day missed; storing a password to avoid that is not a trade worth making for a read-only "
        'poll."}, "wrapper_rationale": "a scheduled task that fails silently is worse than none, because the window '
        "accumulates missing days while looking healthy. run-daily.cmd prefers the worktree, falls back to the main "
        "checkout so it survives the branch being merged, writes a loud failure if the collector is in neither place, "
        'and preserves the exit code.", "branch_note": "the collector currently exists only on branch '
        "worktree-consilience-cto. Main is still at 27b4bc2, last night's handoff, and the main checkout has no "
        'collector.py. The wrapper\'s fallback handles the merge whenever it happens.", "how_to_tell_it_stopped": '
        "\"python collector.py prints 'distinct days recorded N of 30'. If N stops advancing the window has "
        "stalled regardless of what Task Scheduler claims. Running it by hand is idempotent - a second run the same "
        'day returns 304 everywhere and adds nothing.", "reversal": "schtasks /Delete /TN Consilience-EXP27-Collector /F. '
        'Touches nothing else, and the collected log survives deletion.", "still_owed": "the dispatch-time capability '
        "handshake and the three injected fixtures. Neither blocks the clock; both must land before the window "
        'closes or the run cannot answer its own question."}}\n'
    ),
]


def test_a3_tolerates_the_recorded_historical_refusals(tmp_path, capsys):
    """ADR-0043's whole content: a permanent refusal must not block forever.

    Before the amendment, unbroken capture failed A3 at 7 days, at 60 and at 365, while a run
    that LOST a day passed. The only way to satisfy "no data loss" was to lose data.
    """
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        for line in HISTORICAL_REFUSAL_LINES:
            fh.write(line)

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]
    assert "historical baseline" in condition["reason"]
    assert "0 are new" in condition["reason"]


def test_a3_still_fails_on_one_new_refusal(tmp_path, capsys):
    """The amendment is not a removal. One refusal above the baseline still fails."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        for line in HISTORICAL_REFUSAL_LINES:
            fh.write(line)
        fh.write("{not json}\n")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "1 are new" in condition["reason"]


def test_a3_still_fails_on_a_misdated_line(tmp_path, capsys):
    """Misdated lines are deliberately NOT ratcheted.

    A refusal is a historical judgement about a line that is present. A timestamp that
    disagrees with its own file is a live capture fault, and the amendment must not quietly
    tolerate it alongside the refusals.
    """
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(canonical(ev(ts="2026-07-01T12:00:00+00:00")) + "\n")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "misdated" in condition["reason"]


def test_the_capture_refusal_baseline_may_only_fall():
    """A ratchet on the tolerance itself, in the shape used for `append()` bypass.

    ADR-0043's own Evidence-against names the hazard: a ratchet with a non-zero floor can
    normalise its floor. ADR-0105 (accepted 26 August 2026, `decision.gate_amendment` in
    `.harness/log/2026-08-26.jsonl`) raised the floor once, from three to six, to also
    baseline the 22 August torn-append refusals. The number below is the measured ceiling
    after that one authorised raise; it may fall from here but not rise again without a
    further principal event.
    """
    from consilient.cli import CAPTURE_REFUSAL_BASELINE

    assert CAPTURE_REFUSAL_BASELINE <= 6, (
        "the A3 refusal tolerance was raised; ADR-0043/0105 permit it to fall only"
    )


# ------------------------------------------------- A3's evidence source
def _capture_health_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "capture_health", Path("scripts/capture_health.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_capture_health_reports_a_healthy_trajectory_and_a_broken_one(
    tmp_path, monkeypatch
):
    """A3's evidence must be a check, not a heartbeat.

    Until 20 Aug 2026 nothing wrote A3's trajectory daily. The log had files for two days
    because work happened on them; the only scheduled task on the machine writes a different
    file entirely. **A quiet day would have broken the consecutive run and reset A3 to one**,
    silently, while the gate looked like it was progressing.

    The fix must not be a heartbeat. A heartbeat proves a writer ran and says nothing about
    the record, which would turn A3 into a check that cannot fail — the exact defect this
    repository catalogued four times today. This asserts the opposite property: a corrupted
    log produces `healthy: false` rather than a cheerful line.
    """
    module = _capture_health_module()
    log = tmp_path / "log"
    monkeypatch.setattr(module, "LOG", log)
    monkeypatch.setattr(module, "DB", tmp_path / "state.db")

    write_capture_days(log, "2026-08-20")
    healthy = module.inspect()
    assert healthy["healthy"] is True
    assert healthy["events"] == 1
    assert healthy["state_digest"]

    # A line the reader refuses is reported, not fatal — the trajectory is still intact.
    with (log / "2026-08-20.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("{not json}\n")
    refused = module.inspect()
    assert refused["healthy"] is True
    assert refused["refused"] == 1, "a refused line must be counted, not hidden"


def test_capture_health_records_what_it_found(tmp_path, monkeypatch):
    """The recorded event must carry the digest, or it is a heartbeat after all."""
    module = _capture_health_module()
    log = tmp_path / "log"
    monkeypatch.setattr(module, "LOG", log)
    monkeypatch.setattr(module, "DB", tmp_path / "state.db")
    monkeypatch.setattr("sys.argv", ["capture_health.py"])
    write_capture_days(log, "2026-08-20")

    assert module.main() == 0

    events, rejected = _read_live_trajectory(log)
    assert not rejected
    recorded = [event for event in events if event.kind == module.CHECK_KIND]
    assert len(recorded) == 1
    data = recorded[0].raw["data"]
    assert data["healthy"] is True
    assert data["state_digest"], "the check must record the digest it verified"
    assert data["checked_by"] == "scripts/capture_health.py"


def test_historical_refusal_digests_pin_real_log_rejections():
    """Pin every rejection, and check the operational baseline against the full six-digest pin.

    Until 21 Aug 2026 this hashed `HISTORICAL_REFUSAL_LINES` from this file and checked the
    digests were in `cli.HISTORICAL_REFUSAL_DIGESTS` — two hand-written constants agreeing
    with each other. Both could drift from the log together and nothing would notice, while
    `_capture_condition` silently widened A3's tolerance. Three torn concurrent appends on
    22 Aug are also quarantined here, and since ADR-0105's acceptance on 26 August 2026 they
    belong in the operational A3 tolerance too. A new, removed or substituted rejection among
    either day's three still fails.
    """
    import hashlib
    from consilient.cli import HISTORICAL_REFUSAL_DIGESTS

    assert len(HISTORICAL_REFUSAL_DIGESTS) == 6
    for line in HISTORICAL_REFUSAL_LINES:
        digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
        assert digest in HISTORICAL_REFUSAL_DIGESTS, f"digest {digest} not in baseline"

    log = Path(".harness/log")
    if not log.exists():  # pragma: no cover - repository-only check
        pytest.skip("no repository trajectory in this checkout")
    if not (log / "2026-08-20.jsonl").exists():
        pytest.skip("historical repository trajectory is not present in this checkout")
    real = {
        (Path(rejection.path).name, rejection.line, rejection.content_digest)
        for rejection in _read_live_trajectory(log)[1]
    }
    assert real == PINNED_TRAJECTORY_REJECTIONS, (
        "the trajectory's exact rejection set changed; inspect the quarantine before "
        "updating an immutable incident pin"
    )
    assert set(HISTORICAL_REFUSAL_DIGESTS) == {
        digest for _filename, _line, digest in PINNED_TRAJECTORY_REJECTIONS
    }


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


def test_a3_fails_when_the_newest_day_holds_only_a_refusal(tmp_path, capsys):
    """The zero-valid-line day, which every other test in this file happens to avoid.

    MEASURED 29 August 2026. `_capture_condition` counted a day only when its file yielded a
    correctly-dated event, so a torn append landing as the FIRST line of a new day -- the exact
    fault class ADR-0105 baselined after the 22 August torn appends -- left the day out of the
    accounting entirely. A3 then reported a clean `7/7 days` run and never named the refusal.

    Every refusal and misdated test above appends its bad line to a day that already holds a
    valid event, so all of them passed while this hole was open.
    """
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    (log / "2026-08-17.jsonl").write_text("{not json}\n", encoding="utf-8")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "1 are new" in condition["reason"], condition["reason"]


def test_a3_fails_when_the_newest_day_holds_only_a_misdated_line(tmp_path, capsys):
    """The same hole, reached by a line that parses but carries the wrong date."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    (log / "2026-08-17.jsonl").write_text(
        canonical(ev(ts="2026-08-16T12:00:00+00:00")) + "\n", encoding="utf-8"
    )

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "misdated" in condition["reason"], condition["reason"]


def test_an_unreadable_daily_file_refuses_the_whole_report(tmp_path, capsys):
    """It does not reach A3 at all, and that is the correct behaviour.

    An outside review claimed a dated file that cannot be read is silently skipped, leaving A3
    to pass. MEASURED 29 August 2026: it is not. `events.read` retries six times and then
    refuses -- "the trajectory is never partially reported" -- so `consil doctor` emits a
    top-level error naming the unreadable path and exits 2 before any gate is evaluated.

    This test exists so that behaviour cannot be quietly softened into an A3 `fail`, which
    would report a verdict about a history nobody could read.
    """
    log = tmp_path / "log"
    write_capture_days(log, *[f"2026-08-{day:02d}" for day in range(10, 17)])
    (log / "2026-08-17.jsonl").mkdir()

    code = main(["--log", str(log), "--db", str(tmp_path / "s.db"), "--json", "doctor"])
    captured = capsys.readouterr()
    assert code == 2, captured.err
    assert not captured.out.strip(), "a refusal must not also emit a report"
    assert "2026-08-17.jsonl" in captured.err, captured.err


def test_a3_still_ignores_a_jsonl_whose_name_is_not_a_date(tmp_path, capsys):
    """The other half of that split: an unrelated jsonl must still be skipped silently."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    (log / "notes.jsonl").write_text("{not json}\n", encoding="utf-8")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]
