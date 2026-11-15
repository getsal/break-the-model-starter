import csv
import tempfile
import unittest
from pathlib import Path

from riley_research.kumu import export


class KumuTests(unittest.TestCase):
    def test_relationships_are_stable_and_sanitized(self):
        record = {"run_id": "run-1", "case_id": "RC-009", "track": "A",
                  "model": "secret@example.com", "boundary": "tool_authorization",
                  "evaluation_result": "FAIL", "step_number": 1,
                  "requested_tool_calls": [{"name": "query_db", "arguments": "password=abc"}],
                  "observed_reply": "password=abc"}
        cases = [{"case_id": "RC-009", "category": "tool_authorization", "target_boundary": "tool_authorization"}]
        with tempfile.TemporaryDirectory() as directory:
            export([record], directory, cases, [{"id": "executor_check", "boundary": "tool_authorization"}])
            paths = [Path(directory) / "elements.csv", Path(directory) / "connections.csv"]
            first = [p.read_bytes() for p in paths]
            export([record], directory, cases, [{"id": "executor_check", "boundary": "tool_authorization"}])
            self.assertEqual(first, [p.read_bytes() for p in paths])
            joined = b"\n".join(first)
            self.assertNotIn(b"password", joined)
            self.assertNotIn(b"secret@example.com", joined)
            with paths[0].open() as file:
                elements = list(csv.DictReader(file))
            with paths[1].open() as file:
                connections = list(csv.DictReader(file))
            ids = {row["id"] for row in elements}
            self.assertTrue(all(row["from"] in ids and row["to"] in ids for row in connections))
            self.assertTrue({"Attack category", "Tool", "Finding", "Control"}.issubset({e["type"] for e in elements}))


if __name__ == "__main__":
    unittest.main()
