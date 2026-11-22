"""Audit the Year 1 SK listening lesson candidate source gate and Matematik evidence conflict."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1"

def data(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))

class Year1TrainingAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bm = data("bm_sk_listening_7_source_grounded_rph_20261107.json")
        cls.math = data("math_2027_source_count_reconciliation_20261107.json")

    def test_bm_listening_sp_codes_are_exact_and_sk_only(self):
        rows = self.bm["records"]
        expected = {"1.1.1", "1.1.2", "1.1.3", "1.2.1", "1.2.2", "1.2.3", "1.2.4"}
        self.assertEqual({r["sp_training_code"] for r in rows}, expected)
        self.assertEqual(len(rows), 7)
        self.assertEqual(len({r["id"] for r in rows}), 7)
        self.assertEqual(self.bm["school_type"], "SK")
        self.assertEqual(self.bm["status"], "REVIEW_DRAFT_NOT_READY")
        self.assertFalse(self.bm["release_gates"]["source_is_final_dk"])
        for r in rows:
            with self.subTest(rph=r["id"]):
                self.assertEqual(r["school_type"], "SK")
                self.assertEqual(r["status"], "DRAFT_HOLD_NOT_READY")
                self.assertFalse(r["standard_text_is_official_final_dk"])
                self.assertIsNone(r["planned_duration_minutes"])
                for key in ("official_sk", "official_sp", "official_spi"):
                    self.assertIsNone(r[key])
                for key in ("approved_by_teacher", "approved_for_web", "approved_for_telegram", "rpt_scheduled"):
                    self.assertIs(r[key], False)
                self.assertTrue(all(1 <= n <= 118 for n in r["sp_source_pages_pdf_one_based"]))
                self.assertEqual(len(r["stages"]), 4)
                self.assertEqual([x["phase"] for x in r["stages"]],
                    ["Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/PBD dan penutup"])
                for s in r["stages"]:
                    self.assertGreater(len(s["teacher_action"]), 65)
                    self.assertGreater(len(s["pupil_action"]), 55)
                self.assertTrue(r["formative_assessment"])
                self.assertTrue(r["materials"])
        sk = {r["sp_training_code"]: r["sp_training_text"] for r in rows}
        self.assertIn("arahan secara sopan", sk["1.2.3"])
        self.assertIn("situasi di rumah dan di sekolah", sk["1.2.3"])
        self.assertNotIn("arahan dan pertanyaan", sk["1.2.3"])
        self.assertIn("pertanyaan secara sopan", sk["1.2.4"])
        self.assertEqual(self.bm["source"]["sha256"], "447b499db78253c4c3f0559afa791691a010c58d076666917a060531b9637691")

    def test_math_source_discrepancy_stays_visible(self):
        r = self.math
        self.assertEqual(r["status"], "SOURCE_COUNT_CONFLICT_HOLD")
        self.assertEqual(len(r["rows"]), 7)
        self.assertEqual(sum(x["slide_count"] for x in r["rows"]), 28)
        self.assertEqual(sum(x["assignment_code_count"] for x in r["rows"]), 30)
        self.assertEqual(r["reconciliation"]["difference"], 2)
        self.assertEqual(r["source_A"]["training_general_claim"], 30)
        self.assertEqual(r["source_A"]["periods_per_week"], 7)
        self.assertEqual(r["source_A"]["minutes_per_period"], 30)
        self.assertTrue(r["publishing"]["release_blocked"])
        self.assertFalse(r["publishing"]["rpt_ready"])
        self.assertFalse(r["publishing"]["rph_ready"])
        diff = [x for x in r["rows"] if x["slide_count"] != x["assignment_code_count"]]
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["topic"], "Wang")
        self.assertEqual(diff[0]["slide_count"], 2)
        self.assertEqual(diff[0]["assignment_code_count"], 4)
        self.assertEqual(diff[0]["code_list"], ["3.1.1", "3.2.1", "3.2.2", "3.2.3"])
        self.assertFalse(r["reconciliation"]["auto_relabel_or_delete_codes"])

    def test_alam_manusia_model_is_review_only_and_timings_consistent(self):
        doc = data("alam_manusia_pasukan_keselamatan_team_teaching_20261107.json")
        self.assertEqual(doc["status"], "REVIEW_DRAFT_NOT_READY")
        self.assertFalse(doc["source"]["reference_codes"][0]["final_dk_verified"])
        self.assertEqual([x["code"] for x in doc["source"]["reference_codes"]], ["3.1.11", "3.1.12"])
        rph = doc["rph"]
        self.assertEqual(rph["class_size_example"], 30)
        self.assertEqual(rph["proposed_duration_minutes"], 60)
        self.assertEqual(sum(step["minutes"] for step in rph["stages"]), 60)
        self.assertEqual(len(rph["stages"]), 5)
        self.assertIsNone(rph["official_sk"])
        self.assertIsNone(rph["official_sp"])
        self.assertIsNone(rph["official_spi"])
        self.assertIsNone(rph["assessment"]["tp_claimed"])
        self.assertFalse(rph["approved_by_teacher"])
        self.assertFalse(rph["approved_for_web"])
        self.assertFalse(rph["approved_for_telegram"])
        self.assertFalse(rph["rpt_scheduled"])
        for stage in rph["stages"]:
            self.assertTrue(stage["teacher_A"])
            self.assertTrue(stage["teacher_B"])
            self.assertTrue(stage["pupils"])


if __name__ == "__main__":
    unittest.main()
