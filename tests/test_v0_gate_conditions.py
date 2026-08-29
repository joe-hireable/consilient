"""What `consil doctor` reports condition by condition, and whether a condition can be
reported at all. Measured 20 August 2026: of the seven gate conditions, four could not
be satisfied — A3 only by breaking capture, which is the data loss it exists to detect;
B4 circular by construction; and B2 and B3 with no `pass` branch anywhere in the code,
so no artefact anyone could build would make them pass. The AST test that established
that is here, and its known-unpassable set is now EMPTY and may only shrink: a condition
that cannot report `pass` is a wall rather than a gate, and the correct response to a
new one is to give it a success path, not to add its name to the set. B4's tests pin
both halves of the repair — twenty tickets orchestrated on another repository required
Stage 3, which required Gate B, and ADR-0039 separated entry from exit so the honest
report became a count, currently zero — and its conditionality: revert ADR-0039 and B4
must go back to reporting `structurally_unsatisfiable` rather than quietly counting
toward something unreachable, which is what stops the amendment being a one-way door
taken by an agent. Tickets on this repository do not count, aliases of its own name do
not count, and a bare `ticket.completed` with no verifier acceptance does not count. A2
is here because comparing zero events to zero events is not evidence that replay works —
measured 21 August 2026 from a clean install in an empty directory, two `doctor` runs
reported A2 `pass` over zero events."""

import sys

from family_source import family_source
from consilient import projection
from consilient.events import (
    append,
)
from v0_invariants_helpers import (
    _gate_b,
    _spend_scripts,
    doctor_payload,
    ev,
    write_capture_days,
)


def test_doctor_fails_a_gapped_capture_run_and_names_the_gap(tmp_path, capsys):
    write_capture_days(tmp_path / "log", "2026-08-14", "2026-08-15", "2026-08-17")

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3" and condition["status"] == "fail"
    assert "2026-08-16" in condition["reason"]


def test_doctor_passes_seven_clean_consecutive_capture_days(tmp_path, capsys):
    write_capture_days(
        tmp_path / "log",
        "2026-08-14",
        "2026-08-15",
        "2026-08-16",
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
    )

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3" and condition["status"] == "pass"


def test_doctor_reports_a_quarantined_line_in_the_seven_day_run(tmp_path, capsys):
    """Amended by ADR-0043, accepted 20 August 2026. This test used to assert FAIL.

    It asserted that a single quarantined line inside the window fails A3. That was the
    behaviour which made A3 unsatisfiable: refusals are permanent in an append-only log, so
    the condition could only ever be met by breaking capture — losing a day of data in order
    to satisfy "no data loss".

    The half of the old assertion that survives, and the half worth pinning, is the
    REPORTING. ADR-0043 says pre-existing refusals are "counted, reported, and non-blocking".
    Non-blocking is covered by `test_a3_tolerates_the_recorded_historical_refusals`, blocking
    on a new one by `test_a3_still_fails_on_one_new_refusal`. This one guards the failure mode
    neither of those would catch — the count going quiet.
    """
    write_capture_days(
        tmp_path / "log",
        "2026-08-14",
        "2026-08-15",
        "2026-08-16",
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
    )
    with (tmp_path / "log" / "2026-08-20.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("not-json\n")

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3"
    assert "1 refused line(s)" in condition["reason"], (
        "a tolerated refusal must still be named in the verdict, never silently absorbed"
    )


def test_doctor_unknown_evidence_cannot_enable_control(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_capture_days(tmp_path / "log", "2026-08-20")

    payload = doctor_payload(tmp_path, capsys)
    condition = payload["gates"]["A"]["conditions"][0]

    assert condition["id"] == "A1" and condition["status"] == "unknown"
    assert condition["evidence"] == []
    assert {
        name: {item["id"] for item in gate["conditions"]}
        for name, gate in payload["gates"].items()
    } == {"A": {"A1", "A2", "A3"}, "B": {"B1", "B2", "B3", "B4"}}
    assert payload["routing_orchestration_enabled"] is False


def _accepted_b4_docs(root):
    """The two documents B4 reads: the circularity finding, and ADR-0039 accepting its repair."""
    circularity = root / "docs/00-context/gate-b-cannot-be-passed-2026-08-20.md"
    circularity.parent.mkdir(parents=True, exist_ok=True)
    circularity.write_text(
        "Condition 4 can only be satisfied by doing the thing the gate forbids\n",
        encoding="utf-8",
    )
    adr = (
        root
        / "docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md"
    )
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text(
        "# 0039. Stage 3 is entered on approval\n\n"
        "- **Status:** **ACCEPTED 20 August 2026.**\n",
        encoding="utf-8",
    )


def test_doctor_reports_gate_b4_as_unfinished_work_not_a_wall(tmp_path, capsys):
    """Amended after ADR-0039 was ACCEPTED. The circularity was real and is now resolved.

    B4 required twenty tickets orchestrated on another repository; orchestrating another
    repository was Stage 3; Stage 3 began only after Gate B. ADR-0039 separated entry from
    exit, so the work that produces this evidence is permitted and B4 gates *dependence*
    rather than construction.

    Continuing to report `structurally_unsatisfiable` would be reporting something an
    accepted decision has superseded — a check asserting a fact that is no longer true. The
    honest report is a count, and the count is zero.
    """
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][3]

    assert condition["id"] == "B4"
    assert condition["status"] == "fail"
    assert "0 of 20" in condition["reason"]
    assert any(
        source.endswith("gate-b-gates-dependence.md")
        for source in condition["evidence"]
    )


def test_gate_b4_still_reports_a_wall_if_adr_0039_is_not_accepted(
    tmp_path, capsys, monkeypatch
):
    """The repair is conditional on the decision, not on the code having been edited.

    If ADR-0039 were reverted, B4 must go back to reporting the circularity rather than
    quietly counting toward a condition that cannot be reached. This is what stops the
    amendment being a one-way door taken by an agent.
    """
    monkeypatch.chdir(tmp_path)
    for relative in (
        "docs/00-context/gate-b-cannot-be-passed-2026-08-20.md",
        "docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "Condition 4 can only be satisfied by doing the thing the gate forbids\n",
            encoding="utf-8",
        )
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][3]
    assert condition["status"] == "structurally_unsatisfiable"


