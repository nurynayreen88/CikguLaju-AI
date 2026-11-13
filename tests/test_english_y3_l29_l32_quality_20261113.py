"""RPH teaching quality and source integrity tests: Year 3 Lessons 29–32.

Checks lesson structure and the rendered Word/PDF row source. Does not
confirm direct Teacher's Book scans or live Web/Telegram deliveries.
"""
from pathlib import Path
import re
import unittest
from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year3"
REFERENCES = {
    29: ("Reading 3.2 / 3.2.3", "Reading 3.2 / 3.2.2",
         "Student's Book p.115 Activities 1–2; Teacher's Book p.178"),
    30: ("Writing 4.3 / 4.3.1", "Writing 4.1 / 4.1.2",
         "Student's Book p.21; Teacher's Book pp.34, 39–41"),
    31: ("Language Arts 5.2 / 5.2.1", "Speaking 2.1 / 2.1.5",
         "Student's Book pp.22–23; Teacher's Book pp.42–43"),
    32: ("Reading 3.2 / 3.2.2", "Writing 4.2 / 4.2.4",
         "Student's Book p.24 revision activities; Teacher's Book pp.44–45"),
}


def render(n):
    return apply({"subject": "English", "year": "Tahun 3", "lesson_no": n}, {})


class Year3Lessons2932QualityTests(unittest.TestCase):
    def test_preserve_sources_standards_and_60_minutes(self):
        for n, (main, comp, reference) in REFERENCES.items():
            with self.subTest(lesson=n):
                source = (ROOT / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main SK/SP:** {main}", source)
                self.assertIn(f"**Complementary SK/SP:** {comp}", source)
                self.assertIn(reference, source)
                self.assertIn("**Duration:** 60 minutes", source)
                minutes = re.findall(
                    r"(?m)^## (?:Set Induction|Activity [12]|PBD|Closure)"
                    r"[^\n]*\((\d+) minutes\)", source)
                self.assertEqual(list(map(int, minutes)), [5, 15, 25, 10, 5])

    def test_each_rendered_phase_has_distinct_teacher_and_pupil_actions(self):
        for n in REFERENCES:
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
                    for bad in ("NOT READY FOR RELEASE", "**Teacher:**",
                                "materials/lesson_", "CikguLaju original assessment"):
                        self.assertNotIn(bad, body)

    def test_workbook_tasks_are_in_activity_not_pbd(self):
        for n, page, activity in ((30, "p.14", "Activity 2"),
                                  (31, "p.15", "Activity 1"),
                                  (32, "p.16", "Activity 2")):
            with self.subTest(lesson=n):
                rows = render(n)
                self.assertEqual(rows["AKTIVITI UTAMA"].count(f"Workbook {page}, {activity}"), 1)
                self.assertNotIn(f"Workbook {page}", rows["PENTAKSIRAN"])

    def test_skill_specific_pbd_evidence(self):
        read, write, story, awareness = [render(i) for i in range(29, 33)]
        self.assertIn("two accurate reading details", read["PENTAKSIRAN"])
        self.assertIn("two punctuated routine sentences", write["PENTAKSIRAN"])
        self.assertIn("one character and the related job", story["PENTAKSIRAN"])
        self.assertIn("two text-based questions", awareness["PENTAKSIRAN"])
        self.assertEqual(len({x["PENTAKSIRAN"] for x in (read, write, story, awareness)}), 4)


if __name__ == "__main__":
    unittest.main()
