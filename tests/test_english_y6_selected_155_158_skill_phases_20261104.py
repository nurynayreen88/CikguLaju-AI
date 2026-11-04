"""Regression: skill-specific teacher-choice Year 6 Lessons 155–158.

These are draft CikguLaju teaching suggestions, not official SOW-fixed SPs
and not independent classroom or Telegram delivery approvals.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rph_standalone" / "english" / "year6"
INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
CHOICES = {
    155: ("Reading 30", "heading", "main idea"),
    156: ("Writing 30", "captions", "punctuation"),
    157: ("Listening 30", "without displaying a transcript", "specific detail"),
    158: ("Speaking 30", "opening", "speaking target"),
}


class TeacherSelectedSkillSpecificRPH(unittest.TestCase):
    def test_source_standards_timing_and_non_generic_activities(self):
        sow = json.loads(INDEX.read_text(encoding="utf-8"))["lessons"]
        openings, closings = set(), set()
        for lesson, (focus, intro_clue, close_clue) in CHOICES.items():
            with self.subTest(lesson=lesson):
                rec = sow[f"6/{lesson}"]
                self.assertEqual(rec["focus"], focus)
                self.assertIs(rec["teacher_selected"], True)
                self.assertIsNone(rec["main_ls"])
                self.assertIsNone(rec["complementary_ls"])
                txt = (SOURCE / f"lesson_{lesson:03d}.md").read_text(encoding="utf-8")
                self.assertIn("**Main CS/LS:** PILIHAN GURU (SOW)", txt)
                self.assertIn("**Complementary CS/LS:** PILIHAN GURU (SOW)", txt)
                self.assertIn("Teacher-selection notice", txt)
                self.assertIn("CikguLaju suggestions", txt)
                heads = list(re.finditer(r"(?m)^## (.+?) \((\d+) minutes\)$", txt))
                self.assertEqual(len(heads), 6)
                self.assertEqual([int(h.group(2)) for h in heads], [5, 10, 18, 15, 8, 4])
                bodies = []
                for i, head in enumerate(heads):
                    next_section = txt.find("\n## ", head.end())
                    body = txt[head.end():next_section if next_section >= 0 else len(txt)]
                    self.assertIn("**Teacher:**", body)
                    self.assertIn("**Pupils:**", body)
                    bodies.append(body)
                self.assertIn(intro_clue, bodies[0])
                self.assertIn(close_clue, bodies[-1])
                self.assertNotIn("What can you say about this topic?", bodies[0] + bodies[-1])
                openings.add(bodies[0])
                closings.add(bodies[-1])
        self.assertEqual(len(openings), 4)
        self.assertEqual(len(closings), 4)


if __name__ == "__main__":
    unittest.main()
