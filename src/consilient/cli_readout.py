"""The register's own measurements, and the human rendering of every command's result.

V0-14: every command has one JSON contract, and human output is a rendering of the same
result rather than a second semantics.

`render` is that rendering and nothing else. It performs no arithmetic and reads no
file: given a result it prints what the result already says, which is what makes it
impossible -- not merely unlikely -- for the text a person reads and the JSON a caller
parses to disagree. `_experiment_conditions` decides gate conditions A1, B1 and B2 from
the experiment register alone: EXP-01's beta interval and whether its half-width clears
the plus or minus 0.05 tolerance, EXP-05's adapter-two outcome, and the
`critic-beta-measured` figure ADR-0045 requires of EXP-08. A status recorded as DONE is
not sufficient on its own. An entry with no machine-readable interval fails, a stopping
rule that fired fails, and a point estimate lying outside its own interval fails.

The two belong together because both turn something already recorded into the sentence a
reader is handed, and neither may add anything to it. A condition invented during
rendering, or a figure computed on the way to the screen, would be a second source of
truth for a number that already has one.
"""

from __future__ import annotations
from decimal import Decimal
from . import beta as beta_mod
from .cli_replay import (
    CRITIC_BETA,
    CommandResult,
    EXP01_BETA,
    EXPERIMENT_REGISTER,
    GATE_B2_ADR,
)

from .cli_measurements import (
    _condition,
    _experiment_entry,
    _trajectory_line,
)


__all__ = [
    "CRITIC_BETA",
    "CommandResult",
    "EXP01_BETA",
    "EXPERIMENT_REGISTER",
    "GATE_B2_ADR",
    "_condition",
    "_experiment_entry",
    "_trajectory_line",
    "render",
]


def _experiment_conditions() -> tuple[CommandResult, CommandResult, CommandResult]:
    register = EXPERIMENT_REGISTER.as_posix()
    a1_status, a1_entry = _experiment_entry("EXP-01")
    a1_evidence = (register,)
    a1_measurement = EXP01_BETA.search(a1_entry)
    stopping_rule_fired = "stopping rule FIRED" in a1_entry or (
        a1_status is not None and "stopping rule FIRED" in a1_status
    )
    if a1_status is None:
        a1 = _condition("A1", "unknown", "No EXP-01 result is recorded.")
    elif not a1_status.startswith("DONE"):
        a1 = _condition(
            "A1",
            "fail",
            f"EXP-01 is recorded as {a1_status}; must be DONE with a usable beta interval.",
            *a1_evidence,
        )
    elif stopping_rule_fired:
        a1 = _condition(
            "A1",
            "fail",
            "EXP-01 stopping rule fired: history mining could not narrow the interval below "
            "\u00b10.05 and the method was retired without a usable beta measurement.",
            *a1_evidence,
        )
    elif a1_measurement is None:
        a1 = _condition(
            "A1",
            "fail",
            f"EXP-01 is {a1_status}; its entry records no `beta-measured: p [lo, hi]` "
            "measurement with interval half-width <= 0.05, which Gate A requires.",
            *a1_evidence,
        )
    else:
        point, low, high = (float(value) for value in a1_measurement.groups())
        half_width = (high - low) / 2
        if not (0 <= low <= point <= high <= 1):
            a1 = _condition(
                "A1",
                "fail",
                f"Recorded beta {point} lies outside its own interval [{low}, {high}].",
                *a1_evidence,
            )
        elif half_width > 0.05:
            a1 = _condition(
                "A1",
                "fail",
                f"Recorded beta interval [{low}, {high}] half-width {half_width:.4f} exceeds "
                "\u00b10.05 tolerance; does not decide the threshold.",
                *a1_evidence,
            )
        else:
            a1 = _condition(
                "A1",
                "pass",
                f"EXP-01 is DONE; beta is measured at {point} [{low}, {high}] with half-width "
                f"{half_width:.4f} <= 0.05.",
                *a1_evidence,
            )

    b1_status, b1_entry = _experiment_entry("EXP-05")
    b1_result = b1_entry.partition("**Result:**")[2].partition("\n\n")[0]
    no_redesign = "Adapter #2 (Codex) did not force an interface redesign" in " ".join(
        b1_result.split()
    )
    if b1_status is None:
        b1 = _condition("B1", "unknown", "No EXP-05 result is recorded.")
    elif b1_status.startswith("DONE") and no_redesign:
        b1 = _condition(
            "B1", "pass", "EXP-05 is DONE; adapter two forced no redesign.", register
        )
    elif b1_status.startswith("DONE"):
        b1 = _condition(
            "B1", "unknown", "Adapter-two outcome is not recorded.", register
        )
    else:
        b1 = _condition("B1", "fail", f"EXP-05 is recorded as {b1_status}.", register)

    b2_status, b2_entry = _experiment_entry("EXP-08")
    b2_evidence = (register, GATE_B2_ADR.as_posix())
    measurement = CRITIC_BETA.search(b2_entry)
    if b2_status is None:
        b2 = _condition("B2", "unknown", "No EXP-08 result is recorded.")
    elif not b2_status.startswith("DONE"):
        b2 = _condition(
            "B2",
            "fail",
            f"EXP-08 is {b2_status}; must be DONE and carry a `critic-beta-measured: p [lo, hi]` "
            "measurement (ADR-0045).",
            *b2_evidence,
        )
    elif measurement is None:
        b2 = _condition(
            "B2",
            "fail",
            f"EXP-08 is {b2_status}; its entry records no `critic-beta-measured: p [lo, hi]` "
            "measurement, which ADR-0045 requires.",
            *b2_evidence,
        )
    else:
        point, low, high = (float(value) for value in measurement.groups())
        b2 = _condition(
            "B2",
            "pass" if low <= point <= high else "fail",
            f"Critic beta is measured at {point} [{low}, {high}]."
            if low <= point <= high
            else f"Recorded critic beta {point} lies outside its own interval [{low}, {high}].",
            *b2_evidence,
        )
    return a1, b1, b2


