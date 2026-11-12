"""Exact-source Year 3 Workbook task flow: existing pages, no invented links.

This checks presentation/lesson timing, not academic source signoff or live delivery.
"""
from pathlib import Path
import re
import unittest

from english_y3_standalone_render import apply

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone/english/year3"
TASKS = {
    11: ("p.8", "Activity 2"),
    12: ("p.9", "Activity 4"),
    13: ("p.6", "Activity 1"),
    16: ("p.9", "Activity 5"),
    17: ("p.10", "Activity 1"),
}


class WorkbookInActivityTests(unittest.TestCase):
    def test_five_source_tasks_appear_once_in_main_activity_and_not_pbd(self):
        for lesson, (page, task) in TASKS.items():
            with self.subTest(lesson=lesson):
                source = (ROOT / f"lesson_{lesson:03d}.md").read_text("utf-8")
                self.assertIn("## Activity 2", source)
                self.assertIn("## Assessment / PBD (10 minutes)", source)
                self.assertNotIn("Workbook assessment:", source)
                head, tail = source.split("## Assessment / PBD", 1)
                self.assertEqual(len(re.findall(r"Workbook\s+p\.", head)), 1)
                self.assertEqual(len(re.findall(r"Workbook\s+p\.", tail)), 0)
                rows = apply({"subject": "English", "year": "Year 3",
                              "lesson_no": lesson}, {})
                self.assertIn("_standalone_y3_source", rows)
                self.assertIn("Workbook " + page, rows["AKTIVITI UTAMA"])
                self.assertIn(task, rows["AKTIVITI UTAMA"])
                self.assertNotIn("Workbook " + page, rows["PENTAKSIRAN"])
                self.assertEqual(rows["AKTIVITI UTAMA"].count("Workbook " + page), 1)
                self.assertIn("Teacher:", rows["PENTAKSIRAN"])
                self.assertIn("Pupils:", rows["PENTAKSIRAN"])
                self.assertNotIn("NOT READY", rows["AKTIVITI UTAMA"])
                self.assertNotIn("**", rows["AKTIVITI UTAMA"])
                self.assertNotIn("Pengukuhan", rows["AKTIVITI UTAMA"])
                self.assertNotIn("NOT READY", rows["PENUTUP"])
                parts = re.findall(r"^## (?:Set Induction|Activity [12]|Assessment / PBD|Closure)[^\n]*\((\d+) minutes\)",
                                   source, re.M)
                self.assertEqual([int(t) for t in parts], [5,15,25,10,5])
                self.assertEqual(sum(map(int, parts)), 60)

    def test_unrelated_y3_lesson_and_other_year_are_unchanged(self):
        original = {"AKTIVITI UTAMA": "Existing work"}
        self.assertIs(apply({"subject": "English", "year": "Year 2",
                             "lesson_no": 11}, original), original)


if __name__ == "__main__":
    unittest.main()
