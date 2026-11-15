"""Regression: T4 L083 source excerpt is traceable, not academic approval."""
import unittest
from pi_t4_hadith_source_audit import audit,EXCERPT

class PIYear4HadithBookAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()
    def test_original_source_excerpt_and_boundaries(self):
        x=self.r
        self.assertTrue(EXCERPT.startswith("... "))
        self.assertIn("فَلْيُكْرِمْ ضَيْفَهُ",EXCERPT)
        self.assertEqual(x["lesson_id"],"T4-L083")
        self.assertEqual((x["book_pdf_page"],x["book_printed_page"]),(57,51))
        self.assertEqual((x["dskp_pdf_page"],x["dskp_printed_page"]),(39,27))
        self.assertEqual(x["staging_source_excerpt_recovered"],1)
        self.assertEqual(x["physical_activity_steps_after_repair"],3)
    def test_source_repaired_but_no_permission_to_release(self):
        x=self.r
        self.assertEqual(x["complete_original_narration_certified"],0)
        self.assertIs(x["source_missing_critical_flag_still_holds"],True)
        self.assertEqual(x["expert_hadith_approvals"],0)
        self.assertEqual(x["jawi_orthography_approvals"],0)
        self.assertIsNone(x["academic_quality_percent"])
        self.assertIs(x["can_publish"],False)
        self.assertEqual(x["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
