"""Loading the build driver under test, once, for every file that checks it.

`.harness/build_driver.py` is not importable as a package member — it is a script the
loop executes — so every check against it loads it from its path. `DRIVER` is also read
as *source* by several structural checks, which assert on the shape of the file rather
than on its behaviour, and `ROOT` locates `build_loop.py` for the checks that sit beside
the driver's own. All three are needed by more than one of the files this module was
split into, so they live here rather than in whichever one happened to define them
first."""

import atexit
import importlib.util
import shutil
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DRIVER = ROOT / ".harness" / "build_driver.py"


# One throwaway tree per pytest process, one subdirectory of it per load, removed at exit.
_SANDBOX = Path(tempfile.mkdtemp(prefix="build-driver-tests-"))
atexit.register(shutil.rmtree, _SANDBOX, ignore_errors=True)


def _sandbox_instance_paths(module: types.ModuleType) -> None:
    """Repoint every `.harness/` path the loaded driver holds at a throwaway tree.

    MEASURED 30 August 2026, at a cost of about ten hours of stalled pipeline. Four
    zero-byte files -- `U01-verify.out`, `U01-verify.err`, `U01-verify-3.out` and
    `U01-verify-3.err` -- sat in the live `.harness/dispatch/briefs-driver`. U01 is a
    fixture id: the 147-unit plan has never contained it. `spawn_logged` opens both log
    paths with mode 'w' BEFORE it calls `Popen`, so a stubbed `Popen` failed the check
    only after the live directory already held the files, empty.

    Reclamation then read them back. It judges silence from the newest mtime under
    `BRIEFS` for `uid`, `uid-resolve` and `uid-verify`, so for the first 1,800 seconds
    -- PROGRESS_SILENCE_S -- the three checks that seed `in_flight` with U01 passed, and
    from 1,801 onwards they failed for ever: the slot was reclaimed, `live_dispatchers`
    fell to zero and the guarded rebase fired. Because `suite_green()` gates both
    publication and retirement, the whole pipeline stopped half an hour after the files
    were written. Deleting them made all three pass again the same minute, which is the
    whole of the diagnosis and none of the fix.

    Isolation used to be opt-in per check, and that is how it was missed: nine `main()`
    call sites ran with `BRIEFS` unpatched while their neighbours patched it. Rebinding
    at the load makes it the default, and it moves every `Path` under the live
    `.harness/`, not a list of names -- `TICK_LOCK` was already outside every list
    anyone had written.

    `UNITS` is left live deliberately. Nothing in this repository writes
    `.harness/plan-units.json`, and four lane checks read the real plan as evidence;
    redirecting it would turn those into silent skips, which is a worse failure than the
    one being repaired because nothing reports it.
    """
    live = (module.ROOT / ".harness").resolve()
    fake = Path(tempfile.mkdtemp(dir=_SANDBOX)) / ".harness"
    for name, value in vars(module).copy().items():
        if name == "UNITS" or not isinstance(value, Path):
            continue
        resolved = value.resolve()
        if live in resolved.parents:
            setattr(module, name, fake / resolved.relative_to(live))


def _load_driver() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("build_driver_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _sandbox_instance_paths(module)
    return module
