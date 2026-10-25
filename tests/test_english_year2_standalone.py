"""Smoke tests for Year 2 English standalone lesson plans."""
import unittest
from english_standalone_adapter import load_english_rph, get_english_rph, resolve_rph_with_fallback

class EnglishYear2Tests(unittest.TestCase):
    def test_all_lessons(self):
        for number in range(1, 161):
            with self.subTest(lesson=number):
                text = load_english_rph(2, number)
                self.assertIsNotNone(text)
                self.assertIn("Assessment", text)
                self.assertIn("Closure", text)

    def test_subjects_and_fallback(self):
        for name in ("English", "BI", "Bahasa Inggeris"):
            self.assertIsNotNone(get_english_rph(2, name, 80))
        self.assertIsNone(get_english_rph(3, "English", 1))
        self.assertEqual(resolve_rph_with_fallback(2, "Math", 1, lambda: "legacy"), "legacy")
        self.assertIn("Lesson 160", resolve_rph_with_fallback(2, "English", 160, lambda: "legacy"))

if __name__ == "__main__":
    unittest.main()
