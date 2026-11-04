"""English Y4 Lesson030 independent book/audio evidence must remain honest.

This is a source-integrity regression, NOT a playback/content test or teacher
approval. No app.py import, credits, production data or Telegram send.
"""
import json
from pathlib import Path
import re
import unittest

from web.english_y4_pending_draft_preview_runtime import adapt_rows, AUDIO_CONFLICT

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"audits/english_y4_l030_audio_source_evidence_20261104.json"
LESSON=ROOT/"rph_standalone/english/year4/lesson_030.md"
REGISTER=ROOT/"audits/english_2_6_800_lesson_technical_readiness_20261104.md"


class Lesson30AudioEvidence(unittest.TestCase):
    def test_source_and_audio_identity_is_fully_documented(self):
        d=json.loads(DOC.read_text(encoding="utf-8"))
        self.assertEqual((d["year"],d["lesson"]),(4,30))
        self.assertEqual(d["status"],"SOURCE_CONFLICT_AUDIO_CONTENT_NOT_VERIFIED")
        self.assertEqual(d["sow"]["activity_2_audio"],"CD2, Track 29")
        self.assertEqual(d["teacher_book"]["activity_2_audio"],"Class CD1 — Track 29")
        self.assertEqual((d["sow"]["standard_pair"]["main"],
                          d["sow"]["standard_pair"]["complementary"]),("4.3.2","1.2.5"))
        audio=d["audio_files"]
        self.assertEqual(len(audio),2)
        self.assertEqual({a["disc"] for a in audio},{"CD1","CD2"})
        self.assertEqual({a["track"] for a in audio},{29})
        self.assertEqual([a["bytes"] for a in audio],[218335,245857])
        self.assertNotEqual(audio[0]["sha256"],audio[1]["sha256"])
        self.assertNotEqual(audio[0]["duration_seconds"],audio[1]["duration_seconds"])
        for a in audio:
            self.assertRegex(a["sha256"],r"^[a-f0-9]{64}$")
            self.assertTrue(a["ffmpeg_decode_pass"])
            self.assertFalse(a["actual_spoken_content_verified"])
        # Visual check of original Workbook p.14 (PDF page 13), not a CD check.
        wb = d["workbook"]
        self.assertEqual(wb["drive_file_id"], "1vFEGRSrG0ANTweKVOV-TDCAAqL0_i9FX")
        self.assertEqual((wb["printed_page"], wb["pdf_page"], wb["activity"]), (14, 13, 1))
        self.assertTrue(wb["visual_source_check"])
        self.assertTrue(d["release_gates"]["printed_workbook_activity_checked"])
        self.assertIn("have to", wb["observed_content"])
        self.assertNotIn("audio verified", wb["rph_match"].lower())
        for k in ("correct_content_listening_verified",
                  "telegram_audio_mapping_verified",
                  "teacher_word_download_verified",
                  "native_pdf_download_verified",
                  "pedagogical_approval"):
            self.assertFalse(d["release_gates"][k],k)

    def test_rph_and_runtime_keep_explicit_conflict_and_no_ready(self):
        src=LESSON.read_text(encoding="utf-8")
        self.assertIn("CD1 Track 29",src)
        self.assertIn("CD2 Track 29",src)
        self.assertIn("NOT READY FOR RELEASE",src)
        old={"TARIKH":"04/11/2026",
             "MAIN LEARNING STANDARD":"Legacy",
             "COMPLEMENTARY LEARNING STANDARD":"Legacy"}
        st={"subject":"English","year":"Year 4","lesson_no":30,"task":"rph"}
        out=adapt_rows(st,old)
        self.assertIsNot(out,old)
        self.assertIn("DRAF",out["TAJUK"])
        self.assertEqual(out["TARIKH"],old["TARIKH"])
        self.assertEqual(out["MAIN LEARNING STANDARD"],"4.3.2")
        self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"],"1.2.5")
        self.assertIn("AUDIO REFERENCE CONFLICT",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("CD1",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("CD2",out["BAHAN BANTU MENGAJAR"])
        self.assertIs(adapt_rows({**st,"sp_code":"9.9.9"},old),old)
        self.assertIs(adapt_rows({**st,"year":"Year 5"},old),old)
        self.assertIn("AUDIO_SOURCE_CONFLICT_DRAFT",REGISTER.read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
