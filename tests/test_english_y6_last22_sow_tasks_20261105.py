"""Source-specific Year6 final 22 fixed-SOW source tasks, 2026-11-05.

Original KPM Primary Year6 SK SOW PDF stored in connected Drive:
1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z.
This protects source pedagogy, not unplayed audio, teacher signoff or live bot.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"rph_standalone"/"english"/"year6"
IDX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
CASES={
 125:("listening assessment","formative","Lesson 126"),
 126:("Lesson 124","TB p.165","book","question"),
 129:("Sugar, Sugar","PB pp.108–109","TB p.171","context"),
 130:("TB p.172","reference","sugar","fatty"),
 131:("Alice","Tomoko","tablet","PB p.112"),
 132:("reported speech","TB p.174","A/B/C","partner"),
 134:("Bart's","TB p.180","opinion","paragraph"),
 135:("uniform","TB p.180","pros","cons"),
 136:("multi-tasking","PB p.113","Audio 2.15","debate"),
 137:("For/Against","multi-tasking","clarification","debate"),
 139:("The Power of Stories","PB pp.118–120","jigsaw","story"),
 140:("£20,000","school","TB p.184","principal"),
 141:("Lesson 142","poster","short","story"),
 142:("Lesson 141","debate","TB p.182","For"),
 145:("detective","PB pp.122–123","mind map","suspect"),
 146:("Sue Snaps","TB p.192","past-tense","story"),
 147:("PB p.126","Obligation","must","museum"),
 148:("question tag","TB p.194","rising","pair"),
 150:("WB p.107","persistence","PB pp.129","quiz"),
 151:("WB p.110","script","TB p.200","punctuation"),
 152:("Audio 2.19","Nazca","heritage","spelled"),
 153:("TB p.202","mystery","PB p.130","questions"),
}
TIME=[5,10,18,15,8,4]
class SourceAlignedYear6FixedSowLast22(unittest.TestCase):
    def test_fidelity_and_original_numbers(self):
        self.assertEqual(len(CASES),22)
        for n,markers in CASES.items():
            with self.subTest(lesson=n):
                record=IDX[f"6/{n}"]
                self.assertFalse(record["teacher_selected"])
                self.assertTrue(record["main_ls"] and record["complementary_ls"])
                text=(BASE/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                for label,code in (("Main",record["main_ls"]),
                                   ("Complementary",record["complementary_ls"])):
                    self.assertIn(f"**{label} CS/LS:** {code.rsplit('.',1)[0]}/{code}",text)
                self.assertIn("**Teacher reflection:**",text)
                self.assertIn("**RPT:** 2027",text)
                self.assertNotIn("FINAL READY",text)
                for marker in markers:
                    self.assertIn(marker.casefold(),text.casefold(),(n,marker))
                for boilerplate in ("Share one accurate new sentence or fact",
                                    "Check the lesson evidence against the target",
                                    "Check the complementary skill using the short task."):
                    self.assertNotIn(boilerplate,text)
                self.assertEqual([int(m) for m in re.findall(
                    r"(?m)^## [^\n]+ \((\d+) minutes\)$",text)],TIME,n)
                lines=text.splitlines()
                headings=[i for i,z in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",z)]
                self.assertEqual(len(headings),6)
                for h in headings:
                    self.assertTrue(lines[h+1].startswith("**Teacher:**"))
                    self.assertTrue(lines[h+2].startswith("**Pupils:**"))
    def test_cross_lesson_reuse_and_noninvented_assessment(self):
        l125=(BASE/"lesson_125.md").read_text(encoding="utf-8")
        l126=(BASE/"lesson_126.md").read_text(encoding="utf-8")
        l141=(BASE/"lesson_141.md").read_text(encoding="utf-8")
        l142=(BASE/"lesson_142.md").read_text(encoding="utf-8")
        self.assertIn("without generating official scores",l125)
        self.assertIn("Lesson 124",l126)
        self.assertIn("Lesson 142",l141)
        self.assertIn("Lesson 141",l142)
    def test_untouched_language_arts_and_teacher_selected_sources_exist(self):
        for n in (127,128,133,138,143,144,149,154,155,156,157,158,159,160):
            self.assertTrue((BASE/f"lesson_{n:03d}.md").exists())
        for n in (128,144,155,156,157,158,160):
            self.assertTrue(IDX[f"6/{n}"]["teacher_selected"])
if __name__=="__main__":
    unittest.main()
