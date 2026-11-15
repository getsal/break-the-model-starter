import tempfile
import unittest
from pathlib import Path

from riley_research.dashboard import render
from riley_research.kumu import export


class AnalysisTests(unittest.TestCase):
    def test_dashboard_escapes_and_separates_tracks(self):
        records = [{"run_id": "r1", "case_id": "c1", "track": "A", "model": "mock", "evaluation_result": "PASS", "observed_reply": "<script>"},
                   {"run_id": "r2", "case_id": "c2", "track": "B", "model": "local", "evaluation_result": "INCONCLUSIVE"}]
        page = render(records, "A")
        self.assertIn("1 trials", page)
        self.assertNotIn("c2</td>", page)

    def test_kumu_references_existing_elements(self):
        with tempfile.TemporaryDirectory() as directory:
            export([{"run_id": "r", "case_id": "c", "track": "A", "model": "mock", "boundary": "tool"}], directory)
            import csv
            with (Path(directory) / "elements.csv").open() as element_file, (Path(directory) / "connections.csv").open() as connection_file:
                elements = list(csv.DictReader(element_file))
                connections = list(csv.DictReader(connection_file))
            ids = {row["id"] for row in elements}
            self.assertTrue(all(row["from"] in ids and row["to"] in ids for row in connections))


if __name__ == "__main__":
    unittest.main()
