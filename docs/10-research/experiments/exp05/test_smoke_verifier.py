"""The EXP-05 verifier enforces both tests and the ticket's file-scope invariant."""

from run_exp05 import make_repo, verify


if __name__ == "__main__":
    repo = make_repo()
    with (repo / "util.py").open("a", encoding="utf-8") as handle:
        handle.write("\ndef add(a, b):\n    return a + b\n")
    accepted = verify(repo)
    assert accepted["passed"], accepted

    (repo / "test_runner.py").write_text("def test_duplicate():\n    assert True\n")
    rejected = verify(repo)
    assert not rejected["passed"], rejected
    assert rejected["unexpected_files"] == ["test_runner.py"]
    print("smoke verifier rejects functionally passing out-of-scope artefacts")
