"""Verify the Right Now RPH against the SOW and the existing Workbook map."""
import json
from pathlib import Path
import re
import unittest

from english_y3_standalone_render import apply
from resources.english.y3.workbook_verified_map import Y3_WB_VERIFIED_LESSON_MAP
from web.english_y2_y3_standard_runtime import enrich_rows

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_TASKS = {
    33: (18, 1), 34: (18, 2), 35: (19, 1), 36: (19, 2),
    38: (19, 2), 39: (19, 2), 40: (20, 2), 43: (20, 1), 44: (21, 2),
    45: (23, 1), 46: (22, 2),
}
EVIDENCE = {
    33: ("two matching pictures", "visual clue"),
    34: ("one intelligible description", "two action words"),
    35: ("main idea", "word meaning"),
    36: ("three correctly spelt words", "panels supporting two answers"),
    37: ("four actions", "two sections"),
    38: ("two correct pictures", "visual clue"),
    39: ("one action", "help question"),
    40: ("main idea", "two answers"),
    41: ("two picture matches", "two written sentences"),
    42: ("contribution", "one clear description"),
    43: ("five listening answers", "two final written sentences"),
    44: ("one clear description", "three supported questions"),
    45: ("main event", "supporting panel"),
    46: ("two final labels", "two pictured actions"),
    47: ("three pictures", "two independent matches"),
    48: ("two sentences", "two contractions"),
}


class RightNowQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
        cls.sow = json.loads(index.read_text(encoding="utf-8"))["lessons"]

    def test_rendered_standards_and_objectives(self):
        for lesson in EVIDENCE:
            with self.subTest(lesson=lesson):
                state = {"subject": "English", "year": "Year 3", "lesson_no": lesson}
                rows = enrich_rows(state, apply(state, {}))
                sow = self.sow[f"3/{lesson}"]
                self.assertEqual(rows["MAIN LEARNING STANDARD"], sow["main_ls"])
                self.assertEqual(rows["COMPLEMENTARY LEARNING STANDARD"], sow["complementary_ls"])
                source = (ROOT / f"rph_standalone/english/year3/lesson_{lesson:03d}.md").read_text(
                    encoding="utf-8")
                for key, label in (("OBJEKTIF PEMBELAJARAN", "Learning objective"),
                                   ("KRITERIA KEJAYAAN", "Success criteria")):
                    value = re.search(rf"(?m)^\*\*{label}:\*\* (.+)$", source).group(1)
                    self.assertEqual(rows[key], value)
                minutes = re.findall(r"(?m)^## .+?\((\d+) minutes\)$", source)
                self.assertEqual([int(n) for n in minutes], [5, 15, 25, 10, 5])

    def test_workbook_page_matches_download_and_is_in_activity_only(self):
        for lesson in EVIDENCE:
            with self.subTest(lesson=lesson):
                rows = apply({"subject": "English", "year": "Year 3", "lesson_no": lesson}, {})
                matches = re.findall(r"Workbook p\.(\d+), Activity (\d+)", rows["AKTIVITI UTAMA"])
                if lesson in WORKBOOK_TASKS:
                    page, activity = WORKBOOK_TASKS[lesson]
                    self.assertEqual(matches, [(str(page), str(activity))])
                    self.assertEqual(Y3_WB_VERIFIED_LESSON_MAP[lesson]["printed"], page)
                else:
                    self.assertFalse(matches)
                self.assertNotIn("Workbook", rows["PENTAKSIRAN"])

    def test_roles_and_skill_specific_pbd(self):
        for lesson, evidence in EVIDENCE.items():
            with self.subTest(lesson=lesson):
                rows = apply({"subject": "English", "year": "Year 3", "lesson_no": lesson}, {})
                for field, count in (("SET INDUKSI", 1), ("AKTIVITI UTAMA", 2),
                                     ("PENTAKSIRAN", 1), ("PENUTUP", 1)):
                    phase = rows[field]
                    roles = re.findall(r"(?m)^(Teacher|Pupils):", phase)
                    self.assertEqual(roles, ["Teacher", "Pupils"] * count)
                    self.assertNotIn("NOT READY FOR RELEASE", phase)
                    self.assertNotIn("**", phase)
                for phrase in evidence:
                    self.assertIn(phrase, rows["PENTAKSIRAN"].casefold())

    def test_linked_writing_and_listening_sequence_uses_the_same_pupil_draft(self):
        writing = apply({"subject": "English", "year": "Year 3", "lesson_no": 41}, {})
        listening = apply({"subject": "English", "year": "Year 3", "lesson_no": 43}, {})
        self.assertIn("Mark any errors in the slips for Lesson 43", writing["PENTAKSIRAN"])
        self.assertIn("Return the marked slips from Lesson 41", listening["AKTIVITI UTAMA"])
        self.assertIn("number the five pictured actions", listening["AKTIVITI UTAMA"])
        self.assertNotIn("Workbook p.24", listening["AKTIVITI UTAMA"])
