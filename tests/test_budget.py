import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    canonical,
    read_all,
    rejection_digest,
    validate,
)


FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "dotenv",
    "ftplib",
    "getpass",
    "http",
    "httpx",
    "keyring",
    "openai",
    "openrouter",
    "requests",
    "smtplib",
    "socket",
    "subprocess",
    "telnetlib",
    "urllib",
    "urllib3",
    "webbrowser",
    "xmlrpc",
}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "getpass.getpass",
    "importlib.import_module",
    "os.environ.get",
    "os.getenv",
    "os.popen",
    "os.system",
}
BUDGET_IMPORTS = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "events",
    "pathlib",
    "typing",
}
PRODUCT_IMPORTS = BUDGET_IMPORTS | {
    "",
    "argparse",
    "contextlib",
    "contextvars",
    "hashlib",
    "json",
    "math",
    "re",
    "shutil",
    "sqlite3",
    "sys",
}
FORBIDDEN_METHODS = {
    "complete",
    "completion",
    "delete",
    "invoke",
    "patch",
    "post",
    "put",
    "request",
    "send",
    "sendall",
}
BUDGET_FORBIDDEN_METHODS = {"open", "read_bytes", "read_text"}


def qualified_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def capability_violations(source, *, budget_module=False, product_module=False):
    tree = ast.parse(source)
    aliases = {}
    violations = []
    allowed_imports = (
        BUDGET_IMPORTS
        if budget_module
        else PRODUCT_IMPORTS if product_module else None
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                aliases[name.asname or name.name.split(".")[0]] = name.name
                if name.name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(f"forbidden import {name.name}")
                if allowed_imports is not None and name.name not in allowed_imports:
                    violations.append(f"non-refuse-only import {name.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                target = f"{module}.{name.name}" if module else name.name
                aliases[name.asname or name.name] = target
            if module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"forbidden import {module}")
            if allowed_imports is not None and module not in allowed_imports:
                violations.append(f"non-refuse-only import {module}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = qualified_name(node.func)
            root, _, rest = name.partition(".")
            resolved = aliases.get(root, root) + (f".{rest}" if rest else "")
            if (
                resolved in FORBIDDEN_CALLS
                or resolved.split(".")[0] in FORBIDDEN_IMPORT_ROOTS
                or resolved.rsplit(".", 1)[-1] in FORBIDDEN_METHODS
                or (
                    budget_module
                    and resolved.rsplit(".", 1)[-1] in BUDGET_FORBIDDEN_METHODS
                )
            ):
                violations.append(f"forbidden call {resolved}")
        elif isinstance(node, ast.Subscript):
            name = qualified_name(node.value)
            root, _, rest = name.partition(".")
            resolved = aliases.get(root, root) + (f".{rest}" if rest else "")
            if resolved == "os.environ":
                violations.append("forbidden credential environment read")
            if (
                resolved == "__builtins__"
                and isinstance(node.slice, ast.Constant)
                and node.slice.value in {"__import__", "eval", "exec"}
            ):
                violations.append("forbidden dynamic execution lookup")
    return violations


def assert_refuse_only(source, *, budget_module=False, product_module=False):
    violations = capability_violations(
        source, budget_module=budget_module, product_module=product_module
    )
    assert not violations, f"forbidden capability: {violations}"


def budget_state(
    now,
    *,
    weekly="0",
    monthly="0",
    currency="USD",
    observed_at=None,
    rejection_fingerprint=None,
):
    return {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "budget.state",
        "actor": "openrouter-probe",
        "data": {
            "provider": "openrouter",
            "currency": currency,
            "weekly_spent": weekly,
            "monthly_spent": monthly,
            "observed_at": (observed_at or now).isoformat(),
            "rejection_digest": rejection_fingerprint or rejection_digest([]),
        },
    }


def write_state(log_dir, now, **over):
    path = log_dir / f"{now.date().isoformat()}.jsonl"
    over.setdefault("rejection_fingerprint", rejection_digest(read_all(log_dir)[1]))
    append(path, budget_state(now, **over))
    return path


def test_no_ceilings_refuses(tmp_path):
    from consilient import budget

    request = budget.SpendRequest("run-1", Decimal("1.00"), "USD")

    decision = budget.check_budget(tmp_path, (), request)

    assert isinstance(decision, budget.BudgetRefusal)
    assert decision.reason == "no weekly or monthly ceiling is configured"


def test_weekly_ceiling_alone_permits_and_persists_its_attribution(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now, weekly="2.00", monthly="99.00")
    before = log.read_bytes()
    request = budget.SpendRequest("run-42", Decimal("1.25"), "USD")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("4.00"), "USD"),),
        request,
    )

    assert isinstance(decision, budget.BudgetPermission)
    assert decision.record["event"] == "spend.reserved"
    assert decision.record["data"] == {
        "provider": "openrouter",
        "run_id": "run-42",
        "amount": "1.25",
        "currency": "USD",
        "state_observed_at": now.isoformat(),
    }
    assert "human_decision" not in decision.record["data"]
    assert validate(decision.record) == decision.record
    assert log.read_bytes() != before
    events, rejected = read_all(tmp_path)
    assert not rejected
    assert events[-1].raw == decision.record


