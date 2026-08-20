# Cross-family audit, 20 August 2026 — what a different model family found

Every document in this repository was written by Claude. Auditing them with Claude measures
consistency, not correctness. `CONSILIENCE.md`'s second clause and `AGENTS.md` principle 6 both
say the same thing: agreement between agents that share evidence is echo. EXP-16 recorded the
same limitation about itself — *"All 96 agents share one model family. Cross-arm agreement may be
shared prior, not robustness."* [measured]

So overnight on 20 August the 39 ADRs and the specification were handed to **Cursor
(Gemini 3.7 Flash)**, on a snapshot staged outside the repository so it could not write to it. It
returned ten findings. This file records what survived checking, what did not, and what only Joe
can resolve. [measured]

**Every finding below was verified against the repository by hand before being recorded here.**
An auditor's confidence is not evidence.

---

## Applied — two of these were introduced by this project the same night

### 1. The approved specification contradicted itself about ADR-0003
`docs/40-spec/v0-draft.md` § 2 said *"EXP-07 has reopened ADR-0003"*; § 8, updated hours earlier
on 20 August, said it was **not** reopened. Both sentences were in the approved specification at
once, and the second was written by the agent that failed to check the first. [measured] § 2 now
carries the n=30 result. **Fixed.**

### 2. ADR-0016 published to npm; ADR-0032 chose Python
ADR-0016 § 2 said *"ship `skills/` inside the `consilience` package. `npm i consilience`"*. That
was correct when the orchestrator was assumed to be a Node CLI. ADR-0032 chose single-language
Python on 20 August and nobody revisited ADR-0016, so the decision record told the project to
publish its skills through a package manager it does not use. [measured] The reasoning was sound
and is unchanged; only the vehicle was wrong. **Fixed.**

This is the second-order cost of a fast supersession, and it is worth naming: ADR-0032 was
written carefully, with an "Evidence against" section, and it still left a live contradiction in
a file it never mentioned. A supersession is not finished when the new ADR is good; it is
finished when every ADR that depended on the old premise has been visited.

### 3. An invariant the shipped code deliberately does not implement
V0-02, ADR-0015 Gate A condition 2 and ADR-0006 all require *"byte-identical state"* after
delete-and-replay. **SQLite files are not byte-stable.** The header carries a change counter and
a schema cookie, the freelist and page allocation depend on insertion history, and WAL adds a
random salt. [cited]

The shipped code already knew this: `projection.state_digest()` hashes a canonical ordered dump
of the rows, precisely because the file itself cannot be compared. So the documents specified an
invariant the code correctly refused to implement, and the check that exists is *better* than
the one written down. [measured] The specification is corrected here; ADR-0006 and ADR-0015 were
held by other writers at the time and are corrected separately.

This is principle 3 inverted and worth keeping as a case: the usual failure is a documented
invariant with no check. This was a documented invariant whose real check was stronger than the
document, which is a happier failure and just as much drift.

---

## Gated on Joe — a live contradiction about money that no agent may resolve

### 4. ADR-0019 forbids standing spend authorisation. Four later documents assume it.

ADR-0019 is explicit, and it names itself as preferential and reserved:

> *"**Per-transaction permission.** Every spend is approved individually, with the amount, the
> provider and the purpose stated before approval is requested."*
> **What this explicitly forbids:** *"Standing authorisation for a class of purchases. Approval
> is per transaction, not per category."*
> **Consequence:** *"Unattended runs cannot acquire paid capabilities. Some tasks will simply
> stop and wait."*

ADR-0026, ADR-0028, ADR-0033 and `v0-draft.md` § 7.2 all assume the opposite: unattended metered
routing under standing per-task and per-period caps, with ADR-0033 defining the interrupt
condition as *"money leaving an account, or metered spend beyond an authorised cap"* — which
permits autonomous spend **up to** a pre-authorised cap. [measured]

Both cannot hold. And ADR-0019 anticipated exactly this: its own "Evidence against" section
records *"Per-transaction approval breaks unattended operation, which is much of the point"* and
marks the question **Unresolved**. It has stayed unresolved while four later documents quietly
assumed a resolution. [measured]

**This is not an agent's decision.** ADR-0019 says only Joe may overturn it, and it is preferential
— no experiment bears on it. It is also the reason the OpenRouter screening sweep is still
blocked: a provider-enforced cap is precisely the standing authorisation ADR-0019 forbids.

**What Joe has to choose:**
- **(a)** ADR-0019 stands. Unattended runs cannot spend, the OpenRouter arm of EXP-30 is dead as
  designed, and ADR-0026/0028/0033 must be corrected to say so.
