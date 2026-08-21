---
name: adversarial-audit
description: Use before anything leaves this repository or a decision is taken on evidence produced inside it — a draft paper, an ADR about to be accepted, a gate about to be declared passed, a findings file, or a claim of novelty. Covers who may audit (never the author's own model family), the one question that finds holes, the numeric-provenance sweep, the novelty search in the adjacent field, and the refutation pass that stops an audit becoming its own echo. Trigger on "audit", "red team", "check this before we publish", "is this claim safe", "is this novel", "verify the finding", or a claim that all the gates passed.
---

# Adversarial audit

**Auditing a Claude-written artefact with Claude measures consistency, not correctness.**
[measured] — `docs/00-context/cross-family-audit-2026-08-20.md`. That sentence is the whole
method. Everything below follows from it.

Track record, both nights it was run: three defects in about twelve minutes after a 40-test
suite passed and `mypy --strict` was clean; then six defects in one night that three automated
gates had passed. Zero of six candidate publishable claims survived. [measured]

## Who audits

A **different model family from the one that wrote the artefact**, with **no access to the
reasoning that produced it**. Sharing the transcript defeats the point — agreement between
agents that share evidence is echo, not consilience.

Stage the artefact **read-only, outside the repository**, so the auditor cannot quietly fix
what it finds. An auditor that can write becomes a co-author and stops being a witness.

Available families here: Claude, Codex/GPT, Cursor/Gemini, Grok. Use one that did not write
the thing. If only one family is available, say so in the report and mark the audit
`single-family` — that is a weaker instrument, not an equivalent one.

## The question that works

Do not ask "review this". Ask, of every numbered invariant, boundary or gate:

> **Would its check actually catch a violation, and is there a second path to the same state?**

That question found three holes. "Review this code" would very likely have found none.
[measured] It is the `jobboard-v2` shape: a documented boundary that fragmented into five
access paths because nothing banned bypass.

Three specific things it catches, all found here:

- A gate satisfied by a **tautology** — `replay` compared two rebuilds of the same log, so
  drift could not be detected and the gate could not fail. *A gate satisfied by a tautology is
  worse than an open gate, because an open gate is visible.*
- A test that asserts the **claim** rather than the **property** — `lower_bound_on_joint_error`
  was hard-coded `True` with a test asserting it was `True`.
- A constructor that validates **field presence** rather than **field validity** — a `measured`
  β object with zero rejections.

## Numeric provenance: run this on every figure

For each number in the artefact, in order, and stop at the first failure:

1. Does a **producing script** exist, committed, that could emit it?
2. Does the **exact figure appear** in the committed result artefact? Grep the digits. Do not
   rely on memory or on a summary.
3. Is the comparison **like-for-like** — same check set, same sample, same conditional?
4. Did the instrument itself decline to support the claim? A `not_permitted`,
   `insufficient_evidence` or `complete: false` in the result **is the finding**.

This sweep alone produced C1, C2, C5 and C6 in `docs/00-context/corrections-2026-08-21.md`.

## Novelty: search the adjacent field, not your own

Three times in two days this project's novelty search looked in the wrong field. [measured]
The independence result was Knight & Leveson, IEEE TSE **1986**; the composite-β work was
missing Eckhardt & Lee **1985**; harness search was already Meta-Harness, COLM 2026.

So: name the field the claim *would belong to if it were forty years old*, and search that
one. Software-engineering claims about redundant checks live in the reliability literature;
routing claims live in the bandit and model-cascade literature. Finding prior art is a **win** —
cite it and adopt.

## Refute the audit, or the audit is just another opinion

A findings list from one auditor is one model's opinion. Point a **third** family at the
findings themselves and ask it to break them. When this was done, four findings were refuted
outright — including a demonstration exploit that turned out not to move β at all.

Classify every finding: `confirmed` · `partial` · `refuted` · `already-resolved` ·
`unevaluable`. And add the column nobody thinks to ask for:

> **Does a decision turn on this?**

On the first round the answer was *no* for all nine findings — they were documentation-accuracy
defects, not decision defects. That column is what stops an audit generating work.

## Two things that make an audit look stronger than it is

**Consensus does not compound on a shared artefact.** Five reviewers agreeing after reading the
same source lines is *one* source, not five. An independent review-panel project derived the same
rule from its own production failures and tags such findings `static-inference-consensus` to stop
them being counted as corroboration `[cited]`. Say how many *independent* readings a finding has,
not how many agents said it.

**Position changes without new evidence are sycophancy, not convergence.** If reviewers move
toward the majority between rounds and no new fact arrived, the round produced nothing. Count the
moves; a majority of unforced changes means stop and re-dispatch, not publish.

**Before promoting anything to a blocker, name the single cheapest observation that would falsify
it — then make that observation.** A blocker that survived five reviewers and three rounds here
was documentation mistaken for live state; one grep would have killed it `[cited]`.

## Brief the auditor against its own failure modes

All four were observed. Put them in the auditor's brief:

1. Do not conflate a **privacy boundary** with non-existence — content withheld is not content
   missing.
2. Do not confuse your **sandbox's limits** with the artefact's absence — if you could not run
   Python, say so; do not report the result as missing.
3. **Honest labelling is not a gap.** `[asserted]`, `[cited]`, `[ABS]` are the discipline
   working. Do not penalise them.
4. A preserved **historical or superseded** note is not an active contradiction.

## Report shape

Correct the brief in the first paragraph if it is wrong. Then, per finding: the artefact and
line, what is claimed, what the evidence actually supports, classification, decision-impact,
and the cheapest repair. Close with **what you did not check** — an audit that names no blind
spot has one it did not look for.

Tag every claim `[measured]` · `[cited]` · `[asserted]`. Mislabelling is the worst outcome
available to you.

## Harness support

Portable core: everything here. It is a procedure for a reader, not for a tool, and it is
deliberately harness-agnostic because **the audit is only worth anything when it runs on a
harness that did not produce the artefact.** Claude Code reads it as a skill; Codex, Cursor
and Grok CLI reach it through `AGENTS.md`. Paste the four failure modes and the question into
the auditor's brief verbatim when the auditor cannot read this file.

## Adapted from

`wan-huiyan/agent-review-panel` (MIT) — the consensus/sycophancy/falsification-before-promotion
rules and its epistemic tagging, which maps onto this repository's evidence tags. `anthropics/skills`
`skill-creator` (Apache-2.0, Anthropic PBC) — blind comparison, where a judge sees two outputs
without being told which is which. `obra/superpowers` (MIT, Jesse Vincent) — the read-only reviewer
clause, and the rule that a reviewer spawning its own reviewer is a defect rather than extra rigour.
Adapted to this repository's measured incident record; nothing copied verbatim.
