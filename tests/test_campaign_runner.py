import tempfile
import unittest
import json
import socket
import ssl
import sqlite3
import urllib.error
from pathlib import Path
from unittest.mock import patch

from riley_research.campaign_runner import BudgetLedger, summarize_tool_call, validate_manifest, error_details, run_batch
from riley_research.evidence import EvidenceStore


class CampaignRunnerTests(unittest.TestCase):
    def test_error_classification_and_redaction(self):
        cases = [(socket.timeout("timed out"), "TIMEOUT"),
                 (socket.gaierror(-2, "lookup failed"), "DNS_ERROR"),
                 (ssl.SSLError("bad certificate"), "TLS_ERROR"),
                 (ConnectionResetError(54, "reset"), "CONNECTION_ERROR"),
                 (ValueError("api_key=secret"), "UNKNOWN_ERROR")]
        for reason, expected in cases:
            details = error_details(urllib.error.URLError(reason))
            self.assertEqual(details["classification"], expected)
            self.assertNotIn("secret", json.dumps(details))
            self.assertEqual(details["timeout_seconds"], 60)
        details = error_details(urllib.error.HTTPError("https://example.invalid/?token=secret", 429, "secret", {}, None))
        self.assertEqual((details["classification"], details["http_status"]), ("HTTP_ERROR", 429))
        self.assertNotIn("secret", json.dumps(details))

    def test_simulated_batch_stops_and_continues_safely(self):
        from riley_research.track_c_run import HOST
        base = {"batch_id": "b", "case_id": "TC-003", "case_hash": "abc", "prompt": "synthetic",
                "model": "Qwen/Qwen3-30B-A3B-Instruct-2507", "step_number": 1, "repetition": 1,
                "variant": "v1", "target_boundary": "model_instruction", "expected_authorized_behavior": "none"}
        trials = [{**base, "trial_id": str(i), "conversation_group": str(i)} for i in range(4)]
        scenarios = [([urllib.error.URLError(socket.timeout()), {"turn_id": "ok"}, urllib.error.URLError(ConnectionResetError()), {"turn_id": "ok2"}], 4),
                     ([urllib.error.URLError(socket.timeout()), urllib.error.URLError(socket.timeout()), {"turn_id": "unused"}], 2),
                     ([urllib.error.HTTPError("https://example.invalid", 401, "no", {}, None)], 1),
                     ([urllib.error.HTTPError("https://example.invalid", 403, "no", {}, None)], 1),
                     ([urllib.error.HTTPError("https://example.invalid", 429, "no", {}, None)], 1)]
        for outcomes, expected in scenarios:
            with self.subTest(expected=expected, outcomes=outcomes), tempfile.TemporaryDirectory() as d:
                manifest = Path(d) / "manifest.json"
                manifest.write_text(json.dumps(trials))
                ledger, store = Path(d) / "ledger.db", Path(d) / "evidence.db"
                with patch.dict("os.environ", {"API_URL": "https://" + HOST, "API_KEY": "test"}), \
                     patch("riley_research.campaign_runner.load_dotenv"), \
                     patch("riley_research.campaign_runner.time.sleep"), \
                     patch("riley_research.campaign_runner.RileyAdapter") as adapter:
                    adapter.return_value.chat.side_effect = outcomes
                    result = run_batch(manifest, ledger, store)
                    self.assertEqual(adapter.return_value.chat.call_count, expected)
                self.assertEqual(result["completed"], expected)
                evidence = EvidenceStore(store)
                self.assertTrue(evidence.verify())
                self.assertEqual(evidence.list()[0]["evaluation_result"], "ERROR")
                self.assertIn("duration_ms", evidence.list()[0]["error_details"])
                with self.assertRaises(sqlite3.IntegrityError):
                    BudgetLedger(ledger).reserve(trials[0])

    def test_error_streak_is_preserved_across_runs(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = BudgetLedger(Path(d) / "ledger")
            trial = {"trial_id": "a", "batch_id": "b", "model": "Qwen/Qwen3-30B-A3B-Instruct-2507"}
            ledger.reserve(trial)
            ledger.complete("a", "error:URLError")
            self.assertEqual(BudgetLedger(ledger.path).trailing_errors(), 1)
            ledger.reserve({**trial, "trial_id": "b"})
            ledger.complete("b", "error:URLError")
            self.assertEqual(BudgetLedger(ledger.path).trailing_errors(), 2)

    def test_conversation_after_error_is_skipped(self):
        from riley_research.track_c_run import HOST
        base = {"batch_id": "b", "case_id": "TC-005", "case_hash": "abc", "prompt": "synthetic",
                "model": "Qwen/Qwen3-30B-A3B-Instruct-2507", "step_number": 1, "repetition": 1,
                "variant": "v1", "target_boundary": "model_instruction", "expected_authorized_behavior": "none"}
        trials = [{**base, "trial_id": "a", "conversation_group": "g"},
                  {**base, "trial_id": "b", "conversation_group": "g", "step_number": 2},
                  {**base, "trial_id": "c", "conversation_group": "other"}]
        with tempfile.TemporaryDirectory() as d:
            manifest = Path(d) / "manifest.json"
            manifest.write_text(json.dumps(trials))
            with patch.dict("os.environ", {"API_URL": "https://" + HOST, "API_KEY": "test"}), \
                 patch("riley_research.campaign_runner.load_dotenv"), patch("riley_research.campaign_runner.time.sleep"), \
                 patch("riley_research.campaign_runner.RileyAdapter") as adapter:
                adapter.return_value.chat.side_effect = [urllib.error.URLError(socket.timeout()), {"turn_id": "ok"}]
                result = run_batch(manifest, Path(d) / "ledger", Path(d) / "evidence")
            self.assertEqual(result["post_requests"], 2)
            self.assertEqual(adapter.return_value.chat.call_count, 2)

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
