"""Fixtures shared by every instruction-assembly test: a UTC clock, two trajectory
writers, a two-skill tree in which one skill matches on beta and verifier wording while
the other is about tulip bulbs, and the promotion path that puts content into the
adapted layer.

`promoted_layer` needs a measured β and improving execution evidence because that is the
only route the promoter accepts, and it lives here rather than inline so that no test
which depends on an active layer can quietly invent one. The skill tree deliberately
contains one match and one non-match, because a selector tested only against matching
input is not tested at all."""

from datetime import datetime, timezone
from pathlib import Path
from consilient import beta as beta_mod
from consilient import promote
from consilient.events import SCHEMA_VERSION, append
from consilient.instructions import (
    propose_adaptation,
    record_adapted,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def note(log_dir: Path, text: str) -> dict[str, object]:
    return append(
        log_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now(),
            "event": "note.made",
            "actor": "test",
            "data": {"text": text},
        },
    )


def record_event(
    log_dir: Path, kind: str, data: dict[str, object]
) -> dict[str, object]:
    return append(
        log_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now(),
            "event": kind,
            "actor": "test",
            "data": data,
        },
    )


def skills_tree(root: Path) -> Path:
    skills = root / "skills"
    alpha = skills / "alpha-skill"
    alpha.mkdir(parents=True)
    (alpha / "SKILL.md").write_text(
        "---\n"
        "name: alpha-skill\n"
        "description: Use when measuring beta and verifier outcomes.\n"
        "---\n\n"
        "Alpha body.\n",
        encoding="utf-8",
    )
    gamma = skills / "gamma-skill"
    gamma.mkdir(parents=True)
    (gamma / "SKILL.md").write_text(
        "---\n"
        "name: gamma-skill\n"
        "description: Use when planting tulip bulbs in autumn.\n"
        "---\n\n"
        "Gamma body.\n",
        encoding="utf-8",
    )
    return skills


def measured_beta() -> beta_mod.Beta:
    n = 30
    false_accepts = 5
    return beta_mod.Beta(
        beta_mod.MEASURED,
        "self-mod-fixture",
        "instructions-v1",
        n,
        false_accepts,
        false_accepts / n,
        beta_mod.wilson(false_accepts, n),
        ("2026-08-01T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
        False,
    )


def improving_evidence() -> promote.ExecutionEvidence:
    return promote.ExecutionEvidence(
        ran=True,
        suite_passed=True,
        metric_before=0.2,
        metric_after=1.0,
        verifier_version="instructions-v1",
    )


def promoted_layer(
    log_dir: Path, text: str = "Joe reviews diffs on a phone; lead with the verdict."
) -> str:
    outcome = propose_adaptation(
        log_dir, text, measured_beta(), enabled=True, evidence=improving_evidence()
    )
    assert outcome.decision.action == "promote"
    record_adapted(log_dir, candidate_id=outcome.decision.candidate.identity, text=text)
    return outcome.decision.candidate.identity
