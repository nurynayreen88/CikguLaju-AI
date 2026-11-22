"""Keep KP2027 Year 1 Math source-search uncertainty explicit until final DK is read."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1"
AUDIT = ROOT / "math_original_dk_search_audit_20261108.json"

class Year1MathDkSearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_original_dk_not_misrepresented(self):
        a = self.a
        self.assertEqual(a["result"], "ORIGINAL_COMPLETE_DK_NOT_RETRIEVED")
        self.assertEqual(a["release_status"], "SOURCE_HOLD_NOT_READY")
        self.assertFalse(a["caveats"]["official_final_DK_confirmed"])
        self.assertTrue(a["caveats"]["folder_empty_means_no_visible_child_not_proof_of_global_nonexistence"])
        self.assertTrue(a["caveats"]["KSSR_2017_Math_not_authorized_as_KP2027_source"])
        self.assertGreaterEqual(len(a["important_evidence"]), 10)
        self.assertTrue(all(not x["exact_DK_SP_text_provided"] for x in a["important_evidence"]))

    def test_conflict_is_unresolved_and_no_fabrication(self):
        c = self.a["source_conflict"]
        self.assertEqual(c["overall_SP_count_claim_in_comparison_slides"], 30)
        self.assertEqual(c["sum_of_topic_panel_counts"], 28)
        self.assertEqual(c["group_assignment_code_count"], 30)
        self.assertEqual(c["unresolved_count_difference"], 2)
        self.assertEqual(c["concentrated_topic"], "Wang")
        self.assertFalse(c["source_discrepancy_resolved"])
        self.assertEqual(c["original_DK_pages_verified"], 0)
        self.assertEqual(c["assumed_sp_texts_added"], 0)

    def test_official_time_schedule_evidence_does_not_publish(self):
        a = self.a
        policy = next(x for x in a["important_evidence"] if x["kind"] == "KPM_PARLIAMENTARY_WRITTEN_ANSWER")
        self.assertEqual(policy["date"], "2026-02-24")
        self.assertFalse(policy["exact_DK_SP_text_provided"])
        training = next(x for x in a["important_evidence"] if x["kind"] == "TRAINING_KP2027_COMPARISON_PDF")
        self.assertIn("30min", training["observation"])
        self.assertEqual(a["governance"]["material_ready_count"], 0)
        for k in ["change_main_database","change_telegram","change_web","change_production","merge_draft_pr"]:
            self.assertFalse(a["governance"][k])

if __name__ == "__main__":
    unittest.main()
