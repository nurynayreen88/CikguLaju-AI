"""Complete English Year5 numbered audio filename/source-ID coverage.

Source-only confidence: 87/87 SOW CD/Track labels correspond to Drive MP3
candidate IDs. Spoken words, textbook edition, runtime Telegram source IDs
and teacher final approval are separate unverified gates.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=json.loads((ROOT/"audits/english_y5_all_87_sow_audio_refs_to_drive_file_ids_20261105.json").read_text(encoding="utf-8"))
SOW=json.loads((ROOT/"audits/english_y1_y6_960_sow_audio_index_20261105.json").read_text(encoding="utf-8"))
RISK=json.loads((ROOT/"audits/english_y1_y6_audio_source_risk_register_20261105.json").read_text(encoding="utf-8"))

class YearFiveSowFullAudioCrossCheck(unittest.TestCase):
    def test_all_87_refs_have_exact_disc_track_candidate_and_file_id(self):
        source={x["lesson"]:x for x in next(y for y in SOW["years"] if y["year"]==5)["entries"]}
        self.assertEqual(AUDIT["total_sow_lessons"],160)
        self.assertEqual(AUDIT["sow_lessons_with_explicit_audio"],62)
        self.assertEqual(AUDIT["sow_numbered_audio_references"],87)
        self.assertEqual(AUDIT["distinct_cd_track_references"],82)
        self.assertEqual(AUDIT["matched_references_by_cd_track_label"],87)
        self.assertEqual(AUDIT["missing_cd_track_label_references"],0)
        self.assertEqual(len(AUDIT["lesson_audio_candidates"]),62)
        all_pairs=set()
        total=0
        for row in AUDIT["lesson_audio_candidates"]:
            expected=source[row["lesson"]]["sow_explicit_audio_references"]
            found=row["tracks"]
            with self.subTest(lesson=row["lesson"]):
                self.assertEqual(len(found),len(expected))
                self.assertEqual([(x["cd"],x["track"]) for x in found],
                                 [(x["disc_or_audio_volume"],x["track"]) for x in expected])
                for observed,printed in zip(found,expected):
                    self.assertEqual(observed["sow_notation"],printed["original_notation"])
                    self.assertTrue(observed["drive_candidates"])
                    all_pairs.add((observed["cd"],observed["track"]))
                    total+=1
                    for candidate in observed["drive_candidates"]:
                        match=re.fullmatch(
                            r"([123])-(\d{1,3}) English Plus Second Edition Students Book 1(?: \(1\))?\.mp3",
                            candidate["filename"])
                        self.assertIsNotNone(match)
                        self.assertEqual((int(match[1]),int(match[2])),
                                         (observed["cd"],observed["track"]))
                        self.assertTrue(candidate["drive_file_id"])
                        self.assertGreater(candidate["size_bytes"],1000)
                        self.assertEqual(candidate["mime_type"],"audio/mpeg")
        self.assertEqual(total,87)
        self.assertEqual(len(all_pairs),82)

    def test_duplicate_not_misinterpreted_as_missing_or_deleted(self):
        self.assertEqual(AUDIT["inventory_mp3_files"],120)
        self.assertEqual(AUDIT["inventory_unique_cd_track_labels"],119)
        self.assertEqual(AUDIT["extra_duplicate_file_copies"],1)
        multiple=[(r["lesson"],x["cd"],x["track"],x["drive_candidates"])
                  for r in AUDIT["lesson_audio_candidates"] for x in r["tracks"]
                  if len(x["drive_candidates"])>1]
        self.assertEqual(len(multiple),1)
        lesson,cd,track,candidates=multiple[0]
        self.assertEqual((lesson,cd,track),(107,2,12))
        self.assertEqual(len(candidates),2)
        self.assertEqual({x["size_bytes"] for x in candidates},{742553})
        self.assertEqual(AUDIT["duplicate_cd2_track12_sha256_verified"],
                         "447d6aab706f91a8949218af09edc05765ee7b5446807e0a9d747b0e0a773cf4")

    def test_source_coverage_is_not_spoken_audio_or_telegram_approval(self):
        for field in ("independent_teacher_book_audio_content_verified",
                      "audio_speech_verified","textbook_edition_alignment_final_verified",
                      "app_runtime_drive_file_ids_verified",
                      "authenticated_teacher_telegram_send_verified",
                      "lesson_final_ready_approved","original_mp3_or_wma_file_modified"):
            self.assertFalse(AUDIT[field],field)
        risk=next(r for r in RISK["confirmed_risks"]
                  if r["id"]=="Y5_TRACKS_FOUND_NOT_PLAYED")
        self.assertEqual(risk["status"],
                         "SOW_87_OF_87_TRACK_LABELS_AND_DRIVE_IDS_MATCH_CONTENT_AND_TELEGRAM_PENDING")
        self.assertEqual(len(risk["lessons"]),62)

if __name__=="__main__":
    unittest.main()