@pytest.mark.parametrize(
    ("weekly_spent", "monthly_spent", "expected"),
    (
        ("9.00", "1.00", "weekly ceiling would be breached"),
        ("1.00", "9.00", "monthly ceiling would be breached"),
    ),
)
def test_breaching_either_configured_ceiling_refuses(
    tmp_path, weekly_spent, monthly_spent, expected
):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly=weekly_spent, monthly=monthly_spent)

    decision = budget.check_budget(
        tmp_path,
        (
            budget.Ceiling("weekly", Decimal("10.00"), "USD"),
            budget.Ceiling("monthly", Decimal("10.00"), "USD"),
        ),
        budget.SpendRequest("run-limit", Decimal("2.00"), "USD"),
    )

    assert decision == budget.BudgetRefusal(expected)


def test_appended_reservations_accumulate_and_exact_ceiling_is_allowed(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1.00", monthly="1.00")
    ceiling = (budget.Ceiling("weekly", Decimal("3.00"), "USD"),)

    exact = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-exact", Decimal("2.00"), "USD"),
    )
    assert isinstance(exact, budget.BudgetPermission)

    over = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-over", Decimal("0.01"), "USD"),
    )
    assert over == budget.BudgetRefusal("weekly ceiling would be breached")


def test_concurrent_permissions_cannot_jointly_oversubscribe(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)
    ceiling = (budget.Ceiling("weekly", Decimal("1.00"), "USD"),)

    def check(run_id):
        return budget.check_budget(
            tmp_path,
            ceiling,
            budget.SpendRequest(run_id, Decimal("0.75"), "USD"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = list(pool.map(check, ("run-a", "run-b")))

    assert sum(isinstance(d, budget.BudgetPermission) for d in decisions) == 1
    events, rejected = read_all(tmp_path)
    assert not rejected
    assert sum(event.kind == "spend.reserved" for event in events) == 1


def test_new_snapshot_does_not_release_an_unreconciled_reservation(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now)
    ceiling = (budget.Ceiling("weekly", Decimal("5.00"), "USD"),)
    first = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-in-flight", Decimal("4.00"), "USD"),
    )
    assert isinstance(first, budget.BudgetPermission)
    append(log, budget_state(now, weekly="0.00", monthly="0.00"))

    second = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-next", Decimal("2.00"), "USD"),
    )

    assert second == budget.BudgetRefusal("weekly ceiling would be breached")


