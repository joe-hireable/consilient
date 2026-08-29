"""Generate architecture diagrams from the code rather than drawing them.

Hand-drawn permission and event diagrams drifted the moment the code moved. On 23 August
2026 the documentation plan recorded the live case: drafting the permission model from
ADR-0033 put material_choice on the escalate path, while `_disposition_for` in
`src/consilient/effects.py` executes it. Generation is the check that makes that
contradiction visible.

    python scripts/build_diagrams.py          # rewrite docs/diagrams/*.mmd
    python scripts/build_diagrams.py --check  # fail if any diagram has drifted

The generator now spans three files in this directory. `build_diagrams_sources.py`
finds, reads, parses and digests the source files, extracts literals from their syntax
trees, and writes a document atomically under its provenance header.
`build_diagrams_mermaid.py` holds the four renderers, the DIAGRAMS registry and
`render_all`. This file keeps the command line: argument parsing, the drift check and
the write loop."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_diagrams_sources import (
    DIAGRAM_DIR,
    PRODUCER,
    write_atomic,
)

from build_diagrams_mermaid import (
    DIAGRAMS,
    _disposition_edges,
    _emit_control_flow,
    _family_trees,
    _terminal_disposition,
    render_all,
    render_data_model,
    render_event_flow,
    render_modules,
    render_permission,
)

from build_diagrams_sources import (
    COLUMN_CONSTRAINT,
    Diagram,
    ROOT,
    TABLE_RE,
    _admission_classes,
    _assigned_string,
    _columns,
    _constant_string,
    _declared_admission_classes,
    _document,
    _function,
    _ident,
    _known_modules,
    _label,
    _module_id,
    _parse,
    _read,
    _resolve_from,
    _return_strings,
    _source_paths,
    _string_value,
    _tracked_python,
    source_digest,
)

__all__ = [
    "COLUMN_CONSTRAINT",
    "DIAGRAMS",
    "DIAGRAM_DIR",
    "Diagram",
    "PRODUCER",
    "ROOT",
    "TABLE_RE",
    "_admission_classes",
    "_assigned_string",
    "_columns",
    "_constant_string",
    "_declared_admission_classes",
    "_disposition_edges",
    "_document",
    "_emit_control_flow",
    "_family_trees",
    "_function",
    "_ident",
    "_known_modules",
    "_label",
    "_module_id",
    "_parse",
    "_read",
    "_resolve_from",
    "_return_strings",
    "_source_paths",
    "_string_value",
    "_terminal_disposition",
    "_tracked_python",
    "main",
    "render_all",
    "render_data_model",
    "render_event_flow",
    "render_modules",
    "render_permission",
    "source_digest",
    "write_atomic",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if any generated diagram has drifted"
    )
    args = parser.parse_args(argv)
    try:
        rendered = render_all()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if args.check:
        drifted = []
        for name, content in rendered:
            path = DIAGRAM_DIR / name
            current = path.read_bytes() if path.exists() else b""
            if current != content:
                drifted.append(name)
        if drifted:
            joined = ", ".join(drifted)
            print(
                f"FAIL docs/diagrams/{joined} has drifted; run python {PRODUCER}",
                file=sys.stderr,
            )
            return 1
        print("docs/diagrams is current")
        return 0
    for name, content in rendered:
        write_atomic(DIAGRAM_DIR / name, content)
        print(f"wrote docs/diagrams/{name} ({len(content)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
