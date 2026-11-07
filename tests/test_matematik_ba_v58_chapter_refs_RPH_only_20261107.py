"""Matematik v58 — curriculum book CHAPTER references, no exercise-level approval.

Large ZIP tests (15 real archive checks) run locally because ZIP is not public GitHub content.
"""
import json
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v58 as preview

ROOT=Path(__file__).resolve().parents[1]/"audits"
SHA="bb8d1e727c383efd2bfbe2b748570f7b6f4aeb99c7ffffa4f4426bd5baafdc13"

class V58ChapterEvidenceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate=json.loads((ROOT/"matematik_v58_release_gate_RPH_only_20261107.json").read_text(encoding="utf-8"))
    def test_counts_integrity(self):
        x=self.gate
        self.assertEqual(x["rph_total"],585)
        self.assertEqual(x["year4_pairs_total"],34)
        self.assertEqual(x["pairs_with_new_book_chapter_pages"],32)
        self.assertEqual(x["pairs_with_preexisting_specific_refs_untouched"],2)
        self.assertEqual(len(x["preexisting_refs_preserved"]),4)
        self.assertEqual(x["lessons_with_book_chapter_pages_added"],64)
        self.assertEqual(x["off_skill_intros_corrected"],9)
        self.assertEqual(x["changed_sections"],73)
        self.assertEqual(x["changed_rph"],64)
        self.assertEqual(x["unchanged_rph"],521)
        self.assertEqual(x["docx_count"],585)
        self.assertEqual(x["individual_pdf_A4_onepage"],585)
        self.assertEqual(x["markdown_count"],585)
        self.assertEqual(x["merged_year_pdf_count"],5)
        self.assertEqual(x["merged_year4_pdf_pages"],117)
        self.assertEqual(x["BA_year2_3_ref_count"],234)
    def test_archive_identity_and_no_false_signoff(self):
        x=self.gate
        self.assertEqual(x["archive_sha256"],SHA)
        self.assertEqual(x["archive_bytes"],48954101)
        self.assertEqual(x["actual_zip_test_results"],"15/15 PASS")
        self.assertEqual(preview.EXPECTED_SHA256,SHA)
        self.assertEqual(x["book_item_level_exercises_verified"],0)
        self.assertEqual(x["teacher_academic_formal_signoffs"],0)
        self.assertIn("NOT_EXACT_BOOK_EXERCISE",x["book_verification_level"])
    def test_release_fail_closed_and_no_rpt_work(self):
        x=self.gate
        for key in ("academic_all_585_exercise_signoff","telegram_web_real_staging_e2e",
                    "final_ready","rpt_changed","production_modified"):
            self.assertIs(x[key],False)
        self.assertIn("RPH",x["scope"])
        self.assertIn("RPT",x["scope"])
        self.assertIn("DO NOT MERGE",x["release_instruction"])

if __name__=="__main__":
    unittest.main()
