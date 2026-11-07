"""Check that visually reviewed candidate snippets never count as RPH v41 approvals."""
import csv
from pathlib import Path
import unittest

CSV = Path(__file__).resolve().parents[1] / "audits/matematik_ba_9_visual_lesson_candidates_20261107.csv"

class VisualLessonCandidates(unittest.TestCase):
    def test_candidate_set_is_complete_and_unapproved(self):
        with CSV.open(encoding="utf-8", newline="") as f:
            records = list(csv.DictReader(f))
        self.assertEqual(len(records), 9)
        self.assertEqual(len({r["rpt_v28_lesson_candidate"] for r in records}), 9)
        self.assertEqual(sum(r["rpt_v28_lesson_candidate"].startswith("T2-") for r in records), 3)
        self.assertEqual(sum(r["rpt_v28_lesson_candidate"].startswith("T3-") for r in records), 6)
        for record in records:
            with self.subTest(lesson=record["rpt_v28_lesson_candidate"]):
                self.assertEqual(record["ba_page_inspected"], "YES")
                self.assertEqual(record["final_approval"], "NOT_APPROVED")
                self.assertEqual(record["rph_v41_actual_verified"], "NO_ASSET_UNAVAILABLE")
                self.assertTrue(record["printed_activity_label"])
                self.assertTrue(record["visual_observed_task"])
                self.assertTrue(record["book_printed_page"])
                self.assertTrue(record["pdf_page"])
