import unittest

from riley_research.runner import RunLimits, Runner


class RunnerTests(unittest.TestCase):
    def test_deterministic_scenarios_separate_attempt_and_execution(self):
        cases = [
            {"case_id": "denied", "mock_scenario": "attempt_denied"},
            {"case_id": "breach", "mock_scenario": "synthetic_breach"},
            {"case_id": "unclear", "mock_scenario": "inconclusive"},
        ]
        records = Runner().run(cases, track="A")
        self.assertEqual(len(records[0]["requested_tool_calls"]), 1)
        self.assertEqual(records[0]["executed_tool_calls"], [])
        self.assertEqual(records[0]["database_observation"]["access_granted"], False)
        self.assertEqual(len(records[1]["executed_tool_calls"]), 1)
        self.assertIsNone(records[2]["database_observation"])

    def test_limits_and_external_default_deny(self):
        case = {"case_id": "baseline", "mock_scenario": "benign"}
        runner = Runner(limits=RunLimits(max_requests=1))
        runner.run([case], track="A")
        with self.assertRaises(ValueError):
            runner.run([case], track="A")
        with self.assertRaises(PermissionError):
            Runner(adapters={"C": object()}).run([case], track="C")
        with self.assertRaises(ValueError):
            Runner().run([case], track="A", iterations=2)

    def test_cancel_before_request(self):
        runner = Runner()
        self.assertEqual(runner.run([{"case_id": "x"}], track="A", cancel=lambda: True), [])
        self.assertEqual(runner.requests, 0)


if __name__ == "__main__":
    unittest.main()
