# 0031. Implement v0 in Python, with a stdlib-only core

- **Status:** ⛔ SUPERSEDED by [0032](0032-single-language-python-for-the-orchestrator.md), 20 Aug 2026 — same
  answer, properly evidenced, and the distribution question is now closed
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (approval of the specification), Claude Opus 5 (this choice)
- **Inquiry tier reached:** T1 ground — a reversibility argument, not a measurement
- **Executable model:** none.

## Context

Joe approved the v0 specification for implementation on 20 August 2026. [measured] The first
increment needs a language and a layout, and no ADR names either. ADR-0007 fixes the surface
as a CLI; ADR-0006 fixes the store as append-only JSONL plus a SQLite projection. Neither
constrains the implementation.

Two signals pointed in different directions. Every research instrument in the repository is
Python, and CI already installs Python. [measured] But `packages/consil` and
`packages/consilient` are npm name reservations, which implies an intent to distribute on
npm. [measured]

## Decision

**Implement v0 in Python, in `src/consilient/`, with a core that imports nothing outside the
standard library.** Tests live in `tests/` and run under pytest, which the repository already
uses.

**The distribution question is explicitly not decided.** Reserving an npm name is not the same
as choosing a runtime, and `npx consil` remains available later through a thin launcher or a
reimplementation of the CLI layer. That decision is Joe's and belongs in its own ADR.

## Why this is a small decision rather than a large one

The load-bearing artefacts are **language-independent**: the trajectory is JSONL, the
projection is SQLite, and the event schema is JSON. [asserted] A different language could
replay the same log and reproduce the same state digest tomorrow. What is being chosen is the
implementation of a thin recorder, a projection builder, a β computation and an argument
parser — roughly four hundred lines. [measured]

That is the reversibility test from ADR-0021: this can be changed for close to free, so it is
not a decision worth blocking on, and it is recorded rather than debated. [cited]

## Evidence

- `[measured]` Every existing instrument — `experiments/exp01`, `exp05`, `exp07`, `exp27` —
  is Python, as are both CI workflows. A second toolchain would be a new maintenance surface
  for a solo maintainer.
- `[measured]` The core imports only `json`, `sqlite3`, `hashlib`, `argparse`, `math`,
  `dataclasses`, `re` and `pathlib`. No dependency approval is required, so `AGENTS.md`'s
  "ask first: adding a dependency" boundary is not crossed.
- `[measured]` `sqlite3` ships with CPython, which is what ADR-0006's projection needs.
- `[asserted]` A stdlib-only core keeps the replay invariant auditable by anyone with a
  Python install and no lockfile.

## Evidence against

- **The npm reservations are a real signal and this decision ignores them.** If Joe's intent
  is `npx consil`, a Node implementation would avoid a launcher and would match the runtime of
  every harness Consilience orchestrates — Claude Code, Codex and Cursor are all Node CLIs.
  [measured] This is the strongest objection and it is not resolved.
- Python's packaging and single-file distribution story is worse than Node's for a tool whose
  success condition is "worth a stranger's install" (ADR-0004). [asserted]
- Choosing before asking is a small violation of the repository's own habit of asking first;
  it is done because the alternative was to block the first increment overnight on a question
  whose answer does not change the schema. [asserted]
- No prior art was checked for meta-harness implementation languages. [asserted]

## Consequences

**Positive.** The increment shipped with its checks in the same commit and no new toolchain.
CI needed one workflow and no lockfile.

**Negative.** If npm distribution is chosen, the CLI layer is rewritten or wrapped. The core
logic and every test survive that, because they operate on files rather than on a runtime.

**Neutral but load-bearing.** The event schema in `src/consilient/events.py` is now a public
interface under ADR-0023's T2 tier. Changing it is a versioned schema change, not an edit.

## Enforcement

- Check: the invariant suite runs in CI on every push and pull request
  (`.github/workflows/invariants.yml`), including the replay invariant against the real
  trajectory — Gate A condition 2 requires it in CI specifically. [measured]
- Check: `test_the_cli_exposes_no_routing_or_blocking_surface` asserts the observe-only CLI
  exposes no command or option whose name implies routing, dispatch, blocking, acceptance,
  gating or escalation. Stage 3 behaviour cannot arrive by accident. [measured]
- Added in the same commit as the code: yes. [measured]

## What would overturn this

- Joe deciding the distribution channel is npm and that a launcher is unacceptable.
- A dependency proving necessary in the core, which would remove the stdlib-only argument and
  reopen the comparison on equal terms.

## Publication candidate?

No. [asserted] This is an ordinary implementation choice with no falsifiable claim attached.


## Correction: 2026-08-20 — the ecosystem-adjacency premise was false and is superseded

This ADR argued in part from the premise that the neighbouring harnesses are Node CLIs. **Local
inspection the following day showed that they are not.** `@openai/codex` is a 7,236-byte Node shim
that spawns a Rust binary — 50.6 MB of Rust against 98 KB of TypeScript — and Claude Code ships
eight platform binaries with zero dependencies. [measured]

ADR-0032 supersedes this record and reaches the same conclusion on independent grounds, so the
decision is unchanged. The premise is corrected here because a false premise that happens to
support a correct conclusion is the most durable kind of error: nothing downstream ever fails in a
way that exposes it.
