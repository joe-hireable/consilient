"""A source-level scan proving the product tree holds no outbound or credential
capability: no network, no subprocess, no environment read, no dynamic execution, and no
client-shaped method call that would carry one.

The two import allowlists are not a style preference. Each entry was admitted on a date
for a stated reason, and those reasons stay recorded beside the names: `time` for the
bounded backoff in `events.read`, after Windows refused a reader while a concurrent
writer held the trajectory and that collision killed 6 of 6 failed dispatches on 23
August 2026; `fcntl`, `msvcrt`, `os` and `time` as the F01 durability primitives added
22 Aug 2026; `ast` added 23 Aug 2026 for S02; and `html` added 21 Aug 2026 for ADR-0053,
because hand-rolling escaping to avoid an inert import trades a stdlib call for an
injection bug. The dangerous surface stays banned independently of any allowlist.

The negative controls are the point of the file. A guard never shown to fail is not
known to be a guard, so every ban carries a probe that must raise — including the six
containment escapes, and the pin that `promote.py` carries its containment probe as a
payload string rather than importing the capability it probes."""

import ast
from pathlib import Path
import pytest

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "dotenv",
    "ftplib",
    "getpass",
    "http",
    "httpx",
    "keyring",
    "openai",
    "openrouter",
    "requests",
    "smtplib",
    "socket",
    "subprocess",
    "telnetlib",
    "urllib",
    "urllib3",
    "webbrowser",
    "xmlrpc",
}

FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "getpass.getpass",
    "importlib.import_module",
    "os.environ.get",
    "os.getenv",
    "os.popen",
    "os.system",
}

BUDGET_IMPORTS = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "events",
    "pathlib",
    "typing",
}

PRODUCT_IMPORTS = BUDGET_IMPORTS | {
    "",
    "argparse",
    "contextlib",
    "contextvars",
    # `time` earns its place by measurement, not convenience. Windows refuses a reader while a
    # concurrent writer holds the trajectory, and that collision killed 6 of 6 failed dispatches
    # on 23 August 2026. The repair is a bounded backoff in `events.read`, which needs a sleep.
    # It carries no capability: no subprocess, no network, no credential, and `compile`, `eval`,
    # `exec` and `__import__` stay forbidden regardless of what is importable.
    "time",
    # `fcntl`, `msvcrt`, `os` and `time` are the F01 durability primitives: the
    # kernel-backed per-log lock (flock / locking), unbuffered os.write, fsync and
    # ftruncate in `events.py`. Added 22 Aug 2026. The dangerous `os` surface stays
    # banned independently of this list — FORBIDDEN_CALLS still refuses os.system,
    # os.popen, os.getenv and os.environ.get, the environ subscript check stands, and
    # their negative controls below stay green.
    # `ast` is a parser and nothing else. Added 23 Aug 2026 for S02, which inspects a
    # candidate's own source to detect forbidden imports before sealing its evaluation —
    # the same inspection this file performs. It performs no I/O and cannot execute:
    # `compile`, `eval`, `exec`, `__import__` and `getattr` remain in FORBIDDEN_CALLS
    # independently, `promote.py` calls none of them, and their negative controls stay
    # green. The alternative — a hand-rolled regex over Python source — would trade an
    # inert stdlib parser for a scanner that misses cases, which is the same trade the
    # `html` entry below refuses.
    "ast",
    "fcntl",
    "hashlib",
    # `html` is escaping only. Added 21 Aug 2026 for the observability surface (ADR-0053),
    # which must escape trajectory content before it reaches a rendered page. It performs no
    # I/O of any kind, which is the property this allowlist is actually protecting. The
    # alternative — hand-rolling escaping to avoid an import — would trade an inert stdlib
    # call for an injection bug, so it is refused.
    "html",
    "json",
    "math",
    "msvcrt",
    "os",
    "re",
    "shutil",
    "sqlite3",
    "sys",
    "time",
}

FORBIDDEN_METHODS = {
    "complete",
    "completion",
    "delete",
    "invoke",
    "patch",
    "post",
    "put",
    "request",
    "send",
    "sendall",
}

BUDGET_FORBIDDEN_METHODS = {"open", "read_bytes", "read_text"}


