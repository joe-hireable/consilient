# 0007. CLI only, and build no review surface

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request ("you decide, argue for it")
- **Inquiry tier reached:** T2 model — the conclusion is forced by `findings.md` §5
- **Executable model:** `../10-research/experiments/simulations.py` (exp 5)

## Context

Q16 asked which single interaction surface v0 should have: CLI, TUI, or local web. The
second half of this ADR — that there should be no review surface at all — is the part that
actually matters, and it is not obvious.

## Decision

**CLI only.** No TUI, no local web server, no desktop app.

**And build no diff-review interface.** Emit to the reviewer the user already has: git
worktrees, branches, pull requests, their editor. The harness's job is to reduce what
reaches the human, not to render it more attractively.

Human verdicts for the β-meter are collected at merge time by a single CLI prompt.

## Evidence

- `[algebra]` The system's ceiling is `n_max = T_agent_cycle / T_effective_review`
  (`findings.md` §5). The tempting inference is "build a great review UI to cut review
  time". **The arithmetic says otherwise:** the lever is the *critic tier* reducing the
  number of diffs reaching the human, not the human reviewing each one faster. Critic recall
  0.85 moves the ceiling from 3.1 agents to 5.1. A better diff view moves it by whatever
  fraction of 8 minutes a nicer renderer saves — and a good diff reviewer is a large,
  undifferentiated project competing with GitHub, which a solo maintainer will lose.
- `[asserted]` The product orchestrates CLI agents (`0001`) and its users therefore live in
  terminals. A CLI is scriptable, pipeable and composable, which is how open-source
  developer tools actually spread.
- `[asserted]` A TUI is a permanent maintenance surface with poor accessibility and no
  pipeability. Local web means a server, a port, an auth question and a second codebase in a
  second language.
- `[algebra]` The one thing that looked like it needed a UI — collecting human verdicts for
  β — is the easiest thing in a CLI. At merge: *accepted as-is? y / n / edited*. One
  keystroke produces exactly the label `0002` requires. `harness verdict` is the entire
  review surface.

## Evidence against

- `[asserted]` A visual surface is how most developer tools acquire non-expert users, and
  the OSS-community strategy (`0004`) depends on adoption breadth. CLI-only caps reach.
  Counter: the target user already runs Claude Code or Codex in a terminal.
- `[asserted]` "Reduce what reaches the human" assumes the critic tier works. If critic
  recall proves low, the ceiling stays at ~3 agents and better review tooling becomes the
  only remaining lever — at which point this ADR should be revisited, not patched.
- No usability evidence of any kind was gathered. This is reasoning from arithmetic and
  priors, not from users.

## Consequences

**Positive.** One codebase, one language, no server, no auth, no port. Scriptable and
CI-embeddable by default. Effort goes to the critic tier, which is where the measured
leverage is.

**Negative.** Caps adoption among developers who want a GUI. Makes the β-verdict prompt the
only human touchpoint, so if that prompt is annoying, β data collection dies and the product
loses its instrument.

**Neutral but load-bearing.** Because output goes to git worktrees and PRs, the harness must
produce artefacts that are *good* in someone else's viewer — clean commits, useful PR
bodies, honest test output. Presentation quality moves into artefact generation.

## Enforcement

- Check: no HTTP server, no bundler, no frontend dependency in `package.json` (or
  equivalent). Asserted by a dependency-allowlist test, same commit (I1).
- Check: every command works non-interactively with `--json`, so nothing depends on a TTY.

## What would overturn this

- Measured critic recall is low enough that the parallelism ceiling stays at ~3 agents, and
  review-time reduction becomes the only lever left.
- The β-verdict prompt proves to have unacceptable completion rates in practice, indicating
  the human touchpoint needs a richer surface.

## Publication candidate?

No.
