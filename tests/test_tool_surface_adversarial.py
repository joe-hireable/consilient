"""Adversarial suite over the registered tool surface (B09 / B9).

0% on the irreversible set is by construction of ``classify_reversibility``
and the absence of a live handle in the product tree — not by iterating
attacks until they fail. On the reversible set this file reports residual
and utility cost rather than a flattering rate.

A syntactic import-statement scan is not the boundary. The sealed evaluator
was escaped with ``__import__("sys")._getframe()`` because
``find_forbidden_imports`` walks only ``Import`` / ``ImportFrom``. This
suite measures that residual against the live function and refuses to rest
the irreversible 0% on it.

Incumbent, retrieved 2026-08-24: AgentDojo (arXiv:2406.13352) measures
attack success rate with an LLM in the loop; a tool-filter defence still
left 7.5% ASR at 53.3% utility [SNIP]. CaMeL (arXiv:2503.18813) bought
provable security by removing the model's authority over control flow at
84% → 77% utility [ABS]. This suite is the CaMeL-shaped claim applied to
our inventory: class 4 tools have no live handle here. It does not close
R1 (model-level injection). [cited]
"""

from __future__ import annotations

import ast
import hashlib
import inspect
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient.capabilities import (
    REGISTERED_TOOLS,
    CapabilityEntry,
    classify_reversibility,
    default_gate,
)
from consilient.effects import (
    AdmissionFacts,
    EffectManifest,
    derive_admission,
    OUTBOUND_EFFECTS,
)
from consilient.promote import find_forbidden_imports

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "src" / "consilient"

# Family "external" and default shell (no proven sandbox) are the irreversible
# set. Class 3 (subagent) is delegated, not this set. Class 1 is reversible.
IRREVERSIBLE_DEFAULT = tuple(
    (kind, name)
    for (kind, name), family in sorted(REGISTERED_TOOLS.items())
    if family in {"external", "shell"}
)
REVERSIBLE_DEFAULT = tuple(
    (kind, name)
    for (kind, name), family in sorted(REGISTERED_TOOLS.items())
    if family == "file"
)

GETFRAME_ESCAPE = """
def solve(prompt):
    frame = __import__("sys")._getframe()
    while frame is not None:
        for value in frame.f_locals.values():
            if value == prompt:
                return "leaked"
        frame = frame.f_back
    return "miss"
"""


def _default_class(family: str) -> int:
    if family == "file":
        return 1
    if family == "subagent":
        return 3
    return 4


def _commitment(domain: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": "a" * 64,
    }


def _broker(name: str) -> dict[str, str]:
    return {
        "kind": "broker_reference",
        "reference": f"broker://effects/{hashlib.sha256(name.encode()).hexdigest()}",
    }


def _manifest(
    *,
    effects: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
) -> EffectManifest:
    # Unit B01 made `disclosure` REQUIRED for outbound message.send effects, and only
    # permitted for those -- passing one on a non-outbound manifest is refused just as firmly
    # as omitting one on an outbound manifest. This helper predates that contract, so it now
    # supplies the digest exactly when the effect set calls for it. Weakening B01 to accept an
    # outbound send with no disclosure would delete the guarantee that a message this system
    # emits can always be traced to what it disclosed.
    disclosure = "b" * 64 if set(effects) & OUTBOUND_EFFECTS else None
    return EffectManifest(
        disclosure=disclosure,
        operation_id="operation-1",
        work_item_id="work-1",
        attempt_id="attempt-1",
        adapter={
            "id": "test.adapter",
            "version": "v1",
            "implementation_digest": "e" * 64,
        },
        forward=_commitment("effect.manifest.forward"),
        scope=_broker("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=_broker("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=_commitment("effect.manifest.start_state"),
        observer={"id": "observer-1", "policy_digest": "1" * 64},
        expected_state=_commitment("effect.manifest.expected_state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def _admitted(
    *,
    effect_classes: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
    grant_kind: str = "controller_baseline.local_restorable.v1",
) -> CapabilityEntry:
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    gate = default_gate()
    return CapabilityEntry(
        kind="tool",
        name="pytest",
        available=True,
        provenance=("probe:tool:pytest",),
        gate=type(gate)(
            state="admitted",
            reason="exact_grant",
            grant_kind=grant_kind,
            authority_event=None,
            decision_id="decision-1",
            recovery_proof_ref={
                "event_id": "evt-proof-1",
                "event_kind": "effect.receipt",
                "event_sha256": "c" * 64,
            },
            scope=("workspace",),
            operations=operations,
            effect_classes=effect_classes,
            expires_at=expires,
        ),
    )


def _import_statement_modules(source: str) -> set[str]:
    """The class of guard that missed the getframe escape: statements only."""
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".", 1)[0])
    return found


