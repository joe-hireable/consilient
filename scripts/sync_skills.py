"""Keep ``.claude/skills`` aligned with ``.agents/skills``."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / ".agents" / "skills"
MIRROR = ROOT / ".claude" / "skills"
Entry = tuple[str, bytes | str | None]


def _snapshot(root: Path) -> dict[str, Entry]:
    entries: dict[str, Entry] = {}

    def visit(directory: Path) -> None:
        with os.scandir(directory) as children:
            for child in sorted(children, key=lambda item: item.name):
                path = Path(child.path)
                relative = path.relative_to(root).as_posix()
                if child.is_symlink():
                    entries[relative] = ("symlink", os.readlink(path))
                elif child.is_dir(follow_symlinks=False):
                    entries[relative] = ("directory", None)
                    visit(path)
                elif child.is_file(follow_symlinks=False):
                    entries[relative] = ("file", path.read_bytes())
                else:
                    entries[relative] = ("other", None)

    visit(root)
    return entries


def find_drift(source: Path, mirror: Path) -> list[str]:
    if not source.is_dir():
        return [f"source is not a directory: {source}"]
    if mirror.is_symlink():
        if mirror.resolve() == source.resolve():
            return []
        return [f"symlink target differs: {mirror}"]
    if not mirror.exists():
        return [f"missing mirror: {mirror}"]
    if not mirror.is_dir():
        return [f"mirror is not a directory or symlink: {mirror}"]

    wanted = _snapshot(source)
    actual = _snapshot(mirror)
    errors = [f"missing: {path}" for path in sorted(wanted.keys() - actual.keys())]
    errors.extend(f"extra: {path}" for path in sorted(actual.keys() - wanted.keys()))
    for path in sorted(wanted.keys() & actual.keys()):
        wanted_type, wanted_value = wanted[path]
        actual_type, actual_value = actual[path]
        if wanted_type != actual_type:
            errors.append(f"type differs: {path}")
        elif wanted_value != actual_value:
            errors.append(f"content differs: {path}")
    if not errors:
        return []
    return errors


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def repair(source: Path, mirror: Path) -> str:
    """Replace the mirror with a relative symlink, or an exact copy if denied."""
    if not source.is_dir():
        raise FileNotFoundError(f"skills source is missing: {source}")
    descriptor, candidate_name = tempfile.mkstemp(
        prefix=f".{mirror.name}.", dir=mirror.parent
    )
    os.close(descriptor)
    candidate = Path(candidate_name)
    candidate.unlink()
    target = os.path.relpath(source, candidate.parent).replace(os.sep, "/")
    try:
        try:
            os.symlink(target, candidate, target_is_directory=True)
            mode = "symlink"
        except OSError:
            _remove(candidate)
            shutil.copytree(source, candidate, symlinks=True)
            mode = "copy"
        _remove(mirror)
        os.replace(candidate, mirror)
        return mode
    finally:
        _remove(candidate)


def main(
    argv: list[str] | None = None,
    *,
    source: Path = SOURCE,
    mirror: Path = MIRROR,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="report drift without repairing it"
    )
    args = parser.parse_args(argv)

    if args.check:
        errors = find_drift(source, mirror)
        if errors:
            print("skills mirror drift:")
            for error in errors:
                print(f"- {error}")
            return 1
        mode = "symlink" if mirror.is_symlink() else "copy"
        print(f"skills mirror passes: {mode} mirror is current")
        return 0

    try:
        mode = repair(source, mirror)
    except OSError as exc:
        print(f"skills mirror repair failed: {exc}", file=sys.stderr)
        return 1
    errors = find_drift(source, mirror)
    if errors:
        print("skills mirror repair produced drift:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"skills mirror repaired as {mode}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
