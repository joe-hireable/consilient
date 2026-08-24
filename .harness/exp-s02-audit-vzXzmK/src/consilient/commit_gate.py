"""The commit-attribution gate: a commit may contain only what its committer owns.

The work-clash problem is solved at dispatch time (`coordination`): two live runs
cannot claim the same path. The commit-clash problem is not: `git add` and
`git commit` operate on a shared index, so an agent staging by directory — or by
`git add -A` — sweeps a neighbour's half-written work into its own commit. Three
occurrences were measured on 21 August 2026, including commit 4c0b901, whose
message describes one agent's dispatch work while containing four files of
another's. A commit message that describes one agent's work while containing
another's is a false record; in a project whose subject is provenance that is
the worst class of defect available.

This module is the policy. Execution (git and environment IO) lives in
`scripts/commit_gate.py`, wired in by the tracked `.githooks/pre-commit`. The
rules, in the order they are applied:

1. Nothing staged, or no live dispatch claim names this worktree: admit. Solo
   work carries no attribution risk, so it carries no friction.
2. While any claim is live here, the commit must name its committer
   (`CONSILIENT_RUN_ID`). Without identity the checks below cannot tell the
   claim-holder from a bystander, and a badgeless commit would bypass them.
   Anyone not dispatched exports a name of their own once per shell.
3. A staged path overlapping a path claimed by a *different* live run is
   refused. That is the sweep, caught regardless of intent.
4. A committer whose own live claim declared paths may not stage outside them:
   the dispatch declaration is the bound of what this run may record.
5. A committer whose own live claim declared no paths must enumerate what it is
   committing (`CONSILIENT_COMMIT_PATHS`). Measured on 21 August 2026: 17 of 18
   dispatch claims declared no paths, so without this leg the gate would be
   nearly dead in the common case. The enumeration is what turns `git add -A`
   from a habit into a deliberate act.

A dead agent holding a claim needs no handling here: a claim is a projection
with an expiry (run timeout plus grace), checked at read time by
`coordination.live_claims`. Once the clock passes `expires_at` the claim is not
live, rule 1 admits, and no lock file exists to go stale — the measured failure
of `.budget.lock` after a SIGKILL is not reproduced, because there is no file.

What this gate deliberately does not do: it cannot unscramble a file two agents
edited simultaneously in one working tree (that is the dispatch-time claim's
job, and it is why claims exist), and it cannot stop a committer who enumerates
paths it does not own. `--no-verify` remains the documented escape hatch, as
with the secrets stage. The gate makes accidental entanglement fail closed;
deliberate false attribution stays visible in the trajectory instead.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from . import coordination

RUN_ID_ENV = "CONSILIENT_RUN_ID"
PATHS_ENV = "CONSILIENT_COMMIT_PATHS"


@dataclass(frozen=True)
class Refusal:
    """The commit is refused; `reason` tells the committer exactly what fixes it."""

    reason: str


@dataclass(frozen=True)
class Admission:
    """The commit may proceed. `staged` is the canonical staged set checked."""

    committer: str | None
    staged: tuple[str, ...]


Decision = Refusal | Admission


def relevant_claims(
    live: Sequence[coordination.Claim], *, worktree: Path
) -> tuple[coordination.Claim, ...]:
    """The live claims whose recorded cwd is this worktree, or overlaps it.

    Claims from a different worktree share neither index nor working tree with
    a commit made here, so they must not obstruct one. A claim that cannot name
    its tree is declined rather than treated as relevant everywhere: the single
    writer always records a cwd, so an empty one is a foreign schema, not
    evidence about this tree.
    """
    root = coordination.canonical_path(str(worktree))
    kept = []
    for claim in live:
        cwd = claim.cwd.strip()
        if cwd and coordination.paths_overlap(coordination.canonical_path(cwd), root):
            kept.append(claim)
    return tuple(kept)


def _within(path: str, declared: Sequence[str]) -> bool:
    return any(coordination.paths_overlap(path, held) for held in declared)


def check_commit(
    *,
    staged: Sequence[str],
    live: Sequence[coordination.Claim],
    worktree: Path,
    run_id: str | None,
    declared: Sequence[str] | None,
) -> Decision:
    """Admit or refuse one commit. Pure: every input arrives as a parameter."""
    committer = (run_id or "").strip() or None
    if not staged:
        return Admission(committer=committer, staged=())
    claims = relevant_claims(live, worktree=worktree)
    if not claims:
        return Admission(
            committer=committer,
            staged=tuple(
                coordination.canonical_path(path, cwd=worktree) for path in staged
            ),
        )
    if committer is None:
        return Refusal(
            f"{len(claims)} dispatch claim(s) are live in this worktree, so a commit "
            f"must name its committer: {RUN_ID_ENV}=<run id> git commit ... — a "
            "dispatched run finds its run id in its brief; anyone else exports a "
            "name of their own once per shell. Nothing was committed. Escape hatch: "
            "git commit --no-verify, and say why in the message."
        )
    canonical_staged = tuple(
        coordination.canonical_path(path, cwd=worktree) for path in staged
    )
    own = next((claim for claim in claims if claim.run_id == committer), None)
    for path in canonical_staged:
        for claim in claims:
            if claim.run_id == committer:
                continue
            for held in claim.paths:
                if coordination.paths_overlap(path, held):
                    return Refusal(
                        f"staged path {path!r} overlaps a path claimed by live run "
                        f"{claim.run_id} ({claim.ticket}, claim expires "
                        f"{claim.expires_at}). It is not yours to commit: unstage it "
                        "and leave it for the run that owns it. Nothing was "
                        "committed."
                    )
    if own is not None:
        if own.paths:
            for path in canonical_staged:
                if not _within(path, own.paths):
                    return Refusal(
                        f"staged path {path!r} is outside the paths run "
                        f"{committer} claimed at dispatch: {list(own.paths)}. Either "
                        "it is not yours (unstage it) or the claim was too narrow "
                        "(re-dispatch with --claim covering it). Nothing was "
                        "committed."
                    )
        else:
            allowed = tuple(
                coordination.canonical_path(path, cwd=worktree)
                for path in (declared or ())
                if path.strip()
            )
            if not allowed:
                return Refusal(
                    f"run {committer} claimed no paths at dispatch, so enumerate "
                    "what this commit contains: "
                    f"{RUN_ID_ENV}={committer} {PATHS_ENV}=path/one,path/two "
                    "git commit ... — staged: "
                    f"{[path for path in staged]}. Nothing was committed."
                )
            for path in canonical_staged:
                if not _within(path, allowed):
                    return Refusal(
                        f"staged path {path!r} is not in {PATHS_ENV}; run "
                        f"{committer} claimed no paths at dispatch, so every staged "
                        "path must be enumerated. Add it only if it is yours; "
                        "otherwise unstage it. Nothing was committed."
                    )
    return Admission(committer=committer, staged=canonical_staged)
