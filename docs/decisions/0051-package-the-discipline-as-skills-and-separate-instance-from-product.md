# 0051. Package this project's discipline as skills, keep agent files as wiring, and separate instance configuration from product

- **Status:** PROVISIONAL
- **Date:** 2026-08-21
- **Deciders:** Claude Opus 5, under Joe Brown's instruction of 21 August 2026
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — there is no decision variable, objective and unknown parameter to
  name here. This is a placement rule, not a threshold. ADR-0014 set the same precedent.

## Context

Joe asked for more skills and dedicated agents across all harnesses, and was explicit about
method: *"first finding the best fit existing skills that are popular and proven and then
optimising them for our codebase and with our logic from all consilient conversations"*. He asked,
in the same instruction, for *"clear differentiation between building the actual consilient
harness project and configuring it for me to work with as the first user"*.

Two forces make this a decision rather than an obvious call.

**Agent files are not portable and skills nearly are.** Four runtimes are in use here. Only Claude
Code reads `.claude/agents/`; Codex, Cursor and Grok CLI read `AGENTS.md`. `.agents/skills/` is a
Codex/Copilot/Gemini-CLI-side path that Claude Code's own documentation never mentions `[cited]`.
So anything load-bearing placed in an agent definition is invisible to three quarters of the
fleet, and the repository would acquire a rule that most of its agents cannot see — the
`jobboard-v2` shape, arriving through file layout rather than through code.

**A first user's configuration is publishable, and a stranger's fork must not depend on it.** The
repository is heading for a public remote. Subscriptions, machine repair steps and runtime rosters
are useful to exactly one person, and mixing them into `docs/` makes every reader guess which
rules apply to them.

## Decision

Behaviour-changing procedure is written as a **skill** under `.agents/skills/<name>/SKILL.md`,
mirrored into `.claude/skills/` by symlink. Five are added: `measuring-beta`,
`running-experiments`, `adversarial-audit`, `pre-publication-gate` and `dispatching-workers`.
Each is adapted from a proven public collection and carries an *Adapted from* section naming the
source and its licence, and a *Harness support* section naming its portable core.

**Agent definitions carry no rule of their own.** `.agents/agents/<name>.md`, mirrored at
`.claude/agents/`, states which skill the agent follows and adds only isolation, tool limits and a
report shape. Three are added: `consilient-auditor`, `consilient-gate`, `consilient-worker`.

**Instance configuration lives in `instance/`**, contains no secret and no absolute machine path,
and may never be load-bearing: deleting the directory must leave the repository building and
sensible. Anything that genuinely requires a machine path is written outside the repository.

## Evidence

- `[measured]` A clone with `core.symlinks=false` — Git for Windows' default without developer
  mode — checks `.claude/skills` out as a 17-byte text file. This repository was in that state on
  21 August 2026: mode 120000 in the index, `skills-mirror.yml` green on its Linux runner, and
  **no project skill loadable in Claude Code on the principal's machine.** The mirror check could
  not see it, because the defect is in the checkout rather than in the tree.
- `[measured]` `check_record_numbers.py`, written with this ADR, immediately found three live
  duplicate identifiers — `EXP-56`, `EXP-57` and `EXP-58` in the register. R15 specified this
  exact check on 20 August and closed by asserting that all fifteen requirements "now have a
  check". This one did not, and the duplicates it names were still present.
- `[measured]` A first draft of that check also scanned `docs/decisions/index.md` for repeated
  rows, and flagged `0027` — the defect C3 reports. Inspection showed `0002` and `0027` each
  appear once in the curated "load-bearing four" section and once in their topical table, which
  is index cross-listing, not an identifier collision. **C3 is partial on that point**, and the
  first draft of the check would have shipped a false positive into CI. The scan was narrowed to
  duplicate ADR filenames, which is the actual invariant.
- `[measured]` The material each skill encodes is this repository's own incident record: R1, R11,
  R13 and R15 in `docs/20-design/dispatch-layer-requirements-2026-08-20.md`; the six defects in
  `docs/00-context/corrections-2026-08-21.md`; the two leaks in
  `docs/00-context/publication-blocked-2026-08-21.md`; and the four β defects recorded in
  `src/consilient/beta.py`.
- `[cited]` `AGENTS.md` is a cross-harness standard stewarded by the Agentic AI Foundation and
  read natively by Codex, Cursor, Copilot, Gemini CLI and others; it carries no schema. Claude
  Code reads only `.claude/`. That is the whole argument for keeping rules in `AGENTS.md` and in
  skills, and out of agent files.
- `[cited]` Outside Claude Code, the Agent Skills specification permits exactly six frontmatter
  keys: `allowed-tools`, `compatibility`, `description`, `license`, `metadata`, `name`. The two
  existing skills here use `name` and `description` only; the five new ones match, so they remain
  packageable.
- `[cited]` `obra/superpowers` (MIT) reports head-to-head wording tests in which a prohibition
  list produced *more* of the unwanted behaviour than a positive recipe. The new skills state
  refusals and recipes rather than bare prohibitions for that reason.
