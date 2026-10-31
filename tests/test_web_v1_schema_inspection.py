"""Tests for local read-only schema inspection."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tools.inspect_web_v1_sqlite_schema import inspect_schema


class InspectSchemaTests(unittest.TestCase):
    def test_reads_only_schema(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "sample.db"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE lessons (id INTEGER PRIMARY KEY, title TEXT)")
                conn.execute("INSERT INTO lessons(title) VALUES ('private lesson content')")
            inventory = inspect_schema(db)
            self.assertEqual(inventory[0]["table"], "lessons")
            self.assertEqual([x["name"] for x in inventory[0]["columns"]], ["id", "title"])
            self.assertNotIn("private lesson content", repr(inventory))
            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM lessons").fetchone()[0], 1)

    def test_missing_file_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "missing.db"
            with self.assertRaises(FileNotFoundError):
                inspect_schema(missing)
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
