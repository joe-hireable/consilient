# EXP-130 findings — can claim sets be derived from the dependency graph?

**Date:** 22 August 2026
**Status:** `[measured]` for every count in `results-exp130.json`; `[asserted]` for the design
conclusions drawn from them in the spec and ADR-0091.
**Stopping rule:** applied as pre-registered. It did not fire; all five analyses produced results.

Every number below appears in `results-exp130.json`. Re-run
`python docs/10-research/experiments/exp130/run_exp130.py` before relying on them. The script is
deterministic: no network, no clock, no randomness; the plans, the lane table, the Python tree and
the trajectory logs are its only inputs. The replay window grew by one claim between drafts of
these findings (this dispatch's own claim entered the log); the artefact reports the final 110.

## Verdict

**Derived claims are a check, not a replacement.** The pre-registered rule said: if the treatment
(derived claims) refuses more than twice as many historical admissions as the control (declared
claims), adopt derivation as a check only. Treatment refused **7**, control refused **1**: 7 > 2,
so the rule selects *check*. The treatment's conflict pairs are a strict superset of the
control's, so no false admits. Peak safe concurrency fell 9 → 7, so the pre-declared win
condition ("no worse than the lanes") does not hold either: the shape is **mixed**, reported as
mixed.

## Inputs `[measured]`

55 plan units across the four stream plans (37 with declared claim paths; 139 claimed paths in
total), 127 declared `depends_on` edges, 0 dependency cycles. 7 hand-written lanes. 106 Python
files under `src/`, `scripts/`, `tests/`. 110 dispatch claims in the 21–22 Aug trajectory logs.

The import graph: **165 resolved internal edges, 0 unresolved internal imports, 705 unresolved
external imports** (stdlib/third-party — correctly not resolvable to repository files), 0
unparseable files, 0 cycles. Resolution is complete for repo-internal imports; nothing internal
was silently dropped.

## A1 — hand-derived lanes drift `[measured]`

180 pairs of units have overlapping declared claims. Of these, **122 are ordered by no lane**
(they share no lane entry), and **37 of the 122 are ordered by nothing at all** — no lane, and no
dependency path in either direction. Separately: 14 cases where a unit claims a path under a
lane's file but appears in no lane's list, and 3 cases where a lane lists a unit claiming nothing
under that lane's file. 0 lane order inversions; 0 dependency cycles. Drift is not hypothetical:
two-thirds of the pairs that can actually collide by claim overlap (122 of 180) have no lane
ordering anyone wrote down, and 37 of those have no ordering of any kind.

## A2 — derivation cost and the god-node check `[measured]`

Maximum independent set: **9 units under declared claims, 7 under derived claims** — derivation
costs two lanes of peak width. Conflict edges: 872 (control) vs 963 (treatment).

Median derived claim: **14 paths** — the pre-registered god-node loss condition (median covers
more than half of the 106 Python files) did not fire. But the distribution has a real hub:
`src/consilient/events.py` has **61 transitive dependents (58 % of the repository)**, the only
file at ≥ 50 %; 2 files sit at ≥ 30 %. 45.95 % of path-claiming units' derived claims include
`events.py`. A refuse-mode check would serialise nearly half the plan on the event schema. This
is the measured reason the check must ship warn-first.

## A3 — failure coverage `[measured]`

`src/consilient/events.py`: 61 transitive dependents — the graph sees the event-schema coupling
clearly. The git index is not in the import graph (it is not a Python module; recorded as
`git_index_in_import_graph: false`). The four failures classify as: F1 (index) invisible by
construction; F2 (check-then-append) a protocol property, not claim content; F3 (abandonment) a
missing-event property; F4 (lane drift) the one failure derivation genuinely addresses (A1).

## A4 — coupling the import graph misses `[measured]`

63 event-kind string literals are shared by two or more files; **104 file pairs are coupled
through those literals with no import edge in either direction** (examples in the artefact:
`state.db`, `errors.jsonl`, `headroom.json` consumers). Derived claims extend only along import
edges, so derivation cannot couple any of these 104 pairs — that follows from the construction,
not from a separate measurement. 22 of the 139 claimed plan paths are not Python at all (specs,
ADRs, the register, CI workflows); no import graph spans them.

## A5 — replay of 21–22 August `[measured]`

110 dispatch claims. Control (declared paths): 109 admitted, 1 refused. Treatment (declared ∪
transitive dependents): 103 admitted, 7 refused — a strict superset of the control's conflicts.
**Actual concurrent overlapping pairs in the real trajectory: 1** — runs
`20260822T140208-40b9767b0c` and `20260822T140603-d953f3635e`, which re-opened their claims 19
seconds apart (14:58:06, 14:58:25) with `docs/10-research/experiment-register.md` added to both,
and were simultaneously live for ~4 minutes. Both *declared* the shared path, so the race is in
the admission protocol (check-then-append), not in claim content — no claim-derivation policy
catches it. 14 of 110 claims were opened more than once (widened mid-run). Peak concurrency: 18
simultaneously live claims on 21 Aug, 8 on 22 Aug.

## What this cannot decide

Whether derivation helps on a codebase with denser internal imports or more hubs; whether the 7
treatment refusals would have prevented real clashes (the one real clash was a protocol race);
anything about non-Python surfaces beyond counting them; Gate A or Gate B. The import graph is
re-derived per run; this result is a snapshot of this repository on 22 Aug 2026. EXP-98
(organisation-level dependency scheduling) is a different claim and stays where it is.

## Live consequence

ADR-0091 records the decision: declared claims stay authoritative; the derived closure becomes a
warn-first coverage check on Python claims (EXP-131 can kill it); lanes derive from declared
edges; the admission race and abandonment are protocol work (fencing epoch, compare-and-append),
not derivation work; the index race is dissolved by per-run worktrees.
