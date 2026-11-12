"""Four exact English Y4 supplementary worksheets: true PDF, authenticated,
source-bound and no Telegram/Supabase credit mutation.
"""
import io
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from flask import Flask, jsonify
from pypdf import PdfReader
from docx import Document

from web.unified_rph_web import create_blueprint, source_records
from web.english_y4_worksheet_pdf_20261112 import worksheet_metadata, worksheet_pdf, _student_lines
from web.english_y4_worksheet_word_20261112 import worksheet_docx

SOURCE = {x["lesson"]: x for x in source_records(4, "ENGLISH")}
LESSONS = (4, 79, 89, 90)


class WorksheetSourceTests(TestCase):
    def test_source_exact_four_only(self):
        self.assertEqual(len(SOURCE), 160)
        for n in LESSONS:
            self.assertIn(n, SOURCE)
            self.assertIn("Lesson %03d" % n, worksheet_metadata(4, n))
        for n in range(1, 161):
            if n not in LESSONS:
                self.assertIsNone(worksheet_metadata(4, n))
        for year, lesson in ((3, 4), (5, 90), (4, 0), (4, 161)):
            self.assertIsNone(worksheet_pdf(year, lesson))
        self.assertIsNone(worksheet_pdf("4", 4))
        self.assertIsNone(worksheet_pdf(4, "4"))

    def test_all_pdf_printable_single_page_and_no_teacher_answer_key(self):
        for n in LESSONS:
            with self.subTest(lesson=n):
                raw = worksheet_pdf(4, n)
                self.assertTrue(raw.startswith(b"%PDF-"))
                self.assertLess(len(raw), 300000)
                result = PdfReader(io.BytesIO(raw))
                self.assertEqual(len(result.pages), 1, "No overflow/truncated pupil exercises")
                text = result.pages[0].extract_text()
                self.assertIn("English Year 4", text)
                self.assertIn("Name:", text)
                self.assertIn("Lesson %03d" % n, text)
                self.assertIn("Not an official textbook page", text)
                self.assertNotIn("Teacher assessment:", text)
                self.assertNotIn("Answer key", text)
                self.assertNotIn("Purpose:", text)

    def test_editable_word_a4_preserves_pupil_tasks_only(self):
        for n in LESSONS:
            with self.subTest(lesson=n):
                blob = worksheet_docx(4, n)
                self.assertTrue(blob.startswith(bytes.fromhex("504b0304")))
                doc = Document(io.BytesIO(blob))
                self.assertEqual(int(round(doc.sections[0].page_width.mm)), 210)
                self.assertEqual(int(round(doc.sections[0].page_height.mm)), 297)
                text = "\n".join(p.text for p in doc.paragraphs)
                self.assertIn("Lesson %03d" % n, text)
                self.assertIn("Name:", text)
                self.assertNotIn("Teacher assessment:", text)
                self.assertNotIn("Answer key", text)
                self.assertNotIn("Purpose:", text)
        self.assertIsNone(worksheet_docx(3, 4))
        self.assertIsNone(worksheet_docx(4, 2))

    def test_multiline_teacher_sections_are_never_printed_for_pupils(self):
        # The source can gain a multi-line teacher footer later: never remove
        # only its label and accidentally print the answer paragraphs below.
        cases = (
            "**Teacher assessment:** Confidential rubric\nSECRET_RUBRIC",
            "## Teacher notes\nSECRET_TEACHER_NOTES",
            "### Answer key (A)\nSECRET_ANSWERS",
            "**Suggested answers:**\nSECRET_EXAMPLES",
        )
        for tail in cases:
            with self.subTest(footer=tail.splitlines()[0]):
                raw = ("# English Year 4 — Lesson 004 — Writing Sheet\n"
                       "**Purpose:** Confidential planning note\n"
                       "Name: __________________\n"
                       "## A. Complete the sentence\n"
                       "1. She is from Malaysia.\n" + tail +
                       "\nExtra confidential explanations.\n")
                visible = "\n".join(_student_lines(raw))
                self.assertIn("1. She is from Malaysia.", visible)
                self.assertNotIn("Confidential", visible)
                self.assertNotIn("SECRET_", visible)
                self.assertNotIn("Extra confidential", visible)

    def test_lesson_090_invitation_date_is_calendar_neutral(self):
        source = (Path(__file__).resolve().parents[1] /
                  "supplementary_materials/english/year4/lesson_090_worksheet.md"
                  ).read_text(encoding="utf-8")
        self.assertIn("Date: 20 November", source)
        self.assertIn("2 20 November at 2:00 p.m.", source)
        self.assertNotIn("Friday, 20 November", source)
        self.assertIn("Date: 20 November", PdfReader(
            io.BytesIO(worksheet_pdf(4, 90))).pages[0].extract_text())
        doc = Document(io.BytesIO(worksheet_docx(4, 90)))
        student_text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("Date: 20 November", student_text)
        self.assertNotIn("Friday, 20 November", student_text)

    def test_missing_file_fail_closed(self):
        import english_supplementary_materials as registry
        with patch.object(registry, "ROOT", Path("/missing/english_source")):
            self.assertIsNone(worksheet_metadata(4, 4))
            self.assertIsNone(worksheet_pdf(4, 4))


