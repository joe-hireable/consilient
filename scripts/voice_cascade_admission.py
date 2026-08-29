"""The cascade's declared stages, its intent vocabulary and every refusal it can raise.

Nothing here composes a turn or prints a report; this file holds the tables the cascade
consults and the predicates that stop it, drawn from
`docs/20-design/observability-steering-and-embodiment-2026-08-23.md` and
`docs/20-design/supervision-escalation-and-sessions-2026-08-23.md`. `CASCADE` names the
four stage models with the licences and declared weights those documents state,
`INTENTS` names the phrases the cascade will act on and the capability each would reach,
and `Backends` is the injected protocol the stage models arrive through — no default
exists, because a cascade with no models refuses, and a refusal is a truthful outcome
where a fabricated transcript is not. Sizes are the design document's own figures, in
decimal bytes as it states them. They are declared weights, not resident footprints, and
this module never calls them measured.

The refusals are the load-bearing half. `telephony_refusals` stops any sink,
configuration or route naming a provider; `adoption_refusals` stops a stage that is
unrecorded, recorded as refused, or copyleft, reading the record through
`load_components`, which adopts nothing when the record cannot be read. The
principal-authority and reversibility decisions are taken against the `Intent` flags set
here. `spoken` hedges a claim whose evidence class has not been checked before it is
voiced, `truncate_to_played` cuts an assistant turn back to what the human actually
heard on barge-in, and `_readback` draws its confirmation token from the parsed action
rather than asking for a bare yes. `nvidia_used_bytes` and `measured_footprint` refuse
an absolute GPU reading as evidence of a footprint and will decide the 2 GB criterion
only from a before/after delta around a real load.

* **No telephony.** ADR-0102 keeps a dialler out of the public tree. A provider token may
  appear in this file only inside `TELEPHONY_TOKENS`, which is the rule stating the
  prohibition, and a sink naming one stops the turn before a transcript exists.
* **No unadopted component runs.** All four models are cited in the design and recorded
  in neither `docs/legal/adopted-components.json` nor `docs/decisions/adopted-deps.json`,
  so live execution is refused today. Parakeet's CC-BY-4.0 needs a recorded decision, and
  a copyleft stage is refused outright — `piper1-gpl` is the case the design names.
* **Voice proposes; the click commits.** A human review stage cut dictation errors from
  7.4 per 100 words to 0.3% in production [cited, Zhou et al., JAMA Netw Open 2018].
  Nothing here executes, and a principal-authority utterance — approval, verdict, gate
  lift, spend — is refused at any reversibility class under V0-18.

Every `[cited]` reference in this module is second-hand: it is quoted from the two
design documents named above, which retrieved it. None of the underlying papers was read
here.

Nothing is persisted. Inbound speech is personal data of people who never consented, so
no function here writes a transcript anywhere; `events.py` remains the sole writer and
this module is not one of its callers."""

from __future__ import annotations
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Protocol, Sequence

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

COMPONENT_RECORD = ROOT / "docs" / "legal" / "adopted-components.json"

# The unit's own criterion: "under 2 GB resident" for the cascade, leaving the rest of
# the card for the model that thinks. [cited] embodiment design, voice section.
BUDGET_BYTES = 2 * 1024**3

# The provider and protocol tokens below are the rule stating ADR-0102's prohibition.
# This literal is the only place in this module where one may be named, and
# `test_the_module_names_no_telephony_provider_outside_its_own_prohibition` fails if one
# appears anywhere else — the same shape as the private-repository name rule in AGENTS.md.
TELEPHONY_TOKENS: frozenset[str] = frozenset(
    {
        "twilio",
        "vonage",
        "plivo",
        "telnyx",
        "sinch",
        "signalwire",
        "pstn",
        "sip:",
        "sip trunk",
        "10dlc",
    }
)

# Share-alike and reciprocal licences the project will not carry. `piper1-gpl` is the
# case the design names; the existing component check denies "AGPL" by substring and so
# does not catch a bare "GPL-3.0", which is why this list exists here as well.
COPYLEFT_TOKENS: tuple[str, ...] = ("agpl", "gpl", "sspl", "cc-by-sa", "osl")

# Only a claim whose evidence has been checked may be spoken unhedged. Speech cues
# significantly raised perceived accuracy independent of correctness, N=2,165
# [cited, arXiv:2405.06079] — a measured effect this design amplifies on purpose, so the
# evidence tag becomes the spoken hedge.
SPEAKABLE_UNHEDGED: frozenset[str] = frozenset({"measured", "cited"})


