---
name: citing-sources
description: Use whenever writing a `[cited]` claim, an ADR evidence line, a publication draft, or any public statement that rests on external work. Covers the verification-status system in the bibliography, the rule that snippet-only sources cannot be cited publicly, how to promote a source once read, and how to cite numbers without laundering them through secondary sources. Trigger on "cite", "according to", "the paper says", "research shows", or any claim carrying an arXiv ID.
---

# Citing sources

All external sources live in `docs/10-research/bibliography.md`. **Cite from there, never
from memory.** A model's recollection of a paper is a `[asserted]` claim wearing a `[cited]`
costume.

## The verification flags

| Flag | Meaning | Citable publicly? |
|---|---|---|
| `[FULL]` | Paper or page fetched and read | **Yes** |
| `[ABS]` | Abstract or arXiv listing read directly | Only for what the abstract states |
| `[SNIP]` | Seen only in a search-result snippet | **No** |
| `[2ND]` | Known only via blog, aggregator or vendor page | **No** |

Most of the bibliography is `[SNIP]` or `[2ND]`. That is the honest state after one research
session, not a defect — but it is a hard gate on what may leave the repository.

## Before writing any `[cited]` line

1. Open the bibliography. Find the entry.
2. If `[SNIP]` or `[2ND]` — **fetch and read it first.** Then promote the flag and record
   the date.
3. If the claim is a **number**, check you are citing the source that *measured* it, not a
   blog that repeated it. Several figures in the bibliography are flagged specifically
   because they arrived via a Medium post summarising a paper.
4. Write the claim in your own words. Quotes stay short and attributed.

## Numbers deserve extra suspicion

The highest-risk pattern in this repository is a percentage that has been through three
hands: paper → summary blog → our notes → an ADR. Each hop loses conditions, sample sizes
and caveats, and the number survives looking authoritative.

Named examples currently unverified: the 90.7% → 22.5% relay-degradation figure, MemPalace's
recall benchmarks (reported inflated by at least one analysis), the ~351,000-skills figure,
and every memory-tool comparison score.

## Cite what disagrees with you

An ADR's **Evidence against** section is required, and external sources that cut against a
decision belong there. Current examples: *When to Think Deeply* argues against ADR-0009;
FrugalGPT and RouteLLM's real gains argue against ADR-0003.

An ADR that cites only supporting work is advocacy, not a record. If you cannot find
anything against, say what you searched.

## Publication rules

`docs/publications/README.md` sets four gates. Two bear directly here:

- **Is it new?** A documented literature search, including the near misses. If someone did
  it already, cite them and adopt — that is a win, not a loss.
- **Is it honest about limits?** Sample sizes, assumed functional forms, conflicts of
  interest, experiments not run.

Prefer arXiv IDs and DOIs to URLs. URLs rot; identifiers do not.

## Do not redistribute

Papers are copyrighted. Fetch to a gitignored `docs/10-research/sources/` for local reading.
The repository holds citations, not copies.
