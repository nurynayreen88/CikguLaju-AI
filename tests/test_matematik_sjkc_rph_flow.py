from io import BytesIO
import os
from threading import Lock
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from curriculum_version_selector import LEGACY
from staging.matematik_sjkc.tahun_3.rph import RELEASE_FLAG
from web.matematik_sjkc_t3_telegram import install
from web.native_rph_telegram_api import create_native_rph_blueprint


class MatematikSjkcRphFlow(unittest.TestCase):
    def setUp(self):
        self.token = "local-test-" + "x" * 32
        env = patch.dict(os.environ, {
            RELEASE_FLAG: "1",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": self.token,
        })
        env.start()
        self.addCleanup(env.stop)
        self.state = {"year": "Tahun 3", "curriculum_version": LEGACY, "task": "quick_material"}
        self.runtime = SimpleNamespace(
            state={5: self.state}, SUBJECTS_BY_GRADE={"Tahun 3": ["Matematik"]},
            callback=Mock(), send=Mock(), _lesson_to_class_v2439=Mock(),
            _available_materials_v2528=Mock(return_value=["worksheet"]),
            _submit_materials_v2528=Mock(), _material_picker_v2528=Mock(),
            _credit_gate=Mock(return_value=True), send_document=Mock(),
            _telegram_delivery_ok_v25279=Mock(return_value=True),
            _consume_free_after_success_v25282=Mock(),
            _processing_chats=set(), _runtime_lock=Lock(),
            create_word_file=Mock(), create_pdf_file=Mock(),
        )
        app = Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(self.runtime))
        self.client = app.test_client()
        self.auth = {"Authorization": "Bearer " + self.token}
        self.base = "/internal/rph/v1/matematik-sjkc/"
        self.metadata = {"class": "三年级智慧班", "date": "2027-01-17",
                         "time": "09:00 - 10:00", "students": "32",
                         "reflection": "28 murid menguasai kemahiran.\n其余学生需要练习。"}

    def test_catalog_covers_96_lessons_and_requires_release_and_auth(self):
        url = self.base + "options"
        self.assertEqual(self.client.get(url, query_string={"year": 3}).status_code, 401)
        with patch.dict(os.environ, {RELEASE_FLAG: "0"}):
            self.assertFalse(install(self.runtime))
            self.assertEqual(self.client.get(url, headers=self.auth, query_string={"year": 3}).status_code, 404)
        options = self.client.get(url, headers=self.auth, query_string={"year": 3}).get_json()
        self.assertEqual([unit["value"] for unit in options], list(map(str, range(1, 10))))
        pdps = [pdp["lesson_no"] for row in options for pdp in
                self.client.get(url, headers=self.auth, query_string={"year": 3, "unit": row["value"]}).get_json()]
        self.assertEqual(pdps, list(range(1, 97)))
        self.assertEqual(self.client.get(url, headers=self.auth,
                                        query_string={"year": 3, "unit": 1, "pdp": 17}).status_code, 404)

    def test_word_and_pdf_use_selected_pdp_and_teacher_details(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                result = self.client.post(self.base + "render", headers=self.auth, json={
                    "year": 3, "unit": 2, "pdp": 17, "format": fmt, "teacher": self.metadata,
                })
                self.assertEqual(result.status_code, 200)
                self.assertIn("_PdP_017.", result.headers["Content-Disposition"])
                if fmt == "word":
                    document = Document(BytesIO(result.data))
                    self.assertEqual(len(document.tables), 1)
                    text = "\n".join(p.text for p in document.paragraphs)
                else:
                    pages = PdfReader(BytesIO(result.data)).pages
                    self.assertEqual(len(pages), 1)
                    text = pages[0].extract_text()
                for value in self.metadata.values():
                    self.assertIn(value.strip(), text)

    def select_in_telegram(self):
        self.assertTrue(install(self.runtime))
        self.assertEqual(self.runtime.SUBJECTS_BY_GRADE["Tahun 3"], ["Matematik", "Matematik SJKC"])
        self.runtime.callback(5, "sub_Matematik SJKC")
        self.runtime.callback(5, "msjkc3u:1")
        self.runtime.callback(5, "msjkc3p:17")
        self.runtime._lesson_to_class_v2439.assert_not_called()
        self.runtime.callback(5, "msjkc3u:2")
        self.runtime.callback(5, "msjkc3p:17")
        self.runtime._lesson_to_class_v2439.assert_called_once_with(5)
        self.assertEqual(self.runtime._available_materials_v2528(self.state), ["rph", "rph_word"])
        self.state["_materials_selected_v2528"] = ["rph", "rph_word"]

    def test_telegram_word_and_pdf_use_one_trial_after_confirmation(self):
        self.select_in_telegram()
        self.runtime._submit_materials_v2528(5)
        self.assertEqual(self.runtime.send_document.call_count, 2)
        self.runtime._consume_free_after_success_v25282.assert_called_once_with(
            5, "successful_sjkc_rph_delivery")
        self.runtime.create_word_file.assert_not_called()
        self.runtime.create_pdf_file.assert_not_called()
        self.assertFalse(self.runtime._processing_chats)

    def test_telegram_missing_delivery_confirmation_preserves_trial(self):
        self.select_in_telegram()
        self.runtime._telegram_delivery_ok_v25279.return_value = False
        with self.assertLogs("web.matematik_sjkc_t3_telegram", level="ERROR"):
            self.runtime._submit_materials_v2528(5)
        self.runtime._consume_free_after_success_v25282.assert_not_called()
        self.assertFalse(self.runtime._processing_chats)

    def test_telegram_retry_after_partial_delivery_sends_only_the_missing_format(self):
        self.select_in_telegram()
        self.runtime._telegram_delivery_ok_v25279.side_effect = [True, False, True]
        with self.assertLogs("web.matematik_sjkc_t3_telegram", level="ERROR"):
            self.runtime._submit_materials_v2528(5)
        self.runtime._submit_materials_v2528(5)
        extensions = [call.args[1].rsplit(".", 1)[-1] for call in self.runtime.send_document.call_args_list]
        self.assertEqual(extensions, ["pdf", "docx", "docx"])
        self.runtime._credit_gate.assert_called_once()
        self.runtime._consume_free_after_success_v25282.assert_called_once()

    def test_year_two_uses_its_own_units_and_keeps_year_three_available(self):
        from staging.matematik_sjkc.tahun_2 import rph as year_two
        from web.matematik_sjkt_t2_telegram import install_year_two

        self.runtime.SUBJECTS_BY_GRADE["Tahun 2"] = ["Matematik"]
        self.runtime._daily_candidate_v25292 = Mock()
        self.assertTrue(install(self.runtime))
        params = {"year": 2}
        url = self.base + "options"
        self.assertEqual(self.client.get(url, headers=self.auth, query_string=params).status_code, 404)
        with patch.dict(os.environ, {year_two.RELEASE_FLAG: "1"}):
            self.assertTrue(install_year_two(self.runtime, year_two, "sjkc2", "TEST_SJKC_T2_ACTIVE"))
            for year, unit_count in ((2, 8), (3, 9)):
                self.state.update(year=f"Tahun {year}")
                self.runtime.callback(5, "sub_Matematik SJKC")
                unit_buttons = self.runtime.send.call_args.args[2]
                self.assertEqual(len(unit_buttons) - 1, unit_count)
                self.assertTrue(unit_buttons[0][0]["callback_data"].startswith(f"msjkc{year}u:"))
                self.runtime.callback(5, f"msjkc{year}u:1")
                self.runtime.callback(5, f"msjkc{year}p:1")
                self.assertEqual(self.runtime._available_materials_v2528(self.state), ["rph", "rph_word"])
                units = self.client.get(url, headers=self.auth, query_string={"year": year}).get_json()
                self.assertEqual(len(units), unit_count)
                for fmt in ("word", "pdf"):
                    reply = self.client.post(self.base + "render", headers=self.auth, json={
                        "year": year, "unit": 1, "pdp": 1, "format": fmt, "teacher": self.metadata,
                    })
                    self.assertEqual(reply.status_code, 200)
                    self.assertIn(f"_Tahun_{year}_PdP_001.", reply.headers["Content-Disposition"])
            self.assertEqual(self.client.get(url, headers=self.auth,
                                            query_string={"year": 2, "unit": 8, "pdp": 1}).status_code, 404)

    def test_existing_subject_delegates(self):
        self.assertTrue(install(self.runtime))
        self.state.update(subject="Matematik")
        self.assertEqual(self.runtime._available_materials_v2528(self.state), ["worksheet"])
        self.runtime._submit_materials_v2528(5)
        self.runtime.send_document.assert_not_called()
