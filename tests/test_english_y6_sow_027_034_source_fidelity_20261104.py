"""Six fixed-standard English Y6 SOW refinements after Lesson 24.

Original KPM Primary Y6 SK SOW Drive PDF:
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z, Lessons 27–30, 33–34.
This tests source task fidelity, NOT unverified audio or Telegram delivery.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rph_standalone"/"english"/"year6"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
LESSONS={
    27:("3.2.2","1.2.5",("Mr Brockbank","time-machine","TB p.56","really")),
    28:("4.2.3","3.2.4",("grandparents","three","direct speech","inaccuracies","PB p.31")),
    29:("1.2.1","2.1.4",("environment","technology","family life","presentation","future")),
    30:("2.2.1","2.1.4",("museum guide","past","present","future","clarification")),
    33:("3.2.1","3.2.2",("Emma","Canadian","blog","TB p.61","Malaysia")),
    34:("4.2.1","3.2.2",("Emma","true and two false","present-perfect","irregular","PB pp.36–37")),
}
class Year6SixNextSowTasks(unittest.TestCase):
    def test_sow_code_fidelity_pupil_actions_and_draft_guard(self):
        self.assertEqual(len(LESSONS),6)
        for n,(main,comp,markers) in LESSONS.items():
            with self.subTest(lesson=n):
                proof=SOW[f"6/{n}"]
                self.assertFalse(proof["teacher_selected"])
                self.assertEqual((proof["main_ls"],proof["complementary_ls"]),(main,comp))
                text=(SRC/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",text)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",text)
                self.assertIn("**Teacher reflection:**",text)
                self.assertIn("**Learning objective:**",text)
                self.assertIn("**PBD evidence:**",text)
                self.assertNotIn("FINAL READY",text)
                self.assertNotIn("Share one accurate new sentence or fact",text)
                self.assertNotIn("Check the complementary skill using the short task",text)
                for m in markers:
                    self.assertIn(m.casefold(),text.casefold(),m)
                phases=[int(x) for x in re.findall(r"(?m)^## [^\n]+ \((\d+) minutes\)$",text)]
                self.assertEqual(phases,[5,10,18,15,8,4])
                lines=text.splitlines()
                headings=[i for i,l in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",l)]
                self.assertEqual(len(headings),6)
                for pos in headings:
                    self.assertTrue(lines[pos+1].startswith("**Teacher:**"),n)
                    self.assertTrue(lines[pos+2].startswith("**Pupils:**"),n)
    def test_previous_existing_tos_and_teacher_choice_unchanged(self):
        body=(SRC/"lesson_031.md").read_text(encoding="utf-8")
        self.assertIn("Toes",body)
        choice=(SRC/"lesson_032.md").read_text(encoding="utf-8")
        self.assertTrue(SOW["6/32"]["teacher_selected"])
        self.assertIn("PILIHAN GURU",choice)
if __name__=="__main__":
    unittest.main()
