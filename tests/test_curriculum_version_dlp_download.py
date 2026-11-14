"""Check the private Telegram DLP file endpoint and published lesson binding."""

from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask

from dlp_year2_rph import catalog, resolve
from web.native_rph_telegram_api import create_native_rph_blueprint


class DlpDownloadTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda: None, create_pdf_file=lambda: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        self.client = app.test_client()
        self.path = "/internal/rph/v1/dlp"
        self.selection = {"year": 2, "subject": "SCIENCE_DLP", "unit": "10",
                          "lesson": "DLP-SCI-Y2-U10-06"}
        self.teacher = {"class": "2 Bestari", "date": "2026-11-16", "time": "10:00 - 11:00",
                        "students": "30", "reflection": "Teacher’s note: <check> & review."}
        token = "t" * 40
        self.headers = {"Authorization": f"Bearer {token}"}
        env = patch.dict("os.environ", {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
        })
        env.start()
        self.addCleanup(env.stop)

    def download(self, fmt, selection=None, teacher=None):
        return self.client.post(self.path + "/render", headers=self.headers, json={
            "format": fmt, "selection": selection or self.selection, "teacher": teacher or self.teacher,
        })

    def test_readiness_has_no_teaching_content_and_resolves_exact_key(self):
        for subject, units in catalog().items():
            for unit in units:
                for lesson in unit["lessons"]:
                    self.assertEqual(resolve(2, subject, unit["id"], lesson["id"]), (unit, lesson))
        route = self.path + "/availability"
        self.assertEqual(self.client.get(route, query_string=self.selection).status_code, 401)
        available = self.client.get(route, query_string=self.selection, headers=self.headers)
        self.assertEqual(available.json, {"available": True, "formats": ["word", "pdf"]})
        for field, value in (("year", 3), ("subject", "MATH_DLP"), ("unit", "09"),
                             ("lesson", "DLP-SCI-Y2-U10-99")):
            selection = self.selection | {field: value}
            self.assertEqual(self.client.get(route, query_string=selection, headers=self.headers).status_code, 404)
            self.assertEqual(self.download("pdf", selection=selection).status_code, 404)

    def test_download_attaches_real_files_and_prints_teacher_details(self):
        word = self.download("word")
        self.assertEqual(word.status_code, 200)
        self.assertIn('attachment; filename="CIKGULAJU_RPH_DLP-SCI-Y2-U10-06.docx"',
                      word.headers["Content-Disposition"])
        doc = Document(BytesIO(word.data))
        self.assertEqual(doc.paragraphs[2].text, "Explain Observations About a Built Model")
        self.assertIn("2 Bestari", doc.tables[0].cell(2, 1).text)
        self.assertIn("LS 10.1.6", doc.tables[0].cell(3, 1).text)
        self.assertEqual(doc.tables[-1].cell(0, 1).text, self.teacher["reflection"])
        self.assertEqual(len(doc.tables[1].rows), 5)
        pdf = self.download("pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        self.assertEqual(pdf.headers["Cache-Control"], "no-store, private")
        self.assertEqual(self.download("pdf", teacher=self.teacher | {"class": "X" * 41}).status_code, 400)
        self.assertEqual(self.download("pdf", teacher=self.teacher | {"reflection": "x\ny\nz\n1\n2\n3\n4"}).status_code, 400)
        self.assertEqual(self.client.post(self.path + "/render", json={}).status_code, 401)