def _call_import_target(node: ast.Call) -> str | None:
    """The module name a `__import__(...)` / `importlib.import_module(...)` call names.

    MEASURED 26 August 2026: `_LIVE = __import__('subprocess')` reaches the exact same
    live handle as `import subprocess`, but is a Call node, not Import/ImportFrom, so the
    statement-only scan below missed it entirely -- the same class of gap the module
    docstring already names for the getframe escape, except this one governs the product
    tree's own "no live handle" claim, which the suite does not treat as an honest residual.
    """
    func = node.func
    name = None
    if isinstance(func, ast.Name) and func.id == "__import__":
        name = "__import__"
    elif (
        isinstance(func, ast.Attribute)
        and func.attr == "import_module"
        and isinstance(func.value, ast.Name)
        and func.value.id == "importlib"
    ):
        name = "import_module"
    if name is None or not node.args:
        return None
    arg = node.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value.split(".", 1)[0]
    return None


def _product_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            target = _call_import_target(node)
            if target:
                found.add(target)
    return found


def test_irreversible_set_is_class_4_under_default_facts() -> None:
    """0% by construction: the published table labels these 4 with no extra facts."""
    assert IRREVERSIBLE_DEFAULT, "registered irreversible set must be non-empty"
    for kind, name in IRREVERSIBLE_DEFAULT:
        assert classify_reversibility(kind, name) == 4


def test_reversible_set_stays_class_1_so_utility_is_not_sacrificed() -> None:
    """Closing class 1 to chase a flattering 0% would kill the zero-click path."""
    assert REVERSIBLE_DEFAULT, "registered reversible set must be non-empty"
    for kind, name in REVERSIBLE_DEFAULT:
        assert classify_reversibility(kind, name) == 1


@pytest.mark.parametrize(
    "alias",
    (
        "Bash",
        "BASH",
        " bash",
        "bash ",
        "bash\n",
        "webfetch\x00",
        "webfеtch",  # Cyrillic е — not the registered name
        "web_fetch",
        "web-fetch",
        "../webfetch",
        "tool:webfetch",
    ),
)
def test_adversarial_aliases_cannot_downgrade_an_irreversible_name(alias: str) -> None:
    assert classify_reversibility("tool", alias) == 4


@pytest.mark.parametrize(
    ("kind", "name"),
    (
        ("skill", "bash"),
        ("skill", "webfetch"),
        ("plugin", "read"),
        ("mcp", "bash"),
        ("connection", "read"),
        ("tool", "filesystem"),
        ("mcp", "webfetch"),
    ),
)
def test_kind_name_swap_is_class_4(kind: str, name: str) -> None:
    assert classify_reversibility(kind, name) == 4


@pytest.mark.parametrize(("kind", "name"), IRREVERSIBLE_DEFAULT)
def test_caller_supplied_sandbox_flag_cannot_downgrade_external_or_default_shell(
    kind: str, name: str
) -> None:
    family = REGISTERED_TOOLS[(kind, name)]
    if family == "external":
        assert (
            classify_reversibility(
                kind,
                name,
                default_deny_egress_proven=True,
                credential_reach=False,
                effect_classes=("data.read",),
            )
            == 4
        )
        return
    # Shell without a *real* sandbox stays 4. The boolean is a classifier
    # input, not a proof; passing True is the residual on the class-2 path,
    # reported in test_reversible_residual_caller_boolean_is_not_a_sandbox.
    assert classify_reversibility(kind, name) == 4


def test_extra_kwargs_cannot_smuggle_a_downgrade() -> None:
    with pytest.raises(TypeError):
        classify_reversibility("tool", "webfetch", proven=True)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "effect",
    (
        "network.call",
        "external.change",
        "message.send",
        "content.publish",
        "money.commit",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
        "system.change",
        "netwrok.call",
        "",
        "NETWORK.CALL",
    ),
)
def test_smuggled_or_typo_effects_keep_every_registered_tool_at_class_4(
    effect: str,
) -> None:
    for kind, name in REGISTERED_TOOLS:
        assert classify_reversibility(kind, name, effect_classes=(effect,)) == 4


