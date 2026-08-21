"""Fail-closed harness registry and headroom-first selection policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class DispatchRefused(RuntimeError):
    """No registered harness may receive the task."""


@dataclass(frozen=True)
class Harness:
    name: str
    family: str
    pool: str
    invocation: tuple[str, ...]
    used_percent: int | None
    headroom_state: str
    headroom_source: str

    @property
    def headroom_percent(self) -> int | None:
        return None if self.used_percent is None else 100 - self.used_percent

    @property
    def has_headroom(self) -> bool:
        headroom = self.headroom_percent
        return headroom is not None and headroom > 0


REGISTRY = (
    Harness(
        "claude",
        "anthropic",
        "claude-weekly",
        ("claude", "-p", "{brief}"),
        None,
        "nearly exhausted",
        "principal measurement, 2026-08-21",
    ),
    Harness(
        "cursor-composer",
        "cursor-composer",
        "cursor-models-monthly",
        (
            "wsl",
            "-e",
            "bash",
            "-lc",
            'agent="$HOME/.local/bin/cursor-agent"; clean=(env -i '
            '"HOME=$HOME" "PATH=$PATH" "USER=${USER-}" "LOGNAME=${LOGNAME-}" '
            '"LANG=${LANG-}" "LC_ALL=${LC_ALL-}" "TERM=${TERM-}" '
            '"GIT_DIR=$3" "GIT_WORK_TREE=$1"); '
            'top=$("${clean[@]}" git rev-parse --show-toplevel 2>/dev/null) || '
            '{ echo "Workspace binding failed" >&2; exit 70; }; '
            '[[ "$top" == "$1" ]] || '
            '{ echo "Workspace binding mismatch" >&2; exit 70; }; '
            'trust=(); help=$("${clean[@]}" "$agent" --help 2>&1); '
            'if [[ "$help" == *--trust* ]]; then trust=(--trust); fi; '
            'cd -- "$1" && exec "${clean[@]}" "$agent" -p '
            '--model composer-2.5 --output-format text "${trust[@]}" "$2"',
            "consilient-cursor",
            "{cwd}",
            "{brief}",
            "{git_dir}",
        ),
        1,
        "known",
        "principal measurement, 2026-08-21",
    ),
    Harness(
        "grok",
        "xai",
        "supergrok-heavy-weekly",
        ("grok", "-p", "{brief}", "--cwd", "{cwd}"),
        2,
        "known",
        "principal measurement, 2026-08-21",
    ),
    Harness(
        "codex",
        "openai",
        "codex-weekly",
        ("codex", "exec", "-C", "{cwd}", "{brief}"),
        None,
        "unknown",
        "principal measurement, 2026-08-21",
    ),
)


def select_harnesses(
    installed: Mapping[str, bool], *, count: int = 1, requested: str | None = None
) -> tuple[Harness, ...]:
    """Choose installed harnesses by known headroom, keeping fan-out families distinct."""
    if count not in (1, 2):
        raise ValueError("dispatch count must be one or two")

    if requested is not None:
        harness = next((item for item in REGISTRY if item.name == requested), None)
        if harness is None:
            raise DispatchRefused(f"unknown harness {requested!r}")
        if not installed.get(harness.name, False):
            raise DispatchRefused(f"{harness.name} is not installed")
        if not harness.has_headroom:
            raise DispatchRefused(
                f"{harness.name} headroom is {harness.headroom_state}; dispatch refused"
            )
        return (harness,)

    candidates = sorted(
        (
            harness
            for harness in REGISTRY
            if installed.get(harness.name, False)
            and harness.has_headroom
        ),
        key=lambda harness: harness.headroom_percent or 0,
        reverse=True,
    )
    selected: list[Harness] = []
    for harness in candidates:
        if harness.family not in {item.family for item in selected}:
            selected.append(harness)
        if len(selected) == count:
            return tuple(selected)

    raise DispatchRefused(
        f"no installed harness has known headroom for {count} distinct model "
        f"{'families' if count == 2 else 'family'}"
    )
