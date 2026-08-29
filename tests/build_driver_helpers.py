"""Loading the build driver under test, once, for every file that checks it.

`.harness/build_driver.py` is not importable as a package member — it is a script the
loop executes — so every check against it loads it from its path. `DRIVER` is also read
as *source* by several structural checks, which assert on the shape of the file rather
than on its behaviour, and `ROOT` locates `build_loop.py` for the checks that sit beside
the driver's own. All three are needed by more than one of the files this module was
split into, so they live here rather than in whichever one happened to define them
first."""

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("build_driver_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