def test_newest_observation_wins_over_a_later_delayed_snapshot(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    append(log, budget_state(now, weekly="5", observed_at=now - timedelta(seconds=2)))
    append(
        log,
        budget_state(
            now + timedelta(microseconds=1),
            weekly="0",
            observed_at=now - timedelta(seconds=10),
        ),
    )

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-delayed-state", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_ceiling_sequence_is_snapshotted_once(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="5")
    ceiling = budget.Ceiling("weekly", Decimal("5"), "USD")

    class ChangingCeilings:
        def __init__(self):
            self.iterations = 0

        def __len__(self):
            return 1

        def __iter__(self):
            self.iterations += 1
            return iter((ceiling,)) if self.iterations == 1 else iter(())

    decision = budget.check_budget(
        tmp_path,
        ChangingCeilings(),
        budget.SpendRequest("run-changing-config", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_request_without_an_attributable_run_refuses(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("   ", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("request must name a non-empty run_id")


def test_non_request_object_refuses(tmp_path):
    from consilient import budget

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        object(),
    )

    assert decision == budget.BudgetRefusal("request is malformed")


@pytest.mark.parametrize("amount", (Decimal("0"), Decimal("-1"), Decimal("NaN"), 0.1))
def test_non_positive_non_finite_or_binary_float_request_refuses(tmp_path, amount):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-money", amount, "USD"),
    )

    assert decision == budget.BudgetRefusal(
        "request amount must be a finite positive Decimal"
    )


def test_currencies_are_compared_exactly_and_never_converted(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, currency="USD")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "GBP"),),
        budget.SpendRequest("run-currency", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal(
        "request, ceilings and state must use one currency; no conversion is performed"
    )


def test_absent_and_unreadable_state_refuse(tmp_path):
    from consilient import budget

    ceiling = (budget.Ceiling("weekly", Decimal("5"), "USD"),)
    request = budget.SpendRequest("run-state", Decimal("1"), "USD")

    absent = budget.check_budget(tmp_path, ceiling, request)
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("not trajectory state", encoding="utf-8")
    unreadable = budget.check_budget(not_a_directory, ceiling, request)

    assert absent == budget.BudgetRefusal("budget state is absent")
    assert unreadable == budget.BudgetRefusal("budget state is unreadable")


def test_state_observation_older_than_fifteen_minutes_refuses(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, observed_at=now - timedelta(minutes=15, microseconds=1))

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-stale", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")


def test_state_that_expires_between_read_and_reservation_refuses(tmp_path, monkeypatch):
    from consilient import budget

    observed = datetime.now(timezone.utc)
    write_state(tmp_path, observed)
    times = iter(
        (
            observed + timedelta(minutes=14, seconds=59),
            observed + timedelta(minutes=15, microseconds=1),
        )
    )
    monkeypatch.setattr(budget, "_utc_now", lambda: next(times))

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-expiring", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")
    events, _ = read_all(tmp_path)
    assert all(event.kind != "spend.reserved" for event in events)


def test_malformed_state_refuses_instead_of_assuming_zero_spend(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    malformed = budget_state(now)
    del malformed["data"]["monthly_spent"]
    (tmp_path / f"{now.date().isoformat()}.jsonl").write_text(
        canonical(malformed) + "\n", encoding="utf-8"
    )

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-malformed", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")