- **(b)** ADR-0019 is superseded by a new ADR permitting standing caps under stated conditions —
  provider-enforced, numeric, per-period — and the four documents become consistent with it.

Option (b) is what the project has been behaving as though it chose. That is the worst of the
three states, because it is unrecorded.

### 5. ADR-0030 reinstates a management layer ADR-0010 cut, and says `Supersedes: none`

ADR-0010's own table cuts *"Governance layer of role-played executives — None — Echo — cut"* and
*"Planner → implementer handoff — No — Echo"*. `v0-draft.md` § 2 restates it: admitting executive
titles as roles *"would reinstate the governance layer ADR-0010 cut and would require an ADR
superseding it rather than an edit."* [cited]

ADR-0030 then defines `senior_orchestrator` → `middle_manager` → bounded workers, and its header
reads `Supersedes: none`. [measured]

**The honest position is narrower than Cursor's finding.** ADR-0030 is careful in a way the
finding does not credit: it states these are *"work roles, not identities, personalities,
credentials"*, and a middle manager receives only a bounded delegated objective. And its
`middle_manager` candidate is `google/gemini-3.7-flash` — a genuinely different model family from
the `senior_orchestrator`'s Opus 5, which is arguably a different prior and therefore a different
class.

**But "arguably" is the problem.** ADR-0010's rule is that the different class must be *named*,
not inferred by a reader. ADR-0030 does not name it, and it claims to supersede nothing while
touching the exact structure ADR-0010 cut. Either it names its exogenous class and says why the
delegation theorem does not bite, or it supersedes ADR-0010 explicitly. Both are honest; silence
is not.

**Gated on Joe** because EXP-16 stopping rule 1 is parked on his blind grading, and that grading
decides whether hierarchical structure survives at all. Resolving ADR-0030 before that answer
would be deciding the question the experiment exists to answer.

---

## Recorded, lower severity

- **ADR-0007 forbids a TUI or any interactive surface; ADR-0024 specifies consent dialogs with
  "equal visual weight" and previews before send.** A `--json` non-interactive CLI cannot render
  equal visual weight. ADR-0024's mechanisms need restating as CLI mechanics — a `preview`
  subcommand, explicit flags — or ADR-0007 needs to give ground. Under a non-TTY run, ADR-0024's
  *"silence is a decline"* rule also silently declines everything, which may be the right default
  but is currently an accident rather than a decision. [measured]
- **ADR-0014's enforcement clause is not writable as a lint rule.** It requires *"a skill
  containing an imperative that maps to an existing CI check is a lint error."* Deciding whether
  an arbitrary English sentence maps to an existing check is a semantic judgement, not a static
  analysis. [asserted] This is principle 3 failing in its own enforcement section, which is the
  most embarrassing place for it to fail. Either the check becomes a machine-readable annotation
  the skill must carry, or the clause is honestly downgraded to a review guideline under
  ADR-0023.
- **EXP-31's unobservable stopping rule** was found independently, matching what the internal
  sweep recorded at § P8. Two model families finding the same defect from different starting
  points is the first genuine consilience event this project has recorded about itself. [measured]

---

## Rejected — one finding, and the reason matters more than the finding

Cursor's **Finding 1** claimed that `src/consilience/`, the tests, the CI workflow and every
benchmark figure in ADR-0031 and ADR-0032 were *"phantom assertions tagged `[measured]` with zero
backing artefacts"*, on the strength of *"an exhaustive filesystem scan of the repository"*.

That code exists. The scan was exhaustive over the **snapshot it was given**, which contained
`docs/` and three root files and no `src/` at all — because the staging step copied only `docs/`.
The auditor reported absence from a corpus that had been silently truncated, and reported it with
high confidence and specific line numbers. [measured]

**The error is the orchestrator's, not the auditor's.** But the lesson belongs to the product,
because this harness will do exactly this to its own agents:

> **An agent given a partial corpus will report absence as a finding, and absence is the one
> claim a partial corpus cannot support.** Any dispatch that scopes an agent's view must state
> the boundary of that view inside the task, and any finding of the form "X does not exist" from
> a scoped agent must be treated as unevaluable rather than as evidence. [asserted]

That belongs in the admission boundary as a rule about *dispatch*, not about models. The
re-run was given an explicit boundary note and an instruction never to report absence.

**What would overturn it:** a scoped agent correctly establishing absence within a corpus whose
boundary it was told, which is a different and legitimate claim.
