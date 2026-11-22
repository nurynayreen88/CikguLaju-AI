"""Email/Telegram login UI and opt-in sessions: no real user or payment calls."""
import unittest
from unittest.mock import patch

from flask import Flask

from web_v1_email_auth_routes import bp as email_bp
from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_email_auth_ui import LOGIN_HTML, LOGIN_MARKER, install

SECRET = "test-only-session-secret-with-at-least-32-chars"
ORIGIN = "https://cikgulaju-web.onrender.com"
AUTH = {
    "base": "https://unit.supabase.co",
    "publishable_key": "sb_publishable_test",
    "service_key": "sb_secret_test",
    "session_secret": SECRET,
}
UID = 8000000000000000001
AUTH_UUID = "12345678-1234-4234-9234-123456789012"


class RememberEmailLoginTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(email_bp)
        self.client = self.app.test_client()

    def post_login(self, remember=None):
        data = {"email": "sample@example.com", "password": "safe-example-password"}
        if remember is not None:
            data["remember_me"] = remember
        return self.client.post("/api/auth/email/login", base_url=ORIGIN,
                                headers={"Origin": ORIGIN}, json=data)

    def authenticate(self, remember=None):
        with patch("web_v1_email_auth_routes._auth_configuration", return_value=AUTH), \
             patch("web_v1_email_auth_routes._auth_post",
                   return_value=(200, {"user": {"id": AUTH_UUID}})) as auth_post, \
             patch("web_v1_email_auth_routes._account_id", return_value=UID), \
             patch("web_v1_email_auth_routes._config", return_value={"account_backend": "supabase"}), \
             patch("web_v1_email_auth_routes._lookup",
                   return_value={"telegram_user_id": UID}), \
             patch("web.web_referral_routes.capture_after_verified_login"):
            response = self.post_login(remember)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json["authenticated"])
        self.assertEqual(auth_post.call_count, 1)
        return response

    def test_login_defaults_to_12_hours_and_does_not_store_password(self):
        response = self.authenticate()
        cookie = response.headers["Set-Cookie"]
        self.assertIn("Max-Age=43200", cookie)
        self.assertIn("v1.", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertNotIn("safe-example-password", cookie)

    def test_login_remember_me_issues_14_day_cookie_without_password(self):
        response = self.authenticate(True)
        cookie = response.headers["Set-Cookie"]
        self.assertIn("Max-Age=1209600", cookie)
        self.assertIn("v2.", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertNotIn("safe-example-password", cookie)
        ticket = cookie.split(";", 1)[0].split("=", 1)[1]
        issued = int(ticket.split(".")[2])
        self.assertEqual(verify_session_ticket(ticket, SECRET, now=issued+10*86400), UID)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=issued+14*86400+1))

    def test_explicit_false_stays_standard_duration(self):
        self.assertIn("Max-Age=43200", self.authenticate(False).headers["Set-Cookie"])

    def test_login_rejects_invalid_remember_flag_without_auth_call(self):
        with patch("web_v1_email_auth_routes._auth_post") as auth_post:
            response = self.post_login("true")
        self.assertEqual(response.status_code, 400, response.json)
        auth_post.assert_not_called()

    def test_non_same_origin_login_fails_closed(self):
        response = self.client.post("/api/auth/email/login",
                                    headers={"Origin": "https://example.com"},
                                    json={"email": "sample@example.com",
                                          "password": "safe-example-password",
                                          "remember_me": True})
        self.assertEqual(response.status_code, 403)

    def test_registration_without_session_still_requires_email_confirmation(self):
        payload = {"email": "sample@example.com", "password": "safe-example-password",
                   "remember_me": True}
        with patch("web_v1_email_auth_routes._auth_configuration", return_value=AUTH), \
             patch("web_v1_email_auth_routes._auth_post",
                   return_value=(200, {"user": {"id": AUTH_UUID}})), \
             patch("web_v1_email_auth_routes._account_id") as account:
            response = self.client.post("/api/auth/email/register",
                                        base_url=ORIGIN, headers={"Origin": ORIGIN},
                                        json=payload)
        self.assertEqual(response.status_code, 202, response.json)
        self.assertTrue(response.json["confirmation_required"])
        self.assertNotIn("Set-Cookie", response.headers)
        account.assert_not_called()


class LoginUiTests(unittest.TestCase):
    def test_login_and_register_are_separate_tabs_with_remember_opt_in(self):
        self.assertIn('id="email-mode-login"', LOGIN_HTML)
        self.assertIn('id="email-mode-register"', LOGIN_HTML)
        self.assertIn('id="email-register-confirm-wrap" hidden', LOGIN_HTML)
        self.assertIn('id="email-remember-me" type="checkbox"', LOGIN_HTML)
        self.assertNotIn('id="email-remember-me" type="checkbox" checked', LOGIN_HTML)
        self.assertIn("Ingat saya selama 14 hari", LOGIN_HTML)
        self.assertIn('autocomplete="current-password"', LOGIN_HTML)
        self.assertIn('id="email-forgot-button"', LOGIN_HTML)

    def test_page_injects_shared_remember_flag_for_signed_telegram_login(self):
        app = Flask(__name__)
        @app.get("/")
        def home():
            return ('<html><body><h1>Sediakan RPH langkah demi langkah</h1>' +
                    LOGIN_MARKER +
                    '<script>body:JSON.stringify(user)</script></body></html>')
        install(app)
        with patch.dict("os.environ", {"SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test"}):
            response = app.test_client().get("/")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('id="email-mode-login"', text)
        self.assertIn('id="email-remember-me"', text)
        self.assertIn('remember_me:document.getElementById("email-remember-me")', text)
        self.assertIn('no-store', response.headers.get("Cache-Control", ""))


if __name__ == "__main__":
    unittest.main()
