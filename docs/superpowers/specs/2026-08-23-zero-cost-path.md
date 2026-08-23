# Zero-cost path: a native, fail-closed routing ladder

**Status:** specification only; no route, gate, CLI command or provider integration is implemented by
this document. [measured]

**Decision record:** [ADR-0088](../../decisions/0088-make-zero-cost-a-native-fail-closed-routing-ladder.md).
**Killing experiment:** [EXP-132](../../10-research/experiment-register.md#exp-132--can-the-zero-cost-ladder-complete-representative-work-without-hidden-spend-or-verifier-risk-regression-blocked).
[measured]

## 1. Correction and product boundary

**Correction:** a person who installs Consilient, supplies no account and has an ordinary CPU-only
laptop gets no model work from the product today. The hardware probe emits an unknown memory topology
for CPU machines, `local_fit.fit()` refuses that topology, no product caller invokes local acquisition,
and `scripts/dispatch.py` invokes harness CLIs without binding an outcome to its authentication mode,
account or plan. It passes the non-Git ambient environment and rejects common metered keys only for
Grok, so even the current “subscription” path is not proven subscription-only. The local and hosted
adapters in `docs/20-design/backends.md` are research artefacts, not a route. [measured:
`scripts/hardware_probe.py`, `src/consilient/local_fit.py`, `scripts/dispatch.py`,
`docs/00-context/subscription-reach-2026-08-22.md`, `docs/20-design/backends.md`, inspected 2026-08-23]

“Zero configuration” means **no account, API key, sign-up or payment method**. It does not mean no
download: the first local run may need network access to obtain openly licensed weights, unless a
qualified model is already cached. “Zero cost” means Consilient cannot create a monetary charge; it
does not pretend that electricity, hardware, bandwidth or human review has no cost. [asserted]

ADR-0048's capability-level promise is not weakened: every shipped capability needs a fully usable
local path on an admitted hardware profile; a hosted-only feature remains unshippable. The reference
smoke/task envelope below is the first floor to measure, not a substitute for that obligation. A
particular below-floor machine may report that its local route is unavailable, but that refusal cannot
be used as evidence that the capability itself has a local path. A zero-cost request never becomes a
paid request; the ladder may climb past an unavailable machine-specific rung, then refuse after every
eligible rung is exhausted. [measured: ADR-0048] [asserted]

A free third-party API contacts that provider's server, not a Consilient-operated server, so it is
compatible with ADR-0048. It is still neither local nor zero configuration and therefore cannot
satisfy `Z0_LOCAL`. [measured: ADR-0048] [asserted]

## 2. Existing bar and the delta

Ollama already supplies account-free local inference and model download on Windows, macOS and Linux;
`llama.cpp` already supplies CPU inference and quantised GGUF execution. OpenRouter, Google, Groq and
Cloudflare already supply documented free hosted inference. Consilient must reuse those engines and
provider APIs, not build another inference runtime or free-model catalogue. [cited: official sources in
`../../10-research/bibliography.md` §18, all read 2026-08-23]

The bar Consilient must beat is not raw inference. It is one route that joins fresh zero-price proof,
honest local quota leases/bounded bootstrap, exact front-door provider/upstream endpoint/model
provenance, task-native verification, measured false-accept bounds and a structural prohibition on
shedding into spend. EXP-132 measures zero cash spend, useful joint success and adverse
rate-limit/catalogue outcomes on sealed panels; a later coverage-valid experiment is still required
before automatic acceptance. [asserted]

## 3. Current surfaces to reuse

The source review changed the design in six places. [measured]

| Existing surface | Finding | Consequence for this specification |
|---|---|---|
| ADR-0048 | Every capability must remain usable locally by someone who pays nothing and contacts no Consilient-operated server. [measured] | Free hosted APIs are optional rungs, never the zero-configuration definition. [asserted] |
| ADR-0044 as amended by ADR-0064 | Subscription capacity precedes metered use; authorised metered vendors share one ceiling; missing authority refuses. The executable budget path is still OpenRouter-specific. [measured] | Preserve the policy, specify the multi-provider gap, and never use a free quota ledger as spend authority. [asserted] |
| ADR-0027 | Domain, harness, provider and model are independent identities. [measured] | A generic `free` backend or a pooled beta estimate is invalid. [asserted] |
| `local_fit.py` | Conservative fit/acquisition types exist, but CPU topology, disk enforcement, licence/hash admission, an inference-runtime package and a product caller do not. [measured] | Extend the chokepoint; do not create a second downloader or bypass fit. [asserted] |
| `usage.py`, `budget.py`, `routing.py` | Quota and money are separate; spend refuses closed; beta exposure refuses when unmeasured. None is wired into dispatch for this route. [measured] | Extend the existing three boundaries and keep their refusals. [asserted] |
| `dispatch.py`, `coordination.py`, `work_items.py`, `recall.py`, `instructions.py`, `events.py` | One runner, claim projection, task record, bounded context, instruction assembly and append-only writer already exist; authenticated subscription-plan binding and resumable task checkpoints do not. [measured] | Add ladder state to those records; no second orchestrator, scheduler, ledger or event writer. [asserted] |

## 4. The ladder

The dispatcher evaluates rungs in this order and records every considered route, including why it was
skipped. It selects the first route that passes **all** hardware/capability, data-boundary, catalogue
and quota checks; “cheapest” never bypasses “qualified”. Beta is a separate acceptance boundary:
missing safety evidence may leave generation supervised-only, but cannot admit automatic
verifier-accepted/shippable exposure. [asserted]

Within a rung, “best” means the eligible exact composition with the strongest measured task-stratum
joint success, then the most usable reserved headroom, then the lower measured wall time. Missing or
non-transferable measurements rank below measured ones; model self-confidence and provider marketing
never rank a route. [asserted]

| Rung | User requirement | Admissible route | Hard refusal |
|---|---|---|---|
| `Z0_LOCAL` | Consilient install only; no separately installed inference runtime, account, key, sign-up or payment method. [asserted] | A version-pinned, signature/hash-verified local runtime supplied through the approved package path, plus a cached or automatically downloaded licence-approved model whose full envelope fits and whose exact composition is qualified for supervised generation. [asserted] | Missing runtime packaging approval, unknown fit, insufficient RAM/disk, unavailable download, unapproved licence/format/hash, disallowed task data or missing capability evidence. Missing beta blocks automatic acceptance/shipment, not supervised generation. [asserted] |
| `Z1_FREE_KEY` | One key for one supported provider whose authenticated API can prove the account/request cannot be billed; the user may add more. [asserted] | An exact model freshly proved active and zero-priced for every billable dimension, plus either a local lease against observable allowance or the single-request bootstrap in §7. [asserted] | Ambiguous price/plan, billing-enabled account without a machine-enforced zero-price request boundary, multi-request work with unknown allowance, random unreported model identity, data-policy conflict or any paid fallback. [asserted] |
| `S_SUBSCRIPTION` | An existing user subscription, authenticated plan proof and a locally installed harness. A CLI login alone is insufficient. [asserted] | An exact account/plan-bound pool with a provider-side hard zero-marginal-charge boundary: overage and automatic top-up are disabled, or exhaustion is proved unable to debit anything. Fresh included headroom ranks eligible routes but is not the spend boundary. Ambient metered credentials are removed and the provider receipt binds the outcome to that plan. [asserted] | Missing/stale plan or headroom, unproved/active overage or top-up, ambient/selected API-key billing, exhausted quota, unqualified composition, absent credential or failed outer credential isolation. [asserted] |
| `M_METERED` | A permitted vendor credential **and** separately recorded, unexpired, bounded spend authority from the principal. [asserted] | A reservation accepted by the existing fail-closed budget chokepoint under the joint weekly/monthly ceiling. [asserted] | Zero-cost mode, absent/stale budget, absent ceiling, unknown/non-USD price, disallowed vendor, or reservation failure. [asserted] |

The transition from `S_SUBSCRIPTION` to `M_METERED` is not an automatic fallback. It is a distinct
spend-authorised action. A request starting with `cash_ceiling_usd = 0` is structurally unable to
enter `M_METERED`; no timeout, 429, provider message or model suggestion may change that value.
[asserted]

### 4.1 Concrete zero-configuration target

The first supported reference is a Windows 11 x86-64 laptop with four or more CPU cores, 16 GB system
RAM, no discrete GPU and 12 GB free disk. The initial acquisition candidate is Ollama's
`qwen3:1.7b` record: 2.03B parameters, Q4_K_M, 1.4 GB and Apache-2.0 on 2026-08-23. That is only
identity/format/licence evidence, not capability evidence. The first task envelope is text-only, one
candidate at a time, at most 8,000 input tokens, 2,000 output tokens and 20 minutes including first
download; the existing fit boundary may reduce it or refuse. These are engineering floors to test,
not measured sufficiency claims; EXP-132 freezes the 16 GB/no-GPU machine and includes first download
in the deadline. [cited: bibliography §18] [asserted]

The model record does not install an inference runtime. `acquire_local_model()` accepts a caller-
supplied downloader and no current product path installs or invokes Ollama/`llama.cpp`. Zero
configuration therefore requires an approved packaging choice that supplies a pinned runtime without
another user action and verifies its publisher/signature, licence, executable hash and update before
model acquisition. Adding or bundling that dependency remains an implementation blocker requiring the
project's normal dependency approval; until it is resolved, Z0 is unavailable rather than “install
Ollama first”. [measured] [asserted]

Before EXP-132, the honest capability label is `experimental, supervised-only`. Expected work is
bounded text transformation, extraction/classification, short evidence synthesis and small code repairs
with a task-native verifier. Large repository-wide refactors, long-context research, image/audio work,
high-consequence judgement and automatic acceptance are not promised on that reference machine.
[asserted]

If the machine is below the resource floor, offline without a cached qualified model, or cannot run
the task's required modality, the interface says `zero_configuration_unavailable` with the failed
requirement. It then tries `Z1_FREE_KEY` only if a supported key is already present; otherwise it
continues to an existing subscription and finally stops before spend unless prior authority exists.
[asserted]

## 5. Hosted offerings verified from first-party sources

This table is a dated discovery seed, not a permanent allowlist. “Verified” means the vendor's own
documentation described the offering on 2026-08-23; no authenticated inference or metered call was
made. A provider is automatically selectable only when its adapter can prove the same facts for the
specific account and model immediately before dispatch. [cited: bibliography §18] [measured]

| Provider/offering, retrieved 2026-08-23 | Account/key and documented free boundary | Instability that admission must retain |
|---|---|---|
| OpenRouter `openrouter/free` and explicit `:free` variants. [cited] | Account/API key. With under USD 10 lifetime purchased credits, the documented free limit was 20 requests/minute and 50 requests/day; inference price for the named free routes was zero. [cited] | Free models change often, may be unavailable or slow, the aggregate router chooses among models, and fixed model IDs are load-balanced across upstream endpoints with fallbacks on by default. Automatic acceptance requires an explicit `:free` model **and** frozen eligible upstream endpoint with fallbacks off; otherwise retain returned endpoint/fingerprint as a separate supervised composition. [cited] [asserted] |
| Google Gemini Developer API free tier, including selected Flash/Flash-Lite standard models listed as free on the dated pricing page. [cited] | Google AI Studio account/project and an authorisation key. Limits are per project across requests/minute, tokens/minute and requests/day; current account values are visible in AI Studio and are not guaranteed. [cited] | The models endpoint does not itself prove price; intersect live model support with current account tier/pricing. Free-tier content is documented as usable to improve Google products, so private-data eligibility may refuse this route. [cited] [asserted] |
| GroqCloud Free plan. [cited] | GroqCloud account/API key. The dated table listed, for example, `openai/gpt-oss-120b`, `openai/gpt-oss-20b` and `qwen/qwen3.6-27b` at 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute and 200,000 tokens/day. [cited] | Limits are organisation-wide, model exceptions exist and preview models may disappear; the account Limits page is authoritative for quotas and `/openai/v1/models` for active models. [cited] |
| Cloudflare Workers AI Free. [cited] | Cloudflare account ID/token. The free plan documented 10,000 neurons/day, resetting at 00:00 UTC, and failure rather than overage when exhausted; default text generation was 300 requests/minute. [cited] | Some named models require a paid billing method, and Cloudflare moved three formerly free models to paid-only on 2026-07-28. Active model, plan and neuron price must all be rechecked. [cited] |

GitHub Models is deliberately excluded: GitHub's first-party page says the service retired on
2026-07-30. That retirement is direct evidence that a cached “free providers” list is unsafe.
[cited: bibliography §18]

### 5.1 Dynamic discovery contract

Discovery is read-only and cannot itself admit a route. For every candidate it records front-door
provider, upstream endpoint, canonical model ID/revision/system fingerprint, supported methods/context,
every input/output/tool/cache billable
dimension, account plan/billing state, every quota window and remaining amount, concurrency, source
URL/endpoint, provider/endpoint retention and training policy, region, retrieval time and raw response
digest. [asserted]

Admission requires a first-party authenticated observation taken for the same account at task start;
an observation older than 15 minutes, a marketing page alone, a `max_price=0` filter covering only one
price dimension, or a catalogue with no account-tier proof is insufficient. The only quota exception is
§7's one-request bootstrap after the account/request is independently proved unbillable. A 404/403/429,
pricing schema change or conflicting source invalidates the candidate and triggers rediscovery of the
next free provider. It never creates permission to use a paid variant. [asserted]

Provider adapters are small translators into this shared evidence record. `refresh_models.py` remains
discovery-only: a newly visible model is quarantined until exact capability and verifier evidence
qualify it. Automatic catalogue change can remove eligibility immediately; it cannot grant automatic
acceptance. [asserted]

## 6. Admission and automatic climb

For each work item, the existing Owner supplies the task contract, consequence class, verifier
contract, data boundary, maximum context/output and deadline. The ladder then performs one deterministic
admission pass. [asserted]

1. Enumerate exact routes in rung order; preserve provider/model separately. [asserted]
2. Reject routes that cannot satisfy task capability, data boundary, licence or hardware fit. [asserted]
3. For `Z1_FREE_KEY`, refresh zero-price/unbillable-account-or-request proof; for `S_SUBSCRIPTION`, bind
   authentication, account, plan and included headroom, prove a provider-side hard zero-marginal-charge
   boundary with overage/top-up disabled, and strip ambient metered credentials; for `M_METERED`,
   require the already-authored spend reservation. [asserted]
4. Grant a local lease for the full worst-case request, token, daily and concurrency envelope against
   observable allowance. Unknown remaining capacity is not capacity except for §7's bounded one-request
   bootstrap on a structurally unbillable path. [asserted]
5. Obtain the exact-composition candidate ceiling from routing before an artefact can enter an
   automatically verifier-accepted/shippable path. A routing refusal leaves generation explicitly
   supervised-only: the sealed artefact awaits independent authenticated human acceptance and cannot
   be labelled automatically accepted. [asserted]
6. Acquire the existing coordination claim, assemble instructions/recall, and execute through
   `scripts/dispatch.py`. No sibling executor is introduced. [asserted]
7. Append the chosen rung, exact composition, evidence digests, quota lease/bootstrap, cash ceiling and
   every refusal to the existing trajectory before execution. Display the same facts to the user.
   [asserted]

Absence of a top-quality or preferred route is not itself a refusal: the pass continues down the
ladder. Exhaustion of all routes is a refusal with the first actionable missing requirement, such as
`local_ram`, `free_provider_key`, `subscription_headroom`, `human_review` or `spend_authority`.
[asserted]

## 7. Quotas, rate limits and interruption

Free allowance is not money. Extend `usage.py`'s existing provider-native quota record with absolute
limit, remaining amount, reserved amount and reset time for each requests/minute, tokens/minute,
requests/day, tokens/day and concurrency bucket. Keep cash reservations in `budget.py`; a zero-price
call must never manufacture a positive `SpendRequest`. [measured: current types] [asserted]

Before dispatch, the **local** scheduler leases the whole task envelope against every observable bucket
under its own lock. This prevents Consilient processes oversubscribing one account; it is not described
as an atomic reservation at the provider, and other clients may still consume the allowance. If any
required bucket is insufficient, release no partial lease and consider the next zero-cost route.
[asserted]

A provider whose authenticated API proves the account/request is unbillable but exposes no complete
remaining-quota view may bootstrap exactly one non-streaming request, locally paced below every
documented limit, with one candidate and a fixed output cap. A 429/refusal is an adverse terminal
outcome. This exception cannot admit a multi-request/tool loop, cannot be used on a merely assumed free
plan, and counts as candidate exposure. After every response, reconcile whatever authenticated
headers/account state exists and append both lease and observation; disagreement or an unobservable
second request makes the pool unavailable. [asserted]

A rate limit or free allocation exhaustion during generation is a typed adverse terminal outcome,
not success and not a reason to switch models inside the attempt. The partial artefact is sealed and
quarantined; its attempt consumes candidate exposure and it cannot reach the verifier's accepted path.
The reservation is reconciled, `Retry-After`/reset is recorded, and the work item becomes
`blocked_on_quota` or terminal `rate_limited`. [asserted]

There is no resumable task checkpoint in the current product. Until one exists, recovery starts a new
attempt from the original sealed state only if the deadline, free quota and robust candidate ceiling
permit it; otherwise the work stays blocked/refused. A future checkpoint may resume only the same exact
composition from a content-addressed, verifier-ineligible checkpoint with tool effects and quota
receipts sealed. Changing provider/model is a new attempt, never a continuation. [measured] [asserted]

No free-tier failure sheds automatically to a subscription or metered route mid-attempt. A fresh
admission pass may select another **non-metered** rung only within the original request's authority and
candidate ceiling. Metered use always requires a separate pre-existing spend-authorised action.
[asserted]

## 8. Quality, beta and different facts

The brief's logarithmic i.i.d. expression is retained only as a diagnostic. The operational rule from
ADR-0077 is distribution-free: with per-attempt bad-and-accepted risk `q`, an exposure budget
`epsilon`, and upper confidence bound `q_upper`, `n_max = floor(epsilon / q_upper)`. When `q` has not
been measured directly, the conservative substitution is `q_upper := beta_upper`. Unmeasured human
beta therefore permits **zero**, not one, automatically verifier-accepted/shippable candidate
exposures. [algebra] [measured]

`beta = P(verifier accepts | human rejects)`. A weaker free model may produce more bad artefacts, but
that does not by itself imply a larger conditional beta; its errors may be easy for the verifier to
reject. The conservative requirement is stronger and simpler: no free/subscription/local rung inherits
another rung's estimate. Record and bound `q` and beta for the exact front-door provider, upstream
endpoint, model revision/system fingerprint, verifier contract and task stratum; otherwise keep its
output supervised-only. [algebra] [asserted]

The current `Beta` scope contains task family and verifier version only, and the current routing caller
does not enforce provider/model/rung scope. Implementation must close that gap before automatic
acceptance from this ladder. Public benchmarks and provider labels remain priors, never route verdicts.
[measured: `src/consilient/beta.py`, `src/consilient/routing.py`, ADR-0027]

A second model reading the same evidence is not a different class of facts. One Owner remains the
baseline. Additional checks earn weight only through exogenous observations such as executing the
artefact, applying a task-native oracle, fetching a primary source or an independent authenticated
human verdict; model-family diversity is provenance metadata, not `evidence_class`. [measured:
`CONSILIENCE.md`, ADR-0077, task-management specification] [asserted]

## 9. Credentials, privacy and authority

Provider secrets live outside the repository in an OS credential store. Only an outer-isolated,
instance-local broker may resolve an opaque credential identifier and inject the secret into the
provider adapter process. A child model/harness, brief, prompt, environment dump, recall packet,
trajectory event, checkpoint, dashboard and repository file receives no secret value. [asserted]

A gitignored file, opaque reference or same-user broker is not isolation. Under today's same-user,
permission-bypass child launch, every credential-bearing route refuses, including subscription CLIs
whose auth files or token stores are readable by that child. It may activate only after an independently
tested outer process/security namespace lets the authenticated adapter or harness operate while denying
the hostile child file, process, network and IPC access to the broker and subscription credentials. The
conformance test must attempt same-user auth-file reads, process inspection, unauthorised IPC connection
and raw credential retrieval; sink canaries alone are insufficient. [measured: ADR-0084] [asserted]

Logs retain provider, account/project digest, credential ID, key type, auth result and entitlement
proof digest, never the key. Existing secret scans remain mandatory. An adapter that cannot prevent a
child runtime from reading the secret is ineligible. [asserted]

External free tiers are admitted only when the task's data boundary permits that provider's current
terms and data use. A privacy refusal falls back to local or another eligible route, not to redaction
guesses. The principal alone may supply credentials, author spend, approve/publish an artefact or lift
a gate; the ladder may propose and refuse but cannot exercise that authority. [asserted]

For OpenRouter, provider selection happens after the prompt would leave the machine. Before sending a
byte, the request must restrict eligible endpoints to the task's frozen retention/training/region
policy, disable provider/model fallbacks that escape it, and use `data_collection = deny` and/or
`zdr = true` where the contract requires them. An aggregate free router is limited to public data
unless **every** eligible endpoint is proved compatible in advance; a returned provider/model identity
cannot repair a disclosure. For an exact route, set the provider allowlist to one frozen endpoint and
disable fallbacks; otherwise every returned endpoint/fingerprint is a separate supervised composition.
Unknown endpoint policy refuses. [cited: bibliography §18] [asserted]

## 10. User-visible contract and events

Every run displays and records: `rung`, `domain`, `harness`, front-door `provider`, upstream endpoint,
exact `model_revision`/system fingerprint, `cash_ceiling_usd`, `price_proof_at`, quota lease/observation,
beta/q scope and ceiling, data boundary, and why every earlier route was skipped. “Free” without those
receipts is not a valid status.
[asserted]

The terminal state distinguishes `completed_verified`, `completed_pending_human`, `refused`,
`rate_limited`, `catalogue_changed`, `partial_quarantined`, `subscription_required` and
`spend_authority_required`. Only a task-native verifier plus the required authenticated human verdict
may close a supervised-only artefact; an exit code or non-empty diff is insufficient. [asserted]

Reuse is fixed: `dispatch.py` owns execution/fan-out; `coordination.py` owns claims; `work_items.py`
owns task state; `recall.py` owns bounded prior context; `routing.py` owns exposure ceilings;
`usage.py` owns non-cash allowance; `budget.py` owns cash; `instructions.py` owns context assembly; and
`events.py` remains the single append-only writer. The implementation extends these surfaces and their
tests; a second orchestrator, quota ledger, downloader or event stream is a defect. [asserted]

## 11. Acceptance requirements

| ID | Requirement and smallest proving check |
|---|---|
| ZC-01 | A clean Consilient install with no credential **and no preinstalled Ollama/llama.cpp binary** on the frozen 16 GB/no-GPU/12 GB/networked reference acquires its approved runtime/model and completes the frozen local smoke task; model/runtime download is allowed, remote inference and refusal do not pass. [asserted] |
| ZC-01R | A below-floor or offline-without-cache fixture refuses with the exact prerequisite and makes no provider call; this is separate from ZC-01. [asserted] |
| ZC-02 | A zero-cost work item carries immutable `cash_ceiling_usd = 0`; mutation, 429 and provider paid-fallback fixtures cannot admit `M_METERED`. [asserted] |
| ZC-03 | Provider admission fails if any price dimension, account/billing tier, endpoint/model identity or catalogue freshness is absent/ambiguous/non-zero; absent remaining quota also refuses except for the proved-unbillable one-request bootstrap. [asserted] |
| ZC-04 | One ordinary key is sufficient only for a supported adapter whose authenticated API proves the account/request unbillable; it can attempt one bounded request without a second credential. Gemini/Groq remain ineligible if their key alone cannot prove that state. [asserted] |
| ZC-05 | A catalogue-change fixture removes eligibility but cannot add automatic-acceptance authority; stale GitHub Models is rejected. [asserted] |
| ZC-06 | A mid-stream 429 fixture yields `partial_quarantined`/`rate_limited`, consumes exposure, preserves receipts and cannot be classified `ok`. [asserted] |
| ZC-07 | Local leases cover every observable provider-native bucket under one local lock and reconcile after success, refusal, timeout and process-tree kill; no check calls that a provider-side reservation. [asserted] |
| ZC-08 | Beta/q lookup includes upstream endpoint/system fingerprint and task stratum; no estimate means zero automatic verifier-accepted/shippable exposure while explicitly supervised generation remains possible. [asserted] |
| ZC-09 | The trajectory and user display name the rung and exact composition and retain every skipped-route reason. [asserted] |
| ZC-10 | While the authenticated provider adapter or subscription harness still operates, a hostile same-user child cannot read broker or subscription auth files/process memory, connect to IPC without a run-scoped grant or retrieve a raw credential; canaries also stay absent from every child/durable sink. [asserted] |
| ZC-11 | Local/free/subscription failures and ambient Claude/Codex/Grok metered-key mutations never invoke a metered endpoint without separately recorded, current principal-authored authority and an accepted budget reservation. [asserted] |
| ZC-12 | The implementation adds no CLI command, changes no gate result, and retains `events.py` as the sole writer and `dispatch.py` as the sole execution surface. [asserted] |
| ZC-13 | Before any prompt leaves, provider-policy fixtures freeze an eligible upstream endpoint, disable escaping fallbacks and enforce the declared training/retention/region policy; unknown or mismatched policy refuses. [asserted] |
| ZC-14 | Every `S_SUBSCRIPTION` outcome carries authenticated account/plan/headroom evidence, passes the ZC-10 outer-isolation check and proves overage/automatic top-up disabled or an equivalent provider-side hard zero-marginal-charge boundary. Exhaustion and concurrent-headroom race fixtures must refuse without debiting extra usage; a CLI login, local headroom observation or non-empty output alone cannot pass. [asserted] |

## 12. Strongest evidence against, reversal and experiment

The strongest counter-case is that “free” is a trap: small local models may not clear useful quality,
cloud catalogues can vanish, quotas can expire halfway through work, free data terms may exclude the
user's task, and the engineering/verification burden may exceed an honest subscription. Cloudflare's
July 2026 paid-only migration and GitHub Models' July 2026 retirement show the catalogue risk; the
current local backend attempt produced no artefact, and no human-labelled per-rung beta exists.
[cited: bibliography §18] [measured: `docs/20-design/backends.md`, current beta scope]

The decision concedes that case. The product never describes an unqualified attempt as useful work,
never hides rate failure, and says `subscription_required` when the zero-cost floor loses. A
subscription is the honest answer for tasks outside the tested local/free envelope; zero-cost remains
available for the envelope EXP-132 actually confirms. [asserted]

Reversal is cheap: remove cloud-free providers from the discovery seed and retain local plus only
proven subscription routing; if a model-dependent capability has no passing local arm, remove it from
the shipped surface until a later local composition passes rather than weakening ADR-0048. No stored
task or event schema needs to reinterpret paid work as free. [asserted]

EXP-132 is already written in the experiment register with one cold-install smoke, a 40-task warm
utility panel, four 120-task safety pools, local/free-cloud/subscription utility arms, attainable
composition-stratum rejection denominators, adverse missing/rate-limit outcomes, zero-spend kill rules
and a 30-day stop. It limits
every safety conclusion to the sealed panel and cannot activate automatic routing. It is `BLOCKED`
until the route, approved local runtime path, banks, outer credential isolation and authenticated
human-verdict ingress exist. [measured]

## 13. Non-goals

This specification adds no implementation, model download, provider account, credential, metered
call, dependency, CLI command, gate change, new agent role, new evidence class or permission to operate
unattended in another repository. It does not claim that free models are as capable as subscriptions,
that a 3B model fits every 16 GB machine, or that a documented free tier will remain free. [measured]
[asserted]
