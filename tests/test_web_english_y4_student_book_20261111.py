"""Web and Telegram Year4 Student Book parity: strict source token, no quota debit."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, jsonify
from web.unified_rph_web import create_blueprint, source_records

ROOT=Path(__file__).resolve().parents[1]
PDF=b"%PDF-1.7\n"+b"A"*1050

class WebEnglishStudentBookY4Tests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client=self.app.test_client()
        self.row=next(x for x in source_records(4,"ENGLISH") if x["lesson"]==30)
        self.sel={"year":"4","subject":"ENGLISH","unit":self.row["unit"],"lesson":self.row["token"]}

    def _account(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id":1,"authenticated":True},None))

    def test_returns_two_independent_exact_lesson_resources(self):
        with self._account(),patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="Workbook Y4 Lesson 30 p14"),patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
                return_value="Student Book Y4 Lesson 30 p20"):
            response=self.client.get("/api/web/rph/extra-materials",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        entries=response.json["items"]
        self.assertEqual([item["type"] for item in entries],["workbook","textbook"])
        self.assertIn("lesson=e-4-030",entries[1]["url"])
        self.assertIn("/api/web/rph/english-student-book?",entries[1]["url"])
        self.assertEqual(entries[1]["action"],"Download")

    def test_missing_student_book_does_not_hide_workbook(self):
        with self._account(),patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value="Workbook verified"),patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
                side_effect=RuntimeError("Telegram source offline")):
            response=self.client.get("/api/web/rph/extra-materials",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual([x["type"] for x in response.json["items"]],["workbook"])

    def test_exact_pdf_download_and_security_headers(self):
        with self._account(),patch(
                "web.native_telegram_extra_materials_20261106.english_student_book_pdf",
                return_value=PDF):
            response=self.client.get("/api/web/rph/english-student-book",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,"application/pdf")
        self.assertEqual(response.data,PDF)
        self.assertIn("Y4_Lesson_030_Student_Book",response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"],"private, no-store")

    def test_wrong_unit_or_year_never_downloads(self):
        with self._account():
            wrong=self.client.get("/api/web/rph/english-student-book",query_string={
                **self.sel,"unit":"Wrong source unit"})
            self.assertEqual(wrong.status_code,400)
            year2=next(x for x in source_records(2,"ENGLISH") if x["lesson"]==2)
            other=self.client.get("/api/web/rph/english-student-book",query_string={
                "year":"2","subject":"ENGLISH","unit":year2["unit"],"lesson":year2["token"]})
            self.assertEqual(other.status_code,400)

    def test_login_required_and_no_fake_audio(self):
        with patch("web.unified_rph_web._account",
                   side_effect=lambda:(None,(jsonify({"error":"Login"}),401))):
            response=self.client.get("/api/web/rph/english-student-book",query_string=self.sel)
            self.assertEqual(response.status_code,401)
        html=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn('const ownStudentBook=item.type==="textbook"',html)
        self.assertIn('"/api/web/rph/english-student-book?"',html)
        self.assertIn("if(!ownWorkbook&&!ownStudentBook&&!externalMusic)continue;",html)
