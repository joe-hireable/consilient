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
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "40-spec" / "requirements-source.json"
TARGET = ROOT / "docs" / "40-spec" / "requirements.md"
SOURCE_GLOB = "docs/40-spec/requirements-source.json"

SYMBOL = {
    "met": "MET",
    "partial": "PARTIAL",
    "substrate-only": "SUBSTRATE ONLY",
    "absent": "ABSENT",
}


def source_digest() -> str:
    digest = hashlib.sha256()
    relative = SOURCE.relative_to(ROOT).as_posix()
    # Normalise line endings first — see the same repair in build_decision_index.py. Digesting
    # working-tree bytes under `* text=auto eol=lf` bakes the authoring checkout's line endings
    # into the committed header, so the check passes for its author and fails for everyone else.
    file_digest = hashlib.sha256(
        SOURCE.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    digest.update(relative.encode("utf-8"))
    digest.update(b"\0")
    digest.update(file_digest.encode("ascii"))
    digest.update(b"\n")
    return digest.hexdigest()


def render(reqs: list[dict[str, object]]) -> str:
    by_area: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for r in reqs:
        by_area[str(r["area"])].append(r)
    counts = collections.Counter(str(r["status"]) for r in reqs)

    lines: list[str] = []
    add = lines.append
    add("# Requirements — audit-extracted, attribution not attested\n")
    add("> **Producer:** `scripts/build_requirements.py`")
    add(f"> **Source:** `{SOURCE_GLOB}`")
    add(f"> **Source SHA-256:** `{source_digest()}`")
    add(
        "> **Do not hand-edit:** regenerate with `python scripts/build_requirements.py`."
    )
    add("")
    add(
        "> **Provenance warning, 21 August 2026. Read this before citing anything below.**\n"
        ">\n"
        "> These requirements were extracted by an automated audit of the principal's messages.\n"
        '> **At least one quote was fabricated.** Shown R11 — *"Do not let any arm run unbounded.\n'
        '> Hard turn and token caps."* — he stated plainly that those are not his words. Its\n'
        "> attribution is withdrawn below, and two further quotes could not be located in his\n"
        "> transcripts at all.\n"
        ">\n"
        "> **The other 33 are confirmed by the principal himself**, on review, 21 August 2026:\n"
        '> *"Most of them did."* That is the strongest verification available and it outranks any\n'
        "> mechanical check — two of which were attempted here and both were wrong. They searched\n"
        "> a corpus that interleaves his typed messages with tool results, injected file contents\n"
        "> and assistant replies, so a quote matched this document quoting itself. The first\n"
        "> reported 33 of 36 verified by accident, and would have cleared the fabricated one.\n"
        "> **A search for a quote inside a corpus containing that quote's own source file proves\n"
        "> nothing.**\n"
        ">\n"
        "> **An obligation can be right while its attribution is wrong.** Where that holds the\n"
        "> requirement is kept on engineering merit and says so — but it carries no claim on the\n"
        "> principal's authority. Invariant V0-18 means only he can supply that, and a requirement\n"
        "> he did not write must never be quoted back to him as though he had.\n"
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


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the document has drifted"
    )
    args = parser.parse_args()

    try:
        reqs = json.loads(SOURCE.read_text(encoding="utf-8"))
        rendered = render(reqs)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1

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

    write_atomic(TARGET, rendered)
    print(f"wrote {TARGET.relative_to(ROOT)} — {len(reqs)} requirements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
