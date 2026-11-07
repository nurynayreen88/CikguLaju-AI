"""BA item-semantic sample reviews must be documented without silently approving release."""
import csv
from pathlib import Path
import unittest

FILE=Path(__file__).resolve().parents[1]/"audits/matematik_v45_4_item_semantic_samples_20261107.csv"

class FourPageLevelSamples(unittest.TestCase):
    def test_samples_source_sp_and_teacher_gate(self):
        with FILE.open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),4)
        self.assertEqual({r["lesson_id"] for r in rows},
            {"T2-L063","T2-L064","T3-L100","T3-L101"})
        for r in rows:
            with self.subTest(lesson=r["lesson_id"]):
                offset=6 if r["ba_year"]=="2" else 3
                self.assertEqual(int(r["pdf_page"]),int(r["printed_page"])+offset)
                self.assertTrue(r["observed_task"])
                self.assertTrue(r["lesson_objective_link"])
                self.assertEqual(r["judgement"],"EXERCISE_CONTENT_ALIGNING_WITH_SP")
                self.assertEqual(r["release_approval"],"PENDING_TEACHER_SIGNOFF")
                self.assertRegex(r["sp"],r"^\d+\.\d+\.\d+$")

if __name__=="__main__":
    unittest.main()
