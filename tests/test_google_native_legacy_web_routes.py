"""Regression: Google can enter the SAME legacy Web only after verified dual identity.

The existing Telegram cookie is issued only from server-confirmed Google OAuth
+ a previously verified Telegram link + the CURRENT production Web lookup.
Google-only accounts MUST NOT be assigned fake Telegram IDs.
"""
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from flask import Flask
from web.google_native_legacy_web_routes import (
    bp, _verified_linked_telegram, _canonical_google_account,
    _config, COOKIE,
)
from web_v1_sessions import verify_session_ticket

SECRET = "test-secret-for-unified-google-Web-32-characters"
UID = 123456789
ACCOUNT = "2c2f5000-87e6-4e96-8200-676dc5ef1c19"
HOST = "cikgulaju-web.onrender.com"
CFG = {
    "origin": "https://" + HOST, "host": HOST,
    "supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co",
    "apikey": "sb_publishable_test_only", "staging_service_key": "secret_staging_test",
    "secret": SECRET,
}
IDENTITY = {
    "id": ACCOUNT, "email": "Teacher@example.com",
    "email_confirmed_at": "2026-11-07T11:00:00Z",
    "identities": [{"provider": "google"}],
}


class GoogleNativeWebTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        self.client = app.test_client()
        self.cfg = patch("web.google_native_legacy_web_routes._config",
                         return_value=CFG)
        self.cfg.start()
        self.addCleanup(self.cfg.stop)

    def _start(self):
        r = self.client.get("/api/web/google-native/start", base_url=CFG["origin"])
        self.assertEqual(r.status_code, 302)
        target = parse_qs(urlsplit(r.location).query)
        self.assertEqual(target["provider"], ["google"])
        callback = parse_qs(urlsplit(target["redirect_to"][0]).query)
        return callback["state"][0]

    def _callback(self, state, code="fake-code", *, accept=None):
        headers = {} if accept is None else {"Accept": accept}
        return self.client.get("/api/web/google-native/callback?state="+state+
                               "&code="+code, base_url=CFG["origin"], headers=headers)

    def test_google_linked_issues_exact_original_web_cookie(self):
        state = self._start()
        with (patch("web.google_native_legacy_web_routes._json",
                    side_effect=[{"access_token": "x"*70}, IDENTITY]) as exchange,
              patch("web.google_native_legacy_web_routes._verified_linked_telegram",
                    return_value=UID) as verified):
            response = self._callback(state)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.location, "/")
        self.assertEqual(exchange.call_count, 2)
        verified.assert_called_once_with(CFG, ACCOUNT, "teacher@example.com")
        cookie = self.client.get_cookie(COOKIE, domain=HOST)
        self.assertIsNotNone(cookie)
        self.assertEqual(verify_session_ticket(cookie.value, SECRET), UID)

    def test_unlinked_google_does_not_get_telegram_web_cookie(self):
        state = self._start()
        with (patch("web.google_native_legacy_web_routes._json",
                    side_effect=[{"access_token": "x"*70}, IDENTITY]),
              patch("web.google_native_legacy_web_routes._verified_linked_telegram",
                    return_value=None)):
            response = self._callback(state)
        self.assertEqual(response.status_code, 409)
        self.assertIsNone(self.client.get_cookie(COOKIE, domain=HOST))

    def test_google_email_unconfirmed_never_attempts_paid_lookup(self):
        state = self._start()
        invalid = {**IDENTITY, "email_confirmed_at": None}
        with (patch("web.google_native_legacy_web_routes._json",
                    side_effect=[{"access_token": "x"*70}, invalid]),
              patch("web.google_native_legacy_web_routes._verified_linked_telegram") as linked):
            response = self._callback(state)
        self.assertEqual(response.status_code, 503)
        self.assertIsNone(self.client.get_cookie(COOKIE, domain=HOST))
        linked.assert_not_called()

    def test_state_invalid_never_contacts_oauth_backend(self):
        self._start()
        with patch("web.google_native_legacy_web_routes._json") as exchange:
            response = self._callback("wrong-state")
        self.assertEqual(response.status_code, 401)
        exchange.assert_not_called()

    def test_legacy_web_account_required_for_linked_session(self):
        from web.google_native_legacy_web_routes import NativeGoogleLoginUnavailable
        with (patch("web.google_native_legacy_web_routes._canonical_google_account",
                    return_value=ACCOUNT),
              patch("web.google_native_legacy_web_routes.google_staging_account_profile",
                    return_value={"login_email":"teacher@example.com"}),
              patch("web.google_native_legacy_web_routes._link_status",
                    return_value={"linked":True,"staging_only":True,
                                  "telegram_user_id":str(UID)}),
              patch("web.google_native_legacy_web_routes.legacy_config",
                    return_value={"account_backend":"supabase"}) as conf,
              patch("web.google_native_legacy_web_routes._lookup",
                    return_value={"authenticated":True,"telegram_user_id":UID}) as lookup):
            resolved = _verified_linked_telegram(CFG,ACCOUNT,"teacher@example.com")
        self.assertEqual(resolved,UID)
        conf.assert_called_once()
        lookup.assert_called_once()

    def test_mapping_cannot_grant_access_for_wrong_telegram_account(self):
        from web.google_native_legacy_web_routes import NativeGoogleLoginUnavailable
        with (patch("web.google_native_legacy_web_routes._canonical_google_account",
                    return_value=ACCOUNT),
              patch("web.google_native_legacy_web_routes.google_staging_account_profile",
                    return_value={"login_email":"teacher@example.com"}),
              patch("web.google_native_legacy_web_routes._link_status",
                    return_value={"linked":True,"staging_only":True,
                                  "telegram_user_id":str(UID)}),
              patch("web.google_native_legacy_web_routes.legacy_config",
                    return_value={"account_backend":"supabase"}),
              patch("web.google_native_legacy_web_routes._lookup",
                    return_value={"authenticated":True,"telegram_user_id":UID+1})):
            with self.assertRaises(NativeGoogleLoginUnavailable):
                _verified_linked_telegram(CFG,ACCOUNT,"teacher@example.com")

    def test_oauth_binding_does_not_trust_email_only(self):
        from web.google_native_legacy_web_routes import NativeGoogleLoginUnavailable
        with patch("web.google_native_legacy_web_routes._json",
                   return_value=[{"account_id":ACCOUNT,"subject":ACCOUNT}]):
            self.assertEqual(_canonical_google_account(CFG,ACCOUNT),ACCOUNT)
        with patch("web.google_native_legacy_web_routes._json",
                   return_value=[]):
            with self.assertRaises(NativeGoogleLoginUnavailable):
                _canonical_google_account(CFG,ACCOUNT)

    def test_native_login_disabled_unless_opted_in(self):
        with patch("web.google_native_legacy_web_routes._config", return_value=None):
            r=self.client.get("/api/web/google-native/start",base_url=CFG["origin"])
            self.assertEqual(r.status_code,503)


if __name__ == "__main__":
    unittest.main()
