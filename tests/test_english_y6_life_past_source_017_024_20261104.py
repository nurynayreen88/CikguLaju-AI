"""Seven English Year 6 Life in the Past RPH activity-fidelity regressions.

Grounding: original KPM Primary Year 6 SK Scheme of Work PDF
(Google Drive ID 1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z), Lessons 17–24.
Source-level evidence only: no audio sound identity or real Telegram release.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rph_standalone"/"english"/"year6"
INDEX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
EXPECTED={
 17:("3.2.3","3.2.1",("Samuel Pepys","Great Fire of London","TB p.43","context")),
 18:("4.3.3","3.2.1",("comparison table","London","peer","past")),
 19:("1.1.1","1.2.5",("used to","pronunciation","TB p.48","questions")),
 20:("2.1.1","4.2.1",("didn't use to","childhood","PB p.25","paragraph")),
 22:("3.2.1","3.2.2",("Gemma","diary","informal","PB p.28")),
 23:("4.2.3","4.3.1",("Gemma","diary entry","school","punctuation")),
 24:("1.2.2","4.3.2",("classroom","PB p.27","spelling","fifty years")),
}
MINUTES=[5,10,18,15,8,4]
class SevenKpmSowTasks(unittest.TestCase):
    def test_fidelity_pairs_pupil_evidence_and_unchanged_structures(self):
        self.assertEqual(len(EXPECTED),7)
        for n,(main,comp,phrases) in EXPECTED.items():
            with self.subTest(lesson=n):
                original=INDEX[f"6/{n}"]
                self.assertFalse(original["teacher_selected"])
                self.assertEqual((main,comp),(original["main_ls"],original["complementary_ls"]))
                t=(SRC/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",t)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",t)
                self.assertIn("**Teacher reflection:**",t)
                self.assertNotIn("FINAL READY",t)
                self.assertIn("**PBD evidence:**",t)
                self.assertNotIn("Share one accurate new sentence or fact",t)
                self.assertNotIn("Check the lesson evidence against the target",t)
                for phrase in phrases:
                    self.assertIn(phrase.lower(),t.lower(),phrase)
                times=[int(x) for x in re.findall(r"(?m)^## [^\n]+ \((\d+) minutes\)$",t)]
                self.assertEqual(times,MINUTES,n)
                lines=t.splitlines()
                sections=[i for i,z in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",z)]
                self.assertEqual(len(sections),6)
                for idx in sections:
                    self.assertTrue(lines[idx+1].startswith("**Teacher:**"))
                    self.assertTrue(lines[idx+2].startswith("**Pupils:**"))
    def test_protect_existing_literature_source(self):
        s=(SRC/"lesson_021.md").read_text(encoding="utf-8")
        self.assertIn("The Sandwich",s)
        self.assertIn("Flow Map",s)
if __name__=="__main__":
    unittest.main()
