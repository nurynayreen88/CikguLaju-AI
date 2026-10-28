"""Static safety checks for the staged SQL reservation contract.

Run: python -m unittest tests.test_rph_trial_reservation_contract
These checks do NOT replace database concurrency or Telegram integration tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql" / "rph_trial_reservation_staging.sql"


class ReservationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8").lower()

    def test_three_operations_present(self):
        for name in ("reserve", "commit", "release"):
            with self.subTest(name=name):
                self.assertIn(f"public.cikgulaju_{name}_rph_trial", self.sql)

    def test_serialization_on_user_balance(self):
        self.assertGreaterEqual(self.sql.count("for update"), 3)

    def test_durable_request_identity(self):
        self.assertIn("request_id text primary key", self.sql)
        self.assertIn("reservation owner mismatch", self.sql)

    def test_only_commit_debits(self):
        commit = self.sql.split("create or replace function public.cikgulaju_commit_rph_trial", 1)[1]
        release = commit.split("create or replace function public.cikgulaju_release_rph_trial", 1)[1]
        self.assertIn("trial_remaining=trial_remaining-1", commit.split("create or replace function", 1)[0])
        self.assertNotIn("trial_remaining=trial_remaining-1", release)

    def test_rls_and_privileged_access(self):
        self.assertIn("enable row level security", self.sql)
        self.assertIn("to service_role", self.sql)
        self.assertIn("from public,anon,authenticated", self.sql)

    def test_no_destructive_schema_change(self):
        for phrase in ("drop table", "truncate ", "delete from public.cikgulaju_users"):
            self.assertNotIn(phrase, self.sql)


if __name__ == "__main__":
    unittest.main()
