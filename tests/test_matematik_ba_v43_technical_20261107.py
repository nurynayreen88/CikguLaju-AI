"""CI check: 585 math RPH passed structural QA, never infer academic approval.

The 49MB proprietary classroom bundle is intentionally not committed to GitHub.
"""
import csv
import unittest
from collections import Counter
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "audits/matematik_v43_585_technical_qa_20261107.csv"

class MatematikV43TechnicalQATests(unittest.TestCase):
    def test_every_year_117_lessons(self):
        with FILE.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 585)
        self.assertEqual(Counter(int(r["year"]) for r in rows), {y:117 for y in range(2,7)})
        self.assertEqual(len({(r["year"],r["lesson"]) for r in rows}),585)
        for r in rows:
            with self.subTest(year=r["year"],lesson=r["lesson"]):
                for field in ("a4","pdf_contains_sp","docx_contains_sp","pdf_activity_labels","title_bold"):
                    self.assertEqual(r[field],"True")
                self.assertEqual(r["pdf_pages"],"1")
                self.assertEqual(r["min_total"],"60")
                self.assertEqual(r["stage_verification"],"AUTOMATIC_ONLY")
                self.assertGreaterEqual(int(r["number_of_sp"]),1)
                self.assertEqual(r["ba_reference"]=="True", int(r["year"]) in (2,3))

if __name__=="__main__":
    unittest.main()
