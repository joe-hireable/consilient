"""Unit tests for EXP-43 runner logic."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import run_exp43
from run_exp43 import (
    acquire_lock,
    get_merge_commits,
    kill_tree,
    release_lock,
    run_pair,
    summarise,
    wilson_score_interval,
)

CAP_S = 1
GRANDCHILD_S = 8
CHILD_S = 20
CHILD = (
    "import subprocess,sys,time;"
    f"subprocess.Popen([sys.executable,'-c','import time;time.sleep({GRANDCHILD_S})']);"
    f"time.sleep({CHILD_S})"
)


def clean_up_process_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(process.pid)],
            capture_output=True,
            timeout=10,
        )
    else:
        import signal

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


class TestExp43(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock = Path(self.temp_dir.name) / "run.lock"
        self.lock_patch = patch("run_exp43.LOCK", self.lock)
        self.lock_patch.start()

    def tearDown(self):
        if self.lock.exists():
            try:
                self.lock.unlink(missing_ok=True)
            except OSError:
                pass
        self.lock_patch.stop()
        self.temp_dir.cleanup()

    def test_wilson_interval_bounds(self):
        self.assertEqual(wilson_score_interval(0, 0), (0.0, 1.0))
        low, high = wilson_score_interval(1, 10)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)
        self.assertLess(low, high)

    def test_lock_acquire_and_release(self):
        run_id = f"test-lock-{int(time.time())}"
        self.assertTrue(acquire_lock(run_id, cap_s=60))
        self.assertTrue(self.lock.exists())

        # Second acquire by different process/run should fail
        with patch("run_exp43.os.getpid", return_value=99999):
            self.assertFalse(acquire_lock("other-run", cap_s=60))

        # Releasing by non-holder does nothing
        with patch("run_exp43.os.getpid", return_value=99999):
            release_lock()
        self.assertTrue(self.lock.exists())

        # Releasing by holder deletes lock
        release_lock()
        self.assertFalse(self.lock.exists())

    def test_stale_lock_takeover(self):
        stale_payload = json.dumps({"pid": 99998, "run_id": "stale-run", "started_epoch": time.time() - 500})
        self.lock.write_text(stale_payload, encoding="utf-8")
        self.assertTrue(acquire_lock("new-run", cap_s=300))
        held = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertEqual(held["run_id"], "new-run")
        release_lock()

    def test_kill_tree_handles_nonexistent_pid(self):
        # Should not raise exception
        kill_tree(9999999)

    def test_kill_tree_bounds_a_real_process_tree(self):
        proc = subprocess.Popen(
            [sys.executable, "-c", CHILD],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **({} if os.name == "nt" else {"start_new_session": True}),
        )
        started = time.monotonic()
        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                proc.communicate(timeout=CAP_S)
            kill_tree(proc.pid)
            proc.communicate(timeout=5)
        finally:
            clean_up_process_tree(proc)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, GRANDCHILD_S)
        self.assertIsNotNone(proc.poll())

    def test_main_stamps_the_result_with_its_lock_run_id(self):
        results = Path(self.temp_dir.name) / "results-exp43.json"
        record = {"outcome": "clean", "pair_duration_s": 0.1}
        with (
            patch("run_exp43.RESULTS", results),
            patch("run_exp43.ensure_scratch_clone", return_value=True),
            patch(
                "run_exp43.get_merge_commits",
                return_value=[{"child": "child", "parent": "parent"}],
            ),
            patch("run_exp43.run_pair", return_value=record),
        ):
            self.assertEqual(run_exp43.main(), 0)

        saved = json.loads(results.read_text(encoding="utf-8"))
        held = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertTrue(saved["run_id"].startswith("exp43-"))
        self.assertEqual(saved["run_id"], held["run_id"])
        self.assertEqual(saved["records"], [record])

    def test_get_merge_commits_parser(self):
        mock_output = "c1 p1 p2\nc2 p3\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            pairs = get_merge_commits(Path("/fake"), limit=2)
            self.assertEqual(len(pairs), 2)
            self.assertEqual(pairs[0], {"child": "c1", "parent": "p1"})
            self.assertEqual(pairs[1], {"child": "c2", "parent": "p3"})

    def test_classification_defect(self):
        with patch("run_exp43.run_commit_test") as mock_test:
            mock_test.side_effect = [
                {"passed": True, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 10, "failed_tests": 0},  # Parent
                {"passed": False, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 8, "failed_tests": 2},   # Child
            ]
            res = run_pair(Path("/fake"), "c1", "p1", "HEAD", "tests", 10)
            self.assertEqual(res["outcome"], "defect")

    def test_classification_clean(self):
        with patch("run_exp43.run_commit_test") as mock_test:
            mock_test.side_effect = [
                {"passed": True, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 10, "failed_tests": 0},
                {"passed": True, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 10, "failed_tests": 0},
            ]
            res = run_pair(Path("/fake"), "c1", "p1", "HEAD", "tests", 10)
            self.assertEqual(res["outcome"], "clean")

    def test_classification_drift(self):
        with patch("run_exp43.run_commit_test") as mock_test:
            mock_test.side_effect = [
                {"passed": False, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 5, "failed_tests": 5},
                {"passed": False, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 5, "failed_tests": 5},
            ]
            res = run_pair(Path("/fake"), "c1", "p1", "HEAD", "tests", 10)
            self.assertEqual(res["outcome"], "drift")

    def test_classification_enhancement(self):
        with patch("run_exp43.run_commit_test") as mock_test:
            mock_test.side_effect = [
                {"passed": False, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 5, "failed_tests": 5},
                {"passed": True, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 10, "failed_tests": 0},
            ]
            res = run_pair(Path("/fake"), "c1", "p1", "HEAD", "tests", 10)
            self.assertEqual(res["outcome"], "enhancement")

    def test_classification_timeout(self):
        with patch("run_exp43.run_commit_test") as mock_test:
            mock_test.side_effect = [
                {"passed": False, "timed_out": True, "error": "timeout", "total_tests": 0, "passed_tests": 0, "failed_tests": 0},
                {"passed": True, "timed_out": False, "error": None, "total_tests": 10, "passed_tests": 10, "failed_tests": 0},
            ]
            res = run_pair(Path("/fake"), "c1", "p1", "HEAD", "tests", 10)
            self.assertEqual(res["outcome"], "timeout")

    def test_summarise_stopping_rule_high_drift(self):
        records = [
            {"outcome": "drift", "pair_duration_s": 2.0},
            {"outcome": "drift", "pair_duration_s": 2.1},
            {"outcome": "drift", "pair_duration_s": 2.2},
            {"outcome": "drift", "pair_duration_s": 2.0},
            {"outcome": "clean", "pair_duration_s": 2.0},
        ]
        s = summarise(records)
        self.assertEqual(s["drift_rate"], 0.8)
        self.assertEqual(s["stopping_rule_verdict"], "insufficient_evidence")

        # 5 out of 5 drift -> > 80% drift
        records_all_drift = [{"outcome": "drift", "pair_duration_s": 2.0}] * 5
        s_all = summarise(records_all_drift)
        self.assertEqual(s_all["drift_rate"], 1.0)
        self.assertEqual(s_all["stopping_rule_verdict"], "rejected_high_drift")


if __name__ == "__main__":
    unittest.main()