def qualified_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def capability_violations(source, *, budget_module=False, product_module=False):
    tree = ast.parse(source)
    aliases = {}
    violations = []
    allowed_imports = (
        BUDGET_IMPORTS if budget_module else PRODUCT_IMPORTS if product_module else None
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                aliases[name.asname or name.name.split(".")[0]] = name.name
                if name.name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(f"forbidden import {name.name}")
                if allowed_imports is not None and name.name not in allowed_imports:
                    violations.append(f"non-refuse-only import {name.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                target = f"{module}.{name.name}" if module else name.name
                aliases[name.asname or name.name] = target
            # A relative import (`from .capabilities import Gate`) is intra-package by
            # definition and cannot introduce external capability — the sibling module is
            # itself covered by this same check. `node.level > 0` is what distinguishes it,
            # and reading `node.module` alone made every relative import look like a
            # third-party one. Found 23 Aug 2026 when `effects.py` imported a sibling and
            # was refused; it would have recurred for every new intra-package import.
            # FORBIDDEN_IMPORT_ROOTS still applies: a relative import cannot reach `os` or
            # `socket`, and the forbidden-call scan below is unaffected either way.
            if node.level and node.level > 0:
                continue
            if module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"forbidden import {module}")
            if allowed_imports is not None and module not in allowed_imports:
                violations.append(f"non-refuse-only import {module}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = qualified_name(node.func)
            root, _, rest = name.partition(".")
            resolved = aliases.get(root, root) + (f".{rest}" if rest else "")
            if (
                resolved in FORBIDDEN_CALLS
                or resolved.split(".")[0] in FORBIDDEN_IMPORT_ROOTS
                or resolved.rsplit(".", 1)[-1] in FORBIDDEN_METHODS
                or (
                    budget_module
                    and resolved.rsplit(".", 1)[-1] in BUDGET_FORBIDDEN_METHODS
                )
            ):
                violations.append(f"forbidden call {resolved}")
        elif isinstance(node, ast.Subscript):
            name = qualified_name(node.value)
            root, _, rest = name.partition(".")
            resolved = aliases.get(root, root) + (f".{rest}" if rest else "")
            if resolved == "os.environ":
                violations.append("forbidden credential environment read")
            if (
                resolved == "__builtins__"
                and isinstance(node.slice, ast.Constant)
                and node.slice.value in {"__import__", "eval", "exec"}
            ):
                violations.append("forbidden dynamic execution lookup")
    return violations


def assert_refuse_only(source, *, budget_module=False, product_module=False):
    violations = capability_violations(
        source, budget_module=budget_module, product_module=product_module
    )
    assert not violations, f"forbidden capability: {violations}"


def test_product_tree_has_no_outbound_or_credential_capability():
    source_root = Path("src/consilient")
    budget_path = source_root / "budget.py"
    assert_refuse_only(budget_path.read_text(encoding="utf-8"), budget_module=True)
    for path in source_root.rglob("*.py"):
        assert_refuse_only(path.read_text(encoding="utf-8"), product_module=True)


@pytest.mark.parametrize(
    "source",
    (
        "import requests as remote\nremote.post('https://example.invalid')",
        "from subprocess import run as execute\nexecute(['provider'])",
        "import os as operating_system\nkey = operating_system.environ['API_KEY']",
        "def call(provider):\n    provider.complete()",
        "from pathlib import Path\nkey = Path('openrouter.key').read_text()",
        "def call(gateway):\n    getattr(gateway, 'get')('https://example.invalid')",
        "getattr(__builtins__, '__import__')('socket')",
    ),
)
def test_refuse_only_ast_guard_has_a_failing_negative_control(source):
    with pytest.raises(AssertionError, match="forbidden capability"):
        assert_refuse_only(source, budget_module=True)


@pytest.mark.parametrize(
    "source",
    (
        "from http import client\nclient.HTTPSConnection('example.invalid')",
        "def call(gateway):\n    gateway.send(b'data')",
        "eval('1 + 1')",
        "loader = __builtins__['__import__']\nloader('socket')",
        "import boto3",
    ),
)
def test_product_tree_ast_guard_has_a_failing_negative_control(source):
    with pytest.raises(AssertionError, match="forbidden capability"):
        assert_refuse_only(source, product_module=True)


@pytest.mark.parametrize(
    "source",
    (
        "import socket\nsocket.socket().bind(('127.0.0.1', 0))",
        "from socket import socket as bound\nbound().listen(1)",
        "import subprocess\nsubprocess.Popen(['python'])",
        "from urllib.request import urlopen\nurlopen('https://example.invalid')",
        "import ftplib\nftplib.FTP('example.invalid')",
        "import webbrowser\nwebbrowser.open('https://example.invalid')",
    ),
)
def test_containment_escape_capabilities_fail_the_product_ast_guard(source):
    """Six probes: the sealed-instrument escapes must not be product imports."""
    with pytest.raises(AssertionError, match="forbidden capability"):
        assert_refuse_only(source, product_module=True)


def test_promote_containment_probe_is_a_payload_string_not_a_product_import():
    source = Path("src/consilient/promote.py").read_text(encoding="utf-8")
    assert_refuse_only(source, product_module=True)
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "socket" not in imported
    assert "subprocess" not in imported
    assert "tempfile" not in imported
    from consilient.promote import CONTAINMENT_PROBE_SOURCE

    assert '__import__("socket")' in CONTAINMENT_PROBE_SOURCE
    assert "write_outside_scratch" in CONTAINMENT_PROBE_SOURCE
