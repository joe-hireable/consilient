"""The vocabulary of upstream evidence: what a red phase looks like in issue prose.

Every pattern the sweep matches and every extractor that runs on a match lives here —
fenced blocks, runnable snippets, shell invocations, ``Expected: ... Actual: ...``
pairs, ``xfail``/``skip``/``skipif`` marker spans and the issue references inside them.
An extractor turns a body of issue text into a single evidence string, or into the empty
string when upstream never said it. The empty string is the point: nothing here supplies
a missing half, so no verdict further up can rest on prose this file invented.

Conservative parser ceiling: the snippet route recognises only a direct assertion
accompanied by upstream failure evidence; the invocation route needs a shell prompt
outside a fenced block (or a command inside one) and concrete ``Expected: ... Actual:
...`` evidence.

``_open`` and ``_json`` are the family's only network calls, and they are deliberately
blunt — an Accept header, a user agent and an API version, no authorisation header,
every failure surfaced as ``PoolError``. The requested API version, ``2022-11-28``, is
supported through 2028-03-10. The tallying helpers count and print inadmissibility
reasons from finished records; they read classifications and never reach an issue, so a
report cannot revise a verdict after the fact."""

from __future__ import annotations
import sys
import ast
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent

OUT = ROOT / ".harness" / "b4-pool.json"

API = "https://api.github.com"

API_VERSION = "2022-11-28"

USER_AGENT = "ConsilientB4Pool/1.0 (public-read)"

TIMEOUT_S = 60

ARCHIVE_TIMEOUT_S = 180

SEVENTEEN = 17

ALREADY_CREDITED = frozenset(
    {
        # Superseded 26 August 2026: 13369, 14774 and 6505 were closed before the
        # principal required open-issue work (see scripts/b4_tickets.py) and were
        # replaced with three verified, currently-open issues.
        ("pytest-dev/pytest", 14324),
        ("pytest-dev/pytest", 10644),
        ("pytest-dev/pytest", 12175),
    }
)

PERMISSIVE_LICENCES = frozenset(
    {"Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MIT"}
)

FENCE = re.compile(
    r"```(?:python|py|pycon|pytb|sh|bash|console|text)?\s*\n(.*?)```", re.S | re.I
)

RUNNABLE = re.compile(
    r"(?m)^\s*(?:import |from |def |class |assert |@pytest|with pytest)"
)

INVOCATION = re.compile(
    r"(?im)^\s*(?:[$]\s*)?(?:python(?:3)?\s+-m\s+pytest|python(?:3)?\s+-c)\b[^\r\n]*"
    r"|^\s*(?:[$]\s*)?(?:py\.test|pytest)\s+(?:[-./]\S*|\S+\.py(?:\S*)?)[^\r\n]*"
)

INVOCATION_LOOSE = re.compile(
    r"(?im)^\s*(?:[$]\s*)?(?:python(?:3)?\s+-m\s+pytest|python(?:3)?\s+-c|py\.test|pytest)\b"
)

FAILURE = re.compile(
    r"(?i)\b(assertionerror|assert(?:ion)?\s+(?:fails?|failed|failure)|fails?|failed|failure)\b"
)

PASSING_COMMENT = re.compile(r"(?i)#.*\bpass(?:es|ed|ing)?\b")

EXPECTED_ACTUAL = re.compile(
    r"(?is)\bexpected(?:\s+(?:result|behavio[u]?r))?\s*:\s*(?P<expected>[^\r\n.;]+?)"
    r"\s*(?:\.\s*|;|\r?\n+)\s*"
    r"(?:actual|got)(?:\s+(?:result|behavio[u]?r))?\s*:\s*(?P<actual>[^\r\n.]+)"
)

ORACLE = re.compile(
    r"(?ix)\b(expected|should(?:\s+not)?|correct\s+behavio(?:u)?r|instead|but\s+got|"
    r"unexpected|incorrect(?:ly)?)\b"
)

ASSERTION = re.compile(r"\b(?:assert|pytest\.raises|RaisesGroup)\b")

MARKER = re.compile(r"mark\.(?:xfail|skip|skipif)\b")

BARE_ISSUE = re.compile(r"(?<![/\w])#(\d{3,6})\b")

ISSUE_WORD = re.compile(r"\bissues?\s+#?(\d{3,6})\b", re.I)

NEXT = re.compile(r'<([^>]+)>;\s*rel="next"', re.I)


class PoolError(RuntimeError):
    """An unauthenticated public read failed."""


@dataclass(frozen=True)
class Repo:
    name: str
    bug_label: str
    test_paths: tuple[str, ...]


REPOS = (
    Repo("pytest-dev/pytest", "type: bug", ("/testing/",)),
    Repo("pypa/setuptools", "bug", ("/tests/", "/testing/")),
)

MarkerIndex = Mapping[int, list[dict[str, Any]]]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _labels(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, Mapping) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return names


def _dotted_name(node: ast.expr) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _marker_span(text: str, start: int) -> str:
    opening = text.find("(", start)
    if opening < 0:
        return ""
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def _marker_ast(node: ast.expr) -> ast.Call | None:
    if not isinstance(node, ast.Call):
        return None
    if _dotted_name(node.func) in {
        "pytest.mark.xfail",
        "pytest.mark.skip",
        "pytest.mark.skipif",
        "mark.xfail",
        "mark.skip",
        "mark.skipif",
    }:
        return node
    return None


