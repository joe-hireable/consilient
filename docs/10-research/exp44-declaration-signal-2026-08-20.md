> **This is the falsifier named in `exp44-feasibility-pilot-2026-08-20.md`, and it FIRED.**
> That document said: *"if declared AI share is near zero there too while their commit velocity
> and diff-size distributions have visibly shifted, the declaration signal is not measuring
> adoption, the outer proxy fails, and EXP-44 as designed cannot answer its question at any
> sample size."* Declared share was ≤0.03% across all five repositories in 2023–2024 while
> behavioural indicators shifted markedly. **EXP-44 must narrow its claim, and so must P1.**
>
> **The narrowing is less damaging than it looks, and may be an improvement.** What declaration
> actually measures is *autonomous agent trailer insertion* — which is precisely the regime this
> harness operates in. The general claim ("AI authorship breaks defect proxies") is not
> measurable this way. The specific one ("agent-authored commits break defect proxies") is, and
> it is the one Consilient needs. [asserted]
>
> Weakest link, stated by the agent that ran it: behavioural indicators are confounded by
> ordinary engineering change — commitlint adoption, architectural rewrites — so undeclared
> adoption is noisy to isolate. The 2023–2024 shift is suggestive, not conclusive. [asserted]

# EXP-44 Declaration Signal Feasibility Check

**Repositories Selected:** `[measured]` Five fast-moving application/startup repositories active across 2023–2026: `BerriAI/litellm` (AI proxy gateway), `posthog/posthog` (product analytics platform), `calcom/cal.com` (scheduling infrastructure), `continuedev/continue` (AI coding assistant extension), and `PrefectHQ/prefect` (workflow orchestration). Chosen for small-team review cultures, high commit velocities, and early AI tooling adoption unlike foundation-governed runtimes.

### Declared AI Share by Year `[measured]` (293,846 commits total; 91.8 s total wall-clock across 5 bare blobless clones, 18.4 s/repo)
- **`litellm`:** 2023: **0.00%** (0) · 2024: **0.03%** (4) · 2025: **1.47%** (198) · 2026: **20.32%** (6,361)
- **`posthog`:** 2020–2023: **0.00%** (0) · 2024: **0.03%** (3) · 2025: **2.35%** (710) · 2026: **14.95%** (9,046)
- **`cal.com`:** 2021–2023: **0.00%** (0) · 2024: **0.03%** (1) · 2025: **21.92%** (2,202) · 2026: **48.09%** (2,147)
- **`continue`:** 2023: **0.00%** (0) · 2024: **0.03%** (2) · 2025: **0.70%** (82) · 2026: **13.14%** (163)
- **`prefect`:** 2018–2023: **0.00%** (0) · 2024: **0.00%** (0) · 2025: **23.09%** (644) · 2026: **61.34%** (1,460)

### Behavioural Shift vs Declaration `[measured]`
1. **The 2023–2024 Blind Spot:** In 2023–2024, declared AI share was $\le 0.03\%$ across all five repositories. Yet behavioural indicators shifted markedly: `continue` was authored as an AI-native tool from day one with zero declarations; `cal.com` conventional-commit prefixes rose from 13.0% (2022) to 77.6% (2024); `prefect` mean files touched per commit tripled from 1.8 (2022) to 5.8 (2024); `litellm` commits with message bodies jumped from 4.5% to 23.7%.
2. **The 2025–2026 Agent Surge:** Declared share inflected sharply only in 2025–2026 ($13\%\text{--}61\%$), driven exclusively by automated agent bot integrations and trailer-emitting harnesses (`Claude Opus`, `Cursor Agent`, `Devin AI [bot]`) rather than interactive Copilot/IDE autocomplete.

### One-Line Verdict `[asserted]`
**Declaration does not track adoption:** it measures autonomous agent trailer insertion in 2025–2026 while remaining blind to 2023–2024 IDE-level adoption; EXP-44 must narrow its claim to declared agentic workflows rather than general AI adoption.

### Weakest Link in Method `[asserted]`
Behavioural indicators (commit styles, diff sizes) are heavily confounded by non-AI organisational changes (e.g. commitlint adoption in PostHog 2022, architectural rewrites in Prefect), making undeclared adoption noisy to isolate from ordinary engineering scaling.
