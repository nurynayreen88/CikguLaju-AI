"""Staging payment route authorization and manual-review safety checks."""
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from flask import Flask

from web.google_auth_staging_routes import bp as google_bp, TICKET_COOKIE
from web.google_payment_staging_routes import bp as payments_bp
from web_google_identity_sessions import issue_google_identity_ticket
from web_v1_sessions import issue_session_ticket
from web_v1_telegram_auth_routes import COOKIE

SECRET = "google-staging-tests-with-at-least-32-characters"
STAGING = "https://staging.example.test"
GOOGLE_ID = "b1d855d1-a68d-4e93-909b-b71ee8ae9e78"
PAYMENT_ID = "8888ee83-6ff8-430d-bf86-800cd403e5ec"
ADMIN_UID = 123456789
CATALOG = '{"rakan_pembangun":{"enabled":true,"amount_sen":1000}}'


class PaymentApiTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "1",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL": "https://staging.supabase.co",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_testing_key",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY": "staging-service-role-test-placeholder",
            "CIKGULAJU_WEB_SESSION_SECRET": SECRET,
            "CIKGULAJU_GOOGLE_STAGING_ORIGIN": STAGING,
            "CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST": "staging.example.test",
            "CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS": str(ADMIN_UID),
            "CIKGULAJU_GOOGLE_STAGING_PAYMENT_CATALOG_JSON": CATALOG,
            "SUPABASE_URL": "https://live.supabase.co",
        })
        self.env.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(google_bp)
        self.app.register_blueprint(payments_bp)
        self.client = self.app.test_client()

    def tearDown(self):
        self.env.stop()

    def google_login(self):
        self.client.set_cookie(TICKET_COOKIE,
                               issue_google_identity_ticket(GOOGLE_ID, SECRET),
                               domain="staging.example.test")

    def telegram_admin_login(self):
        self.client.set_cookie(COOKIE, issue_session_ticket(ADMIN_UID, SECRET),
                               domain="staging.example.test")

    def get(self, path):
        return self.client.get(path, base_url=STAGING)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=STAGING, **kwargs)

    def test_anonymous_and_telegram_only_cannot_submit_google_payment(self):
        self.assertEqual(self.get("/api/web/google/payments").status_code, 401)
        self.telegram_admin_login()
        self.assertEqual(self.get("/api/web/google/payments").status_code, 401)

    def test_authenticated_google_sees_only_own_payments(self):
        self.google_login()
        with patch("web.google_payment_staging_routes.my_payments",
                   return_value=[]) as query:
            response=self.get("/api/web/google/payments")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["plans"], [
            {"code": "rakan_pembangun", "amount_sen": 1000}])
        query.assert_called_once()
        self.assertEqual(query.call_args.args[1], GOOGLE_ID)

    def test_receipt_requires_origin_and_uses_verified_google_id(self):
        self.google_login()
        pdf=b"%PDF-" + (b"x"*900)
        path="/api/web/google/payments"
        invalid=self.post(path, data={"plan_code":"rakan_pembangun",
                         "receipt":(BytesIO(pdf),"proof.pdf")},
                          content_type="multipart/form-data")
        self.assertEqual(invalid.status_code, 403)
        with (
            patch("web.google_payment_staging_routes.submit_receipt",
                  return_value=PAYMENT_ID) as submit,
            patch("web.google_payment_admin_notify.notify_google_payment_admin",
                  return_value=True) as notify,
            patch("web.google_payment_staging_routes.account_display_name",
                  return_value="Cikgu Ujian"),
        ):
            valid=self.post(path, data={"plan_code":"rakan_pembangun",
                 "receipt":(BytesIO(pdf),"proof.pdf")},
                 content_type="multipart/form-data",
                 headers={"Origin":STAGING})
            notify.assert_called_once()
        self.assertEqual(valid.status_code, 201)
        self.assertEqual(valid.json["status"], "pending")
        self.assertEqual(submit.call_args.args[1], GOOGLE_ID)
        self.assertEqual(submit.call_args.args[2], "rakan_pembangun")

    def test_google_cannot_view_admin_payments(self):
        self.google_login()
        self.assertEqual(self.get("/api/web/google/admin/payments").status_code, 403)
        self.assertEqual(self.get("/admin/google-staging-payments").status_code, 403)

    def test_verified_allowlisted_telegram_admin_can_review(self):
        self.telegram_admin_login()
        account={"telegram_user_id": ADMIN_UID}
        with (
            patch("web_v1_telegram_auth_routes._config",
                  return_value={"CIKGULAJU_WEB_SESSION_SECRET":SECRET}) as conf,
            patch("web_v1_telegram_auth_routes._lookup", return_value=account),
            patch("web.google_payment_staging_routes.review_payment",
                  return_value={"id": PAYMENT_ID, "status":"approved",
                                "already_reviewed":False}) as review,
        ):
            response=self.post("/api/web/google/admin/payments/"+PAYMENT_ID+"/review",
                    json={"action":"approve"},
                    headers={"Origin":STAGING})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(review.call_args.args[3], ADMIN_UID)

    def test_admin_cannot_approve_cross_origin(self):
        self.telegram_admin_login()
        with (
            patch("web_v1_telegram_auth_routes._config",
                  return_value={"CIKGULAJU_WEB_SESSION_SECRET":SECRET}),
            patch("web_v1_telegram_auth_routes._lookup",
                  return_value={"telegram_user_id":ADMIN_UID}),
            patch("web.google_payment_staging_routes.review_payment") as review,
        ):
            response=self.post("/api/web/google/admin/payments/"+PAYMENT_ID+"/review",
                    json={"action":"approve"}, headers={"Origin":"https://evil.test"})
            review.assert_not_called()
        self.assertEqual(response.status_code, 403)

    def test_not_allowlisted_admin_cannot_review(self):
        self.telegram_admin_login()
        with patch.dict(os.environ,
                        {"CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS":"987654321"}):
            self.assertEqual(self.get("/api/web/google/admin/payments").status_code, 403)


if __name__ == "__main__":
    unittest.main()
