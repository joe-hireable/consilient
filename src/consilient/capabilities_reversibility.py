"""The rewind-class table, and the classifier that reads it.

classify_reversibility is a labelling function and nothing more — it returns a class,
never a handle, which is half of the claim tests/test_tool_surface_live_handle.py holds;
the other half is that no file in this family imports a live one. An unregistered kind
and name pair, an effect class outside the contained set, and a shell without proven
default-deny egress are all class 4.

The two comment blocks carried in with these symbols hold the cited derivation of the
four classes and the reason the contained-effect set is named inwards rather than as a
denylist. They are the measured prose of this file and they stay attached to the
constants they describe."""

from typing import Literal

# Rewind classes from Claude Code's documented limits: 1 tool-mediated and
# snapshotted; 2 shell; 3 subagent-delegated; 4 external. Shell that can reach
# the network or a credential is class 4; only proven default-deny egress
# downgrades to 2. Unknown tools, and unknown effect classes, are class 4.
ReversibilityClass = Literal[1, 2, 3, 4]

ToolFamily = Literal["file", "shell", "subagent", "external"]

REGISTERED_TOOLS: dict[tuple[str, str], ToolFamily] = {
    ("tool", "read"): "file",
    ("tool", "write"): "file",
    ("tool", "edit"): "file",
    ("tool", "glob"): "file",
    ("tool", "grep"): "file",
    ("tool", "bash"): "shell",
    ("tool", "shell"): "shell",
    ("tool", "task"): "subagent",
    ("tool", "webfetch"): "external",
    ("tool", "websearch"): "external",
    ("mcp", "filesystem"): "file",
    ("connection", "github"): "external",
}

# The three effect classes whose reach stays inside the admitted root, so the
# tool family decides the class. Named as the contained set rather than as an
# outward denylist, so that an effect class this module has never heard of — a
# new one in effects.EFFECT_CLASSES, a misspelt one, or embodiment's own
# `physical.actuate` — is class 4 by default. A denylist fails open on exactly
# the effects that matter most. `process.run` is contained but not reversible:
# terminating a process is containment, not undo, which is why the file family
# rejects it and only a proven-sandboxed shell carries it at class 2.
# Source: docs/superpowers/specs/2026-08-22-action-surface.md, class-level
# reversibility table and its least-recoverable-atom rule. [cited]
LOCALLY_CONTAINED_EFFECTS = frozenset({"data.read", "file.change", "process.run"})


def classify_reversibility(
    kind: str,
    name: str,
    *,
    effect_classes: tuple[str, ...] = (),
    default_deny_egress_proven: bool = False,
    credential_reach: bool = False,
) -> ReversibilityClass:
    """Return rewind class 1-4; an unknown tool, an unknown effect class or an
    egress-capable shell is 4."""

    family = REGISTERED_TOOLS.get((kind, name))
    if family is None:
        return 4
    declared = frozenset(effect_classes)
    if declared - LOCALLY_CONTAINED_EFFECTS:
        return 4
    if family == "shell":
        if credential_reach or not default_deny_egress_proven:
            return 4
        return 2
    if family == "subagent":
        return 3
    if family == "file":
        if "process.run" in declared:
            return 4
        return 1
    return 4
