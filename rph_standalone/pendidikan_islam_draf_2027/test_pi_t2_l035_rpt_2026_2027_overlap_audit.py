"""Regression: original RPT 2026 already carried ayah 224 overlap."""
import unittest
from pi_t2_l035_rpt_2026_2027_overlap_audit import audit

class PIT2L035OriginalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()
    def test_2026_to_2027_overlapping_ayah_provenance(self):
        d=self.r
        self.assertEqual(d["rpt2027_pdf_pages_checked"],[11,12,14])
        self.assertEqual(d["year2_pdp032_surah_baqarah"],[216,224])
        self.assertEqual(d["year2_pdp035_surah_baqarah"],[224,245])
        self.assertEqual(d["following_2026_rpt_range"],[246,259])
        self.assertEqual(d["intersecting_ayah"],[224])
        self.assertIs(d["overlap_present_in_original_2026_rpt"],True)
        self.assertIs(d["overlap_retained_and_flagged_in_2027_rpt"],True)
    def test_no_change_to_unresolved_quran_boundary(self):
        d=self.r
        self.assertIs(d["intentional_revision_vs_source_typo_resolved"],False)
        self.assertIs(d["original_year2_l035_record_still_wholly_held"],True)
        self.assertIs(d["surah_verse_number_modified"],False)
        self.assertEqual(d["expert_quran_sequence_approvals"],0)
        self.assertEqual(d["teacher_ready"],0)
        self.assertEqual(d["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
