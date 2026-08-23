# Native scientific and mathematical execution on pinned open data

**Correction.** The brief compresses the Inquiry trigger incorrectly: the live rule is
`(G1 one-way door OR G2 high blast radius) AND G3 dispersed priors AND G4 formalizable`, not
one-way-door-and-dispersion-and-formalizability; it also quotes the superseded iid squad formula,
whereas current routing uses the dependence-robust union bound and refuses while human-labelled
beta is unestimated. [measured: `../../20-design/inquiry-tier.md:39-66`;
`../../../src/consilient/routing.py:1-20,60-105`; `python -m consilient.cli beta --json`,
23 August 2026]

**Status:** specification only. This document adds no product import, source file, dependency, CLI
command, gate change, credential, metered call or active route. ADR-0094 records the decision and
EXP-137 is the pre-registered killing experiment. [measured] [asserted]

## 1. Plain answer and the bar

The capability is one scientific Owner with an isolated local execution environment, a pinned
open-data input, a hypothesis fixed before outcome access, and a result bound to the exact data,
code, environment and assumptions that produced it. It is not a second orchestrator and it is not a
fleet of agents role-playing scientists. Additional roles are admitted only when they introduce a
different class of facts, such as independently executing a verifier or checking a dataset licence
against its source. [asserted]

The execution surface itself is occupied territory. ChatGPT Data Analysis already writes and runs
Python in a stateful Jupyter environment for transformations, calculations and statistical analysis;
NumPy, SciPy, SymPy and pandas already supply the requested numerical, statistical, symbolic and
tabular operations. Consilient does not claim greater mathematical breadth. [cited: S1-S5]

The narrower delta is a fail-closed scientific record: no data use before licence admission; no
result without immutable byte and environment identities; no experiment without a prior hypothesis
and stopping rule; no simulated world-number; and no trusted threshold when plausible structural
assumptions reverse it. The measurement that would show this delta is EXP-137's generic-execution
control: if ordinary code execution matches the proposed profile, the laboratory loses and is cut
back to the generic path. [asserted]

The repository previously said code, files, spreadsheets and experiments were table stakes to
consume, with only the decision of *when* to experiment worth building. The principal's newer
instruction expands native assembly, but does not repeal that economy: this design therefore adopts
the mature libraries and extends the existing retrieval and trajectory paths rather than building a
scientific platform. [measured: `../../20-design/living-system.md:106-121`] [asserted]

## 2. Boundary and location

`src/consilient/` remains standard-library-only. The current project declares zero runtime
dependencies and AST checks reject third-party imports across the package. The scientific packages
therefore live in a separately locked local environment used by an isolated runner outside the
product package. The implementation build unit will choose the runner filename; this specification
does not reserve a source path. [measured: `../../../pyproject.toml:28-35`;
`../../../tests/test_v0_invariants.py:3226-3235,4206-4227`] [asserted]

There is one orchestration path: [asserted]

1. `work_items.py` owns the task and the different class of facts expected from it.
2. `dispatch.py` selects the Owner and launches the existing run boundary.
3. `instructions.py` assembles the scientific contract and bounded context; `recall.py` remains the
   only bounded trajectory-context projection.
4. `scripts/knowledge.py` discovers or records the open source and extends its existing
   `knowledge.retrieved` receipt; there is no second retrieval ledger.
5. The isolated runner reads only the admitted manifest and a locked environment, then emits a
   bounded result bundle.
6. `events.py` remains the only append writer; `coordination.py` owns claims and `budget.py` owns
   time/compute ceilings.
7. `routing.py` remains unwired and `routing_orchestration_enabled` remains `false`.

`scripts/knowledge.py` already records a URI, query and content SHA-256 through the single writer,
and `events.py` already requires source, licence, retrieval time, status and digest for a successful
`knowledge.retrieved` event. It is not yet a dataset contract: the current policy puts the licence URL
in `source_url`, accepts any non-empty licence string, never applies its software-licence allowlist,
and permits credential-bearing unmetered connectors. Scientific acquisition extends this path with
separate content/version/licence identities and requires an empty credential set. [measured:
`../../../scripts/knowledge.py:254-284,311-374`;
`../../../scripts/knowledge_policy.py:19-30,96-159,266-291`;
`../../../src/consilient/events.py:509-555`]