def test_gate_b4_counts_only_validated_tickets_on_another_repository(
    tmp_path, capsys, monkeypatch
):
    """Tickets on this repository do not count, and neither do duplicates."""
    monkeypatch.chdir(tmp_path)
    _accepted_b4_docs(tmp_path)
    log = tmp_path / "log" / "2026-08-20.jsonl"
    for index in range(3):
        append(
            log,
            ev(
                event="attempt.outcome",
                data={
                    "repository": "other",
                    "attempt_id": f"att-{index}",
                    "task": f"ticket-{index}",
                    "verifier_accept": True,
                    "harness": "cursor-grok",
                    "corpus_revision": "test-fixture-pin-not-a-commit-sha",
                    "receipt_sha256": "a" * 64,
                },
            ),
        )
        append(
            log,
            ev(
                event="ticket.completed",
                data={
                    "repository": "other",
                    "ticket": f"ticket-{index}",
                    "attempt_id": f"att-{index}",
                },
            ),
        )
    append(
        log,
        ev(
            event="ticket.completed",
            data={
                "repository": "other",
                "ticket": "ticket-0",
                "attempt_id": "att-0",
            },
        ),
    )
    append(
        log,
        ev(
            event="ticket.completed",
            data={"repository": "consilient", "ticket": "ticket-99"},
        ),
    )

    condition = _gate_b(tmp_path, capsys)["B4"]
    assert "3 of 20" in condition["reason"], condition["reason"]


def _reachable_statuses() -> dict[str, set[str]]:
    """Which statuses can each gate condition in `doctor` actually emit?

    Reads `_condition(...)` call sites out of the AST. The status argument is either an
    expression containing string literals, or a local name assigned string literals inside
    the same function; both are resolved.
    """
    import ast

    # The gate conditions moved into a cli sibling on 28 August 2026; reading the entry
    # point alone found none of them and reported every requirement missing.
    source = family_source("cli")
    tree = ast.parse(source)
    reachable: dict[str, set[str]] = {}

    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        assigned: dict[str, set[str]] = {}
        delegated = _delegated_calls(function)
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                literals = {
                    n.value
                    for n in ast.walk(node.value)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                }
                for name in names:
                    assigned.setdefault(name, set()).update(literals)

        for node in ast.walk(function):
            call = node
            if not isinstance(call, ast.Call):
                continue
            if not (isinstance(call.func, ast.Name) and call.func.id == "_condition"):
                continue
            if len(call.args) < 2:
                continue
            identifier, status = call.args[0], call.args[1]
            if not (
                isinstance(identifier, ast.Constant)
                and isinstance(identifier.value, str)
            ):
                continue
            found = {
                n.value
                for n in ast.walk(status)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            }
            if isinstance(status, ast.Name):
                found |= assigned.get(status.id, set())
                found |= _returned_literals(tree, delegated.get(status.id, set()))
            reachable.setdefault(identifier.value, set()).update(found)

    return reachable


