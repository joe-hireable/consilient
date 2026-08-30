"""Sourcing each layer's content and composing the document the agent is shown.

Skills are selected by the task from `.agents/skills/`, never loaded wholesale.
Selection is deterministic token overlap: no model call, no self-reported confidence.
The matched tokens are recorded with the assembly, so the choice is auditable rather
than trusted. The recall pack is recall.pack_events over the trajectory, verbatim and
bounded (EXP-45 measured condensation dropping ~59%), and the scan window is shrunk
until its honest receipt fits rather than the receipt being dropped to make room.

The adapted layer is projected from the record alone: content counts only when a
recorded, unreversed acceptance vouches for its digest, and a reversal removes that
candidate's layer wherever it sits in the applied stack, so the layer falls back to the
previous promotion rather than to nothing. `render` then composes the four sections in
fixed precedence with the core first, and substitutes the inert notice whenever no
promotion stands.

  V0-46  The adapted layer cannot reach the invariant core.

Nothing here writes. Reading a recorded receipt folds the pre-24-August fat-list shape
forward through the same digest, so events already written keep verifying, and an
envelope is rebuilt from the trajectory and the object store without touching either."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from pathlib import Path
from . import promote, recall
from .events import (
    Event,
    read_all,
)
from .instructions_vocabulary import (
    ACTIVE,
    ADAPTED,
    ADAPTED_HEADER,
    ADAPTED_LAYER_PATH,
    ASSEMBLED,
    AdaptedLayer,
    BETTER_THAN_BEST_FILE,
    CORE_VERSION,
    EnvelopePart,
    INERT_NOTICE,
    INVARIANT_CORE,
    InstructionError,
    RECALL_HEADER,
    RECALL_SCAN_EVENTS,
    SKILLS_HEADER,
    SKILL_CHARS,
    SKILL_LIMIT,
    SkillRef,
    _RECEIPT_FIELDS,
    _frontmatter,
)

from .instructions_admission import (
    EnvelopeReconstruction,
    _INERT_LAYER,
    _bounded_protection,
    _guard_privileged_selection,
    _omitted_digest,
    _part_from_binding,
    _render_core,
    _skill_file,
    _tokens,
    record_adapted,
)


__all__ = [
    "ACTIVE",
    "ADAPTED",
    "ADAPTED_HEADER",
    "ADAPTED_LAYER_PATH",
    "ASSEMBLED",
    "AdaptedLayer",
    "BETTER_THAN_BEST_FILE",
    "CORE_VERSION",
    "EnvelopePart",
    "EnvelopeReconstruction",
    "INERT_NOTICE",
    "INVARIANT_CORE",
    "InstructionError",
    "RECALL_HEADER",
    "RECALL_SCAN_EVENTS",
    "SKILLS_HEADER",
    "SKILL_CHARS",
    "SKILL_LIMIT",
    "SkillRef",
    "_INERT_LAYER",
    "_RECEIPT_FIELDS",
    "_bounded_protection",
    "_frontmatter",
    "_guard_privileged_selection",
    "_omitted_digest",
    "_part_from_binding",
    "_render_core",
    "_skill_file",
    "_tokens",
    "reconstruct_envelope",
    "record_adapted",
    "render",
    "select_skills",
]


def select_skills(
    skills_dir: Path,
    task: str,
    *,
    limit: int = SKILL_LIMIT,
    budget_chars: int = SKILL_CHARS,
) -> tuple[tuple[SkillRef, ...], int]:
    """Deterministic task-relevant selection, never wholesale loading.

    A skill is a candidate when at least two distinctive task tokens appear in its
    declared name or description; candidates rank by matched count, ties by name.
    The returned count is how many candidates the character budget excluded.
    """
    if limit < 0 or budget_chars < 1:
        raise ValueError("limit must be >= 0 and budget_chars >= 1")
    task_tokens = _tokens(task)
    candidates: list[tuple[int, str, SkillRef]] = []
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        body = path.read_text(encoding="utf-8")
        fields = _frontmatter(body)
        name = fields.get("name") or path.parent.name
        haystack = _tokens(f"{name} {fields.get('description', '')}")
        matched = tuple(sorted(task_tokens & haystack))
        if len(matched) < 2:
            continue
        relative = path.parent.name
        ref = SkillRef(
            name=name,
            path=f"{skills_dir.as_posix().rstrip('/')}/{relative}/SKILL.md",
            sha256=promote.digest(body),
            matched=matched,
            body=body,
        )
        candidates.append((-len(matched), name, ref))
    candidates.sort(key=lambda item: (item[0], item[1]))
    chosen: list[SkillRef] = []
    spent = 0
    omitted = 0
    for _, _, ref in candidates[:limit] if limit else []:
        if spent + len(ref.body) > budget_chars:
            omitted += 1
            continue
        chosen.append(ref)
        spent += len(ref.body)
    omitted += max(0, len(candidates) - (limit if limit else 0))
    return tuple(chosen), omitted


def _load_named_skill(skills_dir: Path, name: str) -> SkillRef:
    path = _skill_file(skills_dir, name)
    if not path.is_file():
        raise InstructionError(f"the {name} skill is missing from {path.as_posix()}")
    body = path.read_text(encoding="utf-8")
    fields = _frontmatter(body)
    recorded_name = fields.get("name") or path.parent.name
    if recorded_name != name:
        raise InstructionError(
            f"skill at {path.as_posix()} declares name {recorded_name!r}, not {name!r}"
        )
    return SkillRef(
        name=recorded_name,
        path=f"{skills_dir.as_posix().rstrip('/')}/{name}/{BETTER_THAN_BEST_FILE}",
        sha256=promote.digest(body),
        matched=(),
        body=body,
    )


def render(
    skills: Sequence[SkillRef],
    recall_pack: str,
    adapted: AdaptedLayer,
    *,
    core_version: int = CORE_VERSION,
    skills_omitted: int = 0,
) -> str:
    """Compose the document. The core section is built from INVARIANT_CORE only —
    it is the first thing in the text and no parameter of this function can reach it
    (V0-46)."""
    parts = [_render_core(core_version)]
    note = (
        f" ({skills_omitted} further matched skill(s) omitted by the budget)"
        if skills_omitted
        else ""
    )
    parts.append(f"\n{SKILLS_HEADER}{note}\n")
    for skill in skills:
        parts.append(f"\n## {skill.name}\n\n{skill.body.rstrip()}\n")
    parts.append(f"\n{RECALL_HEADER}\n\n{recall_pack.rstrip()}\n")
    adapted_text = adapted.text if adapted.status == ACTIVE else INERT_NOTICE
    parts.append(f"\n{ADAPTED_HEADER}\n\n{adapted_text.rstrip()}\n")
    return "".join(parts)


def _recorded_selection_receipt(recall_data: Mapping[str, object]) -> dict[str, object]:
    """Read a recorded receipt in the current shape OR the pre-24-August fat-list shape.

    Events already written carry the full `omitted` list and must keep verifying, so an old
    record is folded forward by digesting the list it stored. Both sides then route through
    `_omitted_digest`, which is what preserves the property: a different omission set still
    produces a different digest, whichever shape it was recorded in.

    A digest-era record that also inlines `omitted` is not either of those shapes. The
    extra key is kept so equality with `_selection_receipt` fails, and `reconstruct`
    names the co-resident list rather than treating it as invisible extra.

    A pre-digest record whose `omitted` value is not a list of mappings is also kept
    as an extra key rather than hashed as the empty set. Dropping non-mapping rows
    used to let `omitted: ["garbage"]` verify against a complete selection.
    Key presence, not truthiness, decides the digest-era branch: `omitted_digest: null`
    beside `omitted` is still that co-resident shape, not a legacy list.
    """
    data = {field: recall_data.get(field) for field in _RECEIPT_FIELDS}
    if "omitted" in recall_data:
        if "omitted_digest" in recall_data:
            # Digest-era record that still inlines the list. Reconstruct refuses
            # this shape before comparing; keep the key so a caller that only
            # compares receipts cannot treat the fat list as invisible extra.
            data["omitted"] = recall_data.get("omitted")
        else:
            legacy = recall_data.get("omitted")
            if isinstance(legacy, list) and all(
                isinstance(row, Mapping) for row in legacy
            ):
                data["omitted_count"] = len(legacy)
                data["omitted_digest"] = _omitted_digest(legacy)
            else:
                data["omitted"] = legacy
    return data


def _select_recall(
    events: Sequence[Event], *, query: str, limit_chars: int
) -> recall.Selection:
    """Shrink the scan window until its honest receipt fits, then return its provenance."""
    window = min(len(events), RECALL_SCAN_EVENTS)
    protected = _bounded_protection(events)
    while True:
        candidate = (
            events
            if window >= len(events)
            else [
                event
                for index, event in enumerate(events)
                if index in protected or index >= len(events) - window
            ]
        )
        try:
            return _guard_privileged_selection(
                recall.select_events(
                    candidate,
                    query=query,
                    limit_chars=limit_chars,
                    scan_complete=window >= len(events),
                    shrink_to_receipt=True,
                ),
                candidate,
            )
        except ValueError:
            if window <= 1:
                return _guard_privileged_selection(
                    recall.select_events(
                        candidate,
                        query=query,
                        limit_chars=limit_chars,
                        scan_complete=window >= len(events),
                    ),
                    candidate,
                )
            window = max(1, window // 2)


def _adapted_from_events(events: Sequence[Event]) -> AdaptedLayer:
    """Project the adapted layer from the record. Content counts only when a
    recorded, unreversed acceptance vouches for its digest (V0-48). A reversal
    removes that candidate's layer wherever it sits in the applied stack, so the
    layer falls back to the previous promotion rather than to nothing."""
    accepted: dict[str, str] = {}
    reversed_ids: set[str] = set()
    applied: list[AdaptedLayer] = []
    for event in events:
        data = event.data
        if event.kind == promote.ACCEPTED:
            candidate_id = data.get("candidate_id")
            postimage = data.get("postimage_sha256")
            if (
                data.get("path") == ADAPTED_LAYER_PATH
                and isinstance(candidate_id, str)
                and isinstance(postimage, str)
            ):
                accepted[candidate_id] = postimage
        elif event.kind == promote.REVERSED:
            candidate_id = data.get("candidate_id")
            if isinstance(candidate_id, str):
                reversed_ids.add(candidate_id)
                applied = [
                    layer for layer in applied if layer.candidate_id != candidate_id
                ]
        elif event.kind == ADAPTED:
            candidate_id = data.get("candidate_id")
            text = data.get("text")
            text_digest = data.get("text_sha256")
            if not (
                isinstance(candidate_id, str)
                and isinstance(text, str)
                and isinstance(text_digest, str)
            ):
                continue
            if candidate_id not in accepted or candidate_id in reversed_ids:
                continue
            if (
                accepted[candidate_id] != text_digest
                or promote.digest(text) != text_digest
            ):
                continue
            applied = [layer for layer in applied if layer.candidate_id != candidate_id]
            applied.append(AdaptedLayer(ACTIVE, text, candidate_id))
    return applied[-1] if applied else _INERT_LAYER


def reconstruct_envelope(
    log_dir: Path, workspace_root: Path, run_id: str
) -> EnvelopeReconstruction:
    """Rebuild one dispatch envelope from the trajectory and object store."""
    events, _rejected = read_all(log_dir)
    outcome: Event | None = None
    for event in events:
        if event.kind == "dispatch.outcome" and event.data.get("run_id") == run_id:
            outcome = event
    if outcome is None:
        return EnvelopeReconstruction(
            run_id,
            False,
            (EnvelopePart("outcome", False, None, "no dispatch.outcome for run"),),
        )

    assembly_id = outcome.data.get("assembly_id")
    assembled: Event | None = None
    if isinstance(assembly_id, str):
        for event in events:
            if event.kind == ASSEMBLED and event.data.get("assembly_id") == assembly_id:
                assembled = event

    parts: list[EnvelopePart] = []
    pre_run = assembled.data.get("pre_run_records") if assembled is not None else None
    if not isinstance(pre_run, dict):
        pre_run = {}
    parts.append(_part_from_binding("task", pre_run.get("task"), workspace_root))
    parts.append(
        _part_from_binding("instructions", pre_run.get("instructions"), workspace_root)
    )

    receipt = assembled.data.get("recall_receipt") if assembled is not None else None
    if isinstance(receipt, dict) and receipt.get("status") == "ok":
        digest = receipt.get("digest")
        parts.append(
            EnvelopePart(
                "recall_receipt",
                isinstance(digest, str),
                digest if isinstance(digest, str) else None,
                "bound" if isinstance(digest, str) else "missing digest",
            )
        )
    else:
        reason = receipt.get("reason") if isinstance(receipt, dict) else "missing"
        parts.append(
            EnvelopePart(
                "recall_receipt",
                False,
                None,
                str(reason if isinstance(reason, str) and reason else "missing"),
            )
        )

    manifests = (
        assembled.data.get("capability_manifests") if assembled is not None else None
    )
    if manifests == []:
        parts.append(EnvelopePart("capability_manifests", True, None, "none selected"))
    elif isinstance(manifests, list) and manifests:
        valid = True
        first_digest: str | None = None
        for row in manifests:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("identity"), str)
                or not isinstance(row.get("version_digest"), str)
            ):
                valid = False
                break
            if first_digest is None:
                version = row.get("version_digest")
                first_digest = version if isinstance(version, str) else None
        parts.append(
            EnvelopePart(
                "capability_manifests",
                valid,
                first_digest,
                "bound" if valid else "invalid manifest binding",
            )
        )
    else:
        parts.append(EnvelopePart("capability_manifests", False, None, "missing"))

    outputs = outcome.data.get("output_records")
    if not isinstance(outputs, dict):
        outputs = {}
    for name in ("stdout", "stderr", "artefact_manifest", "verifier_outcome"):
        parts.append(_part_from_binding(name, outputs.get(name), workspace_root))

    listed = outputs.get("listed_artefacts")
    if listed is None or listed == []:
        parts.append(EnvelopePart("listed_artefacts", True, None, "none listed"))
    elif isinstance(listed, list):
        failed: list[str] = []
        for index, row in enumerate(listed):
            part = _part_from_binding(f"listed_artefacts[{index}]", row, workspace_root)
            if not part.ok:
                failed.append(part.detail)
        parts.append(
            EnvelopePart(
                "listed_artefacts",
                not failed,
                None,
                "; ".join(failed) if failed else "matched object bytes",
            )
        )
    else:
        parts.append(
            EnvelopePart(
                "listed_artefacts", False, None, "listed_artefacts is not a list"
            )
        )

    return EnvelopeReconstruction(run_id, all(part.ok for part in parts), tuple(parts))
