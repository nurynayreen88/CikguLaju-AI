"""Proof-of-provenance: actual Year5 books are all English Plus 1 Second Edition.

This is a recorded direct visual book-cover review + SHA256 evidence; the test
keeps independent recording speech, exact activity and Telegram delivery
approval false. It does not fetch original assets or touch user state.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
COVERS=json.loads((ROOT/"audits/english_y5_original_three_books_second_edition_cover_evidence_20261105.json").read_text(encoding="utf-8"))
AUDIO=json.loads((ROOT/"audits/english_y5_all_87_sow_audio_refs_to_drive_file_ids_20261105.json").read_text(encoding="utf-8"))
RISKS=json.loads((ROOT/"audits/english_y1_y6_audio_source_risk_register_20261105.json").read_text(encoding="utf-8"))

class OriginalYearFiveBookEdtionProof(unittest.TestCase):
    def test_three_independently_sha256_checked_books_same_edition(self):
        self.assertEqual(COVERS["series"],"English Plus 1")
        self.assertEqual(COVERS["observed_edition"],"Second Edition")
        self.assertEqual(COVERS["observed_year"],"Year 5")
        self.assertEqual([x["type"] for x in COVERS["books"]],
                         ["teacher_book","students_book","workbook"])
        expected={
         "teacher_book":("14Vpj-DjCbOERXdx7rGG8zhzNhsnUEPsM",162,66269773,
                         "28d16fd342559ec87426b50fc39c48d029005ef319e6a37f81ed7efdec3038fe"),
         "students_book":("13B4s4HacQgWn3M2QkzwHif6JdrBqc1Fw",122,44060870,
                          "0f1b0263ccec6689e896ba375690e4d0cb900e00f52a86832e16411c759eff96"),
         "workbook":("1cmRSBYK0_DfKyOOFZW5JazYk7AG6wl8E",110,47031351,
                     "b418aabdada23964f168c46966c0ceb4ef41b7f6eed37df6ca84abb23519cec4"),
        }
        for b in COVERS["books"]:
            fid,pages,size,digest=expected[b["type"]]
            self.assertEqual(b["drive_file_id"],fid)
            self.assertEqual(b["pdf_pages"],pages)
            self.assertEqual(b["size_bytes"],size)
            self.assertEqual(b["sha256"],digest)
            self.assertEqual(b["cover_pdf_page_one_based"],1)
            for label in ("English Plus 1","Second Edition","Year 5"):
                self.assertIn(label,b["visual_cover_text"])
        self.assertTrue(COVERS["all_three_books_series_year_edition_match"])
        self.assertTrue(COVERS["audio_filename_series_and_edition_match_original_book_covers"])

    def test_edition_source_is_not_spoken_audio_or_final_ready(self):
        self.assertTrue(AUDIO["original_book_cover_edition_verified"])
        self.assertTrue(AUDIO["books_and_filename_same_series_year_edition"])
        self.assertEqual(AUDIO["original_book_cover_edition_evidence"],
                         "audits/english_y5_original_three_books_second_edition_cover_evidence_20261105.json")
        self.assertEqual(AUDIO["sow_numbered_audio_references"],87)
        self.assertEqual(COVERS["original_sow_87_numbered_references_filename_match"],87)
        risk=next(x for x in RISKS["confirmed_risks"]
                  if x["id"]=="Y5_TRACKS_FOUND_NOT_PLAYED")
        self.assertTrue(risk["visual_original_edition_covers_verified"])
        for key in ("content_of_all_87_recordings_verified",
                    "exact_audio_task_per_lesson_tb_sb_page_verified",
                    "all_151_fixed_rph_teacher_approved",
                    "real_telegram_audio_send_verified","final_ready_approved"):
            self.assertFalse(COVERS[key],key)
        for key in ("audio_speech_verified",
                    "textbook_edition_alignment_final_verified",
                    "app_runtime_drive_file_ids_verified",
                    "authenticated_teacher_telegram_send_verified",
                    "lesson_final_ready_approved"):
            self.assertFalse(AUDIO[key],key)

if __name__=="__main__":
    unittest.main()
