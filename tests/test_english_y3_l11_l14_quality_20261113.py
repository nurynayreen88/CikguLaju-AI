"""Content regression checks for English Year 3 Lessons 11–14.

These are editorial checks against source and rendered rows, NOT verification
of Teacher's Book/SOW scans or of live Telegram/Web Word/PDF downloads.
"""
from pathlib import Path
import re
import unittest

from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year3"

LESSONS = {
    11: ("1.2 / 1.2.5", "2.2 / 2.2.2", "Student's Book p.9 Activity 5"),
    12: ("2.1 / 2.1.2", "1.2 / 1.2.5", "Student's Book p.10 Activity 1"),
    13: ("3.2 / 3.2.2", "2.1 / 2.1.5", "Student's Book p.11 Activity 1"),
    14: ("4.3 / 4.3.1", "4.3 / 4.3.3", "Student's Book p.11 Activity 1"),
}


class EnglishY3L11L14QualityTests(unittest.TestCase):
    def test_preserve_existing_sk_sp_book_pages_and_60_minute_phases(self):
        for lesson, (main_sp, comp_sp, book) in LESSONS.items():
            with self.subTest(lesson=lesson):
                source = (ROOT / f"lesson_{lesson:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main SK/SP:** {main_sp}", source)
                self.assertIn(f"**Complementary SK/SP:** {comp_sp}", source)
                self.assertIn(book, source)
                self.assertIn("**Duration:** 60 minutes", source)
                times = [int(n) for n in re.findall(
                    r"(?m)^## (?:Set Induction|Activity [12]|Assessment / PBD|Closure)"
                    r"[^\n]*\((\d+) minutes\)", source
                )]
                self.assertEqual(times, [5, 15, 25, 10, 5])

    def test_teacher_pupil_actions_and_assessment_are_specific(self):
        for lesson in LESSONS:
            with self.subTest(lesson=lesson):
                rows = apply({"subject": "English", "year": "Year 3",
                              "lesson_no": lesson}, {})
                self.assertIn("_standalone_y3_source", rows)
                for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
                    self.assertIn("Teacher:", rows[field])
                    self.assertIn("Pupils:", rows[field])
                    self.assertNotIn("NOT READY FOR RELEASE", rows[field])
                    self.assertNotIn("materials/lesson_", rows[field])
                self.assertIn("Activity 1", rows["AKTIVITI UTAMA"])
                self.assertIn("Activity 2", rows["AKTIVITI UTAMA"])

    def test_lesson13_reading_and_14_writing_do_not_duplicate_pbd(self):
        reading = apply({"subject": "English", "year": "Year 3",
                         "lesson_no": 13}, {})
        writing = apply({"subject": "English", "year": "Year 3",
                         "lesson_no": 14}, {})
        self.assertIn("locate one answer using evidence", reading["AKTIVITI UTAMA"])
        self.assertIn("two accurate details", reading["PENTAKSIRAN"])
        self.assertIn("write two family sentences", writing["AKTIVITI UTAMA"])
        self.assertIn("assess two family-description sentences", writing["PENTAKSIRAN"])
        self.assertIn("correct one punctuation error", writing["PENTAKSIRAN"])
        self.assertNotIn("write three family sentences", writing["PENTAKSIRAN"])
        self.assertNotIn("Workbook p.6, Activity 2", writing["PENTAKSIRAN"])
        self.assertIn("Workbook p.6, Activity 1", reading["AKTIVITI UTAMA"])
        self.assertNotIn("Workbook p.6, Activity 1", reading["PENTAKSIRAN"])


if __name__ == "__main__":
    unittest.main()
