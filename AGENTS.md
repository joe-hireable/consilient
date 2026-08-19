# Consilience — agent rules

Universal project rules for any AI coding assistant. `CLAUDE.md` `@`-references this file.

## What this project is

**Consilience** — read [`CONSILIENCE.md`](CONSILIENCE.md) first. It is not background; it is
the source every rule below is derived from.

> "The Consilience of Inductions takes place when an Induction, obtained from one class of
> facts, coincides with an Induction obtained from another **different** class. Thus
> Consilience is a **test of the truth** of the Theory in which it occurs."
> — Whewell, 1840

An open-source **meta-harness**: an orchestrator for agentic work in general — above
existing agents (Claude Code, Codex, opencode, Antigravity CLI, or any other the user
favours), with a native execution path for open models — organised around measuring
**β**, the rate at which automated checks accept a bad artifact. Coding is v0 because it
is the only domain with a cheap automated oracle, so it is where β can be measured; the
architecture itself is domain-blind (see `docs/20-design/architecture-sketch.md`,
"Domain posture", and Q24).

β exists because of Whewell's third clause: convergence is a *test*, and tests have error
rates. The multi-agent constraints exist because of his second clause: **different** class.

**Current phase: pre-approval.** A draft implementation specification exists at
`docs/40-spec/v0-draft.md`, alongside experimental adapters and research instruments.
The draft carries no implementation authority. Research, experiments, ADRs, invariant
checks and specification work are permitted; product implementation is not permitted until
the user explicitly approves the specification or supersedes that gate.

## Working principles for this repo

These are load-bearing. They were derived, not asserted — see `docs/10-research/`.

1. **Claims carry evidence or a confidence label.** Every design claim in `docs/` is
   tagged with its status: `[measured]`, `[simulated]`, `[cited]`, `[asserted]`.
   Never upgrade a tag without new evidence. `[asserted]` is not an insult; it is honest.

2. **Sign and threshold, never point estimates.** Simulations answer "does the answer flip,
   and where?" They do not answer "what is the number?". Do not quote a simulated figure as
   a fact about the world.

3. **A chokepoint without an enforcement rule is not a chokepoint.** The single most
   expensive lesson from `jobboard-v2` (see `docs/30-source-material/prior-repo-assets.md`):
   a documented "unified LLM boundary" fragmented into five access paths because no lint
   rule banned bypass. Any invariant this project declares must ship with the check that
   enforces it, in the same commit.

4. **The Engineering Ratchet.** When something fails, the fix goes in code — a check, a
   type, a constraint — not in a prompt. Once fixed, it cannot regress.

5. **Self-reported model confidence is not a signal.** Use verifier outcomes
   (tests, typecheck, build, human accepted the diff unedited). Never gate on a model's
   claimed confidence score. This is well-documented in the routing literature and was the
   central flaw in the earlier Gemini design session.

6. **Multi-agent needs justification, not enthusiasm.** Whewell's "another **different**
   class" is the test, and there is a theorem behind it (Ao, Gao & Simchi-Levi 2026,
   arXiv:2603.26993): without new *exogenous* signals, a delegated agent network cannot beat
   a centralised decision-maker with the same information. Every proposed multi-agent
   structure must name the different class of facts it introduces. **Agreement between
   agents that share evidence is not consilience — it is echo.**

7. **British English in prose.** Code identifiers stay conventional.

8. **Run it, don't reason about it.** There is an RTX 5090 / 64 GB rig available and
   licences can be bought on request. If a question is answerable by running something
   locally, run it. Local compute is free, and it is what upgrades a claim from
   `[simulated]` to `[measured]`. See `docs/10-research/local-experimentation.md`.

## Boundaries

### Always do
- State assumptions explicitly and label confidence.
- Re-run `docs/10-research/experiments/*.py` before relying on any number in `findings.md`.
- Surface trade-offs when more than one approach is reasonable.

### Ask first
- Writing any implementation code (the project is pre-spec).
- Naming the project.
- Adding a dependency.
- Changing anything in `docs/10-research/` — that's the evidence base.

### Never do
- **Publish anything from `../hireable-3.0` or `../jobboard-v2`.** They are strictly
  private commercial repos, usable as inspiration and as measurement corpora only
  (EXP-01 runs on their histories). Their names and *aggregate measured metrics* may
  appear in docs; their code, file contents, excerpts and detailed file paths may
  never be committed here or included in anything published from here. (Joe,
  19 Aug 2026.)
- Commit secrets or `.env`. `.github/workflows/secret-scan.yml` enforces this against the
  tracked tree and repository history without printing a detected credential.
- Present a simulated figure as an empirical result.
- Add architecture with no falsifiable claim attached to it.
- **Add a structure that cannot be traced back to `CONSILIENCE.md`.** If a proposal does not
  serve provenance, difference-of-class, or measuring the test's error rate, it does not
  belong here.
- Invent terminology. If a concept needs a new name to sound important, it probably isn't
  a concept. (See `docs/30-source-material/gemini-session-critique.md`.)

## The next step is pre-approval convergence

Inspect `docs/10-research/experiment-register.md`, the current ADR index and
`docs/40-spec/v0-draft.md`. Resolve authorised evidence gaps with pre-registered stopping
rules, preserve dissent, and keep the draft specification aligned. Do not cross the product
implementation gate without explicit user approval.
