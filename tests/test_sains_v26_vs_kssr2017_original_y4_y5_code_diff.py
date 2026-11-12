"""Sains v26 verified flag cannot override independent official KSSR2017 code set."""
import unittest
from scripts.audit_sains_v26_vs_kssr2017_original_year4_year5_codes import audit_codes,original_codes

class SainsOriginal2017CodeVsLegacyQA(unittest.TestCase):
    def test_independent_kssr2017_year4_year5_code_inventory(self):
        codes=original_codes()
        self.assertEqual({y:len(v) for y,v in codes.items()},{4:91,5:95})
        self.assertIn("2.3.1",codes[4])
        self.assertNotIn("3.3.1",codes[4])
        self.assertNotIn("3.4.1",codes[4])
        self.assertIn("10.2.1",codes[4])
        self.assertIn("6.1.6",codes[5])
        self.assertNotIn("6.2.1",codes[5])
        self.assertNotIn("10.2.1",codes[5])
    def test_legacy_mismatch_report_never_approved(self):
        audit=audit_codes()
        self.assertFalse(audit["release_ready"])
        self.assertEqual(audit["production_changes"],0)
        for year,report in audit["years"].items():
            self.assertFalse(report["same_numbers_mean_same_standard"])
            self.assertGreater(report["legacy_code_not_in_official"]+
                               report["official_code_not_in_legacy"],0)
            self.assertEqual(report["legacy_v26_db_verified_sp_count"],
                             report["legacy_code_not_in_official"]+
                             report["same_numeric_code_not_equivalent_text_verified"])
            self.assertEqual(report["kssr2017_original_pdf_sp_count"],
                             report["official_code_not_in_legacy"]+
                             report["same_numeric_code_not_equivalent_text_verified"])

if __name__=="__main__":
    unittest.main()