The default **candidate** squad size is one. Agreement among agents seeing the same prompt, data and
code is echo; the open dataset and executed artefact are the exogenous inductions. Every T2/T3 result
seeking decision-grade status must then pass the live Inquiry verification rule: an isolated second
agent receives the sealed data, code, environment, hypothesis and result schema but not the first
write-up, executes the artefact and independently re-derives the decision. This is a verifier, not a
second candidate or a vote. A missing, non-reproducible or disagreeing derivation refuses
decision-grade status; it is never averaged away, and the verifier does not inherit the principal's
authority. [measured: `../../20-design/inquiry-tier.md:85-94`] [asserted]

## 3. Capability surface and exact dependency cost

### 3.1 Operations

| Surface | What the Owner may execute | Implementation floor |
|---|---|---|
| Statistical testing | Descriptive statistics; exact, parametric, rank, permutation and bootstrap tests; effect sizes and intervals; multiplicity correction written in the analysis plan | `numpy`, `scipy.stats`; do not hand-code a test SciPy supplies. [cited: S2, S3] |
| Numerical methods | Linear algebra, roots, interpolation, integration, differential equations, sparse operations and numerical convergence checks | `numpy`, `scipy`. [cited: S2, S3] |
| Symbolic mathematics | Algebraic manipulation, equation solving, calculus, limits, series and symbolic-to-numeric cross-checks | `sympy` with its `mpmath` dependency. [cited: S4] |
| Optimisation | Local/global constrained and unconstrained optimisation, linear programming, least squares, root finding and curve fitting | `scipy.optimize`; CVXPY is not in the floor. [cited: S3] |
| Simulation | Reproducible seeded sampling, Monte Carlo and parameter/structure sweeps; outputs are sign, threshold and regime | `numpy.random`, `scipy`; seeds and bit-generator identity are recorded. [cited: S2] |
| Data acquisition | No-key HTTPS retrieval, bounded redirects/bytes/time, hashing, archive inspection and immutable caching | Python `urllib`, `hashlib`, `ssl`, `zipfile`, `tarfile`, `json`; existing `scripts/knowledge.py`. [asserted] |
| Data cleaning | Schema inspection, typed parsing, joins, missingness, deduplication, filtering, grouping and deterministic transforms over tabular data | `pandas`; stdlib `csv`/`json` for small inputs. [cited: S5] |

This is the full v1 floor. `statsmodels` (regression/GLM/time series), `PyMC` (Bayesian
modelling), `scikit-learn` (predictive modelling), `CVXPY` (specialised convex modelling), `xarray`
(labelled multidimensional data), plotting stacks and notebook servers are absent. A task may propose
one as a separately locked capability only when the pre-registered method cannot be expressed by the
floor; that is a new dependency decision, not an import of convenience. [cited: SciPy itself names
several of these as out of scope, S3] [asserted]

### 3.2 Binding v1 lock and measured cost

On CPython 3.13.11, Windows x86-64, a no-cache binary-only download and isolated target install on
23 August 2026 selected the following complete eight-wheel closure. The download is exactly
**66,334,930 bytes (63.262 MiB)**; the installed target is **10,866 files and 326,691,897 logical
bytes (311.558 MiB)**, including generated bytecode. This is a platform snapshot and says nothing
about other OS/architecture wheels or filesystem allocation units. [measured: `python -m pip
download --disable-pip-version-check --no-cache-dir --only-binary=:all: --platform win_amd64 --python-version 313 --implementation cp --abi
cp313 numpy==2.5.2 scipy==1.18.1 sympy==1.14.0 pandas==3.0.5`; offline `pip install --target`;
file-count and length sum]

