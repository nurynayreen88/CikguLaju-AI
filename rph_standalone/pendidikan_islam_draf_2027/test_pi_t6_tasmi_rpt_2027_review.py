"""Year6 tasmi' teaching drafts cannot falsely claim official verse/SP approval."""
import unittest
from pi_t6_tasmi_rpt_2027_review import audit, PLAN


class PIYear6TasmiRPT2027Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()

    def test_both_rpt_source_lessons_and_four_step_activity(self):
        r=self.report
        self.assertEqual(set(x["id"] for x in r["rows"]),set(PLAN))
        self.assertEqual(r["year6_tasmi_rph_activities_revised"],2)
        self.assertEqual(r["total_planned_surahs_referenced"],8)
        self.assertEqual(r["four_step_lesson_plans"],2)
        self.assertEqual(r["rpt_pages_checked"],[48,49])
        for row in r["rows"]:
            self.assertEqual(row["four_activity_steps"],4)
            self.assertIs(row["original_fields_preserved"],True)
            self.assertIs(row["source_sk_sp_preserved"],True)
            self.assertIs(row["teacher_selection_required"],True)
            self.assertEqual(len(row["surahs"].split("|")),4)

    def test_no_false_dskp_or_quran_verse_claim(self):
        r=self.report
        self.assertEqual(r["ayah_bounds_present_in_original_rpt"],0)
        self.assertEqual(r["fabricated_official_dskp_codes"],0)
        self.assertEqual(r["verse_ranges_teacher_verified"],0)
        self.assertEqual(r["rph_approved_for_teacher_use"],0)
        self.assertEqual(r["jawi_expert_approvals"],0)
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")
        for row in r["rows"]:
            for field in ("actual_ayah_range_verified",
                          "is_official_dskp_three_level_sp",
                          "jawi_approved","content_expert_approved",
                          "runtime_pdf_verified","can_publish"):
                self.assertIs(row[field],False)
            self.assertEqual(row["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
