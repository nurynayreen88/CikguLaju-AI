"""Exact KSSR Year5 DSKP khat source correction guard."""
import unittest
from pi_y5_khat_nasakh_source_audit import audit, UPDATED, LETTER, WORD

class PIY5KhatNasakhDSKPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=audit()

    def test_four_changed_source_codes_and_objective(self):
        r=self.data
        self.assertEqual(r["four_corrected_ayat_and_tekal_sp_records"],4)
        self.assertEqual(r["source_printed_pages"],[43,44])
        self.assertEqual(r["letter_sp_unchanged"],4)
        self.assertEqual(r["word_sp_unchanged"],5)
        self.assertEqual(r["source_year5_records"],143)
        self.assertEqual({x["id"] for x in r["rows"]},UPDATED)
        self.assertEqual(len(LETTER | WORD | UPDATED),13)
        self.assertTrue(r["original_fields_preserved"])
        self.assertIs(r["original_source_rpt_changed"],False)
        self.assertEqual(r["academic_expert_approvals"],0)
        self.assertEqual(r["year5_khat_ready"],0)
        self.assertEqual(r["release"],"NO_GO")

    def test_approval_cannot_be_inferred_from_source_only(self):
        for row in self.data["rows"]:
            self.assertEqual(row["corrected_sp_codes"],["7.2.5","7.2.6"])
            self.assertTrue(row["objective_matches_ayat"])
            self.assertTrue(row["original_preserved"])
            self.assertFalse(row["expert_approved"])
            self.assertFalse(row["teacher_ready"])

if __name__=="__main__": unittest.main()