| Package | Role | Version | Wheel bytes | SHA-256 |
|---|---|---:|---:|---|
| NumPy | direct | 2.5.2 | 12,460,532 | `85aaccb24182c25df891ad0ec333585967e115269d5f1b17f2c9ae005bc96657` |
| SciPy | direct | 1.18.1 | 36,622,841 | `559ed65f60c1af5a03f3912605a1b5114f522c7c32fb23c3376ae8f03219fe28` |
| SymPy | direct | 1.14.0 | 6,299,353 | `e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5` |
| pandas | direct | 3.0.5 | 9,826,896 | `0d298e951f23016ce4699951d044ae6418dbc91bf68cefca0f77666fcbb4e5c6` |
| mpmath | SymPy dependency | 1.3.0 | 536,198 | `a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c` |
| python-dateutil | pandas dependency | 2.9.0.post0 | 229,892 | `a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427` |
| six | python-dateutil dependency | 1.17.0 | 11,050 | `4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274` |
| tzdata | pandas dependency | 2026.3 | 348,168 | `dc096730c87af6cab1b171c9d532be840741ff5d459015e7f6947bd7d7e54931` |

The implementation lock must carry exact versions, wheel hashes, Python/platform tags and upstream
licences, and must pass the existing adopted-component licence gate before use. It is not added to
`pyproject.toml`: installing the Consilient product must not install this environment. An unavailable
or hash-mismatched wheel makes scientific execution unavailable; it never falls back to ambient
packages. [asserted]

The resolution, hashes and footprint were verified, but this temporary target was not execution-
verified: Windows Application Control blocked SciPy's native extension from `%TEMP%`. These
measurements establish dependency cost and artefact identity, not successful scientific execution on
this policy configuration. A later build must import and exercise the locked environment from its
approved isolated location before claiming the capability works. [measured] [asserted]

The producing measurement retained this machine-readable receipt: [measured]

```powershell
$wheelFiles = Get-ChildItem -LiteralPath $wheelDir -File -Filter '*.whl'
$installedFiles = Get-ChildItem -LiteralPath $installDir -File -Recurse
[ordered]@{
    wheel_files = $wheelFiles.Count
    wheel_bytes = ($wheelFiles | Measure-Object Length -Sum).Sum
    wheel_artifacts = @($wheelFiles | Sort-Object Name | ForEach-Object {
        [ordered]@{
            name = $_.Name
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
    installed_files = $installedFiles.Count
    installed_logical_bytes = ($installedFiles | Measure-Object Length -Sum).Sum
} | ConvertTo-Json -Compress
```

The eight `wheel_artifacts` rows are retained as the package/byte/SHA-256 table immediately above;
the aggregate receipt was: [measured]

```json
{"platform":"win_amd64","python":"3.13.11","pip":"26.2.1","wheel_files":8,"wheel_bytes":66334930,"installed_files":10866,"installed_logical_bytes":326691897,"import_status":"blocked_by_windows_application_control_from_temp"}
```

## 4. Open data from discovery to citation

### 4.1 Admission sequence

The sequence is fixed and fail-closed. Metadata-only discovery may inspect catalogue and licence
records, but the hypothesis must be registered before any response body likely to contain observations
is requested or any existing data cache is opened. A bounded acquisition process may then seal bytes
without exposing them to the Owner; only the runner may read them after `experiment.started` binds the
hypothesis and manifest. If the Owner has already seen outcome-bearing bytes, the confirmatory path
refuses: exploration is labelled exploratory and any test needs a new, unseen holdout or later data
version. [asserted]

1. **Discover.** Record the catalogue, exact query, returned candidate identifiers, selection rule,
   retrieval date and rejected near misses. A model-recalled URL is a candidate, not provenance.
2. **Identify.** Prefer a DOI or publisher version identifier. Record both the immutable version URI
   and any moving series/latest URI. [cited: S6, S8]
3. **Licence.** Fetch the human- or machine-readable licence before the data. Record its canonical
   identifier, URL, retrieval date, SHA-256 and obligations. No licence, an ambiguous/custom licence,
   non-commercial-only terms, click-through terms, or a required account/key refuses. Public reach is
   not permission. [cited: S6, S9]
4. **Register.** Append the complete hypothesis from the metadata-only packet. Direct URL, cache and
   content-file reads remain unavailable to the Owner. [asserted]
5. **Safety-admit.** Permit HTTPS only; re-check every redirect; refuse loopback, link-local, private
   network and non-HTTP schemes; cap response bytes, time, member count and expanded archive bytes;
   treat files as inert data; and refuse macros/executables. Public personal or sensitive data still
   requires a separate lawful/ethical authority and otherwise refuses. [asserted]
