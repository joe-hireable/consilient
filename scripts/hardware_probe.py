"""Detect local hardware and emit a JSON profile for `local_fit`.

Impure detection lives here; the fit decision lives in `src/consilient/local_fit.py`.
Anything that cannot be read is emitted as unknown — never inferred.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from consilient.local_fit import (  # noqa: E402
    hardware_profile_from_mapping,
    profile_to_mapping,
    unknown_profile,
)

PROVENANCE = "scripts/hardware_probe.py"
_SUBPROCESS_KW = {"encoding": "utf-8", "errors": "replace", "timeout": 30}


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nvidia_total_vram_bytes() -> int | None:
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=True,
            **_SUBPROCESS_KW,
        ).stdout.strip()
        if not out:
            return None
        total_mib = int(out.splitlines()[0].strip())
        return total_mib * 1024 * 1024
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _rocm_detected() -> bool:
    try:
        subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"],
            capture_output=True,
            check=True,
            **_SUBPROCESS_KW,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _system_ram_bytes() -> int | None:
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        try:
            for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1]) * 1024
        except OSError:
            return None
    if platform.system() == "Darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                check=True,
                **_SUBPROCESS_KW,
            ).stdout.strip()
            return int(out)
        except (OSError, subprocess.SubprocessError, ValueError):
            return None
    return None


def _free_disk_bytes(path: Path = ROOT) -> int | None:
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return None


def _backend() -> str | None:
    if _nvidia_total_vram_bytes() is not None:
        return "cuda"
    if _rocm_detected():
        return "rocm"
    if platform.system() == "Darwin" and platform.machine().lower().startswith("arm"):
        return "metal"
    if _system_ram_bytes() is not None:
        return "cpu"
    return None


def _unified_memory(backend: str | None) -> bool | None:
    if backend == "metal":
        return True
    if backend in {"cuda", "rocm"}:
        return False
    return None


def probe() -> dict[str, object]:
    """Return a JSON-serialisable hardware profile. Failures become all-unknown."""
    try:
        backend = _backend()
        profile = hardware_profile_from_mapping(
            {
                "total_vram_bytes": _nvidia_total_vram_bytes(),
                "system_ram_bytes": _system_ram_bytes(),
                "free_disk_bytes": _free_disk_bytes(),
                "backend": backend,
                "unified_memory": _unified_memory(backend),
                "provenance": PROVENANCE,
                "probed_at": _now_ts(),
            }
        )
        return profile_to_mapping(profile)
    except Exception:
        return profile_to_mapping(unknown_profile(provenance=PROVENANCE, probed_at=_now_ts()))


def main() -> int:
    parser = __import__("argparse").ArgumentParser(
        description="Emit detected hardware as JSON for local_fit."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (default is compact).",
    )
    args = parser.parse_args()
    payload = probe()
    indent = 2 if args.pretty else None
    json.dump(payload, sys.stdout, indent=indent)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
