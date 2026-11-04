"""SOW source-led audit for six refined Year 6 fixed-standard RPH.

Primary Year 6 Scheme of Work PDF (KPM):
Google Drive file 1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z
Printed sections: Lessons 1, 2, 3, 4, 7 and 12.

This confirms task references and source content, NOT actual speech of
unverified audio, authentic user delivery, textbook activity page visual
inspection, or release FINAL READY.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rph_standalone"/"english"/"year6"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CASES={
 1:{"main":"3.2.1","comp":"4.2.4","evidence":("self-introductions","four children's","personality","p.5 Activity 1")},
 2:{"main":"4.2.1","comp":"2.1.1","evidence":("four questions","group members","PB p.5 Activity 3","personality")},
 3:{"main":"1.2.2","comp":"1.1.1","evidence":("jobs","places","photographer","police officer","definitions")},
 4:{"main":"2.1.1","comp":"4.2.1","evidence":("true and two false","picture evidence","corrected statements")},
 7:{"main":"4.2.3","comp":"2.3.1","evidence":("sentence-card game","past continuous","when","four")},
 12:{"main":"4.2.3","comp":"4.3.3","evidence":("newspaper report","headline","introduction","WB p.14","WB p.15","direct speech")}
}
TIME=[5,10,18,15,8,4]
class Year6SixSourceRefinements(unittest.TestCase):
 def test_original_sow_code_and_actual_task(self):
  self.assertEqual(len(CASES),6)
  for n,case in CASES.items():
   with self.subTest(lesson=n):
    item=SOW[f"6/{n}"]
    self.assertFalse(item["teacher_selected"])
    self.assertEqual(item["main_ls"],case["main"])
    self.assertEqual(item["complementary_ls"],case["comp"])
    t=(SOURCE/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
    self.assertRegex(t.splitlines()[0],rf"\bLesson\s+0*{n}\b")
    self.assertIn(f"**Main CS/LS:** {case['main'].rsplit('.',1)[0]}/{case['main']}",t)
    self.assertIn(f"**Complementary CS/LS:** {case['comp'].rsplit('.',1)[0]}/{case['comp']}",t)
    self.assertIn("**Teacher reflection:**",t)
    self.assertNotIn("FINAL READY",t)
    for phrase in case["evidence"]:
     self.assertIn(phrase.lower(),t.lower(),phrase)
    for stale in ("Share one accurate new sentence or fact",
                  "Check the complementary skill using the short task.",
                  "Check the lesson evidence against the target"):
     self.assertNotIn(stale,t)
    hours=[int(x) for x in re.findall(r"(?m)^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)[^\n]* \((\d+) minutes\)$",t)]
    self.assertEqual(hours,TIME,n)
    lines=t.splitlines()
    sections=[i for i,line in enumerate(lines) if re.match(r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",line)]
    self.assertEqual(len(sections),6)
    for i in sections:
     self.assertTrue(lines[i+1].startswith("**Teacher:** "), (n,i))
     self.assertTrue(lines[i+2].startswith("**Pupils:** "), (n,i))
 def test_no_fixed_year6_teacher_choice_gates_affected(self):
  source=SOURCE/"lesson_016.md"
  t=source.read_text(encoding="utf-8")
  self.assertTrue(SOW["6/16"]["teacher_selected"])
  self.assertIn("DRAF",t)
if __name__=="__main__":
 unittest.main()
