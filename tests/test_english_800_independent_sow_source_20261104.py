"""Offline proof ledger for independently read 800 KPM English Y2–6 SOW PDFs.

Read-only. Never treats snapshot source-code presence as pedagogical signoff,
real Telegram delivery, or source-audio speech verification.
"""
import json
from pathlib import Path
import unittest

from web.english_y4_pending_draft_preview_runtime import adapt_rows as y4_pending_rows

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"audits"
CODES=json.loads((BASE/"english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
LEDGER=json.loads((BASE/"english_2_6_independent_sow_pdf_code_ledger_20261104.json").read_text(encoding="utf-8"))
AUDIO=json.loads((BASE/"english_y4_l030_direct_source_audio_20261104.json").read_text(encoding="utf-8"))

class IndependentPrimarySowVerification(unittest.TestCase):
    def test_exact_800_source_rows_and_no_false_final_release(self):
        self.assertEqual(len(CODES),800)
        self.assertEqual(len(LEDGER["rows"]),800)
        self.assertEqual(LEDGER["stats"],{
            "matched":765,"pdf_printing_anomalies":2,"teacher_choice":33,"total":800})
        self.assertNotIn("FINAL READY",LEDGER["verification_scope"])
        status_counts={}
        for year in range(2,7):
            count=0
            for lesson in range(1,161):
                label=f"{year}/{lesson}"
                source=CODES[label]
                row=LEDGER["rows"][label]
                self.assertNotIn("FINAL_READY",row["status"],label)
                if source["teacher_selected"]:
                    self.assertEqual(row["status"],"TEACHER_SELECTED_NOT_FIXED",label)
                    self.assertIsNone(source["main_ls"],label)
                    self.assertIsNone(source["complementary_ls"],label)
                elif row["status"]=="EXACT_SOW_PDF_CODE_MATCH":
                    self.assertIn(source["main_ls"],row["sow_pdf_observed_main_ls"],label)
                    self.assertIn(source["complementary_ls"],
                                  row["sow_pdf_observed_complementary_ls"],label)
                else:
                    self.assertEqual(row["status"],"SOW_PRINTING_ANOMALY_DSKP_RESOLUTION",label)
                    self.assertIn(label,("3/40","3/61"))
                    self.assertTrue(row["explanation"])
                status_counts[row["status"]]=status_counts.get(row["status"],0)+1
                count+=1
            self.assertEqual(count,160)
        self.assertEqual(status_counts,{
            "EXACT_SOW_PDF_CODE_MATCH":765,
            "SOW_PRINTING_ANOMALY_DSKP_RESOLUTION":2,
            "TEACHER_SELECTED_NOT_FIXED":33})

    def test_year3_printing_anomalies_cannot_be_silently_rewritten(self):
        r40,r61=LEDGER["rows"]["3/40"],LEDGER["rows"]["3/61"]
        self.assertNotIn("3.2.1",r40["sow_pdf_observed_main_ls"])
        self.assertIn("3.2.2",r40["sow_pdf_observed_complementary_ls"])
        self.assertEqual(CODES["3/40"]["main_ls"],"3.2.1")
        self.assertIn("3..2.1",r40["explanation"])
        self.assertIn("3.2.2",r61["sow_pdf_observed_main_ls"])
        self.assertNotIn("3.3.1",r61["sow_pdf_observed_complementary_ls"])
        self.assertEqual(CODES["3/61"]["complementary_ls"],"3.3.1")
        self.assertIn("DSKP",r61["explanation"])
        for n in (40,61):
            text=(ROOT/f"rph_standalone/english/year3/lesson_{n:03d}.md").read_text(encoding="utf-8")
            self.assertIn("NOT READY",text)
            self.assertIn("SOW",text)

    def test_y4_l030_book_and_audio_decision_is_evidence_based(self):
        self.assertEqual(AUDIO["lesson"],"English Year 4 Lesson 30 (Writing 6)")
        self.assertFalse(AUDIO["final_ready"])
        printed=AUDIO["printed_sources"]
        self.assertEqual(printed["teacher_book"]["printed_page"],39)
        self.assertEqual(printed["student_book"]["printed_page"],20)
        self.assertEqual(printed["sow"]["lesson"],30)
        self.assertIn("CD1",printed["teacher_book"]["activity_2_audio"])
        self.assertIn("CD2",printed["sow"]["activity_2_audio"])
        cd1,cd2=AUDIO["audio_files"]["CD1_Track29"],AUDIO["audio_files"]["CD2_Track29"]
        self.assertEqual(cd1["bytes"],218335)
        self.assertEqual(cd2["bytes"],245857)
        self.assertNotEqual(cd1["sha256"],cd2["sha256"])
        self.assertNotEqual(cd1["ffprobe_duration_seconds"],cd2["ffprobe_duration_seconds"])
        self.assertTrue(cd1["ffmpeg_decodes"] and cd2["ffmpeg_decodes"])
        self.assertTrue(any("speech" in s.lower() for s in AUDIO["not_verified"]))
        self.assertTrue(any("Telegram" in s for s in AUDIO["not_verified"]))
        self.assertEqual(CODES["4/30"]["main_ls"],"4.3.2")
        self.assertEqual(CODES["4/30"]["complementary_ls"],"1.2.5")

    def test_telegram_y4_l030_word_pdf_preview_uses_correct_source_warning(self):
        state={"subject":"English","year":"Year 4","lesson_no":30,"task":"rph",
               "sp_code":"4.3.2","comp_sp_code":"1.2.5"}
        baseline={"TAJUK":"Old lesson", "BAHAN BANTU MENGAJAR":"Old resources",
                  "TARIKH":"4/11/2026","KELAS":"4 Amanah","REFLEKSI":"Own notes",
                  "OBJEKTIF PEMBELAJARAN":"Legacy objective"}
        out=y4_pending_rows(state,baseline)
        self.assertIsNot(out,baseline)
        self.assertIn("DRAF",out["TAJUK"])
        self.assertIn("TB p.39",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("SB p.20",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("CD1 Track 29",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("CD2 Track 29",out["BAHAN BANTU MENGAJAR"])
        self.assertIn("confirm speech",out["BAHAN BANTU MENGAJAR"])
        self.assertEqual(out["MAIN LEARNING STANDARD"],"4.3.2")
        self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"],"1.2.5")
        for k in ("TARIKH","KELAS","REFLEKSI"):
            self.assertEqual(out[k],baseline[k])
        self.assertEqual(baseline["TAJUK"],"Old lesson")
        other={"subject":"English","year":"Year 5","lesson_no":30,"task":"rph"}
        self.assertIs(y4_pending_rows(other,baseline),baseline)

if __name__=="__main__":
    unittest.main()