6. **Retrieve and seal once.** A bounded acquisition process records the canonical request, response
   status, content type, byte count, `ETag`/`Last-Modified` when supplied, retrieval time and SHA-256,
   then exposes only the receipt. No cookies, credentials or ambient provider tokens enter the
   process. [asserted]
7. **Pin.** Store the exact unread bytes under an instance-private content-addressed object keyed by SHA-256.
   A release is pinned by DOI/version plus bytes; Git data by commit plus archive bytes; an API by the
   canonical request plus raw response bytes. `latest`, an `ETag`, or a Git branch is never a pin.
   [asserted]
8. **Start and open.** `experiment.started` resolves the earlier hypothesis and sealed manifest; the
   isolated runner becomes the only admitted content read path. [asserted]
9. **Transform.** Every derived dataset names ordered parent hashes, transform source and environment
   hashes, parameters, row/column counts before and after, and an output hash. A spreadsheet formula,
   manual edit or model-written cleaning step without a retained executable transform refuses a
   measured claim. [asserted]
10. **Cite.** Emit creator, title, publisher, publication year, resource type, version, persistent
   identifier, rights, retrieval date, content hash and transform lineage. These fields are a narrow
   JSON projection of DataCite plus W3C PROV Entity/Activity/Agent relations, not a new ontology.
   [cited: S7, S8]

### 4.2 Dataset manifest

One canonical manifest contains: [asserted]

- `dataset_id`, title, creators, publisher, publication year and resource type;
- catalogue/query/selection rule and rejected candidate identifiers;
- landing URI, content URI, series URI, version URI, DOI or Git commit;
- source and licence retrieval timestamps;
- licence identifier, URL, text digest, redistribution flag and obligations;
- canonical request, response metadata, media type, compressed/expanded byte counts;
- content SHA-256 and each archive member's relative path, byte count and SHA-256;
- private cache object reference, never raw bytes in the trajectory;
- ordered transforms with input, code, environment, parameter and output hashes;
- citation text and DataCite-compatible fields; and
- availability status: `pinned_cache`, `source_verified`, `source_unavailable`, `hash_mismatch` or
  `licence_unavailable`, with a reason for every non-success state.

The manifest is the `knowledge.retrieved` extension and result input, not a parallel record. The
existing field error is corrected by making `source_url` the dataset/catalogue source and adding a
separate `licence_url`; data licences use an open-data allowlist rather than the current software
licence set. [measured] [asserted]

Raw data remains gitignored instance data unless its licence explicitly permits redistribution and a
separate publication decision includes it. A tracked experiment carries the manifest, transform,
result and citation; private cached bytes and any source whose redistribution term is not satisfied
do not enter Git. [asserted]

### 4.3 Disappearance and expiry

Re-run behaviour is mechanical: [asserted]

- If the exact cached object exists and its hash matches, run from it and report `pinned_cache`; the
  source's current availability is separately checked and reported.
- If the source supplies different bytes, stop with `hash_mismatch`. The replacement is a new dataset
  version and requires a new manifest and, after any outcome is visible, a new experiment epoch.
- If the source is unavailable but the exact cache exists, the historic computation is reproducible
  locally but cannot establish that the source remains current. Any freshness-dependent decision
  expires.
- If neither source nor exact cache exists, the run is `source_unavailable`; the old result remains a
  historical observation but expires as support for a current decision.
- A missing or changed licence refuses even when bytes remain cached. Continued possession is not
  continued permission to reuse or redistribute.

There is no transparent mirror substitution and no fetch of `latest`. A replacement source can be
proposed only as a new, explicitly related Entity with its own licence, hash and comparison. W3C's
version/series distinction is the precedent: a moving series URI is discoverable, while a decision
binds to a version. [cited: S6, S7]

## 5. Hypothesis is a first-class record

### 5.1 Required fields

A hypothesis record is complete only when it contains: [asserted]

