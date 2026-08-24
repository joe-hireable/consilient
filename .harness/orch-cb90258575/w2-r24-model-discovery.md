# R24 — local on-demand model discovery with a freshness gate

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "ADR-0024 requires no telemetry by default, so a central 'model registry' that phones home is
> out. Design it local-first."

Status today: the privacy clause is met and enforced (an AST test bans network imports in
`src/consilient/`). What fails is the discovery clause: `src/consilient/harness.py:177-201` is a
**hand-transcribed snapshot** of one `cursor-agent --list-models` run. It goes stale silently and
nothing detects that. Your job: local, on-demand enumeration plus a freshness gate — no telemetry,
no phone-home, no network in product code.

## The job (one job)

1. Read `src/consilient/harness.py` (the `ModelOption` dataclass, the `MODELS` snapshot, and how
   `select()`/`select_model()` consume them) and the `_run_probe` subprocess pattern in
   `scripts/dispatch.py`. Also read the freshness pattern `_STATE_MAX_AGE` in
   `src/consilient/budget.py` — mirror its shape.
2. Create `scripts/probe_models.py` (stdlib only; execution lives in `scripts/`, never in
   `src/`): enumerate the models the locally installed harness CLIs actually offer, on demand —
   `cursor-agent --list-models` via the existing probe machinery, and the grok/codex equivalents
   **if they exist**; where a vendor has no local enumeration, record `unavailable` honestly
   rather than inventing a list. Write `.harness/models.json` with an `observed_at` RFC3339
   timestamp per source. Subscription CLIs only; no metered calls; no network beyond what the
   installed CLI itself does.
3. Extend `src/consilient/harness.py` with a loader: when `.harness/models.json` exists and is
   fresh (freshness window mirroring `budget.py`'s `_STATE_MAX_AGE` approach — pick a window,
   state it, tag it [asserted]), the registry reflects the probed snapshot; when the snapshot is
   stale or absent, the static `MODELS` remains the documented fallback **and** the staleness is
   surfaced (a function the caller can check — e.g. `registry_freshness()` returning
   fresh/stale/absent) rather than silently trusted. Keep the static `MODELS` export and every
   existing selection behaviour intact — all existing tests must stay green.
4. Create `tests/test_model_discovery.py`:
   - A fixture `.harness/models.json` whose model set disagrees with the static registry is
     detected (a test that would fail if nothing compared them).
   - A stale fixture snapshot is reported stale, not trusted.
   - A fresh agreeing fixture loads.
   - Absent file → absent, fallback intact.
   - Mutation-test: corrupt the fixture's `observed_at` to a stale value, confirm the test fails,
     restore. Report what happened.
5. Run `python scripts/probe_models.py` once for real (it must write `.harness/models.json` —
   verify the artefact, do not trust the exit code), then
   `python -m pytest tests/test_model_discovery.py -q`, full `python -m pytest tests/ -q`,
   `python -m ruff check .`, `python -m mypy --strict src/consilient`. Two tests are currently RED
   from another agent's uncommitted work (a `playwright` import in `src/consilient/computer_use.py`).
   Not yours to fix; add no new red. `.harness/` is instance data — do not commit the JSON.

## OTHER AGENTS ARE WRITING TO THIS TREE RIGHT NOW

Do not open for writing, `git add`, or revert any of:

- `tests/test_v0_invariants.py`, `src/consilient/instructions.py`, `src/consilient/computer_use.py`,
  `docs/10-research/experiment-register.md` (foreign uncommitted work)
- `docs/legal/adopted-components.json`, `.github/scripts/check_component_licences.py`,
  `tests/test_component_licences.py`, `.github/workflows/invariants.yml`,
  `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md`,
  `docs/20-design/capability-layer.md` (claimed by another live run)

Your surface: `scripts/probe_models.py`, `src/consilient/harness.py`, `tests/test_model_discovery.py`.

## Hard limits

- The `consil` CLI is pinned at six commands {record, replay, beta, usage, doctor, dashboard}. Do not add a seventh.
- `src/consilient/` is AST-locked: no subprocess, network, credentials, or third-party imports in product code.
- `routing_orchestration_enabled` stays false. Change no gate condition.
- No secrets anywhere. Never read `C:/Users/jpbpr/.claude/settings.json`. No metered API calls. Do not `git push`.
- Nothing from `../jobboard-v2` or `../hireable-3.0` may reach this repo — no paths, SHAs, or content.
- Never `git add -A`. Stage only the paths this brief names.

## Working rules

- Evidence tags on every claim: [measured] you ran it, [cited] a named source, [asserted] your judgement.
- An invariant ships with its check, in the same commit, mutation-tested.
- Verify by artefact, never by exit code. Never pipe a check into `tail` and read the pipeline's status.
- Correct this brief in your first output sentence if it is wrong, and refuse rather than guess.
  A refusal with a reason is a success.

## Commit

Your dispatched brief carries a commit badge with your run id. Commit only the paths named there
with `CONSILIENT_RUN_ID=<your run id> git commit ...`. If your brief has no badge, do not commit;
leave the work in the tree and say so.
