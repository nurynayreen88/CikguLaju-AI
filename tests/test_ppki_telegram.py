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
from staging.ppki.catalog import MANIPULATIVE_UNIT1, MANIPULATIVE_UNIT_LESSONS, SUBJECT, UNIT, UNIT1, UNIT3, UNIT4, UNIT5
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
                    "cv_ppki_component", f"cv_ppki_unit_{UNIT1}", "cv_ppki_lesson_039"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        self.assertNotIn("lesson_no", self.state[42])
        callback(42, "cv_ppki_pdf_018")
        self.assertFalse(self.documents)
        callback(42, f"cv_ppki_unit_{UNIT1}")
        callback(42, "cv_ppki_lesson_039")
        callback(42, "cv_ppki_word_039")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_039")
        callback(42, "cv_ppki_pdf_039")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        pdf = PdfReader(BytesIO(self.documents[-1][1]))
        self.assertEqual(len(pdf.pages), 1)
        self.assertIn("1.3.3", pdf.pages[0].extract_text())

    def test_manipulative_component_has_its_own_units(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year2", "cv_ppki_subject",
                    "cv_ppki_component_km", f"cv_ppki_unit_{MANIPULATIVE_UNIT1}",
                    "cv_ppki_lesson_040"):
            buttons = [item["callback_data"] for row in self.messages[-1][1] for item in row]
            self.assertIn(key, buttons)
            callback(42, key)
        self.allow = True
        callback(42, "cv_ppki_pdf_040")
        name, body, _ = self.documents[-1]
        self.assertTrue(name.endswith("_040.pdf"))
        text = PdfReader(BytesIO(body)).pages[0].extract_text()
        self.assertIn("Kami Aktif", text)
        self.assertIn("1.2.1", text)
        callback(42, f"cv_ppki_unit_{UNIT1}")
        self.assertIn("Kemahiran Manipulatif", self.messages[-1][0])
        self.assertEqual(len(self.documents), 1)

    def test_rpt_under_own_menu_and_paid_gate(self):
        callback = self.namespace["callback"]
        callback(42, "rpt2027_ppki_pdf2")
        self.assertIn("Akses Terhad", self.messages[-1][0])
        self.assertFalse(self.documents)
        self.allow = True
        for key in ("rpt2027_home", "rpt2027_ppki_home", "rpt2027_ppki_year2", "rpt2027_ppki_pdf2"):
            callback(42, key)
        rpt = PdfReader(BytesIO(self.documents[-1][1]))
        self.assertEqual(len(rpt.pages), 5)
        content = "\n".join(page.extract_text() for page in rpt.pages)
        for number in range(1, 40):
            self.assertIn(f"{number:03d}", content)
        self.assertIn("Agihan PdP Unit 2", content)
        self.assertIn("Rumah Rubina", rpt.pages[3].extract_text())
        self.assertIn("Budi Pekerti Mulia", rpt.pages[4].extract_text())
        self.assertIn("Mari Belajar", rpt.pages[0].extract_text())
        self.assertIn("UNIT_1_2_3_4_5_2027.pdf", self.documents[-1][0])
        callback(42, "rpt2027_ppki_km_pdf2")
        filename, data, _ = self.documents[-1]
        self.assertIn("KEMAHIRAN_MANIPULATIF", filename)
        rpt = PdfReader(BytesIO(data))
        self.assertEqual(len(rpt.pages), 3)
        self.assertIn("Jari Kreatif", rpt.pages[1].extract_text())
        self.assertIn("Lihat, Dengar dan Rasa", rpt.pages[2].extract_text())


