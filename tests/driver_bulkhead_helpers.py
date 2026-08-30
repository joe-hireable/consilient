"""Loading `.harness/build_driver.py` for the Z06 bulkhead units.

The driver is a script rather than a package module, so every check reaches it through
`importlib.util.spec_from_file_location` and a fresh module object. `ROOT` and `DRIVER`
name the path once, so the four modules that pin this driver cannot drift about which
file they are pinning.

Only the loader is shared. Several checks assert on the driver's *source* rather than
its behaviour, because the admission sites they guard live inside `main()` and cannot be
called in isolation; those readers stay in the module that needs them, so a pin cannot
quietly widen to cover code no one meant to pin."""

import importlib.util
import sys
from pathlib import Path

from build_driver_helpers import _sandbox_instance_paths

ROOT = Path(__file__).resolve().parent.parent

DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("build_driver_bulkhead", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _sandbox_instance_paths(module)
    return module