@dataclass(frozen=True)
class Stage:
    """One cascade stage: what runs, under what licence, and how big it is declared to be."""

    role: str
    component: str
    licence: str
    declared_weight_bytes: int
    evidence: str


# Sizes are the design document's own figures, in decimal bytes as it states them. They
# are declared weights, not resident footprints, and this module never calls them measured.
CASCADE: tuple[Stage, ...] = (
    Stage(
        role="vad",
        component="snakers4/silero-vad",
        licence="MIT",
        declared_weight_bytes=2_000_000,
        evidence="[cited] embodiment design, voice section: MIT, 2 MB",
    ),
    Stage(
        role="endpoint",
        component="pipecat-ai/smart-turn",
        licence="BSD-2-Clause",
        declared_weight_bytes=8_000_000,
        evidence="[cited] embodiment design, voice section: BSD-2, 8 MB, ~10 ms CPU",
    ),
    Stage(
        role="asr",
        component="nvidia/parakeet-tdt-0.6b",
        licence="CC-BY-4.0",
        declared_weight_bytes=1_200_000_000,
        evidence="[cited] embodiment design, voice section: CC-BY-4.0, ~1.2 GB",
    ),
    Stage(
        role="tts",
        component="hexgrad/kokoro-82m",
        licence="Apache-2.0",
        declared_weight_bytes=400_000_000,
        evidence="[cited] embodiment design, voice section: Apache-2.0, ~0.4 GB",
    ),
)


@dataclass(frozen=True)
class Intent:
    """A phrase the cascade will act on, bound to the capability it would reach.

    `principal_authority` marks the V0-18 classes — approval, consent, verdict, gate lift,
    spend. They are refused whatever their reversibility class, because the objection is
    who authored the decision, not how hard it is to undo.
    """

    name: str
    trigger: str
    kind: str
    tool: str
    effect_classes: tuple[str, ...]
    principal_authority: bool = False


INTENTS: tuple[Intent, ...] = (
    Intent("read_file", "read the file", "tool", "read", ("data.read",)),
    Intent("run_tests", "run the tests", "tool", "bash", ("process.run",)),
    Intent("search_web", "search the web", "tool", "websearch", ()),
    Intent(
        "approve_dispatch",
        "approve the dispatch",
        "tool",
        "read",
        ("data.read",),
        principal_authority=True,
    ),
)


class Backends(Protocol):
    """The four stage models, injected. No default exists: a cascade with no models
    refuses, and a refusal is a truthful outcome where a fabricated transcript is not."""

    def speech(self, frames: bytes) -> bool: ...

    def endpointed(self, frames: bytes) -> bool: ...

    def transcribe(self, frames: bytes) -> str: ...


# --- the budget ---------------------------------------------------------------------


def projected_weight_bytes(stages: Sequence[Stage] = CASCADE) -> int:
    """Declared weights only — the marginal cost of the cascade on a card whose driver
    context is already resident because something else is running on it."""
    return sum(stage.declared_weight_bytes for stage in stages)


def nvidia_used_bytes() -> int | None:
    """GPU memory currently in use, or None when it cannot be read.

    Verified by artefact: the number is parsed, and an exit code alone is never taken as
    a reading. Text mode carries an explicit encoding because the Windows default is
    cp1252 and crashes on ordinary tool output.
    """
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines or not lines[0].isdigit():
        return None
    return int(lines[0]) * 1024 * 1024


def measured_footprint(before: int | None, after: int | None) -> dict[str, object]:
    """Decide the 2 GB criterion from a before/after delta around a cascade load.

    An absolute reading is refused as evidence. `local-model-fit-arithmetic.md` § 7 says
    of its own 29,442 MiB figure that it "is not the model's footprint" because a
    concurrent process could not be separated from it; the same objection applies here,
    and a delta is the cheapest way to answer it.
    """
    if before is None or after is None:
        return {
            "evidence": "unmeasured",
            "verdict": "unmeasured",
            "delta_bytes": None,
            "budget_bytes": BUDGET_BYTES,
            "reason": "nvidia-smi did not return a readable memory.used value",
        }
    delta = after - before
    if delta < 0:
        return {
            "evidence": "unmeasured",
            "verdict": "unmeasured",
            "delta_bytes": delta,
            "budget_bytes": BUDGET_BYTES,
            "reason": (
                "GPU memory fell across the load, so another process moved during the "
                "reading and no cascade footprint can be attributed from it"
            ),
        }
    return {
        "evidence": "measured",
        "verdict": "within" if delta <= BUDGET_BYTES else "exceeds",
        "delta_bytes": delta,
        "budget_bytes": BUDGET_BYTES,
        "reason": "nvidia-smi memory.used delta across the cascade load",
    }


