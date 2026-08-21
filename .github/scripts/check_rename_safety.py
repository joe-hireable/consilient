"""Check and enforce rename safety across tracked repository files.

ADR-0038 renamed the project from Consilience to Consilient.
This script classifies every occurrence of `Consilienc\\w*` and `consilienc\\w*` in tracked text
files into:
  - `renameable`: refers to the project/product name in living documentation and should be
    renamed to Consilient.
  - `protected`: must NEVER be modified (quotations, blockquotes, ACCEPTED/SUPERSEDED ADR bodies,
    historical/dated documents, transcripts, CONSILIENCE.md, lowercase common noun, URLs, etc.).
  - `ambiguous`: cannot be decided mechanically with full certainty; left for human inspection.

Usage:
  python .github/scripts/check_rename_safety.py
  python .github/scripts/check_rename_safety.py --check
  python .github/scripts/check_rename_safety.py --apply
  python .github/scripts/check_rename_safety.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


# Git exports GIT_DIR, GIT_INDEX_FILE and GIT_WORK_TREE into every hook it runs, and GIT_DIR
# overrides cwd. Measured 21 August 2026: an unscrubbed `git ls-files` in
# check_private_corpus.py read the hook's repository instead of the private corpus it was
# pointed at, and the gate reported on a tree it had never opened. Every git subprocess in
# .github/scripts now runs with these removed.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


@dataclass(frozen=True)
class Occurrence:
    file: str
    line_number: int
    start: int
    end: int
    word: str
    classification: str  # "renameable", "protected", "ambiguous"
    reason: str
    line_content: str


def tracked_files(root: Path) -> list[str]:
    """Return all tracked files in git repository, or all regular files if not a git repo."""
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            env=GIT_ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback for non-git directories (e.g. pytest tmp_path)
        files = []
        for p in root.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                files.append(str(p.relative_to(root)).replace("\\", "/"))
        return sorted(files)


def is_dated_or_historical_path(rel_path: str) -> bool:
    """Check if file path indicates a dated, historical, or immutable log/transcript file."""
    p = Path(rel_path)
    # Dated files with YYYY-MM-DD
    if re.search(r"\d{4}-\d{2}-\d{2}", p.name):
        return True
    # Transcripts, experiment data, logs, source material, publications
    if (
        "docs/10-research/experiments/exp16/transcripts" in rel_path
        or "docs/10-research/experiments/exp16/" in rel_path
        or "docs/10-research/experiments/exp47" in rel_path
        or rel_path.startswith(".harness/log/")
        or rel_path.startswith("docs/30-source-material/")
        or rel_path.startswith("docs/50-publications/")
    ):
        return True
    return False


def is_accepted_or_superseded_adr(rel_path: str, file_content: str) -> bool:
    """Check if file is an ACCEPTED or SUPERSEDED ADR."""
    if rel_path.startswith("docs/decisions/") and rel_path.endswith(".md"):
        if re.search(
            r"-\s+\*\*Status:\*\*\s+.*?\b(ACCEPTED|SUPERSEDED)\b", file_content
        ):
            return True
        if rel_path == "docs/decisions/index.md":
            return True
    return False


def is_provisional_or_proposed_adr(rel_path: str, file_content: str) -> bool:
    """Check if file is a PROPOSED, PROVISIONAL, or DEPRECATED ADR."""
    if rel_path.startswith("docs/decisions/") and rel_path.endswith(".md"):
        if re.search(
            r"-\s+\*\*Status:\*\*\s+.*?\b(PROPOSED|PROVISIONAL|DEPRECATED|CUT)\b",
            file_content,
        ):
            return True
    return False


def is_code_or_fixture_file(rel_path: str) -> bool:
    """Check if file is source code, tests, or scripts/fixtures."""
    if rel_path.startswith("src/") or rel_path.startswith("tests/"):
        return True
    if (
        rel_path.endswith(".py")
        or rel_path.endswith(".js")
        or rel_path.endswith(".cmd")
        or rel_path.endswith(".sh")
        or rel_path.endswith(".json")
        or rel_path.endswith(".jsonl")
    ):
        return True
    return False


def is_inside_quotes_or_spans(line: str, start: int, end: int) -> tuple[bool, str]:
    """Check if token is enclosed within quotations or code/backtick/italic spans."""
    # Blockquotes (markdown >)
    if re.match(r"^\s*>", line):
        return True, "inside_blockquote"

    # Double quotes: "..."
    for m in re.finditer(r"\"[^\"]*\"", line):
        if m.start() <= start and end <= m.end():
            return True, "inside_double_quotes"

    # Smart double quotes: “...” or ”...”
    for m in re.finditer(r"[\u201c\u201d][^\u201c\u201d]*[\u201c\u201d]", line):
        if m.start() <= start and end <= m.end():
            return True, "inside_smart_double_quotes"

    # Markdown backticks `...`
    for m in re.finditer(r"`[^`]*`", line):
        if m.start() <= start and end <= m.end():
            return True, "inside_backtick_span"

    # Markdown italic spans *(not bold)*: *(...)*
    for m in re.finditer(r"(?<!\*)\*(?!\*)([^\*]+)(?<!\*)\*(?!\*)", line):
        if m.start() <= start and end <= m.end():
            return True, "inside_italic_span"

    return False, ""


def is_whewell_concept_in_prose(line: str, word: str, start: int, end: int) -> bool:
    """Check if 'Consilience' is used specifically as Whewell's epistemic concept."""
    surrounding = line[max(0, start - 40) : min(len(line), end + 40)]
    patterns = [
        r"\bthe\s+consilience\s+of\s+inductions\b",
        r"\bconsilience\s+of\s+inductions\b",
        r"\bconsilience\s+check\b",
        r"\bconsilience\s+test\b",
        r"\bconsilience\s+claim\b",
        r"\bconsilience\s+event\b",
        r"\bgenuine\s+consilience\b",
        r"\bdefinition\s+of\s+consilience\b",
        r"\bparticipate\s+in\s+consilience\b",
        r"\bconvergence\s+is\s+consilience\b",
        r"\btrade-offs\s+of\s+consilience\b",
        r"\bjumping\s+together\b",
    ]
    for pat in patterns:
        if re.search(pat, surrounding, re.I):
            return True
    return False


