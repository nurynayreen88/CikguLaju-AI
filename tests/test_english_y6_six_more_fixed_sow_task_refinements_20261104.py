"""Six Year6 KPM SOW fixed-standard task refinements (set 2).

Original PDF: Primary Year6 SK SOW, Drive file
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z.
Source task checks only: no independent audio speech, book page visuals,
teacher final approval or authenticated Telegram delivery.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"rph_standalone"/"english"/"year6"
INDEX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CHECK={
 6:("3.2.3","3.2.2",("electricity","power","four unfamiliar words","TB p.24","text features")),
 8:("1.2.2","1.2.1",("PB p.13","TB p.30","main idea","Values","listening details")),
 9:("2.3.1","3.2.2",("when/while","PB p.12","TB p.28","short story","clock")),
 11:("3.2.2","4.3.1",("direct speech","PB pp.9/14","quotation marks","interview","punctuation")),
 13:("1.2.2","2.1.3",("Mike Dobbs","should/shouldn't","because","four details","TB p.36")),
 14:("2.3.1","1.2.5",("reporting verbs","PB p.16","TB p.35","emergency scene","questions")),
}
TIME=[5,10,18,15,8,4]
class SixFixedSowTasks(unittest.TestCase):
 def test_codes_source_tasks_pbd_minutes_and_reflection(self):
  self.assertEqual(len(CHECK),6)
  for n,(main,comp,phrases) in CHECK.items():
   with self.subTest(lesson=n):
    sow=INDEX[f"6/{n}"]
    self.assertFalse(sow["teacher_selected"])
    self.assertEqual((sow["main_ls"],sow["complementary_ls"]),(main,comp))
    body=(BASE/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
    self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",body)
    self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",body)
    self.assertIn("**Teacher reflection:**",body)
    self.assertNotIn("FINAL READY",body)
    self.assertNotIn("Share one accurate new sentence or fact",body)
    self.assertNotIn("Check the lesson evidence against the target",body)
    for phrase in phrases:
     self.assertIn(phrase.lower(),body.lower(),phrase)
    durations=[int(x) for x in re.findall(r"(?m)^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)[^\n]* \((\d+) minutes\)$",body)]
    self.assertEqual(durations,TIME,n)
    lines=body.splitlines()
    starts=[i for i,z in enumerate(lines) if re.match(r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",z)]
    self.assertEqual(len(starts),6)
    for at in starts:
     self.assertTrue(lines[at+1].startswith("**Teacher:**"))
     self.assertTrue(lines[at+2].startswith("**Pupils:**"))
if __name__=="__main__":
 unittest.main()
