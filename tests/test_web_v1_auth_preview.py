"""Flask test-client checks for isolated Telegram login callback."""
import hashlib
import hmac
import os
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from web_v1_auth_preview import create_auth_preview_app

TOKEN = "12345:test-only"


def sign(fields):
    data = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    key = hashlib.sha256(TOKEN.encode()).digest()
    return {**fields, "hash": hmac.new(key, data.encode(), hashlib.sha256).hexdigest()}


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_auth_preview_app(secret_key="test-session-secret", testing=True)
        self.client = self.app.test_client()
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_TELEGRAM_BOT_USERNAME": "CikguLajuTestBot",
            "CIKGULAJU_WEB_TELEGRAM_BOT_TOKEN": TOKEN,
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_login_requires_signed_identity_and_state(self):
        page = self.client.get("/web/auth/login")
        self.assertEqual(page.status_code, 200)
        with self.client.session_transaction() as sess:
            nonce = sess["web_auth_nonce"]
        signed = sign({"id": "123456", "auth_date": str(int(time.time()))})
        signed["state"] = nonce
        response = self.client.get("/web/auth/callback", query_string=signed)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/web/auth/whoami").json["telegram_user_id"], 123456)

    def test_unsigned_id_rejected(self):
        self.client.get("/web/auth/login")
        with self.client.session_transaction() as sess:
            nonce = sess["web_auth_nonce"]
        response = self.client.get("/web/auth/callback", query_string={
            "id": "999", "auth_date": str(int(time.time())), "state": nonce,
            "hash": "0" * 64})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/web/auth/whoami").status_code, 401)

    def test_callback_state_is_one_time(self):
        self.client.get("/web/auth/login")
        with self.client.session_transaction() as sess:
            nonce = sess["web_auth_nonce"]
        signed = sign({"id": "123456", "auth_date": str(int(time.time()))})
        signed["state"] = nonce
        self.assertEqual(self.client.get("/web/auth/callback", query_string=signed).status_code, 302)
        self.assertEqual(self.client.get("/web/auth/callback", query_string=signed).status_code, 403)


if __name__ == "__main__":
    unittest.main()
