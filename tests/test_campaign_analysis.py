import unittest

from riley_research.campaign_analysis import batch_markdown, batch_summaries, variability_rows
from riley_research.dashboard import render


def trial(run, outcome, *, tool=False, actual=None, model="model-one", evidence="hash"):
    return {"track": "C", "run_id": run, "case_id": "TC-001", "case_hash": "case-hash",
            "model": model, "configuration": "batch:" + run, "evaluation_result": outcome,
            "requested_tool_calls": [{"name": "query_db"}] if tool else [],
            "executed_tool_calls": None, "observed_tool_results": None,
            "database_observation": None, "estimated_cost": 0.01,
            "actual_cost": actual, "evidence_hash": evidence, "turn_id": "turn"}


class CampaignAnalysisTests(unittest.TestCase):
    def test_batch_counts_cost_unknown_and_tool_boundary(self):
        rows = [trial("pilot", "PASS", tool=True, evidence="a" * 64),
                trial("pilot", "INCONCLUSIVE", evidence="b" * 64),
                trial("next", "ERROR", actual=0.02, evidence="c" * 64),
                {"track": "B", "run_id": "pilot", "evaluation_result": "FAIL"}]
        batches = batch_summaries(rows)
        self.assertEqual([b["batch_id"] for b in batches], ["next", "pilot"])
        pilot = batches[1]
        self.assertEqual(pilot["trial_count"], 2)
        self.assertEqual(pilot["outcomes"]["PASS"], 1)
        self.assertEqual(pilot["outcomes"]["INCONCLUSIVE"], 1)
        self.assertEqual(pilot["tool_call_report_rate"], "1/2")
        self.assertEqual(pilot["executor_result_trials"], 0)
        self.assertEqual(pilot["database_result_trials"], 0)
        self.assertEqual(pilot["estimated_cost_total"], "0.02")
        self.assertIsNone(pilot["actual_cost_total"])
        self.assertIn("unknown", batch_markdown(pilot))

    def test_repetition_variability_has_explicit_denominator(self):
        rows = [trial("pilot", "PASS", tool=True), trial("next", "INCONCLUSIVE")]
        variation = variability_rows(rows)
        self.assertEqual(variation[0]["trials"], 2)
        self.assertTrue(variation[0]["outcomes_vary"])
        self.assertTrue(variation[0]["tool_reports_vary"])
        self.assertEqual(variation[0]["tool_call_report_rate"], "1/2")
        page = render(rows, "C")
        self.assertIn("Track C batches", page)
        self.assertIn("Track C repeated prompt variability", page)
        self.assertIn("unknown", page)


if __name__ == "__main__":
    unittest.main()
