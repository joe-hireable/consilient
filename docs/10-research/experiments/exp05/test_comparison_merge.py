"""Selected backend runs must not erase earlier comparison evidence (I2)."""

from run_all import merge_rows


if __name__ == "__main__":
    existing = [
        {"agent": "claude-code", "duration_s": 25.6},
        {"agent": "codex", "duration_s": 20.4},
    ]
    new = [
        {"agent": "codex", "duration_s": 21.0},
        {"agent": "cursor", "duration_s": 47.0},
    ]
    got = merge_rows(existing, new)
    assert got == [
        {"agent": "claude-code", "duration_s": 25.6},
        {"agent": "codex", "duration_s": 21.0},
        {"agent": "cursor", "duration_s": 47.0},
    ]
    print("comparison merge: preserve + replace + append pass")