class PpkiApiTest(unittest.TestCase):
    def test_year3_49_word_pdf_and_rpt_have_exact_scope(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        token = "P" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            source = client.get(prefix + "/catalog?year=3", headers=headers).get_json()
            self.assertEqual(source["year"], 3)
            self.assertEqual(source["units"], [{"value": UNIT1, "label": "Unit 1 · Sekolah, Duniaku"}])
            self.assertEqual(source["kemahiran_manipulatif"], [])
            self.assertEqual([row["value"] for row in source["lessons"]],
                             [f"{number:03d}" for number in range(1, 18)])
            self.assertEqual([unit["value"] for unit in source["additional_units"]], [UNIT, UNIT3, UNIT4, UNIT5])
            self.assertEqual(client.get(prefix + "/catalog?year=3&year=2", headers=headers).status_code, 400)
            teacher = {"class": "3 Bestari", "date": "2027-01-20", "time": "09:00 - 09:30",
                       "students": "8", "reflection": "Ulang dengan pilihan bergambar."}
            units = [{"value": UNIT1, "lessons": source["lessons"]}, *source["additional_units"]]
            expected = (range(1, 18), range(18, 36), range(36, 40), range(40, 44), range(44, 50))
            for unit, numbers in zip(units, expected, strict=True):
                self.assertEqual([row["value"] for row in unit["lessons"]], [f"{n:03d}" for n in numbers])
                for row in unit["lessons"]:
                    selection = {"year": 3, "subject": SUBJECT, "unit": unit["value"], "lesson": row["value"]}
                    for fmt in ("word", "pdf"):
                        response = client.post(prefix + "/render", headers=headers,
                                               json={"selection": selection, "teacher": teacher, "format": fmt})
                        self.assertEqual(response.status_code, 200)
                        self.assertIn("TAHUN_3_" + row["value"], response.headers["Content-Disposition"])
                        if fmt == "word":
                            doc = Document(BytesIO(response.data))
                            text = "\n".join([p.text for p in doc.paragraphs] +
                                             [cell.text for table in doc.tables for cells in table.rows for cell in cells.cells])
                        else:
                            doc = PdfReader(BytesIO(response.data))
                            self.assertEqual(len(doc.pages), 1)
                            text = doc.pages[0].extract_text()
                        self.assertIn("Tahun 3", text)
                        self.assertIn("Ulang dengan pilihan bergambar.", text)
            bad = {**selection, "year": 2}
            self.assertEqual(client.post(prefix + "/render", headers=headers,
                                         json={"selection": bad, "teacher": teacher, "format": "pdf"}).status_code, 404)
            rpt = client.get(prefix + "/rpt.pdf?year=3", headers=headers)
            self.assertEqual(rpt.status_code, 200)
            pages = PdfReader(BytesIO(rpt.data)).pages
            self.assertEqual(len(pages), 5)
            for page, last in zip(pages, ("017", "035", "039", "043", "049"), strict=True):
                text = page.extract_text()
                self.assertIn("Tahun 3", text)
                self.assertIn(last, text)
            self.assertEqual(client.get(prefix + "/rpt-manipulatif.pdf?year=3", headers=headers).status_code, 404)

    def test_all_71_word_pdf_and_protected_access(self):
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
            self.assertEqual([unit["value"] for unit in options["additional_units"]], [UNIT3, UNIT4, UNIT5, UNIT1])
            manipulative = options["kemahiran_manipulatif"]
            self.assertEqual([unit["value"] for unit in manipulative], list(MANIPULATIVE_UNIT_LESSONS))
            for unit in manipulative:
                self.assertEqual([row["value"] for row in unit["lessons"]],
                                 [f"{number:03d}" for number in MANIPULATIVE_UNIT_LESSONS[unit["value"]]])
            units = [{"value": UNIT, "lessons": options["lessons"]}, *options["additional_units"], *manipulative]
            for unit in units:
                selection["unit"] = unit["value"]
                for row in unit["lessons"]:
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
            selection["unit"] = UNIT
            selection["lesson"] = "015"
            self.assertEqual(client.post(prefix + "/render", headers=headers,
                                         json={"selection": selection, "teacher": teacher, "format": "pdf"}).status_code, 404)
            for endpoint, pages in (("/rpt.pdf", 1), ("/rpt-current.pdf", 5), ("/rpt-manipulatif.pdf", 3)):
                response = client.get(prefix + endpoint, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(PdfReader(BytesIO(response.data)).pages), pages)