def test_fresh_state_supersedes_old_quarantine_but_not_a_new_one(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text("{old malformed line}\n", encoding="utf-8")
    fingerprint = rejection_digest(read_all(tmp_path)[1])
    append(log, budget_state(now, rejection_fingerprint=fingerprint))
    ceiling = (budget.Ceiling("weekly", Decimal("5"), "USD"),)
    request = budget.SpendRequest("run-quarantine", Decimal("1"), "USD")

    superseded = budget.check_budget(tmp_path, ceiling, request)
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{new malformed line}\n")
    current = budget.check_budget(tmp_path, ceiling, request)

    assert isinstance(superseded, budget.BudgetPermission)
    assert current == budget.BudgetRefusal("budget state is unreadable")


def test_quarantine_digest_detects_a_same_count_replacement(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text("{first malformed line}\n", encoding="utf-8")
    fingerprint = rejection_digest(read_all(tmp_path)[1])
    append(log, budget_state(now, rejection_fingerprint=fingerprint))
    lines = log.read_text(encoding="utf-8").splitlines(keepends=True)
    log.write_text("{replacement malformed line}\n" + "".join(lines[1:]), encoding="utf-8")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-replaced", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")


def test_budget_state_requires_its_declared_writer(tmp_path):
    now = datetime.now(timezone.utc)
    state = budget_state(now)
    state["actor"] = "untrusted-agent"
    log = tmp_path / f"{now.date().isoformat()}.jsonl"

    with pytest.raises(EventError, match="declared writer 'openrouter-probe'"):
        append(log, state)

    assert not log.exists()


def test_generic_budget_writes_respect_the_admission_lock(tmp_path):
    now = datetime.now(timezone.utc)
    lock = tmp_path / ".budget.lock"
    lock.touch()
    try:
        with pytest.raises(EventError, match="budget trajectory is busy"):
            append(tmp_path / f"{now.date().isoformat()}.jsonl", budget_state(now))
    finally:
        lock.unlink()


def test_budget_events_require_real_utc_timestamps(tmp_path):
    now = datetime.now(timezone.utc)
    impossible = budget_state(now)
    impossible["ts"] = "2026-99-99T00:00:00+00:00"
    offset = budget_state(now.astimezone(timezone(timedelta(hours=1))))
    overflowing = budget_state(now)
    overflowing["data"]["observed_at"] = "0001-01-01T00:00:00+14:00"

    with pytest.raises(EventError, match="valid calendar timestamp"):
        append(tmp_path / "2026-99-99.jsonl", impossible)
    with pytest.raises(EventError, match="ts must use UTC"):
        append(tmp_path / f"{now.date().isoformat()}.jsonl", offset)
    with pytest.raises(EventError, match="observed_at cannot be normalised to UTC"):
        append(tmp_path / f"{now.date().isoformat()}.jsonl", overflowing)


def test_budget_state_contract_is_enforced_at_the_append_chokepoint(tmp_path):
    now = datetime.now(timezone.utc)
    malformed = budget_state(now)
    del malformed["data"]["monthly_spent"]
    log = tmp_path / "state.jsonl"

    with pytest.raises(EventError, match="budget.state.*monthly_spent"):
        append(log, malformed)

    assert not log.exists(), "an invalid state event must not reach the trajectory"


def test_budget_events_must_use_their_timestamped_daily_file(tmp_path):
    now = datetime.now(timezone.utc)
    wrong = tmp_path / "2000-01-01.jsonl"

    with pytest.raises(EventError, match="timestamped daily file"):
        append(wrong, budget_state(now))

    assert not wrong.exists()


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("run_id", "   ", "run_id"),
        ("amount", "NaN", "finite positive"),
        ("currency", "GBP", "currency 'USD'"),
        ("provider", "another-vendor", "provider 'openrouter'"),
    ),
)
def test_spend_reservation_contract_is_enforced_at_append(
    tmp_path, field, value, match
):
    now = datetime.now(timezone.utc)
    record = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "spend.reserved",
        "actor": "consilient.budget",
        "data": {
            "provider": "openrouter",
            "run_id": "run-valid",
            "amount": "1.00",
            "currency": "USD",
            "state_observed_at": now.isoformat(),
        },
    }
    record["data"][field] = value
    log = tmp_path / "spend.jsonl"

    with pytest.raises(EventError, match=match):
        append(log, record)

    assert not log.exists(), "an invalid reservation must not reach the trajectory"


