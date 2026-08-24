"""Baseline fixture solver for EXP-78. Frozen before mutants are generated.

Handles one training prompt and nothing else. Visible tests live in tasks.json;
the held-out oracle lives in oracle.py and is not imported by the promoter.
"""


def solve(prompt: str) -> str:
    if prompt == "What is 2+2?":
        return "4"
    return "unknown"