- UUID, version and the decision it can change, including the reversal if falsified;
- plain-language claim, null and alternative, direction where directional;
- population, unit of analysis, independent/dependent variables and estimand;
- dataset discovery/selection rule, inclusion/exclusion, missingness and outlier rules;
- transformations, test/model/solver, statistic or objective, effect measure and uncertainty method;
- decision threshold, alpha where used, multiplicity rule and largest plausible effect;
- sample or task count, fixed seed/bit generator, repeat count and wall-clock/compute ceiling;
- numerical tolerances, convergence/diagnostic checks and invalid-run conditions;
- parameter ranges and structurally different sensitivity models fixed before outcome access;
- stopping rule, loss/win/inconclusive outcomes and treatment of timeout, refusal and missing data;
- known conflicts, source/licence manifest identities and analysis-environment lock digest; and
- accountable Owner, principal-only decisions excluded from delegation, creation time and superseded
  record when applicable.

### 5.2 Ordering and anti-edit mechanism

Implementation adds `hypothesis.registered` and `experiment.started` event contracts to the existing
atomic event-reference boundary. `hypothesis.registered` carries canonical JSON and its SHA-256 and
must precede any outcome-body request or cache/content-file open. A bounded acquisition process seals
the retrieved bytes and exposes only their manifest; `experiment.started` must then resolve the exact
earlier hypothesis event ID, kind and digest plus the sealed dataset digest before the isolated runner
becomes the only admitted content reader. The result resolves both start and hypothesis references and
the dataset, code and environment digests. [measured: the existing event writer already supplies
UUID event IDs, atomic compare-and-append, non-replaceable transition validators, duplicate-ID
refusal and exact earlier-reference resolution in `../../../src/consilient/events.py`] [asserted]

An edit never replaces a record. Before a run starts, an amendment appends a new version with a
reason and supersedes the old digest. After a run starts or any outcome is visible, a changed method,
threshold, dataset version, timeout rule or sensitivity range is a new experiment; the original run
stays assigned and adverse/inconclusive under its frozen rule. Registered repository experiments must
also have their five fields and largest plausible effect in the authoritative experiment register
before `experiment.started` is accepted. [asserted]

This prevents ordinary outcome-aware editing inside the protocol; it does not claim that a hostile
process running as the same OS user cannot rewrite local storage. Existing trajectory integrity and
tamper controls remain the outer boundary, and the result must say when that boundary was not proved.
[asserted]

## 6. Simulation gate and assumption-determined refusal

### 6.1 When modelling is warranted

T0 reasoning or T1 retrieved evidence wins unless the live Inquiry trigger passes:
`(G1 OR G2) AND G3 AND G4`, and expected regret of error exceeds inquiry cost. G4 requires all of:
[measured: `../../20-design/inquiry-tier.md:24-77`] [asserted]

- a decision variable `d`;
- an objective or ordering `J(d, q)`; and
- one unanchored free parameter `q`.

If any is missing, the scientific Owner refuses a simulation and returns the best T0/T1 answer with
its evidence tag. Naming, copy, a reversible local layout and questions whose uncertainty cannot
change an action do not get a model. A real dataset can warrant T3 measurement without making T2
simulation useful. [asserted]

Whether the plausible range of `q` can change the selected action is a separate cheap screen, not
part of G4. If it cannot, uncertainty in `q` creates no decision regret within the frozen model and
the expected-regret/cost stop keeps the task at T0/T1. [algebra] [asserted]

If the proposed decision needs more than one unanchored free parameter, G4 does not pass: narrow the
question with measured/retrieved bounds or go to T1/T3. A multidimensional sweep must not smuggle an
underidentified question through the one-parameter gate. [measured: `../../20-design/inquiry-tier.md:57-59`]
[asserted]

### 6.2 Two sensitivities, fixed before the run

Every trusted simulated threshold requires both: [asserted]

1. **Parameter sensitivity:** sweep the pre-registered ranges, seeds, correlations and numerical
   tolerances within one model; report the sign, threshold and regimes, including non-convergence.
2. **Structural sensitivity:** run at least two materially different, cited or empirically plausible
   functional forms for every load-bearing assumption: distribution family, link/response shape,
   dependence structure or dynamics. Changing coefficients inside the same equation is not structural
   sensitivity.

