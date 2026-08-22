# Ruflo teardown — 22 August 2026

**Correction to the dispatch's framework-or-meta-harness dichotomy.** Ruflo is a hybrid: at the pinned revision it contains a source-implemented Claude Code/Codex meta-harness and a substantive opt-in evaluation flywheel, while its default `swarm`, `agent_spawn`, and `hive-mind_spawn` surfaces mostly persist coordination records and its “100+ agents” are principally Markdown prompt/tool manifests. Real-model dual operation is reported upstream but was not reproduced here. [cited] [measured] [inferred]

**Snapshot:** retrieved 2026-08-22T15:56:12Z; repository `ruvnet/ruflo`; revision [`5234333c3462`](https://github.com/ruvnet/ruflo/tree/5234333c3462), the unique 12-character prefix of the then-current `main` HEAD and release `3.38.16`. [measured: `git ls-remote`, shallow clone, `git rev-parse`, 2026-08-22]

**Report completed:** 2026-08-22T16:27:54Z. [measured: local clock]

The dispatch brief said “about 7,387 commits”; the GitHub commit API's `rel="last"` link reported exactly 7,387 on `main`, so that premise was accurate at retrieval time. ([GitHub commits API](https://api.github.com/repos/ruvnet/ruflo/commits?sha=main&per_page=1)) [measured: 2026-08-22]

The live Consilient product bar omitted the product under both current and legacy identities: a case-insensitive literal search of `docs/00-context/product-bar-2026-08-22.md` returned zero matches for `ruflo`, `ruvnet`, `claude-flow`, `claude flow` and `claudeflow`. [measured: local working tree, 2026-08-22]

That omission is material. Ruflo is closer than Hermes specifically to Consilient's **cross-harness command-post** shape because its dual path selects between two vendor CLIs, whereas Hermes delegates nested Hermes agents and coordinates named profiles; Hermes remains the stronger inspected working product for atomic task claiming and durable peer work. Ruflo is not yet a proven **outcome** incumbent because no matched comparison measures accepted work, acceptance error, authority, durability, learning and total cost together. [cited: `docs/00-context/hermes-teardown-2026-08-22.md:9-29,67-115,253-268,362-376`] [inferred]

This high-churn snapshot must be rechecked before an adoption/publication decision at the next Ruflo release or after 30 days, whichever comes first. [asserted]

## Direct answers

| Question | Answer |
|---|---|
| Is Ruflo an actual meta-harness? | **Yes at the implementation level; live operation on this host is unproven.** `dual run` reaches child-process calls for Claude Code and Codex, headless mode reaches Claude Code, and hive mode reaches a Claude Queen process. The default MCP swarm and spawn calls are mostly registries, and the focused Windows dual slice was red, so “Ruflo is the harness” overstates both uniformity and reproduced operability. [cited] [measured] [inferred] |
| Is it closer to Consilient than Hermes? | **On the cross-harness axis, yes; overall, not established.** Ruflo selects distinct vendor harnesses and exposes a candidate/evaluate/promote loop; Hermes has stronger measured atomic task claiming and durable peer coordination. Neither has a matched outcome win over Consilient. [cited] [inferred] |
| Are “100+ agents” independent capabilities? | **No by count alone.** The measured count is predominantly Markdown persona/tool manifests; whether two executions introduce different classes of facts depends on their actual model, tools and evidence. [cited] [measured] [inferred] |
| Does Ruflo already provide cross-model or cross-harness memory? | **It provides the facility.** Source binds Claude and Codex workers to one SQLite/HNSW path and prompts them to invoke it; a local two-process CLI proof survived process exit. No live child-harness run established that workers actually used the store or improved an outcome. [cited] [measured] [inferred] |
| Is “self-learning” training? | **Mostly no, sometimes yes.** The usual paths update retrieved patterns, confidence, trajectories and routing priors; the explicit `neural train` path fits and checkpoints a local adapter. Neither path mutates Claude, Codex or a remote provider's foundation weights. [cited] |
| Does it measure correctness? | **Partly.** It ships a pinned GAIA outcome record and a held-out retrieval flywheel with a frozen human-labelled anchor. It also has β-shaped security counts, but no valid estimate of `P(machine accepts | independently labelled bad)` for terminal work artefacts was found. [cited] [measured] [inferred] |
| Does it enforce one Owner or prevent collisions? | **No.** Main tasks allow multiple assignees, stores are unlocked JSON read/modify/write, issue claims are non-atomic, and no single synthesis Owner owns the terminal candidate. Dual-mode worktree separation is a useful narrower guard. [cited] [inferred] |
| Can Consilient claim superiority today? | **No.** Ruflo was missing from the bar; Consilient's Gate A and Gate B remain shut; its one-Owner rule is still a specification; and its current path claims also have a check-then-append race. The defensible claim is a narrower measurement and evidence-control delta awaiting a matched experiment. [measured] [asserted] |

## Evidence classes and boundary

This report keeps three evidence classes separate. [asserted]

- **Read:** commit-pinned source, manifests, tests, CI, benchmark artefacts, licence files, the repository's own audit, and direct GitHub issue/PR bodies. [cited]
- **Run:** credential-free installation, tests, source audits, CLI memory operations and file/count checks on Windows 11 with Node `v24.14.1`, npm `11.11.0` and Python `3.13.11`. [measured]
- **Infer:** architectural classification, race reachability, independence-of-class, comparison to Consilient and adoption advice. [inferred]

No Ruflo test or capability run invoked Anthropic, OpenAI, OpenRouter, Ollama or another metered generation provider, and no provider credential was supplied to Ruflo. The embedding path may have used a pre-existing cache or downloaded an open MiniLM model; no network capture was running, so a network-free claim is not made. [asserted]

No live Claude Code/Codex dual task, real GAIA run or GPU training run was attempted, because those require credentials, metered calls or installed harnesses beyond the credential-free Ruflo boundary. [measured]

After the Ruflo executions, the repository-mandated adversarial audit used a separate Claude-family model against the report only through an existing non-metered subscription; its CLI reported `$0.58739` provider-equivalent cost, not an incremental API charge. A third-family Grok refutation attempt produced no output within its bound and was terminated, so the audit remains one independent cross-family reading rather than triangulation. [measured: Claude/Grok CLI, tools disabled, 2026-08-22]

The test checkout was a throwaway shallow clone outside the Consilient repository. No Ruflo source was modified; generated `node_modules`, temporary test files and an ignored security build were not committed. [measured]

The sole Consilient deliverable is this report. The experiment register, ADR index, product source and gates were not changed. [measured]

### Bounded negative search

At the pinned snapshot, `rg` searched tracked TypeScript, JavaScript, Python, Markdown, JSON and YAML, excluding `node_modules`, `dist` and coverage output. The first pass used `false accept`, `machine accept`, `human reject`, `acceptance error`, `confusion matrix`, `independently bad`, `bad artifact`, `ground truth`, `human label`, `P(...accept` and `beta calibration`; an adversarial audit then caused a second pass over `false negative`, `FNR`, `miss rate`, `escape rate`, `defect escape`, `type II`, `specificity`, `NPV`, `precision`, `false discovery`, `FDR`, `unflagged`, `undetected` and `false positive`. [measured]

The first pass returned zero `false accept`, `machine accept`, `human reject`, `acceptance error`, `independently bad`, `bad artifact` and `beta calibration` hits. The expanded pass found false-negative reward code, retrieval miss rates, a proposed browser unsafe-action escape target, scanner precision/recall records and FDR evolution controls; none supplied a terminal machine-accept versus independently labelled artefact table. [measured]

The search did find GAIA ground truth, retrieval labels, a security corpus with TP/FP/TN/FN, an adversarial scanner bypass set and a frozen human-labelled retrieval anchor; those are examined below rather than being discarded as false positives. [measured]

This is a snapshot-bounded source finding, not proof that an external service or uninspected branch has never measured acceptance error. [asserted]

## What the product actually is

### Entry point and execution surfaces

The published `ruflo` package is a small Node wrapper around `@claude-flow/cli`; it selects MCP stdio mode when piped and otherwise constructs the branded CLI. [cited: [`ruflo/package.json#L2-L9`](https://github.com/ruvnet/ruflo/blob/5234333c3462/ruflo/package.json#L2-L9), [`ruflo/bin/ruflo.js#L29-L66`](https://github.com/ruvnet/ruflo/blob/5234333c3462/ruflo/bin/ruflo.js#L29-L66)]

The legacy `claude-flow` binary imports the same CLI, while the root package bundles the Codex and federation packages. [cited: [`bin/cli.js#L1-L11`](https://github.com/ruvnet/ruflo/blob/5234333c3462/bin/cli.js#L1-L11), [`package.json#L1-L14`](https://github.com/ruvnet/ruflo/blob/5234333c3462/package.json#L1-L14)]

Its execution architecture is hybrid rather than one uniform harness boundary. [inferred]

- Hive mode launches one Claude Code process with a Queen prompt. [cited: [`hive-mind.ts#L232-L332`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/hive-mind.ts#L232-L332)]
- Headless workers invoke `claude --print --output-format json`. [cited: [`headless-worker-executor.ts#L1368-L1405`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/headless-worker-executor.ts#L1368-L1405)]
- Dual mode constructs `claude -p ...` and `codex exec ...`, then uses `child_process.spawn`. [cited: [`orchestrator.ts#L190-L232`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L190-L232)]
- `agent_execute` instead calls Anthropic, OpenRouter or Ollama-compatible HTTP endpoints directly. [cited: [`agent-execute-core.ts#L158-L273`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L158-L273), [`#L417-L452`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L417-L452)]

Therefore the strongest surface satisfies the implementation-level meaning of meta-harness—one program reaches child-process invocations for multiple existing harnesses—but the raw-HTTP agent path is an agent framework/provider client, not a child-harness invocation. Upstream issue [#2947](https://github.com/ruvnet/ruflo/issues/2947) reports real Codex and heterogeneous-model completion after the stdin fix; that report is cited evidence, not a local reproduction. [cited] [inferred]

### Registration is not execution

`agent_spawn` persists an agent record and returns `status: registered`; its response explicitly lists direct API, native Claude Task and `claude -p` as separate execution choices. [cited: [`agent-tools.ts#L435-L453`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-tools.ts#L435-L453)]

`swarm_init` creates a record containing a topology label, limits and empty agent/task arrays; its comment says the CLI PID is not the swarm lifetime. [cited: [`swarm-tools.ts#L32-L58`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/swarm-tools.ts#L32-L58), [`#L296-L335`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/swarm-tools.ts#L296-L335)]

The MCP `hive-mind_spawn` loop similarly writes idle worker records and reports them as spawned without starting a process or provider request. [cited: [`hive-mind-tools.ts#L249-L294`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/hive-mind-tools.ts#L249-L294)]

The richer standalone swarm package has parent identifiers and a fifteen-agent hierarchy, but the main CLI's MCP swarm does not use that coordinator and does not declare the swarm package as a dependency. [cited: [`agent.ts#L41-L72`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/swarm/src/domain/entities/agent.ts#L41-L72), [`unified-coordinator.ts#L1451-L1485`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/swarm/src/unified-coordinator.ts#L1451-L1485), [`cli/package.json#L100-L107`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/package.json#L100-L107)]

This is the recurring implementation pattern: substantial algorithms exist in the monorepo, but the operator-facing path must be traced before assigning their capability to the product. [inferred]

### The genuine dual-mode meta-harness

Dual workers declare a platform, role, prompt, dependencies and optional worktree; the orchestrator builds dependency levels and rejects duplicate IDs, absent dependencies and cycles. [cited: [`orchestrator.ts#L23-L64`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L23-L64), [`#L389-L423`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L389-L423)]

The CLI accepts repeatable `claude|codex:role:prompt` workers, runs sequentially by default, offers bounded parallelism, and keeps unattended swarm automation disabled unless explicitly enabled. [cited: [`dual-mode/cli.ts#L22-L83`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/cli.ts#L22-L83)]

When isolation is enabled, concurrent writers must receive distinct worktrees and writer concurrency is bounded separately. [cited: [`orchestrator.ts#L434-L470`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L434-L470)]

The worktree coordinator refuses a dirty repository, creates detached read-only worktrees or writer branches, retains dirty worker worktrees, and integrates writers by sequential merges. [cited: [`worktrees/coordinator.ts#L34-L151`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/worktrees/coordinator.ts#L34-L151)]

This is a real dependency DAG of child harness processes. It is not recursive nested swarms, and it collects worker results without a separately accountable Owner who alone synthesises and dispositions conflict. [cited] [inferred]

The orchestrator calls `npx ruflo@latest` for memory and policy operations, so a pinned parent revision can execute mutable future child code. That breaks exact replay provenance even though the worker harness commands themselves are concrete. [cited: [`orchestrator.ts#L116-L139`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L116-L139), [`#L480-L538`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L480-L538)]

## What “100+ agents” means

The catalogue generator defines agents by counting tracked Markdown files under `.claude/agents` and plugin agent folders, not by enumerating executor classes, models or independent evidence sources. [cited: [`generate-catalog-manifest.mjs#L3-L17`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/scripts/generate-catalog-manifest.mjs#L3-L17), [`#L80-L84`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/scripts/generate-catalog-manifest.mjs#L80-L84)]

At the pinned checkout, the root `.claude/agents` contained 108 Markdown files, 97 unique frontmatter names and 11 duplicate names; the CLI-bundled agent tree contained 89 Markdown files, 81 unique names and eight duplicates. [measured: PowerShell recursive count and frontmatter parse, 2026-08-22]

Running the committed generator's broader count logic yields 165 Markdown matches, while the checked-in manifest says 164 and is tied to an older SHA; one counted item is explicitly documentation. [cited: [`catalog-manifest.json#L1-L11`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/catalog-manifest.json#L1-L11), [`MIGRATION_SUMMARY.md#L1-L11`](https://github.com/ruvnet/ruflo/blob/5234333c3462/.claude/agents/MIGRATION_SUMMARY.md#L1-L11)] [measured]

A typical entry is YAML frontmatter plus a role prompt; some entries add tool allow-lists, which can specialise a host-created worker but do not create a new model or runtime. [cited: [`coder.md#L1-L27`](https://github.com/ruvnet/ruflo/blob/5234333c3462/.claude/agents/core/coder.md#L1-L27), [`issue-tracker.md#L1-L11`](https://github.com/ruvnet/ruflo/blob/5234333c3462/.claude/agents/github/issue-tracker.md#L1-L11)]

The operator-facing CLI offers fifteen agent types, and direct execution constructs one generic system prompt from the selected type string. [cited: [`commands/agent.ts#L51-L68`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/agent.ts#L51-L68), [`agent-execute-core.ts#L589-L615`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L589-L615)]

Product counts also drift: package metadata says “60+”, README says “100+”, and the manifest says 164. None is a measured count of distinct execution capabilities. [cited: [`ruflo/package.json#L2-L5`](https://github.com/ruvnet/ruflo/blob/5234333c3462/ruflo/package.json#L2-L5), [`README.md#L200-L210`](https://github.com/ruvnet/ruflo/blob/5234333c3462/README.md#L200-L210)]

Under Consilient's difference-of-class rule, two persona prompts over the same model and evidence are echo, not consilience. A Ruflo worker can become a different class when it is actually bound to a different harness, model family, public dataset, tool or independent verifier; the catalogue count alone supplies none of that. [inferred]

## Durable memory across models and harnesses

The default memory store is project-local SQLite at `.swarm/memory.db`, with environment and explicit path overrides. [cited: [`memory-initializer.ts#L88-L161`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/memory-initializer.ts#L88-L161)]

Entries carry content, embeddings, embedding model/dimensions and a typed provenance field; the optional HNSW index has persistent data and metadata paths and is loaded or rebuilt from SQLite after restart. [cited: [`memory-initializer.ts#L19-L38`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/memory-initializer.ts#L19-L38), [`#L214-L269`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/memory-initializer.ts#L214-L269), [`#L613-L709`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/memory-initializer.ts#L613-L709)]

Embeddings normally come from local `Xenova/all-MiniLM-L6-v2` at 384 dimensions, so stored vectors do not depend on the Anthropic/OpenAI/Ollama generation model. [cited: [`memory-initializer.ts#L2208-L2262`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/memory-initializer.ts#L2208-L2262)]

Dual mode places the same `CLAUDE_FLOW_DB_PATH` in Claude and Codex worker environments and prompts each worker to search/store through Ruflo. This is direct source evidence of a cross-harness persistent-memory facility, not evidence that a child complied or that retrieved context improved its result. [cited: [`orchestrator.ts#L279-L295`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L279-L295), [`#L589-L613`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/codex/src/dual-mode/orchestrator.ts#L589-L613)]

### Local persistence proof

With `RUFLO_DAEMON_AUTOSTART=0`, `memory init --backend sqlite --path <temp>/memory.db --verify` passed six of six checks. A first process stored `portable-proof` in namespace `cross-harness` with a 384-dimensional vector and `tool_result` provenance; after it exited, a second process retrieved the exact value `written by harness A; read by harness B`. [measured: local CLI, 2026-08-22]

The resulting SQLite file was 188,416 bytes. This proves disk and cross-process persistence; source establishes that Claude and Codex can share the path, but the run did not exercise either vendor model. [measured] [cited]

Portability has real ceilings. Storage is cwd-specific by default; export's vector flag does not export vectors; import re-stores and re-embeds values; and raw `agent_execute` does not automatically retrieve memory into its prompt. [cited: [`memory-tools.ts#L1313-L1408`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/memory-tools.ts#L1313-L1408), [`agent-execute-core.ts#L555-L615`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L555-L615)]

Invoking `memory --help` without the autostart override started a background daemon and map worker; it was stopped immediately and `daemon status` then reported `STOPPED`. A help path with a process side effect is a measured operational surprise, not evidence of task failure. [measured: local CLI, 2026-08-22]

### Effect on Consilient's portability claim

The live portable-capability specification already concedes that Rulesync and OpenAI cover generic format portability; it narrows the possible delta to per-task provenance, semantic-loss receipts, bounded shared memory, credential/effect controls and measured equivalence. [cited: `docs/superpowers/specs/2026-08-22-portable-capability.md:3-9,53-73`]

Ruflo eliminates a broader novelty claim that no product **provides** persistent vector-backed memory to both Claude Code and Codex. Actual child use, transfer fidelity and outcome gain remain unmeasured here. [cited] [inferred]

It does not eliminate the narrower claim. I found no equivalent task receipt that binds a memory transfer to source bytes, loss accounting, credential isolation, typed effects, acceptance outcome and a cross-harness equivalence measurement. [measured: bounded source search] [asserted]

That surviving claim is still provisional because Consilient has not yet implemented or measured the complete portable capability either. [measured]

## Retrieval, routing state and actual training

Consilient's governing boundary is persistent mutation of learned model state: embedding and retrieving records is retrieval; fitting parameters by optimiser, closed form or direct edit is training. [cited: `docs/decisions/0074-preserve-records-version-capabilities-and-reserve-training-for-parameter-updates.md:62-66`]

Ruflo spans both sides of that boundary, but its ordinary “self-learning” language collapses them. [inferred]

### Retrieval and control-state learning

The default local intelligence loop adjusts stored pattern confidence and use statistics from reward, then persists them. Its “LoRA-style” distillation is explicitly a confidence update, not a parameter fit. [cited: [`intelligence.ts#L239-L410`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/memory/intelligence.ts#L239-L410)]

The MCP tool named `neural_train` embeds inputs and stores searchable patterns; it reports `accuracy: 1.0` when at least one pattern was stored. That is retrieval-state persistence with a misleading metric name, not measured model accuracy. [cited: [`neural-tools.ts#L451-L520`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/neural-tools.ts#L451-L520)]

Model-routing Beta priors also update after `agent_execute`, but “success” means only that a provider returned without an API error; the source identifies accepted output or regression detection as future finer-grained signals. [cited: [`agent-execute-core.ts#L663-L715`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L663-L715), [`#L717-L725`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/agent-execute-core.ts#L717-L725)]

Therefore these routing “Beta” variables are Thompson-sampling parameters, not Consilient's β and not evidence that accepted work is correct. [cited] [inferred]

### Parameter training

The separate `ruflo neural train` command can fit local MicroLoRA/ruvLLM adapter state on embedding-to-embedding pattern batches and save a checkpoint. [cited: [`commands/neural.ts#L11-L47`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/neural.ts#L11-L47), [`native-training.ts#L86-L180`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/native-training.ts#L86-L180)]

The neural library also contains and serialises local LoRA matrices, trajectories, patterns and EWC state. That is genuine learned-state mutation when the training path updates those matrices. [cited: [`sona-manager.ts#L465-L543`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/neural/src/sona-manager.ts#L465-L543), [`#L594-L655`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/neural/src/sona-manager.ts#L594-L655)]

Those adapters transform local representations. No inspected execution path writes Claude, Codex, OpenRouter or Ollama foundation parameters, and persistent retrieval memory must not be described as portable trained weights. [cited] [inferred]

Ruflo's own audit found its persistent pattern-confidence and Q-routing loops genuine, while also finding inflated performance claims and disconnected or inert pieces; its addendum records repairs and says the published WASM MicroLoRA inference path remains inert. [cited: [`intelligence-system-audit-2026-05-29.md#L6-L55`](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/reviews/intelligence-system-audit-2026-05-29.md#L6-L55), [`#L93-L121`](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/reviews/intelligence-system-audit-2026-05-29.md#L93-L121)]

The audit's earlier negative-reward inversion was repaired in `3.10.7`; it is historical evidence of failure and remediation, not a current pinned defect. [cited: [`intelligence-system-audit-2026-05-29.md#L93-L100`](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/reviews/intelligence-system-audit-2026-05-29.md#L93-L100)]

The older local Ruflo assessment's claim that EXP-45 had already refuted ReasoningBank is also too strong: ADR-0074 now records 59.29% mechanical entity loss, not consequential loss, and says dispatch retrieval remains incomplete. [cited: `docs/10-research/ruflo-assessment-2026-08-20.md:67-75`; `docs/decisions/0074-preserve-records-version-capabilities-and-reserve-training-for-parameter-updates.md:17-36`]

## Correctness measurement and β

### What Ruflo genuinely measures

Ruflo ships a GAIA runner with normalisation followed by an LLM judge against ground truth, plus result records with pass rate and cost. [cited: [`gaia-judge.ts#L2-L17`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/benchmarks/gaia-judge.ts#L2-L17), [`gaia-bench.ts#L608-L634`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/gaia-bench.ts#L608-L634)]

The latest committed Level-1 record at this snapshot reports 31/53 passed, 58.49%, estimated provider cost `$3.69483`, mean 4.42 turns and mean 42.18 seconds using `claude-sonnet-4-6`. These are vendor-produced figures present in the pinned artefact, not independently reproduced measurements. [cited: [`gaia-l1-iter63b-convergence-n2.json#L1-L10`](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/benchmarks/runs/gaia-l1-iter63b-convergence-n2.json#L1-L10)]

The artefact is task-outcome evidence in the limited sense that it records per-task ground truth and judgements, not merely latency; it does not prove the run occurred exactly as recorded. It was not rerun here because a real run would make metered model calls, and the shipped catalogue itself says there is no verified GAIA/HAL submission. [cited: [`version.ts#L117-L129`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/version.ts#L117-L129)] [asserted]

The GAIA audit checks answer leakage, no-work results, oracle leakage, grader isolation, normalisation collisions, voting disclosure, split integrity, answer-key reads, dynamic evaluation and judge injection. Its credential-free suite passed 44/44 locally; this validates those audit mechanics, not the provenance of the 31/53 result. [measured: `node plugins/ruflo-workflows/scripts/gaia-audit.test.mjs`, 2026-08-22]

The opt-in flywheel is also substantive. It harvests retrieval patterns, selects on training data, gates on held-out data, checks drift/adversarial cases and replay, runs a canary, records receipts and separates evaluation from explicit locked promotion. [cited: [`harness-flywheel.ts#L1-L21`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/harness-flywheel.ts#L1-L21), [`#L159-L253`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/harness-flywheel.ts#L159-L253), [`flywheel-transaction.ts#L420-L584`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/flywheel-transaction.ts#L420-L584)]

Its human-labelled retrieval anchor is hash-pinned and fails on drift; its own ADR states the honest scope: self-retrieval improves while human-labelled relevance does not regress, not that human relevance itself improves. [cited: [`harness-frozen-eval.ts#L1-L15`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/services/harness-frozen-eval.ts#L1-L15), [`ADR-176#L141-L167`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/docs/adr/ADR-176-proven-self-benchmarking-harness-loop.md#L141-L167)]

These are stronger evaluation mechanics than the old local Ruflo assessment credited. [inferred]

### What it does not measure

GAIA pass rate estimates candidate correctness against a benchmark. It does not estimate how often Ruflo's terminal machine acceptance mechanism confirms independently labelled bad work, because the run does not expose a machine-accept versus independent-truth 2×2 table. [inferred]

The closest in-repo settings-risk benchmark computes TP/FP/TN/FN and recall, so `FN/(TP+FN) = 1 - recall` is algebraically an acceptance-like error if “not flagged” is acceptance. Its scored corpus is byte-identical to fixtures authored from the same hypothesis/session as the scanner; a later independent critic did produce six bypasses, but they were pinned as regression tests rather than added to the scored corpus. [cited: [`settings-risk-benchmark.mjs#L25-L50`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/benchmarks/results/scripts/settings-risk-benchmark.mjs#L25-L50), [`settings-risk-corpus.json#L2-L6`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/benchmarks/settings-risk-corpus.json#L2-L6), [`dream-gist-2026-08-16.md#L35-L45`](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/dream-cycle/dream-gist-2026-08-16.md#L35-L45)] [algebra]

The MetaHarness security wrapper parses TPR/FPR from an external ten-vulnerability/nine-decoy synthetic benchmark, not machine acceptance of independently labelled bad work. [cited: [`security-bench.mjs#L93-L109`](https://github.com/ruvnet/ruflo/blob/5234333c3462/plugins/ruflo-metaharness/scripts/security-bench.mjs#L93-L109)]

Therefore a β-shaped rate exists in Ruflo, but no **valid independently grounded estimate** of Consilient's terminal acceptance error was found. Ruflo does falsify any claim that it has no outcome evaluation at all. [measured] [inferred]

## Swarms, ownership and collision semantics

Main tasks have `assignedTo: string[]`, with no exclusive Owner, lease, claim token or version. [cited: [`task-tools.ts#L17-L35`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/task-tools.ts#L17-L35)]

The task store is an unlocked JSON read/parse/write file. `task_assign` deliberately accepts multiple agents, overwrites the prior assignment, then updates agent state in another write. [cited: [`task-tools.ts#L52-L68`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/task-tools.ts#L52-L68), [`#L352-L429`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/task-tools.ts#L352-L429)]

Two processes can read the same version and lose an assignment or agent-state update. That race is source-inferred; it was not triggered against the shared checkout. [cited] [inferred]

The issue-claim path likewise loads a whole JSON store, checks whether an issue exists, mutates the object and writes the whole file without a lock or compare-and-set. It claims issue identifiers, not owned file paths. [cited: [`claims-tools.ts#L45-L78`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/claims-tools.ts#L45-L78), [`#L96-L163`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/claims-tools.ts#L96-L163)]

The CLI exposes task `--parent` and `--dependencies`, but the MCP schema does not accept those fields, so the CLI-to-tool call silently discards them. [cited: [`commands/task.ts#L68-L121`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/task.ts#L68-L121), [`#L166-L189`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/commands/task.ts#L166-L189), [`task-tools.ts#L70-L108`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/task-tools.ts#L70-L108)]

Dual-mode worktree isolation is the exception: it prevents same-worktree concurrent writers when enabled and caps writers per batch. That is collision avoidance, not a general one-Owner decision protocol. [cited]

### Honest comparison with Consilient

ADR-0067 specifies one accountable Owner, one candidate, no voting, sealed returns and explicit conflict disposition, but it also says enforcement awaits later checks. [cited: `docs/decisions/0067-front-one-chat-with-one-owner-evidence-squads.md:68-72,100-118,130-154,234-250`]

Current Consilient coordination canonicalises paths and rejects equality or ancestor/descendant overlap, but `dispatch.py` performs conflict detection separately from `open_claim()`, and `open_claim()` does not compare-and-set. Two concurrent dispatchers can both observe no conflict and append overlapping claims. [cited: `src/consilient/coordination.py:95-122,213-262`; `scripts/dispatch.py:1374-1445,1555-1601`] [inferred]

Therefore neither pinned Ruflo nor current Consilient is collision-proof, and current Consilient does not yet enforce one Owner. The difference is a specified destination and a narrower path-overlap guard, not a completed superiority result. [measured] [inferred]

## Reproducibility, tests and known failure modes

### Installation is not reproducible at the pinned revision

The documented clean install failed immediately with npm `ETARGET: No matching version found for @claude-flow/mcp@3.0.0-alpha.10`; the registry exposed only `alpha.1`, `.7`, `.8` and `.9`. Separately, the lockfile still declares `alpha.9`, so package metadata and lock state disagree. [measured: `npm ci --dry-run --ignore-scripts --no-audit --no-fund`; `npm view @claude-flow/mcp versions --json`, 2026-08-22] [cited: [`package.json#L67-L73`](https://github.com/ruvnet/ruflo/blob/5234333c3462/package.json#L67-L73), [`package-lock.json#L20-L27`](https://github.com/ruvnet/ruflo/blob/5234333c3462/package-lock.json#L20-L27)]

To obtain a bounded test surface, I installed published `alpha.9` with `--no-save --package-lock=false --ignore-scripts`. This disclosed substitution made `npm ls` report the package invalid against the requested range, and it means the run is not an exact clean-release reproduction. [measured]

The release CI itself carries a baseline of 116 known failing test files and rejects only additions to that set. A passing ratchet means “the known failing-file set did not grow”, not “the suite passed”. [cited: [`ci-test-baseline.txt#L1-L120`](https://github.com/ruvnet/ruflo/blob/5234333c3462/scripts/ci-test-baseline.txt#L1-L120), [`ci-test-ratchet.mjs#L68-L117`](https://github.com/ruvnet/ruflo/blob/5234333c3462/scripts/ci-test-ratchet.mjs#L68-L117), [`.github/workflows/ci.yml#L54-L87`](https://github.com/ruvnet/ruflo/blob/5234333c3462/.github/workflows/ci.yml#L54-L87)]

Root `npm test -- --run --reporter=dot` did not reach a denominator; the Rust runtime aborted while allocating 2,218,070,976 bytes and Vitest lost its IPC channel. [measured: local Windows run, 2026-08-22]

The focused CLI suite completed with 182 test files passed, 46 failed and one skipped; 3,396 tests passed, 164 failed and 80 skipped out of 3,640. Native-module bindings were unavailable because install scripts were deliberately disabled, several workspace builds were absent, and Node 24 is newer than upstream's main CI, so the count is an environment-qualified result rather than 164 independently confirmed product defects. [measured: `npm test -- --reporter=dot --maxWorkers=1 --minWorkers=1`, `v3/@claude-flow/cli`, 2026-08-22]

The dual-mode/worktree slice completed 34 tests with 30 passed and four failed on Windows. Failures included Unix-path expectations, two worktree root-prefix checks rejecting Windows paths, and the stdin-EOF regression fixture; the last fixture failure does not by itself show that a real Codex child still hangs. [measured: `npx vitest run tests/dual-mode.test.ts tests/dual-mode-stdin-2947.test.ts tests/worktrees.test.ts`, 2026-08-22]

The federation workspace passed 25 files and 640/640 tests. [measured: `npm test -- --reporter=dot`, `v3/@claude-flow/plugin-agent-federation`, 2026-08-22]

Credential-free repository smokes also passed hook CJS 12/12, cross-platform hook audit eight commands with zero violations, WASM RVF composition 7/7, gallery CRUD six groups and plugin bridge 7/7. The WASM provider bridge reported 5/6 because an LF-only source regex missed a CRLF file; the underlying function was present. [measured: local scripts, 2026-08-22] [cited: [`smoke-wasm-provider-bridge.mjs#L66-L74`](https://github.com/ruvnet/ruflo/blob/5234333c3462/scripts/smoke-wasm-provider-bridge.mjs#L66-L74), [`agent-wasm.ts#L109-L144`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/ruvector/agent-wasm.ts#L109-L144)]

These mixed results show substantial tested code and a real release/reproducibility problem at the same time. Neither “all theatre” nor “production-green” fits the evidence. [inferred]

### Benchmark claim

Issue [#2125](https://github.com/ruvnet/ruflo/issues/2125) describes the advertised SOTA comparison as Mode A with a stub LLM; real-model Mode B was blocked by a stale credential, CrewAI numbers were proxies, and one Linux Ruflo result was proxied. [cited]

The associated [PR #2124](https://github.com/ruvnet/ruflo/pull/2124) closed unmerged after conflicts, and the pinned main tree contains no `benchmarks/` directory even though the README still advertises the external branch/gist. [cited: [`README.md#L384-L388`](https://github.com/ruvnet/ruflo/blob/5234333c3462/README.md#L384-L388)] [measured: `git ls-tree`]

The [published benchmark gist](https://gist.github.com/ruvnet/298f8c668c8859b369f91734a0e9cbbe) explicitly limits itself to orchestration overhead, not model quality, tool accuracy or capability, and inconsistently describes five-trial medians and seven trials with three warm-ups. Unlike the GAIA JSON, this comparator artefact is absent from pinned `main`, its PR closed unmerged and several values are disclosed proxies; that provenance difference—not independent reproduction—is why it receives less weight here. [cited] [inferred]

The published comparison recipe also imports Unix-only Python `resource` in all three comparator runners; it failed natively on Windows with `ModuleNotFoundError`, while this host's WSL lacked Node. [measured: Python 3.13.11 and WSL inspection, 2026-08-22] [cited: [`LangGraph runner#L14-L20`](https://github.com/ruvnet/ruflo/blob/1803909ae1ff/benchmarks/comparators/langgraph/run.py#L14-L20), [`AutoGen runner#L10-L16`](https://github.com/ruvnet/ruflo/blob/1803909ae1ff/benchmarks/comparators/autogen/run.py#L10-L16), [`CrewAI runner#L13-L19`](https://github.com/ruvnet/ruflo/blob/1803909ae1ff/benchmarks/comparators/crewai/run.py#L13-L19)]

The SOTA table is therefore control-plane performance evidence from another branch, not proof that Ruflo produces better work or that the pinned source reproduces the numbers. [cited] [inferred]

### Open limitations and repaired reports

Open issue [#2640](https://github.com/ruvnet/ruflo/issues/2640) reports complete agent/command overlap, 97% skill overlap and double-firing hooks when the init bundle and marketplace plugins coexist. That is consistent with the measured duplicate catalogue names and is a context/state duplication risk. [cited] [inferred]

Open issue [#2948](https://github.com/ruvnet/ruflo/issues/2948) reports Windows memory commands aborting in SimSIMD with a roughly 4.158 GB allocation; [#2413](https://github.com/ruvnet/ruflo/issues/2413) reports Windows ADR import/path and headed-browser failures despite 15/15 structural smokes; and [#1446](https://github.com/ruvnet/ruflo/issues/1446) reports empty Windows headless-worker output. [cited]

Those issues target older releases and were not re-executed against `3.38.16`; they remain unresolved reports, not confirmed pinned regressions. [asserted]

Open issue [#3052](https://github.com/ruvnet/ruflo/issues/3052) narrows a Node 24/Windows Transformers ESM failure to direct imports while saying the real CLI memory path works; that distinction matches this run's successful CLI memory proof and failing direct/native test surfaces. [cited] [measured]

Issue [#2970](https://github.com/ruvnet/ruflo/issues/2970) reported that the witness verifier exited zero when every built artefact was missing. The pinned source now exits 2 for that source-only condition, so the issue is evidence of a repaired failure mode, not a current source finding. [cited: [`witness/verify.mjs#L85-L113`](https://github.com/ruvnet/ruflo/blob/5234333c3462/plugins/ruflo-core/scripts/witness/verify.mjs#L85-L113)]

Issue [#1916](https://github.com/ruvnet/ruflo/issues/1916) documented task assignment that looked active while no hive worker executed. The pinned source has repaired agent visibility and added `agent_execute`, but `hive-mind_spawn` still creates idle records and task assignment still does not itself run them. [cited]

The failure pattern is not that nothing works. It is that registry success, process success, provider response and artefact correctness are distinct states that the product language sometimes merges. [inferred]

## Licence and adoption boundary

The repository root is MIT, permitting use, copying, modification, distribution and sublicensing subject to preserving the copyright and permission notice. [cited: [`LICENSE#L1-L20`](https://github.com/ruvnet/ruflo/blob/5234333c3462/LICENSE#L1-L20)]

That does not settle the whole distribution. A root lock parse counted 26 direct dependencies, 10 optional dependencies and 994 lock entries; licence metadata included 37 `LGPL-3.0-or-later`, 12 `MPL-2.0`, 10 `Apache-2.0 AND LGPL-3.0-or-later` expressions and nine missing fields. These counts are a review trigger, not a legal incompatibility finding. [measured: PowerShell package-lock parse, 2026-08-22] [cited: [`package-lock.json#L2038-L2052`](https://github.com/ruvnet/ruflo/blob/5234333c3462/package-lock.json#L2038-L2052), [`#L10086-L10098`](https://github.com/ruvnet/ruflo/blob/5234333c3462/package-lock.json#L10086-L10098)]

The nested RuVocal fork also identifies itself inconsistently as Apache-2.0 in its manifest/licence and MIT in its README. Per-component and distribution-mode review is required before copying or shipping those parts. [cited: [`RuVocal manifest#L4-L11`](https://github.com/ruvnet/ruflo/blob/5234333c3462/ruflo/src/ruvocal/rvf.manifest.json#L4-L11), [`RuVocal README#L156-L164`](https://github.com/ruvnet/ruflo/blob/5234333c3462/ruflo/src/ruvocal/README.md#L156-L164)]

Licence CI is advisory: the audit command ends with `|| true` and its step is `continue-on-error`. [cited: [`.github/workflows/ci.yml#L46-L52`](https://github.com/ruvnet/ruflo/blob/5234333c3462/.github/workflows/ci.yml#L46-L52)]

ADR-0065 keeps β, routing, acceptance, trajectory authority, budgets and collision coordination native; it permits adopting work-performing adapters/tools and optional marketplace capabilities when licensing is compatible. [cited: `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md:36-71`]

### Worth adopting or contributing upstream

| Mechanism | Decision under ADR-0065 |
|---|---|
| Claude/Codex command construction, Codex stdin-EOF repair and provider adapter tests | **Tier 2 candidate only after target-platform proof.** These perform work at the harness boundary, but the local stdin regression fixture failed; require that fixture plus one bounded real child smoke to pass on the target Windows runtime before adoption or upstream contribution. [cited] [measured] |
| Distinct worktrees, dependency-cycle validation and writer caps | **Reuse the invariants, not Ruflo as the authority.** They strengthen native coordination, but Consilient must retain and independently test the core decision/collision path. [cited] [inferred] |
| SQLite/HNSW path contract and typed memory provenance | **Tier 2 candidate for a storage adapter.** Do not let it become the sole trajectory/evidence authority; preserve source records and receipts independently. [inferred] |
| Frozen hash-pinned eval, held-out split, canary, replay, immutable receipts, explicit promotion and locked transaction | **Copy the measured discipline into native Tier 1 controls.** These are the strongest upstream mechanisms found, but promotion/acceptance must remain Consilient-owned. [cited] [inferred] |
| Test-driven repair using executable test exit status as fitness | **Tier 2 work capability.** It uses a deterministic oracle and bounded attempts/cost rather than an LLM judge. [cited: [`testgen-tools.ts#L118-L144`](https://github.com/ruvnet/ruflo/blob/5234333c3462/v3/%40claude-flow/cli/src/mcp-tools/testgen-tools.ts#L118-L144)] |
| Prompt/skill catalogue | **Tier 3 optional marketplace material.** Count and evaluate entries individually; never equate file count with independent capacity. [inferred] |

Do **not** adopt the unlocked JSON task/agent registries, topology-as-label semantics, non-atomic claims, API-return-as-quality feedback, `neural_train` naming or mutable `npx ...@latest` child calls. [cited] [inferred]

No dependency should be added merely to obtain these ideas. The smallest safe next move is a component-level experiment or upstream patch against one mechanism, with Consilient retaining the acceptance record. [asserted]

## Claim stress test

| Ruflo or Consilient claim | Stress result |
|---|---|
| “Ruflo is the meta-harness.” | **Narrowly holds.** Dual/hive/headless invoke real harnesses; raw HTTP and registry-only surfaces do not. [cited] |
| “100+ specialised agents.” | **Marketing count, not capability count.** Markdown roles can be useful, but distinct evidence/model/tool bindings must be measured per run. [cited] [measured] |
| “Persistent memory across models.” | **The facility exists.** Storage survives processes and dual mode gives Claude/Codex the same path and usage prompt; actual child use and outcome gain were not run. It is not vendor-weight transfer or receipt-preserving capability equivalence. [cited] [measured] [inferred] |
| “Self-learning.” | **Mixed.** Persistent retrieval/routing state is real; explicit local adapter training is real; provider-return feedback is not task quality; some advertised neural paths remain inert or disconnected. [cited] |
| “Swarms prevent coordination failure.” | **Does not hold generally.** Main stores are non-atomic and multi-assignee; dual-mode worktree isolation is a bounded exception. [cited] [inferred] |
| “SOTA.” | **Not established for task outcomes.** The cited matrix is stub-model orchestration overhead on an unmerged branch with proxies. [cited] |
| “Ruflo has no correctness evidence.” | **False.** GAIA, retrieval labels, security matrices and a flywheel exist. [cited] |
| “Ruflo measures Consilient β.” | **Same-shaped counts exist; a valid estimate was not found.** The scanner has FN/recall, but its scored corpus is fixture-coupled and excludes the held-out bypasses. No terminal acceptance versus independently labelled bad artefact table was located. [cited] [measured] [inferred] |
| “Consilient uniquely provides a cross-harness persistent-memory facility.” | **False if stated broadly.** Ruflo gives Claude and Codex a common persistent vector store and usage instructions; effective use remains unmeasured. [cited] [inferred] |
| “Consilient is already safer at collisions/ownership.” | **Not established.** Its intended contract is stronger, but enforcement and atomic claims are incomplete. [cited] |
| “Ruflo is production-green.” | **Does not hold at this snapshot.** Clean install is impossible unchanged, CI ratchets 116 failing files, and Windows test surfaces are red. [measured] [cited] |

### Threats to validity

This is a Consilient-authored assessment of a competitor, and its residual “advantage” is framed in Consilient's own vocabulary—β, evidence classes, one Owner and receipts. That makes the residual partly definition-shaped: it is a candidate comparison criterion, not independent proof that users value the bundle or that it is novel in the adjacent reliability literature. [asserted]

The final decision must therefore turn on externally valued outcomes and independently held labels in the experiment below, not on whether Ruflo uses Consilient's names. [asserted]

A different model family audited the draft without tools or drafting history and caused material corrections to the omission search, meta-harness/memory strength, β wording, install diagnosis and experiment design. The requested third-family refutation produced no result within its bound, so those corrections have one independent reading plus direct source observations, not cross-family consensus. [measured]

## Exact experiment that would decide the bar

This protocol is proposed, not registered. If authorised, assign the next free experiment ID and preregister it before any outcome is seen. [asserted]

### Arms

1. **Direct single-harness baseline:** choose one harness globally before the main bank using a separate 20-task calibration set: higher joint verifier-plus-human success wins, with lower provider GBP as the tie-breaker. Use that one pinned harness for every main task with the same model/provider, permissions, prompt bytes, cwd and budget used by both products; never select the stronger harness task by task. [asserted]
2. **Ruflo:** pinned `@claude-flow/codex` dual mode, native dependency DAG, shared database and worktree isolation; one predeclared writer worktree is the only terminal candidate, and missing/ambiguous collection is a refusal rather than an operator repair. [asserted]
3. **Consilient single Owner:** one accountable Owner may dispatch the same Claude/Codex workers under the same permissions and budget; only the Owner writes the terminal candidate and every sealed conflict/dissent item must receive a disposition. [asserted]

A fourth Consilient arm may add specialist squads only if the preregistration names the exogenous fact each specialist introduces. Without this arm, a win cannot be attributed to multi-agent organisation. [asserted]

### Frozen task bank and exposure

Start with 80 paired coding tasks in four predeclared strata: localised repair, cross-file feature, adversarial/security fix and ambiguous-requirement change. Draw tasks from permissively licensed public repositories not used to build either system's prompts or fixtures. [asserted]

Before any main outcome is exposed, use exact paired-binomial simulation with the separate calibration set's discordance rate to test whether 80 tasks give at least 80% power for a true `+0.15` success difference to clear the `+0.05` lower-bound bar. If not, increase all arms equally in blocks of 40 to the smallest qualifying size, capped at 400; reaching the cap without the information target is reported as underpowered, not equivalent. [asserted]

Freeze repository commit, task text, model revision, temperature/determinism settings, tools, network policy, credential availability, candidate exposure, verifier exposure, wall-clock limit, token limit, provider-equivalent GBP limit and worker-minute limit before launch. [asserted]

Each arm receives one candidate exposure and one terminal verifier exposure. Timeouts, refusals, missing usage, absent candidates, quarantine and crashes remain in the denominator and receive adverse outcomes; there is no post-hoc retry, merge or operator repair. [asserted]

### Primary outcome

A task succeeds only when an external deterministic verifier passes **and** at least two of three independent blinded reviewers accept the patch without edits. Two reviewers score every patch; a third scores disagreements. Reviewers must not build either system, label the acceptance bank or see the hypotheses. [asserted]

An independent custodian holds the arm mapping and labels until analysis is sealed. Present canonical diffs without product, model, worker-count, commit or transcript identifiers, randomise order, and ask every reviewer to guess the arm; report guess accuracy and treat statistically detectable arm recognition as failed blinding for the human comparison. [asserted]

Compare paired success differences with a two-sided 95% interval and exact paired-binomial/McNemar evidence. Call Consilient better only if the 95% lower bound for `Consilient - Ruflo` exceeds `+0.05`; otherwise report superiority unproven. This protocol makes no equivalence claim. [asserted]

### Acceptance error

Use a separate frozen bank of 160 terminal candidate artefacts, independently labelled before product exposure: 80 bad and 80 good, balanced across the four strata and including plausible near-misses. Submit each through the documented terminal acceptance surface with generation disabled, freeze the machine decision, and publish the full `machine accept/reject/abstain × human good/bad` table. A product with no reachable terminal acceptance decision records `no decision`; it does not silently inherit its task/result status as acceptance. [asserted]

Estimate `P(machine accepts | human bad)` over the 80 independently bad artefacts and false rejection over the 80 independently good artefacts with exact intervals. Abstention, missing decision and withheld confirmation are not dropped; report them, refusals and quarantine beside every rate. There is no machine-decision cell quota, so an always-accept or always-reject system remains measurable rather than making the design unattainable. [asserted]

### Authority and coordination

Inject protected operations requiring explicit human authority and harmless near-misses. One false protected authorisation loses the authority criterion; false refusals are counted separately. [asserted]

At frozen boundaries, kill the parent, one worker and the storage process; restart once. Count recovered accepted completions, duplicate work, duplicate provider effects, lost handoffs, conflicting writers, unresolved dissent and dirty retained worktrees. [asserted]

Launch synchronised overlapping claims from two processes. Pass requires exactly one winner and one explicit refusal with a durable record after restart; a last-writer-wins store fails. [asserted]

### Learning without regression

Give both products the same training set containing one useful procedure, then evaluate unseen matched tasks plus poisoned near-misses. Separate retrieval-state changes from fitted parameter changes and record the exact persisted bytes/checkpoint. [asserted]

Pass requires held-out joint-success lift without an authority breach, poison uptake or regression on the frozen human-labelled anchor. Report all proposed and rejected promotions, not only champions. [asserted]

### Cost and stopping

Record input/output/cache tokens, provider-equivalent GBP, tool calls, wall time, worker-minutes, storage writes, blinded operator minutes and review minutes per joint success. Missing usage is adverse. [asserted]

Consilient clears the full bar only if it wins the primary outcome and acceptance-error criteria, has zero protected breaches, survives the durability probes, shows held-out learning without regression, and keeps both provider GBP and human time within `1.25×` Ruflo. Ruflo clears it symmetrically. The `1.25×` ceiling is an inherited policy tolerance from the Hermes comparison, not an empirical constant; publish sensitivity at `1.0×`, `1.25×` and `1.5×`. [asserted]

Stop when every arm reaches the preregistered power-selected task count and all 160 acceptance artefacts have terminal observations, or when a preregistered safety/budget boundary fires. Do not stop early for a favourable point estimate. [asserted]

### What would falsify this report

- A pinned Ruflo run exposing terminal machine acceptance and independent human truth could overturn the no-β finding. [asserted]
- An atomic cross-process task/claim implementation on the operator path could overturn the collision finding. [asserted]
- Evidence that catalogue entries bind genuinely distinct models, tools or corpora by default could overturn the prompt-role classification. [asserted]
- A clean install and full green suite from the pinned public source could overturn the release finding. [asserted]
- A complete Consilient implementation and matched win are required before turning its narrower evidence-control design into a superiority claim. [asserted]
- A pinned trace in which the documented dual path fails to launch either vendor child would overturn the implementation-level meta-harness verdict; repeated child completion is the positive test. [asserted]
- A live dual run in which Claude/Codex cannot or do not read/write the common store would overturn any functional cross-harness-memory reading while leaving the narrower “facility exists” claim intact. [asserted]
- Independent provenance review showing that the committed GAIA rows were fabricated or invalidly judged would overturn their limited outcome-evidence status. [asserted]

## Repository and citation hygiene checks

`python -m pytest -q tests/test_v0_invariants.py` passed 258/258 tests after the report was added. This checks repository documentation invariants; it does not validate the Ruflo claims. [measured: local working tree, 2026-08-22]

`python -m pytest -q` passed 897 tests with one skip in 32.90 seconds. This is a regression/compatibility check only; the live worktree already contained unrelated concurrent changes and additional tests, so the denominator is not directly comparable to the dispatch brief's 891-test starting baseline. [measured: local working tree, 2026-08-22]

A local permalink audit decoded every commit-pinned Ruflo `blob/5234333...#Lx-Ly` path and verified file/range existence. This catches broken pins only; it does not prove claim-to-source correspondence. [measured: PowerShell link/path audit, 2026-08-22]

A separate manual content trace re-read the load-bearing ranges for child process invocation, worker memory instructions/environment, agent registration, neural training, provider-return routing feedback, task assignment, issue claims, the settings-risk corpus and GAIA result scope. The report now states the narrower property each range supports. [measured: pinned clone source trace, 2026-08-22]

UTF-8 round-trip validation found five `β` symbols, four multiplication signs, 58 smart quotes and zero replacement characters; the independent auditor's reported encoding corruption was a transport/rendering artefact and is refuted for the file on disk. [measured: .NET UTF-8 byte/string check, 2026-08-22]

The report remains the only file created for this dispatch, and the intended commit contains no research-register, ADR-index, source, test or gate change. [measured]

## Plain answer

Ruflo is the closest inspected competitor on Consilient's cross-harness command-post axis, and the existing product bar was wrong to omit it under either current or legacy names. Its source-implemented dual Claude/Codex executor, common persistent vector-memory facility and guarded retrieval flywheel are sufficient prior art to withdraw broad claims of unique meta-harnessing, provisioned cross-harness memory or self-improving evaluation; live child use and outcome gain remain unproven here. [cited] [measured] [inferred]

The teardown does not support the opposite overcorrection. Most of the “100+ agents” are role files; default swarms are often state registries; ordinary feedback rewards provider availability rather than correctness; task/claim stores are non-atomic; the advertised SOTA matrix is stub-model overhead from an unmerged branch; and the pinned release neither installs unchanged nor has a green suite. [cited] [measured]

Consilient's surviving possible advantage is narrower: externally calibrated acceptance error joined to evidence-class admission, one-candidate authority, adverse-outcome accounting, bounded receipts and measured equivalence. Because that bundle is defined in Consilient's own terms, it is an experiment hypothesis—not an independent novelty result—and it is not a product win: the gates remain shut, one Owner is unenforced and path claims are not atomic. [cited] [measured] [asserted]

The decision is therefore: treat Ruflo as the structural bar; reuse or contribute its strongest bounded mechanisms under ADR-0065; do not adopt its core coordinator/verifier as an authority; and run the frozen matched experiment before claiming Consilient is better. [inferred]
