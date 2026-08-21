"""Bind adopted components to a current record and refuse named incompatible licences.

    python .github/scripts/check_component_licences.py --check
    python .github/scripts/check_component_licences.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "docs" / "legal" / "adopted-components.json"
MAX_AGE_DAYS = 180
REQUIRED_FIELDS = ("name", "capability", "source", "licence", "verified", "status")
DENIED_LICENCES = (
    "BUSL",
    "SSPL",
    "AGPL",
    "all rights reserved",
    "sustainable use",
    "proprietary",
    "source-available",
)
DEPENDENCY_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GIT_ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def normalise_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


def findings(record: object, adopted_names: set[str]) -> list[str]:
    """Return every record or adoption-binding violation."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    components = record.get("components")
    if not isinstance(components, list):
        return ["record must contain a components list"]
    if not components:
        errors.append("components list must not be empty")

    supplied: set[str] = set()
    seen: set[str] = set()
    today = date.today()
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"component[{index}] must be an object")
            continue
        raw_name = component.get("name")
        label = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else f"component[{index}]"
        for field in REQUIRED_FIELDS:
            value = component.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: {field} is required and must be non-empty")

        status = component.get("status")
        if isinstance(status, str) and status.strip() and status not in {"supplied", "refused"}:
            errors.append(f"{label}: status must be 'supplied' or 'refused'")

        if isinstance(raw_name, str) and raw_name.strip():
            normalised = normalise_name(raw_name.strip())
            if normalised in seen:
                errors.append(f"{label}: duplicate component name")
            seen.add(normalised)
            if status == "supplied":
                supplied.add(normalised)

        licence = component.get("licence")
        if status == "supplied" and isinstance(licence, str):
            folded = licence.casefold()
            denied = next(
                (token for token in DENIED_LICENCES if token.casefold() in folded),
                None,
            )
            if denied is not None:
                errors.append(f"{label}: supplied entry uses denied licence {denied!r}")

        if status == "refused":
            reason = component.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{label}: refused entry requires a non-empty reason")

        verified = component.get("verified")
        if not isinstance(verified, str) or not verified.strip():
            continue
        try:
            if not ISO_DATE.fullmatch(verified):
                raise ValueError
            verified_date = date.fromisoformat(verified)
        except ValueError:
            errors.append(f"{label}: verified must be an ISO date (YYYY-MM-DD)")
            continue
        if verified_date > today:
            errors.append(f"{label}: verified date {verified} is in the future")
        elif (today - verified_date).days > MAX_AGE_DAYS:
            source = component.get("source")
            errors.append(
                f"{label}: licence record is stale; re-read the licence at {source} "
                "and bump `verified`"
            )

    adopted_by_normalised = {normalise_name(name): name for name in adopted_names}
    for missing in sorted(adopted_by_normalised.keys() - supplied):
        errors.append(
            f"adopted component {adopted_by_normalised[missing]!r} has no supplied record"
        )
    return errors


def git_tracked_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate tracked files")
    return [path for path in completed.stdout.split("\0") if path]


def adopted_names(tracked_paths: list[str]) -> set[str]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("pyproject.toml [project].dependencies must be a list")

    names: set[str] = set()
    for dependency in dependencies:
        if not isinstance(dependency, str) or not (match := DEPENDENCY_NAME.match(dependency)):
            raise ValueError(f"invalid runtime dependency: {dependency!r}")
        names.add(match.group())

    for relative in tracked_paths:
        if not re.search(r"mcp.*\.json$", relative, flags=re.IGNORECASE):
            continue
        config = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError(f"{relative}: MCP config must be a JSON object")
        servers = config.get("mcpServers")
        if servers is None:
            continue
        if not isinstance(servers, dict):
            raise ValueError(f"{relative}: mcpServers must be an object")
        for name in servers:
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{relative}: MCP server names must be non-empty strings")
            names.add(name)
    return names


def self_test() -> None:
    def valid() -> dict[str, object]:
        return {
            "components": [
                {
                    "name": "example/component",
                    "capability": "example",
                    "source": "https://example.test/component",
                    "licence": "MIT",
                    "verified": date.today().isoformat(),
                    "status": "supplied",
                }
            ]
        }

    assert not findings(valid(), set()), "a valid record must be accepted"

    cases: list[tuple[dict[str, object], set[str], str]] = []
    cases.append(({"components": []}, set(), "must not be empty"))
    duplicate = valid()
    duplicate["components"].append(  # type: ignore[union-attr]
        dict(duplicate["components"][0])  # type: ignore[index]
    )
    cases.append((duplicate, set(), "duplicate component name"))
    missing = valid()
    del missing["components"][0]["name"]  # type: ignore[index]
    cases.append((missing, set(), "name"))
    invalid_date = valid()
    invalid_date["components"][0]["verified"] = "not-a-date"  # type: ignore[index]
    cases.append((invalid_date, set(), "ISO date"))
    future = valid()
    future["components"][0]["verified"] = (date.today() + timedelta(days=1)).isoformat()  # type: ignore[index]
    cases.append((future, set(), "future"))
    stale = valid()
    stale["components"][0]["verified"] = (date.today() - timedelta(days=MAX_AGE_DAYS + 1)).isoformat()  # type: ignore[index]
    cases.append((stale, set(), "re-read the licence"))
    refused = valid()
    refused["components"][0].update({"status": "refused", "reason": ""})  # type: ignore[union-attr,index]
    cases.append((refused, set(), "reason"))
    invalid_status = valid()
    invalid_status["components"][0]["status"] = "unknown"  # type: ignore[index]
    cases.append((invalid_status, set(), "status"))
    # The real tree currently has no MCP config or runtime dependency. This fixture keeps
    # the adoption binding failable rather than blessing a vacuous check.
    cases.append((valid(), {"missing/component"}, "missing/component"))
    for denied in DENIED_LICENCES:
        record = valid()
        record["components"][0]["licence"] = denied  # type: ignore[index]
        cases.append((record, set(), "denied licence"))

    for record, adopted, expected in cases:
        errors = findings(record, adopted)
        assert any(expected in error for error in errors), (
            f"detector missed {expected!r}: {errors}"
        )
    print(f"self-test detected {len(cases)} invalid records and accepted 1 valid record")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="scan the tracked tree")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove the required failure modes detect",
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()

    try:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        adopted = adopted_names(git_tracked_paths())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"component-licence invariant failed: {exc}")
        return 1

    errors = findings(record, adopted)
    if errors:
        print("component-licence invariant failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    components = record.get("components", []) if isinstance(record, dict) else []
    print(
        f"component-licence invariant passes: {len(components)} component(s), "
        f"{len(adopted)} adopted name(s) bound"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
