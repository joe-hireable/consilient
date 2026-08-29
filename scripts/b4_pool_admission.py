"""The admission decision for one upstream issue, and the two listings it reads.

ADMISSION RULE
--------------
An issue is admissible only if the red phase comes from upstream, not from us.
It must carry a runnable snippet, stated failing invocation, or matching
``xfail``/``skip``/``skipif`` marker in the upstream test tree, *and* state
the expected behaviour upstream. A matching marker supplies both. An issue
without an upstream-stated oracle is inadmissible: writing one would invent
what "correct" means.

``classify_issue`` applies that rule with no network access at all, and records a
``reason_code`` on refusal as carefully as on admission, so a finished sweep reads as a
distribution of reasons rather than a bare count. The marker route recognises AST-backed
test*/Test* decorators and module ``pytestmark`` calls only. Other report formats are
recorded inadmissible rather than guessed. ``marker_issue_numbers`` and
``marker_evidence`` take issue references only from inside a marker call and only for
the repository being swept, so a link to somebody else's tracker cannot admit a ticket.

Comments are deliberately not fetched: GitHub's unauthenticated REST limit is 60
requests per hour, so comment-per-issue would defeat a conservative sweep. An otherwise
suitable comment-only issue is therefore recorded inadmissible. ``_issues`` walks Link
pagination for open issues carrying the repository's own bug label and drops pull
requests; ``_metadata`` reads the licence and default branch. Both are reads — nothing
in this file writes upstream."""

from __future__ import annotations
import sys
import ast
import re
from pathlib import Path

# bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any, Mapping
from urllib.parse import urlencode
from b4_pool_evidence import (
    API,
    ASSERTION,
    BARE_ISSUE,
    ISSUE_WORD,
    MARKER,
    MarkerIndex,
    NEXT,
    PoolError,
    Repo,
    _blocks,
    _dotted_name,
    _expected_actual,
    _failing_assertion,
    _has_oracle,
    _invocation,
    _json,
    _labels,
    _marker_call,
    _marker_evidence_for,
    _reproducer,
)


__all__ = [
    "API",
    "ASSERTION",
    "BARE_ISSUE",
    "ISSUE_WORD",
    "MARKER",
    "MarkerIndex",
    "NEXT",
    "PoolError",
    "Repo",
    "_blocks",
    "_dotted_name",
    "_expected_actual",
    "_failing_assertion",
    "_has_oracle",
    "_invocation",
    "_json",
    "_labels",
    "_marker_call",
    "_marker_evidence_for",
    "_reproducer",
    "classify_issue",
    "marker_evidence",
    "marker_issue_numbers",
]


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