def test_file_plus_process_run_is_class_4() -> None:
    assert classify_reversibility("tool", "read", effect_classes=("process.run",)) == 4
    assert classify_reversibility("tool", "write", effect_classes=("process.run",)) == 4


def test_unknown_tool_is_class_4_even_when_it_looks_harmless() -> None:
    assert classify_reversibility("tool", "echo") == 4
    assert classify_reversibility("tool", "true") == 4
    assert classify_reversibility("", "read") == 4


def test_every_registered_pair_still_classifies_under_adversarial_default_facts() -> (
    None
):
    for (kind, name), family in REGISTERED_TOOLS.items():
        assert classify_reversibility(kind, name) == _default_class(family)


def test_import_statement_scan_misses_the_getframe_escape() -> None:
    """Honest residual of the scan that is not our boundary."""
    assert _import_statement_modules(GETFRAME_ESCAPE) == set()
    assert find_forbidden_imports(GETFRAME_ESCAPE, frozenset()) == []


def test_irreversible_zero_does_not_rest_on_that_scan() -> None:
    """The construction is the classifier plus no live handle, not the scan."""
    assert classify_reversibility("tool", "bash") == 4
    assert classify_reversibility("tool", "webfetch") == 4
    source = inspect.getsource(classify_reversibility)
    assert "find_forbidden_imports" not in source
    assert "__import__" not in ast.dump(ast.parse(source))


def test_product_classifier_and_admission_have_no_live_irreversible_handle() -> None:
    banned = {"subprocess", "socket", "http", "urllib", "requests", "httpx"}
    for name in ("capabilities.py", "effects.py"):
        imported = _product_imports(PRODUCT / name)
        assert not (imported & banned), (
            f"{name} grew a live handle: {imported & banned}"
        )
    assert classify_reversibility.__code__.co_consts is not None
    # A label, not a callable tool: no handle is returned.
    assert classify_reversibility("tool", "webfetch") == 4


def test_product_scan_catches_a_dunder_import_live_handle(tmp_path: Path) -> None:
    """MEASURED 26 August 2026: `_LIVE = __import__('subprocess')` reached a live
    subprocess handle in the product tree while the full 52-test suite stayed green,
    because `_product_imports` walked only Import/ImportFrom. The scan now also follows
    `__import__(...)` and `importlib.import_module(...)` calls.
    """
    live_handle = tmp_path / "planted.py"
    live_handle.write_text("_LIVE = __import__('subprocess')\n", encoding="utf-8")
    assert _product_imports(live_handle) == {"subprocess"}

    import_module_handle = tmp_path / "planted_importlib.py"
    import_module_handle.write_text(
        "import importlib\n_LIVE = importlib.import_module('socket')\n",
        encoding="utf-8",
    )
    assert "socket" in _product_imports(import_module_handle)


def test_classifier_is_not_an_admission_chokepoint() -> None:
    """Residual: derive_admission does not consult classify_reversibility.

    0% on irreversible *labels* is classifier construction. 0% on irreversible
    *execution* is admission plus the product-tree AST lock, and those two
    are not composed. Wiring them is an effects.py / capabilities.py change
    and is outside this unit's claim list.
    """
    source = inspect.getsource(derive_admission)
    assert "classify_reversibility" not in source


