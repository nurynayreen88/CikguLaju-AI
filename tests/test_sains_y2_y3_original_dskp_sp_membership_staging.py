"""Original KPM source-code audit Sains Year2/3, no release signoff."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from scripts.audit_sains_y2_y3_original_dskp_sp_membership_staging import (
    audit,official_codes,write_report
)

class SainsY2Y3SourceCodeQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=audit()
    def test_independent_source_original_code_ranges(self):
        official=official_codes()
        self.assertEqual({y:len(v) for y,v in official.items()},{2:64,3:60})
        self.assertIn("3.1.4",official[2])
        self.assertIn("3.2.5",official[3])
        self.assertNotIn("6.2.1",official[2])
    def test_96_historical_pdp_codes_present_not_academic_signoff(self):
        r=self.result
        self.assertEqual(r["status"],"KSSR2017_SAINS_YEAR2_YEAR3_SOURCE_CODE_MEMBERSHIP_ONLY_DRAF")
        self.assertEqual(r["production_writes"],0)
        self.assertFalse(r["ready_for_web_telegram"])
        self.assertTrue(r["all_96_old_pdp_code_membership"])
        self.assertEqual({y:(x["historical_pdp_count"],x["historical_pdp_with_official_sp_code"])
                          for y,x in r["years"].items()},
                         {"2":(51,51),"3":(45,45)})
        self.assertTrue(all(x["academic_ready"] is False and
                            x["all_sp_statements_verified"] is False and
                            x["dp_kssr_edition3_alignment_signed_off"] is False
                            for x in r["years"].values()))
    def test_no_final_output(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_report(Path(d)/"FINAL.json")
            self.assertTrue(write_report(Path(d)/"Sains_DRAF.json").exists())

if __name__=="__main__":
    unittest.main()
