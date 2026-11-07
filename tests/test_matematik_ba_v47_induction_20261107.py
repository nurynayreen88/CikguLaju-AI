"""Matematik v47 source-grounded set induksi quality check (staging only)."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "audits"
class MathV47InductionAudit(unittest.TestCase):
    def test_exactly_46_concrete_source_grounded_introductions(self):
        with (ROOT/"matematik_v47_46_set_induksi_terperinci_20261107.csv").open(
             encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),46)
        self.assertEqual(Counter(x["year"] for x in rows),
                         {"2":23,"3":10,"5":6,"6":7})
        self.assertEqual(len({x["lesson_id"] for x in rows}),46)
        for x in rows:
            with self.subTest(lesson=x["lesson_id"]):
                self.assertIn("Guru menunjukkan contoh konkrit berkaitan",
                              x["old_intro"])
                self.assertNotIn("contoh konkrit berkaitan",x["new_intro"])
                self.assertIn("Guru",x["new_intro"])
                self.assertIn("murid",x["new_intro"])
                self.assertTrue(x["existing_activity_1_evidence_excerpt"])
                self.assertGreater(len(x["new_intro"]),40)
                self.assertLess(len(x["new_intro"]),240)
                self.assertEqual(x["review_level"],
                                 "SOURCE_GROUNDED_EDITORIAL_REWRITE")
                self.assertEqual(x["academic_exercise_approved"],"NO")
    def test_release_remains_held_for_academic_checks(self):
        gate=json.loads((ROOT/"matematik_v47_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["QA_A4_one_page"],585)
        self.assertEqual(gate["concrete_intro_improved_count"],46)
        self.assertEqual(gate["BA_year2_3_effective_references"],234)
        self.assertEqual(len(gate["sha256"]),64)
        self.assertEqual(gate["academic_exercise_item_approved"],0)
        self.assertFalse(gate["year4_34_pair_signoff"])
        self.assertFalse(gate["actual_telegram_web_staging_E2E"])
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
if __name__=="__main__":
    unittest.main()