def test_network_call_needs_standing_authority_not_the_local_baseline() -> None:
    """The outbound-fetch residual is CLOSED, and closed narrowly.

    REPLACES test_admission_residual_network_call_can_execute_as_observation, which
    asserted that network.call executes as plain observation under any admitted grant. That
    was an honest residual when it was written [measured 2026-08-24]: network.call is class
    4 on the tool table and irreversible under the least-recoverable-atom rule, but
    READ_ONLY_EFFECTS treated it as observation, and the note recorded the cost of closing
    it -- every webfetch would need a class-4 confirm.

    Commit 5ac16cc closed it by adding a controller-baseline pre-check, so the code and that
    recorded decision disagreed and this test went red. Joe chose the tightening on
    28 August 2026 ("2. keep the tightening"), from two options put to him.

    The cost turned out to be smaller than the original note feared, which is why the
    boundary is worth asserting in all three directions rather than just the refusal:
    the closure is SCOPED TO THE GRANT KIND, not to the effect. A local restorable
    baseline may not reach outbound network; a principal-authority grant still may. The
    zero-click path is not dead, it is reattached to standing authority -- which is what
    an irreversible outbound effect should have required all along.
    """
    manifest = _manifest(effects=("network.call",), operations=("fetch",))

    # 1. The local baseline may NOT reach outbound network. This is the tightening.
    baseline = derive_admission(
        manifest,
        _admitted(effect_classes=("network.call",), operations=("fetch",)),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert baseline.admission == "capability_gap"
    assert baseline.disposition == "refuse"
    assert baseline.reason == "grant_kind_forbids_protected_reach"

    # 2. Standing authority still may. Without this the test would pass for a blanket ban,
    #    and the closure would be wider than anyone chose.
    standing = derive_admission(
        manifest,
        _admitted(
            effect_classes=("network.call",),
            operations=("fetch",),
            grant_kind="principal_authority",
        ),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert standing.admission == "observation"
    assert standing.disposition == "execute"

    # 3. Ordinary reads are untouched. The tightening is about REACH, not about
    #    observation, and a check that cannot tell those apart would be the wrong one.
    read_only = derive_admission(
        _manifest(effects=("data.read",), operations=("read",)),
        _admitted(effect_classes=("data.read",), operations=("read",)),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert read_only.admission == "observation"
    assert read_only.disposition == "execute"

def test_protected_irreversible_effects_do_not_execute_without_standing_authority() -> (
    None
):
    for effect in (
        "money.commit",
        "message.send",
        "content.publish",
        "external.change",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
    ):
        result = derive_admission(
            _manifest(effects=(effect,), operations=("act",)),
            _admitted(
                effect_classes=(effect,),
                operations=("act",),
                grant_kind="principal_authority",
            ),
            AdmissionFacts(authority_standing=False),
        )
        assert result.disposition != "execute", effect
        assert result.admission == "protected_uncovered"


def test_gated_capability_cannot_execute_any_effect() -> None:
    result = derive_admission(
        _manifest(),
        CapabilityEntry(
            kind="tool",
            name="webfetch",
            available=True,
            provenance=("probe:tool:webfetch",),
            gate=default_gate(),
        ),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.disposition == "refuse"


def test_reversible_residual_caller_boolean_is_not_a_sandbox() -> None:
    """Class-2 residual: ``default_deny_egress_proven=True`` is a flag, not a proof.

    Utility of accepting the flag: a proven sandbox can stay on the
    zero-click path. Residual: any caller who can pass the boolean gets
    class 2 for bash. That is not 0%, and this suite does not pretend it is.
    """
    assert (
        classify_reversibility(
            "tool",
            "bash",
            default_deny_egress_proven=True,
        )
        == 2
    )
    assert classify_reversibility("tool", "bash") == 4


def test_reversible_residual_and_utility_cost_are_reported() -> None:
    """File tools remain class 1 — that is the utility, not a missed attack.

    Residual: an admitted ``file.change`` with a recovery proof still
    executes (local overwrite). Utility cost of making those class 4:
    every read/grep/write would stop and disclose, killing the zero-click
    path the design reserves for a closed tool surface.
    """
    class_1 = {
        (kind, name)
        for (kind, name), family in REGISTERED_TOOLS.items()
        if classify_reversibility(kind, name) == 1
    }
    assert class_1 == set(REVERSIBLE_DEFAULT)
    result = derive_admission(
        _manifest(effects=("file.change",), operations=("write",)),
        _admitted(effect_classes=("file.change",), operations=("write",)),
        AdmissionFacts(recovery_proof_passed=True),
    )
    assert result.admission == "recoverable_mutation"
    assert result.disposition == "execute"


def test_registered_tools_table_is_a_plain_dict_and_that_is_residual() -> None:
    """Construction does not freeze the inventory.

    An in-process writer can reclassify. Product code in this unit's surface
    does not assign to the table; freezing it is a capabilities.py change
    outside the claim list. Reported, not flattened.
    """
    assert type(REGISTERED_TOOLS) is dict


def test_suite_is_this_file_and_user_rerunnable() -> None:
    """Published artefact: this module, invoked with pytest, no extra fixture."""
    assert Path(__file__).name == "test_tool_surface_adversarial.py"
    assert IRREVERSIBLE_DEFAULT
    assert REVERSIBLE_DEFAULT
