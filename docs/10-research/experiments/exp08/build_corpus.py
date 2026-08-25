"""EXP-08 corpus builder: paired known-bad and control artefacts.

Source: EXP-47's 20 August 2026 composite survivors
(``results-exp47-2026-08-20.json``), not the 22 August overwrite at
``results-exp47.json`` which reports an empty ``weakest_guards`` list.

Snapshot: ``d579bee`` — the commit EXP-47 actually mutated. The working tree
has moved several hundred commits since; 181 of the 520 uniquely locatable
survivors no longer address HEAD. Revalidation is against this snapshot.
[measured]

Each pair is anchored to a frozen, already-committed plan unit whose ``claims``
include the mutated ``src/consilient/`` path. The sample is seeded; exclusions
are recorded, never dropped silently.

    python docs/10-research/experiments/exp08/build_corpus.py
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CORPUS = HERE / "corpus-exp08.json"
SOURCE_RESULTS = ROOT / "docs/10-research/experiments/exp47/results-exp47-2026-08-20.json"
PLAN_UNITS = ROOT / ".harness/plan-units.json"

# The revision EXP-47 mutated. EXP-57 already pinned the short form; the full
# hash is recorded so the corpus names the object, not a moving ref.
SNAPSHOT_REV = "d579beedd0d88aeebee75666e0a4db89f2c3ac5d"
SOURCE_FILES = (
    "src/consilient/__init__.py",
    "src/consilient/beta.py",
    "src/consilient/cli.py",
    "src/consilient/events.py",
    "src/consilient/projection.py",
)

# Frozen so regeneration cannot drift when later units land. Only units that
# had already committed, as of this builder, and that claim an EXP-47 source
# file. Claims are re-read from plan-units.json at run time so a claim edit
# fails the pairing check rather than silently widening the sample.
ELIGIBLE_UNIT_IDS = (
    "A01",
    "A02",
    "AB",
    "AC",
    "AN",
    "AO",
    "B04",
    "C01",
    "C02",
    "D01",
    "E01",
    "F01",
    "F02",
    "F03",
    "G01",
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "N06",
    "O01",
    "P01",
    "Q01",
    "Q02",
    "R01",
    "S01",
    "S03",
    "T01",
    "V01",
    "X01",
    "Y04",
    "Z05",
)

SEED = 8
N_PAIRS = 120
CHECKS_PASS = {"pytest": "pass", "mypy": "pass", "ruff": "pass"}


def canonical_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def count_reasons(exclusions: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(item["reason"]) for item in exclusions)
    return dict(sorted(counts.items()))


def _translate_windows_gitdir(raw: str) -> str:
    if len(raw) >= 3 and raw[1] == ":" and raw[2] in "\\/":
        return "/mnt/" + raw[0].lower() + raw[2:].replace("\\", "/")
    return raw


def git_env() -> dict[str, str]:
    """Honour this checkout even when a dispatch exported a stale GIT_DIR."""
    env = os.environ.copy()
    git_file = ROOT / ".git"
    if git_file.is_file():
        text = git_file.read_text(encoding="utf-8").strip()
        if text.lower().startswith("gitdir:"):
            raw = text.split(":", 1)[1].strip()
            if os.name != "nt":
                raw = _translate_windows_gitdir(raw)
            env["GIT_DIR"] = raw
            env["GIT_WORK_TREE"] = str(ROOT)
            return env
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=git_env(),
        timeout=60,
    )


def git_show(rev: str, path: str) -> str:
    result = git("show", f"{rev}:{path}")
    if result.returncode != 0:
        raise RuntimeError(f"git show {rev}:{path} failed: {result.stderr.strip()}")
    return result.stdout


def git_blob_sha1(content: str) -> str:
    data = content.encode("utf-8")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def snapshot_digest(blobs: list[tuple[str, str]]) -> str:
    payload = json.dumps(blobs, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def locate(snippet: str, lines: list[str]) -> int | None:
    """Index of the unique line equal to ``snippet`` after stripping, else None."""
    hits = [i for i, line in enumerate(lines) if line.strip() == snippet.strip()]
    return hits[0] if len(hits) == 1 else None


def mutate(text: str, index: int, replacement: str) -> str:
    lines = text.splitlines(keepends=True)
    original = lines[index]
    stripped = original.rstrip("\r\n")
    ending = original[len(stripped) :]
    indent = stripped[: len(stripped) - len(stripped.lstrip())]
    lines[index] = f"{indent}{replacement.strip()}{ending or os.linesep}"
    return "".join(lines)


def verify_source_excludes_equivalents(document: dict[str, Any]) -> dict[str, int]:
    """Refuse the 22 Aug empty re-run and any doctored count reconciliation."""
    counts = document["raw_counts"]
    expected = counts["composite_survived"] - counts["equivalent_mutants"]
    if counts["true_defects_survived"] != expected:
        raise RuntimeError("EXP-47 counts do not reconcile; corpus provenance broken")
    if expected <= 0 or not document.get("weakest_guards"):
        raise RuntimeError(
            "EXP-47 weakest_guards is empty — refusing the 22 Aug trap re-run"
        )
    if len(document["weakest_guards"]) != expected:
        raise RuntimeError(
            "weakest_guards is not the equivalence-corrected survivor set"
        )
    return {
        "equivalent_mutants_excluded_by_exp47": counts["equivalent_mutants"],
        "non_equivalent_survivors": expected,
    }


def classify_guards(
    guards: list[dict[str, Any]], sources: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Include uniquely addressable non-test survivors; record every exclusion."""
    included: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for entry in guards:
        file_path = str(entry["file"])
        orig = str(entry["orig_snippet"])
        mut = str(entry["mut_snippet"])
        base = {
            "source_id": entry["id"],
            "file": file_path,
            "line": entry.get("line"),
            "operator": entry.get("operator"),
        }
        if file_path.startswith("tests/") or "/tests/" in file_path:
            exclusions.append({**base, "reason": "tests_path"})
            continue
        if "\n" in orig or "\n" in mut:
            exclusions.append({**base, "reason": "multiline"})
            continue
        if len(orig) >= 120 or len(mut) >= 120:
            exclusions.append({**base, "reason": "truncated"})
            continue
        if orig.strip() == mut.strip():
            exclusions.append({**base, "reason": "equivalent_snippet"})
            continue
        source = sources.get(file_path)
        if source is None:
            exclusions.append({**base, "reason": "missing_file_at_snapshot"})
            continue
        index = locate(orig, source.splitlines())
        if index is None:
            exclusions.append({**base, "reason": "not_uniquely_locatable"})
            continue
        included.append({**entry, "index": index})
    return included, exclusions


