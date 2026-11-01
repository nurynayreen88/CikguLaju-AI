"""Tests for read-only schema inspection using a disposable SQLite fixture."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from web.audit_rph_schema import inspect_schema


class SchemaAuditTests(unittest.TestCase):
    def test_schema_only_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "sample.sqlite"
            with sqlite3.connect(db) as conn:
                conn.execute(
                    "CREATE TABLE lesson_rph "
                    "(id INTEGER PRIMARY KEY, content TEXT, approval TEXT)"
                )
                conn.execute(
                    "INSERT INTO lesson_rph(content, approval) VALUES (?, ?)",
                    ("PRIVATE EXAMPLE CONTENT", "draft"),
                )
            result = inspect_schema(str(db))
            self.assertEqual(result["integrity"], "ok")
            columns = result["tables"]["lesson_rph"]
            self.assertEqual([c["name"] for c in columns],
                             ["id", "content", "approval"])
            self.assertNotIn("PRIVATE EXAMPLE CONTENT", str(result))

    def test_missing_file_rejected(self):
        with self.assertRaises(FileNotFoundError):
            inspect_schema("/nonexistent/cikgulaju_snapshot.sqlite")


if __name__ == "__main__":
    unittest.main()
