"""Regression tests for the read-only PJPK source-gap queue."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import pjpk_source_gap_queue_v2679 as queue


class SourceGapQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "candidate.db"
        with sqlite3.connect(self.db) as con:
            con.executescript("""
                CREATE TABLE rpt_entries (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    unit_title TEXT, topic TEXT
                );
                CREATE TABLE rpt_entry_standards (
                    rpt_entry_id INTEGER, standard_type TEXT, standard_code TEXT,
                    standard_text TEXT, sequence_no INTEGER
                );
                INSERT INTO rpt_entries VALUES
                    (1, 'Tahun 1', 'Pendidikan Jasmani', 'Unit 1', 'Pergerakan');
                INSERT INTO rpt_entry_standards VALUES
                    (1, 'SP', '1.1.1', 'Teks RPT', 1);
            """)

    def tearDown(self):
        self.tmp.cleanup()

    @patch.object(queue, "load_evidence", return_value={})
    @patch.object(queue, "reconcile_sp_text", return_value={
        "status": "NO_DIRECT_DSKP_TEXT", "dskp_text": "", "source_document": ""
    })
    def test_emits_review_and_missing_sk_without_writing(self, _reconcile, _evidence):
        before = self.db.read_bytes()
        items = queue.build_queue(self.db)
        self.assertEqual({item["record_type"] for item in items},
                         {"SP_SOURCE_REVIEW", "MISSING_SK_LINK"})
        self.assertTrue(all(item["action"] for item in items))
        self.assertEqual(self.db.read_bytes(), before)

    def test_refuses_database_with_wrong_schema(self):
        wrong = Path(self.tmp.name) / "wrong.db"
        with sqlite3.connect(wrong) as con:
            con.execute("CREATE TABLE unrelated (id INTEGER)")
        with self.assertRaisesRegex(RuntimeError, "lacks RPT tables"):
            queue.build_queue(wrong)


if __name__ == "__main__":
    unittest.main()
