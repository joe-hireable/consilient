"""β — the rate at which the automated verifier accepts an artefact the human rejected.

V0-06: routing consumes the composite-verifier β with its sample count and interval.
Per-check outcomes are diagnostics only, because their dependence is unknown (ADR-0012).

β is conditional on an oracle that is itself a test. The human verdict is error-prone,
is not independent of the automated checks, and may not be stationary (Q30). β measures
the pair, not the checks alone, and no caller may present it otherwise.

`lower_bound_on_joint_error` was a hard-coded `True` until 20 August 2026, with a test
asserting it was `True`. That test enforced the *claim*, not the property — the same
"assert the mechanism, not the property" failure this repository has now found in four
separate checks.

The bound only follows if the sample is **not conditioned on the verifier's own
outcome**. If artefacts reach a human only when the checks already accepted them, every
rejected row has `verifier_accept=True` and β is 1 by construction rather than by
measurement. The arithmetic in `compute` is correct; the exposure is entirely in which
rows exist.

Nothing recorded or checked that property, and there is no collection protocol at all —
the meter has received zero rows. So the honest default is that **no bound is claimed**.
A caller who has a sampling protocol that does not condition on the verifier may declare
it, and only then does the bound hold. Found by a cross-family prior-art audit reading
this file against its own defect record."""

from __future__ import annotations
import sqlite3
from collections.abc import Iterable
from dataclasses import replace
from .beta_admission import (
    Beta,
    INSUFFICIENT,
    MIN_COMPOSITE_REJECTION_FRACTION,
    MIN_REJECTIONS,
    admits_human_beta_row,
    composite_verifier_rejection_fraction,
    compute,
    upstream_rows_for_compute,
)

from .beta_admission import (
    AUTHENTICATED_AUTH_STATUS,
    HUMAN_VERDICT_BETA,
    HumanDecision,
    MEASURED,
    PROXY_ESTIMAND_KINDS,
    RejectionKind,
    THIRD_PARTY_MAINTAINER_AUTH_STATUS,
    UPSTREAM_MAINTAINER_ESTIMAND_KIND,
    UPSTREAM_MAINTAINER_PROXY_BETA,
    UpstreamCiOutcome,
    Verdict,
    admits_sizing_input,
    admits_upstream_maintainer_proxy_row,
    both_upstream_cells_representable,
    counts_toward_upstream_beta_numerator,
    refuse_upstream_row,
    upstream_human_verdict_for_beta,
    verifier_verdict_did_not_gate_submission,
    wilson,
)

__all__ = [
    "AUTHENTICATED_AUTH_STATUS",
    "Beta",
    "HUMAN_VERDICT_BETA",
    "HumanDecision",
    "INSUFFICIENT",
    "MEASURED",
    "MIN_COMPOSITE_REJECTION_FRACTION",
    "MIN_REJECTIONS",
    "PROXY_ESTIMAND_KINDS",
    "RejectionKind",
    "THIRD_PARTY_MAINTAINER_AUTH_STATUS",
    "UPSTREAM_MAINTAINER_ESTIMAND_KIND",
    "UPSTREAM_MAINTAINER_PROXY_BETA",
    "UpstreamCiOutcome",
    "Verdict",
    "admits_human_beta_row",
    "admits_sizing_input",
    "admits_upstream_maintainer_proxy_row",
    "both_upstream_cells_representable",
    "composite_verifier_rejection_fraction",
    "compute",
    "compute_upstream_maintainer_beta",
    "counts_toward_upstream_beta_numerator",
    "from_connection",
    "refuse_upstream_row",
    "upstream_human_verdict_for_beta",
    "upstream_rows_for_compute",
    "verifier_verdict_did_not_gate_submission",
    "wilson",
]


def compute_upstream_maintainer_beta(
    rows: Iterable[dict[str, object]],
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
    min_composite_rejection_fraction: float = MIN_COMPOSITE_REJECTION_FRACTION,
) -> Beta:
    """β among upstream contributions that passed the declared admission bar (EXP-144)."""
    if not MIN_COMPOSITE_REJECTION_FRACTION <= min_composite_rejection_fraction <= 1:
        raise ValueError(
            "min_composite_rejection_fraction may only raise the floor from "
            f"{MIN_COMPOSITE_REJECTION_FRACTION} and cannot exceed 1"
        )
    material = list(rows)
    projected = upstream_rows_for_compute(material)
    result = compute(
        projected,
        task_family,
        verifier_version,
        min_rejections,
        sampling_unconditioned=True,
    )
    fraction = composite_verifier_rejection_fraction(
        material,
        task_family,
        verifier_version,
    )
    if fraction is None or fraction < min_composite_rejection_fraction:
        caveat = (
            "beta is conditional on a human verdict that is itself fallible, "
            "not independent of the checks, and possibly non-stationary (Q30); "
            "composite rejection fraction below the EXP-144 floor — protocol failed"
        )
        return replace(
            result,
            verdict=INSUFFICIENT,
            point=None,
            interval=None,
            lower_bound_on_joint_error=False,
            caveat=caveat,
            composite_rejection_fraction=fraction,
        )

    return replace(
        result,
        composite_rejection_fraction=fraction,
        caveat=(
            f"{result.caveat}; upstream maintainer estimand conditional on admission bar "
            f"(EXP-144); composite rejection fraction {fraction:.3f}"
        ),
    )


def from_connection(
    conn: sqlite3.Connection,
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
    sampling_unconditioned: bool | None = None,
) -> Beta:
    from . import projection as projection_mod

    derived = projection_mod.sampling_unconditioned(conn)
    if projection_mod.review_queue_row(conn) is not None:
        sampling = derived
    elif sampling_unconditioned is None:
        sampling = derived
    else:
        sampling = sampling_unconditioned
    rows = [
        {
            "ts": ts,
            "task_family": fam,
            "verifier_version": ver,
            "verifier_accept": bool(acc),
            "human_verdict": verdict,
            "estimand_kind": estimand,
            "auth_status": auth,
        }
        for ts, fam, ver, acc, verdict, estimand, auth in conn.execute(
            "SELECT ts, task_family, verifier_version, verifier_accept, human_verdict,"
            " estimand_kind, auth_status FROM outcomes ORDER BY position"
        )
    ]
    declared_principal_verdict_count = sum(
        1
        for row in rows
        if row["auth_status"] == "declared_principal"
        and (task_family is None or row["task_family"] == task_family)
        and (verifier_version is None or row["verifier_version"] == verifier_version)
    )
    result = compute(
        [row for row in rows if admits_human_beta_row(row)],
        task_family,
        verifier_version,
        min_rejections,
        sampling,
    )
    if not declared_principal_verdict_count:
        return result
    return replace(
        result,
        caveat=(
            f"{result.caveat}; declared-principal verdicts recorded and excluded from "
            f"beta: {declared_principal_verdict_count} (not machine-authenticated)"
        ),
        declared_principal_verdict_count=declared_principal_verdict_count,
    )
