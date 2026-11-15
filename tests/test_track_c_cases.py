import json
import unittest
from pathlib import Path

from research.build_track_c_cases import content_hash


class TrackCCaseTests(unittest.TestCase):
    def test_identity_and_budget(self):
        path = Path(__file__).resolve().parents[1] / "research" / "track_c_cases.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 8)
        self.assertEqual(sum(len(case["steps"]) for case in cases), 9)
        self.assertEqual(len({case["case_id"] for case in cases}), 8)
        self.assertTrue(all(case["case_hash"] == content_hash(case) for case in cases))
        self.assertTrue(all(case["case_version"] == 1 for case in cases))


if __name__ == "__main__":
    unittest.main()
