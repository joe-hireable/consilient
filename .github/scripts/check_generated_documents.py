"""Verify every admitted class-G document through its named producer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MANIFEST = ROOT / "docs" / "generated-manifest.json"
TIMEOUT_S = 120
GIT_ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
SHELL_METACHARACTERS = frozenset(";|&$`<>")
HEADER_PRODUCER = re.compile(r"^\s*>\s*\*\*Producer:\*\*\s*`([^`]+)`\s*$")
HEADER_SOURCE = re.compile(r"^\s*>\s*\*\*Source:\*\*\s*`([^`]+)`\s*$")
HEADER_DIGEST = re.compile(r"^\s*>\s*\*\*Source SHA-256:\*\*\s*`([0-9a-f]{64})`\s*$", re.IGNORECASE)
HEADER_NO_EDIT = re.compile(
    r"^\s*>\s*\*\*Do not hand-edit:\*\*\s*regenerate with `([^`]+)`\.\s*$"
)


@dataclass(frozen=True)
class ManifestEntry:
    output: str
    producer: str
    check_args: tuple[str, ...]
    sources: tuple[str, ...]
    header_producer: str
    header_source: str


@dataclass(frozen=True)
class EntryResult:
    output: str
    ok: bool
    detail: str


def _reject_traversal(value: str, *, label: str) -> None:
    if value.startswith("/") or value.startswith("\\"):
        raise ValueError(f"{label} must be repository-relative")
    parts = Path(value).parts
    if ".." in parts:
        raise ValueError(f"{label} contains traversal")


def _reject_metacharacters(value: str, *, label: str) -> None:
    if any(char in value for char in SHELL_METACHARACTERS):
        raise ValueError(f"{label} contains shell metacharacter")
    if any(char in value for char in "\r\n\t"):
        raise ValueError(f"{label} contains shell metacharacter")


def source_digest(root: Path, sources: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for pattern in sources:
        path = Path(pattern)
        if any(char in pattern for char in "[]*?"):
            parent = root / path.parent
            paths = sorted(parent.glob(path.name))
        else:
            paths = [root / pattern]
        if not paths:
            raise ValueError(f"source pattern matched no files: {pattern}")
        for resolved in paths:
            relative = resolved.relative_to(root).as_posix()
            file_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(file_digest.encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


def _parse_entry(raw: dict[str, object]) -> ManifestEntry:
    required = ("output", "producer", "check_args", "sources", "header")
    missing = [name for name in required if name not in raw]
    if missing:
        raise ValueError(f"manifest entry missing fields: {', '.join(missing)}")
    header = raw["header"]
    if not isinstance(header, dict):
        raise ValueError("manifest entry header must be an object")
    for name in ("producer", "source"):
        if name not in header:
            raise ValueError(f"manifest entry header missing {name}")
    check_args = raw["check_args"]
    sources = raw["sources"]
    if not isinstance(check_args, list) or not all(isinstance(arg, str) for arg in check_args):
        raise ValueError("check_args must be a string array")
    if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
        raise ValueError("sources must be a string array")
    return ManifestEntry(
        output=str(raw["output"]),
        producer=str(raw["producer"]),
        check_args=tuple(str(arg) for arg in check_args),
        sources=tuple(str(source) for source in sources),
        header_producer=str(header["producer"]),
        header_source=str(header["source"]),
    )


def validate_manifest(payload: dict[str, object], *, root: Path) -> list[ManifestEntry]:
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError("entries must be a non-empty array")
    entries = [_parse_entry(entry) for entry in entries_raw if isinstance(entry, dict)]
    if len(entries) != len(entries_raw):
        raise ValueError("every manifest entry must be an object")
    outputs: set[str] = set()
    producers: set[str] = set()
    for entry in entries:
        for label, value in (
            ("output", entry.output),
            ("producer", entry.producer),
            ("header producer", entry.header_producer),
            ("header source", entry.header_source),
        ):
            _reject_traversal(value, label=label)
            _reject_metacharacters(value, label=label)
        for source in entry.sources:
            _reject_traversal(source, label="source")
        for arg in entry.check_args:
            _reject_metacharacters(arg, label="check argument")
        if entry.output in outputs:
            raise ValueError(f"duplicate output {entry.output}")
        if entry.producer in producers:
            raise ValueError(f"duplicate producer {entry.producer}")
        outputs.add(entry.output)
        producers.add(entry.producer)
        producer_path = (root / entry.producer).resolve()
        if not producer_path.is_file() or root.resolve() not in producer_path.parents:
            raise ValueError(f"producer outside repository: {entry.producer}")
        if entry.header_producer != entry.producer:
            raise ValueError(f"header producer mismatch for {entry.output}")
    return entries


def _parse_header(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if match := HEADER_PRODUCER.match(line):
            fields["producer"] = match.group(1)
        elif match := HEADER_SOURCE.match(line):
            fields["source"] = match.group(1)
        elif match := HEADER_DIGEST.match(line):
            fields["source_sha256"] = match.group(1).lower()
        elif match := HEADER_NO_EDIT.match(line):
            fields["regenerate"] = match.group(1)
    return fields


def _verify_header(entry: ManifestEntry, *, root: Path) -> str | None:
    output_path = root / entry.output
    if not output_path.is_file():
        return f"{entry.output}: generated document missing"
    header = _parse_header(output_path.read_text(encoding="utf-8"))
    expected_digest = source_digest(root, entry.sources)
    if header.get("producer") != entry.header_producer:
        return f"{entry.output}: producer header mismatch"
    if header.get("source") != entry.header_source:
        return f"{entry.output}: source header mismatch"
    if header.get("source_sha256") != expected_digest:
        return f"{entry.output}: source SHA-256 header mismatch"
    if header.get("regenerate") not in {entry.producer, f"python {entry.producer}"}:
        return f"{entry.output}: regenerate header mismatch"
    return None


def _run_producer(entry: ManifestEntry, *, root: Path) -> str | None:
    command = [sys.executable, str(root / entry.producer), *entry.check_args]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_S,
            check=False,
            env=GIT_ENV,
        )
    except subprocess.TimeoutExpired:
        return f"{entry.output}: producer timed out after {TIMEOUT_S}s"
    if completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).strip().splitlines()
        message = detail[-1] if detail else f"exit {completed.returncode}"
        return f"{entry.output}: producer failed: {message}"
    return None


def check_manifest(path: Path, *, root: Path) -> tuple[list[EntryResult], int]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return ([EntryResult(output=str(path), ok=False, detail=str(error))], 1)
    if not isinstance(payload, dict):
        return ([EntryResult(output=str(path), ok=False, detail="manifest must be an object")], 1)
    try:
        entries = validate_manifest(payload, root=root)
    except ValueError as error:
        return ([EntryResult(output=str(path), ok=False, detail=str(error))], 1)
    results: list[EntryResult] = []
    adverse = 0
    for entry in entries:
        problems: list[str] = []
        header_problem = _verify_header(entry, root=root)
        if header_problem is not None:
            problems.append(header_problem)
        producer_problem = _run_producer(entry, root=root)
        if producer_problem is not None:
            problems.append(producer_problem)
        if problems:
            adverse += 1
            results.append(EntryResult(output=entry.output, ok=False, detail="; ".join(problems)))
        else:
            results.append(EntryResult(output=entry.output, ok=True, detail="ok"))
    return results, adverse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="path to docs/generated-manifest.json",
    )
    parser.add_argument("--check", action="store_true", help="verify every admitted generated document")
    args = parser.parse_args(argv)
    if not args.check:
        print("FAIL --check is required", file=sys.stderr)
        return 2
    manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    results, adverse = check_manifest(manifest, root=ROOT)
    checked = len(results)
    for result in results:
        status = "ok" if result.ok else "FAIL"
        print(f"{status} {result.output}: {result.detail}")
    print(f"checked={checked} adverse={adverse}")
    return 1 if adverse else 0


if __name__ == "__main__":
    raise SystemExit(main())
