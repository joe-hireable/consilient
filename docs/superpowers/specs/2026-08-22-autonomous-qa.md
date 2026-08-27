# Autonomous QA: one command, defect classes, personas, bounded adversarial generation

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** § 3 (personas as falsifiers) and EXP-96's unclassifiable threshold.

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

- **Status:** implemented in `scripts/qa_battery.py` and `scripts/persona_qa.py`; R34 remains
  **PARTIAL** until sandboxes and a first-class `consil` surface ship. [measured]
- **Satisfies:** R34 obligation for a QA R&D pipeline with synthetic users, seeded faults and
  an unattended loop hook. [asserted]
- **Non-goals:** no new `consil` subcommand; no gate-condition change; no weakening of existing
  checks. [measured]

## 1. One command

```bash
python scripts/qa_battery.py
python scripts/qa_battery.py --dry-run   # report without appending
python scripts/qa_battery.py --json
```

Runs, by reuse rather than reimplementation:

| Step | Tool |
|------|------|
| Test suite | `pytest tests/ -q` |
| Static gates | `mypy --strict`, `ruff check .` |
| Leak gates | `check_secrets`, `check_foreign_identifiers`, `check_private_corpus --require-corpora` |
| Trajectory health | `scripts/capture_health.py --dry-run` |
| Gate state | `consil doctor` |
| Executable models | `pytest tests/test_decision_models.py` |
| Persona falsification | `persona_qa` journeys (in-process) |
| Defect classes | `tests/test_qa_battery.py` check functions |
| Seeded faults | bounded batch with EXP-96 unclassifiable threshold |

Outcome is appended to the trajectory as `qa.battery` through `events.append`, matching
`capture.checked`. [measured]

Exit **0** only when every gate **PASSED**, persona journeys found no defect, and no **new**
defect-class finding is present. Known producer/consumer gaps on the allowlist are reported
but do not fail the battery. [asserted]

## 2. Defect classes (runnable)

| Class | Source incident | Check | Reproduction |
|-------|-----------------|-------|--------------|
| Producer without semantic consumer | Four wiring orphans 22 Aug 2026 (`decision.autonomous`, `instructions.assembled`, `routing.consulted`, `usage.observed`) | `check_producer_consumer_gaps` | Allowlist in `KNOWN_PRODUCER_CONSUMER_GAPS`; fails on new kinds |
| Generated index drift | C3 corrections-2026-08-21; requirements drift | `check_generated_index_drift` | `build_requirements.py --check`; ADR count in `index.md` vs directory |
| `[measured]` without artefact | C1, C5 corrections-2026-08-21 | `check_measured_claims_have_artefacts` | Greenfield 72.8/75.9 figures vs `results-exp43.json` |
| Gate fail-open | Pre-push hook 22 Aug 2026 | `check_gate_fails_when_checker_absent` | `.githooks/pre-push` must FAIL when checker script missing |

A finding is a **failing check with a reproduction**, or it is not reported as a defect.

## 3. Personas (falsifiers, not confirmers)

Four principal-named types exercise the **product** through real CLI surfaces. Each records: [asserted]

- **attempted** — the wrong answer it tried to get accepted
- **system_response** — what the system did
- **accepted_wrongly** — true only on a β failure (silent acceptance)

| Persona | Falsification attempt | Different class of facts |
|---------|----------------------|---------------------------|
| average-joe | Trust prose command count over `consil --help` | Specification vs executable surface |
| developer | Treat broken `pip install -e .` as working | Implicit install oracle |
| contributor | Follow stale CONTRIBUTING claiming no code | Document state vs repository state |
| researcher | Cite register figure without reproducible script | Reference vs artefact execution |
| operator | Accept false-zero beta or undocumented ceilings | CLI state vs documentation |

`operator` cold-directory check: `consil beta` must refuse (exit 2), not report zero. [asserted]

## 4. Adversarial generation (bounded)

Pre-registered **unclassifiable threshold: 10%** (`MAX_UNCLASSIFIABLE_RATE = 0.10`), matching
EXP-96. [measured] [cited: `docs/10-research/experiments/exp96/run_exp96.py`]

When `unclassifiable / generated` exceeds the threshold, the battery **refuses a headline proxy β**
and reports `headline_permitted: false`. Seeded faults are applied in `.harness/qa-seeded/` and
run through `pytest`; syntax errors count as unclassifiable, not as verifier acceptance.

## 5. Unattended loop

Reuse `scripts/run_loop.py` — do not add a second supervisor. A **qa** named loop:

```bash
python scripts/run_loop.py \
  --name qa \
  --interval 3600 \
  --timeout 1200 \
  --cost 0 \
  --max-ticks 24 \
  -- python scripts/qa_battery.py
```

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Interval | 3600 s | Hourly sensing; EXP-70 class-1 battery precedent |
| Timeout | 1200 s | Full suite + gates measured ~35–90 s; headroom for corpora |
| Cost | 0 USD | No metered calls |
| max-ticks | 24 | One day of hourly ticks unless restarted |

**Stops when:** `--stop` kill switch; tick ceiling; budget refusal; command refuses to start;
or `run_loop` single-instance lock held by another process. [measured: `src/consilient/loop.py`]

## 6. Evidence tags

All claims in this document carry `[measured]`, `[asserted]`, or `[cited]` as stated. Proxy β from
the seeded batch is **not** human-verdict β and does not read any gate. [asserted]
