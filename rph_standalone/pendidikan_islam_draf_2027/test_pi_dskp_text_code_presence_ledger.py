"""Year3/4 PDF text extraction failure must not be treated as invalid DSKP."""
import unittest
from pi_dskp_text_code_presence_ledger import audit, CHECKABLE, UNREADABLE


class PIDSKPCodeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()

    def test_source_numbers_have_positive_presence_where_readable(self):
        r=self.report
        self.assertEqual(r["source_pdf_code_types_by_year"],
                         {"2":83,"3":0,"4":5,"5":114,"6":109})
        self.assertEqual(r["full_catalog_rows_checked"],696)
        self.assertEqual(r["code_reference_mismatches_year2_5_6"],0)
        self.assertEqual(tuple(r["fully_machine_readable_code_years"]),CHECKABLE)

    def test_unreadable_pdf_never_yields_false_absence_claim(self):
        r=self.report
        self.assertEqual(tuple(r["incomplete_dskp_pdf_text_years"]),UNREADABLE)
        self.assertEqual(r["false_absence_claims_year3_4"],0)
        self.assertEqual(r["exact_sk_sp_wording_expert_approvals"],0)
        self.assertEqual(r["codes_or_ayat_added_to_rph"],0)
        self.assertFalse(r["db_modified"])
        self.assertEqual(r["release"],"NO_GO")
        self.assertEqual(r["counts"]["HELD_NO_TEACHER_SP"],6)
        self.assertEqual(len(r["rows"]),696)
        self.assertTrue(all(not row["can_publish"] for row in r["rows"]))


if __name__=="__main__":
    unittest.main()
