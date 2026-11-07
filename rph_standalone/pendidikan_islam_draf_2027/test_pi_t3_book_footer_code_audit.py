"""Year3 source textbook SP footer presence is not a full DSKP endorsement."""
import unittest
from pi_t3_book_footer_code_audit import audit,index


class PIYear3BookFooterCodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_original_book_code_coverage_with_one_exception(self):
        r=self.r
        self.assertEqual(len(index()),83)
        self.assertNotIn("6.4.3",index())
        self.assertIn("2.1.4",index())
        self.assertEqual(r["book_pdf_pages"],85)
        self.assertEqual(r["year3_total_draft_lessons"],147)
        self.assertEqual(r["year3_lessons_with_book_footer_code_present"],109)
        self.assertEqual(r["year3_lessons_with_book_footer_code_not_observed"],1)
        self.assertEqual(r["missing_footer_code"],"6.4.3")
        self.assertEqual(r["missing_footer_lesson_ids"],["T3-L146"])
        self.assertIs(r["dskp_6433_visually_confirmed"],True)
        self.assertEqual((r["dskp_pdf_page"],r["dskp_printed_page"]),(51,39))
        self.assertEqual(r["tasmi_verse_based_lessons_without_three_level_sp"],37)
        self.assertEqual(r["source_sp_code_occurrences"],177)
        self.assertEqual(r["distinct_year3_codes_used"],83)

    def test_source_gap_not_mislabelled_curriculum_error(self):
        r=self.r
        self.assertEqual(r["individual_exercise_page_approved"],0)
        self.assertEqual(r["content_expert_approved"],0)
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")
        self.assertEqual(len(r["rows"]),147)
        exception=next(x for x in r["rows"] if x["id"]=="T3-L146")
        self.assertEqual(exception["missing_book_footer_codes"],"6.4.3")
        self.assertIs(exception["dskp_6433_manual_visual_reference"],True)
        self.assertIs(exception["objective_2_needs_sp_alignment_review"],True)
        self.assertIs(exception["source_material_original_preserved"],True)
        self.assertIs(exception["source_book_code_presence_only"],False)
        for x in r["rows"]:
            for key in ("content_expert_approved","book_exercise_page_verified",
                        "full_dskp_text_alignment_verified","can_publish"):
                self.assertIs(x[key],False)
            self.assertEqual(x["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
