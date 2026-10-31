"""Isolated in-memory tests for the optional SQLite catalog adapter."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from web_v1_sqlite_catalog import SqliteLessonCatalog

COLS = {
    "lesson_id": "id", "year": "year", "subject_code": "subject",
    "unit_title": "unit", "lesson_title": "title"
}


class SqliteCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "CREATE TABLE lessons (id TEXT, year INTEGER, subject TEXT, unit TEXT, title TEXT)"
            )
            conn.executemany(
                "INSERT INTO lessons VALUES (?, ?, ?, ?, ?)",
                [("L2", 3, "ENGLISH", "Unit 2", "Lesson 2"),
                 ("L1", 3, "ENGLISH", "Unit 1", "Lesson 1"),
                 ("L3", 4, "ENGLISH", "Unit 1", "Lesson 3")]
            )

    def tearDown(self):
        self.tmp.cleanup()

    def test_filters_and_orders(self):
        catalog = SqliteLessonCatalog(self.db, table="lessons", columns=COLS)
        lessons = catalog.list_lessons(year=3, subject_code="ENGLISH")
        self.assertEqual([x.lesson_id for x in lessons], ["L1", "L2"])

    def test_rejects_untrusted_identifiers(self):
        with self.assertRaises(ValueError):
            SqliteLessonCatalog(self.db, table="lessons; DROP TABLE lessons", columns=COLS)

    def test_missing_database_is_not_created(self):
        missing = self.db.parent / "missing.db"
        catalog = SqliteLessonCatalog(missing, table="lessons", columns=COLS)
        with self.assertRaises(FileNotFoundError):
            catalog.list_lessons(year=3, subject_code="ENGLISH")
        self.assertFalse(missing.exists())

    def test_rejects_invalid_filter(self):
        catalog = SqliteLessonCatalog(self.db, table="lessons", columns=COLS)
        with self.assertRaises(ValueError):
            catalog.list_lessons(year=3, subject_code="ENGLISH' OR 1=1--")


if __name__ == "__main__":
    unittest.main()
