# The perpetual project conversation: what to build, what to abandon

**Date:** 24 August 2026
**Author:** CTO worktree agent
**Status:** design proposal, post-adversarial. One recommendation, not a survey.
**As-of cursor for every `[measured]` claim below:** worktree `worktree-consilience-cto`,
`.harness/log` at 2,951 valid events / 6 rejections, `.harness/dispatch` at 509 recall packs,
reference transcript at 50,885,815 bytes. Measurements taken 24 August 2026. A `[measured]` tag
without a cursor has a shelf life of hours — this transcript grew by 1.2 MB while the previous
draft of this document was being written.
**Extends:** `docs/20-design/condensation-is-a-verifier-2026-08-20.md`, ADR-0067, ADR-0070,
ADR-0074, ADR-0089, `docs/superpowers/specs/2026-08-22-chat-conversation.md`.
**Supersedes:** the β-on-the-summariser proposal in the earlier 24 August draft. See §5.

---

## 1. Thesis

Build the perpetual conversation as a stable **address** over a durable record, not as a perpetual
context window — but do not justify it with the context-window argument, because the context window
is not what is failing. Two things are measurably broken in this repository today and neither is a
capacity problem: the retrieval layer returns **zero events in 313 of 509 recall packs (61.5%), and
all 313 are budget exhaustion rather than a query that matched nothing** `[measured]`; and standing
instructions are breached while their text is verbatim in context — the usage-limits instruction
was restated three times inside a single *uncompacted* window, and principle 9 was breached on a
turn where `AGENTS.md` was injected byte-for-byte from disk `[measured]`. So: fix the packer, bind
instructions to **effects** rather than to presence in the prompt, and record condensation instead
of performing it. Abandon the plan to measure β on the summariser — as specified it equals 1.00 by
construction, and `src/consilient/beta.py` says so in its own docstring. The founding hypothesis of
this whole task, that tool results are what fills the window, is refuted at 10.6%, behind harness
injections at 25.8% `[measured]`; recording that refutation is worth more than the feature it was
meant to justify.

---

## 2. What this conversation actually cost

All from streaming passes over the reference transcript; the file was never opened with a reader.

| Quantity | Value | Tag |
|---|---|---|
| Transcript size / records | 50,885,815 bytes today; 27,444 records at 49,701,460 bytes when first censused | `[measured]` |
| Wall clock | 4 d 18 h, 6,627 API calls, 210 human turns | `[measured]` |
| Auto-compactions | 5, all `trigger: auto`, at lines 4102 / 9078 / 14352 / 19670 / 24235 | `[measured]` |
| Each compaction | ~1,000,500 tokens in → ~34,300 out (29:1), 110–158 s stall | `[measured]` |
| Cumulative dropped | 4,831,249 tokens; 11 min 21 s of dead clock | `[measured]` |
| Compaction overhead | ≈103% of the volume removed — the summariser re-reads the whole window | `[algebra]` |
| Amplification | cache_read 3,501,396,181 tokens against 3,499,071 unique content tokens = **1,000.7× re-read per token written** | `[measured]` |
| Human share | 144,945 characters, median turn 194.5 chars ≈ **1.04%** of all content written | `[measured]` |
| What fills the window | harness injections 25.8%, tool **calls** 19.5%, fixed preamble 11.5%, tool **results** 10.6%, assistant prose 3.2% | `[measured]` |
| Cheapest single term | 6,259 `hook_success` attachments / 1,864,525 bytes whose entire payload is `stdout "{}"`, `exitCode 0` | `[measured]` |
| Fill cadence | 1,142 / 1,067 / 1,183 / 1,185 / 1,128 API calls per 1 M tokens — mean 1,141, **CV 3.8%** | `[measured]` |
| Wall-clock cadence | 25,609–148,871 tokens/hour, a 5.8× spread, because the principal sleeps | `[measured]` |
| Idle gaps > 30 min | 52.0 h of the 103.0 h span | `[measured]` |
| Summary retention | per-hop named-entity carriage 24%; S1→S5 survival 6 of 35 = 17% | `[measured]` |
| Entities that came back | 4 of the 18 dropped at hop 1 reappeared by S5 (`EXP-01`, `EXP-05`, `EXP-08`, `Gate A`) — because they live in `AGENTS.md` and were re-read | `[measured]` |
| Reasoning preserved | 1,860 thinking blocks: 4,234,096 chars of signature, **0 chars of recoverable reasoning** | `[measured]` |

