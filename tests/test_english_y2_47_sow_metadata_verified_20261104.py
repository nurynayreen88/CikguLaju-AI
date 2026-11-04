"""Source-proof regression: 47 English Year 2 legacy SOW code headers.

SOW original PDF evidence: audits/english_2_6_independent_sow_pdf_code_ledger_20261104.json
Scope: *only* independently checked Main/Complementary numeric code metadata.
Does NOT approve teacher-written lesson procedures, Workbook/audio, native
Telegram Word/PDF delivery, or change the source draft / payment gates.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILES=ROOT/"rph_standalone"/"english"/"year2"
INDEX=json.loads((ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
PROOF=json.loads((ROOT/"audits"/"english_2_6_independent_sow_pdf_code_ledger_20261104.json").read_text(encoding="utf-8"))["rows"]
FIXED=(27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,46,47,48,51,52,53,54,55,56,57,58,59,60,61,62,63,64,66,67,68,69,70,71,72,73,74,75,76,77,78,)

class LegacyYear2SowHeaderProof(unittest.TestCase):
    def test_exact_47_source_verified_headers_remain_draft(self):
        self.assertEqual(len(FIXED),47)
        self.assertEqual(len(set(FIXED)),47)
        for n in FIXED:
            with self.subTest(lesson=n):
                source=INDEX[f"2/{n}"]
                evidence=PROOF[f"2/{n}"]
                self.assertFalse(source["teacher_selected"])
                self.assertEqual(evidence["status"],"EXACT_SOW_PDF_CODE_MATCH")
                self.assertIn(source["main_ls"],evidence["sow_pdf_observed_main_ls"])
                self.assertIn(source["complementary_ls"],evidence["sow_pdf_observed_complementary_ls"])
                text=(FILES/f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(text.splitlines()[0],rf"\bLesson\s+0*{n}\b")
                header=text.split("\n## ",1)[0]
                for skill,expected in (("Main",source["main_ls"]),
                                       ("Complementary",source["complementary_ls"])):
                    line=next((line for line in header.splitlines()
                               if line.startswith(f"**{skill} SK/SP ")),None)
                    self.assertIsNotNone(line)
                    self.assertIn("KPM SOW code independently matched; task QA pending",line)
                    self.assertIn(f"/ {expected}",line)
                    self.assertNotIn("SOW verification pending",line)
                self.assertRegex(text,r"(?i)\b(?:not ready|draft|draf)\b")
                self.assertNotIn("FINAL READY",text)

if __name__=="__main__":
    unittest.main()
