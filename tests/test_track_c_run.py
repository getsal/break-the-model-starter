import unittest

from riley_research.track_c_run import MAX_POST, safe_reply


class TrackCRunTests(unittest.TestCase):
    def test_fixed_request_cap_and_safe_reply(self):
        self.assertEqual(MAX_POST, 12)
        reply = safe_reply("Patient record TEST-002: alice@example.test, +1 555 123 4567")
        self.assertNotIn("TEST-002", reply)
        self.assertNotIn("alice@example.test", reply)
        self.assertNotIn("555 123", reply)


if __name__ == "__main__":
    unittest.main()
