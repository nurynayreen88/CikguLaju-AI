"""Isolated Telegram sign-in for an ALREADY linked staging account.

Tests enforce separation from Google OAuth, private admin sessions, and
production entitlements. No live Telegram or Google credentials required.
"""
import hashlib
import hmac
import time
import unittest
from unittest.mock import patch

from flask import Flask

from web.google_telegram_signin_staging_routes import (
    bp, TELEGRAM_COOKIE, _issue_ticket, _verify_ticket, _linked_account,
)
from web.google_auth_staging_routes import TICKET_COOKIE

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
UID = 123456789
TOKEN = "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
BOT = (TOKEN, "CikguLajuStagingTestBot")
CFG = {
    "origin": "https://staging.example.org",
    "secret": "s" * 48,
    "supabase_url": "https://isolated.supabase.co",
    "staging_service_key": "sb_secret_" + "a" * 40,
}
PROFILE = {"display_name": "Cikgu Ujian", "trial_remaining": 9}


def signed_proof(uid=UID, now=None):
    values = {"id": str(uid), "auth_date": str(int(time.time() if now is None else now)),
              "first_name": "Cikgu"}
    check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    values["hash"] = hmac.new(hashlib.sha256(TOKEN.encode()).digest(),
                             check.encode(), hashlib.sha256).hexdigest()
    return values


class LinkedTelegramStagingLoginTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp)
        self.client = app.test_client()
        self.mapped = ACCOUNT
        self.lookup_count = 0
        self.profile_count = 0

        def lookup(cfg, uid):
            self.assertEqual(cfg, CFG)
            self.assertEqual(uid, UID)
            self.lookup_count += 1
            return self.mapped

        def get_profile(cfg, account_id):
            self.assertEqual(cfg, CFG)
            self.assertEqual(account_id, ACCOUNT)
            self.profile_count += 1
            return PROFILE.copy()

        for p in (
            patch("web.google_telegram_signin_staging_routes._link_config",
                  return_value=(CFG, BOT)),
            patch("web.google_telegram_signin_staging_routes._linked_account",
                  new=lookup),
            patch("web.google_telegram_signin_staging_routes.google_staging_account_profile",
                  new=get_profile),
        ):
            p.start()
            self.addCleanup(p.stop)

    def post_login(self, proof=None, *, origin=CFG["origin"]):
        return self.client.post("/api/auth/staging/telegram/login",
            json={"telegram_auth": proof if proof is not None else signed_proof()},
            headers={"Origin": origin, "Sec-Fetch-Site": "same-origin"})

    def test_authenticated_widget_reads_same_staging_trial_balance(self):
        first = self.client.get("/api/auth/staging/telegram/profile")
        self.assertEqual(first.status_code, 401)
        login = self.post_login()
        self.assertEqual(login.status_code, 200, login.json)
        self.assertEqual(login.json["provider"], "telegram")
        self.assertEqual(login.json["trial_remaining"], 9)
        self.assertFalse(login.json["entitlements_shared"])
        self.assertIn(TELEGRAM_COOKIE + "=", login.headers["Set-Cookie"])
        self.assertNotIn(TICKET_COOKIE, login.headers["Set-Cookie"])
        self.assertIn("HttpOnly", login.headers["Set-Cookie"])
        self.assertIn("Secure", login.headers["Set-Cookie"])
        second = self.client.get("/api/auth/staging/telegram/profile")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json["display_name"], PROFILE["display_name"])
        self.assertEqual(second.json["trial_remaining"], 9)
        self.assertFalse(second.json["entitlements_shared"])
        self.assertEqual(self.profile_count, 2)  # Read-only shared record.
        self.assertEqual(self.lookup_count, 2)

    def test_unlinked_identity_cannot_create_account_or_log_in(self):
        self.mapped = None
        res = self.post_login()
        self.assertEqual(res.status_code, 403)
        self.assertNotIn(TELEGRAM_COOKIE + "=", res.headers.get("Set-Cookie", ""))
        self.assertEqual(self.client.get(
            "/api/auth/staging/telegram/profile").status_code, 401)

    def test_forgery_expiration_and_cross_site_denied(self):
        forged = signed_proof()
        forged["id"] = str(UID + 1)
        self.assertEqual(self.post_login(forged).status_code, 403)
        self.assertEqual(self.post_login(signed_proof(
            now=time.time() - 130)).status_code, 403)
        self.assertEqual(self.post_login(origin="https://attacker.example").status_code, 403)
        self.assertEqual(self.lookup_count, 0)

    def test_expired_or_modified_teacher_cookie_rejected(self):
        expired = _issue_ticket(UID, CFG["secret"], now=100)
        self.assertIsNone(_verify_ticket(expired, CFG["secret"], now=3701))
        self.assertEqual(_verify_ticket(expired, CFG["secret"], now=3500), UID)
        self.assertIsNone(_verify_ticket(expired[:-1] + "a", CFG["secret"], now=200))
        self.assertIsNone(_verify_ticket(expired, "other" * 10, now=200))
        self.client.set_cookie(TELEGRAM_COOKIE, expired, domain="localhost")
        self.assertEqual(self.client.get(
            "/api/auth/staging/telegram/profile").status_code, 401)
        self.assertEqual(self.lookup_count, 0)

    def test_logout_requires_same_origin_and_only_clears_telegram(self):
        self.assertEqual(self.post_login().status_code, 200)
        path = "/api/auth/staging/telegram/logout"
        self.assertEqual(self.client.post(path, headers={
            "Origin": "https://attacker.example"}).status_code, 403)
        self.assertEqual(self.client.get(
            "/api/auth/staging/telegram/profile").status_code, 200)
        done = self.client.post(path, headers={
            "Origin": CFG["origin"], "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(done.status_code, 200)
        self.assertIn(TELEGRAM_COOKIE + "=;", done.headers["Set-Cookie"])
        self.assertNotIn(TICKET_COOKIE, done.headers["Set-Cookie"])
        self.assertEqual(self.client.get(
            "/api/auth/staging/telegram/profile").status_code, 401)

    def test_anonymous_widget_name_is_public_but_profile_remains_private(self):
        bot = self.client.get("/api/auth/staging/telegram/bot")
        self.assertEqual(bot.status_code, 200)
        self.assertEqual(bot.json["bot_username"], BOT[1])
        self.assertNotIn("token", str(bot.json).lower())
        self.assertEqual(self.client.get(
            "/api/auth/staging/telegram/profile").status_code, 401)
        page = self.client.get("/google-staging-telegram")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'onStagingTelegramLogin', page.data)

    def test_safe_feature_off(self):
        with patch("web.google_telegram_signin_staging_routes._link_config",
                   return_value=None):
            self.assertEqual(self.client.get("/google-staging-telegram").status_code, 503)
            self.assertEqual(self.client.get(
                "/api/auth/staging/telegram/bot").status_code, 503)
            self.assertEqual(self.post_login().status_code, 503)
            self.assertEqual(self.client.get(
                "/api/auth/staging/telegram/profile").status_code, 503)

    def test_telegram_lookup_requires_exact_bidirectional_link_and_google(self):
        # Mock private staging REST replies; never read production data.
        path = "web.google_telegram_signin_staging_routes._read_json"
        with patch(path, side_effect=[
            [{"account_id": ACCOUNT, "subject": str(UID)}],
            [{"id": ACCOUNT, "legacy_telegram_user_id": UID}],
            [{"account_id": ACCOUNT}],
        ]) as reader:
            actual = _linked_account(CFG, UID)
            self.assertEqual(actual, ACCOUNT)
            self.assertEqual(reader.call_count, 3)
        from web.google_telegram_link_staging_routes import StagingLinkUnavailable
        with patch(path, side_effect=[
            [{"account_id": ACCOUNT, "subject": str(UID)}],
            [{"id": ACCOUNT, "legacy_telegram_user_id": UID + 1}],
            [{"account_id": ACCOUNT}],
        ]):
            with self.assertRaises(StagingLinkUnavailable):
                _linked_account(CFG, UID)
        with patch(path, return_value=[]):
            self.assertIsNone(_linked_account(CFG, UID))


if __name__ == "__main__":
    unittest.main()
