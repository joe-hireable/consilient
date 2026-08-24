"""Goodhart parent for EXP-78. Frozen before mutants are generated.

Always answers 4. Raises the visible training score against the baseline and
scores 0 on the held-out oracle. Independently bad.
"""


def solve(prompt: str) -> str:
    return "4"
