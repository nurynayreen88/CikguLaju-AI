"""Verify the bot menu uses the exact reviewed plans and existing credit gate."""

from collections import Counter
from io import BytesIO
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from web.native_rph_telegram_api import create_native_rph_blueprint
from web.telegram_sk_rph_2027 import install
from web.telegram_rph_entry_choices_20261110 import install as install_entry


class TelegramSKRPH2027Tests(unittest.TestCase):
    def setUp(self):
        self.documents = []
        self.credits = 0
        self.allow_delivery = True
        self.account_allowed = True
        r = self.runtime = SimpleNamespace(
            callback=lambda cid, data: ("legacy", data),
            _continue_after_rph_time=lambda cid, st: "legacy materials",
            state={},
            _runtime_lock=Lock(),
            _processing_chats=set(),
            send=lambda cid, text, keyboard: keyboard,
            send_document=self._send_document,
            _credit_gate=lambda cid, st: self.account_allowed,
            _telegram_delivery_ok_v25279=lambda result: result is True,
            _consume_free_after_success_v25282=self._debit,
            _lesson_to_class_v2439=lambda cid: "existing class picker",
            CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE=True,
            quick=lambda cid: None,
        )
        self.assertTrue(install_entry(r))
        self.assertTrue(install(r))
        self.assertEqual(self.click("choose_grade"), ("legacy", "choose_grade"))
        self.assertIn("sk27:home", self.buttons(r.quick(123)))

    @staticmethod
    def buttons(menu):
        return [button["callback_data"] for row in menu for button in row]

    def click(self, command):
        return self.runtime.callback(123, command)

    def _send_document(self, cid, path, caption):
        self.documents.append((Path(path).name, Path(path).read_bytes()))
        return self.allow_delivery

    def _debit(self, cid, reason):
        self.credits += 1

    def _select(self, scope, unit, code):
        self.click("sk27:home")
        self.click(f"sk27:set:{scope}")
        self.click(f"sk27:unit:{scope}:{unit}")
        self.assertEqual(self.click(f"sk27:pick:{scope}:{unit}:{code}"), "existing class picker")
        state = self.runtime.state[123]
        state.update(rph_class="Bestari", rph_date="18/10/2027", rph_time="08:00 - 09:00",
                     rph_students="32")
        buttons = self.buttons(self.runtime._continue_after_rph_time(123, state))
        return buttons[:2]

    def test_every_exact_selection_can_send_word_and_pdf(self):
        keys = [key for key in self.buttons(self.click("sk27:home")) if key.startswith("sk27:set:")]
        counts = Counter()
        for scope in keys:
            units = [key for key in self.buttons(self.click(scope)) if key.startswith("sk27:unit:")]
            for unit in units:
                lessons = [key for key in self.buttons(self.click(unit)) if key.startswith("sk27:pick:")]
                for key in lessons:
                    _, _, set_id, unit_id, code = key.split(":")
                    with self.subTest(code=code):
                        word, pdf = self._select(set_id, unit_id, code)
                        self.click(word)
                        self.click(pdf)
                        self.assertEqual(self.documents[-2][0], f"CikguLaju_RPH_{code}.docx")
                        self.assertEqual(self.documents[-1][0], f"CikguLaju_RPH_{code}.pdf")
                        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 1)
                        counts[set_id] += 1
        self.assertEqual(counts, {"d4": 69, "s": 116, "m": 54, "s6": 89, "d6": 61, "m5": 69, "d5": 70})
        self.assertEqual(len(self.documents), 1056)
        self.assertEqual(self.credits, 528)

    def test_science_year4_api_returns_the_exact_catalogue_and_files(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda *_: None, create_pdf_file=lambda *_: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        client = app.test_client()
        path = "/internal/rph/v1/dlp"
        token = "cikgulaju-local-test-token-for-science-y4"
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            self.assertEqual(client.get(path + "/year4-science/catalogue").status_code, 401)
            response = client.get(path + "/year4-science/catalogue", headers=headers)
            self.assertEqual(response.status_code, 200)
            catalogue = response.get_json()
            self.assertEqual((catalogue["year"], catalogue["subject"]), (4, "SCIENCE_DLP"))
            self.assertEqual(len(catalogue["units"]), 10)
            self.assertEqual(sum(len(unit["lessons"]) for unit in catalogue["units"]), 69)
            teacher = {"class": "4 Bestari", "date": "22/08/2027", "time": "08:00 - 09:00",
                       "students": "32", "reflection": "Check the evidence in the next lesson."}
            for unit, lesson in (("08", "DLP-SCI-Y4-L46"), ("10", "DLP-SCI-Y4-R10")):
                selection = {"year": 4, "subject": "SCIENCE_DLP", "unit": unit, "lesson": lesson}
                available = client.get(path + "/availability", query_string=selection, headers=headers)
                self.assertEqual(available.get_json(), {"available": True, "formats": ["word", "pdf"]})
                for fmt, suffix in (("word", "docx"), ("pdf", "pdf")):
                    result = client.post(path + "/render", headers=headers,
                                         json={"selection": selection, "teacher": teacher, "format": fmt})
                    self.assertEqual(result.status_code, 200)
                    self.assertIn(f"{lesson}.{suffix}", result.headers["Content-Disposition"])
                    if fmt == "word":
                        doc = Document(BytesIO(result.data))
                        self.assertIn(teacher["class"], doc.tables[0].rows[3].cells[1].text)
                        self.assertEqual(doc.tables[-1].rows[0].cells[1].text, teacher["reflection"])
                    else:
                        page, = PdfReader(BytesIO(result.data)).pages
                        self.assertIn(teacher["class"], page.extract_text())
                wrong = client.get(path + "/availability", query_string={**selection, "unit": "01"},
                                   headers=headers)
                self.assertEqual(wrong.status_code, 404)
            self.assertEqual(client.get(path + "/year4-mathematics/catalogue", headers=headers).status_code, 404)

    def test_wrong_set_old_buttons_and_failed_delivery_cannot_charge(self):
        word, _ = self._select("s", "01", "SK27-SCI-Y5-PDP-001")
        self.allow_delivery = False
        self.click(word)
        self.assertEqual(self.credits, 0)
        self.allow_delivery = True
        self.click(word)
        self.assertEqual(self.credits, 1)
        doc = Document(BytesIO(self.documents[-1][1]))
        self.assertEqual(doc.paragraphs[2].text, "Pemerhatian kualitatif dengan deria")
        self.assertIn("Bestari", doc.tables[0].rows[3].cells[1].text)
        next_word, _ = self._select("m", "01", "DLP-MATH-Y6-L01")
        self.click(word)
        self.assertEqual(len(self.documents), 2)
        self.account_allowed = False
        self.click(next_word)
        self.assertEqual(len(self.documents), 2)
        self.assertEqual(self.credits, 1)
