import unittest

from riley_research.local import VARIANTS, query_db, synthetic_db
from riley_research.remote import RileyAdapter


class LocalBoundaryTests(unittest.TestCase):
    def test_variant_decisions_are_distinct(self):
        for name, expected in (("A", "ok"), ("B", "rejected"), ("C", "rejected"), ("D", "rejected")):
            db = synthetic_db()
            try:
                requested, executed, result = query_db(db, {"scope": "all"}, VARIANTS[name])
                self.assertEqual(result["status"], expected)
                self.assertEqual(bool(executed), name == "A")
                self.assertEqual(requested["arguments"]["scope"], "all")
            finally:
                db.close()

    def test_remote_denied_by_default(self):
        with self.assertRaises(PermissionError):
            RileyAdapter(endpoint="https://example.test", approved=False, allowed_host="example.test",
                         max_requests=1, min_interval_seconds=1, participant="synthetic", team_token="",
                         api_key="", model="model")

    def test_database_variants_use_trusted_role(self):
        db = synthetic_db()
        try:
            _, _, broad = query_db(db, {"scope": "all", "role": "staff"}, VARIANTS["B"])
            self.assertEqual(broad["status"], "rejected")
            _, _, least = query_db(db, {"scope": "all"}, VARIANTS["C"], trusted_role="staff")
            self.assertEqual(least["status"], "denied")
            _, _, rows = query_db(db, {"scope": "all"}, VARIANTS["D"], trusted_role="staff")
            self.assertEqual([r["id"] for r in rows["rows"]], ["P-001"])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
