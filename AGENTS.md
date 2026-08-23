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
   on* for work on a repository other than this one. **Gate B is not passed.** Supervised
   dispatch may `--cwd` into a root the principal has named in the gitignored instance
   file `.harness/allowed-cwds.json` (ADR-0063). That listing does not pass Gate B, does
   not authorise unattended operation, and does not authorise publishing anything from
   those repositories. An unnamed root is still refused. The unattended loop still
   refuses any workspace that is not this repository.
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
(ADR-0058). Gate B still forbids *depending* on it for another repository; instance cwd
allowlisting is ADR-0063 and is not a gate pass.

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

9. **Find the bar, then beat it.** Joe, 21 August 2026: *"In everything we do, and the harness does,
   we should always enforce aiming for better than the best that already exists. That is the bar."*
   And: *"we need to always be finding where the bar is and raising it."*

   **Finding the bar is the work; beating it is the easy half.** Before building a capability, name
   the best thing that already does it — a product, a paper, a library, a competitor — and say what
   it achieves. Then state how this will be better, and **what measurement would show it**. If you
   cannot find an incumbent, say what you searched; "nothing exists" is a claim requiring evidence
   like any other, and it is the claim this project has already got wrong.

   Once found, the bar is not a one-time check. **Record it so it can be re-checked**, because the
   incumbent moves. A bar beaten in August and never re-measured is a bar you have stopped clearing.

   This principle exists because we breached it. `README.md` claimed *"Nothing on the market measures
   it"* while **eight published systems measured β**, including Reflexion in 2023 — and our own
   experiment register already said so on line 1738 while the README contradicted it. [measured]
   That claim was in the public shop window of a project whose entire subject is measurement honesty.

   **Enforcement:** a capability claim in public-facing prose names its incumbent and the evidence,
   or it does not ship. `tests/test_v0_invariants.py` fails a superlative — "nothing", "no one",
   "first", "only" — appearing in public-facing prose without a citation beside it. Beating a bar you
   never located is indistinguishable from not knowing where it was.

10. **Reach for open data and public APIs before reasoning from memory.** Joe, 21 August 2026:
    *"we should encourage the sourcing, downloading, manipulating and utilisation of open source data
    as well... it should be a default practice to use open source data where it might be useful to
    make a decision or build something for a user. Also plugging into public-apis for building stuff
    as well and being able to help users do better than the best existing for anything they ever do."*

    This is not a convenience; it is principle 6 applied. **A public dataset is a different class of
    facts from a model's training**, so an answer derived from data downloaded and run is a genuinely
    independent induction, while an answer recalled from weights is the same class as every other
    answer that model gives. Whewell's test needs two classes, and open data is the cheapest second
    one available.

    It is also how principle 9 is actually done. **You cannot know where the bar is without the data
    that measures it**, and you cannot beat it without something to measure against. EXP-96 pins
    Pallets `itsdangerous` 2.2.0 as a second corpus for exactly this reason.

    In practice: prefer a real dataset over a plausible estimate; prefer a public API over an
    assumption about what it returns; record the source, the licence and the retrieval date, because
    a dataset without provenance is an assertion wearing a number's clothes. **Check the licence
    before use, not after** — a permissive licence is required for anything this project redistributes.

    **Enforcement, stated honestly:** partly enforced, and the gap is real. `evidence_class` on
    trajectory events and the `[measured]`/`[cited]`/`[asserted]` tags already force a claim to
    declare where it came from, and CI checks those. **Nothing yet checks that a question answerable
    from public data was answered that way** — that is a judgement no test currently makes, and until
    one exists this principle binds by discipline, not by machinery.