def classify_token(
    rel_path: str,
    line_number: int,
    word: str,
    start: int,
    end: int,
    line: str,
    file_content: str,
) -> tuple[str, str]:
    """Classify a single token occurrence as renameable, protected, or ambiguous."""
    # 1. Lowercase consilience is always protected as the common noun / concept
    if word.islower():
        return "protected", "lowercase_common_noun_concept"

    # 2. Literal filename CONSILIENCE.md or markdown links to it
    if "CONSILIENCE.md" in line:
        context_window = line[max(0, start - 15) : min(len(line), end + 15)]
        if "CONSILIENCE.md" in context_window:
            return "protected", "filename_or_link_to_consilience_md"

    # 3. If file is CONSILIENCE.md itself
    if Path(rel_path).name == "CONSILIENCE.md":
        return "protected", "grounding_document_consilience_md"

    # 4. Source material directory
    if rel_path.startswith("docs/30-source-material/"):
        return "protected", "source_material_directory"

    # 5. Dated historical documents, transcripts, logs, publications
    if is_dated_or_historical_path(rel_path):
        return "protected", "dated_or_historical_document"

    # 6. Accepted or superseded ADRs
    if is_accepted_or_superseded_adr(rel_path, file_content):
        return "protected", "accepted_or_superseded_adr"

    # 7. Code, fixtures, tests, scripts
    if is_code_or_fixture_file(rel_path):
        return "protected", "code_or_fixture_file"

    # 8. Quotations and formatted spans
    in_quote, quote_reason = is_inside_quotes_or_spans(line, start, end)
    if in_quote:
        return "protected", quote_reason

    # 9. External URLs, orgs, channels, task names
    if re.search(
        r"(joe-hireable/|linear\.app|linear_leg|github\.com|consilience-ai|consilience-dev|#consilience|Consilience-EXP27)",
        line,
    ):
        return "protected", "external_identifier_or_url"

    # 10. Semantic Whewell concept phrases in prose
    if is_whewell_concept_in_prose(line, word, start, end):
        return "protected", "whewell_epistemic_concept"

    # 11. Specific boundary cases:
    # Provisional or proposed ADRs
    if is_provisional_or_proposed_adr(rel_path, file_content):
        return "ambiguous", "provisional_or_proposed_adr_body"

    # Citations of ADR-0008 or fixing of the name on 19 Aug 2026
    if re.search(r"\b(ADR-0008|0008)\b", line):
        return "protected", "adr_0008_historical_citation"
    if "fixed 19 Aug 2026" in line:
        return "ambiguous", "historical_fixing_of_name"

    # Package reservations for consilience
    if rel_path.startswith("packages/") and re.search(
        r"\breserv(ed|ation)\b", line, re.I
    ):
        return "ambiguous", "package_name_reservation_text"

    # Living documentation files where project name is used
    living_doc_roots = [
        "AGENTS.md",
        "README.md",
        ".agents/skills/",
        "docs/40-spec/",
        "docs/publications/",
        "docs/10-research/",
        "docs/20-design/",
        "docs/00-context/",
    ]
    if any(rel_path == root or rel_path.startswith(root) for root in living_doc_roots):
        # If word is capitalized Consilience referring to the project name:
        if word == "Consilience":
            return "renameable", "project_name_in_living_doc"
        elif word == "Consilience's":
            return "renameable", "project_name_possessive_in_living_doc"

    return "ambiguous", "unclassified_boundary_case"


