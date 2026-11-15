import tempfile
import unittest
from pathlib import Path

from riley_research.evidence import EvidenceStore, evaluate, sanitize


class EvidenceTests(unittest.TestCase):
    def test_boundary_evidence_is_conservative(self):
        result = evaluate({"boundary": "tool_authorization", "failure_observed": True,
                           "requested_tool_calls": [{"name": "query_db"}]})
        self.assertEqual(result["evaluation_result"], "INCONCLUSIVE")
        result = evaluate({"boundary": "database_authorization", "failure_observed": True,
                           "observed_reply": "I accessed records"})
        self.assertEqual(result["evaluation_result"], "INCONCLUSIVE")

    def test_store_sanitizes_and_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceStore(Path(directory) / "evidence.sqlite")
            record = store.append({"run_id": "r1", "case_id": "c1", "case_version": "1",
                                   "case_hash": "abc", "track": "A", "evidence_source": "mock",
                                   "evidence_status": "VERIFIED", "evaluation_result": "PASS",
                                   "observed_reply": "Bearer topsecret jane@example.org",
                                   "requested_tool_calls": [{"team_token": "abc"}]})
            self.assertNotIn("topsecret", str(record))
            self.assertNotIn("jane@example.org", str(store.list()))
            self.assertEqual(store.list()[0]["model"], None)
            self.assertTrue(store.verify())
            with self.assertRaises(Exception):
                store.append(record)

    def test_sanitizer_nested(self):
        self.assertEqual(sanitize({"authorization": "x", "nested": ["api_key=abc"]}),
                         {"authorization": "[REDACTED]", "nested": ["[REDACTED]"]})


if __name__ == "__main__":
    unittest.main()
