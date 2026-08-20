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

## Round two — the auditor was pointed at the code, and found the oracle forgeable

The first pass audited documents. The second staged `src/consilience/`, the test suite, the
CI workflow, the specification and the ADRs, with an explicit boundary note, and asked one
question of each numbered invariant: **would its check actually catch a violation, and is
there a second path to the same state?** That is the `jobboard-v2` question — a documented
"unified LLM boundary" fragmented into five access paths because no rule banned bypass, and
it is why working principle 3 exists. [cited]

Three defects, all confirmed by hand against the code before anything was changed, all now
fixed with tests. [measured]

### V0-18 was bypassable, and the thing it guards is β's oracle

**This is the most serious defect this project could have had.**

`_check_human_authority()` returned immediately unless `data["human_decision"]` was present.
But `projection._apply_outcome()` read `data["human_verdict"]` straight off an
`attempt.outcome` event and wrote it into the `outcomes` table — the table `beta.compute()`
reads. `HUMAN_ONLY` contained `"verdict"` all along; the constant was simply never consulted
on that path. [measured]

So this event validated, projected, and moved β:

```json
{"v":1,"ts":"...","event":"attempt.outcome","actor":"claude-code-agent",
 "data":{"task":"t1","verifier_accept":true,"human_verdict":"accept"}}
```

β is *defined* as the rate at which automated checks accept an artefact **the human
rejected**. If an agent can author the human verdict, β is not a measurement of anything —
it is the agents grading themselves, which is the echo failure `CONSILIENCE.md` exists to
name, arriving through the data layer rather than through a meeting.

**Why no test caught it.** The test fixture built outcome events with `actor="agent"` and a
`human_verdict` attached, and every test passed. The fixture could express the forbidden
state, so the suite had been taught to accept it. That is worth more than the bug: **a
fixture that can construct a state the invariant forbids will train the suite to permit
it.** [asserted] The helper now authors verdicts as the principal, with `via`, and five
tests assert the forgery paths are closed while the legitimate path still works.

### Gate A condition 2 was satisfied by a check that could not fail

`cmd_replay` built the projection from the log **twice** and compared the two rebuilds. Two
rebuilds from one log are identical by construction. Worse, `projection.build` unlinks the
database first — so any drift the check existed to detect was destroyed before the
comparison it was meant to feed. [measured]

ADR-0015 records Gate A condition 2 as **satisfied**. It was satisfied by a tautology.

`replay` now digests whatever state is on disk, rebuilds, and compares the two. Where there
is no prior state it reports `compared: false` and `identical: null`, because **a check that
did not run must not report a pass** — and CI now builds the projection before replaying, so
the comparison has a subject. On the real trajectory it reports `compared: true`,
`identical: true` over 51 events. [measured] A new test drifts the database out of band and
asserts the divergence is caught, which the old implementation could not do at all.

### A measured β could be constructed with no evidence behind it

`Beta.__post_init__` asked only whether `point` and `interval` were *present*. A `measured`
verdict could carry zero rejections, a rate outside [0, 1], an inverted interval, or a point
outside its own interval, and would render without complaint. `compute()` enforced the
sample floor, but **a floor is not an invariant if the constructor beneath it does not
hold** — and `compute` also took a `min_rejections` argument that could lower it. [measured]

The constructor now enforces the floor and the arithmetic, and `min_rejections` may only be
raised, never lowered. A knob that can lower an evidence floor is a bypass path around it.

### What this says about the method, which matters more than the three fixes

All three were found by a **different model family reading code Claude wrote**, in about
twelve minutes, after Claude's own 40-test suite passed and `mypy --strict` was clean.
Neither the tests nor the types could find them, because both were written by the author of
the defect and inherited its blind spots. [measured]

That is Whewell's second clause doing real work on this project's own artefacts, and it is
the first time the case for difference-of-class here rests on something measured rather than
asserted. It also sharpens what the harness should do: **the auditor must not share an author
with the artefact, and must be pointed at the invariant rather than at the diff.** Asking
"would this check catch a violation, and is there a second path" found three holes; asking
"review this code" would very likely have found none.

