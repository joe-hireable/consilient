# 5-Dimension Design Critique — vendored reference

- **Source:** `nexu-io/open-design`, `design-templates/critique/SKILL.md`
- **Upstream's own credited source:** `alchaincyf/huashu-design` (MIT) — the
  expert-critique flow that inspired the 5-dimension structure
- **Licence:** Apache-2.0
- **Pinned content hash (git blob SHA):** `0e8d6ccfd1769820b10916083ca152d3a250b4a4`
- **Fetched:** 21 August 2026
- **Upstream URL:** https://github.com/nexu-io/open-design/blob/0e8d6ccfd1769820b10916083ca152d3a250b4a4/design-templates/critique/SKILL.md

This file carries the five dimensions and their scoring bands so that a harness
reading only this repository can run a design critique without fetching from the
upstream registry at agent runtime (ADR-0016 requires vendoring third-party
skills rather than resolving at runtime). The workflow steps and HTML-report contract from the upstream skill are omitted
here; the full upstream skill also specifies a radar-chart SVG output and an
HTML artefact shape.

---

## The 5 dimensions

Each dimension is independent — a surface can score 9/10 on Innovation but
4/10 on Hierarchy and the report should say so plainly. Do not average away
interesting failures.

### 1. Philosophy consistency

Does the artefact pick a clear *direction* and stick to it through every
micro-decision (chrome, spacing, accent, typographic register)?

- **0–4** Three styles fighting each other.
- **5–6** One direction but half the elements drift.
- **7–8** Coherent, occasional drift on edge pages.
- **9–10** Every element argues for the same thesis.

### 2. Visual hierarchy

Can a stranger figure out what to read first, second, third — without being
told?

- **0–4** Everything shouts.
- **5–6** Hierarchy works on hero pages but breaks on body.
- **7–8** Clear tiers, occasional collision.
- **9–10** Eye moves with zero friction.

### 3. Detail execution

The 90/10 stuff — alignment, leading, kerning at large sizes, image framing,
spacing edge cases.

- **0–4** Visible tape and string.
- **5–6** Most pages clean, 1–2 ragged.
- **7–8** Polished, expert eye finds 2–3 misses.
- **9–10** Magazine-grade.

### 4. Functionality

Does the artefact *work* for its intended use? Click targets, navigation,
readability at presentation distance, copy-paste-ability for code blocks.

- **0–4** Visually fine but does not accomplish its job.
- **5–6** Core flow works, edge cases broken.
- **7–8** Robust through normal use.
- **9–10** Defensively engineered.

### 5. Innovation

Does this push past the median? Is there one element that makes people lean
in?

- **0–4** Generic AI-slop median.
- **5–6** Competent and unmemorable.
- **7–8** One memorable moment, the rest solid.
- **9–10** Multiple moves you would steal — but each one obviously serves the
  thesis.

## Scoring discipline

- **Always cite evidence.** "Scored 4 because the hero mixes Playfair with
  Inter on the same line" beats "feels inconsistent". Numbers without evidence
  are rejected.
- **Do not average up.** If Hierarchy is 5 because page 3 is broken, do not
  bump to 7 because pages 1 and 2 are fine. The score is the *worst sustained
  band*.
- **Do not grade-inflate.** A 7 means *strong*, not *acceptable*. Overall mean
  above 8 is suspicious; check yourself.
- **Innovation is allowed to be low.** 5/10 is fine for production deliverables.
  Do not punish appropriate conservatism.

## Action lists

After scoring, produce three lists:

- **Keep** (3–5 bullets) — concrete things working; cite by class, page, or
  element.
- **Fix** (3–6 bullets) — must-do, ordered by visual cost saved per minute
  spent.
- **Quick wins** (3–5 bullets) — 5–15-minute tweaks with disproportionate
  impact.
