"""Web selected-page and original MP3 parity without exposing storage IDs."""
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask, jsonify
from web.unified_rph_web import create_blueprint, source_records
from web.native_telegram_extra_materials_20261106 import (
    english_student_book_metadata, english_audio_tracks,
    ENGLISH_ASSET_SOURCE,
)

ROOT = Path(__file__).resolve().parents[1]


class WebEnglishSourceTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client = self.app.test_client()
        self.row = next(r for r in source_records(4, "ENGLISH") if r["lesson"] == 93)
        self.sel = {"year": "4", "subject": "ENGLISH",
                    "unit": self.row["unit"], "lesson": self.row["token"]}

    def account(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id": 1, "authenticated": True}, None))

    def test_individual_source_download_actions_are_present(self):
        with self.account(), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="English Tahun 4 Lesson 93 Workbook m/s 55"), patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
                return_value="English Tahun 4 Lesson 93 Student Book m/s 66,67"), patch(
                "web.native_telegram_extra_materials_20261106.english_audio_tracks",
                return_value=[{"index": 1, "title": "English Year 4 Lesson 93 CD2 Track 16",
                               "reference": "CD2 Track 16"}]):
            answer = self.client.get("/api/web/rph/extra-materials", query_string=self.sel)
        self.assertEqual(answer.status_code, 200)
        self.assertEqual([r["type"] for r in answer.json["items"]],
                         ["textbook", "workbook", "audio"])
        urls = [r["url"] for r in answer.json["items"]]
        self.assertTrue(all("lesson=e-4-093" in u for u in urls))
        self.assertTrue(any("/english-student-book?" in u for u in urls))
        self.assertTrue(any("/english-audio/1?" in u for u in urls))
        self.assertNotIn("storage_file_id", str(answer.json))

    def test_new_source_503_never_hides_existing_workbook(self):
        with self.account(), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="English Tahun 4 Lesson 93 Workbook m/s 55"), patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
                side_effect=RuntimeError("Telegram old deploy")), patch(
                "web.native_telegram_extra_materials_20261106.english_audio_tracks",
                side_effect=RuntimeError("Telegram old deploy")):
            answer = self.client.get("/api/web/rph/extra-materials", query_string=self.sel)
        self.assertEqual(answer.status_code, 200)
        self.assertEqual([r["type"] for r in answer.json["items"]], ["workbook"])
        self.assertIn("belum dapat disahkan", answer.json["note"])

    def test_pdf_and_mp3_require_exact_selection(self):
        with self.account(), patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_pdf",
                return_value=b"%PDF-1.7\n" + b"X" * 1200), patch(
                "web.native_telegram_extra_materials_20261106.english_audio_mp3",
                return_value=b"ID3" + b"A" * 1200):
            book = self.client.get("/api/web/rph/english-student-book",
                                   query_string=self.sel)
            audio = self.client.get("/api/web/rph/english-audio/1",
                                    query_string=self.sel)
        self.assertEqual(book.status_code, 200)
        self.assertEqual(book.mimetype, "application/pdf")
        self.assertIn("Lesson_093", book.headers["Content-Disposition"])
        self.assertEqual(audio.status_code, 200)
        self.assertEqual(audio.mimetype, "audio/mpeg")
        self.assertEqual(audio.headers["Cache-Control"], "no-store, private")
        with self.account():
            other = self.client.get("/api/web/rph/english-audio/1",
                                    query_string={**self.sel, "unit": "Wrong Unit"})
            bad_track = self.client.get("/api/web/rph/english-audio/5",
                                        query_string=self.sel)
        self.assertEqual(other.status_code, 400)
        self.assertEqual(bad_track.status_code, 400)

    def test_unauthenticated_downloads_are_rejected(self):
        with patch("web.unified_rph_web._account",
                   return_value=(None, ({"error": "Login"}, 401))):
            self.assertEqual(self.client.get(
                "/api/web/rph/english-student-book",
                query_string=self.sel).status_code, 401)
            self.assertEqual(self.client.get(
                "/api/web/rph/english-audio/1",
                query_string=self.sel).status_code, 401)

    def test_wrong_source_and_track_identity_fail_closed(self):
        with patch("web.native_telegram_extra_materials_20261106._json",
                   return_value={"source": "wrong", "available": True,
                                 "year": 4, "lesson": 93, "type": "textbook",
                                 "format": "pdf", "pages": [66, 67],
                                 "title": "English Student Book Y4 Lesson 93",
                                 "status": "VERIFIED_SOURCE"}):
            with self.assertRaises(Exception):
                english_student_book_metadata(4, 93)
        with patch("web.native_telegram_extra_materials_20261106._json",
                   return_value={"source": ENGLISH_ASSET_SOURCE, "available": True,
                                 "year": 4, "lesson": 93, "status": "VERIFIED_SOURCE",
                                 "tracks": [{"index": 2, "title": "English Year 4 Lesson 93 CD2 Track 16",
                                             "reference": "CD2 Track 16"}]}):
            with self.assertRaises(Exception):
                english_audio_tracks(4, 93)

    def test_year_three_lesson_download_uses_same_identity(self):
        row = next(r for r in source_records(3, "ENGLISH") if r["lesson"] == 45)
        params = {"year": 3, "subject": "ENGLISH", "unit": row["unit"], "lesson": row["token"]}
        bridge = "web.native_telegram_extra_materials_20261106."
        with self.account(), patch(bridge + "english_workbook_metadata", return_value="Workbook m/s 23"), patch(
                bridge + "english_student_book_metadata", return_value="Student Book m/s 32, 33") as book, patch(
                bridge + "english_audio_tracks", return_value=[{"index": 1, "title": "CD1 Track 49"}]) as audio:
            reply = self.client.get("/api/web/rph/extra-materials", query_string=params)
        self.assertEqual(reply.status_code, 200)
        book.assert_called_once_with(3, 45)
        audio.assert_called_once_with(3, 45)
        self.assertEqual([row["type"] for row in reply.json["items"]], ["textbook", "workbook", "audio"])
        self.assertTrue(all("lesson=e-3-045" in row["url"] for row in reply.json["items"]))

    def test_year_two_original_wma_is_a_lesson_bound_download(self):
        from web.native_telegram_extra_materials_20261106 import WMA_HEADER
        row = next(r for r in source_records(2, "ENGLISH") if r["lesson"] == 26)
        params = {"year": 2, "subject": "ENGLISH", "unit": row["unit"], "lesson": row["token"]}
        bridge = "web.native_telegram_extra_materials_20261106."
        audio = WMA_HEADER + b"A" * 1600
        with self.account(), patch(bridge + "english_workbook_metadata", return_value=None), patch(
                bridge + "english_student_book_metadata", return_value="Student Book m/s 70"), patch(
                bridge + "english_audio_tracks", return_value=[{"index": 1, "title": "CD2 Track 35"}]), patch(
                bridge + "english_audio_wma", return_value=audio) as source:
            reply = self.client.get("/api/web/rph/extra-materials", query_string=params)
            self.assertEqual([item["type"] for item in reply.json["items"]], ["textbook", "audio"])
            response = self.client.get(reply.json["items"][1]["url"])
        source.assert_called_once_with(26, 1)
        self.assertEqual(response.data, audio)
        self.assertEqual(response.mimetype, "audio/x-ms-wma")
        self.assertTrue(response.headers["Content-Disposition"].endswith(".wma"))

    def test_year_five_and_six_workbook_only_for_exact_lesson(self):
        bridge = "web.native_telegram_extra_materials_20261106."
        for year, lesson in ((5, 29), (6, 13)):
            with self.subTest(year=year, lesson=lesson):
                row = next(r for r in source_records(year, "ENGLISH") if r["lesson"] == lesson)
                params = {"year": year, "subject": "ENGLISH", "unit": row["unit"], "lesson": row["token"]}
                with self.account(), patch(bridge + "english_workbook_metadata",
                        return_value="Buku Aktiviti muka surat disahkan") as metadata, patch(
                        bridge + "english_workbook_pdf", return_value=b"%PDF-1.7\n" + b"A" * 600) as pdf:
                    reply = self.client.get("/api/web/rph/extra-materials", query_string=params)
                    self.assertEqual(reply.status_code, 200)
                    self.assertEqual([r["type"] for r in reply.json["items"]], ["workbook"])
                    download = self.client.get(reply.json["items"][0]["url"])
                metadata.assert_called_once_with(year, lesson)
                pdf.assert_called_once_with(year, lesson)
                self.assertEqual(download.status_code, 200)
                self.assertIn(f"Y{year}_Lesson_{lesson:03d}", download.headers["Content-Disposition"])

    def test_browser_does_not_expose_unverified_or_unrelated_audio(self):
        html = (ROOT / "web_v1_static_preview" / "index.html").read_text("utf8")
        self.assertIn("ownStudentBook", html)
        self.assertIn("ownEnglishAudio", html)
        self.assertIn("externalMusic", html)
        self.assertNotIn("audio_storage_file_id", html)
        today = (ROOT / "web_v1_static_preview" / "rph-today.js").read_text("utf8")
        self.assertIn("/api/web/rph/english-student-book?", today)
        self.assertIn("english-audio", today)


if __name__ == "__main__":
    unittest.main()
