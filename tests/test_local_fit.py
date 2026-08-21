"""V0-08 and V0-10: local model fit gate and download chokepoint."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from consilient.local_fit import (
    FRAMEWORK_FLOOR_BYTES,
    GRAPH_ALLOWANCE_BYTES,
    LOCAL_DOWNLOAD_CHOKEPOINT,
    AcquireResult,
    HardwareProfile,
    LocalModelRequest,
    acquire_local_model,
    fit,
    hardware_profile_from_mapping,
)

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_ROOT = ROOT / "src" / "consilient"
SCRIPTS_ROOT = ROOT / "scripts"

LOCAL_DOWNLOAD_FORBIDDEN_CALLS = frozenset(
    {
        "download_local_model",
        "fetch_model_bytes",
        "pull_model_weights",
    }
)


def qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def local_download_bypass_violations(source: str, *, path_label: str) -> list[str]:
    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []
            self.violations: list[str] = []

        def _outside_chokepoint(self) -> bool:
            return LOCAL_DOWNLOAD_CHOKEPOINT not in self.stack

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name in LOCAL_DOWNLOAD_FORBIDDEN_CALLS and self._outside_chokepoint():
                self.violations.append(
                    f"{path_label}: forbidden download helper {node.name}"
                )
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            name = qualified_name(node.func)
            leaf = name.rsplit(".", 1)[-1]
            if self._outside_chokepoint():
                if leaf in LOCAL_DOWNLOAD_FORBIDDEN_CALLS:
                    self.violations.append(
                        f"{path_label}: forbidden direct download call {name}"
                    )
                if leaf == "downloader":
                    self.violations.append(
                        f"{path_label}: downloader invoked outside chokepoint"
                    )
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(ast.parse(source))
    return visitor.violations


def assert_no_local_download_bypass(source: str, *, path_label: str) -> None:
    violations = local_download_bypass_violations(source, path_label=path_label)
    if violations:
        joined = "; ".join(violations)
        raise AssertionError(f"local download bypass: {joined}")


def _comfortable_request() -> LocalModelRequest:
    return LocalModelRequest(
        parameter_count=1_000_000_000,
        quant_scheme="Q4_K_M",
        context_tokens=4096,
        kv_precision="f16",
        num_layers=32,
        kv_heads=8,
        key_length=128,
        value_length=128,
        d_model=4096,
        vocab_size=32_000,
        batch_size=512,
        parallel_slots=1,
    )


def _comfortable_profile(vram_bytes: int = 32 * 1024**3) -> HardwareProfile:
    return HardwareProfile(
        total_vram_bytes=vram_bytes,
        system_ram_bytes=64 * 1024**3,
        free_disk_bytes=100 * 1024**3,
        backend="cuda",
        unified_memory=False,
        provenance="test",
        probed_at="2026-08-21T00:00:00+00:00",
    )


def test_v0_10_fake_downloader_zero_bytes_for_infeasible_and_unknown_profiles():
    request = _comfortable_request()
    infeasible_profile = _comfortable_profile(vram_bytes=1 * 1024**3)
    unknown_profile = HardwareProfile(
        total_vram_bytes=None,
        system_ram_bytes=None,
        free_disk_bytes=None,
        backend=None,
        unified_memory=None,
        provenance="test",
        probed_at="2026-08-21T00:00:00+00:00",
    )
    transferred: list[int] = []

    def downloader() -> int:
        transferred.append(1_048_576)
        return 1_048_576

    infeasible = acquire_local_model(
        request,
        infeasible_profile,
        downloader=downloader,
    )
    assert infeasible.refused is True
    assert infeasible.transferred_bytes == 0

    unknown = acquire_local_model(
        request,
        unknown_profile,
        downloader=downloader,
    )
    assert unknown.refused is True
    assert unknown.transferred_bytes == 0
    assert transferred == []

    comfortable = acquire_local_model(
        request,
        _comfortable_profile(),
        downloader=downloader,
    )
    assert isinstance(comfortable, AcquireResult)
    assert comfortable.refused is False
    assert comfortable.transferred_bytes == 1_048_576
    assert transferred == [1_048_576]


def test_v0_08_lint_bans_direct_download_bypassing_chokepoint():
    for path in PRODUCT_ROOT.rglob("*.py"):
        assert_no_local_download_bypass(
            path.read_text(encoding="utf-8"),
            path_label=str(path.relative_to(ROOT)),
        )
    for path in SCRIPTS_ROOT.rglob("*.py"):
        assert_no_local_download_bypass(
            path.read_text(encoding="utf-8"),
            path_label=str(path.relative_to(ROOT)),
        )


@pytest.mark.parametrize(
    "source",
    (
        "def download_local_model():\n    return 1",
        "def run():\n    downloader()\n    return 0",
    ),
)
def test_v0_08_local_download_lint_has_a_failing_negative_control(source: str):
    with pytest.raises(AssertionError, match="local download bypass"):
        assert_no_local_download_bypass(source, path_label="negative-control.py")


def test_fit_boundary_at_ninety_percent_vram_total():
    kv = 1 * 1 * 1 * (1 + 1) * 1 * 2.0
    graph = GRAPH_ALLOWANCE_BYTES
    overhead = int(kv + graph + FRAMEWORK_FLOOR_BYTES)
    limit = 900_000_000
    target_weight = limit - overhead
    bpw = 5.05
    parameter_count = None
    for candidate in range(int(target_weight * 8 / bpw) - 2, int(target_weight * 8 / bpw) + 3):
        if int(candidate * bpw / 8) + overhead == limit:
            parameter_count = candidate
            break
    assert parameter_count is not None
    request = LocalModelRequest(
        parameter_count=parameter_count,
        quant_scheme="Q4_K_M",
        context_tokens=1,
        kv_precision="f16",
        num_layers=1,
        kv_heads=1,
        key_length=1,
        value_length=1,
        d_model=1,
        vocab_size=1,
        batch_size=1,
        parallel_slots=1,
    )
    vram_total = limit // 9 * 10  # exact: 0.9 * 1_000_000_000 == 900_000_000
    profile = _comfortable_profile(vram_bytes=vram_total)
    result = fit(request, profile)
    assert result.required_bytes == limit
    assert result.limit_bytes == limit
    assert result.verdict in {"comfortable", "tight"}


def test_hardware_profile_from_mapping_preserves_unknowns():
    profile = hardware_profile_from_mapping({"provenance": "scripts/hardware_probe.py"})
    assert profile.total_vram_bytes is None
    assert profile.backend is None
