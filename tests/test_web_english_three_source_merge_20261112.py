"""Offline staging QA: Workbook + Student Book + source-registered Worksheet coexist.

These checks never call the live Telegram bridge, use Supabase, or debit RPH.
"""
import io
import unittest
from unittest.mock import patch

from flask import Flask, jsonify
from pypdf import PdfReader, PdfWriter
from web.unified_rph_web import create_blueprint, source_records

ROW = next(x for x in source_records(4, "ENGLISH") if x["lesson"] == 4)
SELECT = {"year": "4", "subject": "ENGLISH",
          "unit": ROW["unit"], "lesson": ROW["token"]}


class ThreeSourceContractTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client = self.app.test_client()

    def auth(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id": 123,
                                    "authenticated": True,
                                    "free_remaining": 0}, None))

    @staticmethod
    def pdf():
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_metadata({"/Title": "Verified sample " + "x" * 700})
        buffer = io.BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    def test_workbook_book_and_two_worksheet_formats_are_independent(self):
        with self.auth(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            return_value="English Tahun 4 Lesson 004 Workbook"), patch(
            "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
            return_value="English Tahun 4 Lesson 004 Student Book"), patch(
            "web.native_telegram_extra_materials_20261106.english_student_book_pdf",
            return_value=self.pdf()), patch(
            "web.rph_delivery_quota.authorize_rendered_document",
            side_effect=AssertionError("Book/worksheet must not debit RPH")) as debit:
            result = self.client.get("/api/web/rph/extra-materials", query_string=SELECT)
            self.assertEqual(result.status_code, 200, result.json)
            self.assertEqual([v["type"] for v in result.json["items"]],
                             ["workbook", "student_book", "worksheet", "worksheet_word"])
            self.assertIn("Student Book", result.json["note"])
            self.assertIn("tidak menggunakan kuota", result.json["note"])
            for item in result.json["items"]:
                self.assertIn("lesson=" + ROW["token"], item["url"])
                self.assertIn("unit=", item["url"])
            book = self.client.get(result.json["items"][1]["url"])
            self.assertEqual(book.status_code, 200)
            self.assertEqual(book.headers["Cache-Control"], "no-store, private")
            self.assertEqual(len(PdfReader(io.BytesIO(book.data)).pages), 1)
            self.assertIn("Lesson_004_Student_Book.pdf",
                          book.headers["Content-Disposition"])
            worksheet_pdf = self.client.get(result.json["items"][2]["url"])
            worksheet_docx = self.client.get(result.json["items"][3]["url"])
            self.assertEqual(worksheet_pdf.status_code, 200)
            self.assertEqual(worksheet_docx.status_code, 200)
            debit.assert_not_called()

    def test_book_failure_does_not_hide_workbook_or_worksheet(self):
        with self.auth(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            return_value="English Tahun 4 Lesson 004 Workbook"), patch(
            "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
            side_effect=RuntimeError("Missing Telegram source")):
            res = self.client.get("/api/web/rph/extra-materials", query_string=SELECT)
        self.assertEqual([v["type"] for v in res.json["items"]],
                         ["workbook", "worksheet", "worksheet_word"])

    def test_workbook_failure_does_not_hide_book_or_worksheet(self):
        with self.auth(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            side_effect=RuntimeError("Workbook unavailable")), patch(
            "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
            return_value="English Tahun 4 Lesson 004 Student Book"):
            res = self.client.get("/api/web/rph/extra-materials", query_string=SELECT)
        self.assertEqual([v["type"] for v in res.json["items"]],
                         ["student_book", "worksheet", "worksheet_word"])

    def test_unauthenticated_and_duplicate_query_fields_rejected(self):
        url = "/api/web/rph/english-student-book"
        with patch("web.unified_rph_web._account",
                   side_effect=lambda: (None, (jsonify({"error": "Login"}), 401))):
            self.assertEqual(self.client.get(url, query_string=SELECT).status_code, 401)
        with self.auth():
            for key, other in (("year", "3"), ("subject", "BM"),
                               ("unit", "Other Unit"), ("lesson", "e-4-005")):
                query = list(SELECT.items()) + [(key, other)]
                for route in (url, "/api/web/rph/english-workbook",
                              "/api/web/rph/english-worksheet",
                              "/api/web/rph/english-worksheet-word"):
                    with self.subTest(key=key, route=route):
                        self.assertEqual(self.client.get(route, query_string=query).status_code, 400)
            self.assertEqual(self.client.get(url,
                             query_string={**SELECT, "unit": "Wrong Unit"}).status_code, 400)
            self.assertEqual(self.client.get(url,
                             query_string={**SELECT, "year": "3"}).status_code, 400)

    def test_student_book_rejects_pdf_junk_full_book_and_encrypted(self):
        from web.native_telegram_extra_materials_20261106 import english_student_book_pdf
        from web.native_telegram_rph_client import NativeRPHUnavailable
        valid = self.pdf()
        with patch("web.native_telegram_extra_materials_20261106._get",
                   return_value=valid):
            self.assertEqual(english_student_book_pdf(4, 4), valid)
        writer = PdfWriter()
        for _ in range(5):
            writer.add_blank_page(width=612, height=792)
        buff = io.BytesIO()
        writer.write(buff)
        with self.assertRaises(NativeRPHUnavailable), patch(
            "web.native_telegram_extra_materials_20261106._get",
            return_value=b"%PDF-1.7\n" + b"X" * 700):
            english_student_book_pdf(4, 4)
        with self.assertRaises(NativeRPHUnavailable), patch(
            "web.native_telegram_extra_materials_20261106._get",
            return_value=buff.getvalue()):
            english_student_book_pdf(4, 4)


if __name__ == "__main__":
    unittest.main()
