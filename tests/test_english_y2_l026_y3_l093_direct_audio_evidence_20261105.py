"""Regression for directly inspected Year2/Year3 Teacher's Book audio sources.

Read-only assertions. Recorded TB pages and WMA hash/codec inventory are
human-confirmed evidence and do NOT certify speech content or Telegram send.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = json.loads((ROOT / "audits" /
    "english_y2_l026_y3_l093_direct_tb_audio_check_20261105.json"
    ).read_text(encoding="utf-8"))
RISKS = json.loads((ROOT / "audits" /
    "english_y1_y6_audio_source_risk_register_20261105.json"
    ).read_text(encoding="utf-8"))


class YearTwoThreeAudioPhysicalSourceEvidence(unittest.TestCase):
    def test_exact_lesson_and_teacher_book_page_anchors(self):
        self.assertEqual([(r["year"],r["lesson"]) for r in EVIDENCE["cases"]],
                         [(2,26),(3,93)])
        y2,y3=EVIDENCE["cases"]
        self.assertEqual((y2["book"],y2["tb_printed_page"],y2["sb_page"]),
                         ("Super Minds 1","T70",70))
        self.assertEqual(y2["tb_pdf_zero_based_index"],151)
        self.assertEqual([r["printed_audio"] for r in y2["activity_source"]],
                         ["CD2 Track 35","CD2 Track 36"])
        self.assertEqual((y3["book"],y3["tb_printed_pages"],y3["tb_pdf_zero_based_indices"]),
                         ("Get Smart Plus 3",[96,97],[97,98]))
        self.assertEqual(y3["tb_confirms_track_number"],97)
        self.assertFalse(y3["tb_confirms_disc_number"])
        self.assertIsNone(y3["original_track_file_id"])

    def test_two_original_wma_assets_preserved_as_wma(self):
        y2=EVIDENCE["cases"][0]
        files=y2["original_audio"]
        self.assertEqual(len(files),2)
        self.assertEqual([x["filename"] for x in files],
                         ["CD2-35.wma","CD2-36.wma"])
        self.assertEqual([x["size_bytes"] for x in files],[1832078,1108982])
        self.assertEqual([x["drive_file_id"] for x in files],
                         ["1ZxYROG_L291L8WWIq2_J3NZDiW8giBkK",
                          "1DZnb_IvBrqYfNZqWxuliQlJ-uGPgqIz9"])
        self.assertEqual({x["parent_folder_id"] for x in files},
                         {"1EQxVxNqvyg-dKi_pLTtEomOFwuUTC-cv"})
        self.assertTrue(all(x["container_probe_codec"]=="wmav2" for x in files))
        self.assertTrue(all(len(x["sha256"])==64 for x in files))
        self.assertEqual([round(x["duration_seconds"],3) for x in files],
                         [113.599,68.440])
        self.assertTrue(all(not x["filename"].endswith(".mp3") for x in files))

    def test_source_rph_cites_correct_tracks_but_no_premature_ready(self):
        source2=(ROOT/"rph_standalone/english/year2/lesson_026.md").read_text(encoding="utf-8")
        source3=(ROOT/"rph_standalone/english/year3/lesson_093.md").read_text(encoding="utf-8")
        for label in ("CD2 Track 35","CD2 Track 36"):
            self.assertIn(label,source2)
        self.assertIn("printed Track 97",source3)
        self.assertNotIn("Class CD1 Track 97 (teacher-confirmed",source3)
        self.assertIn("original WMA file IDs",source2)
        self.assertIn("Tony",source3)
        self.assertIn("NOT READY",source2)
        self.assertIn("NOT READY",source3)
        y2,y3=EVIDENCE["cases"]
        self.assertIs(y2["telegram_bot_file_id_route_checked"],True)
        self.assertEqual(y2["telegram_sender"],"_eng12_send_verified_audio")
        self.assertEqual(y2["telegram_sender_literal_entries"],163)
        self.assertEqual(y2["telegram_sender_route_match"],{"CD2_35":True,"CD2_36":True})
        self.assertIs(y3["telegram_bot_file_id_route_checked"],False)
        for row in EVIDENCE["cases"]:
            for unverified in ("spoken_words_checked","actual_bot_send_checked","final_ready_approved"):
                self.assertIs(row[unverified],False)

    def test_actual_telegram_wma_source_id_literals_match_verified_drive(self):
        from tools.audit_english_y2_l026_telegram_route_from_ast_20261105 import extract,EXPECTED
        mapping,_line=extract()
        self.assertEqual(len(mapping),163)
        for name,source_id in EXPECTED.items():
            with self.subTest(track=name):
                self.assertEqual(mapping.get(name),source_id)

    def test_year3_printed_track_is_not_conflated_with_year4_literal_map(self):
        y3=EVIDENCE["cases"][1]
        self.assertFalse(y3["actual_app_year3_specific_top_level_audio_literal_route_found"])
        self.assertFalse(y3["tb_confirms_disc_number"])
        self.assertIsNone(y3["original_track_file_id"])
        self.assertIn("Year3-specific",y3["static_source_scope_limit"])
        from tools.audit_english_y3_l093_static_media_routes_20261105 import run
        report=run()
        self.assertEqual(report["lesson93_literal_matches"],[])
        self.assertFalse(report["actual_media_file_id_verified"])
        self.assertFalse(report["live_telegram_send_verified"])
        self.assertEqual(report["release_status"],"NO_FINAL_READY")

    def test_y3_unique_original_cd1_track97_is_a_candidate_not_audio_approval(self):
        y3=EVIDENCE["cases"][1]
        data=y3["class_cd_inventory"]
        self.assertEqual(data["source_spreadsheet_id"],
                         "1xzRM71yAZDM0ZgW_457RVtAixQ27kit7RiGaG0WASPY")
        self.assertEqual(data["source_sheet"],"YEAR3_CLASS_CD")
        self.assertEqual(data["source_row_number"],98)
        self.assertEqual(data["disc_file_counts"],{"CD1":99,"CD2":91,"CD3":11})
        self.assertEqual(data["total_files"],201)
        self.assertTrue(data["no_track_number_gaps"])
        self.assertEqual(data["unique_disc_containing_track97"],"CD1")
        candidate=data["candidate"]
        self.assertEqual(candidate["title"],"Track 97.mp3")
        self.assertEqual(candidate["drive_file_id"],"1ZC_p24-ggASU_DceLRXUKc26nUssouk-")
        self.assertEqual(candidate["file_size_bytes"],648935)
        self.assertEqual(candidate["sha256"],
                         "f7253c240cd25ff862f911d25ba3a2ffe2ebc46efc91612ade933b4a197a5fa6")
        self.assertEqual(candidate["codec"],"mp3")
        self.assertAlmostEqual(candidate["duration_seconds"],40.222438,places=4)
        self.assertFalse(data["spoken_words_checked"])
        self.assertFalse(data["actual_bot_send_checked"])
        self.assertFalse(data["telegram_bot_file_id_route_checked"])
        self.assertFalse(data["candidate_is_final_approved"])
        self.assertIsNone(y3["original_track_file_id"])
        text=(ROOT/"rph_standalone/english/year3/lesson_093.md").read_text(encoding="utf-8")
        self.assertIn("Track 97 exists only in CD1",text)
        self.assertIn("Do not enable or send this candidate",text)
        self.assertIn("NOT READY FOR RELEASE",text)

    def test_risk_ledger_only_promotes_physical_source_not_delivery(self):
        statuses={r["id"]:r["status"] for r in RISKS["confirmed_risks"]}
        self.assertEqual(statuses["Y2_L26_AUDIO_TB_CHECK"],
                         "ORIGINAL_TB_WMA_AND_BOT_CODE_FILE_IDS_VERIFIED_LIVE_SEND_AND_SPEECH_PENDING")
        self.assertEqual(statuses["Y3_L93_TRACK97_RECHECK"],
                         "TB_TRACK97_AND_ONLY_CD1_CANDIDATE_FILE_HASH_VERIFIED_AUDIO_SPEECH_APP_ROUTE_PENDING")
        self.assertNotIn("FINAL_READY",EVIDENCE["overall_release"])

if __name__=="__main__":
    unittest.main()