**Read the last two rows together.** What survives compaction is not what mattered; it is what is
re-grounded from disk. Anthropic's own documentation states the same rule per mechanism
(`code.claude.com/docs/en/context-window`, "What survives compaction") `[cited]`, which makes this a
genuine consilience — a docs table and a five-generation keyword trace are different classes of
facts and they coincide.

**And the irony, which is the strongest single argument in this document.** On 20 August EXP-45
measured retention 40.71%, consequential loss 0.00%, median session 2.7 minutes, and concluded
*"perpetual memory solves a problem that doesn't exist."* Compaction #1 dropped `EXP-45` from
context the same afternoon — present in S1's entity set, absent from S2 onward — and four days later
the principal requested exactly the architecture it retired `[measured]`. A system that cannot keep
its own killing experiment in view for four days is the case for §4, made against itself.

---

## 3. The design, component by component

Each component is: the change, the invariant, and the check that ships in the same commit.
Principle 3 — a chokepoint without an enforcement rule is not a chokepoint.

### 3.1 The conversation is the trajectory (no new store)

`events.append()` already gives, in one function: schema validation before write, `O_APPEND` with a
kernel-backed per-log lock, `lseek` to EOF, short-write retry, `fsync` inside the lock, `ftruncate`
rollback, and quarantine-as-`Rejection` rather than silent skip `[measured]`. A conversation needs
those properties and nothing else. `conversation.turn` (`work_items.py:22`), `work_item.committed`
(`:20`), `TURN_ROLES` (`:56`) and transport authentication already exist on this branch, which is
**128 commits ahead of `main`, with `main` 0 ahead** `[measured]`.

The consequence that matters: context becomes a **materialised view over the trajectory at a
cursor**, not a buffer that fills. A buffer has one failure mode (overflow) and one remedy
(destruction). A view can be rebuilt at any cursor, for any budget, for any model, and two views of
the same prefix can be diffed.

> **Invariant.** Turn *text* is never written to the append-only log. The log stores `turn_digest`,
> `author`, `transport`, `length` and a content-addressed pointer into a separate, **deletable**
> turn store.
> **Check.** A transition validator refuses a `conversation.turn` payload carrying a `text` field.
> Deleting a turn then leaves a verifiable hole: the digest chain still validates, the content is
> gone, and the receipt says `content_erased` rather than lying about completeness.

