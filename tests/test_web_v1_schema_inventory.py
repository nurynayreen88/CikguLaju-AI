"""Isolated tests for the read-only SQLite schema inventory."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tools.inspect_web_v1_sqlite_schema import inspect_schema


class WebV1SchemaInspectionTests(unittest.TestCase):
    def test_schema_only_no_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "fixture.db"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE lesson_data (id INTEGER, title TEXT)")
                conn.execute("INSERT INTO lesson_data VALUES (1, 'secret RPH body')")
            schema = inspect_schema(db)
            self.assertEqual(schema[0]["table"], "lesson_data")
            self.assertEqual([c["name"] for c in schema[0]["columns"]], ["id", "title"])
            self.assertNotIn("secret RPH body", repr(schema))

    def test_missing_file_fails_without_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "missing.db"
            with self.assertRaises(FileNotFoundError):
                inspect_schema(db)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