@pytest.mark.parametrize(
    "ceilings",
    (
        (
            # Runtime validation must still reject values that evade the Literal type.
            lambda budget: (budget.Ceiling("daily", Decimal("5"), "USD"),)
        ),
        (
            lambda budget: (
                budget.Ceiling("weekly", Decimal("5"), "USD"),
                budget.Ceiling("weekly", Decimal("6"), "USD"),
            )
        ),
        (lambda budget: (budget.Ceiling("weekly", Decimal("NaN"), "USD"),)),
        (lambda budget: (budget.Ceiling("weekly", -1.0, "USD"),)),
        (lambda budget: (object(),)),
        (lambda budget: (budget.Ceiling("weekly", Decimal("1"), ["USD"]),)),
    ),
)
def test_malformed_ceiling_configuration_refuses(tmp_path, ceilings):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        ceilings(budget),
        budget.SpendRequest("run-config", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("ceiling configuration is malformed")


@pytest.mark.parametrize(
    ("now", "observed_at"),
    (
        (
            datetime(2026, 8, 3, 0, 5, tzinfo=timezone.utc),
            datetime(2026, 8, 2, 23, 55, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc),
            datetime(2026, 8, 31, 23, 55, tzinfo=timezone.utc),
        ),
    ),
)
def test_state_from_a_previous_utc_budget_period_is_stale(
    tmp_path, monkeypatch, now, observed_at
):
    from consilient import budget

    monkeypatch.setattr(budget, "_utc_now", lambda: now)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text(
        canonical(budget_state(now, observed_at=observed_at)) + "\n", encoding="utf-8"
    )

    decision = budget.check_budget(
        tmp_path,
        (
            budget.Ceiling("weekly", Decimal("5"), "USD"),
            budget.Ceiling("monthly", Decimal("5"), "USD"),
        ),
        budget.SpendRequest("run-period", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")


def test_malformed_reservation_after_state_refuses_without_crashing(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now)
    malformed = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "spend.reserved",
        "actor": "consilient.budget",
        "data": {
            "provider": "openrouter",
            "run_id": "run-bad-record",
            "currency": "USD",
            "state_observed_at": now.isoformat(),
        },
    }
    with log.open("a", encoding="utf-8") as fh:
        fh.write(canonical(malformed) + "\n")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-next", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")


def test_extreme_decimal_exponents_refuse_instead_of_overflowing(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1e999999999", monthly="0")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("1e999999999"), "USD"),),
        budget.SpendRequest("run-overflow", Decimal("1e999999999"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget values cannot be compared")


def test_positive_request_cannot_round_away_at_a_large_exhausted_ceiling(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    exhausted = "9999999999999999999999999999"
    write_state(tmp_path, now, weekly=exhausted)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal(exhausted), "USD"),),
        budget.SpendRequest("run-precision", Decimal("0.1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_ambient_decimal_precision_cannot_change_the_decision(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1.01")
    with localcontext() as ambient:
        ambient.prec = 1
        decision = budget.check_budget(
            tmp_path,
            (budget.Ceiling("weekly", Decimal("1.02"), "USD"),),
            budget.SpendRequest("run-context", Decimal("0.01"), "USD"),
        )

    assert isinstance(decision, budget.BudgetPermission)


def test_product_tree_has_no_outbound_or_credential_capability():
    source_root = Path("src/consilient")
    budget_path = source_root / "budget.py"
    assert_refuse_only(budget_path.read_text(encoding="utf-8"), budget_module=True)
    for path in source_root.rglob("*.py"):
        assert_refuse_only(path.read_text(encoding="utf-8"), product_module=True)


@pytest.mark.parametrize(
    "source",
    (
        "import requests as remote\nremote.post('https://example.invalid')",
        "from subprocess import run as execute\nexecute(['provider'])",
        "import os as operating_system\nkey = operating_system.environ['API_KEY']",
        "def call(provider):\n    provider.complete()",
        "from pathlib import Path\nkey = Path('openrouter.key').read_text()",
        "def call(gateway):\n    getattr(gateway, 'get')('https://example.invalid')",
        "getattr(__builtins__, '__import__')('socket')",
    ),
)
def test_refuse_only_ast_guard_has_a_failing_negative_control(source):
    with pytest.raises(AssertionError, match="forbidden capability"):
        assert_refuse_only(source, budget_module=True)


@pytest.mark.parametrize(
    "source",
    (
        "from http import client\nclient.HTTPSConnection('example.invalid')",
        "def call(gateway):\n    gateway.send(b'data')",
        "eval('1 + 1')",
        "loader = __builtins__['__import__']\nloader('socket')",
        "import boto3",
    ),
)
def test_product_tree_ast_guard_has_a_failing_negative_control(source):
    with pytest.raises(AssertionError, match="forbidden capability"):
        assert_refuse_only(source, product_module=True)
