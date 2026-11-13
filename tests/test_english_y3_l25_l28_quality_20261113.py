"""Quality regression for Year 3 English Lessons 25–28.

Teacher/pupil specificity and source integrity are checked; Teacher's Book
scan verification and live Web/Telegram delivery remain separate gates.
"""
from pathlib import Path
import re
import unittest

from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone/english/year3"

EXPECTED = {
    25: ("Writing 4.3 / 4.3.2", "Speaking 2.2 / 2.2.2",
         "Student's Book p.19; Teacher's Book p.37"),
    26: ("Language Arts 5.1 / 5.1.2", "Listening 1.2 / 1.2.3",
         "KPM Year 3 SK SOW Lesson 26"),
    27: ("Listening 1.2 / 1.2.1", "Speaking 2.3 / 2.3.1",
         "Student's Book p.19 Activity 4; Teacher's Book p.37"),
    28: ("Speaking 2.1 / 2.1.2", "Listening 1.2 / 1.2.5",
         "Student's Book p.20 Activity 1; Teacher's Book pp.38–39"),
}


def render(n):
    return apply({"subject": "English", "year": "Tahun 3", "lesson_no": n}, {})


class Year3Lessons2528QualityTests(unittest.TestCase):
    def test_source_standards_and_minutes_unchanged(self):
        for n, (main, comp, ref) in EXPECTED.items():
            with self.subTest(lesson=n):
                source = (ROOT / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main SK/SP:** {main}", source)
                self.assertIn(f"**Complementary SK/SP:** {comp}", source)
                self.assertIn(ref, source)
                self.assertIn("**Duration:** 60 minutes", source)
                minutes = re.findall(
                    r"(?m)^## (?:Set Induction|Activity [12]|PBD|Closure)"
                    r"[^\n]*\((\d+) minutes\)", source)
                self.assertEqual(list(map(int, minutes)), [5, 15, 25, 10, 5])

    def test_each_phase_names_roles_without_internal_file_leaks(self):
        for n in EXPECTED:
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertIn("_standalone_y3_source", rows)
                self.assertIn("Activity 1", rows["AKTIVITI UTAMA"])
                self.assertIn("Activity 2", rows["AKTIVITI UTAMA"])
                for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
                    body = rows[field]
                    self.assertIn("Teacher:", body)
                    self.assertIn("Pupils:", body)
                    self.assertLess(body.index("Teacher:"), body.index("Pupils:"))
                    for forbidden in ("NOT READY FOR RELEASE", "materials/lesson_",
                                      "original CikguLaju", "**Teacher:**", "**Pupils:**"):
                        self.assertNotIn(forbidden, body)

    def test_specific_outcomes_for_each_skill(self):
        written, rhyme, listen, speak = (render(n) for n in (25, 26, 27, 28))
        self.assertIn("two understandable original occupation clues", written["PENTAKSIRAN"])
        self.assertIn("Supply two missing transport words", rhyme["PENTAKSIRAN"])
        self.assertIn("Identify two jobs", listen["PENTAKSIRAN"])
        self.assertIn("Ask one occupation question", speak["PENTAKSIRAN"])
        self.assertEqual(len({r["PENTAKSIRAN"] for r in (written, rhyme, listen, speak)}), 4)

    def test_l25_not_relying_on_unbundled_internal_worksheet(self):
        source = (ROOT / "lesson_025.md").read_text(encoding="utf-8")
        self.assertNotIn("materials/lesson_025", source)
        self.assertIn("blank clue card or writing space", source)
        self.assertNotIn("prepare separately", render(25)["PENTAKSIRAN"])

    def test_l28_workbook_task_stays_in_main_activity(self):
        row = render(28)
        self.assertEqual(row["AKTIVITI UTAMA"].count("Workbook p.13, Activity 2"), 1)
        self.assertNotIn("Workbook p.13", row["PENTAKSIRAN"])


if __name__ == "__main__":
    unittest.main()