The pre-registration fixes a source-anchored inventory of plausible structures, the exclusion and
evidence for each rejected form, and the tolerance for a material threshold shift. Before outcome
access, a blinded structural challenger checks that inventory against independently retrieved domain
sources; every proposed rival must cite a source or measured failure mode rather than add model
opinion. An unrecorded serious rival forces a new registration. If the serious model set cannot be
bounded, return `structurally_unbounded` and refuse the action-level conclusion. A sensitivity chosen
after seeing a result is another experiment. Two simulations over the same data are robustness checks,
not different classes of facts and not consilience. [asserted]

For each pre-admitted structure `m`, sweep the complete range of `q` and retain every sign-changing
threshold `tau_m`; a non-monotone structure reports all regimes rather than one root. The threshold
envelope is `[inf(tau_m), sup(tau_m)]`. With no measured uncertainty interval for `q`, that envelope
and its regimes are the entire result. With one, a decision is admitted only where every plausible
structure has the same sign throughout that interval. [algebra] [asserted]

### 6.3 Refusal

The result is `assumption_determined` when any pre-admitted plausible structural form reverses the
sign or selected action, removes the threshold, or moves it beyond the pre-registered material
tolerance. It then reports which assumption caused the reversal, the identified range and the
measurement that could discriminate between forms; it refuses a decision claim and never averages
the models into false precision. A model that obtains its conclusion only because its author chose
that functional form has measured its assumptions. [asserted]

Even a stable simulation reports **sign, threshold and regime**, tagged `[simulated]`; it never says
what a world parameter is. A world-number requires T3 measurement against pinned real data, with the
sampling frame and limits stated. Numerical convergence, a second algorithm or symbolic cross-check
can validate computation but cannot validate the assumed world model. [measured: working principle 2;
`../../20-design/inquiry-tier.md:9-22`] [asserted]

## 7. What execution buys, honestly

| Question | Strong-model reasoning is normally sufficient | Execution is genuinely required |
|---|---|---|
| Method choice | State hypotheses, identify assumptions, choose a standard test/solver, derive simple algebra, criticise causal scope | Prove the actual bytes meet those assumptions and run diagnostics |
| Mathematics | Explain a proof strategy or derive a short closed form whose steps can be inspected | Symbolically simplify/solve a large expression, check identities and boundary cases, or numerically solve when no closed form is available |
| Statistics | Explain what a p-value, interval or effect means and when a test is inappropriate | Parse the observations; compute statistics, resamples, exact tests, intervals and multiplicity-adjusted decisions |
| Data | Suggest likely sources and cleaning risks | Retrieve licence/source metadata, hash bytes, inspect schema/missingness and execute every transform |
| Optimisation | Formulate variables, constraints and objective | Solve, check feasibility/convergence, compare starts/algorithms and locate sensitivity thresholds |
| Simulation | Decide whether a simulation can identify the question | Run seeded sweeps and structural countermodels; expose sign flips and non-convergence |
| Reporting | Explain limitations and cite a method | Bind every reported number to producing data/code/environment artefacts |

For many questions, T0/T1 is cheaper and better. Execution adds no truth merely by running: a wrong
test, biased dataset, data leak, coding error or assumption-determined simulation can produce precise
nonsense. The hypothesis, provenance, diagnostics, structural sensitivity and independent verifier
are therefore the capability; the Python process is only the instrument. [asserted]

## 8. EXP-137: execution, generic tools and the proposed profile

EXP-137 is pre-registered in `../../10-research/experiment-register.md`. Its three arms distinguish
two questions the brief otherwise conflates: [asserted]

- `R` asks whether reasoning without execution is enough.
- `G` gives the same Owner ordinary generic code execution, the same pinned environment and open
  data, but not this scientific contract.
- `S` gives the same surface plus the proposed hypothesis/provenance/sensitivity profile.

Every task is sealed before any arm runs; the bank is not selected by first finding failures in `R`.
All tasks remain intent-to-treat. The report counts both rescues (`R` wrong, execution correct) and
harms (`R` correct, execution wrong), and separately compares `S` with `G`. A positive `S` versus `R`
with no `S` versus `G` benefit proves execution helps but does not prove a native laboratory is
needed. [asserted]

The ADR survives in full only if execution materially beats reasoning and the scientific profile
materially beats generic execution under the register's frozen rule. If generic execution beats
reasoning but matches the profile, a successor keeps the locked environment and open-data receipts
but removes the bespoke profile. If execution does not beat reasoning, the capability contracts to
careful T0/T1 reasoning and citations. [asserted]

