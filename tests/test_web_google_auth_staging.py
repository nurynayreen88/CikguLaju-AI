"""Regression tests for independent, staging-only Google identity verification."""
import os
import unittest
import uuid
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from flask import Flask
from web.google_auth_staging_routes import bp, _seal_state, _unseal_state
from web_google_identity_sessions import (
    issue_google_identity_ticket, verify_google_identity_ticket,
)
from web_v1_sessions import verify_session_ticket
from web.google_account_store import GoogleAccountUnavailable, verified_google_email


SECRET = "staging-unit-test-session-secret-32-chars-minimum"
SUBJECT = "2c2f5000-87e6-4e96-8200-676dc5ef1c19"


class GoogleTickets(unittest.TestCase):
    def test_valid_and_expired(self):
        ticket = issue_google_identity_ticket(SUBJECT, SECRET, now=1000)
        self.assertEqual(verify_google_identity_ticket(ticket, SECRET, now=1200), SUBJECT)
        self.assertIsNone(verify_google_identity_ticket(ticket, SECRET, now=4601))
        self.assertIsNone(verify_google_identity_ticket(ticket, SECRET, now=999))

    def test_tampering_and_legacy_must_fail(self):
        ticket = issue_google_identity_ticket(SUBJECT, SECRET, now=1000)
        self.assertIsNone(verify_google_identity_ticket(ticket + "f", SECRET, now=1001))
        self.assertIsNone(verify_google_identity_ticket(ticket, SECRET + "wrong", now=1001))
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1001))
        with self.assertRaises(ValueError):
            issue_google_identity_ticket("an-email@example.com", SECRET)

    def test_state_signed_and_expiring(self):
        verifier = "A" * 64
        state = "a" * 32
        with patch("web.google_auth_staging_routes.time.time", return_value=300):
            cookie = _seal_state(verifier, state, 200, SECRET)
            self.assertEqual(_unseal_state(cookie, SECRET), (verifier, state))
        with patch("web.google_auth_staging_routes.time.time", return_value=501):
            self.assertIsNone(_unseal_state(cookie, SECRET))
        self.assertIsNone(_unseal_state(cookie[:-1] + "0", SECRET + "different"))


