from contextlib import ExitStack
from io import BytesIO
import os
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app
from web import native_telegram_sjkc_math_client as sjkc


class WebMatematikSjkcRph(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.account = {"telegram_user_id": 123, "free_remaining": 1}
        self.paid = stack.enter_context(patch("web.unified_rph_web._has_paid_access", return_value=True))
        stack.enter_context(patch("web.unified_rph_web._account", return_value=(self.account, None)))
        stack.enter_context(patch.dict(os.environ, {
            "CIKGULAJU_WEB_CATALOG_MODE": "telegram-api",
            "CIKGULAJU_AUTHORITATIVE_API_URL": "https://source.example",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40,
        }))
        stack.enter_context(patch("web_v1_telegram_auth_routes._config", return_value={
            "CIKGULAJU_WEB_SESSION_SECRET": "y" * 40,
            "account_backend": "supabase",
            "supabase_url": "https://db.example",
            "supabase_key": "test-key",
        }))
        self.verify_session = stack.enter_context(patch("web_v1_sessions.verify_session_ticket", return_value=123))
        stack.enter_context(patch("web_v1_telegram_auth_routes._lookup", return_value=self.account))
        source = stack.enter_context(patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource"))
        source.return_value.list_subjects.return_value = [{"value": "BM", "label": "Bahasa Melayu"}]
        stack.enter_context(patch("web.native_telegram_other_draft_client.list_draft_units", return_value=[]))
        stack.enter_context(patch("web.native_telegram_rbt_2027_client.list_rbt_units", return_value=[]))
        stack.enter_context(patch("web.native_telegram_sejarah_2027_client.list_sejarah_units", return_value=[]))
        self.debit = stack.enter_context(patch("web.rph_delivery_quota.authorize_rendered_document"))
        self.query = {"year": 3, "subject": sjkc.SUBJECT, "unit": "2", "lesson": "17",
                      "teacher_class": "3 智慧班", "teacher_date": "2027-01-17",
                      "teacher_start": "09:00", "teacher_end": "10:00", "teacher_students": "32"}

    def test_catalog_lists_year_3_only_when_telegram_source_answers(self):
        with patch.object(sjkc, "options", return_value=[{"value": "1", "label": "Unit 1"}]):
            for year in (2, 3, 4):
                result = self.client.get("/api/options", query_string={
                    "kind": "subjects", "year": year, "curriculum": "sjkc",
                })
                self.assertEqual(any(row["value"] == sjkc.SUBJECT for row in result.get_json()), year == 3)
            sk = self.client.get("/api/options?kind=subjects&year=3")
            self.assertEqual(sk.status_code, 200)
            self.assertNotIn(sjkc.SUBJECT, {row["value"] for row in sk.get_json()})
        with patch.object(sjkc, "options", side_effect=sjkc.NativeRPHUnavailable):
            result = self.client.get("/api/options?kind=subjects&year=3&curriculum=sjkc")
            self.assertEqual(result.get_json(), [])

    def test_catalog_requires_login_and_passes_exact_unit_to_telegram(self):
        params = {"kind": "pdp", "year": 3, "subject": sjkc.SUBJECT, "unit": "2"}
        with patch.object(sjkc, "options", return_value=[{"value": "17", "label": "PdP 017"}]) as options:
            self.verify_session.return_value = None
            self.assertEqual(self.client.get("/api/options", query_string=params).status_code, 401)
            options.assert_not_called()
            self.verify_session.return_value = 123
            result = self.client.get("/api/options", query_string=params)
            self.assertEqual(result.get_json()[0]["value"], "17")
            options.assert_called_once_with(3, "2")

    def test_invalid_unit_returns_bad_request(self):
        response = self.client.get("/api/options", query_string={
            "kind": "pdp", "year": 3, "subject": sjkc.SUBJECT, "unit": "invalid",
        })
        self.assertEqual(response.status_code, 400)

    def test_paid_download_uses_exact_pdP_and_teacher_fields(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt), patch.object(sjkc, "verify", return_value=17) as verify, \
                 patch.object(sjkc, "request_document", return_value=BytesIO(b"document")) as render:
                result = self.client.post("/api/web/rph/" + fmt, query_string=self.query,
                                          json={"reflection": "28 murid menguasai."})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.headers["X-RPH-Access-Mode"], "paid")
                self.assertIn("MATH_SJKC_TAHUN_3_017", result.headers["Content-Disposition"])
                verify.assert_called_once_with(3, "2", "17")
                selected, sent_fmt = render.call_args.args
                self.assertEqual(sent_fmt, fmt)
                self.assertEqual(selected["teacher"], {
                    "class": "3 智慧班", "date": "2027-01-17", "time": "09:00 - 10:00",
                    "students": "32", "reflection": "28 murid menguasai.",
                })
        self.debit.assert_not_called()

    def test_unavailable_or_failed_telegram_render_never_uses_trial(self):
        self.paid.return_value = False
        with patch.object(sjkc, "verify", side_effect=sjkc.NativeRPHUnavailable):
            self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=self.query).status_code, 503)
        with patch.object(sjkc, "verify", return_value=17), \
             patch.object(sjkc, "request_document", side_effect=sjkc.NativeRPHUnavailable):
            self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=self.query).status_code, 503)
        self.debit.assert_not_called()

    def test_trial_debits_after_returned_document(self):
        self.paid.return_value = False
        self.debit.return_value = {"allowed": True, "remaining": 0}
        with patch.object(sjkc, "verify", return_value=17), \
             patch.object(sjkc, "request_document", return_value=BytesIO(b"test PDF")):
            result = self.client.get("/api/web/rph/pdf", query_string=self.query)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["X-RPH-Trial-Remaining"], "0")
        self.assertEqual(self.debit.call_args.args[2], b"test PDF")