## 9. Requirements owed by implementation

No prospective boundary below is claimed implemented. Each build increment must ship its own smallest
executable check in the same commit; specification prose is not enforcement. [measured] [asserted]

| Requirement | Check that must accompany its implementation |
|---|---|
| Product AST lock | Existing package-wide third-party-import test remains green; runner packages never enter product metadata. |
| Exact environment | Clean-machine fixture builds only from the lock, checks wheel hashes/platform and refuses ambient or mismatched imports. |
| One orchestrator | Source ratchet proves dispatch/work-item/coordination/budget/event ownership; no second queue, writer or router. |
| Open/no-key acquisition | Fixtures refuse missing/custom licences, credentials, metered endpoints, private/loopback redirects, hash drift, oversize/archive bombs and ambiguous redistribution. |
| Dataset provenance | Round-trip manifest check resolves source/licence/version/content/transform/citation identities; unavailable source without exact cache expires. |
| Hypothesis ordering | Direct URL, cache and content-file reads before hypothesis/start refuse; result/start events cannot reference a missing, later, wrong-kind or wrong-digest hypothesis; amendment after start creates a new epoch. |
| Simulation refusal | Frozen fixtures include one parameter-stable but structure-flipping case and one source-anchored omitted-form attack; the runner returns `assumption_determined` or `structurally_unbounded` and emits no trusted threshold. |
| Independent verification | A blinded second agent must execute the sealed artefact without the first write-up and re-derive the decision; missing or disagreeing receipts refuse decision-grade status. |
| Evidence labelling | Schema rejects a simulated world-number, a measured claim without producing artefacts and an unavailable value represented as zero. |
| Authority | Fixtures prove the Owner cannot author principal verdicts, approvals, gate lifts, spend or publication. |
| Experiment | EXP-137 runner, sealed bank, raw arm outputs and result artefact produce every reported figure. |

No new CLI subcommand is added. Operator use stays through `scripts/dispatch.py`; direct developer
reproduction runs the retained analysis artefact in its isolated environment. No network is allowed
during analysis after acquisition closes, and no source requiring an account, cookie, token or key is
eligible for this capability. [asserted]

## 10. Evidence against: this may be a laboratory nobody needed

The strongest case is that this is over-engineering. Frontier products already run Python and expose
code for review; the mature scientific stack already solves the operations. Data acquisition is
mostly brittle plumbing around URLs, changing schemas, licences and formats. Every manifest field,
lock refresh and source adapter becomes maintenance that can fail before a competent model answers a
question it could have answered correctly from reasoning and citations. [cited: S1-S5] [asserted]

The scientific profile can also make error more authoritative. Pre-registration freezes a bad plan as
readily as a good one; a p-value does not repair selection bias; a symbolic answer may omit a branch;
an optimiser can converge to the wrong objective; structural sensitivity can become ritual choices
of two similarly wrong models. Domain expertise and causal identification are not installed with
SciPy. [asserted]

The cost is concrete: eight new pinned artefacts, 66,334,930 compressed bytes on the reference
platform, a much larger installed footprint, native-wheel security/compatibility upkeep, open-data
licence review, cache expiry and additional run/review time. Generic harnesses already execute code,
and the earlier internal design explicitly called that table stakes. [measured]

The honest alternative is a short skill: reason carefully, retrieve and cite the source, use ordinary
generic Python only when a calculation is necessary, retain the script, and stop. That is the control
arm in EXP-137, not a straw man. This design concedes if it matches the proposed profile on decision
quality and reproducibility, or if the profile's maintenance/review cost erases its accepted-outcome
gain. [asserted]

Why proceed provisionally: the Inquiry gate keeps most questions out; the runner adopts rather than
reimplements numerical work; existing dispatch/retrieval/event paths own the lifecycle; provenance
and pre-registration address failures that a notebook alone does not prevent; and EXP-137 can delete
the extra machinery before it becomes a product dependency. [asserted]

## 11. Search log and source register

