"""Two-branch staging contract: actual Telegram PDF bytes through authenticated Web routes.

The companion Telegram PR is checked out separately by GitHub Actions.
This never calls a production service, touches Supabase or consumes credits.
"""
import ast
from io import BytesIO
import importlib.util
import os
from pathlib import Path
import re
import sys
import types
import unittest
from unittest.mock import patch

from flask import Flask, jsonify, request
from pypdf import PdfReader

from web.unified_rph_web import create_blueprint, source_records
from web.native_telegram_rph_client import NativeRPHUnavailable

ROOT = Path(__file__).resolve().parents[1]
PARTNER = (ROOT / os.environ.get("CIKGULAJU_PR558_DIR", ".partner-telegram")).resolve()
SECRET = "local-staging-contract-secret-not-production"


def _source_constant(text, name):
    match = re.search(r"(?ms)^" + re.escape(name) + r"\s*=\s*(\{.*?^\})", text)
    if match is None:
        raise AssertionError(f"Partner app.py missing verified {name}")
    return ast.literal_eval(match.group(1))


def _partner_bridge():
    path = PARTNER / "web" / "telegram_english_workbook_api_20261106.py"
    if not path.is_file():
        raise AssertionError("Telegram PR source checkout is required")
    # Standalone auth adapter for an offline WSGI contract. Telegram's real
    # _authorization is independently covered by its own production tests.
    stub = types.ModuleType("web.telegram_verified_rpt_rph_bridge")
    stub._authorization = lambda: request.headers.get("Authorization") == "Bearer " + SECRET
    spec = importlib.util.spec_from_file_location("partner_telegram_english_y4", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"web.telegram_verified_rpt_rph_bridge": stub}):
        spec.loader.exec_module(module)
    return module


class _VerifiedTelegramRuntime:
    def __init__(self):
        source = (PARTNER / "app.py").read_text(encoding="utf-8")
        pages = _source_constant(source, "_Y4_SB_PAGES_V25230")
        main = _source_constant(source, "_EN34_MAIN_SB_V25231")
        self.mapped = pages
        self.main = main
        self._EN_LOCAL_BOOK_CHUNKS_V25234 = {
            (4, "textbook"): [
                (1, 20, "books/english/y4_student_001_020.pdf"),
                (21, 100, "books/english/y4_student_021_100.pdf"),
                (101, 177, "books/english/y4_student_101_177.pdf"),
            ]
        }

    def _en97_units(self, year):
        if year != "Tahun 4":
            return [], []
        rows = [{"lesson_no": n, "unit_name": f"Source Lesson {n}"}
                for n in (30, 43, 103, 157)]
        return rows, ["Source"]

    def _en34_verified_sb_pages_v25230(self, row, year):
        lesson = int(row["lesson_no"])
        return self.main.get((year, lesson), self.mapped.get(lesson, ""))

    @staticmethod
    def _book_physical_page_v25237(state, kind, page):
        if state.get("year") != "Tahun 4" or kind != "textbook":
            return 0
        return page


