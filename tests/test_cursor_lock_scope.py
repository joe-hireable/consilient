from __future__ import annotations

from family_source import seam

import importlib.util
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from consilient.harness import harness_by_id


DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"

CHILD = r"""
import json
import os
import sys
import time
from pathlib import Path

config = Path(sys.argv[1])
marker = Path(sys.argv[2])
start_at = int(sys.argv[3])
started = time.time_ns()
while time.time_ns() < start_at:
    time.sleep(0.001)
try:
    handle = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
except FileExistsError:
    config.write_bytes(b"{broken")
    print("overlapping config startup", file=sys.stderr)
    raise SystemExit(23)
try:
    raw = config.read_bytes()
    json.loads(raw)
    time.sleep(0.2)
finally:
    os.close(handle)
    marker.unlink(missing_ok=True)
time.sleep(5.0)
print(json.dumps({"config_hex": raw.hex(), "started": started, "ended": time.time_ns()}))
"""


def _load_dispatch():
    name = "consilient_dispatch_cursor_lock_scope"
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_cursor_lock_covers_startup_but_not_the_runtime(tmp_path, monkeypatch):
    script = _load_dispatch()
    config = tmp_path / "cli-config.json"
    marker = tmp_path / "config-critical"
    expected = b'{"trust":["workspace"],"model":"composer-2.5"}\n'
    config.write_bytes(expected)
    start_at = time.time_ns() + 1_000_000_000

    def local_cursor(_harness, **kwargs):
        label = kwargs["brief"].parent.name
        return [
            sys.executable,
            "-c",
            CHILD,
            str(config),
            str(marker),
            str(start_at),
            label,
        ]

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", local_cursor)
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_CURSOR_LOCK", tmp_path / "cursor.lock")
    monkeypatch.setattr(seam("dispatch_vocabulary"), "CURSOR_START_SETTLE_S", 1.6, raising=False)
    monkeypatch.setattr(seam("dispatch_vocabulary"), "CURSOR_START_LOCK_TIMEOUT_S", 15.0, raising=False)
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    barrier = threading.Barrier(3)

    def run(label):
        barrier.wait()
        return script.run_harness(
            harness,
            task="local cursor lock check",
            cwd=tmp_path,
            run_dir=tmp_path / label,
            timeout_s=20,
            model="composer-2.5",
            run_id=label,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, label) for label in ("first", "second")]
        barrier.wait()
        results = [future.result() for future in futures]

    assert [result.status for result in results] == ["ok", "ok"], [
        (result.status, result.reason, result.stderr[-400:]) for result in results
    ]
    payloads = [json.loads(result.stdout) for result in results]
    assert [bytes.fromhex(payload["config_hex"]) for payload in payloads] == [
        expected,
        expected,
    ]
    assert config.read_bytes() == expected
    assert json.loads(config.read_text(encoding="utf-8")) == {
        "trust": ["workspace"],
        "model": "composer-2.5",
    }
    assert max(payload["started"] for payload in payloads) < min(
        payload["ended"] for payload in payloads
    )
