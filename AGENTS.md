# Consilient — agent rules

Universal project rules for any AI coding assistant. `CLAUDE.md` `@`-references this file.

## What this project is

**Consilient** — read [`CONSILIENCE.md`](CONSILIENCE.md) first. It is not background; it is
the source every rule below is derived from.

> "The Consilience of Inductions takes place when an Induction, obtained from one class of
> facts, coincides with an Induction obtained from another **different** class. Thus
> Consilience is a **test of the truth** of the Theory in which it occurs."
> — Whewell, 1840

An open-source **Agent Command Post** (ADR-0061): you do not ask a model; you ask
Consilient, and it sends **harnesses** (Claude Code, Codex, Cursor, Grok, opencode, or any
other the user favours), with a native execution path for open models when no delegated
harness fits. Organised around measuring **β**, the rate at which automated checks accept
a bad artifact. Coding is v0 because it is the only domain with a cheap automated oracle,
so it is where β can be measured; the architecture itself is domain-blind (see
`docs/20-design/architecture-sketch.md`, "Domain posture", and Q24). Child runtimes stay
*harnesses*. Consilient is not one.

β exists because of Whewell's third clause: convergence is a *test*, and tests have error
rates. The multi-agent constraints exist because of his second clause: **different** class.

**Current phase: Stage 3, entered 20 August 2026.** Joe entered Stage 3 on that date
under ADR-0039, which reserves entry to the principal, recorded in the trajectory as
`stage.entered` authored by him. Routing, blocking and orchestration behaviour may now be
built and run.

**Two things Stage 3 does not authorise, and they are the ones that matter.**

1. **Gate B still governs dependence.** Under ADR-0039, Gate B is no longer a licence to
   *build* orchestration; it is the evidence that the harness is trustworthy to *depend
   on* for work on a repository other than this one. **Gate B is not passed.** Nothing
   here may be pointed at `../hireable-3.0` or `../jobboard-v2`.
2. **Gate A is not passed either.** Do not take the condition-by-condition state from this
   file — run `consil doctor` and read what it says. This paragraph previously listed
   "A1, A2 and B1 pass … B3 needs the fallback exercised", and on 21 August 2026 three of
   those four were wrong: A1 **fails** (EXP-01's stopping rule fired), A2 reports
   **unknown** on a fresh checkout, and B3 **passes**. [measured] `consil doctor` is the
   authority; a hand-maintained copy of its output in a governance file is a second source
   of truth that drifts, which is what happened here. Since 21 August it also **exits
   non-zero** while the gates are shut, so `consil doctor && …` no longer runs the next
   step. `routing_orchestration_enabled` remains `false` — **the flag reports the gates,
   and the gates are not open.** Entering the stage permits the work; it does not pass the
   gates.

**The operator surface is this repository's commands, not a chat window.** `consil` observes
(`record`, `replay`, `beta`, `usage`, `doctor`, `dashboard`). Orchestration is
`python scripts/dispatch.py`. Open a Claude/Codex/Cursor/Grok session to *build* the
harness; to *run* it, type those commands. The skill is
`.agents/skills/operating-the-harness/SKILL.md`.

Product code in `src/consilient/` remains observe-only *today* because routing is not a
`consil` subcommand, not because orchestration cannot be built. Dispatch is a script
(ADR-0058). Gate B still forbids pointing it at another repository.

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
- Pointing the harness at any repository other than this one. Stage 3 permits building
  orchestration; Gate B governs depending on it, and Gate B is not passed.
- Naming the project.
- Adding a dependency.
- Changing anything in `docs/10-research/` — that's the evidence base.

### Never do
- **Publish anything from `../hireable-3.0` or `../jobboard-v2`.** They are strictly
  private commercial repos, usable as inspiration and as measurement corpora only
  (EXP-01 runs on their histories). Their code, file contents, excerpts, detailed file paths
  and **commit identifiers** may never be committed here or included in anything published
  from here.

  What Joe actually said, 19 Aug 2026, was that they **"must not be published as part of this
  repo"** — flat, with no carve-out. The narrower reading that their *names and aggregate
  measured metrics* may appear is **the orchestrator's inference, not the principal's words**,
  and was found signed in his name by an audit on 21 Aug 2026. It is recorded here as inference
  because a loosening filed under the principal's signature is worse than an invented
  tightening, and because this specific carve-out is what let 71 private commit identifiers
  reach a results file. It stands provisionally until Joe adopts or rejects it. **Where the two
  readings disagree, take his.**
- Commit secrets or `.env`. `.github/workflows/secret-scan.yml` enforces this against the
  tracked tree and repository history without printing a detected credential.
- **Put a secret into a public repository, under any circumstances.** Joe's words, 20 Aug 2026,
  were **"no secrets in public repo"**. Everything after this sentence is **the orchestrator's
  reading of that instruction, not his words** — recorded as inference on 21 Aug 2026 after an
  audit found the expansion signed in his name. It is almost certainly what he meant, and it is
  kept because it is the safe direction; but it deleted a gate condition (B3), so he is owed the
  chance to confirm or narrow it.
  The reading: not merely "do not commit one", but do not place one
  in repository settings, Actions secrets, or anywhere the public repository can reach. A
  capability that needs a credential there is not built — **it runs locally or it does not
  run.** Gate B3 is the first thing this rule cost.
- Present a simulated figure as an empirical result.
- Add architecture with no falsifiable claim attached to it.
- **Add a structure that cannot be traced back to `CONSILIENCE.md`.** If a proposal does not
  serve provenance, difference-of-class, or measuring the test's error rate, it does not
  belong here.
- Invent terminology. If a concept needs a new name to sound important, it probably isn't
  a concept. (See `docs/30-source-material/gemini-session-critique.md`.)

## The next step is Gate A

Inspect `docs/10-research/experiment-register.md`, the current ADR index and
`docs/40-spec/v0-draft.md`. Resolve authorised evidence gaps with pre-registered stopping
rules, preserve dissent, and keep the draft specification aligned. Do not cross the product
implementation gate without explicit user approval.
