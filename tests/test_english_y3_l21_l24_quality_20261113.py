"""Focused RPH content regressions: English Year 3 Lessons 21–24.

Checks existing SOW standards/book refs, observable PBD, Workbook activity
placement and teacher/pupil role separation, not direct TB scan signoff.
"""
from pathlib import Path
import re
import unittest
from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year3"

EXPECTED = {
    21: ("Language Arts 5.3 / 5.3.1", "Language Arts 5.1 / 5.1.1",
         "KPM Primary Year 3 SK Scheme of Work Lesson 21"),
    22: ("Listening 1.2 / 1.2.2", "Listening 1.2 / 1.2.5",
         "Student's Book p.17; Teacher's Book p.35"),
    23: ("Speaking 2.1 / 2.1.2", "Listening 1.2 / 1.2.5",
         "Student's Book p.17; Teacher's Book p.35"),
    24: ("Reading 3.2 / 3.2.4", "Reading 3.2 / 3.2.2",
         "Student's Book p.18; Teacher's Book p.36"),
}


def render(n):
    return apply({"subject": "English", "year": "Year 3", "lesson_no": n}, {})


class Lessons2124QualityTests(unittest.TestCase):
    def test_preserves_source_standards_and_phases(self):
        for n, (main, comp, source_ref) in EXPECTED.items():
            with self.subTest(lesson=n):
                text = (ROOT / f"lesson_{n:03d}.md").read_text("utf-8")
                self.assertIn(f"**Main SK/SP:** {main}", text)
                self.assertIn(f"**Complementary SK/SP:** {comp}", text)
                self.assertIn(source_ref, text)
                self.assertIn("**Duration:** 60 minutes", text)
                minutes = re.findall(
                    r"(?m)^## (?:Set Induction|Activity [12]|PBD|Closure)"
                    r"[^\n]*\((\d+) minutes\)", text)
                self.assertEqual(list(map(int, minutes)), [5, 15, 25, 10, 5])

    def test_user_rows_have_specific_teacher_and_pupil_actions(self):
        for n in EXPECTED:
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertIn("_standalone_y3_source", rows)
                self.assertIn("Activity 1", rows["AKTIVITI UTAMA"])
                self.assertIn("Activity 2", rows["AKTIVITI UTAMA"])
                for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
                    content = rows[field]
                    self.assertIn("Teacher:", content)
                    self.assertIn("Pupils:", content)
                    self.assertLess(content.index("Teacher:"), content.index("Pupils:"))
                    for banned in ("NOT READY", "materials/lesson_", "**Teacher:**",
                                   "CikguLaju original assessment"):
                        self.assertNotIn(banned, content)

    def test_printed_workbook_not_mistaken_for_formative_pbd(self):
        for n, page, activity in ((22, "p.11", "Activity 1"),
                                  (23, "p.11", "Activity 2"),
                                  (24, "p.12", "Activity 1")):
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertEqual(rows["AKTIVITI UTAMA"].count(f"Workbook {page}"), 1)
                self.assertIn(f"Workbook {page}, {activity}", rows["AKTIVITI UTAMA"])
                self.assertNotIn(f"Workbook {page}", rows["PENTAKSIRAN"])

    def test_each_pbd_assesses_the_intended_skill(self):
        la, listening, speaking, reading = (render(n) for n in (21, 22, 23, 24))
        self.assertIn("two brushing movements", la["PENTAKSIRAN"])
        self.assertIn("two details they heard", listening["PENTAKSIRAN"])
        self.assertIn("one complete transport question", speaking["PENTAKSIRAN"])
        self.assertIn("two accurate facts from the text", reading["PENTAKSIRAN"])
        self.assertEqual(len({x["PENTAKSIRAN"] for x in (la, listening, speaking, reading)}), 4)


if __name__ == "__main__":
    unittest.main()
