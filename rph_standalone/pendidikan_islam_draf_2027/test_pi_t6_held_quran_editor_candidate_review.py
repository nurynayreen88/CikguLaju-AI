"""Four Quran RPH editor proposals never change the original withheld rows."""
import unittest
from pi_t6_held_quran_editor_candidate_review import audit,EXPECTED


class PIY6HeldQuranCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_four_review_only_teaching_drafts(self):
        r=self.r
        self.assertEqual(r["editor_candidates_created"],4)
        self.assertEqual(r["source_held_originals_untouched"],4)
        self.assertEqual({x["id"] for x in r["rows"]},set(EXPECTED))
        self.assertEqual(r["year6_juz25_ayah_omitted"],67)
        self.assertEqual(r["juz29_l117_local_three_surah_gap"],0)
        for x in r["rows"]:
            self.assertEqual(x["steps"],4)
            self.assertEqual(x["draft_language"],"RUMI_EDITOR_PENDING_JAWI")
            self.assertIs(x["original_source_held"],True)

    def test_academic_and_jawi_not_auto_approved(self):
        r=self.r
        self.assertEqual(r["actual_teacher_ayah_assignments_approved"],0)
        self.assertEqual(r["jawi_expert_approvals"],0)
        self.assertEqual(r["curriculum_sp_codes_fabricated"],0)
        self.assertEqual(r["public_teacher_rph_added"],0)
        self.assertEqual(r["release"],"NO_GO")
        for x in r["rows"]:
            self.assertIs(x["jawi_checked"],False)
            self.assertIs(x["academic_approved"],False)
            self.assertEqual(x["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
