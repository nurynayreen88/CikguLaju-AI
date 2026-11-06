"""Verify untouched v41 585-lesson matrix and legacy v27 candidate inventory."""
import csv
import unittest
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1] / "audits"


def load(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class BaEvidenceMatrixTests(unittest.TestCase):
    def test_all_585_v41_lessons_present_once(self):
        rows = load("matematik_ba_v41_585_ledger_20261107.csv")
        self.assertEqual(len(rows), 585)
        self.assertEqual(Counter(r["year"] for r in rows),
                         {str(y): 117 for y in range(2, 7)})
        ids = [r["v41_lesson_id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {
            f"T{year}-L{lesson:03d}"
            for year in range(2, 7) for lesson in range(1, 118)})

    def test_no_false_ba_release(self):
        rows = load("matematik_ba_v41_585_ledger_20261107.csv")
        for row in rows:
            with self.subTest(lesson=row["v41_lesson_id"]):
                self.assertEqual(row["approval"], "NOT_APPROVED")
                self.assertEqual(row["ready"], "NO")
                self.assertFalse(row["ba_exact_page"])
                self.assertFalse(row["ba_activity_ref"])

    def test_72_legacy_references_are_not_mapped(self):
        rows = load("matematik_ba_legacy_t2_v27_candidates_20261107.csv")
        self.assertEqual(len(rows), 72)
        self.assertEqual(len({r["legacy_rph_id"] for r in rows}), 72)
        self.assertTrue(all(r["candidate_printed_ba_pages"] for r in rows))
        self.assertTrue(all(
            r["v41_semantic_match_approved"] == "NO" and
            r["v41_lesson_id"] == "UNMAPPED_TO_V41" and
            r["release_status"] == "CANDIDATE_ONLY"
            for r in rows))


if __name__ == "__main__":
    unittest.main()
