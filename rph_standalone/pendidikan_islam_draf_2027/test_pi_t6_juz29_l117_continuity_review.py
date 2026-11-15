"""Preserve Juz29 L117 held despite 100% continuity of Quran chapters 70-72."""
import unittest
from pi_t6_juz29_l117_continuity_review import audit,CHAPTERS,LESSONS


class PIY6Juz29ContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()

    def test_chapter_counts_and_neighboring_pdp_sequence(self):
        r=self.report
        self.assertEqual(len(CHAPTERS),3)
        self.assertEqual(len(LESSONS),3)
        self.assertEqual(r["chapter_70_al_maarij_total_ayat"],44)
        self.assertEqual(r["chapter_71_nuh_total_ayat"],28)
        self.assertEqual(r["chapter_72_al_jinn_total_ayat"],28)
        self.assertEqual(r["three_surahs_total_ayat"],100)
        self.assertEqual(r["three_surahs_mapped_ayat"],100)
        self.assertEqual(r["three_surahs_missing_ayat"],0)
        self.assertEqual(r["rpt_l117_ranges"],[[70,40,44],[71,1,28],[72,1,13]])
        self.assertIs(r["continuity_before_l117"],True)
        self.assertIs(r["continuity_after_l117"],True)
        self.assertIs(r["az_zumar_wrong_juz29_excluded"],True)

    def test_no_premature_l117_publishing(self):
        r=self.report
        self.assertIs(r["original_l117_withheld"],True)
        self.assertIs(r["original_l117_fields_created"],False)
        for n in ("matan_tajwid_expert_approved","teacher_pbd_approved",
                  "jawi_approved","can_publish"):
            self.assertIs(r[n],False)
        self.assertEqual(r["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
