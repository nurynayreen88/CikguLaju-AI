"""Five wholly held Year6 records remain without teaching content."""
import unittest
from pi_y6_held_rpt_2027_source_review import audit,HELD_SOURCE


class PIYear6HeldRPTReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_five_explicit_source_triage_cases(self):
        r=self.r
        self.assertEqual(r["year6_held_lessons_checked"],5)
        self.assertEqual(r["rpt_verse_continuity_gap_cases"],2)
        self.assertEqual(r["proposed_non_official_technical_pdp"],1)
        self.assertEqual(r["rpt_juz29_boundary_review_cases"],1)
        self.assertEqual(set(x["id"] for x in r["rows"]),set(HELD_SOURCE))
        self.assertEqual(r["rpt_pages_checked"],[3,5,7,21,41])
        self.assertEqual(r["generated_held_rph"],0)

    def test_non_destructive_no_false_source_approval(self):
        r=self.r
        self.assertEqual(r["mushaf_source_approvals"],0)
        self.assertEqual(r["original_dskp_sp_approvals"],0)
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")
        for x in r["rows"]:
            self.assertTrue(x["rpt_named_content"])
            self.assertTrue(x["reason"])
            for field in ("authoritative_mushaf_bounds_approved",
                          "original_dskp_sp_approved",
                          "source_completeness_approved",
                          "content_generated","can_publish"):
                self.assertIs(x[field],False)
            self.assertEqual(x["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