- `[cited]` `wan-huiyan/agent-review-panel` (MIT) independently derived *"consensus does not
  compound on a shared artifact"* from its own production failures — the same conclusion as
  `CONSILIENCE.md`'s echo rule, reached from a different class of evidence.
- `[asserted]` The five chosen skills are the highest-value five. Three candidates from
  `.agents/skills/README.md`'s own list were folded into others, and one was cut outright.

## Evidence against

**Nothing here has been measured to change an agent's behaviour, and that is the load-bearing
gap.** The `skill-creator` skill in `anthropics/skills` (Apache-2.0) ships the obvious instrument
— run the same task with and without the skill, in parallel, and grade blind. It was not run.
Every claim that these skills change an outcome is `[asserted]`, which is why the status is
PROVISIONAL.

**The author has a conflict of interest.** This ADR was written by the party that wrote the
artefacts it approves, in the same session, and no auditor of a different family has read them.
That is precisely the arrangement `adversarial-audit` — one of the artefacts — declares invalid.
Flagging it does not fix it.

**Adding files may be the wrong direction for this project's real bottleneck.** Joe's review time
is the constraint. Eight new documents plus a script are eight more things he must read, against
an unmeasured saving. `.agents/skills/README.md` already warned that *"an unused skill is context
cost with no benefit"*, and five of these are unused today.

**`instance/` may be the wrong shape.** A directory implies future files; if it stays a single
README, a section in an existing document would have been cheaper. It is kept because the split
was asked for explicitly and a directory makes the boundary checkable — but the simpler
alternative was real, and is recorded here rather than argued away.

**Three of the four adapted sources are MIT and one is Apache-2.0**, the latter requiring that
changed files be marked. Nothing is copied verbatim — only structure and named techniques are
adapted — which is why attribution sits in an *Adapted from* section rather than a licence header.
If a later change copies text, that judgement has to be revisited. A fifth candidate collection,
`hesreallyhim/awesome-claude-code`, is CC BY-NC-ND 4.0 and was deliberately not drawn on at all.

I searched for prior art on skills encoding *experiment pre-registration* specifically and found
none with evidence of adoption. That is absence of evidence, not evidence of absence.

## Consequences

**Positive.** A rule now has one home per audience: `AGENTS.md` for what every runtime must know,
a skill for procedure, a check for an invariant, an agent file for wiring. The four-family audit
method becomes dispatchable rather than remembered. `check_record_numbers.py` closes the first of
R15's two checks and is already reporting real defects.

**Negative.** Eight artefacts to keep current, and stale guidance is worse than none — the C3
defect was exactly a stale index. `.agents/skills/README.md` is now the inventory, and it will
drift if a new skill lands without updating it. The symlink scheme also stays fragile on Windows
in a way CI structurally cannot detect.

**Neutral but load-bearing.** Agent definitions are now permanently second-class: a rule may not
be introduced in one, so any future agent needing a rule needs a skill first. And `instance/`
constrains what may be written where, for every later contributor.

## Enforcement

- Check: `.github/workflows/skills-mirror.yml` — both `.claude/skills` and `.claude/agents` must
  be symlinks resolving into `.agents/`. Fails CI: **yes**. Added in the same commit: **yes**.
- Check: `.github/scripts/check_record_numbers.py` — no duplicate `EXP-NNN` heading
  or ADR filename. Carries a `--self-test`, matching `check_secrets.py`. Fails CI: **not
  yet** — it currently reports three pre-existing duplicates whose repair is a change to
  `docs/10-research/`, which `AGENTS.md` reserves to the principal. It joins the invariants
  workflow when those four are resolved; until then it runs as a manual gate alongside
  `check_private_corpus.py` and `check_foreign_identifiers.py`. Added in the same commit: **yes**.
- Not enforced by a check, and named as such: that agent files carry no rule of their own. It is a
  placement convention. If it is violated twice, it needs a lint rather than a reminder.

## What would overturn this

- The with-skill/without-skill A/B, graded blind, showing no difference in outcome on this
  repository's own tasks. **That experiment is not registered here and carries no number**,
  because identifiers are allocated by the dispatcher and not by the agent that wants one — R15,
  and the rule stated in `running-experiments`. Whoever runs it takes the number from their brief.
- A different-family auditor finding that one of these skills states a rule no check enforces,
  which would place it in the class ADR-0014 forbids.
- Claude Code gaining native `.agents/` support, which would make the mirror and its Windows
  failure mode unnecessary.

## Publication candidate?

**No.** The placement convention is local. The one finding a stranger might want — that a
symlinked skills mirror silently loads nothing on a default Windows clone while CI stays green —
is a paragraph in someone else's documentation, not a paper.

## Reversal

`git revert` this commit, then `rm -rf .agents/agents instance` and
`git rm --cached .claude/agents`. Nothing outside the added paths is modified except
`.agents/skills/README.md` and `.github/workflows/skills-mirror.yml`.

## Falsifier

If, over the next twenty dispatches, a worker briefed with `dispatching-workers` returns the same
rate of unusable results as one briefed without it, then these skills are decoration and this
decision is wrong. The measurement is cheap, and nobody has taken it.
