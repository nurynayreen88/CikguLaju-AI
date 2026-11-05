"""Year 5 L29–30 original SOW/TB/SB/WB and MP3-identity evidence.

The source checks are deliberately independent of the production-release gate:
having the authentic book pages and MP3 file bytes DOES NOT verify spoken
dialogue, live Telegram delivery, A4 Word output, or teacher signoff.
"""
import json
from pathlib import Path
import unittest

from web.english_y5_standalone_runtime import approved_for_telegram, load_lesson

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT/"audits/english_y5_l029_l030_original_sow_tb_sb_wb_audio_sources_20261105.json").read_text(encoding="utf-8"))
SOW = json.loads((ROOT/"audits/english_y1_y6_960_sow_audio_index_20261105.json").read_text(encoding="utf-8"))
CANDIDATES = json.loads((ROOT/"audits/english_y5_all_87_sow_audio_refs_to_drive_file_ids_20261105.json").read_text(encoding="utf-8"))
GATE = json.loads((ROOT/"rph_standalone/english/year5/sow_standard_gate_2027.json").read_text(encoding="utf-8"))


class YearFiveL29L30OriginalEvidence(unittest.TestCase):
    def test_printed_sow_pages_and_fixed_learning_standards(self):
        self.assertEqual(AUDIT["source_books"]["sow"]["printed_pages_by_lesson"], {"29":64,"30":65})
        self.assertEqual(AUDIT["source_books"]["sow"]["pdf_pages_by_lesson"], {"29":65,"30":66})
        self.assertEqual(AUDIT["source_books"]["teacher_book"]["printed_page"],"T106")
        self.assertEqual(AUDIT["source_books"]["student_book"]["printed_page"],92)
        self.assertEqual(AUDIT["source_books"]["workbook"]["printed_pages"],[18,19])
        self.assertEqual([row["lesson"] for row in AUDIT["lesson_evidence"]],[29,30])
        for lesson,main,complementary in [(29,"1.2.5","4.3.2"),(30,"2.2.1","1.2.5")]:
            with self.subTest(lesson=lesson):
                row=next(x for x in AUDIT["lesson_evidence"] if x["lesson"]==lesson)
                fixed=GATE["lessons"][str(lesson)]
                self.assertFalse(fixed["teacher_choice"])
                self.assertEqual((row["sow_main_sp"],row["sow_complementary_sp"]),
                                 (main,complementary))
                self.assertEqual((fixed["main_ls"],fixed["complementary_ls"]),
                                 (main,complementary))
                self.assertTrue(row["printed_task_alignment_verified"])
                content=(ROOT/f"rph_standalone/english/year5/lesson_{lesson:03}.md").read_text(encoding="utf-8")
                self.assertIn(f"printed p.{row['sow_printed_page']}",content)
                self.assertIn("TB p.106",content)
                self.assertIn("SB p.92",content)
                self.assertIn("PRINTED SOURCE VERIFIED / DRAF",content)
                parsed=load_lesson(lesson)
                self.assertIsNotNone(parsed)

    def test_original_three_mp3_ids_match_both_sow_index_and_drive_inventory(self):
        files={v["label"]:v for v in AUDIT["original_audio_files"]}
        self.assertEqual(set(files), {"CD3.02","CD3.03","CD3.04"})
        sow_y5={v["lesson"]:v for v in next(y for y in SOW["years"] if y["year"]==5)["entries"]}
        candidates={v["lesson"]:v for v in CANDIDATES["lesson_audio_candidates"]}
        expected={29:[("CD3.02",3,2,"1T-HBLwsQ2C4eC3egNFZ9ZgDLsOxDRO6N"),
                      ("CD3.03",3,3,"16N8fUyxWYYyzmeEIYyB7_f1MzLS2i5Zf")],
                  30:[("CD3.04",3,4,"1e4xl-R1CYY3t0XGiWhr8sKxVRzBrTNcX")]}
        for lesson,tracks in expected.items():
            source_labels=[v["original_notation"] for v in sow_y5[lesson]["sow_explicit_audio_references"]]
            self.assertEqual(source_labels,[v[0] for v in tracks])
            candidates_in_lesson=candidates[lesson]["tracks"]
            for (label,disc,track,file_id),row in zip(tracks,candidates_in_lesson):
                self.assertEqual((row["cd"],row["track"],row["sow_notation"]),(disc,track,label))
                self.assertEqual(len(row["drive_candidates"]),1)
                self.assertEqual(row["drive_candidates"][0]["drive_file_id"],file_id)
                self.assertEqual(files[label]["drive_file_id"],file_id)
                self.assertEqual(files[label]["size_bytes"],row["drive_candidates"][0]["size_bytes"])
                self.assertEqual(files[label]["codec"],"mp3")
                self.assertEqual(len(files[label]["sha256"]),64)
                self.assertGreater(files[label]["duration_seconds"],0)

    def test_workbook_is_optional_and_all_final_release_gates_fail_closed(self):
        workbook=AUDIT["source_books"]["workbook"]
        self.assertIn("optional review",workbook["activity_context"])
        for number in (29,30):
            text=(ROOT/f"rph_standalone/english/year5/lesson_{number:03}.md").read_text(encoding="utf-8")
            self.assertIn("optional cross-topic practice only",text)
            self.assertIn("not the SOW core personal-information task",text)
            self.assertIn("Audio speech, authenticated Telegram delivery",text)
            self.assertFalse(approved_for_telegram(number))
        gates=AUDIT["gates"]
        self.assertTrue(gates["official_sow_pair_verified"])
        self.assertTrue(gates["printed_book_activity_verified"])
        self.assertTrue(gates["audio_file_identity_and_codec_verified"])
        for k in ("audio_spoken_contents_verified","authenticated_teacher_telegram_send_verified",
                  "teacher_final_approval","printed_word_a4_per_lesson_verified","final_ready_approved"):
            self.assertIs(gates[k],False,k)

if __name__=="__main__":
    unittest.main()
