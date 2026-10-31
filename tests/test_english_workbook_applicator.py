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

    def test_appends_workbook_without_replacing_assessment(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertEqual(updated.count("Workbook p.48, Activity 2"), 1)
        self.assertIn("**Teacher:** Check pupils' dialogue.", updated)
        self.assertIn("**Pupils:** Perform a short exchange.", updated)
        self.assertIn("Existing closure remains unchanged.", updated)
        self.assertLess(updated.index("**Workbook practice:**"), updated.index("## Closure"))

    def test_workbook_addition_ends_before_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("Teacher checks answers and provides guidance.\n\n## Closure", updated)

    def test_preserves_original_activity_and_closure(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertEqual(updated.split("## Assessment / PBD")[0], self.SAMPLE.split("## Assessment / PBD")[0])
        self.assertEqual(updated.split("## Closure")[1], self.SAMPLE.split("## Closure")[1])

    def test_original_pbd_is_preserved_verbatim(self):
        updated, status = prepare(self.SAMPLE, 48, "Activity 2")
        self.assertEqual(status, "ready")
        original_pbd = self.SAMPLE.split("## Assessment / PBD (10 minutes)\\n", 1)[1].split("## Closure", 1)[0]
        updated_pbd = updated.split("## Assessment / PBD (10 minutes)\\n", 1)[1].split("**Workbook practice:**", 1)[0]
        self.assertEqual(updated_pbd, original_pbd)
        self.assertEqual(updated.count("**Workbook practice:**"), 1)

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

    def test_plain_pbd_heading_is_supported_without_replacement(self):
        original = self.SAMPLE.replace("## Assessment / PBD", "## PBD")
        updated, status = prepare(original, 48, "Activity 2")
        self.assertEqual(status, "ready")
        self.assertIn("**Teacher:** Check pupils' dialogue.", updated)
        self.assertIn("**Pupils:** Perform a short exchange.", updated)
        self.assertEqual(updated.count("**Workbook practice:**"), 1)

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
        start = next((source.index(h) for h in ("## Assessment / PBD", "## Reinforcement / PBD", "## PBD") if h in source), -1)
        if start < 0:
            raise AssertionError("PBD heading missing")
        end = source.find("\n## ", start + 3)
        return source[start:] if end < 0 else source[start:end]

    def test_lesson_070_does_not_assess_ownership_with_location_workbook(self):
        pbd = self.pbd(self.lesson(70))
        self.assertIn("Workbook p.37, Activity 2 covers object locations rather than ownership", pbd)
        self.assertNotIn("Direct pupils to Workbook p.37", pbd)

    def test_lesson_075_requires_matching_listening_recording(self):
        pbd = self.pbd(self.lesson(75))
        self.assertIn("Workbook p.37, Activity 1", pbd)
        self.assertIn("Listen and draw lines", pbd)
        self.assertIn("connecting the objects", pbd)

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
        self.assertIn("written answers about themselves", pbd)
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
        self.assertIn("crossword using its printed clues", pbd)
        self.assertIn("spoken planet questions", pbd)

    def test_lesson_152_planet_labels_are_not_reading_evidence(self):
        pbd = self.pbd(self.lesson(152))
        self.assertIn("Workbook p.80, Activity 1", pbd)
        self.assertIn("Teacher checks the order of planets from the text", pbd)

    def test_lesson_157_planet_labelling_is_not_reading_comprehension(self):
        pbd = self.pbd(self.lesson(157))
        self.assertIn("Workbook p.80, Activity 1", pbd)
        self.assertIn("Teacher checks each pair\'s sequence of model instructions", pbd)

    def test_lesson_160_project_assessment_is_not_overwritten(self):
        pbd = self.pbd(self.lesson(160))
        self.assertIn("revised animal description", pbd)
        self.assertIn("picture-to-text match", pbd)
        self.assertNotIn("Direct pupils to Workbook", pbd)

    def test_lesson_145_uses_written_comparative_forms(self):
        pbd = self.pbd(self.lesson(145))
        self.assertIn("Workbook p.76, Activity 1", pbd)
        self.assertIn("writing comparative adjective forms", pbd)

    def test_lesson_147_uses_picture_vocabulary(self):
        pbd = self.pbd(self.lesson(147))
        self.assertIn("Workbook p.78, Activity 1", pbd)
        self.assertIn("close, far, around and planet", pbd)

    def test_lesson_148_uses_comparative_sentences(self):
        pbd = self.pbd(self.lesson(148))
        self.assertIn("Workbook p.77, Activity 2", pbd)
        self.assertIn("writing comparative sentences", pbd)

    def test_lesson_150_requires_matching_audio(self):
        pbd = self.pbd(self.lesson(150))
        self.assertIn("Workbook p.78, Activity 2", pbd)
        self.assertIn("If the matching recording is verified and available", pbd)
        self.assertIn("number the three monsters", pbd)
        self.assertIn("If the matching recording is verified and available", pbd)
        self.assertIn("do not treat the Workbook audio task as completed", pbd)

    def test_lesson_150_keeps_audio_unverified_when_recording_missing(self):
        pbd = self.pbd(self.lesson(150))
        self.assertIn("Otherwise, respond to the teacher's spoken comparison descriptions", pbd)
        self.assertIn("do not treat the Workbook audio task as completed", pbd)

    def test_lesson_159_uses_verified_story_character_matching(self):
        pbd = self.pbd(self.lesson(159))
        self.assertIn("Workbook p.81, Activity 1", pbd)
        self.assertIn("matching the story characters", pbd)



if __name__ == "__main__":
    unittest.main()
