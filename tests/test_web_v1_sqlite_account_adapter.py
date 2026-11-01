import sqlite3
import tempfile
import unittest
from pathlib import Path

from web_v1_sqlite_account_adapter import lookup_existing_sqlite_account


class SQLiteAccountAdapterTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "test.db"
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE accounts (telegram_id INTEGER PRIMARY KEY, lifetime INTEGER, vip TEXT, credits INTEGER)")
            conn.execute("INSERT INTO accounts VALUES (123, 1, NULL, 7)")

    def lookup(self, uid, **overrides):
        args = {"table": "accounts", "id_column": "telegram_id",
                "lifetime_column": "lifetime", "vip_column": "vip",
                "credits_column": "credits"}
        args.update(overrides)
        return lookup_existing_sqlite_account(self.path, uid, **args)

    def test_existing_account(self):
        result = self.lookup(123)
        self.assertEqual(result["telegram_user_id"], 123)
        self.assertTrue(result["rakan_pembangun"])
        self.assertEqual(result["free_remaining"], 7)

    def test_unknown_account_is_not_created(self):
        self.assertIsNone(self.lookup(999))
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM accounts").fetchone()[0], 1)

    def test_invalid_schema_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            self.lookup(123, table="accounts;DROP TABLE accounts")

    def test_invalid_lifetime_value_fails_closed(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE accounts SET lifetime = 2 WHERE telegram_id = 123")
        self.assertIsNone(self.lookup(123))

    def test_duplicate_column_mapping_is_rejected(self):
        with self.assertRaises(ValueError):
            self.lookup(123, credits_column="lifetime")

    def test_invalid_credit_balance_is_denied(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE accounts SET credits = 11 WHERE telegram_id = 123")
        self.assertIsNone(self.lookup(123))

    def test_null_credit_balance_is_denied_when_mapped(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE accounts SET credits = NULL WHERE telegram_id = 123")
        self.assertIsNone(self.lookup(123))

    def test_invalid_vip_date_is_denied(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE accounts SET vip = '31/12/2027' WHERE telegram_id = 123")
        self.assertIsNone(self.lookup(123))

    def test_valid_vip_date_is_preserved(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE accounts SET vip = '2027-12-31' WHERE telegram_id = 123")
        self.assertEqual(self.lookup(123)["vip_until"], "2027-12-31")

    def test_database_is_not_modified_by_lookup(self):
        before = self.path.read_bytes()
        self.lookup(123)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_database_not_created(self):
        missing = Path(self.folder.name) / "missing.db"
        with self.assertRaises(sqlite3.OperationalError):
            lookup_existing_sqlite_account(missing, 123, table="accounts", id_column="telegram_id")
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