**What would overturn it:** a cross-family audit that returns only false positives, or a
same-family audit that finds defects of this severity. One run of each is not a rate.

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


---

# Four corrections from an audit of this document

The same GPT family that audited the repository was pointed at **these findings** instead. Four
of its objections hold. Each is against me.

## 1. My forged event does not move β — the demonstration was wrong, the hole was not

I wrote that this event *"validated. That projected. That moved β."*

```json
{"event":"attempt.outcome","actor":"claude-code-agent",
 "data":{"task":"t1","verifier_accept":true,"human_verdict":"accept"}}
```

The first two clauses are right. **The third is false.** `compute()` takes its denominator from
rows where `human_verdict == "reject"`:

```python
rejected = [r for r in selected if r.get("human_verdict") == "reject"]
n = len(rejected)
false_accepts = sum(1 for r in rejected if r["verifier_accept"])
```

An **accept** row changes neither `n` nor `k`. It can only widen the reported observation window.
[measured]

**The vulnerability was real and is unchanged**: an agent could author a human verdict, and V0-18
exists to forbid exactly that. But the example I chose to demonstrate it was the one variant that
does not bite. **The event that actually attacks β is a forged `human_verdict: "reject"` with
`verifier_accept: true`** — that lands in both numerator and denominator and inflates β directly,
making the checks look worse than they are. A forged *accept* is the quieter attack: it suppresses
nothing and moves nothing, but it does contaminate the window and the row count.

Picking the harmless variant to illustrate a genuine hole is a species of overclaim I should name
rather than quietly fix: **the fix was right, the severity argument was decorated with an example
that does not support it.**

## 2. "Four later documents assume the opposite" overcounts

ADR-0026 and ADR-0033 do conflict with ADR-0019 — ADR-0026 permits unattended metered work, and
ADR-0033 asks only when spend exceeds an authorised cap. [measured]

But **ADR-0028 says only that metered calls retain hard caps, and says nothing about approval**;
and `v0-draft.md` §7.2 requires an explicitly authorised per-task cap, **which can coexist with
per-transaction approval**. Neither independently establishes the opposite policy.

**The live contradiction is real and involves at least two documents, not four.** The decision Joe
faces is unchanged; my count of who had quietly assumed a resolution was inflated.

## 3. The ADR-0007 versus ADR-0024 contradiction is refuted

I recorded, from the first cross-family pass, that ADR-0007's CLI-only rule contradicts ADR-0024's
consent presentation. **It does not.**

ADR-0007 **explicitly requires a single interactive CLI verdict prompt** and calls that prompt the
entire review surface. Its `--json` requirement says every command must *also* work
non-interactively; it does not ban interactive CLI use. ADR-0024's neutral, equal-weight wording is
implementable in a CLI prompt without a TUI, web server or desktop dialog. [measured]

**Withdrawn.** What survives is narrower and worth keeping: the exact consent mechanics are
underspecified, and ADR-0024's *"silence is a decline"* rule still needs a stated behaviour under
a non-TTY run.

## 4. "Replay catches drift" is too strong

When the projected event count differs from the log count, `cmd_replay` sets `stale=True` and
`compared=False` — but by then `projection.build()` has already unlinked and rebuilt the database.
**State that is simultaneously stale *and* independently drifted is destroyed without ever being
compared.** [measured] The drift test covers the equal-count case only.

**No false pass results** — `compared: false` fails closed, which is the property that matters. But
the unqualified claim that replay *catches drift* is wrong, and the forensic guarantee I implied
does not exist. The honest statement: **replay catches drift when the state is current, and
reports honestly that it did not look when the state is behind.**

Now improved: when the state is stale it is copied aside before the rebuild, so the drifted
artefact survives for inspection instead of being destroyed by the check that noticed it.