def render(command: str, result: CommandResult) -> str:
    if command == "record":
        return f"recorded {result['event']} -> {result['file']}"
    if command == "replay":
        if result.get("version_changed"):
            mark = (
                f"REBUILT — projection version {result.get('prior_version')!r} → "
                f"{result.get('projection_version')!r}"
            )
        elif result["stale"]:
            mark = (
                f"STALE — state covers {result['events_projected']} of {result['events']} "
                "events; rebuilt"
            )
        elif not result["compared"]:
            mark = "NOT COMPARED — no prior state on disk"
        else:
            mark = "identical" if result["identical"] else "DIVERGED"
        line = f"replayed {result['events']} events; state {mark} ({result['digest'][:12]})"
        if result["quarantined"]:
            line += (
                f"\n  QUARANTINED {len(result['quarantined'])} line(s) the log refuses:"
            )
            for r in result["quarantined"]:
                line += f"\n    {r['path']}:{r['line']}  {r['reason']}"
        if result["not_written_by_append"]:
            total = result["events"] + len(result["quarantined"])
            line += (
                f"\n  {result['not_written_by_append']} of {total} logged lines were not "
                "written by append(), so validate() never ran on them"
            )
        traj = _trajectory_line(result)
        if traj:
            line += f"\n  {traj}"
        return line
    if command == "usage":
        lines = []
        for provider in result["providers"]:
            head = f"{provider['provider']:<12} {provider['status'].replace('_', ' ')}"
            if provider["status"] != "ok":
                lines.append(f"{head} — {provider['detail']}")
                continue
            lines.append(head)
            for quota in provider["quotas"]:
                percent = Decimal(quota["used_fraction"]) * 100
                reset = quota["resets_at"] or "no reset time reported"
                lines.append(
                    f"    quota {quota['window']:<8} {percent:>6.1f}% used, "
                    f"resets {reset}  [{quota['provenance']}]"
                )
            for item in provider["spend"]:
                lines.append(
                    f"    spend {item['period']:<8} {item['amount']} {item['currency']}"
                    f"  [{item['provenance']}]"
                )
        ceilings = result["ceilings"]
        if not ceilings["configured"]:
            lines.append(
                f"ceilings: NONE — {ceilings['refusal']}; every metered call refuses"
            )
        else:
            stated = ", ".join(
                f"{c['period']} {c['amount']} {c['currency']}"
                for c in ceilings["limits"]
            )
            lines.append(f"ceilings: {stated}")
        if result["recorded"]:
            lines.append(
                f"recorded {result['recorded']} observation(s) to the trajectory"
            )
        traj = _trajectory_line(result)
        if traj:
            lines.append(traj)
        return "\n".join(lines)
    if command == "beta":
        line = beta_mod.Beta(
            verdict=result["verdict"],
            task_family=result["task_family"],
            verifier_version=result["verifier_version"],
            n_rejected=result["n_rejected"],
            n_false_accept=result["n_false_accept"],
            point=result["point"],
            interval=tuple(result["interval"]) if result["interval"] else None,
            window=tuple(result["window"]) if result["window"] else None,
            lower_bound_on_joint_error=result.get("lower_bound_on_joint_error", False),
            caveat=result.get("caveat", ""),
        ).render()
        extras: list[str] = []
        parser_q = result.get("quarantined", 0)
        relational_q = result.get("relational_quarantine_count", 0)
        if parser_q:
            extras.append(f"parser quarantine: {parser_q} line(s)")
            for row in result.get("rejection_reasons", []):
                extras.append(f"  {row['path']}:{row['line']}  {row['reason']}")
        if relational_q:
            extras.append(f"relational quarantine: {relational_q} row(s)")
            for row in result.get("relational_quarantine", []):
                extras.append(f"  {row['path']}:{row['line']}  {row['reason']}")
        sampling = result.get("sampling_unconditioned", False)
        extras.append(
            "sampling_unconditioned: "
            + (
                "true (projection-derived)"
                if sampling
                else "false (projection-derived)"
            )
        )
        extras.append(f"oracle caveat: {result.get('caveat', '')}")
        traj = _trajectory_line(result)
        if traj:
            extras.append(traj)
        return "\n".join([line] + extras)
    if command == "dashboard":
        traj = result["trajectory"]
        unanswerable = sum(1 for g in result["schema_gaps"] if not g["answerable"])
        gaps = result["capability_gaps"]
        enabled = "yes" if result["routing_orchestration_enabled"] else "no"
        lines = [
            f"wrote {result['written']}",
            f"  {traj['events']} events, {traj['distinct_agents']} agents, "
            f"{traj['distinct_artefacts']} files written",
            f"  routing/orchestration enabled: {enabled}",
            f"  {result['beta_line']}",
            f"  RACI derivable: {'yes' if result['raci']['derivable'] else 'no'}; "
            f"{unanswerable} question(s) the record cannot answer",
            f"  capability gaps: {gaps['total']} recorded, {gaps['distinct']} distinct",
        ]
        source = _trajectory_line(result)
        if source:
            lines.insert(1, f"  {source}")
        return "\n".join(lines)
    if command == "doctor":
        provenance = result["provenance"]
        lines = [
            f"code: {provenance['code']}",
            f"data: {provenance['data']}  log: {provenance['log']}",
        ]
        traj = _trajectory_line(result)
        if traj:
            lines.append(traj)
        for name, gate in result["gates"].items():
            lines.append(f"Gate {name}: {gate['status'].replace('_', '-').upper()}")
            for condition in gate["conditions"]:
                mark = condition["status"].replace("_", "-").upper()
                lines.append(f"  {condition['id']} {mark}: {condition['requirement']}")
                lines.append(f"    {condition['reason']}")
                evidence = ", ".join(condition["evidence"]) or "none"
                lines.append(f"    evidence: {evidence}")
        enabled = "yes" if result["routing_orchestration_enabled"] else "no"
        lines.append(f"routing/orchestration enabled: {enabled}")
        return "\n".join(lines)
    raise ValueError(command)
