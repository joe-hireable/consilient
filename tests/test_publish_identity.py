"""A publication sign-off must be certifiable by a real person, and this worktree must be clean.

THE NEAR MISS, measured 29 August 2026. The driver squashes rather than fast-forwards precisely
so that ONE certification of origin travels to the public repository instead of hundreds, and it
takes that certification from the configured git identity. The guard on that identity was

    "fixture" in signer.lower() or ".invalid" in signer.lower()

and the identity this worktree's LOCAL config actually held was `Test <t@example.com>`, which
contains neither substring. 142 of the 376 unpublished commits were authored by fixture
identities, every commit made that day among them. The guard would have passed and a false
certification would have been filed in public, which is irreversible.

The old check knew the two spellings that had been seen. RFC 2606 and RFC 6761 reserve these
domains so that nobody can own them, which is the actual property, so the property is what is
tested now.

The second test is the one that would have caught it earlier, and it is deliberately about THIS
repository rather than about a function: several tests write a fixture identity into a git config,
and when one of them writes it into the real worktree instead of a tmp_path, every commit after it
is misattributed silently. Nothing looks wrong until a push.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.build_driver_helpers import ROOT, _load_driver

DRIVER = _load_driver()


@pytest.mark.parametrize(
    "signer",
    [
        "Test <t@example.com>",
        "Fixture <fixture@example.invalid>",
        "Someone <tests@example.invalid>",
        "A <a@example.net>",
        "B <b@example.org>",
        "C <c@sub.example>",
        "D <d@host.test>",
        "E <e@localhost>",
        "Fixture Person <real@gethireable.com>",
    ],
)
def test_an_uncertifiable_identity_is_refused(signer: str) -> None:
    assert DRIVER._identity_cannot_certify(signer), (
        f"{signer!r} would be accepted as a certification of origin. It is a reserved or "
        "fixture address, so there is nobody it could certify anything on behalf of."
    )


@pytest.mark.parametrize(
    "signer",
    [
        "Joe Brown <joe@gethireable.com>",
        "Someone Real <someone@anthropic.com>",
        "A Person <person@examples-ltd.co.uk>",
    ],
)
def test_a_real_identity_is_accepted(signer: str) -> None:
    """The guard must not be so wide that it refuses everyone.

    `examples-ltd.co.uk` is in the list on purpose: a substring test for "example" alone would
    refuse a real company, and a guard that blocks publication entirely is its own outage.
    """
    assert not DRIVER._identity_cannot_certify(signer)


def test_this_worktree_has_no_fixture_identity_configured() -> None:
    """The failure mode itself: a test's fixture identity leaking into the real config.

    Checked against the identity git would actually use, not against the config file, because
    the value can arrive from a local override, an includeIf, or the environment, and only
    `git var` resolves all three the way a commit would.
    """
    ident = subprocess.run(
        ["git", "var", "GIT_AUTHOR_IDENT"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip()
    signer = ident.rsplit(">", 1)[0] + ">" if ">" in ident else ident
    assert not DRIVER._identity_cannot_certify(signer), (
        f"this worktree would author commits as {signer!r}, which cannot certify origin. A "
        "test has written a fixture identity into the real repository config instead of a "
        "temporary one. Clear it with:\n"
        "  git config --local --unset user.email\n"
        "  git config --local --unset user.name\n"
        "and find the test that wrote it, because it will do it again."
    )


def test_the_local_config_does_not_override_the_global_identity() -> None:
    """A local override is the mechanism by which the leak persists, so name it directly."""
    overrides = {}
    for key in ("user.email", "user.name"):
        result = subprocess.run(
            ["git", "config", "--local", "--get", key],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            overrides[key] = result.stdout.strip()
    assert overrides == {}, (
        f"this worktree sets {overrides} locally, overriding the global identity. That is how "
        "a fixture identity survives a session and misattributes every commit in it. Unset "
        "both unless there is a recorded reason for a per-worktree identity."
    )


def test_the_guard_is_reachable_from_the_publication_path() -> None:
    """A hardened predicate nothing calls is decoration.

    Asserts the source of `publish_if_ready` actually invokes it, because the previous version
    inlined the check and an inlined check is what drifted out of date.
    """
    source = Path(DRIVER.__file__ or "").read_text(encoding="utf-8")
    marker = source.partition("def publish_if_ready")[2]
    assert "_identity_cannot_certify(signer)" in marker, (
        "publish_if_ready no longer calls _identity_cannot_certify, so the sign-off identity "
        "is being judged by something else, or by nothing"
    )
