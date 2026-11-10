"""Regression: live Web RPH must not charge before a native document exists.

All network and quota calls are mocked. These tests never use real accounts,
secrets, credits or document downloads.
"""
from io import BytesIO
import unittest
from unittest.mock import patch

from flask import Flask
from web.native_telegram_rph_client import NativeRPHUnavailable
from web.unified_rph_web import create_blueprint, source_records


class WebRphDownloadCreditBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client = app.test_client()
        row = source_records(4, "ENGLISH")[0]
        cls.selection = {
            "year": 4, "subject": "ENGLISH",
            "unit": row["unit"], "lesson": row["token"],
        }

    @staticmethod
    def account(credits=5):
        return {
            "authenticated": True,
            "telegram_user_id": 123,
            "free_remaining": credits,
            "rakan_pembangun": False,
        }

    def test_native_failure_is_503_without_attempting_any_trial_debit(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt), \
                 patch("web.unified_rph_web._account",
                       return_value=(self.account(), None)), \
                 patch("web.unified_rph_web._has_paid_access", return_value=False), \
                 patch("web.native_telegram_rph_client.request_native_rph",
                       side_effect=NativeRPHUnavailable("offline")) as native, \
                 patch("web.rph_delivery_quota.authorize_rendered_document") as debit:
                response = self.client.get(
                    "/api/web/rph/" + fmt, query_string=self.selection)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.get_json()["code"], "TELEGRAM_RPH_GENERATOR_UNAVAILABLE")
                native.assert_called_once()
                debit.assert_not_called()

    def test_successful_trial_download_debits_only_after_full_native_render(self):
        for fmt, content in (
            ("pdf", b"%PDF-1.4\n" + b"x" * 1600),
            ("word", b"PK\x03\x04" + b"x" * 1600),
        ):
            with self.subTest(fmt=fmt):
                events = []
                def render(*args, **kwargs):
                    events.append("render")
                    return BytesIO(content)
                def charge(account, uid, data, url, key):
                    self.assertEqual(data, content)
                    self.assertEqual(uid, 123)
                    self.assertEqual(events, ["render"])
                    events.append("debit")
                    return {"allowed": True, "remaining": 4, "reference": "test-only"}
                with patch("web.unified_rph_web._account",
                           return_value=(self.account(), None)), \
                     patch("web.unified_rph_web._has_paid_access",
                           return_value=False), \
                     patch("web.native_telegram_rph_client.request_native_rph",
                           side_effect=render) as native, \
                     patch("web_v1_telegram_auth_routes._config",
                           return_value={"account_backend":"supabase",
                                         "supabase_url":"https://example.invalid",
                                         "supabase_key":"test-only"}), \
                     patch("web.rph_delivery_quota.authorize_rendered_document",
                           side_effect=charge) as debit:
                    response = self.client.get(
                        "/api/web/rph/" + fmt, query_string=self.selection)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, content)
                    self.assertEqual(response.headers["X-RPH-Generator"],
                                     "telegram-native")
                    self.assertEqual(response.headers["X-RPH-Access-Mode"], "trial")
                    self.assertEqual(response.headers["X-RPH-Trial-Remaining"], "4")
                    self.assertEqual(events, ["render", "debit"])
                    native.assert_called_once()
                    debit.assert_called_once()

    def test_paid_access_downloads_even_at_zero_trial_balance_without_debit(self):
        content = b"%PDF-1.4\n" + b"x" * 1600
        with patch("web.unified_rph_web._account",
                   return_value=(self.account(0), None)), \
             patch("web.unified_rph_web._has_paid_access", return_value=True), \
             patch("web.native_telegram_rph_client.request_native_rph",
                   return_value=BytesIO(content)) as native, \
             patch("web.rph_delivery_quota.authorize_rendered_document") as debit:
            response = self.client.get(
                "/api/web/rph/pdf", query_string=self.selection)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, content)
            self.assertEqual(response.headers["X-RPH-Access-Mode"], "paid")
            self.assertNotIn("X-RPH-Trial-Remaining", response.headers)
            native.assert_called_once()
            debit.assert_not_called()

    def test_exhausted_trial_never_renders_or_debits(self):
        with patch("web.unified_rph_web._account",
                   return_value=(self.account(0), None)), \
             patch("web.unified_rph_web._has_paid_access", return_value=False), \
             patch("web.native_telegram_rph_client.request_native_rph") as native, \
             patch("web.rph_delivery_quota.authorize_rendered_document") as debit:
            response = self.client.get(
                "/api/web/rph/word", query_string=self.selection)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.get_json()["code"], "FREE_TRIAL_EXHAUSTED")
            native.assert_not_called()
            debit.assert_not_called()

    def test_uncertain_quota_result_is_not_claimed_as_success(self):
        content = b"%PDF-1.4\n" + b"x" * 1600
        with patch("web.unified_rph_web._account",
                   return_value=(self.account(), None)), \
             patch("web.unified_rph_web._has_paid_access", return_value=False), \
             patch("web.native_telegram_rph_client.request_native_rph",
                   return_value=BytesIO(content)) as native, \
             patch("web_v1_telegram_auth_routes._config",
                   return_value={"account_backend":"supabase",
                                 "supabase_url":"https://example.invalid",
                                 "supabase_key":"test-only"}), \
             patch("web.rph_delivery_quota.authorize_rendered_document",
                   side_effect=TimeoutError("simulated")) as debit:
            response = self.client.get(
                "/api/web/rph/pdf", query_string=self.selection)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.get_json()["code"],
                             "RPH_TRIAL_CHARGE_UNCONFIRMED")
            self.assertNotIn(b"%PDF-", response.data)
            native.assert_called_once()
            debit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
