"""Matematik v60: 68 paired Year4 lesson keys, 8 objective/PBD repairs, staging only.

Note: GitHub runner reads manifest/loader ONLY. 14 real ZIP tests were run offline
against the complete 49MB archive, which is not committed to the public repository.
"""
import json
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v60 as preview

A=Path(__file__).resolve().parents[1]/"audits"
SHA="a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271"

class V60PairedPBDReleaseGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((A/"matematik_v60_release_gate_RPH_only_20261108.json").read_text(encoding="utf-8"))

    def test_exact_archive_and_output_contract(self):
        g=self.g
        self.assertEqual(g["archive_sha256"],SHA)
        self.assertEqual(preview.EXPECTED_SHA256,SHA)
        self.assertEqual(g["archive_bytes"],49194607)
        self.assertEqual(g["rph_total"],585)
        self.assertEqual(g["rph_with_objective_pbd_target_fixes"],8)
        self.assertEqual(g["unchanged_rph"],577)
        self.assertEqual(g["word_docx_count"],585)
        self.assertEqual(g["pdf_A4_onepage_count"],585)
        self.assertEqual(g["markdown_count"],585)
        self.assertEqual(g["merged_pdf_count"],5)
        self.assertEqual(g["year4_merged_pdf_pages"],117)

    def test_68_lesson_teacher_key_cover_with_precise_limits(self):
        g=self.g
        self.assertEqual(g["year4_pairs_count"],34)
        self.assertEqual(g["year4_pair_lessons_count"],68)
        self.assertEqual(g["existing_v59_first_sessions_with_key"],30)
        self.assertEqual(g["new_v60_second_sessions_with_key"],34)
        self.assertEqual(g["new_v60_preexisting_first_sessions_with_key"],4)
        self.assertEqual(g["new_v60_lessons_with_key"],38)
        self.assertEqual(g["new_v60_answer_entries"],144)
        self.assertEqual(g["new_v60_exact_rational_checks"],124)
        self.assertEqual(g["new_v60_teacher_dependent"],14)
        self.assertEqual(g["new_v60_categorical_conceptual"],6)
        self.assertEqual(g["teacher_key_pdf_pages"],24)
        self.assertEqual(len(g["objective_corrections"]),8)
        for lesson,target in {
            "T4-L019":"2 daripada 3","T4-L039":"2 daripada 2","T4-L040":"2 daripada 3",
            "T4-L060":"2 daripada 2","T4-L061":"2 daripada 3","T4-L073":"2 daripada 3",
            "T4-L092":"2 daripada 3","T4-L103":"4 daripada 5",
        }.items():
            self.assertEqual(g["objective_corrections"][lesson],target)

    def test_academic_signoff_and_integration_not_claimed(self):
        g=self.g
        self.assertEqual(g["teacher_formal_academic_signoffs"],0)
        self.assertFalse(g["year4_book_exercises_item_by_item_verified"])
        self.assertFalse(g["telegram_web_real_staging_e2e"])
        self.assertFalse(g["final_ready"])
        self.assertFalse(g["rpt_changed"])
        self.assertFalse(g["production_modified"])
        self.assertIn("Do not merge",g["release_policy"])

if __name__=="__main__":
    unittest.main()
