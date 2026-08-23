# Instruction evidence — 2026-08-23

[measured] The fixed six-month window was searched, but the local evidence base contains records only from 20 July to the 23 August 2026 cutoff: 1,730 JSONL files totalling 682,637,423 bytes (682.64 MB) when scanned, with 270 non-null raw session identifiers; it is not a 789-MB corpus of 1,730 distinct conversations.

## Method

[measured] The bounded parser reused the EXP-45 streaming approach: UTF-8 with replacement, line-by-line JSON, timestamp cutoff, recorded-session grouping and UUID deduplication. It parsed 191,546 lines with zero malformed JSON records and retained 174,982 records at or before 2026-08-23 11:20:09 UTC.

[measured] The byte total is the directory size at scan time rather than a reconstruction at the cutoff; record-level filtering excluded 60 records written after the cutoff.

[measured] The correction population contains 316 main-chain follow-ups across 12 sessions. Only records explicitly marked `typed` or `queued` were eligible; sidechains, tool results, non-text records, SDK/system prompts, records with absent authorship metadata, duplicate UUIDs, XML-prefixed control records and each session's opening retained message were excluded. No transcript excerpt, name, session identifier, transcript-derived or private repository path, credential, tool payload or commit identifier was emitted.

[asserted] Categories are high-precision, case-insensitive lexical classes rather than semantic annotations. Classes overlap; zero means no matching phrase, not proof that the underlying event never occurred. [measured] The frozen high-precision union used for recommendations found 69/316 across 7/12 sessions.

## Repeated correction classes

| Rank | Class | Messages / 316 | Sessions / 12 |
|---:|---|---:|---:|
| 1 | [measured] Locate and beat the existing quality bar | 18 (5.70%) | 2 (16.67%) |
| 2 | [measured] Current research and primary sources | 17 (5.38%) | 5 (41.67%) |
| 3 | [measured] Retain context; avoid repetition | 13 (4.11%) | 4 (33.33%) |
| 4 | [measured] Retry and repair after failure | 9 (2.85%) | 5 (41.67%) |
| 5 | [measured] Verify by artefact or runnable check | 7 (2.22%) | 5 (41.67%) |
| 6 | [measured] Use available tools and agent capacity | 7 (2.22%) | 2 (16.67%) |
| 7 | [measured] Persist to completion | 6 (1.90%) | 3 (25.00%) |
| 8 | [measured] Keep scope surgical | 5 (1.58%) | 3 (25.00%) |
| 9 | [measured] Make progress visible | 3 (0.95%) | 3 (25.00%) |
| 10 | [measured] Output shape and concision | 3 (0.95%) | 2 (16.67%) |

[measured] Additional matches were privacy/external-action boundaries 2/316 in one session, autonomy/no confirmation 1/316 in one, simplicity 1/316 in one, British English 0, explicit anti-sycophancy 0 and budget boundaries 0. None is a recurring cross-session setting in this window.

## Named failures and rates

| Failure class | Messages / 316 | Sessions / 12 |
|---|---:|---:|
| [measured] Static checker omitted before a success claim | 1 (0.32%) | 1 (8.33%) |
| [measured] Exit/process status checked instead of the artefact | 0 (0%) | 0 (0%) |
| [measured] Relative path used after changing directory | 0 (0%) | 0 (0%) |
| [measured] Windows text subprocess omitted UTF-8/replacement handling | 0 (0%) | 0 (0%) |
| [measured] Windows/WSL command or path boundary mishandled | 0 (0%) | 0 (0%) |
| [measured] Timeout failed to kill descendants | 0 (0%) | 0 (0%) |

[measured] Additional recurring classes not named among the brief's examples were context retention 13/316, retry/repair after failure 9/316 and tool/agent/capacity use 7/316.

## Decision

> When an attempt fails, diagnose the root cause, try safe alternatives, and continue until a produced artefact passes the relevant check; stop only at a genuine authority boundary.

[measured] The four constituent classes in this proposed instruction jointly cover 22 distinct follow-ups (6.96%) across 7/12 multi-turn sessions (58.33%).

[asserted] Put this compact behavioural default in genuine personal-instruction surfaces. Keep deterministic checks in hooks, verifiers or shared execution boundaries on their separate evidence; this corpus does not establish transcript recurrence for static/type checks, absolute paths, UTF-8 subprocess capture or descendant timeout handling. Keep task procedures in skills and repository constraints in project instructions.

[measured] `src/consilient/instructions.py` already assembles invariant core, skills, bounded recall and an outcome-gated adapted layer. [asserted] Frequency proposes adapted candidates but cannot promote them; an outcome-labelled experiment must show lower correction incidence without worse verifier rejection, unsafe external action or unfinished work.

[asserted] No source change or second orchestrator is warranted. Existing dispatch, coordination, work-item, recall, routing, budget, instruction and event paths cover the required native placements.

## Falsifier and reversal

[asserted] Blinded annotation finding precision below 90% or materially changing the top-ten order falsifies these rates. Withdraw the rates, replace regex labels with the annotations, and rerun when a genuine six-month export exists.
