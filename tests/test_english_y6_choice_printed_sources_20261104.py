"""Source QA: four Y6 SOW teacher-choice lesson plans use the pictured printed tasks.

The book exercises are source-checked; DSKP selection, recorded content,
teacher signoff and authenticated Telegram delivery are NOT certified here.
No app.py import, database access, message send or credit changes.
"""
import re
import unittest
from pathlib import Path

from web.english_y6_standalone_runtime import adapt_rows, TEACHER_SELECTED_STANDARD

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    16: ("Workbook pp.16–17", ("vocabulary puzzle", "when/while")),
    32: ("Pupil's Book pp.32–33", ("Review 1", "Bill and Anna")),
    48: ("Workbook pp.36–37", ("present-perfect", "interview")),
    64: ("Pupil's Book pp.58–59", ("Review 2", "make/do")),
}


class Year6TeacherChoicePrintedSource(unittest.TestCase):
    def test_four_source_anchors_and_timing(self):
        for n, (reference, anchors) in CASES.items():
            with self.subTest(lesson=n):
                src = (ROOT / "rph_standalone/english/year6" /
                       f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(reference, src)
                for anchor in anchors:
                    self.assertIn(anchor.casefold(), src.casefold())
                self.assertIn("**QA status:** DRAF", src)
                self.assertIn("**Main CS/LS:** PILIHAN GURU (SOW)", src)
                self.assertIn("**Complementary CS/LS:** PILIHAN GURU (SOW)", src)
                self.assertIn("subject to teacher selection", src)
                self.assertEqual(sum(int(x) for x in re.findall(
                    r"^## .+ \((\d+) minutes\)$", src, re.M)), 60)
                self.assertNotRegex(src, r"(?i)(?:Class\s*)?CD[123]\s*Track\s*\d+")
                self.assertNotIn("Listen to an original short recording", src)

    def test_native_word_pdf_rows_take_source_tasks_and_preserve_user_data(self):
        legacy = {
            "TAJUK": "OLD GENERIC", "AKTIVITI UTAMA": "OLD ACTIVITIES",
            "MAIN LEARNING STANDARD": "WRONG SP",
            "COMPLEMENTARY LEARNING STANDARD": "WRONG SP",
            "TARIKH": "04/11/2026", "MASA": "10:00", "KELAS": "6 Maju",
            "REFLEKSI": "Original teacher feedback",
        }
        for n, (_, anchors) in CASES.items():
            with self.subTest(lesson=n):
                out = adapt_rows({"subject": "English", "year": "Year 6",
                                  "lesson_no": n, "task": "rph"}, legacy)
                self.assertIsNot(out, legacy)
                self.assertIn("DRAF", out["TAJUK"])
                self.assertEqual(out["MAIN LEARNING STANDARD"], TEACHER_SELECTED_STANDARD)
                self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"], TEACHER_SELECTED_STANDARD)
                combined = " ".join(str(out[k]) for k in
                                    ("SET INDUKSI", "AKTIVITI UTAMA",
                                     "PENTAKSIRAN", "PENUTUP",
                                     "BAHAN BANTU MENGAJAR"))
                for anchor in anchors:
                    self.assertIn(anchor.casefold(), combined.casefold())
                self.assertIn("Teacher:", out["AKTIVITI UTAMA"])
                self.assertIn("Pupils:", out["AKTIVITI UTAMA"])
                self.assertNotIn("OLD ACTIVITIES", combined)
                for key in ("TARIKH", "MASA", "KELAS", "REFLEKSI"):
                    self.assertEqual(out[key], legacy[key])
                self.assertEqual(legacy["REFLEKSI"], "Original teacher feedback")

    def test_other_years_are_not_overwritten(self):
        old = {"TAJUK": "Original"}
        for year in ("Year 1", "Year 4", "Year 5"):
            self.assertIs(adapt_rows({"subject": "English", "year": year,
                                      "lesson_no": 16}, old), old)


if __name__ == "__main__":
    unittest.main()
