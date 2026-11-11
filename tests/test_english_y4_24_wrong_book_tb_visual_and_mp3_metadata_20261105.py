"""Offline audit invariants for 19 Year4 TB page checks and 24 MP3 source candidates.

These checks protect captured Drive listing / printed TB evidence. They cannot
verify audio speech, Telegram playback, user entitlement or an RPH release.
"""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=json.loads((ROOT/"audits/english_y4_24_wrong_book_tb_visual_and_mp3_metadata_crosscheck_20261105.json").read_text(encoding="utf-8"))
C=json.loads((ROOT/"audits/english_y4_legacy_wma_to_mp3_candidates_20261105.json").read_text(encoding="utf-8"))

class Year4AudioTBAndMP3Evidence(unittest.TestCase):
    def test_exact_count_and_known_source(self):
        self.assertEqual(E["source"]["google_drive_file_id"],"1lBWc96e8DCIMSdxzRuLC7CissHL52q8v")
        rows=E["source_checks"]
        self.assertEqual(len(rows),19)
        self.assertEqual({row["lesson"] for row in rows},
                         {7,8,9,11,12,17,22,24,29,32,48,59,97,98,99,102,103,107,110})
        self.assertEqual(sum(len(row["legacy_wma_tracks"]) for row in rows),24)
        self.assertEqual(sum(len(row["legacy_tracks_not_for_this_lesson"]) for row in rows),4)
        self.assertTrue(all(row["source_verification"]=="VISUALLY_CHECKED_ORIGINAL_TEACHERS_BOOK_PAGE" for row in rows))
        self.assertTrue(all(row["teacher_book_pdf_page"]>0 for row in rows))

    def test_prior_candidates_and_new_metadata_are_consistent(self):
        m=E["drive_listing_verification"]
        self.assertEqual((m["candidate_route_rows_matched_filename_size_id_mime_folder"],m["unique_mp3_files"],m["metadata_mismatches"]),(24,22,0))
        self.assertEqual((m["class_cd1_folder"]["listed_files"],m["class_cd2_folder"]["listed_files"]),(88,88))
        self.assertEqual(C["status"],"CANDIDATE_ONLY_NO_RUNTIME_USE")
        self.assertEqual(len(C["candidates"]),24)
        self.assertEqual(len({r["mp3_candidate"]["file_id"] for r in C["candidates"]}),22)
        rowmap={r["lesson"]:r for r in E["source_checks"]}
        for c in C["candidates"]:
            row=rowmap[c["lesson"]]
            self.assertIn(c["old_reference"],row["legacy_wma_tracks"])
            self.assertTrue(c["mp3_candidate"]["name"].lower().endswith(".mp3"))

    def test_source_conflict_is_preserved_and_audio_not_claimed_approved(self):
        rows={r["lesson"]:r for r in E["source_checks"]}
        self.assertEqual(rows[29]["book_required_tracks"],["CD3 Track 35","CD3 Track 36"])
        self.assertEqual(rows[29]["legacy_tracks_not_for_this_lesson"],["CD1 Track 35","CD1 Track 36"])
        self.assertEqual(rows[103]["book_required_tracks"],["CD2 Track 26"])
        self.assertEqual(rows[103]["legacy_tracks_not_for_this_lesson"],["CD2 Track 27","CD2 Track 28"])
        self.assertEqual(E["additional_confirmed_crosslesson"]["book_required_tracks"],["CD2 Track 27","CD2 Track 28"])
        self.assertEqual(E["totals"]["all_other_legacy_wma_routes_match_printed_disc_track"],20)
        self.assertIn("UNAPPROVED",E["release_status"])
        self.assertTrue(all(not r["audio_content_verified"] and not r["telegram_delivery_verified"] for r in rows.values()))

if __name__=="__main__":
    unittest.main()
