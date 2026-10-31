"""Regression checks for English Year 4 Lesson 030 standalone adapter.

Run: python -m unittest discover -s rph_standalone/english/year4 -p 'test_standalone_renderer_adapter.py'
"""
import unittest
from pathlib import Path
from standalone_renderer_adapter import adapt_year4_standalone


class Lesson030AdapterTest(unittest.TestCase):
    def test_preserves_activity_workbook_audio_and_pbd(self):
        original = (Path(__file__).parent / "lesson_030.md").read_text(encoding="utf-8")
        rendered = adapt_year4_standalone(original)
        for expected in (
            "SET INDUCTION:", "MAIN ACTIVITIES:", "CLOSURE:", "ASSESSMENT:",
            "Activity 1 (15 minutes)", "Activity 2 (20 minutes)",
            "Reinforcement and PBD (10 minutes)",
            "Workbook p.14, Activity 1", "CD1 Track 29",
            "Writing 4.3.2", "Listening 1.2.5",
            "Teacher:", "Pupils:", "LEARNING STANDARD:",
            "Main: Writing 4.3.2", "Complementary: Listening 1.2.5",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
        self.assertLess(rendered.index("Activity 1 (15 minutes)"), rendered.index("Activity 2 (20 minutes)"))
        self.assertLess(rendered.index("Activity 2 (20 minutes)"), rendered.index("Reinforcement and PBD (10 minutes)"))
        self.assertEqual(rendered.count("Workbook p.14, Activity 1"), 1)
        self.assertIn("SET INDUCTION:\n", rendered)
        self.assertIn("CLOSURE:\n", rendered)


if __name__ == "__main__":
    unittest.main()
