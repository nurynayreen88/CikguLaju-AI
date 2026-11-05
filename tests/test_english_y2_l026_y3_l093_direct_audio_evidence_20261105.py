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
        self.assertIn("CD1 Track 97",source3)
        self.assertIn("Tony",source3)
        self.assertIn("NOT READY",source2)
        self.assertIn("NOT READY",source3)
        for row in EVIDENCE["cases"]:
            for unverified in ("spoken_words_checked","telegram_bot_file_id_route_checked",
                               "actual_bot_send_checked","final_ready_approved"):
                self.assertIs(row[unverified],False)

    def test_risk_ledger_only_promotes_physical_source_not_delivery(self):
        statuses={r["id"]:r["status"] for r in RISKS["confirmed_risks"]}
        self.assertEqual(statuses["Y2_L26_AUDIO_TB_CHECK"],
                         "ORIGINAL_TB_AND_FILE_METADATA_VERIFIED_SPEECH_AND_TELEGRAM_PENDING")
        self.assertEqual(statuses["Y3_L93_TRACK97_RECHECK"],
                         "ORIGINAL_TB_TRACK97_VERIFIED_DISC_FILE_AND_TELEGRAM_PENDING")
        self.assertIn("NOT_FINAL",EVIDENCE["overall_release"].replace(
            "SOURCE_EVIDENCE_VERIFIED_DELIVERY_AND_SPEECH_UNVERIFIED",
            "NOT_FINAL_SOURCE_EVIDENCE"))

if __name__=="__main__":
    unittest.main()
