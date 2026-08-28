"""X06 — hashed anchor set: 100 tasks per family, never committed readable.

The instrument, not a live ranking. A short family, a tracked dest, a missing
second run, a hash mismatch or a readable body in the written set must fail here.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_anchor_set.py"

REQUIRED_REPORT_FIELDS = (
    "verdict",
    "point",
    "interval",
    "n",
    "n_clusters",
    "anchor_set_hash",
    "measured_at",
    "drift",
    "drift_interval",
)

EMPTY_CONTENT_SHA256 = hashlib.sha256(b"").hexdigest()


def _load():
    spec = importlib.util.spec_from_file_location("build_anchor_set", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_anchor_set"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def anchors():
    assert SCRIPT.is_file(), "scripts/build_anchor_set.py is the X06 deliverable"
    return _load()


def _git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _bank(
    families: tuple[str, ...] = ("code", "docs"),
    n: int = 100,
    *,
    content: bool = False,
) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    for family in families:
        for i in range(n):
            row = {
                "family": family,
                "id": f"{family}-{i:03d}",
                "cluster": f"{family}-c{i // 20}",
            }
            if content:
                row["content"] = f"task body {family} {i}"
            tasks.append(row)
    return tasks


def _outcomes(
    anchor: dict[str, Any], *, passed: set[str] | None = None, all_pass: bool = True
) -> list[dict[str, Any]]:
    rows = []
    selected = passed if passed is not None else set()
    for task in anchor["tasks"]:
        task_id = str(task["id"])
        ok = task_id in selected if passed is not None else all_pass
        rows.append(
            {
                "family": task["family"],
                "id": task_id,
                "passed": ok,
            }
        )
    return rows


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_tasks_per_family_is_one_hundred(anchors: Any) -> None:
    assert anchors.TASKS_PER_FAMILY == 100


def test_default_dest_sits_under_the_existing_objects_ignore(anchors: Any) -> None:
    """Claim list forbids editing .gitignore; dest must reuse an ignore that already ships."""
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/objects/" in ignored
    dest = Path(anchors.DEFAULT_DEST)
    assert dest.resolve() == (
        ROOT / ".harness" / "objects" / "anchor-set" / "set.json"
    ).resolve()
    rel = dest.resolve().relative_to(ROOT.resolve()).as_posix()
    probe = subprocess.run(
        ["git", "check-ignore", "--quiet", rel],
        cwd=ROOT,
        env=_git_env(),
        check=False,
    )
    assert probe.returncode == 0, f"{rel} is not gitignored; a readable set would be committable"


def test_default_dest_is_not_tracked(anchors: Any) -> None:
    rel = (
        Path(anchors.DEFAULT_DEST)
        .resolve()
        .relative_to(ROOT.resolve())
        .as_posix()
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--", rel],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_git_env(),
        check=True,
    )
    assert tracked.stdout.split() == []


def test_refuses_a_tracked_dest(anchors: Any) -> None:
    dest = ROOT / "docs" / "anchor-set-must-not-land-here.json"
    with pytest.raises(anchors.AnchorSetError, match="readable|commit|tracked|gitignore"):
        anchors.assert_uncommitted_readable(dest, root=ROOT)


def test_allows_a_dest_outside_the_repository(anchors: Any, tmp_path: Path) -> None:
    dest = tmp_path / "set.json"
    assert anchors.assert_uncommitted_readable(dest, root=ROOT) == dest.resolve()


def test_family_short_of_one_hundred_refuses(anchors: Any) -> None:
    with pytest.raises(anchors.AnchorSetError, match="100"):
        anchors.select_anchor_set(_bank(n=99))


def test_selects_exactly_one_hundred_per_family(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank(n=130))
    counts: dict[str, int] = {}
    for task in built["tasks"]:
        counts[str(task["family"])] = counts.get(str(task["family"]), 0) + 1
    assert counts == {"code": 100, "docs": 100}
    assert built["tasks_per_family"] == 100
    assert set(built["families"]) == {"code", "docs"}


def test_hash_is_64_lowercase_hex(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    assert built["hash"] == built["hash"].lower()
    assert len(built["hash"]) == 64
    int(built["hash"], 16)


def test_hash_is_deterministic(anchors: Any) -> None:
    first = anchors.select_anchor_set(_bank())
    second = anchors.select_anchor_set(_bank())
    assert first["hash"] == second["hash"]
    assert [t["id"] for t in first["tasks"]] == [t["id"] for t in second["tasks"]]


def test_hash_changes_when_a_selected_body_changes(anchors: Any) -> None:
    original = anchors.select_anchor_set(_bank(n=100, content=True))
    mutated = _bank(n=100, content=True)
    target = original["tasks"][0]
    for row in mutated:
        if row["id"] == target["id"] and row["family"] == target["family"]:
            row["content"] = "mutated body"
            break
    changed = anchors.select_anchor_set(mutated)
    assert [t["id"] for t in changed["tasks"]] == [t["id"] for t in original["tasks"]]
    assert changed["hash"] != original["hash"]


def test_written_set_carries_content_digest_not_the_body(
    anchors: Any, tmp_path: Path
) -> None:
    built = anchors.select_anchor_set(_bank(n=100, content=True))
    dest = tmp_path / "set.json"
    anchors.write_anchor_set(built, dest, root=ROOT)
    payload = json.loads(dest.read_text(encoding="utf-8"))
    for task in payload["tasks"]:
        assert "content" not in task
        assert "body" not in task
        assert "prompt" not in task
        assert task["content_sha256"] != EMPTY_CONTENT_SHA256
        assert len(task["content_sha256"]) == 64


def test_selection_is_stable_when_a_high_hash_task_is_added(anchors: Any) -> None:
    """Hash sampling: growing the bank must not reshuffle the frozen 100.

    Seeded ``random.sample`` reshuffles on insertion. Ranking by
    sha256(seed, family, id) only admits a new id when it outranks a sitting one.
    """
    base = _bank(n=100)
    built = anchors.select_anchor_set(base)
    sitting = {(t["family"], t["id"]) for t in built["tasks"]}
    sitting_keys = [
        anchors.selection_key(t["family"], t["id"])
        for t in built["tasks"]
        if t["family"] == "code"
    ]
    worst = max(sitting_keys)
    extra_id = None
    for i in range(10_000):
        candidate = f"code-extra-{i}"
        if anchors.selection_key("code", candidate) > worst:
            extra_id = candidate
            break
    assert extra_id is not None
    grown = anchors.select_anchor_set(
        base + [{"family": "code", "id": extra_id, "cluster": "code-c0"}]
    )
    grown_ids = {(t["family"], t["id"]) for t in grown["tasks"]}
    assert grown_ids == sitting


def test_selection_is_not_the_first_n_in_bank_order(anchors: Any) -> None:
    """Insertion-order of a 130-item family is ids 000-099. Hash ranking is not."""
    built = anchors.select_anchor_set(_bank(n=130))
    selected = {str(t["id"]) for t in built["tasks"]}
    first_hundred = {
        f"{family}-{i:03d}" for family in ("code", "docs") for i in range(100)
    }
    assert len(selected) == 200
    assert selected != first_hundred


def test_selection_is_stable_when_the_bank_is_reversed(anchors: Any) -> None:
    bank = _bank(n=130)
    forward = {t["id"] for t in anchors.select_anchor_set(bank)["tasks"]}
    backward = {
        t["id"] for t in anchors.select_anchor_set(list(reversed(bank)))["tasks"]
    }
    assert backward == forward


def test_a_better_ranked_task_is_admitted_when_the_bank_grows(anchors: Any) -> None:
    """A new id that outranks the sitting 100 must enter; insertion-order
    of an append never would.
    """
    base = _bank(n=100)
    built = anchors.select_anchor_set(base)
    sitting = {(t["family"], t["id"]) for t in built["tasks"]}
    sitting_keys = [
        anchors.selection_key(t["family"], t["id"])
        for t in built["tasks"]
        if t["family"] == "code"
    ]
    cutoff = max(sitting_keys)
    extra_id = None
    for i in range(10_000):
        candidate = f"code-better-{i}"
        if anchors.selection_key("code", candidate) < cutoff:
            extra_id = candidate
            break
    assert extra_id is not None
    grown = anchors.select_anchor_set(
        base + [{"family": "code", "id": extra_id, "cluster": "code-c0"}]
    )
    grown_ids = {(t["family"], t["id"]) for t in grown["tasks"]}
    assert ("code", extra_id) in grown_ids
    dropped = sitting - grown_ids
    assert len(dropped) == 1
    dropped_family, dropped_id = dropped.pop()
    assert dropped_family == "code"
    assert anchors.selection_key("code", extra_id) < anchors.selection_key(
        dropped_family, dropped_id
    )


def test_one_bootstrap_draw_collapses_the_interval_not_the_parameter_space(
    anchors: Any,
) -> None:
    """n_boot=1 has a single resample, so both percentiles are that mean.

    Returning the parameter-space clip (0, 1) / (-1, 1) stays wide.
    """
    built = anchors.select_anchor_set(_bank())
    earlier = _outcomes(built, all_pass=True)
    later_fail = {str(task["id"]) for task in built["tasks"] if task["family"] == "code"}
    later = _outcomes(built, passed=later_fail)
    report = anchors.drift_report(built, [earlier, later], n_boot=1)
    low, high = report["interval"]
    dlow, dhigh = report["drift_interval"]
    assert low == high
    assert dlow == dhigh
    assert (low, high) != (0.0, 1.0)
    assert (dlow, dhigh) != (-1.0, 1.0)


def test_empty_family_name_or_id_refuses(anchors: Any) -> None:
    with pytest.raises(anchors.AnchorSetError):
        anchors.select_anchor_set(
            [{"family": "", "id": "x", "cluster": "c"}] + _bank(n=100)[1:]
        )
    with pytest.raises(anchors.AnchorSetError):
        anchors.select_anchor_set(
            [{"family": "code", "id": "", "cluster": "c"}] + _bank(n=100)[1:]
        )


def test_duplicate_id_in_a_family_refuses(anchors: Any) -> None:
    bank = _bank(n=100)
    bank[1] = dict(bank[0])
    with pytest.raises(anchors.AnchorSetError, match="duplicate"):
        anchors.select_anchor_set(bank)


def test_content_digest_mismatch_refuses(anchors: Any) -> None:
    bank = _bank(n=100, content=True)
    bank[0]["content_sha256"] = "ab" * 32
    with pytest.raises(anchors.AnchorSetError, match="content"):
        anchors.select_anchor_set(bank)


def test_write_then_reload_preserves_hash(anchors: Any, tmp_path: Path) -> None:
    built = anchors.select_anchor_set(_bank())
    dest = tmp_path / "nested" / "set.json"
    anchors.write_anchor_set(built, dest, root=ROOT)
    loaded = anchors.load_anchor_set(dest)
    assert loaded["hash"] == built["hash"]
    assert loaded["hash"] == anchors.hash_anchor_set(loaded)


def test_one_run_is_insufficient_data(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    report = anchors.drift_report(built, [_outcomes(built)])
    assert report["verdict"] == "insufficient_data"
    assert report["point"] is None
    assert report["interval"] is None
    assert report["drift"] is None
    for field in REQUIRED_REPORT_FIELDS:
        assert field in report
    assert report["anchor_set_hash"] == built["hash"]
    assert report["n"] == 200


def test_two_runs_report_signed_drift_with_an_interval(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    earlier = _outcomes(built, all_pass=True)
    later_fail = {str(task["id"]) for task in built["tasks"] if task["family"] == "code"}
    later = _outcomes(built, passed=later_fail)
    report = anchors.drift_report(
        built, [earlier, later], measured_at="2026-08-24T00:00:00+00:00", n_boot=200
    )
    assert report["verdict"] == "measured"
    assert report["point"] == pytest.approx(0.5)
    assert report["n"] == 200
    assert report["n_clusters"] >= 2
    assert report["drift"] == pytest.approx(-0.5)
    low, high = report["interval"]
    dlow, dhigh = report["drift_interval"]
    # Cluster-bootstrap percentiles on this 50/50, 10-cluster fixture,
    # not the [0, 1] / [-1, 1] parameter space. n_boot=200 is part of the
    # contract: a vacuous clip to the bounds still satisfies 0 <= low <=
    # point <= high <= 1.
    assert low == pytest.approx(0.2)
    assert high == pytest.approx(0.8)
    assert dlow == pytest.approx(-0.8)
    assert dhigh == pytest.approx(-0.2)
    assert 0.0 < low < report["point"] < high < 1.0
    assert -1.0 < dlow < report["drift"] < dhigh < 1.0
    assert report["measured_at"] == "2026-08-24T00:00:00+00:00"
    assert report["anchor_set_hash"] == built["hash"]


def test_later_better_is_positive_drift(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    earlier = _outcomes(built, passed=set())
    later = _outcomes(built, all_pass=True)
    report = anchors.drift_report(built, [earlier, later], n_boot=50)
    assert report["drift"] == pytest.approx(1.0)


def test_hash_mismatch_refuses_comparison(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    other = anchors.select_anchor_set(_bank(families=("code", "qa")))
    earlier = {"anchor_set_hash": other["hash"], "outcomes": _outcomes(other)}
    later = {"anchor_set_hash": other["hash"], "outcomes": _outcomes(other)}
    with pytest.raises(anchors.AnchorSetError, match="hash"):
        anchors.drift_report(built, [earlier, later])


def test_incomplete_run_refuses(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    rows = _outcomes(built)[:-1]
    with pytest.raises(anchors.AnchorSetError, match="missing|incomplete|cover"):
        anchors.drift_report(built, [rows, _outcomes(built)])


def test_run_that_names_a_foreign_task_refuses(anchors: Any) -> None:
    built = anchors.select_anchor_set(_bank())
    rows = _outcomes(built)
    rows[0] = {**rows[0], "id": "not-in-set"}
    with pytest.raises(anchors.AnchorSetError):
        anchors.drift_report(built, [_outcomes(built), rows])


def test_script_does_not_embed_a_readable_bank(anchors: Any) -> None:
    """The committed builder is not itself the leak."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "hireable" not in source.lower()
    assert "jobboard" not in source.lower()
    assert not hasattr(anchors, "DEFAULT_BANK")
    assert "task body" not in source


