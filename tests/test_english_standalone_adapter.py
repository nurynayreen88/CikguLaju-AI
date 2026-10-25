"""Minimal smoke tests for the read-only English Year 1 RPH adapter."""
import unittest

from english_standalone_adapter import get_english_y1_rph, load_english_y1_rph, resolve_rph_with_fallback


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

    def test_standalone_skips_legacy_generator(self):
        def legacy():
            raise AssertionError("legacy must not run for a valid standalone lesson")
        result = resolve_rph_with_fallback(1, "English", 16, legacy)
        self.assertIn("Lesson", result)

    def test_other_subject_uses_legacy_generator(self):
        calls = []
        def legacy(subject, lesson):
            calls.append((subject, lesson))
            return {"source": "legacy"}
        result = resolve_rph_with_fallback(1, "Matematik", 16, legacy, "Matematik", 16)
        self.assertEqual(result, {"source": "legacy"})
        self.assertEqual(calls, [("Matematik", 16)])

    def test_missing_lesson_uses_legacy_generator(self):
        self.assertEqual(resolve_rph_with_fallback(1, "BI", 161, lambda: "legacy"), "legacy")

    def test_invalid_numeric_identifiers_do_not_match(self):
        for value in (True, 1.5, "1.5", -1, "1/2"):
            with self.subTest(value=value):
                self.assertIsNone(load_english_y1_rph(value))
        self.assertIsNone(get_english_y1_rph(1.5, "English", 16))
        self.assertIsNone(get_english_y1_rph(True, "English", 16))

    def test_metadata_style_lesson_header(self):
        text = load_english_y1_rph(16)
        self.assertIsNotNone(text)
        self.assertIn("**Lesson:** 16", text)

    def test_heading_style_lesson_header(self):
        text = load_english_y1_rph(1)
        self.assertIsNotNone(text)
        self.assertIn("Lesson 1:", text)

    def test_aliases(self):
        for name in ("English", "Bahasa Inggeris", "BI"):
            with self.subTest(subject=name):
                self.assertIsNotNone(get_english_y1_rph(1, name, 16))


if __name__ == "__main__":
    unittest.main()
