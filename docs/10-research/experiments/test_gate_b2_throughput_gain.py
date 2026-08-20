"""Unit tests for gate_b2_throughput_gain.py executable model (ADR-0037)."""

from __future__ import annotations
import pytest

from gate_b2_throughput_gain import (
    critical_beta,
    n_max,
    relative_gain,
    throughput,
    wilson,
)


def test_tautology_proof_n_max_always_exceeds_one():
    """Verify n_max >= 3.125 > 1.0 for all beta in [0.0, 1.0]."""
    T_a = 25.0
    T_r = 8.0
    p_good = 0.55

    for beta_int in range(0, 101, 5):
        b = beta_int / 100.0
        n = n_max(T_a, T_r, p_good, b)
        assert n >= 3.125 - 1e-9
        assert n > 1.0

    # At worst possible critic (beta = 1.0, recall = 0.0)
    assert pytest.approx(n_max(T_a, T_r, p_good, 1.0), abs=1e-5) == 3.125
    # At perfect critic (beta = 0.0, recall = 1.0)
    assert pytest.approx(n_max(T_a, T_r, p_good, 0.0), abs=1e-5) == 25.0 / (0.55 * 8.0)


def test_unassisted_baseline_throughput():
    """Verify unassisted baseline M_0 = (60 / 8) * 0.55 = 4.125 merges/hr."""
    T_r = 8.0
    p_good = 0.55
    m0 = throughput(T_r, p_good, beta=1.0)
    assert pytest.approx(m0, abs=1e-5) == 4.125


def test_critical_beta_closed_form():
    """Verify closed-form critical beta matches relative_gain == 20%."""
    p_good = 0.55
    target_gain = 0.20
    b_crit = critical_beta(p_good, target_gain)
    assert pytest.approx(b_crit, abs=1e-4) == 0.6296
    assert pytest.approx(relative_gain(p_good, b_crit), abs=1e-5) == 0.20


def test_mechanical_straddle():
    """Demonstrate one beta that passes and one that fails."""
    p_good = 0.55
    b_pass = 0.30
    b_fail = 0.85

    gain_pass = relative_gain(p_good, b_pass)
    gain_fail = relative_gain(p_good, b_fail)

    assert gain_pass >= 0.20
    assert pytest.approx(gain_pass, abs=1e-4) == 0.4599

    assert gain_fail < 0.20
    assert pytest.approx(gain_fail, abs=1e-4) == 0.0724


def test_wilson_interval_bounds():
    """Verify Wilson interval returns valid probabilities in [0, 1]."""
    low, high = wilson(18, 60)
    assert 0.0 <= low <= 18 / 60 <= high <= 1.0
    assert pytest.approx(low, abs=1e-3) == 0.199
    assert pytest.approx(high, abs=1e-3) == 0.425
