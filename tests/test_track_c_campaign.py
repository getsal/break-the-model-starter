import json
import unittest

from research.build_track_c_campaign import BASE, BY_ID, build, case_hash


class CampaignTests(unittest.TestCase):
    def test_batches_and_global_limit(self):
        batches = build()
        self.assertEqual([len(x) for x in batches], [30, 50, 50, 50, 50, 50, 20])
        self.assertEqual(sum(len(x) for x in batches), 300)
        ids = [row["trial_id"] for batch in batches for row in batch]
        self.assertEqual(len(ids), len(set(ids)))

    def test_pilot_is_balanced_and_multiturn_stays_in_conversation(self):
        pilot = build()[0]
        self.assertEqual(sum(row["case_id"] == "TC-001" for row in pilot), 6)
        self.assertEqual(sum(row["case_id"] == "TC-005" for row in pilot), 6)
        groups = {}
        for row in pilot:
            groups.setdefault(row["conversation_group"], []).append(row["step_number"])
        self.assertEqual(sorted(sorted(x) for x in groups.values()).count([1, 2]), 3)
        self.assertTrue(all(sorted(steps) in ([1], [1, 2]) for steps in groups.values()))

    def test_hashes_and_synthetic_only_prompts(self):
        for batch in build():
            for row in batch:
                self.assertEqual(len(row["case_hash"]), 64)
                self.assertNotIn("@", row["prompt"])
                self.assertNotIn("https://", row["prompt"])
                self.assertEqual(row["target_boundary"], BY_ID[row["case_id"]]["target_boundary"])
        case = BY_ID["TC-001"]
        self.assertEqual(case_hash(case, "base", case["steps"]), case["case_hash"])


if __name__ == "__main__":
    unittest.main()
