"""Year5 complete 120-MP3 Drive audio manifest and duplicate hash regression.

Does not confirm edition, spoken audio or authenticated Telegram delivery.
No original audio files, database records or user data are modified.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOC=json.loads((ROOT/"audits/english_y5_full_120_mp3_folder_inventory_20261105.json").read_text(encoding="utf-8"))
RISK=json.loads((ROOT/"audits/english_y1_y6_audio_source_risk_register_20261105.json").read_text(encoding="utf-8"))
SOW=json.loads((ROOT/"audits/english_y1_y6_960_sow_audio_index_20261105.json").read_text(encoding="utf-8"))

class YearFiveOriginalAudioFolderInventory(unittest.TestCase):
    def test_complete_disc_ranges_and_duplicate_are_not_overlooked(self):
        self.assertEqual(DOC["returned_item_count"],120)
        self.assertEqual(DOC["total_unique_disc_track_pairs"],119)
        self.assertEqual(DOC["extra_duplicate_copies"],1)
        self.assertEqual([(x["disc"],x["unique_tracks"],x["min_track"],x["max_track"])
                          for x in DOC["per_disc"]],
                         [(1,46,1,46),(2,37,1,37),(3,36,1,36)])
        self.assertTrue(all(x["missing_numbers"]==[] for x in DOC["per_disc"]))
        self.assertEqual(sum(x["unique_tracks"] for x in DOC["per_disc"]),119)
        self.assertIn("Second Edition",DOC["filename_pattern"])

    def test_binary_duplicate_preserved_not_deleted(self):
        dup=DOC["duplicate"]
        self.assertEqual((dup["disc"],dup["track"]),(2,12))
        self.assertEqual(dup["file_size_bytes"],742553)
        self.assertEqual(dup["sha256_both"],"447d6aab706f91a8949218af09edc05765ee7b5446807e0a9d747b0e0a773cf4")
        self.assertTrue(dup["identical_bytes"])
        self.assertFalse(dup["deleted"])
        self.assertNotEqual(dup["primary"]["file_id"],dup["copy"]["file_id"])

    def test_year5_l29_l30_source_file_candidates_not_final_ready(self):
        selected=DOC["selected_sow_audio_candidates"]
        self.assertEqual([(r["year"],r["lesson"],r["disc"],r["track"]) for r in selected],
                         [(5,29,3,2),(5,29,3,3),(5,30,3,4)])
        self.assertEqual(len({r["file_id"] for r in selected}),3)
        y5=next(x for x in SOW["years"] if x["year"]==5)
        index={r["lesson"]:r for r in y5["entries"]}
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in index[29]["sow_explicit_audio_references"]],
                         [(3,2),(3,3)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in index[30]["sow_explicit_audio_references"]],
                         [(3,4)])
        risk=next(x for x in RISK["confirmed_risks"]
                  if x["id"]=="Y5_TRACKS_FOUND_NOT_PLAYED")
        self.assertEqual(risk["status"],
                         "SOW_87_OF_87_TRACK_LABELS_AND_DRIVE_IDS_MATCH_CONTENT_AND_TELEGRAM_PENDING")
        for key in ("audio_speech_verified","telegram_active_route_verified",
                    "teacher_approved","final_ready_approved"):
            self.assertIs(DOC[key],False)

if __name__=="__main__":
    unittest.main()