class WebTelegramYear4PartnerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.partner = _partner_bridge()
        cls.runtime = _VerifiedTelegramRuntime()
        cls.telegram = Flask("telegram_pr558_contract")
        cls.telegram.register_blueprint(cls.partner.create_english_workbook_blueprint(cls.runtime))
        cls.telegram_client = cls.telegram.test_client()
        cls.web = Flask("web_pr559_contract")
        cls.web.register_blueprint(create_blueprint())
        cls.web_client = cls.web.test_client()
        cls.rows = {r["lesson"]: r for r in source_records(4, "ENGLISH")}

    def _select(self, n):
        self.assertIn(n, self.rows, f"Web source catalog has no Lesson {n}")
        row = self.rows[n]
        return {"year": "4", "subject": "ENGLISH",
                "unit": row["unit"], "lesson": row["token"]}

    def _dispatch(self, path, args, *, accept="application/json",
                  limit=130000, opener=None):
        response = self.telegram_client.get(path, query_string=args,
                                            headers={"Authorization": "Bearer " + SECRET})
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise NativeRPHUnavailable("Partner Telegram bridge failed")
        if response.mimetype != accept or len(response.data) > limit:
            raise NativeRPHUnavailable("Partner Telegram content contract mismatch")
        return response.data

    def test_lesson103_sow_page73_only_reaches_web(self):
        # Legacy p73,74-75 conflated L103 speaking with L104 reading.
        # Source SOW Lesson 103 Activity 5 is Student Book p.73 only.
        self.assertIn(self.runtime.mapped[103], ("73, 74–75", "73"))
        query = self._select(103)
        with patch("web.unified_rph_web._account",
                   return_value=({"authenticated": True, "telegram_user_id": 123}, None)), \
             patch("web.native_telegram_extra_materials_20261106._get",
                   side_effect=self._dispatch):
            listed = self.web_client.get("/api/web/rph/extra-materials", query_string=query)
            self.assertEqual(listed.status_code, 200)
            items = [x for x in listed.json["items"] if x["type"] == "student_book"]
            self.assertEqual(len(items), 1)
            self.assertIn("m/s 73", items[0]["title"])
            downloaded = self.web_client.get("/api/web/rph/english-student-book",
                                             query_string=query)

        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.mimetype, "application/pdf")
        self.assertEqual(downloaded.headers["Cache-Control"], "no-store, private")
        self.assertIn("Lesson_103", downloaded.headers["Content-Disposition"])
        actual = PdfReader(BytesIO(downloaded.data), strict=True)
        self.assertEqual(len(actual.pages), 1)
        original = PdfReader(str(PARTNER / "books/english/y4_student_021_100.pdf"),
                             strict=True)
        self.assertEqual(actual.pages[0].get_contents().get_data(),
                         original.pages[52].get_contents().get_data())

    def test_web_displays_and_downloads_both_real_workbook_and_student_book(self):
        """One verified Lesson exposes two independently authenticated PDFs."""
        self.assertEqual(self.runtime.mapped[30], "20")
        query = self._select(30)
        with patch("web.unified_rph_web._account",
                   return_value=({"authenticated": True, "telegram_user_id": 123}, None)), \
             patch("web.native_telegram_extra_materials_20261106._get",
                   side_effect=self._dispatch):
            response = self.web_client.get("/api/web/rph/extra-materials",
                                           query_string=query)
            self.assertEqual(response.status_code, 200)
            material_types = [item["type"] for item in response.json["items"]]
            self.assertIn("workbook", material_types)
            self.assertIn("student_book", material_types)
            book = self.web_client.get("/api/web/rph/english-student-book",
                                       query_string=query)
            workbook = self.web_client.get("/api/web/rph/english-workbook",
                                           query_string=query)
        self.assertEqual(book.status_code, 200)
        self.assertEqual(workbook.status_code, 200)
        self.assertTrue(PdfReader(BytesIO(book.data)).pages)
        self.assertTrue(PdfReader(BytesIO(workbook.data)).pages)
        self.assertNotEqual(book.data, workbook.data)
        self.assertEqual(book.headers["Cache-Control"], "no-store, private")
        self.assertEqual(workbook.headers["Cache-Control"], "no-store, private")

    def test_one_telegram_material_failure_does_not_hide_the_other(self):
        query = self._select(30)
        account = {"authenticated": True, "telegram_user_id": 123}

        def no_workbook(path, args, **kwargs):
            if "/workbook" in path:
                raise NativeRPHUnavailable("Workbook service temporarily unavailable")
            return self._dispatch(path, args, **kwargs)

        def no_student_book(path, args, **kwargs):
            if "/student-book" in path:
                raise NativeRPHUnavailable("Student Book service temporarily unavailable")
            return self._dispatch(path, args, **kwargs)

        for transport, expected in (
            (no_workbook, "student_book"),
            (no_student_book, "workbook"),
        ):
            with self.subTest(expected=expected), \
                 patch("web.unified_rph_web._account",
                       return_value=(account, None)), \
                 patch("web.native_telegram_extra_materials_20261106._get",
                       side_effect=transport):
                response = self.web_client.get("/api/web/rph/extra-materials",
                                               query_string=query)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([item["type"] for item in response.json["items"]],
                                 [expected])
                path = ("/api/web/rph/english-student-book" if
                        expected == "student_book" else "/api/web/rph/english-workbook")
                self.assertEqual(self.web_client.get(path, query_string=query).status_code,
                                 200)

    def test_lesson157_main_pages_and_lesson43_phonics3_page121(self):
        self.assertIn(self.runtime.main[(4, 157)], ("110", "110–111"))
        # Legacy L043 p27-31 is wrong; SOW Lesson 43 specifies Phonics 3 p121.
        self.assertIn(self.runtime.mapped[43], ("27, 28, 29, 30, 31", "121"))
        for lesson, length in ((157, 2), (43, 1)):
            query = self._select(lesson)
            with patch("web.unified_rph_web._account",
                       return_value=({"authenticated": True, "telegram_user_id": 123}, None)), \
                 patch("web.native_telegram_extra_materials_20261106._get",
                       side_effect=self._dispatch):
                listed = self.web_client.get("/api/web/rph/extra-materials",
                                             query_string=query)
                self.assertEqual(listed.status_code, 200)
                found = [x for x in listed.json["items"] if x["type"] == "student_book"]
                self.assertEqual(len(found), 1)
                pdf = self.web_client.get("/api/web/rph/english-student-book",
                                          query_string=query)
            self.assertEqual(pdf.status_code, 200)
            actual = PdfReader(BytesIO(pdf.data), strict=True)
            self.assertEqual(len(actual.pages), length)
            if lesson == 157:
                self.assertIn("m/s 110–111", found[0]["title"])
                source = PdfReader(str(PARTNER / "books/english/y4_student_101_177.pdf"),
                                   strict=True)
                for page, offset in zip(actual.pages, (9, 10)):
                    self.assertEqual(page.get_contents().get_data(),
                                     source.pages[offset].get_contents().get_data())
            if lesson == 43:
                self.assertIn("m/s 121", found[0]["title"])
                source = PdfReader(str(PARTNER / "books/english/y4_student_101_177.pdf"),
                                   strict=True)
                self.assertEqual(actual.pages[0].get_contents().get_data(),
                                 source.pages[20].get_contents().get_data())

    def test_no_login_wrong_unit_and_missing_telegram_bearer(self):
        query = self._select(103)
        with patch("web.unified_rph_web._account",
                   side_effect=lambda: (None, (jsonify({"error": "Login"}), 401))):
            result = self.web_client.get("/api/web/rph/english-student-book",
                                         query_string=query)
            self.assertEqual(result.status_code, 401)

        wrong = dict(query, unit="Wrong Unit")
        with patch("web.unified_rph_web._account",
                   return_value=({"authenticated": True, "telegram_user_id": 123}, None)):
            result = self.web_client.get("/api/web/rph/english-student-book",
                                         query_string=wrong)
            self.assertEqual(result.status_code, 400)

        denied = self.telegram_client.get(
            "/internal/rph/v1/english-extras/student-book.pdf",
            query_string={"year": 4, "lesson": 103})
        self.assertEqual(denied.status_code, 401)


if __name__ == "__main__":
    unittest.main()
