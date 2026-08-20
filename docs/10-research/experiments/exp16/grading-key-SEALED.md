# SEALED — EXP-16 blind grading key

> ## ⛔ DO NOT READ THIS FILE BEFORE GRADING
>
> This is the answer sheet for `grading-pack.md`. It maps every anonymised option back to
> the arrangement that produced it. Reading it first destroys the only property that makes
> the grading worth anything, and there is no way to un-read it — the grading would have to
> be abandoned and the experiment re-run with fresh decisions.
>
> Grade `grading-pack.md` first. Write your answers down. Then come back here.

---

## 1. The mapping

Letters are assigned **independently per decision**. Each letter carries each arm exactly
twice across the six decisions, so counting letters is uninformative by construction.

| Decision | Option M | Option T | Option V |
|---|---|---|---|
| **D1** — plugin or standalone | **Arm A** (single agent) | **Arm B** (Owner meeting) | **Arm C** (free-form) |
| **D2** — v0 success condition | **Arm C** (free-form) | **Arm B** (Owner meeting) | **Arm A** (single agent) |
| **D3** — Inquiry tier | **Arm B** (Owner meeting) | **Arm A** (single agent) | **Arm C** (free-form) |
| **D4** — v0 scope | **Arm A** (single agent) | **Arm C** (free-form) | **Arm B** (Owner meeting) |
| **D5** — local model library | **Arm C** (free-form) | **Arm A** (single agent) | **Arm B** (Owner meeting) |
| **D6** — executable-model ratchet | **Arm B** (Owner meeting) | **Arm C** (free-form) | **Arm A** (single agent) |

Cross-check against the substantive outcomes already recorded in `exp16-results.md`:
D1 the plugin flip is Arm C (Option V); D6 the drop-from-v0 flip is Arm B (Option M).
Both are consistent with the table above. `[measured]`

## 2. Seed and construction

**Seed: `20260820`.** Reproducible from this file alone:

```python
import random
from itertools import permutations

SEED = 20260820
LETTERS = ["M", "T", "V"]
DECISIONS = ["D1", "D2", "D3", "D4", "D5", "D6"]

perms = list(permutations("ABC"))   # exactly 6 orderings for exactly 6 decisions
rng = random.Random(SEED)
rng.shuffle(perms)
mapping = {d: dict(zip(LETTERS, p)) for d, p in zip(DECISIONS, perms)}
```

Using each of the six permutations exactly once guarantees perfect column balance — every
letter carries every arm exactly twice — and no two consecutive decisions share an
ordering. Both properties were asserted in the generator and hold. `[measured]`

**Deviation from the brief, deliberate.** The brief asked for α/β/γ. I used **M/T/V**
instead, because β is this project's central quantity and both α and Δ appear inside the
closed form β\* = (1−α)·e^(−kΔ), which the options quote repeatedly. "Option β says β\*
collapses to 0.028" is a real reading hazard, not a stylistic worry. M, T and V collide
with no symbol used anywhere in the source text. `[asserted]`

## 3. Where each arm's text was recovered from

All three arms were found. Nothing in the pack is invented. `[measured]`

| Arm | Source actually used | Note |
|---|---|---|
| **A** | Workflow result file `tasks/wtutzf75x.output` (JSON, 6 records with `decision` / `rationale` / `overturn` / `dissent_or_uncertainty` / `evidence_classes_used`) | Referenced by `.harness/log/2026-08-19.jsonl` event `arm_a.completed`. Complete for all six decisions. |
| **B** | `scratchpad/exp16/armB-transcript.md`, the `[Dn/B/OWNER]` closing comments | The verbatim owner decisions, in the same session store. |
| **C** | `scratchpad/exp16/armC-transcript.md`, scribe records plus the round-1/round-2 turns | Decision from the scribe record; reasoning condensed from the turns (see §5.2). |

