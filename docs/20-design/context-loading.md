# Dynamic context loading

Status: **v1+ design documentation. Not v0** (ADR-0015 Stage 2). One loader, task-scoped,
domain-blind: tools, skills, MCPs and connections are chosen per task, never per domain.
There is no "code mode" and no "document mode" (see `architecture-sketch.md`).

All four primary sources below were read at origin on 19 Aug 2026 and are [FULL] in the
bibliography, with the caveats found on reading — three of the four headline numbers are
**illustrative examples, not benchmarks**, and the fourth's metric is undefined.

## The three patterns

| Pattern | Mechanism | Reported effect (as verified) | Trade-off |
|---|---|---|---|
| **Tool search / deferred loading** (Anthropic, 24 Nov 2025) | All definitions sent, `defer_loading: true` keeps them out of context until a search tool pulls them | "Typically over 85%" definition-token reduction (worked example: ~77K → ~8.7K). Accuracy on internal MCP evals: Opus 4 49% → 74%, Opus 4.5 79.5% → 88.1% — **the metric is never defined** (selection? task success?); treat as directionally strong, numerically unusable | Cheapest to adopt; adds a search round-trip; quality of tool descriptions becomes load-bearing |
| **Code execution with MCP** (Anthropic, 4 Nov 2025) | Tools presented as a code API on a filesystem; agent reads definitions on demand, intermediate results stay in the sandbox | 150,000 → 2,000 tokens, "a time and cost saving of 98.7%" — **one worked Google-Drive→Salesforce example**, definitions and intermediate results conflated, **zero accuracy claims in the post** | Needs a sandboxed execution environment (the post itself flags the security cost); strongest when intermediate data is large |
| **Code Mode** (Cloudflare — mechanism: Varda & Pai, **26 Sep 2025**; the 99.9% figure: Carey, **20 Feb 2026** — the repo previously carried the wrong date) | MCP tools compiled to a TypeScript API; model writes code against it in a sandboxed Worker | 1,000 vs 1.17M input tokens (tiktoken, Cloudflare's own API) = 99.9% — **against a hypothetical baseline no model could load**; accuracy claims are qualitative only ("agents handle many more tools… when presented as a TypeScript API") | Vendor-shaped runtime; same sandbox cost as code execution |

The three are one idea at three depths: don't put tool schemas in the context window;
let the model pull what it needs, or write code so it never needs the schemas at all.

## Which path each applies to

- **Delegated execution** (Claude Code and peers): **inherited.** Claude Code ships MCP
  tool search natively, auto mode default, since v2.1.7 (13 Jan 2026 — verified from the
  changelog). Orchestrating Claude Code buys progressive disclosure for free; the harness
  must not rebuild it. `[measured]`
- **Native execution** (OpenRouter / local): a bare completions API — the harness supplies
  the layer, from the commoditised options in `capability-layer.md` (MCP gateways,
  framework tool-retrieval, or code-execution agents). **Adopt one; build none.**

## The tool-count evidence — corrected before anything is built on it

The claim as received was "accuracy degrades measurably past ~20–25 available tools
(Less is More)". Checked against the paper (arXiv:2411.15399, read in full):

- **The ~20–25 threshold does not appear in the paper.** Its sole direct comparison is
  one motivating example: Llama3.1-8b-q4 fails at 46 tools and succeeds at 19. No
  tool-count sweep exists, and half the reported degradation is quantisation (63.0% →
  20.4% at q4_0 on BFCL), on 2023–24 sub-10B edge models. The number was folklore.
- **The effect, however, replicates on current models**: Anthropic's own eval (above) is
  a 25-point swing on Opus 4 and still 8.6 points on Opus 4.5 from removing loaded
  definitions; RAG-MCP (arXiv:2505.03275) swept 1 → 11,100 schemas on Qwen-max and found
  >90% selection below ~30 candidates, collapse past ~100, and 13.6% vs 43.1% task
  accuracy for all-tools vs retrieval. `[cited]`
- So: **degradation with irrelevant tools is real and current; the threshold is
  model-dependent, shrinks with model quality, and has never been measured for the
  4B–14B local tier.** That gap is EXP-18.

## The Δ connection — what survived

Of the two mechanisms bundled into "an optimum number of tools" (ADR-0002 § Δ discipline,
`experiments/capability_context_beta_star.py`):

- **Too few tools** is a feasibility cliff (structural zeros — the *capability-layer*
  mechanism). Not a Δ change.
- **Too many tools** is the one claimed Δ mechanism that survived scrutiny: irrelevant
  definitions degrade success **on the same task**, which is a genuine competence term,
  so context discipline narrows Δ and loosens β* — *directionally*. `[algebra]` given the
  mapping. Illustrative magnitude: if the 49→74 figure were task success, it implies a
  competence shift of ~0.14 (half the reference 0.27 gap) and a ~3× β* loosening — but
  the metric is undefined, so the magnitude is `[asserted]` until EXP-18.
- The asymmetry assumption is load-bearing and `[asserted]`: the delegated path is
  already context-disciplined (inherited tool search), so clutter taxes the native/cheap
  path more — that is what makes discipline a *gap-narrowing* rather than
  gap-preserving intervention.

The "optimum" is therefore not a curve with an interesting peak: it is **exactly the
required tool set** — the cliff on one side, the slope on the other. What is unmeasured
is the slope's steepness for local models, and that is the whole of EXP-18
(`../10-research/experiment-register.md`).
