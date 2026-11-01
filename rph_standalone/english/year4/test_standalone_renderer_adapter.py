"""Regression checks for English Year 4 Lesson 030 standalone adapter.

Run: python -m unittest discover -s rph_standalone/english/year4 -p 'test_standalone_renderer_adapter.py'
"""
import unittest
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
                self.assertTrue("PBD" in rendered or "Reinforcement" in rendered)

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
