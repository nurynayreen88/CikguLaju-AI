"""Minimal smoke tests for the read-only English Year 1 RPH adapter."""
import unittest

from english_standalone_adapter import get_english_y1_rph, load_english_y1_rph


class EnglishStandaloneAdapterTests(unittest.TestCase):
    def test_all_160_lessons_load(self):
        for n in range(1, 161):
            with self.subTest(lesson=n):
                text = load_english_y1_rph(n)
                self.assertIsNotNone(text)
                self.assertRegex(text, r"(?i)lesson")
                self.assertRegex(text, r"(?i)closure")
                self.assertRegex(text, r"(?i)(pbd|assessment)")

    def test_guard_other_year_and_subject(self):
        self.assertIsNone(get_english_y1_rph(2, "English", 1))
        self.assertIsNone(get_english_y1_rph(1, "Matematik", 1))
        self.assertIsNone(get_english_y1_rph(1, "English", 0))
        self.assertIsNone(get_english_y1_rph(1, "English", 161))
        self.assertIsNone(get_english_y1_rph(1, "English", "../1"))

    def test_aliases(self):
        for name in ("English", "Bahasa Inggeris", "BI"):
            with self.subTest(subject=name):
                self.assertIsNotNone(get_english_y1_rph(1, name, 16))


if __name__ == "__main__":
    unittest.main()
