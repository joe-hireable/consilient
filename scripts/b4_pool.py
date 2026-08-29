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

The evidence vocabulary — the regexes, the snippet, invocation and marker extractors, the unauthenticated ``_open``/``_json`` read and the reason tallies — now lives in ``b4_pool_evidence.py``. The admission rule itself, ``classify_issue``, together with the marker readers and the issue and repository listings, lives in ``b4_pool_admission.py``. This file keeps the sweep: the test-archive walk, the classifier ratchet and the command line.
"""

from __future__ import annotations
import sys
import argparse
import io
import json
import tarfile
from pathlib import Path

# bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any
from urllib.parse import quote
from b4_pool_evidence import (
    API,
    ARCHIVE_TIMEOUT_S,
    OUT,
    PERMISSIVE_LICENCES,
    PoolError,
    REPOS,
    Repo,
    _now,
    _open,
    _print_counts,
    _reason_counts,
)

from b4_pool_admission import (
    _issues,
    _metadata,
    classify_issue,
    marker_evidence,
    marker_issue_numbers,
)


__all__ = [
    "API",
    "ARCHIVE_TIMEOUT_S",
    "OUT",
    "PERMISSIVE_LICENCES",
    "PoolError",
    "REPOS",
    "Repo",
    "_issues",
    "_metadata",
    "_now",
    "_open",
    "_print_counts",
    "_reason_counts",
    "classify_issue",
    "main",
    "marker_evidence",
    "marker_issue_numbers",
    "self_check",
    "sweep",
]


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
