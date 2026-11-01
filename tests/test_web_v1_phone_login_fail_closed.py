"""Regression tests: phone login remains unavailable until trusted pairing is wired."""
import unittest

from tools.run_web_v1_preview import app


class PhoneLoginFailClosedTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_no_public_login_or_pairing_endpoints(self):
        for path in (
            "/api/auth/telegram",
            "/api/auth/telegram/callback",
            "/api/auth/qr/start",
            "/api/auth/qr/poll",
            "/api/auth/qr/confirm",
        ):
            with self.subTest(path=path):
                for method in ("get", "post"):
                    response = getattr(self.client, method)(path)
                    self.assertIn(response.status_code, (404, 405))

    def test_capabilities_are_explicitly_disabled(self):
        response = self.client.get("/api/auth/capabilities")
        self.assertEqual(response.status_code, 200)
        flags = response.get_json()
        self.assertEqual(flags["status"], "not-configured")
        for key in ("telegram_login_enabled", "phone_qr_pairing_enabled",
                    "existing_account_lookup_enabled", "session_cookie_enabled"):
            self.assertIs(flags[key], False)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_no_authenticated_account_without_signed_identity(self):
        response = self.client.get("/api/account/status")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.get_json()["authenticated"])
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_login_readiness_ui_has_safe_network_fallback(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="telegram-login-readiness"', body)
        self.assertIn('fetch("/api/auth/capabilities"', body)
        self.assertIn("Status login tidak dapat disahkan", body)
        self.assertNotIn("telegram.org/js/telegram-widget.js", body)

    def test_public_preview_never_claims_login_is_active(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Log Masuk dengan Telegram", body)
        self.assertIn("masih dalam pembangunan", body)


if __name__ == "__main__":
    unittest.main()
