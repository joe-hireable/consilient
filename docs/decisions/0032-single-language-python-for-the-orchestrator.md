# 0032. Single-language Python for the orchestrator — supersedes 0031

- **Status:** ACCEPTED
- **Date:** 2026-08-20
- **Deciders:** Claude Opus 5 (technical authority delegated by Joe Brown, 20 Aug 2026)
- **Supersedes:** [0031](0031-implement-v0-in-python-with-a-stdlib-only-core.md), which reached
  the same answer for weaker reasons and left the distribution question open
- **Inquiry tier reached:** T3 measure — nine independent lenses plus six local measurements
- **Executable model:** none.

## Context

ADR-0031 chose Python overnight on a reversibility argument, and named the npm reservations
as its strongest unresolved objection. Joe asked for a proper assessment and delegated the
decision. Nine analysts worked disjoint lenses — shipped tools, distribution, security,
component workload, polyglot cost, an adversarial steelman, agent effectiveness, verifier
strength and developer experience — against seven candidates. Six further facts were measured
locally.

## Decision

**The orchestrator is written in Python, as a single language.** TypeScript and Node remain a
**sidecar we spawn**, which is already the status quo, not a second in-repo language.

Three practices are adopted with it, because two of them close the only real gap the
assessment found:

1. **`mypy` is a CI gate**, running before the tests. Already shipped.
2. **Closed sets are `Literal` types with `assert_never` exhaustiveness.** Measured: mypy
   accepts an exhaustive match, rejects a non-exhaustive one *naming the missing case*, and
   rejects a widened `str`. This is the discriminated-union property TypeScript was thought
   to win uniquely.
3. **`basedpyright` is the language server**, not Pylance, so the toolchain is unencumbered
   in every editor.

## Why, in the order the evidence actually weighed

**1. Eight of nine lenses rated Python a strong fit, including the steelman hired to destroy
it.** Its verdict, quoted because the honesty matters: *"Wins on evidence, not by default —
though the incumbency was lucky rather than reasoned."* [cited] ADR-0031 was a lucky guess;
this one is not.

**2. The ecosystem-adjacency argument for TypeScript is factually false.** [measured] The
harnesses Consilience orchestrates are not Node applications. `@openai/codex@0.148.0` is a
7,236-byte Node shim that spawns a Rust binary; the repository is 50.6 MB Rust to 98 KB
TypeScript. `@anthropic-ai/claude-code` declares `dependencies: []` and ships eight platform
binaries; on this machine it is a 330 MB executable with no Node involvement. `opencode-ai`
is the same pattern. All three moved their real code out of JavaScript and left a shim.
**npm is a distribution channel, not a runtime**, and copying the shim is free while copying
the codebase is not.

**3. The distribution objection does not survive measurement.** [measured] `uv tool install
consilience`: 0.775 s cold, 655 KB, one package, and uv bootstraps Python itself, so the
prerequisite is nothing. One `py3-none-any` wheel serves every OS and both sides of the
WSL boundary — two release artefacts against 18–19 for a compiled core, and 88 lines of CI
against roughly 1,000. PyPI moved 43.3M `pre-commit` and 49.2M `uv` downloads in the week to
18 August 2026. aider's official installer is literally the uv installer. If a single binary
is ever demanded, the stdlib-only core already produces a 52 KB zipapp, measured tonight.

**4. The specific combination proposed — TypeScript plus Python — is the worst option on the
board.** [cited] Li et al. measure the JavaScript–Python pair at a 20.66% bug reopen rate,
the worst combination they report. A second in-repo language would also duplicate the event
schema that all 27 invariant tests currently guard from one definition.

**5. Security favours Python here, and npm is actively hostile.** [cited] Shai-Hulud 2.0 had
compromised 700+ packages and 487 organisations' secrets through preinstall hooks. Publishing
an orchestrator that holds subscription credentials into that registry converts an inherited
risk into an owned one. Python's runtime dependency count is zero, wheels execute nothing at
install, and PyPI's defences — mandatory publish 2FA, trusted publishing, default-on PEP 740
attestations — are at least npm's equal.

**6. No component has a performance or memory-safety requirement Python fails.** [measured]
Replay runs at ~100,000 events/second; a million events, decades of solo work, replays in
10.3 s. Startup is 51 ms, and **26.7 ms bare against Node's 32.5 ms — Python starts faster**.
Thirty-two concurrent subprocesses are supervised in 0.56 s against 16 s serial, because the
workload is process supervision and the GIL is released on I/O. Model inference runs
out-of-process in Ollama.

**7. Python leads on the failure mode that actually dominates.** [measured] SWE-PolyBench
identifies mislocalisation, not code generation, as the principal agent failure mode, and
Python leads file-retrieval recall by 9.3 points and precision by 12.5. That is also the
failure a harness can attack directly.

