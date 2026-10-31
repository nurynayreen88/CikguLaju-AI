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
        self.assertNotIn("**Teacher:** Check pupils' dialogue.", updated)
        self.assertIn("Existing closure remains unchanged.", updated)
        self.assertLess(updated.index("Workbook p.48"), updated.index("## Closure"))

    def test_workbook_replacement_ends_before_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("**Pupils:** Complete Workbook p.48, Activity 2.\n\n## Closure", updated)

    def test_preserves_original_activity_and_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertEqual(updated.split("## Assessment / PBD")[0], self.SAMPLE.split("## Assessment / PBD")[0])
        self.assertEqual(updated.split("## Closure")[1], self.SAMPLE.split("## Closure")[1])

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
        self.assertIsNone(updated)
        self.assertEqual(status, "non_textbook_sow_task")

    def test_reinforcement_pbd_heading_is_supported(self):
        original = self.SAMPLE.replace(
            "## Assessment / PBD", "## Reinforcement / PBD"
        )
        updated, status = prepare(original, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("Workbook p.48, Activity 2", updated)
        self.assertIn("Existing closure remains unchanged.", updated)

    def test_no_assessment_means_no_change(self):
        updated, status = prepare("# Lesson\n## Activity 1\nText\n", 48, "Activity 2")
        self.assertIsNone(updated)
        self.assertEqual(status, "assessment_heading_missing")


class WorkbookMappingRegressionTests(unittest.TestCase):
    """Guard manually verified Year 3 mappings from accidental reversion."""

    ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year3"

    @classmethod
    def lesson(cls, number):
        return (cls.ROOT / f"lesson_{number:03d}.md").read_text(encoding="utf-8")

    @staticmethod
    def pbd(source):
        start = source.index("## Assessment / PBD")
        end = source.find("\n## ", start + 3)
        return source[start:] if end < 0 else source[start:end]

    def test_lesson_070_does_not_assess_ownership_with_location_workbook(self):
        pbd = self.pbd(self.lesson(70))
        self.assertIn("Whose", pbd)
        self.assertNotIn("Direct pupils to Workbook p.37", pbd)

    def test_lesson_075_requires_matching_listening_recording(self):
        pbd = self.pbd(self.lesson(75))
        self.assertIn("Workbook p.37, Activity 1", pbd)
        self.assertIn("matching recording", pbd)
        self.assertIn("draw lines", pbd)

    def test_lesson_067_uses_printed_story_picture_sentences(self):
        pbd = self.pbd(self.lesson(67))
        self.assertIn("Workbook p.39, Activity 1", pbd)
        self.assertIn("Picture 1–4", pbd)

    def test_lesson_052_uses_days_not_seasons_calendar(self):
        pbd = self.pbd(self.lesson(52))
        self.assertIn("Workbook p.27, Activity 3", pbd)
        self.assertNotIn("Workbook p.30, Activity 1", pbd)

    def test_lesson_054_uses_activity_day_task(self):
        pbd = self.pbd(self.lesson(54))
        self.assertIn("Workbook p.27, Activity 1", pbd)
        self.assertNotIn("Workbook p.29, Activity 2", pbd)

    def test_lesson_087_workbook_pbd_sentence_is_complete(self):
        pbd = self.pbd(self.lesson(87))
        self.assertIn("Workbook p.45, Activity 2", pbd)
        self.assertIn("omelettes.", pbd)
        self.assertNotIn("by answering 'Is there any.", pbd)

    def test_lesson_078_checks_possessives_not_furniture_locations(self):
        pbd = self.pbd(self.lesson(78))
        self.assertIn("Workbook p.40, Activity 1", pbd)
        self.assertIn("possessive", pbd)


    def test_lesson_151_uses_verified_personal_questions_on_page_79(self):
        pbd = self.pbd(self.lesson(151))
        self.assertIn("Workbook p.79, Activity 2", pbd)
        self.assertIn("answer about yourself", pbd)
        self.assertNotIn("choosing the correct comparative adjectives", pbd)

    def test_lesson_156_uses_superlative_personal_questions(self):
        pbd = self.pbd(self.lesson(156))
        self.assertIn("Workbook p.79, Activity 2", pbd)
        self.assertIn("superlative", pbd)
        self.assertNotIn("comparative adjectives to describe", pbd)

    def test_lesson_153_uses_verified_page_80_crossword(self):
        pbd = self.pbd(self.lesson(153))
        self.assertIn("Workbook p.80, Activity 2", pbd)
        self.assertIn("crossword", pbd)

    def test_lesson_155_does_not_count_crossword_as_listening(self):
        pbd = self.pbd(self.lesson(155))
        self.assertIn("Workbook p.80, Activity 2", pbd)
        self.assertIn("crossword", pbd)
        self.assertIn("not as listening evidence", pbd)

    def test_lesson_152_planet_labels_are_not_reading_evidence(self):
        pbd = self.pbd(self.lesson(152))
        self.assertIn("Workbook p.80, Activity 1", pbd)
        self.assertIn("not as the sole reading assessment", pbd)

    def test_lesson_159_uses_verified_story_character_matching(self):
        pbd = self.pbd(self.lesson(159))
        self.assertIn("Workbook p.81, Activity 1", pbd)
        self.assertIn("matching the story characters", pbd)



if __name__ == "__main__":
    unittest.main()
