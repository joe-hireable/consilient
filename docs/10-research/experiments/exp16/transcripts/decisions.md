# EXP-16 decision briefs (identical across all three arms)

Six genuinely open decisions from docs/00-context/open-questions.md, 19 Aug 2026. Each
decision must produce: THE DECISION (one sentence), RATIONALE (which evidence, by class),
WHAT WOULD OVERTURN IT (one falsifier), and DISSENT (real disagreement, not smoothed).

## D1 — Plugin or standalone? (ADR-0001 open alternative)
Should the β-meter ship as a plugin to HKUDS/OpenHarness (existing hooks, tool registry,
nonzero audience, but v0.1.x surface and another team's roadmap) or as the standalone
meta-harness ADR-0001 currently commits to? A good answer weighs maintenance tax, audience,
name collision, and what happens when OpenHarness's surface breaks.

## D2 — What is v0's success condition? (Q4)
Full-OSS, no revenue, Joe's hours binding. What is the smallest thing worth a stranger's
`npm install`? What is the smallest thing that makes Joe's own week better? Are they the
same artifact? If not, which is being built? The answer must name a concrete artifact and
a measurable success condition, not a vibe.

## D3 — Does the Inquiry tier belong in v0? (Q14)
The four-gate research trigger (reversibility, blast radius, prior dispersion,
formalizability) is the most intellectually interesting part of the design and possibly
the least urgent. In v0, or deferred? The answer must argue both sides before choosing.

## D4 — What is in v0, honestly? (Q15)
Candidate list: β-meter + cascade + parallel worktrees + budget primitives + critic tier.
Is even that too much for one person? What gets cut? (This is partly preferential — Joe's
appetite for scope is evidence no agent holds.)

## D5 — Does the local model library belong in v0? (Q23)
Hardware-gated local-model discovery is a substantial cross-platform feature for a pre-v0
project. The cascade needs *a* cheap tier — but that could be a cheap API model with no
library at all. In, out, or wrapped (LM Studio et al.) at v0?

## D6 — Executable-model CI ratchet: keep or drop? (Q13)
The proposal: an ADR ships with a runnable decision model; CI re-runs it; a sign flip
fails the build. Genuinely useful, or ceremony with a maintenance cost (dependency rot)?
EXP-10 would measure it over three months — but should the mechanism exist at all in v0?
