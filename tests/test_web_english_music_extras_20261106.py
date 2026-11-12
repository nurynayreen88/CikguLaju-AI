"""Web materials: exact source-bound Lesson, no RPT numeric guess or quota debit."""
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from flask import Flask, jsonify
from pypdf import PdfWriter
from web.native_telegram_extra_materials_20261106 import english_student_book_pdf, english_workbook_pdf
from web.native_telegram_rph_client import NativeRPHUnavailable

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

    @staticmethod
    def _student_book_test_pdf(pages=2, *, encrypted=False):
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=612, height=792)
        if encrypted:
            writer.encrypt("test-only-password")
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    def test_workbook_is_bound_to_source_token_not_rpt_row(self):
        with self._account(),patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
             return_value="English Tahun 2 • Lesson 002 • Buku Aktiviti m/s 58"):
            response=self.client.get("/api/web/rph/extra-materials",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json["items"]),1)
        row=response.json["items"][0]
        self.assertEqual(row["type"],"workbook")
        self.assertIn("lesson=e-2-002",row["url"])
        self.assertIn("unit=",row["url"])
        self.assertEqual(row["action"],"Download")

    def test_material_status_and_description_reflect_actual_availability(self):
        # Do not claim that a source exists when neither book was verified.
        with self._account(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            return_value=None):
            absent = self.client.get("/api/web/rph/extra-materials",
                                     query_string=self.sel)
        self.assertEqual(absent.status_code, 200)
        self.assertEqual(absent.json["items"], [])
        self.assertEqual(absent.json["status"], "BELUM_TERSEDIA")
        self.assertIn("Tiada bahan tambahan", absent.json["note"])

        # A verified Workbook must have an accurate materials note and status.
        with self._account(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            return_value="English Tahun 2 Lesson 002 Workbook"):
            workbook = self.client.get("/api/web/rph/extra-materials",
                                       query_string=self.sel)
        self.assertEqual(workbook.json["status"], "SUMBER_ASAL")
        self.assertEqual([r["type"] for r in workbook.json["items"]],
                         ["workbook"])
        self.assertIn("Student Book dan Workbook", workbook.json["note"])
        self.assertIn("hak edaran", workbook.json["note"])
        self.assertIn("tidak menggunakan kuota", workbook.json["note"])

        # Do not mislabel a Student Book-only result as a Workbook.
        year4 = next(r for r in source_records(4, "ENGLISH")
                     if r["lesson"] == 30)
        params = {"year": "4", "subject": "ENGLISH",
                  "unit": year4["unit"], "lesson": year4["token"]}
        with self._account(), patch(
            "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
            return_value=None), patch(
            "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
            return_value="English Tahun 4 Lesson 030 Student Book"):
            student = self.client.get("/api/web/rph/extra-materials",
                                      query_string=params)
        self.assertEqual(student.json["status"], "SUMBER_ASAL")
        self.assertEqual([r["type"] for r in student.json["items"]],
                         ["student_book"])
        self.assertIn("Student Book", student.json["note"])

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
             return_value=self._student_book_test_pdf()):
            response=self.client.get("/api/web/rph/english-workbook",query_string=self.sel)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,"application/pdf")
        self.assertIn("Lesson_002",response.headers.get("Content-Disposition",""))
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_year4_student_book_download_is_bound_to_exact_lesson(self):
        e4 = next(row for row in source_records(4, "ENGLISH")
                  if row["lesson"] == 30)
        params = {"year":"4", "subject":"ENGLISH",
                  "unit":e4["unit"], "lesson":e4["token"]}
        with self._account(), patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
             return_value="English Tahun 4 Lesson 030 Workbook"), patch(
             "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
             return_value="English Tahun 4 Lesson 030 Student Book"):
            found = self.client.get("/api/web/rph/extra-materials", query_string=params)
        self.assertEqual(found.status_code, 200)
        self.assertEqual([r["type"] for r in found.json["items"]],
                         ["workbook", "student_book"])
        self.assertIn("lesson=e-4-030", found.json["items"][1]["url"])
        with self._account(), patch(
             "web.native_telegram_extra_materials_20261106.english_student_book_pdf",
             return_value=self._student_book_test_pdf()):
            pdf = self.client.get("/api/web/rph/english-student-book", query_string=params)
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertIn("Lesson_030", pdf.headers["Content-Disposition"])
        self.assertEqual(pdf.headers["Cache-Control"], "no-store, private")
        with self._account():
            bad = self.client.get("/api/web/rph/english-student-book",
                                  query_string={**params, "unit":"Wrong Unit"})
            self.assertEqual(bad.status_code, 400)
            wrong_year = self.client.get("/api/web/rph/english-student-book",
                                         query_string=self.sel)
            self.assertEqual(wrong_year.status_code, 400)

    def test_student_book_rejects_fake_oversized_page_count_and_encrypted_pdf(self):
        valid = self._student_book_test_pdf(pages=2)
        with patch("web.native_telegram_extra_materials_20261106._get",
                   return_value=valid):
            self.assertEqual(english_student_book_pdf(4, 30), valid)

        bad_sources = (
            b"%PDF-1.7\n" + b"J" * 800,
            self._student_book_test_pdf(pages=5),
            self._student_book_test_pdf(pages=1, encrypted=True),
        )
        for data in bad_sources:
            with self.subTest(size=len(data)), patch(
                    "web.native_telegram_extra_materials_20261106._get",
                    return_value=data):
                with self.assertRaises(NativeRPHUnavailable):
                    english_student_book_pdf(4, 30)

    def test_workbook_rejects_fake_oversized_page_count_and_encrypted_pdf(self):
        valid = self._student_book_test_pdf(pages=2)
        with patch("web.native_telegram_extra_materials_20261106._get",
                   return_value=valid):
            self.assertEqual(english_workbook_pdf(4, 30), valid)

        bad_sources = (
            b"%PDF-1.7\\n" + b"J" * 800,
            self._student_book_test_pdf(pages=5),
            self._student_book_test_pdf(pages=1, encrypted=True),
        )
        for data in bad_sources:
            with self.subTest(size=len(data)), patch(
                    "web.native_telegram_extra_materials_20261106._get",
                    return_value=data):
                with self.assertRaises(NativeRPHUnavailable):
                    english_workbook_pdf(4, 30)

    def test_duplicate_query_keys_never_select_wrong_english_book(self):
        e4 = next(row for row in source_records(4, "ENGLISH")
                  if row["lesson"] == 30)
        base = [("year", "4"), ("subject", "ENGLISH"),
                ("unit", e4["unit"]), ("lesson", e4["token"])]
        for field, another in (
            ("year", "3"),
            ("subject", "BM"),
            ("unit", "Wrong Unit"),
            ("lesson", "e-4-031"),
        ):
            with self.subTest(field=field), self._account():
                ambiguous = base + [(field, another)]
                listing = self.client.get("/api/web/rph/extra-materials",
                                          query_string=ambiguous)
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.json["items"], [])
                for endpoint in ("english-student-book", "english-workbook"):
                    response = self.client.get("/api/web/rph/" + endpoint,
                                               query_string=ambiguous)
                    self.assertEqual(response.status_code, 400)

    def test_student_book_absent_does_not_hide_verified_workbook(self):
        e4 = next(row for row in source_records(4, "ENGLISH")
                  if row["lesson"] == 30)
        params = {"year":"4", "subject":"ENGLISH",
                  "unit":e4["unit"], "lesson":e4["token"]}
        with self._account(), patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
             return_value="Verified Workbook"), patch(
             "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
             side_effect=RuntimeError("Source unavailable")):
            found = self.client.get("/api/web/rph/extra-materials", query_string=params)
        self.assertEqual(found.status_code, 200)
        self.assertEqual([row["type"] for row in found.json["items"]], ["workbook"])

    def test_student_book_remains_visible_if_workbook_bridge_fails(self):
        e4 = next(row for row in source_records(4, "ENGLISH")
                  if row["lesson"] == 30)
        params = {"year":"4", "subject":"ENGLISH",
                  "unit":e4["unit"], "lesson":e4["token"]}
        with self._account(), patch(
             "web.native_telegram_extra_materials_20261106.english_workbook_metadata",
             side_effect=RuntimeError("Workbook source unavailable")), patch(
             "web.native_telegram_extra_materials_20261106.english_student_book_metadata",
             return_value="Verified Year 4 Student Book"):
            response = self.client.get("/api/web/rph/extra-materials",
                                       query_string=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["type"] for row in response.json["items"]],
                         ["student_book"])

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
            y4 = next(row for row in source_records(4, "ENGLISH")
                      if row["lesson"] == 30)
            private_book = self.client.get(
                "/api/web/rph/english-student-book",
                query_string={"year":"4", "subject":"ENGLISH",
                              "unit":y4["unit"], "lesson":y4["token"]})
            self.assertEqual(private_book.status_code, 401)

    def test_browser_uses_lesson_token_not_rpt_id(self):
        static=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn("/api/web/rph/extra-materials?",static)
        self.assertIn('item.type==="student_book"',static)
        self.assertIn("/api/web/rph/english-student-book?",static)
        self.assertIn("Buka Audio Sumber",static)
        self.assertNotIn('"/api/materials?"',static)


if __name__=="__main__":
    unittest.main()