# --- the refusals -------------------------------------------------------------------


def telephony_refusals(*texts: str) -> tuple[str, ...]:
    """Refuse any sink, configuration or route naming a telephony provider (ADR-0102)."""
    refusals: list[str] = []
    for text in texts:
        folded = text.casefold()
        for token in sorted(TELEPHONY_TOKENS):
            if token in folded:
                refusals.append(
                    f"ADR-0102: telephony is not in the open-source tree; "
                    f"{token!r} is refused"
                )
    return tuple(refusals)


def _normalise(name: str) -> str:
    return re.sub(r"[-_./]+", "-", name).casefold()


def load_components(path: Path = COMPONENT_RECORD) -> list[dict[str, object]]:
    """Read the adopted-component record. An unreadable record adopts nothing."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    components = payload.get("components") if isinstance(payload, dict) else None
    if not isinstance(components, list):
        return []
    return [entry for entry in components if isinstance(entry, dict)]


def _copyleft(licence: str) -> str | None:
    folded = licence.casefold()
    return next((token for token in COPYLEFT_TOKENS if token in folded), None)


def adoption_refusals(
    stages: Sequence[Stage], record: Sequence[dict[str, object]]
) -> tuple[str, ...]:
    """Refuse a stage that is unrecorded, recorded as refused, or copyleft.

    ADR-0065 makes adoption a recorded decision rather than a default. All four stages
    are unrecorded today, which is the honest reason live execution is refused — not a
    missing download.
    """
    index = {
        _normalise(str(entry.get("name", ""))): entry
        for entry in record
        if isinstance(entry.get("name"), str)
    }
    refusals: list[str] = []
    for stage in stages:
        entry = index.get(_normalise(stage.component))
        licences = [stage.licence]
        if entry is not None:
            licences.append(str(entry.get("licence", "")))
        copyleft = next(
            (token for token in (_copyleft(text) for text in licences) if token), None
        )
        if copyleft is not None:
            refusals.append(
                f"{stage.role}: {stage.component} is copyleft ({copyleft.upper()}); "
                f"the project does not carry it"
            )
            continue
        if entry is None:
            refusals.append(
                f"{stage.role}: {stage.component} is not recorded in "
                f"{COMPONENT_RECORD.name}; ADR-0065 makes adoption a decision, "
                f"not a default"
            )
            continue
        if str(entry.get("status", "")) != "supplied":
            refusals.append(
                f"{stage.role}: {stage.component} is recorded as "
                f"{entry.get('status')!r} and does not run"
            )
    return tuple(refusals)


# --- speech -------------------------------------------------------------------------


def spoken(text: str, evidence: str) -> str:
    """Hedge any claim whose evidence has not been checked, before it is voiced."""
    if evidence.casefold() in SPEAKABLE_UNHEDGED:
        return text
    return f"Unverified — {text}"


def truncate_to_played(generated: str, played_chars: int) -> str:
    """Truncate the assistant turn to what the human actually heard on barge-in.

    A turn record containing sentences they never received is the bug that desynchronises
    the agent's memory from the human's, and it is worst on the actions that matter.
    """
    return generated[: max(0, played_chars)].rstrip()


def _parse(transcript: str, intents: Sequence[Intent]) -> tuple[Intent, str] | None:
    folded = transcript.casefold().strip()
    for intent in intents:
        if folded.startswith(intent.trigger):
            return intent, transcript.strip()[len(intent.trigger) :].strip()
    return None


def _readback(intent: Intent, parameter: str) -> str:
    """Read the parsed action back with a distinguishing token, never a bare yes.

    A bare "say yes" prompt is a yes-bias magnet one ASR error from a wrong action, and
    the adversarial critic of this design showed a *fixed* spoken token is no better —
    an ASR error produces it or fails to. So the token is drawn from the parsed action
    itself, which makes the readback a check on the parse rather than an authorisation.
    """
    token = parameter or intent.name
    return f"Proposed: {intent.name.replace('_', ' ')} — {token}. Confirm on screen."


def _outcome(**fields: object) -> dict[str, object]:
    base: dict[str, object] = {
        "outcome": "refused",
        "transcript": None,
        "intent": None,
        "parameter": None,
        "reversibility_class": None,
        "gate": "voice_refused",
        "commit_channel": "non_voice",
        "executed": False,
        "readback": None,
        "speech": "",
        "refusals": (),
    }
    base.update(fields)
    return base
