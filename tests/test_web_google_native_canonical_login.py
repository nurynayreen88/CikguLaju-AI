"""Native CikguLaju Web Google OAuth tests: no mock production writes.

Both providers enter the SAME production Supabase account source. Google-only
users NEVER receive a fabricated Telegram ID or the legacy v1 browser cookie.
"""
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from flask import Flask
from web.google_native_canonical_login_routes import bp
from web_v1_canonical_sessions import COOKIE as GOOGLE_COOKIE, verify_google_principal_ticket
from web_v1_telegram_auth_routes import COOKIE as LEGACY_COOKIE
from web_v1_sessions import issue_session_ticket, verify_session_ticket

SECRET="canonical-test-session-secret-with-enough-characters"
HOST="cikgulaju-web.onrender.com"
BASE="https://"+HOST
ACC="1a267083-8511-4587-a585-857fe35f4a14"
SUB="2c2f5000-87e6-4e96-8200-676dc5ef1c19"
CFG={"origin":BASE,"apikey":"sb_publishable_private_test_client_key_123",
     "secret":SECRET,"supabase_url":"https://soxakntcanbycjoygrcx.supabase.co",
     "supabase_key":"sb_secret_test_private_service_role_abcdef",
     "account_backend":"supabase"}
ID={"id":SUB,"email":"Teacher@example.com",
    "email_confirmed_at":"2026-11-07T12:00:00Z",
    "identities":[{"provider":"google","identity_data":{"email":"Teacher@example.com"}}]}
GOOGLE_ONLY={"account_id":ACC,"login_id":"teacher@example.com",
             "legacy_telegram_user_id":None,"google_only_trial_remaining":10}


class GoogleNativeCanonicalTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()
        enabled=patch("web.google_native_canonical_login_routes._config",return_value=CFG)
        enabled.start()
        self.addCleanup(enabled.stop)

    def _start(self):
        res=self.client.get("/api/auth/google-native/start",base_url=BASE)
        self.assertEqual(res.status_code,302)
        parsed=urlsplit(res.location)
        self.assertEqual(parsed.netloc,"soxakntcanbycjoygrcx.supabase.co")
        args=parse_qs(parsed.query)
        self.assertEqual(args["provider"],["google"])
        self.assertEqual(args["code_challenge_method"],["s256"])
        return parse_qs(urlsplit(args["redirect_to"][0]).query)["state"][0]

    def _callback(self,state):
        return self.client.get("/api/auth/google-native/callback?state="+state+
                               "&code=once-only-test",base_url=BASE)

    def test_verified_google_only_creates_v2_cookie_not_telegram_cookie(self):
        state=self._start()
        with (patch("web.google_native_canonical_login_routes._read_json",
                    side_effect=[{"access_token":"x"*60},ID]),
              patch("web.google_native_canonical_login_routes.register_verified_google_principal",
                    return_value=ACC) as register,
              patch("web.google_native_canonical_login_routes.read_google_principal",
                    return_value=GOOGLE_ONLY) as lookup):
            reply=self._callback(state)
        self.assertEqual(reply.status_code,303)
        self.assertEqual(reply.location,"/google-account")
        ticket=self.client.get_cookie(GOOGLE_COOKIE,domain=HOST)
        self.assertIsNotNone(ticket)
        self.assertEqual(verify_google_principal_ticket(ticket.value,SECRET),ACC)
        self.assertIsNone(self.client.get_cookie(LEGACY_COOKIE,domain=HOST))
        register.assert_called_once_with(CFG,ID)
        lookup.assert_called_once_with(CFG,ACC)

    def test_existing_telegram_link_can_reuse_original_web_session(self):
        state=self._start()
        linked={**GOOGLE_ONLY,"legacy_telegram_user_id":123456789,
                "google_only_trial_remaining":None}
        with (patch("web.google_native_canonical_login_routes._read_json",
                    side_effect=[{"access_token":"x"*60},ID]),
              patch("web.google_native_canonical_login_routes.register_verified_google_principal",
                    return_value=ACC),
              patch("web.google_native_canonical_login_routes.read_google_principal",
                    return_value=linked),
              patch("web.google_native_canonical_login_routes._lookup",
                    return_value={"authenticated":True,"telegram_user_id":123456789}) as read):
            reply=self._callback(state)
        self.assertEqual(reply.status_code,303)
        self.assertEqual(reply.location,"/")
        original=self.client.get_cookie(LEGACY_COOKIE,domain=HOST)
        self.assertEqual(verify_session_ticket(original.value,SECRET),123456789)
        self.assertIsNotNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))
        read.assert_called_once_with(CFG,123456789)

    def test_two_independently_verified_sessions_can_coexist_before_explicit_link(self):
        self.client.set_cookie(LEGACY_COOKIE,
                               issue_session_ticket(987654321,SECRET),domain=HOST)
        state=self._start()
        with (patch("web.google_native_canonical_login_routes._read_json",
                    side_effect=[{"access_token":"x"*60},ID]),
              patch("web.google_native_canonical_login_routes.register_verified_google_principal",
                    return_value=ACC),
              patch("web.google_native_canonical_login_routes.read_google_principal",
                    return_value=GOOGLE_ONLY)):
            reply=self._callback(state)
        self.assertEqual(reply.status_code,303)
        self.assertEqual(reply.location,"/google-account")
        self.assertIsNotNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))
        # Original authenticated Telegram cookie remains a different identity
        # until the user explicitly previews and confirms account linking.
        original=self.client.get_cookie(LEGACY_COOKIE,domain=HOST)
        self.assertEqual(verify_session_ticket(original.value,SECRET),987654321)

    def test_conflicting_existing_link_never_switches_original_telegram_identity(self):
        self.client.set_cookie(LEGACY_COOKIE,
                               issue_session_ticket(987654321,SECRET),domain=HOST)
        state=self._start()
        linked={**GOOGLE_ONLY,"legacy_telegram_user_id":123456789,
                "google_only_trial_remaining":None}
        with (patch("web.google_native_canonical_login_routes._read_json",
                    side_effect=[{"access_token":"x"*60},ID]),
              patch("web.google_native_canonical_login_routes.register_verified_google_principal",
                    return_value=ACC),
              patch("web.google_native_canonical_login_routes.read_google_principal",
                    return_value=linked)):
            reply=self._callback(state)
        self.assertEqual(reply.status_code,409)
        self.assertIsNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))

    def test_bad_state_never_issues_account(self):
        self._start()
        with patch("web.google_native_canonical_login_routes._read_json") as exchange:
            reply=self._callback("not-the-signed-state")
        self.assertEqual(reply.status_code,401)
        exchange.assert_not_called()

    def test_unconfirmed_google_cannot_access_canonical_account(self):
        state=self._start()
        with (patch("web.google_native_canonical_login_routes._read_json",
                    side_effect=[{"access_token":"x"*60},
                                 {**ID,"email_confirmed_at":None}]),
              patch("web.google_native_canonical_login_routes.register_verified_google_principal") as register):
            reply=self._callback(state)
        self.assertEqual(reply.status_code,503)
        register.assert_not_called()
        self.assertIsNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))

    def test_google_session_reads_current_canonical_quota(self):
        self.client.set_cookie(GOOGLE_COOKIE,
                               __import__("web_v1_canonical_sessions").issue_google_principal_ticket(
                                   ACC,SECRET),domain=HOST)
        with (patch("web.google_native_canonical_login_routes.read_google_principal",
                    return_value=GOOGLE_ONLY),
              patch("web.google_native_canonical_login_routes.canonical_rph_access",
                    return_value={"rph_access_mode":"trial",
                                  "rph_trial_remaining":8,"account_id":ACC})):
            reply=self.client.get("/api/auth/google-native/session",base_url=BASE)
        self.assertEqual(reply.status_code,200)
        self.assertEqual(reply.json["login_id"],"teacher@example.com")
        self.assertEqual(reply.json["rph_trial_remaining"],8)
        self.assertFalse(reply.json["linked_telegram"])
        self.assertEqual(reply.headers["Cache-Control"],"no-store, private")

    def test_logout_is_origin_guarded_and_revokes_linked_legacy_session(self):
        from web_v1_canonical_sessions import issue_google_principal_ticket
        self.client.set_cookie(GOOGLE_COOKIE,
                               issue_google_principal_ticket(ACC,SECRET),domain=HOST)
        self.client.set_cookie(LEGACY_COOKIE,
                               issue_session_ticket(123456789,SECRET),domain=HOST)
        bad=self.client.post("/api/auth/google-native/logout",base_url=BASE,
                             headers={"Origin":"https://evil.example"})
        self.assertEqual(bad.status_code,403)
        self.assertIsNotNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))
        self.assertIsNotNone(self.client.get_cookie(LEGACY_COOKIE,domain=HOST))
        good=self.client.post("/api/auth/google-native/logout",base_url=BASE,
                              headers={"Origin":BASE,"Sec-Fetch-Site":"same-origin"})
        self.assertEqual(good.status_code,200)
        self.assertIsNone(self.client.get_cookie(GOOGLE_COOKIE,domain=HOST))
        self.assertIsNone(self.client.get_cookie(LEGACY_COOKIE,domain=HOST))

    def test_google_logout_without_google_session_preserves_independent_telegram(self):
        self.client.set_cookie(LEGACY_COOKIE,
                               issue_session_ticket(123456789,SECRET),domain=HOST)
        good=self.client.post("/api/auth/google-native/logout",base_url=BASE,
                              headers={"Origin":BASE,"Sec-Fetch-Site":"same-origin"})
        self.assertEqual(good.status_code,200)
        original=self.client.get_cookie(LEGACY_COOKIE,domain=HOST)
        self.assertIsNotNone(original)
        self.assertEqual(verify_session_ticket(original.value,SECRET),123456789)

    def test_dashboard_displays_verified_email_login_id_and_real_trial_balance(self):
        with (patch("web.google_native_canonical_login_routes._existing_google_account",
                    return_value=GOOGLE_ONLY),
              patch("web.google_native_canonical_login_routes.canonical_rph_access",
                    return_value={"rph_access_mode":"trial",
                                  "rph_trial_remaining":8,"account_id":ACC})):
            page=self.client.get("/google-account",base_url=BASE)
        self.assertEqual(page.status_code,200)
        self.assertIn(b"ID log masuk Google",page.data)
        self.assertIn(b"teacher@example.com",page.data)
        self.assertIn(b"Baki janaan percuma: 8",page.data)
        self.assertIn(b'href="/google-rph"',page.data)
        self.assertEqual(page.headers["Cache-Control"],"no-store, private")

    def test_paid_linked_google_uses_original_telegram_web_with_no_trial_badge(self):
        linked={**GOOGLE_ONLY,"legacy_telegram_user_id":123456789,
                "google_only_trial_remaining":None}
        with (patch("web.google_native_canonical_login_routes._existing_google_account",
                    return_value=linked),
              patch("web.google_native_canonical_login_routes.canonical_rph_access",
                    return_value={"rph_access_mode":"paid",
                                  "rph_trial_remaining":8,"account_id":ACC})):
            page=self.client.get("/google-account",base_url=BASE)
        self.assertEqual(page.status_code,200)
        self.assertIn(b"Akses RPH tanpa had",page.data)
        self.assertNotIn(b"Baki janaan percuma",page.data)
        self.assertIn(b'href="/"',page.data)

    def test_login_option_visible_only_when_original_web_google_is_enabled(self):
        with patch.dict("os.environ", {"CIKGULAJU_NATIVE_GOOGLE_RPH_ENABLED":"1"}):
            yes=self.client.get("/api/auth/google-native/options",base_url=BASE)
            self.assertEqual(yes.status_code,200)
            self.assertTrue(yes.json["google_available"])
            with patch("web.google_native_canonical_login_routes._config",return_value=None):
                no=self.client.get("/api/auth/google-native/options",base_url=BASE)
                self.assertFalse(no.json["google_available"])
        with patch.dict("os.environ", {"CIKGULAJU_NATIVE_GOOGLE_RPH_ENABLED":"0"}):
            blocked=self.client.get("/api/auth/google-native/options",base_url=BASE)
            self.assertFalse(blocked.json["google_available"])

    def test_flag_off_returns_503(self):
        with patch("web.google_native_canonical_login_routes._config",return_value=None):
            self.assertEqual(self.client.get("/google-login",base_url=BASE).status_code,503)
            self.assertEqual(self.client.get("/api/auth/google-native/start",
                                             base_url=BASE).status_code,503)


if __name__ == "__main__":
    unittest.main()
