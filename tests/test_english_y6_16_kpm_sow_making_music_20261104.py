"""Sixteen English Year 6 original KPM SOW source task regressions.

Original KPM Primary Year6 SK Scheme of Work PDF is in connected Drive,
file ID 1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z (Lessons 81–100).
Checks source fidelity and fixed official CS/LS, not spoken audio identity,
full printed textbook visual fidelity, teacher approval or Telegram delivery.
"""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"rph_standalone"/"english"/"year6"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CASES={
 81:("3.2.4","3.2.1",("jeans","TB p.114","dictionary","recycling")),
 82:("4.3.2","1.1.1",("jeans","-sion","-tion","TB p.116")),
 83:("1.2.2","3.2.2",("passive","PB p.73","TB p.119","sentences")),
 84:("2.1.1","1.2.5",("made of","wood","TB p.120","objects")),
 86:("3.2.2","4.3.2",("recipe","credible","passive","TB p.124")),
 87:("4.2.5","4.3.1",("pasta","PB pp.76–77","passive","sequencing")),
 88:("1.2.2","2.1.1",("adverts","PB p.75","fact","opinion")),
 89:("2.2.2","1.2.4",("advert","persuasive","PB p.78","four-step")),
 91:("3.2.2","2.1.1",("jeans","TB p.128","£50","RM")),
 92:("4.3.3","3.2.2",("ketchup pen","WB p.70","Lesson 94","first draft")),
 93:("1.2.2","1.2.1",("Lumina","Audio 1.29","PB p.78","advantage")),
 94:("2.1.3","4.3.3",("Lesson 92","Lesson 89","radio","TB p.126")),
 97:("3.2.1","1.2.1",("music","PB pp.82–83","song","magazine")),
 98:("4.2.1","2.1.5",("Robin Hood","TB p.134","adjectives","four")),
 99:("1.2.2","2.1.4",("PB p.86","Audio 2.2","concert","schedule")),
100:("2.1.4","4.2.2",("will","going to","PB p.85","WB p.74")),
}
class Year6LatestSixteenKpmSow(unittest.TestCase):
    def test_source_steps_and_exact_fixed_codes(self):
        self.assertEqual(len(CASES),16)
        for n,(main,comp,markers) in CASES.items():
            with self.subTest(lesson=n):
                rec=SOW[f"6/{n}"]
                self.assertFalse(rec["teacher_selected"])
                self.assertEqual((rec["main_ls"],rec["complementary_ls"]),(main,comp))
                content=(FOLDER/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(content.splitlines()[0],rf"\bLesson\s+0*{n}\b")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",content)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",content)
                self.assertIn("**RPT:** 2027",content)
                self.assertIn("**Teacher reflection:**",content)
                self.assertNotIn("FINAL READY",content)
                for marker in markers:
                    self.assertIn(marker.casefold(),content.casefold(),(n,marker))
                for phrase in ("Share one accurate new sentence or fact",
                               "Check the lesson evidence against the target",
                               "Check the complementary skill using the short task."):
                    self.assertNotIn(phrase,content)
                durations=[int(m.group(1)) for m in re.finditer(
                    r"(?m)^## [^\n]+ \((\d+) minutes\)$",content)]
                self.assertEqual(durations,[5,10,18,15,8,4])
                lines=content.splitlines()
                positions=[i for i,z in enumerate(lines)
                           if re.match(r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",z)]
                self.assertEqual(len(positions),6)
                for i in positions:
                    self.assertTrue(lines[i+1].startswith("**Teacher:**"),n)
                    self.assertTrue(lines[i+2].startswith("**Pupils:**"),n)
    def test_cross_lesson_draft_not_restart(self):
        writing=(FOLDER/"lesson_092.md").read_text(encoding="utf-8")
        advert=(FOLDER/"lesson_094.md").read_text(encoding="utf-8")
        self.assertIn("first draft",writing)
        self.assertIn("Lesson 94",writing)
        self.assertIn("Return Lesson 92 drafts",advert)
        self.assertIn("Lesson 89 advert",advert)
        self.assertIn("correct",advert.casefold())
    def test_no_unapproved_language_arts_overwrite(self):
        for n in (80,85,90,95,96,101):
            self.assertTrue((FOLDER/f"lesson_{n:03d}.md").exists())
if __name__=="__main__":
    unittest.main()