11. **No definitive answer is not a reason to stop.** Joe, 22 August 2026: *"If we cant get definitive
    answers we need to get to the best estimate and ensure those answers are constantly strived for
    with experimentation. If there are multiple right answers then again, the best of the bunch."*

    Three obligations follow, and they are the ones this project keeps failing:

    **Decide at the best available estimate.** Absence of a measurement is not permission to defer.
    Produce the answer the evidence supports, **tag it honestly** — `[asserted]` is not a failure —
    and carry on. Waiting for certainty is how a gate becomes a wall, which
    `docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md` catalogues at length.

    **Name the experiment that would improve it, in the same breath.** An estimate with no route to
    becoming a measurement is a guess that has stopped trying. That is what `PROVISIONAL` status is
    for, and why it requires a named killing experiment.

    **Where several answers are defensible, choose the best and record why the others lost.** A menu
    handed upward is work not done. The rejected options belong in the record — the trail of
    reversals is the most valuable thing in `docs/decisions/` and the first thing people delete.

    **And when several answers are all acceptable, stop deliberating and build.** Joe, 22 August 2026:
    *"Sometimes especially in tech there is multiple different 'best' ways... as long as it's built
    with bricks or metal or obsidian or hardened and treated thick wood blablabla then you should pick
    one and start building with the best fit you can find."* This is a satisficing rule **with a
    floor**, and the floor is the whole of it: wet sand is refused, brick and steel are
    interchangeable. **So spend the analysis on locating the floor — what distinguishes wet sand from
    brick here — and almost none on ranking the materials above it.** Deliberation past the point of
    an acceptable answer is waste that looks like rigour.

    This does **not** license upgrading a tag without evidence, and it does not license presenting an
    estimate as a measurement. Principle 1 still binds: `[asserted]` stays `[asserted]` until
    something is run. **Deciding under uncertainty and pretending to certainty are opposites, not
    neighbours.**

    **Enforcement:** `tests/test_v0_invariants.py::test_provisional_adrs_name_a_live_experiment` fails
    when a `PROVISIONAL` ADR names no experiment, or names one absent from the register. A decision
    that admits it is provisional and offers no way out is the failure this principle exists to stop.

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
- **Publish a user's private harvest.** `.harness/training/` and any `--out` dest of
  `scripts/harvest.py` is instance data under ADR-0057; never track or publish it.
- **Publish anything from `../hireable-3.0` or `../jobboard-v2`.** They are strictly
  private commercial repos, usable as inspiration and as measurement corpora only
  (EXP-01 runs on their histories). Their code, file contents, excerpts, detailed file paths
  and **commit identifiers** may never be committed here or included in anything published
  from here.

  What Joe actually said, 19 Aug 2026, was that they **"must not be published as part of this
  repo"** — flat, with no carve-out. An orchestrator later narrowed that to permit their *names and
  aggregate measured metrics*, and filed the narrowing under the principal's signature. An audit on
  21 Aug 2026 found it, and it is what let 71 private commit identifiers reach a results file.

  **Joe rejected that carve-out on 23 August 2026.** His flat words stand: nothing from those
  repositories is published as part of this repo, including their names and including aggregate
  metrics. Where any earlier document relies on the carve-out, the flat reading wins.

  This paragraph is kept rather than deleted because the trail matters more than the tidiness: a
  loosening filed under someone's signature is the failure worth remembering, and deleting the
  record of it would be the second half of the same mistake.

  **One boundary the rejection does not settle, flagged rather than inferred.** The two repository
  names appear in this file and in others, because a prohibition cannot be stated without naming
  what it prohibits. Reading the rejection to forbid the names outright would make the rule itself
  unwritable. The orchestrator has therefore **not** scrubbed them, and is recording the question
  instead of answering it: does the rejection forbid their *names* everywhere, or their *contents,
  metrics and identifiers* while permitting the names where the prohibition itself is stated?
  Until Joe answers, the names stay only where a rule or a boundary requires them, and nothing
  else from those repositories appears anywhere. **Inferring the wider reading silently is the
  exact failure this correction exists to undo.**
- Commit secrets or `.env`. `.github/workflows/secret-scan.yml` enforces this against the
  tracked tree and repository history without printing a detected credential.
- **Put a secret into a public repository, under any circumstances.** Joe's words, 20 Aug 2026,
  were **"no secrets in public repo"**. An orchestrator expanded that into a broader rule and filed
  the expansion in his name; an audit on 21 Aug 2026 found it and relabelled it as inference.

  **Joe adopted the expansion on 23 August 2026**, so it is now his instruction rather than a
  reading of it: not merely "do not commit one", but do not place a secret in repository settings,
  in Actions secrets, or anywhere the public repository can reach. A capability that needs a
  credential there is not built — **it runs locally or it does not run.**

  Gate B3 was the first thing this rule cost, and it stays deleted. That price was paid knowingly.
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
