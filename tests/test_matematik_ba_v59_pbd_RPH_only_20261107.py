"""Matematik v59: verify audit checkpoint and keep RPH PBD academic signoff separate from ZIP QA.

GitHub runner cannot inspect the full private ZIP. 12/12 tests on the REAL ZIP
(and 109 exact teacher-key calculations) were executed offline.
"""
import json
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v59 as preview
AUD=Path(__file__).resolve().parents[1]/"audits"
SHA="79a759be40fd8aadebbf3318d784e042239d290e8cc36b4136380c8fb5c215eb"

class V59SourceScopedPBD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((AUD/"matematik_v59_release_gate_RPH_only_20261107.json").read_text(encoding="utf-8"))
    def test_30_first_lessons_have_120_teacher_key_questions(self):
        x=self.g
        self.assertEqual(x["rph_total"],585)
        self.assertEqual(x["year4_pairs_checked"],34)
        self.assertEqual(x["year4_first_lessons_existing_specific_PBD_untouched"],4)
        self.assertEqual(x["year4_first_lessons_PBD_corrected"],30)
        self.assertEqual(x["original_PBD_items_created"],120)
        self.assertEqual(x["exact_calculation_answers_verified"],109)
        self.assertEqual(x["spatial_or_category_answers_checked"],7)
        self.assertEqual(x["physical_measurement_answers_teacher_required"],4)
        self.assertEqual(x["changed_RPH"]+x["unchanged_RPH_byte_identical"],585)
    def test_file_contract_and_hash(self):
        x=self.g
        self.assertEqual(preview.EXPECTED_SHA256,x["sha256"])
        self.assertEqual(x["sha256"],SHA)
        self.assertEqual(x["archive_bytes"],48994065)
        self.assertEqual(x["actual_archive_tests"],"12/12 PASS")
        self.assertEqual(x["individual_word_pdf_markdown_count_each"],585)
        self.assertEqual(x["pdf_individual_A4_onepage_count"],585)
        self.assertEqual(x["year4_merged_pdf_pages"],117)
        self.assertEqual(x["year2_3_BA_reference_count"],234)
    def test_source_scope_not_book_exercise_signoff(self):
        x=self.g
        self.assertFalse(x["book_exercise_copied_from_textbook"])
        self.assertIn("NOT_OFFICIAL_TEXTBOOK",x["source_level"])
        self.assertEqual(x["formal_teacher_signoff_count"],0)
        self.assertFalse(x["year4_34_pairs_exact_textbook_exercises_verified"])
        self.assertFalse(x["all_585_textbook_items_verified"])
    def test_rpt_and_production_unchanged_release_fails_closed(self):
        x=self.g
        self.assertFalse(x["actual_Telegram_Web_staging_E2E"])
        self.assertFalse(x["rpt_changed"])
        self.assertFalse(x["production_modified"])
        self.assertFalse(x["final_ready"])
        self.assertIn("No main merge",x["release_policy"])
        self.assertIn("RPT out of scope",x["scope"])

if __name__=="__main__":
    unittest.main()
