import os
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import fitz
from flask import Flask

from web.english_integrated_rph_2027 import render
from web.native_rph_telegram_api import create_native_rph_blueprint
from web.telegram_rph_hari_ini_manual_20261110 import _generate_integrated


class IntegratedRPHTests(TestCase):
    def test_both_references_open_one_plan_through_private_http(self):
        app = Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(
            SimpleNamespace(create_word_file=lambda *args: None, create_pdf_file=lambda *args: None)))
        client = app.test_client()
        env = {"CIKGULAJU_ENGLISH_2027_INTEGRATED_RPH_ENABLED": "1",
               "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
               "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 40}
        headers = {"Authorization": "Bearer " + env["CIKGULAJU_AUTHORITATIVE_API_TOKEN"]}
        payload = {"year": 3, "lesson": 13, "unit": "Welcome!",
                   "teacher": {"class": "3 Amanah", "date": "2027-01-18",
                               "time": "08:00 - 09:00", "students": "24"}, "format": "pdf"}
        path = "/internal/rph/v1/english-integrated"
        with patch.dict(os.environ, env):
            self.assertEqual(client.post(path, json=payload).status_code, 401)
            first = client.post(path, json=payload, headers=headers)
            second = client.post(path, json={**payload, "lesson": 14}, headers=headers)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(first.headers["Content-Disposition"], second.headers["Content-Disposition"])
            with fitz.open(stream=first.data) as one, fitz.open(stream=second.data) as two:
                self.assertEqual(len(one), 1)
                self.assertEqual(one[0].get_text(), two[0].get_text())
                self.assertIn("3 Amanah", one[0].get_text())
                self.assertEqual(one[0].get_text().count("Set induction"), 1)
            doc = client.post(path, json={**payload, "format": "word"}, headers=headers)
            self.assertEqual(doc.status_code, 200)
            self.assertTrue(doc.data.startswith(b"PK\x03\x04"))
            self.assertEqual(client.post(path, json={**payload, "unit": "Other"},
                                         headers=headers).status_code, 404)
            self.assertEqual(client.post(path, json={**payload, "format": "metadata"},
                                         headers=headers).json, {"lessons": [13, 14]})
            wrong_time = {**payload, "teacher": {**payload["teacher"], "time": "08:00 - 08:30"}}
            self.assertEqual(client.post(path, json=wrong_time, headers=headers).status_code, 400)

    def test_telegram_checkpoint_uses_end_of_pair_after_confirmed_send(self):
        from datetime import date
        rt = SimpleNamespace(state={7: {"old": True}})
        sent, charges = [], []
        def prepare(cid, entry, row):
            rt.state[cid].update(rph_time="08:00 - 09:00", lesson_no=13)
            return True
        def send(cid, path, caption):
            sent.append((rt.state[cid]["lesson_no"], Path(path).name))
            return {"ok": bool(len(sent) == 2)}
        rt._apply_verified_next_row_v25277 = prepare
        rt._credit_gate = lambda *_: True
        rt._telegram_delivery_ok_v25279 = lambda result: result["ok"]
        rt.send_document = send
        rt._consume_free_after_success_v25282 = lambda *_: charges.append(True)
        args = (rt, 7, {"class_name": "3 Amanah"}, {}, (date(2027, 1, 18), 3, 13, (13, 14)))
        self.assertFalse(_generate_integrated(*args)["ok"])
        self.assertEqual(charges, [])
        self.assertTrue(_generate_integrated(*args)["ok"])
        self.assertEqual(charges, [True])
        self.assertEqual(sent, [(14, "RPH_English_SK_2027_Y3_L013-014.pdf")] * 2)
        self.assertEqual(rt.state[7], {"old": True})

    def test_all_real_pdf_renderers_fit_one_page(self):
        from web.english_integrated_rph_2027 import paired_plan_index
        for (year, number), plan in paired_plan_index().items():
            if number != plan[-1][0][0]:
                continue
            with fitz.open(stream=render(year, number, "pdf", {
                "class": "3 Cemerlang", "date": "2027-01-18", "time": "08:00 - 09:00",
                "students": "40", "reflection": "Follow-up " + "x" * 480,
            })) as document:
                self.assertEqual(len(document), 1, (year, number))
