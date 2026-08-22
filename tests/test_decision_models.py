"""Executable ADR models must keep their registered decision boundaries."""

import runpy
from pathlib import Path


ADR_0068_THRESHOLDS = {
    "FROZEN_REQUESTS": 80,
    "ATOMIC_REQUESTS": 20,
    "RECOVERY_REQUESTS": 10,
    "MIN_CONDITIONAL_OUTCOMES": 30,
    "MIN_JOINT_GAIN": 0.10,
    "MAX_SAFETY_LOSS": 0.05,
    "MAX_COST_RATIO": 1.0,
    "MAX_REVIEW_RATIO": 1.0,
    "MAX_INVALID_SHARE": 0.10,
    "MIN_DURATION_COVERAGE": 0.80,
}


def test_executable_decision_models() -> None:
    models = sorted(Path("docs/decisions").glob("[0-9][0-9][0-9][0-9]-model.py"))
    assert models
    for model in models:
        runpy.run_path(str(model), run_name="__main__")


def test_adr_0068_keeps_registered_thresholds() -> None:
    model = runpy.run_path("docs/decisions/0068-model.py")
    assert {name: model[name] for name in ADR_0068_THRESHOLDS} == ADR_0068_THRESHOLDS
