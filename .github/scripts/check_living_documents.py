"""Admit Class-W written documents: tags, falsifier, review date, restatement, quotes.

ADR-0073 / L04. Standard library only. Exit 0 clean, 1 on stale or broken findings,
2 on misuse. --check is required and takes the paths under examination.

Generated surfaces are read from docs/generated-manifest.json. A written document may
point at those surfaces; a matching substantive sentence is a restatement unless an
adjacent living-doc: restatement-ok directive names the generated path and a rationale.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent.parent

EVIDENCE_TAG = re.compile(
    r"\[(measured|simulated|cited|asserted|algebra)(?:[^\]]*)?\]",
    re.IGNORECASE,
)
DOCUMENT_CLASS = re.compile(r"Document class:\s*\**\s*W\b")
REVIEW_BY = re.compile(
    r"Review by:\s*\**\s*`?(\d{4}-\d{2}-\d{2})`?",
    re.IGNORECASE,
)
FALSIFIER_FIELD = re.compile(
    r"Falsifier:\s*(.+)$",
    re.IGNORECASE,
)
FALSIFIER_HEADING = re.compile(
    r"^#{1,6}\s+.*falsif",
    re.IGNORECASE,
)
RESTATEMENT_OK = re.compile(
    r"living-doc:\s*restatement-ok\s+(\S+?)\s*:\s*(.+?)(?:-->)?\s*$",
    re.IGNORECASE,
)
SOURCE_LINE = re.compile(r"^Source:\s*(.+)\s*$", re.IGNORECASE)
NUMBER_WORD = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred)\b",
    re.IGNORECASE,
)
DIGIT = re.compile(r"\d")
PRINCIPAL_ATTR = re.compile(r"\bprincipal\b", re.IGNORECASE)


@dataclass
class Finding:
    path: str
    detail: str
    bucket: str


@dataclass
class CheckResult:
    checked: int = 0
    stale: int = 0
    suppressed: int = 0
    broken: int = 0
    unknown: int = 0
    findings: list[Finding] = field(default_factory=list)

    def add(self, path: Path, detail: str, bucket: str) -> None:
        self.findings.append(Finding(path=path.as_posix(), detail=detail, bucket=bucket))
        if bucket == "stale":
            self.stale += 1
        elif bucket == "suppressed":
            self.suppressed += 1
        elif bucket == "broken":
            self.broken += 1
        elif bucket == "unknown":
            self.unknown += 1


def _reject_traversal(value: str) -> None:
    if value.startswith("/") or value.startswith("\\"):
        raise ValueError("locator must be repository-relative")
    if ".." in Path(value).parts:
        raise ValueError("locator contains traversal")


def load_manifest(root: Path) -> list[str]:
    path = root / "docs" / "generated-manifest.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return []
    outputs: list[str] = []
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("output"), str):
            outputs.append(entry["output"])
    return outputs


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = EVIDENCE_TAG.sub(" ", text)
    text = re.sub(r"[*_>#~\[\]()]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_sentence(text: str) -> str:
    return strip_markdown(text).lower().rstrip(".")


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"```.*?```", "\n", text, flags=re.DOTALL)
    kept: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if stripped.startswith(">") or stripped.startswith("<!--"):
            continue
        kept.append(stripped)
    parts = re.split(r"(?<=[.!?])\s+", " ".join(kept))
    sentences: list[str] = []
    for part in parts:
        normalised = normalize_sentence(part)
        if len(normalised.split()) >= 8:
            sentences.append(normalised)
    return sentences


def generated_sentences(root: Path, outputs: list[str]) -> set[str]:
    found: set[str] = set()
    for output in outputs:
        path = root / output
        if not path.is_file():
            continue
        found.update(split_sentences(path.read_text(encoding="utf-8")))
    return found


def _blocks(text: str) -> list[str]:
    return re.split(r"\n\s*\n", text)


def _is_skippable_block(block: str) -> bool:
    stripped = block.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith("|"):
        return True
    if stripped.startswith("```") or stripped.startswith("$$"):
        return True
    if stripped.startswith("<!--"):
        return True
    if stripped.startswith(">"):
        return True
    if stripped.startswith(("- ", "* ", "+ ")):
        return True
    if re.match(r"^\d+\.\s", stripped):
        return True
    return False


def _parse_review_date(raw: str) -> date | str:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return "impossible"


def _locator_kind(raw: str, *, root: Path) -> tuple[str, str]:
    value = raw.strip().strip("`")
    lowered = value.lower()
    if "infer" in lowered:
        return "broken", "author inference is not provenance"
    if re.fullmatch(r"\d{1,2}\s+\w+\s+\d{4}", value) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "broken", "a bare date is not provenance"
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return "unknown", "public URL locator not fetched"
    path_part, sep, rest = value.partition(":")
    if not sep:
        return "broken", "locator needs a repository path plus line/event identity"
    try:
        _reject_traversal(path_part)
    except ValueError as error:
        return "broken", str(error)
    target = root / path_part
    if not target.is_file():
        return "broken", f"dead local locator: missing {path_part}"
    if rest.lower().startswith("event") or re.fullmatch(r"[0-9a-fA-F-]{8,}", rest):
        return "checked", "event identity"
    line_text = rest[1:] if rest[:1] in {"L", "l"} else rest
    if line_text.isdigit():
        line_no = int(line_text)
        lines = target.read_text(encoding="utf-8").splitlines()
        if line_no < 1 or line_no > len(lines):
            return "broken", f"dead local locator: line {line_no} missing in {path_part}"
        return "checked", "path plus line"
    return "broken", "locator needs a repository path plus line/event identity"


def check_document(path: Path, *, root: Path, generated: set[str]) -> CheckResult:
    result = CheckResult(checked=1)
    relative = path if path.is_absolute() else root / path
    text = relative.read_text(encoding="utf-8")

    class_hits = DOCUMENT_CLASS.findall(text)
    if len(class_hits) == 0:
        result.add(relative, "missing Document class: W", "broken")
    elif len(class_hits) != 1:
        result.add(relative, "exactly one Document class: W is required", "broken")

    review_matches = list(REVIEW_BY.finditer(text))
    if not review_matches:
        result.add(relative, "missing Review by ISO date", "broken")
    else:
        parsed = _parse_review_date(review_matches[0].group(1))
        if parsed == "impossible":
            result.add(relative, "impossible Review by date", "broken")
        elif isinstance(parsed, date) and parsed < date.today():
            result.add(relative, "Review by date is expired (stale)", "stale")

    falsifier_ok = False
    for line in text.splitlines():
        match = FALSIFIER_FIELD.search(line)
        if match and re.sub(r"[*`\s]", "", match.group(1)):
            falsifier_ok = True
            break
    if not falsifier_ok:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if FALSIFIER_HEADING.search(line):
                remainder = "\n".join(lines[index + 1 :])
                next_heading = re.search(r"^#{1,6}\s+", remainder, re.MULTILINE)
                body = remainder[: next_heading.start()] if next_heading else remainder
                if body.strip():
                    falsifier_ok = True
                break
    if not falsifier_ok:
        result.add(relative, "missing or empty falsifier", "broken")

    for block in _blocks(text):
        if _is_skippable_block(block):
            continue
        if SOURCE_LINE.match(block.strip()):
            continue
        if EVIDENCE_TAG.search(block):
            continue
        words = re.findall(r"[A-Za-z0-9]+", block)
        if len(words) < 8:
            continue
        if DIGIT.search(block) or NUMBER_WORD.search(block):
            result.add(relative, "untagged load-bearing claim paragraph", "broken")

    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith(">"):
            index += 1
            continue
        start = index
        quote: list[str] = []
        while index < len(lines) and (
            lines[index].lstrip().startswith(">") or lines[index].strip() == ""
        ):
            if lines[index].lstrip().startswith(">"):
                quote.append(lines[index])
            elif quote:
                break
            index += 1
        preceding = "\n".join(lines[max(0, start - 6) : start])
        if not (PRINCIPAL_ATTR.search(preceding) and quote):
            continue
        following = []
        look = index
        while look < len(lines) and not lines[look].strip():
            look += 1
        if look < len(lines):
            following.append(lines[look])
        source_match = SOURCE_LINE.match(following[0]) if following else None
        if source_match is None:
            result.add(
                relative,
                "principal quote lacks an adjacent Source: locator",
                "broken",
            )
            continue
        bucket, detail = _locator_kind(source_match.group(1), root=root)
        if bucket != "checked":
            result.add(relative, detail, bucket)

    allowed_outputs = set(load_manifest(root))
    valid_directives: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(lines):
        match = RESTATEMENT_OK.search(line)
        if not match:
            continue
        target = match.group(1).split("#", 1)[0]
        rationale = match.group(2).strip()
        if target in allowed_outputs and rationale:
            valid_directives.append((line_no, target, rationale))
            result.add(
                relative,
                f"restatement suppressed for {target}: {rationale}",
                "suppressed",
            )

    written_sentences = split_sentences(text)
    if generated and written_sentences:
        for sentence in written_sentences:
            if sentence not in generated:
                continue
            if valid_directives:
                continue
            result.add(relative, "literal restatement of a generated surface", "broken")

    return result


def check_paths(paths: list[Path], *, root: Path) -> CheckResult:
    outputs = load_manifest(root)
    generated = generated_sentences(root, outputs)
    combined = CheckResult()
    for raw in paths:
        path = raw if raw.is_absolute() else root / raw
        one = check_document(path, root=root, generated=generated)
        combined.checked += one.checked
        combined.stale += one.stale
        combined.suppressed += one.suppressed
        combined.broken += one.broken
        combined.unknown += one.unknown
        combined.findings.extend(one.findings)
    return combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        nargs="+",
        metavar="PATH",
        help="Class-W documents to admit",
    )
    args = parser.parse_args(argv)
    if not args.check:
        print("FAIL --check is required", file=sys.stderr)
        return 2
    paths = [Path(item) for item in args.check]
    result = check_paths(paths, root=ROOT)
    for finding in result.findings:
        print(f"{finding.bucket} {finding.path}: {finding.detail}")
    print(
        f"checked={result.checked} stale={result.stale} suppressed={result.suppressed} "
        f"broken={result.broken} unknown={result.unknown}"
    )
    return 1 if result.broken or result.stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