class WorksheetWebRoutesTests(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client = self.app.test_client()

    def sel(self, n, **extra):
        v = SOURCE[n]
        return {"year": "4", "subject": "ENGLISH", "unit": v["unit"],
                "lesson": v["token"], **extra}

    def _account(self):
        return patch("web.unified_rph_web._account",
                     return_value=({"telegram_user_id": 123, "authenticated": True,
                                    "free_remaining": 0}, None))

    def test_all_four_worksheets_show_and_download_with_zero_credits(self):
        for n in LESSONS:
            with self.subTest(lesson=n), self._account(), patch(
                    "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                    return_value=None), patch(
                    "web.rph_delivery_quota.authorize_rendered_document",
                    side_effect=AssertionError("Worksheet must not charge RPH credit")) as debit:
                listing = self.client.get("/api/web/rph/extra-materials", query_string=self.sel(n))
                self.assertEqual(listing.status_code, 200, listing.json)
                items = listing.json["items"]
                self.assertEqual(len(items), 2, items)
                self.assertEqual([x["type"] for x in items], ["worksheet", "worksheet_word"])
                self.assertIn("lesson=", items[0]["url"])
                self.assertIn("english-worksheet?", items[0]["url"])
                pdf = self.client.get(items[0]["url"])
                self.assertEqual(pdf.status_code, 200)
                self.assertEqual(pdf.mimetype, "application/pdf")
                self.assertEqual(pdf.headers["Cache-Control"], "no-store, private")
                self.assertEqual(pdf.headers["X-Content-Type-Options"], "nosniff")
                self.assertIn("Worksheet.pdf", pdf.headers.get("Content-Disposition", ""))
                self.assertEqual(len(PdfReader(io.BytesIO(pdf.data)).pages), 1)
                self.assertIn("worksheet-word?", items[1]["url"])
                word = self.client.get(items[1]["url"])
                self.assertEqual(word.status_code, 200)
                self.assertEqual(
                    word.mimetype,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                self.assertEqual(word.headers["Cache-Control"], "no-store, private")
                self.assertIn("Worksheet.docx", word.headers.get("Content-Disposition", ""))
                self.assertIn("Lesson %03d" % n,
                              "\n".join(p.text for p in Document(io.BytesIO(word.data)).paragraphs))
                debit.assert_not_called()

    def test_workbook_unavailable_does_not_hide_local_worksheet(self):
        with self._account(), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                side_effect=RuntimeError("backend offline")):
            response = self.client.get("/api/web/rph/extra-materials",
                                       query_string=self.sel(4))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["type"] for r in response.json["items"]],
                         ["worksheet", "worksheet_word"])

    def test_unmapped_lesson_no_fake_worksheet(self):
        with self._account(), patch(
                "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
                return_value=None):
            listing = self.client.get("/api/web/rph/extra-materials",
                                      query_string=self.sel(5))
            pdf = self.client.get("/api/web/rph/english-worksheet",
                                  query_string=self.sel(5))
            word = self.client.get("/api/web/rph/english-worksheet-word",
                                   query_string=self.sel(5))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json["items"], [])
        self.assertEqual(pdf.status_code, 404)
        self.assertEqual(word.status_code, 404)

    def test_wrong_unit_year_subject_and_extra_param_rejected(self):
        v = self.sel(4)
        invalid = [
            {**v, "unit": "Unit lain"},
            {**v, "subject": "MATH"},
            {**v, "year": "3"},
            {**v, "lesson": SOURCE[5]["token"]},
            {**v, "admin": "1"},
        ]
        with self._account():
            for params in invalid:
                with self.subTest(params=params):
                    status = self.client.get("/api/web/rph/english-worksheet",
                                             query_string=params).status_code
                    self.assertIn(status, (400, 404))
                    status_word = self.client.get("/api/web/rph/english-worksheet-word",
                                                  query_string=params).status_code
                    self.assertIn(status_word, (400, 404))

    def test_single_public_sample_but_all_other_files_remain_private(self):
        # An actual anonymized teacher-created Lesson 004 PDF is demonstrable
        # before login. No generic source selection or premium PDF bypass.
        with patch("web.unified_rph_web._account",
                   side_effect=AssertionError("Demo must not read user accounts")):
            sample = self.client.get("/api/web/demo/worksheet.pdf")
            self.assertEqual(sample.status_code, 200)
            self.assertEqual(sample.headers["X-CikguLaju-Public-Demo"], "1")
            self.assertEqual(sample.mimetype, "application/pdf")
            self.assertEqual(len(PdfReader(io.BytesIO(sample.data)).pages), 1)
            self.assertIn("Lesson 004",
                          PdfReader(io.BytesIO(sample.data)).pages[0].extract_text())
            attempt = self.client.get("/api/web/demo/worksheet.pdf",
                                      query_string={"lesson": "90"})
            self.assertEqual(attempt.status_code, 400)
        with patch("web.unified_rph_web._account",
                   side_effect=lambda: (None, (jsonify({"error":"Login"}), 401))):
            private = self.client.get("/api/web/rph/english-worksheet",
                                      query_string=self.sel(90))
        self.assertEqual(private.status_code, 401)

    def test_unauthenticated_not_listed_or_downloadable(self):
        with patch("web.unified_rph_web._account",
                   side_effect=lambda: (None, (jsonify({"error": "Login"}), 401))):
            for url in ("/api/web/rph/extra-materials",
                        "/api/web/rph/english-worksheet",
                        "/api/web/rph/english-worksheet-word"):
                with self.subTest(url=url):
                    result = self.client.get(url, query_string=self.sel(4))
                    self.assertEqual(result.status_code, 401)


if __name__ == "__main__":
    import unittest
    unittest.main()
