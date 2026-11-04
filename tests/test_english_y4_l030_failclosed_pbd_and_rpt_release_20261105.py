"""Release blockers: Y4 Lesson030 must not tell teachers to play unverified audio.

Source reference from original KPM Year4 SOW Lesson30 versus
Get Smart Plus4 TB p39. Speech mismatch cannot be concluded from
Drive filename, durations, checksum or a passing CI test.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RPH = ROOT / "rph_standalone/english/year4/lesson_030.md"
SOW = ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json"
AUDIO = ROOT / "audits/english_y4_l030_audio_source_evidence_20261104.json"

class Lesson30FailClosed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rph = RPH.read_text(encoding="utf-8")
        cls.idx = json.loads(SOW.read_text(encoding="utf-8"))["lessons"]["4/30"]
        cls.audio = json.loads(AUDIO.read_text(encoding="utf-8"))

    def test_source_fixed_codes_and_draft_status(self):
        self.assertFalse(self.idx["teacher_selected"])
        self.assertEqual((self.idx["main_ls"],self.idx["complementary_ls"]),
                         ("4.3.2","1.2.5"))
        self.assertIn("**Main SP:** Writing 4.3.2",self.rph)
        self.assertIn("**Complementary SP:** Listening 1.2.5",self.rph)
        self.assertIn("**QA status:** NOT READY FOR RELEASE",self.rph)
        self.assertEqual(self.audio["status"],"SOURCE_CONFLICT_AUDIO_CONTENT_NOT_VERIFIED")
        self.assertFalse(self.audio["release_gates"]["correct_content_listening_verified"])
        self.assertFalse(self.audio["release_gates"]["telegram_audio_mapping_verified"])

    def test_no_unconditional_play_or_false_listening_pbd(self):
        self.assertNotIn("**Teacher:** Follow TB Activity 2 using CD1 Track 29",self.rph)
        self.assertNotIn("**Pupils:** Listen to Track 29",self.rph)
        self.assertIn("neither CD1 nor CD2 Track 29 may be played or sent",self.rph)
        self.assertIn("**Listening SP 1.2.5 is pending**",self.rph)
        self.assertIn("Do not record this silent/pair-reading alternative as evidence",self.rph)
        self.assertIn("After track approval",self.rph)
        self.assertIn("correct recording is independently approved",self.rph)
        self.assertIn("Workbook p.15 Activity 3",self.rph)
        self.assertIn("**PBD:** Assess Writing SP 4.3.2",self.rph)
        self.assertIn("**QA status:** NOT READY",self.rph)

    def test_keep_original_phases_and_teacher_choice_boundary(self):
        durations=[int(n) for n in re.findall(
            r"(?m)^## [^\n]+ \((\d+) minutes\)$",self.rph)]
        self.assertEqual(durations,[10,15,20,10,5])
        self.assertEqual(sum(durations),60)
        for marker in ("## Set induction","## Activity 1","## Activity 2",
                       "## Reinforcement and PBD","## Closure"):
            self.assertIn(marker,self.rph)

if __name__=="__main__":
    unittest.main()