Searches on 23 August 2026 used official/primary documentation only: SciPy statistics/numerical/
optimisation; NumPy arrays and simulation; SymPy symbolic features; pandas tabular cleaning; OpenAI
Data Analysis/code execution; W3C PROV and Data on the Web Best Practices; DataCite 4.7; Open
Definition licences; and PyPI release metadata for the exact Windows/Python closure. [measured]

Near misses: Polars was retrieved and rejected from the floor because pandas is the incumbent surface
used by the named frontier execution product and produced the smaller measured reference download;
`statsmodels`, PyMC, scikit-learn, CVXPY and xarray add domain-specific breadth not required by the six
requested operations; Jupyter adds a second interactive surface; `requests`/Pooch duplicate the
stdlib retrieval primitives; hosted code interpreters require an account and do not satisfy the
local/no-credential boundary. These are rejection reasons, not claims that the projects are inferior.
[cited: S1, S3, S5] [measured] [asserted]

- **S1 `[FULL]`** OpenAI, [Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-code-interpreter),
  fetched and read 23 August 2026. Runs Python in a stateful Jupyter environment; supports
  transformations, calculations and statistical analysis; tells users to review code, outputs and
  assumptions.
- **S2 `[FULL]`** NumPy, [NumPy 2.5 documentation](https://numpy.org/doc/stable/) and
  [random sampling](https://numpy.org/doc/stable/reference/random/), fetched and read 23 August
  2026. Arrays, numerical operations and seeded simulation.
- **S3 `[FULL]`** SciPy, [SciPy 1.18.1](https://scipy.org/),
  [`scipy.stats`](https://docs.scipy.org/doc/scipy/reference/stats.html) and
  [`scipy.optimize`](https://docs.scipy.org/doc/scipy/reference/optimize.html), fetched and read
  23 August 2026. Numerical algorithms, tests and optimisation; BSD licence.
- **S4 `[FULL]`** SymPy, [features](https://docs.sympy.org/latest/tutorials/intro-tutorial/features.html)
  and [project page](https://www.sympy.org/en/index.html), fetched and read 23 August 2026. Symbolic
  algebra/calculus/solvers; BSD licence; one required dependency, mpmath.
- **S5 `[FULL]`** pandas, [overview](https://pandas.pydata.org/pandas-docs/stable/getting_started/overview.html),
  [user guide](https://pandas.pydata.org/docs/user_guide/index.html) and
  [tagged licence](https://github.com/pandas-dev/pandas/blob/v3.0.5/LICENSE), fetched and read
  23 August 2026. Tabular data structures, missing data, joins, grouping, I/O and time series.
- **S6 `[FULL]`** W3C, [Data on the Web Best Practices](https://www.w3.org/TR/dwbp/), Recommendation,
  fetched and read 23 August 2026. Licence, provenance, version/series identifiers and preservation.
- **S7 `[FULL]`** W3C, [PROV-O](https://www.w3.org/TR/prov-o/), Recommendation 30 April 2013,
  fetched and read 23 August 2026. Entity, Activity, Agent and derivation relations; also recorded in
  `../../10-research/bibliography.md`.
- **S8 `[FULL]`** DataCite Metadata Working Group, *DataCite Metadata Schema 4.7*,
  documentation DOI [10.14454/qdd3-ps68](https://doi.org/10.14454/qdd3-ps68), released 3 March 2026,
  fetched and read 23 August 2026. Citation properties including identifier, creator, title,
  publisher, year, type, version and rights.
- **S9 `[FULL]`** Open Knowledge Foundation,
  [Open Definition conformant licences](https://opendefinition.org/licenses/), fetched and read
  23 August 2026. Machine-readable open-data licence catalogue; admission still records and follows
  the source's actual terms.

## 12. What would overturn the design

EXP-137 overturns the full profile under the rule in the register. Independently, any of these forces
a successor ADR: the locked environment cannot be reproduced from its hashes; the acquisition path
admits a credential, missing licence or changed bytes; a result binds to a hypothesis written after
start; assumption-determined fixtures emit a trusted threshold; or maintenance plus blinded review
time per jointly accepted outcome is no better than generic execution across the frozen bank.
[asserted]

No outcome authorises spend, publication, automatic routing, extra candidate exposure, a gate lift or
operation in another repository. Those remain the principal's decisions and the existing gates'
authority. [asserted]
