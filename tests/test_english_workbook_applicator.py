"""Regression tests for the opt-in Workbook addition tool.

Run: python -m unittest discover -s tests -p 'test_english_workbook_applicator.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from apply_verified_workbook import prepare


class WorkbookApplicatorTests(unittest.TestCase):
    SAMPLE = (
        "# English Year 3 — Lesson 94\n"
        "## Activity 2 — Role-play (25 minutes)\n"
        "Existing activity remains unchanged.\n\n"
        "## Assessment / PBD (10 minutes)\n"
        "**Teacher:** Check pupils' dialogue.\n"
        "**Pupils:** Perform a short exchange.\n\n"
        "## Closure (5 minutes)\n"
        "Existing closure remains unchanged.\n"
        "**QA:** NOT READY.\n"
    )

    def test_replaces_assessment_without_changing_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertEqual(updated.count("Workbook p.48, Activity 2"), 2)
        self.assertIn("**Teacher:** Check pupils' dialogue.", updated)
        self.assertIn("Existing closure remains unchanged.", updated)
        self.assertLess(updated.index("Workbook p.48"), updated.index("## Closure"))

    def test_workbook_replacement_ends_before_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("**Pupils:** Complete Workbook p.48, Activity 2.\n\n## Closure", updated)

    def test_repeat_application_is_idempotent(self):
        updated, _ = prepare(self.SAMPLE, 48, "Activity 2")
        again, status = prepare(updated, 48, "Activity 2")
        self.assertIsNone(again)
        self.assertEqual(status, "existing_workbook_reference")

    def test_existing_workbook_is_never_duplicated(self):
        original = self.SAMPLE.replace(
            "**Pupils:** Perform a short exchange.",
            "**Pupils:** Complete Workbook p.48, Activity 2.")
        updated, status = prepare(original, 48, "Activity 2")
        self.assertIsNone(updated)
        self.assertEqual(status, "existing_workbook_reference")

    def test_non_textbook_lesson_is_never_auto_modified(self):
        original = self.SAMPLE.replace(
            "## Assessment / PBD",
            "**Audited source mapping:** NON-TEXTBOOK / SOW task.\n\n## Assessment / PBD"
        )
        updated, status = prepare(original, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("Workbook p.48", updated)

    def test_no_assessment_means_no_change(self):
        updated, status = prepare("# Lesson\n## Activity 1\nText\n", 48, "Activity 2")
        self.assertIsNone(updated)
        self.assertEqual(status, "assessment_heading_missing")


if __name__ == "__main__":
    unittest.main()
