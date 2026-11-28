"""KPM DSKP Year6 SP-code (secondary source) audit remains unapproved."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.audit_sains_y6_2021_secondary_mirror_codes_staging import (
    source_code_index,audit,write_report
)
class SainsYear6SecondaryMirrorQA(unittest.TestCase):
    def test_original_2021_year6_96_sp_range_not_old_year5_or_year4(self):
        codes=source_code_index()
        self.assertEqual(len(codes),96)
        for code in ("1.1.12","2.2.6","3.1.6","5.1.7",
                     "6.3.4","8.2.7","12.1.7","13.1.4"):
            self.assertIn(code,codes)
        for code in ("3.2.1","10.2.1","13.2.1"):
            self.assertNotIn(code,codes)

    def test_historical_84_pdp_get_exact_invalid_code_diff_no_release(self):
        a=audit()
        self.assertEqual(a["year"],6)
        self.assertEqual(a["source_official_sp_count"],96)
        self.assertEqual(a["historical_pdp_count"],84)
        self.assertEqual(a["historical_pdp_with_official_sp_code"]+
                         a["historical_pdp_with_invalid_sp_code"],84)
        self.assertEqual(a["historical_pdp_with_invalid_sp_code"],len(a["invalid_sp_details"]))
        self.assertFalse(a["original_kpm_pdf_sha_verified"])
        self.assertEqual(a["kps_1_1_not_separately_indexed"],
                         [f"1.1.{i}" for i in range(1,13)])
        self.assertEqual(a["non_kps_content_sp_not_separately_indexed"],[])
        self.assertEqual(a["rph_kps_integration_signoffs"],0)
        self.assertTrue(a["kps_sk_1_1_1_to_12_may_be_embedded_in_other_lessons_not_missing_12_new_pdp"])
        self.assertFalse(a["ready_for_web_telegram"])
        self.assertEqual(a["official_sp_text_visual_signoffs"],0)
        self.assertEqual(a["original_pdp_rph_book_sequence_signoffs"],0)
        self.assertEqual(a["production_changes"],0)
        self.assertTrue(all(x["academic_release_approved"] is False for x in a["invalid_sp_details"]))

    def test_draft_only(self):
        with TemporaryDirectory() as t:
            path=Path(t)/"Sains_T6_DRAF.json"
            self.assertTrue(write_report(path).is_file())
            with self.assertRaises(ValueError):
                write_report(Path(t)/"Sains_T6_FINAL.json")
if __name__=="__main__":
    unittest.main()