All three live under the 19 August session store
`C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr-Repositories-consilience/c01aa5f0-9999-4816-ac11-f5b5bc157081/`.
That is a temp directory and is not permanent — **if these transcripts matter beyond this
grading, copy them somewhere durable.** `[measured]`

**ClickUp was unreachable.** The MCP connector returned `RATE_LIMIT_EXCEEDED` with a
~13.5-hour retry window after the first task fetch, so Arm B's comments could not be read
back from the live store. The local transcript was used instead. One ClickUp task (D1,
`869em65nx`) was fetched successfully before the limit, and its question statement matches
the D1 brief in `scratchpad/exp16/decisions.md`. That is the only cross-check available,
and it checks the *brief*, not the comments. `[measured]` Slack was reachable and `#consilience-exp16` (`C0BRCQY2MED`) was located, but
the local Arm C transcript was already complete, so the threads were not re-read from
Slack. **Neither the ClickUp comments nor the Slack threads were independently verified
against the local transcripts.** If that matters, verify before publishing anything from
this. `[asserted]`

## 4. Normalisation rules applied

Applied uniformly to all three arms unless stated:

1. **Evidence-class labels replaced by class names.** `E1` → "simulation and algebra",
   `E2` → "verified literature", `E3` → "competitive landscape", `E4` → "project
   constraints". *Why it mattered:* all three arms used E1–E4, but Arms A and B used them
   as citations while Arm C's record used them as participant names ("E4 conceded to E3's
   staleness facts"). Left alone, that alone identifies Arm C on every decision.
2. **"Joe" → "the maintainer"** throughout the options. The briefs are quoted verbatim and
   still say "Joe", which is fine: the briefs were identical across arms.
3. **Private repo names replaced** — `jobboard-v2` → "the main repo", `hireable-3.0` → "a
   weakly-verified contrast repo". Both are private commercial repos; names alone are
   permitted by `AGENTS.md` but there is no reason to spend the allowance here. The
   substance ("a contrast repo is mandatory") is preserved wherever an arm asserted it.
4. **Status vocabulary stripped**: `PROVISIONAL`, "parked on Joe", "per ADR-0020 §3",
   `DECISION:` / `RATIONALE:` / `DISSENT:` headers, "complete"/"decided" ticket states.
5. **Discussion vocabulary stripped**: "4–0", "3–0", "unanimous", "consensus", "the
   group", "all four participants", "my vote", "I'm done unless Joe objects", "sounds like
   three of four are converged".
6. **Tool and role references stripped**: ClickUp, Slack, thread, comment, ticket, Owner,
   Evidence agent, scribe, facilitator, meeting.
7. **Experiment identifiers de-numbered in the option text** — "EXP-01" → "the β
   measurement", "EXP-05" → "the adapter-surface experiment", "EXP-10" → "the three-month
   measurement". Applied uniformly; the arms cited these at similar rates so it is not
   load-bearing, but it removes an incidental register difference. The **briefs** are quoted
   verbatim and still carry "EXP-10", which is correct: the briefs were identical across
   arms and carry no arm information.
8. **Numbers untouched.** Every figure (0.112 → 0.028, ρ=0.6, 24.2 pp, 43.8%, +4.4 pp,
   0.052–0.426, 16% fork-to-star, 114 tests, 63 incidents, ~5,000 trajectories, n=200/800)
   is reproduced exactly as the arm wrote it.

## 5. Judgement calls a reader must know about

### 5.1 Grammatical person was rewritten, not cut — the largest fidelity compromise