def load_plan_units() -> dict[str, Any]:
    return json.loads(PLAN_UNITS.read_text(encoding="utf-8"))


def _commit_subjects() -> list[tuple[str, str]]:
    result = git("log", "--format=%H\t%s")
    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr.strip()}")
    rows: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        digest, subject = line.split("\t", 1)
        rows.append((digest, subject.strip()))
    return rows


def unit_commit_hash(unit: dict[str, Any], subjects: list[tuple[str, str]]) -> str:
    want = (unit.get("commit") or "").strip().lower()
    if not want:
        raise RuntimeError("plan unit has no commit subject")
    for digest, subject in subjects:
        if subject.lower().startswith(want):
            return digest
    raise RuntimeError(f"plan unit is not committed: {want!r}")


def eligible_units(
    units: dict[str, Any], subjects: list[tuple[str, str]]
) -> dict[str, dict[str, Any]]:
    chosen: dict[str, dict[str, Any]] = {}
    source_set = set(SOURCE_FILES)
    for uid in ELIGIBLE_UNIT_IDS:
        unit = units[uid]
        claims = [c for c in unit["claims"] if c in source_set]
        if not claims:
            raise RuntimeError(f"{uid} no longer claims an EXP-47 source file")
        chosen[uid] = {
            "claims": list(unit["claims"]),
            "source_claims": claims,
            "unit_commit": unit_commit_hash(unit, subjects),
        }
    return chosen


def arm_digest(
    unit_id: str,
    eligible: dict[str, dict[str, Any]],
    sources: dict[str, str],
    mutated_file: str | None,
    mutated_text: str | None,
) -> str:
    blobs: list[tuple[str, str]] = []
    for path in sorted(eligible[unit_id]["source_claims"]):
        if mutated_file is not None and path == mutated_file:
            assert mutated_text is not None
            content = mutated_text
        else:
            content = sources[path]
        blobs.append((path, git_blob_sha1(content)))
    return snapshot_digest(blobs)


