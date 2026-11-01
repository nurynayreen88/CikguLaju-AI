import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.inspect_web_v1_account_schema import inspect_schema


class ReadOnlySchemaInspectorTests(unittest.TestCase):
    def test_lists_schema_without_reading_personal_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "sample.db"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE users (telegram_id INTEGER PRIMARY KEY, secret TEXT)")
                conn.execute("INSERT INTO users (telegram_id, secret) VALUES (123, 'private-example')")
            result = inspect_schema(db)
            self.assertEqual(result[0]["table"], "users")
            self.assertEqual([c["name"] for c in result[0]["columns"]], ["telegram_id", "secret"])
            self.assertNotIn("private-example", str(result))

    def test_missing_database_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "missing.db"
            with self.assertRaises(sqlite3.OperationalError):
                inspect_schema(db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
