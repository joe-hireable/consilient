"""Determinism control for the two independent EXP-56 preflight runs."""

import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIRST = HERE / "results-exp56.json"
SECOND = HERE / "results-exp56-rerun-control.json"


def main() -> int:
    first = FIRST.read_bytes()
    second = SECOND.read_bytes()
    same = first == second
    print(f"primary sha256: {hashlib.sha256(first).hexdigest()}")
    print(f"control sha256: {hashlib.sha256(second).hexdigest()}")
    print(f"byte-identical: {same}")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