## Evidence against, including the case I found most persuasive

- **The strongest argument for a typed language is the Idris result, and it is real.** [cited]
  GPT-5 solved 39% of Idris tasks zero-shot against 90% of Python — a 51-point deficit — and
  a compiler-in-the-loop harness feeding diagnostics back over 20 iterations reached 96%,
  above Python's own zero-shot baseline (arXiv:2602.11481). A strong static check can convert
  a capability deficit into an advantage, and Consilience is exactly that kind of harness.
  **The reason it does not decide this:** the same lens records that there was *no Python arm
  at matched iteration count*, so "typed language with a loop beats Python with a loop" is
  not established. It shows the loop is powerful, not that the language must change.
- **Per-language agent benchmarks disagree with each other more than they disagree about
  languages.** [measured] Multi-SWE-bench 2025 puts Python at 52.2% and TypeScript at 2.2%,
  a 23× gap; SWE-bench Multilingual puts Rust highest at 58.14%; ProMax at COLM 2026 finds no
  stable ordering and attributes variance to training data rather than language difficulty.
  Decisively for a meta-harness: the same model on the same TypeScript instances scores 2.23%
  or 11.16% depending only on the scaffold — **scaffold variance is the same order as language
  variance**, which is an argument about what this project builds, not about what it is
  written in.
- **Type-constrained decoding is real and TypeScript-specific.** [cited] It reduces
  compilation errors by more than half (arXiv:2504.09246). The widely repeated "94% of LLM
  compilation errors are type errors" does **not** verify against that paper and is recorded
  here as secondary reporting, not as fact.
- **Pylance is licence-locked to genuine Microsoft VS Code**, and this maintainer supervises
  agents from Cursor, Antigravity, Claude Code and opencode, where it may not legally run.
  [cited] That is a real wound. It is healed by `basedpyright`, which was installed and run
  tonight: 1.0 s over the core, and *stricter* than mypy — 14 errors and 155 warnings where
  mypy reports none. Triaging those 14 is follow-up work, and may find more defects.
- **This decision keeps a codebase that ships its strongest check as opt-in.** `tsc` and
  `rustc` are not optional; `mypy` is. That is mitigated by making it a CI gate, but the
  mitigation is a policy rather than a property of the language, and a policy can be removed.
- The assessment was commissioned and synthesised by the same agent that made the original
  choice. Q19's rule applies: the party that produced the material cannot certify what it
  missed. The steelman lens was included to counter this and failed to overturn the answer,
  which is evidence but not proof.

## Consequences

**Positive.** No rewrite, no second toolchain, no release matrix, no duplicated schema. The
entire research-instrument corpus — every EXP — remains in the same language as the product
that will consume it.

**Negative.** The strongest available static check in this ecosystem is weaker than `tsc
--strict` or `rustc`, and remains opt-in. If the type-constrained-decoding advantage proves
large for agent-authored code specifically, this decision costs real quality.

**Neutral but load-bearing.** "Multi-language where each part suits it" is rejected as a
default posture. A second language now needs a measured trigger, named below.

## Enforcement

- Check: `mypy src/consilience` runs in CI ahead of the test suite, and fails the build.
  Shipped in the same commit as the rule. [measured]
- Check: `test_the_cli_exposes_no_routing_or_blocking_surface` already constrains the CLI
  surface; the exhaustiveness pattern is enforced by the type check, not by review.
- Rule: a second in-repo language requires a new ADR citing a **measured** trigger from the
  list below. Enthusiasm is not a trigger.

## What would overturn this

Each is a measurable trigger, fixed here before any of them is observed:

1. **A hot path appears.** Any component measured above 25% of a user-perceptible budget in
   Python. Current headroom is three to four orders of magnitude; at the maintainer's event
   rate the replay trigger cannot fire for over a decade.
2. **A sandbox requirement appears** that OS primitives cannot satisfy from Python — the one
   genuine memory-safety-adjacent component in the roadmap.
3. **A matched-iteration comparison** shows a typed language beating Python at equal agent
   loop count on this project's own evaluation set. That is the experiment the Idris paper
   did not run, and it is the honest way to settle the point.
4. **`mypy` plus `basedpyright` prove unable to express an invariant** the system needs, after
   the exhaustiveness pattern has been genuinely tried.
5. **A distribution failure in practice** — strangers reporting they could not install it.

## Publication candidate?

No. [asserted] This is an implementation choice. The *method* — nine disjoint lenses, an
adversarial steelman against the incumbent, and local measurement of every performance claim
— is more interesting than the answer, and belongs in a practitioner note if anywhere.
