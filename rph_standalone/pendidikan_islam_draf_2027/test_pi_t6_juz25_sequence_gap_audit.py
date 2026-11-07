"""Juz25 must NOT be described as complete with 67 Quran ayat missing."""
import unittest
from pi_t6_juz25_sequence_gap_audit import audit,ASSIGNED,JUZ25,spans


class PIY6Juz25SourceSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_complete_juz25_inventory_matches_source_not_guess(self):
        r=self.r
        self.assertEqual(len(ASSIGNED),7)
        self.assertEqual(len(JUZ25),5)
        self.assertEqual(r["juz25_expected_ayah_count"],246)
        self.assertEqual(r["juz25_ayah_assigned_in_rpt"],179)
        self.assertEqual(r["juz25_ayah_missing_in_rpt"],67)
        self.assertEqual(r["juz25_missing_non_overlapping_blocks"],4)
        self.assertEqual(r["juz26_pdp026_ahqaf_ayat_not_counted_as_juz25"],14)
        self.assertEqual([(v["surah_number"],v["missing_first_ayah"],
                           v["missing_last_ayah"],v["missing_ayah_count"])
                          for v in r["rows"]],[
                              (41,47,54,8),(43,74,89,16),
                              (44,1,39,39),(45,34,37,4)])
        self.assertEqual(r["missing_fussilat"]+r["missing_zukhruf"]+
                         r["missing_dukhan"]+r["missing_jathiyah"],67)
        self.assertEqual(spans([1,2,3,5,6,9]),[(1,3),(5,6),(9,9)])

    def test_held_rph_remain_untouched_and_no_silent_verse_assignment(self):
        r=self.r
        self.assertEqual(r["original_held_rph_source_records_preserved"],3)
        self.assertEqual(r["automatic_verse_reassignments"],0)
        self.assertEqual(r["exact_tasmi_teacher_assignments_approved"],0)
        self.assertEqual(r["expert_quran_sequence_approvals"],0)
        self.assertEqual(r["rpt_proposed_gap_resolution"],"EDITOR_TEACHER_DECISION_REQUIRED")
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")
        for g in r["rows"]:
            self.assertIs(g["automatically_assigned_to_pdp"],False)
            self.assertIs(g["teacher_or_expert_approved"],False)
            self.assertEqual(g["release"],"NO_GO")

if __name__=="__main__":
    unittest.main()