class GoogleStagingRoutes(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "1",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test_not_real",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY": "staging-only-service-key-placeholder",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL": "https://abcdefghijklmnopqrst.supabase.co",
            "CIKGULAJU_GOOGLE_STAGING_PROJECT_REF": "abcdefghijklmnopqrst",
            "CIKGULAJU_GOOGLE_PRODUCTION_PROJECT_REF": "productionref1234567",
            "CIKGULAJU_WEB_SESSION_SECRET": SECRET,
            "CIKGULAJU_GOOGLE_STAGING_ORIGIN": "https://staging.example.test",
            "CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST": "staging.example.test",
            "SUPABASE_URL": "https://production.supabase.co",
        })
        self.env.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(bp)
        self.client = self.app.test_client()
        self.base = "https://staging.example.test"
        # Callback persists the verified email via private service credentials.
        self.email_store = patch("web.google_auth_staging_routes.save_verified_google_email")
        self.saved_email = self.email_store.start()
        self.addCleanup(self.email_store.stop)

    def tearDown(self):
        self.env.stop()

    def _start(self):
        start = self.client.get("/api/auth/google/start", base_url=self.base)
        self.assertEqual(start.status_code, 302)
        query = parse_qs(urlsplit(start.headers["Location"]).query)
        self.assertEqual(query["provider"], ["google"])
        self.assertEqual(urlsplit(start.headers["Location"]).netloc, "abcdefghijklmnopqrst.supabase.co")
        self.assertEqual(query["code_challenge_method"], ["s256"])
        callback = parse_qs(urlsplit(query["redirect_to"][0]).query)
        return callback["state"][0], start

    def test_staging_login_page_is_behind_flag(self):
        r = self.client.get("/google-staging-login", base_url=self.base)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Cache-Control"], "no-store")
        self.assertIn(b"Teruskan dengan Google", r.data)
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "0"}):
            page = self.client.get("/google-staging-login", base_url=self.base)
            self.assertEqual(page.status_code, 503)
            self.assertTrue(page.mimetype == "text/html")
            self.assertIn(b"Google sedang disediakan", page.data)
            self.assertNotIn(b'href="/api/auth/google/start"', page.data)
            self.assertEqual(page.headers["Cache-Control"], "no-store")

    def test_staging_disabled_fails_closed(self):
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "0"}):
            r = self.client.get("/api/auth/google/start", base_url=self.base)
            self.assertEqual(r.status_code, 503)

    def test_rejects_using_production_supabase_database(self):
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL": "https://production.supabase.co"}):
            r = self.client.get("/api/auth/google/start", base_url=self.base)
        self.assertEqual(r.status_code, 503)

    def test_ref_mismatch_disables_staging_before_credentials_are_sent(self):
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_STAGING_PROJECT_REF": "zzzzzzzzzzzzzzzzzzzz"}):
            r = self.client.get("/api/auth/google/start", base_url=self.base)
            self.assertEqual(r.status_code, 503)

    def test_no_host_spoofing(self):
        r = self.client.get("/api/auth/google/start", base_url="https://other.example.test")
        self.assertEqual(r.status_code, 503)

    def test_missing_state_never_exchanges_code(self):
        state, _ = self._start()
        with patch("web.google_auth_staging_routes._json_response") as exchange:
            r = self.client.get("/api/auth/google/callback?state=bad&code=fake",
                                base_url=self.base)
            self.assertEqual(r.status_code, 401)
            exchange.assert_not_called()
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 401)

    def test_good_google_identity_only_grants_isolated_ticket(self):
        state, _ = self._start()
        with (
            patch("web.google_auth_staging_routes._json_response",
                  side_effect=[{"access_token": "x" * 70},
                               {"id": SUBJECT, "email": "Guru.Ujian@example.com",
                                "email_confirmed_at": "2026-11-07T10:00:00Z",
                                "identities": [{"provider": "google"}]}]) as call,
            patch("web.google_auth_staging_routes.ensure_google_staging_account",
                  return_value=SUBJECT) as create,
        ):
            r = self.client.get("/api/auth/google/callback?state=" + state + "&code=test",
                                base_url=self.base)
            create.assert_called_once()
            self.saved_email.assert_called_once()
            self.assertEqual(self.saved_email.call_args.args[2], "guru.ujian@example.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(call.call_count, 2)
        self.assertTrue(r.json["google_verified"])
        self.assertFalse(r.json["dashboard_access"])
        self.assertNotIn("cikgulaju_web_v1_session", "\n".join(r.headers.getlist("Set-Cookie")))
        status = self.client.get("/api/auth/google/status", base_url=self.base)
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json["dashboard_access"])
        # A forged cross-origin POST must not change the Google-only session.
        malicious = self.client.post("/api/auth/google/logout",
                                     base_url=self.base,
                                     headers={"Origin": "https://attacker.example",
                                              "Sec-Fetch-Site": "cross-site"})
        self.assertEqual(malicious.status_code, 403)
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/google/logout",
                                          base_url=self.base).status_code, 403)
        out = self.client.post("/api/auth/google/logout", base_url=self.base,
                               headers={"Origin": self.base,
                                        "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(out.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 401)

    def test_unavailable_staging_account_fails_closed(self):
        state, _ = self._start()
        with (
            patch("web.google_auth_staging_routes._json_response",
                  side_effect=[{"access_token": "x" * 70},
                               {"id": SUBJECT, "email": "Guru.Ujian@example.com",
                                "email_confirmed_at": "2026-11-07T10:00:00Z",
                                "identities": [{"provider": "google"}]}]),
            patch("web.google_auth_staging_routes.ensure_google_staging_account",
                  side_effect=RuntimeError("staging down")),
        ):
            r = self.client.get("/api/auth/google/callback?state=" + state + "&code=test",
                                base_url=self.base)
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 401)

    def test_browser_redirects_to_staging_account_page(self):
        state, _ = self._start()
        with (
            patch("web.google_auth_staging_routes._json_response",
                  side_effect=[{"access_token":"x"*70},
                               {"id": SUBJECT, "email": "Guru.Ujian@example.com",
                                "email_confirmed_at": "2026-11-07T10:00:00Z",
                                "identities": [{"provider": "google"}]}]),
            patch("web.google_auth_staging_routes.ensure_google_staging_account",
                  return_value=SUBJECT),
        ):
            r=self.client.get("/api/auth/google/callback?state="+state+"&code=test",
                              base_url=self.base,headers={"Accept":"text/html"})
        self.assertEqual(r.status_code,303)
        self.assertEqual(r.location,self.base+"/google-staging-account")
        self.assertIn("cikgulaju_google_staging_ticket", "\\n".join(r.headers.getlist("Set-Cookie")))

    def test_real_browser_accept_header_redirects(self):
        state, _ = self._start()
        # Chrome-like Accept contains */*; JSON can be wildcard-accepted.
        # The user still needs to reach the actual staging Web screen.
        with (
            patch("web.google_auth_staging_routes._json_response",
                  side_effect=[{"access_token": "x" * 70},
                               {"id": SUBJECT, "email": "Guru.Ujian@example.com",
                                "email_confirmed_at": "2026-11-07T10:00:00Z",
                                "identities": [{"provider": "google"}]}]),
            patch("web.google_auth_staging_routes.ensure_google_staging_account",
                  return_value=SUBJECT),
        ):
            r = self.client.get(
                "/api/auth/google/callback?state=" + state + "&code=test",
                base_url=self.base,
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(r.location, self.base + "/google-staging-account")

    def test_profile_rejects_anonymous_and_query_identity_override(self):
        unauthorized = self.client.get("/api/auth/google/profile", base_url=self.base)
        self.assertEqual(unauthorized.status_code, 401)
        page = self.client.get("/google-staging-account", base_url=self.base)
        self.assertEqual(page.status_code, 303)
        self.assertEqual(page.location, "/google-staging-login")
        self.client.set_cookie(
            "cikgulaju_google_staging_ticket",
            issue_google_identity_ticket(SUBJECT, SECRET),
            domain="staging.example.test")
        with patch("web.google_auth_staging_routes.google_staging_account_profile") as read:
            invalid = self.client.get(
                "/api/auth/google/profile?account_id=another-account",
                base_url=self.base)
            self.assertEqual(invalid.status_code, 401)
            read.assert_not_called()

    def test_verified_google_account_profile_is_read_only(self):
        self.client.set_cookie(
            "cikgulaju_google_staging_ticket",
            issue_google_identity_ticket(SUBJECT, SECRET),
            domain="staging.example.test")
        with patch("web.google_auth_staging_routes.google_staging_account_profile",
                   return_value={"display_name": "Cikgu Ujian",
                                 "trial_remaining": 10, "login_email": "guru.ujian@example.com"}) as read:
            reply = self.client.get("/api/auth/google/profile", base_url=self.base)
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json["display_name"], "Cikgu Ujian")
        self.assertEqual(reply.json["trial_remaining"], 10)
        self.assertEqual(reply.json["login_id"], "guru.ujian@example.com")
        self.assertFalse(reply.json["rph_generation_enabled"])
        self.assertFalse(reply.json["real_payments_enabled"])
        self.assertEqual(reply.headers["Cache-Control"], "no-store, private")
        read.assert_called_once()
        self.assertEqual(read.call_args.args[1], SUBJECT)
        html = self.client.get("/google-staging-account", base_url=self.base)
        self.assertEqual(html.status_code, 200)
        self.assertIn(b"Kuota percubaan", html.data)
        self.assertIn(b"/api/auth/google/logout", html.data)
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "0"}):
            disabled = self.client.get("/api/auth/google/profile", base_url=self.base)
        self.assertEqual(disabled.status_code, 503)

    def test_profile_database_failure_never_exposes_user_data(self):
        self.client.set_cookie(
            "cikgulaju_google_staging_ticket",
            issue_google_identity_ticket(SUBJECT, SECRET),
            domain="staging.example.test")
        with patch("web.google_auth_staging_routes.google_staging_account_profile",
                   side_effect=GoogleAccountUnavailable("backend-down")):
            fail = self.client.get("/api/auth/google/profile", base_url=self.base)
        self.assertEqual(fail.status_code, 503)
        self.assertNotIn("backend-down", fail.get_data(as_text=True))


    def test_unconfirmed_email_cannot_be_used_as_login_id(self):
        state, _ = self._start()
        with patch("web.google_auth_staging_routes._json_response",
                   side_effect=[{"access_token": "x" * 70},
                                {"id": SUBJECT, "email": "unverified@example.com",
                                 "email_confirmed_at": None,
                                 "identities": [{"provider": "google"}]}]):
            result = self.client.get("/api/auth/google/callback?state=" + state + "&code=test",
                                     base_url=self.base)
        self.assertEqual(result.status_code, 503)
        self.saved_email.assert_not_called()

    def test_verified_email_normalization_and_spoofing_rejection(self):
        identity = {"email": "Teacher+One@Example.COM",
                    "email_confirmed_at": "2026-11-07T10:00:00Z",
                    "identities": [{"provider": "google"}]}
        self.assertEqual(verified_google_email(identity), "teacher+one@example.com")
        with self.assertRaises(ValueError):
            verified_google_email({**identity, "email": "not-an-email"})
        with self.assertRaises(ValueError):
            verified_google_email({**identity, "identities": [{"provider": "email"}]})

    def test_wrong_provider_does_not_grant_ticket(self):
        state, _ = self._start()
        with patch("web.google_auth_staging_routes._json_response",
                   side_effect=[{"access_token": "x" * 70},
                                {"id": SUBJECT, "identities": [{"provider": "email"}]}]):
            r = self.client.get("/api/auth/google/callback?state=" + state + "&code=test",
                                base_url=self.base)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 401)


if __name__ == "__main__":
    unittest.main()