Arms A and B wrote in the first person singular ("I weighted E4 because…", "I took E4
because…", "I cut the cascade anyway…"). Arm C's decision record is impersonal by
construction, because no single author wrote it. Left as-is, the presence or absence of
"I" identifies Arm C on all six decisions with no inference required.

I therefore converted first-person *procedural* constructions to impersonal ones in all
three arms: "I weighted X over Y" → "X outweighed Y", "I took E4 because" → "constraints
won because". **This is the one place where I rewrote rather than cut**, and it is
uniform, mechanical and applied to A and B (C had nothing to convert). Substantive
first-person content was not touched. `[asserted]`

### 5.2 Arm C's reasoning is a selection across four authors; A and B's is a cut from one

This is the second-largest compromise and it is **asymmetric**. Arms A and B each produced
a single authored reasoning block, so condensing them was pure deletion. Arm C's scribe
record contains a decision and a dissent note but **no reasoning section at all** — its
reasoning exists only distributed across the round-1 and round-2 turns of four
participants. To fill the template's Reasoning field for Arm C I had to *select* which of
those turns' arguments to carry.

I selected on the same basis each time — the arguments the scribe record itself named as
load-bearing, in the order the thread raised them, in the participants' own words. But
selection across four authors is an editorial act that Arms A and B did not receive, and
it plausibly makes Arm C read slightly more coherent than the raw thread was. **If Arm C
grades well, that advantage is a candidate explanation and should be checked against the
raw transcript before the result is believed.** `[asserted]`

### 5.3 Arm B's D4 — the parked version was used, not the later closure

Arm B's D4 owner decision was `PROVISIONAL`, parked awaiting Joe's preferential evidence.
A **later** closure exists (recorded in `exp16-results.md`: "full candidate list, sequenced
β-meter-first with measurement gates", on ClickUp `869em65r1` and Linear HIR-50), written
*after* Joe supplied his weekly hours and scope appetite.

**I used the parked version.** The later one had access to a class of evidence that Arms A
and C never saw, so grading it would compare unlike things and would flatter Arm B on
precisely the decision the brief flagged as preferential. The status vocabulary was
stripped, but the substantive position — budget primitives held back pending a statement
of weekly hours and scope appetite — was kept, because deferring a sub-decision to the
person who holds the missing facts *is* a position, not a process artefact.

This is a defensible choice but it is a choice, and it cuts against Arm B: if you would
rather grade Arm B's finished D4, the text is on the ticket and this decision should be
re-graded separately. `[asserted]`

### 5.4 Arm A's "Preferential remainder:" sections

Arm A alone emitted a labelled section by that exact name on five of six decisions — a
per-decision structural marker that identifies it instantly. The content was preserved and
folded, unlabelled, into the risks field, phrased as "is not an evidence question and has
not been decided here". Applied to Arm A only, because only Arm A produced it.

### 5.5 Arm B's per-class confidence tags were dropped

Arm B's owner rationales ranked evidence classes by the confidence tag attached to each
comment ("E4 — constraints, high confidence — weighted highest"). Those tags are an
artefact of that arm's comment template and were dropped as a format tell. The underlying
substance — that constraints are documented project facts while simulation is model-world
— survives in the reasoning text. This is a small, real degradation of Arm B: it loses an
explicit statement of *how* it weighted, keeping only *what* it weighted. `[asserted]`

### 5.6 Arm C's voluntary passes are not represented

Eleven of Arm C's twenty-four round-2 turns were voluntary passes. The template has no
field for that and it was not represented. On D5 and D6 all four round-2 turns passed, so
those two Arm C options rest on round-1 alone.

## 6. Length audit

Words per option, measured on the finished pack. `[measured]`

| Decision | M | T | V | spread |
|---|---|---|---|---|
| D1 | 320 | 288 | 332 | 44 (13%) |
| D2 | 349 | 271 | 356 | 85 (24%) |
| D3 | 321 | 328 | 321 | 7 (2%) |
| D4 | 352 | 328 | 337 | 24 (7%) |
| D5 | 307 | 328 | 336 | 29 (9%) |
| D6 | 295 | 322 | 351 | 56 (16%) |

By arm: **A mean 339**, **B mean 308**, **C mean 327**. Arm B is ~9% shorter on average,
which is not eyeball-detectable across six decisions and is not monotone (B is the middle
length on D4 and D5). D2 has the worst spread at 85 words, with Arm B shortest.

**Nothing was padded to close these gaps**, per the instruction that a genuine thoroughness
difference should be recorded rather than manufactured away. In the raw sources the
disparity was far larger: Arm A's rationales ran 400–600 words, Arm B's 250–300, Arm C's
scribe records ~100 (over threads of 1,500+ words). The 150-word cap on Reasoning
compressed Arm A hardest.

## 7. Honest assessment of whether the pack is actually blind

**It is blind for the comparison that matters, and probably not blind for the other one.**

### Arm C is likely identifiable — and this is unfixable

Arm C recorded **no dissent on any of the six decisions**; Arms A and B recorded explicit
dissent on all six. In the pack this shows up as exactly one option per decision reading
"None recorded", usually followed by a list of absorbed conditions. By D2 or D3 an
attentive reader will notice the pattern, and from there Arm C is identifiable on every
decision.

I could not fix this without destroying the result. The dissent asymmetry **is** structural
finding 1 of the experiment ("dissent survives structure and dies in discussion"). Writing
manufactured dissent into Arm C, or deleting it from A and B, would have made the pack
blind and worthless. The instruction was explicit that substance must not be equalised, and
I followed it.

Secondary correlated tell: Arm C attaches housekeeping riders — trademark clearance,
package-name reservation, two unread papers — that neither other arm produces at all.

### Arm A versus Arm B is, I believe, genuinely blind

This is the pair stopping rule 1 turns on, and I cannot find a reliable discriminator:

- Both write in the first person; both cite all four classes by name; both record dissent
  on all six decisions; both name an overturn condition.
- Length overlaps heavily (339 vs 308 mean, ranges 320–356 vs 271–337).
- Both use "where X and Y conflicted, Y won" constructions — Arm B more often, but Arm A
  does it too (D1 "the audience argument is real but weak", D3 "the case against, which
  wins"), so it is a frequency difference of two or three instances across six decisions,
  not a marker.
- The substantive positions are the same in four of six cases, which is the finding.

The weak signals I can see, none of which I would bet on: Arm A's dissent sections are
slightly more self-accusing in tone; Arm B's rationales more often enumerate the classes in
order. Both are impressions, not patterns I could state as a rule.

### Residual risks I cannot rule out

1. **You wrote the source material.** You have read `robustness_beta_star.py`, the friction
   log and the literature review. Some phrasing will be familiar and may cue recognition in
   ways I cannot predict or defend against. `[asserted]`
2. **I know the mapping and I wrote the prose.** Every condensation was made by an agent
   that knew which arm it was condensing. I applied the rules mechanically and cut rather
   than rewrote wherever possible, but I cannot certify the absence of unconscious
   asymmetry, and no independent party checked the pack. A second agent re-condensing from
   the raw sources without the arm labels would be the proper control and was not run.
   `[asserted]`
3. **The preamble names the stakes**, including that stopping rule 1 is Arm B versus Arm A
   and that ADR-0020's fate rides on it. That was required by the brief, and it creates an
   incentive to guess. The pack now carries an explicit instruction not to. It is a request,
   not a control. `[asserted]`

### What to do with this

If your grades separate Arm A from Arm B cleanly, that result stands — the A/B blinding is
sound.

If your grades separate Arm C from the other two, discount that separation to the extent
you found yourself recognising the "None recorded" pattern. Stopping rule 2 (Arm C versus
Arm B) is the weaker of the two conclusions this pack can support, and `exp16-results.md`
already records that the experiment cannot decide it for an independent reason: with
partitioned evidence, Arm C was never the structure the delegation theorem punishes.
`[measured]`

## 8. What was not done

- No git command was run and nothing was committed.
- `exp16-results.md`, `experiment-register.md`, `friction-log.md` and the ADRs were not
  touched; other writers hold those.
- The Linear mirror (HIR-47…52) was not read; the ClickUp transcript was the Arm B source
  and the Linear leg is a tooling finding, not a separate decision set.
- No cost figures appear anywhere in `grading-pack.md`. `[measured]`
