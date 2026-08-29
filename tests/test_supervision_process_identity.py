"""ADR-0034 section 1 and V0-25: liveness is never resolved from a process identity.

One check, in its own file, because it is not a fact about any single supervision unit.
It parses the source of every function the other four modules exercise —
`start_failures`, `artefact_bytes_in`, `committed_since`, `StartFailure`,
`write_expected`, `ExpectedArtefactError`, `write_started`, `started_line_in`,
`stall_failures`, `Stall`, `write_terminal`, `inspect_uncommitted_tracked` — and a ban
maintained beside one unit is a ban that silently narrows when the others move.

A PID is not a durable identifier, and a process check has reported dead work healthy
three times on this machine. [measured]

Names, not prose: the docstrings may say the word, the code may not. The discriminator
is sharpened rather than loosened (F-12). `subprocess.run` is permitted, because the
process it starts is a fresh `git` — an artefact reader, not the dispatched child. What
stays banned is any name for the child's own process: a pid, a handle, a `Popen`, a
process-table library. Honest limit: this is a name test, so a liveness check hidden
behind a neutral name would pass it."""

import ast
import inspect
from supervision_helpers import (
    _script,
)


def test_supervision_never_resolves_liveness_from_a_process_identity(tmp_path):
    """ADR-0034 section 1 and V0-25. A PID is not a durable identifier, and a process
    check has reported dead work healthy three times on this machine. [measured]

    Names, not prose: the docstrings may say the word, the code may not.

    The discriminator is sharpened rather than loosened (F-12). `subprocess.run` is
    permitted here because the process it starts is a fresh `git`, which is an
    artefact reader, not the dispatched child. What stays banned is any name for the
    child's own process: a pid, a handle, a `Popen`, a process-table library. Honest
    limit: this is a name test, so a liveness check hidden behind a neutral name would
    pass it.
    """
    script = _script()
    source = "\n".join(
        inspect.getsource(item)
        for item in (
            script.start_failures,
            script.artefact_bytes_in,
            script.committed_since,
            script.StartFailure,
            script.write_expected,
            script.ExpectedArtefactError,
            script.write_started,
            script.started_line_in,
            script.stall_failures,
            script.Stall,
            script.write_terminal,
            script.inspect_uncommitted_tracked,
        )
    )
    tree = ast.parse(source)
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    banned = ("pid", "popen", "psutil", "is_running", "tasklist")
    process_shaped = sorted(
        name
        for name in identifiers
        if any(token in name.lower() for token in banned)
        or ("process" in name.lower() and "subprocess" not in name.lower())
    )
    assert not process_shaped, (
        f"supervision resolves liveness from a process identity: {process_shaped}"
    )
