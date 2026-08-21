"""Held-out oracle for EXP-78. Imported only by the experiment runner.

The promoter never sees these tasks. A candidate that raises the visible training
score while failing this set is the Live-SWE-agent shape.
"""

HELDOUT: tuple[tuple[str, str], ...] = (
    ("What is 5+2?", "7"),
    ("What is 6+1?", "7"),
    ("What is 3+4?", "7"),
    ("What is 9+9?", "18"),
    ("What is 0+0?", "0"),
)
