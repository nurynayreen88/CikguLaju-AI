"""Heavy Quran tasmi editorial teaching improvements must preserve sources."""
import hashlib
import unittest
from pi_heavy_tasmi_editor_overlay import generate, EXPECTED, ACTIVITY, PBD


class HeavyTasmiEditorOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=generate()

    def test_all_14_high_volume_lessons_are_source_locked(self):
        data=self.data
        rows=data["rows"]
        self.assertEqual(data["candidate_rph_activity_and_pbd_overlays"],14)
        self.assertEqual({x["id"] for x in rows},EXPECTED)
        self.assertEqual(data["year5"],4)
        self.assertEqual(data["year6"],10)
        self.assertEqual(data["source_ayah_min"],61)
        self.assertEqual(data["source_ayah_max"],106)
        self.assertEqual(data["original_catalog_files_overwritten"],0)
        self.assertEqual(data["official_ayah_boundaries_reassigned"],0)
        self.assertEqual(data["teacher_exact_subranges_assigned"],0)
        self.assertEqual(data["jawi_or_content_approvals"],0)
        self.assertFalse(data["claim_to_have_completed_full_sp"])
        self.assertEqual(data["teacher_ready"],0)
        self.assertEqual(data["release"],"NO_GO")
        for r in rows:
            self.assertGreater(r["source_range_ayat_count"],60)
            self.assertTrue(r["unchanged_source_sp"])
            self.assertTrue(r["unchanged_source_objective"])
            self.assertEqual(
                hashlib.sha256(r["original_activity"].encode("utf-8")).hexdigest(),
                r["original_activity_sha256"])
            self.assertEqual(
                hashlib.sha256(r["original_pbd"].encode("utf-8")).hexdigest(),
                r["original_pbd_sha256"])
            self.assertEqual(r["proposed_activity_jawi"],ACTIVITY)
            self.assertEqual(r["proposed_pbd_jawi"],PBD)
            self.assertFalse(r["full_sp_completion_certified"])
            self.assertIsNone(r["teacher_selected_exact_ayah"])
            self.assertFalse(r["source_catalog_modified"])
            self.assertFalse(r["source_rpt_modified"])
            self.assertFalse(r["expert_quran_approved"])
            self.assertFalse(r["expert_jawi_approved"])
            self.assertFalse(r["can_publish"])

    def test_four_actions_and_assessment_record_selected_passage(self):
        steps=ACTIVITY.splitlines()
        self.assertEqual(len(steps),4)
        for n,line in enumerate(steps,1):
            self.assertTrue(line.startswith(f"{n}. "),line)
        self.assertIn("SP دان مصحف",ACTIVITY)
        self.assertIn("جولتن اية",ACTIVITY)
        self.assertIn("تسميع",ACTIVITY)
        self.assertIn("ڤبد تسميع اينديويدو",PBD)
        self.assertIn("بوكن ڤڠساسهن",PBD)
        self.assertNotIn("[DISAHKAN]",ACTIVITY+PBD)


if __name__=="__main__":
    unittest.main()
