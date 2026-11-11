"""Fail-closed tests for Telegram's Year4 Student Book page-only export."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import os

from flask import Flask
from pypdf import PdfWriter, PdfReader

from web.telegram_english_studentbook_api_20261111 import (
    _material, _extract, _printed_pages, create_english_studentbook_blueprint,
)


class Year4StudentBookExcerpt(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "books" / "english").mkdir(parents=True)
        for start, end, name in ((1, 20, "y4_student_book_001_020.pdf"),
                                 (21, 45, "y4_student_book_021_045.pdf")):
            writer = PdfWriter()
            for _ in range(start, end + 1):
                writer.add_blank_page(width=300, height=400)
            with (root / "books" / "english" / name).open("wb") as fd:
                writer.write(fd)
        self.root = root
        self.runtime = SimpleNamespace(
            _Y4_SB_PAGES_V25230={30: "20", 103: "20, 21–22",
                                  157: "110–133", 88: "20, 20"},
            _EN_LOCAL_BOOK_CHUNKS_V25234={(4, "textbook"): [
                (1, 20, "books/english/y4_student_book_001_020.pdf"),
                (21, 45, "books/english/y4_student_book_021_045.pdf")]},
            _book_physical_page_v25237=lambda ss, key, p: p,
        )

    def test_selected_printed_pages_are_returned_not_whole_book(self):
        for lesson, expected_count in ((30, 1), (103, 3)):
            with self.subTest(lesson=lesson):
                material = _material(4, lesson, self.runtime, root=self.root)
                self.assertIsNotNone(material)
                data = _extract(material)
                self.assertEqual(len(PdfReader(BytesIO(data)).pages), expected_count)
                self.assertLess(len(data), 8 * 1024 * 1024)
        self.assertIn("Lesson 030", _material(4, 30, self.runtime, root=self.root)["title"])

    def test_unknown_or_long_or_duplicate_page_selection_is_not_delivered(self):
        self.assertIsNone(_material(4, 157, self.runtime, root=self.root))
        self.assertIsNone(_material(4, 88, self.runtime, root=self.root))
        self.assertIsNone(_material(4, 89, self.runtime, root=self.root))
        self.assertIsNone(_material(3, 30, self.runtime, root=self.root))
        self.assertIsNone(_material(5, 30, self.runtime, root=self.root))
        self.assertIsNone(_printed_pages("Student Book 20"))
        self.assertIsNone(_printed_pages("20–999"))

    def test_malformed_chunk_cannot_escape_private_book_directory(self):
        self.runtime._EN_LOCAL_BOOK_CHUNKS_V25234[(4, "textbook")][0] = (
            1, 20, "books/english/../../secret.pdf")
        self.assertIsNone(_material(4, 30, self.runtime, root=self.root))

    def test_private_api_requires_token_and_exact_selection(self):
        app = Flask(__name__)
        app.register_blueprint(create_english_studentbook_blueprint(
            self.runtime, root=self.root))
        client = app.test_client()
        token = "z" * 40
        headers = {"Authorization": "Bearer " + token}
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
        }):
            unauthenticated = client.get(
                "/internal/rph/v1/english-extras/studentbook",
                query_string={"year": "4", "lesson": "30"})
            self.assertEqual(unauthenticated.status_code, 401)
            approved = client.get(
                "/internal/rph/v1/english-extras/studentbook",
                query_string={"year": "4", "lesson": "30"}, headers=headers)
            self.assertEqual(approved.status_code, 200)
            self.assertEqual(approved.json["source"],
                             "telegram-verified-english-studentbook-y4-v1")
            pdf = client.get(
                "/internal/rph/v1/english-extras/studentbook.pdf",
                query_string={"year": "4", "lesson": "30"}, headers=headers)
            self.assertEqual(pdf.status_code, 200)
            self.assertEqual(len(PdfReader(BytesIO(pdf.data)).pages), 1)
            self.assertIn("attachment", pdf.headers["Content-Disposition"])
            self.assertEqual(pdf.headers["Cache-Control"], "private, no-store")
            for params in ({"year": "3", "lesson": "30"},
                           {"year": "4", "lesson": "157"},
                           {"year": "4", "lesson": "30", "extra": "x"},
                           {"year": "4", "lesson": "30", "lesson2": "99"}):
                self.assertEqual(client.get(
                    "/internal/rph/v1/english-extras/studentbook",
                    query_string=params, headers=headers).status_code, 404)
