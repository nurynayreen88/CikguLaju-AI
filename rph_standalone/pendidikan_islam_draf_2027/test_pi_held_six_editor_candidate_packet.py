"""Six formerly blank RPH slots now have quarantined editor candidates."""
import unittest

from pi_held_six_editor_candidate_packet import audit, EXPECTED_HELD


class PIHeldSixEditorPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = audit()

    def test_every_original_held_lesson_has_candidate(self):
        r=self.r
        self.assertEqual(r["fully_held_editor_candidates"],6)
        self.assertEqual(r["total_catalog"],696)
        self.assertEqual(r["nonheld_existing_editor_drafts"],690)
        self.assertEqual(r["proposed_editor_content_total"],696)
        self.assertEqual(tuple(row["id"] for row in r["rows"]),EXPECTED_HELD)
        for row in r["rows"]:
            self.assertTrue(row["original_catalog_withheld"])
            self.assertFalse(row["teacher_publish"])
            self.assertEqual(len(row["candidate"]["aktiviti_utama"]),4)
            self.assertEqual(row["release"],"NO_GO")

    def test_never_confuse_editor_candidate_with_verified_teacher_rph(self):
        r=self.r
        self.assertIs(r["original_held_catalog_modified"],False)
        self.assertFalse(r["t2_l035_ayah224_source_overlap_expert_resolved"])
        self.assertFalse(r["year6_juz25_67_ayah_mapped_in_source_rpt"])
        self.assertEqual(r["teacher_ready"],0)
        self.assertEqual(r["content_expert_approved"],0)
        self.assertEqual(r["jawi_orthography_approved"],0)
        self.assertEqual(r["actual_catalog_entries_released"],0)
        self.assertEqual(r["release"],"NO_GO")
        for row in r["rows"]:
            self.assertFalse(row["expert_verified"])
            self.assertFalse(row["jawi_verified"])
            self.assertFalse(row["official_dskp_sp_assigned"])
            self.assertFalse(row["runtime_generation_tested"])


if __name__=="__main__":
    unittest.main()
