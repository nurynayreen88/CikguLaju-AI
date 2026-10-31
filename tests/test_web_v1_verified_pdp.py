"""Isolated tests for verified RPT/PdP navigation adapter."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from web_v1_verified_pdp import VerifiedPdpCatalog


class VerifiedPdpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "curriculum.db"
        with sqlite3.connect(self.db) as con:
            con.execute("""CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                sequence_no INTEGER, unit_title TEXT, topic TEXT,
                subtopic TEXT, skill_focus TEXT, verified INTEGER, notes TEXT)""")
            con.executemany("INSERT INTO rpt_entries VALUES (?,?,?,?,?,?,?,?,?,?)", [
                (2, "Tahun 3", "Bahasa Inggeris", 2, "Unit B", "B", "", "Writing", 1, ""),
                (1, "Tahun 3", "Bahasa Inggeris", 1, "Unit A", "A", "", "Reading", 1, ""),
                (3, "Tahun 3", "Bahasa Inggeris", 3, "Old", "Old", "", "", 1, "superseded"),
                (4, "Tahun 3", "Bahasa Inggeris", 4, "Draft", "Draft", "", "", 0, ""),
                (5, "Tahun 4", "Bahasa Inggeris", 1, "Other", "Other", "", "", 1, ""),
            ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_verified_only_and_sequence_order(self):
        rows = VerifiedPdpCatalog(self.db).list_pdp(year=3, subject_code="ENGLISH")
        self.assertEqual([r["pdp_no"] for r in rows], [1, 2])
        self.assertEqual(rows[0]["unit_title"], "Unit A")

    def test_bad_inputs(self):
        catalog = VerifiedPdpCatalog(self.db)
        for kwargs in ({"year": True, "subject_code": "ENGLISH"},
                       {"year": 3, "subject_code": "ENGLISH' OR 1=1"},
                       {"year": 3, "subject_code": "ENGLISH", "limit": 999}):
            with self.assertRaises(ValueError):
                catalog.list_pdp(**kwargs)

    def test_missing_db_not_created(self):
        missing = self.db.parent / "missing.db"
        with self.assertRaises(FileNotFoundError):
            VerifiedPdpCatalog(missing).list_pdp(year=3, subject_code="ENGLISH")
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
