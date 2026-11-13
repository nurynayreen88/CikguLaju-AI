"""Web materials: exact source-bound Lesson, no RPT numeric guess or quota debit."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, jsonify

from web.unified_rph_web import create_blueprint, source_records

ROOT=Path(__file__).resolve().parents[1]


class ExtraMaterialsWebTests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client=self.app.test_client()
        self.e2=next(x for x in source_records(2,"ENGLISH") if x["lesson"]==2)
        self.sel={"year":"2","subject":"ENGLISH",
                  "unit":self.e2["unit"],"lesson":self.e2["token"]}

    def _account(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id":1,"authenticated":True},None))

    def test_workbook_is_bound_to_source_token_not_rpt_row(self):
        with self._account(),patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
             return_value="English Tahun 2 • Lesson 002 • Buku Aktiviti m/s 58"), patch(
             "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
             return_value=None), patch(
             "web.native_telegram_extra_materials_20261106.english_audio_tracks",
             return_value=[]):
            response=self.client.get("/api/web/rph/extra-materials",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json["items"]),1)
        row=response.json["items"][0]
        self.assertEqual(row["type"],"workbook")
        self.assertIn("lesson=e-2-002",row["url"])
        self.assertIn("unit=",row["url"])
        self.assertEqual(row["action"],"Download")

    def test_wrong_unit_does_not_expose_book_page(self):
        with self._account():
            response=self.client.get("/api/web/rph/extra-materials",
                         query_string={**self.sel,"unit":"Unit lain"})
            self.assertEqual(response.json["items"],[])
            pdf=self.client.get("/api/web/rph/english-workbook",
                                query_string={**self.sel,"unit":"Unit lain"})
            self.assertEqual(pdf.status_code,400)

    def test_pdf_returns_download_with_original_lesson_identity(self):
        with self._account(),patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_pdf",
             return_value=b"%PDF-1.7\n"+"B".encode()*1050):
            response=self.client.get("/api/web/rph/english-workbook",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,"application/pdf")
        self.assertIn("Lesson_002",response.headers.get("Content-Disposition",""))
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_music_original_link_not_mislabeled_as_download(self):
        params={"year":"3","subject":"MUZIK","unit":"u01","lesson":"001"}
        external="https://drive.google.com/file/d/1l8GZxYtttttttttttttttttttttttttt/view?usp=drivesdk"
        mocked=[{"type":"audio","title":"Audio 5 — lagu sumber","url":external,
                 "action":"Buka Audio Sumber","source_only":True}]
        with self._account(),patch(
             "web.native_telegram_extra_materials_20261106.music_source_links",
             return_value=mocked):
            response=self.client.get("/api/web/rph/extra-materials",query_string=params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json["items"],mocked)
        self.assertIn("hak edar",response.json["note"])

    def test_materials_require_login(self):
        with patch("web.unified_rph_web._account",
                   side_effect=lambda:(None,(jsonify({"error":"Login"}),401))):
            response=self.client.get("/api/web/rph/extra-materials",query_string=self.sel)
            self.assertEqual(response.status_code,401)
            pdf=self.client.get("/api/web/rph/english-workbook",query_string=self.sel)
            self.assertEqual(pdf.status_code,401)

    def test_browser_uses_lesson_token_not_rpt_id(self):
        static=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn("/api/web/rph/extra-materials?",static)
        self.assertIn("Buka Audio Sumber",static)
        self.assertNotIn('"/api/materials?"',static)


if __name__=="__main__":
    unittest.main()
