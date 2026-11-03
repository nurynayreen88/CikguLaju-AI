import types
import unittest
from web.english_y4_standalone_runtime import install


class Year4RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = types.SimpleNamespace(
            _local_rph_text=lambda state: "GENERIC",
            _english_primary_year_number_v2517=lambda year: int("".join(c for c in str(year) if c.isdigit()) or 0),
        )
        self.assertTrue(install(self.runtime))

    def test_year4_uses_specific_student_book_and_audio(self):
        text = self.runtime._local_rph_text({"year": "Tahun 4", "subject": "English", "lesson_no": 1})
        self.assertIn("Class CD1 Track 3", text)
        self.assertIn("Student's Book p.5", text)
        self.assertNotIn("**Teacher:**", text)

    def test_other_subject_and_year_fall_back(self):
        self.assertEqual(self.runtime._local_rph_text({"year": "Tahun 4", "subject": "Mathematics", "lesson_no": 1}), "GENERIC")
        self.assertEqual(self.runtime._local_rph_text({"year": "Tahun 5", "subject": "English", "lesson_no": 1}), "GENERIC")

    def test_missing_lesson_falls_back(self):
        self.assertEqual(self.runtime._local_rph_text({"year": "Tahun 4", "subject": "English", "lesson_no": 999}), "GENERIC")


if __name__ == "__main__":
    unittest.main()
