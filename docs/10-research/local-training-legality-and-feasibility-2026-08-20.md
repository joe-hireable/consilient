# Local model training: legal boundary and RTX 5090 feasibility

**Date checked:** 20 August 2026. **Jurisdictional posture:** this note applies a UK copyright
and data-protection screen; provider contracts also select their own governing law. This is a
technical reading of published terms, not legal advice. Ambiguous uses remain blocked pending
written provider permission or advice from a solicitor who has read the account-specific
contract. [asserted]

## Decision

**Do not train or distil a local model on outputs from the Anthropic, OpenAI, SpaceXAI or
Cursor subscriptions.** Anthropic's policy requires prior authorisation for *any* use of
inputs or outputs to train an AI model; SpaceXAI separately forbids distilling outputs; OpenAI
and Cursor prohibit output-assisted development of competing models and do not define
“compete”. Cursor also passes through the applicable upstream model-provider policy. An
autonomous coding-model trainer cannot make those ambiguities safe. [cited]

**Do permit research on local adapter training when both the exact model revision and every
training example are licence-cleared, provider-output-free and provenance-recorded.** A user
may train on material for which they hold the necessary rights, but “my data” is not itself a
rights category: employment, commissioning, joint authorship, third-party licences,
confidentiality and personal data can all change the answer. [cited]

On this RTX 5090, the realistic default is QLoRA on a 7–14B model. A 30–32B QLoRA run is a
tightly engineered experiment, not a reliable unattended default; a conventional full
fine-tune is realistically about 1B parameters; and a 70B QLoRA base does not fit wholly in
VRAM. [algebra]

This does **not** authorise a learned router in v0. ADR-0003 still excludes one, and EXP-58
below is a blocked experiment rather than a product decision. [measured]

## 1. “Own data” is conditional, not automatic

