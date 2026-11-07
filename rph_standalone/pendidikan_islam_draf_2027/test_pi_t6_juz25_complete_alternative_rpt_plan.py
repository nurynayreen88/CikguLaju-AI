"""No duplicated/missing Quran verses in either tentative Juz25 arrangement."""
import unittest
from pi_t6_juz25_complete_alternative_rpt_plan import plan, SLOTS


class PIJuz25CompleteAlternativesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=plan()

    def test_both_plans_cover_246_verses_once(self):
        r=self.data
        self.assertEqual((r["source_verses_mapped"],r["source_verses_missing"],
                          r["full_juz25_target"]),(179,67,246))
        self.assertEqual(len(r["editor_options"]),2)
        minimal,balanced=r["editor_options"]
        self.assertEqual([x["pdp"] for x in minimal["rows"]],list(SLOTS))
        self.assertEqual([x["total_juz25_ayah"] for x in minimal["rows"]],
                         [40,19,35,56,59,22,15])
        self.assertEqual([x["total_juz25_ayah"] for x in balanced["rows"]],
                         [35,35,35,35,35,35,36])
        for option in r["editor_options"]:
            self.assertEqual(option["total_juz25_verses"],246)
            self.assertTrue(option["all_juz25_ayah_covered_once"])
            self.assertEqual(len(option["rows"]),7)
            self.assertTrue(all(not x["expert_and_teacher_approved"] for x in option["rows"]))

    def test_full_coverage_is_not_academic_or_operational_approval(self):
        r=self.data
        self.assertTrue(r["source_rpt_unchanged"])
        self.assertTrue(r["held_source_rph_unchanged"])
        self.assertTrue(r["juz26_al_ahqaf_scheduling_decision_required"])
        self.assertEqual(r["official_sp_codes_assigned"],0)
        self.assertEqual(r["teacher_approved_plans"],0)
        self.assertFalse(r["approved_for_teacher"])
        self.assertIsNone(r["academic_quality_score_percent"])
        self.assertEqual(r["publication"],"HOLD")
        self.assertEqual(r["release"],"NO_GO")
        self.assertEqual(r["editor_options"][0]["heavy_pdp_for_teacher_to_split"],
                         ["T6-L014","T6-L018"])
        self.assertTrue(r["editor_options"][0]["all_original_juz25_pdp_assignments_preserved"])
        self.assertFalse(r["editor_options"][1]["all_original_juz25_pdp_assignments_preserved"])


if __name__=="__main__":
    unittest.main()
