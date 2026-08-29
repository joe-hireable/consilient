"""M01 — what capture refuses, and where the accepted objects are not allowed to go.

Every refusal here asserts the same two things afterwards: no event was logged, and
nothing was installed. A refusal that still wrote an object or a log line would be worse
than an acceptance, because it would leave a record of the very thing that was not
supposed to be recorded. The cases are a source outside the resolved workspace, a
symlink pointing out of it, private environment files and key or token material
recognised before install rather than after, and a symlinked object shard attempting to
redirect the store itself out of the workspace. The ``.env.example`` case guards the
opposite direction: a documented template is not a private environment file, and over-
refusal is a defect too. The collision case pins that an existing object whose bytes do
not match is refused rather than overwritten, and that the bytes already on disk are
left exactly as they were.

The gitignore check closes the loop and belongs with the refusals for that reason: it is
not enough to refuse what must not enter the store if what does enter can then be
committed. The store is asserted to be explicitly ignored, by asking git rather than by
reading the ignore file."""

import hashlib
import subprocess
from pathlib import Path
import pytest
from consilient import events
from records_helpers import (
    LOG,
    OBJECTS,
    _capture,
    _events,
    _records,
)

ROOT = Path(__file__).resolve().parents[1]


def test_source_outside_the_resolved_workspace_is_refused_without_an_event(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")

    with pytest.raises(events.EventError, match="outside the authorised workspace"):
        _records().capture_file(
            outside,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert not (workspace / OBJECTS).exists()


def test_symlink_escape_is_refused_without_exposing_or_capturing_the_target(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside-secret-free-fixture")
    link = workspace / "escape.bin"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this Windows test environment: {exc}")

    with pytest.raises(events.EventError, match="outside the authorised workspace"):
        _records().capture_file(
            link,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert not (workspace / OBJECTS).exists()


@pytest.mark.parametrize(
    ("relative", "payload"),
    (
        (".env", b"SAFE_NAME=credential-value"),
        ("private.pem", ("-----BEGIN " + "PRIVATE" + " KEY-----").encode()),
        ("token.txt", ("sk" + "-or-v1-" + "a" * 40).encode()),
    ),
)
def test_private_environment_key_and_token_material_are_refused_before_install(
    tmp_path: Path, relative: str, payload: bytes
) -> None:
    workspace = tmp_path / relative.replace(".", "-")
    workspace.mkdir()
    source = workspace / relative
    source.write_bytes(payload)

    with pytest.raises(events.EventError, match="credential|private environment"):
        _records().capture_file(
            source,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert (
        not list((workspace / OBJECTS).rglob("*"))
        if (workspace / OBJECTS).exists()
        else True
    )


def test_documented_environment_template_is_not_mistaken_for_a_private_env_file(
    tmp_path: Path,
) -> None:
    ref, _ = _capture(tmp_path, b"EXAMPLE_NAME=replace-me\n", relative=".env.example")
    assert (tmp_path / Path(ref.object_locator)).is_file()


def test_object_shard_symlink_cannot_redirect_capture_outside_the_private_store(
    tmp_path: Path,
) -> None:
    payload = b"object shard escape"
    digest = hashlib.sha256(payload).hexdigest()
    outside = tmp_path / "outside"
    outside.mkdir()
    shard = tmp_path / OBJECTS / "sha256" / digest[:2]
    shard.parent.mkdir(parents=True)
    try:
        shard.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(
            f"directory symlinks unavailable in this Windows test environment: {exc}"
        )

    with pytest.raises(events.EventError, match="object|store|root|escape"):
        _capture(tmp_path, payload)

    assert _events(tmp_path) == []
    assert list(outside.iterdir()) == []


def test_existing_mismatching_object_is_a_refused_collision_not_an_overwrite(
    tmp_path: Path,
) -> None:
    payload = b"expected bytes"
    digest = hashlib.sha256(payload).hexdigest()
    object_path = tmp_path / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(b"collision bytes")

    with pytest.raises(events.EventError, match="collision|mismatch"):
        _capture(tmp_path, payload)

    assert object_path.read_bytes() == b"collision bytes"
    assert _events(tmp_path) == []


def test_object_store_is_explicitly_untrackable() -> None:
    probe = ".harness/objects/sha256/aa/" + "b" * 62
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", probe],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert ignored.returncode == 0, ".harness/objects/ is not explicitly ignored"
