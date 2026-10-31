"""Unit tests for verified curriculum topic adapter; no production DB access."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from web_v1_verified_topics import VerifiedTopicCatalog


class VerifiedTopicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "curriculum.db"
        with sqlite3.connect(self.path) as con:
            con.execute("""CREATE TABLE curriculum_topics (
                id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                topic TEXT, subtopic TEXT)""")
            con.executemany(
                "INSERT INTO curriculum_topics VALUES (?, ?, ?, ?, ?)",
                [(2, "Tahun 3", "Bahasa Inggeris", "Unit B", ""),
                 (1, "Tahun 3", "Bahasa Inggeris", "Unit A", "Speaking"),
                 (3, "Tahun 4", "Bahasa Inggeris", "Unit C", ""),
                 (4, "Tahun 3", "Sains", "Haiwan", "")],
            )

    def tearDown(self):
        self.temp.cleanup()

    def test_filters_real_schema(self):
        rows = VerifiedTopicCatalog(self.path).list_topics(year=3, subject_code="ENGLISH")
        self.assertEqual([r["topic"] for r in rows], ["Unit A", "Unit B"])
        self.assertEqual(rows[0]["subtopic"], "Speaking")

    def test_rejects_bad_input(self):
        cat = VerifiedTopicCatalog(self.path)
        for year, subject in [(0, "ENGLISH"), (True, "ENGLISH"), (3, "ENGLISH' OR 1=1--")]:
            with self.assertRaises(ValueError):
                cat.list_topics(year=year, subject_code=subject)

    def test_missing_file_not_created(self):
        path = self.path.parent / "missing.db"
        with self.assertRaises(FileNotFoundError):
            VerifiedTopicCatalog(path).list_topics(year=3, subject_code="ENGLISH")
        self.assertFalse(path.exists())

    def test_read_only(self):
        cat = VerifiedTopicCatalog(self.path)
        cat.list_topics(year=3, subject_code="ENGLISH")
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM curriculum_topics").fetchone()[0], 4)


if __name__ == "__main__":
    unittest.main()
