"""Enumerate public upstream issues that are admissible as B4 tickets.

This script reads public GitHub data only: it sends no authorisation header,
does not fetch comments, and never modifies an upstream repository.

ADMISSION RULE
--------------
An issue is admissible only if the red phase comes from upstream, not from us.
It must carry a runnable snippet, stated failing invocation, or matching
``xfail``/``skip``/``skipif`` marker in the upstream test tree, *and* state
the expected behaviour upstream. A matching marker supplies both. An issue
without an upstream-stated oracle is inadmissible: writing one would invent
what "correct" means.

Comments are deliberately not fetched: GitHub's unauthenticated REST limit is
60 requests per hour, so comment-per-issue would defeat a conservative sweep.
An otherwise suitable comment-only issue is therefore recorded inadmissible.
The requested API version, ``2022-11-28``, is supported through 2028-03-10.

Conservative parser ceiling: the snippet route recognises only a direct
assertion accompanied by upstream failure evidence; the invocation route needs
a shell prompt outside a fenced block (or a command inside one) and concrete
``Expected: ... Actual: ...`` evidence. The marker route recognises AST-backed
test*/Test* decorators and module ``pytestmark`` calls only. Other report
formats are recorded inadmissible rather than guessed.

Bar and recheck: the incumbent is GitHub's REST list-issues endpoint, Link
pagination, and public repository archives. [cited, retrieved 2026-08-26]
https://docs.github.com/en/rest/issues/issues#list-repository-issues
https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-tar
https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
https://docs.github.com/en/rest/about-the-rest-api/api-versions
This script adds a B4-specific upstream-red-phase rule and records every
classification and reason in a private instance artefact. [asserted]

Usage: ``python scripts/b4_pool.py [--self-check]``.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import tarfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
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


def marker_issue_numbers(text: str, repository: str) -> set[int]:
    """Read only issue references inside xfail/skip/skipif calls for *repository*."""
    owner, project = repository.split("/", 1)
    own_url = re.compile(
        rf"https?://github\.com/{re.escape(owner)}/{re.escape(project)}/issues/(\d{{3,6}})",
        re.I,
    )
    found: set[int] = set()
    for match in MARKER.finditer(text):
        call = _marker_call(text, match.start())
        if not isinstance(call, str) or not call:
            continue
        found.update(int(number) for number in own_url.findall(call))
        call = own_url.sub("", call)
        found.update(int(number) for number in BARE_ISSUE.findall(call))
        found.update(int(number) for number in ISSUE_WORD.findall(call))
    return found


def marker_evidence(
    text: str, repository: str, source_path: str
) -> dict[int, list[dict[str, Any]]]:
    """Return issue evidence from real test decorators or module pytestmark calls."""
    try:
        tree = ast.parse(text, filename=source_path)
    except SyntaxError:
        return {}
    owner, project = repository.split("/", 1)
    own_url = re.compile(
        rf"https?://github\.com/{re.escape(owner)}/{re.escape(project)}/issues/(\d{{3,6}})",
        re.I,
    )
    found: dict[int, list[dict[str, Any]]] = {}

    def add(call: ast.Call, context: str) -> None:
        source = ast.get_source_segment(text, call) or _dotted_name(call.func)
        numbers = {int(number) for number in own_url.findall(source)}
        scrubbed = own_url.sub("", source)
        numbers.update(int(number) for number in BARE_ISSUE.findall(scrubbed))
        numbers.update(int(number) for number in ISSUE_WORD.findall(scrubbed))
        for number in numbers:
            found.setdefault(number, []).append(
                {
                    "kind": "upstream_test_marker",
                    "source_path": source_path,
                    "line": call.lineno,
                    "context": context,
                    "text": source,
                }
            )

    def add_marks(value: ast.AST, context: str) -> None:
        for node in ast.walk(value):
            if isinstance(node, ast.expr):
                call = _marker_call(node)
                if isinstance(call, ast.Call):
                    add(call, context)

    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test"):
            for decorator in node.decorator_list:
                add_marks(decorator, f"test:{node.name}")
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for decorator in node.decorator_list:
                add_marks(decorator, f"class:{node.name}")
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in statement.targets
        ):
            add_marks(statement.value, "module:pytestmark")
    return found


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


def classify_issue(
    issue: Mapping[str, Any],
    marker_numbers: set[int] | MarkerIndex | None = None,
    retrieval_date: str = "",
    *,
    markers: MarkerIndex | None = None,
) -> dict[str, Any]:
    """Classify one API issue without network access.

    The second positional argument accepts both shapes that landed here: a set
    of marker issue numbers, or a mapping of number to evidence records.
    """
    number = int(issue["number"])
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    record: dict[str, Any] = {
        "number": number,
        "title": title,
        "url": str(issue.get("html_url") or ""),
        "labels": _labels(issue.get("labels")),
        "created_date": str(issue.get("created_at") or ""),
        "retrieval_date": retrieval_date,
        "admissible": False,
        "reason": "",
        "reason_code": "",
    }
    marked, evidence = _marker_evidence_for(number, marker_numbers, markers)
    if marked:
        record.update(
            admissible=True,
            reason_code="admissible_marker",
            reason="upstream test marker names this issue; upstream supplies red phase and oracle",
        )
        if evidence:
            record["reproducer_evidence"] = evidence
            record["oracle_evidence"] = evidence
        return record
    blocks = _blocks(body)
    assertion, failure = _failing_assertion(blocks)
    invocation = _invocation(body, blocks)
    oracle = _expected_actual(body)
    has_assertion = any(ASSERTION.search(block) for block in blocks)
    if assertion:
        record.update(
            admissible=True,
            reason_code="admissible_assertion",
            reason="upstream assertion supplies a concrete red phase and oracle",
            reproducer_evidence={
                "kind": "failing_assertion",
                "text": assertion,
                "failure_passage": failure,
            },
            oracle_evidence={"kind": "assertion", "text": assertion},
        )
        return record
    if invocation and oracle:
        record.update(
            admissible=True,
            reason_code="admissible_invocation",
            reason="upstream supplies a reproducer and expected behaviour; no oracle is invented",
            reproducer_evidence={"kind": "invocation", "text": invocation},
            oracle_evidence={"kind": "expected_actual", "text": oracle},
        )
        return record
    if has_assertion and oracle:
        snippet = next((block for block in blocks if ASSERTION.search(block)), oracle)
        record.update(
            admissible=True,
            reason_code="admissible_snippet",
            reason="upstream supplies a reproducer and expected behaviour; no oracle is invented",
            reproducer_evidence={"kind": "snippet", "text": snippet},
            oracle_evidence={"kind": "expected_actual", "text": oracle},
        )
        return record
    if invocation:
        record.update(
            reason_code="no_oracle",
            reason="has a reproducer but no upstream-stated expected behaviour",
        )
        return record
    runnable, _kind = _reproducer(body)
    if runnable and not has_assertion and not _has_oracle(title, body):
        record.update(
            reason_code="no_oracle",
            reason="has a reproducer but no upstream-stated expected behaviour",
        )
        return record
    record.update(
        reason_code="no_reproducer",
        reason="no runnable snippet, stated failing invocation, or matching upstream test marker",
    )
    return record


def self_check() -> None:
    """Small classifier ratchet: removing either upstream input must not admit an issue."""
    missing = classify_issue({"number": 1, "title": "broken", "body": ""})
    assert missing["admissible"] is False, missing
    assert missing["reason_code"] == "no_reproducer", missing
    no_oracle_snippet = classify_issue(
        {
            "number": 2,
            "title": "odd",
            "body": "```python\nimport pytest\nprint(pytest.__version__)\n```",
        }
    )
    assert no_oracle_snippet["admissible"] is False, no_oracle_snippet
    assert no_oracle_snippet["reason_code"] == "no_oracle", no_oracle_snippet
    no_oracle = classify_issue(
        {
            "number": 2,
            "title": "odd",
            "body": "$ pytest test_case.py\nExpected behaviour:\n",
        }
    )
    assert no_oracle["admissible"] is False, no_oracle
    assert no_oracle["reason_code"] == "no_oracle", no_oracle
    traceback_loose = classify_issue(
        {
            "number": 3,
            "title": "broken",
            "body": "pytest test_case.py\nTraceback (most recent call last):\nValueError: bad",
        }
    )
    assert traceback_loose["admissible"] is False, traceback_loose
    assert traceback_loose["reason_code"] == "no_oracle", traceback_loose
    traceback_only = classify_issue(
        {
            "number": 3,
            "title": "broken",
            "body": "$ pytest test_case.py\nTraceback (most recent call last):\nValueError: bad",
        }
    )
    assert traceback_only["admissible"] is False, traceback_only
    assert traceback_only["reason_code"] == "no_oracle", traceback_only
    actual_only_loose = classify_issue(
        {"number": 4, "title": "odd", "body": "pytest test_case.py\nActual: 2"}
    )
    assert actual_only_loose["admissible"] is False, actual_only_loose
    assert actual_only_loose["reason_code"] == "no_oracle", actual_only_loose
    actual_only = classify_issue(
        {"number": 4, "title": "odd", "body": "$ pytest test_case.py\nActual: 2"}
    )
    assert actual_only["admissible"] is False, actual_only
    assert actual_only["reason_code"] == "no_oracle", actual_only
    snippet_with_expected = classify_issue(
        {
            "number": 5,
            "title": "assertion rewriting doubles a value",
            "body": "```python\ndef test_value():\n    assert value() == 1\n```\nExpected: value is 1; actual: 2.",
        }
    )
    assert snippet_with_expected["admissible"] is True, snippet_with_expected
    template = classify_issue(
        {
            "number": 5,
            "title": "Expected behaviour",
            "body": "```python\nimport pytest\n\ndef example():\n    pass\n\nclass Example:\n    pass\n```\nExpected behaviour:\n",
        }
    )
    assert template["admissible"] is False, template
    assert template["reason_code"] == "no_reproducer", template
    prose = classify_issue(
        {
            "number": 6,
            "title": "odd",
            "body": "pytest should indicate the correct result\nExpected: ok. Actual: bad.",
        }
    )
    assert prose["admissible"] is False, prose
    assert prose["reason_code"] == "no_reproducer", prose
    nonfailing_assertion = classify_issue(
        {"number": 7, "title": "odd", "body": "```python\nassert value() == 1\n```"}
    )
    assert nonfailing_assertion["admissible"] is False, nonfailing_assertion
    assert nonfailing_assertion["reason_code"] == "no_reproducer", nonfailing_assertion
    for number, body in (
        (8, "```python\nassert False\n```\nAssertion failure elsewhere."),
        (9, "```python\nassert 2 + 2 == 4\n```\nAssertion failure elsewhere."),
        (
            10,
            "```python\nassert result == expected  # that passes\n```\nAssertion failure.",
        ),
        (
            11,
            "```python\nassert result == expected\n```\nA different assertion failure occurred.",
        ),
    ):
        rejected = classify_issue(
            {"number": number, "title": "Assertion failure", "body": body}
        )
        assert rejected["admissible"] is False, rejected
        assert rejected["reason_code"] == "no_reproducer", rejected
    admitted = classify_issue(
        {
            "number": 12,
            "title": "assertion rewriting doubles a value",
            "body": "```python\ndef test_value():\n    assert value() == 1\n# assert value() == 1 fails: value() is 2\n```",
        }
    )
    assert admitted["admissible"] is True, admitted
    assert admitted["reproducer_evidence"]["kind"] == "failing_assertion", admitted
    invocation = classify_issue(
        {
            "number": 13,
            "title": "odd result",
            "body": "```sh\npytest test_case.py\n```\nExpected: [1]. Actual: [2].",
        }
    )
    assert invocation["admissible"] is True, invocation
    assert invocation["oracle_evidence"]["kind"] == "expected_actual", invocation
    marked_set = classify_issue({"number": 6, "title": "", "body": ""}, {6})
    assert marked_set["admissible"] is True, marked_set
    marked = classify_issue(
        {"number": 14, "title": "", "body": ""},
        {
            14: [
                {
                    "kind": "upstream_test_marker",
                    "source_path": "testing/test_x.py",
                    "line": 1,
                    "context": "test:test_x",
                    "text": "pytest.mark.xfail(reason='#14')",
                }
            ]
        },
    )
    assert marked["admissible"] is True, marked
    extracted_set = marker_issue_numbers(
        '@pytest.mark.xfail(reason="issue #10042")\n'
        '@pytest.mark.skip(reason="https://github.com/python/cpython/issues/124703")',
        "pytest-dev/pytest",
    )
    assert extracted_set == {10042}, extracted_set
    extracted = marker_evidence(
        '@pytest.mark.xfail(reason="https://github.com/pytest-dev/pytest/issues/10042")\n'
        "def test_example():\n    pass\n",
        "pytest-dev/pytest",
        "testing/test_example.py",
    )
    assert set(extracted) == {10042}, extracted
    assert extracted[10042][0]["context"] == "test:test_example", extracted
    assert "issues/10042" in extracted[10042][0]["text"], extracted
    nested = marker_evidence(
        '@pytest.mark.parametrize("value", [pytest.param(1, marks=pytest.mark.xfail(reason="issue #10043"))])\n'
        "def test_nested(value):\n    pass\n\n"
        '@pytest.mark.skip(reason="issue #10044")\n'
        "class TestClass:\n    pass\n",
        "pytest-dev/pytest",
        "testing/test_nested.py",
    )
    assert set(nested) == {10043, 10044}, nested
    assert nested[10043][0]["context"] == "test:test_nested", nested
    assert nested[10044][0]["context"] == "class:TestClass", nested
    module_mark = marker_evidence(
        'pytestmark = pytest.mark.skipif(True, reason="issue #10045")\n',
        "pytest-dev/pytest",
        "testing/test_module.py",
    )
    assert module_mark[10045][0]["context"] == "module:pytestmark", module_mark
    ignored = marker_evidence(
        '# @pytest.mark.xfail(reason="issue #10042")\n'
        'example = "@pytest.mark.skip(reason=\\"issue #10042\\")"\n'
        '@pytest.mark.xfail(reason="issue #10042")\n'
        "def example():\n    pass\n",
        "pytest-dev/pytest",
        "testing/test_example.py",
    )
    assert ignored == {}, ignored


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


def _metadata(repo: Repo) -> dict[str, Any]:
    owner, project = repo.name.split("/", 1)
    data, _ = _json(f"{API}/repos/{owner}/{project}")
    if not isinstance(data, dict):
        raise PoolError(f"repository metadata for {repo.name} is not an object")
    licence = data.get("license")
    if not isinstance(licence, dict):
        licence = {}
    return {
        "repository": repo.name,
        "licence_spdx": licence.get("spdx_id"),
        "licence_name": licence.get("name"),
        "default_branch": data.get("default_branch") or "main",
    }


def _issues(repo: Repo) -> list[dict[str, Any]]:
    owner, project = repo.name.split("/", 1)
    url: str | None = f"{API}/repos/{owner}/{project}/issues?" + urlencode(
        {"state": "open", "labels": repo.bug_label, "per_page": 100}
    )
    issues: list[dict[str, Any]] = []
    while url:
        page, headers = _json(url)
        if not isinstance(page, list):
            raise PoolError(f"issues payload for {repo.name} is not a list")
        issues.extend(
            item
            for item in page
            if isinstance(item, dict) and "pull_request" not in item
        )
        next_link = NEXT.search(headers.get("link", ""))
        url = next_link.group(1) if next_link else None
    return issues


def _markers(repo: Repo, branch: str) -> dict[int, list[dict[str, Any]]]:
    owner, project = repo.name.split("/", 1)
    url = f"https://codeload.github.com/{quote(owner)}/{quote(project)}/tar.gz/refs/heads/{quote(branch)}"
    payload, _ = _open(url, ARCHIVE_TIMEOUT_S)
    result: dict[int, list[dict[str, Any]]] = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive:
            path = "/" + member.name.replace("\\", "/").lower()
            if (
                not member.isfile()
                or not path.endswith(".py")
                or not any(needle in path for needle in repo.test_paths)
            ):
                continue
            handle = archive.extractfile(member)
            if handle is not None:
                source_path = member.name.partition("/")[2]
                for number, evidence in marker_evidence(
                    handle.read().decode("utf-8", "replace"), repo.name, source_path
                ).items():
                    result.setdefault(number, []).extend(evidence)
    return result


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


def sweep(repo: Repo, retrieval_date: str) -> dict[str, Any]:
    metadata = _metadata(repo)
    if metadata["licence_spdx"] not in PERMISSIVE_LICENCES:
        raise PoolError(
            f"{repo.name} has non-permissive or unrecognised licence {metadata['licence_spdx']!r}"
        )
    markers = _markers(repo, str(metadata["default_branch"]))
    records = [
        classify_issue(issue, markers, retrieval_date) for issue in _issues(repo)
    ]
    admissible = sum(bool(record["admissible"]) for record in records)
    return {
        **metadata,
        "bug_label": repo.bug_label,
        "retrieval_date": retrieval_date,
        "marker_issue_numbers": sorted(markers),
        "swept": len(records),
        "admissible": admissible,
        "inadmissible": len(records) - admissible,
        "inadmissible_reasons": _reason_counts(records),
        "issues": records,
    }


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-check", action="store_true", help="run the no-network classifier check"
    )
    args = parser.parse_args(argv)
    self_check()
    if args.self_check:
        print("self-check passed")
        return 0
    retrieval_date = _now()
    pools = [sweep(repo, retrieval_date) for repo in REPOS]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    admission_rule = __doc__.split("ADMISSION RULE\n--------------\n", 1)[1].split(
        "\n\nComments", 1
    )[0]
    OUT.write_text(
        json.dumps(
            {
                "retrieval_date": retrieval_date,
                "admission_rule": admission_rule,
                "credential_used": False,
                "comments_fetched": False,
                "repositories": pools,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _print_counts(pools)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
