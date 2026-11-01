import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from web_v1_sessions import issue_session_ticket
from web_v1_account_resolver import resolve_feature_access
from web_v1_sqlite_account_adapter import lookup_existing_sqlite_account

SECRET = "test-only-session-secret-with-at-least-32-chars"

class SQLiteAccountIntegrationTests(unittest.TestCase):
    def test_existing_account_can_access_rpt_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "accounts.db"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE accounts (telegram_id INTEGER PRIMARY KEY, lifetime INTEGER, credits INTEGER)")
                conn.execute("INSERT INTO accounts VALUES (123, 1, 4)")
            before = path.read_bytes()
            def lookup(uid):
                return lookup_existing_sqlite_account(path, uid, table="accounts",
                    id_column="telegram_id", lifetime_column="lifetime", credits_column="credits")
            ticket = issue_session_ticket(123, SECRET, now=1800000000)
            self.assertTrue(resolve_feature_access(ticket, SECRET, lookup, "rpt",
                now=1800000000, today=date(2026, 11, 1)))
            self.assertEqual(path.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()