def test_cli_writes_the_set_and_prints_the_hash(anchors: Any, tmp_path: Path, capsys: Any) -> None:
    bank_path = tmp_path / "bank.json"
    dest = tmp_path / "set.json"
    bank_path.write_text(json.dumps(_bank()), encoding="utf-8")
    code = anchors.main(["--bank", str(bank_path), "--out", str(dest)])
    assert code == 0
    payload = json.loads(dest.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out
    assert payload["hash"] in printed
    assert len(payload["tasks"]) == 200


def test_cli_drift_prints_a_measured_report(
    anchors: Any, tmp_path: Path, capsys: Any
) -> None:
    bank_path = tmp_path / "bank.json"
    dest = tmp_path / "set.json"
    bank_path.write_text(json.dumps(_bank()), encoding="utf-8")
    assert anchors.main(["--bank", str(bank_path), "--out", str(dest)]) == 0
    capsys.readouterr()
    built = json.loads(dest.read_text(encoding="utf-8"))
    earlier_path = tmp_path / "run1.json"
    later_path = tmp_path / "run2.json"
    earlier_path.write_text(json.dumps(_outcomes(built)), encoding="utf-8")
    later_path.write_text(json.dumps(_outcomes(built, passed=set())), encoding="utf-8")
    code = anchors.main(
        [
            "--set",
            str(dest),
            "--earlier",
            str(earlier_path),
            "--later",
            str(later_path),
            "--n-boot",
            "50",
        ]
    )
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "measured"
    assert report["drift"] == pytest.approx(-1.0)


def test_cli_refuses_to_write_a_tracked_path(anchors: Any, tmp_path: Path) -> None:
    bank_path = tmp_path / "bank.json"
    bank_path.write_text(json.dumps(_bank()), encoding="utf-8")
    dest = ROOT / "docs" / "anchor-set-must-not-land-here.json"
    with pytest.raises(anchors.AnchorSetError):
        anchors.main(["--bank", str(bank_path), "--out", str(dest)])
    assert not dest.exists()
