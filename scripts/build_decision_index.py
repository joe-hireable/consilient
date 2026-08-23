"""Generate the ADR index from decision-record metadata."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DECISIONS = ROOT / "docs" / "decisions"
TARGET = DECISIONS / "index.md"
SOURCE_GLOB = "docs/decisions/[0-9][0-9][0-9][0-9]-*.md"
STATUS = re.compile(r"^\s*-\s*\*\*Status:\*\*\s*(.+?)\s*$", re.IGNORECASE)
SUPERSEDES = re.compile(
    r"^\s*-\s*\*\*Supersedes(?: in part)?:\*\*\s*(.+?)\s*$", re.IGNORECASE
)
TITLE = re.compile(r"^#\s+(\d{4})\.\s+(.+?)\s*$")
STATUS_RELATION = re.compile(
    r"\b(?P<direction>superseded(?:\s+in\s+part)?\s+by|supersedes(?:\s+in\s+part)?)\b(?P<target>.*)",
    re.IGNORECASE,
)
STATUS_FAMILIES = ("ACCEPTED", "PROPOSED", "PROVISIONAL", "SUPERSEDED", "DEPRECATED")
STATUS_FAMILY = re.compile(
    r"^(?:\*\*)?(?P<family>" + "|".join(STATUS_FAMILIES) + r")(?:\*\*)?(?=$|\s)",
    re.IGNORECASE,
)
CUT_RETAINED = re.compile(
    r"^CUT(?:\s+\([^)]*\))?\s*/\s*RETAINED(?:\s+\([^)]*\))?(?:\s+—.*)?$",
    re.IGNORECASE,
)
EXPLICIT_REFERENCE = re.compile(
    r"\bADR-(\d{4})\b|\[(?:ADR-)?(\d{4})\]|`(?:ADR-)?(\d{4})`", re.IGNORECASE
)
LEADING_REFERENCE = re.compile(r"^\s*(?:\[|`)?(?:ADR-)?(\d{4})\b", re.IGNORECASE)


@dataclass(frozen=True)
class Decision:
    number: str
    path: Path
    title: str
    status: str
    relations: tuple[str, ...]
    digest: str


def _metadata(lines: list[str], pattern: re.Pattern[str]) -> list[str]:
    return [match.group(1).strip() for line in lines if (match := pattern.match(line))]


def _canonical_status(number: str, status: str) -> str | None:
    plain = status.strip().removeprefix("⛔ ")
    family = STATUS_FAMILY.match(plain)
    if family is not None:
        return family.group("family").upper()
    if number == "0020" and CUT_RETAINED.match(plain) is not None:
        return "CUT / RETAINED"
    return None


def _reference(value: str, *, leading: bool = False) -> str | None:
    match = (
        LEADING_REFERENCE.match(value) if leading else EXPLICIT_REFERENCE.search(value)
    )
    if match is None:
        return None
    return next(group for group in match.groups() if group is not None)


def _status_relation(status: str) -> str | None:
    match = STATUS_RELATION.search(status)
    if match is None:
        return None
    direction = match.group("direction").lower()
    target = _reference(
        match.group("target"), leading=direction.startswith("superseded")
    )
    if target is None:
        return None
    return (
        f"superseded by {target}"
        if direction.startswith("superseded")
        else f"supersedes {target}"
    )


def _parse(path: Path) -> Decision:
    text = path.read_text(encoding="utf-8")
    number = path.name[:4]
    lines = text.splitlines()
    title_match = TITLE.match(lines[0]) if lines else None
    if title_match is None or title_match.group(1) != number:
        raise ValueError(f"{path.name}: missing title metadata")
    title = " ".join(title_match.group(2).split())
    if not title:
        raise ValueError(f"{path.name}: missing title metadata")
    header = []
    for line in lines[1:]:
        if line.startswith("##"):
            break
        header.append(line)
    statuses = _metadata(header, STATUS)
    if len(statuses) != 1:
        raise ValueError(
            f"{path.name}: missing Status metadata"
            if not statuses
            else f"{path.name}: multiple Status metadata rows"
        )
    raw_status = statuses[0]
    status = _canonical_status(number, raw_status)
    if status is None:
        raise ValueError(f"{path.name}: unrecognised status {raw_status!r}")
    relations = [
        relation for relation in [_status_relation(raw_status)] if relation is not None
    ]
    for value in _metadata(header, SUPERSEDES):
        target = _reference(value)
        if target is not None:
            relations.append(f"supersedes {target}")
    return Decision(
        number=number,
        path=path,
        title=title,
        status=status,
        relations=tuple(dict.fromkeys(relations)),
        # Normalise line endings before digesting. `.gitattributes` sets `* text=auto eol=lf`, so a
        # file checked out on Windows carries CRLF in the working tree and LF in the object store.
        # Digesting the working-tree bytes bakes the checkout's line endings into the committed
        # header, and the result is a check that passes for whoever generated it and fails for
        # everyone else. Measured 23 August 2026: this check passed in the authoring worktree and
        # exited 1 on a clean checkout of the same commit, with 31 CRLF files responsible — so the
        # gate would have gone red on the public repository immediately after publication.
        digest=hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
    )


def _escape(value: str) -> str:
    return re.sub(r"([\\|*_\[\]<>])", r"\\\1", " ".join(value.split()))


def decisions() -> list[Decision]:
    parsed = [
        _parse(path) for path in sorted(DECISIONS.glob("[0-9][0-9][0-9][0-9]-*.md"))
    ]
    by_number: dict[str, Decision] = {}
    for decision in parsed:
        if decision.number in by_number:
            raise ValueError(f"duplicate ADR number {decision.number}")
        by_number[decision.number] = decision
    return sorted(parsed, key=lambda decision: decision.number)


def source_digest(records: list[Decision]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record.path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def render(records: list[Decision]) -> bytes:
    lines = [
        "# Decision index",
        "",
        "> **Producer:** `scripts/build_decision_index.py`",
        f"> **Source:** `{SOURCE_GLOB}`",
        f"> **Source SHA-256:** `{source_digest(records)}`",
        "> **Do not hand-edit:** regenerate with `python scripts/build_decision_index.py`.",
        "",
        "| ADR | Decision | Status | Supersession |",
        "|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| [{record.number}]({record.path.name}) | {_escape(record.title)} | "
            f"{_escape(record.status)} | {'; '.join(record.relations) or '—'} |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the index has drifted"
    )
    args = parser.parse_args(argv)
    try:
        rendered = render(decisions())
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if args.check:
        current = TARGET.read_bytes() if TARGET.exists() else b""
        if current != rendered:
            print(
                "FAIL docs/decisions/index.md has drifted; run python scripts/build_decision_index.py"
            )
            return 1
        print("docs/decisions/index.md is current")
        return 0
    write_atomic(TARGET, rendered)
    print(f"wrote docs/decisions/index.md ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
