"""M06 — the boundary of what this unit is, pinned in the source rather than in
behaviour.

This unit records provenance; it does not train, promote or activate. Both tests here
defend that sentence, and neither touches a log, a fixture or a lineage, which is why
they sit apart from the rest of the suite. ``mutation_class_for`` decides what even
counts as a persistent mutation: fitting an embedding, running an optimiser and a
closed-form solve are all data-driven training, a direct edit is a non-data-driven state
change, and a frozen embedding lookup or an inference call is not a model change at all
— it returns ``None`` rather than a class, because recording every inference as a change
would bury the real mutations in noise. An unrecognised procedure is refused outright
rather than guessed into the nearest class.

The second test parses ``src/consilient/events.py`` and asserts on the syntax tree: no
training, inference, transport or subprocess import may appear; capability selection and
``getattr`` may not appear at all; and the change kind must stay distinct from the
record and capability kinds. It is a source-level pin deliberately, so it fails on the
import being added rather than later on the behaviour that import would have enabled."""

import ast
from pathlib import Path
import pytest
from consilient import events


def test_embedding_fit_is_training_and_frozen_embedding_is_not_a_model_change() -> None:
    assert events.mutation_class_for("embedding_fit") == "data_driven_training"
    assert events.mutation_class_for("optimiser") == "data_driven_training"
    assert events.mutation_class_for("closed_form") == "data_driven_training"
    assert events.mutation_class_for("direct_edit") == "non_data_driven_state_change"
    assert events.mutation_class_for("frozen_embedding") is None
    assert events.mutation_class_for("embedding_inference") is None
    with pytest.raises(events.EventError, match="procedure"):
        events.mutation_class_for("retrieval")


def test_unit_imports_no_trainer_changes_no_model_bytes_and_cannot_activate() -> None:
    source_path = (
        Path(__file__).resolve().parents[1] / "src" / "consilient" / "events.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    forbidden = {
        "torch",
        "transformers",
        "peft",
        "trl",
        "accelerate",
        "openai",
        "anthropic",
        "huggingface_hub",
        "datasets",
        "sklearn",
        "subprocess",
        "socket",
        "http",
        "urllib",
        "requests",
    }
    assert not (imported & forbidden), sorted(imported & forbidden)
    dumped = ast.dump(tree)
    assert "select_capabilities" not in dumped
    assert "getattr" not in dumped
    assert "from .capabilities" not in source
    assert "from consilient.capabilities" not in source
    assert "MODEL_CHANGE_KIND" in dumped
    assert events.MODEL_CHANGE_KIND not in {
        events.CAPABILITY_VERSIONED_KIND,
        events.RECORD_CAPTURED_KIND,
    }
