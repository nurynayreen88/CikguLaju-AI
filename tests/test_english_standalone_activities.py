"""Regression tests for the non-destructive English RPH activity merge.

Run: python -m unittest discover -s tests -p 'test_english_standalone_activities.py'
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_english_standalone_rph import build
from merge_english_standalone_activity_proposals import merge_records


class EnglishStandaloneActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = build()
        cls.merged, cls.stats = merge_records(cls.original)

    def test_unique_lessons(self):
        keys = [(r["year"], r["lesson_no"]) for r in self.merged]
        self.assertEqual(len(keys), len(set(keys)))

    def test_original_activities_are_unchanged(self):
        for before, after in zip(self.original, self.merged):
            for activity in before["activities"]:
                self.assertIn(activity, after["activities"])

    def test_all_supplements_are_explicitly_provisional(self):
        for record in self.merged:
            for activity in record["activities"]:
                if activity.get("provenance") == "TEACHER_DEVELOPED_PROPOSAL_NOT_TB":
                    self.assertEqual(activity["review_status"], "PENDING_PEDAGOGICAL_REVIEW")
                    self.assertFalse(record["activity_quality"]["ready_for_teacher_review"])

    def test_no_duplicate_phases(self):
        for record in self.merged:
            phases = [a["phase"] for a in record["activities"]]
            self.assertEqual(len(phases), len(set(phases)))

    def test_core_phases_present_in_current_source_batch(self):
        self.assertEqual(len(self.merged), 51)
        for record in self.merged:
            self.assertFalse(record["activity_quality"]["missing_phases"], record["lesson_no"])

    def test_no_unmatched_or_conflicting_proposals(self):
        self.assertEqual(self.stats["unmatched_proposals"], [])
        self.assertEqual(self.stats["conflicting_proposals"], [])


if __name__ == "__main__":
    unittest.main()
