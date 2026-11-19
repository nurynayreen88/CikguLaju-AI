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

from staging.matematik.penjana_2027 import DPK_ROUTE, ROUTE, register_downloads
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
        self.assertEqual(counts, {"s": 116, "m": 54, "s6": 89, "d6": 61, "m5": 69,
                                  "d5": 70, "mt4": 117, "mt5": 117, "mt6": 117,
                                  "dp2": 117, "dp3": 117})
        self.assertEqual(len(self.documents), 2088)
        self.assertEqual(self.credits, 1044)

    def test_dpk_private_route_keeps_edition_year_and_grouped_standards(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-dpk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        teacher = {"class": "Bestari", "date": "2027-10-18",
                   "students": "32", "reflection": "Semak sekali lagi."}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            for year, unit_id, number, codes in ((2, 7, 111, "7.1.2, 7.2.1"), (3, 9, 117, "9.2.2")):
                query = {"year": year, "subject": "MATH"}
                units = client.get(DPK_ROUTE + "/units", query_string=query, headers=headers).json["items"]
                lesson = f"SK27-DPK3-MATH-Y{year}-L{number:03d}"
                selection = {**query, "unit": units[unit_id-1]["value"], "lesson": lesson}
                self.assertEqual(client.get(ROUTE + "/availability", query_string=selection,
                                            headers=headers).status_code, 404)
                self.assertEqual(client.get(DPK_ROUTE + "/availability", query_string=selection).status_code, 401)
                response = client.post(DPK_ROUTE + "/render", headers=headers, json={
                    "selection": selection,
                    "teacher": {**teacher, "time": "08:00-09:00" if year == 2 else "08:00-08:30"},
                    "format": "word",
                })
                self.assertEqual(response.status_code, 200, response.get_json(silent=True))
                document = Document(BytesIO(response.data))
                self.assertIn("DPK Edisi 3", document.paragraphs[1].text)
                self.assertIn("SP " + codes, document.tables[0].rows[4].cells[1].text)
                self.assertIn("Semak sekali lagi.", document.tables[-1].rows[1].cells[1].text)

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

    def test_year_four_preserves_grouped_standards_and_thirty_minute_plan(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-sk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        query = {"year": 4, "subject": "MATH"}
        lesson = "SK27-MATH-Y4-L005"
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            units = client.get(ROUTE + "/units", query_string=query, headers=headers).json["items"]
            self.assertEqual(len(units), 8)
            selection = {**query, "unit": units[0]["value"], "lesson": lesson}
            response = client.post(ROUTE + "/render", headers=headers, json={
                "selection": selection,
                "teacher": {"class": "Bestari", "date": "2027-01-18",
                            "time": "08:00-08:30", "students": "32"},
                "format": "word",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.get(ROUTE + "/availability",
                                        query_string=selection | {"unit": units[1]["value"]},
                                        headers=headers).status_code, 404)
        word, _ = self._select("mt4", "01", lesson)
        self.click(word)
        for data in (response.data, self.documents[-1][1]):
            doc = Document(BytesIO(data))
            fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
            self.assertIn("30 minit", fields["Lesson / tempoh"])
            self.assertIn("SP 1.5.1, 1.5.2", fields["SK / SP"])

    def test_private_web_render_matches_telegram_for_year_six_ratio(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-sk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        query = {"year": 6, "subject": "MATH"}
        lesson = "SK27-MATH-Y6-L097"
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            self.assertEqual(client.get(ROUTE + "/units", query_string=query).status_code, 401)
            units = client.get(ROUTE + "/units", query_string=query, headers=headers).json["items"]
            self.assertEqual(len(units), 8)
            selection = {**query, "unit": units[6]["value"], "lesson": lesson}
            wrong_unit = {**selection, "unit": units[0]["value"]}
            self.assertEqual(client.get(ROUTE + "/availability", query_string=wrong_unit,
                                        headers=headers).status_code, 404)
            teacher = {"class": "Bestari", "date": "2027-10-18", "time": "08:00-09:00", "students": "32"}
            response = client.post(ROUTE + "/render", headers=headers, json={
                "selection": selection, "teacher": teacher, "format": "word",
            })
            self.assertEqual(response.status_code, 200)
        word, _ = self._select("mt6", "07", lesson)
        self.click(word)
        native, telegram = (Document(BytesIO(data)) for data in
                            (response.data, self.documents[-1][1]))
        self.assertEqual(native.paragraphs[2].text, telegram.paragraphs[2].text)
        native_header = native.tables[0].rows
        telegram_header = telegram.tables[0].rows
        self.assertEqual(native_header[4].cells[1].text, telegram_header[4].cells[1].text)
        self.assertIn("SK 7.2", native_header[4].cells[1].text)
