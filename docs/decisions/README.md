# Architecture Decision Records

Every non-trivial architecture decision in this project gets an ADR. The ADR is the unit of
record — not a chat message, not a commit message, not someone's memory.

## What makes an ADR here different

Three rules, all enforceable:

**1. Every claim carries an evidence tag.**

| Tag | Means | Example |
|---|---|---|
| `[measured]` | Observed in this repo or a real system we ran | "β = 0.08 ± 0.03 over 64 labelled diffs in jobboard-v2" |
| `[simulated]` | Output of a model with assumed functional forms | "β* ≈ 0.11 at a 0.27 capability gap" |
| `[cited]` | From a source, with the source named | "Delegated networks are dominated by centralised Bayes (arXiv:2603.26993)" |
| `[algebra]` | Exact derivation, no assumptions beyond the stated ones | "n_max = T_cycle / T_review" |
| `[asserted]` | Someone's judgement, no evidence yet | "A local-first store will feel better to contributors" |

`[asserted]` is not shameful. Pretending `[asserted]` is `[measured]` is.
**Never upgrade a tag without new evidence.** Downgrades are allowed and expected.

**2. Decisions that clear the Inquiry-tier bar ship with an executable model.**

`0007-cheap-first-routing.md` ships alongside `0007-model.py`. CI re-runs it. If the model
no longer produces the same sign, the build fails and the ADR is marked `SUPERSEDED` or the
model is fixed. This is the Engineering Ratchet applied to reasoning rather than code.

Not every ADR needs one — see `../20-design/inquiry-tier.md` for the four gates. Roughly:
one-way doors with dispersed priors and a formalizable structure get a model. Naming
conventions do not.

**3. Sources are cited properly, including the ones that disagree.**

An ADR that cites only supporting work is advocacy, not a record. Where the literature
cuts against the decision, say so in the ADR and say why you did it anyway.

## Statuses

`PROPOSED` → `ACCEPTED` → (`SUPERSEDED by NNNN` | `DEPRECATED`)

Plus one this project adds: **`PROVISIONAL`** — accepted for now, but resting on
`[simulated]` or `[asserted]` evidence, with a named experiment that would confirm or kill
it. A `PROVISIONAL` ADR that has sat unconfirmed for three months is a bug.

## Numbering and files

```
docs/decisions/
  README.md              this file
  _template.md
  NNNN-kebab-title.md
  NNNN-model.py          optional executable model
  index.md               generated; do not hand-edit
```

Four digits, monotonic, never reused. Title is the decision, not the topic:
`0007-route-cheap-first-with-verifier-escalation.md`, not `0007-routing.md`.

## Relationship to the other docs

- `../00-context/decisions-so-far.md` is the **session log** — a fast, informal record of
  what was decided in conversation. It is the raw material.
- `docs/decisions/` is the **formal record**. Backfilling from the session log into ADRs is
  a task for the brainstorm phase (see `../00-context/open-questions.md`).
- `../10-research/` holds the evidence base ADRs cite.

Do not let the session log become the record. It has no evidence tags and no review.

## Superseding, not editing

Never rewrite an ACCEPTED ADR to reflect a changed mind. Write a new one that supersedes it
and say what changed and why. The value of this directory is the trail of reversals, which
is exactly what a reader in six months needs and exactly what gets deleted first.
