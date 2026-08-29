"""The public surface of the harness family — policy, not process.

Process execution does not live anywhere in this package: src/consilient/ is AST-locked
against subprocess, sockets and credentials, and scripts/dispatch.py is the runner. This
module now holds no logic at all. It re-exports the fifty-eight names that thirty files
across src/, tests/ and scripts/ take from this path, so that splitting the
implementation into seven subject modules costs no importer a line.

The file keeps its name and its history deliberately. Import from it and the seam is
invisible; import from a sibling and you have said which half of the subject you meant.

Every name below is re-exported, never redefined, and __all__ is explicit because mypy
runs with strict = True and therefore no_implicit_reexport. A name absent from __all__
is not importable from here, which is the intended way to add one: put it in its subject
module, then add it here on purpose.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    Policy lives here. Process execution does not: `src/consilient/` is AST-locked against
    `subprocess`, sockets and credentials. `scripts/dispatch.py` is the runner.

    Selection prefers the pool with the most remaining headroom and never silently spends an
    exhausted pool. Refusing with a reason is the success path when the scarce resource is
    the only thing left.
"""

from .harness_registry import (
    Harness,
)

from .harness_grammar import (
    GrammarConstraint,
    UNCONSTRAINED_SCHEMA_KEY,
    derive_grammar_constraint,
    grammar_accepts,
    schema_digest,
)

from .harness_headroom import (
    EXHAUSTED_USED_PERCENT,
    headroom_freshness_refusal,
    load_pools,
    pools_from_mapping,
    remaining_percent,
    snapshot_mapping,
)

from .harness_models import (
    MODELS,
    ModelOption,
    ReasoningCapability,
    UNMAPPED_REASONING_PROVENANCE,
    allows_reasoning_scaffold,
    cursor_models_pool_ids,
    cursor_pool_for_model,
    model_family,
    models_for_harness,
    parse_list_models,
    pool_for_model,
    registry_drift,
)

from .harness_recording import (
    DISPATCH_OUTCOME_KIND,
    classify_artefact,
    classify_gap,
    judge_fanout,
    make_run_id,
    now_ts,
    parse_status,
    record_fanout,
    record_gap,
    record_outcome,
    record_refusal,
)

from .harness_registry import (
    DEFAULT_PERMISSION_MODE,
    DEFAULT_POOLS,
    DISPATCH_ACTOR,
    Decision,
    FanoutDecision,
    HARNESSES,
    PermissionMode,
    PoolState,
    Probe,
    harness_by_id,
    load_permission_mode,
    permission_flags,
)

from .harness_requests import (
    REQUEST_RECORD_FIELDS,
    REQUEST_RECORD_KIND,
    RequestTiming,
    build_request_timing,
    extract_usage_from_output,
    record_request,
    validate_request_record,
)

from .harness_selection import (
    describe_registry,
    select,
    select_fanout,
    select_model,
)

__all__ = [
    "DEFAULT_PERMISSION_MODE",
    "DEFAULT_POOLS",
    "DISPATCH_ACTOR",
    "DISPATCH_OUTCOME_KIND",
    "Decision",
    "EXHAUSTED_USED_PERCENT",
    "FanoutDecision",
    "GrammarConstraint",
    "HARNESSES",
    "Harness",
    "MODELS",
    "ModelOption",
    "PermissionMode",
    "PoolState",
    "Probe",
    "REQUEST_RECORD_FIELDS",
    "REQUEST_RECORD_KIND",
    "ReasoningCapability",
    "RequestTiming",
    "UNCONSTRAINED_SCHEMA_KEY",
    "UNMAPPED_REASONING_PROVENANCE",
    "allows_reasoning_scaffold",
    "build_request_timing",
    "classify_artefact",
    "classify_gap",
    "cursor_models_pool_ids",
    "cursor_pool_for_model",
    "derive_grammar_constraint",
    "describe_registry",
    "extract_usage_from_output",
    "grammar_accepts",
    "harness_by_id",
    "headroom_freshness_refusal",
    "judge_fanout",
    "load_permission_mode",
    "load_pools",
    "make_run_id",
    "model_family",
    "models_for_harness",
    "now_ts",
    "parse_list_models",
    "parse_status",
    "permission_flags",
    "pool_for_model",
    "pools_from_mapping",
    "record_fanout",
    "record_gap",
    "record_outcome",
    "record_refusal",
    "record_request",
    "registry_drift",
    "remaining_percent",
    "schema_digest",
    "select",
    "select_fanout",
    "select_model",
    "snapshot_mapping",
    "validate_request_record",
]
