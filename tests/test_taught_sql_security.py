"""Static security gate for staging-only SQL. Run: python -m unittest tests.test_taught_sql_security"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "rph_hari_ini" / "sql"


class SQLSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = (ROOT / "001_taught_progress_staging_review_only.sql").read_text()
        cls.rpc = (ROOT / "002_atomic_confirm_staging_review_only.sql").read_text()
        cls.rollback_test = (ROOT / "003_atomic_confirm_disposable_db_tests.sql").read_text()

    def test_separate_tables(self):
        self.assertIn("create table if not exists public.rph_taught_progress", self.schema)
        self.assertIn("create table if not exists public.rph_taught_events", self.schema)

    def test_school_year_in_keys(self):
        self.assertIn("primary key (telegram_user_id, school_year, class_key, subject_key)", self.schema)

    def test_rls_enabled(self):
        for table in ("rph_taught_progress", "rph_taught_events"):
            self.assertIn(f"alter table public.{table} enable row level security", self.schema)

    def test_no_public_grants(self):
        self.assertNotIn("grant execute", self.rpc.lower())
        self.assertIn("revoke all on function", self.rpc.lower())

    def test_transaction_lock(self):
        self.assertIn("for update;", self.rpc.lower())

    def test_idempotency_key(self):
        self.assertIn("session_instance_id)", self.schema)
        self.assertIn("unique (telegram_user_id, school_year, class_key, subject_key, lesson_sequence)", self.schema)

    def test_no_legacy_mutation(self):
        for script in (self.schema, self.rpc, self.rollback_test):
            self.assertNotIn("update public.rph_progress", script.lower())
            self.assertNotIn("delete from public.rph_generation_history", script.lower())

    def test_test_rollback(self):
        self.assertTrue(self.rollback_test.strip().lower().endswith("rollback;"))

    def test_no_unsafe_definer(self):
        self.assertIn("security invoker", self.rpc.lower())
        self.assertNotIn("security definer", self.rpc.lower().replace("-- this function is intentionally not security definer.", ""))


if __name__ == "__main__":
    unittest.main()
