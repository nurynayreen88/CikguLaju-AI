"""Focused academic-content regressions for English Y3 Lessons 17–20.

This verifies existing SK/SP and references are preserved, source-to-RPH
rendering, teacher/pupil roles, Workbook placement, and measurable PBD.
It does NOT replace Teacher's Book scan review or live Web/Telegram testing.
"""
from pathlib import Path
import re
import unittest

from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone/english/year3"

SOURCES = {
    17: ("1.2 / 1.2.2", "1.3 / 1.3.1", "SB p.15; TB p.32"),
    18: ("Speaking 2.1 / 2.1.2", "Writing 4.3 / 4.3.2", "Student's Book p.15 Activities 1–2"),
    19: ("Reading 3.2 / 3.2.1", "Reading 3.2 / 3.2.2", "Student's Book pp.16–17"),
    20: ("Writing 4.3 / 4.3.3", "Writing 4.3 / 4.3.1", "KPM Year 3 SK SOW Lesson 20"),
}


def render(n):
    return apply({"subject": "English", "year": "Year 3", "lesson_no": n}, {})


class Lessons1720QualityTests(unittest.TestCase):
    def test_preserves_existing_sow_codes_materials_and_timing(self):
        for n, (main_sp, comp_sp, book) in SOURCES.items():
            with self.subTest(lesson=n):
                source = (ROOT / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main SK/SP:** {main_sp}", source)
                self.assertIn(f"**Complementary SK/SP:** {comp_sp}", source)
                self.assertIn(book, source)
                self.assertIn("**Duration:** 60 minutes", source)
                times = re.findall(
                    r"(?m)^## (?:Set Induction|Activity [12]|Assessment / PBD|PBD|Closure)"
                    r"[^\n]*\((\d+) minutes\)", source
                )
                self.assertEqual(list(map(int, times)), [5, 15, 25, 10, 5])

    def test_roles_pbd_and_no_developer_paths_in_teacher_rows(self):
        for n in SOURCES:
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertIn("_standalone_y3_source", rows)
                self.assertIn("Activity 1", rows["AKTIVITI UTAMA"])
                self.assertIn("Activity 2", rows["AKTIVITI UTAMA"])
                for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
                    text = rows[field]
                    self.assertIn("Teacher:", text)
                    self.assertIn("Pupils:", text)
                    self.assertLess(text.index("Teacher:"), text.index("Pupils:"))
                    self.assertNotIn("NOT READY", text)
                    self.assertNotIn("materials/lesson_", text)
                    self.assertNotIn("CikguLaju original assessment", text)
                    self.assertNotIn("**Teacher:**", text)
                    self.assertNotIn("Complete the lesson task", text)

    def test_wb_is_main_activity_only_in_17_and_20(self):
        for n, page, activity in ((17, "p.10", "Activity 1"), (20, "p.10", "Activity 2")):
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertEqual(rows["AKTIVITI UTAMA"].count("Workbook p.10"), 1)
                self.assertIn(f"Workbook {page}, {activity}", rows["AKTIVITI UTAMA"])
                self.assertNotIn("Workbook p.10", rows["PENTAKSIRAN"])

    def test_distinct_skill_evidence_and_assessment(self):
        listen, speak, read, write = (render(n) for n in (17, 18, 19, 20))
        self.assertIn("two routines they heard", listen["PENTAKSIRAN"])
        self.assertIn("one classmate's response", speak["PENTAKSIRAN"])
        self.assertIn("point to one line", read["PENTAKSIRAN"])
        self.assertIn("two routine sentences", write["PENTAKSIRAN"])
        self.assertIn("one third-person example", write["PENTAKSIRAN"])
        self.assertNotEqual(read["PENTAKSIRAN"], write["PENTAKSIRAN"])


if __name__ == "__main__":
    unittest.main()
