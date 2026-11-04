"""Validate twelve Year 3 pupil tasks against original KPM Primary Y3 SOW.

Original source PDF: Google Drive 1_-uNQsXiNfuorjMD1ObUUhmCi_L1i3L5,
Lessons 4–16. No audio playback, workbook task, TB visual QA, Telegram
downloads or teacher FINAL READY implied by this source-text regression.
"""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"rph_standalone"/"english"/"year3"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
KEYS={
    4:("family picture","Has he/she got"),
    5:("classmate","yearbook"),
    6:("p.7 Activity 3","apostrophes"),
    8:("sports texts","p.9 Activity 2"),
    9:("Can he/she","Activities 3–4"),
    10:("action card","original action-song verse"),
    11:("Can you help me, please?","Activity 5"),
    12:("What time is it?","half past"),
    13:("Fay","question strip"),
    14:("Writing Tip","punctuation"),
    15:("puppets","SB pp.12–13"),
    16:("Sections A–C","punctuation"),
}
TEMPLATES=(
  "Complete the referenced tasks, collaborate where appropriate and practise the main and complementary skills.",
  "Complete the referenced tasks, practising both standards.",
  "Complete the lesson activities and practise both skills.",
)
class Year3PupilTaskSpecificity(unittest.TestCase):
    def test_original_sow_scoped_actions(self):
        self.assertEqual(len(KEYS),12)
        for n,markers in KEYS.items():
            with self.subTest(lesson=n):
                r=SOW[f"3/{n}"]
                self.assertFalse(r["teacher_selected"])
                t=(FOLDER/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(t.splitlines()[0],rf"\bLesson\s+0*{n}\b")
                header=t.split("\n## ",1)[0]
                self.assertIn(r["main_ls"],header)
                self.assertIn(r["complementary_ls"],header)
                self.assertIn("NOT READY FOR RELEASE",t)
                for template in TEMPLATES:
                    self.assertNotIn(template,t)
                for marker in markers:
                    self.assertIn(marker,t)
                phases=[int(x) for x in re.findall(r"(?m)^## .*? \((\d+) minutes\)",t)]
                self.assertEqual(phases,[5,15,25,10,5])
                self.assertEqual(sum(phases),60)
                self.assertIn("## Activity 2",t)
                self.assertIn("**Pupils:**",t)
                self.assertIn("**Teacher:**",t)
    def test_story_and_review_follow_original_sow_pages(self):
        story=(FOLDER/"lesson_015.md").read_text(encoding="utf-8")
        self.assertIn("Student's Book pp.12–13 (story)",story)
        self.assertIn("Teacher's Book p.19 and pp.28–29",story)
        review=(FOLDER/"lesson_016.md").read_text(encoding="utf-8")
        self.assertIn("worksheet Section C",review)
        self.assertIn("SOW worksheet Sections A and B",review)
if __name__=="__main__":
    unittest.main()