def scan_repository(root: Path) -> list[Occurrence]:
    """Scan all tracked files in repository and classify all occurrences."""
    occurrences: list[Occurrence] = []
    pattern = re.compile(r"\b[Cc]onsilienc\w*\b")

    for rel_path in tracked_files(root):
        file_path = root / rel_path
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in pattern.finditer(line):
                word = match.group(0)
                start, end = match.start(), match.end()
                classification, reason = classify_token(
                    rel_path, line_num, word, start, end, line, content
                )
                occurrences.append(
                    Occurrence(
                        file=rel_path,
                        line_number=line_num,
                        start=start,
                        end=end,
                        word=word,
                        classification=classification,
                        reason=reason,
                        line_content=line,
                    )
                )

    return occurrences


def apply_rename_sweep(root: Path, occurrences: list[Occurrence]) -> int:
    """Apply rename to all renameable occurrences only. Returns count of replacements."""
    renameable_by_file: dict[str, list[Occurrence]] = {}
    for occ in occurrences:
        if occ.classification == "renameable":
            renameable_by_file.setdefault(occ.file, []).append(occ)

    total_renamed = 0
    for rel_path, file_occs in sorted(renameable_by_file.items()):
        file_path = root / rel_path
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            print(f"Error reading {rel_path}: {err}", file=sys.stderr)
            continue

        lines = content.splitlines(keepends=True)
        # Group by line number
        line_map: dict[int, list[Occurrence]] = {}
        for occ in file_occs:
            line_map.setdefault(occ.line_number, []).append(occ)

        new_lines: list[str] = []
        for idx, line in enumerate(lines, start=1):
            if idx not in line_map:
                new_lines.append(line)
                continue

            # Replace from right to left to preserve character offsets
            sorted_occs = sorted(line_map[idx], key=lambda o: o.start, reverse=True)
            cur_line = line
            for occ in sorted_occs:
                replacement = (
                    "Consilient"
                    if occ.word == "Consilience"
                    else "Consilient's"
                    if occ.word == "Consilience's"
                    else "Consilient"
                )
                cur_line = (
                    cur_line[: occ.start] + replacement + cur_line[occ.end :]
                )
                total_renamed += 1
            new_lines.append(cur_line)

        file_path.write_text("".join(new_lines), encoding="utf-8")

    return total_renamed


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", default=".", help="Root directory of the repository"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI invariant check: fails if renameable occurrences remain",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply rename sweep for renameable occurrences",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    occurrences = scan_repository(root)

    renameable = [o for o in occurrences if o.classification == "renameable"]
    protected = [o for o in occurrences if o.classification == "protected"]
    ambiguous = [o for o in occurrences if o.classification == "ambiguous"]

    if args.json:
        payload = {
            "total": len(occurrences),
            "counts": {
                "renameable": len(renameable),
                "protected": len(protected),
                "ambiguous": len(ambiguous),
            },
            "occurrences": [asdict(o) for o in occurrences],
        }
        print(json.dumps(payload, indent=2))
        if args.check and len(renameable) > 0:
            return 1
        return 0

    if args.apply:
        count = apply_rename_sweep(root, occurrences)
        print(f"Applied rename sweep: {count} occurrence(s) updated.")
        return 0

    print("=== Consilience -> Consilient Rename Safety Check ===")
    print(f"Total occurrences scanned: {len(occurrences)}")
    print(f"  - Renameable: {len(renameable)}")
    print(f"  - Protected:  {len(protected)}")
    print(f"  - Ambiguous:  {len(ambiguous)}")

    if renameable:
        print(f"\n[Renameable Occurrences: {len(renameable)}]")
        for o in renameable:
            print(f"  {o.file}:{o.line_number} [{o.word}] -> {o.reason}")
            print(f"    {o.line_content.strip()[:100]}")

    if ambiguous:
        print(f"\n[Ambiguous Occurrences: {len(ambiguous)}]")
        for o in ambiguous:
            print(f"  {o.file}:{o.line_number} [{o.word}] -> {o.reason}")
            print(f"    {o.line_content.strip()[:100]}")

    if args.check:
        if len(renameable) > 0:
            print(
                f"\nFAIL: {len(renameable)} un-renamed project reference(s) found in tracked files.",
                file=sys.stderr,
            )
            return 1
        print("\nPASS: No un-renamed project references found. Protected spans intact.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
