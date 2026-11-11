"""Only exact Telegram Year 4 Student Book pages may be served to Web."""
import os
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from flask import Flask
from pypdf import PdfReader

from web.telegram_english_student_book_api_20261111 import (
    _material, _extract, _page_numbers, create_english_student_book_blueprint,
)

ROOT = Path(__file__).resolve().parents[1]

class StudentBookY4Tests(TestCase):
    def test_telegram_source_map_no_page_guessing(self):
        self.assertEqual(_page_numbers("12–13"), (12, 13))
        self.assertEqual(_page_numbers("73, 74–75"), (73, 74, 75))
        self.assertEqual(_page_numbers("27, 28, 29, 30, 31"), ())
        self.assertIsNone(_material(3, 30))
        self.assertIsNone(_material(4, 43))
        self.assertIsNone(_material(4, 999))
        self.assertIsNone(_material(4, 1))
        # Supplementary resource p133 must not leak into main L157 excerpt.
        self.assertEqual(_material(4, 157)["pages"], (110,))

    def test_pdf_excerpt_is_not_entire_book_and_matches_selected_pages(self):
        for lesson, pages in ((11, (12,13)), (30, (20,)), (157, (110,))):
            with self.subTest(lesson=lesson):
                source = _material(4, lesson)
                self.assertEqual(source["pages"], pages)
                result = _extract(source)
                self.assertTrue(result.startswith(b"%PDF-"))
                self.assertEqual(len(PdfReader(BytesIO(result)).pages),len(pages))
                self.assertLess(len(result),8*1024*1024)

    def test_authenticated_endpoint_fails_closed(self):
        app=Flask(__name__)
        app.register_blueprint(create_english_student_book_blueprint())
        client=app.test_client()
        path="/internal/rph/v1/english-extras/student-book"
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40}):
            self.assertEqual(client.get(path,query_string={"year":"4","lesson":"11"}).status_code,401)
            headers={"Authorization":"Bearer "+"z"*40}
            good=client.get(path,query_string={"year":"4","lesson":"11"},headers=headers)
            self.assertEqual(good.status_code,200)
            self.assertEqual(good.json["type"],"textbook")
            self.assertEqual(good.json["lesson"],11)
            pdf=client.get(path+".pdf",query_string={"year":"4","lesson":"11"},headers=headers)
            self.assertEqual(pdf.status_code,200)
            self.assertEqual(pdf.mimetype,"application/pdf")
            self.assertEqual(PdfReader(BytesIO(pdf.data)).get_num_pages(),2)
            self.assertEqual(pdf.headers["Cache-Control"],"private, no-store")
            bad=client.get(path,query_string={"year":"4","lesson":"43"},headers=headers)
            self.assertEqual(bad.status_code,404)
            extra=client.get(path,query_string={"year":"4","lesson":"11","extra":"x"},headers=headers)
            self.assertEqual(extra.status_code,404)

    def test_runtime_registration_exists(self):
        launcher=(ROOT/"tools"/"run_telegram_with_curriculum_api.py").read_text("utf8")
        self.assertIn("create_english_student_book_blueprint()", launcher)