def _delegated_calls(function) -> dict[str, set[str]]:
    """Local helper names a status variable was assigned from, e.g. `s, r = _helper()`."""
    import ast

    out: dict[str, set[str]] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        callee = node.value.func
        if not isinstance(callee, ast.Name):
            continue
        names: set[str] = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Tuple):
                names |= {e.id for e in target.elts if isinstance(e, ast.Name)}
        for name in names:
            out.setdefault(name, set()).add(callee.id)
    return out


def _returned_literals(tree, callees: set[str]) -> set[str]:
    """String literals any of the named module-level functions can return."""
    import ast

    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name not in callees:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Return) and inner.value is not None:
                found |= {
                    c.value
                    for c in ast.walk(inner.value)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                }
    return found


def test_every_gate_condition_has_a_reachable_pass_state():
    """A gate condition that cannot report PASS is not a gate, it is a wall.

    Measured 20 Aug 2026: of the seven conditions, four cannot be satisfied. A3 is
    satisfiable only by breaking capture, which is the data loss it exists to detect
    (ADR-0043). B4 is circular by construction (ADR-0039). And **B2 and B3 have no `pass`
    branch at all** — every path through `_fallback_condition` and through B2's arm of
    `_experiment_conditions` returns `unknown` or `fail`, so no artefact anyone could build
    would make them pass.

    The set is now EMPTY. B2 and B3 were given success criteria by ADR-0045 and ADR-0046, and
    B4 stopped being circular when ADR-0039 was accepted — all on the day this test was
    written. Every one of the seven conditions can now report `pass`.

    That is the whole point: an empty set means every gate condition is a gate. If a future
    condition arrives without a success path, this fails, and the correct response is to give
    it one rather than to add its name here.

    The three are grandfathered BY NAME and the set may only SHRINK. Adding an identifier
    here is not permitted; removing one is the whole point.
    """
    from consilient.cli import REQUIREMENTS

    reachable = _reachable_statuses()
    assert set(reachable) == set(REQUIREMENTS), (
        f"conditions found in the AST {sorted(reachable)} do not match "
        f"REQUIREMENTS {sorted(REQUIREMENTS)}"
    )

    known_unpassable: set[str] = set()
    unpassable = {key for key, statuses in reachable.items() if "pass" not in statuses}
    assert unpassable <= known_unpassable, (
        f"a gate condition lost its pass state: {sorted(unpassable - known_unpassable)}. "
        "A condition that cannot report pass is a wall, not a gate."
    )


def test_gate_b4_ignores_bare_ticket_completed_and_repo_aliases(
    tmp_path, capsys, monkeypatch
):
    """Gate B4 ignores bare ticket.completed without verifier acceptance and filters internal repo aliases."""
    monkeypatch.chdir(tmp_path)
    _accepted_b4_docs(tmp_path)
    log = tmp_path / "log" / "2026-08-20.jsonl"

    # Bare ticket.completed without attempt.outcome is ignored
    append(
        log,
        ev(
            event="ticket.completed",
            data={"repository": "foreign-repo", "ticket": "T1"},
        ),
    )
    # Internal repo aliases are ignored even with outcome
    for idx, alias in enumerate(
        ("consilient", "consilience", "joe-hireable/consilient", "consilient-work")
    ):
        append(
            log,
            ev(
                event="attempt.outcome",
                data={
                    "repository": alias,
                    "attempt_id": f"a-{idx}",
                    "task": f"T-{idx}",
                    "verifier_accept": True,
                },
            ),
        )
        append(
            log,
            ev(
                event="ticket.completed",
                data={
                    "repository": alias,
                    "ticket": f"T-{idx}",
                    "attempt_id": f"a-{idx}",
                },
            ),
        )

    condition = _gate_b(tmp_path, capsys)["B4"]
    assert "0 of 20" in condition["reason"], condition["reason"]


def test_gate_a2_does_not_pass_on_an_empty_trajectory(tmp_path, capsys):
    """Comparing zero events to zero events is not evidence that replay works.

    Measured 21 August 2026 from a clean install in an empty directory: two `consil doctor`
    runs reported A2 `pass`, reason "Compared 0 events; canonical state is identical." The
    first run creates the state the second one compares against, and both are rebuilds of
    the same empty log. That is A1 — two rebuilds compared — one invocation further out.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    log_dir.mkdir(parents=True)
    projection.build(log_dir, db).close()  # a prior projection exists, over zero events

    condition = {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"]
    }["A2"]

    assert condition["status"] == "unknown", condition["reason"]
    assert "zero events" in condition["reason"]


def test_gate_a2_still_passes_on_a_non_empty_identical_replay(tmp_path, capsys):
    """The narrowing must not have blunted the condition it narrows."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    write_capture_days(log_dir, "2026-08-20")
    projection.build(log_dir, db).close()

    condition = {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"]
    }["A2"]

    assert condition["status"] == "pass", condition["reason"]
    assert "Compared 1 events" in condition["reason"]


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)
