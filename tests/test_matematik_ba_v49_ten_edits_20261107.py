"""v49 source-grounded fixes: BNM RM1 brackets and 20-minute duplicate labels."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"audits"
def rows():
    with (ROOT/"matematik_v49_10_section_fixes_20261107.csv").open(encoding="utf8",newline="") as f:
        return list(csv.DictReader(f))

class MathsV49Audit(unittest.TestCase):
    def test_ten_edits_nine_lessons(self):
        r=rows()
        self.assertEqual(len(r),10)
        self.assertEqual(len({x["lesson_id"] for x in r}),9)
        self.assertEqual(Counter(x["issue"] for x in r),
            {"REDUNDANT_DURATION_LABEL":7,
             "RM1_BNM_BRACKET_1_MALAYSIAN_RINGGIT":3})
        for x in r:
            with self.subTest(lesson=x["lesson_id"],section=x["section"]):
                self.assertNotEqual(x["before"],x["after"])
                self.assertEqual(x["teacher_signoff"],"PENDING")
                if x["issue"]=="REDUNDANT_DURATION_LABEL":
                    self.assertIn("(20 minit)",x["before"])
                    self.assertNotIn("(20 minit)",x["after"])
                else:
                    self.assertIn("=1 Malaysian ringgit",x["after"])
                    self.assertIn("BNM",x["after"])
                    self.assertIn("RM1",x["after"])
    def test_release_academic_hold(self):
        g=json.loads((ROOT/"matematik_v49_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(g["rph_total"],585)
        self.assertEqual(g["changed_sections"],10)
        self.assertEqual(len(g["changed_lessons"]),9)
        self.assertEqual(g["unchanged_rph_count"],576)
        self.assertEqual(g["BA_year2_3_references"],234)
        self.assertEqual(g["PDF_A4_onepage"],585)
        self.assertEqual(g["academic_item_level_approved"],0)
        self.assertFalse(g["final_ready"])
        self.assertFalse(g["production_modified"])
        self.assertFalse(g["real_Telegram_Web_staging_E2E"])
if __name__=="__main__":
    unittest.main()