def build_manifest() -> dict[str, Any]:
    document = json.loads(SOURCE_RESULTS.read_text(encoding="utf-8"))
    provenance = verify_source_excludes_equivalents(document)
    sources = {path: git_show(SNAPSHOT_REV, path) for path in SOURCE_FILES}
    included, exclusions = classify_guards(document["weakest_guards"], sources)

    units = load_plan_units()
    subjects = _commit_subjects()
    eligible = eligible_units(units, subjects)

    assigned: list[dict[str, Any]] = []
    rng = random.Random(SEED)
    ordered = sorted(included, key=lambda e: (e["file"], e["id"]))
    for entry in ordered:
        owners = sorted(
            uid
            for uid, meta in eligible.items()
            if entry["file"] in meta["source_claims"]
        )
        if not owners:
            exclusions.append(
                {
                    "source_id": entry["id"],
                    "file": entry["file"],
                    "line": entry.get("line"),
                    "operator": entry.get("operator"),
                    "reason": "no_claiming_unit",
                }
            )
            continue
        assigned.append({**entry, "unit_id": rng.choice(owners)})

    if len(assigned) < N_PAIRS:
        raise RuntimeError(
            f"only {len(assigned)} pairable items; need {N_PAIRS}"
        )
    selected = rng.sample(assigned, N_PAIRS)
    selected.sort(key=lambda e: (e["unit_id"], e["file"], e["id"]))

    pairs: list[dict[str, Any]] = []
    for offset, entry in enumerate(selected, start=1):
        uid = entry["unit_id"]
        file_path = entry["file"]
        pristine = sources[file_path]
        mutated = mutate(pristine, entry["index"], entry["mut_snippet"])
        if mutated == pristine:
            raise RuntimeError(f"mutation was a no-op for source_id {entry['id']}")
        control_digest = arm_digest(uid, eligible, sources, None, None)
        bad_digest = arm_digest(uid, eligible, sources, file_path, mutated)
        pairs.append(
            {
                "pair_id": f"{offset:04d}",
                "unit_id": uid,
                "unit_commit": eligible[uid]["unit_commit"],
                "base_commit": SNAPSHOT_REV,
                "seed": SEED,
                "source_id": entry["id"],
                "file": file_path,
                "line": entry["line"],
                "index": entry["index"],
                "operator": entry["operator"],
                "orig_snippet": entry["orig_snippet"],
                "mut_snippet": entry["mut_snippet"],
                "bad": {
                    "mutated": True,
                    "snapshot_digest": bad_digest,
                    "checks": dict(CHECKS_PASS),
                },
                "control": {
                    "mutated": False,
                    "snapshot_digest": control_digest,
                    "checks": dict(CHECKS_PASS),
                },
            }
        )

    exclusions.sort(key=lambda e: (str(e.get("reason")), str(e.get("file")), e.get("source_id") or 0))
    return {
        "experiment_id": "EXP-08",
        "seed": SEED,
        "n_pairs": len(pairs),
        "snapshot_rev": SNAPSHOT_REV,
        "source_results": str(SOURCE_RESULTS.relative_to(ROOT).as_posix()),
        "source_results_reason": (
            "Register live record, 20 Aug 2026: 1,931 mutants, 586 non-equivalent "
            "composite survivors. results-exp47.json is the 22 Aug re-run with "
            "pytest_survived 0 and empty weakest_guards — an empty corpus."
        ),
        "checks_source": "exp47-2026-08-20-composite-survivor",
        "provenance": provenance,
        "exclusion_counts": count_reasons(exclusions),
        "exclusions": exclusions,
        "pairs": pairs,
    }


def main() -> None:
    manifest = build_manifest()
    CORPUS.write_bytes(canonical_dump(manifest).encode("utf-8"))
    counts = manifest["exclusion_counts"]
    print(f"wrote {CORPUS} ({manifest['n_pairs']} pairs)")
    print(f"exclusions: {sum(counts.values())} {counts}")


if __name__ == "__main__":
    main()
