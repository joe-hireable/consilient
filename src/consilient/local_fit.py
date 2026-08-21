"""Local model hardware fit — pure policy only.

The decision lives here; detection lives in `scripts/hardware_probe.py`. They meet over a
JSON profile document. Anything unknown is fail-closed: no substitute defaults.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .events import SCHEMA_VERSION, EventPayload, append

FitVerdict = Literal["comfortable", "tight", "infeasible", "unknown"]
Backend = Literal["cuda", "rocm", "metal", "cpu", "unknown"]
KvPrecision = Literal["f16", "q8_0", "q4_0"]

# [cited] docs/10-research/local-model-fit-arithmetic.md §5 and §2
VRAM_SAFETY_FACTOR = 0.9
GRAPH_ALLOWANCE_BYTES = 3 * 1024**3
FRAMEWORK_FLOOR_BYTES = int(0.8 * 1024**3)
TIGHT_MARGIN_FRACTION = 0.05

# Planning bpw — nominal quant names are not bpw. [cited] local-model-fit-arithmetic.md §2
PLANNING_BPW: dict[str, float] = {
    "Q4_K_M": 5.05,
    "Q5_K_M": 5.95,
    "Q6_K": 6.6,
    "Q8_0": 8.5,
    "fp16": 16.0,
    "bf16": 16.0,
    "MXFP4": 4.25,
}

KV_BYTES_PER_ELEMENT: dict[KvPrecision, float] = {
    "f16": 2.0,
    "q8_0": 1.0,
    "q4_0": 0.5,
}

LOCAL_DOWNLOAD_CHOKEPOINT = "acquire_local_model"
LOCAL_REFUSED_KIND = "dispatch.refused"
LOCAL_DISPATCH_ACTOR = "consilient.dispatch"


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refusal_event(ts: str, data: dict[str, object]) -> EventPayload:
    payload = dict(data)
    payload.setdefault("supervised", True)
    return {
        "v": SCHEMA_VERSION,
        "ts": ts,
        "event": LOCAL_REFUSED_KIND,
        "actor": LOCAL_DISPATCH_ACTOR,
        "data": payload,
    }


def _record_local_refusal(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    reason: str,
    considered: list[str],
) -> EventPayload:
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        _refusal_event(
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "status": "refused",
                "reason": reason,
                "considered": considered,
            },
        ),
    )


@dataclass(frozen=True)
class HardwareProfile:
    total_vram_bytes: int | None
    system_ram_bytes: int | None
    free_disk_bytes: int | None
    backend: Backend | None
    unified_memory: bool | None
    provenance: str | None
    probed_at: str | None


@dataclass(frozen=True)
class LocalModelRequest:
    """The unit of fit is (model, context, KV precision), not the model alone."""

    parameter_count: int | None
    quant_scheme: str | None
    context_tokens: int | None
    kv_precision: KvPrecision | None
    num_layers: int | None
    kv_heads: int | None
    key_length: int | None
    value_length: int | None
    d_model: int | None
    vocab_size: int | None
    batch_size: int | None
    parallel_slots: int | None


@dataclass(frozen=True)
class FitResult:
    verdict: FitVerdict
    required_bytes: int | None
    limit_bytes: int | None
    reason: str


@dataclass(frozen=True)
class AcquireResult:
    transferred_bytes: int
    verdict: FitVerdict
    reason: str
    refused: bool


def hardware_profile_from_mapping(data: Mapping[str, object]) -> HardwareProfile:
    """Parse a probe JSON document into a profile. Missing keys become unknown."""

    def optional_int(key: str) -> int | None:
        value = data.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value

    def optional_backend(key: str) -> Backend | None:
        value = data.get(key)
        if value is None:
            return None
        if value not in {"cuda", "rocm", "metal", "cpu", "unknown"}:
            return None
        return value  # type: ignore[return-value]

    def optional_bool(key: str) -> bool | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, bool):
            return None
        return value

    def optional_str(key: str) -> str | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            return None
        return value

    return HardwareProfile(
        total_vram_bytes=optional_int("total_vram_bytes"),
        system_ram_bytes=optional_int("system_ram_bytes"),
        free_disk_bytes=optional_int("free_disk_bytes"),
        backend=optional_backend("backend"),
        unified_memory=optional_bool("unified_memory"),
        provenance=optional_str("provenance"),
        probed_at=optional_str("probed_at"),
    )


def profile_to_mapping(profile: HardwareProfile) -> dict[str, object]:
    return {
        "total_vram_bytes": profile.total_vram_bytes,
        "system_ram_bytes": profile.system_ram_bytes,
        "free_disk_bytes": profile.free_disk_bytes,
        "backend": profile.backend,
        "unified_memory": profile.unified_memory,
        "provenance": profile.provenance,
        "probed_at": profile.probed_at,
    }


def unknown_profile(*, provenance: str, probed_at: str | None = None) -> HardwareProfile:
    """All-unknown profile for a failed probe — the gate must refuse."""
    return HardwareProfile(
        total_vram_bytes=None,
        system_ram_bytes=None,
        free_disk_bytes=None,
        backend=None,
        unified_memory=None,
        provenance=provenance,
        probed_at=probed_at,
    )


def _weight_bytes(request: LocalModelRequest) -> int | None:
    if request.parameter_count is None or request.quant_scheme is None:
        return None
    bpw = PLANNING_BPW.get(request.quant_scheme)
    if bpw is None:
        return None
    return int(request.parameter_count * bpw / 8)


def _kv_bytes(request: LocalModelRequest) -> int | None:
    if (
        request.context_tokens is None
        or request.kv_precision is None
        or request.num_layers is None
        or request.kv_heads is None
        or request.key_length is None
        or request.value_length is None
        or request.parallel_slots is None
    ):
        return None
    element_bytes = KV_BYTES_PER_ELEMENT.get(request.kv_precision)
    if element_bytes is None:
        return None
    per_token = (
        request.num_layers
        * request.context_tokens
        * (request.key_length + request.value_length)
        * request.kv_heads
        * element_bytes
    )
    return int(request.parallel_slots * per_token)


def _graph_bytes(request: LocalModelRequest) -> int | None:
    if (
        request.batch_size is None
        or request.d_model is None
        or request.vocab_size is None
    ):
        return None
    logits = 4 * request.batch_size * (request.d_model + request.vocab_size)
    return max(logits, GRAPH_ALLOWANCE_BYTES)


def _memory_limit_bytes(profile: HardwareProfile) -> int | None:
    if profile.unified_memory is True:
        return None
    if profile.unified_memory is None and profile.backend in {None, "unknown"}:
        return None
    if profile.backend == "cpu":
        return profile.system_ram_bytes
    return profile.total_vram_bytes


def fit(request: LocalModelRequest, profile: HardwareProfile) -> FitResult:
    """Return a fit verdict. Unknown inputs or topology yield `unknown`, never a guess."""
    if profile.unified_memory is not False:
        reason = (
            "unified memory topology is not modelled"
            if profile.unified_memory is True
            else "unified-vs-discrete memory is unknown"
        )
        return FitResult(
            verdict="unknown",
            required_bytes=None,
            limit_bytes=None,
            reason=reason,
        )

    if profile.backend is None:
        return FitResult(
            verdict="unknown",
            required_bytes=None,
            limit_bytes=None,
            reason="hardware profile missing: backend",
        )

    if profile.backend == "cpu":
        if profile.system_ram_bytes is None:
            return FitResult(
                verdict="unknown",
                required_bytes=None,
                limit_bytes=None,
                reason="hardware profile missing: system_ram_bytes",
            )
    elif profile.total_vram_bytes is None:
        return FitResult(
            verdict="unknown",
            required_bytes=None,
            limit_bytes=None,
            reason="hardware profile missing: total_vram_bytes",
        )

    weight = _weight_bytes(request)
    kv = _kv_bytes(request)
    graph = _graph_bytes(request)
    if weight is None or kv is None or graph is None:
        return FitResult(
            verdict="unknown",
            required_bytes=None,
            limit_bytes=None,
            reason="model request missing terms for W, KV or G",
        )

    required = weight + kv + graph + FRAMEWORK_FLOOR_BYTES
    limit_source = _memory_limit_bytes(profile)
    if limit_source is None:
        return FitResult(
            verdict="unknown",
            required_bytes=required,
            limit_bytes=None,
            reason="no readable memory limit for this backend",
        )

    limit = int(VRAM_SAFETY_FACTOR * limit_source)
    if required > limit:
        return FitResult(
            verdict="infeasible",
            required_bytes=required,
            limit_bytes=limit,
            reason=(
                f"required {required} bytes exceeds {VRAM_SAFETY_FACTOR:g} * "
                f"{limit_source} = {limit} bytes"
            ),
        )

    spare = limit - required
    if spare == 0 or spare / limit <= TIGHT_MARGIN_FRACTION:
        verdict: FitVerdict = "tight"
        reason = f"required {required} bytes within {spare} bytes of limit {limit}"
    else:
        verdict = "comfortable"
        reason = f"required {required} bytes with {spare} bytes spare below limit {limit}"

    return FitResult(
        verdict=verdict,
        required_bytes=required,
        limit_bytes=limit,
        reason=reason,
    )


def acquire_local_model(
    request: LocalModelRequest,
    profile: HardwareProfile,
    *,
    downloader: Callable[[], int],
    log_dir: Path | None = None,
    run_id: str = "",
    task: str = "",
    cwd: str = "",
    ts: str | None = None,
) -> AcquireResult:
    """Single chokepoint for harness-initiated model bytes. Refusal is the success path."""
    verdict = fit(request, profile)
    if verdict.verdict in {"infeasible", "unknown"}:
        reason = f"local model acquisition refused: {verdict.reason}"
        if log_dir is not None:
            _record_local_refusal(
                log_dir,
                ts=ts or _now_ts(),
                run_id=run_id,
                task=task,
                cwd=cwd,
                reason=reason,
                considered=[
                    f"verdict={verdict.verdict}",
                    f"required_bytes={verdict.required_bytes}",
                    f"limit_bytes={verdict.limit_bytes}",
                ],
            )
        return AcquireResult(
            transferred_bytes=0,
            verdict=verdict.verdict,
            reason=reason,
            refused=True,
        )

    transferred = downloader()
    return AcquireResult(
        transferred_bytes=transferred,
        verdict=verdict.verdict,
        reason=verdict.reason,
        refused=False,
    )
