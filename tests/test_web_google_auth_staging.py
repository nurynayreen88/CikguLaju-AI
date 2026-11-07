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
            "CIKGULAJU_GOOGLE_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test_not_real",
            "CIKGULAJU_WEB_SESSION_SECRET": SECRET,
            "CIKGULAJU_GOOGLE_STAGING_ORIGIN": "https://staging.example.test",
            "CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST": "staging.example.test",
            "SUPABASE_URL": "https://example.supabase.co",
        })
        self.env.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(bp)
        self.client = self.app.test_client()
        self.base = "https://staging.example.test"

    def tearDown(self):
        self.env.stop()

    def _start(self):
        start = self.client.get("/api/auth/google/start", base_url=self.base)
        self.assertEqual(start.status_code, 302)
        query = parse_qs(urlsplit(start.headers["Location"]).query)
        self.assertEqual(query["provider"], ["google"])
        self.assertEqual(query["code_challenge_method"], ["s256"])
        callback = parse_qs(urlsplit(query["redirect_to"][0]).query)
        return callback["state"][0], start

    def test_staging_disabled_fails_closed(self):
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "0"}):
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
        with patch("web.google_auth_staging_routes._json_response",
                   side_effect=[{"access_token": "x" * 70},
                                {"id": SUBJECT, "identities": [{"provider": "google"}]}]) as call:
            r = self.client.get("/api/auth/google/callback?state=" + state + "&code=test",
                                base_url=self.base)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(call.call_count, 2)
        self.assertTrue(r.json["google_verified"])
        self.assertFalse(r.json["dashboard_access"])
        self.assertNotIn("cikgulaju_web_v1_session", "\n".join(r.headers.getlist("Set-Cookie")))
        status = self.client.get("/api/auth/google/status", base_url=self.base)
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json["dashboard_access"])
        out = self.client.post("/api/auth/google/logout", base_url=self.base)
        self.assertEqual(out.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/google/status",
                                         base_url=self.base).status_code, 401)

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
