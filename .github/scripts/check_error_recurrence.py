"""Fail when an identity recurs after a record links it to a prevention check."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from consilient.error_tracking import (  # noqa: E402
    ErrorRecordError,
    prevented_recurrences,
    read_records,
)


def _check_exists(reference: str) -> bool:
    relative, separator, node = reference.partition("::")
    path = ROOT / relative
    if not path.is_file():
        return False
    if not separator:
        return True
    names = node.partition("[")[0].split(".")
    if relative.startswith("tests/") and (
        not names[-1].startswith("test")
        or (len(names) > 1 and not names[0].startswith("Test"))
    ):
        return False
    try:
        body = ast.parse(path.read_text(encoding="utf-8")).body
    except (OSError, SyntaxError, UnicodeError):
        return False
    for index, name in enumerate(names):
        match = next(
            (
                item
                for item in body
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                and item.name == name
            ),
            None,
        )
        if match is None:
            return False
        if index < len(names) - 1:
            if not isinstance(match, ast.ClassDef):
                return False
            body = match.body
    return not isinstance(match, ast.ClassDef)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="canonical error-record JSONL")
    args = parser.parse_args(argv)
    try:
        records = read_records(args.record)
        findings = prevented_recurrences(records)
    except (ErrorRecordError, OSError) as exc:
        print(f"error recurrence check failed: {exc}")
        return 1
    missing = [
        (line, check)
        for line, record in enumerate(records, start=1)
        if isinstance((check := record.get("prevention_check")), str)
        and not _check_exists(check)
    ]
    for line, check in missing:
        print(f"{args.record}:{line}: prevention check does not exist: {check}")
    for line, prevented_line, identity, check in findings:
        print(
            f"{args.record}:{line}: prevented error {identity} recurred; "
            f"line {prevented_line} names {check}"
        )
    if findings or missing:
        print(
            "error recurrence check FAILED: "
            f"{len(findings)} recurrence(s), {len(missing)} missing check(s)"
        )
        return 1
    print(f"error recurrence check passes: {len(records)} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
