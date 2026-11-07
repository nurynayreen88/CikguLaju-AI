"""Matematik v48: real dated RM1 exchange-rate SP must not be taught with fake currency X/Y/Z."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

AUDITS=Path(__file__).resolve().parents[1]/"audits"
class V48CurrencyDSKPGate(unittest.TestCase):
    def test_four_rph_21_edits_and_real_sources(self):
        with (AUDITS/"matematik_v48_4_matawang_semakan_dskp_20261107.csv").open(
                encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),21)
        self.assertEqual(Counter(r["lesson_id"] for r in rows),{
            "T3-L060":6,"T4-L055":3,"T4-L056":6,"T4-L057":6})
        for r in rows:
            with self.subTest(lesson=r["lesson_id"],section=r["section"]):
                self.assertTrue(r["before"])
                self.assertTrue(r["after"])
                self.assertNotIn("SIMULASI",r["after"])
                self.assertNotIn("mata wang X rekaan",r["after"])
                self.assertNotIn("kadar simulasi",r["after"])
                self.assertEqual(r["approval_state"],"ACADEMIC_TEACHER_SIGNOFF_PENDING")
                if r["section"]=="Rujukan":
                    self.assertIn("www.bnm.gov.my/latest-rates",r["after"])
                    self.assertIn("DSKP",r["after"])
        self.assertTrue(any(r["lesson_id"]=="T3-L060" and "RM1" in r["after"] for r in rows))
        self.assertTrue(any(r["lesson_id"]=="T4-L057" and "RM1" in r["after"] for r in rows))
    def test_release_remains_staging_only(self):
        gate=json.loads((AUDITS/"matematik_v48_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["version"],"v48")
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["changed_sections"],21)
        self.assertEqual(gate["PDF_A4_one_page"],585)
        self.assertEqual(gate["year2_3_BA_reference_count"],234)
        self.assertEqual(gate["DSKP_Y3_SP_4_6_2_PDF_page"],61)
        self.assertEqual(gate["DSKP_Y4_SP_3_5_2_PDF_page"],57)
        self.assertFalse(gate["static_currency_rates_included"])
        self.assertTrue(gate["teacher_needs_dated_BNM_table_for_lesson"])
        self.assertEqual(gate["academic_exercise_signoff_count"],0)
        self.assertFalse(gate["actual_telegram_web_staging_e2e"])
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
if __name__=="__main__":
    unittest.main()