def _marker_call(
    text_or_node: str | ast.expr, start: int | None = None
) -> str | ast.Call | None:
    """Extract a marker call from source text *or* from an AST node.

    Both shapes landed in this file: the regex span ``(text, start)`` and the
    AST recogniser ``(node,)``. Callers that used either must keep working.
    """
    if isinstance(text_or_node, str):
        if start is None:
            raise TypeError(
                "start is required when extracting a marker from source text"
            )
        return _marker_span(text_or_node, start)
    return _marker_ast(text_or_node)


def _blocks(body: str) -> list[str]:
    return [block.strip() for block in FENCE.findall(body) if block.strip()]


def _reproducer(body: str) -> tuple[bool, str]:
    blocks = _blocks(body)
    if any(RUNNABLE.search(block) or ASSERTION.search(block) for block in blocks):
        return True, "snippet"
    if INVOCATION_LOOSE.search(body):
        return True, "invocation"
    if any(INVOCATION_LOOSE.search(block) for block in blocks):
        return True, "invocation"
    return False, ""


def _has_oracle(title: str, body: str) -> bool:
    return bool(ORACLE.search(f"{title}\n{body}") or ASSERTION.search(body))


def _dynamic_assertion(node: ast.Assert) -> bool:
    if (
        isinstance(node.test, ast.Compare)
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
    ):
        if ast.dump(node.test.left, include_attributes=False) == ast.dump(
            node.test.comparators[0], include_attributes=False
        ):
            return False
    return any(
        isinstance(child, (ast.Attribute, ast.Call, ast.Name, ast.Subscript))
        for child in ast.walk(node.test)
    )


def _failing_assertion(blocks: Iterable[str]) -> tuple[str, str]:
    for block in blocks:
        try:
            tree = ast.parse(block)
        except SyntaxError:
            continue
        lines = block.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assert) or not _dynamic_assertion(node):
                continue
            source = ast.get_source_segment(block, node) or lines[node.lineno - 1]
            assertion = source.split("#", 1)[0].strip()
            if PASSING_COMMENT.search(lines[node.lineno - 1]):
                continue
            start = max(0, node.lineno - 2)
            end_lineno = node.end_lineno
            end = min(
                len(lines), (end_lineno if end_lineno is not None else node.lineno) + 1
            )
            for index in range(start, end):
                passage = lines[index].strip()
                if PASSING_COMMENT.search(passage) or FAILURE.search(passage) is None:
                    continue
                if index == node.lineno - 1 or "".join(assertion.split()) in "".join(
                    passage.split()
                ):
                    return assertion, passage
    return "", ""


def _invocation(body: str, blocks: Iterable[str]) -> str:
    outside_fences = FENCE.sub("", body)
    match = INVOCATION.search(outside_fences)
    if match is not None and match.group(0).lstrip().startswith("$"):
        return match.group(0).strip()
    for block in blocks:
        match = INVOCATION.search(block)
        if match is not None:
            return match.group(0).strip()
    return ""


def _expected_actual(body: str) -> str:
    match = EXPECTED_ACTUAL.search(body)
    if match is None:
        return ""
    expected = match.group("expected").strip()
    actual = match.group("actual").strip()
    if not expected or not actual:
        return ""
    return match.group(0).strip()


def _marker_evidence_for(
    number: int,
    positional: set[int] | MarkerIndex | None,
    markers: MarkerIndex | None,
) -> tuple[bool, list[dict[str, Any]]]:
    """Accept both marker shapes: a set of numbers, or an evidence mapping."""
    evidence: list[dict[str, Any]] = []
    marked = False
    if isinstance(positional, Mapping):
        hit = positional.get(number)
        if hit:
            marked = True
            evidence.extend(hit)
    elif isinstance(positional, (set, frozenset)):
        marked = number in positional
    if markers:
        hit = markers.get(number)
        if hit:
            marked = True
            evidence.extend(hit)
    return marked, evidence


def _open(url: str, timeout: int) -> tuple[bytes, dict[str, str]]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read(), {
                key.lower(): value for key, value in response.headers.items()
            }
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise PoolError(
            f"unauthenticated GET {url} failed: HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise PoolError(f"unauthenticated GET {url} failed: {error.reason}") from error


def _json(url: str, timeout: int = TIMEOUT_S) -> tuple[Any, dict[str, str]]:
    payload, headers = _open(url, timeout)
    try:
        return json.loads(payload), headers
    except json.JSONDecodeError as error:
        raise PoolError(f"invalid JSON from {url}") from error


def _reason_counts(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                str(record["reason_code"])
                for record in records
                if not record["admissible"]
            ).items()
        )
    )


def _print_counts(pools: list[dict[str, Any]]) -> None:
    totals: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    further = 0
    for pool in pools:
        print(pool["repository"])
        print(f"  licence: {pool['licence_spdx'] or pool['licence_name']}")
        print(f"  retrieval_date: {pool['retrieval_date']}")
        for key in ("swept", "admissible", "inadmissible"):
            print(f"  {key}: {pool[key]}")
            totals[key] += int(pool[key])
        print("  inadmissible-with-reason-breakdown:")
        for reason, count in pool["inadmissible_reasons"].items():
            print(f"    {reason}: {count}")
        reasons.update(pool["inadmissible_reasons"])
        for issue in pool["issues"]:
            if (
                issue["admissible"]
                and (pool["repository"], issue["number"]) not in ALREADY_CREDITED
            ):
                further += 1
    print("combined")
    for key in ("swept", "admissible", "inadmissible"):
        print(f"  {key}: {totals[key]}")
    print("  inadmissible-with-reason-breakdown:")
    for reason, count in sorted(reasons.items()):
        print(f"    {reason}: {count}")
    print(
        "  seventeen further admissible tickets exist: "
        f"{'yes' if further >= SEVENTEEN else 'no'} (further={further}; excluding pytest #14324, #10644, #12175)"
    )
