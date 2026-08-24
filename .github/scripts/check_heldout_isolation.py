"""Refuse held-out contracts supplied to an unsandboxed same-user dispatch."""

from __future__ import annotations

import argparse


def refusal_reason(contract: str) -> str:
    return (
        f"held-out contract {contract!r} is reachable by this same-OS-user unsandboxed "
        "dispatch; refusing before child launch"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heldout-contract", required=True)
    args = parser.parse_args(argv)
    print(refusal_reason(args.heldout_contract))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
