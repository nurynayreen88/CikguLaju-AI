"""Regression tests for verified PdP navigation completeness (isolated SQLite)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web_v1_verified_pdp import VerifiedPdpCatalog


class VerifiedPdpLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "catalog.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, sequence_no INTEGER, unit_title TEXT,
                topic TEXT, subtopic TEXT, skill_focus TEXT, year_label TEXT,
                subject TEXT, verified INTEGER, notes TEXT)""")

    def seed(self, count):
        with sqlite3.connect(self.db) as conn:
            conn.executemany(
                """INSERT INTO rpt_entries
                   (sequence_no,unit_title,topic,subtopic,skill_focus,
                    year_label,subject,verified,notes)
                   VALUES (?, 'Unit A', 'Topic', 'Lesson', 'Listening',
                           'Tahun 2', 'English', 1, '')""",
                [(i,) for i in range(1, count + 1)],
            )

    def catalog(self, limit=500):
        with patch("web_v1_verified_pdp.SUBJECTS", {"EN": "English"}):
            return VerifiedPdpCatalog(self.db).list_pdp(
                year=2, subject_code="EN", limit=limit
            )

    def test_exact_limit_is_complete(self):
        self.seed(500)
        self.assertEqual(len(self.catalog()), 500)

    def test_over_limit_fails_instead_of_silent_truncation(self):
        self.seed(501)
        with self.assertRaisesRegex(ValueError, "exceeds navigation limit"):
            self.catalog()

    def test_small_custom_limit(self):
        self.seed(3)
        with self.assertRaisesRegex(ValueError, "exceeds navigation limit"):
            self.catalog(limit=2)

    def test_read_does_not_mutate_database(self):
        self.seed(2)
        self.assertEqual(len(self.catalog()), 2)
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM rpt_entries").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
