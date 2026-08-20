"""Unit tests for EXP-43 runner logic."""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from run_exp43 import (
    acquire_lock,
    release_lock,
    run_pair,
    summarise,
    wilson_score_interval,
    LOCK,
)


class TestExp43(unittest.TestCase):
    def tearDown(self):
        if LOCK.exists():
            try:
                LOCK.unlink(missing_ok=True)
            except OSError:
                pass

    def test_wilson_interval_bounds(self):
        self.assertEqual(wilson_score_interval(0, 0), (0.0, 1.0))
        low, high = wilson_score_interval(1, 10)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)
        self.assertLess(low, high)

    def test_lock_acquire_and_release(self):
        run_id = f"test-lock-{int(time.time())}"
        self.assertTrue(acquire_lock(run_id, cap_s=60))
        self.assertTrue(LOCK.exists())

        # Second acquire by different process/run should fail
        with patch("run_exp43.os.getpid", return_value=99999):
            self.assertFalse(acquire_lock("other-run", cap_s=60))

        # Releasing by non-holder does nothing
        with patch("run_exp43.os.getpid", return_value=99999):
            release_lock()
        self.assertTrue(LOCK.exists())

        # Releasing by holder deletes lock
        release_lock()
        self.assertFalse(LOCK.exists())

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
        self.assertEqual(s["stopping_verdict"] if "stopping_verdict" in s else s["stopping_rule_verdict"], "insufficient_evidence")

        # 5 out of 5 drift -> > 80% drift
        records_all_drift = [{"outcome": "drift", "pair_duration_s": 2.0}] * 5
        s_all = summarise(records_all_drift)
        self.assertEqual(s_all["drift_rate"], 1.0)
        self.assertEqual(s_all["stopping_rule_verdict"], "rejected_high_drift")


if __name__ == "__main__":
    unittest.main()
