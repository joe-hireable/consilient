"""Regenerate `docs/40-spec/requirements.md` from the audited requirement set.

The document is generated, never hand-edited, for one reason: every requirement must trace
to the principal's verbatim words. On 21 August 2026 an audit of 72 hours of his messages
found two rules filed under his signature that he never wrote -- one a loosening that let 71
private commit identifiers reach a results file. Prose drifts; a generated file cannot.

Source of truth is `docs/40-spec/requirements-source.json`, produced by that audit: each
entry carries his quote, the obligation derived from it, the measured status of the code,
the gap, an effort estimate and whether it blocks other work.

    python scripts/build_requirements.py            # rewrite the document
    python scripts/build_requirements.py --check     # fail if it has drifted

`--check` is what CI should run. A generated file nobody verifies is a hand-edited file
waiting to happen.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs/40-spec/requirements-source.json"
TARGET = ROOT / "docs/40-spec/requirements.md"

SYMBOL = {
    "met": "MET",
    "partial": "PARTIAL",
    "substrate-only": "SUBSTRATE ONLY",
    "absent": "ABSENT",
}


def render(reqs: list[dict[str, object]]) -> str:
    by_area: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for r in reqs:
        by_area[str(r["area"])].append(r)
    counts = collections.Counter(str(r["status"]) for r in reqs)

    lines: list[str] = []
    add = lines.append
    add("# Requirements — derived from the principal's own words\n")
    add(
        "> **Source of truth: what Joe Brown typed.** Every requirement below carries his verbatim\n"
        "> quote. Nothing here is inferred from a document, a commit message or an orchestrator's\n"
        "> summary. That constraint exists because on 21 August 2026 an audit found two rules filed\n"
        "> under his signature that he never wrote — one of them a loosening that let 71 private\n"
        "> commit identifiers reach a results file. **A requirement without his words is not a\n"
        "> requirement.**\n"
    )
    add(
        "**Generated** from a 72-hour audit of his messages, 18–21 August 2026, assessed against the\n"
        "code as built. Regenerate with `python scripts/build_requirements.py`; verify with\n"
        "`--check`. **Do not hand-edit.**\n"
    )
    add(
        f"**{len(reqs)} requirements. {counts['met']} met · {counts['partial']} partial · "
        f"{counts['substrate-only']} substrate only · {counts['absent']} absent.** [measured]\n"
    )
    add(
        "**Status meanings.** *Met* — implemented and enforced by a test that can fail. *Partial* —\n"
        "some of it works. *Substrate only* — the machinery exists but nothing uses it, which is the\n"
        "most misleading state because a code inventory reads as progress while a user gets nothing.\n"
        "*Absent* — no implementation.\n"
    )

    blockers = [r for r in reqs if r["blocks"]]
    add(
        f"## Blocking requirements\n\nThese unblock other work, so they come first. "
        f"**{len(blockers)} of {len(reqs)}.**\n"
    )
    add("| id | area | requirement | status | effort |")
    add("|---|---|---|---|---|")
    for r in blockers:
        add(
            f"| **{r['id']}** | {r['area']} | {str(r['requirement'])[:95]} | "
            f"{SYMBOL[str(r['status'])]} | {r['effort']} |"
        )
    add("")

    for area in sorted(by_area):
        add(f"\n## {area.title()}\n")
        for r in sorted(by_area[area], key=lambda x: str(x["id"])):
            flags = []
            if r["blocks"]:
                flags.append("**blocks other work**")
            if r["repeated"]:
                flags.append("**he asked more than once**")
            add(f"### {r['id']} — {SYMBOL[str(r['status'])]}\n")
            add(f"> {str(r['quote']).strip()}\n")
            add(f"**Obligation.** {r['requirement']}\n")
            suffix = f"effort: {r['effort']}\n"
            add(" · ".join(flags) + " · " + suffix if flags else suffix)
            if r["status"] != "met":
                add(f"**Gap.** {str(r['gap']).strip()}\n")
            if r["evidence"]:
                add(f"**Evidence.** {str(r['evidence']).strip()}\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the document has drifted")
    args = parser.parse_args()

    reqs = json.loads(SOURCE.read_text(encoding="utf-8"))
    rendered = render(reqs)

    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != rendered:
            print(
                f"FAIL {TARGET.name} has drifted from {SOURCE.name}. "
                "Run `python scripts/build_requirements.py` and commit the result."
            )
            return 1
        print(f"{TARGET.name} matches {SOURCE.name}: {len(reqs)} requirements")
        return 0

    TARGET.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)} — {len(reqs)} requirements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
