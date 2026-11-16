import os
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import fitz
from flask import Flask

from web.english_integrated_rph_2027 import render
from web.native_rph_telegram_api import create_native_rph_blueprint
from web.telegram_rph_hari_ini_manual_20261110 import _generate_integrated, install


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
            criteria = client.post(path, json={**payload, "format": "pbd"},
                                   headers=headers).json
            self.assertEqual(criteria["lesson"], "Lesson 013 + 014")
            self.assertIn("3.2", criteria["sp"])
            self.assertNotEqual(criteria["criteria1"], criteria["criteria2"])
            wrong_time = {**payload, "teacher": {**payload["teacher"], "time": "08:00 - 08:30"}}
            self.assertEqual(client.post(path, json=wrong_time, headers=headers).status_code, 400)

    def test_telegram_checkpoint_uses_end_of_pair_after_confirmed_send(self):
        rt = SimpleNamespace(state={7: {"old": True}})
        sent, charges = [], []
        def prepare(cid, entry, row):
            rt.state[cid].update(rph_time="08:00 - 09:00", lesson_no=13)
            return True
        def send(cid, path, caption):
            sent.append((rt.state[cid]["lesson_no"], Path(path).name))
            ok = len(sent) == 2
            if ok:
                charges.append(True)
            return {"ok": ok}
        rt._apply_verified_next_row_v25277 = prepare
        rt._credit_gate = lambda *_: True
        rt._profile_class_record = lambda *_: {"students": 24}
        rt._telegram_delivery_ok_v25279 = lambda result: result["ok"]
        rt.send_document = send
        args = (rt, 7, {"class_name": "3 Amanah"}, {}, (date(2027, 1, 18), 3, 13, (13, 14)))
        self.assertFalse(_generate_integrated(*args)["ok"])
        self.assertEqual(charges, [])
        self.assertTrue(_generate_integrated(*args)["ok"])
        self.assertEqual(charges, [True])
        self.assertEqual(sent, [(14, "RPH_English_SK_2027_Y3_L013-014.pdf")] * 2)
        self.assertEqual(rt.state[7], {"old": True})

    def test_daily_menu_bootstraps_exact_pair_and_rechecks_stale_preview(self):
        slot = {"class_name": "3 Amanah", "subject": "English", "day": "Isnin",
                "start": "08:00", "end": "09:00"}
        rt = SimpleNamespace(state={}, menu=lambda cid: None, callback=lambda *args: None)
        rt.send = lambda *args: args[1]
        rt._timetable_entries = lambda cid: [slot]
        rt._today_rows_v25272 = lambda cid: ("Isnin", [(0, slot)])
        rt._entry_with_subject_v25294 = lambda entry, subject: {**entry, "subject": subject}
        rt._daily_candidate_v25292 = lambda *args: (None, "legacy")
        rt._next_curriculum_summary_v25276 = lambda row: "Legacy summary"
        rt._generate_one_quick_rph_v25278 = lambda *args: self.fail("Unexpected legacy generation")
        rt._generate_calendar_row_v25293 = lambda *args: self.fail("Unexpected unpaired generation")
        rt._telegram_delivery_ok_v25279 = lambda result: result
        rt._send_document_before_v25277 = lambda *args: True
        rt._profile_class_record = lambda *args: {}
        rt._teacher_profile = lambda cid: {"state_name": "Selangor"}
        rt._subject_alias_candidates_v25294 = lambda *args: (["English"], "")
        rt._norm_subject_v2393 = str.casefold
        rt._get_rph_progress_v25274 = lambda *args: {}
        rt._checkpoint_no_v25276 = lambda row: row["_sequence_no"]
        rt._resolve_next_curriculum_v25276 = lambda *args: {"_sequence_no": 3, "year": "Year 3"}
        rt._english_primary_year_number_v2517 = lambda year: int(year.split()[-1])
        rt._resolve_next_english_v25276 = lambda year, last: {"_sequence_no": last + 1, "year": year}
        def preview(cid):
            row, source = rt._daily_candidate_v25292(cid, slot)
            rt.state.setdefault(cid, {})["_daily_suggestions_v25292"] = [
                {"entry": slot, "row": row, "source": source}] if row else []
            return rt._next_curriculum_summary_v25276(row) if row else source
        rt._today_rpt_suggestions_v25292 = preview
        self.assertTrue(install(rt))
        module = "web.english_integrated_rph_2027"
        with patch(module + ".enabled", return_value=True), patch(module + ".teaching_date") as now, \
                patch("web.telegram_rph_hari_ini_manual_20261110._generate_integrated",
                      return_value={"ok": True}) as generate:
            now.return_value = date(2027, 1, 4)
            self.assertEqual(rt.callback(7, "todayrph272"), "Lesson 001 + 002 • Satu RPH")
            self.assertIn("1/1", rt.callback(7, "daily292_generate"))
            self.assertEqual(generate.call_args.args[-1][-1], (1, 2))

            rt.callback(7, "todayrph272")
            now.return_value = date(2027, 1, 5)
            self.assertIn("Cadangan telah berubah", rt.callback(7, "daily292_generate"))
            self.assertEqual(generate.call_count, 1)

            for closed in (date(2027, 2, 8), date(2027, 3, 8), date(2027, 10, 27),
                           date(2027, 11, 1)):
                now.return_value = closed
                self.assertEqual(rt.callback(7, "todayrph272"), "english_2027_no_teaching_session")

            now.return_value = date(2027, 1, 4)
            rt._get_rph_progress_v25274 = lambda *args: {"last_success_at": "2027-01-03T18:00:00+00:00"}
            row, source = rt._daily_candidate_v25292(7, slot)
            self.assertEqual((row["_sequence_no"], source), (3, "checkpoint"))
            rt._get_rph_progress_v25274 = lambda *args: {"last_success_at": "2026-11-20T00:00:00+00:00"}
            self.assertEqual(rt.callback(7, "todayrph272"), "Lesson 001 + 002 • Satu RPH")

            rt._resolve_next_english_v25276 = lambda year, last: {"_sequence_no": last + 2, "year": year}
            self.assertEqual(rt.callback(7, "todayrph272"), "english_2027_exact_lesson_unavailable")

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
