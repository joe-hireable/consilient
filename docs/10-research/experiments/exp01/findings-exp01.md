# EXP-01 findings — first β measurement on real repositories

Run 19 Aug 2026. Method: mine RECORDED CI verdicts (statusCheckRollup at merge) via the
GitHub API — no check replay needed for the first pass — then proxy-label outcomes and
**audit the labels** (32-agent sample, one agent per sampled label, verdicts
abstract-only). Per the privacy rule (AGENTS.md): per-PR records live in `data/`
(gitignored, never committed); this file carries aggregates only.

## Raw aggregates `[measured]`

| | jobboard-v2 | hireable-platform |
|---|---|---|
| merged PRs analysed | 300 | 56 |
| CI green at merge | 202 | 42 |
| **CI red but merged anyway** | **98 (33%)** | 7 |
| no recorded checks | 0 | 7 |
| proxy-labelled bad (reverted/hotfixed) | 203 (0/203) | 22 (0/22) |
| **raw** β̂ = P(bad-labelled \| green) | 128/202 = **0.63** | 18/42 = **0.43** |

## The raw numbers are wrong, and measuring *why* is the actual result

The 0.63 on the strongly-verified repo is self-refuting, and the label audit
(15 bad-pairs + 5 cleans per repo, seeded sample) explains it:

- **Hotfix-label precision: 1/15 ≈ 0.07 on BOTH repos** (Wilson 95% [0.01, 0.30]).
  The fix-regex + file-overlap heuristic fires on conventional-commit `fix(...)` titles
  and shared config/manifest files — it measured development velocity, not defect
  escapes. `[measured]`
- **Clean-label miss rate: ~1/5 per repo** (n=5 each; Wilson [0.04, 0.62]) — the
  14-day/na(ï)ve-window heuristic also misses real escapes. `[measured]`
- Corrected estimates (raw counts × audited precision/miss rates):
  **jobboard-v2 β̂ ≈ 0.12, honest interval ≈ [0.02, 0.42]; hireable-platform β̂ ≈ 0.14,
  wider.** The intervals span the decision threshold — which is precisely ADR-0002's
  predicted regime: *near β\*, small labelled samples cannot decide; report
  insufficient-data, not a verdict.* The instrument's honest output today for both
  repos: **"insufficient data — do not route cheap yet."** `[measured]`, correction
  factors from n=15/n=5 audits — treat as provisional.

**EXP-01's stopping rule does NOT fire yet**: the interval is wide because the *audit*
is small (15 of 128 flagged pairs examined), not because history is exhausted. The path
to a decision-grade β̂ exists and is enumerable: audit all ~146 flagged pairs
(agent-hours, not human-weeks), and replace the naive heuristic with reference-based
labels (`Fixes #N` links, revert references, `closingIssuesReferences` — the API exposes
them) before widening the window.

## Findings that needed no correction

1. **The human overrides the verifier constantly.** 98/300 jobboard-v2 PRs (33%) merged
   with red CI. "The checks accepted it" describes a minority-plus of merges only after
   assuming green-at-merge; on this repo the *human* is the acceptance gate and the CI
   is advisory. Any β instrument must model the override channel, not assume it away.
   `[measured]`
2. **Red CI carried real signal on the strongly-checked repo even when overridden**:
   red-merged PRs drew later "fixes" at 0.77 vs green-merged 0.63 (same labelling noise
   on both sides, RR ≈ 1.2). On the weakly-checked repo: 0.43 vs 0.43 — its red checks
   were uninformative. Suggestive only (proxy labels), but the direction matches the
   thesis: verification quality varies by repo and is measurable. `[measured, noisy]`
3. The two audit-confirmed true escapes are archetypal β events, described abstractly:
   a shipped feature losing a user-visible affordance after reload (checks green), and
   shipped configuration referencing non-existent resources that validation accepted.
   `[measured]`

## Limitations

- Label audit is LLM-judged (same model family as everything else in this project —
  the standing Q19 caveat). Joe spot-checking even 5 verdicts would materially harden it.
- Correction factors from n=15 and n=5 samples; intervals above propagate their Wilson
  bounds and are dominated by them.
- hireable-platform history is short (56 PRs) — it may never support a tight β̂ alone.
- `statusCheckRollup` reflects the checks GitHub recorded; local-only checks (the ~40
  `check:*` scripts run outside CI) are invisible to this pass.

## Next steps (in order)

1. Reference-based labelling (revert links, `Fixes #N`, issue references) → re-mine.
2. Full audit of all flagged pairs with the improved labels (agent-run, human-sampled).
3. Then and only then: compare β̂ against β\*(Δ̂) from ADR-0025's probe (EXP-20) — the
   two-routes consilience check.
