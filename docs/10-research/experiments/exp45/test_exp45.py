"""Unit tests for EXP-45 runner and metrics."""

import json
from pathlib import Path

from run_exp45 import (
    BoundaryEvent,
    analyze_boundary_retention,
    bootstrap_ci,
    extract_record_entities,
    normalize_path,
    percentile,
    point_biserial_r,
    rank_data,
    run_exp45_analysis,
    spearman_rho,
)


def test_percentile_and_bootstrap_ci():
    arr = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert percentile(arr, 0) == 1.0
    assert percentile(arr, 50) == 3.0
    assert percentile(arr, 100) == 5.0
    assert percentile([], 50) == 0.0
    assert percentile([42.0], 50) == 42.0

    low, high = bootstrap_ci(arr, n_boot=500, ci=0.95, seed=123)
    assert 1.0 <= low <= high <= 5.0
    assert bootstrap_ci([10.0]) == (10.0, 10.0)
    assert bootstrap_ci([]) == (0.0, 0.0)


def test_rank_and_correlations():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert spearman_rho(x, y) == 1.0

    y_rev = [5.0, 4.0, 3.0, 2.0, 1.0]
    assert spearman_rho(x, y_rev) == -1.0

    # Ties in ranks
    ties = [1.0, 2.0, 2.0, 4.0]
    ranks = rank_data(ties)
    assert ranks == [1.0, 2.5, 2.5, 4.0]

    # Zero variance or small vectors
    assert spearman_rho([1.0], [2.0]) == 0.0
    assert spearman_rho([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) == 0.0

    # Point-biserial correlation
    continuous = [10.0, 12.0, 11.0, 25.0, 30.0, 28.0]
    binary = [0, 0, 0, 1, 1, 1]
    r_pb = point_biserial_r(continuous, binary)
    assert r_pb > 0.9

    assert point_biserial_r([1.0, 2.0], [0, 0]) == 0.0
    assert point_biserial_r([1.0, 1.0], [0, 1]) == 0.0


def test_normalize_path():
    assert normalize_path("src\\consilient\\beta.py") == "src/consilient/beta.py"
    assert normalize_path("./docs/10-research/exp.md") == "docs/10-research/exp.md"
    assert normalize_path('"C:\\Users\\test\\file.txt"') == "C:/Users/test/file.txt"


def test_extract_record_entities():
    rec = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Read",
                    "input": {"file_path": "src/consilient/events.py", "limit": 50},
                },
                {
                    "type": "text",
                    "text": "Checking calculateBetaMetric and sessionHandler in events module.",
                },
            ]
        },
    }
    entities, read_files, discovery_commands = extract_record_entities(rec, turn_idx=1)
    entity_names = {e.name for e in entities}
    assert "src/consilient/events.py" in entity_names
    assert "src/consilient/events.py" in read_files
    assert "calculateBetaMetric" in entity_names
    assert "sessionHandler" in entity_names
    assert len(discovery_commands) == 0

    rec_bash = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Bash",
                    "input": {"command": "grep -rn 'compact_boundary' docs/"},
                }
            ]
        },
    }
    entities_b, read_files_b, disc_b = extract_record_entities(rec_bash, turn_idx=2)
    assert "grep" in {e.name for e in entities_b}
    assert "grep -rn 'compact_boundary' docs/" in disc_b


def test_analyze_boundary_retention_synthetic():
    records = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "src/file_a.py"},
                    },
                    {"type": "text", "text": "Function AlphaBeta is defined here."},
                ]
            },
        },
        {
            "type": "system",
            "subtype": "compact_boundary",
            "compactMetadata": {"trigger": "auto", "preTokens": 1000, "postTokens": 50},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "src/file_a.py"},
                    },
                    {"type": "text", "text": "Re-reading AlphaBeta implementation."},
                ]
            },
        },
    ]
    b_event = BoundaryEvent(
        session_id="test_sess",
        boundary_type="compact_boundary",
        record_index=1,
        turn_index=1,
    )
    analysis, survival_rows = analyze_boundary_retention(records, b_event)
    assert analysis.pre_read_files_count == 1
    assert analysis.post_reread_files_count == 1
    assert analysis.reread_rate == 1.0
    assert analysis.retention_rate > 0.0
    assert len(survival_rows) >= 2


def test_run_exp45_analysis_synthetic(tmp_path: Path):
    for i in range(12):
        sess_file = tmp_path / f"session_{i}.jsonl"
        lines = [
            {"type": "user", "sessionId": f"sess_{i}", "timestamp": "2026-08-01T10:00:00Z", "message": "hello"},
            {
                "type": "assistant",
                "sessionId": f"sess_{i}",
                "timestamp": "2026-08-01T10:01:00Z",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "src/code.py"}},
                        {"type": "text", "text": "EntityOne EntityTwo"},
                    ]
                },
            },
            {
                "type": "system",
                "subtype": "compact_boundary",
                "sessionId": f"sess_{i}",
                "compactMetadata": {"trigger": "auto", "preTokens": 5000, "postTokens": 100},
            },
            {
                "type": "assistant",
                "sessionId": f"sess_{i}",
                "timestamp": "2026-08-01T10:05:00Z",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "src/code.py"}},
                        {"type": "text", "text": "EntityOne only"},
                    ]
                },
            },
        ]
        with open(sess_file, "w", encoding="utf-8") as fp:
            for line in lines:
                fp.write(json.dumps(line) + "\n")

    out_json = tmp_path / "results.json"
    results = run_exp45_analysis(tmp_path, out_json)

    assert results["experiment_id"] == "EXP-45"
    assert results["longevity_and_frequency"]["total_files"] == 12
    assert results["longevity_and_frequency"]["total_compact_boundary_events"] == 12
    assert out_json.exists()
    assert results["verdict"] in (
        "admitted_verifier_with_bite",
        "falsifier_1_near_lossless",
        "falsifier_2_loss_does_not_bite",
        "insufficient_evidence",
    )
