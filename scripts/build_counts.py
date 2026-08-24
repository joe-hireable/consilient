"""Fill the generated count regions in README.md and CLAUDE.md from disk.

Hand-written restatements of these numbers drifted: README.md claimed 34 ADRs
and 35 registered experiments while the tree held 95 and 109, and CLAUDE.md
independently claimed 45 and 47 against the same disk. [measured] Generation
from the files is the repair; `--check` is the ratchet.

    python scripts/build_counts.py            # rewrite the generated regions
    python scripts/build_counts.py --check    # fail if a region has drifted

Counts: ADR files matching `docs/decisions/[0-9][0-9][0-9][0-9]-*.md`, EXP
headings in `docs/10-research/experiment-register.md`, and named steps in
`.github/workflows/invariants.yml`. The ADR and experiment regexes are the
ones `tests/test_generated_documents.py` already uses, so the two cannot
disagree about what they are counting.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ADR_GLOB = "[0-9][0-9][0-9][0-9]-*.md"
EXP_HEADING = re.compile(r"^#{2,4}\s*EXP-\d+", re.MULTILINE)
STEP_NAME = re.compile(r"^\s+- name: .+$", re.MULTILINE)
MARKER = "scripts/build_counts.py"

TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("README.md", ("inventory", "experiments")),
    ("CLAUDE.md", ("inventory",)),
)


def counts(root: Path) -> tuple[int, int, int]:
    adrs = len(list((root / "docs" / "decisions").glob(ADR_GLOB)))
    register = root / "docs" / "10-research" / "experiment-register.md"
    experiments = len(EXP_HEADING.findall(register.read_text(encoding="utf-8")))
    workflow = root / ".github" / "workflows" / "invariants.yml"
    steps = len(STEP_NAME.findall(workflow.read_text(encoding="utf-8")))
    return adrs, experiments, steps


def bodies(adr_count: int, experiment_count: int, step_count: int) -> dict[str, dict[str, str]]:
    return {
        "README.md": {
            "inventory": (
                f"{adr_count} ADRs, {experiment_count} registered experiments, "
                f"{step_count} invariant checks in CI."
            ),
            "experiments": f"{experiment_count} experiments with stopping rules",
        },
        "CLAUDE.md": {
            "inventory": f"{adr_count} ADRs and {experiment_count} registered experiments",
        },
    }


def _region_pattern(name: str) -> re.Pattern[str]:
    ident = re.escape(f"{MARKER}#{name}")
    return re.compile(
        rf"<!-- BEGIN GENERATED: {ident} -->\n.*?\n<!-- END GENERATED: {ident} -->",
        re.DOTALL,
    )


def splice(text: str, name: str, body: str, *, path: str) -> str:
    begin = f"<!-- BEGIN GENERATED: {MARKER}#{name} -->"
    end = f"<!-- END GENERATED: {MARKER}#{name} -->"
    replacement = f"{begin}\n{body}\n{end}"
    updated, n = _region_pattern(name).subn(replacement, text, count=1)
    if n != 1:
        raise ValueError(f"{path}: missing generated region {name}")
    return updated


def render(root: Path) -> dict[Path, str]:
    rendered_bodies = bodies(*counts(root))
    documents: dict[Path, str] = {}
    for relative, names in TARGETS:
        path = root / relative
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        for name in names:
            text = splice(text, name, rendered_bodies[relative][name], path=relative)
        documents[path] = text
    return documents


def write_atomic(path: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
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
        "--check", action="store_true", help="fail if a generated region has drifted"
    )
    args = parser.parse_args(argv)
    try:
        documents = render(ROOT)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if args.check:
        drifted = [
            path.relative_to(ROOT).as_posix()
            for path, expected in documents.items()
            if path.read_text(encoding="utf-8").replace("\r\n", "\n") != expected
        ]
        if drifted:
            print(
                "FAIL "
                + ", ".join(drifted)
                + " drifted; run python scripts/build_counts.py"
            )
            return 1
        print("generated counts are current")
        return 0
    for path, expected in documents.items():
        write_atomic(path, expected)
        print(f"wrote {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
