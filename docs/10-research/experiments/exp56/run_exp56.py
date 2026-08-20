"""EXP-56 preflight: prove the registered corpus and model surface are usable.

The scored runner deliberately does not exist unless this gate passes. Reconstructing
discarded EXP-47 labels after seeing its aggregates would amend the pre-registration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


MODEL_IDS = (
    "claude-sonnet-5-low",
    "claude-opus-5-thinking-high",
    "claude-fable-5-thinking-max",
    "claude-opus-4-8-medium",
    "gpt-5.6-sol-none",
    "gpt-5.6-terra-medium",
    "gpt-5.6-luna-high",
    "gpt-5.4-mini-xhigh",
    "gemini-3.7-flash-low",
    "gemini-3.6-flash-high",
    "gemini-3.1-pro",
    "cursor-grok-4.6-low",
    "cursor-grok-4.5-high",
    "kimi-k3-max",
    "kimi-k2.7-code",
    "glm-5.2-high",
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXP47_RESULTS = HERE.parent / "exp47" / "results-exp47.json"
RESULTS = HERE / "results-exp56.json"
IDENTITY_PROBE = HERE / "identity-probe-exp56.json"
REGISTRATION_COMMIT = "f65d96d895396f8815bf521ee5cc5b6c048dedd1"
REGISTERED_TOTAL = 1931
REGISTERED_KILLED = 1285
REGISTERED_EQUIVALENT = 60
REGISTERED_NON_EQUIVALENT_SURVIVORS = 586


def verify_source_snapshot(source_commit: str, manifest: dict[str, str]) -> bool:
    commit = subprocess.run(
        ["git", "cat-file", "-e", f"{source_commit}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if commit.returncode:
        return False
    for path, expected_hash in manifest.items():
        blob = subprocess.run(
            ["git", "show", f"{source_commit}:{path}"],
            cwd=ROOT,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if (
            blob.returncode
            or hashlib.sha256(blob.stdout).hexdigest() != expected_hash.lower()
        ):
            return False
    return True


def audit_inputs(
    exp47: dict,
    cursor_version: str,
    model_listing: str,
    call_records: list[dict] | None = None,
) -> dict:
    rows = exp47.get("mutants")
    rows = rows if isinstance(rows, list) else []
    raw_counts = exp47.get("raw_counts")
    raw_counts = raw_counts if isinstance(raw_counts, dict) else {}
    reported_total = exp47.get("sample_size")
    reported_total = (
        reported_total
        if isinstance(reported_total, int) and not isinstance(reported_total, bool)
        else 0
    )
    reported_survivors = raw_counts.get("composite_survived")
    reported_survivors = (
        reported_survivors
        if isinstance(reported_survivors, int)
        and not isinstance(reported_survivors, bool)
        else 0
    )
    reported_equivalent = raw_counts.get("equivalent_mutants")
    reported_equivalent = (
        reported_equivalent
        if isinstance(reported_equivalent, int)
        and not isinstance(reported_equivalent, bool)
        else 0
    )
    killed_rows = sum(
        isinstance(row, dict)
        and row.get("outcome") == "killed"
        and row.get("classification") == "non_equivalent"
        for row in rows
    )
    equivalent_rows = sum(
        isinstance(row, dict)
        and row.get("outcome") == "survived"
        and row.get("classification") == "equivalent"
        for row in rows
    )
    non_equivalent_survivor_rows = sum(
        isinstance(row, dict)
        and row.get("outcome") == "survived"
        and row.get("classification") == "non_equivalent"
        for row in rows
    )
    weakest = exp47.get("weakest_guards")
    survivor_rows = len(weakest) if isinstance(weakest, list) else 0
    manifest = exp47.get("input_sha256")
    source_commit = exp47.get("source_commit")
    source_declared = bool(
        isinstance(source_commit, str)
        and len(source_commit) == 40
        and all(character in "0123456789abcdef" for character in source_commit.lower())
        and isinstance(manifest, dict)
        and manifest
        and all(isinstance(path, str) for path in manifest)
        and any(path.startswith("src/") for path in manifest)
        and any(path.startswith("tests/") for path in manifest)
        and all(
            isinstance(digest, str)
            and len(digest) == 64
            and all(character in "0123456789abcdef" for character in digest.lower())
            for digest in manifest.values()
        )
    )
    source_verified = bool(
        source_declared and verify_source_snapshot(source_commit, manifest)
    )
    prompt_inputs_present_rows = sum(
        isinstance(row, dict)
        and isinstance(row.get("source_region"), str)
        and bool(row["source_region"].strip())
        and isinstance(row.get("covering_tests"), list)
        and bool(row["covering_tests"])
        and all(
            isinstance(test, str) and bool(test.strip())
            for test in row["covering_tests"]
        )
        for row in rows
    )

    missing = []
    aggregates_ready = (
        reported_total == REGISTERED_TOTAL
        and raw_counts.get("total_mutants") == REGISTERED_TOTAL
        and reported_survivors
        == REGISTERED_EQUIVALENT + REGISTERED_NON_EQUIVALENT_SURVIVORS
        and reported_equivalent == REGISTERED_EQUIVALENT
        and raw_counts.get("true_defects_survived")
        == REGISTERED_NON_EQUIVALENT_SURVIVORS
    )
    if not aggregates_ready:
        missing.append("registered EXP-47 aggregate partition")
    if killed_rows != REGISTERED_KILLED:
        missing.append("item-level killed outcomes")
    if equivalent_rows != REGISTERED_EQUIVALENT:
        missing.append("item-level equivalent identities")
    if (
        len(rows) == REGISTERED_TOTAL
        and non_equivalent_survivor_rows
        != REGISTERED_NON_EQUIVALENT_SURVIVORS
    ):
        missing.append("item-level non-equivalent survivor outcomes")
    if len(rows) != REGISTERED_TOTAL:
        missing.append("complete item-level EXP-47 corpus")
    if not source_verified:
        missing.append("source snapshot identity")
    if rows:
        identities = [
            row.get("id") if isinstance(row, dict) else None for row in rows
        ]
        if (
            not all(
                isinstance(identity, (int, str))
                and not isinstance(identity, bool)
                and (not isinstance(identity, str) or bool(identity.strip()))
                for identity in identities
            )
            or len(set(identities)) != len(identities)
        ):
            missing.append("unique item identities")
        if prompt_inputs_present_rows != len(rows):
            missing.append("mutated source regions and covering tests")
        survivor_identities = {
            row["id"]
            for row in rows
            if isinstance(row, dict)
            and "id" in row
            and row.get("outcome") == "survived"
            and row.get("classification") == "non_equivalent"
        }
        weakest_identities = {
            row.get("id")
            for row in weakest
            if isinstance(row, dict)
            and isinstance(row.get("id"), (int, str))
            and not isinstance(row.get("id"), bool)
        } if isinstance(weakest, list) else set()
        if weakest_identities != survivor_identities:
            missing.append("EXP-47 survivor identity mapping")
    corpus_shape_ready = len(rows) == REGISTERED_TOTAL and not missing
    # ponytail: shape and blob checks cannot prove row derivation; add a
    # re-registered mutation receipt and verifier before allowing scoring.
    item_provenance_verified = False
    if corpus_shape_ready and not item_provenance_verified:
        missing.append("item provenance from the pinned snapshot")
    corpus_ready = corpus_shape_ready and item_provenance_verified

    listed = {}
    for line in model_listing.splitlines():
        if " - " in line:
            model_id, label = line.split(" - ", 1)
            if model_id and " " not in model_id:
                listed[model_id] = label
    verified = all(model_id in listed for model_id in MODEL_IDS)
    status = (
        "ready_for_scored_run"
        if corpus_ready and verified
        else "stopped_before_scored_calls"
    )

    calls = call_records or []
    unidentified_calls = sum(
        not isinstance(call, dict)
        or call.get("served_identity_reported") is not True
        or not isinstance(call.get("served_model"), str)
        or not call["served_model"].strip()
        or call["served_model"].startswith("unknown:")
        for call in calls
    )

    return {
        "experiment_id": "EXP-56",
        "registration_commit": REGISTRATION_COMMIT,
        "status": status,
        "stop_reasons": [
            *missing,
            *([] if verified else ["requested Cursor model IDs not listed"]),
        ],
        "model_calls": len(calls),
        "identity_probe_calls": sum(
            isinstance(call, dict) and call.get("purpose") == "identity_probe"
            for call in calls
        ),
        "scored_calls": sum(
            isinstance(call, dict) and bool(call.get("scored")) for call in calls
        ),
        "unidentified_served_model_calls": unidentified_calls,
        "call_records": calls,
        "corpus_audit": {
            "reported_total": reported_total,
            "item_rows": len(rows),
            "killed_rows": killed_rows,
            "equivalent_rows": equivalent_rows,
            "weakest_guard_rows": survivor_rows,
            "partition_non_equivalent_survivor_rows": non_equivalent_survivor_rows,
            "prompt_inputs_present_rows": prompt_inputs_present_rows,
            "source_snapshot_declared": source_declared,
            "source_snapshot_verified": source_verified,
            "shape_ready": corpus_shape_ready,
            "item_provenance_verified": item_provenance_verified,
            "ready": corpus_ready,
            "missing": missing,
        },
        "cursor_discovery": {
            "version": cursor_version.strip(),
            "listed_entries": len(listed),
            "explicit_model_ids": len(listed) - int("auto" in listed),
            "requested_ids_verified": verified,
            "requested_id_labels": {
                model_id: listed.get(model_id) for model_id in MODEL_IDS
            },
            "listing_sha256": hashlib.sha256(
                model_listing.encode("utf-8")
            ).hexdigest(),
        },
        "requested_model_ids": list(MODEL_IDS),
        "per_model_metrics": None,
        "hindsight_optimal_ceiling": None,
        "agreement_matrix": None,
        "model_variance": None,
        "same_served_weights_observed": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=RESULTS)
    args = parser.parse_args()

    version = subprocess.run(
        ["wsl", "-e", "bash", "-lc", "cursor-agent --version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout
    listing = subprocess.run(
        ["wsl", "-e", "bash", "-lc", "cursor-agent --list-models"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout
    exp47 = json.loads(EXP47_RESULTS.read_text(encoding="utf-8"))
    call_records = [json.loads(IDENTITY_PROBE.read_text(encoding="utf-8"))]
    result = audit_inputs(exp47, version, listing, call_records)
    result["exp47_results_sha256"] = hashlib.sha256(
        EXP47_RESULTS.read_bytes()
    ).hexdigest()
    result["identity_probe_sha256"] = hashlib.sha256(
        IDENTITY_PROBE.read_bytes()
    ).hexdigest()

    output = args.output.resolve()
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    os.replace(temporary, output)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ready_for_scored_run" else 2


if __name__ == "__main__":
    raise SystemExit(main())
