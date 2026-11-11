"""Regression tests for Web referral first-touch, member-only access and attribution."""
import unittest
from unittest.mock import patch
from flask import Flask

from web.web_referral_routes import install, pending_referral, capture_after_verified_login, REF_COOKIE


class WebReferralTests(unittest.TestCase):
    def make_app(self):
        app = Flask(__name__)
        app.add_url_rule("/", "home", lambda: "CikguLaju")
        install(app)
        return app

    @patch("web_v1_telegram_auth_routes._config")
    def test_visit_before_login_keeps_signed_cookie(self, config):
        config.return_value = {"CIKGULAJU_WEB_SESSION_SECRET": "a" * 48}
        app = self.make_app()
        client = app.test_client()
        code = "A" * 24
        res = client.get("/?ref=" + code)
        self.assertEqual(res.status_code, 200)
        self.assertIn(REF_COOKIE + "=", res.headers.get("Set-Cookie", ""))
        self.assertIn("HttpOnly", res.headers["Set-Cookie"])
        self.assertIn("Secure", res.headers["Set-Cookie"])
        with app.test_request_context("/", headers={"Cookie": res.headers["Set-Cookie"].split(";")[0]}):
            self.assertEqual(pending_referral(), code)

    @patch("web_v1_telegram_auth_routes._config")
    def test_bad_code_never_sets_referral_cookie(self, config):
        config.return_value = {"CIKGULAJU_WEB_SESSION_SECRET": "a" * 48}
        res = self.make_app().test_client().get("/?ref=abc")
        self.assertNotIn(REF_COOKIE, res.headers.get("Set-Cookie", ""))

    @patch("web.web_referral_routes.pending_referral", return_value="B" * 24)
    @patch("web.web_referral_routes._rest")
    def test_verified_user_attribution_uses_rpc(self, rest, _pending):
        rest.return_value = {"captured": True}
        self.assertTrue(capture_after_verified_login(123456))
        rest.assert_called_once_with(
            "POST", "rpc/referral_capture_signup",
            body={"p_referred_user_id": 123456, "p_referral_code": "B" * 24})

    @patch("web.web_referral_routes.pending_referral", return_value="B" * 24)
    @patch("web.web_referral_routes._rest")
    def test_never_award_or_capture_anonymous(self, rest, _pending):
        self.assertFalse(capture_after_verified_login(None))
        self.assertFalse(capture_after_verified_login(-1))
        rest.assert_not_called()

    def test_private_web_navigation_is_hidden_until_authorized(self):
        from pathlib import Path
        base = Path(__file__).resolve().parents[1] / "web_v1_static_preview"
        html = (base / "index.html").read_text("utf-8")
        referral = (base / "web-referral.js").read_text("utf-8")
        admin = (base / "admin-usage.js").read_text("utf-8")
        self.assertIn('id="web-referral-tab"', html)
        self.assertIn('id="web-admin-tab"', html)
        self.assertIn('.sidebar-menu .sidebar-tab[hidden]{display:none!important}', html)
        self.assertIn('if(targetButton?.hidden)return;', html)
        self.assertIn('window.cikgulajuReferralInit?.();', html)
        self.assertIn('tab.hidden = false;', referral)
        self.assertIn('if (data.enabled !== true) { revoke(); return; }', referral)
        self.assertIn('tab.hidden = true;', admin)
        self.assertIn('if (res.status === 401 || res.status === 403)', admin)

    @patch("web.web_referral_routes._auth_uid", return_value=123)
    @patch("web.web_referral_routes._rest")
    def test_disabled_member_has_no_link(self, rest, _uid):
        rest.return_value = [{"referral_code": "C" * 24, "enabled": False}]
        data = self.make_app().test_client().get("/api/web/referral").json
        self.assertEqual(data, {"enabled": False})
        self.assertNotIn("link", data)


if __name__ == "__main__":
    unittest.main()
