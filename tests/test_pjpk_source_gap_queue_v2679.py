"""Regression tests for the read-only PJPK source-gap queue."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import pjpk_source_gap_queue_v2679 as queue
from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text


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



class VerifiedEvidenceSupplementTests(unittest.TestCase):
    def test_source_cited_year1_pj_standards_are_available_for_exact_reconciliation(self):
        evidence = load_evidence()
        expected = {
            "1.1.1": "Melakukan pergerakan yang melibatkan kesedaran tubuh badan dari segi bentuk, imbangan, pemindahan berat badan, dan layangan.",
            "1.1.7": "Melakukan pergerakan yang berbeza penggunaan daya antara ringan dengan berat.",
            "2.1.1": "Menyatakan bentuk badan, imbangan, pemindahan berat badan, dan layangan semasa melakukan aktiviti.",
            "2.1.7": "Mengenal pasti penggunaan daya yang berbeza dalam pergerakan.",
            "5.4.2": "Mempamerkan rasa seronok semasa melakukan aktiviti dalam kumpulan.",
        }
        for code, text in expected.items():
            with self.subTest(code=code):
                result = reconcile_sp_text(
                    "Tahun 1", "Pendidikan Jasmani", code, text, evidence
                )
                self.assertEqual(result["status"], "EXACT_TEXT_MATCH")
                self.assertIn("DSKP KSSR Semakan 2017 PJPK Tahun 1", result["source_document"])
                self.assertTrue(result.get("source_file_id", "").startswith("https://fliphtml5.com/"))


if __name__ == "__main__":
    unittest.main()
