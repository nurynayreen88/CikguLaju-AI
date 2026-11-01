"""Regression checks for English Year 4 Lesson 030 standalone adapter.

Run: python -m unittest discover -s rph_standalone/english/year4 -p 'test_standalone_renderer_adapter.py'
"""
import unittest
import re
from pathlib import Path
from standalone_renderer_adapter import adapt_year4_standalone


class Lesson030AdapterTest(unittest.TestCase):
    def test_all_160_lessons_preserve_core_sections(self):
        from standalone_renderer_adapter import adapt_year4_standalone
        folder = Path(__file__).parent
        for lesson_no in range(1, 161):
            with self.subTest(lesson=lesson_no):
                original = (folder / f"lesson_{lesson_no:03d}.md").read_text(encoding="utf-8")
                rendered = adapt_year4_standalone(original)
                for field in ("TOPIC:", "MAIN LEARNING STANDARD:", "COMPLEMENTARY LEARNING STANDARD:",
                              "STANDARD PEMBELAJARAN:", "SET INDUCTION:", "MAIN ACTIVITIES:", "CLOSURE:"):
                    self.assertIn(field, rendered)
                self.assertIn("Activity 1", rendered)
                self.assertIn("Activity 2", rendered)
                main_activities = rendered.split("MAIN ACTIVITIES:\n", 1)[1].split("\nCLOSURE:", 1)[0]
                self.assertRegex(main_activities, r"(?im)^(?:PBD|Reinforcement)\b")
                self.assertIn("Activity 1", main_activities)
                self.assertIn("Activity 2", main_activities)
                self.assertLess(main_activities.index("Activity 1"), main_activities.index("Activity 2"))
                # Validate nonempty content between actual renderer field headers.
                for field in ("TOPIC", "MAIN LEARNING STANDARD", "COMPLEMENTARY LEARNING STANDARD",
                              "SET INDUCTION", "MAIN ACTIVITIES", "CLOSURE"):
                    match = re.search(r"(?ms)^" + re.escape(field) +
                                      r":\n(.*?)(?=^[A-Z][A-Z ]+:\n|\Z)", rendered)
                    self.assertIsNotNone(match, f"Missing {field} in lesson {lesson_no}")
                    self.assertTrue(match.group(1).strip(), f"Empty {field} in lesson {lesson_no}")

    def test_legacy_lesson_001_keeps_third_activity_and_excludes_qa(self):
        original = (Path(__file__).parent / "lesson_001.md").read_text(encoding="utf-8")
        rendered = adapt_year4_standalone(original)
        for expected in (
            "TOPIC:\n1 — Where are you from?",
            "Listening 1.2 / 1.2.2",
            "Listening 1.1 / 1.1.1",
            "Class CD1 Track 3",
            "LEARNING OBJECTIVES:\nPupils listen for country/name information",
            "Activity 1 — Flag vocabulary",
            "Activity 2 — Listen and write",
            "Activity 3 — Malaysian flag listening",
            "PBD / Reinforcement",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
        self.assertLess(rendered.index("Activity 2 — Listen"), rendered.index("Activity 3 — Malaysian"))
        self.assertNotIn("Verified mapping and limits", rendered)
        self.assertNotIn("NOT READY FOR RELEASE", rendered)

    def test_lesson_070_resources_preserved(self):
        original = (Path(__file__).parent / "lesson_070.md").read_text(encoding="utf-8")
        rendered = adapt_year4_standalone(original)
        self.assertIn("TEACHING AND LEARNING MATERIALS:\nSB pp.52–53", rendered)
        self.assertIn("TB pp.82–83", rendered)

    def test_separate_audio_metadata_preserved(self):
        source = "\n".join([
            "**Topic:** Test topic",
            "**Main SP:** Listening 1.2.2",
            "**Complementary SP:** Speaking 2.1.1",
            "**Materials:** Student's Book p.5",
            "**Audio:** CD1 Track 4 (Activity 3 dialogue)",
            "## Set induction", "Warm-up",
            "## Activity 1", "Task",
            "## Activity 2", "Task",
            "## PBD / Reinforcement", "Assess",
            "## Closure", "End",
        ])
        rendered = adapt_year4_standalone(source)
        self.assertIn("Student's Book p.5", rendered)
        self.assertIn("Audio: CD1 Track 4 (Activity 3 dialogue)", rendered)
        self.assertEqual(rendered.count("Audio: CD1 Track 4"), 1)

    def test_audio_not_duplicated_when_already_in_references(self):
        source = "\n".join([
            "**Topic:** Test topic",
            "**Main SP:** Listening 1.2.2",
            "**Complementary SP:** Speaking 2.1.1",
            "**References:** SB p.5; CD1 Track 4 (Activity 3 dialogue)",
            "**Audio:** CD1 Track 4 (Activity 3 dialogue)",
            "## Set induction", "Warm-up",
            "## Activity 1", "Task",
            "## Activity 2", "Task",
            "## PBD / Reinforcement", "Assess",
            "## Closure", "End",
        ])
        rendered = adapt_year4_standalone(source)
        self.assertEqual(rendered.count("CD1 Track 4 (Activity 3 dialogue)"), 1)

    def test_qa_notes_are_not_exported_into_rph(self):
        source = "\n".join([
            "**Topic:** Test topic",
            "**Main SP:** Writing 4.3.2",
            "**Complementary SP:** Listening 1.2.5",
            "## Set induction (5 minutes)", "Teacher: Warm-up",
            "## Activity 1 (15 minutes)", "Pupils: First task",
            "## Activity 2 (20 minutes)", "Pupils: Second task",
            "## PBD / Reinforcement (10 minutes)", "Teacher: Assess pupils",
            "## Closure (5 minutes)", "Teacher: Summarise",
            "## Source mapping and QA", "INTERNAL_QA_ONLY_DO_NOT_EXPORT",
        ])
        result = adapt_year4_standalone(source)
        self.assertIn("Teacher: Summarise", result)
        self.assertNotIn("INTERNAL_QA_ONLY_DO_NOT_EXPORT", result)
        self.assertNotIn("Source mapping and QA", result)

    def test_pbd_heading_variants(self):
        from standalone_renderer_adapter import adapt_year4_standalone
        for heading in (
            "PBD / Reinforcement (5 minutes)",
            "PBD / reinforcement (10 minutes)",
            "Reinforcement / PBD (10 minutes)",
            "Reinforcement and PBD (10 minutes)",
        ):
            with self.subTest(heading=heading):
                source = "\n".join(["## Set induction (10 minutes)", "Warm-up", "", "## Activity 1 (15 minutes)", "Task", "", "## " + heading, "Teacher checks responses", "", "## Closure (5 minutes)", "End"])
                result = adapt_year4_standalone(source)
                self.assertIn(heading, result)
                self.assertIn("Teacher checks responses", result)

    def test_preserves_activity_workbook_audio_and_pbd(self):
        original = (Path(__file__).parent / "lesson_030.md").read_text(encoding="utf-8")
        rendered = adapt_year4_standalone(original)
        for expected in (
            "SET INDUCTION:", "MAIN ACTIVITIES:", "CLOSURE:", "ASSESSMENT:",
            "Activity 1 (15 minutes)", "Activity 2 (20 minutes)",
            "Reinforcement and PBD (10 minutes)",
            "Workbook p.14, Activity 1", "CD1 Track 29",
            "Writing 4.3.2", "Listening 1.2.5",
            "Teacher:", "Pupils:", "LEARNING STANDARD:", "STANDARD PEMBELAJARAN:",
            "Main: Writing 4.3.2", "Complementary: Listening 1.2.5",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
        self.assertLess(rendered.index("Activity 1 (15 minutes)"), rendered.index("Activity 2 (20 minutes)"))
        self.assertLess(rendered.index("Activity 2 (20 minutes)"), rendered.index("Reinforcement and PBD (10 minutes)"))
        self.assertEqual(rendered.count("Workbook p.14, Activity 1"), 1)
        self.assertIn("SET INDUCTION:\n", rendered)
        self.assertIn("CLOSURE:\n", rendered)
        self.assertIn("Main: Writing 4.3.2\nComplementary: Listening 1.2.5", rendered)
        self.assertIn("STANDARD PEMBELAJARAN:\nMain: Writing 4.3.2\nComplementary: Listening 1.2.5", rendered)
        self.assertIn("MAIN LEARNING STANDARD:\nWriting 4.3.2", rendered)
        self.assertIn("COMPLEMENTARY LEARNING STANDARD:\nListening 1.2.5", rendered)


if __name__ == "__main__":
    unittest.main()
