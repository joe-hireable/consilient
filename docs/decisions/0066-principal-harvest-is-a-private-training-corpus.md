# 0066. The principal's Consilient usage is a private training corpus; fine-tunes are native backends; the data is never published

- **Status:** ACCEPTED 21 August 2026. Accepted by Joe Brown in the orchestration chat: harvest his Consilient usage across the four paid harness subscriptions, train local models in the 30–35B class, keep the data unpublished, and reuse it as new bases appear. Recorded here because "used to improve Consilient" in [0057](0057-a-users-trajectory-is-their-data.md) named the *purpose* and not the *path*.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the instruction). Operator (the mechanism: gitignored harvest, refuse-if-publishable dest, adapters as native backends under 0026/0027/0054).
- **Extends:** [0057](0057-a-users-trajectory-is-their-data.md) (privacy), [0064](0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md) (local-first training), [0018](0018-self-modification-gated-by-measured-verifier.md) (no promotion on unmeasured β), [0027](0027-compose-domain-harness-provider-and-model.md) (a fine-tune is a *model*, not a routing policy), [0065](0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md) (judgement stays native; the trained weights are a backend).
- **Does not supersede:** 0057 (the data remains the user's), 0018 (RSI/RL still cannot persist without measured β), 0003 (this is not a learned routing policy in v0).
- **Inquiry tier reached:** T1 ground — the privacy rule is already decided; the new work is the harvest chokepoint and the native-backend admission.
- **Executable model:** none — whose data this is, and whether it may be published, is a values decision. Gate G4 is not satisfied.

## Context

Joe's instruction, 21 August 2026, restated as execution rather than as a menu:

1. **His** Consilient usage trains **his** models.
2. The training data is **never released publicly**.
3. The resulting models may be used as **native** Consilient backends.
4. Start from the best current open weights around **30–35B**, trained locally on the RTX 5090 / 64 GB rig, for free, on traces from Claude Code, Codex, SuperGrok Heavy and Cursor Ultra.
5. Train specifically where those subscriptions are currently unreliable.
6. The same corpus feeds reinforcement learning, reflective self-learning and recursive self-learning.
7. The corpus must survive a base-model swap: new frontiers drop, the harvest does not start from scratch.
8. Whenever a frontier / expensive model is used, the interaction is harvested.

[0057](0057-a-users-trajectory-is-their-data.md) already forbids publishing the trajectory and permits opt-in use "to improve Consilient only." It does not say *how*. Without a harvest path, "improve Consilient" is a hope and the expensive traces sit in gitignored dispatch folders until a disk is wiped.

[0064](0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md) already says local-first fine-tunes on this machine. It does not say the *corpus* is the principal's Consilient usage, nor that adapters persist across base-model generations.

Two one-way doors:

- Publishing the harvest cannot be undone (0057, the same incident).
- Training a competing public model on vendor outputs may be a terms-of-service violation even if the weights never leave the machine. Harvest-for-private-use is the conservative reading of his words; shipping a distilled model is not authorised by this ADR.

## Decision

**Every dispatch of a paid or frontier harness is harvested into a private, durable corpus that is never tracked and never published. Fine-tunes of open 30–35B-class bases on that corpus are native Consilient backends. They are admitted to routing only under the existing hardware-fit and measured-capability rules. Recursive or reflective self-learning may *consume* the harvest; it may not *persist a change* until ADR-0018's β gate says so.**

Concretely:

1. **Harvest is the default, not an opt-in.** `scripts/harvest.py` projects `.harness/log` and `.harness/dispatch/<run-id>/` into append-only JSONL. A frontier run that produces no harvest line is a defect in the harvest, not a choice.
2. **The dest is unpublishable by construction.** Default is `.harness/training/` (gitignored). `--out` may be an absolute path *outside* this repository (a disk Joe owns, or a folder a private sync tool already mirrors). A dest *inside* the repository that is not gitignored is refused. GitHub, Hugging Face public, and any path the public remote can reach are not dests.
3. **The corpus outlives the base.** Harvest JSONL plus adapter directories are the durable artefact. When a better 30–35B base is released, training starts from that base on the *same* harvest; it does not replay the four subscriptions.
4. **A fine-tune is a model, not a policy.** Composition stays domain × harness × provider × model (0027). The trained weights are the model. Routing them still requires hardware fit (0026) and a measured capability against a verifier contract (0054). An unmeasured adapter is a local file, not a default route.
5. **RSI/RL read the harvest; they do not write the product.** Reflective and recursive loops that *propose* a change go through `promote.decide`. Unmeasured promoter β refuses persistence (0018, measured composite β ≈ 0.31). This ADR does not lower that gate.
6. **Starting bases, retrieved 21 August 2026, not recalled.** For a single RTX 5090-class box in the 30–35B band the current open-weight candidates are **Qwen3-Coder 30B-A3B** (agentic coding, ~19 GB Q4, 24 GB-class) `[cited]`, **Qwen3.6-35B-A3B** (lab-reported SWE-bench Verified 73.4%, Q4 claimed to fit a 5090) `[cited]`, and **Gemma 4 31B** dense (Apache-2.0, BenchAlign v5 score 60 on 21 Aug 2026) `[cited]`. The first two are the coding/agent harvest targets; Gemma is the different-class dense baseline. This ADR does not download them. Acquisition still goes through `acquire_local_model`.

## Evidence

- `[measured]` `.harness/log/` and `.harness/dispatch/` are already gitignored (ADR-0057). Two days of trajectory reached the public remote *before* that ignore existed. A second copy of the same data under a tracked `data/training/` would recreate the incident.
- `[measured]` Dispatch already records harness, family, pool, task, status, artefact bytes and the brief/stdout under a run id. The expensive interaction is already on disk; it is not being captured by a training projector.
- `[cited]` 0057: the principal's words — *"my usage of consilient should remain private just like anyone elses unless they agree to share data in which case that is private and used to improve consilient only."* This ADR is the "used to improve" path for the first user, without making the log public.
- `[cited]` 0064: local-first fine-tunes on the 5090; hosted training only prepaid.
- `[cited]` WhatLLM.org, 16 July 2026, *Best Local LLM for Coding in 2026*: Qwen3-Coder 30B-A3B as the 24 GB coding sweet spot, official Ollama Q4 ~19 GB. Retrieved 21 August 2026.
- `[cited]` Heiko P., *The State of Open Coding AI Models in August 2026*, Towards AI, 10 August 2026: Qwen 3.6-35B-A3B claimed to fit a single RTX 5090 at Q4; Qwen lab SWE-bench Verified 73.4%. Retrieved 21 August 2026. Vendor numbers, not our measurement.
- `[cited]` BenchLM.ai open-weight leaderboard, data verified 21 August 2026: Gemma 4 31B dense, Apache-2.0, BenchAlign v5 score 60, reference hardware 1× RTX 4090 24 GB.
- `[cited]` 0018: no self-modification on an unmeasured acceptance signal. Live-SWE-agent cut GPT-5-Nano from 44% to 14% after building task-local tools `[cited]` in `instructions.py`.
- `[asserted]` The different class of facts a 30–35B fine-tune introduces, relative to Opus/Codex/Grok/Cursor, is *this user's accepted and rejected traces plus verifier outcomes* — not another copy of pretraining. Agreement between a fine-tune and the teacher on shared evidence is echo; disagreement with a human verdict is signal.

## Evidence against

- `[asserted]` **Vendor terms of service.** Anthropic, OpenAI, xAI and Cursor historically restrict using their outputs to train competing models. Private local adapters for the account that paid for the traces is the reading most likely to match his intent; it is not legal advice, and **this ADR does not authorise distributing a distilled model**. A ToS that forbids even private fine-tunes would overturn clause 1 for that vendor; harvest of *our* trajectory metadata (task, verdict, checks, artefact hashes) would still stand.
- `[cited]` **Distillation rarely matches the teacher.** The 30–35B class is behind the closed frontier on unified leaderboards (BenchLM, 21 Aug 2026: double-digit gap between open-weight and proprietary leaders). Fine-tuning on traces can specialise; it will not turn Qwen-Coder into Opus. Claiming "exceedingly more reliable" before a measured β on the adapter is the failure 0018 exists to prevent.
- `[cited]` **Recursive self-learning without a sound verifier is how the field already failed.** 0018's prior-art table: DGM, SICA, Live-SWE-agent all promote on test-says-better. Our measured composite β is not below the persistence threshold. This ADR feeds those loops; it does not turn them on.
- `[asserted]` **A private cloud copy is a second leak surface.** "Free storage" that Consilient reaches (GitHub LFS, a public bucket, an HF dataset under `joe-hireable`) is a public repository by another name. The dest-outside-repo allowance is for a folder *Joe already syncs with a tool he controls*. Consilient does not grow a network client to upload harvest.
- **Single operator, one machine.** The harvest schema will drift. That is cheaper than a second source of truth in `docs/`.

## Consequences

**Positive** — expensive traces become a corpus instead of a disk full of gitignored transcripts. New bases reuse the same harvest. Privacy is a check, not a promise.

**Negative** — disk grows with every dispatch; harvest JSONL will contain file contents from worktrees (including commercial ones). That is why it must never be tracked. A careless `--out` to a path inside the repo is refused, but `--out` to a Dropbox folder that later syncs publicly is Joe's to not do.

**Neutral but load-bearing** — a fine-tune is not a Gate B pass and not a routing default. Native means "Consilient can run it locally as a model"; it does not mean "the public package ships Joe's weights."

## Enforcement

- Check: `tests/test_harvest.py` — dest inside the repo and not gitignored raises; dest gitignored or outside the repo is accepted; duplicate `run_id` is skipped; a frontier dispatch example is written; `.harness/training/` is gitignored and untracked.
- Check: `test_no_user_trajectory_is_tracked` remains; a sibling `test_no_training_corpus_is_tracked` covers `.harness/training/`.
- Fails CI: yes.
- Same commit as the implementation: yes.
- Not a check: the weights. They never enter git.

## What would overturn this

- The principal forbids using subscription outputs even privately. Then harvest metadata only (run_id, harness, status, verdict) and drop transcripts.
- A measured adapter β worse than the teacher on the same tasks, with interval. Then stop promoting that adapter; keep harvesting.
- ADR-0018's β gate passing. Then RSI may persist, still from this harvest, not instead of it.

## Publication candidate?

No. The decision is instance law for the first user's data. The general claim — user traces train user-local adapters, never a public corpus — is already in 0057 and 0064.
