"""Eight original KPM SOW English Year6 music / film source regressions.

Original Primary Year6 SK Scheme of Work in Google Drive:
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z, Lessons 102–110.
No existing copyrighted song lyric copied; media identity and live
Telegram delivery remain independent release gates.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
RPH=ROOT/"rph_standalone"/"english"/"year6"
SOW=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CASES={
    102:("3.2.1","1.1.1",("PB pp.88–89","rhyme","TB p.142","title")),
    103:("4.3.2","1.1.1",("PB p.88","first/worst","verse","TB p.143")),
    104:("1.3.1","3.2.2",("PB p.87","dictionary","TB p.140","dialogue")),
    105:("2.1.1","4.2.5",("PB p.90","TB p.144","favourite song","four")),
    107:("3.2.1","2.3.1",("PB p.91","film","script","emotion")),
    108:("4.2.1","4.3.1",("interview","question marks","blog","three to five")),
    109:("1.2.3","3.3.1",("PB pp.92–95","Audio 2.6","play","four")),
    110:("2.1.1","2.2.1",("speaking assessment","two candidates","examiner","feedback")),
}
class KpmYear6MusicFilmEight(unittest.TestCase):
    def test_pairs_topic_pbd_60min_and_nonrelease(self):
        self.assertEqual(len(CASES),8)
        for n,(main,comp,phrases) in CASES.items():
            with self.subTest(lesson=n):
                rec=SOW[f"6/{n}"]
                self.assertFalse(rec["teacher_selected"])
                self.assertEqual((rec["main_ls"],rec["complementary_ls"]),(main,comp))
                t=(RPH/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(t.splitlines()[0],rf"\bLesson\s+0*{n}\b")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",t)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",t)
                self.assertIn("**Teacher reflection:**",t)
                self.assertIn("**RPT:** 2027",t)
                self.assertIn("**PBD evidence:**",t)
                self.assertNotIn("FINAL READY",t)
                for marker in phrases:
                    self.assertIn(marker.casefold(),t.casefold(),(n,marker))
                self.assertNotIn("Share one accurate new sentence or fact",t)
                self.assertNotIn("Check the lesson evidence against the target",t)
                minutes=[int(m) for m in re.findall(r"(?m)^## [^\n]+ \((\d+) minutes\)$",t)]
                self.assertEqual(minutes,[5,10,18,15,8,4])
                lines=t.splitlines()
                section=[i for i,z in enumerate(lines)
                         if re.match(r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",z)]
                self.assertEqual(len(section),6)
                for pos in section:
                    self.assertTrue(lines[pos+1].startswith("**Teacher:**"))
                    self.assertTrue(lines[pos+2].startswith("**Pupils:**"))
    def test_adjacent_language_arts_not_regenerated(self):
        self.assertTrue((RPH/"lesson_106.md").exists())
        self.assertEqual(SOW["6/106"]["focus"],"Language Arts 20")
    def test_speaking_test_is_formative_not_exam_grade(self):
        s=(RPH/"lesson_110.md").read_text(encoding="utf-8")
        self.assertIn("formative",s.casefold())
        self.assertIn("not numerical scores",s)
        self.assertNotIn("official mark",s.split("**PBD evidence:**")[0])
if __name__=="__main__":
    unittest.main()
