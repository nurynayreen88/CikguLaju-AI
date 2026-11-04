"""QA: Year 6 Language Awareness 5–8: task-specific suggestions, not final releases.

Do not treat page citations as verification of printed exercises. Teacher selection
of main/complementary DSKP standards and actual Telegram delivery remain pending.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rph_standalone" / "english" / "year6"
INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
CHOICES = {
    96: ("Language Awareness 5", "Academy Stars Year 6 Pupil Book pages 80-81",
         ("main idea", "four", "flowchart", "process-stage")),
    112: ("Language Awareness 6", "Academy Stars Year 6 Workbook pages 80-81",
          ("music", "two questions", "partner", "report")),
    128: ("Language Awareness 7", "Academy Stars Year 6 Pupil Book pages 106-107",
          ("story", "four", "alternative ending", "evidence")),
    144: ("Language Awareness 8", "Academy Stars Year 6 Workbook pages 100-101",
          ("opinion", "two", "three-sentence", "reason")),
}

class Year6TeacherSelectedFocusTests(unittest.TestCase):
    def test_focus_materials_standards_and_classroom_phases(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))["lessons"]
        first_phases, last_phases = set(), set()
        for n, (focus, page_ref, clues) in CHOICES.items():
            with self.subTest(lesson=n):
                official = index[f"6/{n}"]
                self.assertEqual(official["focus"], focus)
                self.assertTrue(official["teacher_selected"])
                self.assertIsNone(official["main_ls"])
                self.assertIsNone(official["complementary_ls"])
                source = (SRC / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                low = source.lower()
                self.assertIn(page_ref, source)
                self.assertIn("**Main CS/LS:** PILIHAN GURU (SOW)", source)
                self.assertIn("**Complementary CS/LS:** PILIHAN GURU (SOW)", source)
                self.assertIn("Teacher-selection notice", source)
                self.assertIn("**Teacher reflection:**", source)
                self.assertIn("**Duration:** 60 minutes", source)
                for clue in clues:
                    self.assertIn(clue.lower(), low)
                matches = list(re.finditer(r"(?m)^## (.+?) \((\d+) minutes\)$", source))
                self.assertEqual([int(m.group(2)) for m in matches], [5, 10, 18, 15, 8, 4])
                sections = []
                for i, m in enumerate(matches):
                    end = matches[i + 1].start() if i + 1 < len(matches) else source.index("## Differentiation", m.end())
                    segment = source[m.end():end]
                    self.assertIn("**Teacher:**", segment)
                    self.assertIn("**Pupils:**", segment)
                    sections.append(segment)
                self.assertNotIn("revisit common errors in the unit", low)
                self.assertNotIn("complete the review task and discuss", low)
                self.assertNotIn("one accurate new sentence or fact", low)
                first_phases.add(sections[0])
                last_phases.add(sections[-1])
        self.assertEqual(len(first_phases), len(CHOICES))
        self.assertEqual(len(last_phases), len(CHOICES))

if __name__ == "__main__":
    unittest.main()
