"""Sealed-manifest builders and the promote_loop bridge shared by the
test_promote_instrument_* family.

Not named test_*, so pytest does not collect it. It is on sys.path because pytest
prepends the directory of every collected test module, and tests/ holds no __init__.py.

Everything here constructs the sealed instrument of S02 (ADR-0076): the EXP-78
development tasks read from disk, the held-out items a candidate must never see, the
manifest whose digest seals both, and the one call that evaluates a candidate against
it. They are constructors taking keyword overrides rather than fixtures, so each test
spells out only the fact it is varying and inherits nothing invisibly. They were worth
extracting rather than duplicating because four files building a sealed manifest four
slightly different ways is how a suite stops checking the implementation and starts
agreeing with it.

`_contained_execute` is a deliberate test double: it reports the containment probe
denied and then runs the candidate for real. A sandbox that actually blocked socket bind
and out-of-scratch write would return those denials from the probe payload itself; this
double stands in for that sandbox so the scoring tests can exercise the sealed
instrument at all. It is the default `execute` for every evaluation here, which is
precisely why the containment tests refuse it and pass their own."""

import importlib.util
import json
from pathlib import Path
from consilient.promote import (
    CONTAINMENT_DENIED,
    CONTAINMENT_PROBE_SOURCE,
    AdverseTable,
    EvaluationPackage,
    EvaluationRefusal,
    ExecuteFn,
    LineageRegistry,
    SealedManifest,
    digest,
    evaluate_sealed,
    manifest_digest,
)

EXP78 = Path("docs/10-research/experiments/exp78")

TRAINING = [
    (row["prompt"], row["expected"])
    for row in json.loads((EXP78 / "tasks.json").read_text(encoding="utf-8"))
]

HELDOUT = [
    ("What is 5+2?", "7"),
    ("What is 6+1?", "7"),
    ("What is 3+4?", "7"),
]


def _exp78(name: str) -> str:
    return (EXP78 / name).read_text(encoding="utf-8")


def _loop_module():
    script = Path("scripts/promote_loop.py")
    spec = importlib.util.spec_from_file_location("promote_loop", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest_dict(*, hidden: list[tuple[str, str]] | None = None) -> dict[str, object]:
    development = [(prompt, expected) for prompt, expected in TRAINING]
    hidden_items = hidden if hidden is not None else list(HELDOUT)
    payload = {
        "lineage_id": "exp78-lineage",
        "qualification_batch_id": "batch-001",
        "development_tasks": [{"prompt": p, "expected": e} for p, e in development],
        "hidden_items": [{"prompt": p, "expected": e} for p, e in hidden_items],
        "predecessor_digest": digest("predecessor"),
        "epoch_anchor_digest": digest("epoch"),
        "allowed_imports": [],
        "acceptance_threshold": 1.0,
        "seed": "1040076",
    }
    payload["instrument_digest"] = manifest_digest(payload)
    return payload


def _manifest(**kwargs: object) -> SealedManifest:
    data = _manifest_dict(**kwargs)
    return SealedManifest.from_mapping(data)


def _run_candidate(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
    run_candidate = _loop_module().run_candidate
    return run_candidate(source, prompts)


def _adverse(**overrides: int) -> AdverseTable:
    base = {
        "refusals": 0,
        "timeouts": 0,
        "quarantine": 0,
        "missing_telemetry": 0,
        "boundary_attempts": 0,
    }
    base.update(overrides)
    return AdverseTable(**base)


def _contained_execute(
    source: str, prompts: list[str]
) -> tuple[bool, list[str | None]]:
    """Test double: report the probe denied, then run the candidate for real.

    A sandbox that actually blocked socket bind and out-of-scratch write would
    return these denials from the probe payload itself. This double stands in
    for that sandbox so scoring tests can still exercise the sealed instrument.
    """
    if source == CONTAINMENT_PROBE_SOURCE:
        return True, [CONTAINMENT_DENIED] * len(prompts)
    return _run_candidate(source, prompts)


def _evaluate(
    manifest: SealedManifest,
    *,
    candidate: str,
    baseline: str,
    registry: LineageRegistry | None = None,
    adverse: AdverseTable | None = None,
    contained: bool = True,
    scratch_preimage: str = "scratch-before",
    scratch_postimage: str = "scratch-before",
    execute: ExecuteFn | None = None,
) -> EvaluationPackage | EvaluationRefusal:
    return evaluate_sealed(
        manifest,
        candidate_source=candidate,
        baseline_source=baseline,
        execute=_contained_execute if execute is None else execute,
        registry=registry or LineageRegistry(),
        adverse=adverse or _adverse(),
        contained=contained,
        scratch_preimage_digest=digest(scratch_preimage),
        scratch_postimage_digest=digest(scratch_postimage),
    )
