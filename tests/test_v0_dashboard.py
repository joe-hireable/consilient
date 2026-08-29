"""V0-30 and ADR-0053: the observability surface renders the record and never forms an
opinion of its own. Four properties make that real rather than promised. It cannot
disagree with `doctor` about the gates — the whole structure is compared, not a summary
line, so a divergence in any status, reason or evidence path fails here rather than
being discovered by someone reading a green page about a stopped system. It cannot
disagree with `beta`, and the rendered sentence is `Beta.render()`'s own output, so the
expert disclosure cannot paraphrase the number into something friendlier than it is. It
cannot render a failing condition in the passing style, which would be a verifier
accepting a bad artefact — β, committed by the instrument that measures β — and the
converse is asserted too, or the test would be satisfied by a page that is simply always
red. And it cannot reach outside the file it wrote: one `<script src>` or one font URL
turns it into a page that needs the network, and every objection ADR-0007 raised about a
local server comes back. The RACI panel is pinned in both directions because an honest
absence is the claim most likely to rot into an invented matrix, and `artefacts` is free
text whose values on the real log include four that are not files, so a bare identifier
is reported under its own heading rather than drawn as a directory."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from consilient.cli import main
from consilient.events import (
    canonical,
    read_all,
)
from v0_invariants_helpers import (
    HUMAN,
    _spend_scripts,
    doctor_payload,
    ev,
    outcome,
    verdict,
)


# ------------------------------------------------------ V0-30, ADR-0053 (observability)
# The surface renders the record and never forms an opinion of its own. Three properties
# make that real rather than promised: it cannot disagree with the CLI about an
# authoritative number, it cannot render a failing gate in the passing style, and it cannot
# reach outside the file it wrote. The fifth test pins the honesty of the RACI panel, which
# is the claim most likely to rot into an invented graph once someone wants one.
def dashboard_payload(tmp_path, capsys, log=None, db=None):
    """Run `consil dashboard --json` the way a user would, and return its one contract.

    `db` is a parameter because A2 is legitimately order-dependent: the first `doctor` run
    against a database that does not exist reports "no prior projection existed" and cannot
    compare, while the second compares against what the first wrote. Two runs sharing one
    database therefore differ for a correct reason, and a comparison test must give each
    run its own so it is measuring drift rather than measuring history.
    """
    out = tmp_path / "dash.html"
    code = main(
        [
            "--log",
            str(log or (tmp_path / "log")),
            "--db",
            str(db or (tmp_path / "state.db")),
            "--json",
            "dashboard",
            # `--out` is dashboard-specific, so unlike --json/--log/--db it is only valid
            # after the subcommand.
            "--out",
            str(out),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert out.exists(), "dashboard reported success without writing the file"
    return payload, out.read_text(encoding="utf-8")


def _seeded_log(tmp_path):
    log = tmp_path / "log"
    log.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).date().isoformat()
    work = ev(
        event="work.completed",
        actor="agent-one",
        data={
            "runtime_identity": "claude-code/session-a",
            "logical_identity": "builder",
            "work_role": "implementer",
            "artefacts": ["src/consilient/dashboard.py", "docs/decisions/0053.md"],
            "principal": HUMAN,
        },
    )
    lines = [
        canonical(work),
        canonical(outcome("a-1", "task-one", True)),
        canonical(verdict("a-1", "reject")),
    ]
    (log / (day + ".jsonl")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log


def test_the_dashboard_cannot_disagree_with_doctor_about_the_gates(tmp_path, capsys):
    """The page's gate block is `cmd_doctor`'s result, not a second reading of the gates.

    Two surfaces reporting the same thing is two chances to be wrong. This asserts equality
    of the whole structure rather than of a summary line, so a divergence anywhere in it —
    a status, a reason, an evidence path — fails here rather than being discovered by
    someone reading a green page about a stopped system.
    """
    log = _seeded_log(tmp_path)
    payload, _ = dashboard_payload(tmp_path, capsys, log=log)
    # A2 names the database it compared, in both its reason and its evidence, and it reports
    # differently on a first run than on a second. So the two runs must start from the same
    # path AND the same absence, or the test measures ordering rather than drift.
    (tmp_path / "state.db").unlink()
    truth = doctor_payload(tmp_path, capsys)
    assert payload["gates"] == truth["gates"]
    assert (
        payload["routing_orchestration_enabled"]
        == truth["routing_orchestration_enabled"]
    )


def test_the_dashboard_cannot_disagree_with_the_beta_command(tmp_path, capsys):
    log = _seeded_log(tmp_path)
    payload, html_text = dashboard_payload(tmp_path, capsys, log=log)
    code = main(
        ["--log", str(log), "--db", str(tmp_path / "state.db"), "--json", "beta"]
    )
    assert code == 0
    truth = json.loads(capsys.readouterr().out)
    for field in ("verdict", "n_rejected", "n_false_accept", "point", "interval"):
        assert payload["beta"][field] == truth[field], field
    # The rendered sentence is `Beta.render()`'s own output, so the expert disclosure cannot
    # paraphrase the number into something friendlier than it is.
    assert payload["beta_line"] in html_text


def test_a_failing_gate_condition_never_renders_in_the_passing_style(tmp_path, capsys):
    """The defect this project exists to catch, applied to its own dashboard.

    A surface that showed green where a gate fails would be a verifier accepting a bad
    artefact — beta, committed by the instrument that measures beta.
    """
    from consilient import dashboard as dash

    payload, _ = dashboard_payload(tmp_path, capsys, log=_seeded_log(tmp_path))
    conditions = [c for g in payload["gates"].values() for c in g["conditions"]]
    assert any(c["status"] != "pass" for c in conditions), (
        "fixture no longer exercises a failing condition; this test would pass vacuously"
    )

    rendered = dash.render_html(payload)
    for condition in conditions:
        marker = 'class="cond s-' + condition["status"] + '"'
        assert marker in rendered, condition["id"] + " did not render its own state"
    assert 'class="verdict is-on"' not in rendered, (
        "the page declared the system enabled while a condition was failing"
    )
    assert "Consilient is watching, not acting." in rendered

    # And the converse: with every condition passing it must be willing to say so, or this
    # test would be satisfied by a page that is simply always red.
    happy = json.loads(json.dumps(payload))
    for gate in happy["gates"].values():
        for condition in gate["conditions"]:
            condition["status"] = "pass"
    happy["routing_orchestration_enabled"] = True
    assert 'class="verdict is-on"' in dash.render_html(happy)


def test_the_rendered_page_references_nothing_outside_itself(tmp_path, capsys):
    """ADR-0007's surviving prohibitions, enforced rather than promised.

    "A rendered file, not a web app" is only true while the file is self-contained. One
    `<script src>` or one font URL turns it into a page that needs the network, and every
    objection ADR-0007 raised about a local server comes back.
    """
    _, rendered = dashboard_payload(tmp_path, capsys, log=_seeded_log(tmp_path))
    for forbidden in ("<script", "src=", "http://", "https://", "@import", "url("):
        assert forbidden not in rendered, "page reached outside itself via " + forbidden


def test_the_dashboard_renders_from_an_empty_trajectory(tmp_path, capsys):
    """No data is a state to render, not a crash and not a zero.

    The real trajectory has no budget events and no human verdicts, so several panels are
    already exercising their empty path in production. This pins the fully-empty case.
    """
    empty = tmp_path / "log"
    empty.mkdir(parents=True, exist_ok=True)
    payload, rendered = dashboard_payload(tmp_path, capsys, log=empty)
    assert payload["trajectory"]["events"] == 0
    assert payload["agents"] == []
    assert payload["beta"]["verdict"] == "insufficient_data"
    assert payload["usage"]["windows"] == []
    assert "absence of observation, not an observation of zero" in rendered
    assert "<h1>" in rendered


def test_raci_is_reported_as_underivable_while_the_record_lacks_its_fields(
    tmp_path, capsys
):
    """The honest-absence claim, pinned so it cannot quietly become an invented matrix.

    RACI attaches to a piece of work (ADR-0020), and the trajectory carries no stable
    work-item identifier, no `accountable`, no `consulted` and no `informed`. The panel must
    say so. If someone later derives a matrix anyway, this fails — and if the schema gains
    the fields, the second half fails, which is the reminder to rebuild the panel rather
    than leave it asserting an absence that is no longer true.
    """
    from consilient import dashboard as dash

    payload, rendered = dashboard_payload(tmp_path, capsys, log=_seeded_log(tmp_path))
    assert payload["raci"]["derivable"] is False
    assert "cannot be derived" in rendered

    informed = next(x for x in payload["raci"]["letters"] if x["letter"] == "I")
    assert informed["derivable"] == "no"
    assert informed["coverage"] == 0

    events, _ = read_all(tmp_path / "log")
    for field in dash.RACI_FIELDS + dash.WORK_ITEM_FIELDS:
        assert not any(field in e.data for e in events), (
            field + " now appears in the trajectory; the RACI panel's claim that it is "
            "absent is stale and must be rebuilt"
        )


def test_a_non_path_value_is_never_drawn_as_a_directory(tmp_path, capsys):
    """`artefacts` is free text, and on the real log four of its values are not files.

    Drawing a bare commit identifier as a directory node would state a fact the record does
    not contain. They are excluded from the graph and reported under their own heading, so
    neither the invention nor a silent drop is possible.
    """
    from consilient import dashboard as dash

    assert dash._is_path("docs/decisions/0053.md")
    assert dash._is_path("AGENTS.md")
    assert not dash._is_path("6088e3e")
    assert not dash._is_path("private handoff memo only")

    log = tmp_path / "log"
    log.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).date().isoformat()
    noisy = ev(
        event="work.completed",
        actor="agent-one",
        data={
            "runtime_identity": "claude-code/session-a",
            "artefacts": ["docs/decisions/0053.md", "6088e3e"],
        },
    )
    (log / (day + ".jsonl")).write_text(canonical(noisy) + "\n", encoding="utf-8")

    payload, rendered = dashboard_payload(tmp_path, capsys, log=log)
    assert [a["path"] for a in payload["artefacts"]] == ["docs/decisions/0053.md"]
    assert [a["value"] for a in payload["annotations"]] == ["6088e3e"]
    assert not any(e["group"] == "6088e3e" for e in payload["edges"])
    # Excluded from the graph, but not lost: it is still reported to the reader.
    assert "6088e3e" in rendered


def test_the_dashboard_adds_no_dependency_outside_the_standard_library():
    """ADR-0031's stdlib-only core, checked over the whole package.

    ADR-0007 named "no frontend dependency" as its enforcement, and ADR-0053 keeps it. The
    dashboard is where that rule is most tempting to break.
    """
    import ast

    root = Path(__file__).resolve().parents[1] / "src" / "consilient"
    external = set()
    for source in sorted(root.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                # level > 0 is a relative import: our own package, not a dependency.
                names = [] if node.level else [(node.module or "").split(".")[0]]
            else:
                continue
            external.update(n for n in names if n and n not in sys.stdlib_module_names)
    assert not external, "consilient imports outside stdlib: " + repr(sorted(external))


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)
