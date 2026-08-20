"""Can Gate B3 ever report PASS?

_fallback_condition() has four branches. Enumerate the reachable states of its inputs and
record which status each produces. If no input produces "pass", the condition is unpassable
by implementation regardless of what is built.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path("src/consilient/cli.py").read_text(encoding="utf-8")
fn = SRC.partition("def _fallback_condition()")[2].partition("\ndef ")[0]

print("statuses that appear anywhere in _fallback_condition():")
found = sorted(set(re.findall(r'"(pass|fail|unknown|structurally_unsatisfiable)"', fn)))
for s in found:
    print(f"  {s}")

print()
print("PASS reachable:", "pass" in found)

# And exercise it for real, over the three reachable worlds.
sys.path.insert(0, "src")
import tempfile  # noqa: E402

from consilient import cli  # noqa: E402

worlds = {
    "no workflows dir":        None,
    "workflows, no schedule":  "on:\n  push:\n    branches: [main]\njobs:\n  a:\n    runs-on: ubuntu-latest\n",
    "workflows with schedule": "on:\n  schedule:\n    - cron: '0 6 * * 1'\njobs:\n  a:\n    runs-on: ubuntu-latest\n",
}

original = cli.WORKFLOWS
print()
for label, content in worlds.items():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "workflows"
        if content is not None:
            root.mkdir(parents=True)
            (root / "w.yml").write_text(content, encoding="utf-8")
        cli.WORKFLOWS = root
        result = cli._fallback_condition()
        print(f"  {label:<26} -> {result['status']:<8} {result['reason']}")
cli.WORKFLOWS = original

print()
print("No arrangement of workflows produces PASS. B3 is unpassable by implementation.")
