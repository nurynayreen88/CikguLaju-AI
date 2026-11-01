import hashlib
import hmac
import os
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app


class TelegramAuthRoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "accounts.db")
        with sqlite3.connect(self.db) as conn:
            conn.execute("CREATE TABLE teachers (telegram_id INTEGER PRIMARY KEY, lifetime INTEGER, credits INTEGER)")
            conn.execute("INSERT INTO teachers VALUES (12345, 1, 10)")
        self.config = {
            "CIKGULAJU_WEB_BOT_TOKEN": "12345:test-only-bot-token",
            "CIKGULAJU_WEB_SESSION_SECRET": "test-session-signing-secret-32-characters-long",
            "CIKGULAJU_WEB_ACCOUNT_DB": self.db,
            "CIKGULAJU_WEB_ACCOUNT_TABLE": "teachers",
            "CIKGULAJU_WEB_ACCOUNT_ID_COLUMN": "telegram_id",
            "CIKGULAJU_WEB_ACCOUNT_LIFETIME_COLUMN": "lifetime",
            "CIKGULAJU_WEB_ACCOUNT_CREDITS_COLUMN": "credits",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self, uid):
        data = {"id": str(uid), "auth_date": str(int(time.time()))}
        check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        key = hashlib.sha256(self.config["CIKGULAJU_WEB_BOT_TOKEN"].encode()).digest()
        data["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
        return data

    def test_disabled_without_configuration(self):
        with patch.dict(os.environ, self.config, clear=True):
            os.environ.pop("CIKGULAJU_WEB_BOT_TOKEN")
            self.assertEqual(self.client.post("/api/auth/telegram/widget", json=self.payload(12345)).status_code, 503)

    def test_valid_login_cookie_session_logout(self):
        with patch.dict(os.environ, self.config, clear=True):
            response = self.client.post("/api/auth/telegram/widget", json=self.payload(12345))
            self.assertEqual(response.status_code, 200)
            cookie = response.headers["Set-Cookie"]
            self.assertIn("Secure", cookie)
            self.assertIn("HttpOnly", cookie)
            self.assertEqual(self.client.get("/api/auth/telegram/session").status_code, 200)
            self.assertEqual(self.client.post("/api/auth/telegram/logout").status_code, 200)
            self.assertEqual(self.client.get("/api/auth/telegram/session").status_code, 401)

    def test_unknown_account_is_not_created(self):
        with patch.dict(os.environ, self.config, clear=True):
            self.assertEqual(self.client.post("/api/auth/telegram/widget", json=self.payload(99999)).status_code, 403)
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0], 1)

    def test_tampered_signature_rejected(self):
        with patch.dict(os.environ, self.config, clear=True):
            data = self.payload(12345)
            data["id"] = "99999"
            self.assertEqual(self.client.post("/api/auth/telegram/widget", json=data).status_code, 401)


if __name__ == "__main__":
    unittest.main()
