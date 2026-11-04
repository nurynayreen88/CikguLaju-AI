"""Non-destructive English Y6 KPM SOW fixed-standard source fidelity for Lessons 113–124.

Original source: Primary Year6 SK Scheme of Work in Google Drive PDF
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z.
Do not infer final teacher signoff, media speech, full print review or Telegram.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"rph_standalone"/"english"/"year6"
IDX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
LESSONS={
 113:("3.2.1","3.3.1",("PB pp.96–97","moral","TB p.153","independent")),
 114:("4.2.3","3.2.2",("email","Lesson 119","TB p.154","first draft")),
 115:("1.2.2","2.1.4",("PB p.99","first-conditional","six","TB p.157")),
 116:("2.1.4","4.2.2",("PB p.100","might","may","could")),
 118:("3.2.2","3.2.1",("reading assessment","independently","formative","not as an invented")),
 119:("4.2.3","3.2.1",("Lesson 114","TB p.162","original email","summary")),
 120:("1.2.3","1.2.1",("PB p.101","truth","synonym","four")),
 121:("2.1.4","4.2.2",("topic picture cards","might","if + present","three")),
 123:("3.2.1","2.1.3",("PB p.105","genre","recommend","book")),
 124:("4.3.3","4.2.3",("PB p.104","review","Lesson 126","first-draft")),
}
class Year6TenFixedSowStoryAndFeedback(unittest.TestCase):
    def test_exact_original_pairs_and_six_phase_fidelity(self):
        self.assertEqual(len(LESSONS),10)
        for n,(main,comp,markers) in LESSONS.items():
            with self.subTest(n=n):
                ref=IDX[f"6/{n}"]
                self.assertFalse(ref["teacher_selected"])
                self.assertEqual((ref["main_ls"],ref["complementary_ls"]),(main,comp))
                body=(P/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(f"**Main CS/LS:** {main.rsplit('.',1)[0]}/{main}",body)
                self.assertIn(f"**Complementary CS/LS:** {comp.rsplit('.',1)[0]}/{comp}",body)
                self.assertIn("**Teacher reflection:**",body)
                self.assertIn("**RPT:** 2027",body)
                self.assertNotIn("FINAL READY",body)
                for phrase in markers:
                    self.assertIn(phrase.casefold(),body.casefold(),(n,phrase))
                for generic in (
                    "Share one accurate new sentence or fact",
                    "Check the lesson evidence against the target",
                    "Check the complementary skill using the short task.",
                ):
                    self.assertNotIn(generic,body)
                time=[int(m) for m in re.findall(r"(?m)^## [^\n]+ \((\d+) minutes\)$",body)]
                self.assertEqual(time,[5,10,18,15,8,4])
                lines=body.splitlines()
                phase=[i for i,x in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",x)]
                self.assertEqual(len(phase),6)
                for i in phase:
                    self.assertTrue(lines[i+1].startswith("**Teacher:**"))
                    self.assertTrue(lines[i+2].startswith("**Pupils:**"))
    def test_first_drafts_are_reused_not_recreated(self):
        email=(P/"lesson_114.md").read_text(encoding="utf-8")
        revision=(P/"lesson_119.md").read_text(encoding="utf-8")
        book=(P/"lesson_124.md").read_text(encoding="utf-8")
        self.assertIn("return in Lesson 119",email)
        self.assertIn("return teacher-marked Lesson 114 drafts",revision)
        self.assertIn("Lesson 126",book)
    def test_reading_assessment_is_formative_not_fake_grades(self):
        reading=(P/"lesson_118.md").read_text(encoding="utf-8")
        self.assertIn("formative",reading.lower())
        self.assertIn("not as an invented official UASA score",reading)
        self.assertNotIn("FINAL READY",reading)
if __name__=="__main__":
    unittest.main()
