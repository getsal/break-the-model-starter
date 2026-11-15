import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from riley_research.campaign_runner import BudgetLedger, summarize_tool_call, validate_manifest


class CampaignRunnerTests(unittest.TestCase):
    def test_persistent_global_request_cap(self):
        with tempfile.TemporaryDirectory() as directory, patch("riley_research.campaign_runner.MAX_POST", 2):
            path = Path(directory) / "ledger.sqlite"
            for n in range(2):
                ledger = BudgetLedger(path)
                ledger.reserve({"trial_id": f"t{n}", "batch_id": "b", "model": "Qwen/Qwen3-30B-A3B-Instruct-2507"})
            with self.assertRaises(RuntimeError):
                BudgetLedger(path).reserve({"trial_id": "t2", "batch_id": "b", "model": "Qwen/Qwen3-30B-A3B-Instruct-2507"})
            self.assertEqual(BudgetLedger(path).summary()["post_requests"], 2)

    def test_manifest_rejects_duplicate_and_unknown_model(self):
        base = {"trial_id": "x", "batch_id": "b", "case_id": "TC-001", "case_hash": "abc",
                "prompt": "synthetic", "model": "Qwen/Qwen3-30B-A3B-Instruct-2507",
                "conversation_group": "g", "step_number": 1, "repetition": 1,
                "variant": "base", "target_boundary": "tool_invocation",
                "expected_authorized_behavior": "none"}
        with self.assertRaises(ValueError):
            validate_manifest([base, base])
        with self.assertRaises(ValueError):
            validate_manifest([{**base, "model": "unknown"}])

    def test_tool_argument_summary_never_keeps_values(self):
        summary = summarize_tool_call({"name": "query_db", "args": {"sql": "SELECT * FROM private_patients"}})
        self.assertTrue(summary["mentions_restricted_data"])
        self.assertFalse(summary["result_field_present"])
        self.assertNotIn("private_patients", str(summary))


if __name__ == "__main__":
    unittest.main()
