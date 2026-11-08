"""No unsupported claim of six Ramadan fasting pillars may leave staging."""
import unittest
from pi_primary_source_fiqh_copyedit_audit import audit


class PISourceFiqhTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.r=audit()

    def test_primary_book_rukun_puasa(self):
        r=self.r
        self.assertTrue(r["two_rukun_puasa_correction_applied_in_staging"])
        self.assertEqual(r["source_book_page_printed"],130)
        self.assertTrue(r["original_rpt_year4_pdp107_six_rukun_incorrect"])
        self.assertFalse(r["source_sp_modified"])
        self.assertFalse(r["expert_fiqh_approved"])
        self.assertFalse(r["teacher_release"])

    def test_three_other_reversible_copyedits(self):
        r=self.r
        self.assertEqual(r["other_exact_word_duplicate_fixes"],3)
        self.assertEqual(len(r["rows"]),4)
        self.assertEqual({item["id"] for item in r["rows"]},
                         {"T4-L103","T4-L107","T5-L103","T5-L138"})
        self.assertTrue(all(item["original_saved"] and not item["published"]
                            for item in r["rows"]))
        self.assertEqual(r["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
