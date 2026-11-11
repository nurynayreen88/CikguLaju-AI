"""Matematik v54: 87 Year 2 evidence-anchored introductions, RPH only.

This protects the change ledger, SHA and release hold. It does not replace
item-level textbook verification or live Telegram/Web E2E.
"""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
from rph_standalone.matematik import staging_preview_v54 as preview

AUD=Path(__file__).resolve().parents[1]/"audits"

class MatematikV54ConcreteIntroductions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (AUD/"matematik_v54_87_set_induksi_T2_RPH_sahaja_20261107.csv").open(
            encoding="utf8",newline=""
        ) as f:
            cls.edits=list(csv.DictReader(f))

    def test_87_distinct_year2_lessons_and_intros(self):
        self.assertEqual(len(self.edits),87)
        self.assertEqual(len({r["lesson_id"] for r in self.edits}),87)
        self.assertEqual(len({r["after"] for r in self.edits}),87)
        self.assertEqual({r["year"] for r in self.edits},{"2"})
        self.assertEqual({r["section"] for r in self.edits},{"Set induksi (5 minit)"})
        for r in self.edits:
            with self.subTest(rph=r["lesson_id"]):
                self.assertIn("mengaitkannya dengan tajuk",r["before"])
                self.assertNotIn("mengaitkannya dengan tajuk",r["after"])
                self.assertIn("murid",r["after"].lower())
                self.assertTrue(65<=len(r["after"])<=160)
                self.assertTrue(r["after"].endswith("."))
                self.assertTrue(r["source_activity_1"])
                self.assertEqual(r["review"],"RPH_ACT1_ANCHORED_NO_FORMAL_TEACHER_SIGNOFF")

    def test_release_staging_no_rpt_no_production(self):
        gate=json.loads((AUD/"matematik_v54_release_gate_RPH_only_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["year2_lessons_total"],117)
        self.assertEqual(gate["year2_generic_intros_before"],87)
        self.assertEqual(gate["year2_generic_intros_after"],0)
        self.assertEqual(gate["changed_year2_rph"],87)
        self.assertEqual(gate["unchanged_rph"],498)
        self.assertEqual(gate["individual_pdf_onepage_a4"],585)
        self.assertEqual(gate["merged_year2_pdf_pages"],117)
        self.assertEqual(gate["teacher_signoff_count"],0)
        self.assertFalse(gate["academic_item_all_reviewed"])
        self.assertFalse(gate["rpt_changed"])
        self.assertFalse(gate["production_modified"])
        self.assertFalse(gate["real_telegram_web_staging_e2e"])
        self.assertFalse(gate["final_ready"])
        self.assertEqual(gate["archive_sha256"],preview.EXPECTED_SHA256)

if __name__=="__main__":
    unittest.main()
