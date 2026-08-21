"""Tests for the EXP-12 archive self-improvement instrument."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "rsi_archive_loop.py"

spec = importlib.util.spec_from_file_location("rsi_archive_loop", SCRIPT)
assert spec and spec.loader
rsi = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rsi
spec.loader.exec_module(rsi)


def test_helpful_candidate_raises_heldout():
    record = rsi.run_generation(0, rsi.DEFAULT_FIXTURE, skill=rsi.HELPFUL_SKILL)
    assert record["r"] == 1.0
    assert record["heldout_success"] == 1.0
    assert record["delta_heldout"] == 0.0
    assert record["persisted"] is False


def test_harmful_candidate_goodharts_delta_heldout():
    record = rsi.run_generation(0, rsi.DEFAULT_FIXTURE, skill=rsi.HARMFUL_SKILL)
    assert record["r"] == 1.0
    assert record["heldout_success"] == 0.0
    assert record["delta_heldout"] == 1.0
    assert record["persisted"] is False


def test_pluggable_verifier_accepts_harmful_while_heldout_flat():
    def weak_verifier(candidate: str) -> bool:
        return candidate == rsi.HARMFUL_SKILL

    r = rsi.compute_r_with_verifier(rsi.HARMFUL_SKILL, weak_verifier)
    heldout = rsi.compute_heldout_success(rsi.HARMFUL_SKILL, rsi.DEFAULT_FIXTURE)
    assert r == 1.0
    assert heldout == 0.0
    assert rsi.delta_heldout(r, heldout) == 1.0


def test_may_persist_refuses_at_exp47_beta():
    assert rsi.may_persist(0.3132, "skill") is False
    assert rsi.may_persist(0.19, "skill") is True
    assert rsi.may_persist(0.20, "skill") is False


def test_jsonl_is_append_only(tmp_path: Path):
    jsonl = tmp_path / "generations.jsonl"
    rsi.run_generation(0, rsi.DEFAULT_FIXTURE, jsonl_path=jsonl, beta_hat=0.3132)
    rsi.run_generation(1, rsi.DEFAULT_FIXTURE, jsonl_path=jsonl, beta_hat=0.3132)

    lines = jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["generation"] == 0
    assert second["generation"] == 1
    assert first["persisted"] is False
    assert second["persisted"] is False
    assert first["beta_hat"] == 0.3132

    rsi.run_generation(2, rsi.DEFAULT_FIXTURE, jsonl_path=jsonl)
    assert len(jsonl.read_text(encoding="utf-8").strip().splitlines()) == 3
