"""Official DSKP SP4.2 codes do not certify proposed CikguLaju PdP60."""
import unittest
from pi_t6_sp42_primary_source_audit import audit,SP


class PIY6SP42PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=audit()

    def test_original_dskp_sp_codes_and_complementary_amali(self):
        r=self.result
        self.assertEqual(r["source_dskp_pdf_page"],46)
        self.assertEqual(r["source_dskp_printed_page"],34)
        self.assertEqual(r["sp_codes_visually_present"],list(SP))
        self.assertEqual(r["rpt_pdf_page"],21)
        self.assertIs(r["rpt_additional_pdp_declared_as_cikgulaju_suggestion"],True)
        self.assertEqual(r["l059_kbat_off_topic_question_replaced"],1)
        self.assertIs(r["l059_original_assessment_preserved"],True)
        self.assertEqual(r["l060_editor_candidate_created"],1)
        self.assertEqual(r["l060_editor_candidate_main_activity_steps"],4)

    def test_no_auto_promotion_of_proposed_or_held_rph(self):
        r=self.result
        self.assertIs(r["l060_original_year6_record_still_wholly_held"],True)
        self.assertEqual(r["independent_official_dskp_lesson_numbers_claimed"],0)
        self.assertEqual(r["expert_fiqh_approvals"],0)
        self.assertEqual(r["expert_jawi_approvals"],0)
        self.assertEqual(r["eligible_teacher_lessons"],0)
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
