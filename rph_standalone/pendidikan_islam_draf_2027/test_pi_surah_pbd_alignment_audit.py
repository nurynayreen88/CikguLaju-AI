"""Targeted regression for source-aligned Quran names and lesson PBD ranges."""
import unittest
from pi_surah_pbd_alignment_audit import audit, CHANGED, RPT_SOURCE_ERRORS


class PISurahPbdAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=audit()

    def test_no_named_surah_or_assessment_verse_mismatch(self):
        r=self.data
        self.assertGreaterEqual(r["quran_rph_with_explicit_source_surah_checked"],180)
        self.assertEqual(r["named_surah_or_pbd_range_remaining_mismatches"],0)
        self.assertEqual(r["problems"],[])

    def test_source_copy_errors_repaired_without_pretending_rpt_updated(self):
        r=self.data
        self.assertEqual(r["lessons_with_precise_corrections"],11)
        self.assertEqual(r["curriculum_RPT2027_copy_errors_flagged"],7)
        self.assertEqual(len(CHANGED),11)
        self.assertEqual(len(RPT_SOURCE_ERRORS),7)
        self.assertEqual(len({x["id"] for x in r["rows"]}),11)
        self.assertFalse(r["source_RPT2027_modified"])
        self.assertFalse(r["source_DSKP_modified"])
        self.assertEqual(r["teacher_publishable"],0)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertEqual(r["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
