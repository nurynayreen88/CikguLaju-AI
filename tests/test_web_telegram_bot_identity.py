"""Do not leak Telegram bot tokens while diagnosing legacy login-widget domains."""
import json
import unittest
from unittest.mock import patch

from tools.run_web_production import app


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, size):
        return self.payload[:size]


class TelegramBotIdentityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.env = {
            "CIKGULAJU_WEB_BOT_USERNAME": "@CikguLajuBot",
            "CIKGULAJU_WEB_BOT_TOKEN": "123456:testing-token-never-deploy",
        }

    @patch("urllib.request.urlopen")
    def test_matching_bot(self, urlopen):
        urlopen.return_value = FakeResponse({"ok": True, "result": {"username": "CikguLajuBot", "id": 123}})
        with patch.dict("os.environ", self.env):
            r = self.client.get("/api/auth/telegram/bot-identity")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["expected_domain"], "cikgulaju-web.onrender.com")
        self.assertTrue(r.json["username_matches_token"])
        self.assertTrue(r.json["telegram_bot_identity_checked"])
        self.assertNotIn("testing-token", r.get_data(as_text=True))
        self.assertNotIn("123456:", r.get_data(as_text=True))

    @patch("urllib.request.urlopen")
    def test_mismatched_bot(self, urlopen):
        urlopen.return_value = FakeResponse({"ok": True, "result": {"username": "OtherBot"}})
        with patch.dict("os.environ", self.env):
            r = self.client.get("/api/auth/telegram/bot-identity")
        self.assertEqual(r.status_code, 409)
        self.assertFalse(r.json["username_matches_token"])
        self.assertEqual(r.json["telegram_token_bot_username"], "OtherBot")
        self.assertNotIn("testing-token", r.get_data(as_text=True))

    @patch("urllib.request.urlopen", side_effect=RuntimeError("fake network error"))
    def test_no_credentials_in_exception(self, _):
        with patch.dict("os.environ", self.env):
            r = self.client.get("/api/auth/telegram/bot-identity")
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.json["username_matches_token"])
        self.assertNotIn("testing-token", r.get_data(as_text=True))

    def test_missing_env_is_rejected(self):
        with patch.dict("os.environ", {"CIKGULAJU_WEB_BOT_USERNAME": "", "CIKGULAJU_WEB_BOT_TOKEN": ""}):
            r = self.client.get("/api/auth/telegram/bot-identity")
        self.assertEqual(r.status_code, 503)


if __name__ == "__main__":
    unittest.main()