The UK Intellectual Property Office says the creator is usually first copyright owner, but
work made by an employee in the course of employment belongs first to the employer; a
commissioner does not automatically own commissioned work; and joint work can require every
owner's agreement. [cited] The source is the IPO's
[Ownership of copyright works](https://www.gov.uk/guidance/ownership-of-copyright-works),
read in full 20 August 2026.

| Material proposed for training | Position |
|---|---|
| Code and prose solely authored by the principal, outside employment/client obligations, with no incorporated third-party material | The principal normally controls the relevant copyright and may copy it for local training. [cited] |
| Employee, client, commissioned or jointly authored work | Do not treat it as “own” until the governing contract and ownership chain are checked. [cited] |
| Repository dependencies, copied snippets, documentation and datasets | The licence of each incorporated work still applies; possession of the repository is not permission to repurpose every file. [cited] |
| Prompts or trajectories containing another person's personal data | Locality does not remove UK GDPR processing. The ICO requires a purpose and lawful basis for each distinct training operation. [cited] |
| Frontier-model responses assigned to the subscriber under provider terms | Assignment of output rights does not cancel the same contract's training, competition, extraction or distillation restrictions. [cited] |

The ICO states: “Whenever you are processing personal data – whether to train a new AI system,
or make predictions using an existing one – you must have an appropriate lawful basis to do
so.” [cited] Its
[AI lawfulness guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-lawfulness-in-ai/)
was read in full 20 August 2026. A shipped trainer therefore needs a dataset inventory,
purpose, lawful-basis record, minimisation step and deletion/objection handling wherever user
data contains personal data. [cited]

## 2. Frontier outputs: the current terms

These are the terms applicable to the named paid subscriptions, plus the corresponding
business/API terms where they materially differ. Quotes are verbatim and were read from the
linked first-party pages on 20 August 2026. [measured]

### Anthropic — Claude Pro/Max and Claude Code on an individual plan

Anthropic's Consumer Terms govern Claude.ai, Claude Pro and other individual products; its
Commercial Terms expressly say consumer offerings are governed separately. [cited]

The incorporated [Usage Policy](https://www.anthropic.com/legal/aup) says users must not
engage in:

> “Utilization of inputs and outputs to train an AI model (e.g., ‘model scraping’ or
> ‘model distillation’) without prior authorization from Anthropic”

That is not limited to competing models. The
[Consumer Terms](https://www.anthropic.com/legal/consumer-terms) also prohibit using the
services “[t]o develop any products or services that compete with our Services, including to
develop or train any artificial intelligence or machine learning algorithms or models”.
Neither page defines “compete”. [cited]

The [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) govern the API/business
case and prohibit access “to build a competing product or service, including to train
competing AI models”. The Usage Policy still applies to all users. [cited]

**Verdict:** no Claude input or output enters training, teacher logits, synthetic examples,
rewards, preference pairs or evaluation data without Anthropic's prior written authorisation.
[cited]

### OpenAI — ChatGPT/Codex subscription

The consumer [Terms of Use](https://openai.com/policies/row-terms-of-use/), effective
1 January 2026, say:

> “Use Output to develop models that compete with OpenAI.”

They also prohibit automatically or programmatically extracting data or Output. The terms
assign OpenAI's interest in Output to the user, but “compete” is not defined. [cited]

The [Services Agreement](https://openai.com/policies/services-agreement/), also effective
1 January 2026, applies to APIs and named business products, not ordinary consumer use. It
adds a “Permitted Exception” for models primarily intended to categorise, classify or
organise data **only if they are not distributed or made commercially available**, plus
fine-tuning supplied as an OpenAI service. That exception is absent from the consumer terms
governing the subscription named in this brief. [cited]

**Verdict:** a general local coding model is too close to OpenAI's products to treat as
non-competing. A private verifier classifier may be distinguishable, but the consumer terms
provide neither the business agreement's classifier exception nor a definition of
competition; do not automate output ingestion without written clearance. [asserted]

### SpaceXAI — SuperGrok Heavy

The [Consumer Terms](https://x.ai/legal/terms-of-service), effective 26 June 2026, say the
user retains ownership rights in User Content. The incorporated
[Acceptable Use Policy](https://x.ai/legal/acceptable-use-policy), effective 14 August 2026,
prohibits:

> “Using the Service or any Output to develop (or assist anyone in developing) machine
> learning models or any products or services that compete with SpaceXAI, whether directly
> or indirectly”

and separately prohibits:

> “Scraping, harvesting or reselling any Input or Output, or distilling model data or
> Outputs”

“Compete” and “distilling” are not defined there. [cited]

The enterprise/API
[Terms](https://x.ai/legal/terms-of-service-enterprise), last updated 14 August 2026, are
stricter: the customer must not “use any Output to train any foundation models, large
language models, or other artificial intelligence systems except as may be expressly
permitted in an Order Form”. [cited]

**Verdict:** SuperGrok output distillation is prohibited on the text read. A non-distillation,
non-competing classifier remains ambiguous, not cleared. [cited]

### Cursor Ultra

The individual [Terms of Service](https://cursor.com/terms-of-service) prohibit using “the
Service or any Suggestions to develop or train a model that is competitive with the
Service”. Anysphere assigns its interest in Suggestions to the user, but does not define
“competitive”. [cited]

The [Acceptable Use Policy](https://cursor.com/acceptable-use-policy) applies regardless of
subscription tier. It prohibits using the Service or Suggestions to develop ML models or AI
services that compete with Anysphere **or the Model Providers**, prohibits scraping,
harvesting or distilling Suggestions, and says an upstream provider's acceptable-use policy
also applies when Cursor routes to that provider. [cited]

The business MSA carries the same competitive-model restriction; a business tier therefore
does not remove it. [cited]

**Verdict:** Cursor output is not a clean circumvention route to Claude, OpenAI, Gemini or
Grok training data. The upstream policy remains applicable, and a local coding model is
facially competitive with Cursor's coding service. [cited]

### Combined answer

| Question | Answer |
|---|---|
| Does every provider forbid all training? | No. Anthropic's current Usage Policy is categorical absent prior authorisation. OpenAI and Cursor frame the core restriction around competing models. SpaceXAI combines a competition restriction with a separate ban on distilling outputs. [cited] |
| Is “competing” defined? | Not in the Anthropic Consumer/Commercial Terms, OpenAI consumer Terms, SpaceXAI AUP or Cursor Terms/AUP read for this note. [cited] |
| Do subscription and API/business terms differ? | Yes. OpenAI's business agreement has a narrow private-classifier exception absent from consumer terms; SpaceXAI's enterprise terms prohibit any output training absent an Order Form; Anthropic separates consumer and commercial contracts but its Usage Policy applies to all users; Cursor's individual and MSA restrictions are materially aligned. [cited] |
| May Consilient distil the four subscriptions into a local coding model? | No under the conservative, automatable boundary. At least Anthropic and SpaceXAI prohibit the proposed mechanism directly, while OpenAI and Cursor leave an undefined competition test that a coding-model trainer cannot safely self-adjudicate. [cited] |

## 3. Does logging an output cross the line?

Storage is not itself model training, and the terms read do not define an ordinary
single-session operational record as training. They do contain separate extraction rules:
Anthropic restricts crawling, scraping or harvesting; OpenAI consumer terms prohibit
automatic or programmatic extraction of Output; SpaceXAI prohibits scraping or harvesting
Input or Output; and Cursor prohibits scraping, harvesting or distilling Suggestions.
[cited]

The safe trajectory boundary is therefore:

1. Record provider, harness, requested and served model, timestamps, usage, artefact
   references, verifier results and a content digest; do not put raw frontier responses in
   the durable training corpus. [asserted]
2. Where a raw response is operationally necessary for debugging, keep it local,
   access-controlled, retention-limited and explicitly excluded from every training-data
   selector. [asserted]
3. Do not bulk-export subscription outputs or convert operational logs into examples,
   preference pairs, rewards or teacher targets without written provider permission.
   [cited]

This preserves provenance without pretending that ownership of an Output grants every use
of it. [asserted]

## 4. Open-weight models: rights attach to exact revisions

“Llama”, “Qwen”, “Mistral”, “DeepSeek”, “Gemma” and “Phi” are families, not licences. The
exact repository and revision must be resolved before download or training. [cited]

| Model checked | Licence read | Fine-tune locally? | Redistribute the fine-tune? | May a Consilient user do the same on rights-cleared data? |
|---|---|---|---|---|
| Llama 3.3 | [Llama 3.3 Community License](https://developer.meta.com/ai/llama3_3/license/) | Yes. The grant permits modifications and derivative works. [cited] | Yes, with the agreement, notice, “Built with Llama”, the `Llama` name prefix for a distributed trained model, the AUP, and the 700M-MAU special licence threshold. [cited] | Yes, after accepting and complying with that custom licence; Consilient must not label it Apache/MIT. [cited] |
| Qwen3-32B | [Apache-2.0 licence file](https://huggingface.co/Qwen/Qwen3-32B/raw/main/LICENSE) | Yes. [cited] | Yes, with Apache-2.0 licence, modification and NOTICE obligations. [cited] | Yes, under the same obligations. [cited] |
| Qwen3.8-Max | [Qwen3.8-Max custom licence](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE) | Yes, expressly. [cited] | Yes, but display and separate-licence thresholds apply at 100M MAU / US$20M monthly revenue and to large Model-as-a-Service or AI Work Assistant businesses. [cited] | Yes below those conditions; exact-revision checking is mandatory because this is not Qwen3-32B's Apache licence. [cited] |
| Mistral-7B-v0.3 | [Official model card](https://huggingface.co/mistralai/Mistral-7B-v0.3/raw/main/README.md), marked Apache-2.0 | Yes. [cited] | Yes, with Apache-2.0 obligations. [cited] | Yes; other Mistral/Codestral revisions must be checked separately. [cited] |
| DeepSeek-R1 and R1-Distill-Qwen | [Official model card](https://huggingface.co/deepseek-ai/DeepSeek-R1/raw/main/README.md), MIT | Yes; the card expressly permits modifications, derivatives and distillation. [cited] | Yes, with the MIT notice; distilled Qwen and Llama variants also retain their base-family licence obligations. [cited] | Yes, subject to both the DeepSeek notice and the named base model's licence. [cited] |
| Gemma 1–3 | [Gemma Terms](https://ai.google.dev/gemma/terms), modified 1 April 2026 | Yes; fine-tunes are “Model Derivatives”. [cited] | Yes, with the terms, downstream use restrictions, modified-file notices and required Notice file. [cited] | Yes only if those flow-down conditions and the Prohibited Use Policy are accepted. [cited] |
| Gemma 4 | [Google's Gemma 4 Apache-2.0 page](https://ai.google.dev/gemma/apache_2) | Yes. Google's older Gemma terms explicitly direct Gemma 4 to this separate Apache-2.0 licence. [cited] | Yes, with Apache-2.0 obligations. [cited] | Yes, under Apache-2.0. [cited] |
| Microsoft Phi-4 | [MIT licence file](https://huggingface.co/microsoft/phi-4/raw/main/LICENSE) | Yes. [cited] | Yes, with the MIT copyright and permission notice. [cited] | Yes, under the same obligations. [cited] |

The product-safe shape is a trainer that accepts a user-selected exact model revision and a
user-controlled dataset, shows the resolved licence before any download, records acceptance
and hashes, and emits the required notices with any exported adapter. It should not bundle a
claim that an entire family is redistributable. [asserted]

Consilient can distribute training **capability** without redistributing weights. If it
downloads, hosts or exports a base or derivative itself, it takes on the corresponding
distribution obligations. [asserted]

## 5. What 32,607 MiB can actually train

`nvidia-smi` reported `NVIDIA GeForce RTX 5090, 32607 MiB, driver 610.62` on 20 August 2026.
[measured] That is 31.84 GiB before the display, CUDA context, allocator reserves,
activations, temporary workspaces and dataloader/runtime overhead. [algebra]

### Memory arithmetic

For a conventional mixed-precision AdamW full fine-tune, a defensible static estimate is:

`2 bytes weights + 2 gradients + 4 FP32 master weights + 4 first moment + 4 second moment
= 16 bytes/parameter`, before activations and runtime; implementations can approach
18 bytes/parameter. [algebra]

| Parameter count | 16 B/parameter | 18 B/parameter | GPU-only verdict before activations |
|---:|---:|---:|---|
| 1B | 14.9 GiB | 16.8 GiB | Feasible with checkpointing and a controlled sequence/batch. [algebra] |
| 1.5B | 22.4 GiB | 25.1 GiB | Marginal; little activation headroom. [algebra] |
| 2B | 29.8 GiB | 33.5 GiB | Does not fit as a conventional full fine-tune once activations exist. [algebra] |
| 3B | 44.7 GiB | 50.3 GiB | Does not fit. [algebra] |

For LoRA with a BF16/FP16 frozen base, base weights alone cost about
`2 × parameters`; trainable adapters, their gradients/optimizer state and activations are
additional. [algebra]

| Base | BF16/FP16 base weights only | LoRA verdict |
|---:|---:|---|
| 7B | 13.0 GiB | Comfortable with gradient checkpointing and sensible sequence length. [algebra] |
| 8B | 14.9 GiB | Comfortable. [algebra] |
| 14B | 26.1 GiB | Edge case: short sequences, batch one and careful target modules only. [algebra] |
| 32B | 59.6 GiB | Does not fit GPU-only. [algebra] |

For QLoRA, NF4 plus quantisation metadata is roughly `0.55–0.65 bytes/parameter` for the
frozen base. This is a planning bound, not a measured allocation; adapters, activations,
dequantisation workspaces and runtime remain additive. [algebra]

| Base | Quantised base planning range | QLoRA verdict |
|---:|---:|---|
| 8B | 4.1–4.8 GiB | Comfortable; the best first experimental scale. [algebra] |
| 14B | 7.2–8.5 GiB | Comfortable at modest context. [algebra] |
| 32B | 16.4–19.4 GiB | Plausible but tight after training state and activations; benchmark before admitting unattended runs. [algebra] |
| 70B | 35.9–42.4 GiB | Quantised base alone exceeds the card; CPU offload is required and changes the throughput regime. [algebra] |

The packed-weight arithmetic is optimistic. This machine measured a 19 GB decimal
`gemma4:31b` Ollama artefact occupying 29,442 MiB in use during inference, leaving only
3,180 MiB free. [measured] A QLoRA backend has a different allocation pattern, but that
measurement is enough to reject “the 4-bit file fits, therefore training fits” as an
admission rule. [asserted]

MoE active-parameter counts reduce compute, not the memory needed to keep experts resident;
training fit is governed by total parameters. [algebra] Long contexts enlarge activations,
so an experiment that fits at 512 tokens does not establish that repository-scale sequences
fit. [algebra]

### Practical training envelope

| Method | Reliable target on this card | What is not a default |
|---|---|---|
| Full fine-tune | Up to about 1B with checkpointing. [algebra] | 1.5B is marginal; 2B+ conventional AdamW is out. [algebra] |
| LoRA on BF16/FP16 base | 7–8B. [algebra] | 14B is an edge experiment; 30B+ is out GPU-only. [algebra] |
| QLoRA | 7–14B. [algebra] | 30–32B requires a measured batch/sequence configuration; 70B is out without offload. [algebra] |

“Free” means no provider token bill. Electricity, SSD writes, GPU opportunity cost, failed
runs and human evaluation remain real costs. [asserted]

For dynamic personalisation, keep the base frozen and produce versioned adapters in bounded
offline batches. Each batch needs an immutable dataset manifest, a held-out verifier that was
not part of the reward, a comparison with the previous adapter, and a one-command rollback.
Do not update weights continuously from the model's own unverified outputs: that collapses
provenance and trains the model towards the current verifier's blind spots. [asserted]

## 6. Training on measurements: legally cleaner, but not yet clean

EXP-47's kill/survive labels are mechanical outcomes from `pytest`, `mypy` and `ruff`; they
are measurements, not frontier-model outputs. [measured] The source examples are a separate
issue. The mutants contain this repository's source text, and the current git/trajectory
record does not establish line-by-line that none of that text originated in a frontier-model
response. Mechanical labels do not cleanse the examples they label. [measured]

Therefore:

- A model trained only on independently authored or licence-cleared examples plus mechanical
  verifier measurements is outside the provider-output clauses quoted above. [asserted]
- A text model trained on EXP-47 diffs is **not yet proved** output-free. Either establish
  source provenance, construct a clean corpus, or obtain provider authorisation before using
  those diffs as training text. [asserted]
- Frontier assistance may write generic training software, but no provider response may
  become an example, target, reward, teacher signal or evaluation answer under the
  conservative boundary. OpenAI's and Cursor's undefined “competing” clauses still need
  advice if their outputs materially develop the trained model. [asserted]

The proposed predictor also has a utility problem. The full EXP-47 composite checks ran
1,931 mutants in 104.1 seconds, about 0.054 seconds per mutant. [measured] Predicting whether
those checks will run green is dominated by running them. The only potentially valuable task
is different: after the real checks pass, predict which accepted artefacts still resemble
known false accepts and deserve a different evidence class, such as generated tests or human
review. [asserted]

EXP-56 measures the hindsight routing ceiling among its fixed set of zero-shot reviewer
models on mutation detection. It does not bound a future fine-tuned model that is not in that
candidate set, and it does not by itself establish that verifier-outcome prediction improves
routing. [algebra] EXP-58 therefore treats EXP-56 as a baseline and gate, not as proof that
training is useful. [asserted]

## 7. Decision record

**Reasoning.** The rejected option was continuous distillation of all frontier interactions
into a local coding model. It is blocked by current terms, mixes uncertain rights into an
irreversible weight artefact, and has no held-out evidence that it improves verified work.
The selected option is bounded local adapter research on an exact licensed model and an
output-free, provenance-complete corpus. [asserted]

**Reversal path.** Revert this decision and its experiment registration with
`git revert HEAD`. No model, dependency or downloaded weight was created by this decision.
[measured]

**Falsifiers.** Reopen the frontier-output boundary if a provider gives written
account-specific permission or publishes terms that unambiguously permit the exact training
and distribution use. Reject the local-training direction if EXP-58 cannot beat its frozen
and non-neural baselines under a leakage-resistant split, or if its gain disappears on an
output-free held-out corpus. [asserted]

## Sources read in full

- Anthropic:
  [Consumer Terms](https://www.anthropic.com/legal/consumer-terms),
  [Commercial Terms](https://www.anthropic.com/legal/commercial-terms),
  [Usage Policy](https://www.anthropic.com/legal/aup). Read 20 August 2026; the rendered
  Consumer and Usage pages displayed no effective date. [measured]
- OpenAI:
  [consumer Terms of Use](https://openai.com/policies/row-terms-of-use/) and
  [Services Agreement](https://openai.com/policies/services-agreement/), both effective
  1 January 2026. Read 20 August 2026. [measured]
- SpaceXAI:
  [Consumer Terms](https://x.ai/legal/terms-of-service), effective 26 June 2026;
  [AUP](https://x.ai/legal/acceptable-use-policy), effective 14 August 2026; and
  [Enterprise Terms](https://x.ai/legal/terms-of-service-enterprise), last updated
  14 August 2026. Read 20 August 2026. [measured]
- Anysphere:
  [Cursor Terms](https://cursor.com/terms-of-service),
  [AUP](https://cursor.com/acceptable-use-policy), and
  [MSA](https://cursor.com/terms/msa). Read 20 August 2026; the rendered pages displayed no
  publication/effective date beyond acceptance-based effectiveness in the MSA. [measured]
- Model licences: the exact first-party licence/model-card URLs linked in §4, all read
  20 August 2026. [measured]
- UK rights and data protection:
  [IPO ownership guidance](https://www.gov.uk/guidance/ownership-of-copyright-works) and
  [ICO AI lawfulness guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-lawfulness-in-ai/),
  read 20 August 2026. [measured]
