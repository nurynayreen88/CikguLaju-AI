"""Staging regression tests: never infer or mix PJ/PK without verified mapping."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from web_v1_verified_pdp import list_explicit_pjpk_entries


class PjpkComponentIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "pjpk.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, sequence_no INTEGER, unit_title TEXT,
                topic TEXT, subtopic TEXT, year_label TEXT,
                subject TEXT, verified INTEGER, notes TEXT)""")
            conn.executemany(
                "INSERT INTO rpt_entries VALUES (?, ?, 'Unit', 'Topic', 'Lesson', 'Tahun 2', 'PJPK', 1, '')",
                [(1, 1), (2, 2), (3, 3), (4, 4)],
            )

    def add_map(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE web_v1_pjpk_map (
                rpt_entry_id INTEGER, component TEXT, verified INTEGER)""")
            conn.executemany("INSERT INTO web_v1_pjpk_map VALUES (?, ?, ?)", [
                (1, "PJ", 1), (2, "PK", 1), (3, "PJ", 1),
                (3, "PK", 1), (4, "PJ", 0),
            ])

    def test_missing_map_exposes_nothing(self):
        self.assertEqual(list_explicit_pjpk_entries(self.db, 2, "PJ"), [])

    def test_only_verified_unambiguous_components(self):
        self.add_map()
        self.assertEqual([r["id"] for r in list_explicit_pjpk_entries(self.db, 2, "PJ")], [1])
        self.assertEqual([r["id"] for r in list_explicit_pjpk_entries(self.db, 2, "PK")], [2])

    def test_invalid_component_rejected(self):
        with self.assertRaises(ValueError):
            list_explicit_pjpk_entries(self.db, 2, "PJPK")


if __name__ == "__main__":
    unittest.main()
