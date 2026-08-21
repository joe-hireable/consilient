#!/usr/bin/env python3
"""Enumerate the live cursor-agent model surface and keep the registry honest (R24).

`src/consilient/harness.py`'s MODELS literal is a snapshot of
`cursor-agent --list-models`; it goes stale silently. This script is the local,
on-demand enumeration the registry never had. No telemetry: one local subprocess,
on demand, writing nothing unless asked.

    python scripts/refresh_models.py            # report drift, exit 1 on any
    python scripts/refresh_models.py --write    # refresh the MODELS literal in place

`--write` preserves the registered order of surviving ids (that order is the
preference claim, [asserted]) and appends new ids sorted. Vendor-pool ids
(claude-*/gpt-*/gemini-*) and `auto` are never written: the first bill to the
avoided Other Models pool, the second is an unnamed spend.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.harness import (  # noqa: E402
    MODELS,
    ModelOption,
    cursor_models_pool_ids,
    model_family,
    parse_list_models,
    registry_drift,
)

HARNESS_PY = ROOT / "src" / "consilient" / "harness.py"
CURSOR_WSL_BINARY = Path("/home/jpbpr/.local/bin/cursor-agent")
PROBE_TIMEOUT_S = 30


def _run(argv: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PROBE_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        return -1, "", f"not found: {exc}"
    except subprocess.TimeoutExpired:
        return -1, "", f"probe timed out after {PROBE_TIMEOUT_S}s"
    except OSError as exc:
        return -1, "", f"{type(exc).__name__}: {exc}"
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def list_models_live() -> tuple[str, ...] | str:
    """Live ids from the local cursor-agent, or a refusal reason string."""
    if CURSOR_WSL_BINARY.exists():
        code, out, err = _run([str(CURSOR_WSL_BINARY), "--list-models"])
    else:
        import shutil

        native = shutil.which("cursor-agent")
        if native is not None:
            code, out, err = _run([native, "--list-models"])
        else:
            bridge = shutil.which("wsl")
            if bridge is None:
                return "cursor-agent is not reachable (no native binary and no wsl bridge)"
            code, out, err = _run([bridge, "-e", "bash", "-lc", "cursor-agent --list-models"])
    if code != 0 or not out.strip():
        return f"cursor-agent --list-models failed (exit {code}): {err.strip() or 'no output'}"
    ids = parse_list_models(out)
    if not ids:
        return "cursor-agent --list-models produced no parseable ids"
    return ids


def render_registry(live_ids: tuple[str, ...], existing: tuple[ModelOption, ...]) -> str:
    """The replacement MODELS block: surviving ids keep their order, new ids append."""
    pool_ids = cursor_models_pool_ids(live_ids)
    live_set = set(pool_ids)
    known = {item.id: item for item in existing if item.harness_id == "cursor-composer"}
    ordered = [item.id for item in existing if item.id in live_set]
    ordered += [mid for mid in pool_ids if mid not in known]
    today = datetime.now(timezone.utc).date().isoformat()
    lines = [
        f"# `cursor-agent --list-models` on this machine, {today} [measured]: "
        f"{len(live_ids)} ids. Refreshed by scripts/refresh_models.py --write; order of",
        "# surviving ids preserved (preference, [asserted]); new ids appended sorted. The",
        "# Cursor Models pool serves the non-vendor families below; claude-*/gpt-*/gemini-*",
        "# bill to the avoided Other Models pool (CURSOR_OTHER_PREFIXES). `auto` is",
        "# deliberately absent: selection must name what it spends.",
        "MODELS: tuple[ModelOption, ...] = (",
    ]
    for mid in ordered:
        lines.append(
            f'    ModelOption("{mid}", "cursor-composer", "{model_family(mid)}", "cursor-models"),'
        )
    lines.append(")")
    return "\n".join(lines)


def write_registry(live_ids: tuple[str, ...]) -> None:
    text = HARNESS_PY.read_text(encoding="utf-8")
    start = text.find("# `cursor-agent --list-models`")
    end = text.find("\n)\n", text.find("MODELS: tuple[ModelOption, ...] = ("))
    if start == -1 or end == -1:
        raise SystemExit("could not locate the MODELS block in harness.py; refusing to rewrite")
    replacement = render_registry(live_ids, MODELS)
    HARNESS_PY.write_text(text[:start] + replacement + text[end + 3 :], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh the MODELS literal")
    args = parser.parse_args()

    live = list_models_live()
    if isinstance(live, str):
        print(f"refused: {live}")
        return 2
    missing, stale = registry_drift(live)
    if not missing and not stale:
        print(f"registry matches the machine ({len(cursor_models_pool_ids(live))} pool ids)")
        return 0
    if missing:
        print(f"live but unregistered ({len(missing)}): {', '.join(missing)}")
    if stale:
        print(f"registered but no longer live ({len(stale)}): {', '.join(stale)}")
    if args.write:
        write_registry(live)
        print("harness.py MODELS literal refreshed; re-run to confirm, then commit")
        return 0
    print("drift: run with --write to refresh the registry")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
