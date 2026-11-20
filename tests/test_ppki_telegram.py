"""Exact PPKI menu, API, RPH rendering and RPT entitlement."""
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from curriculum_version_telegram import install
from rpt_2027.english.telegram_downloads import install as install_rpt
from staging.ppki.catalog import SUBJECT, UNIT
from web.telegram_ppki_api import create_ppki_blueprint


class PpkiTelegramTest(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.documents = []
        self.allow = False
        self.state = {42: {"task": "rph", "subject": "Sains", "lesson_no": "999"}}
        self.namespace = {
            "state": self.state, "SUBJECTS_BY_GRADE": {}, "SUBJECT_LABEL": {},
            "callback": lambda *_: None, "subjects": lambda *_: None, "year": lambda *_: None,
            "send": lambda _, message, kb=None: self.messages.append((message, kb)),
            "send_document": self._send_file, "_credit_gate": lambda *_: self.allow,
            "_access_info": lambda _: {"active": self.allow}, "_is_admin": lambda _: False,
            "_telegram_delivery_ok_v25279": lambda result: result == {"ok": True},
        }
        self.assertTrue(install(self.namespace))
        self.assertTrue(install_rpt(self.namespace))

    def _send_file(self, _, path, caption):
        file = Path(path)
        self.documents.append((file.name, file.read_bytes(), caption))
        return {"ok": True}

    def test_choice_chain_and_document_gate(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year2", "cv_ppki_subject",
                    "cv_ppki_component", "cv_ppki_unit", "cv_ppki_lesson_014"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        self.assertNotIn("lesson_no", self.state[42])
        callback(42, "cv_ppki_pdf_013")
        self.assertFalse(self.documents)
        callback(42, "cv_ppki_lesson_014")
        callback(42, "cv_ppki_word_014")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_014")
        callback(42, "cv_ppki_pdf_014")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        pdf = PdfReader(BytesIO(self.documents[-1][1]))
        self.assertEqual(len(pdf.pages), 1)
        self.assertIn("2.3.4", pdf.pages[0].extract_text())

    def test_rpt_under_own_menu_and_paid_gate(self):
        callback = self.namespace["callback"]
        callback(42, "rpt2027_ppki_pdf2")
        self.assertIn("Akses Terhad", self.messages[-1][0])
        self.assertFalse(self.documents)
        self.allow = True
        for key in ("rpt2027_home", "rpt2027_ppki_home", "rpt2027_ppki_year2", "rpt2027_ppki_pdf2"):
            callback(42, key)
        rpt = PdfReader(BytesIO(self.documents[-1][1]))
        content = rpt.pages[0].extract_text()
        for number in range(1, 15):
            self.assertIn(f"{number:03d}", content)
        self.assertIn("Agihan PdP Unit 2", content)


class PpkiApiTest(unittest.TestCase):
    def test_all_14_word_pdf_and_protected_access(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        self.assertEqual(client.get(prefix + "/catalog").status_code, 401)
        self.assertEqual(client.get(prefix + "/rpt.pdf").status_code, 401)
        token = "P" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            options = client.get(prefix + "/catalog", headers=headers).get_json()
            self.assertEqual([row["value"] for row in options["lessons"]],
                             [f"{number:03d}" for number in range(1, 15)])
            teacher = {"class": "2 Bestari", "date": "2027-03-04", "time": "08:00 - 08:30",
                       "students": "7", "reflection": "Ulang dengan kad gambar."}
            selection = {"year": 2, "subject": SUBJECT, "unit": UNIT, "lesson": "001"}
            for row in options["lessons"]:
                selection["lesson"] = row["value"]
                for fmt in ("word", "pdf"):
                    response = client.post(prefix + "/render", headers=headers,
                                           json={"selection": selection, "teacher": teacher, "format": fmt})
                    self.assertEqual(response.status_code, 200, response.get_json(silent=True))
                    if fmt == "word":
                        doc = Document(BytesIO(response.data))
                        text = "\n".join(cell.text for table in doc.tables for cells in table.rows for cell in cells.cells)
                    else:
                        doc = PdfReader(BytesIO(response.data))
                        self.assertEqual(len(doc.pages), 1)
                        text = doc.pages[0].extract_text()
                    self.assertIn("2 Bestari", text)
                    self.assertIn("Ulang dengan kad gambar.", text)
            selection["lesson"] = "015"
            self.assertEqual(client.post(prefix + "/render", headers=headers,
                                         json={"selection": selection, "teacher": teacher, "format": "pdf"}).status_code, 404)