This reverses the earlier draft and it is forced. There is no deletion, tombstone or redaction path
anywhere in `src/consilient/events.py` `[measured]`; the file is engineered specifically so an
acknowledged line cannot be unwritten. The principal raised privacy unprompted twice in four days
("none of my credentials leak into the public repo"; "my usage of consilient should remain private
just like anyone elses") `[measured]`. Appending verbatim human text to an unerasable store, for a
months-long conversation, in a product other people will run, is not a tradeoff — it is a defect.

**A one-word defect found while checking that.** `work_items.py:854`:

```python
if "sha256" in trajectory.casefold() and redactions:
    raise events.EventError("secret hashes must not be stored in conversation.turn")
```

The guard is conditional on `redactions` being non-empty, so a turn carrying a raw credential with
an empty `redactions` array passes validation and is fsync'd into an append-only log `[measured]`.
It protects the redaction *bookkeeping*, not the secret — "assert the mechanism, not the property",
the failure `beta.py`'s own docstring says this repository has already found in four separate
checks. Drop the `and redactions` conjunct. One word, one test.

### 3.2 The packer: single-pass banded fit

The defect is `_compact_select_events` (`recall.py:374–462`): `while kept: …rebuild the entire pack
text…; if it fits, return; else evict the lowest-ranked candidate` `[measured]`. That is O(n) full
renders of an O(n)-byte document. Measured on the live log today:

| candidates | wall clock | pack chars | events rendered |
|---|---|---|---|
| 300 | 3,644 ms | 162 | **0** |
| 600 | 18,755 ms | 162 | **0** |
| 1,200 | 38,831 ms | 161 | **0** |

`read_all` over the same log: 805 ms `[measured]`. Two prior passes measured the same shape at
different magnitudes — 166–455 s at n=2,837, and 0.3–7.0 s at n≤1,200. Three passes agree on sign
and superlinearity and disagree on magnitude by roughly 10×, which is machine load. Report sign and
threshold, not a point estimate (principle 2). **It is already degenerate at n=300**, so the earlier
claim that "the rate is rising as the log grows" was wrong; it was total from the start.

Admission policy — three signals combined **lexicographically by band, never as a weighted sum**,
because any weighting that lets recency outbid a pin will, on some turn, drop the pin:

- **Band 4** — the live `work_item.committed` at its latest revision, its success-criteria digest, its source turns.
- **Band 3** — the pinned class (§4).
- **Band 2** — adverse and contested: `dispatch.refused`, `attempt.verdict.correction`, anything carrying dissent or unresolved authority (`_has_dissent`, `_has_unresolved_authority` already exist at `recall.py:214,225`).
- **Band 0** — ordinary history, query-matched, most recent first.

Four rules on top: **one render pass** — compute each candidate's rendered length once, sort, admit
greedily, O(n log n); **band floors**, so a fat band-4 event cannot starve band 3; **oversize
degrades to a pointer, never to absence** — `stable_id`, kind, timestamp, first 200 characters,
digest, and the exact command that fetches it in full; **recency is a tie-break inside a band and
nothing else**, since recency-based preservation is precisely why the incumbent's per-hop entity
retention is 24%.

> **Invariant.** A pack over a non-empty candidate set renders at least one event.
> **Checks, all three in the same commit.** (a) property test: `len(candidates) > 0 ⇒
> events_in_pack > 0`, asserted against the *candidate set*, not the pack count; (b) a wall-clock
> ceiling at 10,000 candidates; (c) regression fixture: replay each of the 509 recorded dispatch
> queries against its own prefix.

The fixture objection is closed by measurement. The worry was that some zero-event packs are
legitimate `_NO_MATCH_PACK` results, so a fixture demanding ≥1 event would train the packer to
fabricate relevance. I classified all 313: **313 budget-exhausted, 0 no-match, 0 empty-log**
`[measured]`. The fixture is safe.

Note that `pack_events` returns a bare `str` while `Selection` (`recall.py:115`) carries the receipt
internally `[measured]`. Adding `rendered_length` per omission, `referenced_ids` distinct from
`omitted_ids`, and `band_budget` requires returning `Selection`. Budget that API change; it is small
and it is currently budgeted nowhere.

### 3.3 `conversation.instruction` — a pointer, not a second copy

Standing instructions already have a durable home that works: `CLAUDE.md`, `AGENTS.md` and
`docs/decisions/`. `AGENTS.md` carries the postmortem of what happens when a second one appears — a
hand-maintained copy of `consil doctor` output drifted and three of four gate states were wrong on
21 August, *"a second source of truth that drifts, which is what happened here"* `[cited]`.

So the trajectory records the **event** that the principal stated a preference, its verbatim text,
and a pointer to the authoritative file or gate. The file holds the text that gets injected. One
place to read, one place to edit, and the append-only log tells you when and by whom it changed —
which is what a trajectory is actually good for.

Payload: `instruction_id`, `text`, `subject` (short slug: `harness-selection`, `publication`,
`spending`), `applies_to` (path or gate id), `enforced_by` (capability gate id, or null),
`expires_at` (or null), `supersedes` (id or null).

> **Invariants and checks**, all via the existing `events.register_transition_validator`
> (`events.py:2441`), which refuses re-registration of a kind and runs inside the batched-append
> critical section `[measured]`:
>
> 1. `supersedes` naming an id absent from the prefix, or already superseded → refused at append.
> 2. A second unsuperseded instruction with the same `subject` that does not name the first in
>    `supersedes` → **refused at append**. The contradiction surfaces at write time, in front of the
>    human who caused it.
> 3. An instruction whose append would take the unsuperseded pinned set over its ceiling → refused.
>    The human retires something at the moment they add something, when it costs ten seconds and
>    they have the context to choose.
> 4. `enforced_by` is null → the receipt labels the instruction **`unenforced`**, explicitly, every
>    time it is injected. A pin whose only enforcement is that its bytes are in the prompt *is* a
>    prompt, and principle 4 forbids fixing things with prompts. Labelling it stops it masquerading
>    as enforcement.

Rule 3 is not hypothetical. Instruction-bearing human turns run at 14/day (59 of 207 turns over 4.2
days) `[measured]`; converting even 20% into durable instructions is 2.8/day. Against an 8,000-char
budget holding roughly 40 pointer-stubs, a monotone pinned set with a fail-closed assertion is a
**scheduled session halt around day 14** `[algebra]` — and the pinned class is already 3.3× over
budget on day zero, because `CLAUDE.md` + `AGENTS.md` + `CONSILIENCE.md` is 26,526 bytes
`[measured]`. Bound it at append, not at read.

`expires_at` exists because this corpus produced three harness-specific instructions in four days
(SuperGrok Heavy, ultracode, Cursor Composer); at that rate month three has ~65, most naming
products that have changed or gone. Without expiry the retirement path is a human authoring 65
supersessions — spending the one resource this project treats as scarce.

### 3.4 `context.condensed` — record, never mutate

```
conversation_id
window        {first_event_id, last_event_id, prefix_digest}
input_digest  prior summary + preserved tail — what the summariser ACTUALLY read
depth         integer; S2 summarises S1's summary, so depth >= 2 is a claim about a claim
summary_text, summary_digest
retained_ids, referenced_ids, dropped_ids
producer      {model_id, prompt_digest, harness_version}
pin_assertion {required_ids, present_ids, result}
tokens {pre, post}, duration_ms
trigger       scheduled | ceiling | manual
```

`input_digest` and `depth` are separate from `window.prefix_digest` because from hop 2 onward
"check the summary against the prefix" checks the wrong object. Record the recursion, and refuse to
trust a summary past a chosen depth.

Costs, honestly. **Storage negligible:** five summaries of ~20 KB over 4.2 days ≈ 9 MB/year per
conversation, against 47 MB of transcript for the same four days `[algebra]`. **Compute nothing
new:** the summariser already reads the window; recording adds one validated append. **Replay is the
real bill:** `projection.build()` unlinks the database and re-reads the whole log, and
`events.read_all` parses and validates every line on every recall, every assemble and every
projection build — 805 ms today and growing without bound `[measured]`.

**Latency becomes a gain rather than a cost.** Fill is turn-driven at CV 3.8% while wall time varies
5.8×, and there were 52.0 h of idle gaps over 30 minutes `[measured]`. Schedule condensation at ~70%
of the predicted turn count during a gap and the stall is zero, not smaller.

> **Invariants.** Condensation never mutates the prefix (append-only assertion). The scheduler falls
> back to ceiling-trigger when the per-model cadence constant has fewer than *n* observations —
> 1,141 ± 43 calls per 1 M is measured on `claude-opus-5[1m]` and does not transfer — and `trigger`
> records which mode fired, so the calibration is measurable rather than assumed.

**One justification is withdrawn.** The earlier draft sold recording partly on the grounds that you
can re-condense the same prefix with a different model and compare. `CONSILIENCE.md` classifies
exactly that structure: *"Debate over shared context | No | Echo."* Two summarisers over one prefix
are two inductions from **one** class of facts; their disagreement tells you the summarisers differ.
The justification that survives is diffing the summary against the **repository**, which is a
different class.

### 3.5 The three tiers

The principal named three: one durable per-project conversation as the default, several concurrent
project conversations, and disposable throwaway ones for a quick question to a specific model.

| | Tier 1 — project | Tier 2 — concurrent projects | Tier 3 — disposable |
|---|---|---|---|
| `conversation_id` | one, stable for the project's life | one per project | **absent** |
| Trajectory writes | all kinds | all kinds | **none** |
| May author commitments / instructions | yes, if `transport.authenticated` | yes | **refused at `validate()`** |
| Recall scope | own conversation + project pinned set + invariant core | same | **invariant core only** |
| Condensation | scheduled | scheduled | never; it dies first |
| Model | may change mid-conversation | may change | **fixed at open** |

One enforceable sentence: **a `work_item.committed` or `conversation.instruction` whose source turn
is not an authenticated turn in a durable conversation is refused by `validate()`.** The plumbing
exists — `_source_turns_authenticated` already gates protected commitments (`work_items.py:1323`)
`[measured]`. Tier 3 is defined by absence rather than by a flag, so "delete my throwaway chat" is a
no-op that cannot fail. Promotion — replaying a disposable conversation's turns into a durable one
with `imported_from` — is one-way; you cannot un-append.

**Tier 2 is the justification for the whole architecture and should be stated as such.** See §7.

---

## 4. What must never be dropped — and what that actually guarantees

**The distinction is not importance. It is re-derivability.**

> **Restatable detail** is anything reconstructible from a named artefact on disk. Rule: *if it has
> a path and a digest, it is a pointer, not a payload.*
>
> **The pinned class** is what exists only because a human said it, or a decision was taken:
> standing instructions, corrections, refusals, gates, thresholds, the live commitment.

The evidence is clean. Every measured rediscovery in the reference transcript —
`quota-pools-and-routes-2026-08-21.md`, `supergrok-feasibility-2026-08-20.md`, `ruflo-adoption` —
concerned a fact that was **in a named file on disk the entire time** `[cited]`. Storage never
failed; the trigger did. The transcript states it better than I can: *"an agent cannot search for
what it doesn't know it has forgotten"* (L19413) `[cited]`.

So: **restatable detail needs a better retrieval trigger (§3.2); the pinned class needs never to be
summarised at all.**

**Guaranteed:**

1. **Verbatim or nothing.** A pinned item is re-injected byte-for-byte from its authoritative file
   after every assembly and every condensation. Check: the source string must appear as an exact
   substring of the assembled context; a paraphrase fails.
2. **Fail closed.** `assert_pins(context_text)` runs after every assemble and every condensation and
   raises, halting exactly as `consil doctor` exits non-zero while the gates are shut. No prompt is
   involved anywhere in this mechanism — that is the difference from ConstraintRot's Constraint
   Pinning, which restores 0% at the prompt layer `[cited]` and is therefore one bad summariser away
   from regression.
3. **Supersession, not deletion**, validated at append (§3.3).

**Not guaranteed, and this is the correction that matters. Presence in context does not cause
compliance.** Measured on this corpus:

- The usage-limits instruction is restated at least seven times across the session, and **lines
  10734, 12022 and 14338 all sit inside window 3, with no compaction between them** (boundaries at
  4103 / 9079 / 14353 / 19671 / 24236) `[measured]`. It was restated three times inside one
  uncompacted context window. Condensation did not cause that breach; condensation had not happened.
- L17673, *"Better than best standard remember!!"* — that is principle 9, which lives in `AGENTS.md`
  (17,518 bytes), which `CLAUDE.md` `@`-references, and which is therefore injected verbatim from
  disk on every single turn `[measured]`. The exact mechanism proposed above was in force,
  uncompacted and unparaphrased, on the turn that was breached.

`assert_pins` would have passed on every one of those turns; the pin *was* present. So the claim
"β on the pinned class = 0.00 by construction" is true and **irrelevant**: it measures presence in
the buffer, and the failure is non-compliance with text that is present.

**The repair, and it is where the ratchet belongs.** The usage-limits instruction is not "prefer
Codex"; it is *"do not spend Claude quota on granular work"* — a precondition on an action.
`src/consilient/effects.py` and `capabilities.py` already exist to gate actions. `enforced_by` names
a capability gate; instructions without one are recorded and explicitly labelled `unenforced`. That
converts the honest subset into code and stops the rest pretending to be enforcement.

**The user-visible failure this leaves open, stated precisely because the corpus contains it.** The
instruction is given at 20 Aug 23:43. The assistant continues doing the opposite. Nothing reports
anything: the pin is present, the receipt is clean, `consil doctor` is unchanged, no event fires.
Output quality does not visibly degrade — it is good work done with the wrong resource. The human
detects it **13 hours and ~1,900 records later**, from a vendor dashboard `[measured]`. For any
instruction that cannot be expressed as a capability gate, this design does not improve that
detection story at all. Say that out loud rather than letting the pinned class imply otherwise.

---

## 5. The compaction-β measurement: abandoned, and what replaces it

**Abandoned.** The earlier draft proposed β_condense = P(dropped | mattered), mapped onto
`beta.compute` with `verifier_accept := item was dropped`. It is not identifiable. The denominator
needs the cell **retained ∧ mattered**, and none of the three proposed label sources can produce it:

- **Breach** presupposes the instruction was *absent*; a retained instruction that mattered produces compliance, which is silent and unlabelled.
- **Rediscovery** has `dropped_ids` in its predicate. It structurally cannot fire on a retained item.
- **Contradiction** labels what the summary got wrong, i.e. what it failed to carry.

Every labellable row therefore carries `verifier_accept = True`, so **β = 1.00 at any sample size,
on any corpus, for any summariser** `[algebra]`, and the Wilson interval would tighten around 1.0 in
a way that looks exactly like a converging measurement. The refutation is already in the module the
design proposed to reuse — `src/consilient/beta.py`, lines 17–19, verbatim `[measured]`:

> "The bound only follows if the sample is **not conditioned on the verifier's own outcome**. If
> artefacts reach a human only when the checks already accepted them, every rejected row has
> `verifier_accept=True` and β is 1 by construction rather than by measurement."

A design that reads a file for its constants and not for its warnings is the same failure as an
agent reading a summary instead of the prefix. Publishing a Wilson interval around 1.00 and calling
it β on a summariser would be the exact failure this project was founded to catch — published by the
project whose subject is measurement honesty.

**A second defect in the rediscovery label, measured.** Of the 18 entities dropped at hop 1, **four
came back** (22.2%) — `EXP-01`, `EXP-05`, `EXP-08`, `Gate A`, plus `ADR-0043` on a `.X..X` pattern —
because they live in `AGENTS.md` and `docs/` and were re-read `[measured]`. That is the retrieval
system working as intended. A rediscovery detector cannot separate "re-derived something it should
never have lost" from "read a file, which is the point", so roughly a fifth of that numerator is
successful retrieval mislabelled as loss.

**What survives.**

1. **A descriptive rate, honestly named.** Post-boundary rediscovery rate per boundary, with a
   well-defined denominator (candidate items in the window), reported as a diagnostic and **never
   routed on**. Not called β. Enforcement: the estimand kind is registered in `beta.py`'s
   `PROXY_ESTIMAND_KINDS` alongside the existing proxies, so it cannot be presented as the
   human-verdict β.
2. **The only construction that identifies it, if you ever want a number.** An **ablation**, not an
   observation: at each boundary, sample *k* retained items, re-run the continuation with each one
   removed, and score both continuations against an oracle this project already trusts (tests,
   typecheck, `consil doctor`). That produces `retained ∧ mattered` because you *make* the
   counterfactual instead of waiting for it. It is expensive, and it is the price of a non-circular
   number. Deferred to §7 step 7, gated on the packer and the projection being fixed first.
3. **β itself is untouched** where it already works: the rate at which an automated check accepts a
   bad artefact. Nothing here changes that meter.

**And the bar was narrowed until it was empty.** The earlier draft's unoccupied row — "fidelity
measurement of a single condensation event" — asks "did this summary keep what the source said?",
which is **summarisation faithfulness**, a field with a decade of published numbers: FactCC, SummaC,
QAFactEval, AlignScore, and RULER / needle-in-a-haystack for retention specifically `[cited]`. The
prior search was scoped by *mechanism* (agent compaction) rather than by *estimand* (summary
fidelity), which is why it came back empty. Principle 9 says finding the bar is the work, and a bar
defined as "this measurement, in this harness, in this year" is not a bar — it is the move that
produced *"Nothing on the market measures it"* while eight published systems measured β. The
defensible claim is narrower and true: **faithfulness scored per boundary, on a live multi-day agent
trajectory, against a replayable prefix.** A new setting, not a new metric.

---

## 6. What this does not solve

Every adversarial finding, with status. Nothing refuted is quietly retained.

| # | Finding | Status |
|---|---|---|
| 1 | β_condense = 1.00 by construction | **Closed by abandonment** (§5). The ablation is the only non-circular route and it is deferred, not assumed. |
| 2 | Pins do not cause compliance; the corpus shows breach with the text verbatim in context | **Partially closed.** `enforced_by` converts the gateable subset into code. The ungateable residue is **open and named** in §4: no improvement on the 13-hour detection latency measured. |
| 3 | Fail-closed plus a monotone pinned set is a scheduled halt around day 14 | **Closed** by the append-time ceiling (§3.3, rule 3). |
| 4 | A second source of truth for standing instructions | **Closed** by pointer-not-copy (§3.3). |
| 5 | Supersession validates structure, not semantics | **Partially closed.** `subject` catches same-topic contradictions at append; `expires_at` retires conditionals. **Open:** two instructions that genuinely conflict across *different* subjects are both still pinned, and nothing detects it. |
| 6 | The zero-event fixture may train the packer to fabricate relevance | **Closed by measurement:** 313 of 313 zero-event packs are budget exhaustion, 0 no-match `[measured]`. |
| 7 | Erasure versus append-only provenance | **Mostly closed** by digest-plus-pointer (§3.1). **Open:** deleting a turn already covered by a `context.condensed` summary still requires re-running the summariser, which changes `summary_digest` and invalidates every downstream assembly digest. Nothing solves that; the honest posture is that summaries are derived artefacts, a deletion invalidates them, and that is recorded rather than hidden. |
| 8 | Re-condensing one prefix with two models is echo | **Conceded**; the justification is withdrawn (§3.4). `input_digest` and `depth` adopted. |
| 9 | The bar was narrowed until it was empty | **Conceded**; incumbent estimand named, claim narrowed to the setting (§5). |
| 10 | The null hypothesis — a hand-written continuation brief — is in the corpus and it worked | **Conceded.** Line 12 of the transcript is exactly that, written by the principal, at the start of this very session `[measured]`. It costs ~25 min/day of his attention at 1.2 briefs/day; it gets pinned-class fidelity by the same construction argument; it deletes by deleting a file; its stale instructions die by omission; its context is bounded by what a human will type. For a **single** project conversation it is not obviously beaten. This design wins on provenance, and decisively on **concurrency** — see §7. |
| 11 | Missing as-of cursors, wrong line numbers, 6 unexamined rejections, `pack_events` returns `str` | **Closed:** cursor in the header; `MIN_REJECTIONS` is `beta.py:38`; the `Selection` return-type change is budgeted in §3.2. **Open:** nobody has looked at the 6 quarantined rejections on the live log. |

**Also not solved, and it is the largest single term:** harness injections are 25.8% of re-read
context, and 6,259 of them are `hook_success` records whose entire payload is `stdout "{}"` and
`exitCode 0` `[measured]`. That comes from *our own* hook configuration, is orthogonal to everything
above, and is the cheapest available win. It is step 3 in §7 for that reason.

**And the framing to give him plainly:** Claude Code has not solved context engineering. It has made
the conversation disposable and moved the durable part to `CLAUDE.md`. That is a good design and a
much smaller claim, and it is the design this document copies and then instruments.

---

## 7. Sequencing — by risk reduction per unit of your attention

Steps 0–3 need **no perpetual-conversation argument at all**. They are worth doing whatever you
decide about the rest.

| # | Step | Exists already? | What it buys | Your attention |
|---|---|---|---|---|
| **0** | Drop the `and redactions` conjunct at `work_items.py:854` | code exists, the guard is wrong | Stops a raw credential entering an **unerasable** log. Trust boundary; one word. | ~2 min |
| **1** | Single-pass banded fit + pointer admission in `recall.py` | `Selection`, ranks, band signals and dissent detectors all exist; the loop is wrong | Turns 61.5% empty packs and 3.6–39 s builds into sub-second packs that always carry something. This is the live production failure. | ~30 min |
| **2** | Merge the 128 commits on `worktree-consilience-cto` into `main` | fully built, **unmerged** | `conversation.turn`, `work_item.committed`, transport authentication, receipts. `main` is 0 ahead, so this is a fast-forward-shaped merge, not a reconciliation. | ~20 min, mostly `consil doctor` |
| **3** | Hook results with exit 0 and empty stdout are not appended to context | our own hook config | The largest controllable context term (25.8% class; 1.86 MB of `{}`). | ~5 min |
| **4** | Incremental projection: cursor + index on `(conversation_id, kind, commitment_id)` | **nothing exists** — genuinely new | Stops paying a full parse-and-validate scan per recall, per assemble, per projection build. Without it, months-long is arithmetically impossible. | ~45 min |
| **5** | `conversation.instruction` / `.correction` with `subject`, `expires_at`, `enforced_by`, append-time ceiling | `register_transition_validator`, `effects.py`, `capabilities.py` exist | Standing preferences get a durable, bounded, non-contradictory home wired to real gates. | ~40 min |
| **6** | `context.condensed` as a record; scheduled at ~70% of predicted turns in an idle gap | nothing exists | Removes the 110–158 s mid-task stall; makes the summary a checkable claim about a surviving prefix. | ~30 min |
| **7** | Ablation study of condensation fidelity (§5.2) | nothing; **gated on 1 and 4** | The only non-circular number. Expensive. Do not start before the packer and the projection are fixed. | a decision, then hands-off |

**Already built and merely unwired:** `conversation.turn`, `work_item.committed`, transport
authentication, `Selection` with its receipt fields, `ALWAYS_INCLUDE_KINDS`, `_has_dissent`,
`_has_unresolved_authority`, `_source_turns_authenticated`, `instructions.assemble` — **live in
production dispatch at `scripts/dispatch.py:974`, with 371 `instructions.assembled` events in the
log** — `reconstruct()` with per-layer drift, `beta.compute` with Wilson intervals, `effects.py`,
`capabilities.py`. **Genuinely new:** the incremental projection (step 4), the instruction kinds
(step 5), `context.condensed` (step 6).

**Where this design decisively beats the null hypothesis: step 2 onwards, and only for Tier 2.** One
person cannot hand-write continuation briefs for six concurrent project conversations at 1.2 briefs
a day each. That — not context capacity — is the argument for the architecture, and it is the
argument to accept or reject it on.

---

## 8. Acceptance tests

Runnable, each failing today.

1. **Packer non-degeneracy.** For every one of the 509 recorded dispatch queries, replayed against
   its own prefix: `len(candidates) > 0 ⇒ events_in_pack > 0`. Fails today on 313 of 509.
2. **Packer bound.** `pack_events` over 10,000 synthetic events completes under a fixed wall-clock
   ceiling. Fails today at n=1,200.
3. **Secret guard.** A `conversation.turn` payload containing a 64-hex digest and an **empty**
   `redactions` array raises `EventError`. Passes validation today.
4. **No turn text in the log.** A `conversation.turn` payload carrying a `text` field is refused.
5. **Verbatim pin.** For any log with an unsuperseded instruction, the assembled context contains
   its source string as an exact substring; a paraphrase fails the assertion.
6. **Unenforced is labelled.** An instruction with `enforced_by = null` appears in the receipt marked
   `unenforced` every time it is injected.
7. **Subject exclusivity.** Appending a second unsuperseded instruction with an existing `subject`
   and no `supersedes` raises at append.
8. **Pinned-set ceiling.** Appending an instruction that would take the unsuperseded set over the
   ceiling raises at append. (Deliberately fails today: `CLAUDE.md` + `AGENTS.md` + `CONSILIENCE.md`
   is 26,526 bytes against an 8,000-char budget — the test's first job is to make you set the
   ceiling honestly.)
9. **Projection equivalence.** `state_digest()` is identical between a full rebuild and an
   incremental apply over the same prefix.
10. **Condensation is append-only.** After a `context.condensed`, every pre-boundary event id still
    resolves in the log and `prefix_digest` is unchanged.
11. **Cadence fallback.** With fewer than *n* observations for a model, the scheduler records
    `trigger: ceiling`, not `scheduled`.
12. **Estimand honesty.** The post-boundary rediscovery rate is registered as a proxy estimand, and
    `beta.compute` refuses to report it as the human-verdict β.

---

## 9. Open questions

Four, one sentence each.

1. **Is Tier 2 concurrency the thing you actually want?** If in practice you run one project
   conversation at a time, the hand-written continuation brief already works and steps 5–7 are not
   worth your review time.
2. **What is the ceiling on the pinned set?** Name a number — say twenty unsuperseded instructions —
   because the check in step 5 cannot be written without one, and defaulting it silently is how it
   becomes wrong.
3. **Do you accept that turn text never enters the append-only log**, living instead in a separate
   deletable store behind a digest, given you have twice raised privacy unprompted?
4. **Do you want the ablation (step 7) at all**, knowing it is the only honest fidelity number, that
   it costs real compute re-running continuations, and that skipping it means this project publishes
   no number about compaction quality?
