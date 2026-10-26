import sqlite3
import unittest
from rph_trial_quota import ensure_schema, reserve, complete, remaining, QuotaDenied

class TrialQuotaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        ensure_schema(self.db)

    def tearDown(self):
        self.db.close()

    def test_five_only(self):
        for i in range(5):
            self.assertEqual(reserve(self.db, 10, f"job-{i}"), "reserved")
            complete(self.db, f"job-{i}", delivered=True)
        self.assertEqual(remaining(self.db, 10), 0)
        with self.assertRaises(QuotaDenied):
            reserve(self.db, 10, "job-6")

    def test_failed_job_refunds_once(self):
        reserve(self.db, 10, "failed")
        complete(self.db, "failed", delivered=False)
        complete(self.db, "failed", delivered=False)
        self.assertEqual(remaining(self.db, 10), 5)

    def test_duplicate_not_double_charged(self):
        reserve(self.db, 10, "same")
        reserve(self.db, 10, "same")
        self.assertEqual(remaining(self.db, 10), 4)

    def test_pioneer_does_not_consume(self):
        self.assertIsNone(reserve(self.db, 10, "pioneer", has_full_access=True))
        self.assertEqual(remaining(self.db, 10), 5)

if __name__ == "__main__":
    unittest.main()
