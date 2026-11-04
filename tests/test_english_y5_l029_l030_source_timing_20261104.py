"""Year 5 L29/30 original KPM SOW task and timing checks.

Source: Primary Year 5 SK SOW pp.65–66 (L29/L30), available in Drive
file 1FHJm1tl7IamOSZWIndUMoytm6SGoexAV. Audio content and Telegram
are NOT independently approved by this source-level test.
"""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rph_standalone"/"english"/"year5"
INDEX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
TASKS={
    29: {"main":"1.2.5","comp":"4.3.2","tracks":("CD3.02","CD3.03"),
         "words":("Tobias","Luke","spelling","information table"),
         "workbook":"p.18-19"},
    30: {"main":"2.2.1","comp":"1.2.5","tracks":("CD3.04",),
         "words":("Eriko","Liam","When's...?","swap roles"),
         "workbook":"p.19"},
}
class Year5SourceVerifiedTiming(unittest.TestCase):
    def test_sow_codes_source_pages_phases_and_draft_gates(self):
        for n,expected in TASKS.items():
            with self.subTest(lesson=n):
                rec=INDEX[f"5/{n}"]
                self.assertFalse(rec["teacher_selected"])
                self.assertEqual((rec["main_ls"],rec["complementary_ls"]),
                                 (expected["main"],expected["comp"]))
                t=(SOURCE/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn("Duration: 60 minutes",t)
                self.assertIn("SB p.92",t)
                self.assertIn("TB p.106",t)
                for track in expected["tracks"]:
                    self.assertIn(track,t)
                for word in expected["words"]:
                    self.assertIn(word,t)
                self.assertIn(expected["workbook"],t)
                self.assertIn("SOW-aligned draft",t)
                self.assertIn("content not yet played",t)
                self.assertIn("Workbook (existing source QA map)",t)
                phases=list(re.finditer(r"(?m)^[1-5]\. (.+?) \((\d+) min\):",t))
                self.assertEqual(len(phases),5)
                self.assertEqual([int(m.group(2)) for m in phases],
                                 [8,12,15,17,8])
                self.assertEqual(sum(int(m.group(2)) for m in phases),60)
                for i,match in enumerate(phases):
                    end=phases[i+1].start() if i+1<len(phases) else t.index("\nPBD:",match.end())
                    part=t[match.end():end]
                    self.assertIn("**Teacher:**",part)
                    self.assertIn("**Pupils:**",part)

    def test_specific_pbd_not_replaced_by_generic_task(self):
        a=(SOURCE/"lesson_029.md").read_text(encoding="utf-8")
        b=(SOURCE/"lesson_030.md").read_text(encoding="utf-8")
        self.assertIn("Listening 1.2.5",a)
        self.assertIn("Writing 4.3.2",a)
        self.assertIn("Speaking 2.2.1",b)
        self.assertIn("Listening 1.2.5",b)
        self.assertNotIn("SOW verification pending",a+b)
        self.assertNotIn("FINAL READY",a+b)

if __name__=="__main__":
    unittest.main()
