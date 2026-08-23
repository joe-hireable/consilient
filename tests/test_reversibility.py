"""Fail-closed reversibility classes for registered capabilities.

B3 / B03: shell that can reach the network or a credential is class 4; an
unknown tool is class 4. This is a declared classifier, not EXP-35's measured
misclassification rate.
"""

from __future__ import annotations

import pytest

from consilient.capabilities import (
    REGISTERED_TOOLS,
    classify_reversibility,
)


def test_unknown_tool_is_class_4() -> None:
    assert classify_reversibility("tool", "not-a-registered-tool") == 4


def test_unregistered_kind_name_pair_is_class_4() -> None:
    assert classify_reversibility("skill", "read") == 4


def test_case_variant_of_a_registered_name_is_class_4() -> None:
    assert classify_reversibility("tool", "Bash") == 4


def test_padded_or_empty_name_is_class_4() -> None:
    assert classify_reversibility("tool", "") == 4
    assert classify_reversibility("tool", " bash") == 4


def test_file_tools_are_class_1() -> None:
    assert classify_reversibility("tool", "read") == 1
    assert classify_reversibility("mcp", "filesystem") == 1


def test_file_tool_declaring_network_is_class_4() -> None:
    assert (
        classify_reversibility("tool", "read", effect_classes=("network.call",))
        == 4
    )


def test_file_tool_declaring_process_run_is_class_4() -> None:
    assert classify_reversibility("tool", "read", effect_classes=("process.run",)) == 4


def test_shell_without_proven_default_deny_is_class_4() -> None:
    assert classify_reversibility("tool", "bash") == 4
    assert classify_reversibility("tool", "shell") == 4


def test_sandboxed_shell_with_proven_default_deny_is_class_2() -> None:
    assert (
        classify_reversibility(
            "tool",
            "bash",
            default_deny_egress_proven=True,
        )
        == 2
    )


def test_sandboxed_shell_with_credential_reach_is_class_4() -> None:
    assert (
        classify_reversibility(
            "tool",
            "bash",
            default_deny_egress_proven=True,
            credential_reach=True,
        )
        == 4
    )


def test_sandboxed_shell_declaring_network_is_class_4() -> None:
    assert (
        classify_reversibility(
            "tool",
            "bash",
            effect_classes=("process.run", "network.call"),
            default_deny_egress_proven=True,
        )
        == 4
    )


def test_subagent_tool_is_class_3() -> None:
    assert classify_reversibility("tool", "task") == 3


def test_external_tools_are_class_4() -> None:
    assert classify_reversibility("tool", "webfetch") == 4
    assert classify_reversibility("connection", "github") == 4


def _default_class(family: str) -> int:
    if family == "file":
        return 1
    if family == "subagent":
        return 3
    return 4


@pytest.mark.parametrize(
    ("kind", "name", "family"),
    [(kind, name, family) for (kind, name), family in sorted(REGISTERED_TOOLS.items())],
)
def test_every_registered_tool_classifies_under_default_facts(
    kind: str, name: str, family: str
) -> None:
    assert classify_reversibility(kind, name) == _default_class(family)
