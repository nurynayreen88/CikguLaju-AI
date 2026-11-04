"""12 original-SOW English Year 6 Adventure Time / Cool Jobs task checks.

Official KPM Primary Year 6 SK SOW PDF (Drive file
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z), Lessons 35–50.
Audio speech identity, detailed print exercise QA and Telegram delivery
are separate release checks not asserted here.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rph_standalone"/"english"/"year6"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CHECK={
 35:("1.2.5","2.1.1",("Camping experiences","PB p.38","four questions","TB p.67")),
 36:("2.1.1","1.2.5",("Find Someone Who","Have you ever","Adilah","TB p.65")),
 38:("3.2.2","4.3.3",("Emma","Whistler","mind map","PB p.40","blog")),
 39:("4.3.3","4.2.3",("birthday","mind map","PB p.41","Lesson 44","first draft")),
 40:("1.2.2","1.3.1",("Mike","PB p.39","interview","fact","Values")),
 41:("2.3.1","1.2.3",("worksheets A and B","picture","retell","three")),
 43:("3.3.1","3.2.1",("independent reading","PB p.44","wildlife","four events")),
 44:("4.2.5","4.3.1",("Lesson 39","correction code","second draft","cohesion")),
 45:("1.2.2","1.3.1",("PB p.43","job advert","interview","appearance")),
 46:("2.1.1","1.2.5",("adventure camp","TB p.72","interview","PB p.42")),
 49:("3.2.3","3.2.4",("Unusual Jobs","PB p.48","dictionary","four texts")),
 50:("4.2.1","3.2.2",("Adela","Tyler","Jill","Derek","PB p.50")),
}
TIME=[5,10,18,15,8,4]
class TwelveOriginalSowSpecificTasks(unittest.TestCase):
    def test_original_pairs_task_evidence_and_time(self):
        self.assertEqual(len(CHECK),12)
        for number,(main,comp,markers) in CHECK.items():
            with self.subTest(lesson=number):
                sow=SOW[f"6/{number}"]
                self.assertFalse(sow["teacher_selected"])
                self.assertEqual((sow["main_ls"],sow["complementary_ls"]),(main,comp))
                body=(SRC/f"lesson_{number:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(body.splitlines()[0],rf"\bLesson\s+0*{number}\b")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",body)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",body)
                self.assertIn("**Teacher reflection:**",body)
                self.assertIn("**Learning objective:**",body)
                self.assertIn("**PBD evidence:**",body)
                for word in markers:
                    self.assertIn(word.casefold(),body.casefold(),(number,word))
                for old in ("Share one accurate new sentence or fact",
                            "Check the lesson evidence against the target",
                            "Check the complementary skill using the short task."):
                    self.assertNotIn(old,body)
                minutes=[int(x) for x in re.findall(r"(?m)^## [^\n]+ \((\d+) minutes\)$",body)]
                self.assertEqual(minutes,TIME,number)
                lines=body.splitlines()
                headings=[i for i,t in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",t)]
                self.assertEqual(len(headings),6)
                for h in headings:
                    self.assertTrue(lines[h+1].startswith("**Teacher:**"))
                    self.assertTrue(lines[h+2].startswith("**Pupils:**"))
                self.assertNotIn("FINAL READY",body)
    def test_legacy_language_arts_and_teacher_choice_untouched(self):
        for n,term in ((37,"Akbar's Dream"),(48,"PILIHAN GURU")):
            self.assertIn(term,(SRC/f"lesson_{n:03d}.md").read_text(encoding="utf-8"))
        self.assertTrue(SOW["6/48"]["teacher_selected"])
if __name__=="__main__":
    unittest.main()
