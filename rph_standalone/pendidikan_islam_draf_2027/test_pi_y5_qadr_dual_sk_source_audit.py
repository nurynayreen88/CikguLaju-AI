"""Prevent Year5 al-Qadr tilawah vs hafazan SP numbering regression."""
import unittest

from pi_y5_qadr_dual_sk_source_audit import audit,LESSONS

class PIY5QadrDualSKTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.result=audit()

    def test_kpm_source_exact_codes(self):
        x=self.result
        self.assertEqual(x["original_year5_catalog_size"],143)
        self.assertEqual(x["fixed_combined_sk_lessons"],2)
        self.assertEqual(x["source_field_replacements"],3)
        self.assertEqual(x["source_dskp_printed_pages"],[19,21])
        self.assertEqual({r["id"] for r in x["rows"]},LESSONS)
        self.assertEqual(x["academic_expert_approved"],0)
        self.assertEqual(x["ready_for_teacher"],0)
        self.assertFalse(x["source_rpt_modified"])
        self.assertEqual(x["release"],"NO_GO")

    def test_dual_sk_preserved_not_conflated(self):
        l={r["id"]:r for r in self.result["rows"]}
        self.assertEqual(l["T5-L069"]["correction_fields"],["sp"])
        self.assertEqual(l["T5-L073"]["correction_fields"],["set_induksi","sp"])
        for x in l.values():
            self.assertTrue(x["combined_sk_preserved"])
            self.assertTrue(x["sp_131_matches_memorization"])
            self.assertFalse(x["expert_approved"])
            self.assertFalse(x["ready"])

if __name__=="__main__":unittest.main()
