from io import BytesIO
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from staging.matematik_sjkc.tahun_3.rph import lessons
from web.native_rph_telegram_api import create_native_rph_blueprint


class MatematikSjkcRphPreviewTest(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(SimpleNamespace(
            create_word_file=lambda *_: self.fail("Used SK renderer"),
            create_pdf_file=lambda *_: self.fail("Used SK renderer"),
        )))
        self.client = app.test_client()
        self.token = "local-test-" + "x" * 32
        env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": self.token,
        })
        env.start()
        self.addCleanup(env.stop)
        self.path = "/internal/rph/v1/matematik-sjkc/preview"
        self.data = {"year": 3, "unit": 1, "pdp": 1, "format": "word"}

    def request(self, **changes):
        return self.client.post(self.path, json=self.data | changes,
                                headers={"Authorization": "Bearer " + self.token})

    def test_requires_internal_renderer_access(self):
        self.assertEqual(self.client.post(self.path, json=self.data).status_code, 401)
        with patch.dict(os.environ, {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "0"}):
            self.assertEqual(self.request().status_code, 503)

    def test_rejects_invalid_and_cross_unit_selections(self):
        for case in ({"year": "3"}, {"unit": True}, {"format": "docx"},
                     {"format": []}, {"pdp": 1.0}, {"teacher": "unexpected"}):
            with self.subTest(case=case):
                self.assertEqual(self.request(**case).status_code, 400)
        for case in ({"year": 2}, {"unit": 2}, {"pdp": 0}, {"pdp": 97}):
            with self.subTest(case=case):
                self.assertEqual(self.request(**case).status_code, 404)

    def test_missing_selected_document_returns_service_unavailable(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            from staging.matematik_sjkc.tahun_3 import rph
            (source / "year_3_2027.json").write_bytes((rph.ROOT / "year_3_2027.json").read_bytes())
            with patch.object(rph, "ROOT", source), self.assertLogs(level="ERROR"):
                response = self.request(format="pdf")
            self.assertEqual(response.status_code, 503)

    def test_word_and_pdf_use_the_same_matching_pdp(self):
        for pdp in (1, 17, 35, 47, 96):
            lesson = lessons()[pdp - 1]
            with self.subTest(pdp=pdp):
                word = self.request(unit=lesson["unit_number"], pdp=pdp)
                self.assertEqual(word.status_code, 200)
                self.assertIn("private", word.headers["Cache-Control"])
                self.assertIn(f"_PdP_{pdp:03}.docx", word.headers["Content-Disposition"])
                document = Document(BytesIO(word.data))
                self.assertEqual(len(document.tables), 1)
                self.assertEqual(document.paragraphs[2].text, lesson["topic"])
                self.assertIn(", ".join(lesson["sp"]), document.paragraphs[4].text)
                self.assertNotIn('w:type="page"', document.element.body.xml)

                pdf = self.request(unit=lesson["unit_number"], pdp=pdp, format="pdf")
                self.assertEqual(pdf.status_code, 200)
                self.assertIn(f"_PdP_{pdp:03}.pdf", pdf.headers["Content-Disposition"])
                pages = PdfReader(BytesIO(pdf.data)).pages
                self.assertEqual(len(pages), 1)
                text = pages[0].extract_text()
                self.assertIn(f"PdP {pdp:03}", text)
                self.assertIn("".join(lesson["topic"].split()), "".join(text.split()))
