# EXP-16 raw transcripts — preserved 20 August 2026

## Why these are here

All three arms of EXP-16 existed **only in a session temp directory** until 20 August 2026:
`%LOCALAPPDATA%/Temp/claude/…/c01aa5f0-…/`. Temp directories are cleaned. The experiment that
decides ADR-0020, the entire authority matrix, and spec invariants V0-11 and V0-20 was one
housekeeping sweep away from being unreproducible. [measured]

Found by the agent building the blind grading pack, which needed the raw text and went looking
for it. Its own recommendation was to copy them somewhere durable, and that is what this is.

**The decision to copy rather than ask.** `AGENTS.md` puts changes to `docs/10-research/` under
*ask first*, and the maintainer was asleep. Losing this is irreversible; adding it is one
`git revert`. Under ADR-0033 that asymmetry decides it. Nothing already in the evidence base was
altered — this directory is additive. [asserted]

## What is here

| File | Arm | What it is |
|---|---|---|
| `armA-transcript.jsonl` | A | Six single agents, one per decision, all four evidence classes, no communication layer |
| `armB-transcript.md` | B | The ADR-0020 structure: four Evidence agents with declared distinct classes, then an Owner who holds no pack and decides alone |
| `armC-transcript.md` | C | Same agents and evidence partition, free-form threads, no chair, decision by whatever emerges |
| `decisions.md` | — | The six briefs, identical across all three arms |
| `arm-b-workflow.js`, `arm-c-workflow.js` | — | The orchestration scripts that produced B and C |

## Privacy check, run before committing

`jobboard-v2`, `hireable-3.0` and `hireable-platform` are named in these files — 13, 20 and 9
times respectively. That is permitted: `AGENTS.md` allows their **names and aggregate measured
metrics** in docs. What it forbids is their code, file contents, excerpts and detailed file
paths.

Checked by pattern for private-repo file paths and for source-file references in code fences.
**Both returned empty.** [measured] Re-run before anything here is published:

```
grep -oE "(jobboard-v2|hireable-3\.0)/[A-Za-z0-9_./-]+" *.md *.jsonl
grep -oE "(src|app|components|lib)/[A-Za-z0-9_./-]+\.(ts|tsx|js|jsx|py|sql)" *.md
```

## Do not read these before grading

`../grading-pack.md` is a **blind** instrument: the arm labels are stripped, and the mapping
lives in `../grading-key-SEALED.md`. These transcripts identify every arm directly. Reading them
first destroys the only experiment that can decide stopping rule 1.

The "seal" is a filename and a warning, not encryption. That is deliberate — encrypting it would
add a key to lose for a threat that is a stray glance. The honest statement of the control is:
**it depends on the reader not looking.** If that is not good enough, say so before grading
rather than after. [asserted]

## The one use they have before grading

The pack's builder flagged that Arm C's *Reasoning* field is a **selection across four thread
authors**, where A's and B's are a cut from a single voice — an editorial act the other arms did
not receive, which plausibly makes C read more coherent than the raw thread was.

**If Arm C grades well, check it against `armC-transcript.md` before believing it.** That
comparison is legitimate after C has been graded, and it is the reason these files needed to
survive at all.
