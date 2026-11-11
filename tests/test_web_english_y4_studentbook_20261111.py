"""Web ↔ Telegram per-Lesson Student Book parity, without breaking Workbook."""
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask, jsonify

from web.unified_rph_web import create_blueprint, source_records
from web.native_telegram_rph_client import NativeRPHUnavailable
from web.native_telegram_extra_materials_20261106 import (
    english_studentbook_metadata, STUDENTBOOK_Y4_SOURCE,
)

ROOT = Path(__file__).resolve().parents[1]


class Year4WebStudentBookTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client = self.app.test_client()
        row = next(row for row in source_records(4, "ENGLISH") if row["lesson"] == 30)
        self.sel = {"year": "4", "subject": "ENGLISH",
                    "unit": row["unit"], "lesson": row["token"]}

    def _account(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id": 1, "authenticated": True}, None))

    def test_two_independent_downloadable_resources_for_same_lesson(self):
        with self._account(), patch(
                "web.native_telegram_extra_materials_20261106.english_studentbook_metadata",
                return_value="English Tahun 4 • Lesson 030 • Student Book m/s 20"), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="English Tahun 4 • Lesson 030 • Workbook m/s 15"):
            response = self.client.get("/api/web/rph/extra-materials",
                                       query_string=self.sel)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["type"] for r in response.json["items"]],
                         ["textbook", "workbook"])
        self.assertTrue(response.json["items"][0]["url"].startswith(
            "/api/web/rph/english-studentbook?"))
        self.assertIn("lesson=e-4-030", response.json["items"][0]["url"])
        self.assertEqual(response.json["items"][0]["action"], "Download")

    def test_studentbook_unavailable_does_not_hide_workbook(self):
        with self._account(), patch(
                "web.native_telegram_extra_materials_20261106.english_studentbook_metadata",
                side_effect=NativeRPHUnavailable("Missing Telegram route")), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="Workbook verified source"):
            response = self.client.get("/api/web/rph/extra-materials",
                                       query_string=self.sel)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["type"] for r in response.json["items"]], ["workbook"])

    def test_standalone_pdf_is_lesson_bound_and_private(self):
        payload = b"%PDF-1.7\n" + b"X" * 1000
        with self._account(), patch(
                "web.native_telegram_extra_materials_20261106.english_studentbook_pdf",
                return_value=payload) as fetch:
            response = self.client.get("/api/web/rph/english-studentbook",
                                       query_string=self.sel)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("Lesson_030_StudentBook", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        fetch.assert_called_once_with(4, 30)

    def test_wrong_unit_and_year_must_not_download_studentbook(self):
        with self._account():
            wrong = self.client.get("/api/web/rph/english-studentbook",
                                    query_string={**self.sel, "unit": "Wrong unit"})
            self.assertEqual(wrong.status_code, 400)
            wrong_year = self.client.get("/api/web/rph/english-studentbook",
                                         query_string={**self.sel, "year": "3"})
            self.assertEqual(wrong_year.status_code, 400)

    def test_login_required_for_metadata_and_download(self):
        with patch("web.unified_rph_web._account",
                   side_effect=lambda: (None, (jsonify({"error": "Login"}), 401))):
            for path in ("/api/web/rph/extra-materials",
                         "/api/web/rph/english-studentbook"):
                self.assertEqual(self.client.get(
                    path, query_string=self.sel).status_code, 401)

    def test_service_metadata_cannot_change_lesson_or_source(self):
        good = {"source": STUDENTBOOK_Y4_SOURCE, "available": True,
                "year": 4, "lesson": 30, "type": "textbook",
                "format": "pdf", "status": "VERIFIED_SOURCE",
                "title": "English Tahun 4 • Lesson 030 • Student Book m/s 20"}
        with patch("web.native_telegram_extra_materials_20261106._json",
                   return_value=good):
            self.assertIn("Lesson 030", english_studentbook_metadata(4, 30))
        with patch("web.native_telegram_extra_materials_20261106._json",
                   return_value={**good, "lesson": 31}):
            with self.assertRaises(NativeRPHUnavailable):
                english_studentbook_metadata(4, 30)
        with self.assertRaises(ValueError):
            english_studentbook_metadata(3, 30)

    def test_browser_supports_student_book_without_external_drive_link(self):
        html = (ROOT / "web_v1_static_preview" / "index.html").read_text("utf8")
        self.assertIn('const ownStudentBook=item.type==="textbook"', html)
        self.assertIn('/api/web/rph/english-studentbook?', html)
        self.assertIn("!ownWorkbook&&!ownStudentBook&&!externalMusic", html)


if __name__ == "__main__":
    unittest.main()
