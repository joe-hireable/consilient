"""Fixtures shared by the dispatch suites — the script loader and the two probe
snapshots every one of them needs.

`dispatch.py` is a script, not a package module (ADR-0058), so it is loaded by path and
cached in `sys.modules`; loading it once per session is what makes
`monkeypatch.setattr(script, ...)` in the other files address the same object.
`INSTALLED` is the all-present probe snapshot and `CAP_HELP` the help text a CLI would
print if it exposed both native caps — both are fixtures, not observations of this
machine.

`_git` runs git with every `GIT_*` variable stripped from the environment. That is not
tidiness: these tests build throwaway repositories, and a harness that inherited
`GIT_DIR` from its parent would write the fixture's commits into whatever repository
that pointer named."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from consilient.harness import (
    HARNESSES,
    Probe,
)

DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"

INSTALLED = tuple(
    Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
)

CAP_HELP = (
    "  --max-turns <N>\n  --max-tokens <N>\n"
    "  --always-approve --force --trust --skip-git-repo-check"
)


def _load_script():
    name = "consilient_dispatch_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "t@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "t@example.com"
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
